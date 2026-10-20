"""Full, private Schema 16 export and empty-instance recovery.

Requires explicit isolated source/destination paths; invokes the normal export
and recovery contracts, including full exact offline-byte verification.
"""
import json
import os
from pathlib import Path
import shutil
import sys
import time
from review_desk import bundle, read_cache, resource_bundle, resources, editing_api
from review_desk.store import Store

source, target, output = map(Path, sys.argv[1:4])
assert os.environ.get('REVIEW_RESOURCES_OFFLINE') == '1'
assert (source/'performance-copy.json').is_file() and not target.exists()
assert source != target and source.name == 'recovery-source' and target.name == 'recovered-empty'
started = time.monotonic()
store = Store(source/'.runtime/review.sqlite3')
read_cache.attach(store)
before = resource_bundle.database_identity(store.db_path)
print(json.dumps({'phase':'export','tables':len(before)}),flush=True)
manifest = bundle.export(store, source/'export')
store.close()
assert resource_bundle.database_identity(source/'.runtime/review.sqlite3') == before
print(json.dumps({'phase':'exported','seconds':time.monotonic()-started,'snapshot_sha256':manifest['snapshot']['sha256']}),flush=True)
target.mkdir()
resource_bundle.copy_instance_metadata(source,target)
shutil.copytree(source/'export',target/'export')
shutil.copytree(source/'resource-bundle',target/'resource-bundle',copy_function=os.link)
checks={'objects':0,'bytes':0,'seconds':0}
original = resources.verify_remote
def measured(root,spec):
    tick=time.monotonic()
    result=original(root,spec)
    checks['objects']+=1;checks['bytes']+=spec['bytes'];checks['seconds']+=time.monotonic()-tick
    if checks['objects']%100==0:print(json.dumps({'phase':'verify',**checks}),flush=True)
    return result
resources.verify_remote=measured
store=Store(target/'.runtime/review.sqlite3')
try:
    assert len(store.objects())==0
    restored=bundle.restore(store,target/'export')
    read_cache.attach(store)
    assert resource_bundle.database_identity(store.db_path)==before
    indexes=[r[1] for r in store.db.execute('PRAGMA index_list(production_current_operations)')]
    assert 'production_operation_format' in indexes
    evidence=json.loads((source/'performance-copy.json').read_text())
    result=editing_api.dispatch(store,target,'review',evidence['workloads'][1]['body'])
    report={'complete':True,'seconds':time.monotonic()-started,'database':before,'snapshot_sha256':manifest['snapshot']['sha256'],
            'exact_remote_verification':checks,'mode':'offline; network disabled; complete catalog and snapshot bytes verified by normal restore','indexes':indexes,'review_elements':len(result['elements']),
            'review_keys':sorted(result),'boundary':'Full private source, normal Schema 16 export and restore into an empty instance; all business tables equal. No formal database replaced. Offline originals cloned from the retained complete medium; source and empty target share immutable private hardlinks, and target materializes its own verified cache.'}
    output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='database'}),flush=True)
finally:
    store.close()
