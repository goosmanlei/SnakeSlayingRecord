"""CAS increments for current production; no saved previous production bodies."""
import hashlib
import json
from pathlib import Path
import sqlite3

KEYS = {
    'objects': ('id',), 'revisions': ('id',),
    'dependencies': ('from_revision','to_revision','role'),
    'comments': ('id',), 'material_content': ('id',),
    'material_archive_files': ('path',), 'material_aliases': ('alias_id',),
    'business_codes': ('object_id',), 'business_comments': ('comment_id',),
    'business_relations': ('object_id',), 'business_relation_aliases': ('alias_id',), 'audiovisual_notes': ('object_id',),
    'production_current_records': ('object_id',),
    'production_submissions': ('operation_id',), 'production_candidates': ('id',),
    'production_candidate_targets': ('candidate_id','material_id'),
    'production_comment_quotes': ('comment_id',), 'production_current_operations': ('id',),
    'production_response_excerpts': ('evidence_id','locator'),
}
MUTABLE = {'objects','revisions','dependencies','comments','production_current_records',
           'material_aliases','material_archive_files','business_relations','audiovisual_notes'}
FORMAT = 'production-current-publication-v1'

def publication_media(changes):
    try:from .generation_publication import revision_media
    except ImportError:from generation_publication import revision_media
    from review_desk.material_reference import EVIDENCE
    result={v['file']:v for v in revision_media(changes['revisions'])}
    for change in changes['production_current_operations']:
        if not change['after']:continue
        receipt=json.loads(change['after']['result'])
        if receipt.get('format')!=EVIDENCE:continue
        for item in receipt['references']:
            component=item.get('component')
            if component:
                name=component['file'];expected={k:component[k] for k in ('file','sha256','bytes')}
                if name in result and result[name]!=expected:raise ValueError('recovered original media conflict')
                result[name]=expected
    return [result[name] for name in sorted(result)]

def canonical(value):
    return json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'))

