#!/usr/bin/env python3
"""Summarize the frozen browser ABAB comparison without dropping slow samples.

The baseline input may contain an abandoned candidate: only its baseline rows
are reused. The comparison input contains the final candidate and second round.
Primary latency is the page's user-action -> correct-content/two-paint endpoint.
"""
import argparse
from collections import defaultdict
import json
from pathlib import Path
from urllib.parse import urlsplit


def quantile(values, q):
    values = sorted(values)
    if not values: return None
    index = (len(values)-1)*q
    low = int(index)
    return values[low]+(values[min(low+1,len(values)-1)]-values[low])*(index-low)


def stats(values):
    return {'n': len(values), 'median': quantile(values,.5), 'p25': quantile(values,.25),
            'p75': quantile(values,.75), 'iqr': quantile(values,.75)-quantile(values,.25) if values else None,
            'min': min(values) if values else None, 'max': max(values) if values else None}


def rows(path):
    with path.open() as stream:
        for line in stream:
            if line.strip(): yield json.loads(line)


def summarize(baseline, comparison, server_logs=(), round_numbers=(1,2)):
    server = defaultdict(list)
    for path in server_logs:
        for item in rows(path):server[item['side']].append(item)
    groups = defaultdict(list)
    for row in [*(r for r in rows(baseline) if r['side']=='baseline'), *rows(comparison)]:
        if row['round'] not in round_numbers:continue
        if row['condition']=='setup': continue
        groups[(row['round'],row['side'],row['path'],row['condition'])].append(row)
    output = [];failures=[]
    for key,values in sorted(groups.items()):
        valid=[r for r in values if not r.get('failed')]
        failures.extend({'id':r['id'],'error':r.get('failed'),'network':r.get('networkError')} for r in values if r.get('failed') or r.get('networkError'))
        def metric(row,name):
            after={m['name']:m['value'] for m in row['metrics_after']['metrics']}
            before={m['name']:m['value'] for m in (row.get('metrics_before') or {}).get('metrics',[])}
            return 1000*(after.get(name,0)-before.get(name,0))
        service = defaultdict(list)
        for row in valid:
            begin=(row['time_origin']+row['start'])/1000
            end=(row['time_origin']+row['end'])/1000
            for request in server.get(row['side'], []):
                if begin<=request['at']<=end and request['path'].startswith('/api/'):
                    service[urlsplit(request['path']).path].append(request)
        output.append({'round':key[0],'side':key[1],'path':key[2],'condition':key[3],
            'latency_ms':stats([r['ms'] for r in valid]),'ids':[r['id'] for r in values],
            'content_sha256':sorted({r['content_sha256'] for r in valid}),
            'primary_requests':stats([len(r['resources']) for r in valid]),
            'primary_transfer_bytes':stats([sum(e['transfer'] for e in r['resources']) for r in valid]),
            'primary_encoded_body_bytes':stats([sum(e['encoded'] for e in r['resources']) for r in valid]),
            'browser_task_ms_including_observer_and_media':stats([metric(r,'TaskDuration') for r in valid]),
            'browser_script_ms_including_observer':stats([metric(r,'ScriptDuration') for r in valid]),
            'browser_layout_ms':stats([metric(r,'LayoutDuration') for r in valid]),
            'browser_heap_bytes':stats([r['heap']['used'] for r in valid if r.get('heap')]),
            'visible_media_load_events_ms':stats([max([0,*[i['at']-r['start'] for i in r['media']['images'] if i['at']>=r['start']]]) for r in valid]),
            'unloaded_visible_media':sum(sum(not i['complete'] or not i['width'] for i in r['media']['visible']) for r in valid),
            'related_service':{path:{'requests':len(items),'wall_ms':stats([r['wall_ms'] for r in items]),
                'thread_cpu_ms':stats([r['cpu_ms'] for r in items]),'peak_rss_bytes':max(r['peak_rss_bytes'] for r in items),
                'cache_states':{state:sum(r.get('read_cache')==state for r in items) for state in sorted({r.get('read_cache','unknown') for r in items})}}
                for path,items in service.items()}})
    indexed={(r['round'],r['side'],r['path'],r['condition']):r for r in output};comparisons=[]
    cases=sorted({(r['path'],r['condition']) for r in output})
    for round_number in round_numbers:
        for path,condition in cases:
            left=indexed.get((round_number,'baseline',path,condition));right=indexed.get((round_number,'candidate',path,condition))
            if not left or not right:
                comparisons.append({'round':round_number,'path':path,'condition':condition,'complete':False});continue
            a,b=left['latency_ms'],right['latency_ms'];drop=a['median']-b['median'];noise=max(a['iqr'],b['iqr'])
            slow=path not in ('breakdown.shot','shots.shot','materials.page')
            comparisons.append({'round':round_number,'path':path,'condition':condition,'complete':a['n']>=10 and b['n']>=10,
                'baseline_ms':a['median'],'candidate_ms':b['median'],'drop_ms':drop,'noise_ms':noise,
                'slow_path':slow,'improvement_pass':drop>noise if slow else None,
                'regression':-drop>noise,'candidate_p75_ms':b['p75'],'target_300ms_pass':b['p75']<=300,
                'content_equal':left['content_sha256']==right['content_sha256']})
    return {'quartiles':'Hyndman-Fan type 7, fixed before measurement','failure_policy':'all raw failures and slow samples retained',
            'media_metric':'actual image load events after the action, separate from main readiness; cached images without a new event are zero; playback verified separately',
            'browser_cpu_metric':'Chrome Performance metrics; includes the shared observer and post-readiness media collection; not tool round-trip wall time',
            'service_metric':'Requests that started in the same origin timestamp interval as the primary action; native server wall and thread CPU, process lifetime peak RSS; API time is not browser latency',
            'rounds':list(round_numbers),'cases':len(cases),'failures':failures,'paths':output,'comparisons':comparisons}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--baseline',type=Path,required=True);p.add_argument('--comparison',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True);p.add_argument('--require-complete',action='store_true')
    p.add_argument('--server-log',type=Path,action='append',default=[])
    p.add_argument('--round',type=int,action='append',dest='rounds')
    p.add_argument('--comment-receipts',type=Path,
                   help='directory of exact isolated comment readbacks for supplemental/impact comparisons')
    a=p.parse_args();result=summarize(a.baseline,a.comparison,a.server_log,a.rounds or (1,2))
    if a.comment_receipts:
        for comparison in result['comparisons']:
            if not comparison.get('complete'):continue
            if comparison['path'] in ('card.history.current','card.history.select','comments.save'):
                comparison['slow_path']=False
                comparison['improvement_pass']=None
            if comparison['path']=='comments.save':
                semantic=[]
                for side in ('baseline','candidate'):
                    path=a.comment_receipts/f"{side}-write-r{comparison['round']}-comments.json"
                    saved=json.loads(path.read_text())
                    if len(saved)!=10:raise ValueError('ten exact comment readbacks are required')
                    semantic.append([{key:row[key] for key in ('body','target_object_id','target_revision_id','anchor','status','version')} for row in saved])
                comparison['semantic_content_equal']=semantic[0]==semantic[1]
                comparison['content_hash_comparison']='not applicable: isolated writes have unique IDs and timestamps'
                comparison['target_300ms_pass']=None
    a.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    problems=[r for r in result['comparisons'] if r.get('complete') and (r.get('regression') or r.get('improvement_pass') is False or not r.get('semantic_content_equal',r.get('content_equal')) or r.get('target_300ms_pass') is False)]
    print(json.dumps({'cases':result['cases'],'failures':result['failures'],'complete_comparisons':sum(r['complete'] for r in result['comparisons']),'problems':problems},ensure_ascii=False))
    if a.require_complete and (result['failures'] or problems or not all(r['complete'] for r in result['comparisons'])):raise SystemExit(1)


if __name__=='__main__':main()
