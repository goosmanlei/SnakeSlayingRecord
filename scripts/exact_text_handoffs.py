"""Bind and package authored text decisions; never discover or invent wording."""
from copy import deepcopy
import hashlib
from io import BytesIO
import json
from pathlib import Path
import re
import zipfile

from audiovisual_design import ROOT, reference, future, union_sources

DIRECTORY = ROOT / 'production/audiovisual/text-handoffs'
CATALOG = ROOT / 'production/audiovisual/exact-text.json'


def load():
    data = json.loads(CATALOG.read_text())
    screenplay = ROOT / 'imports/screenplay-04.json'
    if data['screenplay_sha256'] != hashlib.sha256(screenplay.read_bytes()).hexdigest():
        raise ValueError('text handoffs require review against the changed screenplay')
    blocks = {f'{s["id"]}:{i}': next(b['text'] for b in e['blocks'] if b['id'] == bid)
              for e in json.loads(screenplay.read_text())['episodes'] for s in e['scenes']
              for i, bid in enumerate(s['block_ids'], 1)}
    seen = set()
    for item in data['handoffs']:
        if not re.fullmatch(r'[a-z0-9-]+', item['id']) or item['id'] in seen:
            raise ValueError('duplicate or unsafe handoff identity')
        seen.add(item['id'])
        folder = DIRECTORY / item['id']
        if folder.is_symlink() or not (folder / 'README.md').is_file():
            raise ValueError('handoff needs a real readable document: ' + item['id'])
        for exact in item['texts']:
            if exact['words'] not in blocks[exact['source']]:
                raise ValueError('authored words differ from exact source: ' + str(exact))
        for path in folder.iterdir():
            if path.is_symlink() or not path.is_file():
                raise ValueError('handoff files must be regular local files')
    return data


def records(data, av, entities, states):
    shots = {r['object_id']: r for r in av if r['kind'] == 'AV_SHOT'}
    result = []
    for item in data['handoffs']:
        targets = [shots[oid] for oid in item['shots']]
        # The exact screenplay references are inherited from the actual shots;
        # the document names the precise paragraph for each authored fragment.
        sources = union_sources(s for r in targets for s in r['payload']['sources'])
        oid = 'material-text-' + item['id']
        scope = future(targets[0]['object_id'])
        body = (DIRECTORY / item['id'] / 'README.md').read_text().strip()
        payload = {'format': 'production-requirement-v1', 'title': item['title'],
            'blocks': [{'id': 'handoff-' + str(i), 'text': re.sub(r'^#+ ', '', part)}
                       for i, part in enumerate(body.split('\n\n'), 1)], 'scope': scope,
            'slot': 'text-' + item['id'], 'media_type': 'project', 'required': True,
            'usage': 'editorial', 'purpose': item['use'], 'sources': sources,
            'entities': [reference(entities[e]) for e in item.get('entities', [])],
            'states': [reference(states[s]) for s in item.get('states', [])],
            'specification': {'delivery': 'ZIP 内含 UTF-8 原词、可编辑 SVG 文字和制作交接；静态排版不代表真实运动通过'}}
        result.append({'object_id': oid, 'kind': 'REQUIREMENT', 'payload': payload})
        for target in targets[1:]:
            result.append({'object_id': 'text-use-' + item['id'] + '-' + target['object_id'],
                'kind': 'RELATION', 'payload': {'format': 'production-relation-v1',
                'title': item['title'] + '在本镜的交接', 'blocks': [{'id': 'use', 'text': item['use']}],
                'relation_type': 'applicability', 'subject': future(oid),
                'scope': future(target['object_id']), 'basis': 'production_choice',
                'reason': item['use'], 'sources': target['payload']['sources']}})
    return result


def package(item):
    """Deterministic archive of already authored files, not a layout generator."""
    output = BytesIO()
    with zipfile.ZipFile(output, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted((DIRECTORY / item['id']).iterdir()):
            info = zipfile.ZipInfo(path.name, (2026, 10, 9, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, path.read_bytes())
    return output.getvalue()


def bind_current(records_to_bind, store, production):
    """For isolated handoff prototypes before the full score is recompiled."""
    rows = deepcopy(records_to_bind)
    own = {r['object_id'] for r in rows}
    for row in rows:
        for _, ref in production.references(row['payload']):
            if ref['revision_id'].startswith('@') and ref['object_id'] not in own:
                ref['revision_id'] = production.record(store, ref['object_id'])['id']
    return rows
