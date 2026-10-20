"""Execute motives, oppression, both severed ties and a causal-result slot."""
from copy import deepcopy
from functools import lru_cache
import json

from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog
from noema.review_registry import load_reviews
from noema.semantic_reviews import digest, selection_binding, validate_hashes
from noema.script import transcribe
from scripts.compose_political_withdrawal import (
    ROOT, FULL, CORE, BASIS, ANNOTATIONS, PRIMITIVES, MEANINGS, LIMITS, parent, build, closure)
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown, symbol
from scripts.check_public_slow_attainment import REVIEWS as PREVIOUS_REVIEWS

INDEX = 'data/semantic-review-index-v136.json'
AUDIT = 'data/political-withdrawal-reading-v1.json'
REPORT = 'reports/political-withdrawal-v1.json'
DOC = 'docs/political-withdrawal-v1.md'
INVENTORY = 'artifacts/written-units-v1/kant-1784.json'
PRIOR = 'reports/public-slow-attainment-v1.json'
REVIEWS = PREVIOUS_REVIEWS + [('data/public-slow-attainment-reading-v1.json', [60])]
PEOPLE = ('target', 'ruler', 'oppressor', 'despotic', 'oppressive', 'pressure', 'process', 'event', 'other')
SCENES = ('before', 'after')
EXTRA = '''
r ztarget[] a.r zruler[] a.r zdespotic[] a.r zoppressor[] a.r zoppressive[] a.
r zpressure[] a.r zprocess[] a.r zfirst[] d.r zlast[] d.
r zhistory[d] c.r zbefore[d d] c.r zkind[a] c.r zcandidate[a d d] c.
'''
ARGS = '''k ztarget[] k zruler[] k zdespotic[] k zoppressor[] k zoppressive[] k zpressure[]
k zprocess[] k zfirst[] k zlast[] p zhistory p zbefore'''
RESULT = '''
d zresult[target a] e[b point[k r2qe[v target k zruler[] k zdespotic[] k zoppressor[]
k zoppressive[] k zpressure[] k zprocess[] k zfirst[] v point p zhistory p zbefore]]].
'''


def read(path):
    return json.loads((ROOT / path).read_text(encoding='utf-8'))


@lru_cache(None)
def catalog():
    return load_catalog(ROOT, BASIS)


@lru_cache(None)
def fixture(kind):
    roots = {'withdrawal': ['r2qe'], 'pressure': ['r2qc'], 'harm': ['r2qb', 'rqqu', 'r2pb', 'r2od'],
             'candidate': ['rqc', 'r2qe', 'g3'], 'quotation': ['hznreport', 'r2qe']}[kind]
    doc = deepcopy(catalog().document)
    doc.update(declarations=closure(doc, roots), statements=[])
    question = {
        'withdrawal': 'q[k r2qe[' + ARGS + ']].',
        'pressure': 'q[k r2qc[k zoppressor[] k ztarget[] k zpressure[] k zoppressive[] k zfirst[]]].',
        'harm': 'q[k r2qb[k zpressure[] k ztarget[] k zfirst[]]].'
                'q[w[k h226k[k zpressure[] k ztarget[] k zfirst[]]]['
                'k rqqu[k zpressure[] r[p r2pb] k ztarget[] r[p r2od] k zfirst[]]]].',
        'candidate': RESULT + 'q[k rqc[k ztarget[] p zkind r[p zresult] k zfirst[] p zcandidate p dg p g3]].',
        'quotation': RESULT + 'r znode[] a.r zauthor[] a.'
                     'q[k hznreport[k znode[] k zauthor[] r d[k zresult[k ztarget[]]] k znode[] k zlast[]]].',
    }[kind]
    return parse(format_graph(doc, 'compact') + EXTRA + question)


