#!/usr/bin/env python3
"""Migrate or validate derived file history against an exact system checkout."""
import argparse
import json
from pathlib import Path
import sys


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--system',type=Path,required=True)
    parser.add_argument('--database',type=Path,required=True)
    parser.add_argument('action',choices=('migrate','check'))
    args=parser.parse_args()
    sys.path.insert(0,str(args.system.resolve()))
    from review_desk.store import Store
    from review_desk import method_files
    store=Store.open_existing(args.database.resolve(strict=True))
    try:
        if args.action=='migrate': result=method_files.migrate(store)
        else:
            method_files.require_history(store)
            method_files.validate(store)
            result={'validated':True}
        print(json.dumps(result,ensure_ascii=False))
    finally:store.close()


if __name__=='__main__':main()
