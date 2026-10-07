#!/usr/bin/env python3
"""Run one task validation process group with a measured resident-memory cap."""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import signal
import re
import shutil
import subprocess
import sys
import time


def resident_kib(pid):
    rows={}
    for line in subprocess.check_output(['ps','-axo','pid=,ppid=,rss='],text=True).splitlines():
        child,parent,rss=map(int,line.split());rows[child]=(parent,rss)
    owned={pid}
    while True:
        found={child for child,(parent,_) in rows.items() if parent in owned}
        if found<=owned:break
        owned.update(found)
    return sum(rows.get(child,(0,0))[1] for child in owned)


def stop_group(process):
    if process.poll() is not None:return
    try:os.killpg(process.pid,signal.SIGTERM)
    except ProcessLookupError:return
    try:process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        try:os.killpg(process.pid,signal.SIGKILL)
        except ProcessLookupError:pass
        process.wait(timeout=5)


def host_memory():
    if sys.platform!='darwin':return {}
    def run(*command):return subprocess.check_output(command,text=True,timeout=3)
    values=run('vm_stat')
    page=int(re.search(r'page size of (\d+)',values)[1])
    compressed=int(re.search(r'Pages occupied by compressor:\s+(\d+)',values)[1])*page
    swap=float(re.search(r'used = ([\d.]+)M',run('sysctl','vm.swapusage'))[1])*1024*1024
    pressure=int(run('sysctl','-n','kern.memorystatus_vm_pressure_level').strip())
    return {'pressure':pressure,'compressed_bytes':compressed,'swap_bytes':int(swap)}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--limit-mib',type=int,default=1024)
    parser.add_argument('--timeout-seconds',type=int,default=1800)
    parser.add_argument('--report',type=Path,required=True)
    parser.add_argument('--owned-container',help='exact newly created docker run --name target to stop on interruption')
    parser.add_argument('command',nargs=argparse.REMAINDER)
    args=parser.parse_args();command=args.command
    if command[:1]==['--']:command=command[1:]
    if not command or args.limit_mib<32:parser.error('command and at least 32 MiB required')
    if args.owned_container:
        if command[:2]!=['docker','run'] or '--name' not in command or command[command.index('--name')+1]!=args.owned_container:
            parser.error('owned container must match this docker run command')
        existing=subprocess.run(['docker','inspect',args.owned_container],capture_output=True,timeout=5)
        if existing.returncode==0:parser.error('container already exists; refuse ownership claim')
    if args.report.exists():parser.error('new report path required')
    args.report.parent.mkdir(parents=True,exist_ok=True)
    baseline=host_memory();latest=baseline;sample_at=0
    if baseline.get('pressure',1)>1:parser.error('host memory pressure elevated; high-resource validation not started')
    if shutil.disk_usage(args.report.parent).free<50*1024**3:parser.error('less than 50 GiB free; validation not started')
    process=subprocess.Popen(command,start_new_session=True)
    start=time.monotonic();peak=0;status=None
    try:
        while process.poll() is None:
            peak=max(peak,resident_kib(process.pid))
            if peak>args.limit_mib*1024:status='memory_limit_exceeded';break
            if time.monotonic()-start>args.timeout_seconds:status='time_limit_exceeded';break
            if time.monotonic()-sample_at>=5:
                latest=host_memory();sample_at=time.monotonic()
                if latest.get('pressure',1)>1:status='host_memory_pressure';break
                if latest.get('swap_bytes',0)-baseline.get('swap_bytes',0)>512*1024**2:status='host_swap_growth';break
                if latest.get('compressed_bytes',0)-baseline.get('compressed_bytes',0)>2*1024**3:status='host_compression_growth';break
                if shutil.disk_usage(args.report.parent).free<50*1024**3:status='disk_reserve';break
            time.sleep(.5)
        if status:
            stop_group(process)
        else:status='passed' if process.returncode==0 else 'failed'
    except BaseException:
        status='interrupted';stop_group(process)
        raise
    finally:
        container_state=None
        if args.owned_container:
            subprocess.run(['docker','stop','--time','1',args.owned_container],capture_output=True,timeout=5)
            observed=subprocess.run(['docker','inspect','--format','{{json .State}}',args.owned_container],capture_output=True,text=True,timeout=5)
            if observed.returncode==0:container_state=json.loads(observed.stdout)
        result={'format':'bounded-validation-run-v1','recorded_at':datetime.now(timezone.utc).isoformat(),
            'command':command,'status':status,'exit_code':process.returncode,'peak_rss_mib':round(peak/1024,2),
            'pid':process.pid,'host_before':baseline,'host_last_sample':latest,
            'owned_container':args.owned_container,'container_state':container_state,
            'limit_mib':args.limit_mib,'elapsed_seconds':round(time.monotonic()-start,2)}
        args.report.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(result,ensure_ascii=False),flush=True)
    raise SystemExit(0 if status=='passed' else 1)


if __name__=='__main__':main()
