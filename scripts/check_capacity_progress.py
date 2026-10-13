"""Check fixed-cohort capacity gains without counting missing assessments as failures."""
import argparse
from fractions import Fraction
import hashlib
from itertools import product
import json

from noema.finite_semantics import Content, FunctionValue, SequenceValue
from noema.grammar import format_graph, parse
from noema.meaning_basis import audit_basis
from noema.policy_descriptions import close_policy_description
from noema.script import encode, decode
from scripts.check_conditional_release import values
from scripts.check_described_appraisals import candidate
from scripts.check_rod_setup import guarded
from scripts.check_scoped_counts import arithmetic
from scripts.check_bounded_hindrance import STATE_SORT, quoted
from scripts.compose_capacity_progress import ROOT, PARENT, generic_composed, source_composed

REPORT = ROOT / 'reports/capacity-progress-v1.json'
PEOPLE = ('one', 'two')
SCENES = ('before', 'offlow', 'offhigh', 'onlow', 'onhigh')
DOMAIN = ('x', 'y', *PEOPLE, 'faculty', 'plan', 'act', 'guide')


def finite_checks():
    doc = parse(generic_composed()[0] + '''
r za[] j[a].r zb[a] e.r zc[a] e.r zd[a] c.r ze[] d.r zf[] d.r zg[d d] c.r zh[] b.
q[k rej[k za[] p zd p zc k ze[] k zf[] p zg]].
q[e[k rei[k za[] p zb k ze[] k zf[]]][k zh[]]].
''')
    def run(properties, assessed, population=PEOPLE, scope=PEOPLE, ordered=True):
        delta = sum(int(properties[PEOPLE.index(person)*2+1]) - int(properties[PEOPLE.index(person)*2]) for person in population)
        model = {**arithmetic(), 'za': lambda: SequenceValue(tuple(population), '"individual"'),
            'zb': lambda person: Content(('before', 'after'), tuple(properties[PEOPLE.index(person)*2:PEOPLE.index(person)*2+2])),
            'zc': lambda person: Content(('before', 'after'), tuple(assessed[PEOPLE.index(person)*2:PEOPLE.index(person)*2+2])),
            'zd': lambda person: person in scope, 'ze': lambda: 'before', 'zf': lambda: 'after',
            'zg': lambda first, last: ordered and (first, last) == ('before', 'after'), 'zh': lambda: Fraction(delta)}
        return values(doc, model, PEOPLE, ('before', 'after'))
    count = 0
    for properties in product((False, True), repeat=4):
        for assessed in product((False, True), repeat=4):
            actual = run(properties, assessed)
            if actual != [all(assessed), True]:
                raise ValueError('Count change or assessment gate differs')
            count += 1
    contrasts = {}
    props, assessed = (False, True, True, True), (True,) * 4
    for name, options, expected in (
        ('reordered', {'population': tuple(reversed(PEOPLE))}, [True, True]),
        ('omitted_person', {'population': ('one',)}, [False, True]),
        ('duplicate', {'population': ('one', 'one', 'two')}, [False, True]),
        ('empty', {'population': (), 'scope': ()}, [False, True]),
        ('out_of_scope', {'scope': ('one',)}, [False, True]),
        ('not_later', {'ordered': False}, [False, True]),
        ('changed_scope_is_distinct_measure', {'population': ('one',), 'scope': ('one',)}, [True, True]),
    ):
        actual = run(props, assessed, **options)
        if actual != expected:
            raise ValueError('Population comparison differs: ' + str((name, actual)))
        contrasts[name] = actual
    return {'property_and_assessment_cases': count, 'contrasts': contrasts,
        'raw_count_is_not_an_assessment_certificate': True}


