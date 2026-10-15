"""Check joint success against causal protection using actual Noema definitions."""
import argparse
from copy import deepcopy
from functools import lru_cache
from fractions import Fraction
import hashlib
from itertools import product
import json

from noema.constructed import parse, format_graph
from noema.constructed_semantics import evaluate_document, SequenceValue, Content, FunctionValue
from noema.script import transcribe
from scripts.compose_collective_protection import ROOT, LIBRARY, EXAMPLE, BASIS, JOINT, PROTECTION, build, basis

REPORT = ROOT / 'reports/collective-protection-v1.json'
VARIABLES = ('pf', 'tf', 'sf')
DOMAIN = ('m1', 'm2', 'chief', 'group', 'plan', 'other', *VARIABLES)
ASSIGNMENTS = tuple(product((False, True), repeat=3))
SCENES = ('anchor', *['w' + ''.join(str(int(b)) for b in row) for row in ASSIGNMENTS])
PROTECT = (True, True, False, False, True, True, True, True)


@lru_cache(maxsize=1)
def setup(): return parse((ROOT / EXAMPLE).read_text(encoding='utf-8'))


def oracle(table):
    solutions = {(p, t): [s for s in (False, True) if s == table[4*int(p)+2*int(t)+int(s)]]
        for p, t in product((False, True), repeat=2)}
    return bool(all(solutions.values()) and all(solutions[False, False]) and not any(solutions[False, True])
        and all(solutions[True, False]) and all(solutions[True, True]))


def values(table=PROTECT, variant='baseline', *, indices=None, memoize=True):
    doc = deepcopy(setup())
    if indices is not None: doc['statements'] = [doc['statements'][i] for i in indices]
    def forbidden(*args): raise AssertionError('Unexpected primitive')
    model = {d['name']: forbidden for d in doc['declarations'] if d['kind'] == 'primitive'}
    def bits(point): return tuple(ch == '1' for ch in point[1:]) if point.startswith('w') else (False, False, True)
    def equation(item, state):
        if variant == 'unknown_mechanism': raise ValueError('Unknown mechanism')
        if item == 'sf': return table[4*int(state('pf'))+2*int(state('tf'))+int(state('sf'))]
        if item == 'tf' and variant == 'preventive': return False
        return item in VARIABLES and variant != 'unintervened_mismatch'
    def execution(planner, group, person, plan, anchor, point):
        if variant == 'unknown_execution': raise ValueError('Unknown execution')
        expected = ('m1' if variant == 'wrong_planner' else 'chief', 'other' if variant == 'wrong_group' else 'group',
            'other' if variant in ('wrong_plan','only_other_plan') else 'plan', 'w000' if variant == 'wrong_anchor' else 'anchor')
        if (planner, group, plan, anchor) != expected or person not in ('m1', 'm2'): return False
        if variant == 'missing_member_activity' and person == 'm2': return False
        if variant == 'comparison_member_mismatch' and person == 'm2' and point == 'w101': return False
        return bits(point)[0]
    def activity(point): return bits(point)[2] and not (variant == 'comparison_activity_mismatch' and point == 'w001')
    def threat(point): return bits(point)[1] != (variant == 'comparison_threat_mismatch' and point == 'w010')
    def content(fn): return Content(SCENES, tuple(fn(point) for point in SCENES))
    def record(point):
        if variant == 'unknown_record': raise ValueError('Unknown record')
        row = bits('w000' if variant == 'wrong_record' else point)
        def value(item):
            if variant == 'record_outside_variables' and item == 'chief': return True
            return row[VARIABLES.index(item)] if item in VARIABLES else False
        return FunctionValue(('individual',), 'truth', value)
    def selected(planner, group, plan, anchor, point):
        points = ('w101',) if variant == 'preventive' else ('w111','w101') if variant == 'one_bad_record' else ('w111',)
        chosen = 'other' if variant == 'only_other_plan' else 'plan'
        return variant != 'empty_selected' and (planner, group, plan, anchor) == ('chief', 'group', chosen, 'anchor') and point in points
    def outcomes(planner, group, plan, anchor, point):
        return variant != 'outside_outcomes' and selected(planner, group, plan, anchor, point)
    members = {'duplicate_member': ('m1', 'm1', 'm2'), 'missing_member': ('m1',), 'empty_members': ()}.get(variant, ('m1', 'm2'))
    variables = {'duplicate_variable': (*VARIABLES, 'pf'), 'missing_threat': ('pf', 'sf')}.get(variant, VARIABLES)
    model.update(ha=lambda a,b: a+b, hc=lambda a,b: a<b, hd=lambda truth: Fraction(int(truth)),
        jgplanner=lambda: 'chief', jggroup=lambda: 'group', jgmembers=lambda: SequenceValue(members, '"individual"'),
        jganchor=lambda: 'anchor', jgplan=lambda: 'plan',
        jgmembersof=lambda group, person, anchor: (group, anchor) == ('group', 'anchor') and person in ('m1', 'm2'),
        jgavailable=lambda planner, group, plan, anchor: variant != 'unavailable' and (planner,group,plan,anchor) ==
            ('chief','group','other' if variant == 'only_other_plan' else 'plan','anchor'),
        jgoutcomes=outcomes, jgselected=selected, jgexecuted=execution,
        jgvariables=lambda: SequenceValue(variables, '"individual"'), jgequations=equation,
        jgfactor=lambda: 'pf', jgthreatfactor=lambda: 'pf' if variant == 'same_factors' else 'tf',
        jgmodelgoal=lambda state: state('sf'),
        jgworlds=lambda state: 'w000' if variant == 'wrong_worlds' else 'w'+''.join(str(int(state(item))) for item in VARIABLES),
        jgactivity=lambda: content(activity), jgthreat=lambda: content(threat), jgrecords=record)
    return [r['value'] for r in evaluate_document(doc, individuals=DOMAIN, situations=SCENES, primitives=model,
        max_steps=50_000_000, memoize_definitions=memoize, memoize_expressions=memoize)]


