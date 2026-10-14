"""Check local hypotheses, discharge and scope-sensitive reuse in Noema."""
from copy import deepcopy
from fractions import Fraction
from functools import lru_cache
from itertools import product
import argparse
import hashlib
import json

from noema.constructed import parse, format_graph
from noema.constructed_semantics import Content, FunctionValue, SequenceValue, evaluate_document
from noema.script import transcribe
from scripts.compose_scoped_reasons import ROOT, PARENT, SOURCE, CORE, EXAMPLE, BASIS, TRACE, JUDGED, build, basis
from scripts.compose_limits import call as k
from scripts.check_reason_traces import FORMULAS as OLD_FORMULAS, CASES as OLD_CASES, INVALID as OLD_INVALID, case_for as old_case
from scripts.check_reason_traces import setup as old_setup, model_for as old_model, DOMAIN as OLD_DOMAIN

REPORT = ROOT / 'reports/scoped-reasons-v1.json'
FORMULAS = dict(OLD_FORMULAS)
P, Q, C = FORMULAS['p'], FORMULAS['q'], FORMULAS['conjunction']
FORMULAS.update(identity=k('rqq', P, P), q_to_p=k('rqq', Q, P), conjunction_to_p=k('rqq', C, P))
FORMULAS.update(nested=k('rqq', P, FORMULAS['q_to_p']), duplicate=k('rqq', P, FORMULAS['identity']))
SCENES = ('before', 'after')
DTYPE = {'kind': 'description', 'result': 'content'}
CANON_DESC = json.dumps(DTYPE, sort_keys=True, separators=(',', ':'))


def line(form, scope, rule, left='p', right='q', base=()):
    return dict(form=form, scope=tuple(scope), rule=rule, left=left, right=right, base=tuple(base))


def example(rows, goal, premises=()):
    return dict(rows=rows, goal=goal, premises=tuple(premises))


CASES = {
    'identity': example([line('p', ('p',), 5), line('identity', (), 6, 'p', 'p')], 'identity'),
    'nested': example([line('p', ('p',), 5), line('p', ('p', 'q'), 7, 'q', 'p', ('p',)),
        line('q_to_p', ('p',), 6, 'q', 'p'), line('nested', (), 6, 'p', 'q_to_p')], 'nested'),
    'outer_assumption': example([line('p', ('p', 'q'), 5), line('q_to_p', ('p',), 6, 'q', 'p'),
        line('nested', (), 6, 'p', 'q_to_p')], 'nested'),
    'duplicate': example([line('p', ('p', 'p'), 5), line('identity', ('p',), 6, 'p', 'p'),
        line('duplicate', (), 6, 'p', 'identity')], 'duplicate'),
    'conjunction': example([line('conjunction', ('conjunction',), 5), line('p', ('conjunction',), 3),
        line('conjunction_to_p', (), 6, 'conjunction', 'p')], 'conjunction_to_p'),
    'vacuous': example([line('q', ('p',), 0), line('implication', (), 6)], 'implication', ('q',)),
    'weakening': example([line('q', (), 0), line('q', ('p',), 7, 'p', 'q'), line('implication', (), 6)], 'implication', ('q',)),
    'scoped_mp': example([line('implication', (), 0), line('implication', ('p',), 7), line('p', ('p',), 5),
        line('q', ('p',), 1), line('implication', (), 6)], 'implication', ('implication',)),
    'unused_local_goal': example([line('identity', ('identity',), 5), line('p', ('p',), 5),
        line('identity', (), 6, 'p', 'p')], 'identity'),
}
INVALID = ('unclosed', 'forged_release', 'wrong_discharge', 'different_assumption', 'scope_mix', 'future',
    'wrong_order', 'collapsed_duplicate', 'alias_scope', 'bad_prefix', 'open_after_closed', 'wrong_goal', 'empty', 'fractional_rule')


