"""Publish reviewed statements without deleting the cumulative manuscripts.

Keep every declaration and its original meaning provenance. Only the statement
list is selected; no simplification, deduplication or semantic judgment occurs.
Run through project_work check so the existing content-addressed cache is used.
"""
from copy import deepcopy
from functools import lru_cache
import json
from pathlib import Path

from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog, _references
from noema.review_registry import load_reviews
from noema.semantic_reviews import canonical_digest, digest, require
from noema.script import transcribe

ROOT = Path(__file__).resolve().parents[1]
SOURCE_INDEX = 'data/semantic-review-index-v455.json'
INDEX = 'data/semantic-review-index-v456.json'
MANIFEST = 'data/reviewed-works-assembly-v1.json'
DOC = 'docs/reviewed-works-assembly-v1.md'
OUTPUTS = {
    'kant-1784': ('examples/v016/kant-reviewed-complete-v1.noema',
                  'data/kant-reviewed-complete-basis-v1.json',
                  'data/kant-reviewed-complete-identifiers-v1.json'),
    'einstein-1905': ('examples/v014/einstein-reviewed-complete-v1.noema',
                      'data/einstein-reviewed-complete-basis-v1.json',
                      'data/einstein-reviewed-complete-identifiers-v1.json'),
}


def read(path):
    return json.loads((ROOT / path).read_text(encoding='utf-8'))


def encode(value):
    return json.dumps(value, ensure_ascii=False, indent=2) + '\n'


def select_statements(document, bindings):
    """Preserve occurrence order, scoped statement bodies and all declarations."""
    require(bool(bindings), 'No reviewed bindings')
    for binding in bindings:
        indices = binding['statements']
        require(isinstance(indices, list) and bool(indices) and
                all(type(n) is int and 0 <= n < len(document['statements']) for n in indices),
                'Invalid reviewed statement index')
        require(indices == sorted(set(indices)), 'Repeated or unordered review selection')
    indices = sorted({n for b in bindings for n in b['statements']})
    remap = {old: new for new, old in enumerate(indices)}
    result = deepcopy(document)
    result['statements'] = [deepcopy(document['statements'][n]) for n in indices]
    rebound = [dict(review=b['review'], statements=[remap[n] for n in b['statements']])
               for b in bindings]
    return result, rebound, remap


