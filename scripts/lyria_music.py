#!/usr/bin/env python3
"""Lyria song generation: offline preview by default, explicit one-shot submission."""
import argparse
import base64
import datetime
import decimal
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request

ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/interactions"
MODEL = "lyria-3.5"
# Official list price checked 2026-10-03; an estimate, not a billing guarantee.
ESTIMATED_USD = decimal.Decimal("0.08")


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def digest(data):
    return hashlib.sha256(data).hexdigest()


def dump(value):
    return json.dumps(value, ensure_ascii=False, indent=2) + "\n"


def atomic_write(path, data):
    """Replace only this run's metadata; keep private files private."""
    fd, name = tempfile.mkstemp(prefix=".write-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def save_original(path, data):
    if path.is_symlink():
        raise ValueError("original must not be a symlink")
    if path.exists():
        if path.read_bytes() != data:
            raise ValueError("existing original differs; refusing overwrite")
        return
    with path.open("xb") as stream:
        os.chmod(path, 0o600)
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())


def private_runtime(workspace):
    workspace = workspace.resolve(strict=True)
    runtime = workspace / ".runtime"
    if runtime.is_symlink():
        raise ValueError(".runtime must not be a symlink")
    runtime.mkdir(exist_ok=True, mode=0o700)
    directory = runtime / "lyria"
    if directory.is_symlink():
        raise ValueError(".runtime/lyria must not be a symlink")
    directory.mkdir(exist_ok=True, mode=0o700)
    return directory


def shared_root(workspace):
    # git-common-dir points to the same repository from all task worktrees.
    common = subprocess.check_output(
        ["git", "rev-parse", "--git-common-dir"], cwd=workspace, text=True
    ).strip()
    path = Path(common)
    if not path.is_absolute():
        path = workspace / path
    return path.resolve(strict=True).parent


def read_source(spec_path, field, spec):
    name = spec.get(field)
    if not isinstance(name, str) or not name:
        raise ValueError(field + " must name a UTF-8 file (relative to spec)")
    path = (spec_path.parent / name).resolve(strict=True)
    raw = path.read_bytes()
    text = raw.decode("utf-8").strip()
    if not text:
        raise ValueError(field + " is empty")
    expected = spec.get(field.replace("_file", "_sha256"))
    if expected is not None and expected != digest(raw):
        raise ValueError(field + " checksum differs from selected version")
    return text, {"path": str(path), "sha256": digest(raw)}


def prepare(spec_path):
    spec_path = spec_path.resolve(strict=True)
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    allowed = {"id", "song_entity_id", "model", "lyrics_file", "lyrics_sha256",
               "directions_file", "directions_sha256", "output_format"}
    if not isinstance(spec, dict) or set(spec) - allowed:
        raise ValueError("unknown specification fields; see production/lyria-music.md")
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,79}", spec.get("id", "")):
        raise ValueError("id must be a lowercase filename-safe attempt identifier")
    if spec.get("model", MODEL) != MODEL:
        raise ValueError("this program supports only " + MODEL)
    if not isinstance(spec.get("song_entity_id"), str) or not spec["song_entity_id"]:
        raise ValueError("song_entity_id is required")
    fmt = spec.get("output_format", "mp3")
    if fmt not in ("wav", "mp3"):
        raise ValueError("output_format must be wav or mp3")
    lyrics, lyric_source = read_source(spec_path, "lyrics_file", spec)
    directions, direction_source = read_source(spec_path, "directions_file", spec)
    prompt = (directions + "\n\n以下是完整歌词。按段落演唱，不增删、替换歌词，"
              "不要唱出说明文字；若无法遵循，产出仍须人工核对。\nLyrics:\n" + lyrics)
    payload = {"model": MODEL, "input": prompt, "store": False}
    # Music-specific docs: omit response_format for default MP3; use only
    # type=audio for WAV. Generic MIME/delivery fields were rejected live.
    if fmt == "wav":
        payload["response_format"] = {"type": "audio"}
    metadata = {"attempt_id": spec["id"], "song_entity_id": spec["song_entity_id"],
                "spec_sha256": digest(spec_path.read_bytes()),
                "sources": {"lyrics": lyric_source, "directions": direction_source},
                "requested_format": fmt, "estimated_cost_usd": str(ESTIMATED_USD),
                "price_checked": "2026-10-03", "audio_accepted": False}
    return payload, metadata


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None  # Never forward the credential to another location.


