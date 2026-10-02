"""Authored full forms after reviewing all 42 scenes of locked screenplay four.

Inheritance here is an authoring convenience only. Emitted STATE revisions contain
all dimensions; consumers never combine fragments. Scene schedules describe only
production-relevant changes, not every ordinary movement or facial expression.
"""
from copy import deepcopy

MODEL = 'complete-v1'
DIMENSION_LABELS = {'appearance':'整体外观','clothing':'服装','injury':'伤势','health':'健康','fatigue':'疲劳','voice':'声音','attachments':'随身物',
                    'layout':'空间布局','dressing':'场景布置','time_light':'时间与光照','structure':'完整形态','condition':'状况',
                    'contents':'组成与内容','placement':'使用位置','lyrics_scope':'歌词范围','rendition':'演唱方式','performers':'演唱者'}

# Baseline descriptions are deliberately scoped to an initial/current form, not
# copied from the catalogue's lifetime summaries. Unspecified art stays unknown.
BASE = {
    'li-ji': '女孩李寄；头发跑松，肩有挑水磨出的红印，双手附干浆糊及指缝羊毛。',
    'a-heng': '清瘦女孩阿蘅，洗旧青衣，袖口挽得整齐；能稳定打拍并唱曲。',
    'li-xiao': '李寄五姐李绡，比两个女孩高一头，袖子扎紧，戏班劳作时动作利落。',
    'li-dan': '码头工李诞，宽厚肩背，穿做工短衣，肩上压出深汗印。',
    'li-mother': '李寄母亲，料理家务并照护病人；具体面容、衣着与声线待审。',
    'heng-mother': '阿蘅母亲病中，披旧演出衣，咳嗽、气弱，端碗途中会停，需照护。',
    'zhou': '周掌柜，腰间布围裙沾满米粉，熟练量米；面容与音色待审。',
    'zhao': '赵执事，褐衣，腰挂一串庙院钥匙；声音不高。',
    'mo-er': '墨耳是瘦黄狗，左耳尖缺一角；卧、跑、吃食不另拆形态。',
    'tao': '陶伯是阿禾父亲，年老；削竹生活中的面容、服装及声线待审。',
    'a-he': '阿禾是陶伯女儿；祭队回忆中被带走，回头在围观者里找到李诞；该画面未写阿禾台词。',
    'xiao-man': '小满，去年遭强迫献祭；本剧以名字、母亲证词和遗物追溯，无活人出镜。',
    'sun-liu': '孙六，戏班鼓手，粗壮胳膊裸露；日常做工形态，具体衣色和声线待审。',
    'priest': '巫祝穿深色祭服；面容、服饰细节和声线待审。',
    'clerk-liang': '梁书吏，县衙办理登记与查证的书吏；面容、衣着及声线待审。',
    'officer-cheng': '程差役，鬓边已有白发；差役服装、面容和声线待审。',
    'magistrate': '县丞，在县衙履职时的身份；官服、面容和声线待审。',
    'temple-tall': '瘦高庙工，身形瘦高；借绳与验院确认为同一人，服装和音色待审。',
    'temple-guards': '守院庙工两人，分别可辨，与两个矮凳相配；两人的衣着面容待审。',
    'officer-second': '另一名差役，留守前院与账箱，与程差役保持外观区别；面容衣着待审。',
    'stonemason': '石匠，使用锤凿处理外段盖石；面容衣着与工具细节待审。',
    'helpers-four': '四名乡亲：两人穿码头搬货短褂，两人裤脚沾白灰；各自轮廓须可辨。',
    'elders-two': '两位乡老，各有独立站位与行动；面容、衣着及声音待审。',
    'ticket-woman': '领粮妇人，抱孩子并持粮票、布袋；服装面容待审。',
    'ticket-child': '妇人怀里的孩子，穿鞋；年龄、性别外观和衣色未明。',
    'woodcutter': '挑柴老汉，扁担竖在腿边听曲；年老，衣着和音色待审。',
    'rice-listeners': '米铺门口数名听客，有人提米袋；人数与个体造型待审，不强配主角身份。',
    'street-passers': '河街路人，能向赵执事打招呼；服装、人数与个体造型待审。',
    'neighbor-woman': '邻妇，照看病人和协助家务；面容衣着待审，区别其他未具名邻居。',
    'boatman': '渡口船家，正在装货捆绳；具体性别外貌、服装和音色未明确。',
    'old-woman': '庙仓老妇人，带着瘦女孩；年老，面容衣着与音色待审。',
    'thin-girl': '瘦女孩，与李寄差不多高，手抱碎纸，由老妇人牵着；衣着待审。',
    'clerk-notice': '照壁前抱文书的书吏，身份不与梁书吏合并；面容衣着待审。',
    'clerks-other': '县衙其他书吏，是可区分的群演组成；人数、面容与衣着按镜头审阅。',
    'clerk-proclamation': '宣读告示的书吏，与已革退梁书吏分开；面容衣着声线待审。',
    'xiaoman-mother': '小满母亲，认领断梳并申诉；面容衣着待审，悲痛表演按场次正文。',
    'singer-teacher': '邻村歌娘，晾演出衣并教唱；具体穿着不是晾着的旧红袖，面容声线待审。',
    'new-steward': '新管事，逐行解释清账并退粮；面容、服装及声线待审。',
    'delivery-worker': '送单庙工，当堂指认日期；未与瘦高庙工合并，面容衣着待审。',
    'order-writer': '备粮单经手人，当堂认字迹；面容衣着与声线待审。',
    'temple-crowd': '庙前乡民，有领粮家庭及抬粮汉子等不同组成；态度、站位按正文，造型待审。',
    'troupe-workers': '戏班搬物伙计与台上演员按组成区分，衣着和演出装扮待审。',
    'lead-chorus': '十几个前殿领唱者组成的人群，与阿蘅共唱；各声部与造型待审。',
    'temple-workers': '未具名庙工群演类别；不同场的拧臂者、搬粮者、拖开陶伯者不推定同人。',
    'temple-children': '庙会儿童与家长群体，儿童看戏、家长牵护；人数和造型待审。',
    'procession-crowd': '阿禾被带走时的祭队与围观者，属李诞回忆时空；具体人数服装待审。',
    'ticket-elder': '听不清告示的老人，拿着揉皱粮票；面容、服装待审。',
    'offscreen-caller': '窗外叫李寄归家的人，仅声音，姓名与人物身份未明。',
    'yard-audience': '晒场观众，散场提凳子归家；人数、衣着与组成待审。',
    'xu-bride': '许家即将出嫁的女儿，仅被提及；没有出镜、声音与婚礼画面要求。',
    'snake': '大蛇，体段约李诞大腿粗，有鳞片花纹；身体留北洞，头伸入封顶短石道取食。',
    'rice-shop': '临河街米铺，门外唱曲处接量米柜，内有账与油灯；门口、柜台和街道位置须连贯。',
    'river-street': '街道沿河，米铺、竹器摊、道具屋和民居沿街相连；河岸与归家方向一致。',
    'bamboo-stall': '对街竹器摊，陶伯坐着削篮口，身旁一张空小凳。',
    'prop-house': '道具屋门朝河，屋里戏箱和卷幕布，门槛旁屋外窗台干净，外连浅滩。',
    'shallows': '道具屋外浅滩，有上游、下游石缝和暗水；岸边大石可铺纸。',
    'drying-area': '道具屋外晾布横杆、绳架，与浅滩及对岸相望。',
    'heng-home': '阿蘅家含床、桌、窗、灶、院门及门前松动石阶；病人床与出入口关系清楚。',
    'li-home': '李家含堂屋、里屋、院、灶与可闩门；饭桌、床铺和门保持连贯位置。',
    'temple-front': '庙前殿、石阶、台前、西侧井与东仓门相连；柜和廊下位置清楚。',
    'temple-grain': '山庙仓院存粮、账箱及领粮桌；东门联系前院，区别封闭后院。',
    'temple-back': '高墙接山岩，唯一后门；北洞闸、向南短石道和投食门，外侧留人站位。',
    'hill-steps': '下山石阶连接山庙与河街；廊下、门道及阶下方向清楚。',
    'county-office': '县衙照壁、廊下登记桌和堂前案桌各有位置；不合成无方向的单一背景。',
    'ferry': '临岸货船、窄船板和系船位置；石沿、河面与货舱关系清楚。',
    'singer-yard': '歌娘院子有晾衣绳、旧红袖与小凳，女孩面对歌娘坐。',
    'village-yard': '晒场临时戏台，幕前、台侧、台下观众与通河街出口位置连贯。',
    'songbook': '阿蘅手抄歌本，原装订完整，末页数个生字有圈；尚未夹入领唱旧纸。',
    'rice-bag': '阿蘅随身小布米袋，袋口可撑开扎紧；唱工米入袋前为空袋。',
    'rice-measure': '米铺小木斗，能刮平米再倾倒；容量形制待审，满空变化按动作。',
    'grain': '可辨米粒及各处米粮；工米、预付米、领粮按每场准确数量分组，不混同。',
    'book-basket': '倒扣竹篮，篮底可摊歌本，置米铺门外；非陶伯手上竹篮。',
    'river-stone': '压歌本纸页的河石，置摊开的页上；大小形状待审。',
    'carrying-pole': '挑柴老汉的扁担，竖在腿边，木质具体色泽待审。',
    'water-flask': '阿蘅水壶，壶中有足以蘸湿布巾的水；形制与容量待审。',
    'cloth': '同一条擦手布巾，使用前尚未蘸水；具体材质色泽待审。',
    'cake': '李寄怀中半块饼，尚未掰去喂狗的一角；厚度纹理待审。',
    'paste-wool': '手上已干浆糊和指缝羊毛，少量附着物，不是伤口。',
    'keys': '一串庙院钥匙，第一集挂赵执事腰侧；各齿形与串环细节待审。',
    'lead-lyrics': '几张迎蛇领唱旧纸，可读“米饵奉蛇神，四邻得安宁。”，不改词。',
    'bamboo-basket': '陶伯正在编削篮口的竹篮，有未完成篮口；不是垫书竹篮。',
    'shaving-knife': '陶伯削篮口的小刀，刀形待审；停下、重新刮不增加状态。',
    'empty-stool': '陶伯身旁空小凳，席位无人，大小材质待审。',
    'street-laundry': '临河几户门前晾晒衣物，轻风可动；衣物组成待审。',
    'curtain': '戏班幕布和幕杆关联组成，第一集挂道具屋外；具体花纹待审。',
    'stage-drum': '戏班台鼓，试鼓或演出敲击；鼓型与鼓皮音色待审。',
    'waist-drum': '孙六腰间小鼓，可转到身前敲击；与台鼓分开。',
    'paper-snake': '半副竹骨纸蛇，下颌待装竹条，嘴可开合；非真实山洞蛇。',
    'paper-moon': '可用线操控的纸月亮，纸面完整；形色待审。',
    'stage-tools': '幕杆、竹杆、木槌、凿与戏箱等工具组；本场实际组成按引用正文，不增刀械。',
    'name-plaque': '长木祭名牌，边有新刮浅木色处，牌面阿蘅名字；开始藏于布包。',
    'red-rope': '戏箱角红绳系双回结，绳结拉紧；尚未剪借。',
    'debt-note': '原借据有阿蘅母亲手印；手印前贴新纸篡为七斗并添供奉字样，纸角翘起露旧墨。',
    'debt-overlay': '盖在借据手印前的新贴纸，写添粮条款及“愿入庙供奉”，与原纸相接。',
    'work-ledger': '歌本背页以炭头记下“一天两升”的约定，尚无当天完工数。',
    'grain-ticket': '领粮窄纸票，可核日期和票号；不同持票户各有组成，不同一张票瞬移。',
    'stop-order': '应募准备期暂停送祭、阿蘅免祭且不抓别人补数的文书，含本人非自愿及照票发粮。',
    'volunteer-notice': '照壁旧木告示牌边角晒裂，下钉窄木片写“暂停送人入洞”，列兵刃口粮赏钱。',
    'old-lantern': '李家旧灯，灯罩裂缝补窄纸，灯芯未点。',
    'bandage': '李寄掌心包布，位置与额角布区分；未渗血时形态，具体布色待审。',
    'wood-knife': '家用柴刀，用于劈柴和磨刀；非县库厚背刀。',
    'heavy-blade': '县库厚背刀及配套刀套，刀身可穿窄缝，具体长度、刃形待审。',
    'carrying-strap': '宽布背带，两层粗线补缝可见，可兜病人腿弯；与麻绳不同。',
    'medicine-pot': '煎药罐中药或药渣按场呈现；罐重，需两手或协助托底，形制待审。',
    'rice-urn': '阿蘅家灶边米缸，清账归家时有小半缸粮。',
    'feeding-channel': '北洞到南门的封顶短石道，盖石到成人膝边；原细缝能察看，尚无下刀窄缝。',
    'feeding-door': '石道南端厚木投食门，粗横闩卡牢整石门框；关闭锁稳。',
    'cave-gate': '北端洞闸沿立柱滑动，落到底石，木栓穿牢；蛇在北洞侧。',
    'gate-pin': '穿牢洞闸立柱的木栓，闸落底才可插入。',
    'crossbeam': '尚未绑接的长木横杠，长度能在后院转过而不碰墙。',
    'hemp-rope': '陶伯送来的粗麻绳捆与孙六准备的旧布，尚未装到石角。',
    'bait-basin': '饵盆内拌肉米饵，放在南端投食门内，试验取食用。',
    'meat-rice-bait': '拌肉的米饵，供蛇取食，不含活人或墨耳。',
    'channel-plan': '门、闸和通道位置图，尚未补画新刀缝；南北位置不得颠倒。',
    'grain-order': '窄纸备粮原单写阿蘅家住处、祭户米两斗及庙仓记号；日期早于点名一天。',
    'grain-copy': '照备粮原单抄写的内容和日期，是抄件，非原单。',
    'shop-ledger': '周掌柜米铺底账含收到备粮单日期，夹纸条标出该页。',
    'evidence-chest': '仓院存账箱，带封条，具体外形待审；开箱检查后重新封好。',
    'sacrificial-registers': '前年阿禾、去年小满和当年阿蘅三本祭册，各有年份、名字与自愿入祀记载。',
    'approval-orders': '前两次准祭批文原件两份，签押与今年停祭文书同名。',
    'evidence-receipt': '梁书吏收原据、贴纸和唱工记录后出具的收单凭记；不是原借据。',
    'hairpin': '洞内清出的阿禾竹簪，簪尾浅纹刻歪；以歪纹供陶伯认领。',
    'broken-comb': '洞内清出的半把断梳，有梳齿，供小满母亲认领。',
    'petition': '陶伯折好的诉状，要求旧批文与祭册证据一并送郡复查。',
    'public-verdict': '郡复查告示，包括刑责、革职、非自愿、销祭名、永废人祭与照发接济粮原文。',
    'cleared-debt-receipt': '清账退粮凭据，记旧债销清和多收粮退还，有核验印记。',
    'copied-pages': '晒干泡皱旧残页旁的新抄纸，写到“柳影到船边”后留空，未擅填缺词。',
    'writing-board': '补词夹板与笔，供核词、抄写，新旧纸依本场内容放置。',
    'family-meal': '归家饭食与桌凳组：烙饼、炖肉、炒蛋、汤、净碗和长板凳，数量按本场。',
    'boat-song': '原文两句舟行唱词，一道险滩后翻两页唱归家句；中间两道滩省去。',
    'blue-awning-song': '《送青篷》已会片段，原文未唱出的段落不补写。',
    'snake-welcome-song': '迎蛇领唱调，原旧纸可读“米饵奉蛇神，四邻得安宁。”，前殿集体长句。',
    'blessing-stage-song': '“米饵献上，明月还乡——”从远处庙戏传入阿蘅家，不假定与领唱调同曲。',
}