def sha(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()

def pk(table,row):
    return tuple(row[k] for k in KEYS[table])

def verify_applied(db, plan, identity):
    """Read back every changed row from a fresh post-commit snapshot."""
    original_factory = db.row_factory
    db.row_factory = sqlite3.Row
    try:
        if [r[0] for r in db.execute('PRAGMA integrity_check')] != ['ok']:
            raise ValueError('published database integrity check failed')
        if (not db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='generation_publications'").fetchone()
                or not db.execute('SELECT 1 FROM generation_publications WHERE id=?', (identity,)).fetchone()):
            raise ValueError('publication transaction receipt is missing on readback')
        counts = {}
        for table, changes in plan['changes'].items():
            for change in changes:
                where = ' AND '.join(k+'=?' for k in KEYS[table])
                row = db.execute('SELECT * FROM '+table+' WHERE '+where, change['key']).fetchone()
                if (dict(row) if row else None) != change['after']:
                    raise ValueError('publication readback differs: '+table+' '+str(change['key']))
            counts[table] = len(changes)
        return {'integrity': 'ok', 'transaction_receipt': True, 'exact_changed_rows': counts}
    finally:
        db.row_factory = original_factory

def supported(obj,revision):
    from review_desk.production_current import RECORD_KINDS
    if obj['kind'] in RECORD_KINDS:return True
    payload=json.loads(revision['payload'])
    return (obj['version']==revision['version']==1 and
            (obj['kind']=='NOTE' and payload.get('format') in ('managed-method-execution-v1','managed-method-artifact-v1') and payload.get('private') is False
             or obj['kind']=='GUIDANCE' and payload.get('format')=='comment-handling-v1'))

def build(before,after):
    from review_desk.semantic_consolidation import allows_publication_change
    receipts = [json.loads(r['result']) for r in after.get('production_current_operations', [])]
    if set(before)!=set(after) or before['production_current_policy']!=after['production_current_policy']:
        raise ValueError('current publication requires the same migrated schema and baseline')
    changes={table:[] for table in KEYS if table in before}
    for table,old_rows in before.items():
        if table=='comment_events':continue
        if table not in changes:
            if sorted(map(canonical,old_rows))!=sorted(map(canonical,after[table])):
                raise ValueError('current production cannot change '+table)
            continue
        old={pk(table,r):r for r in old_rows};new={pk(table,r):r for r in after[table]}
        for key in sorted(old.keys()|new.keys()):
            a,b=old.get(key),new.get(key)
            if a==b:continue
            semantic = allows_publication_change(table,a,b,receipts)
            if b is None and table not in ('dependencies','material_aliases') and not semantic:
                raise ValueError('current publication cannot remove evidence: '+table)
            if a is not None and table not in MUTABLE and not semantic:
                raise ValueError('immutable evidence changed: '+table)
            changes[table].append({'key':list(key),'before_sha256':sha(a) if a else None,'after':b})
    old_events={r['id']:r for r in before['comment_events']};new_events={r['id']:r for r in after['comment_events']}
    if any(new_events.get(i)!=r for i,r in old_events.items()):raise ValueError('original comment events changed')
    objects={r['id']:r for r in after['objects']};revisions={r['id']:r for r in after['revisions']}
    scope={r['after']['id'] for r in changes['objects']}
    scope.update(r['after']['target_object_id'] for r in changes['comments'])
    if any(not supported(objects[oid],revisions[objects[oid]['current_revision']]) for oid in scope):
        raise ValueError('current publication cannot change story, configuration or method definitions')
    changed={r['after']['id'] for r in changes['revisions']}
    refs={d['to_revision'] for d in after['dependencies'] if d['from_revision'] in changed}-changed
    old_revisions={r['id']:r for r in before['revisions']}
    expected={rid:sha(old_revisions[rid]) for rid in refs}
    try:from .generation_publication import revision_media
    except ImportError:from generation_publication import revision_media
    return {'format':FORMAT,'baseline':before['production_current_policy'],'scope':sorted(scope),
            'changes':changes,'expected_references':expected,
            'comment_events':[r for i,r in sorted(new_events.items()) if i not in old_events],
            'media':publication_media(changes)}

def apply(db,plan,*,identity=None,media_root=None):
    try:from .generation_publication import journal,publication_id,revision_media,validate_numbered_row
    except ImportError:from generation_publication import journal,publication_id,revision_media,validate_numbered_row
    from review_desk import production_current as current, production as p
    from review_desk.store import Store
    from review_desk.production_current_bundle import validate
    from review_desk.semantic_consolidation import allows_publication_change, is_retired
    if plan.get('format')!=FORMAT or set(plan.get('changes',{}))!=set(KEYS):raise ValueError('invalid current publication')
    if plan['media']!=publication_media(plan['changes']):raise ValueError('current media manifest differs')
    original_factory=db.row_factory
    def lookup(table,keys):
        row=db.execute('SELECT * FROM '+table+' WHERE '+' AND '.join(k+'=?' for k in KEYS[table]),keys).fetchone()
        return dict(row) if row else None
    def mutate():
        db.row_factory=sqlite3.Row
        receipts = [json.loads(r['result']) for r in db.execute('SELECT result FROM production_current_operations')]
        receipts += [json.loads(c['after']['result']) for c in plan['changes']['production_current_operations'] if c['after']]
        if [dict(r) for r in db.execute('SELECT * FROM production_current_policy')]!=plan['baseline']:
            raise ValueError('current migration baseline differs')
        scope=set(plan['scope']);saved={};changed_rids={c['after']['id'] for c in plan['changes']['revisions']}
        if not {c['after']['id'] for c in plan['changes']['objects']}<=scope:raise ValueError('objects outside scope')
        for rid,expected in plan['expected_references'].items():
            if sha(lookup('revisions',(rid,)))!=expected:raise ValueError('current dependency changed: '+rid)
        for table,changes in plan['changes'].items():
            seen=set();columns={r['name'] for r in db.execute('PRAGMA table_info('+table+')')}
            for change in changes:
                key=tuple(change['key']);new=change['after'];old=lookup(table,key)
                if key in seen or (sha(old) if old else None)!=change['before_sha256']:raise ValueError('formal row changed: '+table)
                seen.add(key);saved[table,key]=old
                if new is not None and (set(new)!=columns or pk(table,new)!=key):raise ValueError('row schema or identity changed')
                semantic=allows_publication_change(table,old,new,receipts)
                if new is None and table not in ('dependencies','material_aliases') and not semantic:raise ValueError('cannot delete current evidence')
                if old and table not in MUTABLE and not semantic:raise ValueError('immutable evidence cannot change')
                row=new or old
                owner=row.get('object_id') or row.get('target_object_id')
                if table not in ('business_codes',) and owner and owner not in scope:raise ValueError('row outside current publication scope')
                if table=='dependencies' and row['from_revision'] not in changed_rids:raise ValueError('dependency outside changed content')
                if table=='revisions':
                    obj=next((c['after'] for c in plan['changes']['objects'] if c['after']['id']==row['object_id']),None)
                    if not obj or not supported(obj,row):raise ValueError('non-production revision')
                    if old and obj['kind'] not in current.RECORD_KINDS:raise ValueError('immutable non-production revision')
                    if old and (row['id']!=old['id'] or row['object_id']!=old['object_id']):raise ValueError('current identity changed')
                    before=json.loads(old['payload']) if old else None;after=json.loads(row['payload'])
                    if old and obj['kind']=='CALL':
                        for field in ('method','tool','model','parameters','prompt','inputs','output','randomization','execution','method_basis','generation_requirement','prepared_plan','request','response','cost','request_id','actual_seed'):
                            if field in before and before[field]!=after.get(field):raise ValueError('real call evidence changed: '+field)
                        if before['status']=='completed' and after['status']!='completed':raise ValueError('completed call moved backwards')
                    if old and obj['kind']=='ASSET':
                        if any(before.get(f)!=after.get(f) for f in ('production','external_source')):raise ValueError('candidate source changed')
                        if is_retired(after):
                            original_hash=before['original_content_sha256'] if is_retired(before) else current.checksum(before)
                            if after.get('original_content_sha256')!=original_hash:raise ValueError('candidate retirement differs from exact original')
                            components=after.get('components') or [{('file' if k=='former_file' else k):v for k,v in c.items()} for c in after.get('former_components', [])]
                            original_components=before.get('components') or [{('file' if k=='former_file' else k):v for k,v in c.items()} for c in before.get('former_components', [])]
                            if components!=original_components:raise ValueError('retired original metadata changed')
                        else:
                            components={c['id']:c for c in after['components']}
                            if any(components.get(c['id'])!=c for c in before['components']):raise ValueError('candidate original changed')
                if old and table=='objects' and any(old[f]!=new[f] for f in ('id','kind','created_at','current_revision')):raise ValueError('current object identity changed')
                if old and table=='comments' and any(old[f]!=new[f] for f in ('id','source_id','target_object_id','target_revision_id','anchor','created_at')):raise ValueError('original opinion changed')
        store=Store.__new__(Store);store.db=db
        dbfile=next(r[2] for r in db.execute('PRAGMA database_list') if r[1]=='main')
        store.db_path=(Path(media_root)/'.runtime/review.sqlite3') if media_root else Path(dbfile)
        store._material_functions();db.execute('PRAGMA defer_foreign_keys=ON')
        # CAS metadata first allows checksum triggers to validate each updated body.
        order=['objects','production_current_records','revisions']+[t for t in KEYS if t not in ('objects','production_current_records','revisions')]+['production_current_records']
        current_pass=0
        for table in order:
            if table=='production_current_records':current_pass+=1
            for change in plan['changes'][table]:
                key=tuple(change['key']);new=change['after'];old=saved[table,key]
                if table=='production_current_records' and (old is None)!=(current_pass==2):continue
                where=' AND '.join(k+'=?' for k in KEYS[table])
                if new is None:db.execute('DELETE FROM '+table+' WHERE '+where,key)
                elif old is None:
                    db.execute('INSERT INTO '+table+' ('+','.join(new)+') VALUES ('+','.join('?' for _ in new)+')',tuple(new.values()))
                else:
                    fields=[k for k in new if k not in KEYS[table]]
                    db.execute('UPDATE '+table+' SET '+','.join(k+'=?' for k in fields)+' WHERE '+where,tuple(new[k] for k in fields)+key)
        changed_comments={c['after']['id'] for c in plan['changes']['comments']};events=[]
        for row in plan['comment_events']:
            if set(row)!={'id','comment_id','action','body','at'} or row['comment_id'] not in changed_comments:raise ValueError('comment event outside changed opinion')
            r=db.execute('INSERT INTO comment_events(comment_id,action,body,at) VALUES (?,?,?,?)',tuple(row[k] for k in ('comment_id','action','body','at')))
            events.append({'source_id':row['id'],'published_id':r.lastrowid})
        current.read_adapters(store)
        from review_desk.material_storage import row_factory
        db.row_factory=row_factory(store)
        from review_desk.material_archives import read_scope
        # The media root may be a clean worktree without a live database. Read
        # archived metadata from this transaction instead of rebuilding an
        # exported content index for each original being validated.
        with read_scope(store):
            validate(store)
        for table in ('business_codes','business_comments'):
            for change in plan['changes'][table]:validate_numbered_row(db,table,change['after'],scope,{})
        return {'contract':FORMAT,'changed_rows':{t:len(v) for t,v in plan['changes'].items()},'comment_events':events}
    try:return journal(db,identity or publication_id(plan),mutate)
    finally:
        db.row_factory=original_factory
        try:from .material_model_io import sqlite_compatibility
        except ImportError:from material_model_io import sqlite_compatibility
        sqlite_compatibility(db)
