#!/usr/bin/env python3
"""Measure full isolated HTTP reads; preserve first, warmup and raw samples."""
import argparse, hashlib, json, math, platform, sqlite3, statistics, time
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import build_opener, ProxyHandler


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--url',required=True);ap.add_argument('--database',type=Path,required=True);ap.add_argument('--system-commit',required=True);ap.add_argument('--output',type=Path,required=True);ap.add_argument('--compare',type=Path);ap.add_argument('--samples',type=int,default=50)
    a=ap.parse_args()
    if a.samples<50:ap.error('at least 50 warmed samples per class are required')
    db=sqlite3.connect(a.database);db.row_factory=sqlite3.Row
    historical=db.execute("SELECT json_extract(r.payload,'$.target.object_id') entity,r.id FROM revisions r JOIN objects o ON o.id=r.object_id WHERE o.kind='JUDGMENT' AND json_extract(r.payload,'$.acceptance_model')='entity-generation-v1' ORDER BY r.created_at LIMIT 1").fetchone()
    rows=[(r['id'],r['kind'],json.loads(r['payload'])) for r in db.execute('SELECT o.id,o.kind,r.payload FROM objects o JOIN revisions r ON r.id=o.current_revision')]
    counts={oid:sum(kind=='ASSET' and any(x['object_id']==oid for x in p.get('subjects',[])) for _,kind,p in rows) for oid,kind,p in rows if kind=='ENTITY'}
    requests=[('typical',{'entity_id':'entity-a-he'}),('most_media',{'entity_id':max(counts,key=counts.get)}),('historical',{'entity_id':historical['entity'],'revision_id':historical['id']})]
    result={'system_commit':a.system_commit,'machine':platform.platform(),'python':platform.python_version(),'server':'Python HTTPServer, loopback, one process','database_sha256':hashlib.sha256(a.database.read_bytes()).hexdigest(),'counts':{t:db.execute('SELECT count(*) FROM '+t).fetchone()[0] for t in ['objects','revisions','comments','comment_events','material_rounds','material_members']},'samples_per_class':a.samples,'percentile':'sorted[ceil(n*0.95)-1]','classes':[]}
    opener=build_opener(ProxyHandler({}));previous=json.loads(a.compare.read_text()) if a.compare else None
    if previous:
        if previous['counts']!=result['counts']:ap.error('business-data counts differ from baseline')
        if previous['samples_per_class']!=a.samples:ap.error('sample counts differ from baseline')
        if [(x['class'],x['params']) for x in previous['classes']]!=requests:ap.error('request set differs from baseline')
    def read(url):
        start=time.perf_counter()
        with opener.open(url,timeout=30) as response: body=response.read()
        return (time.perf_counter()-start)*1000,json.loads(body)
    for name,params in requests:
        url=a.url.rstrip('/')+'/api/production/entity-review?'+urlencode(params)
        first,content=read(url);warm=[read(url)[0] for _ in range(5)];samples=[read(url)[0] for _ in range(a.samples)]
        digest=hashlib.sha256(json.dumps(content,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()
        p95=sorted(samples)[math.ceil(len(samples)*.95)-1]
        row={'class':name,'params':params,'first_ms':first,'warmup_ms':warm,'samples_ms':samples,'median_ms':statistics.median(samples),'p95_ms':p95,'response_sha256':digest,'response_bytes':len(json.dumps(content,ensure_ascii=False).encode())}
        if previous:
            before=next(x for x in previous['classes'] if x['class']==name);row.update(response_equal=digest==before['response_sha256'],reduction=1-p95/before['p95_ms'],passed=p95<=300 and p95<=before['p95_ms']*.5 and digest==before['response_sha256'])
        result['classes'].append(row);print(name,round(first,2),round(row['median_ms'],2),round(p95,2),flush=True)
        a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    db.close()
    if previous and not all(x['passed'] for x in result['classes']):raise SystemExit(1)
if __name__=='__main__':main()