def default_dimensions(kind, text):
    if kind == 'character':
        return dict(appearance=text, clothing='除上述明确服装外，具体衣饰待首轮审阅。',
                    injury='除上述明示体征外，本阶段其他伤势未明确，不凭空增添。',
                    health='本阶段健康细节未明确；已知病情见完整形态描述。',
                    fatigue='本阶段未明确持续疲劳；瞬时表演按场次正文。',
                    voice='对白、呼吸或动物声依正文；具体声线待审。',
                    attachments='随身及手持物以本场实体引用和动作起止为准；不跨场凭空携带。')
    if kind == 'space':
        return dict(layout=text, dressing='布置按本场引用正文；细部空间尺寸与机位待审。', time_light='具体时段见本场，光线和色彩待审。')
    if kind == 'prop':
        return dict(structure=text, condition='维持上述完整形态，未明确的材质、色泽与磨损细节待审。',
                    contents='组成与内容以上述描述及引用正文为准；未写内容不补造。',
                    placement='持有者与位置依本场引用和动作起止；普通转手不另拆状态。')
    return dict(lyrics_scope=text, rendition='原文所示唱法；旋律、节拍、声线和编配待基准审阅。', performers='按本场原文的实际演唱者。')


# entity -> form key -> (readable label, complete dimension overrides, evidence).
# Evidence is a (scene number, block numbers) tuple. All inherited dimensions are
# materialized by compile_forms. Schedules below are the only timeline authority.
FORMS = {}


