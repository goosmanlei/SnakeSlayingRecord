#!/usr/bin/env python3
"""Reject business resource bytes in the current Git index (also used by CI)."""
import json
from pathlib import Path
import re
import subprocess

MEDIA={'.png','.jpg','.jpeg','.webp','.gif','.svg','.ico','.wav','.mp3','.m4a','.flac','.ogg',
       '.mp4','.mov','.webm','.zip','.pdf','.srt','.ass','.blend','.tar','.gz','.sqlite3','.db'}
CATALOGS={'config/resource-catalog.json','export/resource-catalog.json'}


def cloud_identity(spec):
    return (spec.get('source', 'oss') == 'oss'
            and re.fullmatch(r'[0-9a-f]{64}', spec.get('sha256', ''))
            and spec.get('sha256') == spec.get('verified_sha256')
            and spec.get('version_id') not in (None, '', 'null')
            and isinstance(spec.get('key'), str) and '/' in spec['key']
            and not any(k in spec for k in ('body', 'content', 'data', 'url', 'signed_url')))


def check(root, revision=None):
    entries=subprocess.check_output(['git','-C',str(root),*(['ls-tree','-r','-z',revision] if revision else ['ls-files','--stage','-z'])]).split(b'\0')
    errors=[]
    for item in filter(None,entries):
        meta,name=item.split(b'\t',1)
        if revision:mode,kind,oid=meta.decode().split();stage='0'
        else:mode,oid,stage=meta.decode().split()
        name=name.decode()
        if stage!='0':errors.append(name+': unresolved merge');continue
        if mode=='120000':errors.append(name+': tracked symlink');continue
        suffix=Path(name).suffix.lower()
        if name.startswith('export/assets/') or suffix in MEDIA:
            errors.append(name+': business resources belong in OSS');continue
        size=int(subprocess.check_output(['git','-C',str(root),'cat-file','-s',oid]))
        if suffix in ('.json','.jsonl') and size>1024*1024 and name not in CATALOGS:
            errors.append(name+': large data snapshot belongs in OSS');continue
        if size>8*1024*1024:
            errors.append(name+': unusually large tracked file needs resource classification');continue
        data=subprocess.check_output(['git','-C',str(root),'cat-file','blob',oid])
        if data.startswith(b'version https://git-lfs.github.com/spec/v1\n'):
            errors.append(name+': resource LFS pointer is forbidden')
        if re.search(rb'data:(?:image|audio|video|application/(?:zip|octet-stream))[^,]{0,120};base64,[A-Za-z0-9+/=]{256}',data):
            errors.append(name+': embedded business media bytes')
        if name in CATALOGS:
            value=json.loads(data)
            if value.get('format')!='project-resources-v1' or set(value)!={'format','project','bucket','region','entries'}:
                errors.append(name+': unsupported lightweight catalog')
            for path,spec in value.get('entries',{}).items():
                for selected in [spec,*spec.get('variants',{}).values()]:
                    if not cloud_identity(selected):
                        errors.append(name+': invalid verified resource: '+path)
        if name == 'export/manifest.json':
            manifest = json.loads(data)
            if manifest.get('schema_version') == 16 and not cloud_identity(manifest.get('snapshot', {})):
                errors.append(name+': recovery snapshot requires a verified cloud identity')
    if errors:raise ValueError('\n'.join(errors))
    return {'tracked_files':len(list(filter(None,entries))),'resource_bytes':0,'lfs_pointers':0}


if __name__=='__main__':
    print(json.dumps(check(Path(__file__).resolve().parent.parent)))
