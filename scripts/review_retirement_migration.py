"""Classify this story's exact old approvals and publish a minimal comment delta.

No generation, creative text edits or formal-service operations are performed
here. Unknown record shapes stop preparation for inspection.
"""
import argparse
import json
from pathlib import Path
import re
import sys
import uuid


def prepare(store):
    from review_desk import production as p, review_retirement as retirement
    rows = store.db.execute("SELECT r.*,o.kind,b.number FROM revisions r JOIN objects o ON o.id=r.object_id "
        "LEFT JOIN business_codes b ON b.object_id=o.id WHERE o.kind IN ('JUDGMENT','REPRESENTATION') ORDER BY r.id").fetchall()
    dispositions = {}
    for row in rows:
        body = json.loads(row['payload']); number = row['number']; rid = row['id']
        item = None
        if row['kind'] == 'REPRESENTATION':
            expected = {'blocks','choices','entities','format','media','review_model','sources','states','title','unknowns'}
            if set(body) != expected or body['review_model'] != 'entity-review-v1' or any(body[k] for k in ('media','sources','choices','unknowns')) or len(body['blocks']) != 1 or not re.fullmatch(r'本次送审包括.+的基础信息和全部 \d+ 个完整状态。当前未提交素材；旧候选尚未完成与完整状态的适配核对。', body['blocks'][0]['text']):
                raise ValueError('未分类的送审包装独有内容：'+row['object_id'])
            item = {'action':'delete','reason':'仅重复实体与完整状态的送审包装，无独有作品信息或意见。'}
        elif number in range(8,57):
            if body.get('actor') != 'Codex 技术命名复核' or body.get('verdict') != 'impact_resolved':
                raise ValueError('命名流程历史发生变化')
            item = {'action':'delete','reason':'仅对已退役状态的命名变更作流程消解；没有独有作品内容。'}
        elif number in (57,58):
            if body.get('reason') not in ('采纳阿禾当前版本：基础信息、1 个完整状态及页面列出的 0 份素材。','取消当前采纳，保留历史制作与意见。','重新认可原基础信息、完整状态与关联素材；不授予生成许可。'):
                raise ValueError('纯审批循环出现独有意见')
            item = {'action':'delete','reason':'批准、撤销、再批准的模板流程循环，无实际意见，不生成评论。'}
        elif body.get('actor') == 'Codex':
            target = p.ref_record(store,body['target'])
            if body['reason'] in json.dumps(target['payload'],ensure_ascii=False):
                item = {'action':'delete','reason':'同一 AI 技术说明已完整保留在准确原件正文，不复制评论。'}
            elif number in (1,4,5,6,7) and body['reason'] == '原件格式和返回字幕已核查；本会话不支持直接听辨，不能以字幕一致代替音色、咬字和演唱审阅。':
                item = {'action':'delete','reason':'通用待听审声明，无独有检查发现；原件规格与调用事实保持。'}
            elif number == 3:
                item = {'action':'import','reason':'保留独有的实际尺寸与画面检查说明。','body':body['reason'],
                    'source':{'author':'Codex','occurred_at':row['created_at'],'statement_kind':'ai_check',
                              'scope':'当时对这份准确造型候选的规格与视觉检查；不是用户意见或母版批准。'}}
        elif body.get('actor') == 'user':
            existing = body.get('user_feedback',{}).get('comment_id')
            if number == 150 and row['version'] == 2:
                existing = 'b8f1aa0f-e8fa-5575-87e8-0ae9e3e0504f'
            if existing:
                comment = store.comment(existing)
                if not comment or {'object_id':comment['target_object_id'],'revision_id':comment['target_revision_id']} != body['target']:
                    raise ValueError('原意见准确归属不一致')
                statement = body.get('user_feedback',{}).get('statement','唱腔中的词还是不对')
                if statement not in comment['body']:
                    raise ValueError('原意见正文未包含已核实的用户原话')
                item = {'action':'reuse','reason':'复用已有准确用户评论；仅追加旧记录来源，不重写正文、锚点、时间或状态。',
                    'comment_id':existing,'expected_comment':{k:comment[k] for k in ('target_object_id','target_revision_id','anchor','body','created_at','updated_at','version','status')},
                    'source':{'author':body['actor'],'occurred_at':comment['created_at'],'statement_kind':'verbatim',
                              'scope':'用户当时对这份准确录音的实际反馈；原意见及其范围保持。'}}
            elif body.get('evidence',{}).get('source') == 'user_conversation' and body['evidence'].get('reply'):
                evidence = body['evidence']
                scope = '当时固定审阅集合中的这份准确原件；不扩展到其他身份、派生候选、镜头效果或任务完成。'
                if number in range(79,113):
                    scope = '当时固定 35 份候选集合中的继续执行回复；保留与本原件的关联，不将未评论推断为质量认可。裹手布仍待修正。'
                elif number in (59,60,61,62):
                    scope = '仅针对这份准确原件作为母版；不代表其他身份、派生候选、镜头效果或任务完成。'
                item = {'action':'import','reason':'用户原话仅在旧记录中存在，迁入准确原件的历史评论。','body':evidence['reply'],
                    'source':{'author':body['actor'],'occurred_at':evidence['recorded_at'],'statement_kind':'verbatim',
                              'scope':scope,**{k:evidence[k] for k in ('file_sha256','question_item_id','audio_review','review_set') if k in evidence}}}
        if item is None:
            raise ValueError('未分类的决定修订：'+row['object_id']+' v'+str(row['version']))
        if item['action'] == 'import':
            item.update(comment_id=str(uuid.uuid5(uuid.NAMESPACE_URL,'review-retirement:'+rid)),target=body['target'],anchor={'type':'global'})
            store.validate_target(body['target']['object_id'],body['target']['revision_id'],item['anchor'])
        if item['action'] != 'delete':
            item['source']['source_code'] = 'DC'+str(number).zfill(3)
            if body.get('task'):item['source']['task']=body['task']
        dispositions[rid] = item
    retired = {r['id'] for r in rows}
    updates = []
    for row in p.current_records(store):
        if row['kind'] in ('JUDGMENT','REPRESENTATION','CALL'):continue
        paths = [path for path,ref in p.references(row['payload'],include_unavailable=True) if ref['revision_id'] in retired]
        if paths:
            if row['object_id'] != 'entity-boat-song' or paths != ['payload.song_work.diction_pilot_review.judgment']:
                raise ValueError('出现未核实的当前内容审批引用：'+row['object_id'])
            updates.append({'object_id':row['object_id'],'expected_revision':row['id'],'remove_paths':paths})
    return retirement.plan(store,dispositions,updates)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--system',type=Path,required=True)
    parser.add_argument('--database',type=Path,required=True)
    parser.add_argument('action',choices=('prepare','apply'))
    parser.add_argument('--plan',type=Path,required=True)
    args=parser.parse_args();sys.path.insert(0,str(args.system.resolve()))
    from review_desk.store import Store
    from review_desk import review_retirement
    store=Store.open_existing(args.database)
    try:
        if args.action=='prepare':
            document=prepare(store);args.plan.parent.mkdir(parents=True,exist_ok=True)
            args.plan.write_text(json.dumps(document,ensure_ascii=False,indent=2)+'\n')
            from collections import Counter
            print(json.dumps({'id':document['id'],'revisions':len(document['revisions']),'actions':dict(Counter(x['action'] for x in document['dispositions'].values()))}))
        else:
            print(json.dumps(review_retirement.apply(store,json.loads(args.plan.read_text())),ensure_ascii=False))
    finally:store.close()


if __name__=='__main__':main()
