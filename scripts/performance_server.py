#!/usr/bin/env python3
"""Identical request timing wrapper for the two isolated performance instances.

Select exact system code with PYTHONPATH. This measures service CPU/wall time,
not browser latency. No SQL tracing/profiler runs during the browser comparison.
"""
import argparse
import json
import os
from pathlib import Path
import platform
import resource
import time


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--side',choices=('baseline','candidate'),required=True)
    parser.add_argument('--port',type=int,required=True)
    parser.add_argument('--instance-subdir', choices=(
        'baseline-write-r1','candidate-write-r1','baseline-write-r2','candidate-write-r2',
        'baseline-write-r4','candidate-write-r4','baseline-write-r5','candidate-write-r5',
        'baseline-navigation-r6','candidate-navigation-r6','baseline-navigation-r7','candidate-navigation-r7',
        'correctness-instance'), help='separate disposable copy for write/history regression')
    parser.add_argument('--diagnostics',action='store_true',
                        help='record connection/queue/transaction costs outside paired timing')
    args=parser.parse_args()
    runtime=Path(__file__).resolve().parents[1]/'.runtime/system-performance'
    root=(runtime/(args.instance_subdir or args.side+'-instance')).resolve()
    if root.parent!=runtime.resolve() or not (root/'.runtime/review.sqlite3').is_file():
        raise ValueError('an independent frozen snapshot copy is required')
    diagnostic=None
    if args.diagnostics:
        if args.side!='candidate' or not args.instance_subdir:
            raise ValueError('diagnostics require a disposable candidate correctness copy')
        from performance_diagnostics import Diagnostics
        diagnostic=Diagnostics(runtime/f'diagnostics-{args.port}.jsonl')
        diagnostic.install()
    from review_desk.server import ReviewHandler,ReviewServer
    original_file=ReviewHandler._file
    observer=(runtime/'probe.js').read_bytes()
    def file_with_observer(handler,path,mime):
        if path.name!='index.html':return original_file(handler,path,mime)
        page=handler.server.web_assets.index if hasattr(handler.server,'web_assets') else path.read_bytes()
        data=page.replace(b'<meta charset="utf-8">',b'<meta charset="utf-8"><script>'+observer+b'</script>',1)
        handler.send_response(200);handler.send_header('Content-Type',mime)
        handler.send_header('Content-Length',str(len(data)));handler.send_header('Cache-Control','no-store')
        handler.end_headers();handler.wfile.write(data)
    ReviewHandler._file=file_with_observer
    config=json.loads((root/'config/instance.json').read_text())
    log=runtime/(args.side+'-server.jsonl')
    def instrument(method):
        def measured(handler):
            if diagnostic:diagnostic.request(True)
            before=resource.getrusage(resource.RUSAGE_SELF);start=time.perf_counter();cpu_start=time.thread_time();stamp=time.time()
            error=None
            try:return method(handler)
            except BaseException as exc:
                error=type(exc).__name__;raise
            finally:
                after=resource.getrusage(resource.RUSAGE_SELF)
                row={'at':stamp,'pid':os.getpid(),'side':args.side,'sample':handler.headers.get('X-Perf-Sample'),
                     'method':handler.command,'path':handler.path,'wall_ms':(time.perf_counter()-start)*1000,
                     'cpu_ms':(time.thread_time()-cpu_start)*1000,
                     'process_cpu_interval_ms':((after.ru_utime+after.ru_stime)-(before.ru_utime+before.ru_stime))*1000,
                     'peak_rss_bytes':after.ru_maxrss*(1 if platform.system()=='Darwin' else 1024),'error':error}
                row['read_cache']=getattr(handler,'_cache_state','bypass')
                with log.open('a') as out:out.write(json.dumps(row)+'\n')
                if diagnostic:diagnostic.request(False)
        return measured
    for name in ('do_GET','do_POST','do_PATCH','do_PUT'):
        if hasattr(ReviewHandler,name):setattr(ReviewHandler,name,instrument(getattr(ReviewHandler,name)))
    ReviewHandler.log_message=lambda *_args:None
    with ReviewServer(('127.0.0.1',args.port),root,config) as server:
        if diagnostic:diagnostic.start(server)
        print(json.dumps({'side':args.side,'port':args.port,'pid':os.getpid(),'python':platform.python_version(),
                          'source':__import__('review_desk').__path__[0],'instance':str(root)}),flush=True)
        try:server.serve_forever()
        except KeyboardInterrupt:pass
    if diagnostic:diagnostic.close()


if __name__=='__main__':main()
