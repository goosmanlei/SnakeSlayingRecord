#!/usr/bin/env python3
"""Compare exact JSON transmission representations on captured API responses.

This is an offline CPU/size probe, not a browser performance measurement.
Every representation must round-trip the complete response without data loss.
"""
import argparse
import gzip
import json
from pathlib import Path
import time


def graph_pack(value):
    nodes, known = [], {}

    def walk(item):
        if isinstance(item, dict):
            node = ['o', [[key, walk(child)] for key, child in item.items()]]
        elif isinstance(item, list):
            node = ['a', [walk(child) for child in item]]
        elif isinstance(item, str) and len(item) >= 64:
            node = ['s', item]
        else:
            return item
        key = json.dumps(node, ensure_ascii=False, separators=(',', ':'))
        index = known.get(key)
        if index is None:
            index = len(nodes)
            known[key] = index
            nodes.append(node)
        return {'$': index}

    root = walk(value)
    return {'format': 'review-graph-v1', 'root': root, 'nodes': nodes}


def graph_pack_fast(value):
    nodes, known, records = [], {}, {}
    def walk(item):
        identity = (item.get('id'), item.get('object_id')) if isinstance(item, dict) and 'payload' in item and isinstance(item.get('id'), str) else None
        if identity:
            for original, reference in records.get(identity, []):
                if original == item:
                    return reference
        if isinstance(item, dict):
            data = [(key, walk(child)) for key, child in item.items()]
            key = ('o', tuple(data))
            node = ['o', [[key, wire(child)] for key, child in data]]
        elif isinstance(item, list):
            data = tuple(walk(child) for child in item)
            key = ('a', data)
            node = ['a', [wire(child) for child in data]]
        elif isinstance(item, str) and len(item) >= 64:
            key = ('s', item)
            node = ['s', item]
        else:
            return (type(item).__name__, item)
        index = known.get(key)
        if index is None:
            index = len(nodes)
            known[key] = index
            nodes.append(node)
        reference = ('ref', index)
        if identity:
            records.setdefault(identity, []).append((item, reference))
        return reference
    def wire(item):
        return {'$': item[1]} if item[0] == 'ref' else item[1]
    return {'format': 'review-graph-v1', 'root': wire(walk(value)), 'nodes': nodes}


def graph_unpack(graph):
    def walk(item):
        if not isinstance(item, dict):
            return item
        kind, data = graph['nodes'][item['$']]
        if kind == 's':
            return data
        if kind == 'a':
            return [walk(child) for child in data]
        return {key: walk(child) for key, child in data}

    return walk(graph['root'])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--fast', action='store_true')
    args = parser.parse_args()
    original = gzip.decompress(args.input.read_bytes())
    value = json.loads(original)
    start = time.perf_counter()
    graph = (graph_pack_fast if args.fast else graph_pack)(value)
    packed = json.dumps(graph, ensure_ascii=False, separators=(',', ':')).encode()
    pack_ms = (time.perf_counter() - start) * 1000
    start = time.perf_counter()
    restored = graph_unpack(json.loads(packed))
    unpack_ms = (time.perf_counter() - start) * 1000
    assert value == restored, 'transmission representation changed the response'
    zipped = gzip.compress(packed, compresslevel=1, mtime=0)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(zipped)
    print(json.dumps({'input': str(args.input), 'output': str(args.output),
                      'original_bytes': len(original), 'graph_bytes': len(packed),
                      'graph_gzip1_bytes': len(zipped), 'nodes': len(graph['nodes']),
                      'pack_ms': pack_ms, 'unpack_ms': unpack_ms,
                      'equal': True}))


if __name__ == '__main__':
    main()