def source_checks():
    text, basis = source_composed()
    extra = '''r za[] j[a].r zb[a] c.r zc[] d.r zd[] h[h[a] c] d.r ze[d d] c.
r zf[] j[a].r zg[] h[a h[a] c] c.r zh[] a.r zi[] b.r zj[] d.r zk[d] c.
d zl[] e[b point[k zk[v point]]].r zm[] b.r zn[] a.r zo[] b.
'''
    args = 'k za[] p zb k zc[] k zd[] p ze k zf[] k zg[] k zh[] k zi[]'
    doc = candidate(text, extra + 'q[k hzg[' + args + ']].q[t[k hzi[k zl[] ' + args + ']][k zj[]]].' + '''
q[e[c[k hzh[k za[] k zc[] k zd[]]][i[item a][e[v item][k zh[]]]]][k zm[]]].
q[e[c[k hzh[k za[] k zc[] k zd[]]][i[item a][e[v item][k zn[]]]]][k zo[]]].
''')
    def model(selected, variant='baseline', expected_gains=(1, 2)):
        result = guarded(selected)
        result.update(arithmetic())
        population = ('one',) if variant == 'omitted_person' else ('one', 'one', 'two') if variant == 'duplicate' else () if variant == 'empty' else PEOPLE
        def worlds(state):
            if variant == 'wrong_worlds':
                return 'offhigh'
            return SCENES[1 + 2 * int(state('x')) + int(state('y'))]
        def capable(person, point):
            if point == 'before':
                return variant == 'one_already_capable' and person == 'one' or variant == 'both_already_capable'
            return person == 'one' or point.endswith('high')
        def available(person, plan, point):
            return person in PEOPLE and plan == 'plan' and not (variant == 'no_methods_with_larger_tolerance' and person == 'one' and point == 'onlow')
        def selected_outcome(person, plan, start, end):
            if variant == 'unknown_assessment' and person == 'one' and start == 'onlow':
                raise ValueError('Unknown capability assessment')
            omitted = variant == 'unassessed_before' and start == 'before' or variant == 'unassessed_after' and start == 'onlow'
            return available(person, plan, start) and start == end and not (person == 'one' and omitted)
        def own_use(person, faculty, activity, point):
            if variant == 'unknown_use' and person == 'one' and point == 'onlow':
                raise ValueError('Unknown independent use')
            return person in PEOPLE and (faculty, activity) == ('faculty', 'act') and capable(person, point)
        result.update(za=lambda: SequenceValue(population, '"individual"'), zb=lambda person: person in PEOPLE,
            zc=lambda: 'before', zd=lambda: FunctionValue((STATE_SORT,), 'situation', worlds),
            ze=lambda first, last: variant != 'not_later' and first == 'before' and last != 'before',
            zf=lambda: SequenceValue(('x', 'y'), '"individual"'),
            zg=lambda: FunctionValue(('individual', STATE_SORT), 'truth', lambda variable, state:
                False if variable == 'x' else not state('y') if variant == 'no_solution' else not state('x')),
            zh=lambda: 'x', zi=lambda: Fraction(0 if variant == 'zero_tolerance' else 2 if variant == 'no_methods_with_larger_tolerance' else 1),
            zj=lambda: 'offhigh' if variant == 'not_actual_policy' else 'onhigh' if variant == 'not_actual_result' else 'onlow',
            zk=lambda point: point.startswith('on'), zm=lambda: Fraction(expected_gains[0]),
            zn=lambda: 'y', zo=lambda: Fraction(expected_gains[1]),
            aa=lambda person: person in PEOPLE and not (variant == 'nonhuman_scope' and person == 'two'),
            ab=lambda faculty, person, point: faculty == 'faculty' and person in PEOPLE,
            ac=own_use,
            ad=lambda guide, person, activity, point: variant == 'guided_outcome' and
                (guide, person, activity, point) == ('guide', 'one', 'act', 'onlow'),
            ae=available, af=lambda person, plan, start, end: available(person, plan, start) and start == end,
            ap=selected_outcome)
        return result
    cases = {}
    for name, expected, gains in (
        ('baseline', [True, True], (1, 2)),
        ('zero_tolerance', [False, False], (1, 2)),
        ('one_already_capable', [True, True], (0, 1)),
        ('both_already_capable', [True, True], (-1, 0)),
        ('omitted_person', [False, False], (1, 1)),
        ('duplicate', [False, False], (2, 3)),
        ('empty', [False, False], (0, 0)),
        ('unassessed_before', [False, False], (1, 2)),
        ('unassessed_after', [False, False], (0, 2)),
        ('guided_outcome', [False, False], (0, 2)),
        ('no_methods_with_larger_tolerance', [True, True], (0, 2)),
        ('nonhuman_scope', [False, False], (1, 1)),
        ('not_later', [False, False], (1, 2)),
        ('wrong_worlds', [True, False], (2, 2)),
        ('not_actual_policy', [True, False], (1, 2)),
        ('not_actual_result', [True, False], (1, 2)),
        ('no_solution', [False, False], (1, 2)),
    ):
        actual = values(doc, model(doc, name, gains), DOMAIN, SCENES)
        if actual != [*expected, True, True]:
            raise ValueError('Native capacity progress differs: ' + str((name, actual)))
        cases[name] = {'valid_bounded_comparison': actual[0], 'qualified_policy': actual[1],
            'on_gain': gains[0], 'off_gain': gains[1], 'native_gains_match': actual[2:]}
    for variant in ('unknown_assessment', 'unknown_use'):
        try:
            values(doc, model(doc, variant), DOMAIN, SCENES)
        except ValueError as exc:
            if 'Unknown ' not in str(exc):
                raise
        else:
            raise ValueError('Unknown capacity became incapacity')
    base = candidate(text, extra)
    target = close_policy_description(base, quoted('hzi', True), [quoted(name, reference) for name, reference in (
        ('zl', False), ('za', False), ('zb', True), ('zc', False), ('zd', False), ('ze', True),
        ('zf', False), ('zg', False), ('zh', False), ('zi', False))])
    permission = {'kind': 'ask', 'body': {'kind': 'call', 'symbol': 'hza',
        'arguments': [quoted('zh')['body']] * 3 + [target, quoted('zj')['body']]}}
    only = {**base, 'statements': [permission]}
    guarded_model = guarded(only)
    syntax = json.dumps(target['body'], sort_keys=True, separators=(',', ':'), ensure_ascii=False)
    guarded_model.update(zh=lambda: 'x', zj=lambda: 'onlow',
        h7l=lambda source, person, role, desc, bindings, sign, context: desc.syntax == syntax and bindings.items == () and sign)
    if values(only, guarded_model, DOMAIN, SCENES) != [True]:
        raise ValueError('Permission evaluated the capacity measure')
    for notation in ('compact', 'full'):
        form = format_graph(only, notation)
        if parse(form) != parse(format_graph(only)) or parse(decode(encode(form, 'v2'))) != parse(form):
            raise ValueError('Assessed capacity target roundtrip differs')
    return {'cases': cases, 'unknown_capacity_and_assessment_refused': True,
        'native_capacity_definitions_not_replaced_by_primitives': True,
        'permission_does_not_evaluate_capacity': True, 'qualified_target_roundtrips': True}


