#!/usr/bin/env python3
"""Compile reviewed direct relationships against the locked complete screenplay.

This is story data, not a generic extraction engine. Each authored relationship
names an explicit evidence phrase. Mere scene co-occurrence is never an edge.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT=Path(__file__).resolve().parents[1]
# from | to | relationship | category | evidence scene | evidence regex
# Parent/child and ownership arrows read from left to right. Phase-specific
# operations carry their verified scene, while stable relations apply globally.
SPEC_TEXT='''
li-dan|li-ji|父亲与女儿|personal|s014|爹，我想报名
li-mother|li-ji|母亲与女儿|personal|s027|旧灯递给女儿
li-xiao|li-ji|五姐与妹妹|personal|s003|李绡让妹妹
li-dan|li-xiao|父亲与女儿|personal|s033|李绡：两头分开了。爹
heng-mother|a-heng|母亲与女儿|personal|s010|阿蘅母亲：不去
tao|a-he|父亲与女儿|personal|s036|回头叫我
xiaoman-mother|xiao-man|母亲与女儿|personal|s036|小满母亲：小满
ticket-woman|ticket-child|母亲与孩子|personal|s008|抱孩子
li-ji|a-heng|相互照应|personal|s036|在廊口接住她的手
a-he|a-heng|曾教她翻花绳|personal|s002|她还教过我翻花绳
sun-liu|a-heng|教过她数拍|personal|s008|这还是您教我的
li-xiao|a-heng|安排洗幕布工作|personal|s005|李绡数出洗布的工钱
a-heng|mo-er|掰饼喂食|use|s002|阿蘅掰下一小角喂它
li-dan|sun-liu|共同做工的旧交|personal|s014|她爹跟我、孙六
li-mother|heng-mother|照料病人|personal|s016|你娘醒了，我在这儿
neighbor-woman|heng-mother|协助照料|personal|s015|邻妇
singer-teacher|a-heng|教唱并核清缺词|personal|s039|歌娘：认
zhou|a-heng|安排唱活并付米|personal|s001|我替你应下了
zhao|a-heng|以领唱招募并胁迫入祭|personal|s006|进庙领唱
priest|a-heng|点名入祭|personal|s008|巫祝转过牌面
boatman|a-heng|拒绝载母女出走|personal|s011|我不敢载
old-woman|thin-girl|带领同行|personal|s012|女孩
offscreen-caller|li-ji|窗外呼唤归家|personal|s040|窗外有人叫她回家
li-ji|mo-er|照顾并喂食|personal|s002|墨耳
li-xiao|troupe-workers|参与同一戏班制作演出|personal|s003|台架
sun-liu|troupe-workers|参与同一戏班演出|personal|s008|鼓声
li-dan|li-home|一家住所|spatial|s014|李诞
li-mother|li-home|一家住所|spatial|s027|李寄母亲
li-ji|li-home|一家住所|spatial|s042|门槛
li-xiao|li-home|一家住所|spatial|s042|领妹妹回家
a-heng|heng-home|母女住所|spatial|s010|母亲
heng-mother|heng-home|母女住所|spatial|s007|阿蘅母亲靠在床边
a-heng|li-home|暂住与归家吃饭|spatial|s034|阿蘅
heng-mother|li-home|搬来养病|spatial|s026|李家里屋
zhou|rice-shop|经营米铺|ownership|s001|周掌柜提着小木斗
tao|bamboo-stall|经营竹器摊|ownership|s002|陶伯
singer-teacher|singer-yard|院中教唱|spatial|s039|院中晾着演出衣
boatman|ferry|在渡口接洽乘船|spatial|s011|船家
rice-shop|river-street|临河街开门|spatial|s001|河街的米铺
bamboo-stall|river-street|位于对街|spatial|s002|对街
prop-house|shallows|门前浅滩|spatial|s003|走下门前的浅滩
prop-house|drying-area|门外洗晾幕布|spatial|s005|找晾绳
temple-front|temple-grain|院东门通往粮仓|spatial|s008|院东通往粮仓
temple-back|feeding-channel|院内封闭石道|spatial|s018|石道
feeding-channel|feeding-door|南端投食入口|spatial|s018|院北岩根
feeding-channel|cave-gate|北端通山洞|spatial|s018|院北岩根
temple-front|hill-steps|沿石阶下山|spatial|s037|石阶
troupe-workers|prop-house|存放并制作道具|use|s003|台架
troupe-workers|village-yard|散戏前演出|performance|s041|晒场
yard-audience|village-yard|观看演出|performance|s041|掌声
rice-listeners|a-heng|听曲并回应|performance|s001|听客笑起来
woodcutter|a-heng|听曲并发现省段|performance|s001|老汉：二道
temple-children|paper-snake|观看纸蛇戏|performance|s008|孩子们
lead-chorus|snake-welcome-song|共同领唱|performance|s007|领唱
a-heng|boat-song|演唱跳段版本|performance|s001|阿蘅（唱）：一道险滩
a-heng|blue-awning-song|从缺词到补全演唱|performance|s039|阿蘅
singer-teacher|blue-awning-song|补唱并核清末词|performance|s039|归来认旧桥
heng-mother|songbook|逐句哼曲供抄写|performance|s002|一句一句哼的
a-heng|songbook|抄写并持有|ownership|s002|抄了七个晚上
blue-awning-song|songbook|歌词记入歌本|use|s040|新纸
snake-welcome-song|lead-lyrics|领唱歌词载于旧纸|use|s003|米饵奉蛇神
zhao|lead-lyrics|交出领唱旧词|use|s002|领唱的词在这儿
troupe-workers|blessing-stage-song|祈福戏唱段|performance|s010|米饵献上
a-heng|snake-welcome-song|在前殿领唱|performance|s007|阿蘅站在
blue-awning-song|xu-bride|婚事所需唱曲|performance|s001|许家嫁女儿
a-heng|rice-bag|携带唱曲所得米|ownership|s001|撑开布袋
zhou|rice-measure|量米付唱工|use|s001|周掌柜提着小木斗
rice-measure|grain|计量米粮|use|s001|倒进去
rice-bag|grain|盛装米粮|use|s001|撑开布袋
songbook|book-basket|倒扣竹篮支承歌本|spatial|s001|倒扣的竹篮
river-stone|songbook|压住摊开的书页|use|s001|压一块河石
woodcutter|carrying-pole|听曲时持扁担|use|s001|扁担竖在腿边
a-heng|water-flask|倒水蘸湿布巾|use|s002|水壶
water-flask|cloth|倒水蘸湿|use|s002|布巾
li-ji|cloth|擦净手上浆糊|use|s002|擦
li-ji|paste-wool|劳作后手上附着|use|s001|干浆糊
mo-er|cake|吃女孩留下的饼|use|s002|饼
zhao|keys|收缴前腰间持有|ownership|s002|腰间挂着一串钥匙
officer-cheng|keys|验院后收走|ownership|s019|收走赵执事的钥匙
tao|bamboo-basket|编削篮口|use|s002|陶伯
tao|shaving-knife|削竹用刀|use|s002|刀
bamboo-stall|empty-stool|摊旁留有空位|spatial|s002|空
river-street|street-laundry|沿街民居晾衣|spatial|s002|晾
prop-house|curtain|屋外挂幕布|spatial|s002|幕布挂在一间道具屋外
sun-liu|stage-drum|为纸蛇戏配鼓|performance|s008|孙六
sun-liu|waist-drum|用腰鼓招呼邻里|use|s015|腰边的小鼓
troupe-workers|paper-snake|制作与操演|use|s003|纸蛇
paper-snake|paper-moon|蛇口吞吐纸月亮|use|s008|纸月亮
li-ji|paper-moon|持牵线操演|use|s008|李寄放低纸月亮
troupe-workers|stage-tools|搭台与收拾|use|s042|杆子靠稳在戏箱
temple-tall|red-rope|从戏班借用|use|s008|红绳
red-rope|name-plaque|绑缠祭名木牌|use|s008|牌下新系的红绳
name-plaque|a-heng|牌上记祭名|use|s008|巫祝转过牌面
li-ji|name-plaque|抢扯时受伤|use|s009|额角
heng-mother|debt-note|借粮时按手印|use|s026|手印是我按的
zhao|debt-overlay|篡改借据贴纸|use|s028|新纸贴在我娘手印前
debt-overlay|debt-note|贴于原据手印前|spatial|s022|贴纸揭下
a-heng|work-ledger|记录两天唱工|use|s026|递上唱工记录
clerk-liang|evidence-receipt|收证后出具|use|s026|写好收单凭记
a-heng|evidence-receipt|持凭记说明证据已交|use|s028|凭记
ticket-woman|grain-ticket|询问凭票领粮|use|s008|在哪儿换米
ticket-elder|grain-ticket|听告示后展开粮票|use|s037|老人
magistrate|stop-order|准许停祭与除蛇|use|s021|县丞：准
officer-cheng|stop-order|宣读并执行|use|s028|展开文书
county-office|volunteer-notice|照壁张贴应募告示|spatial|s013|照壁
clerk-notice|volunteer-notice|解说应募条件|use|s013|书吏
li-ji|old-lantern|携灯并照归家路|use|s042|灯举
li-mother|old-lantern|交给女儿|use|s027|裂缝补着窄纸
li-ji|bandage|手掌包扎|use|s023|将掌心裹好
li-ji|wood-knife|劈柴磨破掌心|use|s005|柴劈开了
li-ji|heavy-blade|持厚背刀斩蛇|use|s031|掌心的布透出一点血
li-dan|heavy-blade|示范沿缝落刀|use|s023|带她沿空缝
sun-liu|carrying-strap|提供补缝背带|ownership|s015|孙六肩上搭着
li-dan|carrying-strap|背病人时使用|use|s015|孙六扶着背带
heng-mother|medicine-pot|病中服药所需|use|s015|药
heng-home|rice-urn|灶边米缸|spatial|s038|米缸
stonemason|feeding-channel|改外段石盖刀缝|use|s023|石匠沿接缝
gate-pin|cave-gate|闸落底后穿栓固定|use|s018|穿牢的木栓
crossbeam|cave-gate|绑接后持续压闸|use|s024|长杠横到闸板
tao|hemp-rope|提供麻绳并提醒护角|ownership|s025|绳子别贴石角
sun-liu|hemp-rope|加旧布护垫|use|s025|布
hemp-rope|crossbeam|捆扎压杠并护角|use|s029|重新加固横杠
helpers-four|crossbeam|四名乡亲合力压杠|use|s029|两名乡亲
sun-liu|crossbeam|西侧压杠|use|s029|西侧孙六
li-xiao|crossbeam|西侧压杠|use|s029|西侧孙六
officer-cheng|crossbeam|东侧压杠|use|s029|东侧程差役
li-dan|crossbeam|临危加入东侧压杠|use|s030|挤到程差役身旁
elders-two|temple-back|守门道并找帮手|use|s029|手指门道
meat-rice-bait|bait-basin|盛装蛇饵|use|s029|盆里是拌肉的米饵
bait-basin|feeding-channel|推入南门至刀缝以南|spatial|s029|推到刀缝以南
snake|meat-rice-bait|沿石道进食|use|s018|吃
li-ji|snake|在闸与刀缝限制内斩蛇|use|s032|李寄
li-dan|channel-plan|收存并使用通道图|use|s020|卷进昨日画的通道图
li-xiao|channel-plan|补出刀缝说明站位|use|s026|在图上补出刀缝
zhou|grain-order|保留提前备粮证据|use|s020|单
delivery-worker|grain-order|指认送单日期|use|s036|庙工
order-writer|grain-order|认下原单笔迹|use|s036|经手
li-dan|grain-copy|抄录原单日期内容|use|s020|抄
zhou|shop-ledger|提供店账作证|ownership|s036|周掌柜的店账
officer-second|evidence-chest|看守封存证据|use|s022|守箱的差役
sacrificial-registers|a-he|旧祭册记名|use|s036|翻开阿禾
sacrificial-registers|xiao-man|旧祭册记名|use|s036|翻开阿禾
sacrificial-registers|a-heng|当年祭册记名|use|s036|今年
magistrate|approval-orders|前两次准祭签押|use|s036|批文
a-he|hairpin|遗物竹簪|ownership|s035|竹簪
xiao-man|broken-comb|遗物断梳|ownership|s035|小满的母亲
tao|petition|具状要求复查|use|s036|陶伯从衣襟里
clerk-proclamation|public-verdict|宣读复查结果|use|s037|书吏
public-verdict|a-he|确认非自愿被迫献祭|use|s037|皆非自愿入祀
public-verdict|xiao-man|确认非自愿被迫献祭|use|s037|皆非自愿入祀
public-verdict|a-heng|销去祭名|use|s037|阿蘅
new-steward|cleared-debt-receipt|清账并退粮|use|s037|新管事
a-heng|cleared-debt-receipt|带回清账凭据|use|s037|账纸
cleared-debt-receipt|songbook|凭据夹入歌本|spatial|s038|凭据压在歌本内
copied-pages|songbook|补页装订并保留旧页|use|s040|旧
li-ji|writing-board|记词交歌娘核对|use|s039|夹板
li-home|family-meal|归家聚餐|spatial|s034|桌
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
    result=[];evidence=[];missing=[]
    stable_labels={'父亲与女儿','母亲与女儿','五姐与妹妹','母亲与孩子','共同做工的旧交','一家住所','母女住所','经营米铺','经营竹器摊','临河街开门','位于对街','门前浅滩','院东门通往粮仓','院内封闭石道','南端投食入口','北端通山洞','灶边米缸','遗物竹簪','遗物断梳'}
    for line in SPEC_TEXT.strip().splitlines():
        left,right,label,category,sid,pattern=line.split('|')
        ep,scene,blocks=scene_index[sid];matches=[i for i,b in enumerate(blocks) if re.search(pattern,b['text'])]
        if not matches:missing.append((left,right,sid,pattern));continue
        index=matches[0];excerpt=blocks[max(0,index-2):min(len(blocks),index+3)]
        source={'object_id':ep['object_id'],'revision_id':ep['id'],'scene_id':sid,'block_ids':[b['id'] for b in excerpt]}
        a,b=entities[left],entities[right];oid=f'relationship-{left}-{right}-{category}'
        title=f'{a["payload"]["title"]} · {label} · {b["payload"]["title"]}'
        payload={'format':'production-relation-v1','relation_type':'entity','title':title,
                 'blocks':[{'id':'relationship','text':f'{a["payload"]["title"]} — {label} {"↔" if label in ("相互照应","共同做工的旧交") else "→"} {b["payload"]["title"]}。'}],
                 'entities':[{'object_id':r['object_id'],'revision_id':r['id']} for r in (a,b)],
                 'label':label,'direction':'mutual' if label in ('相互照应','共同做工的旧交') else 'forward','category':category,'basis':'script','sources':[source],
                 'applies_to':[] if label in stable_labels else [source]}
        try:old=p.record(store,oid)
        except KeyError:old=None
        if not old or old['payload']!=payload:result.append({'object_id':oid,'kind':'RELATION','expected_version':old['version'] if old else 0,'payload':payload})
        evidence.append({'id':oid,'title':title,'source':source,'excerpt':'\n'.join(b['text'] for b in excerpt)})
    if missing:raise ValueError('missing evidence phrases: '+json.dumps(missing,ensure_ascii=False))
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
