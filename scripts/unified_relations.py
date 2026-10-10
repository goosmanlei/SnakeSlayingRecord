"""Story-specific, reviewable relationship cutover; never replace a live database."""
import argparse
import copy
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

HISTORY = {'commit': 'b84f7bc8c2aa3ac62dd19c33912ad5d20fba4d34',
           'file': 'export/objects.json',
           'sha256': '314e7962531248c4e18ab1769810896bb622931aca7f2e74c5ffefeb32ee3c7d'}


def ref(row):
    return {'object_id': row['object_id'], 'revision_id': row['id']}


def unique(values):
    return list({json.dumps(v, sort_keys=True, ensure_ascii=False): v for v in values}.values())


def prose(text):
    return str(text or '').strip().strip('；。') + '。' if text else ''


def stage_text(shot):
    return '；'.join(s['description'].rstrip('。') for s in shot['payload'].get('key_states', []))


def compose(rows, historic, read):
    """One coherent text, with scope restrictions rather than hidden subedges."""
    first = rows[0]; value = first['payload']
    kind = value.get('type_id') if first['kind'] == 'MATERIAL_RELATION' else value['relation_type']
    source = historic.get(first['object_id'], first)['payload']
    sources = [ref(r) for r in rows]
    contexts = []
    if kind == 'entity':
        ends = [r['object_id'] for r in value['entities']]
        sources += value['sources']; contexts += value.get('applies_to', [])
        summary = value['label']
        body = '\n'.join(b['text'] for b in value['blocks'])
        if first['object_id'] == 'relationship-li-ji-a-heng-personal':
            summary = '从一起撑布到换手抄词，相互照应并保留各自决定。'
            body = ('李寄帮阿蘅撑起湿布，阿蘅把干净布边递给她并避开伤口；到堂前收妥凭据，李寄在廊口接住阿蘅的手。'
                    '这种照应延续到灯下抄词：李寄掌心新疤绷紧时，阿蘅接笔，让她慢慢念，纸留在两人中间。'
                    '动作中的帮助随处境交换，阿蘅自己的谈判、留证和选择不交由李寄代言。')
        elif first['object_id'] == 'relationship-zhao-a-heng-personal':
            summary = '以领唱和免债招募，继而以债账胁迫；阿蘅拒住并当面对质。'
            body = ('赵执事以进庙领唱、免债和额外祭粮要求阿蘅住到祭礼结束；阿蘅坚持只白天唱、散后回家，'
                    '他转而把欠账算作七斗，并以工钱抵债。后来堂前，赵仍辩称只是唱曲，阿蘅拿今年祭册上的名字和送入日期反问。'
                    '招募、胁迫和对质属于同一段关系的发展，按所在阶段表演，不把后来的揭露提前为两人当时已知。')
        return ends, 'related', summary, [prose(body)], unique(sources), unique(contexts), kind
    if kind == 'applicability':
        ends = [value['subject']['object_id'], value['scope']['object_id']]
        shot = read(ends[1]); contexts = [ref(shot)]
        sources += [value['subject'], value['scope'], *shot['payload'].get('sources', [])]
        summary, body = TEXT_STAGES[ends[1]]
        return ends, 'forward', summary, [body], unique(sources), contexts, kind
    upstream = read(value['upstream']['object_id']); downstream = read(value['downstream_id'])
    ends = [upstream['object_id'], downstream['object_id']]
    sources += [value['upstream']]
    contexts = [r['payload']['context'] for r in rows]
    sources += contexts
    title = upstream['payload']['title'].replace(' · 整体参考', '').replace(' · 身份母版', '')
    kinds = {r['payload'].get('type_id') for r in rows}
    if 'voice-reuse' in kinds:
        source = next(historic.get(r['object_id'], r)['payload'] for r in rows if r['payload'].get('type_id') == 'voice-reuse')
        alternative = next(historic.get(r['object_id'], r)['payload'] for r in rows if r['payload'].get('type_id') == 'existing-candidate')
        summary = '旧原件提供声音身份；片段选择、当前表演和认可分别判断。'
        body = [prose(source['preserve']) + prose(source['change']),
                '同一原件既可供比较，也可按当前方案选定的组成和时段复用。' + prose(alternative['check'])]
        return ends, 'forward', summary, body, unique(sources), unique(contexts), 'voice-reuse-merged'
    if kind == 'identity-state':
        summary = '身份母版约束同一主体，完整状态在本阶段内变化。'
        body = ['母版保留主体身份、轮廓、比例与结构；状态差异为：' + prose(source['change']),
                '状态中的动作、持物和声音描述按具体场镜选用，不把跨场的允许行为同时画入一张参考。' + prose(source.get('check'))]
    elif kind == 'state-frame':
        summary = title + '只约束本镜起点已可见的身份与状态。'
        prompt = downstream['payload'].get('generation', {}).get('prompt', '')
        start = next((line.split('：', 1)[1] for line in prompt.splitlines() if line.startswith('只画动作开始的瞬间：')), '')
        body = ['本参考约束' + title + '的轮廓、比例及当前可见状态；位置、持物与姿势服从本镜起点，不连带重演参考中的其他动作。' + ('起点为：' + prose(start) if start else ''),
                '全镜连续性要求为：' + prose(source.get('check')) + '首帧只呈现此前已经成立的部分，后续动作与结果留给视频。']
    elif kind == 'space-camera':
        summary = '保持空间结构和通道，只改变本镜机位、景别与光线。'
        body = [prose(source['purpose']) + prose(source['preserve']) + prose(source['change']), prose(source.get('check'))]
    elif kind == 'frame-video':
        summary = '起始图约束已可见构图与手位，后续声画按本镜顺序展开。'
        body = [prose(source['purpose']) + prose(source['preserve']),
                '从该起点重新生成本镜动作、对白、呼吸与环境声。' + prose(source.get('check'))]
    elif kind == 'voice-performance':
        summary = source['purpose'].split('：')[0] + '只提供声音身份，语气、气息和空间按本镜重演。'
        body = [prose(source['purpose']) + prose(source['preserve']),
                '台词、呼吸、音量、情绪、声源距离和入声时点由本镜正文决定；不继承参考试读词、旧语气、录音空间或演唱旋律。' + prose(source.get('check'))]
    elif kind == 'state-video':
        summary = prose(source['purpose'])
        body = [prose(source['preserve']) + prose(source['change']), prose(source.get('check'))]
    elif kind == 'reference':
        summary = ('曲调只约束旋律与节拍，角色音色和本镜词句分别确定。' if '曲调' in source['purpose']
                   else '机位提供构图和空间轴线，人物道具按动作起点进入。')
        body = [prose(source['purpose']) + prose(source['preserve']) + prose(source['change']), prose(source.get('check'))]
    elif kind == 'existing-candidate':
        summary = '旧候选供比较；准确选择与新方案认可不能由关系代替。'
        body = [prose(source['purpose']) + prose(source['preserve']), prose(source['change']) + prose(source.get('check'))]
    else:
        raise ValueError('未审阅的关系家族：' + str(kind))
    if set(ends) == {'material-form-a-heng-blue-overall', 'material-av-e01-a01-s01-first-frame'}:
        summary = '保留阿蘅身份与干燥青衣；歌本在手、河石在篮，尚未翻页。'
        body = ['阿蘅沿用日常完整状态的清瘦比例、低髻和洗旧青绿衣，衣鞋干燥，脸与手不增加新伤。'
                '首帧只在空竹篮旁站定：歌本尚在手中，河石搁在篮面；不提前摊书、压石或翻过两页。',
                '后续摊本、压石、演唱和翻页属于视频的动作过程；未交付的米工钱和后入画的李寄不放进起点。']
    return ends, 'related' if kind == 'existing-candidate' else 'forward', summary, [b for b in body if b], unique(sources), unique(contexts), kind