def validate_proxy(proxy):
    if proxy is not None:
        parsed = urllib.parse.urlsplit(proxy)
        if (parsed.scheme != "http" or not parsed.hostname
                or parsed.username or parsed.password or not parsed.port
                or parsed.path not in ("", "/") or parsed.query or parsed.fragment):
            raise ValueError("--proxy must be an HTTP proxy without embedded credentials")
    return proxy


def redact(raw, key, proxy_user=None):
    secrets = [key]
    if proxy_user:
        secrets.extend([proxy_user, *proxy_user.split(":", 1),
                        base64.b64encode(proxy_user.encode()).decode()])
    for secret in secrets:
        if secret:
            raw = raw.replace(secret.encode(), b"[REDACTED]")
    return raw


def request_json(url, key, payload=None, timeout=30, proxy=None, proxy_user=None):
    body = None if payload is None else dump(payload).encode("utf-8")
    request = urllib.request.Request(url, data=body, headers={
        "x-goog-api-key": key, "Content-Type": "application/json",
        "User-Agent": "SnakeSlayingRecord-Lyria/1"})
    handlers = [NoRedirect()]
    if proxy is not None:
        proxy_url = validate_proxy(proxy)
        if proxy_user:
            user, password = proxy_user.split(":", 1)
            parsed = urllib.parse.urlsplit(proxy_url)
            auth = urllib.parse.quote(user, safe="") + ":" + urllib.parse.quote(password, safe="")
            proxy_url = urllib.parse.urlunsplit(parsed._replace(netloc=auth + "@" + parsed.netloc))
        handlers.append(urllib.request.ProxyHandler({"https": proxy_url}))
    opener = urllib.request.build_opener(*handlers)
    with opener.open(request, timeout=timeout) as response:
        raw = response.read()
    try:
        parsed = json.loads(raw)
    except (ValueError, UnicodeDecodeError):
        parsed = None
    return raw, parsed


def output_blocks(response):
    blocks = []
    for step in response.get("steps", []):
        if step.get("type") == "model_output":
            blocks.extend(step.get("content", []))
    # Older Interactions responses use a top-level outputs array.
    if not blocks:
        blocks = response.get("outputs", [])
    return blocks


def probe(path):
    result = subprocess.run(["ffprobe", "-v", "error", "-show_format",
                             "-show_streams", "-of", "json", str(path)],
                            capture_output=True, text=True, timeout=30)
    if result.returncode:
        raise ValueError("ffprobe could not decode provider audio")
    info = json.loads(result.stdout)
    audio = [s for s in info.get("streams", []) if s.get("codec_type") == "audio"]
    if len(audio) != 1:
        raise ValueError("expected one audio stream per returned audio block")
    stream = audio[0]
    container = info.get("format", {}).get("format_name", "")
    codec = stream.get("codec_name", "")
    native_wav = ("wav" in container.split(",") and codec.startswith("pcm_"))
    extension = "wav" if "wav" in container.split(",") else "mp3" if codec == "mp3" else "bin"
    duration = float(info.get("format", {}).get("duration", 0))
    if not 0 < duration < float("inf"):
        raise ValueError("provider audio has invalid duration")
    return {"container": container, "codec": codec, "sample_rate": stream.get("sample_rate"),
            "channels": stream.get("channels"), "duration_seconds": duration,
            "native_pcm_wav": native_wav, "extension": extension}