def model(doc, variant='baseline'):
    values = {d['name']: unknown for d in doc['declarations'] if d['kind'] == 'primitive'}
    values.update({n: (lambda value=value: value) for n, value in
                   [('ztarget', 'target'), ('zruler', 'ruler'), ('zdespotic', 'despotic'),
                    ('zoppressor', 'oppressor'), ('zoppressive', 'despotic' if variant == 'same_order' else 'oppressive'),
                    ('zpressure', 'pressure'), ('zprocess', 'process'), ('zfirst', 'before'), ('zlast', 'after')]})
    oppressive = values['zoppressive']()
    kinds = {'r2pz'} if variant in ('power_only', 'other_order') else {'r2py', 'r2pz'} if variant == 'both_motives' else {'r2py'}
    def tied_goal(actor, goal, roles, point, role):
        name = symbol(goal)
        selected = set(kinds)
        if variant == 'disjoint_excess' and role == 'excess':
            selected = {'r2pz'}
        if variant == 'disjoint_purpose' and role == 'purpose':
            selected = {'r2pz'}
        if variant == 'other_order' and name == 'r2pz':
            wanted = ('oppressor', 'other')
        else:
            wanted = ('oppressor',) if name == 'r2py' else ('oppressor', oppressive)
        return (actor, point) == ('oppressor', 'before') and name in selected and roles.items == wanted
    def subjection(order, target, point):
        if target != 'target' or order not in ('despotic', oppressive):
            return False
        if point == 'before':
            return not (variant == 'no_prior_despotism' and order == 'despotic') and \
                not (variant == 'no_prior_oppression' and order == oppressive)
        return variant == 'declassification_only' or \
            variant == 'still_despotism' and order == 'despotic' or \
            variant == 'still_oppression' and order == oppressive
    values.update(
        aa=lambda person: person in ('target', 'ruler', 'oppressor') and
            not (variant == 'nonhuman_ruler' and person == 'ruler'),
        h226i=lambda holder, order, point: (holder, order, point) == ('ruler', 'despotic', 'before')
            and variant != 'no_control',
        h226j=lambda holder, order, point: (holder, order, point) == ('ruler', 'despotic', 'before')
            and variant != 'constrained_rule',
        h226k=lambda act, target, point: (act, target, point) == ('pressure', 'target', 'before')
            and variant != 'no_imposed_constraint',
        h226m=lambda actor, goal, roles, point: variant != 'no_excess' and tied_goal(actor, goal, roles, point, 'excess'),
        h226n=subjection,
        h226o=lambda process, order, target, first, last:
            (process, target, first, last) == ('process', 'target', 'before', 'after')
            and order in ('despotic', oppressive) and variant != 'no_severing'
            and not (variant == 'only_one_severed' and order == oppressive),
        h226p=lambda act, order, point: (act, order, point) == ('pressure', oppressive, 'before')
            and variant != 'unrelated_order_action',
        hzxq=lambda actor, goal, roles, point: variant != 'no_desire' and tied_goal(actor, goal, roles, point, 'desire'),
        hztl=lambda actor, act, goal, roles, point: act == 'pressure' and variant != 'no_purpose'
            and tied_goal(actor, goal, roles, point, 'purpose'),
        dg=lambda act, point: (act, point) in (('pressure', 'before'), ('event', 'after')) and
            not (variant == 'no_pressure_occurrence' and act == 'pressure') and
            not (variant == 'no_event_occurrence' and act == 'event'),
        df=lambda actor, act, point:
            (actor, act, point) == ('oppressor', 'pressure', 'before') and variant != 'no_oppressor_participation' or
            (actor, act, point) == ('target', 'process', 'after') and variant != 'passive_target',
        ur=lambda person, point: (person, point) == ('target', 'before') and variant != 'no_harm',
        hzie=lambda factor, fdesc, target, edesc, point:
            (factor, target, point) == ('pressure', 'target', 'before') and
            (symbol(fdesc), symbol(edesc)) == ('r2pb', 'r2od') and variant != 'no_harm_cause',
        zhistory=lambda point: point in SCENES and not (variant == 'missing_endpoint' and point == 'after'),
        zbefore=lambda first, last: (first, last) ==
            (('after', 'before') if variant == 'reverse_time' else ('before', 'after')),
        ag=lambda process, first, last: (process, first, last) == ('process', 'before', 'after')
            and variant != 'no_process',
        la=lambda target, process, first, last: (target, process, first, last) ==
            ('target', 'process', 'before', 'after') and variant != 'unrelated_target',
        zkind=lambda act: act == 'event',
        zcandidate=lambda act, reference, result: (act, reference, result) == ('event', 'before', 'after')
            and variant != 'wrong_candidate',
        g3=lambda act, target, result, point: (act, target, point) == ('event', 'target', 'after')
            and symbol(result) == 'zresult' and variant != 'no_result_cause',
    )
    return values


