#!/usr/bin/env python3
"""Loopback Redis versus a local SQLite blob cache; not page latency.

Start an isolated official Redis instance without persistence, then provide the
two graph.json.gz probe outputs and Redis source archive in --root. This script
writes only that instance's two benchmark keys and a disposable SQLite cache.
"""
import argparse
import hashlib
import json
from pathlib import Path
import platform
import socket
import sqlite3
import statistics
import time


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1]/'.runtime/system-performance/architecture')
    parser.add_argument('--port', type=int, default=62408)
    args = parser.parse_args()
    root = args.root
    sock = socket.create_connection(('127.0.0.1', args.port), 2)
    stream = sock.makefile('rb')

    def command(*args):
        args = [value.encode() if isinstance(value, str) else value for value in args]
        sock.sendall(b'*'+str(len(args)).encode()+b'\r\n'+b''.join(
            b'$'+str(len(value)).encode()+b'\r\n'+value+b'\r\n' for value in args))
        line = stream.readline()
        if line[:1] == b'$':
            data = stream.read(int(line[1:-2]))
            assert stream.read(2) == b'\r\n'
            return data
        if line[:1] == b'-':
            raise RuntimeError(line)
        return line[1:-2]

    report = {'kind': 'serialized-response-cache-microbenchmark', 'samples_per_backend': 30,
              'platform': platform.platform(),
              'redis_version': command('INFO', 'server').decode().split('redis_version:')[1].split('\r')[0],
              'redis_artifact_sha256': hashlib.sha256((root/'redis-7.2.16.tar.gz').read_bytes()).hexdigest(),
              'caveat': 'Persistent loopback connection and OS warm files; excludes projection, compression, browser and invalidation cost.',
              'results': {}}
    with sqlite3.connect(root/'cache-comparison.sqlite3') as database:
        database.execute('CREATE TABLE IF NOT EXISTS values_cache (key TEXT PRIMARY KEY, value BLOB NOT NULL)')
        for label in ('card-large', 'scene'):
            blob = (root/(label+'.graph.json.gz')).read_bytes()
            assert command('SET', label, blob) == b'OK'
            database.execute('INSERT OR REPLACE INTO values_cache VALUES (?,?)', (label, blob))
            database.commit()
            rows = {}
            for backend in ('sqlite', 'redis'):
                samples = []
                for _ in range(30):
                    start = time.perf_counter_ns()
                    value = (database.execute('SELECT value FROM values_cache WHERE key=?', (label,)).fetchone()[0]
                             if backend == 'sqlite' else command('GET', label))
                    samples.append((time.perf_counter_ns()-start)/1e6)
                    assert value == blob
                rows[backend] = {'samples_ms': samples, 'median_ms': statistics.median(samples)}
            report['results'][label] = {'bytes': len(blob), **rows}
    report['redis_memory_info'] = command('INFO', 'memory').decode()
    stream.close()
    sock.close()
    (root/'middleware-comparison.json').write_text(json.dumps(report, ensure_ascii=False, indent=2))
    print(json.dumps({label: {backend: value[backend]['median_ms'] for backend in ('sqlite', 'redis')}
                      for label, value in report['results'].items()}))


if __name__ == '__main__':
    main()
