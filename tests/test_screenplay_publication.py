import json
import shutil
import tempfile
import unittest
from pathlib import Path

from review_desk.bundle import export, restore
from review_desk.screenplay import import_screenplay
from review_desk.store import Conflict, Store
from scripts.publish_screenplay import publish
from review_desk.material_content_stream import members


def seed_basis(store, root, document, destination):
    # This test exercises screenplay publication, not a restore of every media
    # result in the growing production archive. Keep the exact real upstream
    # histories and their dependency closure; full production restore is tested
    # separately with bounded resources.
    path=root/'export/objects.json'
    objects={row['id']:row for row in members(path,'objects') if row['kind'] in {'SOURCE','STORY','GUIDANCE'}}
    revisions=[r for r in members(path,'revisions') if r['object_id'] in objects]
    by_revision={row['id']:row for row in revisions}
    dependencies=[d for d in members(path,'dependencies') if d['from_revision'] in by_revision]
    wanted={ref['object_id'] for ref in document['basis'].values()}
    while True:
        revision_ids={r['id'] for r in revisions if r['object_id'] in wanted}
        linked={by_revision[d['to_revision']]['object_id'] for d in dependencies if d['from_revision'] in revision_ids}
        if linked<=wanted:break
        wanted.update(linked)
    selected=[r for r in revisions if r['object_id'] in wanted]
    if any(objects[oid]['kind'] not in {'SOURCE','STORY','GUIDANCE'} for oid in wanted):
        raise AssertionError('screenplay basis unexpectedly depends on production media')
    with store.db:
        for oid in sorted(wanted):
            row=objects[oid];store.db.execute('INSERT INTO objects VALUES (?,?,?,?,?,?)',tuple(row[k] for k in ('id','kind','current_revision','version','created_at','updated_at')))
        for row in selected:store.db.execute('INSERT INTO revisions VALUES (?,?,?,?,?)',tuple(row[k] for k in ('id','object_id','version','payload','created_at')))
        for row in dependencies:
            if row['from_revision'] in revision_ids:store.db.execute('INSERT INTO dependencies VALUES (?,?,?)',tuple(row[k] for k in ('from_revision','to_revision','role')))
    asset_names=set()
    for source in json.loads((root/'export/materials.json').read_text()):
        if source['id'] not in wanted:continue
        store.put_source(source)
        asset_names.update(a['file'] for a in source.get('assets',[]))
        if (source.get('media') or {}).get('file'):asset_names.add(source['media']['file'])
    for row in selected:
        payload=json.loads(row['payload'])
        if objects[row['object_id']]['kind']=='SOURCE':
            asset_names.update(a['file'] for a in payload.get('assets',[]))
            if (payload.get('media') or {}).get('file'):asset_names.add(payload['media']['file'])
        else:asset_names.update(v['file'] for s in payload.get('sections',[]) for v in s.get('visuals',[]))
    (destination/'export/assets').mkdir()
    for name in asset_names:shutil.copyfile(root/'export/assets'/name,destination/'export/assets'/name)
    source=store.source(document['basis']['story']['object_id']);block=source['blocks'][0]
    store.create_comment({'id':'existing-basis-comment','source_id':source['id'],'body':'Existing review preserved in the publication fixture',
                          'anchor':{'block_id':block['id'],'end_block_id':block['id'],'start':0,'end':5,'quote':block['text'][:5]}})


