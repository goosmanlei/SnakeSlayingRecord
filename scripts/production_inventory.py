#!/usr/bin/env python3
"""Compile the manually reviewed screenplay-four inventory into exact references.

Catalog and scene appearances are authored below after reading all 42 scenes.
Text search only locates evidence inside those authored appearances; it does not
decide whether a named person is present. Outputs are real production data, not
fixtures. Revisions are resolved by the review desk's atomic batch importer.
"""
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def scenes(value):
    result = set()
    for part in value.split(','):
        if not part:
            continue
        a, _, b = part.partition('-')
        result.update(range(int(a), int(b or a) + 1))
    return result


# id | name | type | aliases | actual visual scenes | facts | evidence patterns
CATALOG = r"""
li-ji|李寄|character||1-20,22-23,26-34,36-42|李诞的女儿、李绡的妹妹；第一集手有干浆糊、头发跑松、肩有挑水红印。|李寄
a-heng|阿蘅|character||1-10,15-20,22,26-34,36-42|以唱曲和劳动补贴家用；第一集清瘦，穿洗旧青衣，袖口整齐，脚下能稳稳打拍。|阿蘅
li-xiao|李绡|character|五姐|3,5-6,7-9,14-18,20,22-24,26-34,41-42|李寄的五姐，戏班做道具、布置台口并照顾妹妹；动作利落。|李绡,五姐
li-dan|李诞|character|李寄父亲|14-34,36-37,41|李寄父亲，码头做工；参与停祭、准备和压闸，给李寄示范沿缝下刀。|李诞,父亲,李家几人
li-mother|李寄母亲|character||14,16,26-27,34,41|接济阿蘅一家、照看病人，备饭等众人回来，递出补过灯罩的旧灯。第一集阿蘅所说的“婶婶”指她；第四集同称呼指邻妇，不设全局同名别名。|李寄母亲,婶婶,母亲
heng-mother|阿蘅母亲|character|阿蘅的娘|7,10,15-16,26-27,34,38,40-42|患病需照护，曾逐句哼曲让女儿抄歌本；借粮时只同意借还粮，没有同意献祭。|阿蘅母亲,阿蘅的娘,她娘,我娘,母亲
zhou|周掌柜|character|周叔|1,4,17,20,28,36|米铺掌柜，安排许家唱活并预付米；后提交早于点名日期的备粮证据。|周掌柜,周叔,掌柜
zhao|赵执事|character||2,6,9,12,17-19,21-22,28,30,36-37|第一集褐衣、腰挂钥匙；以领唱邀阿蘅进庙，后被查出篡改借据并参与献祭。|赵执事
mo-er|墨耳|character||2-3,7,16,26-27,41-42|瘦黄狗，左耳尖缺一角；斩蛇当天留在李家，未带去后院。|墨耳,瘦黄狗
tao|陶伯|character||2,14,25,28,35-37|阿禾的父亲，编削竹器；第一集身旁有空小凳，听到女儿名字停刀。|陶伯,老人
a-he|阿禾|character|阿禾姐姐|14|陶伯之女，前年被强迫献祭；第六集李诞回忆中回头在围观人群找到李诞，该画面没有阿禾台词。“她回头叫我”来自第十五集陶伯当堂证词。|阿禾
xiao-man|小满|character|下湾的小满||去年被强迫献祭；本剧以被提及、案卷和遗物追溯，没有安排其活人出镜。|小满
sun-liu|孙六|character||8-9,15,17-19,23-27,29-34,41-42|戏班鼓手，出力接病人、装杠和压闸；有小腰鼓和缝补两层的宽布背带。|孙六
priest|巫祝|character||8-9,17,24,28,30,36-37|穿祭衣、声称梦示祭名，阻拦查册；最终因强迫献祭等罪被押赴郡狱。|巫祝
clerk-liang|梁书吏|character||17,22,26,36|报名时误写自愿入祀，后核验借据和记录口供；最终因虚记革退。|梁书吏,书吏
officer-cheng|程差役|character|老程|17-19,21-24,28-30,32-37|鬓角发白的差役，实地验门闸、封存证据、参与压杠，并守住事后封闭措施。|程差役,老程
magistrate|县丞|character||17,21,36|签过前两年准祭批文，本次准停祭与除蛇；经郡中复查被革职。|县丞
temple-tall|瘦高庙工|character||8,18-19|借戏班红绳并处理祭名木牌；阿蘅在验院时认出同一人，后说明投食与送人的门闸次序。第五集拧李寄胳膊的庙工未明确为他。|瘦高庙工
temple-guards|守院庙工二人|character||10,15|被派在阿蘅家院口守着，两个矮凳与两名守院者需要同框；搬病人时挪开凳子。|两个庙工,庙工,守着,凳
officer-second|另一名差役|character||22,24,28,30|奉调看守账箱、前院和被调查者；与一直参与后院工作的程差役分开。|另一名差役,差役,同伴
stonemason|石匠|character||23,33|受请只改通道外段的盖石，按厚背刀开窄缝；蛇死后再次被请来处理现场。|石匠
helpers-four|四名压杠乡亲|character||23-24,29-34|两人穿码头短褂，两人裤脚有白灰；其中一名码头工有对白，四人都参加压杠。|四名乡亲,码头工,工友,乡亲,两人,三人
elders-two|两位乡老|character||28-33,36|见证封册并维持门道；危急时一人找帮手、一人留门口引路。|乡老,老人
ticket-woman|领粮妇人|character||8,28,37|庙会时抱孩子询问粮票，后再问不送人是否仍给米；关系到粮食胁迫的呈现。|妇人
ticket-child|领粮妇人的孩子|character||8,28,37|被母亲抱着，庙会场丢过一只鞋；不是祭名候选女孩。|孩子,鞋
woodcutter|挑柴老汉|character|老汉|1|在米铺外听阿蘅唱曲，扁担立腿边，发现她跳过两道滩后打趣。|挑柴老汉,老汉
rice-listeners|米铺听客|character||1|米铺门口数名听客笑、提米袋、进铺；其中一人说“下回补上”。|听客,下回补上,量米
street-passers|河街路人|character||2|第一集有人向赵执事打招呼；不与米铺老汉或陶伯合并身份。|有人经过,打招呼
neighbor-woman|邻妇|character|邻居妇人|7,15,34,41|帮阿蘅母亲照看药罐、搬褥子和照路，归家饭桌端菜，散戏后陪病人先回家；其他未具名邻居不自动合并为她。|邻妇,邻居妇人
boatman|船家|character||11|渡口船家担心庙里扣货，拒绝载女孩出走。|船家
old-woman|庙仓老妇人|character||12|在庙仓带着瘦女孩，担心自家孩子被替补点名。|老妇人,妇人
thin-girl|庙仓瘦女孩|character||12|与老妇人同行，手中捏碎纸；与阿蘅、小满和领粮妇人的孩子分别登记。|女孩,纸
clerk-notice|照壁前书吏|character||13|县衙照壁前解说应募与停送条件；剧本未明确其是否为梁书吏。|书吏
clerks-other|其他书吏|character||17,36|县衙另有办文书的书吏，问责时由另一人接替梁书吏记录。|书吏
clerk-proclamation|宣读告示书吏|character||37|二十多天后宣读郡中复查结果；不能默认为已革退的梁书吏。|书吏
xiaoman-mother|小满母亲|character|小满的母亲|35-36|认领女儿的断梳，陈述小满并非自愿献祭并要求问责。|小满母亲,小满的母亲
singer-teacher|邻村歌娘|character|歌娘|39|曾替许家唱歌，在邻村院中教阿蘅补全《送青篷》，核清“认旧桥”。|歌娘,唱歌的那位
new-steward|新管事|character||37|核清旧债和唱工，逐行向阿蘅说明并退还多收的粮。|新管事
delivery-worker|送单庙工|character||36|当堂指认证据单送达日期；剧本没有明确其与瘦高庙工是否同一人。|送单的庙工
order-writer|备粮单经手人|character||36|另一名经手人认下备粮原单上的笔迹；与送单庙工区分。|经手人,笔迹
temple-crowd|庙前乡民|character||8-9,28-30,37|庙会、领粮与听告示的人群；部分人因恐惧不愿帮压杠，不能全体画成同一态度。|人群,乡民,队,众,围观,汉子,人们
troupe-workers|戏班伙计与台上演员|character||3,6,8,41|搬幕杆、台架和戏箱的伙计与祈福戏演员；没有明确姓名，不并入孙六或两姐妹。|搬杆,抬出幕杆,屋后有人,伙计,台上人,台架,戏
lead-chorus|前殿领唱众人|character||7|十几个领唱的人与阿蘅同唱；人数原文为约数，不虚构各人的姓名。|十几个领唱,前殿
temple-workers|未具名庙工|character||9,12,14,28|第五集拧李寄胳膊、仓院搬粮、回忆中拖开陶伯与封册说明年份的人；剧本未确认这些为同一人，登记为群演类别，具体分身待镜头设计。|庙工,搬粮
temple-children|庙会儿童与家长|character||8-9|台下看纸蛇与月亮的儿童、拉住孙子的老汉和家长；不与第一集挑柴老汉合并。|孩子,孙子,老汉,母亲
procession-crowd|阿禾祭队与围观者|character||14|李诞回忆中祭队挤过人群，阿禾被带走；区别于当下庙会时空。|祭队,人群
ticket-elder|告示前持票老人|character||37|听不清告示，由抱孩子的妇人重复最后一句后展开揉皱粮票；身份未与乡老或挑柴老汉合并。|听不清的老人,老人
offscreen-caller|窗外唤李寄归家的人|character|||第十七集窗外叫李寄回家，剧本未说明身份；仅需声音。|窗外有人叫她回家
yard-audience|晒场观众|character||41|观看戏班散戏前最后一首歌，鼓掌后提凳子回家。|台下,散场,掌声
xu-bride|许家女儿|character|||许家即将出嫁的女儿仅被提及，第一集无需出镜、声线或婚礼画面。|许家,嫁女儿
snake|大蛇|character||18,30-33|盘踞山洞，经短石道吃饵；斩蛇发生在两门与盖石限制内，从未放进院中。|蛇头,花纹,鳞片,断口,大蛇,蛇
rice-shop|周家米铺|space|米铺|1-2,4|河街临街店铺，门口能唱曲换米；内有量米柜、账、油灯，傍晚收铺；第二场赵执事先站在米铺檐下。|米铺,铺子,柜,掌柜
river-street|河街|space||1-2,15,19,27,42|沿河民居与日常生计空间，米铺、竹器摊、道具屋可以沿街联系。|河街,街道,河边,街角,巷口,山阶
bamboo-stall|陶伯竹器摊|space|竹器摊|2|在第一集女孩所在街道的对街，陶伯坐摊前削篮口，旁有空小凳。|竹器摊,对街
prop-house|道具屋|space||2-3,5,42|戏班存放制作道具的屋子，屋外挂幕布；与浅滩、晾布位置相邻。|道具屋,戏箱,幕布
shallows|道具屋外浅滩|space|浅滩|3,6|用于洗布，河水可以冲走纸页；李寄也由浅滩涉水过河。|浅滩,河水,水里,河
drying-area|晾布处|space|晾布架|3,5-6|戏班晾洗幕布之处；阿蘅劳动与赵执事展示借据发生于此。|晾,布架,幕布
heng-home|阿蘅家|space||7,10,15,38-40,42|含病人床铺、窗下抄歌桌、灶边米缸、院口和门前松动石阶。|阿蘅家,床,窗,院,门
li-home|李家|space||14-16,20,26-27,34,42|堂屋、卧处、里屋、院子、灶边相连；接阿蘅母女暂住，最后门未闩。|李家,堂屋,里屋,院,灶,门
temple-front|山庙前殿与台前|space|山庙前院|7-9,24,28,30,37|前殿、阶前临时戏台与领粮动线；西侧有井，东侧通仓院。|前殿,正殿,阶,台,井,庙
temple-grain|山庙仓院|space|庙仓院|12,19,22,28,37|存粮和账册证据的仓院，领粮与查账在此发生；与后院不同。|仓,账箱,领粮,粮
temple-back|庙后封闭小院|space|封闭后院|18-19,23-25,29-33|高墙接山崖，唯一后门上锁；院内短石道南投食门、北洞闸，人不入洞。|后院,小院,后门,石道,院
hill-steps|下山石阶|space||19,25,37|庙与河街之间的出入路，具有下山方向和归家灯光。|下山,石阶,廊下,阶下
county-office|县衙|space|县衙照壁,县衙廊下|13,17,21,35-36|照壁募蛇榜、廊下登记桌和堂前案桌；公开文书与问责不能混为一个无方向背景。|县衙,衙,廊,登记桌,案
ferry|渡口|space||11|有货物、船板与系船绳的渡船停靠处。|渡口,船板,船
singer-yard|邻村歌娘院子|space|歌娘院中|39|晾演出衣、女孩坐小凳听歌娘补词；旧红袖与晾衣绳可见。|院,歌娘,红袖
village-yard|村中晒场|space|晒场|41|戏班演出和散场空间，台前台侧与回河街方向清楚。|晒场,台,幕
songbook|阿蘅歌本|prop|歌本|1-7,9,16-17,22,37-38,40-42|母亲逐句哼、阿蘅抄七晚的本子；被李寄掷水后失词，最后保留旧残页并订入补全的新页。第三十九场带出两张新旧纸，本体未明确出镜。|歌本,本子,旧页,新页,本,新旧纸
rice-bag|阿蘅米袋|prop|小米袋|1-4,37|布袋盛唱曲所得米；第一集由阿蘅携带，第二集退米，清账后再由两女孩一起接米。|米袋,布袋,袋口,袋子,粮袋
rice-measure|米铺小木斗|prop|小木斗|1,4,37|量米器具，刮平后倒米与额外抓的一把米分开呈现。|木斗,量米,刮平
grain|米粮|prop||1-2,4,8,12,28,30,37-38|作为报酬、借粮、接济与退还的生活物资；计量内容遵从各场原文。|米,粮
book-basket|垫歌本竹篮|prop||1|倒扣在米铺门外，用于摊歌本；与陶伯正在削的篮子不是同一物。|竹篮,篮前
river-stone|压页河石|prop||1|压着摊开的歌本抵住河风。|河石
carrying-pole|挑柴扁担|prop|老汉扁担|1|挑柴老汉将扁担竖在腿边，构成其听歌姿态。|扁担,挑柴
water-flask|阿蘅水壶|prop|水壶|2|阿蘅倒水蘸湿布巾，供李寄清掉手上的浆糊与羊毛。|水壶
cloth|擦手布巾|prop|布巾|2|被蘸湿、翻面再递回李寄，擦手后歌本才能转手。|布巾
cake|半块饼|prop||2|李寄留给墨耳的半块饼，交阿蘅掰下一小角喂狗。|半块饼,小角,饼
paste-wool|干浆糊与羊毛|prop||1-3|戏班劳作留下的少量附着物；第一集从李寄手指清除，不能画成伤口。|浆糊,羊毛
keys|庙院钥匙串|prop|钥匙|2,18-19,29|第一集挂赵执事腰间；验院后由程差役收走，祭日再用于开后门。|钥匙,开锁,锁门
lead-lyrics|迎蛇领唱旧纸|prop|领唱词纸|2-3,6|赵执事将旧领唱词放在歌本上，包含祭蛇换安宁的歌词。|旧纸,领唱,米饵奉蛇神
bamboo-basket|陶伯在编的竹篮|prop||2|篮口正在被削，听到阿禾名字时动作停止，场尾重新刮削。|篮口
shaving-knife|陶伯削竹刀|prop|削竹刀|2|削篮口的小刀；停刀与重新刮削承担声音和情绪作用。|刀,刮
empty-stool|竹器摊空小凳|prop|空小凳|2|陶伯身边空置，镜头应看清空位。|小凳
street-laundry|河街晾衣|prop||2|临河民居门前晾衣，提供民间生活环境和轻微风动。|晾着衣裳
curtain|戏班幕布|prop|幕布|2-3,5-6,8,41-42|道具屋外可见，需洗晾并用于演出台口，散场有拆卸。|幕布,幕杆,半幅幕
stage-drum|戏班台鼓|prop||8|第一集从道具屋方向传来试鼓；第四集孙六以鼓点配合纸蛇戏。第一集鼓体不必出镜。|鼓,孙六
waist-drum|孙六小腰鼓|prop|小腰鼓|15|接病人时用鼓声招呼邻里；与台鼓分别登记。|腰鼓,鼓
paper-snake|戏班纸蛇|prop|纸蛇|3,8-9,18|竹骨与纸制的戏班道具，嘴可牵动吞吐纸月亮；不是山洞大蛇。|纸蛇,竹骨,蛇嘴
paper-moon|戏班纸月亮|prop|纸月亮|8-9|纸蛇祈福戏中被吞后应吐出的月亮，点名时卡在蛇嘴。|月亮,月
stage-tools|戏班竹竿与工具箱|prop|戏箱|3,8-9,15-19,23-26,41-42|幕杆、竹竿、木槌等戏班工具与戏箱按各场用途出现，不当作刀械。|竹竿,竹杆,幕杆,戏箱,工具,木槌,箱里
name-plaque|阿蘅祭名木牌|prop|祭名牌|8-9|用红绳缠着、边沿刮过的木牌；李寄抢扯时撞伤额角。|木牌,牌,名字
red-rope|戏台借出的红绳|prop|红绳|8-9|瘦高庙工借来缠祭牌，打双圈结；有剪断与李寄抢扯状态。|红绳,双圈,绳
debt-note|阿蘅家借据|prop|借据|6,22,26,36|母亲按手印的借粮凭据；原约本息六斗，贴纸篡为七斗并添供奉字样。第二十八场已交差役，只口头举证，阿蘅出示的是收单凭记。|借据,手印
debt-overlay|借据篡改贴纸|prop|贴纸|6,22,26,36|贴在原借据手印前，揭开后与原据分别留证。|贴纸,新纸,贴,七斗
work-ledger|阿蘅唱工记录|prop|唱工记录|6-7,16-17,26,37|阿蘅记录唱两天、每天两升的工钱，用于清债核对；第二十八场口头举证，实际出示的是收单凭记。|炭,两升,唱工,四升,记录,工钱纸,记工钱
grain-ticket|领粮票|prop|粮票|8,17,28,37|乡民领粮凭票，停祭后接济仍照发。|粮票,票号,窄纸
stop-order|停祭与除蛇文书|prop|免祭文书|17,21-22,26,28|从应募期间停送、阿蘅免祭，到第九集补明除蛇成败都不得向任何户索人；具体文字绑定各场；第十三场的停送规则在应募告示上，尚无本次文书实物。|文书,暂停送人,免祭,任何一户,白纸
volunteer-notice|照壁应募告示|prop|应募榜|13|旧告示招人除蛇，并写明应募时暂停送人入洞。|告示,应募,暂停送人
old-lantern|李家旧灯|prop|旧灯|16,27-29,33-34,41-42|灯罩裂缝补着窄纸；白天未点也带着，最终点亮照回家的路。|旧灯,灯罩,灯芯,提着灯,灯
bandage|李寄裹手与额角布|prop|裹手布|5,9,13-14,23,31-34|手掌和额角的伤口包布需区分位置，斩蛇后手重新包扎。|裹,布,伤,包
wood-knife|家用柴刀|prop|柴刀|5,16|用于劈柴和磨刀；与县里借的厚背刀不是同一件。|柴刀,劈柴,磨
heavy-blade|县库厚背刀|prop|厚背刀|23-24,26-27,29-33|从县库领取，有刀套，沿石盖窄缝下刀；第十七场口头请留刀，第三十四场只由程差役报告已收回待交库，不据此要求刀出镜。|厚背刀,刀套,刀,刃
carrying-strap|孙六宽布背带|prop|宽布背带|15|有两层补缝，用于背病人；不是压闸的麻绳。|背带,布带,两层
medicine-pot|煎药罐与药渣|prop|药罐|15-16,26|照顾阿蘅母亲时携带、煎药或倒药渣的生活道具。|药罐,药锅,药渣,药
rice-urn|阿蘅家米缸|prop|米缸|38|债清后灶边已有小半缸粮；不夸大成富足，不凭家境虚构前期空缸镜头。|米缸
feeding-channel|短石道与盖石|prop|短石道|18-19,23-24,29-33|连通北山洞和南投食门，顶上石盖封闭；第十集仅在外段接缝开能过刀身的窄缝。第二十一、二十六场用图说明，不出现实物。|石道,通道,石盖,盖石,刀缝
feeding-door|南端投食木门|prop|投食门|18-19,23-24,29-33|投食时与北闸按次序开关，蛇吃时南门横闩必须锁稳。|投食门,前门,横闩,矮门
cave-gate|北端洞闸|prop|洞闸|18-19,23-24,29-33|木闸可落底插栓，压蛇时落不到底、不能插栓，需要持续承重。|洞闸,闸板,后闸,落闸,木栓,木闸
gate-pin|洞闸木栓|prop|木栓|18-19,23-24,29|落底后穿栓，提闸前抽出放墙边；不能误画压蛇时还插牢。|木栓,栓
crossbeam|压闸长横杠|prop|横杠,长杠|23-24,26,29-33|绑接洞闸，初始七人压，李诞加入后两边各四人。|横杠,长杠,长木,杠
hemp-rope|陶伯麻绳与护垫|prop|麻绳|25-27,29-32|陶伯送麻绳并提醒避开石角，孙六加旧布垫；绳与垫分别能被辨认。|麻绳,绳捆,绳,旧布,垫布
bait-basin|蛇饵盆|prop|饵盆|18,23,29|经南门放入，正式除蛇前推到刀缝以南，蛇头过缝才能吃。|饵盆,盆
meat-rice-bait|拌肉米饵|prop|米饵|8-9,18,29|用于喂蛇，不能以活人或墨耳作饵。|米饵,拌肉,饵
channel-plan|李诞通道图|prop|通道图|20-21,23,26|先画门闸通道，后补刀缝，供所有人理解站位和停止办法。|通道图,图,刀缝
grain-order|提前备粮原单|prop|备粮原单|20,22,28,36|有阿蘅家住处、祭户粮与日期，日期早于庙会点名一天。|原单,备粮,窄纸,单子
grain-copy|备粮抄单|prop|抄单|20-22|李诞照原单抄日期内容，先交县衙；与原单分开核对。|抄单,抄件,抄下,纸
shop-ledger|周掌柜底账|prop|底账,店账|20,28,36|米铺记录收到备粮单的日期，掌柜公开提交作证。|底账,店账,账本,账
evidence-chest|封存账箱|prop|账箱|22,28|仓院查借据用的账箱和封册时装箱的位置分别依来源呈现；同一件箱子并非剧本明确，制作时分设箱组件。|账箱,箱,封存
sacrificial-registers|三年原祭册|prop|祭册|17,28,36|前年阿禾、去年小满、当年阿蘅三本，年份和名字分别可读；第二十四场柜内只提及未开柜。三册是并存的组成，不是同一册的三个候选版本。|祭册,三本,册子,旧册
approval-orders|前两次准祭批文|prop|准祭批文|21,36-37|县丞签押与本次停祭文书为同一个名字，后有抄件公开；两年两份与公开抄件分别登记组成。|准祭批文,批文,签押
evidence-receipt|阿蘅收单凭记|prop|收单凭记|26,28|梁书吏收借据和唱工记录后出具，阿蘅拿它公开说明证据已交。|凭记
hairpin|阿禾竹簪|prop|竹簪|35-36|从洞内清出，簪尾浅纹刻歪，陶伯据此认领。|竹簪,簪
broken-comb|小满断梳|prop|断梳|35-36|洞中清出的半把梳子，小满母亲认领并握着申诉。|断梳,梳齿
petition|陶伯诉状|prop|状子,诉状|36|要求旧批文随状子和证据一并送郡复查。|状子,诉状
public-verdict|郡复查告示|prop|新告示|37|记明刑责、革职、阿禾小满非自愿、阿蘅销祭名、永废人祭和照发接济粮。|告示,最后一句,名字
cleared-debt-receipt|清账退粮凭据|prop|清账凭据|37-38|给阿蘅核对并带回，夹在歌本里；显示债销清、多收粮退还。|凭据,清账,账纸
copied-pages|补抄歌页与装订线|prop|补抄新纸|5,38-40|最初缺半行；向歌娘核词后补写、穿线订牢，旧残页留在本后。|新纸,新页,新旧纸,半行,针,线,补抄
writing-board|补词夹板与笔|prop|夹板|39-40|李寄记词、歌娘核字，李寄手疤绷紧后把笔交给阿蘅。|夹板,笔,写
family-meal|归家饭食与桌凳|prop||27,34,42|饼、炖肉、炒蛋和汤，板桌与借来的凳子容纳帮忙乡亲；最后留温饭和净碗。|饼,肉,鸡蛋,炒蛋,汤,碗,凳,板
boat-song|舟行曲（未具名）|song||1|第一集阿蘅跳过两道滩直唱归家句；剧本仅给两句歌词，曲名及被省两段原文未知。|一道险滩,船靠岸,两段
blue-awning-song|送青篷|song||3-5,38-41|作品内容与演唱状态分开：先会前段，歌本受损缺末词，歌娘补全后终于唱完；第五场阿蘅也哼到断句处。|送青篷,青篷,柳影,莫怕,归来认旧桥,隔水灯
snake-welcome-song|迎蛇领唱调|song||7|赵执事旧词有“米饵奉蛇神，四邻得安宁。”；阿蘅在前殿做两天领唱。|迎蛇,米饵奉蛇神,领唱
blessing-stage-song|祈福戏唱段|song||10|第五集庙中远远传来“米饵献上，明月还乡——”；未明确它与迎蛇领唱调为同一作品，不强行合并。|米饵献上,明月还乡,祈福戏
"""

