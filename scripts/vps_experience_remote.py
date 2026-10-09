#!/usr/bin/env python3
"""The lijizhanshe instance's locked, forward-only VPS publisher (stdlib only)."""
import argparse
import fcntl
import hashlib
import ipaddress
import json
import os
from pathlib import Path
import re
import shutil
import socket
import sqlite3
import subprocess
import tarfile
import time
from zoneinfo import ZoneInfo
from urllib.parse import urlsplit

HOME = Path.home()
CONTROL = HOME / 'my-config/lijizhanshe'
TARGET = HOME / 'www/lijizhanshe'
PAGE = HOME / 'www/.lijizhanshe-control'
NGINX = HOME / 'my-config/nginx.me.leiguoguo/default.conf'
CONTAINER = 'lijizhanshe-app'
LABEL = 'org.leiguoguo.instance=lijizhanshe'
NETWORK = 'nginxmeleiguoguo_default'
NGINX_CONTAINER = 'nginx.me.leiguoguo'
BEGIN, END = '# BEGIN lijizhanshe experience', '# END lijizhanshe experience'


def run(*args, **kwargs):
    return subprocess.run(args, check=True, capture_output=True, text=True, **kwargs).stdout


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda: f.read(1024*1024), b''):
            h.update(chunk)
    return h.hexdigest()


def portable_image(path, tag, revision):
    """Read the Docker save config identity, shared by both image stores."""
    def member_bytes(name):
        with tarfile.open(path, 'r|gz') as archive:
            for number, member in enumerate(archive):
                if number >= 10000:
                    raise ValueError('image archive has too many members')
                if member.name == name:
                    if not member.isfile() or member.size > 1024*1024:
                        raise ValueError('invalid image metadata member')
                    return archive.extractfile(member).read()
        raise ValueError('image metadata member is missing')
    entries = json.loads(member_bytes('manifest.json'))
    if len(entries) != 1 or entries[0].get('RepoTags') != [tag]:
        raise ValueError('image archive tag differs')
    config = member_bytes(entries[0]['Config'])
    value = json.loads(config)
    labels = value.get('config', {}).get('Labels', {})
    if value.get('architecture') != 'amd64' or labels.get('org.leiguoguo.instance') != 'lijizhanshe' or labels.get('org.opencontainers.image.revision') != revision:
        raise ValueError('image archive architecture, ownership or revision differs')
    return 'sha256:'+hashlib.sha256(config).hexdigest()


def safe(path):
    path = Path(path)
    for part in (path, *path.parents):
        if part.is_symlink():
            raise ValueError('symlink boundary: ' + str(part))
    return path


def counts(path):
    files = [p for p in safe(path).rglob('*') if p.is_file()] if path.exists() else []
    if any(p.is_symlink() for p in files):
        raise ValueError('unexpected symlink inside instance')
    return {'files': len(files), 'bytes': sum(p.stat().st_size for p in files)}


def database(path):
    db = sqlite3.connect(path.resolve().as_uri()+'?mode=ro', uri=True)
    try:
        db.execute('PRAGMA temp_store=FILE')
        if db.execute('PRAGMA quick_check').fetchall() != [('ok',)]:
            raise ValueError('database integrity failure')
        if db.execute('PRAGMA foreign_key_check').fetchall():
            raise ValueError('database foreign key failure')
        if db.execute('PRAGMA journal_mode').fetchone()[0] != 'delete':
            raise ValueError('unreviewed database journal mode')
        result = {}
        for (name,) in db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' AND name!='read_generations' ORDER BY name"):
            q = '"'+name.replace('"', '""')+'"'
            columns = ['"'+r[1].replace('"', '""')+'"' for r in db.execute('PRAGMA table_info('+q+')')]
            h, n = hashlib.sha256(), 0
            for row in db.execute('SELECT * FROM '+q+' ORDER BY '+','.join(columns)):
                h.update(json.dumps(row, ensure_ascii=False, separators=(',', ':')).encode()+b'\n')
                n += 1
            result[name] = {'rows': n, 'sha256': h.hexdigest()}
        return result
    finally:
        db.close()


def state():
    p = CONTROL/'state.json'
    return json.loads(p.read_text()) if p.exists() else {'phase': 'absent'}


def save(s, phase, **values):
    s.pop('last_error', None)
    s.update(values, phase=phase, updated_at=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()))
    p = CONTROL/'state.json.tmp'
    p.write_text(json.dumps(s, ensure_ascii=False, indent=2)+'\n')
    os.replace(p, CONTROL/'state.json')
    return s


