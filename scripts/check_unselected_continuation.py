"""Check deliberated choice, unselected responses, and a counterfactual comparison."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest, selection_binding, validate_hashes
from noema.script import transcribe
from scripts.compose_unselected_continuation import ROOT, FULL, CORE, BASIS, ANNOTATIONS, PARENT, PARENT_BASIS, MEANINGS, PRIMITIVES, LIMITS, parent, build, closure
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown, symbol
from scripts.check_graded_change import VALUES, SOURCE_PEOPLE, SOURCE_SCENES, SOURCE_DECLS, SOURCE_ARGS
from scripts.check_internalized_state import source_values as prior_values

INDEX = 'data/semantic-review-index-v91.json'
AUDIT = 'data/unselected-continuation-reading-v1.json'
REPORT = 'reports/unselected-continuation-v1.json'
DOC = 'docs/unselected-continuation-v1.md'
INVENTORY = 'artifacts/written-units-v1/kant-1784.json'


def read(path):
    return json.loads((ROOT / path).read_text(encoding='utf-8'))


@lru_cache(None)
def catalog():
    return load_catalog(ROOT, BASIS)


@lru_cache(None)
def fixture(roots, suffix):
    d = deepcopy(catalog().document)
    d.update(declarations=closure(d, roots.split()), statements=[])
    return parse(format_graph(d, 'compact') + suffix)


@lru_cache(None)
def structure_checks():
    old, new = parent(), catalog()
    assert new.document['declarations'][:-7] == old.document['declarations']
    assert new.document['statements'] == old.document['statements'] and len(new.document['statements']) == 51
    assert all(new.entries[n] == entry for n, entry in old.entries.items())
    assert set(new.entries) - set(old.entries) == set(MEANINGS) | set(PRIMITIVES)
    for path in read(INDEX)['works']['kant-1784']['reviews']:
        r = read(path); validate_hashes(ROOT, r['source_sha256'])
        ids = [s['index'] for s in r['selection']['statements']]
        assert r['selection'] == selection_binding(old, ids) == selection_binding(new, ids)
    assert len(read(INDEX)['works']['kant-1784']['reviews']) == 12
    for path, body in build().items():
        assert (ROOT / path).read_text(encoding='utf-8') == body, path
    for path in (FULL, CORE):
        d = parse((ROOT / path).read_text(encoding='utf-8'))
        for style in ('compact', 'full'):
            text = format_graph(d, style)
            assert parse(text) == parse(transcribe(text, alphabet='v2')) == d
    core = parse((ROOT / CORE).read_text(encoding='utf-8'))
    assert core['statements'] == [] and core['declarations'] == closure(new.document, list(MEANINGS))
    assert reading() == read(AUDIT); validate_hashes(ROOT, read(AUDIT)['source_sha256'])
    return dict(new_definitions=5, new_primitives=2, preserved_statements=51, new_authored_assertions=0,
        preserved_review_selections=12, reviewed_nonblank_characters=2212, roundtrips=True,
        comparison_dimension_composed=True, lexical_equivalence_not_claimed=True)


def prepare():
    from scripts.audit_opening_scope import write_exact, encoded
    write_exact(ROOT / AUDIT, encoded(reading()))


TRUE = 'e[k zperson[]][k zperson[]]'
FALSE = 'u[' + TRUE + ']'
DECLS = 'r zperson[] a.r zreference[] a.r zanchor[] d.'


@lru_cache(None)
def selection_checks():
    doc = fixture('r2cw r2cr hznn', DECLS + 'r zjudgment[] a.' +
        ''.join('q[k r2cw[k zperson[] k zreference[] r[p r2cr] ' + sign + ' k zanchor[]]].' for sign in (TRUE, FALSE)) +
        'q[k hznn[k zjudgment[] k zreference[] r[p r2cr] ' + TRUE + ' k zanchor[]]].')
    def values(bits=(True, True, False, True), variant='baseline'):
        actor, positive, negative, belief = bits
        model = {d['name']: unknown for d in doc['declarations'] if d['kind'] == 'primitive'}
        model.update(zperson=lambda: 'person', zreference=lambda: 'reference', zanchor=lambda: 'now', zjudgment=lambda: 'process',
            fa=lambda p, judgment, point: actor and (p, judgment, point) == (
                'method' if variant == 'other_person' else 'person', 'method' if variant == 'split_judgment' else 'process', 'now'),
            hzzf=lambda judgment, target, description, polarity, point: (positive if polarity else negative) and (
                judgment, target, symbol(description), point) == ('process', 'method' if variant == 'other_target' else 'reference',
                'bf' if variant == 'other_property' else 'r2cr', 'before' if variant == 'prior_decision' else 'now'),
            hznn=lambda judgment, target, description, polarity, point: belief and (judgment, target, symbol(description), polarity, point) == (
                'process', 'reference', 'r2cr', True, 'now'))
        return model
    rows = []
    for bits in product((False, True), repeat=4):
        actual = evaluate(doc, values(bits), SOURCE_PEOPLE, SOURCE_SCENES, True)
        assert actual == [bits[0] and bits[1], bits[0] and bits[2], bits[3]], (bits, actual)
        rows.append(dict(bits=list(bits), values=actual))
    contrasts = {}
    for name in ('other_person', 'split_judgment', 'other_target', 'other_property', 'prior_decision'):
        actual = evaluate(doc, values(variant=name), SOURCE_PEOPLE, SOURCE_SCENES, True)
        assert actual == [False, False, True], (name, actual)
        contrasts[name] = actual
    for name in ('fa', 'hzzf', 'hznn'):
        model = values(); model[name] = unknown
        try: evaluate(doc, model, SOURCE_PEOPLE, SOURCE_SCENES, True)
        except ValueError as error: assert 'Unknown' in str(error)
        else: raise AssertionError(name)
    return dict(combinations=rows, contrasts=contrasts, unknown_inputs_refused=3,
                descriptive_assent_does_not_imply_practical_selection=True)


def source_values(doc, variant='baseline'):
    values = prior_values(doc, variant)
    def candidates(pattern, p, description, anchor, point, candidate):
        return (pattern, p, symbol(description), anchor) == ('reference', 'person', 'bf', 'now') and candidate in (
            ('before',) if point == 'before' else SOURCE_SCENES)
    def choice(judgment, target, description, polarity, point):
        if (target, symbol(description)) != ('reference', 'r2cr'): return False
        if judgment != ('process' if polarity else 'method'): return False
        if variant == 'currently_selected': return polarity and point == 'now'
        if variant == 'currently_opposed': return not polarity and point == 'now'
        if variant == 'selected_successes': return polarity and point in ('after', 'now')
        if variant == 'opposed_successes': return not polarity and point in ('after', 'now')
        if variant == 'all_selected': return polarity
        return False
    values.update(hzzb=lambda pattern, point: pattern == 'reference' and point in ('after', 'now'),
        hzie=lambda factor, prop, target, result, point: variant != 'no_internal_cause' and (
            factor, symbol(prop), target, symbol(result)) == ('reference', 'r2cr', 'person', 'bf') and point in ('after', 'now'),
        hzzd=candidates,
        hzzg=lambda target, person, description, anchor, point, candidate: variant != 'empty_selection_comparison' and (
            target, person, symbol(description), anchor) == (
                'process' if variant == 'other_comparison_target' else 'reference', 'person', 'r2cr', 'now'),
        fa=lambda p, judgment, point: p == 'person' and judgment in ('process', 'method'),
        hzzf=choice)
    return values


@lru_cache(None)
def occurrence_checks():
    doc = fixture('r2ct r2cx r2cy', DECLS + ''.join(
        'q[t[k ' + name + '[k zreference[] k zperson[]]][k zanchor[]]].' for name in ('r2ct', 'r2cx', 'r2cy')))
    rows = []
    for active, positive, negative in product((False, True), repeat=3):
        values = source_values(doc)
        values['hzzb'] = lambda pattern, point: active and pattern == 'reference' and point in ('after', 'now')
        values['hzzf'] = lambda judgment, target, description, polarity, point: (positive if polarity else negative) and (
            judgment, target, symbol(description), point) == ('process' if polarity else 'method', 'reference', 'r2cr', 'now')
        actual = evaluate(doc, values, SOURCE_PEOPLE, SOURCE_SCENES, True)
        expected = [active, active and not positive and not negative, active and negative and not positive]
        assert actual == expected, ((active, positive, negative), actual)
        rows.append(dict(active=active, positive=positive, negative=negative, values=actual))
    values = source_values(doc, 'no_internal_cause')
    assert evaluate(doc, values, SOURCE_PEOPLE, SOURCE_SCENES, True) == [False, False, False]
    for name in ('hzzf', 'hzie'):
        values = source_values(doc); values[name] = unknown
        try: evaluate(doc, values, SOURCE_PEOPLE, SOURCE_SCENES, True)
        except ValueError as error: assert 'Unknown' in str(error)
        else: raise AssertionError(name)
    return dict(combinations=rows, no_internal_cause_rejected=True, unknown_inputs_refused=2,
                native_immaturity_and_internal_contribution_executed=True,
                contrary_decision_is_not_a_stopping_capacity_test=True)


@lru_cache(None)
def degree_checks():
    suffix = DECLS + 'r zscale[a] c.'
    for name in VALUES: suffix += 'r z' + name.lower() + '[] a.'
    for name in VALUES:
        suffix += 'q[k r2cz[k zreference[] k zperson[] k zanchor[] k zanchor[] p zscale k z' + name.lower() + '[] k zlow[] k ztop[]]].'
    doc = fixture('r2cz', suffix); rows = []
    for choices in product((False, True), repeat=3):
        selected = {point for point, flag in zip(SOURCE_SCENES, choices) if flag}
        values = source_values(doc)
        values.update({('z' + n.lower()): (lambda n=n: n) for n in VALUES})
        values['hzzf'] = lambda judgment, target, description, polarity, point: polarity and (
            judgment, target, symbol(description)) == ('process', 'reference', 'r2cr') and point in selected
        actual = evaluate(doc, values, SOURCE_PEOPLE, SOURCE_SCENES, True)
        cases = set(SOURCE_SCENES) - selected; successes = cases & {'after', 'now'}
        expected = [bool(cases) and ((degree == 'low') == (not successes)) and
                    ((degree == 'top') == (successes == cases)) for degree in VALUES]
        assert actual == expected, (choices, actual, expected)
        rows.append(dict(selected=sorted(selected), candidates=sorted(cases), values=actual))
    contrasts = {}
    for variant in ('all_selected', 'empty_selection_comparison', 'other_comparison_target', 'selected_successes', 'opposed_successes'):
        values = source_values(doc, variant)
        values.update({('z' + n.lower()): (lambda n=n: n) for n in VALUES})
        actual = evaluate(doc, values, SOURCE_PEOPLE, SOURCE_SCENES, True)
        expected = [True, False, False, False] if variant in ('selected_successes', 'opposed_successes') else [False] * 4
        assert actual == expected, (variant, actual)
        contrasts[variant] = actual
    for name in ('hzzg', 'hzzf', 'hzze'):
        values = source_values(doc); values.update({('z' + n.lower()): (lambda n=n: n) for n in VALUES}); values[name] = unknown
        try: evaluate(doc, values, SOURCE_PEOPLE, SOURCE_SCENES, True)
        except ValueError as error: assert 'Unknown' in str(error)
        else: raise AssertionError(name)
    return dict(selection_subsets=rows, contrasts=contrasts, unknown_inputs_refused=3,
                empty_profile_not_a_disposition=True, intermediate_degrees_not_derived_from_counts=True)


@lru_cache(None)
def source_checks():
    doc = fixture('r2cv r2da', SOURCE_DECLS + ''.join(
        'q[t[k ' + name + '[' + SOURCE_ARGS + ']][k zanchor[]]].' for name in ('r2cv', 'r2da')))
    rows = {}
    for name in ('baseline', 'currently_selected', 'currently_opposed', 'selected_successes', 'opposed_successes',
                 'all_selected', 'empty_selection_comparison', 'other_comparison_target', 'missing_prior', 'ambiguous_prior', 'no_process'):
        actual = evaluate(doc, source_values(doc, name), SOURCE_PEOPLE, SOURCE_SCENES, True)
        old = name not in ('missing_prior', 'ambiguous_prior', 'no_process')
        new = name in ('baseline', 'currently_selected', 'currently_opposed')
        assert actual == [old, new], (name, actual, old, new)
        rows[name] = actual
    values = source_values(doc); values['zmeasured'] = unknown
    try: evaluate(doc, values, SOURCE_PEOPLE, SOURCE_SCENES, True)
    except ValueError as error: assert 'Unknown' in str(error)
    else: raise AssertionError('zmeasured')
    return dict(contrasts=rows, unknown_inputs_refused=1, native_acquisition_cause_and_graded_change_executed=True,
                current_selection_not_required_absent_for_disposition=True, inconsistent_raw_assessments_not_hidden_by_filter=True)


@lru_cache(None)
def quotation_checks():
    doc = fixture('r2da uc', SOURCE_DECLS + 'r znode[] a.q[k uc[k znode[] k zperson[] r[k r2da[' + SOURCE_ARGS + ']] k zanchor[]]].')
    expected = doc['statements'][0]['body']['arguments'][2]['body']; rows = {}
    for variant in ('baseline', 'false_attribution', 'wrong_person', 'wrong_context', 'obsolete_content'):
        values = {e['name']: unknown for e in doc['declarations'] if e['kind'] == 'primitive'}
        wanted = deepcopy(expected)
        if variant == 'obsolete_content': wanted['symbol'] = 'r2cv'
        values.update(zperson=lambda: 'person', znode=lambda: 'process', zanchor=lambda: 'now',
            uc=lambda node, author, content, scene: variant != 'false_attribution' and (node, author, scene) == (
                'process', 'method' if variant == 'wrong_person' else 'person', 'after' if variant == 'wrong_context' else 'now') and json.loads(content.syntax) == wanted)
        actual = evaluate(doc, values, SOURCE_PEOPLE, SOURCE_SCENES)
        assert actual == [variant == 'baseline'], (variant, actual)
        rows[variant] = actual
    return dict(contrasts=rows, world_contents_unknown=True, rank_zero_quote_accepted=True,
                diagnostic_quotation_not_added_to_manuscript=True)


def reading():
    u = next(u for u in read(INVENTORY)['units'] if u['id'] == 'kant-1784:u0010')
    paths = {INDEX, INVENTORY, FULL, BASIS, PARENT, PARENT_BASIS, 'reports/internalized-state-v1.json'}
    return dict(status='unselected_continuation_comparison_interpretation_candidate', reviewer='assistant_review',
        document=FULL, meaning_basis=BASIS, source=dict(unit=u['id'], unit_sha256=u['text_sha256'],
            range=[62, 107], text=u['text'][62:107]), definitions=list(MEANINGS),
        decision='経験に由来する内的な因果的寄与へ、その都度の実践的決定をやり直さなくても働く比較を接続する。現在の一例、事実判断、反対の決定をした一例、停止能力の否定を分け、句全体の完成とはしない。',
        references=[
            dict(url='https://korpora.org/Kant/aa07/149.html', title='Kant, Anthropologie AA VII149', accessed='2026-10-20',
                 use='考えなしの反復と内的な強制を論じつつ、意図的に採用する習慣も認める後年の記述を参照する。1784年の句へ現在の反対意思を必須とせず、今回の比較モデルも唯一の読解とはしない。'),
            dict(url='https://korpora.org/Kant/aa08/036.html', title='Kant, Aufklärung AA VIII036', accessed='2026-10-20',
                 use='本性となった未成熟と、定式・自由な運動・自己の働きかけの文脈を確認する。AA転記であり原版画像の検証ではない。')],
        interpretation_limits=LIMITS, unselected_comparison_composed=True, nature_reference_fully_composed=False,
        whole_sentence_semantically_verified=False, whole_unit_semantically_verified=False, new_verified_sentence_characters=0,
        semantic_equivalence_automatically_proved=False,
        source_sha256={p: digest((ROOT / p).read_bytes()) for p in sorted(paths)})


def build_report():
    results = {}
    for name, fn in [('selection', selection_checks), ('occurrence', occurrence_checks), ('degree', degree_checks),
                     ('source', source_checks), ('quotation', quotation_checks), ('structure', structure_checks)]:
        results[name] = fn(); print(name + ' checked', flush=True)
    r = reading()
    paths = set(build()) | set(catalog().source_sha256) | set(r['source_sha256']) | {
        AUDIT, DOC, 'scripts/compose_unselected_continuation.py', 'scripts/check_unselected_continuation.py', 'scripts/register_unselected_continuation.py',
        'tests/test_unselected_continuation.py', 'scripts/check_internalized_state.py', 'scripts/compose_internalized_state.py',
        'scripts/check_graded_change.py', 'scripts/compose_graded_change.py', 'scripts/compose_limits.py',
        'scripts/check_pastoral_roles.py', 'scripts/check_motive_causes.py', 'scripts/compose_grounded_step.py',
        'noema/constructed.py', 'noema/constructed_semantics.py', 'noema/meaning_catalog.py', 'noema/semantic_reviews.py', 'noema/script.py'}
    return dict(status='unselected_continuation_and_contrary_decision_comparison_checked', document=FULL, **results,
        alignment=dict(**r['source'], definitions=list(MEANINGS), status='explicit_interpretive_annotation'),
        unselected_comparison_composed=True, nature_reference_fully_composed=False, whole_sentence_semantically_verified=False,
        new_verified_sentence_characters=0, new_covered_characters=0,
        verified_full_units={'kant-1784': 0, 'einstein-1905': 0}, semantic_equivalence_automatically_proved=False,
        source_sha256={p: digest((ROOT / p).read_bytes()) for p in sorted(paths)})


if __name__ == '__main__':
    from scripts.audit_opening_scope import write_exact, encoded
    prepare()
    write_exact(ROOT / REPORT, encoded(build_report()))