# Each description belongs to one actual shot. Shared text assets do not make
# every phase of that asset simultaneously visible in all of these shots.
TEXT_STAGES = {
 'av-e01-a03-s06': ('旧纸抽出并落到歌本后才露首张十字。', '起镜旧纸仍未抽出。赵执事取出后放在歌本上，首张按准确字稿处理，其余页不增加可读词；纸和本保持分离，不先画成夹好。'),
 'av-e03-a01-s06': ('只保留已知五字与缺词空白，接纸后才夹回残本。', '阿蘅已接过新纸，既有五字之后留白；试哼在缺处停住，之后由她夹纸收本。不补写后来歌娘核定的词，不重演前镜的递纸。'),
 'av-e07-a04-s03': ('残页与缺词空白仍在；本镜用歌本和记工凭据陈述债情。', '歌本由未展开到展开，旧残页破口与缺词空白保持，记工纸和免祭纸各在原位。已知字稿用于可见纸面；不在此镜重演补抄、递接或修好歌本。'),
 'av-e16-a03-s01': ('新旧纸并列仍缺词，李寄看空白而不拿笔。', '泡皱旧页和半补新纸分开，既有五字之后仍空。物质好转不等于歌词已经补齐，不借后来的核全页填入新词。'),
 'av-e16-a03-s03': ('母女唱到同一断处停下，纸上缺词保持留白。', '母亲先哼、阿蘅后接，二人在原缺处停住。新旧纸未包起，空白不补字，不提前使用歌娘教授的后续词。'),
 'av-e03-a02-s09': ('背页只有工价约定，向李寄说明时不出现已做工钱。', '赵已离场，阿蘅持歌本与炭头，李寄走近后才看背页。此时记的是一日两升的工价约定，不是已经完成第一日劳动的收入。'),
 'av-e04-a01-s03': ('约定已在，落笔后才出现第一笔两升工钱。', '第一夜起点只已有“一日两升”的约定，第一笔位置为空。阿蘅写下当天墨记和第一笔“两升”后才显相应字层；日期保持未定的墨记，不编清晰日期。第二笔和圈合计尚未出现，约定额不算工钱。'),
 'av-e04-a01-s05': ('第二夜先有第一笔，再写第二笔；两笔圈成四升。', '起点保留同页工价约定和第一笔“两升”，第二笔为空，圈尚未合。第二笔随落笔出现，之后只圈两笔已做工钱，合计四升；圈不包含“一日两升”的约定，不产生第三笔收入或可读的虚构日期。'),
 'av-e07-a02-s06': ('取出记工纸后显示工作约定，唱调不等于自愿献祭。', '阿蘅从衣内取纸后，以已有约定和两笔记工说明自己答应的是唱调。原字层不增改为同意入祭；不把取纸动作提前到首帧。'),
 'av-e07-a02-s04': ('梁取来旧祭册后才显旧条款，不提前换成新文书。', '前两年祭册抄本由梁书吏取来再翻开，旧册上的自愿说法属于受质疑的记录。新白纸、本人非自愿声明和永久禁祭条款此时都不提前写入。'),
 'av-e07-a03-s03': ('非自愿声明随书吏落笔出现，写完后才收手。', '新白纸正在记录已经宣布的条件，本人非自愿的空行尚未写。阿蘅要求后才写入“不是自愿的”相应字稿；不提前盖印、按手印或折纸，不混作另一张免祭纸。'),
 'av-e07-a03-s04': ('按本镜交接分别处理应募纸和阿蘅免祭纸。', '承接已写成的非自愿记录，纸张各守其用途与交接顺序；准确文字以本镜源文和交接方案为准。此阶段不提前带入之后补定的永久禁祭与外部改造条款。'),
 'av-e09-a02-s04': ('县丞宣布不论成败不得索人，书吏换纸后才写入。', '起点新增条款尚空。父亲先问、县丞看口供停顿再宣布，梁换到新纸写完整句，父亲等写完才指图。此镜不提前出现改造许可或盖印，也不把保障附加为除蛇成功的条件。'),
 'av-e09-a03-s01': ('摊开已盖印新文书，阿蘅确认“任何一户”后再看一遍。', '父亲把县衙带来的完整新文书摊在仓院干木板上，阿蘅指停“任何一户”旁而不遮字，听李绡读准确一句，再看一次才让开。父亲随后收妥，不与将取出的借据、原单混堆；纸上条款已经完成，不重演书写。'),
 'av-e11-a03-s01': ('阿蘅取出自己的折纸后读字，李寄随后移灯相助。', '起点文书还在衣内，李寄未移灯。阿蘅取出展开，表达仍怕对方改口、要亲自再说不是自愿的决定，李寄才挪灯照字。只使用这张准确文书已有字稿，不偷换成父亲持有的另一份文书或补新条款。'),
 'av-e15-a04-s01': ('旧贴纸与祭册并置对质，不能合为同一文书。', '赵先指已揭贴纸上的“供奉”，阿蘅随后把今年祭册转向他。姓名字区不镜像，送入日期只保留字段位置，不编可读日历日期；旧据、贴纸、祭册及后续裁定分别保留。'),
 'av-e15-a04-s08': ('旧册翻开后并置状纸与两份批文，同署名揭示批准责任。', '父亲先翻到阿禾、小满两页，指“自愿入祀”和各页脚官印；完整追问后梁停笔。陶伯随后取出状纸，程再放两份准祭批文。签押只作为同一人的笔迹图形核对，不虚构可读全名或新判决，首帧不提前陈列全部纸张。'),
 'av-e09-a03-s05': ('两纸已揭离；放下贴纸后用木条对明供奉小字与手印。', '起点原约已经全露，湿贴纸仍由梁托住。先把贴纸摊在旁边，再拿木条指两纸原接位，供奉小字末尾与旧据手印对应，之后放回木条。不重演前镜揭纸，不把供奉小字写回原据，不将两纸重新粘合；未给原词的条款保持不可清晰拼读。'),
 'av-e16-a04-s04': ('核全新页已在，阿蘅亲自唱过旧缺处到旧桥。', '歌娘已逐行核妥新页，阿蘅才重新起唱。准确词稿用于本次完整演唱与纸面，不改成歌娘代唱；“认旧桥”按已核原词，不回写早期的缺词页。'),
 'av-e16-a04-s05': ('核全页保留；先收前镜尾音，再由阿蘅主动轻唱缺句。', '不重复前镜整段末句。歌娘收拍与回应后，阿蘅自发再唱刚学会的缺词，李寄完整听完；纸面使用已核字稿，不重新补写或倒退为未知缺词。'),
 'av-e17-a01-s01': ('新誊页尚未到半页，核稿与誊写进度分开。', '歌娘核稿可完整，新誊纸只按当前已写进度显字；李寄新疤发紧笔歪发生在写到半页后。新纸未订，不能拿已完成字页充当起点。'),
 'av-e17-a01-s03': ('阿蘅接笔后逐字完成末行，文字随书写显现。', '起点末行未完成，李寄慢念、阿蘅逐字写，最后才放笔；完成字稿是最终校对依据，不在第一帧提前铺满末行。'),
 'av-e17-a01-s04': ('新页已写好未装订；唱过旧断处而不再留缺词。', '本镜纸面已经誊好，歌本由翻回前页进入演唱；阿蘅唱过旧断处，母亲只无词轻哼末句。此镜不装订、不先把旧页归后。'),
 'av-e17-a01-s05': ('完整字页先散放，再装订；旧残页保留。', '新誊页文字已完成，起点仍未对齐、未订，针线在侧。按动作把旧残页夹后、新页穿孔订入，不能用订牢状态作开场，也不删旧页泡皱痕迹。'),
 'av-e17-a01-s06': ('新页已订牢，试翻核线结，完整文字保持。', '承接已完成的装订，翻过去再翻回来，核线结未松。字层跟随纸页运动，新旧纸质感与残页位置保持，不再重演书写或穿线。'),
 'av-e17-a03-s03': ('新旧页交接处已补齐，李寄停手抬眼等待。', '完整歌页已可使用；本镜在新旧交接处唤起旧日断句的记忆，不重新擦掉已补词，也不让文字替代李寄停手、抬眼的反应。'),
 'av-e17-a04-s07': ('进门后才把修好的整本摊到母亲面前。', '阿蘅起点仍持本在门外，推门、走近后才摊本。完整歌词已订牢，旧残页仍保留；不把母亲、已摊开的歌本或完整桌面提前透墙放进首帧。'),
}


