#!/usr/bin/env python3
"""Register later-episode needs from the reviewed scene inventory, without producing media."""
import argparse
import json
from pathlib import Path
import sys
from production_data import refresh_drafts

ROOT = Path(__file__).resolve().parents[1]


def compile_needs(store, production):
    lock = json.loads((ROOT / 'production/source-lock.json').read_text())
    episode_numbers = {e['object_id']: e['number'] for e in lock['episodes']}
    records, counts = [], []
    for scene in production.current_records(store, {'PREPARATION'}):
        p = scene['payload']
        number = episode_numbers[p['source']['object_id']]
        if number == 1:
            continue  # E1 needs are specified at shot level in episode01/shots.json.
        scope = {'object_id': scene['object_id'], 'revision_id': scene['id']}
        image_count = 0

        def add(slot, title, purpose, media_type, entities, states, sources):
            records.append({
                'object_id': f"need-{scene['object_id']}-{slot}", 'kind': 'REQUIREMENT', 'expected_version': 0,
                'payload': {'format': 'production-requirement-v1', 'title': p['title'] + ' · ' + title,
                            'blocks': [{'id': 'purpose', 'text': purpose}], 'scope': scope,
                            'slot': slot, 'purpose': purpose, 'required': True, 'media_type': media_type,
                            'usage': 'generation_input' if media_type == 'image' else 'post_audio',
                            'entities': entities, 'states': states, 'sources': sources,
                            'specification': {'minimum_long_edge': 3840, 'native_4k': True} if media_type == 'image'
                            else {'minimum_sample_rate': 48000},
                            'planning_level': 'scene',
                            'choices': ['本任务登记后续集场需求；角度、录音分句和镜头细化在相应制作任务中确定。'],
                            'unknowns': ['尚无本场完整逐镜设计与实际媒体就绪结论。']}})

        for occurrence in p['occurrences']:
            if occurrence['mode'] == 'mention':
                continue
            entity = production.ref_record(store, occurrence['entity'], {'ENTITY'})
            ep = entity['payload']
            refs = [occurrence['entity']]
            if occurrence['mode'] in ('visual', 'visual_voice') and ep['entity_type'] != 'song':
                add('visual-' + entity['object_id'], ep['title'] + '画面参考',
                    '供本场实际呈现的身份、空间或道具状态使用；可复用合适的精确版本。不能用仅被提及对象的立绘替代本场必需画面。',
                    'image', refs, occurrence['states'], occurrence['evidence'])
                image_count += 1
        counts.append({'episode': number, 'scene': p['source']['scene_id'], 'title': p['title'],
                       'image': image_count, 'source': p['source']})
    counts.sort(key=lambda c: (c['episode'], c['scene']))
    if len(counts) != 40:
        raise ValueError('expected all 40 later-episode scenes from the locked screenplay')
    return {'format': 'production-import-v1', 'records': records}, counts


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--system', type=Path, required=True)
    parser.add_argument('--instance', type=Path, required=True)
    parser.add_argument('--import-records', action='store_true')
    args = parser.parse_args()
    sys.path.insert(0, str(args.system.resolve()))
    from review_desk.store import Store
    from review_desk import production
    store = Store(args.instance.resolve() / '.runtime/review.sqlite3')
    try:
        document, counts = compile_needs(store, production)
        changes = refresh_drafts(store, production, document, apply=args.import_records)
        destination = ROOT / 'production/scene-requirements.json'
        destination.write_text(json.dumps(document, ensure_ascii=False, indent=2) + '\n')
        lines = ['# 全剧集场需求登记', '',
                 '版本四的 42 场均已完成实体检查。第一集两场细化到 33 镜，见 [逐镜设计](episode01/shots.md)；此表登记其余 40 场实际呈现／发声所需的素材，不要求本任务生产后续各集媒体。', '',
                 '一项需求表示一个使用位置，不等于必须新造一个文件。同一素材可服务多个场或多个实体；同场不同剧情状态保留独立状态引用。仅提及的人和物不据此要求画面；对白、歌词和环境动作声依据保留在场次与后续镜头描述中，随画面生成。', '',
                 '画面引用完整状态；角色音色与歌曲旋律基准登记在实体状态内，同一基准可供多个镜头参考。只需描述即可随镜呈现的声音状态，不再要求独立原件。', '',
                 '表中数量是计划槽位数，不是已经制作的素材数。需求仍需在后续镜头设计时确定角度、时段与具体版本；没有用图像提示词、平台链接或占位声充作实际媒体。', '',
                 '| 集 | 场 | 场次 | 画面参考槽位 |',
                 '| --- | --- | --- | ---: |']
        for count in counts:
            lines.append(f"| {count['episode']} | {count['scene']} | {count['title']} | {count['image']} |")
        lines.extend(['', f"后续 40 场共 {len(document['records'])} 项计划需求。来源、实体、状态及准确集场修订保存在 [完整需求数据](scene-requirements.json)，并在隔离审阅台的‘全剧制作’按集场浏览。", '',
                      '第一集后续生成以自己的逐镜需求为准；其他各集的本表并不代表镜头设计、素材或最终视频已完成。', ''])
        (ROOT / 'production/scene-requirements.md').write_text('\n'.join(lines))
        print(json.dumps({'scenes': len(counts), 'requirements': len(document['records']), 'changed_records': len(changes['records']), 'imported': args.import_records}))
    finally:
        store.close()


if __name__ == '__main__':
    main()
