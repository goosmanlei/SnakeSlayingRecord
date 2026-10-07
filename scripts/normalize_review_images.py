#!/usr/bin/env python3
"""Normalize local review image tags without rebuilding or deleting images."""
import argparse
import json
from pathlib import Path
import re
import autonomous_optimization_release as base


LEGACY = re.compile(r'(?:ao-task-\d{8}-\d{4}-base:[0-9a-f]{64}|'
                    r'story-review-desk:(?:materials|autonomous)-[0-9a-f]{12}-[0-9a-f]{12})')


def plan(story_main):
    story_main = story_main.resolve()
    app = base.inspect(base.APP)
    labels = app['Config']['Labels']
    base.require(labels.get('com.docker.compose.project.working_dir') == str(story_main), 'another formal instance')
    base.require(app['State']['Running'] and app['State'].get('Health', {}).get('Status') == 'healthy', 'formal app unhealthy')
    release_file = Path(labels['com.docker.compose.project.config_files'])
    releases = story_main / '.runtime/service-releases'
    base.require(release_file.name == 'compose.release.json' and
                 release_file.parent.parent == releases and not release_file.is_symlink(), 'unknown release path')
    root = release_file.parent
    base.require(root.resolve().parent == releases.resolve(), 'release path escapes service releases')
    m, receipt = base.read(root / 'manifest.json'), base.read(root / 'image.json')
    current = app['Image']
    base.require(receipt['image'] == current and
                 receipt['manifest_sha256'] == base.sha((root / 'manifest.json').read_bytes()), 'active release identity differs')
    base.require(base.read(release_file)['services']['app']['image'] == current, 'active compose image differs')
    previous = m['previous_app']['image']
    current_image = base.inspect(current, image=True)
    previous_image = base.inspect(previous, image=True)
    current_layers = current_image['RootFS']['Layers']
    ids = set(base.run([base.DOCKER, 'image', 'ls', '--no-trunc', '--format', '{{.ID}}']).decode().splitlines())
    images = [base.inspect(i, image=True) for i in sorted(ids)]
    fixed_base = base.image_tag_target(base.IMAGE_BASE)
    if fixed_base is None:
        # Bootstrap once from the oldest local ancestor owned by these releases.
        candidates = [i for i in images if any(LEGACY.fullmatch(t) for t in i.get('RepoTags') or [])
                      and current_layers[:len(i['RootFS']['Layers'])] == i['RootFS']['Layers']]
        fixed_base = min(candidates, key=lambda i: len(i['RootFS']['Layers']))['Id'] if candidates else current
    runtime_base = base.inspect(fixed_base, image=True)
    for key in ('Cmd', 'Entrypoint', 'WorkingDir', 'User'):
        base.require((runtime_base['Config'].get(key) or '') == (current_image['Config'].get(key) or ''), 'base process configuration differs')
    keep = {current, previous, fixed_base}
    removals = [{'tag': tag, 'image': i['Id']} for i in images if i['Id'] in keep
                for tag in i.get('RepoTags') or [] if LEGACY.fullmatch(tag)]
    return {'story_main': str(story_main), 'container': app['Id'], 'release': str(root),
            'aliases': {base.IMAGE_BASE: fixed_base, base.IMAGE_PREVIOUS: previous_image['Id'], base.IMAGE_CURRENT: current},
            'remove_tags': removals, 'images_deleted': 0, 'service_restarted': False}


def normalize(story_main, apply=False):
    # Same publication lock as formal releases, then the shared image-tag lock.
    with base.publication_locks({'story_main': str(story_main.resolve()),
                                 'system_main': str(story_main.resolve().parent / 'story-review-desk-python')}):
        with base.image_tag_lock(story_main):
            result = plan(story_main)
            if not apply:
                return result
            aliases = result['aliases']
            existing_base = base.image_tag_target(base.IMAGE_BASE)
            base.require(existing_base in (None, aliases[base.IMAGE_BASE]), 'base tag changed')
            for tag, image_id in aliases.items():
                base.run([base.DOCKER, 'tag', image_id, tag])
                base.require(base.inspect(tag, image=True)['Id'] == image_id, 'stable alias differs')
            removed = []
            for item in result['remove_tags']:
                image = base.inspect(item['tag'], image=True)
                base.require(image['Id'] == item['image'] and
                             any(t in (image.get('RepoTags') or []) and i == item['image'] for t, i in aliases.items()),
                             'old tag has no fixed alias; do not remove its image')
                base.run([base.DOCKER, 'image', 'rm', item['tag']])
                base.require(base.inspect(item['image'], image=True)['Id'] == item['image'], 'image no longer available')
                base.require(base.image_tag_target(item['tag']) is None, 'old tag still present')
                removed.append(item['tag'])
            app = base.inspect(base.APP)
            base.require(app['Id'] == result['container'] and app['Image'] == aliases[base.IMAGE_CURRENT] and
                         app['State'].get('Health', {}).get('Status') == 'healthy', 'formal service changed')
            return {**result, 'removed_tags': removed}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--story-main', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    print(json.dumps(normalize(args.story_main, args.apply), ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