# Additional fact/choice distinctions that cannot be inferred from aliases.
NOTES = {
    'li-ji': {'choices':['首轮候选赭红上衣、灰蓝裤、低髻属于待审造型，不是剧本指定颜色。'], 'unknowns':['确切年龄、身高及面部母版尚未选定。']},
    'a-heng': {'unknowns':['确切年龄、面容、完整声线和旋律尚待基准审阅。']},
    'mo-er': {'unknowns':['“牵起墨耳”未写明是否使用牵绳，镜头设计须明确动作方式。']},
    'clerk-notice': {'unknowns':['照壁前书吏与梁书吏没有明确同人依据，保持独立角色身份。']},
    'ticket-woman': {'choices':['第十六集抱孩子妇人可沿用第四、十二集群演造型，作为待审选角连续性。'], 'unknowns':['第十六集没有再次明说这位妇人与第四集为同一人。']},
    'delivery-worker': {'unknowns':['送单庙工与瘦高庙工是否同一人未明，不合并。']},
    'sacrificial-registers': {'choices':['以一组道具管理三本实体册，组件/状态内分别标明前年、去年和当年，不用候选版本代表年份。']},
    'stage-drum': {'unknowns':['第一集只写道具屋传来试鼓声，不能据此确定鼓手为孙六；第一集用项目级声音需求登记。']},
}