def build_report():
    documents = {}
    for path, text in build().items():
        assert (ROOT/path).read_text(encoding='utf-8') == text
        doc = parse(text)
        for notation in ('full','compact'):
            form = format_graph(doc,notation)
            assert parse(form) == doc and parse(transcribe(form,alphabet='v2')) == doc
        documents[path] = dict(declarations=len(doc['declarations']), statements=len(doc['statements']), characters=len(text))
    assert json.loads((ROOT/BASIS).read_text(encoding='utf-8')) == basis()
    matrix = []
    for corners in product((False, True), repeat=4):
        table = tuple(corners[2*int(p)+int(t)] for p,t,s in ASSIGNMENTS)
        result = values(table)
        assert result == [False,True,oracle(table),oracle(table),oracle(table),oracle(table),True], (corners,result)
        matrix.append(dict(corners=corners,result=result))
    contrasts = {}
    for name in ('comparison_member_mismatch','comparison_activity_mismatch','comparison_threat_mismatch','wrong_worlds',
                 'same_factors','duplicate_variable','missing_threat'):
        result = values(variant=name)
        assert result == [False,True,False,False,False,False,True], (name,result)
        contrasts[name] = result
    for name in ('missing_member_activity','wrong_planner','wrong_group','wrong_plan','wrong_anchor','duplicate_member',
                 'missing_member','empty_members','empty_selected','outside_outcomes','unavailable'):
        result = values(variant=name)
        assert result == [False,False,False,False,False,False,True], (name,result)
        contrasts[name] = result
    for name, table in [('multiple_solutions', tuple(row[2] for row in ASSIGNMENTS)),
                        ('no_solution', tuple(not row[2] for row in ASSIGNMENTS))]:
        result = values(table)
        assert not oracle(table) and result == [False,True,False,False,False,False,True]
        contrasts[name] = result
    for name in ('wrong_record','record_outside_variables','unintervened_mismatch','one_bad_record'):
        result = values(variant=name)
        assert result == [False,True,True,True,False,False,True], (name,result)
        contrasts[name] = result
    contrasts['preventive'] = values(variant='preventive')
    assert contrasts['preventive'] == [False,True,True,True,True,True,True]
    contrasts['only_other_plan'] = values(variant='only_other_plan')
    assert contrasts['only_other_plan'] == [False,False,False,True,False,True,True]
    for name in ('unknown_execution','unknown_mechanism','unknown_record'): assert values(variant=name,indices=(6,)) == [True]
    paths = [LIBRARY,EXAMPLE,BASIS,JOINT,PROTECTION,'scripts/compose_collective_protection.py',
        'scripts/check_collective_protection.py','tests/test_collective_protection.py',
        'noema/constructed.py','noema/constructed_discourse.py','noema/constructed_semantics.py','noema/guarded_ranked_semantics.py']
    return json.loads(json.dumps(dict(status='specified_protective_comparison_not_full_public_peace',documents=documents,
        matrix=matrix,contrasts=contrasts,roundtrips=True,independent_solution_oracle=True,
        limitations=basis()['limitations'],source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in paths})))


def main():
    cli = argparse.ArgumentParser(description=__doc__); cli.add_argument('--verify-only',action='store_true');args=cli.parse_args()
    result = build_report()
    if args.verify_only: assert json.loads(REPORT.read_text(encoding='utf-8')) == result
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream: json.dump(result,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print('Joint activity, protective comparisons and shared content verified')


if __name__ == '__main__': main()