def build(store, history):
    from review_desk import production as p, business_relations as br
    historical = {r['object_id']: r for r in history}
    legacy = [r for r in p.current_records(store, {'RELATION', 'MATERIAL_RELATION'}) if br.is_legacy(r['kind'], r['payload'])]
    cache = {}
    def read(oid):
        if oid not in cache: cache[oid] = p.record(store, oid)
        return cache[oid]
    groups = defaultdict(list)
    for row in legacy:
        if row['object_id'] not in historical or br.pair(br.legacy_endpoints(row)) != br.pair(br.legacy_endpoints(historical[row['object_id']])):
            raise ValueError('历史与当前对象对不一致：' + row['object_id'])
        groups[br.pair(br.legacy_endpoints(row))].append(row)
    records, families, aliases = [], Counter(), {}
    for ends, group in sorted(groups.items()):
        endpoint_ids, direction, summary, paragraphs, sources, contexts, family = compose(group, historical, read)
        oid = br.identity(endpoint_ids)
        payload = br.normalize({'format': 'production-relation-v1', 'relation_type': 'business',
            'title': ' · '.join(read(e)['payload']['title'] for e in ends),
            'endpoints': endpoint_ids, 'direction': direction, 'summary': summary,
            'blocks': [{'id': 'relation-' + str(i+1), 'text': text} for i, text in enumerate(paragraphs)],
            'sources': sources, 'contexts': contexts, 'status': 'withdrawn' if all(r['payload'].get('status') == 'withdrawn' for r in group) else 'active'})
        records.append({'object_id': oid, 'kind': 'RELATION', 'expected_version': 0, 'payload': payload})
        families[family] += 1
        for row in group: aliases[row['object_id']] = oid
    return {'format': 'unified-relations-migration-v1', 'history': HISTORY,
            'expected_heads': {r['object_id']: r['id'] for r in legacy},
            'aliases': aliases, 'records': records, 'families': dict(families)}