# Explicit offscreen voices. Songs have voice rather than a material body.
VOICE_ONLY = {'stage-drum':{2,7}, 'offscreen-caller':{40}}
MODE_OVERRIDES = {('rice-listeners',1):'visual_voice', ('street-passers',2):'visual_voice',
                  ('lead-chorus',7):'visual_voice', ('temple-crowd',30):'visual_voice',
                  ('temple-guards',15):'visual_voice', ('helpers-four',23):'visual_voice',
                  ('temple-children',8):'visual_voice', ('li-mother',14):'visual_voice',
                  ('heng-mother',38):'visual_voice', ('heng-mother',40):'visual_voice'}

LYRICS = {
    'boat-song': [(1,'b002','一道险滩水急，船头慢慢行——','开头'),
                  (1,'b004','船靠岸，灯来迎，家里人等到如今——','跳过两道滩后的归家句')],
    'blue-awning-song': [(41,'b009','青篷起，水轻摇，送你过了石板桥。桨莫急，缆慢抛，岸上叮咛还未了——','第一段'),
                         (41,'b011','青篷过河湾，柳影到船边——','第二段前半'),
                         (41,'b013','莫怕远山高，隔水灯相照。明年春水暖，归来认旧桥——','补全的第二段后半')],
    'snake-welcome-song': [(3,'b014','米饵奉蛇神，四邻得安宁。','旧领唱纸上可读句')],
    'blessing-stage-song': [(10,'b010','米饵献上，明月还乡——','远处唱段')],
}


