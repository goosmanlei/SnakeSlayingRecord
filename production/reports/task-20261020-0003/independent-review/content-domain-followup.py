"""Independent comment/content cache probe; run from desk with PYTHONPATH=.:tests.

Only fixture-owned temporary SQLite/files and a private loopback server are used.
"""
import copy
from contextlib import contextmanager
import http.client
import json
from pathlib import Path
import sys
import threading
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path.cwd()))
sys.path.insert(0, str(Path.cwd() / 'tests'))
import test_production_current as fixtures
from audiovisual_fixture import composition
from review_desk import business_relations, entity_contract, production as p
from review_desk import production_current as current, read_cache
from review_desk.review_text import production_text_blocks
from review_desk.server import ReviewHandler, ReviewServer
from review_desk.store import Conflict


RESULTS = {}


class ContentDomainFollowup(unittest.TestCase):
    def setUp(self):
        self.f = fixtures.CurrentProductionTest('test_response_excerpt_survives_later_edit')
        self.f.setUp()
        self.f.setup_plans()
        composition(self.f)
        need = self.f.need('wet')
        need['object_id'] = 'shot-sound'
        need['payload'].update(scope=self.f.ref('shot'), title='镜头声音', usage='editorial', specification={})
        need['payload']['generation'] = copy.deepcopy(p.record(self.f.store, 'need-full-overall')['payload']['generation'])
        need['payload']['generation']['output']['name'] = '镜头声音'
        self.f.put(need)
        ends = sorted(['shot', 'songbook'])
        self.relation_id = business_relations.identity(ends)
        self.f.put(self.f.spec(self.relation_id, 'RELATION', relation_type='business',
            endpoints=ends, direction='forward', summary='镜头中的歌本', sources=[], contexts=[]))
        self.store = self.f.store
        self.assertTrue(current.enabled(self.store))
        read_cache.attach(self.store)

    def tearDown(self):
        self.f.tearDown()

    @contextmanager
    def server(self):
        server = ReviewServer(('127.0.0.1', 0), self.f.root, {'title': 'Private content-domain followup'})
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        client = http.client.HTTPConnection(*server.server_address, timeout=5)
        try:
            def get(path):
                client.request('GET', path)
                response = client.getresponse()
                value = json.loads(response.read())
                self.assertEqual(response.status, 200, (path, value))
                return value, response.getheader('X-Review-Cache')
            yield get
        finally:
            client.close()
            server.shutdown()
            server.server_close()
            thread.join()

    def request(self, oid='shot-sound'):
        row = p.record(self.store, oid)
        if oid == 'shot-sound':
            block = next(b for b in production_text_blocks(row['payload']) if b.get('field') == 'generation.prompt')
            anchor = {'type': 'text', 'block_id': block['id'], 'end_block_id': block['id'],
                      'start': 0, 'end': 4, 'quote': block['text'][:4]}
        else:
            anchor = {'type': 'global'}
        return {'target_object_id': oid, 'target_revision_id': row['id'],
                'expected_edit_token': row['edit_token'], 'anchor': anchor, 'body': '私有复核意见'}

    def test_actual_production_comments_preserve_content_hits_and_refresh_comment_consumers(self):
        content_paths = (
            '/api/production/index?view=settings',
            '/api/production/materials',
            '/api/production/materials?scope=av&episode=av-episode&grouped=1&compact=1&cards=1',
            '/api/business-codes',
        )
        breakdown = '/api/production/breakdown?episode=av-episode'
        workspace = '/api/production/entity-review?entity_id=shot&view=workspace'
        with patch.object(ReviewHandler, 'log_message', lambda *a: None), \
             patch.object(entity_contract, '_entity_workspace', wraps=entity_contract._entity_workspace) as build, \
             patch.object(entity_contract, '_comment_targets', wraps=entity_contract._comment_targets) as targets, \
             self.server() as get:
            before = {}
            for path in (*content_paths, breakdown):
                before[path], _ = get(path)
                self.assertEqual(get(path)[1], 'hit', path)
            initial, _ = get(workspace)
            initial_refs = {(r['object_id'], r['revision_id']) for r in initial['comment_targets']}
            relation = p.record(self.store, self.relation_id)
            self.assertNotIn((relation['object_id'], relation['id']), initial_refs)
            self.assertEqual(build.call_count, 1)
            generation = dict(self.store.db.execute('SELECT name,token FROM read_generations'))
            content_token = read_cache.token(self.store, domain='content')
            all_token = read_cache.token(self.store)

            comment = self.store.create_comment(self.request())
            relation_comment = self.store.create_comment(self.request(self.relation_id))
            changed = {name for name, token in self.store.db.execute('SELECT name,token FROM read_generations')
                       if generation[name] != token}
            self.assertEqual(changed, {'comments', 'comment_events', 'business_comments', 'production_comment_quotes'})
            self.assertEqual(read_cache.token(self.store, domain='content'), content_token)
            self.assertNotEqual(read_cache.token(self.store), all_token)
            for table in ('business_comments', 'production_comment_quotes'):
                self.assertEqual(self.store.db.execute('SELECT count(*) FROM '+table).fetchone()[0], 2)
            headers = {}
            for path in content_paths:
                value, headers[path] = get(path)
                self.assertEqual(headers[path], 'hit', path)
                self.assertEqual(value, before[path], path)
            fresh, state = get(breakdown)
            self.assertEqual(state, 'miss')
            self.assertEqual({c['id'] for c in fresh['comment_index']}, {comment['id'], relation_comment['id']})
            episode_targets = {(r['object_id'], r['revision_id']) for r in fresh['episodes'][0]['comment_targets']}
            self.assertIn((comment['target_object_id'], comment['target_revision_id']), episode_targets)

            fresh_workspace, _ = get(workspace)
            self.assertEqual(build.call_count, 1)
            self.assertEqual(targets.call_count, 2)
            refs = {(r['object_id'], r['revision_id']) for r in fresh_workspace['comment_targets']}
            self.assertEqual(refs - initial_refs, {(relation['object_id'], relation['id'])})
            comments, _ = get('/api/comments?target_object_id=shot-sound')
            self.assertEqual(len(comments), 1)
            received = comments[0]
            self.assertEqual(received['id'], comment['id'])
            self.assertEqual(received['business_code'], 'C001')
            self.assertEqual(received['original_context']['original_revision_id'], comment['target_revision_id'])
            self.assertEqual(received['original_context']['excerpt']['anchor'], comment['anchor'])
            self.assertEqual(received['original_context']['content_sha256'], current.checksum(p.record(self.store, 'shot-sound')['payload']))
            self.assertTrue(received['original_context']['matches_current'])
            self.store.change_comment(comment['id'], 'CLOSE', 1)
            closed, closed_state = get(breakdown)
            self.assertEqual(closed_state, 'miss')
            self.assertEqual(next(c for c in closed['comment_index'] if c['id'] == comment['id'])['status'], 'CLOSED')
            self.assertEqual(get(content_paths[0])[1], 'hit')
            RESULTS['real_comment_creation'] = {'changed_tables': sorted(changed), 'http_content_routes': headers,
                'content_payloads_unchanged': True, 'breakdown_created_and_closed_fresh': True,
                'workspace_structure_builds': build.call_count, 'workspace_comment_target_reads': targets.call_count,
                'new_relation_target_added_after_cache_hit': True, 'comment_code': received['business_code'],
                'exact_quote_and_content_hash_preserved': True}

    def test_content_edit_keeps_old_comment_excerpt_and_rejects_stale_or_mismatched_target(self):
        request = self.request()
        comment = self.store.create_comment(request)
        before = read_cache.token(self.store, domain='content')
        row = p.record(self.store, 'shot-sound')
        value = copy.deepcopy(row['payload'])
        value['generation']['prompt'] = '另一段真实当前制作文字。'
        self.f.put({'object_id': row['object_id'], 'kind': row['kind'],
                    'expected_version': row['version'], 'payload': value})
        self.assertNotEqual(read_cache.token(self.store, domain='content'), before)
        after = self.store.comment(comment['id'])
        self.assertFalse(after['original_context']['matches_current'])
        self.assertEqual(after['original_context']['excerpt']['anchor'], request['anchor'])
        self.assertEqual(after['original_context']['content_sha256'], current.checksum(row['payload']))
        fresh = self.request()
        with self.assertRaises(Conflict):
            self.store.create_comment({**fresh, 'expected_edit_token': request['expected_edit_token']})
        with self.assertRaises(ValueError):
            self.store.create_comment({**fresh, 'target_revision_id': self.f.ref('shot')['revision_id']})
        self.assertEqual(len(self.store.comments()), 1)
        RESULTS['source_change_and_exactness'] = {'content_token_changed': True,
            'old_excerpt_retained': True, 'matches_current': False, 'stale_edit_rejected': True,
            'mismatched_revision_rejected': True, 'no_rejected_comment_inserted': True}


if __name__ == '__main__':
    run = unittest.main(exit=False)
    if run.result.wasSuccessful():
        Path(__file__).with_suffix('.json').write_text(json.dumps(RESULTS, ensure_ascii=False, indent=2)+'\n')
    raise SystemExit(0 if run.result.wasSuccessful() else 1)