def form(entity, key, label, evidence, **dimensions):
    FORMS.setdefault(entity, {})[key] = (label, dimensions, evidence)


def inherit(entity, key, parent, label, evidence, **dimensions):
    values = deepcopy(FORMS[entity][parent][1])
    values.update(dimensions)
    form(entity, key, label, evidence, **values)


form('li-ji','paste','劳作后未擦手',(1,[10,11,30,32]), injury='肩有挑水红印，不是出血伤；掌心磨伤、额角伤尚未发生。', clothing='衣色与造型待审，头发跑松；第一集候选配色未被接受。')
inherit('li-ji','clean','paste','已擦净双手',(2,[5,6]), appearance='李寄，头发仍跑松，肩上仍有挑水红印；手上干浆糊和羊毛已擦净。')
form('li-ji','wet','捞书后衣裤湿',(3,[24,27,28]), appearance='李寄，下水捞页后衣裤湿；头发与此前造型保持身份。', clothing='卷起裤脚仍湿，第四场湿裤脚滴水；具体湿痕待审。', injury='下水失足但被阿蘅扶稳，未写新增伤口；后续掌心磨伤、额角伤尚未发生。')
form('li-ji','abrasion','劈柴掌心磨破',(5,[1,6,13]), appearance='李寄，掌心磨破沾木屑，清洗处理中。', injury='一只手掌磨破，清理木屑；额角未发生祭牌伤。', clothing='前晚被嘱换湿衣，本日日常衣物按连续性安排为干衣，具体款色待审。')
form('li-ji','wrapped','掌心包布、额角未伤',(5,[26,27]), appearance='李寄，双手已擦净，掌心旧磨伤已包布；额角尚未受祭牌伤。', injury='掌心包布保护旧伤，不给额角提前加伤。', clothing='日常干衣，款色待审。')
inherit('li-ji','splash','wrapped','掌心包布、裤脚溅湿',(6,[2,31]), clothing='挑水涉浅滩后裤脚溅水；衣物款色待审。')
inherit('li-ji','fresh','wrapped','掌心包布、额角流血',(9,[6,17]), appearance='李寄，掌心旧伤包布并存额角新伤。', injury='祭牌撞破额角，血滴到手背；掌心为旧磨伤。')
inherit('li-ji','compress','fresh','掌心包布、额角压布',(9,[26]), injury='掌心包布；额角新伤用另一块布压住或扎紧，位置分别清楚。')
inherit('li-ji','healing','compress','掌心包布、额角旧伤',(23,[19,20]), appearance='李寄，掌心旧伤包布；额角已是旧伤，不能每场重新出血。', injury='掌心磨伤仍需裹好；额角旧伤可见，何时去除额布未明，作为待审连续性安排。')
inherit('li-ji','blood','healing','裹手布渗血、额角旧伤',(31,[17,19,20,21]), injury='斩击震手使一只手的包布渗血；额角旧伤并存，非新砸伤。', fatigue='持重刀斩击后呼吸急，尚未到断蛇后力竭。')
inherit('li-ji','spent','blood','斩击力竭、手布渗血',(32,[17,20,21,22]), fatigue='连续斩击后手指仍弯、膝软，需搀扶；汗浸额角旧伤。', appearance='李寄，汗湿额角旧伤，掌心包布渗血，四肢疲软；身形与原身份一致。')
inherit('li-ji','rewrapped','spent','归家重新包手',(34,[17,21]), appearance='李寄，掌心已换新布包扎，额角旧伤仍需保持连续；战后余疲尚在。', injury='手掌已重新包扎，额角旧伤；拿筷子不利索。', fatigue='战后余疲尚在，能坐下进食，不能立刻轻快庆祝。')
form('li-ji','scar','掌心新疤',(40,[2,17]), appearance='李寄，掌心新疤，容貌和比例延续既有身份。', injury='掌心新疤用力时绷紧；额角伤后外观程度未明确，连续性待审。', fatigue='较斩蛇当天已过去一段时间，未写持续力竭；不外推完全康复。', clothing='日常衣物，具体款色待审。')
form('a-heng','blue','日常洗旧青衣',(1,[1,6]), clothing='洗旧青衣，袖口整齐挽起；具体配色和补缀待审。')
form('a-heng','wet','捞书后湿衣袖',(3,[20,28]), appearance='清瘦阿蘅，捞书滑跪入浅水，袖口和下身有湿痕。', clothing='原青衣湿，第四场米粒粘湿袖；具体湿痕待审。')
form('a-heng','hoarse','连唱后嗓哑',(7,[4,5]), appearance='清瘦阿蘅，身份衣着延续日常基准。', clothing='洗旧青衣，袖口整齐挽起；此前湿衣已干的连续性安排待审。', voice='连续两日领唱后嗓哑，能以手示意嗓子；具体沙哑程度待声音审阅。')
inherit('a-heng','wet-shoes','hoarse','嗓音劳累、鞋被水浸',(8,[35]), clothing='青衣延续，水漫过鞋面，鞋湿透；衣摆湿痕范围待审。', voice='前两日唱哑，庙会当天有对白；残余沙哑程度未明，不能自动当作完全恢复。')
form('a-heng','later','点名后日常形态',(16,[14,19]), appearance='清瘦阿蘅，身份沿用已确认青衣方向；已穿好鞋，未再标湿鞋。', voice='对白与后续演唱依场次；持续沙哑未再明写，恢复程度是待审选择。')
inherit('a-heng','tears','later','确认安全后泪痕',(33,[24]), appearance='清瘦阿蘅，原衣着，脸上泪痕；额抵李绡肩后哭出声。', voice='从极轻问话到喘出哭声；不是新增固定声线。')
form('li-dan','work','码头短衣汗印',(14,[2]), clothing='码头做工短衣，宽肩有深汗印。')
form('li-dan','memory','前年祭队旁的李诞',(14,[15]), appearance='李诞，在前年阿禾祭队回忆中握挑货扁担，未迈出。', clothing='回忆时码头衣着具体细节未写；不复制当晚新汗印为事实。', voice='该回忆段未写李诞对白。')
form('li-dan','coat','码头衣加外衣',(14,[21,35]), appearance='李诞，宽肩，做工短衣外加外衣。', clothing='穿上外衣，翻好卷起的袖子；后续干湿与细节按连续性审阅。')
inherit('li-dan','loaded','coat','压杠汗湿承重',(30,[9,11,14]), fatigue='持续压杠，胸近膝、呼吸断续，肩不能离杠。', clothing='原工作衣与肩垫，汗湿程度随承重；垫布仍在肩上。')
inherit('li-dan','sore','loaded','卸杠后肩痛',(34,[3,24,25]), clothing='原工作衣延续；肩垫已磨落，不再画在肩下。', fatigue='卸载后肩痛、抬臂迟疑，未写骨折出血。')
inherit('li-dan','after','coat','后续作证与清账',(36,[22,27,30]), fatigue='斩蛇后作证与清账时未再明写肩痛；恢复程度待审，不沿用压杠姿态或预认完全康复。')
inherit('li-dan','recovered','coat','后期日常做工',(41,[2,6]), fatigue='斩蛇一个多月后能扶幕杆；未写持续承重后肩痛，不外推其他健康事实。')
form('li-xiao','loaded','压杠汗湿承重',(31,[6,15]), fatigue='肩不离杠，汗流眼中只以袖擦；仍持续承重。')
form('sun-liu','loaded','持续压杠',(30,[24,25]), fatigue='持续肩压横杠，仍在承重，不能提前坐下卸力。')
form('helpers-four','loaded','四人压杠衣着与疲劳',(30,[24,26]), fatigue='四人持续承重，胳膊、腿发颤；袖口扎好，码头短褂与白灰裤脚仍可辨。')
form('officer-cheng','loaded','压杠承重',(32,[15]), fatigue='压杠时膝抵石基，仍在承重；未写新增伤口。')
form('heng-mother','recovering','归家仍易疲累',(38,[2]), appearance='阿蘅母亲，归家后仍气弱，能轻哼并坐台下听歌。', health='抱褥子需坐床沿喘气，不表现为完全康复。', clothing='居家衣着待审；第四十一场膝搭薄衣，散场披上。', fatigue='稍用力即需喘息。', voice='轻哼或轻声说话，音色与前期病声保持同人。')
form('zhou','plain','未穿围裙的出门形态',(20,[1]), appearance='周掌柜，面容与店内一致，未穿围裙。', clothing='普通外出衣，无米粉围裙；习惯仍在衣襟擦手。')
form('zhao','no-keys','褐衣、腰侧无钥匙',(19,[17,19]), appearance='赵执事，褐衣身份不变，腰侧钥匙已被收走。', attachments='腰侧空着；不得把钥匙画回，其他手持物按本场。')
inherit('zhao','custody','no-keys','无钥匙、被押解',(37,[3,4]), appearance='赵执事，腰侧空着，由差役押下山；原文未指定囚服。')
form('priest','custody','被押解形态',(37,[3,4]), appearance='巫祝，由差役押下山；保持身份，原文未指定囚服。')
form('ticket-child','one-shoe','掉一只鞋',(8,[19]), clothing='原衣着，一只鞋掉落，随后穿回；鞋形待审。')