def compile_inventory():
    script = json.loads((ROOT/'imports/screenplay-04.json').read_text())
    lock = json.loads((ROOT/'production/source-lock.json').read_text())
    if hashlib.sha256((ROOT/'imports/screenplay-04.json').read_bytes()).hexdigest() != lock['screenplay']['file_sha256']:
        raise ValueError('approved input changed; locate impact before replacing it')
    episodes = {e['number']:e for e in script['episodes']}
    revisions = {e['number']:e['revision_id'] for e in lock['episodes']}
    scene_map = {}
    for number, ep in episodes.items():
        for scene in ep['scenes']:
            blocks = [b for b in ep['blocks'] if b['id'] in scene['block_ids']]
            scene_map[int(scene['id'][1:])] = (number, ep, scene, blocks)
    def source(sn, blocks=None):
        number, ep, scene, whole = scene_map[sn]
        return {'object_id':ep['id'], 'revision_id':revisions[number], 'scene_id':scene['id'],
                'block_ids':[b['id'] for b in (blocks or whole)]}
    def ref(oid):
        return {'object_id':oid, 'revision_id':'@'+oid}
    def record(oid, kind, title, text, **fields):
        return {'object_id':oid, 'kind':kind, 'expected_version':0, 'payload':{
            'format':'production-'+kind.lower().replace('_','-')+'-v1', 'title':title,
            'blocks':([{'id':'description','text':text}] if text else []), **fields}}
    records = [record('production-input-screenplay04','INPUT_LOCK','版本四制作输入',
        '用户已确认版本四定稿。本任务交付第一集正式镜头生成前的生产准备；画面为二维人物与轻手绘背景，动态分镜16:9。',
        screenplay={k:lock['screenplay'][k] for k in ('object_id','revision_id')},
        episodes=[{k:e[k] for k in ('object_id','revision_id')} for e in lock['episodes']],
        approval={k:lock['approval'][k] for k in ('actor','statement','scope')},
        specification={'visual_style':'二维人物＋轻手绘背景','aspect_ratio':'16:9','fps':24,
                       'animatic_width':1920,'animatic_height':1080,'audio_sample_rate':48000,
                       'image_resolution_requirement':'native 4K; actual GPT Image 2.5 output discrepancy pending',
                       'i2i_preferred_max_generations':1,'i2i_absolute_max_generations':2})]
    entries, appearances = {}, {sn:[] for sn in scene_map}
    for line in CATALOG.strip().splitlines():
        key, name, kind, aliases, visual, fact, patterns = line.split('|')
        oid = 'entity-'+key
        shown = scenes(visual)
        patterns = patterns.split(',')
        located = {}
        for sn, (_, ep, scene, blocks) in scene_map.items():
            found = [b for b in blocks if any(word in b['text'] for word in patterns)]
            if found:
                located[sn] = found
        # Character aliases used as broad pronouns are evidence locators only;
        # do not invent a mention in unrelated scenes from "mother" or "clerk".
        mention_patterns = [name, *[a for a in aliases.split(',') if a]]
        mentioned = {sn for sn,(_,_,_,blocks) in scene_map.items()
                     if any(any(word in b['text'] for word in mention_patterns) for b in blocks)}
        if kind == 'song':
            mentioned |= set(located)
        if key == 'xu-bride':
            mentioned |= set(located)
        if key == 'li-mother':
            mentioned.add(2)
        all_scenes = shown | mentioned | VOICE_ONLY.get(key,set())
        refs = [source(sn, located.get(sn)) for sn in sorted(all_scenes)]
        if not refs:
            raise ValueError('no located evidence for '+name)
        details = NOTES.get(key,{})
        entries[key] = {'id':oid,'name':name,'kind':kind,'scenes':all_scenes,'sources':refs}
        extra = {}
        if kind == 'song':
            extra['lyrics'] = []
            for sn, bid, text, section in LYRICS[key]:
                block = next(b for b in scene_map[sn][3] if b['id'].endswith('-'+bid))
                if text not in block['text']:
                    raise ValueError('lyric differs from approved text: '+key)
                extra['lyrics'].append({'section':section,'text':text,'source':source(sn,[block])})
            extra['composition_status'] = '歌词原文锁定；曲调、声线和表演为待审制作选择。'
            if key == 'boat-song':
                extra['content_unknowns'] = ['正式曲名和省去两段歌词未写出；不假定与《送青篷》同曲。']
        records.append(record(oid,'ENTITY',name,fact,entity_type=kind,
            subtype='animal' if key in ('mo-er','snake') else 'group' if key in ('helpers-four','elders-two','temple-crowd','rice-listeners','street-passers','yard-audience','temple-guards','clerks-other','troupe-workers','lead-chorus','temple-workers','temple-children','procession-crowd') else 'individual' if kind=='character' else kind,
            aliases=[a for a in aliases.split(',') if a], facts=[fact], choices=details.get('choices',[]),
            unknowns=details.get('unknowns',[]), sources=refs, **extra))
        for sn in sorted(all_scenes):
            evidence = located.get(sn)
            mode = 'mention'
            if sn in shown:
                speaking = kind == 'character' and any(
                    b['text'].startswith(s + mark)
                    for b in scene_map[sn][3]
                    for s in [name, *aliases.split(',')] if s
                    for mark in ('：', '（唱）'))
                mode = 'voice' if kind=='song' else 'visual_voice' if speaking else 'visual'
            if sn in VOICE_ONLY.get(key,set()):
                mode = 'voice'
            mode = MODE_OVERRIDES.get((key,sn), mode)
            appearances[sn].append({'entity':ref(oid),'states':[], 'mode':mode,'evidence':[source(sn,evidence)]})
    # Full snapshots and explicit transitions are authored after all-scene review.
    from production_forms import compile_forms
    compile_forms(records, appearances, entries, source, ref, record, scene_map)
    for sn,(number,ep,scene,blocks) in scene_map.items():
        records.append(record(f'preparation-s{sn:03d}','PREPARATION',scene['heading'],
            '',
            source=source(sn), occurrences=appearances[sn], checked=True, state_model='complete-v1',
            notes='人物称谓只在有同人依据时合并；空间实体不等同于剧情场次。'))
    return {'format':'production-import-v1','records':records}