@lru_cache(None)
def build():
    source = read(SOURCE_INDEX)
    verified = load_reviews(ROOT, SOURCE_INDEX)
    require(set(source['works']) == set(OUTPUTS), 'Unexpected work inventory')
    target = deepcopy(source)
    target['source_sha256'] = {}
    files = {}
    manifest = dict(version='reviewed-works-assembly-v1', source_index=SOURCE_INDEX,
                    output_index=INDEX, works={}, semantic_judgments_added=0,
                    original_manuscripts_and_evidence_preserved=True,
                    completion_audit_still_required=True)
    for work, active in source['works'].items():
        catalog = load_catalog(ROOT, active['meaning_basis'])
        units = [u for u in read(active['source_inventory'])['units'] if u['kind'] != 'editorial']
        require({u['id'] for u in units} == {r['unit'] for r in verified['works'][work]},
                'The source work still has an unreviewed author unit')
        document, bindings, remap = select_statements(catalog.document, active['reviews'])
        full, basis, annotations = OUTPUTS[work]
        body = format_graph(document, 'compact') + '\n'
        files[full] = body
        files[basis] = encode(dict(
            status='all_author_units_selected_under_registered_readings',
            document=full, parent=active['document'],
            inherited_meaning_basis=active['meaning_basis'],
            primitives={}, definitions={}, new_signatures={},
            limitations=[
                '登録済みの全文判断が選択する主張を元の出現順で収録する。新しい意味判断や原文同義性の証明ではない。',
                '宣言・意味規約・引用名を全て保持し、判断対象でない旧主張は累積稿へ保存する。未使用の宣言は語彙の履歴であり本文の追加主張ではない。',
                '原文順の案内と旧新の文番号はreviewed-works-assembly-v1.jsonに保持する。六成果物の完成監査は別に行う。']))
        ann = read(active['identifier_annotations'])
        ann.update(document=full, document_sha256=digest(body.encode('utf-8')))
        files[annotations] = encode(ann)
        target['works'][work].update(document=full, meaning_basis=basis,
                                    identifier_annotations=annotations, reviews=bindings)
        by_unit = {read(b['review'])['unit']: b for b in active['reviews']}
        rows = []
        for unit in units:
            binding = by_unit[unit['id']]
            review = read(binding['review'])
            original_indices = [s['index'] for s in review['selection']['statements']]
            order = review.get('source_order_statements')
            rows.append(dict(unit=unit['id'], review=binding['review'],
                             source_unit_sha256=unit['text_sha256'],
                             old_statements=binding['statements'],
                             statements=[remap[n] for n in binding['statements']],
                             source_order_statements=(None if order is None else [
                                 remap[binding['statements'][original_indices.index(n)]] for n in order]),
                             ordering=('original_review_selection_only' if order is None else
                                       'explicit_source_order_from_original_review')))
        omitted = [dict(index=n, kind=s['kind'], sha256=canonical_digest(s),
                        direct_references=sorted(_references(s)))
                   for n, s in enumerate(catalog.document['statements']) if n not in remap]
        manifest['works'][work] = dict(
            source_document=active['document'], document=full,
            source_statement_count=len(catalog.document['statements']),
            statement_count=len(document['statements']),
            all_declarations_preserved=len(document['declarations']),
            statement_index_map=[dict(old=old, new=new) for old, new in remap.items()],
            units=rows, omitted_from_reading_edition=omitted)
    for active in target['works'].values():
        paths = {active[k] for k in ('document', 'meaning_basis', 'identifier_annotations', 'source_inventory')}
        paths.update(b['review'] for b in active['reviews'])
        for path in paths:
            raw = files[path].encode('utf-8') if path in files else (ROOT / path).read_bytes()
            target['source_sha256'][path] = digest(raw)
    target['source_sha256'] = dict(sorted(target['source_sha256'].items()))
    files[INDEX] = encode(target)
    manifest['source_sha256'] = {
        path: digest((ROOT / path).read_bytes())
        for path in (SOURCE_INDEX, DOC, 'scripts/assemble_reviewed_works.py', 'tests/test_reviewed_works_assembly.py')}
    files[MANIFEST] = encode(manifest)
    return files


def prepare():
    from scripts.audit_opening_scope import write_exact
    for path, text in build().items():
        write_exact(ROOT / path, text)


@lru_cache(None)
def assembly_checks():
    files = build()
    for path, text in files.items():
        require((ROOT / path).read_text(encoding='utf-8') == text, 'Assembly artifact differs: ' + path)
    # This checks every ORIGINAL judgment and then its statement, transitive
    # meaning and designation binding against the new complete manuscript.
    verified = load_reviews(ROOT, INDEX)
    source = read(SOURCE_INDEX)
    target = read(INDEX)
    results = {}
    for work, active in target['works'].items():
        current = load_catalog(ROOT, active['meaning_basis'])
        old = load_catalog(ROOT, source['works'][work]['meaning_basis'])
        require(current.entries == old.entries, 'A declaration or its meaning provenance changed')
        used = {n for b in active['reviews'] for n in b['statements']}
        require(used == set(range(len(current.document['statements']))), 'Unreviewed statement in reading edition')
        for style in ('compact', 'full'):
            text = format_graph(current.document, style)
            require(parse(text) == current.document, 'Format round trip differs')
            require(parse(transcribe(text, alphabet='v2')) == current.document, 'Native alphabet round trip differs')
        results[work] = dict(units=len(verified['works'][work]),
                             statements=len(current.document['statements']),
                             declarations=len(current.entries),
                             all_meanings_and_original_judgments_preserved=True,
                             every_statement_selected_by_a_whole_unit_review=True,
                             compact_full_and_native_alphabet_roundtrips=True)
    return results, verified['source_sha256']


def build_report():
    results, pins = assembly_checks()
    pins = dict(pins)
    for path in {*build(), DOC, 'scripts/assemble_reviewed_works.py', 'tests/test_reviewed_works_assembly.py'}:
        pins[path] = digest((ROOT / path).read_bytes())
    return dict(status='two_complete_reviewed_reading_editions_assembled', works=results,
                original_evidence_preserved=True, semantic_judgments_added=0,
                completion_audit_still_required=True,
                semantic_equivalence_automatically_proved=False,
                source_sha256=dict(sorted(pins.items())))
