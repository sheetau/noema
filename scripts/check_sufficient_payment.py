"""Distinguish paying part of a price from being able to cover the work."""
from copy import deepcopy
from fractions import Fraction
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog, _references
from noema.semantic_reviews import digest, selection_binding, validate_hashes
from noema.script import transcribe
from scripts.compose_sufficient_payment import ROOT, FULL, CORE, LIBRARY, BASIS, ANNOTATIONS, PARENT, PARENT_BASIS, PRIMITIVES, parent, build, closure
from scripts.check_conditional_forecast import source_values as previous_values
from scripts.check_payment_expectation import PEOPLE, SCENES, alignment
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown, symbol
from scripts.check_designation_order import substantive
from scripts.fetch_sufficient_payment_evidence import PATH as EVIDENCE, validate

INDEX = 'data/semantic-review-index-v59.json'
REPORT = 'reports/sufficient-payment-v1.json'
AUDIT = 'data/sufficient-payment-reading-v1.json'
DOC = 'docs/sufficient-payment-v1.md'


def generic_checks():
    doc = parse((ROOT / LIBRARY).read_text(encoding='utf-8') + '''
r jp[] a.r jr[] a.r jt[] a.r js[] d.r ju[a d] c.
r jc[a a a i[h[a] e] d] b.r jn[a a i[h[a] e] d] b.r jl[b b] c.
d jwork[person a] e[b scene[k ju[v person v scene]]].
q[k rqxz[k jp[] k jr[] k jt[] r[p jwork] k js[] p jc p jn p jl]].''')
    def values(credit, required, variant='baseline'):
        credit_key = ['transfer', 'payer', 'receiver', 'jwork', 'now']
        required_key = ['payer', 'receiver', 'jwork', 'now']
        for prefix, key, fields in [('credit', credit_key, ('transfer', 'payer', 'receiver', 'task', 'scene')),
                ('required', required_key, ('payer', 'receiver', 'task', 'scene'))]:
            for i, field in enumerate(fields):
                if variant == prefix + '_' + field: key[i] = 'other'
        return dict(jp=lambda: 'payer', jr=lambda: 'receiver', jt=lambda: 'transfer', js=lambda: 'now', ju=unknown,
            jc=lambda t, p, r, d, s: credit if (t, p, r, symbol(d), s) == tuple(credit_key) else Fraction(0),
            jn=lambda p, r, d, s: required if (p, r, symbol(d), s) == tuple(required_key) else Fraction(0), jl=lambda a, b: a < b)
    domain = ('payer', 'receiver', 'transfer', 'other'); scenes = ('now', 'other')
    amounts = tuple(map(Fraction, (-1, 0, '1/2', 1, 2, 3)))
    rows = []
    for credited, required in product(amounts, repeat=2):
        actual = evaluate(doc, values(credited, required), domain, scenes)[0]
        assert actual == (required > 0 and credited >= required)
        rows.append(dict(credited=str(credited), required=str(required), value=actual))
    bindings = {}
    for variant in ('baseline', 'credit_transfer', 'credit_payer', 'credit_receiver', 'credit_task', 'credit_scene',
            'required_payer', 'required_receiver', 'required_task', 'required_scene'):
        actual = evaluate(doc, values(Fraction(2), Fraction(2), variant), domain, scenes)[0]
        assert actual == (variant == 'baseline'); bindings[variant] = actual
    # Rescaling a common unit preserves the relation. No fixed currency or amount
    # appears in the production definition; fractional boundaries are exact.
    scales = []
    for factor in (Fraction(1, 100), Fraction(3, 2), Fraction(100)):
        result = [evaluate(doc, values(v * factor, Fraction(2) * factor), domain, scenes)[0]
            for v in (Fraction(1), Fraction(2), Fraction(3))]
        assert result == [False, True, True]; scales.append(result)
    for name in ('jc', 'jn', 'jl'):
        v = values(Fraction(2), Fraction(2)); v[name] = unknown
        try: evaluate(doc, v, domain, scenes)
        except ValueError as e: assert 'Unknown' in str(e)
        else: raise AssertionError(name)
    return dict(amount_combinations=rows, bindings=bindings, common_rescaling=scales,
        unknown_inputs_refused=3, ordinary_evaluation=True, quoted_work_not_executed=True)


@lru_cache(None)
def questions(previous=False):
    c = parent() if previous else load_catalog(ROOT, BASIS)
    d = deepcopy(c.document); d.update(declarations=closure(d, ['tp', 'tq', 't2', 't3', 'wh']), statements=[])
    return parse(format_graph(d, 'compact') + 'r jperson[] a.' + ''.join(
        'q[t[k ' + n + '[k jperson[]]][k wh[]]].' for n in ('tp', 'tq', 't2', 't3')))


