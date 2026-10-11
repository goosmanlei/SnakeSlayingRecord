"""Read back the reviewed scope, handoffs, exact inputs and protected history."""
import argparse
import collections
import hashlib
import json
from pathlib import Path
import sqlite3
import sys


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def audit(store, baseline, decisions):
    from review_desk import production as p, production_current as current
    from review_desk import material_origin, material_reference, semantic_consolidation as semantic, ui_projection
    rows = {r['object_id']: r for r in p.current_records(store)}
    active = {oid: r for oid, r in rows.items() if r['payload'].get('status') != 'withdrawn'}
    needs = [r for r in active.values() if r['kind'] == 'REQUIREMENT']
    states = [r for r in active.values() if r['kind'] == 'STATE']
    shots = [r for r in active.values() if r['kind'] == 'AV_SHOT']
    errors = []
    ownership = []
    current_inputs = []
    frozen_inputs = []
    state_audit = []
    for row in needs:
        origin = material_origin.validate(store, row['payload'])
        ownership.append({'material': row['object_id'], 'code': material_reference.code(store, row['object_id']),
                          'origin': origin['object_id'], 'kind': origin['kind'],
                          'purpose': row['payload']['purpose']})

    def read_input(value, index, consumer, history):
        slot = current.input_slot(store, value, index)
        if slot.get('nonmedia'):
            return None
        item = {'consumer': consumer, 'index': index, 'reference': value.get('reference', value),
                'disposition': slot.get('disposition'), 'material': slot.get('canonical_material_id'),
                'candidate': slot.get('candidate_number'), 'issues': slot['issues']}
        for key in ('component_id', 'crop', 'range', 'sha256'):
            if key in value: item[key] = value[key]
        if slot.get('component'): item['original_sha256'] = slot['component']['sha256']
        if slot.get('reason'): item['reason'] = slot['reason']
        if slot.get('subjects'): item['subjects'] = slot['subjects']
        if not history and slot['issues'] not in ([], ['尚未选定候选']): errors.append(item)
        return item

    for row in needs:
        for i, value in enumerate(row['payload'].get('generation', {}).get('inputs', [])):
            item = read_input(value, i, row['object_id'], False)
            if item: current_inputs.append(item)
    for row in store.db.execute('SELECT c.id,s.snapshot FROM production_candidates c JOIN production_submissions s ON s.operation_id=c.operation_id ORDER BY c.id'):
        for i, value in enumerate(json.loads(row['snapshot'])['request'].get('inputs', [])):
            item = read_input(value, i, row['id'], True)
            if item: frozen_inputs.append(item)
    for oid, choice in decisions['states'].items():
        row = rows.get(oid) or p.record(store, oid)
        if choice['action'] == 'retain':
            assert row['payload'].get('status') != 'withdrawn', oid
        else:
            semantic.validate_retirement(store, oid, 'STATE', row['payload'])
            assert set(row['payload']) <= {'format','title','status','original_kind','original_content_sha256','operation_id','reason','blocks'}, oid
        state_audit.append({'state': oid, 'action': choice['action'], 'reason': choice['reason'],
                            'direct_materials': [v['material'] for v in ownership if v['origin'] == oid]})
    keys = []
    for row in shots:
        for key in row['payload']['key_states']:
            targets = [v['object_id'] for v in key['requirements']]
            assert targets and all(active[v]['payload']['scope']['object_id'] == row['object_id'] for v in targets)
            keys.append({'shot': row['object_id'], 'key': key['id'], 'description': key['description'],
                         'direct_materials': targets,
                         'decision': '保留：本镜起点或指定可读阶段有独立准备用途，直接需求已逐项核对。'})
    entries = ui_projection.material_entries(store)
    assert {r['object_id'] for r in entries} == {r['object_id'] for r in needs}
    semantic.validate(store)
    material_reference.validate_evidence(store)
    protected = {}
    old = sqlite3.connect(baseline); old.row_factory = sqlite3.Row
    try:
        for table in ('production_submissions','production_candidates','production_candidate_targets','comments','comment_events'):
            before = sorted((dict(r) for r in old.execute('SELECT * FROM '+table)), key=lambda r: json.dumps(r, sort_keys=True))
            after = sorted((dict(r) for r in store.db.execute('SELECT * FROM '+table)), key=lambda r: json.dumps(r, sort_keys=True))
            protected[table] = {'before': len(before), 'after': len(after), 'unchanged': before == after, 'sha256': digest(before)}
            assert before == after, table
        for kinds, label in ((('CALL','ASSET'), 'calls_and_originals'),
                             (('STORY','EPISODE','SOURCE','INPUT_LOCK'), 'story_works')):
            query = 'SELECT r.* FROM revisions r JOIN objects o ON o.id=r.object_id WHERE o.kind IN ('+','.join('?' for _ in kinds)+') ORDER BY r.id'
            before = [dict(r) for r in old.execute(query, kinds)]
            after = [dict(r) for r in store.db.execute(query, kinds)]
            protected[label] = {'before': len(before), 'after': len(after), 'unchanged': before == after, 'sha256': digest(before)}
            assert before == after, label
    finally:
        old.close()
    candidate_count = store.db.execute('SELECT count(*) FROM production_candidates').fetchone()[0]
    assert not store.db.execute('SELECT candidate_id FROM production_candidate_targets GROUP BY candidate_id HAVING count(*)!=1').fetchone()
    return {'format': 'unique-origin-audit-v1',
            'counts': {'materials': len(needs), 'origins': dict(collections.Counter(v['kind'] for v in ownership)),
                       'states': len(states), 'reviewed_states': len(state_audit), 'shots': len(shots),
                       'shot_keys': len(keys), 'candidates': candidate_count,
                       'current_media_inputs': len(current_inputs), 'frozen_media_inputs': len(frozen_inputs),
                       'current_self_candidate_uses': sum(v['consumer']==v['material'] and v['candidate'] is not None for v in current_inputs)},
            'ownership': ownership, 'states': state_audit, 'shot_keys': keys,
            'current_inputs': current_inputs, 'frozen_inputs': frozen_inputs,
            'protected': protected, 'unexpected_current_input_issues': errors}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--system', type=Path, required=True)
    parser.add_argument('--database', type=Path, required=True)
    parser.add_argument('--baseline', type=Path, required=True)
    parser.add_argument('--decisions', type=Path, default=Path('production/unique-origin/reviewed-decisions.json'))
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(); sys.path.insert(0, str(args.system.resolve()))
    from review_desk.store import Store
    from review_desk import production as p
    store = Store(args.database)
    try:
        with p.read_scope(store): result = audit(store, args.baseline, json.loads(args.decisions.read_text()))
        args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n')
        print(json.dumps({'counts': result['counts'], 'input_issues': len(result['unexpected_current_input_issues'])}))
    finally:
        store.close()


if __name__ == '__main__': main()
