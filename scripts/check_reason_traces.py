"""Exercise the Noema-defined reason checker, never a Python proof substitute."""
from copy import deepcopy
from fractions import Fraction
from functools import lru_cache
from itertools import product
import argparse
import hashlib
import json

from noema.constructed import parse, format_graph
from noema.constructed_semantics import evaluate_document, Content, FunctionValue, SequenceValue
from noema.script import transcribe
from scripts.compose_reason_traces import ROOT, PARENT, SOURCE, BASIS, TRACE, JUDGED, build, basis
from scripts.compose_limits import call as k

REPORT = ROOT / 'reports/reason-traces-v1.json'
SCENES = ('before', 'after')
DOMAIN = ('person', 'judgment', 'reason', 'topic', 'other', 'p', 'i', 'q', 'c', 'bad')
P, Q, ALIAS = 'r[k jap[]]', 'r[k jaq[]]', 'r[k jaalias[]]'
FORMULAS = dict(p=P, q=Q, alias=ALIAS, implication=k('rqq', P, Q), conjunction=k('rqr', P, Q), alias_implication=k('rqq', ALIAS, Q))
CASES = {
    'mp': dict(steps=('p', 'i', 'q'), forms=dict(p='p', i='implication', q='q'), rules=dict(p=0, i=0, q=1), premises=('p', 'implication'), goal='q'),
    'and_intro': dict(steps=('p', 'q', 'c'), forms=dict(p='p', q='q', c='conjunction'), rules=dict(p=0, q=0, c=2), premises=('p', 'q'), goal='conjunction'),
    'and_left': dict(steps=('c', 'p'), forms=dict(c='conjunction', p='p'), rules=dict(c=0, p=3), premises=('conjunction',), goal='p'),
    'and_right': dict(steps=('c', 'q'), forms=dict(c='conjunction', q='q'), rules=dict(c=0, q=4), premises=('conjunction',), goal='q'),
    'premise': dict(steps=('p',), forms=dict(p='p'), rules=dict(p=0), premises=('p',), goal='p'),
    'reused_conclusion': dict(steps=('p', 'q', 'c', 'bad'), forms=dict(p='p', q='q', c='conjunction', bad='p'),
        rules=dict(p=0, q=0, c=2, bad=3), premises=('p', 'q'), goal='p'),
}
INVALID = ('empty', 'future', 'circular', 'wrong_goal', 'bad_prefix', 'alias', 'reversed', 'fractional_rule', 'missing_premise')


def case_for(name):
    row = deepcopy(CASES.get(name, CASES['mp']))
    if name == 'empty': row['steps'] = ()
    if name == 'future': row['steps'] = ('q', 'p', 'i')
    if name == 'circular': row['steps'] = ('q',)
    if name == 'wrong_goal': row['goal'] = 'p'
    if name == 'bad_prefix':
        row['steps'] = ('bad',) + row['steps']; row['forms']['bad'] = 'p'; row['rules']['bad'] = 5
    if name == 'alias':
        row['forms']['i'] = 'alias_implication'; row['premises'] = ('p', 'alias_implication')
    if name == 'reversed':
        row.update(steps=('q', 'i', 'p'), goal='p', premises=('q', 'implication'), rules=dict(q=0, i=0, p=1))
        row['forms']['p'] = 'p'
    if name == 'fractional_rule': row['rules']['q'] = Fraction(1, 2)
    if name == 'missing_premise': row['premises'] = ('p',)
    if name == 'repeat': row['steps'] += ('q',)
    if name not in {*CASES, *INVALID, 'repeat'}:
        raise ValueError('Unknown diagnostic case')
    return row


@lru_cache(maxsize=None)
def setup(name='mp', connection=False, truth=False):
    row = case_for(name)
    text = (ROOT / SOURCE).read_text(encoding='utf-8')
    text += 'r jap[] e.r jaq[] e.r jaalias[] e.r jaseed[' + ' '.join(['i[e]'] * len(FORMULAS)) + '] c.'
    text += 'r jasteps[] j[a].r japremises[i[e]] c.r jaforms[a] i[e].r jarules[a] b.r jaleft[a] i[e].r jaright[a] i[e].'
    text += 'r japerson[] a.r jasubject[] a.r jabefore[] d.r jaafter[] d.'
    text += 'r jajudgments[a a d] c.r jamatters[a a d] c.r caused[a a d] c.'
    text += 'r jaconclusions[a d] i[e].r japroofs[a d] j[a].r japremisesfor[a d] h[i[e]] c.r jaclaimed[a i[e] d] c.'
    bindings = {n: 'p ja' + n for n, _ in TRACE if n not in ('steps', 'goal')}
    bindings.update(steps=k('jasteps'), goal=FORMULAS[row['goal']])
    seed = k('jaseed', *FORMULAS.values())
    queries = [seed, k('rqu', *(bindings[n] for n, _ in TRACE)), k('rqv', *(bindings[n] for n, _ in TRACE))]
    if connection:
        bindings.update({n: 'p ja' + n for n, _ in JUDGED if n not in ('person', 'subject', 'context', 'used')})
        bindings.update(person=k('japerson'), subject=k('jasubject'), used='p caused')
        for point in ('before', 'after'):
            bindings['context'] = k('ja' + point)
            queries.append(k('rqx', *(bindings[n] for n, _ in JUDGED)))
    if truth:
        queries += ['t[s[' + FORMULAS[n] + ']][k jaafter[]]' for n in ('p', 'q', 'implication', 'conjunction')]
    doc = parse(text + ''.join('q[' + q + '].' for q in queries))
    return dict(document=doc, case=row)