def source_values(variant='baseline'):
    base = variant if variant in (
        'baseline', 'already_paid', 'no_method', 'empty_results', 'no_transfer', 'gift', 'failed_goal',
        'thinking_required', 'empty_cases', 'self_takes_over', 'artifact_takes_over', 'wrong_beneficiary',
        'not_unpleasant', 'empty_forecast', 'wrong_forecast_description', 'not_future',
        'unable_and_no_forecast', 'hypothetical_anchor', 'wrong_forecast_anchor') else 'baseline'
    v = previous_values(base)
    credit = Fraction({'partial': '1/2', 'partial_no_forecast': '1/2', 'excess': '3', 'negative_credit': '-1',
        'no_charge': '0', 'negative_charge': '0'}.get(variant, '2'))
    required = Fraction({'no_charge': '0', 'negative_charge': '-1'}.get(variant, '2'))
    credit_key = ['transfer', 'person', 'worker', 'bm', 'paid']
    required_key = ['person', 'worker', 'bm', 'paid']
    for prefix, key, fields in [('credit', credit_key, ('transfer', 'payer', 'receiver', 'task', 'scene')),
            ('required', required_key, ('payer', 'receiver', 'task', 'scene'))]:
        for i, field in enumerate(fields):
            if variant == prefix + '_' + field: key[i] = 'other'
    payment_scene = lambda s: 'paid' if variant == 'already_paid' and s == 'now' else s
    v.update(hzxj=lambda t, p, r, d, s: credit if (t, p, r, symbol(d), payment_scene(s)) == tuple(credit_key) else Fraction(0),
        hzxk=lambda p, r, d, s: required if (p, r, symbol(d), payment_scene(s)) == tuple(required_key) else Fraction(0),
        hc=lambda a, b: a < b)
    if variant == 'partial_no_forecast': v['tw'] = lambda *args: False
    return v


def source_checks():
    prior_report = json.loads((ROOT / 'reports/conditional-forecast-v1.json').read_text(encoding='utf-8'))
    old_rows = prior_report['source']['contrasts']; rows = {}
    for variant, row in old_rows.items():
        scenes = (*SCENES, 'hyp') if 'anchor' in variant else SCENES
        actual = evaluate(questions(), source_values(variant), PEOPLE, scenes, True)
        assert actual == row['current'], (variant, actual, row)
        rows[variant] = actual
    for variant in ('partial', 'partial_no_forecast', 'excess', 'negative_credit', 'no_charge', 'negative_charge',
            'credit_transfer', 'credit_payer', 'credit_receiver', 'credit_task', 'credit_scene',
            'required_payer', 'required_receiver', 'required_task', 'required_scene'):
        actual = evaluate(questions(), source_values(variant), PEOPLE, SCENES, True)
        expected = [variant == 'excess', True, variant != 'partial_no_forecast', True]
        assert actual == expected, (variant, actual)
        rows[variant] = actual
    countermodels = {}
    for variant in ('baseline', 'partial', 'partial_no_forecast'):
        old = evaluate(questions(True), source_values(variant), PEOPLE, SCENES, True)
        assert old == [True, True, variant != 'partial_no_forecast', variant != 'partial_no_forecast']
        countermodels[variant] = dict(previous=old, current=rows[variant])
    for variant in ('baseline', 'partial_no_forecast', 'hypothetical_anchor'):
        scenes = (*SCENES, 'hyp') if 'anchor' in variant else SCENES
        assert evaluate(questions(), source_values(variant), PEOPLE, scenes) == rows[variant]
    for name in ('hzxj', 'hzxk', 'hc', 's2', 'ae', 'tw', 'tu', 'tx', 'ts'):
        v = source_values(); v[name] = unknown
        try: evaluate(questions(), v, PEOPLE, SCENES, True)
        except ValueError as e: assert 'Unknown' in str(e)
        else: raise AssertionError(name)
    d = deepcopy(questions()); d['statements'] = []
    d = parse(format_graph(d, 'compact') + 'q[t[k to[k jperson[]]][k wh[]]].q[t[k tp[k jperson[]]][k wh[]]].')
    paid = {}
    for variant, expected in [('baseline', [False, True]), ('already_paid', [True, True]), ('no_method', [False, False])]:
        actual = evaluate(d, source_values(variant), PEOPLE, SCENES, True)
        assert actual == expected; paid[variant] = actual
    return dict(contrasts=rows, countermodels=countermodels, current_definitions_executed=True,
        ordinary_comparisons=3, unknown_inputs_refused=9, pure_memoization=True,
        paid_and_ability=paid, false_premise_not_counted_as_ability=True)


