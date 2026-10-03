#!/usr/bin/env python3
"""Preserve an image_gen original and the metadata the tool actually returned."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess

try:
    from .generation_workspace import generation_root, contained
except ImportError:
    from generation_workspace import generation_root, contained

ROOT = Path(__file__).resolve().parents[1]


def main():
    global ROOT
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--id', required=True)
    parser.add_argument('--response-metadata', required=True, type=Path)
    parser.add_argument('--workspace', type=Path, default=ROOT)
    args = parser.parse_args()
    ROOT = generation_root(args.workspace)
    if not re.fullmatch(r'[a-z0-9-]+', args.id):
        parser.error('invalid call label')
    request_path = ROOT / 'production/requests' / (args.id + '.json')
    request = json.loads(request_path.read_text())
    assert request['id'] == args.id and request['tool'] == 'image_gen.imagegen'
    metadata = json.loads(args.response_metadata.read_text())
    assert metadata['response_keys'] == ['image_url', 'output_hint']
    match = re.search(r' as (/[^\n]+\.png) by default\.', metadata['output_hint'])
    if not match:
        parser.error('tool did not expose an original file; recover before any retry')
    source = Path(match.group(1))
    managed = Path.home() / '.codex/generated_images'
    assert source.is_file() and not source.is_symlink() and managed.resolve() in source.resolve().parents
    sha = hashlib.sha256(source.read_bytes()).hexdigest()
    destination = contained(ROOT, ROOT / 'export/assets' / (sha + '.png'))
    destination.parent.mkdir(parents=True, exist_ok=True)
    assert not destination.is_symlink() and not destination.parent.is_symlink()
    receipt_path = contained(ROOT, ROOT / 'production/receipts' / (args.id + '-builtin-complete.json'))
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    assert not receipt_path.exists(), 'do not overwrite a real tool receipt'
    if destination.exists():
        assert hashlib.sha256(destination.read_bytes()).hexdigest() == sha
    else:
        shutil.copyfile(source, destination)
    probe = json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-show_streams', '-of', 'json', str(destination)]))
    stream = probe['streams'][0]
    assert stream['codec_name'] == 'png' and stream['width'] > 0 and stream['height'] > 0
    receipt = {'id': args.id, 'status': 'COMPLETED', 'tool': 'image_gen.imagegen',
        'completion_evidence': 'tool returned an image and the exact saved original passed decoding and SHA verification',
        'tool_surface_model': 'GPT Image', 'underlying_model_id': None, 'provider_call_id': None,
        'response_artifact_id': source.stem, 'source_file': str(source),
        'file': destination.relative_to(ROOT).as_posix(), 'sha256': sha,
        'width': stream['width'], 'height': stream['height'], 'codec': stream['codec_name'],
        'request_file_sha256': hashlib.sha256(request_path.read_bytes()).hexdigest(),
        'billing_usage': None, 'native_size_note': '工具直接返回的原生像素；未暴露尺寸设置或底层型号，不声称4K或已核实隐藏上限。',
        'response_keys': metadata['response_keys'], 'output_hint': metadata['output_hint']}
    receipt_path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({k: receipt[k] for k in ('id', 'file', 'sha256', 'width', 'height')}))


if __name__ == '__main__':
    main()
