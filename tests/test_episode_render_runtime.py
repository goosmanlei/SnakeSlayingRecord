"""Runtime base changes require an explicit candidate and a verified service."""
import json
import contextlib
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parents[1] / 'scripts'))
import autonomous_optimization_release as base
import episode_render_runtime as runtime
import material_review_release as material


class RuntimeUpgrade(unittest.TestCase):
    def setUp(self):
        self.old, self.new, self.app, self.other = ['sha256:' + c * 64 for c in 'abcd']
        self.tag = 'story-review-desk:owned-render-test'
        self.m = {'image_policy': base.IMAGE_POLICY, 'base_image_tag': base.IMAGE_BASE,
                  'build_base_image': self.new, 'previous_app': {'image': self.old},
                  'source_hashes': {}, 'runtime_upgrade': {
                      'previous_base': self.old, 'image': self.new, 'tag': self.tag, 'probe': {'frames': 3}}}

    def test_prepare_freezes_probe_and_never_moves_shared_alias(self):
        policy = {'image_policy': base.IMAGE_POLICY, 'base_image_tag': base.IMAGE_BASE,
                  'build_base_image': self.old}
        with patch.object(base, 'stable_image_policy', return_value=policy), \
             patch.object(base, 'inspect', return_value={'Id': self.new}), \
             patch.object(runtime, 'probe', return_value={'frames': 3}), patch.object(base, 'run') as run:
            value = runtime.prepare(self.old, self.tag, 'a' * 64)
            self.assertEqual(value['runtime_upgrade']['previous_base'], self.old)
            self.assertEqual(value['build_base_image'], self.new)
            run.assert_not_called()
            for tag in (base.IMAGE_BASE, 'untrusted.example/image:tag'):
                with self.assertRaises(ValueError): runtime.prepare(self.old, tag, 'a' * 64)

    def test_base_or_candidate_drift_stops_build(self):
        with patch.object(base, 'image_tag_target', return_value=self.other), patch.object(base, 'inspect') as inspect:
            with self.assertRaisesRegex(ValueError, 'base changed'): runtime.check_build_base(self.m)
            inspect.assert_not_called()
        with patch.object(base, 'image_tag_target', return_value=self.old), \
             patch.object(base, 'inspect', return_value={'Id': self.other}):
            with self.assertRaisesRegex(ValueError, 'candidate tag changed'): runtime.check_build_base(self.m)

    def test_base_drift_stops_release_before_database_or_service_changes(self):
        with patch.object(material, 'authorized', return_value=(Path('/unused'), self.m)), \
             patch.object(base, 'publication_locks', return_value=contextlib.nullcontext()), \
             patch.object(base, 'image_tag_target', return_value=self.other), \
             patch.object(material, 'checks') as checks, patch.object(base, 'run') as run:
            with self.assertRaisesRegex(ValueError, 'base changed'): material.apply(None)
            checks.assert_not_called(); run.assert_not_called()

    def test_build_from_candidate_preserves_shared_base_and_checks_rendering(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); self.m['story_main'] = str(root)
            (root / 'build-image-id').write_text(self.app)
            with patch.object(base, 'image_tag_target', return_value=self.old), \
                 patch.object(base, 'inspect', side_effect=lambda name, image=False: {'Id': self.new if name == self.tag else name}), \
                 patch.object(base, 'run') as run, patch.object(base, 'source_check'), \
                 patch.object(runtime, 'probe', return_value={'frames': 3}):
                self.assertEqual(base.build_stable_image(root, self.m), self.app)
                run.assert_not_called()
            with patch.object(runtime, 'check_build_base'), patch.object(base, 'inspect', return_value={'Id': self.app}), \
                 patch.object(base, 'source_check'), patch.object(runtime, 'probe', return_value={'frames': 0}):
                with self.assertRaisesRegex(ValueError, 'rendering runtime differs'): base.build_stable_image(root, self.m)

    def test_only_healthy_exact_service_can_publish_base_and_drift_is_atomic(self):
        with tempfile.TemporaryDirectory() as folder:
            self.m['story_main'] = folder
            aliases = {base.IMAGE_BASE: self.old}; active = self.app
            def inspect(name, image=False):
                if not image:return {'Image': active, 'State': {'Running': True, 'Health': {'Status': 'healthy'}}}
                return {'Id': aliases.get(name, name)}
            def run(args):aliases[args[3]] = args[2]
            with patch.object(base, 'inspect', side_effect=inspect), patch.object(base, 'run', side_effect=run) as calls, \
                 patch.object(base, 'image_tag_target', side_effect=lambda tag: aliases.get(tag)):
                aliases[base.IMAGE_BASE] = self.other
                with self.assertRaisesRegex(ValueError, 'base changed'):base.update_image_aliases(self.m, {'image': self.app})
                calls.assert_not_called()
                aliases[base.IMAGE_BASE] = self.old
                base.update_image_aliases(self.m, {'image': self.app})
                self.assertEqual(aliases[base.IMAGE_BASE], self.new)
                self.assertEqual(aliases[base.IMAGE_CURRENT], self.app)
                active = self.old
                base.update_image_aliases(self.m, {'image': self.app}, recovered=True)
                self.assertEqual(aliases[base.IMAGE_BASE], self.old)


if __name__ == '__main__': unittest.main()
