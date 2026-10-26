"""Inventory the complete selected manuscripts before visible-format migration.

No declaration is removed, renamed, evaluated or declared semantically reusable.
Quoted references participate in dependency closure just like other references.
"""
from collections import Counter, defaultdict
from copy import deepcopy
from functools import lru_cache
from pathlib import Path
import argparse
import hashlib
import json

from noema.constructed import parse
from noema.constructed_discourse import normalize_document
from noema.meaning_catalog import load_catalog, _object
from noema.identifiers import load_annotations
from scripts.shared_modality import renamed
from scripts.visible_senses_vocabulary import SensesVocabulary
from scripts.visible_sharing import nodes, MAX_EXPANDED_NODES

ROOT = Path(__file__).resolve().parents[1]
STATE = 'data/work-state.json'
REPORT = 'reports/manuscript-transfer-v1.json'
OUT = 'output/manuscript-transfer-v1'
LIBRARIES = ('answers', 'claim-choice', 'conversation', 'deadlines', 'discourse',
             'evidence', 'focus', 'generality', 'modality', 'norms', 'plurality',
             'quantities', 'readings', 'reference', 'revision', 'selection',
             'senses', 'situation-reference', 'speech', 'time')


def require(condition, message):
    if not condition:
        raise ValueError(message)


