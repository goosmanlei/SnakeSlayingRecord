import copy
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from register_generation_batch import validate_builtin_plan, validate_reference_authorization


class ReferenceGuardTests(unittest.TestCase):
    def setUp(self):
        self.asset = {'object_id': 'asset-river-03', 'revision_id': 'source-revision'}
        self.state = {'object_id': 'river-day', 'revision_id': 'state-revision'}
        self.entity = {'object_id': 'river', 'revision_id': 'entity-revision'}
        self.payload = {'media_type': 'image', 'states': [self.state], 'subjects': [self.entity],
                        'verification': {'self_review_status': 'changes_requested'}, 'lineage': {'i2i_depth': 0}}
        self.request = {'same_state_repair': {'source': self.asset, 'reason': 'Move the misplaced stall only'},
                        'lineage': {'i2i_depth': 1, 'references': [self.asset]}}

    def validate(self, request=None, state=None):
        def resolve(reference, kinds):
            self.assertEqual(reference, self.asset)
            self.assertEqual(kinds, {'ASSET'})
            return {'payload': self.payload}
        validate_reference_authorization(resolve, request or self.request, [self.asset], [state or self.state], self.entity, 'image')

    def test_unaccepted_candidate_can_only_repair_its_own_complete_state(self):
        self.validate()
        with self.assertRaisesRegex(AssertionError, 'cannot change'):
            self.validate(state={'object_id': 'river-night', 'revision_id': 'other-state'})

    def test_missing_approval_cannot_be_silently_treated_as_a_repair(self):
        request = copy.deepcopy(self.request); request.pop('same_state_repair')
        with self.assertRaisesRegex(AssertionError, 'approved master required'):
            self.validate(request)

    def test_same_state_repair_does_not_reset_lineage(self):
        self.payload['lineage']['i2i_depth'] = 2
        self.request['lineage']['i2i_depth'] = 3
        with self.assertRaises(AssertionError):
            self.validate()

    def test_later_user_feedback_can_repair_exact_candidate_without_rewriting_original_qa(self):
        self.payload['verification']['self_review_status'] = 'self_pass'
        feedback = {'object_id': 'user-feedback', 'revision_id': 'feedback-revision'}
        self.request['same_state_repair']['feedback'] = feedback
        decision = {'actor': 'user', 'verdict': 'changes_requested', 'target': self.asset}
        def resolve(reference, kinds):
            if kinds == {'JUDGMENT'}:
                self.assertEqual(reference, feedback)
                return {'payload': decision}
            return {'payload': self.payload}
        def check(state=None):
            validate_reference_authorization(resolve, self.request, [self.asset], [state or self.state], self.entity, 'image')
        check()
        with self.assertRaisesRegex(AssertionError, 'cannot change'):
            check({'object_id': 'different-state', 'revision_id': 'another'})
        decision['target'] = {'object_id': 'other', 'revision_id': 'wrong'}
        with self.assertRaisesRegex(AssertionError, 'another candidate'):
            check()
        self.assertEqual(self.payload['verification']['self_review_status'], 'self_pass')

    def test_user_approval_does_not_reset_or_extend_image_lineage(self):
        judgment = {'object_id': 'review-source', 'revision_id': 'review-revision'}
        self.payload['lineage']['i2i_depth'] = 2
        request = {'master_approval': judgment, 'lineage': {'i2i_depth': 1, 'references': [self.asset]}}
        def resolve(reference, kinds):
            if kinds == {'JUDGMENT'}:
                return {'payload': {'actor': 'user', 'verdict': 'accepted', 'target': self.asset}}
            return {'payload': self.payload}
        for depth in (1, 3):
            request['lineage']['i2i_depth'] = depth
            with self.assertRaisesRegex(AssertionError, 'two-generation limit'):
                validate_reference_authorization(resolve, request, [self.asset], [self.state], self.entity, 'image')