def preflight():
    if os.uname().machine != 'x86_64':
        raise ValueError('the prepared runtime requires x86_64')
    memory = {line.split(':', 1)[0]: int(line.split()[1])*1024
              for line in Path('/proc/meminfo').read_text().splitlines() if ':' in line}
    if memory.get('MemAvailable', 0) < 1536*1024**2 or memory.get('SwapFree', 0) < 512*1024**2:
        raise ValueError('insufficient available memory/swap reserve for the bounded application')
    if run('docker', 'info', '--format', '{{.CgroupVersion}}').strip() != '2':
        raise ValueError('review runtime limits on this cgroup configuration')
    nginx = json.loads(run('docker', 'inspect', NGINX_CONTAINER))[0]
    required = {'/etc/nginx/conf.d/default.conf': NGINX,
                '/usr/share/nginx/html': HOME/'www'}
    mounts = {item['Destination']: item for item in nginx['Mounts']}
    for destination, source in required.items():
        safe(source)
        mount = mounts.get(destination, {})
        if mount.get('Source') != str(source) or mount.get('RW') is not False:
            raise ValueError('shared nginx mount boundary differs: '+destination)
    if not nginx['State']['Running'] or NETWORK not in nginx['NetworkSettings']['Networks']:
        raise ValueError('shared nginx service/network is unavailable')
    if run('systemctl', 'is-active', 'xray').strip() != 'active':
        raise ValueError('existing Xray service is not healthy; do not add deployment load')
    run('docker', 'exec', NGINX_CONTAINER, 'nginx', '-t')
    run('docker', 'network', 'inspect', NETWORK)
    return {'memory_available': memory['MemAvailable'], 'swap_free': memory['SwapFree'],
            'nginx_container': nginx['Id'], 'cgroup_version': '2', 'xray': 'active'}


def credential_values():
    credentials = safe(CONTROL/'credentials.env')
    if not credentials.is_file() or credentials.stat().st_mode & 0o077:
        raise ValueError('protected server credentials.env is required')
    values = {}
    for line in credentials.read_text().splitlines():
        if not line or line.startswith('#'):
            continue
        if '=' not in line:
            raise ValueError('credentials must use Docker env-file key=value format')
        key, value = line.split('=', 1)
        if key in values:
            raise ValueError('duplicate credential setting')
        values[key] = value
    return values


def runtime_target():
    values = credential_values()
    if values.get('REVIEW_USE_XRAY_LOOPBACK', '0') == '0':
        return {'network': NETWORK, 'bind_host': '0.0.0.0',
                'upstream': 'http://'+CONTAINER+':8765', 'probe_host': '127.0.0.1'}
    if values.get('REVIEW_USE_XRAY_LOOPBACK') != '1':
        raise ValueError('invalid loopback Xray setting')
    try:
        proxy = urlsplit(values.get('HTTPS_PROXY', ''))
        valid = proxy.scheme == 'http' and proxy.hostname == '127.0.0.1' and proxy.port and proxy.username and proxy.password
    except ValueError:
        valid = False
    if not valid:
        raise ValueError('protected authenticated loopback HTTP proxy is required')
    network = json.loads(run('docker', 'network', 'inspect', NETWORK))[0]
    gateways = [item.get('Gateway') for item in network.get('IPAM', {}).get('Config', [])
                if item.get('Gateway') and ipaddress.ip_address(item['Gateway']).version == 4
                and ipaddress.ip_address(item['Gateway']) in ipaddress.ip_network(item['Subnet'])]
    if network.get('Driver') != 'bridge' or len(gateways) != 1:
        raise ValueError('one actual IPv4 Docker bridge gateway is required')
    address = ipaddress.ip_address(gateways[0])
    if not any(address in ipaddress.ip_network(cidr) for cidr in ('10.0.0.0/8', '172.16.0.0/12', '192.168.0.0/16')):
        raise ValueError('application binding must stay on a private Docker bridge')
    return {'network': 'host', 'bind_host': str(address),
            'upstream': 'http://'+str(address)+':8765', 'probe_host': str(address)}


