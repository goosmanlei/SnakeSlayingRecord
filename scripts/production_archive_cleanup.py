#!/usr/bin/env python3
"""Rewrite exact owned archives, preserving protected inputs and redacted facts."""
import argparse
import collections
import json
from pathlib import Path
import shutil
import sys
import tarfile
import tempfile

from generated_candidates_inventory import sha
from production_local_cleanup import protected, safe, story_author


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', type=Path, required=True)
    p.add_argument('--system', type=Path, required=True)
    p.add_argument('--inventory', type=Path, required=True)
    p.add_argument('--reset-plan', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--resume', action='store_true')
    p.add_argument('--refresh-text', action='store_true')
    p.add_argument('--remove-author-sources', action='store_true')
    p.add_argument('--refresh-databases', action='store_true')
    a = p.parse_args()
    root = a.root.resolve(strict=True)
    sys.path.insert(0, str(a.system.resolve(strict=True)))
    from production_history_cleanup import clean, framework, content_index, redact_database, stream_redact, text_records, embedded_records, redact_embedded_database, obsolete_author_source
    output = a.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    if a.refresh_text or a.remove_author_sources or a.refresh_databases:
        previous = [json.loads(line) for line in (output/'files.jsonl').open()]
        def author_source(name):
            return (any(name.endswith('/production/audiovisual/'+n) for n in ('appearances.txt','frame-subjects.txt','state-ranges.txt','state-transitions.txt'))
                    or '/production/extraction/episodes/' in '/'+name and Path(name).suffix=='.json')
        affected = set()
        if a.remove_author_sources:
            for line in (a.inventory/'archive-members.jsonl').open():
                item = json.loads(line)
                if author_source(item['member']) and not protected(item['member']): affected.add(item['archive'])
        updated = []
        for item in previous:
            if a.remove_author_sources and item['path'] not in affected:
                updated.append(item); continue
            src = output/item['staged']
            assert sha(src) == item['after']
            staged = output/'refresh-archive.tmp'
            changed = 0
            mode = 'w:gz' if item['path'].endswith(('.gz', '.tgz')) else 'w'
            with tempfile.TemporaryDirectory(prefix='archive-text-', dir=output) as temporary:
                temp = Path(temporary)
                databases = {}
                if a.refresh_databases:
                    original = safe(root, item['path'])
                    if sha(original) != item['before']:
                        raise ValueError('original archive changed: '+item['path'])
                    with tarfile.open(original, 'r|*') as archive:
                        for member in archive:
                            embedded = story_author(member.name)
                            if not member.isfile() or Path(member.name).suffix not in ('.db', '.sqlite3') or protected(member.name) and not embedded:
                                continue
                            db = temp/('database-'+str(len(databases))+'.sqlite3')
                            with archive.extractfile(member) as data, db.open('wb') as target:
                                shutil.copyfileobj(data, target, 1024*1024)
                            if embedded: redact_embedded_database(db)
                            else: redact_database(db)
                            databases[member.name] = db
                with tarfile.open(src, 'r|*') as source, tarfile.open(staged, mode) as target:
                    for member in source:
                        if a.refresh_databases:
                            replacement = databases.get(member.name)
                            if replacement:
                                member.size = replacement.stat().st_size
                                with replacement.open('rb') as data: target.addfile(member, data)
                                changed += 1
                            elif member.isfile():
                                with source.extractfile(member) as data: target.addfile(member, data)
                            else: target.addfile(member)
                            continue
                        if member.isfile() and obsolete_author_source(member.name) and not protected(member.name):
                            changed += 1; continue
                        if a.remove_author_sources:
                            if member.isfile() and author_source(member.name) and not protected(member.name):
                                changed += 1; continue
                            if member.isfile():
                                with source.extractfile(member) as data: target.addfile(member,data)
                            else: target.addfile(member)
                            continue
                        embedded = story_author(member.name) and Path(member.name).suffix in ('.json', '.sqlite3', '.db')
                        framework_file = Path(member.name).name == 'objects.json' and Path(member.name).parent.name == 'export'
                        if (not member.isfile() or protected(member.name) and not embedded
                                or Path(member.name).suffix not in ('.jsonl', '.log', '.stdout', '.txt', '.sqlite3', '.db') and not embedded and not framework_file):
                            if member.isfile():
                                with source.extractfile(member) as data: target.addfile(member, data)
                            else: target.addfile(member)
                            continue
                        raw, cleaned = temp/'raw', temp/'cleaned'
                        with source.extractfile(member) as data, raw.open('wb') as out:
                            shutil.copyfileobj(data, out, 1024*1024)
                        if framework_file:
                            altered = bool(framework(raw, cleaned)); chosen = cleaned
                        elif not embedded and Path(member.name).suffix in ('.sqlite3', '.db'):
                            altered = bool(redact_database(raw)); chosen = raw
                        elif embedded and Path(member.name).suffix in ('.sqlite3', '.db'):
                            altered = bool(redact_embedded_database(raw)); chosen = raw
                        elif embedded:
                            if raw.stat().st_size > 64*1024*1024:
                                raise ValueError('protected story JSON needs bounded inspection: '+member.name)
                            try:
                                old = json.loads(raw.read_text()); new = embedded_records(old)
                            except (ValueError, UnicodeDecodeError): old = new = None
                            altered = old != new
                            if altered: cleaned.write_text(json.dumps(new,ensure_ascii=False,indent=2)+'\n')
                            chosen = cleaned if altered else raw
                        else:
                            try: altered = text_records(raw, cleaned)
                            except UnicodeDecodeError: altered = 0
                            chosen = cleaned if altered else raw
                        changed += int(bool(altered)); member.size = chosen.stat().st_size
                        with chosen.open('rb') as data: target.addfile(member, data)
                        raw.unlink()
                        if cleaned.exists(): cleaned.unlink()
            if changed:
                after = sha(staged); destination = output/(after+'.redacted'); staged.rename(destination)
                item = {**item, 'after': after, 'staged': destination.name,
                        'details': {**item['details'], ('refreshed_original_databases' if a.refresh_databases else 'author_sources_removed' if a.remove_author_sources else 'additional_redacted_text'): changed}}
            else: staged.unlink()
            updated.append(item)
            print(json.dumps({'text_refreshed': item['path'], 'changed_members': changed}), flush=True)
        temporary = output/'files.refreshed.jsonl'
        with temporary.open('w') as out:
            for item in updated: out.write(json.dumps(item, ensure_ascii=False)+'\n')
        temporary.replace(output/'files.jsonl')
        return
    if (output/'files.jsonl').exists() and not a.resume:
        raise ValueError('archive plan already exists; preserve prior preparation')
    known = set(json.loads((a.inventory/'media-catalogue.json').read_text()))
    known.update(json.loads((a.inventory.parent/'engineering-derived-hashes.json').read_text()))
    known.add('b60925b5e5d07d52eaca435c688838463dc7026c3475ff3475cffc9b5eea6df9')
    plan = json.loads(a.reset_plan.read_text())
    known.update(v['physical_sha256'] for v in plan['erased_files'].values() if v.get('physical_sha256'))
    known.update(v['sha256'] for v in plan['erased_files'].values())
    archives = [json.loads(line) for line in (a.inventory/'files.jsonl').open()
                if json.loads(line)['disposition'] == 'archive-review']
    counts = collections.Counter()
    done = set()
    if a.resume and (output/'files.jsonl').exists():
        for line in (output/'files.jsonl').open():
            item = json.loads(line); done.add(item['path']); counts.update(item['details']); counts['archives'] += 1
    with (output/'files.jsonl').open('a' if a.resume else 'w') as manifest:
        for entry in archives:
            if entry['path'] in done: continue
            archive = safe(root, entry['path'])
            before = sha(archive)
            print('preparing', entry['path'], flush=True)
            removed = collections.Counter()
            with tempfile.TemporaryDirectory(prefix='archive-redact-', dir=output) as temporary:
                temp = Path(temporary)
                graphs = {}
                # Matching content graphs are disk-backed and temporary; no
                # original production data is kept after preparing this archive.
                with tarfile.open(archive, 'r|*') as source:
                    for member in source:
                        if member.isfile() and Path(member.name).name == 'material-content.json':
                            target = temp/(str(len(graphs))+'.graph.json')
                            with source.extractfile(member) as data, target.open('wb') as out:
                                shutil.copyfileobj(data, out, 1024*1024)
                            graphs[str(Path(member.name).parent)] = target
                staged = output/'current-archive.tmp'
                mode = 'w:gz' if archive.name.endswith(('.gz', '.tgz')) else 'w'
                with tarfile.open(archive, 'r|*') as source, tarfile.open(staged, mode) as target:
                    for member in source:
                        if not member.isfile():
                            target.addfile(member)
                            continue
                        name = member.name
                        if protected(name):
                            with source.extractfile(member) as data:
                                target.addfile(member, data)
                            continue
                        raw = temp/'member.raw'
                        with source.extractfile(member) as data, raw.open('wb') as out:
                            shutil.copyfileobj(data, out, 1024*1024)
                        suffix = Path(name).suffix.lower()
                        if sha(raw) in known or Path(name).name.startswith('read-cache.sqlite3'):
                            removed['candidate_or_cache_files'] += 1
                            removed['deleted_bytes'] += member.size
                            raw.unlink()
                            continue
                        if ('/production/audiovisual/text-handoffs/' in '/'+name or
                            '/production/audiovisual/' in '/'+name and Path(name).stem[1:].isdigit() and Path(name).stem.startswith('e')):
                            removed['old_author_sources'] += 1
                            removed['deleted_bytes'] += member.size
                            raw.unlink()
                            continue
                        cleaned = temp/'member.cleaned'
                        changed = False
                        if suffix in ('.sqlite3', '.db'):
                            info = redact_database(raw)
                            changed = bool(info)
                            if changed:
                                removed['redacted_databases'] += 1
                        elif suffix == '.json':
                            if Path(name).name == 'objects.json' and Path(name).parent.name == 'export':
                                graph_path = graphs.get(str(Path(name).parent))
                                graph = None
                                index = temp/'content.sqlite3'
                                try:
                                    if graph_path:
                                        graph = content_index(graph_path, index)
                                    framework(raw, cleaned, graph)
                                finally:
                                    if graph:
                                        graph.db.close(); index.unlink()
                                changed = True
                            elif Path(name).name == 'material-content.json' and Path(name).parent.name == 'export':
                                cleaned.write_text('{"format":"material-content-v1","material_content":[],"production_history_redacted":true}\n')
                                changed = True
                            elif member.size > 64*1024*1024:
                                changed = bool(stream_redact(raw, cleaned))
                            else:
                                try:
                                    old = json.loads(raw.read_text()); new = clean(old)
                                except (ValueError, UnicodeDecodeError):
                                    new = old = None
                                if new != old:
                                    cleaned.write_text(json.dumps(new, ensure_ascii=False, indent=2)+'\n')
                                    changed = True
                            if changed:
                                removed['redacted_json'] += 1
                        elif suffix in ('.jsonl', '.log', '.stdout', '.txt'):
                            try:
                                changed = bool(text_records(raw, cleaned))
                            except UnicodeDecodeError:
                                changed = False
                            if changed:
                                removed['redacted_text'] += 1
                        chosen = cleaned if changed and cleaned.exists() else raw
                        member.size = chosen.stat().st_size
                        with chosen.open('rb') as data:
                            target.addfile(member, data)
                        for path in (raw, cleaned):
                            if path.exists(): path.unlink()
                after = sha(staged)
                target = output/(after+'.redacted')
                staged.rename(target)
            if sha(archive) != before:
                raise ValueError('archive changed during preparation: '+entry['path'])
            item = {'path': entry['path'], 'action': 'redact', 'before': before, 'after': after,
                    'bytes': archive.stat().st_size, 'staged': target.name,
                    'mode': archive.stat().st_mode & 0o777, 'details': dict(removed)}
            manifest.write(json.dumps(item, ensure_ascii=False)+'\n'); manifest.flush()
            counts.update(removed); counts['archives'] += 1
            print(json.dumps({'archive': entry['path'], **removed}), flush=True)
    (output/'summary.json').write_text(json.dumps(counts, indent=2)+'\n')
    print(json.dumps(counts), flush=True)


if __name__ == '__main__':
    main()