def add_states(records, appearances, entries, source, ref, record, scene_map):
    # Filled from the reviewed state schedule, never from image candidate counts.
    for state in STATES:
        key, entity, label, dimension, appearance, evidence_scene, words, fact = state
        title = entries[entity]['name'] + '·' + label
        sn = evidence_scene
        blocks = [b for b in scene_map[sn][3] if any(w in b['text'] for w in words.split(','))]
        if not blocks:
            raise ValueError('state evidence missing: '+key)
        oid = 'state-'+key
        places = scenes(appearance)
        continuity = ['跨场沿用此状态是根据前后文提出的制作连续性安排，具体镜头仍需复核。'] if places - {sn} else []
        records.append(record(oid,'STATE',title,fact,entity=ref(entries[entity]['id']),dimensions=dimension,
            sources=[source(sn,blocks)],facts=[fact],choices=continuity,unknowns=[],
            previous_states=[ref('state-'+key) for key in PREVIOUS.get(key, [])]))
        for s in scenes(appearance):
            attached = False
            for occurrence in appearances[s]:
                if occurrence['entity']['object_id']==entries[entity]['id'] and occurrence['mode']!='mention':
                    occurrence['states'].append(ref(oid))
                    attached = True
            if not attached:
                raise ValueError(f'state {key} appears without its entity in scene {s}')