def model_for(data, truths=None, variant='baseline'):
    row, stored = data['case'], {}
    def forbidden(*args):
        raise ValueError('Quoted formula was executed while checking its proof')
    model = {d['name']: forbidden for d in data['document']['declarations'] if d['kind'] == 'primitive'}
    def seed(*values):
        stored.update(zip(FORMULAS, values)); return True
    def premise(desc):
        if variant == 'unknown_premise':
            raise ValueError('Premise adoption is unknown')
        return any(desc.syntax == stored[n].syntax for n in row['premises'])
    def forms(step):
        return stored[row['forms'][step]]
    def claimed(judgment, desc, point):
        return judgment == 'judgment' and desc.syntax == stored['p' if variant == 'wrong_claim' else row['goal']].syntax
    model.update(jaseed=seed, jasteps=lambda: SequenceValue(row['steps'], '"individual"'), japremises=premise,
        jaforms=forms, jarules=lambda step: Fraction(row['rules'][step]),
        jaleft=lambda step: stored['q' if variant == 'reverse_references' else 'p'],
        jaright=lambda step: stored['p' if variant == 'reverse_references' else 'q'],
        japerson=lambda: 'person', jasubject=lambda: 'topic', jabefore=lambda: 'before', jaafter=lambda: 'after',
        jajudgments=lambda person, judgment, point: (person, judgment) == ('person', 'judgment'),
        jamatters=lambda judgment, subject, point: (judgment, subject) == ('judgment', 'other' if variant == 'wrong_subject' else 'topic'),
        caused=lambda judgment, reason, point: (judgment, reason, point) == ('other' if variant == 'wrong_user' else 'judgment', 'reason', 'after'),
        jaconclusions=lambda judgment, point: stored[row['goal']],
        japroofs=lambda reason, point: SequenceValue(row['steps'] if (reason, point) == ('other' if variant == 'wrong_reason' else 'reason', 'before' if variant == 'wrong_context' else 'after') else (), '"individual"'),
        japremisesfor=lambda reason, point: FunctionValue(({'kind':'description','result':'content'},), 'truth', premise),
        jaclaimed=claimed)
    if data['case'] == case_for('reversed'):
        model.update(jaleft=lambda step: stored['q'], jaright=lambda step: stored['p'])
    if truths is not None:
        for name, value in (('jap', truths[0]), ('jaq', truths[1]), ('jaalias', truths[0])):
            model[name] = lambda value=value: Content(SCENES, (value, value))
    return model


def values(name='mp', connection=False, truth=False, truths=None, variant='baseline'):
    data = setup(name, connection, truth)
    return [r['value'] for r in evaluate_document(data['document'], individuals=DOMAIN, situations=SCENES,
        primitives=model_for(data, truths=truths, variant=variant), max_steps=8_000_000)]


def build_report():
    text = build(); assert (ROOT / SOURCE).read_text(encoding='utf-8') == text
    assert json.loads((ROOT / BASIS).read_text(encoding='utf-8')) == basis()
    doc = parse(text)
    for notation in ('full', 'compact'):
        form = format_graph(doc, notation)
        assert parse(form) == doc and parse(transcribe(form, alphabet='v2')) == doc
    cases = {}
    for name in (*CASES, *INVALID, 'repeat'):
        result = values(name)
        valid = name not in INVALID
        assert result == [True, valid, valid and name != 'premise'], (name, result)
        cases[name] = result
    soundness = []
    for name in CASES:
        for truths in product((False, True), repeat=2):
            result = values(name, truth=True, truths=truths)
            valuation = dict(zip(('p', 'q', 'implication', 'conjunction'), result[-4:]))
            row = CASES[name]
            assert not all(valuation[p] for p in row['premises']) or valuation[row['goal']]
            soundness.append(dict(case=name, truths=list(truths), result=result))
    connections = {}
    for variant in ('baseline', 'wrong_claim', 'wrong_subject', 'wrong_user', 'wrong_reason', 'wrong_context'):
        result = values(connection=True, variant=variant)
        assert result == [True, True, True, False, variant == 'baseline'], (variant, result)
        connections[variant] = result
    direct_assumption = values('reused_conclusion', connection=True)
    assert direct_assumption == [True, True, True, False, False]
    paths = [PARENT, SOURCE, BASIS, 'scripts/compose_reason_traces.py', 'scripts/check_reason_traces.py', 'tests/test_reason_traces.py',
        'noema/constructed.py', 'noema/constructed_discourse.py', 'noema/constructed_semantics.py', 'noema/guarded_ranked_semantics.py',
        'scripts/compose_origin_clock.py', 'scripts/compose_limits.py', 'scripts/compose_situated_criticism.py']
    return dict(status='checked_finite_deductive_reason_traces_not_general_insight', document=SOURCE,
        declarations=len(doc['declarations']), characters=len(text), new_definitions=9, new_primitives=0,
        revised_author_statements=0, roundtrips=True, certificates=cases, truth_tables=soundness, same_judgment_connections=connections,
        conclusion_as_premise_valid_but_not_independent_support=direct_assumption,
        source_note=dict(status='support_library_not_a_new_source_alignment', concerns='Kant u0015 Einsichten and existing ya reason support',
            semantic_completion=False), limitations=basis()['unresolved'], verified_semantic_units=0,
        source_sha256={p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in paths})


def main():
    cli = argparse.ArgumentParser(description=__doc__); cli.add_argument('--verify-only', action='store_true'); args = cli.parse_args()
    result = build_report()
    if args.verify_only:
        assert json.loads(REPORT.read_text(encoding='utf-8')) == result
    else:
        with REPORT.open('x', encoding='utf-8', newline='\n') as stream:
            json.dump(result, stream, ensure_ascii=False, indent=2); stream.write('\n')
    print('Noema reason traces, truth tables, and judgment bindings verified')


if __name__ == '__main__':
    main()
