"""Fixed aliases, concurrent candidates and interrupted-build recovery."""
import argparse
import contextlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parents[1] / 'scripts'))
import autonomous_optimization_release as r
import material_review_release as material
import normalize_review_images as normalize


class StableImages(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.old, self.new, self.digest = ['sha256:' + c * 64 for c in 'abc']
        self.m = {'image_policy': r.IMAGE_POLICY, 'base_image_tag': r.IMAGE_BASE,
                  'build_base_image': self.old, 'previous_app': {'image': self.old},
                  'story_main': str(self.root), 'source_hashes': {'review_desk/a.py': 'hash'}}

    def test_prepare_reads_fixed_base_without_moving_any_tag(self):
        with patch.object(r, 'image_tag_target', return_value=self.old), \
             patch.object(r, 'inspect', return_value={'Id': self.old}), patch.object(r, 'run') as run:
            self.assertEqual(r.stable_image_policy(self.new)['build_base_image'], self.old)
            run.assert_not_called()

    def test_changed_base_stops_before_build_or_tag_overwrite(self):
        with patch.object(r, 'inspect', return_value={'Id': self.old}), \
             patch.object(r, 'image_tag_target', return_value=self.new), patch.object(r, 'run') as run:
            with self.assertRaisesRegex(ValueError, 'base changed'):
                r.build_stable_image(self.root, self.m)
            run.assert_not_called()

    def test_incompatible_base_is_rejected_during_prepare(self):
        with patch.object(r, 'image_tag_target', return_value=self.old), \
             patch.object(r, 'inspect', side_effect=[{'Id': self.old, 'Config': {'Cmd': ['wrong']}},
                                                    {'Id': self.new, 'Config': {'Cmd': ['review']}}]), \
             patch.object(r, 'run') as run:
            with self.assertRaisesRegex(ValueError, 'process configuration'):
                r.stable_image_policy(self.new)
            run.assert_not_called()

    def test_symlinked_build_id_stops_before_docker(self):
        (self.root / 'build-image-id').symlink_to(self.root / 'foreign-id')
        with patch.object(r, 'pin_stable_base') as pin:
            with self.assertRaisesRegex(ValueError, 'symlink'):
                r.build_stable_image(self.root, self.m)
            pin.assert_not_called()

    def test_candidates_have_independent_ids_and_no_tag_arguments(self):
        commands = []
        def build(command):
            commands.append(command)
            Path(command[command.index('--iidfile') + 1]).write_text(self.digest)
        def inspect(name, image=False):
            return {'Id': self.old if name == r.IMAGE_BASE else self.new}
        with patch.object(r, 'pin_stable_base'), patch.object(r, 'inspect', side_effect=inspect), \
             patch.object(r, 'run', side_effect=build), patch.object(r, 'source_check') as check:
            for name in ('candidate-one', 'candidate-two'):
                root = self.root / name; root.mkdir()
                self.assertEqual(r.build_stable_image(root, self.m), self.new)
        self.assertEqual(len(commands), 2)
        self.assertNotEqual(commands[0][-2], commands[1][-2])
        for command in commands:
            self.assertNotIn('-t', command); self.assertNotIn('--tag', command)
        self.assertEqual(check.call_count, 2)

    def test_completed_build_is_reverified_without_rebuilding(self):
        (self.root / 'build-image-id').write_text(self.digest)
        def inspect(name, image=False):
            return {'Id': self.old if name == r.IMAGE_BASE else self.new}
        with patch.object(r, 'pin_stable_base'), patch.object(r, 'inspect', side_effect=inspect), \
             patch.object(r, 'run') as run, patch.object(r, 'source_check') as check:
            self.assertEqual(r.build_stable_image(self.root, self.m), self.new)
            run.assert_not_called(); check.assert_called_once_with(self.new, self.m['source_hashes'])

    def test_service_drift_never_moves_current_or_previous(self):
        with patch.object(r, 'inspect', return_value={'Image': self.old}), patch.object(r, 'run') as run:
            with self.assertRaisesRegex(ValueError, 'active service'):
                r.update_image_aliases(self.m, {'image': self.new})
            run.assert_not_called()

    def test_publication_and_rollback_move_aliases_after_verification(self):
        aliases = {}
        active = self.new
        def inspect(name, image=False):
            if not image:
                return {'Image': active, 'State': {'Running': True, 'Health': {'Status': 'healthy'}}}
            return {'Id': aliases.get(name, name)}
        def run(command):
            self.assertEqual(command[:2], [r.DOCKER, 'tag'])
            aliases[command[3]] = command[2]
        with patch.object(r, 'inspect', side_effect=inspect), patch.object(r, 'run', side_effect=run):
            r.update_image_aliases(self.m, {'image': self.new})
            self.assertEqual(aliases, {r.IMAGE_CURRENT: self.new, r.IMAGE_PREVIOUS: self.old})
            active = self.old
            r.update_image_aliases(self.m, {'image': self.new}, recovered=True)
            self.assertEqual(aliases, {r.IMAGE_CURRENT: self.old, r.IMAGE_PREVIOUS: self.new})

    def test_legacy_bundle_does_not_move_aliases(self):
        with patch.object(r, 'inspect') as inspect:
            self.assertEqual(r.update_image_aliases({}, {}), {})
            inspect.assert_not_called()

    def test_material_receipt_freezes_id_without_claiming_tag_was_published(self):
        (self.root / 'manifest.json').write_text('{}')
        with patch.object(material, 'load_bundle', return_value=(self.root, self.m)), \
             patch.object(r, 'build_stable_image', return_value=self.new), contextlib.redirect_stdout(io.StringIO()):
            material.build(argparse.Namespace(bundle=self.root))
        receipt = json.loads((self.root / 'image.json').read_text())
        self.assertEqual(receipt['image'], self.new)
        self.assertEqual(receipt['publish_tag'], r.IMAGE_CURRENT)
        self.assertNotIn('tag', receipt)

    def test_normalization_removes_only_tags_with_a_verified_fixed_alias(self):
        legacy = 'story-review-desk:materials-' + 'd' * 12 + '-' + 'e' * 12
        aliases = {r.IMAGE_BASE: self.old, r.IMAGE_PREVIOUS: self.old, r.IMAGE_CURRENT: self.new}
        result = {'container': 'container', 'aliases': aliases,
                  'remove_tags': [{'tag': legacy, 'image': self.old}], 'images_deleted': 0}
        tags = {legacy: self.old}
        commands = []
        def run(command):
            commands.append(command)
            if command[1] == 'tag': tags[command[3]] = command[2]
            elif command[1:3] == ['image', 'rm']: del tags[command[3]]
            else: self.fail('unexpected mutation')
        def inspect(name, image=False):
            if not image:
                return {'Id': 'container', 'Image': self.new, 'State': {'Health': {'Status': 'healthy'}}}
            image_id = tags.get(name, name)
            return {'Id': image_id, 'RepoTags': [t for t, i in tags.items() if i == image_id]}
        with patch.object(r, 'publication_locks', return_value=contextlib.nullcontext()), \
             patch.object(normalize, 'plan', return_value=result), \
             patch.object(r, 'image_tag_target', side_effect=lambda t: tags.get(t)), \
             patch.object(r, 'inspect', side_effect=inspect), patch.object(r, 'run', side_effect=run):
            normalized = normalize.normalize(self.root, apply=True)
        self.assertEqual(normalized['removed_tags'], [legacy])
        self.assertEqual(commands[-1], [r.DOCKER, 'image', 'rm', legacy])
        self.assertEqual(normalized['images_deleted'], 0)


if __name__ == '__main__': unittest.main()
