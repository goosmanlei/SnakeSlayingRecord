#!/usr/bin/env python3
"""Apply individually authored shot readings without rebuilding media plans.

The reading documents name exact existing material revisions. This entry point
only writes an isolated task instance; formal application needs the reviewed
cleanup manifest and a separately authorized publication window.
"""
import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys

from generation_workspace import generation_root, isolated_instance, contained

ROOT = Path(__file__).resolve().parents[1]


def prepare(store, sources):
    from review_desk import production as p, audiovisual_cleanup as cleanup
    from review_desk.audiovisual import READING_CONTRACT
    from review_desk.audiovisual_notes import get as note
    from review_desk.store import canonical
    from review_desk.version_consolidation import new_identity
    records, resolved, notes, authored, selected = [], {}, {}, {}, set()
    current = {r['object_id']: r for r in p.current_records(store, {'AV_EPISODE','AV_SCENE','AV_SHOT'})}
    def append(row, payload):
        if row['payload'] == payload:
            resolved[row['object_id']] = row['id'];return
        oid = row['object_id']
        records.append({'object_id': oid, 'kind': row['kind'], 'expected_version': row['version'], 'payload': payload})
        resolved[oid] = new_identity(store, oid, row['version']+1, payload)
    for path in sources:
        document = json.loads(path.read_text())
        relative = path.relative_to(ROOT).as_posix()
        authored[relative] = hashlib.sha256(path.read_bytes()).hexdigest()
        if document['format'] != 'audiovisual-reading-v1':raise ValueError('unsupported authored reading')
        source = (ROOT / document['reading']['source']).resolve(strict=True)
        if not source.is_relative_to(ROOT) or hashlib.sha256(source.read_bytes()).hexdigest() != document['reading']['source_sha256']:
            raise ValueError('locked screenplay changed; read and author against the current input')
        for item in document['shots']:
            oid = item['object_id']; row = current[oid]
            if oid in selected:raise ValueError('duplicate authored shot')
            if item['sources'] != row['payload']['sources']:raise ValueError('authored story evidence differs')
            selected.add(oid)
            payload = {k: deepcopy(v) for k,v in row['payload'].items()
                       if k not in cleanup.AV_FIELDS | {'retired_design_text'}}
            payload.update(reading_contract=READING_CONTRACT, blocks=[], purpose=item['purpose'],
                           key_states=item['key_states'], products=item['products'],
                           authoring={'file':relative, 'object_id':oid})
            append(row, payload)
        for oid, body in document.get('working_notes', {}).items():
            if oid in notes:raise ValueError('duplicate working note')
            if oid not in current or current[oid]['kind'] not in {'AV_EPISODE','AV_SCENE'}:
                raise ValueError('working note must belong to a current episode or scene')
            if note(store,oid)['body'] != body:
                notes[oid] = {'object_id':oid, 'body':body, 'expected_etag':note(store,oid)['etag']}
    # Exact composition changes propagate upward; other shot payloads do not.
    for kind, field in (('AV_SCENE','shots'),('AV_EPISODE','scenes')):
        for row in current.values():
            if row['kind'] != kind or not any(ref['object_id'] in selected for ref in row['payload'][field]):continue
            oid = row['object_id'];selected.add(oid)
            payload = {k:deepcopy(v) for k,v in row['payload'].items() if k not in cleanup.AV_FIELDS | {'retired_design_text'}}
            payload.update(reading_contract=READING_CONTRACT, blocks=[])
            payload[field] = [{'object_id':ref['object_id'], 'revision_id':resolved.get(ref['object_id'],ref['revision_id'])}
                              for ref in row['payload'][field]]
            if oid not in notes and not note(store,oid)['body']:
                notes[oid] = {'object_id':oid, 'body':row['payload'].get('purpose',''), 'expected_etag':note(store,oid)['etag']}
            append(row,payload)
    removal = cleanup.plan(store, selected)
    removal['heads'].update({oid:resolved[oid] for oid in selected if oid in resolved})
    return {'format':'audiovisual-reading-migration-v1', 'authored_sha256':authored,
            'import': {'format':'production-import-v1', 'expected_heads':{oid:current[oid]['id'] for oid in selected},'records':records},
            'cleanup':removal, 'working_notes':list(notes.values())}


def apply(store, plan, validate_only=False):
    from review_desk import production as p, audiovisual_cleanup as cleanup
    from review_desk.audiovisual_notes import get as note
    from review_desk.store import now, Conflict
    store.db.execute('BEGIN IMMEDIATE')
    try:
        for item in plan['working_notes']:
            if note(store,item['object_id'])['etag'] != item['expected_etag']:raise Conflict('working note changed')
        imported = p._import_records(store,plan['import'],transaction=False) if plan['import']['records'] else {'records':[]}
        result = cleanup.apply(store,plan['cleanup'],transaction=False)
        for item in plan['working_notes']:
            store.db.execute('INSERT INTO audiovisual_notes VALUES (?,?,?) ON CONFLICT(object_id) DO UPDATE SET body=excluded.body,updated_at=excluded.updated_at',
                             (item['object_id'],item['body'],now()))
        if validate_only:store.db.rollback()
        else:store.db.commit()
        return {**result,'new_readings_and_compositions':len(imported['records']), 'validate_only':validate_only}
    except BaseException:
        store.db.rollback();raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('prepare','apply','validate'))
    parser.add_argument('--system', type=Path, required=True)
    parser.add_argument('--instance', type=Path, required=True)
    parser.add_argument('--source', type=Path, action='append', required=True)
    parser.add_argument('--plan', type=Path, required=True)
    args=parser.parse_args()
    root=generation_root(ROOT); instance=isolated_instance(root,args.instance)
    path=contained(root,args.plan);sources=[contained(root,p) for p in args.source]
    sys.path.insert(0,str(args.system.resolve(strict=True)))
    from review_desk.store import Store
    store=Store(instance/'.runtime/review.sqlite3')
    try:
        actual=prepare(store,sources)
        if args.command=='prepare':
            path.parent.mkdir(parents=True,exist_ok=True)
            path.write_text(json.dumps(actual,ensure_ascii=False,indent=2)+'\n')
            print(json.dumps({'append':len(actual['import']['records']), 'redact':len(actual['cleanup']['revisions']),
                              'remove_decisions':len(actual['cleanup']['decisions'])}))
        else:
            plan=json.loads(path.read_text())
            if plan!=actual:raise ValueError('authored content or database changed; prepare a fresh migration')
            print(json.dumps(apply(store,plan,validate_only=args.command=='validate')))
    finally:store.close()


if __name__=='__main__':main()
