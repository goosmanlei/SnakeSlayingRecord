#!/usr/bin/env python3
"""Seed Audio 1.0 calls with immutable input receipts and quota reservations.

Adapted only the HTTP payload/response contract from Jiutouan's
scripts/generate_seed_audio.py, git blob b1b02ecc08ac5074a3b61f8be5b5c4f58b478912.
Rechecked against official audio-generation-http documentation 2026-10-01.
No legacy story, task store, deployment, approvals or credentials are copied.
"""
import argparse
import base64
import datetime
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import tempfile
import urllib.error
import urllib.request
import uuid

try:
    from .generation_workspace import generation_root, contained, primary_root, git
except ImportError:
    from generation_workspace import generation_root, contained, primary_root, git

try:
    from .material_model_io import read_json as material_read_json, read_bytes as material_read_bytes, sqlite_compatibility
except ImportError:
    from material_model_io import read_json as material_read_json, read_bytes as material_read_bytes, sqlite_compatibility

ROOT = Path(__file__).resolve().parents[1]
API_URL = "https://openspeech.bytedance.com/api/v3/tts/create"


def json_write(path, value):
    path = contained(generation_root(ROOT), path)
    contained(ROOT, path.with_suffix(path.suffix + ".tmp"))
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")
    temp.replace(path)


def payload_for(spec):
    prompt = spec.get("text_prompt", "")
    if not isinstance(prompt, str) or not 1 <= len(prompt) <= 3000:
        raise ValueError("text_prompt must contain 1–3000 characters")
    payload = {"model": "seed-audio-1.0", "text_prompt": prompt,
               "audio_config": {"format": "wav", "sample_rate": 48000, "pitch_rate": 0,
                                "speech_rate": 0, "loudness_rate": 0, "enable_subtitle": True},
               "watermark": {}}
    refs, audit = [], []
    for index, ref in enumerate(spec.get("references", []), 1):
        if index > 3 or "@音频" + str(index) not in prompt:
            raise ValueError("up to three references must be cited in upload order")
        relative = Path(ref['file'])
        if relative.is_absolute() or len(relative.parts) != 3 or relative.parts[:2] != ('export', 'assets'):
            raise ValueError('references must be registered project originals under export/assets')
        path = ROOT / relative
        if (path.is_symlink() or path.parent.is_symlink() or path.parent.parent.is_symlink()
                or path.resolve().parent != (ROOT / 'export/assets').resolve()):
            raise ValueError('reference cannot escape managed originals')
        if not path.is_file() or path.stat().st_size > 10 * 1024 * 1024:
            raise ValueError("missing or oversized reference")
        data = path.read_bytes()
        sha = hashlib.sha256(data).hexdigest()
        if sha != ref.get("sha256"):
            raise ValueError("reference checksum differs from selected version")
        probe = json.loads(subprocess.check_output(["ffprobe", "-v", "error", "-show_format", "-show_streams", "-of", "json", str(path)]))
        duration = float(probe["format"]["duration"])
        if not 0 < duration <= 30 or not any(s["codec_type"] == "audio" for s in probe["streams"]):
            raise ValueError("reference audio must be no longer than 30 seconds")
        refs.append({"audio_data": base64.b64encode(data).decode()})
        audit.append({**ref, "duration_seconds": duration, "reference_number": index})
    if refs:
        payload["references"] = refs
    return payload, audit


def remaining_allowance(quota, receipts):
    if quota.get('model') != 'seed-audio-1.0' or quota.get('service_status') != '已开通':
        raise ValueError('an activated seed-audio-1.0 quota observation is required')
    remaining = quota['remaining_seconds']
    if type(remaining) not in (int, float) or not math.isfinite(remaining) or remaining < 0:
        raise ValueError('invalid observed remaining allowance')
    charges = {}
    for index, old in enumerate(receipts):
        if old.get('quota_id') != quota['id']:
            continue
        status = old.get('status')
        duration = old.get('original_duration', 120) if status == 'completed' else 0 if status == 'rejected' else 120
        if type(duration) not in (int, float) or not math.isfinite(duration) or duration < 0 or status == 'completed' and duration == 0:
            raise ValueError('invalid billing duration; allowance cannot be safely calculated')
        # Git copies of one receipt represent one call. If one copy is still
        # pending, retain the larger reservation until that copy is reconciled.
        identity = old.get('request_id') or ('legacy', index)
        charges[identity] = max(charges.get(identity, 0), duration)
    return remaining - sum(charges.values())


def quota_receipts(workspace):
    receipts = []
    for entry in git(workspace, 'worktree', 'list', '--porcelain', '-z').split(b'\0'):
        if not entry.startswith(b'worktree '):
            continue
        root = Path(os.fsdecode(entry[9:]))
        if not root.is_dir():
            continue
        folder = contained(root, 'production/receipts')
        for path in folder.glob('seed-*.json'):
            receipts.append(material_read_json(contained(root,path)))
    return receipts