def prop(entity, key, label, evidence, description):
    form(entity, key, label, evidence, structure=description,
         condition='完整形态如上；材质、颜色及未写磨损细节待审。')


prop('songbook','inserted','完整本夹领唱旧纸',(2,[20,22]), '阿蘅手抄歌本，装订未损，生字圈仍在；夹有赵执事给的几张迎蛇领唱旧纸。')
prop('songbook','papers-on-top','完整歌本上放领唱旧纸',(2,[20]), '阿蘅手抄歌本，装订未损，末页生字圈保留；赵执事给的几张旧纸平放本上，尚未合入。')
prop('songbook','wet','浸水裂页失词',(3,[20,24,28,29]), '同一手抄歌本浸湿，从装订处裂开，末段仅半页且洇黑；部分纸漂失，领唱旧纸是否留存未明，不凭空复原。')
prop('songbook','dry','晒干残本与未补全新页',(5,[14,19]), '同一歌本的泡皱残页晒干，夹入新抄纸；“柳影到船边”后留空，生字旧迹按残页可见范围保留。')
prop('songbook','account','残本增加记工背页',(6,[28]), '晒干泡皱残本，未补全歌页与记工背页并存；背页先记一天两升，后按场加入日期及两笔工钱，不提前补词。')
prop('songbook','receipt','残本夹清账凭据',(37,[18]), '晒干残本仍缺末词，未补全新页和已记唱工内容保留；夹入清账退粮凭据。')
prop('songbook','repaired','补齐订牢并保留残页',(40,[14,15,16]), '同一本歌本，歌词已核正补全，新页穿线订牢；旧泡皱残页夹在本后，已有凭据与记录不擅删，具体归放待审。')
prop('rice-bag','wages','装当天唱工米',(1,[17,19]), '同一小布袋，已接小木斗倒入的当天唱工米，尚未添许家预付米；袋口正收拢。')
prop('rice-bag','advance','工米与预付米同袋',(1,[23,26]), '同一小布袋，当天工米加额外一小把许家预付米；袋口已可扎紧，未凭空分成两袋。')
prop('rice-bag','returned','退回预付米后扎袋',(4,[13,15,16]), '同一小布袋，多给的一小把米逐粒退回木斗后扎紧；剩余工米未写退光。')
prop('rice-bag','refund','共同接退粮后的米袋',(37,[21,22]), '同一布袋接入清账退粮，重量使袋底下沉；系好袋绳后由两女孩共提，随后李诞接过。')
prop('cloth','damp','蘸水擦手后翻面',(2,[2,5]), '同一擦手布巾已蘸少量水，擦过浆糊和羊毛后翻面继续用；污湿范围待审。')
prop('cake','corner','半饼缺一小角',(2,[8]), '原半块饼掰去喂墨耳的一小角，余下主体仍在；缺口连续，不瞬间消失。')
prop('paste-wool','removed','从指缝搓落并擦除',(2,[5,6]), '少量干浆糊与羊毛已从手指搓落、擦到布上；手上不再附着，绝非血污。')
prop('paste-wool','paste','道具制作浆糊',(3,[5,6]), '端来供纸蛇装竹条的浆糊，容器与量待审；不是第一集已擦除的手上残渣。')
prop('stage-drum','audible','画外试鼓与起鼓',(2,[31]), '戏班台鼓的画外声音，第一集从道具屋方向传来，鼓体不要求出镜；实际鼓型和敲击音色待审。')
prop('keys','cheng','程差役收管钥匙',(19,[17]), '同一串庙院钥匙由程差役收走，赵执事腰侧空；祭日由程差役持它开锁。')
prop('curtain','wet','洗晾中的湿幕布',(3,[7,15]), '戏班幕布洗过，沉重湿布可滴水、拧干，晾在横杆；不是另一套新幕。')
prop('curtain','stage','搭台演出幕布',(8,[3,20]), '同批戏班幕布安装为台前与后台分界，有幕缝；具体干湿依晾后连续性待审。')
prop('curtain','packed','散场卸下幕杆',(41,[18]), '散场卸下的幕杆与幕布，李绡和孙六各扛一头，回道具屋靠稳；折卷方式待审。')
prop('paper-snake','assembled','装好竹条可开口',(3,[6]), '竹骨纸蛇下颌已装好竹条，纸嘴可开合；仍为戏班道具，不等同真蛇。')
prop('paper-snake','moon','半张蛇嘴含纸月亮',(8,[12,27]), '完整纸蛇嘴半张，纸月亮已含住，牵线停时仍卡在里面；纸面和竹骨待审。')
prop('paper-snake','boxed','收进戏箱',(18,[1]), '演后纸蛇已收进戏箱，外观延续道具身份；收纳折叠方式未写，待审。')
prop('paper-moon','held','卡在纸蛇嘴中',(8,[12,27]), '同一纸月亮由牵线放低后卡在半张纸蛇嘴中；点名打断，未完成吐月动作。')
prop('name-plaque','bound','新刮牌边绑红绳',(8,[24,31,32]), '长木祭名牌，边新刮浅木色；借来的红绳连原双回结绑在牌下，牌面写阿蘅。')
prop('red-rope','cut','剪借后绑祭牌',(8,[23,31]), '从戏箱角剪出的一段红绳，保留双回结，系到新刮边祭牌下；拉扯不新增材质损坏。')
prop('debt-note','uncovered','揭纸露原约六斗',(22,[10,12,23]), '原借据手印仍在，盖纸已湿揭分离，完整露出“本息共六斗”；原件单独夹好留证。')
prop('debt-overlay','removed','湿揭后独立留证',(22,[12,13,14,23]), '篡改贴纸从旧据湿揭下，仍见添粮与“愿入庙供奉”；与原据分别摊放、夹好，不撕毁。')
prop('work-ledger','one','约定下记第一日工钱',(7,[3]), '歌本背页已有“一日两升”约定，增加第一日日期与两升，第二日尚未记入。')
prop('work-ledger','two','两日四升记录',(7,[5]), '同一记工纸有两个日期、各两升，圈在一起为四升；后取出交验，不改成两斗或现银。')
prop('stop-order','all','除蛇成败都不得索人',(21,[16,17,23]), '新白纸文书承接停祭免祭、照发粮要求，补明除蛇成败都不准向任何一户索人；盖印。')
prop('old-lantern','lit','裂缝补纸透暖光',(16,[3]), '同一旧灯，罩裂缝补窄纸，灯芯点亮，补纸透微黄光；色温与亮度待审。')
prop('bandage','head','掌心裹布与额角压布',(9,[26]), '同一组伤处布：掌心旧伤包布，另一块压额角新伤；两处清楚，不合成一条缠全头的布。')
prop('bandage','blood','掌心布渗血',(31,[20]), '掌心包布受斩击震动渗少量血；额角旧伤并存，额布是否仍用待审，不提前画新伤。')
prop('bandage','new','归家重新包扎',(34,[17]), '归家手掌重新包过的干净布，仍影响拿筷；不得沿用满血旧布当新包扎。')
prop('heavy-blade','sheathed','入套携带保管',(23,[35]), '同一县库厚背刀插入刀套，夜放父亲睡铺旁，次晨系入工具捆；尺寸身份保持。')
prop('heavy-blade','bloody','斩蛇后的刀刃',(31,[16,19]), '同一厚背刀出套，刃沿窄缝反复斩击，开始沾蛇伤痕迹；未写崩刃，血污范围待审。')
prop('feeding-channel','cut','盖石新增窄刀缝',(23,[12,14,16]), '原封顶短石道，仅外段两盖石接边凿出刀身宽狭缝；其余盖严，北洞口未扩大。')
prop('feeding-channel','covered','窄刀缝上盖木条',(24,[5]), '外段已留刀身宽窄缝，现以木条临时盖住；其余盖石严实。')
prop('feeding-door','open','南门开、北闸插栓',(18,[20]), '南投食厚木门横闩抽开、门开启，北洞闸必须落底插栓；人可退出手后关门，具体门扇轴位待审。')
prop('cave-gate','up','洞闸提起、木栓抽出',(18,[24]), '北洞闸沿立柱提起，木栓已抽出；南投食门须关好卡稳，蛇可由北入道。')
prop('cave-gate','loaded','压蛇半落、不能插栓',(30,[3,5]), '北洞闸压在蛇身上未落底，木栓不能插回，需人持续肩压横杠；南门仍闩牢。')
prop('cave-gate','released','断蛇确认后卸力仍封闭',(33,[11,12,14]), '确认断蛇后人慢慢卸力，闸板未再上顶；原文未写落底插栓，不擅画插牢，门仍不许开。')
prop('gate-pin','out','抽出放墙边',(29,[17]), '同一洞闸木栓抽出，置身后墙边；闸压蛇未到底时保持未插入。')
prop('crossbeam','installed','横杠绑接试牢',(24,[1,3,4]), '长横杠绑在洞闸外横木，结已收紧试牢，两端留空；尚未七人承重。')
prop('crossbeam','seven','七人持杠承重',(29,[14,17]), '绑牢长横杠西侧四人、东侧三人，七人提闸及压杠；李诞尚在西侧看缝。')
prop('crossbeam','eight','八人持续压杠',(30,[9,10]), '同一绑接长杠，李诞加入东侧，东西各四人持续承重；直到断蛇确认前不松肩。')
prop('hemp-rope','padded','石角加垫并绷紧',(29,[2]), '同一粗麻绳加固横杠，可能擦石角处垫旧布，绳与布可分别辨认；张紧但未写断裂。')
prop('bait-basin','empty','空盆试位',(23,[12,17]), '同一饵盆空置在南端试位，随后取出换湿草试刀；盆形身份保持。')
prop('bait-basin','south','装饵推至刀缝以南',(29,[6,8,9]), '同一饵盆装拌肉米饵，已推至新刀缝以南，蛇头须先过缝才能吃；不是空盆。')
prop('channel-plan','slot','补画刀缝的通道图',(26,[11,12]), '门闸通道图上新补刀缝，空碗示南饵位、筷子示横杠；原南北门关系不变。')
prop('evidence-chest','open','原据查验中开箱',(22,[7]), '仓院账箱验封后打开，取原据查验，差役在旁；不是封册场另一箱的确定同件。')
prop('evidence-chest','registers','三年祭册装箱封存',(28,[25,40,41]), '装三年原祭册的账箱，封箱最后纸条贴平，差役看守；与仓院旧账箱是否同件未明。')
prop('sacrificial-registers','copies','县衙祭册抄本与今年册',(17,[19,24,42]), '县衙调出前两年报送祭册抄本，另有今年报送册；姓名年份可读，不把抄本当后日封出的三本原件。')
prop('approval-orders','copies','旧批文公开抄件',(37,[6]), '前两次准祭批文的抄件两份，贴在复查告示旁；签押与原件一致，不冒充原纸。')
prop('copied-pages','confirmed','歌娘核全歌词的新纸',(39,[7,11,12]), '旧泡皱残页与新核词纸并存，末句确认“归来认旧桥”；已补正误字，未装订。')
prop('copied-pages','bound','新页补抄订牢',(40,[9,14,15,16]), '核全歌词重新抄好的新页已与本子穿线订牢，线结压平；旧残页夹后保存。')
prop('family-meal','prepared','备饭材料与空碗',(27,[4,5,7,8]), '李家半袋白面及炖肉、鸡蛋等备饭材料，碗在灶边数好；还未变成上桌熟菜。')
prop('family-meal','warm','灶边温饭桌留净碗',(42,[20]), '家中灶边温着饭，桌上留一只净碗；不是斩蛇归家那桌宴席仍摆到一个多月后。')

