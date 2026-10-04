#!/usr/bin/env python3
"""Build a disposable UI acceptance fixture; never export or publish it as story data.

Run from the story task worktree:
  python3 scripts/ui_unification_browser_fixture.py \
    --system .runtime/ui-unification/system \
    --instance .runtime/ui-unification/browser-fixture

All new media are locally synthesized test patterns/tones, not AI generations
or story deliverables. Existing destinations are always rejected. The original
initialization baseline is retained untouched. No export/prepare command exists.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
import time
from urllib.parse import urlencode

from generation_review import initialize
from generation_workspace import contained, generation_root, isolated_instance
from generation_publication import backup

ROOT = Path(__file__).resolve().parents[1]
PREFIX = 'ui-fixture-'
NOTICE = '仅技术验收：本地色块与短音，非 AI 生成、非收费成果，禁止正式发布或交付。'
POLICY = {'purpose': 'ui-acceptance-only', 'synthetic': True,
          'ai_generated': False, 'external_service_used': False,
          'export_for_delivery_allowed': False, 'formal_publication_allowed': False}


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def write_json(path, value):
    with Path(path).open('x') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


def destination(root, requested):
    instance = isolated_instance(root, requested)
    if any('baseline' in part.lower() or 'formal' in part.lower()
           for part in instance.relative_to(root).parts):
        raise ValueError('technical fixture cannot target a baseline or formal directory')
    if instance.exists():
        raise ValueError('fixture destination already exists; choose a new .runtime path; no overwrite/resume')
    return instance


def build(root, system, instance):
    # Validate everything before initialization creates any destination files.
    system = contained(root, system).resolve(strict=True)
    if not (system / 'review_desk/store.py').is_file():
        raise ValueError('--system must name this task worktree review system')
    for executable in ('ffmpeg', 'ffprobe'):
        if not shutil.which(executable):
            raise ValueError(executable + ' is required for real local media')
    evidence = root / 'production/breakdown/evidence/browser-fixture-readback.json'
    legacy = json.loads(evidence.read_text())
    if not legacy.get('comments') or not legacy.get('adoptions'):
        raise ValueError('prior fixture evidence lacks comment/adoption examples')
    sys.path.insert(0, str(system))
    from review_desk import production as p, material_plans as mp
    from review_desk import production_breakdown as bd
    from review_desk.production_media import ingest, validate_component
    from review_desk.store import Store

    initialize(root, instance)
    runtime = instance / '.runtime'
    baseline = runtime / 'generation-base.sqlite3'
    baseline_hash = sha(baseline)
    write_json(instance / 'TECHNICAL_FIXTURE_DO_NOT_PUBLISH.json', {
        **POLICY, 'notice': NOTICE, 'source_evidence': str(evidence.relative_to(root)),
        'source_evidence_sha256': sha(evidence), 'baseline_sha256': baseline_hash})
    config_path = instance / 'config/instance.json'
    config = json.loads(config_path.read_text())
    config.update(title='技术验收夹具 · 禁止正式交付', technical_fixture=POLICY)
    config_path.write_text(json.dumps(config, ensure_ascii=False, indent=2) + '\n')

    # Imports commit independently in the public API. Build a private DB first;
    # only a fully verified result replaces this NEW instance's serving DB.
    staging = runtime / 'ui-fixture-build.sqlite3'
    backup(runtime / 'review.sqlite3', staging)
    store = Store(staging)
    initial_heads = {r['id']: r['current_revision'] for r in store.objects()}
    if any(k.startswith(PREFIX) for k in initial_heads):
        raise ValueError('initialization snapshot already contains technical fixture objects')
    created, commands, media, comments = [], [], {}, []
    scratch = runtime / 'technical-media'
    scratch.mkdir()

    def ref(oid):
        row = p.record(store, oid)
        return {'object_id': oid, 'revision_id': row['id']}

    def put(oid, kind, **payload):
        if not oid.startswith(PREFIX):
            raise ValueError('fixture may only create/update its own object prefix')
        try:
            expected = p.record(store, oid)['version']
        except KeyError:
            expected = 0
        value = {'format': 'production-' + p.KINDS[kind] + '-v1',
                 'title': '技术验收 · ' + oid.removeprefix(PREFIX),
                 'blocks': [{'id': 'fixture-notice', 'text': NOTICE}],
                 **payload, 'technical_fixture': POLICY}
        p.import_records(store, {'format': 'production-import-v1', 'records': [{
            'object_id': oid, 'kind': kind, 'expected_version': expected, 'payload': value}]})
        if oid not in created:
            created.append(oid)
        return ref(oid)

    def run_media(name, arguments):
        path = scratch / name
        command = ['ffmpeg', '-hide_banner', '-loglevel', 'error', '-nostdin',
                   '-n', *arguments, str(path)]
        subprocess.run(command, check=True, timeout=60, capture_output=True)
        with path.open('rb') as stream:
            component = ingest(instance, stream, name)
        validate_component(instance, component)
        commands.append({'file': component['file'], 'argv': command,
                         'exit_code': 0, 'notice': NOTICE})
        media[name] = component
        return component

    def make_asset(oid, component, prompt, seed=None, needs=(), input_image=None):
        call = oid + '-call'
        inputs = [{**input_image, 'component_id': 'original'}] if input_image else []
        fields = dict(method='generation', tool='local-ffmpeg-technical-fixture',
                      status='submitted', inputs=inputs, outputs=[],
                      model='local-ffmpeg-technical-fixture-v1',
                      parameters={'duration_seconds': 4, 'width': 640, 'height': 360},
                      randomization={'mode': 'random'}, prompt=prompt,
                      execution={'command_index': len(commands) - 1,
                                 'actual_local_execution': True, 'paid_call': False})
        if seed is not None:
            fields['actual_seed'] = seed
        lineage = {'i2i_depth': 0, 'references': []} if component['mime'].startswith('image/') else {}
        put(call, 'CALL', **fields, lineage=lineage)
        asset = put(oid, 'ASSET', media_type=component['mime'].split('/')[0],
                    subjects=[], states=[], components=[component], production=ref(call),
                    lineage=lineage, candidate_requirements=list(needs))
        fields.update(status='completed', outputs=[asset])
        put(call, 'CALL', **fields, lineage=lineage)
        return asset

    def plan(prompt, image):
        return {'format': 'generation-plan-v1', 'method': 'generate',
                'tool': 'local-ffmpeg-technical-fixture', 'model': 'local-ffmpeg-technical-fixture-v1',
                'parameters': {'duration_seconds': 4, 'width': 640, 'height': 360},
                'randomization': {'mode': 'random'}, 'prompt': prompt,
                'inputs': [{'reference': image, 'component_id': 'original',
                            'use': '图片1：本地合成的准确色块原件，仅验收引用链接'}],
                'output': {'name': '技术色块视频', 'description': NOTICE,
                           'review_criteria': ['仅核对版本、调用、引用、媒体与评论；不是创作质量验收']},
                'blockers': []}

    def need(oid, scope, prompt, image):
        return put(oid, 'REQUIREMENT', scope=scope, slot=oid, required=False,
                   purpose=NOTICE, media_type='video', usage='editorial', entities=[], states=[],
                   specification={}, generation=plan(prompt, image))

    def video(oid, seed, prompt, image, needs):
        # The actual seed deterministically controls local hue and tone frequency.
        # This is not a fabricated model receipt: argv records the real process.
        base = instance / 'export/assets' / media['reference.png']['file']
        component = run_media(oid + '.mp4', [
            '-loop', '1', '-i', str(base), '-f', 'lavfi', '-i',
            f'sine=frequency={220 + seed * 3}:sample_rate=48000:duration=4',
            '-vf', f'hue=h={seed * 13},drawgrid=width=80:height=60:thickness=2:color=white@0.7',
            '-af', 'volume=0.12', '-t', '4', '-r', '24', '-c:v', 'libx264',
            '-preset', 'ultrafast', '-pix_fmt', 'yuv420p', '-c:a', 'aac',
            '-movflags', '+faststart', '-metadata', 'comment=TECHNICAL FIXTURE; NOT A DELIVERABLE'])
        return make_asset(oid, component, prompt, seed, needs, image)

    def adopt(oid, scope, need_ref, asset):
        return put(oid, 'RELATION', relation_type='adoption', scope=scope,
                   slot=p.ref_record(store, need_ref)['payload']['slot'], asset=asset,
                   component_id='original', usage='editorial',
                   range={'start_seconds': .5, 'end_seconds': 2.5}, reason=NOTICE + ' 明确采用旧候选。')

    def comment(oid, target, anchor, scope=None):
        value = {'id': oid, 'target_object_id': target['object_id'],
                 'target_revision_id': target['revision_id'], 'body': NOTICE,
                 'anchor': anchor}
        if scope:
            value['material_context'] = {'material_id': scope[0], 'number': scope[1], 'model': 'plan-v1'}
        comments.append(store.create_comment(value))

    try:
        catalog = bd.catalog(store)
        episode = p.record(store, catalog['episode'])
        if episode['payload'].get('number') != 1:
            raise ValueError('current input lock does not start at episode 1; select context explicitly')
        scene = catalog['scenes'][0]
        original_shot = next(s for s in catalog['shots'] if s['payload']['parent'] == bd.ref(scene))
        source_payload = copy.deepcopy(original_shot['payload'])
        for key in ('format', 'title', 'blocks'):
            source_payload.pop(key, None)
        history = put(PREFIX + 'shot-history', 'SHOT_DESIGN', **{
            **source_payload, 'purpose': '技术验收历史镜头：旧修订', 'number': 1})
        current = put(PREFIX + 'shot-history', 'SHOT_DESIGN', **{
            **source_payload, 'purpose': '技术验收历史镜头：当前修订', 'number': 1})
        pending_shot = put(PREFIX + 'shot-pending', 'SHOT_DESIGN', **{
            **source_payload, 'purpose': '技术验收：当前方案未生成', 'number': 2})

        image_component = run_media('reference.png', ['-f', 'lavfi', '-i',
            'color=c=red:s=640x360:r=1,drawbox=x=160:y=90:w=320:h=180:color=yellow:t=fill',
            '-frames:v', '1', '-threads', '1'])
        image = make_asset(PREFIX + 'image-reference', image_component, NOTICE + ' 合成红底黄框输入图片。')
        audio_component = run_media('tone.wav', ['-f', 'lavfi', '-i',
            'sine=frequency=660:sample_rate=48000:duration=4', '-af', 'volume=0.12', '-c:a', 'pcm_s16le'])
        audio = make_asset(PREFIX + 'audio-tone', audio_component, NOTICE + ' 合成 660Hz 短音。')

        prompt1 = NOTICE + ' 方案一：图片1为准确色块底图；按实际种子改变色相并加短音。'
        prompt2 = NOTICE + ' 方案二：保留图片1的黄色方框与网格，检查版本切换后的准确引用。'
        main_id, pending_id = PREFIX + 'need-shot-video', PREFIX + 'need-pending-video'
        main1 = need(main_id, current, prompt1, image)
        old1 = video(PREFIX + 'video-v1-old', 11, prompt1, image, [main1])
        time.sleep(1.05)  # Store timestamps are seconds; keep newest ordering observable.
        new1 = video(PREFIX + 'video-v1-new', 22, prompt1, image, [main1])
        main2 = need(main_id, current, prompt2, image)
        scene_need = need(PREFIX + 'need-scene-video', bd.ref(scene), prompt2, image)
        episode_need = need(PREFIX + 'need-episode-video', bd.ref(episode), prompt2, image)
        history_need = need(PREFIX + 'need-history-video', history, prompt2, image)
        old2 = video(PREFIX + 'video-v2-old-adopted', 33, prompt2, image,
                     [main2, scene_need, episode_need, history_need])
        time.sleep(1.05)
        new2 = video(PREFIX + 'video-v2-new', 44, prompt2, image, [main2])
        adoption = adopt(PREFIX + 'adoption-shot-old', current, main2, old2)
        adopt(PREFIX + 'adoption-scene', bd.ref(scene), scene_need, old2)
        adopt(PREFIX + 'adoption-episode', bd.ref(episode), episode_need, old2)
        pending1 = need(pending_id, pending_shot, prompt1, image)
        # Associate an actual prior local result; do not pretend another run occurred.
        prior = p.record(store, new1['object_id'])
        put(prior['object_id'], 'ASSET', **{
            **prior['payload'], 'candidate_requirements': [main1, pending1]})
        need(pending_id, pending_shot, prompt2 + ' 当前版本故意不执行。', image)

        video_component = p.ref_record(store, old2)['payload']['components'][0]
        comment(PREFIX + 'comment-video-time', old2, {
            'type': 'time', 'component_id': 'original', 'asset_file': video_component['file'],
            'start_seconds': .5, 'end_seconds': 1.5}, (main_id, 2))
        comment(PREFIX + 'comment-audio-time', audio, {
            'type': 'time', 'component_id': 'original', 'asset_file': audio_component['file'],
            'start_seconds': .2, 'end_seconds': .3})
        comment(PREFIX + 'comment-image-region', image, {
            'type': 'region', 'visual_id': 'original', 'asset_file': image_component['file'],
            'points': [{'x': .25, 'y': .25}, {'x': .75, 'y': .25},
                       {'x': .75, 'y': .75}, {'x': .25, 'y': .75}]})
        comment(PREFIX + 'comment-historical-shot', history, {'type': 'global'})

        versions, waiting = mp.snapshot(store, main_id), mp.snapshot(store, pending_id)
        assert [(v['number'], len(v['results'])) for v in versions] == [(2, 2), (1, 2)]
        assert [(v['number'], len(v['results'])) for v in waiting] == [(2, 0), (1, 1)]
        calls = []
        for version in versions:
            for candidate in version['results']:
                call = p.ref_record(store, candidate['payload']['production'])
                assert call['payload']['inputs'] == [{**image, 'component_id': 'original'}]
                assert '图片1' in call['payload']['prompt']
                calls.append({'version': version['number'], 'candidate': bd.ref(candidate),
                              'call': bd.ref(call), 'prompt': call['payload']['prompt'],
                              'actual_seed': call['payload']['actual_seed']})
        assert len({c['call']['object_id'] for c in calls}) == 4
        assert bd.context(store, history['object_id'], history['revision_id'])['requirements'][0]['object_id'] == history_need['object_id']
        for scope, expected in [(current, main_id), (bd.ref(scene), scene_need['object_id']),
                                (bd.ref(episode), episode_need['object_id'])]:
            assert expected in {n['object_id'] for n in bd.context(store, **{
                'object_id': scope['object_id'], 'revision_id': scope['revision_id']})['requirements']}
        heads = {r['id']: r['current_revision'] for r in store.objects()}
        assert all(heads[oid] == revision for oid, revision in initial_heads.items())
        assert not store.db.execute('PRAGMA foreign_key_check').fetchall()
        mp.validate(store)
        assert sha(baseline) == baseline_hash
        routes = {
            'production': {'workspace': 'production.workspace', 'breakdown_episode': episode['object_id'],
                           'breakdown_scene': scene['object_id'], 'breakdown_object': current['object_id'],
                           'breakdown_revision': current['revision_id']},
            'historical_shot': {'workspace': 'production.workspace', 'breakdown_episode': episode['object_id'],
                                'breakdown_scene': scene['object_id'], 'breakdown_object': history['object_id'],
                                'breakdown_revision': history['revision_id']},
            'materials': {'workspace': 'materials.workspace', 'production_object': main_id,
                          'material_id': main_id, 'material_version': 2}}
        receipt = {'format': 'ui-unification-technical-fixture-v1', **POLICY, 'notice': NOTICE,
                   'instance': str(instance.relative_to(root)), 'baseline_sha256': baseline_hash,
                   'baseline_unchanged': True, 'existing_object_heads_unchanged': True,
                   'episode': bd.ref(episode), 'scene': bd.ref(scene),
                   'shot_current': current, 'shot_history': history, 'shot_pending': pending_shot,
                   'main_requirement': main_id, 'pending_requirement': pending_id,
                   'main_versions': [{'number': v['number'], 'candidates': len(v['results'])} for v in versions],
                   'pending_versions': [{'number': v['number'], 'candidates': len(v['results'])} for v in waiting],
                   'candidates': calls, 'adoption': p.ref_record(store, adoption),
                   'image_input': image, 'audio': audio, 'comments': comments,
                   'created_objects': created, 'media': media, 'commands': commands,
                   'routes': {key: '/?' + urlencode(value) for key, value in routes.items()},
                   'browser_verified': False, 'server_started': False,
                   'plan_contract': '同版独立 CALL 保持相同 prompt；不同 prompt 依法形成下一方案版本。',
                   'publication_boundary': '此夹具不得传给 generation_review export/prepare 或任何正式发布工具。'}
    finally:
        store.close()
    staging.replace(runtime / 'review.sqlite3')
    receipt['fixture_database_sha256'] = sha(runtime / 'review.sqlite3')
    write_json(runtime / 'browser-fixture-readback.json', receipt)
    return {'instance': receipt['instance'], 'receipt': str((runtime / 'browser-fixture-readback.json').relative_to(root)),
            'created_objects': len(created), 'main_versions': receipt['main_versions'],
            'pending_versions': receipt['pending_versions'], 'routes': receipt['routes'], 'notice': NOTICE}


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--workspace', type=Path, default=ROOT)
    parser.add_argument('--system', type=Path, default=Path('.runtime/ui-unification/system'))
    parser.add_argument('--instance', type=Path, default=Path('.runtime/ui-unification/browser-fixture'))
    args = parser.parse_args()
    try:
        root = generation_root(args.workspace)
        instance = destination(root, args.instance)
        result = build(root, args.system, instance)
    except (ValueError, OSError, subprocess.SubprocessError) as error:
        parser.exit(2, 'fixture refused/failed: ' + str(error) + '\n')
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