def rebind(store):
    from review_desk import production as p, business_relations as br, material_relations
    records = []
    aliases = dict(store.db.execute('SELECT alias_id,relation_id FROM business_relation_aliases'))
    for row in p.current_records(store, {'REQUIREMENT'}):
        payload = copy.deepcopy(row['payload']); changed = 0
        for item in payload.get('generation', {}).get('inputs', []):
            old = item.get('relation')
            if not old or old['object_id'] not in aliases: continue
            for key, value in material_relations.rules(store, item, row['object_id']).items():
                if key in br.CHOICES: item[key] = value
            item['relation'] = ref(p.record(store, aliases[old['object_id']]))
            changed += 1
        if not changed: continue
        payload['method_adjustment'] = {'parent': ref(row), 'operation': 'relation-contract'}
        records.append({'object_id': row['object_id'], 'kind': 'REQUIREMENT', 'expected_version': row['version'], 'payload': payload})
    return {'format': 'production-import-v1', 'records': records}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--system', type=Path, required=True)
    parser.add_argument('--instance', type=Path, required=True)
    sub = parser.add_subparsers(dest='action', required=True)
    plan = sub.add_parser('plan'); plan.add_argument('--history', type=Path, required=True); plan.add_argument('--output', type=Path, required=True)
    apply = sub.add_parser('apply-relations'); apply.add_argument('--plan', type=Path, required=True)
    binding = sub.add_parser('rebind'); binding.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(); sys.path.insert(0, str(args.system.resolve()))
    from review_desk.store import Store
    from review_desk import business_relations as br
    store = (Store if args.action == 'apply-relations' else Store.open_readonly)(args.instance / '.runtime/review.sqlite3')
    try:
        if args.action == 'apply-relations':
            print(json.dumps(br.apply_migration(store, json.loads(args.plan.read_text())), ensure_ascii=False)); return
        result = build(store, json.loads(args.history.read_text())) if args.action == 'plan' else rebind(store)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
        print(json.dumps({'output': str(args.output), 'records': len(result['records']), 'families': result.get('families')}, ensure_ascii=False))
    finally: store.close()


if __name__ == '__main__': main()