@lru_cache(None)
def motive_checks():
    doc = fixture('pressure')
    variants = ('baseline', 'power_only', 'both_motives', 'other_order', 'no_desire', 'no_excess', 'no_purpose',
                'disjoint_excess', 'disjoint_purpose', 'no_imposed_constraint', 'no_harm',
                'no_harm_cause', 'no_pressure_occurrence', 'no_oppressor_participation', 'unrelated_order_action')
    rows = {}
    for variant in variants:
        values = model(doc, variant)
        actual = evaluate(doc, values, PEOPLE, SCENES, True)
        assert actual == [variant in ('baseline', 'power_only', 'both_motives')], (variant, actual)
        rows[variant] = actual
    for primitive in ('h226m', 'hzxq', 'hztl', 'h226k', 'hzie'):
        values = model(doc); values[primitive] = unknown
        try:
            evaluate(doc, values, PEOPLE, SCENES, True)
        except ValueError as error:
            assert 'Unknown' in str(error)
        else:
            raise AssertionError(primitive)
    return dict(contrasts=rows, motive_goal_never_executed=True,
                desire_excess_and_purpose_must_share_goal_and_actor=True,
                oppression_requires_actual_harm_and_cause=True, unknown_inputs_refused=5)


@lru_cache(None)
def withdrawal_checks():
    doc = fixture('withdrawal')
    variants = ('baseline', 'same_order', 'power_only', 'no_control', 'constrained_rule', 'nonhuman_ruler',
                'no_prior_despotism', 'no_prior_oppression', 'still_despotism', 'still_oppression',
                'declassification_only', 'passive_target', 'no_severing', 'only_one_severed',
                'no_process', 'unrelated_target', 'reverse_time', 'missing_endpoint')
    rows = {}
    for variant in variants:
        actual = evaluate(doc, model(doc, variant), PEOPLE, SCENES, True)
        assert actual == [variant in ('baseline', 'same_order', 'power_only')], (variant, actual)
        rows[variant] = actual
    return dict(contrasts=rows, both_original_ties_end=True,
                same_or_different_orders_allowed=True, native_rcf_and_motives_executed=True,
                declassification_without_withdrawal_refused=True)


@lru_cache(None)
def candidate_checks():
    direct = fixture('harm')
    for variant in ('baseline', 'no_imposed_constraint', 'no_harm', 'no_harm_cause', 'no_pressure_occurrence'):
        actual = evaluate(direct, model(direct, variant), PEOPLE, SCENES, True)
        assert actual == [variant == 'baseline'] * 2, (variant, actual)
    doc = fixture('candidate')
    rows = {}
    for variant in ('baseline', 'no_result_cause', 'no_event_occurrence', 'wrong_candidate',
                    'still_oppression', 'no_process'):
        actual = evaluate(doc, model(doc, variant), PEOPLE, SCENES, True)
        assert actual == [variant == 'baseline'], (variant, actual)
        rows[variant] = actual
    quoted = fixture('quotation')
    values = {d['name']: unknown for d in quoted['declarations'] if d['kind'] == 'primitive'}
    values.update(ztarget=lambda: 'target', znode=lambda: 'node', zauthor=lambda: 'author', zlast=lambda: 'after',
                  hznreport=lambda n, a, claim, s, r:
                      (n, a, s, r) == ('node', 'author', 'node', 'after') and claim.rank == 3)
    assert evaluate(quoted, values, ('target', 'node', 'author'), SCENES, True) == [True]
    return dict(contrasts=rows, native_rqc_result_slot_accepts_closed_rank_zero_function=True,
                closed_harm_expansion_agrees_with_native_rqqu=True,
                activity_kind_is_test_parameter_not_yet_revolution=True,
                quoted_attribution_does_not_execute_world=True)


