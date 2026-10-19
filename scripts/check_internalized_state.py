"""Finite countermodels for acquired internal contribution, with native capacity."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest, selection_binding, validate_hashes
from noema.script import transcribe
from scripts.compose_internalized_state import ROOT, FULL, CORE, BASIS, ANNOTATIONS, PARENT, PARENT_BASIS, MEANINGS, PRIMITIVES, LIMITS, parent, build, closure
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown, symbol
from scripts.check_graded_change import VALUES, SOURCE_PEOPLE, SOURCE_SCENES, SOURCE_DECLS, SOURCE_ARGS, source_values as prior_values

INDEX = 'data/semantic-review-index-v90.json'
AUDIT = 'data/internalized-state-reading-v1.json'
REPORT = 'reports/internalized-state-v1.json'
DOC = 'docs/internalized-state-v1.md'
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
    assert new.document['declarations'][:-11] == old.document['declarations']
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
    return dict(new_definitions=6, new_primitives=5, preserved_statements=51, new_authored_assertions=0,
        preserved_review_selections=12, reviewed_nonblank_characters=2212, roundtrips=True,
        comparison_dimension_composed=True, lexical_equivalence_not_claimed=True)


def prepare():
    from scripts.audit_opening_scope import write_exact, encoded
    write_exact(ROOT / AUDIT, encoded(reading()))


ORIGIN_DECLS = 'r zperson[] a.r zpattern[] a.r znow[] d.r zpast[] d.'


@lru_cache(None)
def origin_document():
    return fixture('r2cq r2cs r2cr', ORIGIN_DECLS + '''
q[t[k r2cq[k zperson[]]][k zpast[]]].
q[t[k r2cs[k zperson[] k zpattern[]]][k znow[]]].
q[t[k r2cr[k zpattern[]]][k znow[]]].''')


def origin_values(doc, flags=(True, True, True, True), variant='baseline'):
    activity, experience, formation, ownership = flags
    values = {d['name']: unknown for d in doc['declarations'] if d['kind'] == 'primitive'}
    points = SOURCE_SCENES
    values.update(zperson=lambda: 'person', zpattern=lambda: 'reference', znow=lambda: 'now', zpast=lambda: 'before',
        dg=lambda a, s: activity and (a, s) == ('process', 'before'),
        df=lambda p, a, s: (p, a, s) == ('person', 'process', 'before'),
        ad=lambda guide, p, a, s: (guide, p, a, s) == (
            'person' if variant == 'self_guidance' else 'method', 'person',
            'reference' if variant == 'other_activity' else 'process', 'before'),
        h3e=lambda p, e, task, s: experience and (p, e, symbol(task), s) == (
            'method' if variant == 'other_experiencer' else 'person', 'process',
            'bf' if variant == 'state_as_activity' else 'r2cq', 'now' if variant == 'present_experience' else 'before'),
        hzyz=lambda pattern, p, s: ownership and (pattern, p) == (
            'process' if variant == 'other_pattern_owner' else 'reference', 'person'),
        hzzb=lambda p, s: variant != 'dormant' and p == 'reference' and s == 'now',
        hzzc=lambda e, pattern, earlier, point: formation and (e, pattern, earlier, point) == (
            'method' if variant == 'other_experience_cause' else 'process',
            'process' if variant == 'other_formed_pattern' else 'reference',
            'after' if variant == 'other_origin_point' else 'before', 'now'),
        ia=lambda p, anchor, point: p == 'person' and anchor == 'now' and point in points and not (
            variant == 'past_outside_history' and point == 'before'),
        ic=lambda a, b, anchor: anchor == 'now' and (points.index(a) < points.index(b) or (
            variant == 'cyclic_history' and (a, b) == ('now', 'before'))))
    return values


@lru_cache(None)
def origin_checks():
    doc = origin_document(); people = ('person', 'process', 'reference', 'method')
    rows = []
    for bits in product((False, True), repeat=4):
        actual = evaluate(doc, origin_values(doc, bits), people, SOURCE_SCENES, True)
        expected = [bits[0], all(bits), True]
        assert actual == expected, (bits, actual)
        rows.append(dict(bits=list(bits), values=actual))
    contrasts = {}
    for name in ('self_guidance', 'other_activity', 'other_experiencer', 'state_as_activity', 'present_experience',
                 'other_pattern_owner', 'other_experience_cause', 'other_formed_pattern', 'other_origin_point',
                 'past_outside_history', 'cyclic_history', 'dormant'):
        actual = evaluate(doc, origin_values(doc, variant=name), people, SOURCE_SCENES, True)
        assert actual == [name not in ('self_guidance', 'other_activity'), name == 'dormant', name != 'dormant'], (name, actual)
        contrasts[name] = actual
    for name in ('dg', 'df', 'ad', 'h3e', 'hzyz', 'hzzc', 'ia', 'ic', 'hzzb'):
        values = origin_values(doc); values[name] = unknown
        try: evaluate(doc, values, people, SOURCE_SCENES, True)
        except ValueError as error: assert 'Unknown' in str(error)
        else: raise AssertionError(name)
    return dict(combinations=rows, contrasts=contrasts, unknown_inputs_refused=9,
                native_guided_activity_executed=True, dormant_formed_pattern_can_exist=True)


def source_values(doc, variant='baseline'):
    values = prior_values(doc)
    origin = origin_values(doc, variant=variant)
    for name in ('dg', 'df', 'ad', 'h3e', 'hzyz', 'hzzb', 'hzzc', 'ia', 'ic'):
        values[name] = origin[name]
    def opportunity(p, point): return p == 'person' and point == 'before'
    def available(p, method, point): return method == 'method' and opportunity(p, point)
    def result(p, method, point, out): return available(p, method, point) and out == 'now'
    values.update(ae=available, af=result, ap=result,
        hzsc=lambda p, anchor, point: opportunity(p, point), hzsd=lambda p, anchor, point: p == 'person',
        hzse=opportunity, hzsg=lambda p, m, anchor, point: (p, m) == ('person', 'method'),
        hzsh=lambda p, m, anchor, point: p == 'person',
        ac=lambda p, faculty, act, s: variant == 'currently_capable' and (p, faculty, act, s) == ('person', 'faculty', 'process', 'now'))
    def measured(p, description, reference, anchor, point, degree):
        if (p, symbol(description), reference, anchor) != ('person', 'bf', 'reference', 'now'): return False
        assigned = dict(before={'low'}, after={'nearB'}, now={'nearB'})
        if variant == 'missing_prior': assigned['before'] = set()
        if variant == 'ambiguous_prior': assigned['before'] = {'low', 'top'}
        if variant == 'no_increase': assigned['before'] = {'nearB'}
        return degree in assigned[point]
    def candidates(pattern, p, description, anchor, point, candidate):
        identity = (pattern, p, symbol(description), anchor) == ('reference', 'person', 'bf', 'now')
        domain = ('before',) if point == 'before' else ('before', 'now')
        if variant == 'empty_candidates': domain = ()
        if variant == 'all_success_candidates': domain = ('now',)
        return identity and candidate in domain
    values.update(zmeasured=measured, hzzd=candidates,
        hzze=lambda p, description, s: variant == 'renewed_external_support' and (p, symbol(description), s) == ('person', 'bf', 'now'),
        hzie=lambda factor, prop, target, result_prop, s: variant != 'no_internal_cause' and (factor, symbol(prop), target, symbol(result_prop), s) == (
            'process' if variant == 'other_causal_pattern' else 'reference', 'r2cr', 'person', 'bf', 'now'))
    if variant == 'no_process': values['ag'] = lambda *args: False
    if variant == 'wrong_measured_reference':
        values['zmeasured'] = lambda p, d, ref, anchor, point, degree: ref == 'process'
    return values


@lru_cache(None)
def contribution_checks():
    doc = fixture('r2ct', 'r zperson[] a.r zreference[] a.r zanchor[] d.q[t[k r2ct[k zreference[] k zperson[]]][k zanchor[]]].')
    rows = {}
    for name in ('baseline', 'dormant', 'other_pattern_owner', 'no_internal_cause', 'other_causal_pattern', 'currently_capable', 'renewed_external_support'):
        actual = evaluate(doc, source_values(doc, name), SOURCE_PEOPLE, SOURCE_SCENES, True)
        assert actual == [name in ('baseline', 'renewed_external_support')], (name, actual)
        rows[name] = actual
    for name in ('hzie', 'hzsh'):
        values = source_values(doc); values[name] = unknown
        try: evaluate(doc, values, SOURCE_PEOPLE, SOURCE_SCENES, True)
        except ValueError as error: assert 'Unknown' in str(error)
        else: raise AssertionError(name)
    return dict(contrasts=rows, unknown_inputs_refused=2, native_immaturity_and_actual_causal_contribution_executed=True)


@lru_cache(None)
def degree_checks():
    suffix = 'r zperson[] a.r zreference[] a.r zanchor[] d.r zscale[a] c.'
    for name in VALUES: suffix += 'r z' + name.lower() + '[] a.'
    for name in VALUES:
        suffix += 'q[k r2cu[k zreference[] k zperson[] k zanchor[] k zanchor[] p zscale k z' + name.lower() + '[] k zlow[] k ztop[]]].'
    doc = fixture('r2cu', suffix); rows = []
    for bits in product((False, True), repeat=3):
        chosen = {s for s, included in zip(SOURCE_SCENES, bits) if included}
        values = source_values(doc)
        values.update({('z' + name.lower()): (lambda name=name: name) for name in VALUES})
        values['hzzd'] = lambda pattern, p, desc, anchor, point, candidate: (
            pattern, p, symbol(desc), anchor, point) == ('reference', 'person', 'bf', 'now', 'now') and candidate in chosen
        actual = evaluate(doc, values, SOURCE_PEOPLE, SOURCE_SCENES, True)
        # Explicit set oracle: success only in 'now'; no cardinality-to-degree rule.
        successes = chosen & {'now'}
        expected = [bool(chosen) and ((degree == 'low') == (not successes)) and
                    ((degree == 'top') == (successes == chosen)) for degree in VALUES]
        assert actual == expected, (bits, actual, expected)
        rows.append(dict(candidates=sorted(chosen), values=actual))
    for name in ('hzzd', 'hzze'):
        values = source_values(doc); values.update({('z' + n.lower()): (lambda n=n: n) for n in VALUES}); values[name] = unknown
        try: evaluate(doc, values, SOURCE_PEOPLE, SOURCE_SCENES, True)
        except ValueError as error: assert 'Unknown' in str(error)
        else: raise AssertionError(name)
    return dict(candidate_subsets=rows, unknown_inputs_refused=2, intermediate_degrees_not_derived_from_counts=True)


@lru_cache(None)
def source_checks():
    doc = fixture('r2cv', SOURCE_DECLS + 'q[t[k r2cv[' + SOURCE_ARGS + ']][k zanchor[]]].')
    rows = {}
    for name in ('baseline', 'no_internal_cause', 'no_process', 'renewed_external_support', 'empty_candidates',
                 'all_success_candidates', 'missing_prior', 'ambiguous_prior', 'wrong_measured_reference'):
        actual = evaluate(doc, source_values(doc, name), SOURCE_PEOPLE, SOURCE_SCENES, True)
        assert actual == [name == 'baseline'], (name, actual)
        rows[name] = actual
    values = source_values(doc); values['zmeasured'] = unknown
    try: evaluate(doc, values, SOURCE_PEOPLE, SOURCE_SCENES, True)
    except ValueError as error: assert 'Unknown' in str(error)
    else: raise AssertionError('zmeasured')
    return dict(contrasts=rows, unknown_inputs_refused=1, native_composed_origin_cause_degree_and_change_executed=True,
                inconsistent_raw_assessments_not_hidden_by_endpoint_filter=True)


@lru_cache(None)
def quotation_checks():
    doc = fixture('r2cv uc', SOURCE_DECLS + 'r znode[] a.q[k uc[k znode[] k zperson[] r[k r2cv[' + SOURCE_ARGS + ']] k zanchor[]]].')
    expected = doc['statements'][0]['body']['arguments'][2]['body']; rows = {}
    for variant in ('baseline', 'false_attribution', 'wrong_person', 'wrong_context', 'obsolete_content'):
        values = {e['name']: unknown for e in doc['declarations'] if e['kind'] == 'primitive'}
        wanted = deepcopy(expected)
        if variant == 'obsolete_content': wanted['symbol'] = 'r2cp'
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
    paths = {INDEX, INVENTORY, FULL, BASIS, PARENT, PARENT_BASIS, 'reports/graded-change-v1.json'}
    return dict(status='acquired_internal_contribution_comparison_interpretation_candidate', reviewer='assistant_review',
        document=FULL, meaning_basis=BASIS, source=dict(unit=u['id'], unit_sha256=u['text_sha256'],
            range=[62, 107], text=u['text'][62:107]), definitions=list(MEANINGS),
        decision='本性との比較候補を、指導下の経験による形成、現在の内的因果的寄与、外的更新なしの比較、同じ尺度での程度増加と保持へ具体化する。原文の唯一の読解や句全体の完成とはしない。',
        references=[
            dict(url='https://korpora.org/Kant/aa07/149.html', title='Kant, Anthropologie AA VII149', accessed='2026-10-20',
                 use='後年の習慣論にある内的な強制と反復、別の自然への類比を参照する。1784年の語義や今回の反事実的比較を一意に決める証拠とはしない。'),
            dict(url='https://korpora.org/Kant/aa08/036.html', title='Kant, Aufklärung AA VIII036', accessed='2026-10-20',
                 use='対象句と後続の指導・独立した試行・自由な運動への不慣れの文脈を確認する。AA転記であり1784年原版の画像検証とはしない。')],
        interpretation_limits=LIMITS, comparison_dimension_composed=True, nature_reference_fully_composed=False,
        whole_sentence_semantically_verified=False, whole_unit_semantically_verified=False, new_verified_sentence_characters=0,
        semantic_equivalence_automatically_proved=False,
        source_sha256={p: digest((ROOT / p).read_bytes()) for p in sorted(paths)})


def build_report():
    results = {}
    for name, fn in [('origin', origin_checks), ('contribution', contribution_checks), ('degree', degree_checks),
                     ('source', source_checks), ('quotation', quotation_checks), ('structure', structure_checks)]:
        results[name] = fn(); print(name + ' checked', flush=True)
    r = reading()
    paths = set(build()) | set(catalog().source_sha256) | set(r['source_sha256']) | {
        AUDIT, DOC, 'scripts/compose_internalized_state.py', 'scripts/check_internalized_state.py', 'scripts/register_internalized_state.py',
        'tests/test_internalized_state.py', 'scripts/check_graded_change.py', 'scripts/compose_graded_change.py',
        'scripts/compose_limits.py', 'scripts/check_pastoral_roles.py', 'scripts/check_motive_causes.py',
        'scripts/compose_grounded_step.py', 'noema/constructed.py', 'noema/constructed_semantics.py',
        'noema/meaning_catalog.py', 'noema/semantic_reviews.py', 'noema/script.py'}
    return dict(status='acquired_internal_contribution_with_withdrawal_comparison_checked', document=FULL, **results,
        alignment=dict(**r['source'], definitions=list(MEANINGS), status='explicit_interpretive_annotation'),
        comparison_dimension_composed=True, nature_reference_fully_composed=False, whole_sentence_semantically_verified=False,
        new_verified_sentence_characters=0, new_covered_characters=0,
        verified_full_units={'kant-1784': 0, 'einstein-1905': 0}, semantic_equivalence_automatically_proved=False,
        source_sha256={p: digest((ROOT / p).read_bytes()) for p in sorted(paths)})


if __name__ == '__main__':
    from scripts.audit_opening_scope import write_exact, encoded
    prepare()
    write_exact(ROOT / REPORT, encoded(build_report()))
