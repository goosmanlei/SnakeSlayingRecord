#!/usr/bin/env python3
"""Inventory exact state owners, relation history and submitted input references.

This command only opens an isolated task instance. The review-only explanation
inventory stays in runtime and is removed after approved physical cleanup.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import wave
from urllib.parse import urlencode
from urllib.request import ProxyHandler, build_opener

ROOT = Path(__file__).resolve().parents[1]


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def audit(a):
    from generation_workspace import isolated_instance
    instance = isolated_instance(ROOT, a.instance)
    sys.path.insert(0, str(a.system.resolve()))
    from review_desk.store import Store, canonical
    from review_desk import production as p, relation_explanations as explanations, business_codes
    store = Store(instance / '.runtime/review.sqlite3')
    try:
        rows = p.current_records(store)
        heads = {r['object_id']: r for r in rows}
        states = []
        for state in sorted((r for r in rows if r['kind'] == 'STATE'), key=lambda r: r['object_id']):
            ref = state['payload'].get('entity')
            owner = p.ref_record(store, ref, {'ENTITY'}) if ref else None
            states.append({'state': {'object_id':state['object_id'],'revision_id':state['id']}, 'title': state['payload']['title'],
                           'original_owner': ref, 'owner': ref, 'owner_title': owner['payload']['title'] if owner else None,
                           'model': state['payload'].get('state_model', 'historical-fragment'),
                           'status': state['payload'].get('status', 'active'),
                           'basis': '原状态的准确实体引用；保留已有归属，未新增历史关联' if owner else '待判断',
                           'sources': state['payload'].get('sources', []), 'changed': False})
        plan = explanations.plan(store)
        history, references = [], {}
        for item in plan['revisions']:
            old = p.record(store, revision_id=item['revision_id'])
            incoming = [dict(r) for r in store.db.execute('''SELECT d.*,o.id AS object_id,o.kind,
                d.from_revision=o.current_revision AS current FROM dependencies d
                JOIN revisions r ON r.id=d.from_revision JOIN objects o ON o.id=r.object_id
                WHERE d.to_revision=?''', (old['id'],))]
            outgoing = [dict(r) for r in store.db.execute('SELECT * FROM dependencies WHERE from_revision=?', (old['id'],))]
            history.append({**item, 'title': old['payload']['title'], 'label': old['payload']['label'],
                            'blocks': old['payload']['blocks'], 'current_revision': old['current_revision'],
                            'comments': [c for c in plan['comments'] if c['target_revision_id'] == old['id']],
                            'incoming': incoming, 'outgoing': outgoing,
                            'after': '旧修订保留关系事实和准确定位；说明原文清理，旧文字定位明确失效，不展示最新原文'})
        old_ids = {r['revision_id'] for r in plan['revisions']}
        semantic = {rid:[] for rid in old_ids}
        def locate(value, path=''):
            if isinstance(value,dict):
                for k,v in value.items(): yield from locate(v,path+'/'+k)
            elif isinstance(value,list):
                for i,v in enumerate(value): yield from locate(v,path+'/'+str(i))
            elif isinstance(value,str) and value in old_ids: yield value,path
        for rev in store.revisions():
            row = p.record(store, revision_id=rev['id'])
            payload = row['payload']
            for rid,path in locate(payload):
                semantic[rid].append({'object_id':row['object_id'],'revision_id':row['id'],'kind':row['kind'],
                                      'current':row['id']==row['current_revision'],'path':path})
            refs = []
            if row['kind'] == 'RELATION' and payload.get('relation_type') == 'entity':
                refs += [('relation-source', r, {}, i) for i,r in enumerate(payload.get('sources', []))]
                refs += [('relation-application', r, {}, i) for i,r in enumerate(payload.get('applies_to', []))]
            if row['kind'] == 'CALL':
                refs += [('actual-input', v.get('reference', v), v, i) for i,v in enumerate(payload.get('inputs', []))]
            for role, ref, selection, index in refs:
                key = canonical({'reference': ref, **{k:selection[k] for k in ('component_id','crop','range') if k in selection}})
                item = references.setdefault(key, {'reference': ref, 'selection': {k:selection[k] for k in ('component_id','crop','range') if k in selection}, 'uses': []})
                item['uses'].append({'object_id': row['object_id'], 'revision_id': row['id'], 'role': role, 'index':index})
        for item in history: item['payload_references']=semantic[item['revision_id']]
        opener = build_opener(ProxyHandler({}))
        for item in references.values():
            ref = item['reference']
            try:
                row = p.ref_record(store, ref)
                source = row['kind'] in ('EPISODE','STORY','SOURCE') or bool(ref.get('scene_id') or ref.get('block_ids'))
                if source: p.source_excerpt(store, ref)
                else: p.snapshot(store, object_id=ref['object_id'], revision_id=ref['revision_id'])
                selection = item['selection']
                if selection.get('component_id'):
                    _, component = p.component_for(store, ref, selection['component_id'])
                    try:
                        p.validate_selection(component, selection)
                    except ValueError:
                        # PCM metadata in two historic calls was rounded. Check
                        # the submitted range against original WAV frames,
                        # never edit its immutable call or component descriptor.
                        path=instance/'export/assets'/component['file']
                        if component['mime']!='audio/wav' or hashlib.sha256(path.read_bytes()).hexdigest()!=component['sha256']:raise
                        with wave.open(str(path),'rb') as audio:
                            duration=audio.getnframes()/audio.getframerate()
                        p.validate_selection({**component,'duration_seconds':duration},selection)
                        item['precision_check']={'registered_duration_seconds':component['duration_seconds'],'original_pcm_duration_seconds':duration,'historical_input_unchanged':True}
                query = {'object_id':ref['object_id'], 'revision_id':ref['revision_id']}
                if ref.get('scene_id'): query['scene_id'] = ref['scene_id']
                if ref.get('block_ids'): query['block_ids'] = ','.join(ref['block_ids'])
                item['kind'], item['route'] = row['kind'], '/api/production' + ('/source' if source else '') + '?' + urlencode(query)
                if a.base_url:
                    with opener.open(a.base_url.rstrip('/') + item['route'], timeout=30) as response:
                        json.load(response)
                item['readable'] = True
            except (ValueError, OSError) as error:
                item['readable'], item['error'] = False, str(error)
        old_ids = {r['revision_id'] for r in plan['revisions']}
        archives = []
        files = subprocess.check_output(['git','-C',str(ROOT),'ls-files','-z'], text=True).split('\0')
        for name in files:
            if not name.endswith(('.json','.md','.py')): continue
            raw = (ROOT / name).read_bytes()
            hits = sorted(r for r in old_ids if r.encode() in raw)
            if hits: archives.append({'path':name, 'revisions':hits, 'sha256':hashlib.sha256(raw).hexdigest()})
        result = {'format':'entity-material-audit-v1', 'state_count':len(states),
                  'unowned_states':sum(r['owner'] is None for r in states),
                  'state_models':dict(Counter(r['model'] for r in states)), 'states':states,
                  'relationship_cleanup':plan, 'archive_references':archives,
                  'references':list(references.values()), 'reference_count':len(references),
                  'reference_failures':sum(not r['readable'] for r in references.values()),
                  'codes':business_codes.dump(store)}
        save(a.output, result)
        # This full text is intentionally NOT a managed archive or recovery copy.
        # It exists only for the user's pre-deletion review.
        save(a.output.parent / 'relationship-before-review.json', history)
        print(json.dumps({k:result[k] for k in ('state_count','unowned_states','state_models','reference_count','reference_failures')}, ensure_ascii=False))
    finally:
        store.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--system', type=Path, required=True)
    parser.add_argument('--instance', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--base-url')
    audit(parser.parse_args())