def encoded(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def references(value, quoted=False):
    """Return all static references and those lexically inside a quote.

    The latter is a conservative warning, not an analysis of all ways a runtime
    description can be constructed or compared.
    """
    all_names, quoted_names = set(), set()
    if isinstance(value, dict):
        quoted = quoted or value.get('kind') == 'quote'
        if value.get('kind') in ('call', 'function_ref'):
            all_names.add(value['symbol'])
            if quoted:
                quoted_names.add(value['symbol'])
        children = value.values()
    elif isinstance(value, list):
        children = value
    else:
        children = ()
    for child in children:
        a, q = references(child, quoted)
        all_names.update(a)
        quoted_names.update(q)
    return all_names, quoted_names


def dependency_graph(document):
    direct = {}
    for declaration in document['declarations']:
        name = declaration['name']
        require(name not in direct, 'Duplicate declaration: ' + name)
        refs, _ = references(declaration.get('body'))
        require(refs <= direct.keys(), 'Unknown, forward or recursive reference: ' + name)
        direct[name] = refs
    require(references(document['statements'])[0] <= direct.keys(), 'Unknown statement reference')
    return direct


def closure(names, direct):
    result, pending = set(), set(names)
    while pending:
        name = pending.pop()
        require(name in direct, 'Unknown dependency: ' + name)
        if name not in result:
            result.add(name)
            pending.update(direct[name] - result)
    return result


def edition_candidate(document):
    """Check an explicit 0.16 candidate while retaining the selected original."""
    candidate = deepcopy(document)
    candidate['schema_version'] = candidate['lexicon_version'] = '0.16'
    normalized = normalize_document(candidate)
    require(normalized == candidate, 'Edition change modifies normalized payload')
    return dict(source_edition=document['schema_version'], target_edition='0.16',
                declarations_and_statements_unchanged=True,
                source_payload_sha256=digest(encoded({k: document[k] for k in ('declarations', 'statements')})),
                applied=False, semantic_review_transferred=False)


def mapping_specs(basis):
    result = []
    for path, mapping in basis.get('source_renamings', {}).items():
        result.append((path, mapping))
    for field in ('preserved_definitions', 'preserved_sources'):
        for row in basis.get(field, []):
            mapping = row.get('renaming', row.get('names'))
            if isinstance(mapping, list):
                mapping = {name: name for name in mapping}
            require(isinstance(mapping, dict) and mapping, 'Missing explicit preservation mapping')
            result.append((row['document'], mapping))
    return result


def complete_mapping(originals, mapping, other_sources):
    """Import inherited rename keys only when their source declaration matches."""
    result = dict(mapping)
    for other, aliases in other_sources:
        for old, new in aliases.items():
            if old in originals and old in other and originals[old] == other[old]:
                require(old not in result or result[old] == new, 'Conflicting inherited rename: ' + old)
                result[old] = new
    return result


def inventory(document, entries, identifiers, candidates):
    direct = dependency_graph(document)
    require(set(entries) == set(direct), 'Meaning inventory differs')
    require(set(identifiers) <= set(direct), 'Unknown designation')
    uses = defaultdict(list)
    statements = []
    for index, statement in enumerate(document['statements']):
        refs, quoted = references(statement)
        needed = closure(refs, direct)
        for name in needed:
            uses[name].append(index)
        statements.append(dict(index=index, kind=statement['kind'], direct_dependencies=sorted(refs),
                               quoted_dependencies=sorted(quoted), transitive_declarations=len(needed),
                               nodes=nodes(statement)))
    rows = []
    for index, declaration in enumerate(document['declarations']):
        name = declaration['name']; entry = entries[name]
        require(entry['declaration'] == declaration and entry['kind'] == declaration['kind'],
                'Meaning declaration differs: ' + name)
        require(isinstance(entry['meaning_ja'], str) and entry['meaning_ja'].strip(), 'Missing meaning')
        compatible = []
        for candidate in candidates.get(name, []):
            # An identically spelled symbol in another source is not evidence.
            if declaration == candidate['declaration']:
                compatible.append({k: v for k, v in candidate.items() if k != 'declaration'})
        _, quoted = references(declaration.get('body'))
        rows.append(dict(index=index, symbol=name, kind=declaration['kind'],
                         declaration_sha256=digest(encoded(declaration)), nodes=nodes(declaration),
                         meaning_basis=entry['meaning_basis'], meaning_ja=entry['meaning_ja'],
                         argument_roles=entry.get('arguments'), designation_forms=identifiers.get(name, []),
                         direct_dependencies=sorted(direct[name]), quoted_dependencies=sorted(quoted),
                         statement_indices=uses[name], structural_shared_candidates=compatible,
                         visible_spelling_assigned=False))
    counts = Counter((r['kind'], bool(r['statement_indices'])) for r in rows)
    summary = dict(declarations=len(rows), statements=len(statements), nodes=nodes(document),
                   primitives=sum(r['kind'] == 'primitive' for r in rows),
                   definitions=sum(r['kind'] == 'definition' for r in rows),
                   reachable_declarations=sum(bool(r['statement_indices']) for r in rows),
                   reachable_primitives=counts['primitive', True], reachable_definitions=counts['definition', True],
                   retained_unreferenced_primitives=counts['primitive', False],
                   retained_unreferenced_definitions=counts['definition', False],
                   designations=len(identifiers),
                   structural_shared_candidates=sum(bool(r['structural_shared_candidates']) for r in rows),
                   declarations_containing_quoted_references=sum(bool(r['quoted_dependencies']) for r in rows),
                   single_declarations_over_node_budget=[r['symbol'] for r in rows if r['nodes'] > MAX_EXPANDED_NODES],
                   largest_declarations=[dict(symbol=r['symbol'], nodes=r['nodes'])
                                         for r in sorted(rows, key=lambda r: (-r['nodes'], r['index']))[:10]])
    return dict(summary=summary, declarations=rows, statements=statements)


@lru_cache(maxsize=1)
def build():
    pins = {}

    def pin(path):
        target = (ROOT / path).resolve()
        require(target.is_relative_to(ROOT), 'Input outside project')
        name = target.relative_to(ROOT).as_posix(); raw = target.read_bytes(); stamp = digest(raw)
        require(name not in pins or pins[name] == stamp, 'Input changed during inventory')
        pins[name] = stamp
        return raw

    def read(path):
        return pin(path).decode('utf-8')

    def read_json(path):
        return json.loads(read(path), object_pairs_hook=_object)

    state = read_json(STATE); index = read_json(state['review_index'])
    prior = read_json(state['progress_report'])
    visible_report = read_json('reports/visible-senses-v1.json')
    for path, stamp in visible_report['source_sha256'].items():
        pin(path)
        require(pins[path] == stamp, 'Published visible source changed: ' + path)
    vocab = SensesVocabulary(); candidates = defaultdict(list); origin_rows = []
    for library in LIBRARIES:
        path = 'data/shared-' + library + '-basis-v1.json'; basis = read_json(path)
        require(path in visible_report['source_sha256'], 'Library absent from visible evidence: ' + path)
        ds = parse(read(basis['document']))['declarations']
        require(set(basis['public_contracts']) == {d['name'] for d in ds}, 'Public contract inventory differs')
        for d in ds:
            require(d == vocab._plain_declaration(d['name']), 'Shared declaration changed: ' + d['name'])
        sources = [(source, mapping, {d['name']: d for d in parse(read(source))['declarations']})
                   for source, mapping in mapping_specs(basis)]
        for source, mapping, originals in sources:
            require(set(mapping) <= originals.keys(), 'Missing source definition')
            complete = complete_mapping(originals, mapping, [(ds, m) for _, m, ds in sources])
            for old, new in mapping.items():
                d = originals[old]
                require(renamed(d, complete) == vocab._plain_declaration(new),
                        'Preservation mapping changes definition: ' + source + ':' + old)
                row = dict(shared_word=new, mapping_basis=path, source_document=source,
                           source_symbol=old, kind=d['kind'], declaration=d, semantic_replacement_authorized=False)
                if d['kind'] == 'definition':
                    candidates[old].append(row)
                origin_rows.append({k: v for k, v in row.items() if k != 'declaration'})
    works = {}
    for work, spec in index['works'].items():
        catalog = load_catalog(ROOT, spec['meaning_basis'], document_path=spec['document'])
        for path, stamp in catalog.source_sha256.items():
            read(path)
            require(pins[path] == stamp == prior['source_sha256'].get(path),
                    'Selected catalog differs from preserved evidence: ' + path)
        annotations = load_annotations(ROOT, spec['meaning_basis'], spec['identifier_annotations'])
        read(spec['identifier_annotations'])
        require(pins[spec['identifier_annotations']] == annotations.digest
                == prior['source_sha256'].get(spec['identifier_annotations']), 'Designation evidence changed')
        identifiers = {r['symbol']: r['forms'] for r in annotations.annotations['entries']}
        result = inventory(catalog.document, catalog.entries, identifiers, candidates)
        result.update(document=spec['document'], meaning_basis=spec['meaning_basis'],
                      identifier_annotations=spec['identifier_annotations'],
                      edition_candidate=edition_candidate(catalog.document))
        works[work] = result
    for path in ('scripts/manuscript_transfer.py', 'tests/test_manuscript_transfer.py',
                 'docs/manuscript-transfer-v1.md'):
        read(path)
    return dict(works=works, source_mappings=origin_rows, source_sha256=dict(sorted(pins.items())),
                public_vocabulary=dict(edition=12, words=len(vocab._words), definitions=len(vocab._definitions),
                                       primitives=sum(vocab._plain_declaration(n)['kind'] == 'primitive'
                                                      for n in vocab._words)))


def artifact(work):
    return OUT + '/' + work + '.json'


def prepare():
    result = build()
    for work, data in result['works'].items():
        path = ROOT / artifact(work)
        body = json.dumps(data, ensure_ascii=False, indent=2) + '\n'
        require(not path.exists() or path.read_text(encoding='utf-8') == body,
                'Existing transfer inventory differs; use a new edition')
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists():
            path.write_text(body, encoding='utf-8', newline='\n')


def build_report():
    result = build(); hashes = {}
    for work, data in result['works'].items():
        path = artifact(work); raw = (ROOT / path).read_bytes()
        require(json.loads(raw.decode('utf-8'), object_pairs_hook=_object) == data, 'Saved inventory differs')
        hashes[path] = digest(raw)
    return dict(schema='noema-manuscript-transfer-inventory-1',
                works={w: {k: d[k] for k in ('document', 'meaning_basis', 'identifier_annotations', 'summary', 'edition_candidate')}
                       for w, d in result['works'].items()}, public_vocabulary=result['public_vocabulary'],
                explicit_preservation_mappings=len(result['source_mappings']),
                source_sha256=result['source_sha256'], artifact_sha256=hashes,
                existing_limits=dict(expanded_nodes=MAX_EXPANDED_NODES, changed=False),
                declarations_removed=0, primitives_added=0, manuscript_mutations=0,
                full_manuscript_visible_decoding=False, semantic_replacement_authorized=False,
                limits=[
                    'All selected declarations remain in source order, including statically unreferenced declarations.',
                    'Reference closure includes quotations but does not evaluate function arguments or prove semantic necessity.',
                    'Preservation mappings establish exact renamed syntax only; they do not authorize merging names or transferring semantic judgments.',
                    'Designation spellings identify objects, not their conceptual meanings or referent identity.',
                    'Node counts are exact for the existing expanded-node guard, not glyph, shape, row, page or human effort estimates.',
                    'The explicit edition candidate changes only version headers; selected manuscripts and registered judgments remain unchanged.',
                    'This inventory is not a visible dictionary, a manuscript decoder, OCR or evidence of independent human reading.'])


def main(argv=None):
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('work', choices=('kant-1784', 'einstein-1905'))
    cli.add_argument('symbol', help='Selected manuscript symbol; spelling alone is not shared identity')
    args = cli.parse_args(argv)
    from noema.validation_cache import ValidationCache
    cache = ValidationCache(ROOT)
    try:
        # This module has already imported load_catalog; use the installed
        # adapter explicitly rather than claiming its alias was patched.
        with cache.adapters():
            from noema import meaning_catalog
            state = json.loads((ROOT / STATE).read_text(encoding='utf-8'))
            spec = json.loads((ROOT / state['review_index']).read_text(encoding='utf-8'))['works'][args.work]
            catalog = meaning_catalog.load_catalog(ROOT, spec['meaning_basis'], document_path=spec['document'])
            require(args.symbol in catalog.entries, 'Unknown selected symbol')
            direct = dependency_graph(catalog.document)
            entry = deepcopy(catalog.entries[args.symbol])
            entry['direct_dependencies'] = sorted(direct[args.symbol])
            entry['transitive_declarations'] = len(closure([args.symbol], direct))
            entry['statement_indices'] = [i for i, s in enumerate(catalog.document['statements'])
                                          if args.symbol in closure(references(s)[0], direct)]
            entry['work'] = args.work
            print(json.dumps(entry, ensure_ascii=False, indent=2))
    finally:
        cache.close()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
