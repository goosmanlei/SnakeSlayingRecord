#!/usr/bin/env python3
"""Read-only HTTP timings for the delivered 17-episode breakdown fixture."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import platform
import statistics
import time
import urllib.request


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--url',required=True);p.add_argument('--database',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
    checks=[('episode01','breakdown?episode=screenplay-04-lantern-home-e01','shots',33),
            ('episode17','breakdown?episode=screenplay-04-lantern-home-e17','shots',18),
            ('shot_context','context?object_id=shot-e17-002','requirements',6),
            ('scene_video_filter','materials?episode=screenplay-04-lantern-home-e17&scene=s042&media=video','items',7)]
    output={'format':'breakdown-http-performance-v1','machine':platform.platform(),'python':platform.python_version(),
        'server':'Python HTTPServer, loopback, one process','samples_per_class':50,
        'percentile':'sorted[ceil(n*0.95)-1]','database_sha256':hashlib.sha256(a.database.read_bytes()).hexdigest(),'classes':[]}
    for name,path,key,count in checks:
        samples=[];first=None;digest=None;size=0
        for i in range(56):
            start=time.perf_counter()
            with opener.open(a.url.rstrip('/')+'/api/production/'+path,timeout=10) as response:raw=response.read()
            elapsed=(time.perf_counter()-start)*1000;data=json.loads(raw)
            if len(data[key])!=count:raise ValueError(name+' content scope changed')
            value=hashlib.sha256(raw).hexdigest()
            if digest and digest!=value:raise ValueError(name+' changed during measurement')
            digest=value;size=len(raw)
            if i==0:first=elapsed
            if i>=6:samples.append(elapsed)
        row={'class':name,'path':path,'verified_count':count,'first_ms':first,'samples_ms':samples,
             'median_ms':statistics.median(samples),'p95_ms':sorted(samples)[math.ceil(len(samples)*.95)-1],
             'response_sha256':digest,'response_bytes':size}
        output['classes'].append(row);print(name,round(row['p95_ms'],2))
    a.output.write_text(json.dumps(output,ensure_ascii=False,indent=2)+'\n')


if __name__=='__main__':main()
