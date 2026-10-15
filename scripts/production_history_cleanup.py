"""Redact inactive local production copies while retaining story and accounting.

These outputs are explicitly historical evidence, never valid recovery bundles.
The caller supplies exact paths/hashes and coordinates active writers.
"""
import hashlib
import json
import re
import sqlite3
from pathlib import Path
from types import SimpleNamespace

from review_desk import production_reset as reset
from review_desk.store import canonical
from review_desk.material_storage import hydrate
from review_desk.material_content_stream import rows

PRODUCTION_KINDS = reset.KINDS | {'SHOT', 'SCENE', 'ASSEMBLY', 'DELIVERABLE',
    'MATERIAL_RELATION', 'JUDGMENT', 'REPRESENTATION', 'REVIEW', 'DECISION'}
EMPTY_TABLES = {'audiovisual_notes', 'business_relations', 'business_relation_aliases',
    'business_relation_runs', 'material_aliases', 'material_archive_files',
    'production_submissions', 'production_candidates', 'production_candidate_targets',
    'production_current_operations', 'production_response_excerpts'}
EMPTY_PREFIXES = ('material_definition', 'material_plan', 'material_candidate',
    'material_round', 'material_member', 'material_feedback', 'material_comment_scope',
    'business_candidate', 'consolidation_definition', 'consolidation_version',
    'audiovisual_cleanup', 'state_cleanup', 'relation_explanation_redaction')
CONTENT_FIELDS = {'prompt', 'production_description', 'generation_prompt', 'input_contents', 'basis_contents',
    'reference_contents', 'requirements', 'entities', 'states', 'shots',
    'material_plans', 'material_definitions', 'current_records', 'before_records',
    'after_records', 'prepared_plan', 'request_body', 'raw_response', 'response_body',
    'specification', 'generation', 'material_plan', 'camera_plan', 'staging_plan',
    'lighting_plan', 'sound_plan', 'material_content', 'input', 'download_url',
    'audio_url', 'image_url', 'video_url', 'output_url'}
RECORD_FORMATS = {'production-'+k.lower().replace('_', '-')+'-v1' for k in PRODUCTION_KINDS} | {'production-retirement-v1'}
ERASED_IDENTITIES = set()


def configure(plan):
    global ERASED_IDENTITIES
    ERASED_IDENTITIES = set(plan.get('deleted_identities', plan['deleted_objects']))


def remaining_fields(value):
    """Remove only untyped old description/state fields in audited evidence."""
    if isinstance(value, list):
        return [remaining_fields(v) for v in value]
    if isinstance(value, dict):
        if value.get('format') in ('managed-method-skill-v1', 'managed-method-resource-v1', 'managed-method-binding-v1', 'managed-method-activation-v1'):
            return value
        if {'target_object_id', 'body', 'anchor'} <= value.keys():
            return value
        old = any(value.get(k) in ERASED_IDENTITIES for k in ('object_id', 'id', 'entity_id', 'material_id') if isinstance(value.get(k), str))
        result = {}
        for k, v in value.items():
            if k in ('comments', 'comment_events', 'anchor', 'excerpt'):
                result[k] = v
            elif k == 'production_description' or k == 'dimensions' and old:
                result[k+'_deleted'] = {'sha256': hashlib.sha256(canonical(v).encode()).hexdigest()}
            else:
                result[k] = remaining_fields(v)
        return result
    if isinstance(value, str) and value.lstrip().startswith(('{', '[')):
        try: old = json.loads(value)
        except ValueError: return value
        new = remaining_fields(old)
        return canonical(new) if old != new else value
    return value


def obsolete_author_source(name):
    """Explicit old compilation sources, separate from story and teaching."""
    name = '/' + str(name).lstrip('/')
    exact = (
        'production/audiovisual/review.md', 'production/audiovisual/stage-review.md',
        'production/audiovisual/state-preparation.md', 'production/audiovisual/text-review.md',
        'production/state-preparation-review.md', 'production/full-generation/voice-scope.md',
        'production/song-stage/music-plan.md', 'production/song-stage/s041-proposed.md',
        'production/song-stage/history/approved-inputs/music-plan.md',
        'production/song-stage/history/approved-inputs/review-packet.md',
        'production/songbook-two-nights/assessment-result.md',
        'production/songbook-work-ledger-two-shot/assessment-result.md',
    )
    return any(name.endswith('/'+p) for p in exact) or (
        '/production/song-stage/lyrics/' in name and Path(name).suffix in ('.md', '.txt'))


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024*1024), b''):
            h.update(chunk)
    return h.hexdigest()


