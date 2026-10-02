#!/usr/bin/env python3
"""Author the complete approved V4 episode-one shot/need package.

This is a production design, not generated footage. Timing is provisional until
the accepted voices and complete animatic are actually watched and heard.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
from production_data import refresh_drafts

ROOT=Path(__file__).resolve().parents[1]

# scene, source blocks, planned seconds, title, purpose, framing, spatial,
# start, end, continuity, visible entities, states, key props, motion, sounds.
SHOTS=[
 (1,'1-2',9,'河街唱曲开场','建立唱曲换米的生活场面与阿蘅的稳当',
  '16:9 中全景，阿蘅偏右，米铺门与量米柜在后，听客从左侧入画；歌本与倒扣竹篮在腰下前景',
  '机位在街道河侧朝铺面；行进到道具屋的方向统一为画面右侧。阿蘅朝街，听客在她左前',
  '歌本已摊开压河石；阿蘅吸气，脚尖准备拍子','第一句唱完，脚下拍子稳定，听客注意着她',
  '首镜不先给山庙或危险符号。门内量米与门外唱曲同属一条街',
  'a-heng,woodcutter,rice-listeners,rice-shop,river-street','heng-blue,book-intact,river-day,rice-shop-day','songbook,book-basket,river-stone,grain,carrying-pole','局部动作：口型、脚拍、风掀衣角；背景人物缓慢办事','近处歌声；轻河风、远水与米铺轻动静，音乐不盖清唱'),
 (1,'3',3,'老汉跟拍与翻页','让观众先察觉阿蘅跳段，保留轻松的趣味',
  '中近景，老汉与竖在腿边的扁担占左半，右前景能见阿蘅翻页的手',
  '沿用河侧机位，老汉望画面右上方阿蘅，书篮位置不挪',
  '老汉正随前一句点头，手扶扁担','阿蘅翻过两页，老汉的点头迟疑一下',
  '上一镜歌曲句尾留完后翻页；翻页前后河石位置一致，不压住正在翻的页',
  'a-heng,woodcutter,rice-shop','heng-blue,book-intact','songbook,book-basket,river-stone,carrying-pole','完整关键动作：抬河石、连续翻两页、落手压稳；老汉局部反应','纸页声和呼吸，上一句尾音自然落下'),
 (1,'4,6',10,'直接唱归家','把归家歌词唱清，并表现阿蘅忍笑',
  '阿蘅胸上近景，视线略偏左对着老汉，画面下缘留歌本边',
  '机位仍在同一侧；老汉在画外左，阿蘅脚拍虽不见仍连续',
  '翻页后重新接上调子','归家句尾腔收住，嘴角要笑又忍住',
  '镜头 4 老汉的“二道——哎，到了？”可在此镜末尾接入，归家歌词保持完整，不互相盖字',
  'a-heng,rice-shop','heng-blue,book-intact','songbook','局部动作：自然换气、忍笑与尾腔，机位固定','完整第二句清唱；老汉插话的入点在后续声音排练中细调'),
 (1,'5-7',7,'老汉发现省了两段','明确这次省唱是人物间熟悉的玩笑',
  '老汉腰上中景，扬下巴看阿蘅，身后两位听客听着',
  '老汉看右，阿蘅在画外右；扁担始终竖腿旁，不在切镜后换手换边',
  '老汉顺嘴数到第二道滩','打趣完扬下巴，等阿蘅回答',
  '不重唱镜头 3 的歌词。上一镜尾腔可少量跨切；两句老汉台词顺序不变',
  'woodcutter,rice-listeners,rice-shop','','carrying-pole','局部动作：下巴和眉眼；静止保持等回答','老汉对白，听客轻笑尚未齐起'),
 (1,'8',8,'让船早些到家','建立阿蘅机灵又体贴的说话方式',
  '回阿蘅中近景，书篮下沿可见，正对老汉说话',
  '保留画面左的老汉肩缘，阿蘅仍望左，不跨越两人轴线',
  '尾腔刚收住，阿蘅带笑吸气','话说完欠一点身，等听客的反应',
  '对白语气由唱腔回到自然口语，同一人声线协调，不做播音式旁白',
  'a-heng,woodcutter,rice-shop','heng-blue','songbook,book-basket','局部表演，固定镜头','阿蘅对白完整；环境比歌段稍回升'),
 (1,'9',4,'听客散开办事','表现唱曲融在真实生计里，并给李寄留出入场通道',
  '恢复中全景，听客笑着提袋，另两人从后方进店',
  '门在阿蘅后侧，听客只沿门前空地进出；李寄稍后从左侧挤进',
  '听客围在篮前','前方出现空隙，阿蘅欠身回应',
  '袋、扁担与人的路径互不穿透；群众“下回补上”只一人说，其余笑声轻',
  'a-heng,woodcutter,rice-listeners,rice-shop,river-street','heng-blue','songbook,book-basket,carrying-pole,grain','完整小群体动作：提袋、侧身入铺；阿蘅局部欠身','听客一句“下回补上”、轻笑、米袋摩擦与脚步'),
 (1,'10-11',5,'浆糊手按住书页','以动作引入李寄的急性子和手部状态',
  '歌本与手的近景起，轻抬至李寄半身；肩领边能读出红印',
  '李寄从画面左入，站阿蘅左侧并肩向书篮，阿蘅在右',
  '河风掀页，李寄手刚伸入画','手压页边，她尚未站稳已找到跳过的页',
  '干浆糊少量可见；不能画成白手套、血或伤口。书始终在阿蘅一侧掌握',
  'li-ji,a-heng,rice-shop','liji-paste,liji-water-mark,heng-blue,book-intact','songbook,book-basket,river-stone,paste-wool','完整关键动作：入画按页；小幅抬镜跟脸','纸页拍动、轻脚步；不加夸张出场音效'),
 (1,'12-16',12,'两个人的打趣','建立亲密关系与李寄不装客气的口吻',
  '固定双人腰上中景，李寄左、阿蘅右；歌本位于两人之间',
  '两人距离一臂以内，李寄看书再看阿蘅；阿蘅用手边书角轻碰她',
  '李寄指向被省的页','阿蘅说少一句不许跑，李寄接住玩笑',
  '书角轻碰手臂的触点明确；此处还没正式交书，阿蘅仍控制本子',
  'li-ji,a-heng,rice-shop','liji-paste,liji-water-mark,heng-blue,book-intact','songbook','局部对白表演＋书角轻碰的明确接触动作','两人四句对白，背景河街保持低电平'),
 (1,'17-19',7,'当天的工米','让观众看清第一份米是当天所得',
  '三人中景转手部近景，木斗、袋口和倒米动作完整入框',
  '周掌柜由店门向前，阿蘅右侧撑袋，李寄靠左看书；木斗从上方对袋口',
  '掌柜出门把木斗的米刮平，阿蘅袋口尚未撑开','木斗倒尽，阿蘅将要系袋，掌柜出声留住',
  '先等袋撑稳再倒；米流结束后木斗退出，不与下一把预付米剪成同一次倒米',
  'zhou,a-heng,li-ji,rice-shop','zhou-apron,heng-blue,liji-paste,bag-wages','rice-measure,rice-bag,grain,songbook','完整关键动作：刮平、撑袋、倒尽、收斗','“这是今天的。”米粒落袋、木斗刮平、布口摩擦'),
 (1,'20',14,'明天许家的唱活','说明阿蘅下一份收入与需要练好的曲子',
  '周掌柜中近景，阿蘅半侧背在前景；镜头稳定留完整口语节奏',
  '掌柜在门口面朝街，两女孩面朝店；李寄仍在阿蘅左边翻歌本',
  '掌柜叫住正系袋的阿蘅','把明天唱活和傍晚先唱一遍交代完',
  '《送青篷》此处只被提及，不能在镜头里插播尚未学会的完整歌段或许家婚礼',
  'zhou,a-heng,li-ji,rice-shop','zhou-apron,heng-blue,liji-paste','songbook,rice-bag,rice-measure','局部表演：自然停顿、手势；固定镜头','周掌柜整段对白，明确“明天”和“傍晚”'),
 (1,'21-22',4,'生字圈与承诺','留下阿蘅其实仍需看词的可见依据',
  '手与末页特写，几处生字圈清楚；上缘见阿蘅收住笑的下半脸',
  '李寄手从左翻页，阿蘅手从右压住，纸角不跳位置',
  '末页被翻开，圈字露出来','阿蘅压页并向掌柜保证这回不省',
  '整页歌词不擅写未公布内容；实际可读字只取定稿已给的《送青篷》原文',
  'a-heng,li-ji,rice-shop','heng-blue,liji-paste,book-intact','songbook','局部动作：翻页、压页与眼神；特写固定','阿蘅保证的对白，纸页轻响'),
 (1,'23-25',10,'另外预付的一小把','区分第二份米的用途，为退米一场建立依据',
  '稍宽三人景，保留掌柜回柜再过来的完整方向；添米时近景不跳过撑袋',
  '柜在掌柜后侧，阿蘅原地重新开袋，李寄让出倒米位置',
  '第一份已入袋，掌柜转回柜边','额外一把米添完，阿蘅道谢，掌柜手离开袋口',
  '第二份必须是一小把手抓，不能又倒一整斗；两次支付声音和动作分段可辨',
  'zhou,a-heng,li-ji,rice-shop','zhou-apron,heng-blue,liji-paste,bag-advance','rice-bag,grain,songbook','完整关键动作：回柜抓米、返回示意、重新撑袋、添米','掌柜预付说明与阿蘅道谢；少量米落布袋'),
 (1,'26-29',7,'相约晚些一起练','从掌柜的生计安排回到女孩间的小约定',
  '檐外双人中景，米袋结在画面下部，李寄凑近书页',
  '两人侧移半步让出店门，阿蘅右手侧留袋，李寄仍在左',
  '阿蘅扎袋，两人让到檐外','李寄答应晚些陪练，视线从书页抬回阿蘅',
  '这一承诺仍是日常小事，不提前表现第二集扔书后的歉疚',
  'li-ji,a-heng,rice-shop','liji-paste,liji-water-mark,heng-blue,bag-advance,book-intact','songbook,rice-bag','局部对白与半步移位','三句对白、布袋打结'),
 (1,'30-32',9,'不让红肩再提米','由阿蘅的体贴转入擦手的自然理由',
  '双人半身景保留手、肩领和米袋；末尾落在李寄摊手笑',
  '李寄伸向下方米袋，阿蘅把袋留在自己一侧，另一手递书到两人之间',
  '李寄想提米袋','阿蘅看红印留袋，递书发现浆糊收回；李寄双手摊开',
  '书没有交成，袋也没换主人；下一场由此开始擦手，不应凭切镜完成交换',
  'li-ji,a-heng,rice-shop','liji-paste,liji-water-mark,heng-blue,bag-advance,book-intact','songbook,rice-bag,paste-wool','完整关键动作：伸手、留袋、递书又收、摊手','“你先把手给我看看。”衣布轻响，保留微笑呼吸'),
 (2,'1',4,'河街的前方','建立道具屋与对街竹器摊的位置，给后面的反应镜头落地',
  '沿街中远景，米铺留左后，道具屋幕布在右前，河面仅作侧后景',
  '女孩由米铺向画面右侧走出少许，在街角停；陶伯摊位在她们对街，不能隔一条河',
  '从檐外向道具屋方向接镜','女孩在街角停住，阿蘅准备取水壶',
  '相邻两场仍是同一日连续时刻；衣色、发髻、袋结、书的主人延续镜头 14',
  'li-ji,a-heng,river-street,rice-shop,prop-house,bamboo-stall','river-day,heng-blue,liji-paste','songbook,rice-bag,street-laundry,curtain','简单横向移动跟随半步，再固定','河水、轻风、衣裳布响与远处民居动静'),
 (2,'2-4',10,'先把手擦干净','通过珍惜歌本的话建立物件价值',
  '双人腰上中景，水壶口、布巾和李寄双手在同一画面',
  '阿蘅右、李寄左；米袋先搁两人脚旁可見，歌本夹在阿蘅前臂与身侧',
  '阿蘅倒少量水蘸巾','李寄接巾，一边辩称早干一边摊手给看',
  '手忙时书和米袋有可见落点。将米袋短暂放脚边属于制作走位选择，不改对白',
  'li-ji,a-heng,river-street','liji-paste,liji-water-mark,heng-blue,cloth-damp','water-flask,cloth,songbook,rice-bag','完整关键动作：倒水、蘸巾、递接；对白自然','两人对白，少量倒水与湿布声'),
 (2,'5-6',5,'羊毛掉出来才交书','做清洁动作的结果，让歌本第一次真正转手',
  '手部近景，羊毛掉落可见，略拉宽保留交书与接书',
  '李寄手在左前，阿蘅右侧翻巾后再把歌本递到李寄两掌上',
  '李寄搓手落下一撮羊毛','布巾翻面后擦净，李寄双手接稳歌本',
  '本镜由脏手转换为净手；后续近景不得继续出现同一团白浆糊',
  'li-ji,a-heng,river-street','liji-paste,liji-clean,heng-blue,cloth-damp,book-intact','paste-wool,cloth,songbook','完整关键动作：搓落羊毛、翻巾、擦净、交书','轻搓、巾布、纸本接手，无新增对白'),
 (2,'6-7',5,'招呼墨耳','以固定耳尖特征建立狗的身份',
  '低机位中景，街角卧狗在右前，李寄在左蹲下招手',
  '墨耳距女孩两三步，朝李寄抬头；缺口在狗的左耳，反打也不镜像换边',
  '墨耳卧着，李寄抱书蹲下','听见呼唤后墨耳起身欲跑来',
  '歌本由李寄一臂抱稳；蹲下不把书放到脏地上。猫狗声不擅加大声吠叫',
  'li-ji,a-heng,mo-er,river-street','liji-clean,dog-rest','songbook,rice-bag','完整关键动作：蹲、招手、狗抬头起身','“墨耳，过来。”轻爪步、呼吸，环境不变'),
 (2,'8-10',8,'留给狗的饼','恢复两人的轻松与阿蘅对李寄的小了解',
  '低些的双人中景，狗与递饼的手都入框',
  '李寄左、阿蘅右，墨耳在两人前方偏右；视线先落在狗再相互看',
  '墨耳摇尾跑到脚边','李寄半句话没说完，注意忽然移到米铺方向',
  '半块饼先交阿蘅，再掰小角喂；未喂完部分留在阿蘅手里／收好，不能凭空整块吃掉',
  'li-ji,a-heng,mo-er,river-street','liji-clean,heng-blue,dog-approach,cake-corner','cake,songbook,rice-bag','完整关键动作：跑近、交饼、掰角、低手喂；狗不扑脸','女孩两句对白、轻爪步和咀嚼声'),
 (2,'11-12',6,'钥匙串旁的目光','先让观众通过李寄注意到赵执事的存在',
  '由李寄收笑切到中景赵执事，褐衣、钥匙在腰侧，路人从前景经过',
  '赵执事站米铺檐下，在女孩左后方；他望画面右向阿蘅',
  '李寄停下话，赵执事一直看阿蘅','路人招呼，他略点头后离檐',
  '不加恶人俯拍、阴影变脸或威胁配乐；危险感来自注视与女孩停顿',
  'li-ji,zhao,street-passers,rice-shop,river-street','liji-clean,zhao-keys','keys','局部目光和点头；末尾一步离檐','路人“赵执事”，细小钥匙碰声，街声短暂留空'),
 (2,'13-15',6,'从母亲身体问起','显示邀约从阿蘅的现实难处切入',
  '三人中景，赵执事左、阿蘅右、李寄中后半步',
  '沿街的原轴线不反转；赵向右走来停在一臂半之外，不围住女孩',
  '赵执事走近压低声音','阿蘅回答还得养，李寄盯着他',
  '李寄仍拿歌本；阿蘅空手回答，米袋留脚旁以便之后提起',
  'zhao,a-heng,li-ji,river-street','zhao-keys,heng-blue,liji-clean','songbook,rice-bag,keys','简单移步到停，继而局部对话','赵执事与阿蘅两句对白，声音不高但字清楚'),
 (2,'16-17',5,'李寄抢答不会','把保护欲和越俎代庖落在一句打断上',
  '三人较紧中景，赵执事问阿蘅，李寄从中间抢一句',
  '李寄未跨到赵执事身前，视线从他转向阿蘅，轴线维持',
  '赵执事还在等阿蘅的回答','李寄抢答，阿蘅转眼看她',
  '台词“不会”清楚而短，不演成歇斯底里吵架，便于下一镜阿蘅自己回答',
  'zhao,a-heng,li-ji,river-street','zhao-keys,heng-blue,liji-clean','songbook,keys','局部抢答与眼神反应','赵执事提迎蛇调、李寄“不会”，不重叠盖住问句'),
 (2,'18-19',6,'阿蘅把歌本接回来','让阿蘅自己决定问清工作条件',
  '阿蘅半身近景，画面左下看见歌本从李寄手中交来',
  '阿蘅先看左侧李寄，再向更左前方赵执事抬眼，两个视线落点有区别',
  '李寄手里抱书，阿蘅伸手','歌本回阿蘅手里，她问会前两段、唱几天',
  '李寄自然松手，不争抢；书封朝向延续镜头 17 的接书结果',
  'a-heng,li-ji,zhao,river-street','heng-blue,liji-clean,book-intact','songbook','完整关键动作：看一眼、伸接、李寄松手；随后对白','阿蘅问句、纸本摩擦，留短停顿'),
 (2,'20-21',6,'旧领唱词放在歌本上','把可追溯的工作邀约物件交到阿蘅手里',
  '赵执事袖与阿蘅托书的手部中近景，上半脸可见',
  '旧纸从画面左袖内抽出，平放到右侧歌本上；两人不同时握住同一纸角',
  '赵执事从袖内取出几张旧纸','纸已放稳，他交代学会来找便收手',
  '纸张是旧领唱词，正式可读歌词以 s003 已给原文为限；第一集无需硬推文字特写',
  'zhao,a-heng,li-ji,river-street','zhao-keys,heng-blue,book-intact','lead-lyrics,songbook,keys','完整关键动作：抽纸、落纸、收手','赵执事“领唱的词在这儿。学会了来找我。”与纸声'),
 (2,'22',5,'背影与合上的本子','让阿蘅保留这份邀约，李寄欲取纸未果',
  '三人中远景，赵执事沿街转向上山岔口，女孩留前景',
  '上山方向是已标出的远侧岔口，不穿过陶伯的摊位或河面；两人视线追他的背影',
  '旧纸摊在歌本上，赵转身','李寄伸手前阿蘅合上歌本，纸收在内',
  '纸不留在赵袖里，也不掉地；阿蘅合书不是新撕书动作',
  'zhao,a-heng,li-ji,river-street','zhao-keys,heng-blue,liji-clean,book-intact','lead-lyrics,songbook','完整关键动作：离开、想拿纸、合书；固定镜头','脚步和钥匙远去、合书声；给下一句留安静'),
 (2,'23',6,'阿禾也是去唱歌','第一次把这份唱工同失踪女孩连起来',
  '李寄中近景，身后能辨对街摊位的方向；阿蘅肩缘在右前',
  '李寄看阿蘅后短暂望向对街，视线给镜头 27 的陶伯反应导向',
  '李寄伸出的手停在书前','说出阿禾名字，目光扫向摊位',
  '不插阿禾牺牲回忆，第一集只是名字与陶伯的现实反应',
  'li-ji,a-heng,river-street','liji-clean,heng-blue','songbook','局部表演，固定镜头','李寄完整问句，削竹声先在背景细细存在'),
 (2,'24',4,'空凳边的刀停了','用手的停顿和空位呈现损失',
  '陶伯与身旁空小凳的中景，削篮口的手在下部清楚，脸不抬',
  '反打到对街靠河一边；女孩在画外对面，陶伯听得见普通说话，河不是两边之间的障碍',
  '陶伯正削篮口','听见名字刀停住，空凳无人，头仍低着',
  '反打前有镜头 26 的视线；不放大到只见刀而看不到空凳',
  'tao,bamboo-stall,river-street','','bamboo-basket,shaving-knife,empty-stool','完整关键动作：削到停；停住后静止保持','刮竹声由有到无，街声仍在但轻；无新增悲情音乐'),
 (2,'25',4,'翻花绳的记忆','让阿禾有过具体的生活关系',
  '保持陶伯与空凳少许，再回阿蘅看向对街的近景',
  '阿蘅视线向对街陶伯，低声说，不把人叫过来',
  '对街削竹声停着','阿蘅说完，嘴唇合住，目光仍留在对街',
  '只用画外／切回对白，不新增阿禾活人、花绳或追忆画面',
  'a-heng,tao,bamboo-stall,river-street','heng-blue','empty-stool,songbook','静止保持与简单切回','阿蘅“她还教过我翻花绳。”'),
 (2,'26',8,'两个没有回来的名字','交代祭蛇的重复与今年迫近的危险',
  '两女孩胸上双人景，李寄左、阿蘅右，远处摊位边缘作空间线索',
  '李寄转回阿蘅，阿蘅仍望对街后慢慢收目光',
  '阿蘅刚说完旧事','李寄说今年又要点名字，等她回答',
  '年份、阿禾和小满名字一字不改；不展示剧本没有安排的尸体或蛇袭画面',
  'li-ji,a-heng,river-street','liji-clean,heng-blue','songbook','局部对白表演，固定镜头','李寄完整台词，减少杂声但保留河街空间'),
 (2,'27-28',11,'先提起眼下的米袋','阿蘅同时承认害怕和生计需要',
  '双人中景，阿蘅从对街收回目光，俯身提起脚旁米袋再说话',
  '米袋落点沿用镜头 16／21，书夹左臂、空右手提袋；李寄让半步',
  '两人沉默，阿蘅看竹器摊','米袋已提稳，她说要问清楚再唱与以后怎么办',
  '提米动作先于生计问句，不能用旁白说明贫困；袋中仍有当天工米和预付',
  'a-heng,li-ji,river-street','heng-blue,liji-clean,bag-advance','rice-bag,songbook','完整关键动作：低头、提袋、站稳，继而对白','布袋提起和阿蘅完整台词，留一口思索的气'),
 (2,'29-30',8,'你家也不宽裕','让帮助与现实限制都被听见',
  '近些的双人侧面中景，李寄向阿蘅靠一点，阿蘅轻声回应',
  '两人仍处同一侧轴线；目光回到对方，手中的袋和书不交换',
  '李寄急着提供自家粮','阿蘅说已受过照顾，两人短暂停着',
  '语气不责备李寄母亲，不追加家人贫困闪回；“婶婶”在本场指李寄母亲',
  'li-ji,a-heng,river-street','liji-clean,heng-blue,bag-advance','rice-bag,songbook','局部对白与眼神','两人两句对白，鼓声在结束后才进入'),
 (2,'31',8,'循着试鼓声往前走','以行动结束讨论，关系仍同行',
  '沿街中远景，阿蘅先朝右前道具屋走，李寄看一眼米袋再带墨耳跟上',
  '沿用镜头 15 的街轴；墨耳在李寄脚边，不穿过阿蘅或米袋',
  '鼓声从右前道具屋传来，三者还在原处','女孩与狗沿右前方向离开画面，间距自然收拢',
  '“牵起墨耳”按轻招手并扶狗颈引走处理，为待审动作选择；本稿不凭空增加未写的牵绳',
  'a-heng,li-ji,mo-er,river-street,prop-house','heng-blue,liji-clean,dog-approach,bag-advance','rice-bag,songbook,curtain,street-laundry','完整关键动作：起步、看袋、招引狗、跟上；机位固定','道具屋方向试鼓两三下、步声、狗轻爪步，鼓手身份不作指定'),
 (2,'32',3,'竹刀重新刮过篮口','让日常继续，保留未解决的危险和失去',
  '回陶伯手与篮口中近景，空凳保留一角',
  '与镜头 27 同侧同机位略近，刀、篮口和空凳关系不变',
  '削竹刀仍停在原处','刀重新缓缓刮过篮口，画面结束',
  '不新增陶伯抬头长叹或哭；声桥可接下一集生活声，但本集成段收尾',
  'tao,bamboo-stall','','bamboo-basket,shaving-knife,empty-stool','一个完整刮削动作后保持','刮竹声重新响起，鼓声远去；不增加旁白'),
]


def numbers(value):
    result=[]
    for part in value.split(','):
        a,_,b=part.partition('-');result.extend(range(int(a),int(b or a)+1))
    return result


def complete_states_for_blocks(occurrence, block_ids):
    """Select the full initial form and only transitions actually shown here."""
    first = min(int(b.rsplit('b',1)[1]) for b in block_ids)
    last = max(int(b.rsplit('b',1)[1]) for b in block_ids)
    active = occurrence['states'][0]
    selected, transitions = [], []
    for transition in occurrence.get('transitions', []):
        change_at = min(int(b.rsplit('b',1)[1]) for b in transition['source']['block_ids'])
        if change_at < first:
            active = transition['to']
        elif change_at <= last:
            if not set(transition['source']['block_ids']) <= set(block_ids):
                raise ValueError('shot must cover its complete state transition evidence')
            if not selected:
                selected.append(active)
            selected.append(transition['to'])
            transitions.append(transition)
    return selected or [active], transitions


def compile_shots(store, production):
    lock=json.loads((ROOT/'production/source-lock.json').read_text())
    source_bytes=(ROOT/'imports/screenplay-04.json').read_bytes()
    if hashlib.sha256(source_bytes).hexdigest()!=lock['screenplay']['file_sha256']:
        raise ValueError('approved screenplay changed; review the input lock before recompiling')
    script=json.loads(source_bytes)['episodes'][0]
    episode_ref={k:lock['episodes'][0][k] for k in ('object_id','revision_id')}
    block_map={b['id']:b for b in script['blocks']}
    def ref(oid):
        value=production.record(store,oid)
        return {'object_id':oid,'revision_id':value['id']}
    def record(oid,kind,title,body,**values):
        return {'object_id':oid,'kind':kind,'expected_version':0,'payload':{
            'format':'production-'+production.KINDS[kind]+'-v1','title':title,
            'blocks':[{'id':'description','text':body}],**values}}
    def source(scene,ids):
        return {**episode_ref,'scene_id':f's{scene:03d}','block_ids':[f"screenplay-04-lantern-home-s{scene:03d}-b{b:03d}" for b in ids]}
    records=[]; covered=set(); all_cues=[]; total_frames=0
    occurrences = {sn: {o['entity']['object_id']: o for o in production.record(store, f'preparation-s{sn:03d}')['payload']['occurrences']}
                   for sn in (1,2)}
    voices={'李寄':'li-ji','阿蘅':'a-heng','周掌柜':'zhou','赵执事':'zhao','老汉':'woodcutter'}
    for index,item in enumerate(SHOTS,1):
        (scene,ids,seconds,title,purpose,framing,spatial,start,end,continuity,entities,states,props,motion,fx)=item
        oid=f'shot-e01-{index:03d}'; block_ids=source(scene,numbers(ids))['block_ids'];covered.update(block_ids)
        body_blocks=[block_map[bid] for bid in block_ids]
        dialogue=[]
        for block in body_blocks:
            match=re.match(r'^(李寄|阿蘅|周掌柜|赵执事|老汉)(（唱）)?：(.*)$',block['text'])
            if match and not (scene==1 and index==3 and block['id'].endswith('b006')):
                speaker,singing,text=match.groups()
                dialogue.append({'type':'singing' if singing else 'dialogue','speaker':speaker,'entity':ref('entity-'+voices[speaker]),
                                 'text':text,'source':{**source(scene,[]),'block_ids':[block['id']]}})
        if index==6:
            dialogue.append({'type':'dialogue','speaker':'一位听客','entity':ref('entity-rice-listeners'),'text':'下回补上',
                             'source':source(1,[9])})
        if index==20:
            dialogue.append({'type':'dialogue','speaker':'河街路人','entity':ref('entity-street-passers'),'text':'赵执事',
                             'source':source(2,[12])})
        # Dialogue appears exactly once even where a shot shares action blocks.
        cue_start=round(0.5*24)
        cue_weight=sum(len(re.sub(r'[^\u4e00-\u9fffA-Za-z0-9]','',c['text'])) for c in dialogue) or 1
        cue_frames=seconds*24-24
        for cue in dialogue:
            cue['id']=f'e01-line-{len(all_cues)+1:03d}'
            weight=len(re.sub(r'[^\u4e00-\u9fffA-Za-z0-9]','',cue['text']))
            duration=round(cue_frames*weight/cue_weight)
            cue.update(shot_id=oid,planned_start_frame=cue_start,planned_end_frame=cue_start+duration,fps=24)
            cue_start+=duration
            cue['timing_status']='镜内预计窗口，随画面生成后实际观看与听辨复核'
            cue['delivery']='native_audio'
            all_cues.append(cue)
        sound=dialogue+[{'type':'environment_and_action','description':fx,'timing_status':'镜内预计窗口，随画面生成后实际观看与听辨复核','delivery':'native_audio'}]
        actor_keys=[v for v in entities.split(',') if v]
        prop_keys=[v for v in props.split(',') if v]
        sound_entity_keys=['boat-song'] if index in (1,3) else ['stage-drum'] if index==32 else []
        state_refs, state_transitions, first_states, last_states = [], [], [], []
        for key in dict.fromkeys(actor_keys+prop_keys+sound_entity_keys):
            occurrence = occurrences[scene].get('entity-'+key)
            if not occurrence or occurrence['mode']=='mention':
                raise ValueError('shot entity has no actual scene occurrence: '+key)
            full, changes = complete_states_for_blocks(occurrence, block_ids)
            state_refs.extend(full); state_transitions.extend(changes)
            first_states.append(full[0]); last_states.append(full[-1])
        shot=record(oid,'SHOT_DESIGN',f'E01-{index:03d} {title}',purpose,
                    episode=episode_ref,scene_id=f's{scene:03d}',source=source(scene,numbers(ids)),number=index,
                    purpose=purpose,framing=framing,spatial=spatial,action_start=start,action_end=end,
                    continuity=continuity,duration_frames=seconds*24,fps=24,sound=sound,
                    entities=[ref('entity-'+v) for v in dict.fromkeys(actor_keys+prop_keys+sound_entity_keys)],states=state_refs,
                    state_model='complete-v1',state_transitions=state_transitions,
                    audio_delivery='seedance-native-audio-v1',animatic_method='Seedance 2.0 有声视听预演；不是正式镜头交付',
                    motion=motion,planned_start_frame=total_frames,visual_status='尚未生成分镜画面')
        records.append(shot);total_frames+=seconds*24
        scope={'object_id':oid,'revision_id':'@'+oid}
        def need(slot,title,purpose,media,usage,entity_keys=(),required=True,spec=None,forms=None):
            needed_entity_ids={'entity-'+key for key in entity_keys}
            relevant_states=[s for s in (forms if forms is not None else state_refs) if production.record(store,s['object_id'])['payload']['entity']['object_id'] in needed_entity_ids]
            records.append(record('need-'+oid+'-'+slot,'REQUIREMENT',f'E01-{index:03d} · {title}',purpose,
                scope=scope,slot=slot,purpose=purpose,media_type=media,usage=usage,required=required,
                entities=[ref('entity-'+key) for key in entity_keys],states=relevant_states,
                specification=spec or {}))
        image_spec={'minimum_long_edge':3840,'native_4k':True}
        need('composition','构图／关键画面','按本镜空间、景别和动作起点形成 16:9 构图图；关键手部接触不得被背景遮挡。','image','generation_input',actor_keys+prop_keys,
             spec={**image_spec,'minimum_width':3840,'minimum_height':2160},forms=first_states)
        for key in actor_keys:
            entity=production.record(store,'entity-'+key)['payload']
            if entity['entity_type']=='character':
                need('character-'+key,entity['title']+'身份与状态参考','用于同一人物跨镜与跨角度辨识，提供该镜所需身体、衣着和手部状态；可一材多用。','image','generation_input',[key],spec=image_spec)
            elif entity['entity_type']=='space':
                need('space-'+key,entity['title']+'空间机位参考','能对应本镜视线、门口、街轴与物件落点的实际背景或空间参考。','image','generation_input',[key],spec=image_spec)
        for key in prop_keys:
            entity=production.record(store,'entity-'+key)['payload']
            need('prop-'+key,entity['title']+'参考','可用独立原件或经审阅的组合图局部；采用须绑定具体文件与必要裁切。','image','generation_input',[key],spec=image_spec)
        if index in (2,7,9,12,14,16,17,18,19,23,24,25,30,32):
            need('end-keyframe','动作结束与下一镜承接图','同时标明交接后的手、书、袋、纸或人物位置，供关键动作生成和下一镜连续性参考。','image','generation_input',actor_keys+prop_keys,spec=image_spec,forms=last_states)
    expected={b['id'] for b in script['blocks']}
    if covered!=expected:raise ValueError('episode block coverage mismatch: '+str(expected-covered))
    dialogue_ids=[c['source']['block_ids'][0] for c in all_cues]
    if len(dialogue_ids)!=len(set(dialogue_ids)):raise ValueError('a dialogue block was repeated across shots')
    expected_dialogue={b['id'] for b in script['blocks'] if re.match(r'^[^：]{1,12}：',b['text'])}
    if not expected_dialogue<=set(dialogue_ids):raise ValueError('missing dialogue blocks')
    return {'format':'production-import-v1','records':records},all_cues,total_frames


def render(document,cues,frames,names):
    shots=[r['payload'] for r in document['records'] if r['kind']=='SHOT_DESIGN']
    lines=['# 第一集逐镜设计与素材需求','',
           f'正式依据为版本四第 1 集《两份米》，两场、64 个正文块。此设计分为 {len(shots)} 镜，预计 {frames/24:.0f} 秒；24 fps、16:9、1080p 动态分镜及 48 kHz 声音为首轮待审制作规格。时长来自本稿排练安排，尚未由完整实际声音和动态分镜回看验证。','',
           '本稿不改剧情或对白。所有已发表对白与演唱均逐句引用，声音共 '+str(len(cues))+' 个台词／演唱单元（包含正文中写出的听客与路人招呼）。画面参考是待满足的素材槽位，声音保留原句、说话人及预计时间，随画面生成，提示词和占位声不算完成。','',
           '## 共用空间与连续性','',
           '机位以沿河街道为共同参照。主轴从米铺向道具屋，起初画面右侧为前进方向；陶伯在对街而非河对岸，赵执事先在米铺檐下，离开时转向远侧上山岔口。河侧朝米铺的主机位与对街反打之间，先给人物视线或较宽镜头交代方向。这个具体布局是待审制作选择，不是剧本额外地理事实。','',
           '第一场歌本保持由阿蘅掌握，李寄可以翻看但两次递书均未正式交接；第二场擦净手后才交李寄，面对赵执事时阿蘅接回。旧领唱纸落在歌本上，阿蘅合书保留。米袋始终属于阿蘅，第一份工米与第二份预付米分别表现。第二场擦手需要腾手，设计让米袋暂置脚旁，之后按剧本提起。墨耳左耳缺口不随反打镜像。','',
           '固定镜头与清楚的动作优先。口型、眼神、脚拍等局部动作可以在稳定画面上完成；交书、添米、翻巾、喂狗等必须完整演出，另需动作结束参考。具体母版未接受前不批量派生。图像坚持干净平涂人物，不以颗粒、布纹或纸纹代替轻手绘；从母版出发以图生图优先一代，最深累计最多两代。','',
           '## 镜头表','']
    for p in shots:
        start=p['planned_start_frame']/24;end=start+p['duration_frames']/24
        lines.extend([f"### {p['title']} · {start:.0f}–{end:.0f} 秒",'',
                      f"剧情来源：{p['scene_id']} / "+', '.join(x.rsplit('-',1)[-1] for x in p['source']['block_ids'])+'。','',
                      f"叙事目的：{p['purpose']}",'',f"景别／构图：{p['framing']}",'',f"空间：{p['spatial']}",'',
                      f"动作：{p['action_start']} → {p['action_end']}",'',f"运动分工：{p['motion']}",'',
                      f"衔接：{p['continuity']}",'','声音：',''])
        for cue in p['sound']:
            lines.append('- '+(f"{cue['id']} · {cue['speaker']}（{'唱' if cue['type']=='singing' else '说'}）：{cue['text']}" if 'text' in cue else cue['description']))
        lines.extend(['','出场或发声实体：'+'、'.join(names[r['object_id']] for r in p['entities'])+'。','',
                      '完整状态（同一实体按动作顺序列出）：'+'、'.join(names[r['object_id']] for r in p['states'])+'。','',
                      '状态转换：'+('；'.join(names[t['from']['object_id']]+' → '+names[t['to']['object_id']]+'，依据 '+','.join(b.rsplit('-',1)[-1] for b in t['source']['block_ids']) for t in p['state_transitions']) or '本镜完整形态不变，动作与位置变化见上文')+'。','',
                      '必要素材：',''])
        shot_id=next(r['object_id'] for r in document['records'] if r['payload'] is p)
        needs=[r['payload'] for r in document['records'] if r['kind']=='REQUIREMENT' and r['payload']['scope']['object_id']==shot_id]
        for usage,label in [('generation_input','后续生成输入'),('post_audio','后期声音')]:
            labels=[n['title'].split(' · ',1)[1] for n in needs if n['usage']==usage]
            if labels:lines.append('- '+label+'：'+'；'.join(labels)+'。')
        lines.extend(['','每个台词的镜内排练窗口见 `dialogue-cues.json`；窗口按字数暂分，并非声音实测。实体、状态及素材槽位的精确修订依赖见 `shots.json`。',''])
    lines.extend(['## 逐镜视听预演输入','',
                  '图像按实体／状态复用准确素材版本。音频仅输入选定角色音色与歌曲旋律参考；对白、演唱、环境和动作声通过 Seedance 2.0 提示词随画面生成。逐镜计划见 seedance/manifest.json，包含预计时间与承接，缺原件或准确采用时不能宣称可执行或已生成。','',
                  '原生 4K 当前存在工具输出差异：OpenArt 两次 high/4K 请求均返回 2016×2688，尚未取得规格调整确认。因此本文保留要求，未把现有图像候选记为达标原件。'])
    return '\n'.join(lines)+'\n'


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--system',type=Path,required=True);parser.add_argument('--instance',type=Path,required=True);parser.add_argument('--import-records',action='store_true');args=parser.parse_args()
    sys.path.insert(0,str(args.system.resolve()))
    from review_desk.store import Store
    from review_desk import production
    store=Store(args.instance.resolve()/'.runtime/review.sqlite3')
    try:
        document,cues,frames=compile_shots(store,production)
        target=ROOT/'production/episode01';target.mkdir(parents=True,exist_ok=True)
        (target/'shots.json').write_text(json.dumps(document,ensure_ascii=False,indent=2)+'\n')
        names={r['object_id']:r['payload']['title'] for r in production.current_records(store)}
        (target/'shots.md').write_text(render(document,cues,frames,names))
        (target/'dialogue-cues.json').write_text(json.dumps(cues,ensure_ascii=False,indent=2)+'\n')
        changes=refresh_drafts(store,production,document,apply=args.import_records)
        print(json.dumps({'shots':len(SHOTS),'planned_seconds':frames/24,'dialogue_cues':len(cues),'requirements':len(document['records'])-len(SHOTS),'changed_records':len(changes['records']),'imported':args.import_records},ensure_ascii=False))
    finally:store.close()


if __name__=='__main__':main()