class ScreenplayPublicationTest(unittest.TestCase):
    document_path = 'imports/screenplay-01.json'

    def setUp(self):
        root = Path(__file__).resolve().parents[1]
        self.temp = tempfile.TemporaryDirectory(prefix='screenplay-publish-test-')
        self.candidate = Path(self.temp.name) / 'candidate'
        self.target = Path(self.temp.name) / 'target'
        (self.candidate / 'imports').mkdir(parents=True)
        (self.candidate / 'export').mkdir()
        self.document = json.loads((root / self.document_path).read_text())
        ids = [self.document['id']] + [e['id'] for e in self.document['episodes']]
        (self.candidate / self.document_path).write_text(json.dumps(self.document, ensure_ascii=False))
        prepared = Store(self.candidate / '.runtime/review.sqlite3')
        try:
            seed_basis(prepared,root,self.document,self.candidate)
            # A not-yet-published edition cannot already have review comments.
            # Remove only those comments from this disposable candidate; keep
            # every other edition's comments for the preservation assertions.
            with prepared.db:
                for object_id in ids:
                    prepared.db.execute(
                        'DELETE FROM comment_events WHERE comment_id IN '
                        '(SELECT id FROM comments WHERE target_object_id=?)',
                        (object_id,))
                    prepared.db.execute(
                        'DELETE FROM comments WHERE target_object_id=?', (object_id,))
            import_screenplay(prepared, self.document)
            export(prepared, self.candidate / 'export')
        finally:
            prepared.close()
        self.target.mkdir()
        out = self.target / 'export'; out.mkdir()
        shutil.copytree(self.candidate / 'export/assets', out / 'assets')
        self.store = Store(self.target / '.runtime/review.sqlite3')
        restore(self.store, self.candidate / 'export')
        # Only this disposable restored fixture is reduced to the prepublication state.
        with self.store.db:
            for id in ids:
                self.store.db.execute('DELETE FROM dependencies WHERE from_revision IN (SELECT id FROM revisions WHERE object_id=?)', (id,))
                self.store.db.execute('DELETE FROM revisions WHERE object_id=?', (id,))
                self.store.db.execute('DELETE FROM objects WHERE id=?', (id,))

    def tearDown(self):
        self.store.close(); self.temp.cleanup()

    def dump(self):
        return '\n'.join(self.store.db.iterdump())

    def publish(self, apply=False):
        return publish(self.candidate, self.target, apply, self.document_path)

    def test_dry_run_append_idempotence_and_exact_export(self):
        before = self.dump()
        self.assertTrue(self.publish()['dry_run'])
        self.assertEqual(before, self.dump())
        result = self.publish(True)
        self.assertEqual(result['objects'], 1 + len(self.document['episodes']))
        self.assertFalse(result['already_present'])
        self.assertTrue(self.publish(True)['already_present'])
        export(self.store, self.target / 'export')
        files = list(json.loads((self.candidate / 'export/manifest.json').read_text())['files']) + ['manifest.json']
        self.assertTrue(all((self.target / 'export' / f).read_bytes() == (self.candidate / 'export' / f).read_bytes() for f in files))

    def test_new_formal_comment_is_preserved(self):
        source = self.store.source('refinement-09-lantern-home-v9')
        block = source['blocks'][0]
        self.store.create_comment({'id':'publication-preservation-test', 'source_id':source['id'],
                                  'body':'Disposable preservation test',
                                  'anchor':{'block_id':block['id'],'end_block_id':block['id'],
                                            'start':0,'end':5,'quote':block['text'][:5]}})
        comments, events = self.store.comments(), self.store.events()
        self.publish(True)
        self.assertEqual(comments, self.store.comments())
        self.assertEqual(events, self.store.events())

    def test_newer_story_stops_before_write(self):
        source = self.store.source('refinement-09-lantern-home-v9')
        self.store.put_source({**source, 'id':'newer-published-story', 'order':source.get('order', 0) + 1})
        before = self.dump()
        with self.assertRaises(ValueError):
            self.publish(True)
        self.assertEqual(before, self.dump())

    def test_collision_never_overwrites_or_partially_appends(self):
        self.store.put_object(self.document['episodes'][1]['id'], 'NOTE', {'body':'Existing unrelated content'})
        before = self.dump()
        with self.assertRaises(Conflict):
            self.publish(True)
        self.assertEqual(before, self.dump())


class SecondScreenplayPublicationTest(ScreenplayPublicationTest):
    document_path = 'imports/screenplay-02.json'


if __name__ == '__main__':
    unittest.main()
