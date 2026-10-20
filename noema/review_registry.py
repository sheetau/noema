"""Compact registrations referencing immutable, fully validated judgments.

Rebinding never creates a semantic judgment. It checks the original complete
review, current source, statements, transitive meanings and designation forms.
"""
from copy import deepcopy
from pathlib import Path

from . import identifiers, meaning_catalog, semantic_reviews as legacy

SCHEMA = 'noema-semantic-review-index-2'


def merge_pins(target, incoming):
    for name, value in incoming.items():
        legacy.require(name not in target or target[name] == value, 'Conflicting review provenance: ' + name)
        target[name] = value


def selected_identifiers(root, basis, annotations, symbols, loaded=None):
    if annotations is None:
        return {}
    if loaded is None:
        loaded = {}
    key = (basis, annotations)
    if key not in loaded:
        loaded[key] = identifiers.load_annotations(root, basis, annotations).show()['entries']
    values = loaded[key]
    return {row['symbol']: row for row in values if row['symbol'] in symbols}


def validate_binding(root, work, active, binding, current, inventory, catalogs=None, annotations=None):
    legacy.require(isinstance(binding, dict) and set(binding) == {'review', 'statements'},
                   'Invalid compact review binding')
    name = binding['review']
    review = legacy.read_json(root, name)
    original = {key: review.get(key) for key in
                ('document', 'meaning_basis', 'identifier_annotations')}
    original['source_inventory'] = review.get('source', {}).get('inventory')
    legacy.require(original['source_inventory'] == active['source_inventory'],
                   'Rebinding changes source inventory')
    if catalogs is None:
        catalogs = {}
    if original['meaning_basis'] not in catalogs:
        catalogs[original['meaning_basis']] = meaning_catalog.load_catalog(root, original['meaning_basis'])
    old = catalogs[original['meaning_basis']]
    legacy.require(old.document_path == original['document'], 'Original review basis differs')
    row = legacy.validate_review(root, name, work, original, old, inventory)
    # The legacy whole-review protocol pins its manuscript, source, evidence and
    # all inherited meaning inputs. Reuse it rather than weakening its checks.
    selected = legacy.selection_binding(current, binding['statements'])
    previous = review['selection']
    legacy.require(
        [s['sha256'] for s in selected['statements']] ==
        [s['sha256'] for s in previous['statements']] and
        selected['dependency_sha256'] == previous['dependency_sha256'] and
        selected['dependencies'] == previous['dependencies'],
        'Review requires rereading: statements or dependency conventions changed: ' + name)
    symbols = set(selected['dependencies'])
    legacy.require(
        selected_identifiers(root, original['meaning_basis'], original['identifier_annotations'], symbols, annotations) ==
        selected_identifiers(root, active['meaning_basis'], active['identifier_annotations'], symbols, annotations),
        'Review requires rereading: selected identifier forms changed: ' + name)
    row.update(document=active['document'], selection=selected,
               registration='unchanged_selection_rebound_to_active_manuscript')
    row['source_sha256'][name] = legacy.digest(legacy.path_in(root, name).read_bytes())
    return row


def load_reviews(root, index_path, cache=None):
    if cache:
        with cache.hash_transaction():
            return _load_reviews(root, index_path, cache)
    return _load_reviews(root, index_path)


