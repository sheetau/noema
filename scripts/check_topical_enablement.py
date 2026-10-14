"""Check fixed topical scope, nested ability and assessed collective shortfalls."""
import argparse
from fractions import Fraction
import hashlib
from itertools import product
import json

from noema.finite_semantics import SequenceValue
from noema.higher_order_semantics import evaluate_document
from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from scripts.check_described_appraisals import candidate
from scripts.check_rod_setup import guarded
from scripts.check_scoped_counts import arithmetic
from scripts.compose_limits import call as k
from scripts.compose_topical_enablement import ROOT, PARENT, BUILDERS, JUDGMENT, CHECKED, CAPABLE, ENABLING, POSSIBLE, COLLECTIVE, SOURCE, ENABLE_SOURCE, GROUP_SOURCE

REPORT = ROOT / 'reports/topical-enablement-v1.json'
PEOPLE = ('alice', 'bob')
DOMAIN = (*PEOPLE, 'teacher', 'faith', 'matterone', 'mattertwo', 'plan', 'actone', 'acttwo', 'facultya', 'facultyb', 'reason')
SCENES = ('now', 'trained', 'firstonly', 'secondonly', 'judged', 'failed')
EXTRA = '''r jkperson[] a.r jkcontext[] d.r jktopic[] a.r jkanchor[] d.r jkenabler[] a.
r jkpopulation[] j[a].r jkscope[a] c.r jkcurrentupper[] b.r jkenableupper[] b.
r jktopics[a a a d] c.r jkrelevant[a a] c.r jkavailable[a a a d] c.r jkoutcomes[a a a d d] c.r jkselected[a a a d d] c.
r jkenabling[a a a d] c.r jkeffects[a a a d d] c.
r jkowned[a a d] c.r jkuse[a a a d] c.r jkjudgments[a a d] c.r jkmatters[a a d] c.
r jkreasons[a a d] c.r jksupport[a a d] c.r jkguidance[a a a d] c.'''
REFS = {n: 'k jk' + n + '[]' for n in ('person', 'context', 'topic', 'anchor', 'enabler', 'population', 'currentupper', 'enableupper')}
REFS.update({n: 'p jk' + n for n in ('scope', 'topics', 'relevant', 'available', 'outcomes', 'selected', 'enabling', 'effects',
    'owned', 'use', 'judgments', 'matters', 'reasons', 'support', 'guidance')})
REFS['goals'] = 'i[person a matter a][' + k('rlk', 'v person', 'v matter', *(REFS[n] for n, _ in JUDGMENT)) + ']'


def expressions(source=False):
    fields = [('hzeq', SOURCE), ('hzer', SOURCE), ('hzes', ENABLE_SOURCE), ('hzet', ENABLE_SOURCE)] if source else [
        ('rll', CHECKED), ('rlm', CAPABLE), ('rln', ENABLING), ('rlo', POSSIBLE)]
    functions = {}
    for field, (name, params) in zip(('assessed', 'capable', 'enableassessed', 'enableable'), fields, strict=True):
        if source:
            functions[field] = k(name, *(REFS[n] for n, _ in params))
        else:
            refs = {**REFS, 'person': 'v person', 'context': 'v point'}
            functions[field] = 'i[person a][b point[' + k(name, *(refs[n] for n, _ in params)) + ']]'
    return functions


def setup(text, source=False):
    functions = expressions(source)
    queries = ['t[c[' + functions[n] + '][k jkperson[]]][k jkcontext[]]' for n in functions]
    refs = {**REFS, **functions}
    group = k('hzeu' if source else 'rlp', *(refs[n] for n, _ in (GROUP_SOURCE if source else COLLECTIVE)))
    return candidate(text, EXTRA + ''.join('q[' + expr + '].' for expr in (*queries, group)))


