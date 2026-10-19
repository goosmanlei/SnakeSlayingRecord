"""Explicit, frozen runtime upgrade for the episode rendering worker.

Preparation/build never move the shared base alias. The normal release moves
it only after verifying the new service, together with current/previous.
"""
import json
import re
import autonomous_optimization_release as base


PROBE = r'''
import hashlib,json,subprocess,tempfile
from pathlib import Path
def run(args):return subprocess.check_output(args,stderr=subprocess.PIPE)
ffmpeg=run(['ffmpeg','-version']).decode().splitlines()[0]
ffprobe=run(['ffprobe','-version']).decode().splitlines()[0]
font=Path('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')
assert font.is_file()
with tempfile.TemporaryDirectory() as folder:
 p=Path(folder)/'probe.ass'
 p.write_text('[Script Info]\nScriptType: v4.00+\nPlayResX: 320\nPlayResY: 180\n'
 '[V4+ Styles]\nFormat: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding\n'
 'Style: Default,Noto Sans CJK SC,28,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,1,0,2,10,10,10,1\n'
 '[Events]\nFormat: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text\n'
 'Dialogue: 0,0:00:00.00,0:00:00.08,Default,,0,0,0,,两份米\n')
 raw=run(['ffmpeg','-v','error','-f','lavfi','-i','color=black:s=320x180:r=24:d=0.125',
  '-vf','subtitles='+str(p),'-pix_fmt','gray','-frames:v','3','-f','rawvideo','-'])
 size=320*180;ink=[sum(v>80 for v in raw[i*size:(i+1)*size]) for i in range(3)]
 assert len(raw)==size*3 and ink[0]>100 and ink[1]>100 and ink[2]==0,ink
print(json.dumps({'ffmpeg':ffmpeg,'ffprobe':ffprobe,'font_sha256':hashlib.sha256(font.read_bytes()).hexdigest(),'chinese_subtitle_ink':ink,'frames':3}))
'''


def probe(image):
    config = base.inspect(image, image=True)['Config']
    base.require(config.get('Entrypoint') == ['tini', '-g', '--'] and
                 config.get('Cmd') == ['python', '-m', 'review_desk', '--instance', '/instance',
                                       'serve', '--render-worker', '--host', '0.0.0.0', '--port', '8765']
                 and config.get('WorkingDir') == '/app', 'render runtime process differs')
    return json.loads(base.run([base.DOCKER, 'run', '--rm', '--network', 'none', '--cpus', '2',
                                '--memory', '1g', '--entrypoint', 'python', image, '-c', PROBE]))


def prepare(previous_image, tag, dockerfile_sha256):
    base.require(isinstance(dockerfile_sha256, str) and re.fullmatch(r'[0-9a-f]{64}', dockerfile_sha256),
                 'render runtime needs the reviewed Dockerfile hash')
    base.require(isinstance(tag, str) and re.fullmatch(r'story-review-desk:[a-zA-Z0-9_.-]+', tag)
                 and tag not in (base.IMAGE_BASE, base.IMAGE_CURRENT, base.IMAGE_PREVIOUS),
                 'render runtime needs an explicit local candidate tag')
    policy = base.stable_image_policy(previous_image)
    image = base.inspect(tag, image=True)['Id']
    base.require(re.fullmatch(r'sha256:[0-9a-f]{64}', image), 'render runtime needs exact image ID')
    policy['runtime_upgrade'] = {'tag': tag, 'image': image,
                                 'previous_base': policy['build_base_image'],
                                 'dockerfile_sha256': dockerfile_sha256, 'probe': probe(image)}
    policy['build_base_image'] = image
    return policy


def check_build_base(manifest):
    upgrade = manifest['runtime_upgrade']
    base.require(base.image_tag_target(base.IMAGE_BASE) in (None, upgrade['previous_base']),
                 'runtime base changed before upgrade build')
    base.require(base.inspect(upgrade['tag'], image=True)['Id'] == upgrade['image'] ==
                 manifest['build_base_image'], 'render runtime candidate tag changed')


def alias_target(manifest, recovered):
    upgrade = manifest['runtime_upgrade']
    current = base.image_tag_target(base.IMAGE_BASE)
    base.require(current in (None, upgrade['previous_base'], upgrade['image']),
                 'runtime base changed before verified publication')
    return upgrade['previous_base'] if recovered else upgrade['image']