def case_for(name):
    if name.startswith('old_'):
        old = old_case(name[4:]); reversed_ = name == 'old_reversed'
        return example([line(old['forms'][step], (), old['rules'][step], 'q' if reversed_ else 'p', 'p' if reversed_ else 'q')
            for step in old['steps']], old['goal'], old['premises'])
    if name in CASES: return deepcopy(CASES[name])
    case = deepcopy(CASES['identity'])
    if name == 'unclosed': case = example(case['rows'][:1], 'p')
    elif name == 'forged_release': case = example([line('p', ('p',), 5), line('p', (), 7, 'p', 'q', ('p',))], 'p')
    elif name == 'wrong_discharge': case['rows'][-1] = line('implication', (), 6); case['goal'] = 'implication'
    elif name == 'different_assumption': case['rows'][-1] = line('q_to_p', (), 6, 'q', 'p'); case['goal'] = 'q_to_p'
    elif name == 'scope_mix': case = example([line('implication', (), 0), line('p', ('p',), 5), line('q', ('p',), 1), line('implication', (), 6)], 'implication', ('implication',))
    elif name == 'future': case['rows'].reverse()
    elif name == 'wrong_order':
        case = deepcopy(CASES['outer_assumption']); case['rows'][0]['scope'] = ('q', 'p')
    elif name == 'collapsed_duplicate':
        case = deepcopy(CASES['duplicate']); case['rows'][0]['scope'] = ('p',)
    elif name == 'alias_scope': case['rows'][0]['scope'] = ('alias',)
    elif name == 'bad_prefix': case['rows'].insert(0, line('p', (), 8))
    elif name == 'open_after_closed': case['rows'].append(line('p', ('p',), 5)); case['goal'] = 'p'
    elif name == 'wrong_goal': case['goal'] = 'p'
    elif name == 'empty': case['rows'] = []
    elif name == 'fractional_rule': case['rows'][0]['rule'] = Fraction(1, 2)
    else: raise ValueError('Unknown diagnostic example')
    return case


@lru_cache(maxsize=None)
def setup(name='identity', connection=False, truth=False):
    case = case_for(name)
    text = (ROOT / CORE).read_text(encoding='utf-8')
    text += 'r jap[] e.r jaq[] e.r jaalias[] e.r jaseed[' + ' '.join(['i[e]'] * len(FORMULAS)) + '] c.'
    text += 'r jasteps[] j[a].r japremises[i[e]] c.r jaforms[a] i[e].r jarules[a] b.r jaleft[a] i[e].r jaright[a] i[e].'
    text += 'r jascopes[a] j[i[e]].r jabases[a] j[i[e]].'
    text += 'r japerson[] a.r jasubject[] a.r jabefore[] d.r jaafter[] d.'
    text += 'r jajudgments[a a d] c.r jamatters[a a d] c.r caused[a a d] c.'
    text += 'r jaconclusions[a d] i[e].r japroofs[a d] j[a].r japremisesfor[a d] h[i[e]] c.r jaclaimed[a i[e] d] c.'
    refs = {n: 'p ja' + n for n, _ in TRACE if n not in ('steps', 'goal')}
    refs.update(steps=k('jasteps'), goal=FORMULAS[case['goal']])
    queries = [k('jaseed', *FORMULAS.values())] + [k(check, *(refs[n] for n, _ in TRACE)) for check in ('rrc', 'rrd', 'rre')]
    if connection:
        refs.update({n: 'p ja' + n for n, _ in JUDGED if n not in ('person', 'subject', 'context', 'used')})
        refs.update(person=k('japerson'), subject=k('jasubject'), used='p caused')
        for point in SCENES:
            refs['context'] = k('ja' + point); queries.append(k('rrg', *(refs[n] for n, _ in JUDGED)))
    if truth:
        queries += ['t[s[' + form + ']][k jaafter[]]' for form in FORMULAS.values()]
    return dict(document=parse(text + ''.join('q[' + q + '].' for q in queries)), case=case,
        ids=tuple('step' + str(i) for i in range(len(case['rows']))))