def model_for(doc, bits=(False, False, True, False), variant='baseline', population=PEOPLE, upper=2):
    model = guarded(doc)
    model.update({n: fn for n, fn in arithmetic().items() if n in model})
    matters = ('matterone', 'mattertwo'); acts = dict(zip(matters, ('actone', 'acttwo')))
    faculties = dict(zip(PEOPLE, ('facultya', 'facultyb')))
    def topics(person, topic, matter, anchor):
        return person in PEOPLE and topic == 'faith' and matter in matters and (anchor == 'now' or matter == 'matterone')
    def available(person, matter, plan, point):
        if person not in PEOPLE or matter not in matters or plan != 'plan': return False
        i = PEOPLE.index(person)
        return bits[i] if point == 'now' else bits[i + 2] if point == 'trained' else (
            point == 'firstonly' and matter == 'matterone' or point == 'secondonly' and matter == 'mattertwo')
    def outcomes(person, matter, plan, start, end):
        return available(person, matter, plan, start) and end == 'judged'
    def selected(person, matter, plan, start, end):
        return available(person, matter, plan, start) and variant != 'empty_selected' and end == ('failed' if variant == 'outside_outcome' else 'judged')
    def enabling(actor, person, plan, point):
        wanted = 'alice' if variant == 'wrong_enabler' else 'teacher'
        return actor == wanted and person in PEOPLE and plan == 'plan' and point == 'now' and variant != 'no_enabling_method'
    def effects(actor, person, plan, start, end):
        return enabling(actor, person, plan, start) and variant != 'no_effects' and end in (
            ('firstonly', 'secondonly') if variant == 'split_results' else ('trained',))
    model.update(jkperson=lambda: 'alice', jkcontext=lambda: 'now', jktopic=lambda: 'faith', jkanchor=lambda: 'now', jkenabler=lambda: 'teacher',
        jkpopulation=lambda: SequenceValue(tuple(population), '"individual"'), jkscope=lambda p: p in PEOPLE,
        jkcurrentupper=lambda: Fraction(upper), jkenableupper=lambda: Fraction(upper), jktopics=topics,
        jkrelevant=lambda person, matter: topics(person, 'faith', matter, 'now'), jkavailable=available,
        jkoutcomes=outcomes, jkselected=selected, jkenabling=enabling, jkeffects=effects,
        jkowned=lambda faculty, person, point: faculties.get(person) == faculty and point == 'judged',
        jkuse=lambda person, faculty, act, point: person in PEOPLE and point == 'judged' and act in acts.values() and faculty == (
            faculties[PEOPLE[1 - PEOPLE.index(person)]] if variant == 'wrong_faculty' else faculties[person]),
        jkjudgments=lambda person, act, point: person in PEOPLE and act in acts.values() and point == 'judged',
        jkmatters=lambda act, matter, point: acts.get(matter) == act and point == 'judged' and not (variant == 'missing_matter' and matter == 'mattertwo'),
        jkreasons=lambda act, reason, point: act in acts.values() and reason == 'reason' and point == 'judged',
        jksupport=lambda reason, act, point: reason == 'reason' and act in acts.values() and point == 'judged' and variant != 'unsupported',
        jkguidance=lambda other, person, act, point: other == 'teacher' and person in PEOPLE and act in acts.values() and point == 'judged' and variant == 'guided')
    if 'aa' in model: model['aa'] = lambda person: person in (*PEOPLE, 'teacher')
    for name, field in (('ab', 'owned'), ('ac', 'use'), ('fa', 'judgments'), ('fb', 'matters'), ('fc', 'reasons'), ('fd', 'support'), ('ad', 'guidance')):
        if name in model: model[name] = model['jk' + field]
    return model


def values(doc, model):
    return [row['value'] for row in evaluate_document(doc, primitives=model, individuals=DOMAIN, situations=SCENES, max_steps=8_000_000)]


def checks(texts):
    docs = [setup(texts[0]), *[setup(t, True) for t in texts[1:]]]; cases = []
    for bits in product((False, True), repeat=4):
        expected = [True, bits[0], True, bits[2], sum(bits[:2]) < 2 and sum(bits[2:]) < 2]
        rows = [values(doc, model_for(doc, bits)) for doc in docs]
        if rows != [expected] * 3: raise ValueError('Ability and enabling conflated: ' + repr((bits, rows)))
        cases.append(dict(bits=list(bits), result=expected))
    contrasts = {}
    expected_variants = {
        'unsupported': [True, False, True, False, True], 'guided': [True, False, True, False, True],
        'wrong_faculty': [True, False, True, False, True], 'missing_matter': [True, False, True, False, True],
        'empty_selected': [False, False, True, False, False], 'outside_outcome': [False, False, True, False, False],
        'no_enabling_method': [True, True, True, False, False], 'wrong_enabler': [True, True, True, False, False],
        'no_effects': [True, True, False, False, False], 'split_results': [True, True, True, False, False],
    }
    for variant, expected in expected_variants.items():
        rows = [values(doc, model_for(doc, (True,) * 4, variant)) for doc in docs]
        if rows != [expected] * 3: raise ValueError('Topical contrast mismatch: ' + repr((variant, rows)))
        contrasts[variant] = expected
    counts = []
    for population, upper, expected in ((PEOPLE, 2, True), (tuple(reversed(PEOPLE)), 2, True), (('alice',), 2, False),
        (('alice', 'alice'), 2, False), ((), 1, False), (PEOPLE, 0, False), (PEOPLE, 3, False), (PEOPLE, 1, False)):
        rows = [values(doc, model_for(doc, (False, True, True, False), population=population, upper=upper))[-1] for doc in docs]
        if rows != [expected] * 3: raise ValueError('Collective scope or upper bound differs')
        counts.append(dict(population=list(population), upper=upper, result=expected))
    return dict(cases=cases, contrasts=contrasts, counts=counts, fixed_topic_scope=True,
        enabling_can_fail_despite_current_ability=True, success_in_one_joint_outcome_required=True)