def check_runtime_target(target):
    if target['network'] != 'host':
        return
    proxy = urlsplit(credential_values()['HTTPS_PROXY'])
    with socket.create_connection((proxy.hostname, proxy.port), timeout=3):
        pass
    with socket.socket() as probe:
        try:
            probe.bind((target['bind_host'], 8765))
        except OSError:
            info = json.loads(run('docker', 'inspect', CONTAINER))[0]
            if (info['Config'].get('Labels', {}).get('org.leiguoguo.instance') != 'lijizhanshe'
                    or not info['State']['Running'] or info['HostConfig']['NetworkMode'] != 'host'
                    or info['Config']['Cmd'] != runtime_command(target)):
                raise ValueError('private application port is not available for this instance') from None


def runtime_command(target):
    return ['python', '-m', 'review_desk', '--instance', '/instance', 'serve',
            '--host', target['bind_host'], '--port', '8765']


def credential_check():
    values = credential_values()
    try:
        maximum = int(values.get('REVIEW_POLISH_MAX_ATTEMPTS', '0'))
        daily = int(values.get('REVIEW_POLISH_DAILY_LIMIT', '0'))
    except ValueError:
        maximum = daily = 0
    if not values.get('OPENAI_API_KEY', '').strip() or maximum <= 0 and daily <= 0:
        raise ValueError('server API credential and positive call cap are required')
    usage = safe(CONTROL/'usage/attempts.json')
    if daily > 0:
        ZoneInfo(values.get('REVIEW_POLISH_BUDGET_TIMEZONE', 'Asia/Shanghai'))
    if usage.exists():
        value = json.loads(usage.read_text())
        if type(value['attempts']) is not int or value['attempts'] < 0:
            raise ValueError('invalid API usage counter; inspect without resetting it')


def nginx_workers():
    listing = run('docker', 'exec', NGINX_CONTAINER, 'ps', '-o', 'pid,args')
    return {line.split()[0] for line in listing.splitlines()
            if 'nginx: worker process' in line and line.split()[0].isdigit()}


def configure(maintenance):
    safe(NGINX)
    text = NGINX.read_text()
    if BEGIN in text or END in text:
        if text.count(BEGIN) != 1 or text.count(END) != 1 or text.index(END) < text.index(BEGIN):
            raise ValueError('unexpected nginx integration markers')
        original = text[:text.index(BEGIN)] + text[text.index(END)+len(END):]
    else:
        original = text
    if original.count('location / {') != 1:
        raise ValueError('unexpected shared nginx config; inspect before editing')
    PAGE.mkdir(mode=0o755, exist_ok=True)
    (PAGE/'maintenance.html').write_text('<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>李寄斩蛇 · 升级中</title><body style="font-family:system-ui;background:#faf8f0;color:#264936;max-width:32rem;margin:15vh auto;padding:2rem"><h1>升级中</h1><p>李寄斩蛇体验版正在更新，请稍后再试。</p></body></html>')
    content = '''
        root /usr/share/nginx/html/.lijizhanshe-control;
        error_page 503 /__lijizhanshe_maintenance__;
        try_files /no-business-entry =503;
''' if maintenance else '''
        resolver 127.0.0.11 valid=10s ipv6=off;
        set $lijizhanshe_upstream http://lijizhanshe-app:8765;
        proxy_pass $lijizhanshe_upstream;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_request_buffering off;
        proxy_read_timeout 90s;
        client_max_body_size 8192m;
'''
    if not maintenance:
        content = content.replace('http://lijizhanshe-app:8765', runtime_target()['upstream'])
    block = BEGIN+'''
    location = /lijizhanshe { return 308 /lijizhanshe/$is_args$args; }
    location ^~ /lijizhanshe/ {
        auth_basic off;
        add_header Cache-Control "no-store" always;
'''+content+'''
    }
    location = /__lijizhanshe_maintenance__ {
        internal;
        alias /usr/share/nginx/html/.lijizhanshe-control/maintenance.html;
        default_type text/html;
        charset utf-8;
        add_header Cache-Control "no-store, no-cache, must-revalidate" always;
        add_header Retry-After 60 always;
    }
'''+END
    candidate = (text[:text.index(BEGIN)] + block + text[text.index(END)+len(END):]
                 if BEGIN in text else original.replace('location / {', block+'\n\tlocation / {', 1))
    # This is a file bind mount: preserve its inode. Running workers still use
    # the old parsed config until a successful test and graceful reload.
    with NGINX.open('w') as f:
        f.write(candidate); f.flush(); os.fsync(f.fileno())
    try:
        run('docker', 'exec', NGINX_CONTAINER, 'nginx', '-t')
        previous = nginx_workers()
        if not previous:
            raise ValueError('cannot verify nginx worker identities before reloading')
        run('docker', 'exec', NGINX_CONTAINER, 'nginx', '-s', 'reload')
    except Exception:
        NGINX.write_text(text)
        run('docker', 'exec', NGINX_CONTAINER, 'nginx', '-t')
        raise
    (CONTROL/'maintenance').write_text('on\n' if maintenance else 'off\n')
    # A successful signal is not a completed transition. Let existing requests
    # drain without terminating shared workers or another site's connections.
    for attempt in range(30):
        current = nginx_workers()
        if current and not previous.intersection(current):
            return
        if attempt < 29:
            time.sleep(1)
    raise RuntimeError('nginx previous workers are still draining; inspect before clearing the instance')


