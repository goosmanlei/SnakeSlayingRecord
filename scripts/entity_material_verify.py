#!/usr/bin/env python3
"""Verify that task cleanup changed only approved explanation payloads."""
import argparse
import hashlib
import json
from pathlib import Path
import sqlite3
import sys

from entity_material_release import fingerprint, NEW_TABLES

ROOT = Path(__file__).resolve().parents[1]


def verify(a):
    sys.path.insert(0, str(a.system.resolve()))
    from review_desk import relation_explanations as cleanup
    plan = json.loads((ROOT / 'production/entity-material/cleanup-plan.json').read_text())['relationships']
    before, after = fingerprint(a.before), fingerprint(a.after)
    if set(after) != set(before) | NEW_TABLES:
        raise ValueError('unexpected database table change')
    for name in before:
        if name != 'revisions' and before[name] != after[name]:
            raise ValueError('unapproved business data change: ' + name)
    if before['revisions']['schema'] != after['revisions']['schema'] or before['revisions']['count'] != after['revisions']['count']:
        raise ValueError('revision schema/count changed')
    with sqlite3.connect(a.before) as src, sqlite3.connect(a.after) as dst:
        src.row_factory = dst.row_factory = sqlite3.Row
        originals = {r['id']:dict(r) for r in src.execute('SELECT * FROM revisions')}
        expected = {r['revision_id'] for r in plan['revisions']}
        changed = set()
        for row in dst.execute('SELECT * FROM revisions'):
            row = dict(row)
            previous = originals[row['id']]
            if row != previous:
                if row['id'] not in expected or {**row,'payload':previous['payload']} != previous:
                    raise ValueError('unapproved revision change')
                old, new = json.loads(previous['payload']), json.loads(row['payload'])
                if new != cleanup.cleaned(old) or cleanup.facts(old) != cleanup.facts(new):
                    raise ValueError('relationship facts changed')
                changed.add(row['id'])
        if changed != expected:
            raise ValueError('incomplete explanation cleanup')
        if dst.execute('PRAGMA integrity_check').fetchone()[0] != 'ok' or dst.execute('PRAGMA foreign_key_check').fetchone():
            raise ValueError('database integrity failure')
        counts = {name:dst.execute('SELECT count(*) FROM "'+name+'"').fetchone()[0] for name in ('objects','revisions','comments','comment_events')}
    import subprocess
    original_manifest = json.loads(subprocess.check_output(['git','-C',str(ROOT),'show',a.base+':export/manifest.json']))
    current = json.loads((ROOT / 'export/manifest.json').read_text())
    assets = {k:v for k,v in original_manifest['files'].items() if k.startswith('assets/')}
    if assets != {k:v for k,v in current['files'].items() if k.startswith('assets/')}:
        raise ValueError('media/managed archive bytes changed')
    result = {'format':'entity-material-preservation-v1', 'changed_revisions':len(changed),
              'other_business_tables_unchanged':True, 'comments_and_events_unchanged':True,
              'relation_facts_and_endpoints_unchanged':True, 'new_tables':sorted(NEW_TABLES),
              'media_and_archive_hashes_unchanged':len(assets), 'schema_version':current['schema_version'],
              'integrity_check':'ok', 'counts':counts, 'formal_writes':False}
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(result,ensure_ascii=False))


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--system',type=Path,required=True)
    p.add_argument('--before',type=Path,required=True)
    p.add_argument('--after',type=Path,required=True)
    p.add_argument('--base',required=True)
    p.add_argument('--output',type=Path,required=True)
    verify(p.parse_args())