form('snake','held','完整蛇身受闸压',(30,[3,6,11]), appearance='大蛇同一鳞片花纹，头在南门内、颈受北闸压，身体留洞，尚未刀伤。', injury='闸压但未开始斩击；具体受压变形待审。')
inherit('snake','shallow','held','颈部浅刀口',(31,[19]), injury='颈部同一处第一刀浅口，鳞片仍挣动，不提前断开。')
inherit('snake','deep','shallow','同处伤口加深',(32,[4,5]), injury='第二刀和后续刀落同处，伤口逐渐加深，仍未断开。')
inherit('snake','severed','deep','断口错开仍有余动',(32,[18,20,24,26]), injury='颈断开，断口两边错开，刀可触底石；仍听洞内擦撞余动。')
inherit('snake','still','severed','断开后确认静止',(33,[4,6,7,9,10]), fatigue='等待、察看后确认不再动，不能在断开瞬间就宣布静止。')


def space(entity, key, label, evidence, dressing, light):
    form(entity, key, label, evidence, dressing=dressing, time_light=light)


space('rice-shop','day','日间开铺',(1,[1,17]), '门开，量米柜营业；外有倒扣篮、歌本和听客。', '日间，具体光色待审。')
space('rice-shop','closing','留最后门板与油灯',(4,[1]), '半扇门板留开，柜上腾位看残页，一盏油灯；末尾合上门板。', '暮色至入夜，油灯照纸。')
space('river-street','day','日间河街',(2,[1]), '临河晾衣、米铺檐、对街竹器摊、道具屋幕布。', '日间；同一生活街景规则。')
space('river-street','night','夜路与家灯',(19,[22]), '沿河民居灯亮，归家动线不变；具体亮灯户和道具按场。', '入夜河水与家灯／手提灯，明暗待审。')
space('river-street','dawn','清晨出门',(27,[16,23]), '民居巷口接山路，晨间生活布置。', '清晨天亮，随身旧灯未点。')
space('bamboo-stall','day','日间削篮摊位',(2,[24,32]), '陶伯座旁空小凳，手中竹篮与削竹刀。', '同一日间河街光线。')
space('prop-house','work','日间道具制作处',(3,[1,2]), '戏箱、卷幕布、干净窗台、纸蛇与幕杆；门外连浅滩晾架。', '日间到暮色，具体时段随场来源。')
space('prop-house','night','夜间归还幕杆',(42,[19]), '戏箱旁靠稳拆回的幕杆。', '夜间提灯与屋内光，细部待审。')
space('shallows','day','日间洗布浅滩',(3,[7,15]), '石头、流动河水、洗布盆，能沿浅滩过河。', '日间。')
space('shallows','dusk','暮色残页岸边',(3,[29]), '岸边大石铺满湿残页，暗水吞去失页。', '暮色落下，不能当作晴昼。')
space('drying-area','wet','洗晾湿幕布',(5,[23,28]), '湿幕布展开挂绳，横杆滴水；第六场旁有记工炭头。', '日间，具体色彩待审。')
space('heng-home','sick','病中居家',(7,[6,16]), '病床、旧演出衣、水壶与药罐；窗下歌本桌。', '按本场日间／清晨来源，灯光切换在镜头注明。')
space('heng-home','guarded','门外庙工守院',(10,[16,17]), '病床照护布置，院门旁两个庙工和矮凳；窗扇合上。', '庙会当日稍后；入夜搬人时门外邻里举灯。')
space('heng-home','return','债清归家的房间',(38,[1,2,3]), '灶边米缸小半缸粮，床脚叠褥，窗台摊新旧歌页。', '日间，窗外河水可闻。')
space('heng-home','lamplit','灯下补词与归家',(40,[1,14]), '床、桌、补全新页与保留旧页，门外松动石阶不变。', '夜间灯下，第四十二场门内光接手提灯。')
space('li-home','dinner','晚饭桌与门闩',(14,[1,9,16]), '灶上汤、碗桌、缺口小碗，门可闩；尚未铺好病人床。', '晚饭时至夜间。')
space('li-home','guest','病人床与临时睡铺',(14,[38,44]), '干净褥子为病人留床，家人临时睡铺、灶与院门保持位置。', '夜间与黎明交接依场内时间，具体分镜需注明。')
space('li-home','day','日间接待与备图',(20,[1,12,18]), '病人留宿布置仍在，桌上可放夹板、图和水碗。', '日间，室内光待审。')
space('li-home','meal','除蛇归家众人用饭',(34,[2,5,10,16]), '院搭长板、邻家借凳，饼肉蛋汤上桌；病人仍在里屋，门留缝。', '归家时，旧灯仍未点。')
space('li-home','open','夜归门未闩',(42,[20,22]), '灶边温饭，桌留净碗，门半开未闩；不再预设病人住在李家。', '夜间旧灯光落门槛外。')
space('temple-front','chorus','前殿白日领唱',(7,[1]), '十几个领唱者，殿门外亮；台前布置按需要明确。', '白日领唱，后切黄昏路口。')
space('temple-front','festival','庙会戏台与粮票队',(8,[2,20,28]), '中央戏台，西井、东仓门队伍、正殿阶前，纸蛇戏与祭牌。', '清晨至午后日影移动。')
space('temple-front','sealed','拆台后封祭册柜',(24,[6,11]), '戏台已拆去半边，神龛后柜贴封条，差役廊下守。', '备战日下午至暮色。')
space('temple-front','grain','祭日领粮与封册',(28,[1,25,40]), '领粮队、柜中取册并封箱，前院留道，巫祝赵执事受看守。', '第三日清晨至日间。')
space('temple-front','verdict','新告示与旧批文抄件',(37,[1,2,6]), '新告示贴墙、旁贴两份旧批文抄件，群众听读领粮。', '二十多天后日间。')
space('temple-grain','stock','囤粮与记账',(12,[1]), '米袋堆高、赵执事桌后勾账，搬粮通道可过。', '庙会当日，具体光色待审。')
space('temple-grain','sealed','封账与原据查验',(22,[5,7,27]), '封账箱、桌上新文书与原据，差役验封看守。', '次日查证，具体光色待审。')
space('temple-grain','refund','新管事清账退粮',(37,[13,21]), '清账桌在亮处，队伍推进，木斗向米袋倒粮。', '二十多天后日间。')
space('temple-back','original','原盖石、未绑长杠',(18,[2,7]), '南厚门、北落闸与木栓，原盖石细缝，尚无刀缝及加装横杠。', '初次午后验院至暮色。')
space('temple-back','cut','已开刀缝、长杠待绑',(23,[16,35]), '盖石外段已凿窄刀缝，其余盖严；长杠抬到立柱旁，尚未绑接，不提前加盖条。', '加工日间，具体光色待审。')
space('temple-back','bound','长杠已绑、刀缝待盖',(24,[3,4]), '盖石外段已凿窄刀缝，长杠已绑闸板外侧并检查绳结；刀缝尚未盖木条。', '第二日收工前，具体光色待审。')
space('temple-back','modified','已开刀缝和绑杠',(24,[1,3,5]), '盖石外段窄缝、临时盖条、已绑长杠；后门到石道无工具阻道。', '第二日加工至暮色。')
space('temple-back','battle','祭日绳垫与空门道',(29,[1,2,5,11]), '长杠加绳与旧布护垫，西侧平石放刀；灯在后门内靠墙，门道留空。', '第三日清晨至日间，院内无鼓声。')
space('hill-steps','dusk','暮色下山',(25,[7]), '后门外至廊下石阶，连河街家灯。', '暮色或入夜，按来源场次保持连续。')
space('hill-steps','day','日间押解下山',(37,[4]), '石阶通庙前与山下，差役押两人行进。', '二十多天后日间。')
space('county-office','notice','照壁临近关门',(13,[1,2,8]), '旧应募木牌与窄木条，抱文书的书吏将离开。', '当日将关衙，具体光色待审。')
space('county-office','register','白日登记与问话',(17,[1,37]), '廊下登记桌，文书、册子、图纸按当天用途置放。', '日间，日影移过廊柱。')
space('county-office','relic','廊下认领遗物',(35,[1,2]), '小桌两块净布、竹簪、断梳，长凳中间留空。', '数日后，日间光色待审。')
space('county-office','hearing','堂前证据问责',(36,[1,32]), '案桌陈三本祭册、借据贴纸、原单、底账、旧批文及诉状。', '认遗物后堂内，光色待审。')
space('ferry','loaded','货船临岸装货',(11,[1]), '货船贴岸、窄板晃，舱里装箩筐。', '庙会当日稍后。')
space('ferry','withdrawn','船板撤离岸边',(11,[7,9]), '同一货船，窄船板已拖回，岸沿露水；不另造码头。', '与前一状态连续。')
space('singer-yard','day','日间晾衣教歌',(39,[1,20]), '旧红袖晾绳、歌娘及女孩小凳，新旧歌词纸。', '日间，轻风晃衣绳。')
space('village-yard','setup','搭幕杆待开场',(41,[2,6]), '戏箱、幕杆、绳结，准备演出。', '暮色前搭台。')
space('village-yard','song','暮色演唱至散场',(41,[7,17,18]), '幕前唱歌、台侧歌本、台下病人及观众，末尾卸杆。', '暮色转夜，散场点旧灯。')

