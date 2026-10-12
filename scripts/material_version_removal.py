#!/usr/bin/env python3
"""Remove retired material-version indexes without retaining their physical data."""
import argparse
import json
from pathlib import Path
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--system', type=Path, required=True)
    parser.add_argument('--database', type=Path, required=True)
    parser.add_argument('action', choices=('apply', 'check'))
    args = parser.parse_args()
    sys.path.insert(0, str(args.system.resolve(strict=True)))
    from review_desk.store import Store
    from review_desk.material_version_retirement import apply, validate_absent
    store = Store.open_existing(args.database.resolve(strict=True))
    try:
        if args.action == 'apply':
            result = apply(store)
        else:
            validate_absent(store)
            result = {'validated': True}
        print(json.dumps(result, ensure_ascii=False))
    finally:
        store.close()


if __name__ == '__main__':
    main()
