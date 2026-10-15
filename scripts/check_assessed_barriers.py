"""Check causal barriers, complete method assessment and appearance together."""
import argparse
from copy import deepcopy
from functools import lru_cache
import hashlib
from itertools import product
import json
from noema.constructed import parse,format_graph
from noema.constructed_semantics import evaluate_document,FunctionValue,SequenceValue
from noema.script import transcribe
from noema.diagnostic_short_circuit import lower
from scripts.compose_assessed_barriers import ROOT,PARENT,LIBRARY,SOURCE,CORE,BASIS,build,basis
from scripts.compose_qualified_utterance import closure
from scripts import check_apparent_liberty as previous

REPORT=ROOT/'reports/assessed-barriers-v1.json'
DOMAIN=previous.DOMAIN+('factor','opportunity','unassessed')
SCENES=previous.SCENES+('offfail','offsuccess','onsuccess','lf','hs','lc')


@lru_cache(maxsize=4)
def document(path):return parse((ROOT/path).read_text(encoding='utf-8'))


@lru_cache(maxsize=1)
def fixture():
    doc=deepcopy(previous.fixture());doc['statements']=[];names={d['name'] for d in doc['declarations']}
    for d in closure(document(SOURCE),['iadcontrast']):
        if d['name'] not in names:doc['declarations'].append(d);names.add(d['name'])
    q=['t[k iacappearance[]][k jalanchor[]]','k iadaligned[k jalanchor[]]',
       'k iadbarrier[k jalperson[] k jalactivity[] k jalanchor[]]','k iadboundaries[k jalanchor[]]',
       't[k iadcontrast[]][k jalanchor[]]',
       'k xe[k jalperson[] k iachigher[k jalanchor[]] p iacavailable p iacprospects p iacevaluated]',
       'k xg[k jalperson[] k iacgoal[k jalperson[] k jalactivity[]] k iachigher[k jalanchor[]] p iacavailable p iacprospects p iacevaluated]',
       'e[r d[k iadcontrast[]]][r d[k iadcontrast[]]]']
    return parse(format_graph(doc,'compact')+''.join('q['+x+'].' for x in q))


def model(*,table=3,appearance=True,off_success=True,observed_on=True,variant='baseline'):
    primitives=previous.model(mental_view=appearance)
    old_higher=primitives['iachigher'];old_lower=primitives['iaclower'];old_allowed=primitives['iacallowed']
    old_available=primitives['iacavailable'];old_evaluated=primitives['iacevaluated']
    points={'offfail':'lf','offsuccess':'lc' if variant=='changed_off_regime' else 'l0','anchor':'h0','onsuccess':'hs'}
    def higher(view):return points[view] if view in points else old_higher(view)
    def lower_point(view):return 'l0' if view in points else old_lower(view)
    def state_view(state):
        if variant=='unknown_mapping':raise ValueError('Unknown state mapping')
        index=2*int(state('factor'))+int(state('opportunity'))
        return ['offfail','anchor' if variant=='wrong_mapping' else 'offsuccess','anchor','onsuccess'][index]
    def observed(view):
        if variant=='unknown_observation':raise ValueError('Unknown observation')
        def state(variable):
            return (variable=='factor' and observed_on) or (variable=='opportunity' and variant=='inconsistent_observation') or (variable=='other' and variant=='outside_observation')
        return FunctionValue(('individual',),'truth',state)
    def equations(variable,state):
        if variant=='unknown_equations':raise ValueError('Unknown equation')
        if variable=='factor':return True
        return bool(table&(1<<(2*int(state('factor'))+int(state('opportunity')))))
    def allowed(*args):
        args=list(args);scene=args[-1]
        if variant=='unknown_norm':raise ValueError('Unknown permission')
        if variant=='changed_off_regime' and scene=='lc' and args[3]=='a':return False
        args[-1]='h0' if scene=='hs' else 'l0' if scene in ('lf','lc') else scene
        return old_allowed(*args)
    def available(person,method,scene):
        if variant=='unknown_methods':raise ValueError('Unknown method availability')
        if variant=='no_methods_on' and scene=='h0':return False
        if person=='p1' and method=='unassessed':
            return variant=='unassessed_on' and scene=='h0' or variant=='unassessed_off' and scene=='l0'
        if person=='p1' and method=='mb':
            if scene in ('l0','lc'):return off_success
            if scene=='hs':return True
            if scene=='h0' and variant=='reachable_on':return True
        if scene in ('lf','hs','lc'):return person in ('p1','p2') and method=='ma'
        return old_available(person,method,scene)
    def evaluated(person,method,start,end):
        if variant=='unknown_assessment':raise ValueError('Unknown assessment')
        if method=='unassessed':return False
        if variant=='empty_evaluation' and start=='h0':return False
        if variant=='invalid_evaluation' and start=='h0' and method=='ma':return end=='win_b'
        return old_evaluated(person,method,start,end)
    variables=('factor','opportunity')
    if variant=='duplicate_variables':variables+=('factor',)
    if variant=='missing_factor':variables=('opportunity',)
    def targets(person,activity):
        if variant=='unknown_targets':raise ValueError('Unknown boundary targets')
        if variant=='empty_targets':return False
        return (person,activity)==('p1','a' if variant=='wrong_goal' else 'b') or variant=='extra_target' and (person,activity)==('p2','b')
    primitives.update(iachigher=higher,iaclower=lower_point,iacallowed=allowed,iacavailable=available,iacevaluated=evaluated,
        iadvariables=lambda:SequenceValue(variables,json.dumps('individual')),iadequations=equations,iadfactor=lambda:'factor',
        iadview=state_view,iadobserved=observed,iadtargets=targets)
    if variant=='target_outside_scope':primitives['iacmentalactivities']=lambda p,a:a=='a'
    return primitives


