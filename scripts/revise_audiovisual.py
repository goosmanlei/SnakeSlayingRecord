#!/usr/bin/env python3
"""Revise authored shot readings in isolation; exact media plans are preserved.

Use media_method.py for an individual product plan. The retired bulk compiler
must not recreate common conditions or silently rewrite every media reference.
"""
import sys
from pathlib import Path
from audiovisual_reading import main

if __name__ == '__main__':
    if '--source' not in sys.argv:
        for path in sorted((Path(__file__).resolve().parents[1] / 'production/audiovisual/readings').glob('e*.json')):
            sys.argv.extend(['--source', str(path)])
    main()
