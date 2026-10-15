"""Check a later normative consequence in the shared collective world model."""
import argparse
from copy import deepcopy
from functools import lru_cache
import hashlib
import json
from noema.constructed import parse, format_graph
from noema.constructed_semantics import SequenceValue, FunctionValue, evaluate_document
from noema.script import transcribe
from scripts.compose_political_consequence import ROOT, PARENT, LIBRARY, SOURCE, CORE, BASIS, HIGH, STATE, REST, FIELDS, build, basis
from scripts.compose_qualified_utterance import closure
from scripts.compose_restricted_utterance import primitive
from scripts.check_caused_choice import evaluate
from scripts.check_scoped_counts import arithmetic
from scripts.check_apparent_liberty import UNITS
from scripts import check_thinking_disposition as thinking
from scripts import check_collective_conditional as previous
from scripts import check_joint_development as joint

REPORT = ROOT / 'reports/political-consequence-v1.json'
PEOPLE = ('person', 'other')
VARIABLES = ('one', 'two', 'outcome')


@lru_cache(maxsize=4)
def document(path): return parse((ROOT / path).read_text(encoding='utf-8'))


@lru_cache(maxsize=1)
def fixture():
    text = (ROOT / LIBRARY).read_text(encoding='utf-8'); args = []
    for name, sort in FIELDS:
        provider = name == 'observed' or not sort.startswith('h[')
        text += primitive('jp' + name, 'h[] ' + sort if provider else sort)
        args.append('k jp' + name + '[]' if provider else 'p jp' + name)
    return parse(text + 'q[k rx5[' + ' '.join(args) + ']].')


def values(table=8, *, variant='baseline', memoize=True):
    catalogue = () if variant == 'empty' else PEOPLE + ('person',) if variant == 'duplicate' else PEOPLE[:1] if variant == 'omitted' else PEOPLE
    def factor(person):
        if variant == 'same_factor': return 'one'
        if variant == 'undeclared': return 'outside'
        return VARIABLES[PEOPLE.index(person)] if person in PEOPLE else 'outside'
    def equation(variable, state):
        if variant == 'unknown_equation': raise ValueError('Unknown political equation')
        if variable in VARIABLES[:2]: return True
        if variable == 'outcome':
            if variant == 'ambiguous': return state(variable)
            if variant == 'no_off_solution' and not state('one') and not state('two'): return not state(variable)
            return bool(table & (1 << (2 * int(state('one')) + int(state('two')))))
        return False
    def checked(state):
        if not state('one') and not state('two'):
            if variant == 'unknown_off': raise ValueError('Unknown political assessment')
            if variant == 'unreviewed_off': return False
        return True
    def premise(person, state):
        if variant == 'wrong_premise' and person == 'other': return True
        return state(factor(person)) if person in PEOPLE else False
    p = dict(arithmetic(), jpcontributors=lambda: SequenceValue(catalogue, '"individual"'),
        jppeople=lambda person: variant != 'empty' and person in PEOPLE, jpfactors=factor,
        jpvariables=lambda: SequenceValue(VARIABLES, '"individual"'), jpequations=equation, jppremise=premise,
        jpchecked=checked, jpeffect=lambda state: state('outcome'),
        jpobserved=lambda: FunctionValue(('individual',), 'truth', lambda x: x in VARIABLES))
    doc = fixture(); p = {d['name']: p[d['name']] for d in doc['declarations'] if d['kind'] == 'primitive'}
    return evaluate(doc, p, PEOPLE + VARIABLES + ('outside',), ('now',), memoize=memoize)


@lru_cache(maxsize=1)
def source_fixture():
    doc = deepcopy(document(CORE)); doc['statements'] = []
    names = {d['name'] for d in doc['declarations']}
    for d in closure(document(SOURCE), ['rxv']):
        if d['name'] not in names: doc['declarations'].append(d); names.add(d['name'])
    text = format_graph(doc, 'compact') + '''
r jpcommunity[] a.r jpstart[] d.r jpend[] d.r jpactor[] a.r jpsource[] a.r jpoffice[] a.r jpperson[] a.
r jpprobes[d] c.
'''
    for name, truth in (('jpold', 'u[e[n p a b][n p a b]]'), ('jpnew', 'e[n p a b][n p a b]')):
        text += 'd ' + name + '[bindings j[a]] e[c[k rxv[k jpactor[] l[a][k jpperson[]] ' + \
            'i[person a][e[v person][k jpperson[]]] i[person a point d][e[n p a b][n p a b]] ' + \
            'i[actor a person a point d][' + truth + ']]][v bindings]].'
    text += 'r jpremaining[' + REST[2:-3] + '] c.'
    context = 'k jpcommunity[] k jpstart[] k jpend[]'
    gov = 'k jpsource[] k jpactor[] k jpoffice[] r[p jpold] r[p jpnew] p jpprobes'
    observed = 'k iapobserved[' + context + ']'
    queries = [
        'k iascausal[r b[p iahinner] ' + context + ' ' + gov + ']',
        'k iaschecked[' + context + ' ' + gov + ' ' + observed + ']',
        'k iaseffect[' + context + ' ' + gov + ' ' + observed + ']',
        'k iasschema[r b[p iahinner] ' + gov + ' p jpremaining]',
        'k iasschema[r b[p iahvocation] ' + gov + ' p jpremaining]',
        'k iapnecessary[r b[p iahinner] ' + context + ']',
        'k iasschema[r b[p iahthinking] ' + gov + ' p jpremaining]']
    return parse(text + ''.join('q[' + q + '].' for q in queries))


