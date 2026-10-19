#!/usr/bin/env python3
"""Resumable, bounded upload and full-byte verification of an exact inventory."""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
from pathlib import Path
import sys
import time
import threading


def migrate(root, inventory, workers):
    from review_desk import resources as r, media_previews as previews
    source = json.loads(inventory.read_text())
    if source['missing']:
        raise ValueError('inventory has unresolved references')
    rows = [item for item in source['files'] if item['storage'] == 'oss']
    if any(item['archive'] for item in rows):
        raise ValueError('hydrate and verify logical archive originals before upload')
    if sum(item['logical']['bytes'] for item in rows) > 16 * 1024**3:
        raise ValueError('inventory exceeds this migration transfer budget')
    config = r.settings(root)
    available = dict(r._catalog(root, config))
    connections = threading.local()
    started = time.time()
    def transfer(item):
        import alibabacloud_oss_v2 as oss
        if not hasattr(connections, 'value'):
            connections.value = r.client(config, administrative=True)
        def mime_matches(value):
            head=connections.value.head_object(oss.HeadObjectRequest(
                bucket=config['bucket'],key=value['key'],version_id=value['version_id']))
            if head.content_length!=value['bytes']:raise ValueError('cloud resource length changed')
            return (head.content_type or '').split(';',1)[0].lower()==value['mime'].lower()
        path = root / item['path']
        saved = available.get(item['path']) or r._catalog(root, config).get(item['path'])
        if saved:
            r.validate_descriptor(config, saved)
            if any(saved[k] != item['logical'][k] for k in ('sha256','bytes')):
                raise ValueError('resumed resource identity changed: ' + item['path'])
            if saved['mime'] != item['mime']:
                raise ValueError('resumed resource MIME differs from inventory: ' + item['path'])
            spec = dict(saved)
            if not mime_matches(spec):
                raise ValueError('original MIME requires an explicit immutable catalog repair: '+item['path'])
        else:
            spec = r.upload(root, path, expected_sha=item['logical']['sha256'], administrative=True, mime=item['mime'])
            spec['mime'] = item['mime']
            spec['role'] = item['category']
            spec['disposition'] = item['disposition']
            spec = r.register(root, item['path'], spec)
        variants = (('small','large') if spec['mime'].startswith('image/') else
                    ('poster',) if spec['mime'].startswith('video/') else
                    ('waveform',) if spec['mime'].startswith('audio/') else ())
        spec.setdefault('variants', {})
        for variant in variants:
            if variant in spec['variants']:
                r.validate_descriptor(config, spec['variants'][variant])
                if mime_matches(spec['variants'][variant]):continue
            file, preview = previews.prepare(root, path, spec['sha256'], variant, spec['mime'])
            if preview['sha256'] == spec['sha256']:
                derivative = {k:v for k,v in spec.items() if k != 'variants'}
            else:
                derivative = r.upload(root, file, category='derivatives', expected_sha=preview['sha256'], administrative=True,mime=preview['mime'])
            derivative.update({k:v for k,v in preview.items() if k not in ('sha256','bytes')})
            spec['variants'][variant] = derivative
            r.register(root, item['path'], spec)
        return item['path'], spec['bytes']
    completed = 0
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(transfer, row) for row in rows]
        try:
            for future in as_completed(futures):
                name, size = future.result()
                completed += 1
                if completed % 10 == 0 or completed == len(rows):
                    print(json.dumps({'verified_paths': completed, 'total': len(rows), 'elapsed_seconds': round(time.time()-started), 'last': name}), flush=True)
        except BaseException:
            for future in futures: future.cancel()
            raise
    catalog = r.freeze_catalog(root, root/'config/resource-catalog.json')
    unique = {s['key']+'@'+s['version_id']:s['bytes'] for x in catalog['entries'].values() for s in [x,*x.get('variants',{}).values()]}
    receipt = {'format': 'oss-migration-complete-v1', 'inventory_sha256': r.hash_file(inventory),
        'paths': len(rows), 'cloud_versions': len(unique), 'verified_bytes': sum(unique.values()),
        'catalog_sha256': r.hash_file(root/'config/resource-catalog.json'), 'elapsed_seconds': round(time.time()-started)}
    r.atomic_json(root/'.runtime/oss-migration/upload-receipt.json', receipt)
    print(json.dumps(receipt), flush=True)


if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--system', type=Path, required=True)
    p.add_argument('--root', type=Path, default=Path(__file__).resolve().parent.parent)
    p.add_argument('--inventory', type=Path, required=True)
    p.add_argument('--workers', type=int, choices=(1,2), default=2)
    args=p.parse_args();sys.path.insert(0,str(args.system.resolve()))
    try:
        migrate(args.root.resolve(), args.inventory.resolve(), args.workers)
    except Exception as error:
        # SDK errors may embed signed endpoints. Emit only our safe domain errors.
        print(str(error) if type(error) in (ValueError,FileNotFoundError) else 'migration failed: '+type(error).__name__,file=sys.stderr)
        sys.exit(1)