# Legacy partial-state schedule, retained only for migration correspondence and
# exact historical replay. New compilation uses production_forms.py snapshots.
STATES = [
    ('liji-paste','li-ji','手有干浆糊',{'hands':'dry_paste'},'1-2',1,'干浆糊','手沾干浆糊，第一场不能接歌本；第二场从指缝搓出羊毛。'),
    ('liji-clean','li-ji','双手已擦净',{'hands':'clean'},'2',2,'擦净手','擦净手后才接住歌本；清洁动作与书的转手有因果。'),
    ('liji-water-mark','li-ji','跑松头发与挑水红印',{'hair':'loosened','shoulder':'red_pressure_mark'},'1-2',1,'头发跑松','肩上有挑水磨出的红印，头发跑松；不画成出血伤。'),
    ('liji-wet','li-ji','涉水后湿裤脚',{'clothes':'wet_trousers'},'3-4',4,'湿裤脚,湿衣服','捞歌页之后湿裤脚滴水，阿蘅叫她回去先换湿衣服。'),
    ('liji-abrasion','li-ji','劈柴后掌心磨破',{'hands':'abraded_with_wood_chips'},'5',5,'磨破,木屑','劈柴磨破掌心，沾着木屑，李绡替她清理。'),
    ('liji-wrapped','li-ji','掌心包布',{'hands':'wrapped'},'5-7,9-14,16-19,22-23,26-30',5,'裹着的手','手掌伤处包布；第二十三场父亲再次裹好，第三十场她自己系紧松开的布。'),
    ('liji-forehead-blood','li-ji','额角新伤',{'forehead':'fresh_cut_bleeding'},'9',9,'额头,额角的血','祭牌撞破额头，血落到手背；与干浆糊、掌心旧伤分开。'),
    ('liji-forehead-cloth','li-ji','额角压布',{'forehead':'cloth_compress'},'9-14',10,'额上的布','李绡取布压额，阿蘅接替并折紧；李寄走访时仍捏着这块布。'),
    ('liji-forehead-old','li-ji','额角旧伤',{'forehead':'healing_cut'},'31-33',32,'额角的旧伤','斩蛇时额角旧伤被汗浸湿，父亲最后碰未伤的一侧。'),
    ('liji-hand-blood','li-ji','裹手布渗血',{'hands':'blood_seeping_wrap'},'31-33',31,'布透出一点血','第一次斩击震手，布透血；斩蛇后阿蘅托腕避开掌心。'),
    ('liji-exhausted','li-ji','斩击后力竭',{'fatigue':'exhausted','posture':'arms_stiff_knees_weak'},'32-33',32,'膝盖发软,手指仍弯着','连续斩击后手指仍弯、膝盖发软，需阿蘅扶住，不能立刻轻快庆祝。'),
    ('liji-rewrapped','li-ji','归家后手掌重新包扎',{'hands':'rewrapped'},'34',34,'手重新包过','手已重新包过，拿筷子不利索，改用另一只手吃饼。'),
    ('liji-scar','li-ji','掌心新疤',{'hands':'new_scar'},'40',40,'掌心的新疤','补歌本时新疤绷紧，写歪一笔后交笔；不改成新的刀伤。'),
    ('heng-blue','a-heng','洗旧青衣',{'clothes':'washed_blue_rolled_cuffs'},'1-2',1,'洗旧的青衣','清瘦女孩，青衣洗旧、袖口整齐，脚下稳稳打拍。'),
    ('heng-wet','a-heng','浅水中捞书',{'clothes':'wet_lower_clothes'},'3-4',3,'跪倒了,冲进浅水','为捞歌本冲进浅水滑跪；具体湿痕范围在视觉基准中确定。'),
    ('heng-hoarse','a-heng','连唱两日嗓哑',{'voice':'hoarse_after_work'},'7',7,'唱哑的嗓子','第二日黄昏指着唱哑的嗓子，李寄不追问，陪她归家。'),
    ('heng-wet-shoes','a-heng','点名后湿鞋',{'clothes':'wet_shoes'},'8-10',8,'水漫过鞋面','退步撞翻水桶，水漫过鞋面；回家母亲看见湿透的鞋。'),
    ('heng-crying','a-heng','安全确认后哭出声',{'emotion':'relief_with_grief'},'33',33,'先流泪,哭声','确认不再送人后额头抵在李绡肩上，先流泪再哭出声。'),
    ('dan-work','li-dan','码头工衣汗印',{'clothes':'dock_short_coat_sweat_mark'},'14-15',14,'深汗印','短衣、宽肩有深汗印；第十四场另取外衣。'),
    ('dan-load','li-dan','八人压杠承重',{'action':'east_side_load','fatigue':'straining'},'30-33',30,'东侧,胸口几乎','放下刀沿南端绕到东侧，加入后八人持续压，胸口几乎贴膝。'),
    ('dan-sore','li-dan','归家肩部疼痛',{'shoulder':'sore_after_load'},'34',34,'疼得,肩膀','归家被碰肩即缩，仍感觉横杠压着，不虚构骨折或出血。'),
    ('xiao-sweat','li-xiao','压杠不能腾手',{'fatigue':'sweat_stiff_fingers'},'31-33',31,'五姐额上的汗','汗流进眼只能偏头蹭袖，肩不离杠，结束后慢慢掰开僵硬手指。'),
    ('mother-ill','heng-mother','病中需照护',{'health':'cough_and_weakness'},'7,10,15-16,26-27,34',7,'咳得弯下腰','咳嗽、喘气，端碗动作停在中途，需要扶持；第十五场由李诞背走。'),
    ('mother-recovering','heng-mother','归家后仍易疲劳',{'health':'weak_but_attends_song'},'38,40-42',38,'喘口气','回家抱褥子仍需坐下喘气；后坐台下听歌，不表现为完全康复。'),
    ('zhou-apron','zhou','米粉围裙',{'clothes':'flour_dusted_apron'},'1,4',1,'布围裙','腰间布围裙沾满米粉，木斗量米动作熟练。'),
    ('zhou-no-apron','zhou','上门送单未穿围裙',{'clothes':'no_apron'},'20',20,'围裙没穿','到李家送原单时没有穿围裙，仍习惯在衣襟上擦手。'),
    ('zhao-keys','zhao','褐衣腰挂钥匙',{'clothes':'brown','keys':'on_belt'},'2',2,'褐衣人','褐衣、腰间钥匙，与第一集短暂的打招呼反应共同建立身份。'),
    ('zhao-no-keys','zhao','被押下山腰侧空着',{'keys':'absent','custody':'escorted'},'37',37,'腰侧空着','差役押巫祝和赵执事下山，腰侧已无钥匙；剧本未指定囚服。'),
    ('dog-rest','mo-er','卧在街角',{'action':'lying'},'2',2,'街角卧着','瘦黄狗卧街角，左耳缺尖保持方向和辨识。'),
    ('dog-approach','mo-er','跑来接食跟随',{'action':'approach_eat_follow'},'2',2,'摇着尾巴跑来,喂它','被李寄招呼后摇尾跑近，吃阿蘅掰下的一角饼，末尾跟两女孩走。'),
    ('book-intact','songbook','完整而有生字圈',{'condition':'intact_circled_words'},'1-3',1,'生字旁画着圈','未入水前完整，末页生字有圈；第二场夹入旧领唱词纸。'),
    ('book-wet-torn','songbook','浸水裂页失词',{'condition':'soaked_torn_missing_words'},'3-4',3,'浸透的纸,裂开','从装订处裂页，两张纸漂走，一页沉入暗水；许家曲子末句无法续唱。'),
    ('book-dry-gap','songbook','晒干残页夹半行新纸',{'condition':'dried_wrinkled_incomplete'},'5-7,9,16-17,22,37-38',5,'晒干的残页,留下空白','晒干残页与补抄新纸并存，柳影到船边后留白，不能提前画成补齐。'),
    ('book-receipt','songbook','夹有清账凭据',{'insert':'cleared_debt_receipt'},'37-38',37,'折进歌本','清账退粮凭据折进歌本；旧残页状态仍并存。'),
    ('book-repaired','songbook','补词订牢保留旧页',{'condition':'restored_with_old_pages'},'40-42',40,'穿线订牢,旧残页','补齐歌词的新页对齐订牢，泡皱旧残页夹到本后；不是换一本无历史的新书。'),
    ('bag-wages','rice-bag','装有当日工米',{'contents':'today_wage_rice'},'1',1,'才倒进去','先倒当天唱工米；额外预付米是后续独立动作。'),
    ('bag-advance','rice-bag','工米与许家预付米同袋',{'contents':'wages_and_advance'},'1-4',1,'另外抓来一小把米','小木斗倒完后另外抓一小把预付米，阿蘅重新撑袋接住再扎口。'),
    ('bag-returned','rice-bag','预付米已退还、袋口扎紧',{'contents':'wages_after_return'},'4',4,'最后一粒放下','将早先多给的米一粒不剩放回木斗后扎袋，未写把全部工米退光。'),
    ('bag-refund','rice-bag','清账退粮入袋',{'contents':'cleared_debt_refund'},'37',37,'两人的手跟着一道放低','开始是空袋，两女孩共同接退粮，李诞随后接走粮袋。'),
    ('cloth-damp','cloth','蘸水翻面',{'condition':'damp'},'2',2,'蘸湿布巾,翻个面','少量水蘸湿，第一次擦手后翻面继续擦，不突然变成另一条干巾。'),
    ('cake-corner','cake','已掰下一小角',{'condition':'half_with_corner_removed'},'2',2,'小角','半块饼先从李寄交阿蘅，再掰一小角给墨耳；不瞬间整块消失。'),
    ('keys-seized','keys','由程差役收管',{'holder':'officer_cheng'},'19,29',19,'收走赵执事的钥匙','验院后程差役锁门收走钥匙，正式开后门由他开锁。'),
    ('paper-moon-held','paper-moon','卡在蛇嘴',{'position':'paper_snake_mouth'},'8-9',8,'月亮卡在里面','纸月亮含在半张的纸蛇嘴中，点名打断表演，不能自行吐出完成戏。'),
    ('plaque-shaved','name-plaque','新刮边与红绳',{'edge':'fresh_shaving','binding':'red_double_loop'},'8-9',8,'木色,双回结','布包滑开显出新刮木边，借出的红绳有原结；巫祝转面显示阿蘅。'),
    ('debt-covered','debt-note','贴纸遮改为七斗',{'overlay':'attached'},'6',6,'新贴的一小片纸','旧手印前贴纸翘角，露旧墨；赵执事按平并收回，不让阿蘅揭。'),
    ('debt-uncovered','debt-note','原约六斗露出',{'overlay':'removed','text':'本息共六斗'},'22,26,36',22,'本息共六斗','湿润揭纸后原约完整露出，原件和贴纸分别夹好。'),
    ('overlay-removed','debt-overlay','湿揭分离留证',{'condition':'removed_separate_evidence'},'22,26,36',22,'新纸摊在旁边','贴纸与旧据分别摊放、指认原来的相接位置，再分别收存。'),
    ('ledger-one-day','work-ledger','第一日两升',{'earned_grain':'2_sheng'},'7',7,'第一笔工钱','约定一日两升下记第一日工钱。'),
    ('ledger-two-days','work-ledger','两日四升',{'earned_grain':'4_sheng'},'7,26,37',7,'四升','两笔各两升圈在一起，后交核账；不改成两斗或现金工钱。'),
    ('order-first','stop-order','暂停送祭与阿蘅免祭',{'scope':'temporary_stop_and_aheng_exemption'},'17',17,'即刻暂停送祭,免祭文书','县里同意应募准备期间停送、阿蘅免祭、不准抓人补数，阿蘅核对后收入衣襟。'),
    ('order-all','stop-order','任何户均不得索人',{'scope':'all_households_regardless_of_outcome'},'21-22,26',21,'换纸落笔,杀不了蛇','第九集追问除蛇失败后怎么办，新文书补足任何一户都不得索人；与前一纸并存可追溯。'),
    ('lamp-lit','old-lantern','补纸透暖光',{'light':'lit','shade':'patched_crack'},'16,41-42',42,'微黄的光','裂缝补纸透微黄灯光；最终照清松动石阶和回家门槛。'),
    ('lamp-unlit','old-lantern','天亮仍带未点灯',{'light':'unlit','shade':'patched_crack'},'27-29,33-34',27,'灯芯没有点燃','母亲坚持天亮也带上，斩蛇后到家灯仍未点。'),
    ('blade-sheathed','heavy-blade','入套携带',{'condition':'sheathed'},'23,26-27,29',23,'收回套里','试刀后入套，夜放父亲睡铺旁，清晨系入工具捆，进院后再取出。'),
    ('blade-cutting','heavy-blade','同一刀缝直落',{'condition':'in_use'},'23,31-33',31,'刀落下,抽出刀','双手握稳沿缝直下、原路抽回，不撬缝，不伸手入道。'),
    ('channel-original','feeding-channel','原盖石封顶',{'cover':'original_closed'},'18-19',18,'顶上盖严','原有细缝只能察看，盖严通道；不得提前出现可下刀的新缝。'),
    ('channel-cut','feeding-channel','新增窄刀缝',{'cover':'blade_width_slot'},'23-24,29-33',23,'只够刀身穿入','石匠只改外段盖石接边，归位后窄缝只容刀身，其余盖严。'),
    ('channel-covered','feeding-channel','木条暂盖',{'slot':'covered_with_wood_strip'},'24,29',24,'木条盖住刀缝','装杠完毕木条盖缝，正式投饵提闸后李诞才移开。'),
    ('door-open','feeding-door','后闸落底时开启',{'door':'open'},'18,23,29',18,'打开投食门','只在北闸落底插栓后开南门放饵或检验；人与蛇始终有闸隔开。'),
    ('door-barred','feeding-door','关门横闩卡稳',{'door':'barred'},'18-19,23-24,29-33',29,'关门，上闩','收手后关门上闩并推验，提北闸及斩蛇全程南门不动。'),
    ('gate-down','cave-gate','落底插栓',{'gate':'down_pinned'},'18-19,23-24,29',18,'木栓穿回立柱','落到底后插木栓，验牢才准接近或打开南门。'),
    ('gate-up','cave-gate','抽栓提起',{'gate':'raised_unpinned'},'18,29',29,'抽出木栓,提起闸板','木栓抽出置墙边，七人提闸，蛇从北侧进入；不可同时开南门。'),
    ('gate-loaded','cave-gate','压蛇未到底不能插栓',{'gate':'loaded_unpinned'},'30-33',30,'停在半途','压着蛇身落不到底，只能持续承重；断蛇后继续压至确认不动。'),
    ('beam-installed','crossbeam','绑接并试牢',{'load':'unloaded_installed'},'23-24,29',24,'绑接处,结没有松','长杠绑接闸板外横木、检查根脚与两端余地。'),
    ('beam-seven','crossbeam','七人承重',{'load':'seven_people'},'29-30',29,'七人一起','西侧四人、东侧三人；没有李诞，第十三集开始压不住。'),
    ('beam-eight','crossbeam','两侧各四人',{'load':'eight_people'},'30-33',31,'东侧李诞,八个人','李诞加入东侧后两边各四人，斩断后仍压，不能提前少人或松手。'),
    ('rope-pad','hemp-rope','石角有旧布护垫',{'protection':'old_cloth_at_stone_edges'},'29-32',29,'垫上旧布','可能磨到石角的位置加垫，绳张紧时仍能辨认垫布。'),
    ('bait-empty','bait-basin','空盆试位',{'contents':'empty'},'23',23,'空饵盆','改缝时空盆试南端位置，试刀另换湿草，不能带活蛇试刀。'),
    ('bait-filled','bait-basin','肉米饵过刀缝以南',{'contents':'meat_rice','position':'south_of_slot'},'29',29,'刀缝以南','正式饵在新刀缝以南，蛇头完全过缝才落闸；墨耳留家。'),
    ('snake-feeding','snake','由北向南取食',{'action':'feeding_north_to_south'},'18,30',18,'头在前头吃','头探石道取食，身子在洞里，颈横闸下；粗细由李诞大腿比照。'),
    ('snake-held','snake','闸下被压挣动',{'action':'held_struggling'},'30-32',30,'反向一顶,往北滑','闸压住仍上顶，头撞南门，颈部花纹在刀缝下移动。'),
    ('snake-cut','snake','伤口逐次加深',{'injury':'neck_cut_deepening'},'31-32',31,'浅浅一道','第一刀只浅口，第二刀较深，后续砍同一处；非一刀完成。'),
    ('snake-severed','snake','断开后尚待静止确认',{'injury':'severed','action':'residual_motion_then_still'},'32-33',32,'断口的两边错开','断口错开、刀到底，仍有声往山里拖；八人继续压直至确认。'),
    ('rice-shop-day','rice-shop','日间营业',{'time':'day','doors':'open'},'1',1,'米铺开着门','开门量米，门外听歌的人来去，河风掀页。'),
    ('rice-shop-closing','rice-shop','油灯与最后门板',{'time':'evening','doors':'last_panel_open'},'4',4,'一盏油灯,半扇门板','留最后半扇门板等女孩，余一盏油灯，告别后合上。'),
    ('river-day','river-street','日常风与生活动静',{'time':'day','mood':'ordinary_life'},'1-2',2,'晾着衣裳','临河门前晾衣，道具屋幕布与竹器摊同属生活街景。'),
    ('river-night','river-street','归家灯光',{'time':'night','mood':'homecoming'},'19,42',42,'灯罩的补纸,河水拍着岸','河水、轻晃的灯和行走影子，方向连续回到两家的门。'),
    ('li-home-hospitality','li-home','已为病人铺床',{'set':'bedding_for_guest'},'14-16,26-27,34',14,'干净褥子,病人睡床','把干净褥子拿出，病人睡床，外间家人照常劳动与等候。'),
    ('li-home-open','li-home','末尾门未闩温饭',{'door':'unlatched','set':'warm_food_clean_bowl'},'42',42,'门没有闩,干净碗','门半开、灶边温饭、桌留净碗，与第十四场先闩门再开门照应。'),
    ('boat-song-short','boat-song','略两段唱归家',{'performance':'abridged_a_cappella'},'1',1,'阿蘅（唱）,翻过两页','先唱一道险滩，翻两页直接唱靠岸归家；被略歌词不补写。'),
    ('blue-song-missing','blue-awning-song','缺词停在船边',{'performance':'interrupted_missing_lyrics'},'4,38',4,'青篷过河湾,谁也没接','会的段落唱到柳影到船边停止；不是歌曲原作的结束。'),
    ('blue-song-teaching','blue-awning-song','歌娘慢唱补全',{'performance':'taught_and_corrected'},'39',39,'歌娘（唱）,认。回来','歌娘接后半段，放慢末句以确认“认旧桥”，阿蘅重唱连上。'),
    ('blue-song-soft','blue-awning-song','抄写时低唱哼唱',{'performance':'quiet_singing_humming'},'40',40,'低声起唱,轻轻哼完','阿蘅低唱补全句，母亲轻哼末句，声线与台上完整表演协调。'),
    ('blue-song-complete','blue-awning-song','散戏前完整演唱',{'performance':'complete_live_song'},'41',41,'阿蘅（唱）','第一段与补齐的第二段全部唱完，最后一音收住后才有掌声。'),
    ('welcome-lead','snake-welcome-song','前殿集体领唱',{'performance':'temple_lead_chorus'},'7',7,'跟着唱完长句','阿蘅在人群中领唱，两天工钱分别记录，旋律尚待创作。'),
    ('blessing-distant','blessing-stage-song','远处传入家中',{'performance':'offscreen_distant'},'10',10,'米饵献上','庙中祈福唱声远传到家中，与母女拥抱同一时刻。'),
]

