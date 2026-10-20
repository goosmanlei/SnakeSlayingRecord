"""Bounded normal reads; no writes, cache clearing or concurrency on formal services."""
import argparse, hashlib, json, subprocess, tempfile, time
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('base');p.add_argument('spec');p.add_argument('output');p.add_argument('--rounds',type=int,default=3);p.add_argument('--publication',default='');p.add_argument('--only');a=p.parse_args()
assert 1<=a.rounds<=3
spec=json.loads(Path(a.spec).read_text()); workloads=spec['workloads']; rows=[]
with tempfile.TemporaryDirectory(prefix='production-readback-') as tmp:
 for w in workloads:
  if a.only and w['name'] not in a.only.split(','):continue
  for index in range(a.rounds):
   body=Path(tmp)/'body'; headers=Path(tmp)/'headers'
   cmd=['curl','--silent','--show-error','--max-time','90','--compressed','-H','Accept: application/vnd.review-desk.graph+json','-D',str(headers),'-o',str(body),'-w','%{json}',a.base.rstrip('/')+w['path']]
   if a.publication:cmd[1:1]=['-H','X-Review-Publication: '+a.publication]
   if w.get('method')=='HEAD':cmd.insert(1,'--head')
   if 'body' in w:cmd[1:1]=['-H','Content-Type: application/json','--data-binary',json.dumps(w['body'])]
   start=time.time();r=subprocess.run(cmd,capture_output=True,text=True)
   v=json.loads(r.stdout) if r.stdout else {};raw=body.read_bytes() if body.exists() else b''
   selected={k:v.get(k) for k in ('http_code','time_namelookup','time_connect','time_appconnect','time_pretransfer','time_starttransfer','time_total','size_download','num_connects','http_version','exitcode')}
   cache=next((line.split(':',1)[1].strip() for line in headers.read_text().splitlines() if line.lower().startswith('x-review-cache:')),None)
   row={'workload':w['name'],'index':index,'started_at':start,'cache':cache,**selected,'decoded_bytes':len(raw) if w.get('method')!='HEAD' else None,'sha256':hashlib.sha256(raw).hexdigest() if w.get('method')!='HEAD' else None}
   if r.returncode or v.get('http_code') not in (200,307):row['error']=r.stderr or ('HTTP '+str(v.get('http_code')))
   rows.append(row);Path(a.output).write_text(json.dumps({'base':a.base,'boundary':'Three sequential normal reads per workload; existing formal cache, first observed is not forced cold. Curl DNS/TCP/TLS/starttransfer/total are wall time; no server or browser CPU inference. Redirects are not followed. No response body or signed URL retained.','samples':rows},indent=2)+'\n')
print(json.dumps({'samples':len(rows),'failures':sum('error'in r for r in rows)}))