def quote_checks(texts):
    rows = []
    for text in texts:
        base = setup(text, True); base['statements'] = []
        fields = {**REFS, 'context': 'v point'}
        content = 'b point[' + k('hzeu', *(fields[n] for n, _ in GROUP_SOURCE)) + ']'
        doc = parse(format_graph(base, 'compact') + 'q[e[r[' + content + ']][r[' + content + ']]].')
        result = values(doc, guarded(doc))
        if result != [True]: raise ValueError('Describing a deficit executed unknown abilities')
        rows.append(result)
    return rows


def build_report():
    texts, documents, sizes = [], {}, {}
    for builder, stem in BUILDERS:
        text, basis = builder(); texts.append(text); doc = parse(text)
        if (ROOT / basis['document']).read_text(encoding='utf-8') != text or json.loads((ROOT / ('data/' + stem + '-basis-v1.json')).read_text(encoding='utf-8')) != basis:
            raise ValueError('Topical enablement artifact differs')
        for notation in ('full', 'compact'):
            form = format_graph(doc, notation)
            if parse(form) != doc or parse(decode(encode(form, 'v2'))) != doc: raise ValueError('Topical enablement roundtrip differs')
        documents[basis['document']] = audit_basis(doc, basis); sizes[stem] = len(text)
    parent, child = parse((ROOT / PARENT).read_text(encoding='utf-8')), parse(texts[1])
    if child['declarations'][:len(parent['declarations'])] != parent['declarations'] or child['statements'] != parent['statements']:
        raise ValueError('Historical parent changed')
    unit = next(u for u in json.loads((ROOT / 'artifacts/written-units-v1/kant-1784.json').read_text(encoding='utf-8'))['units'] if u['id'] == 'kant-1784:u0014')
    phrase = 'Daß die Menschen, wie die Sachen jetzt stehen, im Ganzen genommen, schon im Stande wären, oder darin auch nur gesetzt werden könnten, in Religionsdingen sich ihres eigenen Verstandes ohne Leitung eines Andern sicher und gut zu bedienen, daran fehlt noch sehr viel.'
    start = unit['text'].index(phrase)
    paths = {*documents, PARENT, *['data/' + stem + '-basis-v1.json' for _, stem in BUILDERS],
        'scripts/compose_topical_enablement.py', 'scripts/check_topical_enablement.py', 'scripts/check_scoped_counts.py',
        'scripts/check_described_appraisals.py', 'scripts/check_rod_setup.py', 'noema/higher_order_semantics.py',
        'noema/finite_semantics.py', 'noema/extraction.py', 'artifacts/written-units-v1/kant-1784.json'}
    return dict(status='partial_fixed_topic_ability_and_enablement', documents=documents, sizes=sizes,
        interpretation=checks(texts), quotation=quote_checks(texts[1:]), parent_preserved=True, roundtrips=True,
        new_definitions=11, new_primitives=0, new_author_statements=0,
        alignment=dict(semantic_completion=False, segments=[dict(unit=unit['id'], unit_sha256=unit['text_sha256'],
            status='explicit_interpretive_annotation', range=[start, start + len(phrase)], text=phrase,
            definitions=['rlk', 'rll', 'rlm', 'rln', 'rlo', 'rlp', 'hzeq', 'hzer', 'hzes', 'hzet', 'hzeu'])]),
        verified_full_units={'kant-1784': 0, 'einstein-1905': 0},
        source_sha256={name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in sorted(paths)})


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--verify-only', action='store_true'); args = parser.parse_args()
    result = build_report()
    if args.verify_only:
        if result != json.loads(REPORT.read_text(encoding='utf-8')): raise ValueError('Topical enablement report differs')
    else:
        with REPORT.open('x', encoding='utf-8', newline='\n') as stream:
            json.dump(result, stream, ensure_ascii=False, indent=2); stream.write('\n')
    print('Fixed topical capability, possible enablement and collective assessment checked')


if __name__ == '__main__': main()