def model_for(data, truths=None, variant='baseline'):
    case, ids, stored = data['case'], data['ids'], {}
    records = dict(zip(ids, case['rows']))
    def forbidden(*args): raise ValueError('Quoted proposition was executed by the scope checker')
    def seed(*items): stored.update(zip(FORMULAS, items)); return True
    def scopes(step):
        if variant == 'unknown_scope': raise ValueError('Hypothesis scope is unknown')
        return SequenceValue(tuple(stored[n] for n in records[step]['scope']), CANON_DESC)
    def premise(desc):
        if variant == 'unknown_premise': raise ValueError('Premise adoption is unknown')
        return any(desc.syntax == stored[n].syntax for n in case['premises'])
    model = {d['name']: forbidden for d in data['document']['declarations'] if d['kind'] == 'primitive'}
    model.update(jaseed=seed, jasteps=lambda: SequenceValue(ids, '"individual"'), japremises=premise,
        jaforms=lambda step: stored[records[step]['form']], jarules=lambda step: Fraction(records[step]['rule']),
        jaleft=lambda step: stored[records[step]['left']], jaright=lambda step: stored[records[step]['right']],
        jascopes=scopes, jabases=lambda step: SequenceValue(tuple(stored[n] for n in records[step]['base']), CANON_DESC),
        japerson=lambda: 'person', jasubject=lambda: 'topic', jabefore=lambda: 'before', jaafter=lambda: 'after',
        jajudgments=lambda person, judgment, point: (person, judgment) == ('person', 'judgment'),
        jamatters=lambda judgment, subject, point: (judgment, subject) == ('judgment', 'other' if variant == 'wrong_subject' else 'topic'),
        caused=lambda judgment, reason, point: (judgment, reason, point) == ('other' if variant == 'wrong_user' else 'judgment', 'reason', 'after'),
        jaconclusions=lambda judgment, point: stored[case['goal']],
        japroofs=lambda reason, point: SequenceValue(ids if (reason, point) == ('other' if variant == 'wrong_reason' else 'reason', 'before' if variant == 'wrong_context' else 'after') else (), '"individual"'),
        japremisesfor=lambda reason, point: FunctionValue((DTYPE,), 'truth', premise),
        jaclaimed=lambda judgment, desc, point: judgment == 'judgment' and desc.syntax == stored['p' if variant == 'wrong_claim' else case['goal']].syntax)
    if truths is not None:
        for name, value in (('jap', truths[0]), ('jaq', truths[1]), ('jaalias', truths[0])):
            model[name] = lambda value=value: Content(SCENES, (value, value))
    return model


def values(name='identity', connection=False, truth=False, truths=None, variant='baseline'):
    data = setup(name, connection, truth)
    return [r['value'] for r in evaluate_document(data['document'], individuals=('person', 'judgment', 'reason', 'topic', 'other') + data['ids'],
        situations=SCENES, primitives=model_for(data, truths, variant), max_steps=8_000_000)]


def previous_values(name):
    data = deepcopy(old_setup(name))
    independent = deepcopy(data['document']['statements'][-1]); independent['body']['symbol'] = 'rqy'
    data['document']['statements'].append(independent)
    return [r['value'] for r in evaluate_document(data['document'], individuals=OLD_DOMAIN, situations=SCENES, primitives=old_model(data))]


def written_example(variant='baseline'):
    doc = parse((ROOT / EXAMPLE).read_text(encoding='utf-8'))
    model = dict(jrfirst=lambda: 'first', jrsecond=lambda: 'second', jrcontext=lambda: 'point',
        jrrule=lambda step: Fraction(5 if step == 'first' else (0 if variant == 'wrong_rule' else 6)),
        jrselect=lambda step, p, implication: p if step == 'first' else implication,
        jrscopeselect=lambda step, p: SequenceValue((p,) if step == 'first' or variant == 'open_scope' else (), CANON_DESC))
    return evaluate_document(doc, individuals=('first', 'second'), situations=('point',), primitives=model)