def source_model(table=8, *, variant='baseline', all_false=False, remaining=True, calls=None):
    p, domain, scenes = previous.source_model(all_false=all_false)
    old = dict(p)
    variables = joint.VARIABLES + ('policy',)
    domain += tuple(x for x in ('policy', 'government', 'office') if x not in domain)
    scenes += ('political', 'normbase', 'normchanged', 'normkept')
    def path(state):
        start = joint.BEGINS[(state('causeone'), state('causetwo'))]
        result = (start, 'middle', 'after') if state('gain') else (start, 'flatmiddle', 'flatend')
        return result if variant == 'missing_later_point' else result + ('political',)
    def equation(c, s, e, variable, state):
        if variable == 'policy':
            if variant == 'unknown_policy_equation': raise ValueError('Unknown policy equation')
            return bool(table & (1 << (2 * int(state('causeone')) + int(state('causetwo')))))
        return old['iapequations'](c, s, e, variable, state)
    def last(c, s, e, state):
        if variant == 'unknown_last': raise ValueError('Unknown political end')
        return path(state)[1] if variant == 'early' else old['ianend'](c, s, e, state) if variant == 'simultaneous' else 'political'
    def normpoint(c, s, e, state, point):
        if calls is not None: calls.append(('normpoint', c, s, e, tuple(state(x) for x in variables), point))
        if point == 'political': return 'normchanged' if state('policy') else 'normkept'
        return 'normbase'
    def reviewed(source, actor, office, code, point):
        if calls is not None: calls.append(('review', source, actor, office, code, point))
        if variant == 'unknown_off_review' and point == 'normkept': raise ValueError('Unknown off-side norm assessment')
        if variant == 'unreviewed_off' and point == 'normkept': return False
        if variant == 'unreviewed_new_off' and point == 'normkept' and thinking.code_is(code, 'jpnew'): return False
        return (source, actor, office) == ('norm', 'government', 'office') and point in ('normbase', 'normchanged', 'normkept') and any(
            thinking.code_is(code, name) for name in ('jpold', 'jpnew'))
    def required(source, actor, office, code, bindings, polarity, point):
        if calls is not None: calls.append(('norm', source, actor, office, code, bindings.items, polarity, point))
        if variant == 'unknown_off_norm' and point == 'normkept': raise ValueError('Unknown off-side norm')
        expected_actor = 'other' if variant == 'wrong_government' else 'government'
        if (source, actor, office) != ('norm', expected_actor, 'office') or bindings.items or not polarity: return False
        if thinking.code_is(code, 'jpold'): return point in ('normbase', 'normkept') or variant == 'old_retained'
        if thinking.code_is(code, 'jpnew'): return point == 'normchanged'
        return False
    def rest(reading, community, contributors, anchor, start, end, late):
        if calls is not None: calls.append(('remaining', reading, community, contributors.items, anchor, start, end, late))
        if variant == 'unknown_remaining': raise ValueError('Unknown dignity remainder')
        return remaining and community == 'community' and contributors.items == PEOPLE and (anchor, start, end, late) == ('end', 'end', 'after', 'political')
    def conditional_path(scene):
        result = (scene, 'middle', 'after')
        return result if variant == 'missing_later_point' else result + ('political',)
    p.update(jpcommunity=lambda: 'community', jpstart=lambda: 'end', jpend=lambda: 'after', jpactor=lambda: 'government',
        jpsource=lambda: 'norm', jpoffice=lambda: 'office', jpperson=lambda: 'person', jpprobes=lambda point: point == 'normbase',
        jpremaining=rest, iapvariables=lambda c, s, e: SequenceValue(variables, '"individual"'), iapequations=equation,
        iapobserved=lambda c, s, e: FunctionValue(('individual',), 'truth', lambda x: x in variables),
        ianhistory=lambda c, s, e, state, point: point in path(state),
        ianbefore=lambda c, s, e, state, left, right: left in path(state) and right in path(state) and path(state).index(left) < path(state).index(right),
        iaqhistory=lambda c, a, s, point: (c, a) == ('community', 'end') and s in joint.BEGINS.values() and point in conditional_path(s),
        iaqbefore=lambda c, a, s, l, r: (c, a) == ('community', 'end') and s in joint.BEGINS.values() and l in conditional_path(s) and r in conditional_path(s) and conditional_path(s).index(l) < conditional_path(s).index(r),
        iaslast=last, iasnormpoint=normpoint, iasreviewed=reviewed, h7k=required)
    return p, domain, scenes


