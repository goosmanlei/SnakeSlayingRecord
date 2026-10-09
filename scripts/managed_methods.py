"""Instance method bootstrap and exact backend delivery; never calls models."""
import argparse
import copy
import json
import sys
import tempfile
from pathlib import Path


def _install(store, seed):
    from review_desk import methods
    saved = {}
    for source in seed.get('sources', []):
        row = methods.sync_source(store, Path(__file__).resolve().parents[1], source)
        saved[('resource', source['name'])] = row
    for source in seed['records']:
        value = copy.deepcopy(source)
        for ref in value['payload'].get('resources', []):
            name = ref.pop('name')
            row = saved.get(('resource', name)) or methods.read(store, 'method.resource.' + name)
            ref.update(methods.reference(row))
        oid = 'method.' + value['category'] + '.' + value['name']
        exists = store.db.execute('SELECT 1 FROM objects WHERE id=?', (oid,)).fetchone()
        if exists:
            row = methods.read(store, oid)
            intended = {**value['payload'], 'format': methods.FORMATS[value['category']]}
            if row['payload'] != intended:
                raise ValueError('已维护的方法与初始包不同；不覆盖：' + oid)
        else:
            row = methods.save(store, value)
        saved[(value['category'], value['name'])] = row
    for binding in seed['bindings']:
        row = saved[('skill', binding['method'])]
        name = binding['work_type']
        oid = 'method.binding.' + name
        if store.db.execute('SELECT 1 FROM objects WHERE id=?', (oid,)).fetchone():
            continue
        methods.save(store, {'category': 'binding', 'name': name, 'expected_version': 0,
                            'payload': {'work_type': name, 'rules': [{**methods.reference(row), 'when': binding.get('when', {})}]}})
    return {'installed': len(saved), 'bindings': len(seed['bindings'])}


def install(store, seed):
    # Stage against the actual maintained registry, then append one atomic
    # package. An invalid later method cannot leave an earlier binding enabled.
    from review_desk import methods
    from review_desk.store import Store
    with tempfile.TemporaryDirectory(prefix='method-bootstrap-') as directory:
        staged = Store(Path(directory) / '.runtime/review.sqlite3')
        try:
            methods.restore_registry(staged, methods.export_registry(store))
            result = _install(staged, seed)
            result['restored'] = methods.restore_registry(store, methods.export_registry(staged))
            return result
        finally:
            staged.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--system', type=Path, required=True)
    parser.add_argument('--instance', type=Path, required=True)
    sub = parser.add_subparsers(dest='action', required=True)
    init = sub.add_parser('install')
    init.add_argument('--seed', type=Path, default=Path(__file__).resolve().parents[1] / 'content/managed-methods.json')
    args = parser.parse_args()
    sys.path.insert(0, str(args.system.resolve()))
    from review_desk.store import Store
    store = Store(args.instance / '.runtime/review.sqlite3')
    try:
        print(json.dumps(install(store, json.loads(args.seed.read_text())), ensure_ascii=False))
    finally:
        store.close()


if __name__ == '__main__':
    main()