form('boat-song','short','省段清唱归家句',(1,[2,3,4]), rendition='阿蘅清唱，一道险滩后翻两页转归家句；不补未知省段。', performers='阿蘅。')
form('blue-awning-song','practice','受损前低声练曲',(3,[15]), rendition='阿蘅洗布时低声练《送青篷》，未给出的句段不补写。', performers='阿蘅。')
form('blue-awning-song','missing','缺词处停下',(4,[4,5,7]), lyrics_scope='“青篷过河湾，柳影到船边——”后无法接词；不是作品原本结尾。', rendition='唱或哼到缺词处停下；第五场哼而摇头，第三十八场母女同停。', performers='阿蘅；第三十八场母亲先哼、阿蘅接唱。')
form('blue-awning-song','teaching','歌娘核词接全',(39,[5,7,11,14,16]), lyrics_scope='第二段从船边接到“莫怕远山高，隔水灯相照。明年春水暖，归来认旧桥——”。', rendition='歌娘慢唱核“认”字，阿蘅跟唱并自行连上；不改歌词。', performers='阿蘅与歌娘。')
form('blue-awning-song','soft','补抄时低唱轻哼',(40,[10,12,13]), lyrics_scope='已核全第二段，含“莫怕远山高，隔水灯相照”和末句。', rendition='阿蘅低唱，母亲轻轻哼完末句；曲调与台前版同源。', performers='阿蘅、母亲。')
form('blue-awning-song','complete','暮色台前完整演唱',(41,[9,11,13,14]), lyrics_scope='按实体准确歌词原文完整唱第一段和补全第二段。', rendition='完整演唱，尾音收住后才有掌声；旋律及伴奏待审。', performers='阿蘅。')
form('snake-welcome-song','chorus','前殿集体领唱',(7,[1]), rendition='阿蘅与十几个领唱者共唱长句，两日工作；未知长句歌词不凭空补写。', performers='阿蘅及前殿领唱众人。')
form('blessing-stage-song','distant','远处戏声',(10,[10]), rendition='唱声顺河面远传入家，唱毕喝彩；声场距离按镜头设计。', performers='庙中未具名戏班演唱者。')