def verified_package(s):
    root = safe(CONTROL/'incoming'/s['publication_id']/'unpacked')
    m = json.loads((root/'manifest.json').read_text())
    if m['publication_id'] != s['publication_id']:
        raise ValueError('publication identity differs')
    expected = set(m['files']) | {'manifest.json'}
    actual = {str(p.relative_to(root)) for p in root.rglob('*') if p.is_file()}
    if actual != expected:
        raise ValueError('package has missing or extra files')
    for rel, info in m['files'].items():
        p = safe(root/rel)
        if p.stat().st_size != info['bytes'] or sha(p) != info['sha256']:
            raise ValueError('package checksum differs: '+rel)
    if database(root/'instance/.runtime/review.sqlite3') != m['database']:
        raise ValueError('snapshot database differs')
    return root, m


def stage(args):
    s = state()
    if s['phase'] not in ('absent', 'complete') and s.get('publication_id') != args.publication:
        raise ValueError('another incomplete publication exists; inspect status and recover it')
    package = safe(CONTROL/'incoming'/args.publication/'bundle.tar')
    if sha(package) != args.sha256:
        raise ValueError('uploaded package checksum differs; old application untouched')
    free = shutil.disk_usage(TARGET.parent).free
    if free < package.stat().st_size*3 + 5*1024**3:
        raise ValueError('insufficient disk reserve')
    root = package.parent/'unpacked'
    if root.exists():
        try:
            verified_package({'publication_id':args.publication})
        except (ValueError, OSError, KeyError):
            # A prior interrupted extraction is not a recovery source. The
            # complete archive was verified above, so rebuild only its staging.
            safe(root)
            shutil.rmtree(root)
    if not root.exists():
        root.mkdir()
        with tarfile.open(package) as archive:
            entries = archive.getmembers()
            if len(entries) > 10000 or sum(e.size for e in entries) > 30*1024**3:
                raise ValueError('package exceeds bounded extraction budget')
            for e in entries:
                rel = Path(e.name)
                if not e.isfile() or rel.is_absolute() or '..' in rel.parts or e.name not in ('manifest.json', 'image.tar.gz') and not e.name.startswith('instance/'):
                    raise ValueError('unsafe package member')
                dest = safe(root/rel); dest.parent.mkdir(parents=True, exist_ok=True)
                with archive.extractfile(e) as src, dest.open('xb') as dst:
                    shutil.copyfileobj(src, dst, 1024*1024)
    provisional = {'publication_id': args.publication}
    _, m = verified_package(provisional)
    if m.get('format') != 'lijizhanshe-experience-v1' or m.get('architecture') != 'amd64' or m.get('image_tag') != 'lijizhanshe-experience:'+args.publication:
        raise ValueError('unsupported package format, architecture or image identity')
    credential_check()
    environment = preflight()
    target = runtime_target()
    check_runtime_target(target)
    environment['runtime'] = target
    return save(s, 'staged', publication_id=args.publication, package_sha256=args.sha256,
                image_id=m['image_id'], image_tag=m['image_tag'], story_commit=m['story_commit'], desk_commit=m['desk_commit'], preflight=environment, maintenance_confirmed=False)


def maintain(s):
    if s['phase'] not in ('staged', 'maintenance', 'failed', 'verified', 'complete', 'open'):
        raise ValueError('stage a verified package first')
    credential_check()
    preflight()
    configure(True)
    return save(s, 'maintenance', maintenance_confirmed=True)


