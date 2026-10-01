"""Story-side authoring and exact replay helpers, using review-desk operations."""
import copy
import json


def refresh_drafts(store, production, document, apply=False):
    """Prepare in a DB copy, then commit only changed drafts with optimistic versions.

    Accepted screenplay input is checked by the calling story compiler. This
    helper does not select assets, create reviews, or change user acceptance.
    """
    from review_desk.store import Store
    clone = Store(':memory:')
    store.db.backup(clone.db)
    clone.db_path = store.db_path  # File inspection uses the actual instance originals.
    changes, resolved = [], {}
    try:
        for source in document['records']:
            payload = copy.deepcopy(source['payload'])
            for _, ref in production.references(payload):
                if ref['revision_id'].startswith('@'):
                    alias = ref['revision_id'][1:]
                    if alias != ref['object_id'] or alias not in resolved:
                        raise ValueError('draft reference must name an earlier draft')
                    ref['revision_id'] = resolved[alias]
            try:
                current = production.record(clone, source['object_id'])
            except KeyError:
                current = None
            if current and current['payload'] == payload:
                resolved[source['object_id']] = current['id']
                continue
            revision = {**source, 'payload': payload, 'expected_version': current['version'] if current else 0}
            batch = {'format': 'production-import-v1', 'records': [revision]}
            value = production.import_records(clone, batch)['records'][0]
            resolved[source['object_id']] = value['revision']
            changes.append(revision)
    finally:
        clone.close()
    batch = {'format': 'production-import-v1', 'records': changes}
    if changes:
        production.import_records(store, batch, validate_only=not apply)
    return batch


def exact_replay(store, production):
    """Keep real production revision history; do not include isolated comments."""
    revisions = {r['id']: r for r in store.revisions()
                 if json.loads(r['payload']).get('format') in production.FORMATS}
    object_kinds = {r['id']: r['kind'] for r in store.objects()}
    parents = {rid: set() for rid in revisions}
    for dep in store.dependencies():
        if dep['from_revision'] in parents and dep['to_revision'] in revisions:
            parents[dep['from_revision']].add(dep['to_revision'])
    per_object = {}
    for row in sorted(revisions.values(), key=lambda r: (r['object_id'], r['version'])):
        previous = per_object.get(row['object_id'])
        if previous:
            parents[row['id']].add(previous)
        per_object[row['object_id']] = row['id']
    # Review submission/acceptance checks the *whole current state collection*.
    # Ordinary dependency sorting can replay a later, unrelated new state first.
    # Preserve that temporal boundary even after a bundle reordered table rows.
    payloads = {rid: json.loads(row['payload']) for rid, row in revisions.items()}
    for rid, payload in payloads.items():
        target = payload
        if payload.get('format') == 'production-judgment-v1' and payload.get('verdict') == 'accepted':
            target = payloads.get(payload['target']['revision_id'], {})
        if target.get('review_model') != 'entity-review-v1':
            continue
        entity_ref = target['entities'][0]
        included = {r['object_id']: r['revision_id'] for r in [entity_ref, *target['states']]}
        for later_id, later in revisions.items():
            if later['object_id'] in included:
                if later['version'] > revisions[included[later['object_id']]]['version']:
                    parents[later_id].add(rid)
            elif (object_kinds[later['object_id']] == 'STATE' and payloads[later_id].get('state_model') == 'complete-v1' and
                  payloads[later_id]['entity']['object_id'] == entity_ref['object_id']):
                parents[later_id].add(rid)
        if payload.get('format') == 'production-judgment-v1':
            submission = revisions[payload['target']['revision_id']]
            for later_id, later in revisions.items():
                if later['object_id'] == submission['object_id'] and later['version'] > submission['version']:
                    parents[later_id].add(rid)
    batches, batch, batch_ids, done = [], [], set(), set()
    while len(done) < len(revisions):
        available = sorted((r for r in revisions.values() if r['id'] not in done and parents[r['id']] <= done),
                           key=lambda r: (r['created_at'], r['object_id'], r['version']))
        if not available:
            raise ValueError('production replay has a dependency cycle')
        for row in available:
            if row['object_id'] in batch_ids:
                batches.append({'format': 'production-import-v1', 'records': batch})
                batch, batch_ids = [], set()
            batch.append({'object_id': row['object_id'], 'kind': object_kinds[row['object_id']],
                          'expected_version': row['version'] - 1, 'payload': json.loads(row['payload'])})
            batch_ids.add(row['object_id'])
            done.add(row['id'])
    if batch:
        batches.append({'format': 'production-import-v1', 'records': batch})
    return {'format': 'production-replay-v1', 'batches': batches,
            'revisions': sorted(revisions), 'heads': per_object}