def source_values(table=8, *, indices=(0, 1, 2), **options):
    p, domain, scenes = source_model(table, **options)
    doc = deepcopy(source_fixture()); doc['statements'] = [doc['statements'][i] for i in indices]
    p = {d['name']: p.get(d['name'], thinking.forbidden) for d in doc['declarations'] if d['kind'] == 'primitive'}
    return evaluate(doc, p, domain, scenes, budget=60_000_000)


def attribution(path=CORE, variant='baseline'):
    doc = deepcopy(document(path)); doc['statements'] = doc['statements'][-1:]
    p = {d['name']: thinking.forbidden for d in doc['declarations'] if d['kind'] == 'primitive'}
    p.update(iagnode=lambda: 'other' if variant == 'node' else 'node', wa=lambda: 'other' if variant == 'author' else 'author',
        iagscope=lambda: 'other' if variant == 'scope' else 'scope', wh=lambda: 'outside' if variant == 'context' else 'end',
        iasreport=lambda node, author, code, scope, point: (node, author, scope, point) == ('node', 'author', 'scope', 'end') and thinking.code_is(code, 'iasschema', 2))
    return [r['value'] for r in evaluate_document(doc, individuals=thinking.DOMAIN, situations=thinking.SCENES, primitives=p)]


def alignment():
    unit = next(u for u in json.loads((ROOT / UNITS).read_text(encoding='utf-8'))['units'] if u['id'] == 'kant-1784:u0017')
    return dict(unit=unit['id'], text_sha256=unit['text_sha256'], status='explicit_interpretive_annotation',
        definitions=['iaschecked', 'iaseffect', 'iascausal', 'iasschema', 'iasattribution'], adds_new_text_coverage=False,
        semantic_completion=False, political_causal_template_connected=True, dignity_content_unfilled=True)


def build_report():
    documents = {}
    for path, text in build().items():
        assert (ROOT / path).read_text(encoding='utf-8') == text
        doc = parse(text)
        for notation in ('full', 'compact'):
            form = format_graph(doc, notation)
            assert parse(form) == doc and parse(transcribe(form, alphabet='v2')) == doc
        documents[path] = dict(declarations=len(doc['declarations']), statements=len(doc['statements']), characters=len(text))
    assert json.loads((ROOT / BASIS).read_text(encoding='utf-8')) == basis()
    for table in range(16): assert values(table) == [table in (8, 10, 12, 14)]
    assert values(memoize=False) == values()
    assert source_values() == [True, True, True]
    assert source_values(indices=(3,)) == [True]
    assert source_values(15) == [False, True, True]
    assert source_values(variant='simultaneous') == [False, False, False]
    for path in (CORE, SOURCE):
        assert attribution(path) == [True]
        for variant in ('node', 'author', 'scope', 'context'): assert attribution(path, variant) == [False]
    parent, child = document(PARENT), document(SOURCE)
    assert child['declarations'][:len(parent['declarations'])] == parent['declarations']
    assert child['statements'][:-1] == parent['statements'][:-1]
    paths = [PARENT, LIBRARY, SOURCE, CORE, BASIS, UNITS,
        'scripts/compose_political_consequence.py', 'scripts/check_political_consequence.py', 'tests/test_political_consequence.py',
        'scripts/check_collective_conditional.py', 'scripts/check_joint_development.py', 'scripts/check_caused_choice.py',
        'noema/constructed.py', 'noema/constructed_semantics.py', 'noema/constructed_closure_semantics.py', 'noema/diagnostic_short_circuit.py']
    return dict(status='collective_conditional_and_later_normative_dependency_checked', documents=documents,
        causal_tables=16, source_alignment=alignment(), roundtrips=True, uncached_generic_baseline_checked=True,
        limitations=basis()['limitations'], verified_full_units={'kant-1784': 0, 'einstein-1905': 0},
        source_sha256={p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in paths})


def main():
    cli = argparse.ArgumentParser(description=__doc__); cli.add_argument('--verify-only', action='store_true'); args = cli.parse_args()
    report = build_report()
    if args.verify_only: assert json.loads(REPORT.read_text(encoding='utf-8')) == report
    else:
        with REPORT.open('x', encoding='utf-8', newline='\n') as stream:
            json.dump(report, stream, ensure_ascii=False, indent=2); stream.write('\n')
    print('Later political dependency checked; government identity, dignity and full source semantics remain incomplete')


if __name__ == '__main__': main()