def outcome_checks():
    rows = {}
    for variant in ('both_sufficient', 'one_partial', 'outside_partial', 'separate_methods', 'only_partial'):
        v = source_values(); paths = {('plan', 'paid'), ('plan', 'partial')}
        if variant == 'separate_methods': paths = {('plan', 'paid'), ('alternate', 'partial')}
        if variant == 'only_partial': paths = {('plan', 'partial')}
        v.update(ae=lambda p, m, s: p == 'person' and s == 'now' and any(m == a for a, b in paths),
            af=lambda p, m, s, e: (p, s) == ('person', 'now') and (m, e) in paths,
            ap=lambda p, m, s, e: (p, s) == ('person', 'now') and (m, e) in paths and not (variant == 'outside_partial' and e == 'partial'),
            ti=lambda t, p, r, m, s: (t, p, r, m) == ('transfer', 'person', 'worker', 'medium') and s in ('paid', 'partial'),
            hzxj=lambda t, p, r, d, s: Fraction(2 if s == 'paid' or variant == 'both_sufficient' else 1)
                if (t, p, r, symbol(d)) == ('transfer', 'person', 'worker', 'bm') else Fraction(0),
            hzxk=lambda p, r, d, s: Fraction(2) if (p, r, symbol(d)) == ('person', 'worker', 'bm') else Fraction(0))
        actual = evaluate(questions(), v, (*PEOPLE, 'alternate'), (*SCENES, 'partial'), True)
        expected_capacity = variant in ('both_sufficient', 'outside_partial', 'separate_methods')
        assert actual[0] == expected_capacity, (variant, actual)
        rows[variant] = actual
    return dict(contrasts=rows, all_selected_results_of_same_method_checked=True)


def attribution_checks():
    doc = parse((ROOT / CORE).read_text(encoding='utf-8')); rows = {}
    for variant in ('baseline', 'other_author', 'other_node', 'other_description', 'other_context', 'reverse_order'):
        v = {d['name']: unknown for d in doc['declarations'] if d['kind'] == 'primitive'}
        v.update(t4=lambda: 'payment', s3=lambda: 'examples', wa=lambda: 'author', wh=lambda: 'text',
            s4=lambda n, a, t, c: (n, a, symbol(t), c) == ('other' if variant == 'other_node' else 'payment',
                'other' if variant == 'other_author' else 'author', 'tr' if variant == 'other_description' else 't3',
                'other' if variant == 'other_context' else 'text'),
            ue=lambda a, b, c: (a, b, c) == (('payment', 'examples', 'text') if variant == 'reverse_order' else ('examples', 'payment', 'text')))
        actual = evaluate(doc, v, ('payment', 'examples', 'author', 'other'), ('text',))
        assert actual == [variant == 'baseline']; rows[variant] = actual
    return dict(contrasts=rows, prices_and_payment_facts_unknown=True)


def structure():
    old, new = parent(), load_catalog(ROOT, BASIS)
    assert old.document['statements'] == new.document['statements'] and len(new.document['statements']) == 43
    assert set(new.entries) - set(old.entries) == set(PRIMITIVES) | {'rqxz', 'rqya'}
    assert [n for n in old.entries if old.entries[n]['declaration'] != new.entries[n]['declaration']] == ['to']
    assert all(substantive(old.entries[n]) == substantive(new.entries[n]) for n in old.entries if n != 'to')
    assert [d['name'] for d in old.document['declarations']] == [d['name'] for d in new.document['declarations'] if d['name'] in old.entries]
    saved = deepcopy(old.entries['to']['declaration']); saved['name'] = 'rqya'
    assert saved == new.entries['rqya']['declaration']
    affected = [i for i, s in enumerate(new.document['statements']) if 'to' in {d['name'] for d in closure(new.document, _references(s))}]
    assert affected == [5]
    index = json.loads((ROOT / INDEX).read_text(encoding='utf-8'))
    for path in index['works']['kant-1784']['reviews']:
        review = json.loads((ROOT / path).read_text(encoding='utf-8')); ids = [s['index'] for s in review['selection']['statements']]
        a, b = selection_binding(old, ids), selection_binding(new, ids)
        assert a == review['selection'] and a['statements'] == b['statements'] and a['dependencies'] == b['dependencies']
        assert all(substantive(old.entries[n]) == substantive(new.entries[n]) for n in a['dependencies'])
    for ids in ([2, 3], [4, 42], [6]):
        a, b = selection_binding(old, ids), selection_binding(new, ids)
        assert a['statements'] == b['statements'] and a['dependencies'] == b['dependencies']
        assert all(substantive(old.entries[n]) == substantive(new.entries[n]) for n in a['dependencies'])
    for path, text in build().items(): assert (ROOT / path).read_text(encoding='utf-8') == text
    for path in (FULL, CORE, LIBRARY):
        d = parse((ROOT / path).read_text(encoding='utf-8'))
        for style in ('full', 'compact'):
            text = format_graph(d, style); assert parse(text) == parse(transcribe(text, alphabet='v2')) == d
    validate(json.loads((ROOT / EVIDENCE).read_text(encoding='utf-8')))
    return dict(preserved_statements=43, changed_definitions=['to'], affected_statements=affected,
        new_primitives=2, new_definitions=2, preserved_review_meanings=11,
        earlier_sentence_meanings_preserved=True, roundtrips=True)