for entity, evidence, fatigue in [
    ('li-xiao',(33,[18]),'卸杠后慢慢掰开僵硬手指，仍有汗和承重余疲。'),
    ('sun-liu',(33,[15,16]),'卸杠后腿抖，只能靠墙坐下，先咳一声；归家时仍需稳端碗。'),
    ('helpers-four',(33,[1,15]),'卸杠后退出，保留承重后的腿抖、汗湿，程度按各人表演。'),
    ('officer-cheng',(33,[13,14]),'卸杠后扶石盖才站稳，仍留守，不凭空添新伤。')]:
    inherit(entity,'spent','loaded','卸杠后余疲',evidence,fatigue=fatigue)
inherit('li-dan','pad-fallen','loaded','压杠、肩垫磨开',(32,[6]), clothing='工作衣汗湿，肩上垫布已磨开，布角落下；不能松手调整。')

# Explicit scene schedules. An initial form is followed only by real material
# transitions. Re-entering an earlier form (closed -> open -> closed) is valid.
SCHEDULE = {}


def use(entity, scene_numbers, key):
    from production_inventory import scenes
    for sn in scenes(scene_numbers):
        SCHEDULE[entity, sn] = [(key, None)]


def sequence(entity, sn, *steps):
    SCHEDULE[entity, sn] = list(steps)


use('li-ji','1-2','paste'); sequence('li-ji',2,('paste',None),('clean',[6]))
sequence('li-ji',3,('clean',None),('wet',[24,27,28])); use('li-ji','4','wet')
sequence('li-ji',5,('abrasion',None),('wrapped',[26])); sequence('li-ji',6,('wrapped',None),('splash',[31]))
use('li-ji','7-8','wrapped'); sequence('li-ji',9,('wrapped',None),('fresh',[6]),('compress',[26]))
use('li-ji','10-22','compress'); use('li-ji','23-30','healing')
sequence('li-ji',31,('healing',None),('blood',[20])); sequence('li-ji',32,('blood',None),('spent',[17,21]))
use('li-ji','33','spent'); use('li-ji','34,36','rewrapped'); use('li-ji','37-42','scar')
use('a-heng','1-3,5-6','blue'); sequence('a-heng',3,('blue',None),('wet',[20])); use('a-heng','4','wet')
sequence('a-heng',7,('blue',None),('hoarse',[4])); sequence('a-heng',8,('hoarse',None),('wet-shoes',[35]))
use('a-heng','9-10','wet-shoes'); use('a-heng','15-42','later'); sequence('a-heng',33,('later',None),('tears',[24]))
sequence('li-dan',14,('work',None),('memory',[15]),('work',[16]),('coat',[21,35]))
use('li-dan','15-29','coat'); sequence('li-dan',30,('coat',None),('loaded',[9,10,11])); use('li-dan','31','loaded')
sequence('li-dan',32,('loaded',None),('pad-fallen',[6])); sequence('li-dan',33,('pad-fallen',None),('sore',[28,29]))
use('li-dan','34','sore'); use('li-dan','36-37','after'); use('li-dan','41','recovered')
for entity in ('li-xiao','sun-liu','helpers-four','officer-cheng'):
    sequence(entity,29,('base',None),('loaded',[14,17])); use(entity,'30-32','loaded')
    sequence(entity,33,('loaded',None),('spent',[11,12,15,18])); use(entity,'34','spent')
use('heng-mother','38-42','recovering'); use('zhou','20,28,36','plain')
sequence('zhao',19,('base',None),('no-keys',[17,19])); use('zhao','21-36','no-keys'); use('zhao','37','custody'); use('priest','37','custody')
sequence('ticket-child',8,('base',None),('one-shoe',[19]),('base',[19]))
sequence('songbook',2,('base',None),('papers-on-top',[20]),('inserted',[22])); sequence('songbook',3,('inserted',None),('wet',[20,29]))
use('songbook','4','wet'); use('songbook','5','dry'); sequence('songbook',6,('dry',None),('account',[28]))
use('songbook','7-36','account'); sequence('songbook',37,('account',None),('receipt',[18])); use('songbook','38','receipt')
sequence('songbook',40,('receipt',None),('repaired',[14,15])); use('songbook','41-42','repaired')
sequence('rice-bag',1,('base',None),('wages',[17]),('advance',[23])); use('rice-bag','2-3','advance')
sequence('rice-bag',4,('advance',None),('returned',[13,16])); sequence('rice-bag',37,('base',None),('refund',[21,22]))
sequence('cloth',2,('base',None),('damp',[2])); sequence('cake',2,('base',None),('corner',[8]))
sequence('paste-wool',2,('base',None),('removed',[5,6])); use('paste-wool','3','paste')
sequence('keys',19,('base',None),('cheng',[17])); use('keys','29','cheng')
use('curtain','3,5-6','wet'); use('curtain','8','stage'); sequence('curtain',41,('stage',None),('packed',[18])); use('curtain','42','packed')
sequence('paper-snake',3,('base',None),('assembled',[6])); sequence('paper-snake',8,('assembled',None),('moon',[12])); use('paper-snake','9','moon'); use('paper-snake','18','boxed')
sequence('paper-moon',8,('base',None),('held',[12])); use('paper-moon','9','held')
sequence('name-plaque',8,('base',None),('bound',[31,32])); use('name-plaque','9','bound')
sequence('red-rope',8,('base',None),('cut',[23,31])); use('red-rope','9','cut')
sequence('debt-note',22,('base',None),('uncovered',[10,12])); use('debt-note','26,36','uncovered')
sequence('debt-overlay',22,('base',None),('removed',[12,13,23])); use('debt-overlay','26,36','removed')
sequence('work-ledger',7,('base',None),('one',[3]),('two',[5])); use('work-ledger','16-37','two')
use('stop-order','21-28','all'); use('old-lantern','16,42','lit'); sequence('old-lantern',41,('base',None),('lit',[19]))
sequence('bandage',9,('base',None),('head',[26])); use('bandage','13-14','head'); sequence('bandage',31,('base',None),('blood',[20])); use('bandage','32-33','blood'); use('bandage','34','new')
sequence('heavy-blade',23,('base',None),('sheathed',[35])); use('heavy-blade','24,26-27','sheathed')
sequence('heavy-blade',29,('sheathed',None),('base',[10])); sequence('heavy-blade',31,('base',None),('bloody',[16,19])); use('heavy-blade','32-33','bloody')
sequence('feeding-channel',23,('base',None),('cut',[12,14,16])); sequence('feeding-channel',24,('cut',None),('covered',[5]))
sequence('feeding-channel',29,('covered',None),('cut',[18])); use('feeding-channel','30-33','cut')
sequence('feeding-door',18,('base',None),('open',[20]),('base',[21]))
sequence('feeding-door',23,('base',None),('open',[11]),('base',[17]),('open',[19]),('base',[25]),('open',[29]))
sequence('feeding-door',24,('open',None),('base',[5])); sequence('feeding-door',29,('base',None),('open',[6]),('base',[9]))
sequence('cave-gate',18,('base',None),('up',[24]),('base',[34])); sequence('cave-gate',29,('base',None),('up',[17]))
sequence('cave-gate',30,('up',None),('loaded',[3])); use('cave-gate','31-32','loaded'); sequence('cave-gate',33,('loaded',None),('released',[11,12,14]))
sequence('gate-pin',18,('base',None),('out',[24]),('base',[34])); sequence('gate-pin',29,('base',None),('out',[17]))
use('gate-pin','30-33','out')
sequence('crossbeam',24,('base',None),('installed',[3,4])); sequence('crossbeam',29,('installed',None),('seven',[14,17]))
sequence('crossbeam',30,('seven',None),('eight',[9,10])); use('crossbeam','31-32','eight'); sequence('crossbeam',33,('eight',None),('installed',[11,12]))
sequence('hemp-rope',29,('base',None),('padded',[2])); use('hemp-rope','30-33','padded')
use('bait-basin','23','empty'); use('bait-basin','29','south')
sequence('channel-plan',26,('base',None),('slot',[11])); sequence('evidence-chest',22,('base',None),('open',[7]),('base',[27])); use('evidence-chest','28','registers')
use('sacrificial-registers','17','copies'); use('approval-orders','37','copies')
sequence('copied-pages',39,('base',None),('confirmed',[7,12])); sequence('copied-pages',40,('confirmed',None),('bound',[14,15]))
use('family-meal','27','prepared'); use('family-meal','42','warm')
sequence('snake',30,('base',None),('held',[3])); sequence('snake',31,('held',None),('shallow',[19]))
sequence('snake',32,('shallow',None),('deep',[4]),('severed',[18,20])); sequence('snake',33,('severed',None),('still',[6,9,10]))
use('rice-shop','1-2','day'); use('rice-shop','4','closing')
use('river-street','1-2','day'); use('river-street','15,19,42','night'); use('river-street','27','dawn')
use('bamboo-stall','2','day'); use('prop-house','2-5','work'); use('prop-house','42','night')
sequence('shallows',3,('day',None),('dusk',[29])); use('shallows','6','day'); use('drying-area','3,5-6','wet')
use('heng-home','7','sick'); sequence('heng-home',10,('sick',None),('guarded',[16,17])); use('heng-home','15','guarded'); use('heng-home','38-39','return'); use('heng-home','40,42','lamplit')
sequence('li-home',14,('dinner',None),('guest',[38,44])); use('li-home','15-16,26-27','guest'); use('li-home','20','day'); use('li-home','34','meal'); use('li-home','42','open')
use('temple-front','7','chorus'); use('temple-front','8-9','festival'); use('temple-front','24','sealed'); use('temple-front','28,30','grain'); use('temple-front','37','verdict')
use('temple-grain','12','stock'); use('temple-grain','19,22,28','sealed'); use('temple-grain','37','refund')
use('temple-back','18-19','original'); sequence('temple-back',23,('original',None),('cut',[16])); sequence('temple-back',24,('cut',None),('bound',[3,4]),('modified',[5])); use('temple-back','25','modified'); use('temple-back','29-33','battle')
use('hill-steps','19,25','dusk'); use('hill-steps','37','day')
use('county-office','13','notice'); use('county-office','17,21','register'); use('county-office','35','relic'); use('county-office','36','hearing')
sequence('ferry',11,('loaded',None),('withdrawn',[7,9])); use('singer-yard','39','day'); sequence('village-yard',41,('setup',None),('song',[7]))
use('boat-song','1','short'); use('blue-awning-song','3','practice'); use('blue-awning-song','4-5,38','missing'); use('blue-awning-song','39','teaching'); use('blue-awning-song','40','soft'); use('blue-awning-song','41','complete')
use('snake-welcome-song','7','chorus'); use('blessing-stage-song','10','distant')
use('stage-drum','2,7','audible')