def finish(run, response, receipt):
    if response.get("status") not in (None, "completed"):
        raise ValueError("provider interaction is not completed; no automatic resubmission")
    files, text = [], []
    for block in output_blocks(response):
        if block.get("type") == "text":
            text.append(block.get("text", ""))
        elif block.get("type") == "audio":
            if not isinstance(block.get("data"), str):
                raise ValueError("audio block has no inline data; URI downloads are not automatic")
            raw = base64.b64decode(block["data"], validate=True)
            source = run / ("audio-%02d.original" % (len(files) + 1))
            save_original(source, raw)
            actual = probe(source)
            output = source.with_suffix("." + actual.pop("extension"))
            save_original(output, raw)
            source.unlink()
            files.append({"file": output.name, "sha256": digest(raw), "bytes": len(raw),
                          "reported_mime_type": block.get("mime_type"), **actual})
    if not files:
        raise ValueError("provider returned no audio; response preserved")
    if text:
        atomic_write(run / "provider-text.txt", "\n\n".join(text).encode("utf-8"))
    wanted = receipt["requested_format"]
    matches = all(f["native_pcm_wav"] if wanted == "wav" else f["codec"] == "mp3"
                  for f in files)
    receipt.update(status="completed" if matches else "completed_format_mismatch",
                   finished_at=now(), interaction_id=response.get("id"),
                   provider_model=response.get("model"), files=files,
                   usage=response.get("usage"), audio_accepted=False,
                   lyric_check="pending", listening_review="pending")
    atomic_write(run / "receipt.json", dump(receipt).encode("utf-8"))
    return matches


