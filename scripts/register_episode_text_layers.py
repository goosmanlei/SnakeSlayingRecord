#!/usr/bin/env python3
"""Register existing episode text as real external originals, without rendering.

Run only in a task's initialized private review instance. Source timing/content
comes from the exact film snapshot, not from a new transcript or generated text.
"""
import argparse
import copy
import io
import json
from pathlib import Path
import sys

from generation_workspace import generation_root, isolated_instance


def register(root, instance, output_id):
    from review_desk.store import Store, canonical
    from review_desk import editing as edit, editing_review as review, production as p, business_relations as relations
    from review_desk.production_media import ingest
    store = Store(instance/'.runtime/review.sqlite3')
    try:
        output = edit.read(store, output_id)
        project = output['payload']['project']
        sources = {s['id']:s for s in project['sources']}
        bindings = {key:review.binding(store, source) for key,source in sources.items()}
        _, items = review.elements(project)
        pictures = [e for e in items if e['element_type']=='clip' and e['track_key']=='track:picture']
        names = {'name-aheng':'new26-aheng', 'name-liji':'new26-liji', 'name-lixiao':'new26-lixiao', 'name-zhou':'new26-zhou',
                 'name-zhao':'new26-zhao', 'name-tao':'new26-tao'}
        groups = {}
        for item in items:
            if item['element_type']=='clip':
                item['binding']=bindings[item['source_id']]
                continue
            # An expression starts in its producing shot; an insert during the
            # same line is a use, not a second production origin.
            matches=[c for c in pictures if c['start_frame']<=item['start_frame']<c['end_frame']]
            if len(matches)!=1:
                raise ValueError('字层起点必须有一个真实承载镜头：'+item['element_id'])
            origin=bindings[matches[0]['source_id']]['origin']
            uses={bindings[c['source_id']]['origin']['object_id']:bindings[c['source_id']]['origin'] for c in pictures
                  if c['start_frame']<item['end_frame'] and c['end_frame']>item['start_frame']}
            entry={**item, 'entry_id':item['element_type']+'-'+item['element_id'],
                   'uses':list(uses.values()), 'identity_sources':[]}
            if item['element_id'] in names:
                person=p.record(store,names[item['element_id']])
                if item['title'].split('\n')[0]!=person['payload']['title']:
                    raise ValueError('人名条必须核对真实人物姓名')
                entry['identity_sources']=[review.ref(person)]
            groups.setdefault(origin['object_id'], {'origin':origin,'entries':[]})['entries'].append(entry)
        registrations=[]
        for owner,group in groups.items():
            shot=p.record(store,owner)
            document={'format':'episode-text-layer-v1','output':review.ref(output),
                      'snapshot':output['payload']['snapshot'],'project_digest':review.checksum(project),
                      'source_component':next(c for c in output['payload']['components'] if c['id']=='project'),
                      'spec':project['spec'],'origin':group['origin'],'entries':group['entries']}
            component=ingest(instance,io.BytesIO((canonical(document)+'\n').encode()),'text-layer.json')
            oid='text-layer-'+output['payload']['project']['episode']['object_id']+'-'+owner
            asset={'format':'production-asset-v1','title':shot['payload']['title']+' · 成片字层',
                   'material_category':'text-layer','media_type':'project','slot':'episode-text',
                   'scope':review.ref(shot),'subjects':[review.ref(shot)],'states':[],
                   'external_source':{'kind':'external','description':'从准确既有成片工程确定性提取的字层工程。文字和时间未修改；原成片渲染早于本次素材登记。',
                                      'output':review.ref(output),'source_component':document['source_component']},
                   'components':[component], 'text_layer':document,
                   'blocks':[{'id':entry['entry_id'],'text':entry['title']} for entry in group['entries']]}
            existing=store.db.execute('SELECT current_revision FROM objects WHERE id=?',(oid,)).fetchone()
            if existing:
                saved=p.record(store,oid)
                original=saved['payload'].get('text_layer')
                if original!=document:
                    component['id']='edition-'+output['id'][:12]
                    layers=copy.deepcopy(saved['payload'].get('text_layers',{'original':original}))
                    if component['id'] in layers and layers[component['id']]!=document:
                        raise ValueError('历史字层原件不一致；不得覆盖')
                    if component['id'] not in layers:
                        layers[component['id']]=document
                        expanded=copy.deepcopy(saved['payload']);expanded['text_layers']=layers
                        expanded['components'].append(component)
                        expanded['blocks'].extend({'id':component['id']+'-'+e['entry_id'],'text':e['title']} for e in group['entries'])
                        store.put_object(oid,'ASSET',expanded,saved['edit_token'],[{'revision_id':v['revision_id'],'role':role} for role,v in p.references(expanded)])
                        saved=p.record(store,oid)
            else:
                store.put_object(oid,'ASSET',asset,0,[{'revision_id':v['revision_id'],'role':role} for role,v in p.references(asset)])
                saved=p.record(store,oid)
            cid=store.db.execute('SELECT id FROM production_candidates WHERE asset_object_id=?',(oid,)).fetchone()[0]
            src={'asset':review.ref(saved),'candidate_id':cid,'component':component}
            uses={u['object_id']:u for e in group['entries'] for u in e['uses']}
            for use in uses.values():
                endpoints=[oid,use['object_id']]
                rid=relations.identity(endpoints)
                relation=relations.normalize({'format':'production-relation-v1','title':'字层在镜头中的使用', 'relation_type':'business',
                          'endpoints':endpoints,'direction':'forward','status':'active',
                          'sources':[review.ref(saved),review.ref(output)],
                          'contexts':[{k:use[k] for k in ('object_id','revision_id')}],
                          'blocks':[{'id':'usage','text':'此镜头使用该真实字层原件中的相交条目；具体文字、时间、条目和唯一制作出处以原件及准确成片关联为准。'}], 'summary':'此镜头使用该真实字层原件中的相交条目；具体文字、时间、条目和唯一制作出处以原件及准确成片关联为准。'})
                old=store.db.execute('SELECT 1 FROM objects WHERE id=?',(rid,)).fetchone()
                prior=p.record(store,rid) if old else None
                if not prior or prior['payload']!=relation:
                    store.put_object(rid,'RELATION',relation,prior['edit_token'] if prior else 0,[{'revision_id':v['revision_id'],'role':role} for role,v in p.references(relation)])
            for entry in group['entries']:
                item=next(e for e in items if review.element_key(e)==review.element_key(entry))
                item['binding']=review.binding(store,src,entry['entry_id'])
            registrations.append({'asset':review.ref(saved),'origin':group['origin'],'entries':len(group['entries']),
                                  'uses':list(uses.values()),'component':component})
        association={'format':review.FORMAT,'title':project['title']+' · 素材关联',
                     'output':review.ref(output),'version':1,'previous':None,'elements':items,
                     'note':'登记后追加的准确素材关联；不改变旧成片或声称旧渲染使用了事后登记的素材。'}
        association['digest']=review.checksum(association)
        association=review.append_association(store,association)
        editable=edit.read(store,'edit-'+project['episode']['object_id'])
        future=copy.deepcopy(editable['payload'])
        if all(future.get(k)==project.get(k) for k in ('clips','subtitles','titles','spec','sources')):
            for group,kind in [('subtitles','subtitle'),('titles','title')]:
                for entry in future.get(group,[]):
                    entry['material_ref']=next(e['binding'] for e in items if e['element_type']==kind and e['element_id']==entry['id'])
            editable=edit.save(store,instance,future,editable['version'])
        result={'output':review.ref(output),'association':review.ref(association),'association_digest':association['payload']['digest'],
                'subtitle_entries':len(project.get('subtitles',[])),'title_entries':len(project.get('titles',[])),
                'materials':registrations,'editable_project':review.ref(editable)}
        return result
    finally:
        store.close()


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--system',type=Path,required=True)
    parser.add_argument('--instance',type=Path,required=True)
    parser.add_argument('--output',required=True)
    parser.add_argument('--include-history',action='store_true')
    parser.add_argument('--report',type=Path,help='Task-scoped registration receipt; relative to the story worktree')
    args=parser.parse_args()
    root=generation_root(Path(__file__).resolve().parents[1])
    instance=isolated_instance(root,args.instance)
    sys.path.insert(0,str(args.system.resolve(strict=True)))
    result=register(root,instance,args.output)
    if args.include_history:
        from review_desk.store import Store
        from review_desk import editing as edit
        s=Store(instance/'.runtime/review.sqlite3')
        try: others=[o['object_id'] for o in edit.records(s,'EPISODE_FILM') if o['object_id']!=args.output and o['payload']['project']['episode']['object_id']=='new26-e01']
        finally:s.close()
        result['history']=[register(root,instance,oid) for oid in others]
    report=root/(args.report or Path('production/reports/task-20261019-0002/text-layer-registration.json'))
    report.parent.mkdir(parents=True,exist_ok=True)
    report.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='materials'},ensure_ascii=False))