def _load_reviews(root, index_path, cache=None):
    root = Path(root).resolve()
    if cache:
        hit = cache.get('compact-reviews', index_path)
        if hit is not None:
            return hit
    index = legacy.read_json(root, index_path)
    if index.get('schema_version') == 'noema-semantic-review-index-1':
        return legacy.load_reviews(root, index_path)
    legacy.require(index.get('schema_version') == SCHEMA, 'Unknown review index schema')
    legacy.require(set(index) == {'schema_version', 'works', 'source_sha256'},
                   'Invalid compact registry fields')
    pins = deepcopy(index['source_sha256'])
    legacy.validate_hashes(root, pins)
    legacy.require(isinstance(index['works'], dict) and index['works'], 'Missing active works')
    result = {}
    catalogs, annotations = {}, {}
    for work, active in index['works'].items():
        legacy.require(set(active) == {'document', 'meaning_basis', 'identifier_annotations',
                                     'source_inventory', 'reviews'}, 'Invalid active document record')
        legacy.require(isinstance(active['reviews'], list), 'Invalid review bindings')
        required = {active[k] for k in ('document', 'meaning_basis', 'source_inventory')}
        if active['identifier_annotations']:
            required.add(active['identifier_annotations'])
        required.update(b['review'] for b in active['reviews'])
        legacy.require(required <= set(pins), 'Unpinned compact registration input')
        current = meaning_catalog.load_catalog(root, active['meaning_basis'])
        catalogs[active['meaning_basis']] = current
        legacy.require(current.document_path == active['document'], 'Active basis document differs')
        merge_pins(pins, current.source_sha256)
        if active['identifier_annotations']:
            selected_identifiers(root, active['meaning_basis'], active['identifier_annotations'], set(), annotations)
        inventory = legacy.read_json(root, active['source_inventory'])
        result[work] = []
        seen = set()
        for binding in active['reviews']:
            row = validate_binding(root, work, active, binding, current, inventory, catalogs, annotations)
            legacy.require(row['unit'] not in seen, 'Duplicate reviewed unit')
            seen.add(row['unit'])
            merge_pins(pins, row.pop('source_sha256'))
            result[work].append(row)
    pins[index_path] = legacy.digest(legacy.path_in(root, index_path).read_bytes())
    result = dict(status='provenance_validated_explicit_review_judgments',
                  works=result, source_sha256=pins,
                  semantic_equivalence_automatically_proved=False)
    if cache:
        # Re-read content after validation: never save a mixed-generation result.
        legacy.require(cache.hashes(pins) == pins, 'Input changed during review registration')
        cache.put('compact-reviews', index_path, result, pins)
    return result


def compact_index(root, index_path, *, work=None, basis=None, annotations=None, reviews=()):
    """Prepare a small new registry; supplied reviews replace the same unit only."""
    root = Path(root).resolve()
    old = legacy.read_json(root, index_path)
    # First validate the source registration; malformed history is never blessed.
    load_reviews(root, index_path)
    result = dict(schema_version=SCHEMA, works=deepcopy(old['works']), source_sha256={})
    if old['schema_version'] == 'noema-semantic-review-index-1':
        for active in result['works'].values():
            active['reviews'] = [
                dict(review=name, statements=[s['index'] for s in
                     legacy.read_json(root, name)['selection']['statements']])
                for name in active['reviews']]
    if work is not None:
        legacy.require(work in result['works'], 'Unknown registration work')
        active = result['works'][work]
        legacy.require(annotations is None or basis is not None,
                       'Specify --basis when changing annotations')
        if basis:
            catalog = meaning_catalog.load_catalog(root, basis)
            active.update(document=catalog.document_path, meaning_basis=basis,
                          identifier_annotations=annotations)
        by_unit = {legacy.read_json(root, b['review'])['unit']: b for b in active['reviews']}
        for name in reviews:
            record = legacy.read_json(root, name)
            legacy.require(record['work'] == work, 'Replacement review work differs')
            by_unit[record['unit']] = dict(review=name, statements=[
                s['index'] for s in record['selection']['statements']])
        active['reviews'] = list(by_unit.values())
    else:
        legacy.require(not basis and annotations is None and not reviews,
                       'Specify --work when changing a registration')
    catalogs, loaded_annotations = {}, {}
    for work_name, active in result['works'].items():
        current = meaning_catalog.load_catalog(root, active['meaning_basis'])
        catalogs[active['meaning_basis']] = current
        inventory = legacy.read_json(root, active['source_inventory'])
        for binding in active['reviews']:
            validate_binding(root, work_name, active, binding, current, inventory, catalogs, loaded_annotations)
        paths = {active[k] for k in ('document', 'meaning_basis', 'source_inventory')}
        paths.update(b['review'] for b in active['reviews'])
        if active['identifier_annotations']:
            paths.add(active['identifier_annotations'])
        result['source_sha256'].update({
            p: legacy.digest(legacy.path_in(root, p).read_bytes()) for p in sorted(paths)})
    return result
