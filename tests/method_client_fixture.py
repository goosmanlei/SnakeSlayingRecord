"""In-process transport fixture; ledger contract is tested in the desk suite."""
import copy
from scripts import reader_review as reader


class Client:
    def __init__(self, *args):
        self.executions = {}
        self.results = {}

    def resolve(self, work_type, conditions=None):
        mode = (conditions or {}).get('mode', 'full')
        body = {'full': reader.INSTRUCTIONS, 'summary-reader': reader.SUMMARY_READER_INSTRUCTIONS,
                'summary': reader.SUMMARY_INSTRUCTIONS, 'recall-reader': reader.RECALL_READER_INSTRUCTIONS,
                'grounding': reader.GROUNDING_INSTRUCTIONS}[mode]
        package = {'binding': {'object_id': 'method.binding.' + work_type, 'revision_id': 'binding-v1'},
                   'method': {'object_id': 'method.skill.' + work_type, 'revision_id': 'method-v1'},
                   'version': 1, 'title': work_type, 'work_type': work_type, 'conditions': conditions or {},
                   'files': {'SKILL.md': body}, 'resources': [], 'required_inputs': ['context'],
                   'steps': ['draft', 'review', 'result'] if work_type == 'novel-writing' else ['result']}
        package['sha256'] = reader.digest(package)
        return package

    def prepare(self, request):
        key = tuple(request[k] for k in ('work_type', 'run_id', 'step_id', 'target'))
        if key in self.executions:
            old = self.executions[key]
            if old['payload']['inputs'] != request['inputs']:
                raise ValueError('fixture input conflict')
            return copy.deepcopy(old)
        record = {'object_id': 'execution-' + reader.digest(key), 'revision_id': reader.digest(request),
                  'payload': {**copy.deepcopy(request), 'package': self.resolve(request['work_type'], request.get('conditions'))}}
        self.executions[key] = record
        return copy.deepcopy(record)

    def artifact(self, execution, request, stage, output):
        if self.prepare(request) != execution:
            raise ValueError('wrong execution')
        key = (execution['revision_id'], stage)
        if key in self.results and self.results[key] != output:
            raise ValueError('immutable result')
        self.results[key] = copy.deepcopy(output)
        return {'stage': stage, 'output': output}