def alignment():
    old = json.loads((ROOT / 'reports/bounded-hindrance-v1.json').read_text(encoding='utf-8'))['alignment']
    row = dict(old['segments'][0])
    row['definitions'] = ['hzg', 'hzh', 'hzi']
    row['review_ja'] = '進歩の候補尺度を、同じ対象集団・共通始点のfo/h4lによる能力人数の純増へ接続した。未評価と能力なし、純増と個人の獲得過程を区別する。原文の啓蒙の全意味と人数尺度の同一性は未確認。'
    return {'segments': [row], 'new_source_ranges': False, 'semantic_completion': False}


def build_report():
    documents = {}
    for builder, stem in ((generic_composed, 'capacity-progress'), (source_composed, 'kant-capacity-progress')):
        text, basis = builder()
        doc = parse(text)
        if (ROOT / basis['document']).read_text(encoding='utf-8') != text or json.loads(
                (ROOT / ('data/' + stem + '-basis-v1.json')).read_text(encoding='utf-8')) != basis:
            raise ValueError('Stored capacity progress differs')
        for notation in ('compact', 'full'):
            form = format_graph(doc, notation)
            if parse(form) != doc or parse(decode(encode(form, 'v2'))) != doc:
                raise ValueError('Capacity progress roundtrip differs')
        documents[basis['document']] = audit_basis(doc, basis)
    parent = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    if doc['declarations'][:len(parent['declarations'])] != parent['declarations'] or doc['statements'] != parent['statements']:
        raise ValueError('Parent changed')
    paths = [*documents, PARENT, 'data/capacity-progress-basis-v1.json', 'data/kant-capacity-progress-basis-v1.json',
        'scripts/compose_capacity_progress.py', 'scripts/check_capacity_progress.py', 'reports/bounded-hindrance-v1.json',
        'noema/policy_descriptions.py', 'noema/finite_semantics.py', 'noema/discourse.py']
    return json.loads(json.dumps({'status': 'partial_assessed_capacity_count_not_complete_enlightenment_progress',
        'documents': documents, 'finite': finite_checks(), 'source': source_checks(), 'alignment': alignment(),
        'roundtrips': True, 'parent_preserved': True, 'new_source_assertions': 0, 'new_primitives': 0,
        'notation_size': {'canonical_source_document_characters': len(text),
            'added_characters': len(text) - len((ROOT / PARENT).read_text(encoding='utf-8'))},
        'verified_full_units': {'kant-1784': 0, 'einstein-1905': 0},
        'source_sha256': {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in paths}}, ensure_ascii=False))


def main():
    cli = argparse.ArgumentParser()
    cli.add_argument('--verify-only', action='store_true')
    args = cli.parse_args()
    report = build_report()
    if args.verify_only:
        if report != json.loads(REPORT.read_text(encoding='utf-8')):
            raise ValueError('Capacity progress report differs')
    else:
        with REPORT.open('x', encoding='utf-8', newline='\n') as stream:
            json.dump(report, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
    print('Common-baseline cohort gains connected to native assessed capacity')


if __name__ == '__main__':
    main()