def reading():
    unit = next(u for u in read(INVENTORY)['units'] if u['id'] == 'kant-1784:u0011')
    return dict(status='political_withdrawal_result_partial', document=FULL, meaning_basis=BASIS,
                source=dict(unit=unit['id'], unit_sha256=unit['text_sha256'],
                            range=[950, 1040], text=unit['text'][950:1040]),
                interpretation=LIMITS, definitions=list(MEANINGS),
                lexical=[
                    dict(url='https://www.duden.de/rechtschreibung/Abfall', sense=2, role='active_political_severance'),
                    dict(url='https://www.duden.de/rechtschreibung/Despotismus', role='unrestricted_rule_auxiliary'),
                    dict(url='https://www.duden.de/rechtschreibung/gewinnsuechtig', role='excessive_material_gain_motive'),
                    dict(url='https://www.duden.de/rechtschreibung/herrschsuechtig', role='excessive_control_motive'),
                ],
                whole_sentence_semantically_verified=False, newly_reviewed_sentence_characters=0,
                preserved_first_four_sentence_characters=771,
                unresolved=['革命の活動種類', '公衆と結果対象範囲', '思考様式の真の改革',
                            '候補・様相・対比・著者帰属', '新旧の偏見と導く描写', '第五文と段落の通読'],
                source_sha256={p: digest((ROOT / p).read_bytes()) for p in (FULL, BASIS, DOC, INVENTORY, PRIOR)})


@lru_cache(None)
def structure_checks():
    old, new = parent(), catalog()
    assert new.document['statements'] == old.document['statements'] and len(new.document['statements']) == 61
    assert all(new.entries[n] == e for n, e in old.entries.items())
    reviews = load_reviews(ROOT, INDEX)['works']['kant-1784']
    for row in reviews:
        assert row['selection'] == selection_binding(new, [s['index'] for s in row['selection']['statements']])
    for path, indices in REVIEWS:
        record = read(path)
        assert record['selection'] == selection_binding(new, indices)
        validate_hashes(ROOT, record['source_sha256'])
    validate_hashes(ROOT, read(PRIOR)['source_sha256'])
    assert read(AUDIT) == reading()
    for path, body in build().items():
        assert (ROOT / path).read_text(encoding='utf-8') == body
    for path in (FULL, CORE):
        doc = parse((ROOT / path).read_text(encoding='utf-8'))
        for notation in ('compact', 'full'):
            text = format_graph(doc, notation)
            assert parse(text) == parse(transcribe(text, alphabet='v2')) == doc
    return dict(preserved_whole_unit_reviews=len(reviews), preserved_sentence_characters=771,
                preserved_statements=61, added_definitions=len(MEANINGS),
                added_basic_relations=len(PRIMITIVES), old_definitions_unchanged=True, roundtrips=True)


def prepare():
    from scripts.audit_opening_scope import write_exact, encoded
    for path, body in build().items():
        write_exact(ROOT / path, body)
    write_exact(ROOT / AUDIT, encoded(reading()))


def build_report():
    results = {}
    for name, fn in [('motives', motive_checks), ('withdrawal', withdrawal_checks),
                     ('candidate', candidate_checks), ('structure', structure_checks)]:
        results[name] = fn()
        print(name + ' checked', flush=True)
    paths = set(build()) | set(catalog().source_sha256) | {
        INDEX, AUDIT, DOC, INVENTORY, PRIOR, *[p for p, _ in REVIEWS],
        'scripts/compose_political_withdrawal.py', 'scripts/check_political_withdrawal.py',
        'tests/test_political_withdrawal.py', 'scripts/check_pastoral_roles.py',
        'scripts/check_motive_causes.py', 'scripts/check_public_slow_attainment.py'}
    return dict(status='political_withdrawal_result_partial', document=FULL, **results,
                alignment=dict(**read(AUDIT)['source'], definitions=list(MEANINGS),
                               status='partial_despotism_motivated_oppression_and_withdrawal'),
                whole_sentence_semantically_verified=False, whole_unit_semantically_verified=False,
                verified_full_units={'kant-1784': 0, 'einstein-1905': 0},
                source_sha256={p: digest((ROOT / p).read_bytes()) for p in sorted(paths)})
