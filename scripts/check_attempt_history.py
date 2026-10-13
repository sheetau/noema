"""Countermodels for never allowed, never tried, inability and explanations."""
import argparse
import hashlib
from itertools import product
import json

from noema.finite_semantics import evaluate_document
from noema.grammar import format_graph, parse
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from scripts.check_described_appraisals import candidate
from scripts.check_described_explanations import symbol
from scripts.check_rod_setup import guarded
from scripts.compose_attempt_history import ROOT, PARENT, generic_composed, source_composed

REPORT = ROOT / 'reports/attempt-history-v1.json'
DOMAIN = ('person', 'other', 'ability', 'act', 'plan', 'leader')
SCENES = ('old', 'recent', 'now', 'later', 'alternative', 'success')


def values(doc, model, scenes=SCENES):
    return [r['value'] for r in evaluate_document(doc, individuals=DOMAIN, situations=scenes,
        primitives=model, max_steps=5_000_000, memoize_definitions=True, memoize_expressions=True)]


def evidence_checks():
    doc = parse(generic_composed()[0] + '''
r za[d] c.r zb[d] c.r zc[d] c.
q[k rac[p za p zb]].q[k rad[p za p zb p zc]].q[k rae[p za p zb p zc]].
''')
    rows = []
    for chosen, positive, negative in product(product((False, True), repeat=2), repeat=3):
        scene = ('old', 'now')
        model = {key: lambda point, items=items: items[scene.index(point)]
            for key, items in (('za', chosen), ('zb', positive), ('zc', negative))}
        actual = values(doc, model, scene)
        absent = all(not selected or not yes for selected, yes in zip(chosen, positive))
        complete = all(not selected or yes != no for selected, yes, no in zip(chosen, positive, negative))
        if actual != [absent, complete, absent and complete]:
            raise ValueError('Missing or inconsistent evidence became a certified negative')
        rows.append(dict(scope=list(chosen), positive=list(positive), negative=list(negative), results=actual))
    return rows


QUERIES = '''
r za[] a.r zb[] d.
q[t[k h3[k za[]]][k zb[]]].q[t[k h6[k za[]]][k zb[]]].
q[t[k h4[k za[]]][k zb[]]].q[t[k h5[k za[]]][k zb[]]].
'''


def source_model(doc, *, allowed=False, attempted=False, able=False, explanation=True, variant='baseline'):
    model = guarded(doc)
    history = ('old', 'recent', 'now', 'later')
    if variant == 'empty_past':
        history = ('now', 'later')
    if variant == 'missing_anchor':
        history = ('old', 'recent', 'later')

    def ordered(first, second, context):
        if variant == 'reflexive_order' and first == second == 'old':
            return True
        if variant == 'cyclic_order' and (first, second) == ('later', 'old'):
            return True
        return SCENES.index(first) < SCENES.index(second)

    def permission(agent, person, activity, point):
        expected_person = 'other' if variant == 'different_person' else 'person'
        expected_activity = 'bb' if variant == 'different_activity' else 'bm'
        expected_agent = 'other' if variant == 'different_agent' else 'leader'
        expected_point = {'permission_now': 'now', 'permission_future': 'later',
                          'permission_alternative': 'alternative', 'permission_older': 'old'}.get(variant, 'recent')
        return allowed and (agent, person, symbol(activity), point) == (
            expected_agent, expected_person, expected_activity, expected_point)

    def explains(first, factor, second, effect, context):
        expected = ['person', 'h3', 'person', 'h4', 'now']
        wrong = {'wrong_factor_person': 0, 'wrong_factor': 1, 'wrong_effect_person': 2,
                 'wrong_effect': 3, 'wrong_context': 4}
        if variant in wrong:
            expected[wrong[variant]] = 'other'
        return explanation and [first, symbol(factor), second, symbol(effect), context] == expected

    model.update(za=lambda: 'person', zb=lambda: 'now', aa=lambda person: person == 'person',
        ia=lambda person, context, point: person == 'person' and context == 'now' and point in history,
        ic=ordered, g7=permission,
        ei=lambda person, activity, point: attempted and (person, symbol(activity), point) == ('person', 'bm', 'recent'),
        ab=lambda ability, person, point: (ability, person, point) == ('ability', 'person', 'success'),
        ac=lambda person, ability, act, point: (person, ability, act, point) == ('person', 'ability', 'act', 'success'),
        # Every successful use in this fixture is guided: bm must not silently become bb.
        ad=lambda leader, person, act, point: (leader, person, act, point) == ('leader', 'person', 'act', 'success'),
        ae=lambda person, plan, start: able and (person, plan, start) == ('person', 'plan', 'now'),
        af=lambda person, plan, start, end: (person, plan, start, end) == ('person', 'plan', 'now', 'success'),
        ap=lambda person, plan, start, end: variant != 'missing_assessment' and (
            person, plan, start, end) == ('person', 'plan', 'now', 'success'), ea=explains)
    return {name: fn for name, fn in model.items() if name in guarded(doc)}


def independence_checks():
    doc = candidate(source_composed()[0], QUERIES)
    rows = []
    for allowed, attempted, able, explained in product((False, True), repeat=4):
        result = values(doc, source_model(doc, allowed=allowed, attempted=attempted, able=able, explanation=explained))
        if result != [not allowed, not attempted, not able, not allowed and not able and explained]:
            raise ValueError('Permission, attempt, ability or explanation was inferred from another: ' + repr(result))
        rows.append(dict(allowed=allowed, attempted=attempted, able=able, explained=explained, result=result))
    return rows