def save_original(audio):
    sha = hashlib.sha256(audio).hexdigest()
    folder = contained(generation_root(ROOT), 'export/assets')
    if folder.is_symlink() or folder.parent.is_symlink():
        raise ValueError('managed originals directory cannot be a symlink')
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / (sha + '.wav')
    if target.is_symlink():
        raise ValueError('original cannot be a symlink')
    fd, temporary = tempfile.mkstemp(prefix='.seed-', suffix='.wav', dir=folder)
    temp = Path(temporary)
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(audio); stream.flush(); os.fsync(stream.fileno())
        try:
            os.link(temp, target)
        except FileExistsError:
            if hashlib.sha256(target.read_bytes()).hexdigest() != sha:
                raise ValueError('existing original checksum differs; refusing overwrite')
    finally:
        temp.unlink(missing_ok=True)
    return target, sha


def main():
    global ROOT
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("spec", type=Path)
    parser.add_argument("--submit", action="store_true")
    parser.add_argument("--quota", type=Path)
    parser.add_argument('--workspace', type=Path, default=ROOT)
    args = parser.parse_args()
    ROOT = generation_root(args.workspace) if args.submit else args.workspace.resolve()
    args.quota = args.quota or ROOT / "production/receipts/seed-quota-20261001.json"
    spec = material_read_json(args.spec)
    payload, refs = payload_for(spec)
    display = {k:v for k,v in payload.items() if k != "references"}
    display["references"] = refs
    if not args.submit:
        print(json.dumps(display, ensure_ascii=False, indent=2))
        return
    key = os.environ.get("VOLCENGINE_SPEECH_API_KEY")
    if not key:
        parser.error("VOLCENGINE_SPEECH_API_KEY is not configured")
    label = spec.get("id", "")
    if not label or any(c not in "abcdefghijklmnopqrstuvwxyz0123456789-" for c in label):
        parser.error("spec id must be a lowercase filename-safe identifier")
    receipt_path = ROOT / "production/receipts" / ("seed-" + label + ".json")
    # Only account coordination is shared. Originals and call receipts remain
    # in the selected worktree, including requests with uncertain billing.
    account_root = primary_root(ROOT)
    run_folder = contained(account_root, '.runtime/production')
    contained(ROOT, receipt_path)
    contained(account_root, run_folder / "seed-audio.lock")
    run_folder.mkdir(parents=True, exist_ok=True)
    with (run_folder / "seed-audio.lock").open("a") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        if receipt_path.exists():
            parser.error("this attempt already has a receipt; do not resubmit it")
        quota = json.loads(args.quota.read_text())
        remaining = remaining_allowance(quota, quota_receipts(ROOT))
        if remaining < 120:
            parser.error("remaining verified allowance is below a worst-case 120-second request")
        request_id = str(uuid.uuid4())
        body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode()
        receipt = {"id": label, "status": "submitted", "request_id": request_id, "quota_id": quota["id"],
                   "submitted_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                   "endpoint": API_URL, "input": display, "input_sha256": hashlib.sha256(body).hexdigest(),
                   "remaining_before_seconds": remaining, "reserved_seconds": 120}
        json_write(receipt_path, receipt)
        request = urllib.request.Request(API_URL, data=body, method="POST", headers={
            "Content-Type": "application/json", "X-Api-Key": key, "X-Api-Request-Id": request_id})
        try:
            with urllib.request.urlopen(request, timeout=300) as response:
                result = json.load(response)
                receipt["log_id"] = response.headers.get("X-Tt-Logid")
            if result.get("code") not in (None, 0, 200):
                receipt.update(status="rejected", code=result.get("code"), message=result.get("message"))
            else:
                audio = base64.b64decode(result["audio"], validate=True)
                if not audio:
                    raise ValueError("empty provider audio")
                target, sha = save_original(audio)
                charged = result['original_duration']
                if type(charged) not in (int, float) or not math.isfinite(charged) or charged <= 0:
                    raise ValueError('invalid provider billing duration')
                receipt.update(status="completed", original_duration=result["original_duration"], duration=result.get("duration"),
                               subtitle=result.get("subtitle"), file=target.relative_to(ROOT).as_posix(), sha256=sha, bytes=len(audio))
        except urllib.error.HTTPError as exc:
            receipt.update(status="rejected" if 400 <= exc.code < 500 else "unknown", http_status=exc.code,
                           log_id=exc.headers.get("X-Tt-Logid"))
        except (OSError, ValueError, KeyError):
            receipt["status"] = "unknown"
        json_write(receipt_path, receipt)
        print(json.dumps({k:receipt.get(k) for k in ("id", "status", "request_id", "file", "duration", "original_duration", "http_status")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
