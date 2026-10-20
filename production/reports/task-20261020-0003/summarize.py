"""Recalculate comparisons from retained sequential samples; no service access."""
import json
from pathlib import Path
root=Path(__file__).parent/'evidence'
labels={'small_image':'小图签名 / 307','film_review':'成片 review','shot_entities':'单镜实体索引','shot_card':'镜头大卡','scene':'整场视听','materials':'全素材目录','editing_catalog':'完整成片目录 API','global_entities':'全局实体目录'}
for env,after in [('local','final-local-accepted.json'),('vps','final-vps.json')]:
 before=json.loads((root/('before-'+env+'.json')).read_text());after=json.loads((root/after).read_text())
 def value(data,name,condition,field='server_ms',stat='median'):
  return next(r for r in data['summary'] if r['workload']==name and r['condition']==condition)[field][stat]
 print('\n'+env+' (ms)\n|读取|暖态中位 前→后|暖态 P95 前→后|首次中位 前→后|评论后中位 前→后|\n|---|---:|---:|---:|---:|')
 for name,label in labels.items():
  cells=[label]
  for c,s in [('warm','median'),('warm','p95'),('first_build','median'),('after_comment','median')]:cells.append(f'{value(before,name,c,stat=s):.2f} → {value(after,name,c,stat=s):.2f}')
  print('|'+ '|'.join(cells)+'|')
 print('warm request-thread CPU median')
 for name in ('small_image','film_review'):
  b=value(before,name,'warm','server_thread_cpu_ms');a=value(after,name,'warm','server_thread_cpu_ms');print(name,f'{b:.3f} -> {a:.3f}; reduction {(b-a)/b*100:.2f}%')