def compile_forms(records, appearances, entries, source, ref, record, scene_map):
    if set(BASE) != set(entries):
        raise ValueError('full-form baseline catalogue differs: ' + str(set(BASE) ^ set(entries)))
    used, places = {}, {}
    actual_scenes = {}
    for sn, occurrences in appearances.items():
        for occurrence in occurrences:
            if occurrence['mode'] != 'mention':
                key = occurrence['entity']['object_id'].removeprefix('entity-')
                actual_scenes.setdefault(key, []).append(sn)
    for sn, occurrences in appearances.items():
        for occurrence in occurrences:
            key = occurrence['entity']['object_id'].removeprefix('entity-')
            steps = SCHEDULE.get((key, sn), [('base', None)])
            if occurrence['mode'] == 'mention':
                # Mentioning a person does not replay their whole physical change.
                available = actual_scenes.get(key, [])
                closest = max((s for s in available if s <= sn), default=min(available, default=sn))
                steps = [SCHEDULE.get((key, closest), [('base', None)])[-1]]
            occurrence['states'] = []
            occurrence['transitions'] = []
            for index, (form_key, blocks) in enumerate(steps):
                form_id = f'form-{key}-{form_key}'
                used[key, form_key] = form_id
                places.setdefault((key, form_key), []).append((sn, occurrence))
                occurrence['states'].append(ref(form_id))
                if index:
                    selected = [b for b in scene_map[sn][3] if int(b['id'].rsplit('b', 1)[1]) in blocks]
                    if len(selected) != len(blocks):
                        raise ValueError(f'transition evidence absent: {key}/{sn}/{blocks}')
                    before = steps[index - 1][0]
                    occurrence['transitions'].append({'from': ref(f'form-{key}-{before}'), 'to': ref(form_id),
                        'action': '；'.join(b['text'] for b in selected), 'source': source(sn, selected)})
    for (key, form_key), oid in sorted(used.items()):
        entry = entries[key]
        dimensions = default_dimensions(entry['kind'], BASE[key])
        if form_key == 'base':
            label, overrides, evidence = ('已知事实（仅提及）' if key in ('xiao-man','xu-bride') else '基准完整形态'), {}, None
        else:
            label, overrides, evidence = FORMS[key][form_key]
        dimensions.update(overrides)
        sources = []
        if evidence:
            sn, ids = evidence
            blocks = [b for b in scene_map[sn][3] if int(b['id'].rsplit('b',1)[1]) in ids]
            if len(blocks) != len(ids):
                raise ValueError('full state evidence absent: ' + oid)
            sources.append(source(sn, blocks))
        actual = [(sn,o) for sn,o in places[key,form_key] if o['mode'] != 'mention']
        for sn, occurrence in actual or places[key,form_key][:1]:
            for s in occurrence['evidence']:
                if s not in sources:
                    sources.append(s)
        if not sources:
            raise ValueError('no source: '+oid)
        medium = 'none' if key in ('xiao-man','xu-bride') else 'audio' if entry['kind'] == 'song' or key == 'offscreen-caller' else 'image'
        # The offscreen drum's audible full form needs sound, not an unseen prop image.
        if key == 'stage-drum' and form_key == 'audible':
            medium = 'audio'
        text = '\n'.join(f'{DIMENSION_LABELS[name]}：{value}' for name,value in dimensions.items())
        primary = sources[0]
        facts = [b['text'] for b in scene_map[int(primary['scene_id'][1:])][3] if b['id'] in primary['block_ids']]
        unknowns = [v for v in dimensions.values() if any(w in v for w in ('待审','未明'))]
        description_only=oid in {'form-stage-drum-audible','form-blue-awning-song-missing','form-blue-awning-song-practice','form-blue-awning-song-soft','form-blue-awning-song-teaching'}
        records.append(record(oid,'STATE',entry['name']+'·'+label,text, state_model=MODEL,
            entity=ref(entry['id']), dimensions=dimensions, reference_media=medium,
            **({'reference_mode':'description','production_description':text} if description_only else {}),
            facts=facts, choices=['同一完整形态跨场复用；未写换装、湿痕消退、伤愈程度的衔接属于待审连续性安排，不冒充新增剧本事实。'],
            unknowns=unknowns, sources=sources))
    # References need every form to exist before occurrences and requirements.
    for (key, form_key), oid in sorted(used.items()):
        row = next(r for r in records if r['object_id'] == oid)
        p = row['payload']
        if p['reference_media'] == 'none' or p.get('reference_mode')=='description':
            continue
        records.append(record('need-'+oid+'-overall','REQUIREMENT',p['title']+'·整体参考',
            '说明该实体此时的完整形态；细节、角度和声音补充不能代替整体参考。候选须明确审阅并显式采用。',
            scope=ref(oid),slot='overall',required=True,purpose='完整状态整体参考',media_type=p['reference_media'],
            usage='generation_input',
            entities=[ref(entries[key]['id'])],states=[ref(oid)],
            specification={'reference_role':'overall', **({'minimum_long_edge':3840,'native_4k':True} if p['reference_media']=='image' else {'minimum_sample_rate':48000})}))
