"""Enumerate every canonical material and ordered input, without semantic verdicts.

Run with the task's desk on PYTHONPATH. The output is evidence for an author to
read and judge; structural success never means the references are appropriate.
"""
import argparse
import json
from collections import Counter
from pathlib import Path


def inventory(instance):
    from review_desk.store import Store
    from review_desk import production as p
    from review_desk.ui_projection import material_entries
    from review_desk.material_categories import CATEGORIES
    from review_desk.material_reference import code
    from review_desk.material_storage import canonical_id
    from review_desk.material_relations import active_inputs, rules, cycle_issues
    from review_desk.shot_references import slots
    from review_desk import business_relations, production_current

    store = Store(instance / '.runtime/review.sqlite3')
    try:
        with p.read_scope(store):
            entries = material_entries(store, uses=False, identities=False)
            materials, consumers = [], {}
            owners = {}
            for raw in store.db.execute('''SELECT c.asset_object_id,t.material_id
                FROM production_candidates c JOIN production_candidate_targets t ON t.candidate_id=c.id'''):
                owners.setdefault(raw['asset_object_id'], []).append(canonical_id(store, raw['material_id']))
            relations, relation_ids = [], {}
            for row in business_relations.current(store):
                value = row['payload']
                if value.get('status') == 'withdrawn':
                    continue
                endpoints = [p.record(store, oid) for oid in value['endpoints']]
                if not any(e['kind'] in ('REQUIREMENT', 'ASSET') for e in endpoints):
                    continue
                relations.append({'object_id': row['object_id'], 'revision_id': row['id'],
                    'payload': value, 'endpoints': [{'object_id': e['object_id'], 'kind': e['kind'],
                        'title': e['payload']['title']} for e in endpoints], 'semantic_review': None})
                for endpoint in endpoints:
                    if endpoint['kind'] in ('REQUIREMENT', 'ASSET'):
                        mids = owners.get(endpoint['object_id'], [canonical_id(store, endpoint['object_id'])])
                        for mid in mids:
                            relation_ids.setdefault(mid, []).append(row['object_id'])
            for entry in sorted(entries, key=lambda e: code(store, e['canonical_material_id']) or ''):
                row = p.record(store, entry['object_id'])
                payload = row['payload']
                plan = payload.get('generation')
                active, route_issues = active_inputs(store, plan or {}, row['object_id'])
                active_indices = {i for i, _ in active}
                ordered = []
                for slot in slots(store, (plan or {}).get('inputs', [])):
                    value = slot['value']
                    target = slot.get('record')
                    target_mid = slot.get('canonical_material_id')
                    if target_mid:
                        consumers.setdefault(target_mid, []).append({'material_id': entry['canonical_material_id'],
                            'index': slot['index'], 'active': slot['index'] in active_indices,
                            'layer': 'current-plan', 'kind': 'demand' if target and target['kind']=='REQUIREMENT' else 'exact-original'})
                    ordered.append({**{k: v for k, v in slot.items() if k not in ('record', 'candidate')},
                        'active': slot['index'] in active_indices,
                        'rule': rules(store, value, row['object_id']),
                        'target_kind': target['kind'] if target else None,
                        'target_scope': target['payload'].get('scope') if target else None,
                        'target_purpose': target['payload'].get('purpose') if target else None,
                        'target_status': target['payload'].get('status') if target else None,
                        'semantic_review': None})
                materials.append({'material_id': entry['canonical_material_id'], 'object_id': row['object_id'],
                    'code': code(store, entry['canonical_material_id']), 'revision_id': row['id'],
                    'content_sha256': row.get('content_sha256'), 'category': payload.get('material_category'),
                    'title': payload['title'], 'scope': payload.get('scope'), 'states': payload.get('states', []),
                    'purpose': payload.get('purpose'), 'specification': payload.get('specification'),
                    'scope_content': p.ref_record(store, payload['scope'])['payload'] if payload.get('scope') else None,
                    'sources': payload.get('sources', []), 'generation': plan,
                    'slots': ordered, 'route_issues': route_issues,
                    'cycle_issues': cycle_issues(store, row) if plan else [], 'semantic_review': None})
            for item in materials:
                item['consumers'] = consumers.get(item['material_id'], [])
                item['business_relations'] = relation_ids.get(item['material_id'], [])
                item['candidates'] = [dict(r) for r in store.db.execute('''SELECT c.id,c.asset_object_id,t.number,
                    c.operation_id FROM production_candidate_targets t JOIN production_candidates c ON c.id=t.candidate_id
                    WHERE t.material_id=? ORDER BY t.number''', (item['material_id'],))]
            candidates = []
            actual_consumers = {}
            for raw in store.db.execute('SELECT * FROM production_candidates ORDER BY id'):
                saved = production_current.submission(store, raw['operation_id'])
                targets = [dict(t) for t in store.db.execute('SELECT material_id,number FROM production_candidate_targets WHERE candidate_id=? ORDER BY material_id', (raw['id'],))]
                snapshot = saved['snapshot']
                actual_slots = slots(store, snapshot.get('request', {}).get('inputs', []))
                for slot in actual_slots:
                    source = slot['value'].get('reference', slot['value'])
                    mids = owners.get(source.get('object_id'), [slot.get('canonical_material_id')])
                    for mid in mids:
                        if mid:
                            actual_consumers.setdefault(mid, []).append({'layer': 'submitted-candidate',
                                'candidate_id': raw['id'], 'operation_id': raw['operation_id'],
                                'targets': targets, 'index': slot['index'], 'value': slot['value']})
                candidates.append({**dict(raw), 'targets': targets, 'submission_sha256': saved['snapshot_sha256'],
                    'origin': saved['origin'], 'request': snapshot.get('request', {}),
                    'input_contents': snapshot.get('input_contents', []), 'gaps': snapshot.get('gaps', []),
                    'slots': [{k:v for k,v in slot.items() if k not in ('record','candidate')}
                        for slot in actual_slots],
                    'semantic_review': None})
            for item in materials:
                item['actual_consumers'] = actual_consumers.get(item['material_id'], [])
                item['business_relations'] = sorted(set(item['business_relations']))
            counts = Counter(item['category'] for item in materials)
            summary = {'materials': len(materials), 'categories': {k: counts[k] for k in CATEGORIES},
                'with_plan': sum(item['generation'] is not None for item in materials),
                'without_plan': sum(item['generation'] is None for item in materials),
                'zero_inputs': sum(not item['slots'] for item in materials),
                'input_slots': sum(len(item['slots']) for item in materials),
                'input_kinds': dict(Counter(slot['target_kind'] for item in materials for slot in item['slots'])),
                'preparation_slots': sum(slot['issues']==['尚未选定候选'] for item in materials for slot in item['slots']),
                'invalid_slots': sum(bool([i for i in slot['issues'] if i!='尚未选定候选']) for item in materials for slot in item['slots']),
                'business_relations': len(relations), 'candidates': len(candidates),
                'materials_with_cycles': sum(bool(item['cycle_issues']) for item in materials)}
            return {'format': 'material-reference-inventory-v2', 'summary': summary, 'materials': materials,
                    'business_relations': relations, 'candidates': candidates}
    finally:
        store.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--instance', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = inventory(args.instance.resolve())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(result['summary'], ensure_ascii=False))


if __name__ == '__main__':
    main()