class MultipleMasterTests(unittest.TestCase):
    def setUp(self):
        self.refs = [{'object_id': 'asset-'+str(i), 'revision_id': 'rev-'+str(i)} for i in range(2)]
        self.decisions = [{'object_id': 'review-'+str(i), 'revision_id': 'accepted-'+str(i)} for i in range(2)]
        self.depths = [0, 1]
        self.request = {'master_approvals': self.decisions, 'lineage': {'i2i_depth': 2, 'references': self.refs}}

    def validate(self):
        def resolve(ref, kinds):
            if kinds == {'ASSET'}:
                return {'payload': {'lineage': {'i2i_depth': self.depths[self.refs.index(ref)]}}}
            i = self.decisions.index(ref)
            return {'payload': {'actor': 'user', 'verdict': 'accepted', 'target': self.refs[i]}}
        validate_reference_authorization(resolve, self.request, self.refs, [], {}, 'image')

    def test_each_submitted_reference_requires_its_own_exact_acceptance(self):
        self.validate()
        self.request['master_approvals'] = self.decisions[:1]
        with self.assertRaisesRegex(AssertionError, 'one ordered approval'):
            self.validate()

    def test_reordered_or_borrowed_acceptance_cannot_authorize_inputs(self):
        for approvals in [list(reversed(self.decisions)), [self.decisions[0]] * 2]:
            self.request['master_approvals'] = approvals
            with self.assertRaisesRegex(AssertionError, 'ordered reference'):
                self.validate()

    def test_mixed_singular_and_plural_acceptance_is_rejected(self):
        self.request['master_approval'] = self.decisions[0]
        with self.assertRaisesRegex(AssertionError, 'one ordered approval'):
            self.validate()

    def test_clean_master_does_not_reset_deepest_reference(self):
        self.depths[1] = 2
        for claimed in (1, 2, 3):
            self.request['lineage']['i2i_depth'] = claimed
            with self.assertRaisesRegex(AssertionError, 'two-generation limit'):
                self.validate()


class BuiltinPlanTests(unittest.TestCase):
    def setUp(self):
        self.plan = {'method': 'generate', 'model': 'GPT Image', 'prompt': 'Only the exact character',
                     'parameters': {'transparent_background': False}, 'blockers': []}
        self.request = {'model': 'GPT Image', 'request': {'prompt': self.plan['prompt'], 'transparent_background': False}}

    def test_call_must_match_immutable_plan_text_and_actual_parameters(self):
        validate_builtin_plan(self.plan, self.request)
        self.request['request']['prompt'] += ' and a second person'
        with self.assertRaisesRegex(AssertionError, 'submitted prompt differs'):
            validate_builtin_plan(self.plan, self.request)
        self.request['request']['prompt'] = self.plan['prompt']
        self.request['request']['transparent_background'] = True
        with self.assertRaisesRegex(AssertionError, 'submitted parameters differ'):
            validate_builtin_plan(self.plan, self.request)

    def test_unexposed_size_and_unbound_required_inputs_cannot_be_registered(self):
        self.request['request']['size'] = '4K'
        with self.assertRaisesRegex(AssertionError, 'unsupported built-in parameter'):
            validate_builtin_plan(self.plan, self.request)
        self.request['request'].pop('size')
        self.plan['blockers'] = ['child master approval required']
        with self.assertRaisesRegex(AssertionError, 'not executable'):
            validate_builtin_plan(self.plan, self.request)

    def test_reference_limit_is_checked_before_a_new_call(self):
        for count in (5, 6):
            paths = [f'/managed/original-{i}.png' for i in range(count)]
            self.request['request']['referenced_image_paths'] = paths
            self.plan['parameters']['referenced_image_paths'] = paths
            if count == 5:
                validate_builtin_plan(self.plan, self.request)
            else:
                with self.assertRaisesRegex(AssertionError, 'at most 5'):
                    validate_builtin_plan(self.plan, self.request)


if __name__ == '__main__': unittest.main()