def deleted(value, oid=None, kind=None):
    return {'format': 'redacted-production-evidence-v1', 'production_content_deleted': True,
            'object_id': oid or value.get('object_id'), 'original_kind': kind,
            'original_sha256': hashlib.sha256(canonical(value).encode()).hexdigest(),
            'replay_disabled': True}


def clean(value):
    if isinstance(value, list):
        return [clean(v) for v in value]
    if not isinstance(value, dict):
        if isinstance(value, str):
            from review_desk.candidate_reset import media_bytes
            media = media_bytes(value)
            if media is not None:
                return {'media_deleted': True, 'sha256': hashlib.sha256(media).hexdigest(), 'bytes': len(media)}
        if isinstance(value, str) and value.lstrip().startswith(('{', '[')):
            try:
                parsed = json.loads(value)
            except ValueError:
                return value
            after = clean(parsed)
            return canonical(after) if after != parsed else value
        return value
    fmt = value.get('format', '')
    if not isinstance(fmt, str):
        fmt = ''
    if fmt in ('managed-method-skill-v1', 'managed-method-resource-v1',
               'managed-method-binding-v1', 'managed-method-activation-v1'):
        return value
    if (fmt.startswith('managed-method-') and value.get('work_type') in
            ('audiovisual-design', 'media-plan', 'material-assessment', 'generation-preflight',
             'result-review', 'text-layer', 'video-plan', 'image-plan', 'voice-plan', 'song-plan')):
        return deleted(value)
    if fmt == 'production-call-v1':
        return reset.accounting(value)
    if fmt in RECORD_FORMATS | {'state-cleanup-receipt-v1'}:
        return deleted(value)
    result = {}
    old_identity = any(value.get(k) in ERASED_IDENTITIES for k in ('object_id', 'id', 'entity_id', 'material_id') if isinstance(value.get(k), str))
    for k, v in value.items():
        if k in ('comments', 'comment_events', 'anchor', 'excerpt'):
            result[k] = v
        elif k in CONTENT_FIELDS or k == 'dimensions' and old_identity:
            result[k+'_deleted'] = {'sha256': hashlib.sha256(canonical(v).encode()).hexdigest()}
        else:
            result[k] = clean(v)
    return result


def embedded_records(value):
    """Erase production snapshots embedded in otherwise protected story work."""
    if isinstance(value, list):
        return [embedded_records(v) for v in value]
    if isinstance(value, dict):
        fmt = value.get('format')
        if not isinstance(fmt, str): fmt = None
        if fmt == 'production-call-v1': return reset.accounting(value)
        if fmt in RECORD_FORMATS | {'state-cleanup-receipt-v1'}: return deleted(value)
        if fmt in ('managed-method-skill-v1', 'managed-method-resource-v1'): return value
        return {k: v if k in ('comments', 'comment_events', 'anchor', 'excerpt') else embedded_records(v) for k, v in value.items()}
    if isinstance(value, str) and value.lstrip().startswith(('{', '[')):
        try: old = json.loads(value)
        except ValueError: return value
        new = embedded_records(old)
        return canonical(new) if new != old else value
    return value