PREVIOUS = {
    'liji-clean':['liji-paste'], 'liji-wrapped':['liji-abrasion'],
    'liji-forehead-cloth':['liji-forehead-blood'], 'liji-forehead-old':['liji-forehead-cloth'],
    'liji-hand-blood':['liji-wrapped'], 'liji-rewrapped':['liji-hand-blood'], 'liji-scar':['liji-rewrapped'],
    'mother-recovering':['mother-ill'], 'zhou-no-apron':['zhou-apron'], 'zhao-no-keys':['zhao-keys'],
    'dog-approach':['dog-rest'], 'book-wet-torn':['book-intact'], 'book-dry-gap':['book-wet-torn'],
    'book-repaired':['book-dry-gap'], 'bag-advance':['bag-wages'], 'bag-returned':['bag-advance'],
    'debt-uncovered':['debt-covered'], 'ledger-two-days':['ledger-one-day'], 'order-all':['order-first'],
    'channel-cut':['channel-original'], 'channel-covered':['channel-cut'],
    'gate-up':['gate-down'], 'gate-loaded':['gate-up'], 'beam-seven':['beam-installed'], 'beam-eight':['beam-seven'],
    'snake-held':['snake-feeding'], 'snake-cut':['snake-held'], 'snake-severed':['snake-cut'],
    'rice-shop-closing':['rice-shop-day'], 'river-night':['river-day'],
    'blue-song-teaching':['blue-song-missing'], 'blue-song-soft':['blue-song-teaching'],
    'blue-song-complete':['blue-song-soft'],
}


