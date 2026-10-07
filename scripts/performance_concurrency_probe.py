#!/usr/bin/env python3
"""Bounded localhost reads used alongside real-browser media and comment writes."""
import argparse
import concurrent.futures
import hashlib
import json
from pathlib import Path
import platform
import resource
import threading
import time
from urllib.request import Request, urlopen
from urllib.parse import urlsplit


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--base',required=True)
    p.add_argument('--media',required=True,help='observed production-file URL path')
    p.add_argument('--output',required=True,type=Path)
    p.add_argument('--interval',type=float,default=1,help='1 to 5 seconds between each client round')
    a=p.parse_args()
    if urlsplit(a.base).hostname!='127.0.0.1' or not a.media.startswith('/api/production/files/') or not 1<=a.interval<=5:
        raise ValueError('isolated localhost and an observed original-media path are required')
    paths=['/api/production/card?object_id=entity-li-ji',
           '/api/production/scene?object_id=preparation-s002&revision_id=cab284f511de11dd442b3c04391a5aaaa4201649115570e1ac368aa7571fe0c4&view=shots',
           '/api/comments',a.media]
    start=time.monotonic();barrier=threading.Barrier(12)
    def worker(number):
        rows=[];barrier.wait()
        for iteration in range(8):
            path=paths[(number+iteration)%len(paths)]
            headers={'Accept':'application/vnd.review-desk.graph+json','Accept-Encoding':'gzip'}
            if path==a.media:headers={'Range':'bytes=0-65535'}
            stamp=time.time();begin=time.perf_counter()
            row={'worker':number,'iteration':iteration,'path':path,'at':stamp}
            try:
                with urlopen(Request(a.base+path,headers=headers),timeout=20) as response:
                    body=response.read(2*1024*1024+1)
                    if len(body)>2*1024*1024:raise ValueError('unexpected response over 2 MiB diagnostic limit')
                    row.update(status=response.status,bytes=len(body),sha256=hashlib.sha256(body).hexdigest(),
                               cache=response.headers.get('X-Review-Cache'),
                               content_range=response.headers.get('Content-Range'),
                               content_encoding=response.headers.get('Content-Encoding'))
                    if response.status!=(206 if path==a.media else 200):raise ValueError('unexpected HTTP status')
            except Exception as exc:row['error']=str(exc)
            row['elapsed_ms']=(time.perf_counter()-begin)*1000;rows.append(row)
            time.sleep(max(0,start+(iteration+1)*a.interval-time.monotonic()))
        return rows
    with concurrent.futures.ThreadPoolExecutor(max_workers=12) as pool:
        rows=[r for group in pool.map(worker,range(12)) for r in group]
    usage=resource.getrusage(resource.RUSAGE_SELF)
    result={'base':a.base,'clients':12,'maximum_requests':96,'interval_seconds':a.interval,'rows':rows,
            'duration_seconds':time.monotonic()-start,
            'client_peak_rss_bytes':usage.ru_maxrss*(1 if platform.system()=='Darwin' else 1024),
            'client_cpu_seconds':usage.ru_utime+usage.ru_stime,
            'note':'API/Range load only; real user actions and playback verified separately in Chrome'}
    a.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'requests':len(rows),'errors':[r for r in rows if r.get('error')],
                      'duration_seconds':result['duration_seconds']},ensure_ascii=False))
    if any(r.get('error') for r in rows):raise SystemExit(1)


if __name__=='__main__':main()
