#!/usr/bin/env python3
"""Compare exact shot material identity sets; read-only, no publishing."""
import argparse,hashlib,json,sys
from pathlib import Path
parser=argparse.ArgumentParser();parser.add_argument('--system',type=Path,required=True);parser.add_argument('--instance',type=Path,required=True);parser.add_argument('--baseline',type=Path,required=True);parser.add_argument('--output',type=Path,required=True);a=parser.parse_args()
sys.path.insert(0,str(a.system.resolve()))
from review_desk.store import Store
from review_desk import ui_projection as u,production_breakdown as b
s=Store(a.instance/'.runtime/review.sqlite3');before=json.loads(a.baseline.read_text());result=[];errors=[]
for sid,scene in before.items():
 data=u.scene(s,sid,scene['revision']);actual={x['record']['object_id']:x for x in data['shots']}
 if set(actual)!=set(scene['shots']):errors.append({'scene':sid,'reason':'shot set changed'})
 for oid,expected in scene['shots'].items():
  shot=actual[oid];items=shot['context']['materials'];ids=[m['canonical_material_id'] for m in items]
  grouped={}
  for m in items:grouped.setdefault(m['classification']['key'],[]).append(m['canonical_material_id'])
  flat=[mid for values in grouped.values() for mid in values]
  if set(ids)!=set(expected['materials']) or len(ids)!=len(set(ids)) or sorted(ids)!=sorted(flat):errors.append({'shot':oid,'reason':'material set changed or duplicated'})
  if shot['record']['id']!=expected['revision']:errors.append({'shot':oid,'reason':'revision drift'})
  result.append({'shot':oid,'revision':expected['revision'],'material_ids':ids,'groups':grouped})
report={'scenes':len(before),'shots':len(result),'associations':sum(len(v['material_ids']) for v in result),'errors':errors,'results':result}
a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='results'}));s.close()
if errors:raise SystemExit(1)