def submit(payload, metadata, workspace, max_cost, timeout, proxy=None, proxy_user=None):
    key = os.environ.get("GOOGLE_API_KEY", "").strip()
    if not key:
        raise ValueError("GOOGLE_API_KEY is not available in this process")
    if not shutil.which("ffprobe"):
        raise ValueError("ffprobe is required before submission")
    budget = decimal.Decimal(max_cost)
    if not budget.is_finite() or budget < ESTIMATED_USD:
        raise ValueError("--max-cost-usd must cover the estimated USD 0.08 for this one request")
    root = private_runtime(shared_root(workspace))
    lock_path = root / "account.lock"
    if lock_path.is_symlink():
        raise ValueError("account lock must not be a symlink")
    with lock_path.open("a") as lock:
        os.chmod(lock_path, 0o600)
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        run = private_runtime(workspace) / metadata["attempt_id"]
        run.mkdir(mode=0o700)  # Existing attempt always refuses another paid POST.
        receipt = dict(metadata, status="prepared", created_at=now(),
                       max_cost_usd=str(budget), endpoint=ENDPOINT,
                       proxy=proxy or "system/environment proxy settings")
        atomic_write(run / "request.json", dump(payload).encode("utf-8"))
        receipt.update(status="submitted", submitted_at=now())
        atomic_write(run / "receipt.json", dump(receipt).encode("utf-8"))
        response_saved = False
        try:
            raw, response = request_json(ENDPOINT, key, payload, timeout, proxy, proxy_user)
            # Remove the credential if a provider unexpectedly echoes it.
            raw = redact(raw, key, proxy_user)
            atomic_write(run / "response.json", raw)
            response_saved = True
            response = json.loads(raw)
            receipt.update(status="provider_completed_local_pending",
                           interaction_id=response.get("id"))
            atomic_write(run / "receipt.json", dump(receipt).encode("utf-8"))
            matches = finish(run, response, receipt)
            return run, receipt, matches
        except BaseException as error:
            status = "local_processing_failed" if response_saved else "unknown"
            detail = type(error).__name__
            if isinstance(error, urllib.error.HTTPError):
                status = "rejected" if error.code in (400, 401, 403, 404, 422) else "unknown"
                detail = "HTTP %s" % error.code
                try:
                    provider_error = json.loads(error.read())
                    atomic_write(run / "provider-error.json",
                                 redact(dump(provider_error).encode("utf-8"), key, proxy_user))
                except Exception:
                    pass
            receipt.update(status=status, error=detail, updated_at=now())
            atomic_write(run / "receipt.json", dump(receipt).encode("utf-8"))
            raise RuntimeError("%s; inspect %s; do not automatically resubmit" % (detail, run)) from None


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("spec", type=Path, nargs="?")
    parser.add_argument("--workspace", type=Path, default=Path.cwd(),
                        help="task worktree root; outputs stay in its .runtime/lyria")
    action = parser.add_mutually_exclusive_group()
    action.add_argument("--submit", action="store_true")
    action.add_argument("--check", action="store_true", help="local prerequisites only")
    action.add_argument("--check-api", action="store_true", help="read-only model metadata GET")
    action.add_argument("--recover", type=Path, help="reprocess a saved response, no network")
    parser.add_argument("--max-cost-usd", help="explicit ceiling for estimated cost of one POST")
    parser.add_argument("--timeout", type=int, default=600)
    parser.add_argument("--proxy", help="explicit HTTP proxy URL without embedded credentials")
    parser.add_argument("--proxy-user-env", help="environment variable containing proxy username:password")
    args = parser.parse_args(argv)
    proxy_user = None
    try:
        if args.timeout <= 0:
            raise ValueError("timeout must be positive")
        validate_proxy(args.proxy)
        if args.proxy_user_env:
            if not args.proxy or not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", args.proxy_user_env):
                raise ValueError("--proxy-user-env requires --proxy and an environment variable name")
            proxy_user = os.environ.get(args.proxy_user_env)
            if (not proxy_user or ":" not in proxy_user or
                    not all(proxy_user.split(":", 1)) or "\n" in proxy_user or "\r" in proxy_user):
                raise ValueError("proxy credential environment must contain username:password")
        if args.check or args.check_api:
            checks = {"GOOGLE_API_KEY_configured": bool(os.environ.get("GOOGLE_API_KEY", "").strip()),
                      "ffprobe_available": bool(shutil.which("ffprobe")), "model": MODEL,
                      "generation_tested": False, "proxy": args.proxy or "system/environment"}
            if args.check_api:
                if not checks["GOOGLE_API_KEY_configured"]:
                    raise ValueError("GOOGLE_API_KEY is not configured")
                _, model = request_json("https://generativelanguage.googleapis.com/v1beta/models/" + MODEL,
                                        os.environ["GOOGLE_API_KEY"], timeout=min(args.timeout, 30),
                                        proxy=args.proxy, proxy_user=proxy_user)
                if not isinstance(model, dict):
                    raise ValueError("model metadata response is not a JSON object")
                checks["model_metadata"] = {k: model.get(k) for k in
                                            ("name", "displayName", "supportedGenerationMethods")}
                checks["generation_access"] = "unverified (metadata GET only)"
            print(dump(checks), end="")
            return 0
        if args.recover:
            run = args.recover.resolve(strict=True)
            root = private_runtime(args.workspace)
            if run.parent != root.resolve() or not run.is_dir():
                raise ValueError("recover must name an attempt in this workspace's .runtime/lyria")
            with (run / "recover.lock").open("a") as lock:
                fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                receipt = json.loads((run / "receipt.json").read_text())
                response = json.loads((run / "response.json").read_text())
                matches = finish(run, response, receipt)
            print(dump({"run_directory": str(run), "receipt": receipt}), end="")
            return 0 if matches else 2
        if args.spec is None:
            raise ValueError("provide a specification or choose --check")
        payload, metadata = prepare(args.spec)
        if not args.submit:
            print(dump({"mode": "offline_preview", "endpoint": ENDPOINT,
                        "request": payload, "metadata": metadata}), end="")
            return 0
        if args.max_cost_usd is None:
            raise ValueError("--submit requires --max-cost-usd (one request, no automatic retries)")
        run, receipt, matches = submit(payload, metadata, args.workspace.resolve(strict=True),
                                       args.max_cost_usd, args.timeout, args.proxy, proxy_user)
        print(dump({"run_directory": str(run), "receipt": receipt}), end="")
        return 0 if matches else 2
    except urllib.error.HTTPError as error:
        detail = ""
        try:
            detail = str(json.loads(error.read()).get("error", {}).get("message", ""))
        except Exception:
            pass
        detail = redact(detail.encode(), os.environ.get("GOOGLE_API_KEY", ""), proxy_user).decode()
        print("error: read-only API check returned HTTP %s: %s; generation access unverified" %
              (error.code, detail), file=sys.stderr)
        return 1
    except (Exception, KeyboardInterrupt) as error:
        # Do not print network URLs/headers or exception chains containing credentials.
        message = str(error) if isinstance(error, (ValueError, RuntimeError)) else type(error).__name__
        message = redact(message.encode(), os.environ.get("GOOGLE_API_KEY", ""), proxy_user).decode()
        print("error: " + message, file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