def clear(s):
    removed = {'containers': [], 'volumes': [], 'images': [], 'old_instance': counts(TARGET)}
    ids = run('docker', 'ps', '-aq', '--filter', 'label='+LABEL).split()
    named = run('docker', 'ps', '-aq', '--filter', 'name=^/'+CONTAINER+'$').split()
    if set(named)-set(ids):
        raise ValueError('container name is owned by another application')
    for ident in ids:
        info = json.loads(run('docker', 'inspect', ident))[0]
        if any(x['Source'] not in (str(TARGET), str(CONTROL/'usage')) for x in info['Mounts']):
            raise ValueError('unexpected instance container mount')
        run('docker', 'stop', '--time', '30', ident)
        run('docker', 'rm', ident); removed['containers'].append(ident)
    for ident in run('docker', 'volume', 'ls', '-q', '--filter', 'label='+LABEL).split():
        if run('docker', 'ps', '-aq', '--filter', 'volume='+ident).strip():
            raise ValueError('instance volume still referenced')
        run('docker', 'volume', 'rm', ident); removed['volumes'].append(ident)
    safe(TARGET)
    if TARGET.exists():
        if TARGET.resolve() != HOME/'www/lijizhanshe':
            raise ValueError('unexpected instance root')
        shutil.rmtree(TARGET)
    for ident in set(run('docker', 'image', 'ls', '-q', '--no-trunc', '--filter', 'label='+LABEL).split()):
        if ident == s['image_id']:
            run('docker','tag',ident,s['image_tag'])
            tags=json.loads(run('docker','image','inspect',ident))[0].get('RepoTags') or []
            for tag in tags:
                if tag.startswith('lijizhanshe-experience:') and tag!=s['image_tag']:
                    run('docker','image','rm',tag)
            continue
        if run('docker', 'ps', '-aq', '--filter', 'ancestor='+ident).strip():
            continue
        tags = json.loads(run('docker', 'image', 'inspect', ident))[0].get('RepoTags') or []
        if any(not t.startswith('lijizhanshe-experience:') for t in tags):
            raise ValueError('old dedicated image has unexpected external tags')
        run('docker', 'image', 'rm', ident); removed['images'].append(ident)
    return removed


def replace(s, fail=False):
    if not s.get('maintenance_confirmed') or (CONTROL/'maintenance').read_text().strip() != 'on':
        raise ValueError('maintenance must protect the whole prefix before clearing')
    root, m = verified_package(s)
    target = runtime_target()
    check_runtime_target(target)
    # Containerd may report an index digest locally, whereas classic Docker
    # reports the config digest after loading the exact same save archive.
    s['image_id'] = portable_image(root/'image.tar.gz', m['image_tag'], m['desk_commit'])
    removed = clear(s)
    s.setdefault('cleanups', []).append(removed)
    save(s, 'cleared')
    if fail:
        raise RuntimeError('controlled verification fault after old instance clearance')
    run('docker', 'load', '-i', str(root/'image.tar.gz'))
    image = json.loads(run('docker', 'image', 'inspect', m['image_tag']))[0]
    if image['Architecture'] != 'amd64' or image['Config'].get('Labels', {}).get('org.leiguoguo.instance') != 'lijizhanshe':
        raise ValueError('wrong image architecture or ownership')
    if image['Id'] != s['image_id']:
        raise ValueError('loaded image config differs from the verified archive')
    shutil.copytree(root/'instance', TARGET)
    save(s, 'deployed')
    (CONTROL/'usage').mkdir(mode=0o700, exist_ok=True)
    run('docker', 'run', '-d', '--name', CONTAINER, '--label', LABEL,
        '--restart', 'unless-stopped', '--network', target['network'],
        '--cpus', '1', '--memory', '1g', '--memory-swap', '1536m', '--pids-limit', '64',
        '--log-opt', 'max-size=10m', '--log-opt', 'max-file=3',
        '--env-file', str(CONTROL/'credentials.env'),
        '-e', 'REVIEW_BASE_PATH=/lijizhanshe', '-e', 'REVIEW_ENVIRONMENT=experience',
        '-e', 'REVIEW_PUBLICATION_ID='+s['publication_id'],
        '-e', 'REVIEW_PUBLIC_ENTRY=https://leiguoguo.me/lijizhanshe/',
        '-e', 'REVIEW_UPLOAD_RESERVE_BYTES=5368709120',
        '-e', 'REVIEW_POLISH_BUDGET_FILE=/usage/attempts.json',
        '-v', str(CONTROL/'usage')+':/usage',
        '-v', str(TARGET)+':/instance', image['Id'], *runtime_command(target))
    return save(s, 'started')