def scope_checks():
    doc = candidate(source_composed()[0], QUERIES)
    expected = {
        'baseline': False, 'different_person': True, 'different_activity': True, 'different_agent': False,
        'permission_now': True, 'permission_future': True, 'permission_alternative': True,
        'permission_older': False, 'empty_past': True,
        'missing_anchor': False, 'reflexive_order': False, 'cyclic_order': False,
    }
    rows = {}
    for variant, absent in expected.items():
        result = values(doc, source_model(doc, allowed=True, variant=variant))
        valid = variant not in ('missing_anchor', 'reflexive_order', 'cyclic_order')
        if result != [absent, valid, True, absent]:
            raise ValueError('Person/activity/history/anchor binding differs: ' + variant + repr(result))
        rows[variant] = result
    return rows


def ability_checks():
    doc = candidate(source_composed()[0], QUERIES + 'q[t[k bf[k za[]]][k zb[]]].')
    rows = {}
    for variant, able, expected in (
            ('baseline', True, [True, True, False, False, True]),
            ('missing_assessment', True, [True, True, False, False, False]),
            ('baseline', False, [True, True, True, True, True])):
        result = values(doc, source_model(doc, able=able, variant=variant))
        if result != expected:
            raise ValueError('Guidance exclusion or missing assessment became inability: ' + repr(result))
        rows[variant + ':' + str(able)] = result
    return rows


def explanation_checks():
    doc = candidate(source_composed()[0], QUERIES)
    rows = {}
    for variant in ('baseline', 'wrong_factor_person', 'wrong_factor', 'wrong_effect_person', 'wrong_effect', 'wrong_context'):
        result = values(doc, source_model(doc, variant=variant))
        if result != [True, True, True, variant == 'baseline']:
            raise ValueError('Causal explanation accepted a different subject, description or context')
        rows[variant] = result
    return rows


def alignment():
    path = ROOT / 'artifacts/written-units-v1/kant-1784.json'
    inventory = json.loads((ROOT / 'reports/written-units-v1.json').read_text(encoding='utf-8'))
    if hashlib.sha256(path.read_bytes()).hexdigest() != inventory['works']['kant-1784']['units_sha256']:
        raise ValueError('Source inventory changed')
    unit = next(u for u in json.loads(path.read_text(encoding='utf-8'))['units'] if u['id'] == 'kant-1784:u0010')
    if hashlib.sha256(unit['text'].encode()).hexdigest() != unit['text_sha256']:
        raise ValueError('Third paragraph changed')
    start = unit['text'].index('ist vor der Hand')
    end = unit['text'].index('. Satzungen')
    return {'unit': unit['id'], 'unit_sha256': unit['text_sha256'], 'start': start, 'end': end,
        'source': unit['text'][start:end], 'definitions': ['bm', 'h2', 'h3', 'h4', 'h5'],
        'status': 'partial_explicit_reading', 'full_semantic_equivalence': False,
        'actual_attempt_absence_not_asserted': True,
        'indefinite_agent_not_resolved_to_a_specific_guardian': True,
        'remaining': ['generalization and anaphora over the whole paragraph', 'social letting and effective opportunity',
                      'emphasis and exact temporary duration', 'grounding of ability and explanation',
                      'surrounding affection, habituation and metaphors']}


def build_report():
    documents = {}
    for builder, name in ((generic_composed, 'attempt-history'), (source_composed, 'kant-attempt-history')):
        text, basis = builder()
        doc = parse(text)
        if (ROOT / basis['document']).read_text(encoding='utf-8') != text or json.loads(
                (ROOT / ('data/' + name + '-basis-v1.json')).read_text(encoding='utf-8')) != basis:
            raise ValueError('Stored attempt history differs')
        for notation in ('compact', 'full'):
            form = format_graph(doc, notation)
            if parse(form) != doc or parse(decode(encode(form, 'v2'))) != doc:
                raise ValueError('Attempt history roundtrip differs')
        documents[basis['document']] = audit_basis(doc, basis)
    parent = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    if doc['statements'] != parent['statements'] or doc['declarations'][:len(parent['declarations'])] != parent['declarations']:
        raise ValueError('Previous Kant content changed')
    paths = list(documents) + [PARENT, 'data/attempt-history-basis-v1.json', 'data/kant-attempt-history-basis-v1.json',
        'data/attempt-history-reading-review-v1.json', 'scripts/compose_attempt_history.py', 'scripts/check_attempt_history.py',
        'noema/finite_semantics.py', 'noema/discourse.py', 'artifacts/written-units-v1/kant-1784.json', 'reports/written-units-v1.json']
    return {'status': 'partial_scoped_permission_history_and_present_inability', 'documents': documents,
        'evidence': evidence_checks(), 'independence': independence_checks(), 'scope': scope_checks(),
        'ability': ability_checks(), 'explanation': explanation_checks(), 'alignment': alignment(),
        'roundtrips': True, 'parent_preserved': True, 'finite_interpretations_not_all_histories': True,
        'verified_full_units': {'einstein-1905': 0, 'kant-1784': 0},
        'notation_size': {'canonical_source_document_characters': len(text),
                         'added_characters': len(text) - len((ROOT / PARENT).read_text(encoding='utf-8'))},
        'source_sha256': {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in paths}}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--verify-only', action='store_true')
    args = parser.parse_args()
    report = build_report()
    if args.verify_only:
        if report != json.loads(REPORT.read_text(encoding='utf-8')):
            raise ValueError('Attempt history report differs')
    else:
        with REPORT.open('x', encoding='utf-8', newline='\n') as stream:
            json.dump(report, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
    print('Negative history, evidence completeness and current ability distinguished')


if __name__ == '__main__':
    main()