def redact_embedded_database(path):
    db = sqlite3.connect(path)
    patches = []
    try:
        tables = [r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")]
        for table in tables:
            columns = [r[1] for r in db.execute('PRAGMA table_info("'+table+'")') if r[2].upper() in ('TEXT', 'JSON')]
            for column in columns:
                for rid, raw in db.execute('SELECT rowid,"'+column+'" FROM "'+table+'"'):
                    if not isinstance(raw, str) or not raw.lstrip().startswith(('{', '[')): continue
                    if len(raw) > 64*1024*1024: raise ValueError('story input cell exceeds reviewed bound')
                    try: old = json.loads(raw)
                    except ValueError: continue
                    new = embedded_records(old)
                    if new != old: patches.append((table, column, rid, canonical(new), hashlib.sha256(raw.encode()).hexdigest()))
        if not patches: return None
        db.execute('PRAGMA secure_delete=ON'); db.execute('BEGIN IMMEDIATE')
        triggers = list(db.execute("SELECT name,sql FROM sqlite_master WHERE type='trigger'"))
        for name, _ in triggers: db.execute('DROP TRIGGER "'+name.replace('"','""')+'"')
        for table, column, rid, after, before in patches:
            db.execute('UPDATE "'+table+'" SET "'+column+'"=? WHERE rowid=?', (after, rid))
        db.execute('CREATE TABLE IF NOT EXISTS production_history_redactions (table_name TEXT,column_name TEXT,row_identity INTEGER,original_sha256 TEXT,notice TEXT)')
        db.executemany('INSERT INTO production_history_redactions VALUES (?,?,?,?,?)', ((t,c,r,h,'仅剥离故事工作输入中的旧制作对象；故事内容保留，旧制作快照不可重放。') for t,c,r,_,h in patches))
        for _, sql in triggers: db.execute(sql)
        if db.execute('PRAGMA foreign_key_check').fetchone(): raise ValueError('embedded snapshot redaction broke foreign keys')
        db.commit()
        if db.execute('PRAGMA journal_mode').fetchone()[0]=='wal': db.execute('PRAGMA wal_checkpoint(TRUNCATE)')
        db.execute('VACUUM')
        return {'redacted_embedded_cells':len(patches)}
    except BaseException:
        db.rollback(); raise
    finally: db.close()


def redact_database(path):
    """Inactive Store databases only; no initialization, migration or live write."""
    from review_desk.store import Store
    source = Store.open_readonly(path)
    tables = {r[0] for r in source.db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    if 'objects' not in tables:
        source.close()
        return None
    kinds = {r[0]: r[1] for r in source.db.execute('SELECT id,kind FROM objects')}
    erased = {oid for oid, kind in kinds.items() if kind in PRODUCTION_KINDS}
    calls = {oid for oid, kind in kinds.items() if kind == 'CALL'}
    if not erased and not calls:
        source.close()
        return None
    updates = []
    size = 0
    try:
        for row in source.db.execute('SELECT id,object_id,payload FROM revisions'):
            oid = row['object_id']
            if oid in erased:
                body = deleted(json.loads(row['payload']), oid, kinds[oid])
            elif oid in calls:
                raw = row['payload']
                if '_material_fields' in json.loads(raw):
                    raw = hydrate(source, raw)
                body = reset.accounting(json.loads(raw))
            elif kinds.get(oid) in ('NOTE', 'GUIDANCE'):
                old = json.loads(row['payload']); body = clean(old)
                if body == old: continue
            else:
                continue
            payload = canonical(body)
            size += len(payload.encode())
            if size > 128*1024*1024:
                raise ValueError('sanitized historical changes exceed reviewed 128 MiB bound')
            updates.append((payload, row['id']))
    finally:
        source.close()
    db = sqlite3.connect(path)
    db.execute('PRAGMA secure_delete=ON')
    db.execute('BEGIN IMMEDIATE')
    triggers = list(db.execute("SELECT name,sql FROM sqlite_master WHERE type='trigger'"))
    try:
        for name, _ in triggers:
            db.execute('DROP TRIGGER "'+name.replace('"', '""')+'"')
        db.executemany('UPDATE revisions SET payload=? WHERE id=?', updates)
        count = len(updates)
        db.executemany('UPDATE objects SET kind=? WHERE id=?', ((reset.DELETED, oid) for oid in erased))
        for table in sorted(tables):
            if table in EMPTY_TABLES or table.startswith(EMPTY_PREFIXES):
                db.execute('DELETE FROM "'+table+'"')
        if 'production_current_records' in tables:
            db.execute('DELETE FROM production_current_records')
        if 'production_current_baselines' in tables:
            db.execute('DELETE FROM production_current_baselines')
        if 'dependencies' in tables:
            db.execute("DELETE FROM dependencies WHERE from_revision IN (SELECT r.id FROM revisions r JOIN objects o ON r.object_id=o.id WHERE o.kind IN (?,?)) OR to_revision IN (SELECT r.id FROM revisions r JOIN objects o ON r.object_id=o.id WHERE o.kind=?)", (reset.DELETED, 'CALL', reset.DELETED))
        if 'material_content' in tables:
            # Only requirements/calls and generated metadata use this store.
            # Their logical facts have just been materialized above.
            if db.execute("SELECT 1 FROM revisions WHERE json_type(payload,'$._material_fields') IS NOT NULL LIMIT 1").fetchone():
                raise ValueError('unclassified retained content graph root')
            db.execute('DELETE FROM material_content')
        for table in ('generation_publications', 'consolidation_runs'):
            if table not in tables:
                continue
            for oid, raw in list(db.execute('SELECT id,receipt FROM '+table)):
                db.execute('UPDATE '+table+' SET receipt=? WHERE id=?', (canonical(deleted(json.loads(raw), oid)), oid))
        db.execute('CREATE TABLE IF NOT EXISTS production_history_redacted (id TEXT PRIMARY KEY, notice TEXT NOT NULL)')
        db.execute('INSERT OR REPLACE INTO production_history_redacted VALUES (?,?)', ('full-production-reset', '剥离制作正文与媒体后的历史证据；禁止作为恢复包或生产输入。'))
        for _, sql in triggers:
            db.execute(sql)
        if db.execute('PRAGMA foreign_key_check').fetchone():
            raise ValueError('historical redaction broke foreign keys')
        db.commit()
        if db.execute('PRAGMA journal_mode').fetchone()[0] == 'wal':
            db.execute('PRAGMA wal_checkpoint(TRUNCATE)')
        db.execute('VACUUM')
        return {'deleted_objects': len(erased), 'preserved_calls': len(calls), 'redacted_revisions': count}
    except BaseException:
        source.close()
        db.rollback()
        raise
    finally:
        db.close()


class Reader:
    """One top-level array member at a time; no whole exported database load."""
    def __init__(self, source):
        self.source, self.buffer, self.eof = source, '', False
        self.decoder = json.JSONDecoder()

    def fill(self):
        chunk = self.source.read(65536)
        self.buffer += chunk
        self.eof = not chunk

    def space(self):
        while True:
            self.buffer = self.buffer.lstrip()
            if self.buffer or self.eof:
                return
            self.fill()

    def token(self, text):
        self.space()
        if not self.buffer.startswith(text):
            raise ValueError('invalid streamed JSON structure')
        self.buffer = self.buffer[len(text):]

    def value(self):
        self.space()
        while True:
            try:
                result, end = self.decoder.raw_decode(self.buffer)
                if end == len(self.buffer) and not self.eof:
                    self.fill()
                    continue
                if type(result) in (int, float) and end < len(self.buffer) and self.buffer[end] not in ',]} \t\r\n':
                    if self.eof:
                        raise ValueError('invalid number in streamed JSON')
                    self.fill()
                    continue
                self.buffer = self.buffer[end:]
                return result
            except json.JSONDecodeError:
                if self.eof:
                    raise ValueError('truncated streamed JSON value')
                if len(self.buffer) > 64*1024*1024:
                    raise ValueError('single JSON member exceeds reviewed 64 MiB bound')
                self.fill()


def content_index(path, destination):
    db = sqlite3.connect(destination)
    db.execute('CREATE TABLE material_content(id TEXT PRIMARY KEY,body TEXT NOT NULL)')
    for row in rows(path):
        if hashlib.sha256(row['body'].encode()).hexdigest() != row['id']:
            raise ValueError('corrupt historical content node')
        db.execute('INSERT INTO material_content VALUES (?,?)', (row['id'], row['body']))
    db.commit()
    return SimpleNamespace(db=db)


def stream_redact(source, destination):
    """Redact a large historical request/delta without loading its containers."""
    changed = 0
    with Path(source).open() as src, Path(destination).open('w') as out:
        r = Reader(src)
        def walk(path=(), discard=False):
            nonlocal changed
            r.space()
            if path and path[-1] == 'payload' and not discard:
                value = r.value()
                after = clean(value)
                changed += int(after != value)
                out.write(canonical(after))
                return
            if r.buffer.startswith('{'):
                r.token('{')
                if not discard: out.write('{')
                first = True
                r.space()
                while not r.buffer.startswith('}'):
                    key = r.value(); r.token(':')
                    if not discard:
                        if not first: out.write(',')
                        out.write(json.dumps(key)+':')
                    first = False
                    keep_comment = any(k in ('comments', 'comment_events', 'anchor', 'excerpt') for k in path)
                    remove = not keep_comment and (key in CONTENT_FIELDS or key == '_material_fields'
                        or key == 'material_content' or key in EMPTY_TABLES or key.startswith(EMPTY_PREFIXES))
                    if remove and not discard:
                        walk((*path, key), True)
                        out.write('null'); changed += 1
                    else:
                        walk((*path, key), discard)
                    r.space()
                    if r.buffer.startswith('}'): break
                    r.token(',')
                r.token('}')
                if not discard: out.write('}')
            elif r.buffer.startswith('['):
                r.token('[')
                if not discard: out.write('[')
                first = True; r.space()
                while not r.buffer.startswith(']'):
                    if not discard and not first: out.write(',')
                    first = False; walk((*path, '[]'), discard); r.space()
                    if r.buffer.startswith(']'): break
                    r.token(',')
                r.token(']')
                if not discard: out.write(']')
            else:
                value = r.value()
                if not discard:
                    if path and path[-1] == 'kind' and value in PRODUCTION_KINDS:
                        value = reset.DELETED; changed += 1
                    out.write(canonical(value))
        walk(); r.space()
        if r.buffer: raise ValueError('trailing historical JSON bytes')
        out.write('\n')
    return changed


def text_records(source, destination):
    """Bounded JSONL/tool output redaction, leaving unrelated prose unchanged."""
    if Path(source).stat().st_size <= 64*1024*1024:
        text = Path(source).read_text()
        if ('AXWebArea' in text and re.search(r'^\s*\d+ (?:heading|text) (?:ASH|AS|AE|EN|ST|M)\d+\s*[·|]', text, re.M)
                and any(s in text for s in ('叙事目的', '素材详情', '素材方案', '当前方案', '生成方案'))):
            Path(destination).write_text(canonical({
                'format': 'redacted-production-page-evidence-v1',
                'original_sha256': hashlib.sha256(text.encode()).hexdigest(),
                'production_content_deleted': True, 'replay_disabled': True,
                'notice': '旧页面制作正文及Prompt快照已剥离；原意见由正式评论及原摘录保存。'})+'\n')
            return 1
        start = min((i for token in ('{', '[') for i in [text.find(token)] if i >= 0), default=-1)
        if start >= 0:
            try:
                value, end = json.JSONDecoder().raw_decode(text[start:])
            except ValueError:
                pass
            else:
                if not text[start+end:].strip():
                    after = clean(value)
                    Path(destination).write_text(text[:start]+canonical(after)+'\n' if after != value else text)
                    return int(after != value)
    changed = 0
    with Path(source).open() as src, Path(destination).open('w') as out:
        while True:
            line = src.readline(64*1024*1024+1)
            if not line:
                break
            if len(line) > 64*1024*1024:
                raise ValueError('single text record exceeds reviewed bound')
            start = min((i for token in ('{', '[') for i in [line.find(token)] if i >= 0), default=-1)
            if start >= 0:
                try:
                    value, end = json.JSONDecoder().raw_decode(line[start:])
                except ValueError:
                    pass
                else:
                    after = clean(value)
                    if after != value:
                        line = line[:start]+canonical(after)+line[start+end:]
                        changed += 1
            out.write(line)
    return changed


def framework(source, destination, graph=None):
    """Write an explicitly non-recoverable, text-redacted old framework."""
    changed = 0
    kinds = {}
    with Path(source).open() as src, Path(destination).open('w') as out:
        r = Reader(src)
        r.token('{')
        out.write('{')
        first = True
        while True:
            key = r.value()
            r.token(':')
            if not first:
                out.write(',')
            first = False
            out.write(json.dumps(key)+':')
            r.space()
            if r.buffer.startswith('['):
                r.token('[')
                out.write('[')
                first_row = True
                r.space()
                while not r.buffer.startswith(']'):
                    value = r.value()
                    after = value
                    if key == 'objects':
                        kinds[value['id']] = value['kind']
                        if value.get('kind') in PRODUCTION_KINDS:
                            after = {**value, 'kind': reset.DELETED}
                    elif key == 'revisions':
                        raw = value['payload']
                        body = json.loads(raw)
                        if body.get('format') == 'production-call-v1' and '_material_fields' in body:
                            if graph is None:
                                raise ValueError('call accounting requires the matching content graph')
                            body = json.loads(hydrate(graph, raw))
                        if kinds.get(value['object_id']) in PRODUCTION_KINDS | {'CALL', 'NOTE', 'GUIDANCE'}:
                            after = {**value, 'payload': canonical(clean(body))}
                    elif (key in EMPTY_TABLES or key.startswith(EMPTY_PREFIXES)
                          or key in ('material_content', 'production_current_records', 'production_current_baselines')):
                        after = None
                    else:
                        after = clean(value)
                    if after != value:
                        changed += 1
                    if after is not None:
                        if not first_row:
                            out.write(',')
                        out.write(canonical(after))
                        first_row = False
                    r.space()
                    if r.buffer.startswith(']'):
                        break
                    r.token(',')
                r.token(']')
                out.write(']')
            else:
                out.write(canonical(clean(r.value())))
            r.space()
            if r.buffer.startswith('}'):
                break
            r.token(',')
        r.token('}')
        r.space()
        if r.buffer:
            raise ValueError('trailing framework bytes')
        out.write(',"production_history_redacted":true}\n')
    return changed
