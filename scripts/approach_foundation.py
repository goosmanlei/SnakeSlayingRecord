#!/usr/bin/env python3
"""Project reading routes and append missing professional sources without rewriting history."""
import argparse
import copy
import json
import re
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]


def heading_slug(text):
    return re.sub(r'[^\w\-\s]', '', text.lower()).strip().replace(' ', '-')


def reading_routes(root=ROOT):
    from sync_video_handbook import derive
    from sync_filmcraft import FILES, section_id, anchor_id, source_catalog
    video = derive((root/'production/seedance-video-handbook.md').read_bytes(), root)
    routes = {}
    def entry(file, node, section=''):
        return {'category':'resource','object':'method.resource.'+('video-handbook' if node=='video-plan' else 'filmcraft-execution'),
                'node':'method.skill.'+node,'file':file, 'section':section}
    default = entry('references/handbook.md','video-plan')
    anchors = {'approach-video-handbook-'+s['id']: {**default,'section':s['id']} for s in video['sections']}
    routes['video-handbook'] = {'default':default,'anchors':anchors}
    anchors = {}
    for name in FILES:
        body = source_catalog(root)[0].decode() if name=='sources.md' else (root/'production/filmcraft'/name).read_text()
        sid = section_id(name)
        file = 'production/filmcraft/'+name
        value = entry(file,'story-structure')
        anchors['approach-filmcraft-'+sid] = value
        for line in body.splitlines():
            if re.match(r'#{2,3} ',line):
                title=line.split(' ',1)[1]
                anchors['approach-filmcraft-'+anchor_id(sid,title)] = {**value,'section':heading_slug(title)}
    routes['filmcraft'] = {'default':entry('production/filmcraft/README.md','story-structure'),'anchors':anchors}
    return routes


def project_document(original, root=ROOT):
    tabs={t['id']:copy.deepcopy(t) for t in original['tabs']}
    for key in ('story','materials'):
        diagram=tabs[key]['sections'][0]['diagram']
        for node in diagram['nodes']:node.pop('href',None)
        diagram['methods']=[]
        if key=='materials':diagram['note']='';diagram['feedback']['label']=''
    def page(id,label):
        return {'id':id,'label':label,'title':label,'lead':'','sections':[]}
    return {**original,'tabs':[tabs['vision'],page('model','数据模型'),page('foundation','基础流程'),tabs['story'],tabs['materials']],
            'reading_routes':reading_routes(root)}


def synchronize(root=ROOT, check=False):
    path = root/'content/production-approach.json'
    original=json.loads(path.read_text())
    result=project_document(original,root)
    if check:
        if result!=original:raise ValueError('制作思路及旧阅读路由未与唯一源同步')
    else:path.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    return {'tabs':[t['id'] for t in result['tabs']], 'legacy_anchors':sum(len(r['anchors']) for r in result['reading_routes'].values())}


def _update_methods(store, root=ROOT):
    from review_desk import methods
    previous=methods.read(store,'method.resource.filmcraft-execution')
    payload=previous['payload']
    spec={'name':'filmcraft-execution','title':payload['title'],'preserve_paths':True,'expected_version':previous['version'],
          'sections':{key:{k:v for k,v in payload['source']['files'][path].items() if k in ('path','section')} for key,path in payload['sections'].items()},
          'companions':copy.deepcopy(payload.get('companions',{}))}
    spec['sections']['applications']={'path':'production/filmcraft/applications.md'}
    spec['sections']['video-handbook']={'path':'production/seedance-video-handbook.md'}
    # Chapter delivery needs its diagrams and readable citations. Other chapters
    # remain exact link targets in the same resource, not implicit dependencies.
    spec['companions']={section:[name for name in names
                                if name.endswith('.svg') or name=='production/filmcraft/sources.md']
                        for section,names in spec['companions'].items()}
    for section in ('applications','guide','quick-reference','sources'):
        spec['companions'].pop(section,None)
    for section in ('applications','guide'):
        spec['companions'][section]=['production/source-lock.json']
    new=methods.sync_source(store,root,spec)
    resources={new['object_id']:new}
    changes={previous['object_id']:{'before':previous['revision_id'],'after':new['revision_id']}} if previous['revision_id']!=new['revision_id'] else {}
    video=methods.read(store,'method.resource.video-handbook')
    payload=video['payload']
    source={'name':'video-handbook','title':payload['title'],'expected_version':video['version'],
            'preserve_paths':False,'sections':{}}
    for section,file in payload['sections'].items():
        source['sections'][section]={k:v for k,v in payload['source']['files'][file].items() if k in ('path','section')}
    current=methods.sync_source(store,root,source)
    resources[current['object_id']]=current
    if video['revision_id']!=current['revision_id']:
        changes[video['object_id']]={'before':video['revision_id'],'after':current['revision_id']}
    catalog=methods.catalog(store)
    active={rule['object_id'] for binding in catalog['binding'] for rule in binding['payload']['rules']}
    saved={}
    for row in catalog['skill']:
        if row['object_id'] not in active:continue
        p=copy.deepcopy(row['payload'])
        for ref in p.get('resources',[]):
            if ref['object_id'] in resources:ref['revision_id']=resources[ref['object_id']]['revision_id']
        if p!=row['payload']:
            updated=methods.save(store,{'category':'skill','name':row['object_id'].removeprefix('method.skill.'),'expected_version':row['version'],'payload':p})
            saved[row['object_id']]=updated
            changes[row['object_id']]={'before':row['revision_id'],'after':updated['revision_id']}
    for row in catalog['binding']:
        p=copy.deepcopy(row['payload'])
        for rule in p['rules']:
            if rule['object_id'] in saved:rule['revision_id']=saved[rule['object_id']]['revision_id']
        if p!=row['payload']:
            updated=methods.save(store,{'category':'binding','name':row['object_id'].removeprefix('method.binding.'),'expected_version':row['version'],'payload':p})
            changes[row['object_id']]={'before':row['revision_id'],'after':updated['revision_id']}
    return changes


def update_methods(store, root=ROOT):
    # Build against a method-only copy first; malformed source or later binding
    # failures cannot leave an earlier method enabled on the actual instance.
    import tempfile
    from review_desk.store import Store
    try:
        from .method_migration import configuration_registry, restore_configuration
    except ImportError:
        from method_migration import configuration_registry, restore_configuration
    with tempfile.TemporaryDirectory(prefix='approach-methods-') as directory:
        staged=Store(Path(directory)/'review.sqlite3')
        try:
            restore_configuration(staged,configuration_registry(store))
            result=_update_methods(staged,root)
            restore_configuration(store,configuration_registry(staged))
            return result
        finally:staged.close()


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check',action='store_true')
    parser.add_argument('--system',type=Path)
    parser.add_argument('--instance',type=Path)
    args=parser.parse_args()
    result={'reading':synchronize(check=args.check)}
    if args.instance:
        sys.path.insert(0,str(args.system.resolve()))
        from review_desk.store import Store
        store=Store.open_existing(args.instance/'.runtime/review.sqlite3')
        try:result['methods']=update_methods(store)
        finally:store.close()
    print(json.dumps(result,ensure_ascii=False))