def readable_inventory(document):
    records = document['records']
    by_id = {r['object_id']:r for r in records}
    entities = [r for r in records if r['kind']=='ENTITY']
    states = [r for r in records if r['kind']=='STATE']
    preparations = [r for r in records if r['kind']=='PREPARATION']
    def title(ref):
        return by_id[ref['object_id']]['payload']['title']
    def evidence(ref):
        ep = ref['object_id'].rsplit('-e',1)[-1]
        blocks = ','.join(b.rsplit('-',1)[-1] for b in ref.get('block_ids',[]))
        return f"E{ep}/{ref.get('scene_id','')} {blocks}"
    def occurrence_scenes(oid, mode=None):
        return [r['payload']['source']['scene_id'] for r in preparations
                if any(o['entity']['object_id']==oid and
                       (o['mode']!='mention' if mode=='shown' else o['mode']=='mention' if mode=='mention' else True)
                       for o in r['payload']['occurrences'])]
    lock = records[0]['payload']
    lines = ['# 全剧实体、状态与逐场出场清单', '',
             f"本清单依据用户已确认的剧本版本四，整版修订 `{lock['screenplay']['revision_id']}`。逐场检查覆盖 17 集、42 场、1,114 个正文块，整理出 {len(entities)} 个实体记录和 {len(states)} 个必要状态。实体记录包括实名对象、匿名角色类别与必要环境物件，数量不等于演员或媒体文件数。", '',
             '画面为二维人物＋轻手绘背景，主画幅 16:9；本任务媒体生产聚焦第一集，交付终点是正式镜头生成前的生产准备。此清单是第一轮审阅材料，尚未获得用户对具体造型、声线、旋律和状态设计的接受。', '',
             '## 使用方法与边界', '',
             '- 稳定实体回答“是谁／是什么”；实体状态定义一个实体在某一时刻的完整形态，统一命名为“实体完整名称·完整形态说明”。衣着、伤势、疲劳等同时存在的特征已经合在同一状态里；候选图的版本、素材数量和普通动作不另造状态。',
             '- 出现分为画面、声音、画面与声音、仅提及。只被提及的阿禾、小满等不因此要求第一集生成角色图或声线。阿禾的回忆出镜另在第十四场登记。',
             '- 表中 E 表示分集，s 表示全剧场次编号，b 表示该场正文块。精确分集修订和全部定位在同目录 inventory.json 与 source-lock.json，可由系统批量解析、校验及导入。',
             '- 剧本事实与制作选择、未知分开。跨场连续性是依据前后文提出的制作安排，状态说明明确标出；没有写出的伤势、服装更换、歌词和曲名不补成事实。',
             '- 一次实际呈现或发声至少引用一个完整状态。同场经过多个状态时，按发生顺序逐对登记转换、动作与准确正文依据；关门→开门→关门可以复用先前形态。',
             '- 需要独立媒体的状态通常采用一份整体参考，允许多个角度、局部或声音补充；整体参考缺失时，细节不能使状态就绪。描述型声音状态保留完整描述，随镜头生成，不要求独立原件。仅提及的小满和许家女儿保留已知事实，不由此生成媒体要求。当前整体参考均待制作、审阅和显式采用。',
             '- “婶婶”“书吏”“庙工”等称呼按所在场次识别，不作全剧无条件别名；未明确同一人的角色保留独立身份或明确的群演类别。', '',
             '## 第一集制作边界', '',
             '第一集包含米铺门口与河街邀请两场。需要李寄、阿蘅、周掌柜、赵执事、挑柴老汉、米铺听客、河街路人、陶伯和墨耳；包括舟行曲、道具屋试鼓、米粮与木斗、歌本及旧词纸、竹篮和河石、水壶与布巾、半块饼、钥匙、削竹刀与竹篮、空小凳、衣裳与幕布。画外鼓手身份未知，台鼓声音按准确状态描述随镜头生成。', '',
             '## 实体与必要状态', '']
    labels = {'character':'角色与群演、动物','space':'空间','prop':'道具与必需环境元素','song':'歌曲'}
    for kind, label in labels.items():
        subset = [e for e in entities if e['payload']['entity_type']==kind]
        lines.extend([f'### {label}（{len(subset)} 项）',''])
        for entity in subset:
            p = entity['payload']; oid = entity['object_id']
            lines.extend([f"#### {p['title']}",'',f"稳定 ID：`{oid}`。" + ('别名：'+ '、'.join(p['aliases'])+'。' if p['aliases'] else ''),'', *p['facts'],''])
            for label2,key in [('制作选择','choices'),('待确认','unknowns')]:
                for item in p[key]: lines.append(f'- {label2}：{item}')
            lines.extend(['',f"呈现／发声：{'、'.join(occurrence_scenes(oid,'shown')) or '无'}。",f"仅提及：{'、'.join(occurrence_scenes(oid,'mention')) or '无'}。",''])
            associated = [s for s in states if s['payload']['entity']['object_id']==oid]
            associated.sort(key=lambda s: (s['payload']['sources'][0]['scene_id'], s['payload']['sources'][0]['block_ids'][0], s['object_id']))
            if associated:
                lines.extend(['| 完整状态 | 完整形态描述（含明确的待审细节） | 来源 |','| --- | --- | --- |'])
                for state in associated:
                    sp = state['payload']; note = sp['blocks'][0]['text'].replace('\n','<br>')
                    lines.append(f"| {sp['title']} (`{state['object_id']}`) | {note} | {evidence(sp['sources'][0])} |")
                lines.append('')
            if p.get('lyrics'):
                for lyric in p['lyrics']:
                    lines.extend([f"{lyric['section']}（{evidence(lyric['source'])}）：",'',f"> {lyric['text']}",''])
                lines.extend([p['composition_status'],*p.get('content_unknowns',[]),''])
            lines.extend(['依据：'+'；'.join(evidence(s) for s in p['sources'])+'。',''])
    lines.extend(['## 42 场覆盖与出场对应',''])
    modes = {'visual':'画面','voice':'声音','visual_voice':'画面与声音','mention':'仅提及'}
    for record in preparations:
        p = record['payload']
        lines.extend([f"### {p['title']}（{p['source']['scene_id']}）",'',f"检查 {len(p['source']['block_ids'])} 个正文块，分集修订 `{p['source']['revision_id']}`。",''])
        for mode,label in modes.items():
            names = [title(o['entity']) for o in p['occurrences'] if o['mode']==mode]
            if names: lines.append(f"- {label}：{'、'.join(names)}。")
        lines.extend(['','| 实体 | 完整状态顺序 | 转换依据 |','| --- | --- | --- |'])
        for occurrence in p['occurrences']:
            if occurrence['mode']=='mention':continue
            lines.append('| '+title(occurrence['entity'])+' | '+' → '.join(title(s) for s in occurrence['states'])+' | '+('；'.join(evidence(t['source']) for t in occurrence['transitions']) or '本场完整形态不变')+' |')
        lines.append('')
    return '\n'.join(lines).rstrip()+'\n'


if __name__ == '__main__':
    if not STATES:
        raise SystemExit('State schedule incomplete; no production inventory published.')
    result=compile_inventory()
    (ROOT/'production/inventory.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    (ROOT/'production/inventory.md').write_text(readable_inventory(result))
    print(json.dumps({'records':len(result['records']),'scenes':42},ensure_ascii=False))
