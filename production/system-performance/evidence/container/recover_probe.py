from pathlib import Path
import json,hashlib,sqlite3,subprocess,time,urllib.request,urllib.error,datetime
r=Path(__file__).resolve().parent
res=json.loads((r/'resources.json').read_text());container=res['container_id'];instance=Path(res['instance']);dbpath=instance/'.runtime/review.sqlite3'
receipt={'at':datetime.datetime.now().astimezone().isoformat(),'candidate':res['candidate'],'image':res['image'],'stages':[]}
def save(): (r/'recovery.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
def command(args):return subprocess.check_output(args,text=True).strip()
def record(name,**result):receipt['stages'].append({'name':name,**result});save()
def call(path,port=62516,headers={}):
 request=urllib.request.Request(f'http://127.0.0.1:{port}'+path,headers=headers)
 try:response=urllib.request.urlopen(request,timeout=45)
 except urllib.error.HTTPError as e:response=e
 with response:return response.status,dict(response.headers),response.read()
def ready(port):
 for attempt in range(40):
  try:
   s,_,b=call('/api/instance',port);assert s==200;return json.loads(b)
  except (OSError,AssertionError):time.sleep(.25)
 raise RuntimeError('server not ready')
def business():
 d=sqlite3.connect(dbpath.as_uri()+'?mode=ro',uri=True);d.execute('BEGIN');h=hashlib.sha256();counts={}
 for table, in d.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' AND name!='read_generations' ORDER BY name"):
  h.update(table.encode());counts[table]=0
  for row in d.execute('SELECT * FROM "'+table+'" ORDER BY rowid'):
   h.update(json.dumps(row,ensure_ascii=False,separators=(',',':')).encode());h.update(b'\n');counts[table]+=1
 d.close();return {'sha256':h.hexdigest(),'counts':counts}
paths=['/api/production/card?object_id=need-shot-e01-021-sound-reference','/api/comments']
def contents(port=62516):
 out={}
 for path in paths:
  start=time.perf_counter();status,headers,body=call(path,port);assert status==200,(path,status,body[:150]);value=json.loads(body);out[path]={'sha256':hashlib.sha256(json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest(),'bytes':len(body),'wall_ms':(time.perf_counter()-start)*1000}
 return out
def same(a,b):assert {k:v['sha256'] for k,v in a.items()}=={k:v['sha256'] for k,v in b.items()}
inspection=json.loads(command(['docker','inspect',container]))[0];assert inspection['Config']['Labels']['codex.task']=='task-20261006-0005';ready(62516)
before=business();record('before',business=before)
base=contents();record('initial',responses=base)
status=json.loads(command(['docker','exec',container,'python','-m','review_desk','--instance','/instance','read-cache','status']))
cleared=json.loads(command(['docker','exec',container,'python','-m','review_desk','--instance','/instance','read-cache','clear']))
assert cleared['entries']==0 and cleared['generation']!=status['generation'];after=contents();same(base,after);record('online-clear',before=status,cleared=cleared,responses=after)
command(['docker','restart',container]);ready(62516);after=contents();same(base,after);record('restart',responses=after)
command(['docker','stop',container])
for name,image,disabled in [('disabled',res['image'],True),('previous-code','sha256:6fab456861dea401671c1673860ce43fb07c7b8230af1bc863c8e0608bb7931c',False)]:
 config=instance/'config/instance.json';old=config.read_bytes()
 if name=='previous-code':
  value=json.loads(old);value['review_desk_commit']='bc31d7dc424ccec1328926cc034a67f4be579fcf';config.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
 args=['docker','run','-d','--name','task-20261006-0005-recovery','--label','codex.task=task-20261006-0005','--cpus','4','--memory','2g','--pids-limit','128','-p','127.0.0.1:62517:8765','-v',str(instance)+':/instance']
 if disabled:args+=['-e','REVIEW_READ_CACHE=0']
 cid=command(args+[image,'python','-m','review_desk','--instance','/instance','serve','--host','0.0.0.0','--port','8765']);record(name+'-created',container=cid,image=image)
 try:
  ready(62517);after=contents(62517);same(base,after);record(name,responses=after,business=business())
 finally:
  command(['docker','stop',cid]);command(['docker','rm',cid]);config.write_bytes(old);record(name+'-removed',container=cid)
cache=instance/'.runtime/read-cache.sqlite3';size=cache.stat().st_size;cache.unlink();record('remove-disposable-cache',path=str(cache),bytes=size,absent=not cache.exists())
command(['docker','start',container]);ready(62516);after=contents();same(base,after);final=business();assert final==before;record('empty-cache-rebuild',responses=after,cache_recreated=cache.exists(),business=final)
media='a7d678681c2e490de0a7dc8aca163131f68e196ceda703dc9c9282418c589272.wav';path='/api/production/files/'+media
s,h,original=call(path);assert s==200;assert hashlib.sha256(original).hexdigest()==media.split('.')[0];etag=h['ETag'];checks=[]
for headers,status,start,end in [({'Range':'bytes=0-1023'},206,0,1024),({'Range':'bytes=-513'},206,len(original)-513,len(original)),({'Range':'bytes=0-1023','If-Range':'"wrong"'},200,0,len(original))]:
 s,h,b=call(path,headers=headers);assert s==status and b==original[start:end];checks.append({'request':headers,'status':s,'bytes':len(b),'content_range':h.get('Content-Range'),'sha256':hashlib.sha256(b).hexdigest()})
s,h,b=call(path,headers={'If-None-Match':etag});assert s==304 and not b;checks.append({'request':{'If-None-Match':etag},'status':s,'bytes':len(b)})
s,h,b=call(path,headers={'Range':'bytes='+str(len(original))+'-'});assert s==416;checks.append({'request':'out-of-range','status':s})
for path in ['/api/production/files/../review.sqlite3','/api/production/files/%2e%2e%2freview.sqlite3','/api/production/files/not-a-digest.wav']:
 s,h,b=call(path);assert s in (400,404);checks.append({'request':path,'status':s})
record('actual-media-range',media=media,bytes=len(original),etag=etag,checks=checks)
print(json.dumps({'stages':len(receipt['stages']),'business_equal':True,'responses_equal':True,'media_ok':True}))