def audit():
    a = alignment()
    paths = (PARENT, PARENT_BASIS, INDEX, EVIDENCE, 'artifacts/written-units-v1/kant-1784.json',
        'artifacts/first-cause-reading-v1/page-482.jpg', 'data/conditional-forecast-reading-v1.json',
        'reports/conditional-forecast-v1.json', 'docs/payment-expectation-v1.md')
    return dict(status='sufficient_consideration_connected_not_whole_sentence_review', reviewer='assistant_review',
        source=dict(unit=a['unit'], unit_sha256=a['unit_sha256'], range=[a['start'], a['end']], text=a['source']),
        reading='bezahlen kannを、その仕事を賄うのに必要な対価を支払えるという読みで具体化する。任意の一部を払えるだけとは分ける。',
        historical_evidence='歴史辞典は単なる出金、物の価値への償い、受領した物の価値を支払う負担を分ける。第三の用法には支払えないという絶対用法がある。これだけでカントの意図が一意に証明されるとはしない。',
        counterexample='旧toでは仕事の対価として一部を渡せるだけでtpが成立した。新toは同じ移転・本人・受け手・仕事の算入額と必要額を比較する。',
        decisions=['共通の比較定義を作り、具体的な値は本文へ埋め込まない。',
            '支払いの生起、媒体の受容、対価への結合はrfに残し、数量だけで支払いにしない。',
            '必要額を支払後の残高へ読み替えない。無償や部分払いの表現能力は旧定義を保存して残す。',
            '条件文が空虚に真になる場合と、支払能力がある場合を別の照会で区別する。'],
        remaining=['同一尺度の対価額という基本関係をさらに構成すること、非数量的な支払条件の扱い',
            '支払いの文全体の語義・nurとschonの働きの通し確認', '第二段落と二作品全文'],
        whole_unit_semantically_verified=False, whole_sentence_semantically_verified=False,
        semantic_equivalence_automatically_proved=False,
        source_sha256={p: digest((ROOT / p).read_bytes()) for p in paths})


def build_report():
    results = {}
    for name, fn in [('generic', generic_checks), ('source', source_checks), ('outcomes', outcome_checks),
            ('attribution', attribution_checks), ('structure', structure)]:
        results[name] = fn(); print(name + ' checked', flush=True)
    reading = audit(); assert json.loads((ROOT / AUDIT).read_text(encoding='utf-8')) == reading
    validate_hashes(ROOT, reading['source_sha256'])
    paths = set(build()) | set(parent().source_sha256) | set(reading['source_sha256']) | {AUDIT, DOC,
        'scripts/compose_sufficient_payment.py', 'scripts/check_sufficient_payment.py', 'scripts/register_sufficient_payment.py',
        'tests/test_sufficient_payment.py', 'scripts/fetch_sufficient_payment_evidence.py', 'scripts/fetch_pastoral_role_evidence.py',
        'scripts/check_conditional_forecast.py', 'scripts/compose_conditional_forecast.py', 'scripts/check_payment_expectation.py',
        'scripts/compose_payment_expectation.py', 'scripts/check_pastoral_roles.py', 'scripts/check_motive_causes.py',
        'scripts/check_designation_order.py', 'scripts/compose_falling_depiction.py', 'noema/constructed.py',
        'noema/constructed_discourse.py', 'noema/constructed_semantics.py', 'noema/meaning_catalog.py', 'noema/semantic_reviews.py', 'noema/script.py'}
    return dict(status='payment_amount_sufficiency_distinguished_from_partial_consideration', document=FULL, **results,
        alignment=dict(**reading['source'], definitions=['rqxz', 'rqya', 'to', 'tp'], status='explicit_interpretive_annotation'),
        new_covered_characters=0, verified_full_units={'kant-1784': 0, 'einstein-1905': 0},
        source_sha256={p: digest((ROOT / p).read_bytes()) for p in sorted(paths)})


def main():
    from scripts.audit_opening_scope import write_exact, encoded
    write_exact(ROOT / AUDIT, encoded(audit())); write_exact(ROOT / REPORT, encoded(build_report()))


if __name__ == '__main__':
    main()
