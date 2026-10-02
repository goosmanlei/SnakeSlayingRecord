#!/usr/bin/env python3
"""Compile reviewed direct relationships against the locked complete screenplay.

This is story data, not a generic extraction engine. Each authored relationship
uses an authored, exact block selection. Mere scene co-occurrence is never an edge.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
# from | to | relationship | category; exact evidence lives in the selection file
# Parent/child and ownership arrows read from left to right. Phase-specific
# operations carry their verified scene, while stable relations apply globally.
SPEC_TEXT='''
li-dan|li-ji|父亲与女儿|personal
li-mother|li-ji|母亲与女儿|personal
li-xiao|li-ji|五姐与妹妹|personal
li-dan|li-xiao|父亲与女儿|personal
heng-mother|a-heng|母亲与女儿|personal
tao|a-he|父亲与女儿|personal
xiaoman-mother|xiao-man|母亲与女儿|personal
ticket-woman|ticket-child|母亲与孩子|personal
li-ji|a-heng|相互照应|personal
a-he|a-heng|曾教她翻花绳|personal
sun-liu|a-heng|教过她数拍|personal
li-xiao|a-heng|安排洗幕布工作|personal
a-heng|mo-er|掰饼喂食|use
li-dan|sun-liu|共同做工的旧交|personal
li-mother|heng-mother|照料病人|personal
neighbor-woman|heng-mother|协助照料|personal
singer-teacher|a-heng|教唱并核清缺词|personal
zhou|a-heng|安排唱活并付米|personal
zhao|a-heng|以领唱招募并胁迫入祭|personal
priest|a-heng|点名入祭|personal
boatman|a-heng|拒绝载母女出走|personal
old-woman|thin-girl|带领同行|personal
offscreen-caller|li-ji|窗外呼唤归家|personal
li-ji|mo-er|照顾并喂食|personal
li-xiao|troupe-workers|参与同一戏班制作演出|personal
sun-liu|troupe-workers|参与同一戏班演出|personal
li-dan|li-home|一家住所|spatial
li-mother|li-home|一家住所|spatial
li-ji|li-home|一家住所|spatial
li-xiao|li-home|一家住所|spatial
a-heng|heng-home|母女住所|spatial
heng-mother|heng-home|母女住所|spatial
a-heng|li-home|暂住与归家吃饭|spatial
heng-mother|li-home|搬来养病|spatial
zhou|rice-shop|经营米铺|ownership
tao|bamboo-stall|经营竹器摊|ownership
singer-teacher|singer-yard|院中教唱|spatial
boatman|ferry|在渡口接洽乘船|spatial
rice-shop|river-street|临河街开门|spatial
bamboo-stall|river-street|位于对街|spatial
prop-house|shallows|门前浅滩|spatial
prop-house|drying-area|门外洗晾幕布|spatial
temple-front|temple-grain|院东门通往粮仓|spatial
temple-back|feeding-channel|院内封闭石道|spatial
feeding-channel|feeding-door|南端投食入口|spatial
feeding-channel|cave-gate|北端通山洞|spatial
temple-front|hill-steps|沿石阶下山|spatial
troupe-workers|prop-house|存放并制作道具|use
troupe-workers|village-yard|参与搭台与散戏|performance
yard-audience|village-yard|观看演出|performance
rice-listeners|a-heng|听曲并回应|performance
woodcutter|a-heng|听曲并发现省段|performance
temple-children|paper-snake|观看纸蛇戏|performance
lead-chorus|snake-welcome-song|共同领唱|performance
a-heng|boat-song|演唱跳段版本|performance
a-heng|blue-awning-song|从缺词到补全演唱|performance
singer-teacher|blue-awning-song|补唱并核清末词|performance
heng-mother|songbook|逐句哼曲供抄写|performance
a-heng|songbook|抄写并持有|ownership
blue-awning-song|songbook|歌词记入歌本|use
snake-welcome-song|lead-lyrics|领唱歌词载于旧纸|use
zhao|lead-lyrics|交出领唱旧词|use
troupe-workers|blessing-stage-song|祈福戏唱段|performance
a-heng|snake-welcome-song|在前殿领唱|performance
blue-awning-song|xu-bride|婚事所需唱曲|performance
a-heng|rice-bag|携带唱曲所得米|ownership
zhou|rice-measure|量米付唱工|use
rice-measure|grain|计量米粮|use
rice-bag|grain|盛装米粮|use
songbook|book-basket|搁在倒扣竹篮上|spatial
river-stone|songbook|压住摊开的书页|use
woodcutter|carrying-pole|听曲时持扁担|use
a-heng|water-flask|倒水蘸湿布巾|use
water-flask|cloth|倒水蘸湿|use
li-ji|cloth|擦净手上浆糊|use
li-ji|paste-wool|劳作后手上附着|use
mo-er|cake|吃女孩留下的饼|use
zhao|keys|收缴前腰间持有|ownership
officer-cheng|keys|验院后收走|ownership
tao|bamboo-basket|编削篮口|use
tao|shaving-knife|削竹用刀|use
bamboo-stall|empty-stool|摊旁留有空位|spatial
river-street|street-laundry|沿街民居晾衣|spatial
prop-house|curtain|屋外挂幕布|spatial
sun-liu|stage-drum|为纸蛇戏配鼓|performance
sun-liu|waist-drum|用腰鼓招呼邻里|use
troupe-workers|paper-snake|制作与操演|use
paper-snake|paper-moon|蛇口吞吐纸月亮|use
li-ji|paper-moon|持牵线操演|use
troupe-workers|stage-tools|搭台与收拾|use
temple-tall|red-rope|从戏班借用|use
red-rope|name-plaque|绑缠祭名木牌|use
name-plaque|a-heng|牌上记祭名|use
li-ji|name-plaque|抢扯时受伤|use
heng-mother|debt-note|借粮时按手印|use
zhao|debt-overlay|篡改借据贴纸|use
debt-overlay|debt-note|贴于原据手印前|spatial
a-heng|work-ledger|记录两天唱工|use
clerk-liang|evidence-receipt|收证后出具|use
a-heng|evidence-receipt|持凭记说明证据已交|use
ticket-woman|grain-ticket|询问凭票领粮|use
ticket-elder|grain-ticket|听告示后展开粮票|use
magistrate|stop-order|准许停祭与除蛇|use
officer-cheng|stop-order|持文书索取原祭册|use
county-office|volunteer-notice|照壁张贴应募告示|spatial
clerk-notice|volunteer-notice|解说应募条件|use
li-ji|old-lantern|携灯并照归家路|use
li-mother|old-lantern|交给女儿|use
li-ji|bandage|手掌包扎|use
li-ji|wood-knife|劈柴磨破掌心|use
li-ji|heavy-blade|持厚背刀斩蛇|use
li-dan|heavy-blade|示范沿缝落刀|use
sun-liu|carrying-strap|提供补缝背带|ownership
li-dan|carrying-strap|背病人时使用|use
heng-mother|medicine-pot|病中服药所需|use
heng-home|rice-urn|灶边米缸|spatial
stonemason|feeding-channel|改外段石盖刀缝|use
gate-pin|cave-gate|闸落底后穿栓固定|use
crossbeam|cave-gate|绑接后持续压闸|use
tao|hemp-rope|提供麻绳并提醒护角|ownership
sun-liu|hemp-rope|加旧布护垫|use
hemp-rope|crossbeam|捆扎压杠并护角|use
helpers-four|crossbeam|四名乡亲合力压杠|use
sun-liu|crossbeam|西侧压杠|use
li-xiao|crossbeam|西侧压杠|use
officer-cheng|crossbeam|东侧压杠|use
li-dan|crossbeam|临危加入东侧压杠|use
elders-two|temple-back|守门道并找帮手|use
meat-rice-bait|bait-basin|盛在饵盆内|use
bait-basin|feeding-channel|推入南门至刀缝以南|spatial
snake|meat-rice-bait|沿石道进食|use
li-ji|snake|在闸与刀缝限制内斩蛇|use
li-dan|channel-plan|收存并使用通道图|use
li-xiao|channel-plan|补出刀缝说明站位|use
zhou|grain-order|保留提前备粮证据|use
delivery-worker|grain-order|指认送单日期|use
order-writer|grain-order|认下原单笔迹|use
li-dan|grain-copy|抄录原单日期内容|use
zhou|shop-ledger|提供店账作证|ownership
officer-second|evidence-chest|看守封存证据|use
sacrificial-registers|a-he|旧祭册记名|use
sacrificial-registers|xiao-man|旧祭册记名|use
sacrificial-registers|a-heng|当年祭册记名|use
magistrate|approval-orders|前两次准祭签押|use
a-he|hairpin|遗物竹簪|ownership
xiao-man|broken-comb|遗物断梳|ownership
tao|petition|具状要求复查|use
clerk-proclamation|public-verdict|宣读复查结果|use
public-verdict|a-he|确认非自愿被迫献祭|use
public-verdict|xiao-man|确认非自愿被迫献祭|use
public-verdict|a-heng|销去祭名|use
new-steward|cleared-debt-receipt|清账并退粮|use
a-heng|cleared-debt-receipt|带回清账凭据|use
cleared-debt-receipt|songbook|凭据夹入歌本|spatial
copied-pages|songbook|补页装订并保留旧页|use
li-ji|writing-board|记词交歌娘核对|use
li-home|family-meal|归家聚餐|spatial
'''


def compile_relations(store,p):
    screenplay_path=ROOT/'imports/screenplay-04.json'
    source_hash=hashlib.sha256(screenplay_path.read_bytes()).hexdigest()
    lock=json.loads((ROOT/'production/source-lock.json').read_text())
    if source_hash!=lock['screenplay']['file_sha256']:raise ValueError('locked screenplay changed')
    rows=p.current_records(store);entities={r['object_id'].removeprefix('entity-'):r for r in rows if r['kind']=='ENTITY'}
    scene_index={}
    for episode in json.loads(screenplay_path.read_text())['episodes']:
        expected=next(r for r in lock['episodes'] if r['object_id']==episode['id']);ep=p.ref_record(store,expected)
        if ep['current_revision']!=ep['id']:raise ValueError('locked episode has a newer revision; review input before proceeding')
        blocks={b['id']:b for b in ep['payload']['blocks']}
        for scene in ep['payload']['scenes']:scene_index[scene['id']]=(ep,scene,[blocks[b] for b in scene['block_ids']])
    selections=json.loads((ROOT/'production/relationship-evidence-selection.json').read_text())['relations']
    expected_ids={'relationship-'+ '-'.join([line.split('|')[0],line.split('|')[1],line.split('|')[3]]) for line in SPEC_TEXT.strip().splitlines()}
    if set(selections)!=expected_ids:raise ValueError('evidence selection must cover each authored relationship exactly once')
    result=[];evidence=[]
    stable_labels={'父亲与女儿','母亲与女儿','五姐与妹妹','母亲与孩子','共同做工的旧交','一家住所','母女住所','经营米铺','经营竹器摊','临河街开门','位于对街','门前浅滩','院东门通往粮仓','院内封闭石道','南端投食入口','北端通山洞','灶边米缸','遗物竹簪','遗物断梳'}
    for line in SPEC_TEXT.strip().splitlines():
        left,right,label,category=line.split('|')
        oid=f'relationship-{left}-{right}-{category}'
        selection=selections[oid];label=selection.get('label',label)
        sources=[];excerpts=[]
        for selected in selection['sources']:
            ep,scene,blocks=scene_index[selected['scene_id']]
            ids=selected['blocks']
            if not ids or len(ids)!=len(set(ids)):raise ValueError('distinct explicit evidence blocks required: '+oid)
            by_number={int(b['id'].rsplit('b',1)[1]):b for b in blocks}
            if any(i not in by_number for i in ids):raise ValueError('evidence block outside selected scene: '+oid)
            excerpt=[by_number[i] for i in ids]
            sources.append({'object_id':ep['object_id'],'revision_id':ep['id'],'scene_id':scene['id'],'block_ids':[b['id'] for b in excerpt]})
            excerpts.append({'scene_id':scene['id'],'heading':scene['heading'],'text':'\n'.join(b['text'] for b in excerpt)})
        source=sources[0]
        a,b=entities[left],entities[right]
        title=f'{a["payload"]["title"]} · {label} · {b["payload"]["title"]}'
        payload={'format':'production-relation-v1','relation_type':'entity','title':title,
                 'blocks':[{'id':'relationship','text':f'{a["payload"]["title"]} — {label} {"↔" if label in ("相互照应","共同做工的旧交") else "→"} {b["payload"]["title"]}。'}],
                 'entities':[{'object_id':r['object_id'],'revision_id':r['id']} for r in (a,b)],
                 'label':label,'direction':'mutual' if label in ('相互照应','共同做工的旧交') else 'forward','category':category,'basis':'script','sources':sources,
                 'applies_to':[] if label in stable_labels else sources}
        try:old=p.record(store,oid)
        except KeyError:old=None
        if not old or old['payload']!=payload:result.append({'object_id':oid,'kind':'RELATION','expected_version':old['version'] if old else 0,'payload':payload})
        evidence.append({'id':oid,'title':title,'source':source,'sources':sources,'excerpts':excerpts,'excerpt':'\n\n'.join(e['heading']+'\n'+e['text'] for e in excerpts), 'selection_reason':selection.get('reason','原文直接支撑，保留已核对范围。')})
    if len({r['id'] for r in evidence})!=len(evidence):raise ValueError('duplicate relationship identity')
    connected={oid for row in result for oid in [r['object_id'] for r in row['payload']['entities']]}
    existing={r['object_id'] for r in rows if r['kind']=='RELATION' and r['payload'].get('relation_type')=='entity'}
    for row in rows:
        if row['object_id'] in existing:connected.update(r['object_id'] for r in row['payload']['entities'])
    checks=[{'entity_id':r['object_id'],'title':r['payload']['title'],'result':'已登记直接关系' if r['object_id'] in connected else '已检查；当前仅登记出场身份，不根据同场出现补造直接关系'} for r in entities.values()]
    heads={r['object_id']:r['id'] for r in rows if r['kind'] in ('ENTITY','RELATION','INPUT_LOCK')}
    heads.update({r['object_id']:r['revision_id'] for r in lock['episodes']})
    doc={'format':'production-import-v1','expected_heads':heads,'records':result}
    return {'format':'entity-relationships-batch-v1','source_sha256':source_hash,'document':doc,'evidence':evidence,'entity_checks':checks,
            'summary':{'entities_checked':len(checks),'relationships':len(evidence),'entities_with_relationships':len(connected),'changes':len(result)}}


def main():
    cli=argparse.ArgumentParser(description=__doc__);cli.add_argument('command',choices=['plan','apply']);cli.add_argument('--system',type=Path,required=True);cli.add_argument('--instance',type=Path,required=True);cli.add_argument('--file',type=Path,required=True);args=cli.parse_args()
    sys.path.insert(0,str(args.system.resolve()))
    from review_desk.store import Store
    from review_desk import production as p
    store=Store(args.instance.resolve()/'.runtime/review.sqlite3')
    try:
        if args.command=='plan':
            value=compile_relations(store,p)
            if value['document']['records']:p.import_records(store,value['document'],validate_only=True)
            args.file.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n');print(json.dumps(value['summary'],ensure_ascii=False))
        else:
            value=json.loads(args.file.read_text());fresh=compile_relations(store,p)
            if value!=fresh:raise ValueError('relationship source or current versions changed; prepare again')
            print(json.dumps(p.import_records(store,value['document']) if value['document']['records'] else {'no_changes':True}))
    finally:store.close()


if __name__=='__main__':main()
