"""Check reversible typed template codes and their adopted source classification."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse, format_graph
from noema.constructed_discourse import function_sort, sequence_sort, question_sort, description_sort
from noema.expression_codes import encode_expression, decode_expression, is_template_code
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest, selection_binding, validate_hashes
from noema.script import transcribe
from scripts.compose_polymorphic_forms import ROOT, FULL, CORE, LIBRARY, BASIS, ANNOTATIONS, PARENT, PARENT_BASIS, MEANINGS, PRIMITIVES, LIMITS, MAPPING, parent, build, closure, replace_symbols
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown, symbol

INDEX = 'data/semantic-review-index-v100.json'
REPORT = 'reports/polymorphic-forms-v1.json'
AUDIT = 'data/polymorphic-forms-reading-v1.json'
DOC = 'docs/polymorphic-forms-v1.md'
INVENTORY = 'artifacts/written-units-v1/kant-1784.json'
FIRST = 'data/nature-sentence-reading-v1.json'
SECOND = 'data/confirmed-incapacity-reading-v1.json'
PRIOR = ('reports/instrumental-misuse-v1.json', 'reports/conditioned-persistence-v1.json')
SIGNATURES = [([], 'content'), (['individual'], 'content'), (['individual', 'individual'], 'truth'),
    (['individual', 'number', 'situation'], 'content'),
    ([function_sort(['individual'], 'content'), sequence_sort('number'), question_sort(['individual'])], 'message'),
    ([description_sort('content'), 'truth'], sequence_sort('individual'))]


def read(path): return json.loads((ROOT / path).read_text(encoding='utf-8'))


@lru_cache(None)
def catalog(): return load_catalog(ROOT, BASIS)


def fixture(roots, suffix=''):
    doc = deepcopy(catalog().document); doc.update(declarations=closure(doc, roots), statements=[])
    return parse(format_graph(doc, 'compact') + suffix)


def runtime_quote(value):
    return dict(kind='quote', body=json.loads(value.syntax), **({'rank': value.rank} if value.rank else {}))


def code_fixture(parameters, result, nonfunction=False):
    doc = fixture(['r2fe', 'r2fm', 'hzzza'], 'r zform[] a.r zpoint[] d.')
    for name in ('ztemplate', 'zother'):
        doc['declarations'].append(dict(kind='primitive', name=name, parameters=parameters, result=result))
    type_ = result if nonfunction else function_sort(parameters, result)
    body = dict(kind='call', symbol='ztemplate', arguments=[]) if nonfunction else dict(kind='function_ref', symbol='ztemplate')
    quotation = dict(kind='quote', body=body)
    code = encode_expression(doc, quotation, type_)
    doc['declarations'].append(dict(kind='definition', name='zcode', parameters=[], result=description_sort('truth'), body=code))
    doc = parse(format_graph(doc, 'compact') + 'q[k r2fe[k zform[] k zcode[] k zpoint[] p hzzza]].q[k r2fd[k zcode[]]].')
    return doc, code, type_, quotation


@lru_cache(None)
def template_checks():
    rows = []
    for parameters, result in SIGNATURES:
        doc, code, type_, original = code_fixture(parameters, result)
        assert decode_expression(doc, code) == (type_, original)
        def model(variant):
            values = {d['name']: unknown for d in doc['declarations'] if d['kind'] == 'primitive'}
            expected = deepcopy(code['body'])
            if variant == 'other_code': expected['arguments'][0]['symbol'] = 'zother'
            values.update(zform=lambda: 'form', zpoint=lambda: 'now',
                r2fd=lambda value: is_template_code(doc, runtime_quote(value)),
                hzzza=lambda form, value, point: form == ('other' if variant == 'other_form' else 'form') and
                    point == ('elsewhere' if variant == 'other_point' else 'now') and json.loads(value.syntax) == expected)
            return values
        variants = {}
        for name in ('baseline', 'other_form', 'other_code', 'other_point'):
            actual = evaluate(doc, model(name), ('form', 'other'), ('now', 'elsewhere'), True)
            assert actual == [name == 'baseline', True], (parameters, result, name, actual)
            variants[name] = actual
        for name in ('r2fd', 'hzzza'):
            values = model('baseline'); values[name] = unknown
            try: evaluate(doc, values, ('form',), ('now',), True)
            except ValueError as error: assert 'Unknown' in str(error)
            else: raise AssertionError(name)
        rows.append(dict(parameters=parameters, result=result, values=variants))
    doc, code, _, _ = code_fixture([], 'truth', True)
    values = {d['name']: unknown for d in doc['declarations'] if d['kind'] == 'primitive'}
    values.update(zform=lambda: 'form', zpoint=lambda: 'now', r2fd=lambda value: is_template_code(doc, runtime_quote(value)), hzzza=lambda *args: True)
    assert evaluate(doc, values, ('form',), ('now',), True) == [False, False]
    return dict(signatures=rows, combinations=24, unknown_inputs_refused=12, nonfunction_code_refused=True,
        original_contents_never_executed=True, arity_or_sort_table_not_used_by_implementation=True)


@lru_cache(None)
def bridge_checks():
    doc = fixture(['r2fm', 'r2fd'], 'r ztemplate[a] e.r zother[a] e.')
    code = encode_expression(doc, dict(kind='quote', body=dict(kind='function_ref', symbol='ztemplate')), function_sort(['individual'], 'content'))
    doc['declarations'].append(dict(kind='definition', name='zcode', parameters=[], result=description_sort('truth'), body=code))
    doc = parse(format_graph(doc, 'compact') + '''q[e[k r2fm[r[p ztemplate]]][k zcode[]]].
q[k r2fd[k r2fm[r[p ztemplate]]]].q[e[k r2fm[r[p zother]]][k zcode[]]].''')
    values = dict(ztemplate=unknown, zother=unknown, r2fd=lambda value: is_template_code(doc, runtime_quote(value)))
    actual = evaluate(doc, values, ('form',), ('now',), True)
    assert actual == [True, True, False]
    refused = fixture(['r2fg'], 'r zform[] a.r zpoint[] d.q[t[k r2fg[k zform[]]][k zpoint[]]].')
    values = {d['name']: unknown for d in refused['declarations'] if d['kind'] == 'primitive'}
    values.update(zform=lambda: 'form', zpoint=lambda: 'now')
    try: evaluate(refused, values, ('form',), ('now',), True)
    except ValueError as error: assert 'Cannot finitely quantify' in str(error) and 'description' in str(error), str(error)
    else: raise AssertionError('Description universe replaced by known codes')
    return dict(legacy_adapter_values=actual, no_automatic_storage_fact_migration=True,
        quantified_classification_explicitly_refused=True)


@lru_cache(None)
def presentation_checks():
    doc = fixture(['r2fk'], 'q[k r2fk[]].'); rows = {}
    for variant in ('baseline', 'node', 'author', 'target', 'depiction', 'context', 'obsolete_target', 'reversed'):
        wanted = ['node', 'author', 'r2fj', 'h2b', 'now']
        if variant in ('node', 'author', 'target', 'depiction', 'context'):
            wanted[('node', 'author', 'target', 'depiction', 'context').index(variant)] = 'other'
        if variant == 'obsolete_target': wanted[2] = 'r2es'
        if variant == 'reversed': wanted[2:4] = ['h2b', 'r2fj']
        values = {d['name']: unknown for d in doc['declarations'] if d['kind'] == 'primitive'}
        values.update(h2d=lambda: 'node', wa=lambda: 'author', wh=lambda: 'now',
            rbt=lambda n, a, target, depiction, point: [n, a, symbol(target), symbol(depiction), point] == wanted)
        actual = evaluate(doc, values, ('node', 'author', 'other'), ('now',), True)
        assert actual == [variant == 'baseline'], (variant, actual)
        rows[variant] = actual
    values['rbt'] = unknown
    try: evaluate(doc, values, ('node', 'author', 'other'), ('now',), True)
    except ValueError as error: assert 'Unknown' in str(error)
    else: raise AssertionError('Unknown presentation accepted')
    return dict(cases=rows, unknown_inputs_refused=1, world_contents_not_executed_by_attribution=True)


@lru_cache(None)
def reused_checks():
    old, new = parent(), catalog()
    for p in PRIOR: validate_hashes(ROOT, read(p)['source_sha256'])
    for roots in (['r2eq', 'h26', 'h2b'], ['r2ey'], ['ho2', 'h3b']):
        assert closure(old.document, roots) == closure(new.document, roots)
    for source in ('h27', 'r2er', 'r2es', 'r2et', 'r2ez'):
        expected = replace_symbols(deepcopy(old.entries[source]['declaration']), MAPPING)
        expected['name'] = MAPPING[source]
        assert new.entries[MAPPING[source]]['declaration'] == expected
    for p, ids in ((FIRST, [51]), (SECOND, [11, 12])):
        r = read(p); validate_hashes(ROOT, r['source_sha256']); assert r['selection'] == selection_binding(new, ids)
    return dict(reports=list(PRIOR), use_cause_persistence_and_conditional_profile_unchanged=True,
        finite_evidence_reused_without_claiming_full_rerun=True, first_sentence_review_preserved=True,
        second_sentence_review_preserved=True, preserved_reviewed_sentence_characters=247)


def reading():
    unit = next(u for u in read(INVENTORY)['units'] if u['id'] == 'kant-1784:u0010')
    paths = {INDEX, INVENTORY, FULL, BASIS, PARENT, PARENT_BASIS, FIRST, SECOND, *PRIOR}
    return dict(status='fixed_unary_template_restriction_removed_from_partial_source_classification', document=FULL, meaning_basis=BASIS,
        source=dict(unit=unit['id'], unit_sha256=unit['text_sha256'], range=[293, 473], text=unit['text'][293:473]),
        alignment=[], selection=selection_binding(catalog(), [10, 52, 53]),
        decision='固定した表現の構成を保持する読みは維持し、個体一つを引数に取る型への制約を外す。第三文の意味一致の判断は追加しない。',
        interpretation_limits=LIMITS, revised_statement_indices=[52], preserved_statement_indices=[10, 53],
        whole_sentence_semantically_verified=False, whole_unit_semantically_verified=False,
        new_verified_sentence_characters=0, preserved_reviewed_sentence_characters=247,
        semantic_equivalence_automatically_proved=False,
        source_sha256={p: digest((ROOT / p).read_bytes()) for p in sorted(paths)})


@lru_cache(None)
def structure_checks():
    old, new = parent(), catalog()
    assert new.document['declarations'][:-11] == old.document['declarations']
    assert all(new.entries[n] == e for n, e in old.entries.items())
    assert set(new.entries) - set(old.entries) == set(MEANINGS) | set(PRIMITIVES)
    assert len(new.document['statements']) == len(old.document['statements']) == 54
    assert [i for i, (a, b) in enumerate(zip(old.document['statements'], new.document['statements'])) if a != b] == [52]
    assert new.document['statements'][52]['body']['symbol'] == 'r2fk'
    reviews = read(INDEX)['works']['kant-1784']['reviews']; assert len(reviews) == 12
    for p in reviews:
        r = read(p); validate_hashes(ROOT, r['source_sha256'])
        ids = [s['index'] for s in r['selection']['statements']]
        assert r['selection'] == selection_binding(old, ids) == selection_binding(new, ids)
    for path, body in build().items(): assert (ROOT / path).read_text(encoding='utf-8') == body, path
    for path in (FULL, CORE, LIBRARY):
        doc = parse((ROOT / path).read_text(encoding='utf-8'))
        for style in ('compact', 'full'):
            text = format_graph(doc, style)
            assert parse(text) == parse(transcribe(text, alphabet='v2')) == doc
    assert reading() == read(AUDIT)
    assert not {'rbs', 'hw2', 'h22'} & {d['name'] for d in closure(new.document, ['r2fk', 'r2fl'])}
    return dict(new_definitions=9, new_primitives=2, structural_predicates=1, source_storage_relations=1,
        authored_statements=54, preserved_statements=53, revised_statement_indices=[52],
        preserved_review_selections=12, reviewed_nonblank_characters=2212,
        preserved_reviewed_sentence_characters=247, old_unary_classifier_removed_from_current_target=True, roundtrips=True)


def prepare():
    from scripts.audit_opening_scope import write_exact, encoded
    write_exact(ROOT / AUDIT, encoded(reading()))


def build_report():
    results = {}
    for name, fn in [('templates', template_checks), ('bridge', bridge_checks), ('presentation', presentation_checks),
                     ('reused', reused_checks), ('structure', structure_checks)]:
        results[name] = fn(); print(name + ' checked', flush=True)
    paths = set(build()) | set(catalog().source_sha256) | set(reading()['source_sha256']) | {
        AUDIT, DOC, 'noema/expression_codes.py', 'noema/description_templates.py', 'noema/constructed_discourse.py',
        'tests/test_expression_codes.py', 'tests/test_polymorphic_forms.py', 'scripts/compose_polymorphic_forms.py',
        'scripts/check_polymorphic_forms.py', 'scripts/register_polymorphic_forms.py'}
    for p in PRIOR: paths.update(read(p)['source_sha256'])
    return dict(status='typed_template_classification_adopted_without_unary_restriction', document=FULL, **results,
        alignment=[], whole_sentence_semantically_verified=False, whole_unit_semantically_verified=False,
        new_verified_sentence_characters=0, preserved_reviewed_sentence_characters=247, new_covered_characters=0,
        verified_full_units={'kant-1784': 0, 'einstein-1905': 0}, semantic_equivalence_automatically_proved=False,
        source_sha256={p: digest((ROOT / p).read_bytes()) for p in sorted(paths)})


if __name__ == '__main__':
    from scripts.audit_opening_scope import write_exact, encoded
    prepare(); write_exact(ROOT / REPORT, encoded(build_report()))