def build_report():
    texts = build(); assert json.loads((ROOT / BASIS).read_text(encoding='utf-8')) == basis()
    documents = {}
    for path, text in texts.items():
        assert (ROOT / path).read_text(encoding='utf-8') == text
        doc = parse(text)
        for notation in ('full', 'compact'):
            form = format_graph(doc, notation)
            assert parse(form) == doc and parse(transcribe(form, alphabet='v2')) == doc
        documents[path] = dict(declarations=len(doc['declarations']), statements=len(doc['statements']), characters=len(text))
    parent = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    assert parse(texts[SOURCE])['declarations'][:len(parent['declarations'])] == parent['declarations']
    cases, invalid, parity, connections, truth_tables = {}, {}, {}, {}, []
    for name in CASES:
        actual = values(name); assert actual == [True, True, True, name != 'scoped_mp'], (name, actual)
        cases[name] = actual
        for truths in product((False, True), repeat=2):
            result = values(name, truth=True, truths=truths)
            valuation = dict(zip(FORMULAS, result[4:]))
            premises_hold = all(valuation[n] for n in CASES[name]['premises'])
            for record in CASES[name]['rows']:
                assert not (premises_hold and all(valuation[n] for n in record['scope'])) or valuation[record['form']]
            assert not premises_hold or valuation[CASES[name]['goal']]
            truth_tables.append(dict(case=name, truths=list(truths), result=result))
    for name in INVALID:
        result = values(name); assert result == [True, False, False, False], (name, result)
        invalid[name] = result
    for name in (*OLD_CASES, *OLD_INVALID, 'repeat'):
        old, new = previous_values(name), values('old_' + name)
        assert old == new, (name, old, new)
        parity[name] = dict(previous=old, empty_scope=new)
    for variant in ('baseline', 'wrong_claim', 'wrong_subject', 'wrong_user', 'wrong_reason', 'wrong_context'):
        result = values(connection=True, variant=variant)
        assert result == [True, True, True, True, False, variant == 'baseline'], (variant, result)
        connections[variant] = result
    written = written_example()
    assert written == [{'kind':'assert','value':True}] * 7 + [{'kind':'ask','value':x} for x in (True, True, False, True)]
    paths = [PARENT, SOURCE, CORE, EXAMPLE, BASIS, 'scripts/compose_scoped_reasons.py', 'scripts/check_scoped_reasons.py',
        'scripts/compose_reason_traces.py', 'scripts/check_reason_traces.py', 'tests/test_scoped_reasons.py',
        'reports/reason-traces-v1.json', 'noema/constructed.py', 'noema/constructed_discourse.py', 'noema/constructed_semantics.py',
        'noema/guarded_ranked_semantics.py', 'noema/extraction.py', 'scripts/compose_origin_clock.py', 'scripts/compose_limits.py', 'scripts/compose_situated_criticism.py']
    return dict(status='scoped_reason_records_with_hypothesis_discharge', documents=documents,
        new_library_definitions=7, new_library_primitives=0, example_record_definitions=2, example_data_symbols=6,
        preserved_parent_declarations=True, revised_author_statements=0, roundtrips=True, valid_cases=cases,
        rejected_cases=invalid, empty_scope_comparisons=parity, truth_tables=truth_tables, judgment_connections=connections,
        written_proof_record=written,
        source_note=dict(status='support_library_not_new_source_alignment', semantic_completion=False),
        limitations=basis()['unresolved'], verified_semantic_units=0,
        source_sha256={p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in paths})


def main():
    cli = argparse.ArgumentParser(description=__doc__); cli.add_argument('--verify-only', action='store_true'); args = cli.parse_args()
    result = build_report()
    if args.verify_only: assert json.loads(REPORT.read_text(encoding='utf-8')) == result
    else:
        with REPORT.open('x', encoding='utf-8', newline='\n') as stream:
            json.dump(result, stream, ensure_ascii=False, indent=2); stream.write('\n')
    print('Scoped hypotheses, discharge, judgment connection and truth tables verified')


if __name__ == '__main__': main()