def verify(s):
    root, m = verified_package(s)
    if database(TARGET/'.runtime/review.sqlite3') != m['database']:
        raise ValueError('running database does not match the full snapshot')
    for rel, meta in m['files'].items():
        if not rel.startswith('instance/') or rel == 'instance/.runtime/review.sqlite3':
            continue
        if sha(TARGET/rel[len('instance/'):]) != meta['sha256']:
            raise ValueError('running file checksum differs: '+rel)
    info = json.loads(run('docker', 'inspect', CONTAINER))[0]
    h = info['HostConfig']
    target = runtime_target()
    if not info['State']['Running'] or h['Memory'] != 1024**3 or h['MemorySwap'] != 1536*1024**2 or h['NanoCpus'] != 10**9 or h['PidsLimit'] != 64 or h['PortBindings']:
        raise ValueError('runtime limits or network boundary differ')
    if h['NetworkMode'] != target['network'] or info['Config']['Cmd'] != runtime_command(target):
        raise ValueError('runtime network or private application binding differs')
    if target['network'] == 'host':
        env = dict(item.split('=', 1) for item in info['Config']['Env'])
        if env.get('HTTPS_PROXY') != credential_values().get('HTTPS_PROXY') or env.get('REVIEW_USE_XRAY_LOOPBACK') != '1':
            raise ValueError('runtime loopback proxy setting differs')
    probe = "import json,urllib.request;print(json.dumps(json.load(urllib.request.urlopen('http://"+target['probe_host']+":8765/lijizhanshe/api/instance',timeout=20))))"
    for attempt in range(10):
        try:
            value = json.loads(run('docker', 'exec', CONTAINER, 'python', '-c', probe))
            if value['deployment']['publication_id'] != s['publication_id']:
                raise ValueError('wrong live publication')
            break
        except subprocess.CalledProcessError:
            if attempt == 9: raise
            time.sleep(1)
    return save(s, 'verified', container_id=info['Id'], limits={k:h[k] for k in ['Memory','MemorySwap','NanoCpus','PidsLimit','RestartPolicy','LogConfig']})


def cleanup(s):
    if s['phase'] != 'open':
        raise ValueError('only clean recovery package after the application is open')
    incoming = safe(CONTROL/'incoming')
    removed = counts(incoming)
    shutil.rmtree(incoming); incoming.mkdir(mode=0o700)
    if any(incoming.iterdir()): raise ValueError('staging cleanup incomplete')
    return save(s, 'complete', removed_staging=removed)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('command', choices=['stage','maintain','replace','verify','open','cleanup','status'])
    p.add_argument('--publication'); p.add_argument('--sha256'); p.add_argument('--fail-after-clear', action='store_true')
    args = p.parse_args()
    if args.publication and not re.fullmatch(r'[A-Za-z0-9_-]{1,100}',args.publication):
        raise ValueError('invalid publication identity')
    safe(CONTROL); safe(TARGET); safe(PAGE)
    CONTROL.mkdir(mode=0o700, parents=True, exist_ok=True)
    with (CONTROL/'publish.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX|fcntl.LOCK_NB)
        s = state()
        try:
            if args.command == 'status':
                s = {**s, 'instance': counts(TARGET), 'containers': run('docker','ps','-a','--filter','label='+LABEL,'--format','{{.ID}} {{.Names}} {{.Status}}').splitlines(), 'maintenance': (CONTROL/'maintenance').read_text().strip() if (CONTROL/'maintenance').exists() else 'unconfigured'}
            elif args.command == 'stage': s = stage(args)
            elif args.command == 'maintain': s = maintain(s)
            elif args.command == 'replace': s = replace(s, args.fail_after_clear)
            elif args.command == 'verify': s = verify(s)
            elif args.command == 'open':
                if s['phase'] != 'verified': raise ValueError('verify before opening')
                configure(False); s = save(s, 'open', maintenance_confirmed=False)
            else: s = cleanup(s)
        except Exception as exc:
            # Preserve phase and minimal reason, never copy data or secrets.
            s = state()
            save(s, s['phase'], last_error=type(exc).__name__+': '+str(exc)[:300])
            raise
        print(json.dumps(s, ensure_ascii=False, indent=2))


if __name__ == '__main__': main()