def values(*,indices=tuple(range(8)),memoize=True,budget=3_000_000,**options):
    doc=deepcopy(fixture());doc['statements']=[doc['statements'][i] for i in indices]
    doc,primitives=lower(doc,model(**options))
    return [r['value'] for r in evaluate_document(doc,individuals=DOMAIN,situations=SCENES,primitives=primitives,
        max_steps=budget,memoize_definitions=memoize,memoize_expressions=memoize)]


def attribution(path=CORE,variant='baseline'):
    doc=deepcopy(document(path));doc['statements']=doc['statements'][-1:]
    def forbidden(*args):raise AssertionError('Attribution evaluated model or barrier')
    primitives={d['name']:forbidden for d in doc['declarations'] if d['kind']=='primitive'}
    def report(node,author,code,scope,scene):
        return (node,author,scope,scene)==('node','author','scope','anchor') and code.rank==3 and json.loads(code.syntax)==dict(kind='call',symbol='iadcontrast',arguments=[])
    primitives.update(iacnode=lambda:'other' if variant=='node' else 'node',wa=lambda:'other' if variant=='author' else 'author',
        iacscope=lambda:'other' if variant=='scope' else 'scope',wh=lambda:'other' if variant=='anchor' else 'anchor',iadreport=report)
    return [r['value'] for r in evaluate_document(doc,individuals=DOMAIN,situations=SCENES,primitives=primitives)]


def independent(table):
    solutions={f:[a for a in (False,True) if a==bool(table&(1<<(2*int(f)+int(a))))] for f in (False,True)}
    return True in solutions[False] and bool(solutions[True]) and not any(solutions[True])


def alignment():
    units=json.loads((ROOT/previous.UNITS).read_text(encoding='utf-8'))['units'];unit=next(u for u in units if u['id']=='kant-1784:u0017')
    phrase='und setzt ihr doch unübersteigliche Schranken';start=unit['text'].index(phrase)
    return dict(unit=unit['id'],text_sha256=unit['text_sha256'],status='explicit_interpretive_annotation',
        segments=[dict(start=start,end=start+len(phrase),text=phrase)],definitions=['iadaligned','iadbarrier','iadboundaries','iadcontrast','iadattribution'],
        semantic_completion=False,causal_model_relative=True,expectation_contrast_unfinished=True)


CONTRASTS=('wrong_mapping','changed_off_regime','reachable_on','empty_evaluation','invalid_evaluation','unassessed_on',
    'inconsistent_observation','outside_observation','duplicate_variables','missing_factor','empty_targets','wrong_goal','extra_target','target_outside_scope')
UNKNOWNS=('unknown_mapping','unknown_observation','unknown_equations','unknown_norm','unknown_methods','unknown_assessment','unknown_targets')


def build_report():
    documents={}
    for path,text in build().items():
        assert (ROOT/path).read_text(encoding='utf-8')==text
        doc=parse(text)
        for notation in ('full','compact'):
            form=format_graph(doc,notation);assert parse(form)==doc and parse(transcribe(form,alphabet='v2'))==doc
        documents[path]=dict(declarations=len(doc['declarations']),statements=len(doc['statements']),characters=len(text))
    assert json.loads((ROOT/BASIS).read_text(encoding='utf-8'))==basis()
    equations=[]
    for table in range(16):
        result=values(table=table);assert result[2:5]==[independent(table)]*3,(table,result)
        equations.append(dict(table=table,result=result))
    matrix=[]
    for flags in product((False,True),repeat=3):
        appearance,success,observed=flags;result=values(appearance=appearance,off_success=success,observed_on=observed)
        assert result[0]==appearance and result[2:4]==[success and observed]*2 and result[4]==all(flags),(flags,result)
        matrix.append(dict(flags=list(flags),result=result))
    contrasts={name:values(variant=name) for name in CONTRASTS};assert all(not row[4] for row in contrasts.values()),contrasts
    for name in ('unassessed_off','no_methods_on'):assert values(variant=name)==[True]*8
    for name in UNKNOWNS:
        assert values(variant=name,indices=(7,))==[True]
        try:values(variant=name,indices=(4,))
        except ValueError as error:assert 'Unknown' in str(error)
        else:raise AssertionError(name)
    for path in (SOURCE,CORE):
        assert attribution(path)==[True]
        for variant in ('node','author','scope','anchor'):assert attribution(path,variant)==[False]
    assert values(memoize=False,budget=20_000_000)==values()
    old,new=document(PARENT),document(SOURCE)
    assert new['declarations'][:len(old['declarations'])]==old['declarations'] and new['statements'][:-1]==old['statements'][:-1]
    paths=[PARENT,LIBRARY,SOURCE,CORE,BASIS,previous.UNITS,'scripts/compose_assessed_barriers.py','scripts/check_assessed_barriers.py',
        'scripts/check_apparent_liberty.py','tests/test_assessed_barriers.py','noema/constructed.py','noema/constructed_discourse.py',
        'noema/constructed_semantics.py','noema/diagnostic_short_circuit.py']
    return dict(status='assessed_inability_under_explicit_causal_model',documents=documents,equations=equations,matrix=matrix,contrasts=contrasts,
        roundtrips=True,cached_step_budget=3_000_000,uncached_step_budget=20_000_000,source_alignment=alignment(),limitations=basis()['limitations'],verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in paths})


def main():
    cli=argparse.ArgumentParser(description=__doc__);cli.add_argument('--verify-only',action='store_true');args=cli.parse_args()
    result=build_report()
    if args.verify_only:assert json.loads(REPORT.read_text(encoding='utf-8'))==result
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:json.dump(result,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print('Assessed causal barriers, actual observations and apparent advantage verified')


if __name__=='__main__':main()
