"""Check fixed-content causal dependence, including assessed counterfactual histories."""
import argparse
from copy import deepcopy
from fractions import Fraction
from functools import lru_cache
import hashlib
import json
from noema.constructed import parse,format_graph
from noema.constructed_semantics import evaluate_document,SequenceValue,FunctionValue
from noema.script import transcribe
from scripts.compose_caused_choice import ROOT,PARENT,LIBRARY,SOURCE,CORE,BASIS,HIGH,TAIL,STATE,build,basis
from noema.constructed_closure_semantics import evaluate_document as evaluate_cached
from noema.diagnostic_short_circuit import lower
from scripts.check_apparent_liberty import UNITS
from scripts import check_thinking_disposition as thinking
from scripts import check_gradual_choice as gradual

REPORT=ROOT/'reports/caused-choice-v1.json'
VARIABLES=('factor','gain')


def evaluate(doc,primitives,individuals,situations,*,memoize=True,budget=5_000_000):
    doc,primitives=lower(doc,primitives)
    return [r['value'] for r in evaluate_cached(doc,individuals=individuals,situations=situations,primitives=primitives,
        max_steps=budget,memoize_definitions=memoize,memoize_expressions=memoize,memoize_closures=memoize)]


@lru_cache(maxsize=4)
def document(path):return parse((ROOT/path).read_text(encoding='utf-8'))


@lru_cache(maxsize=1)
def fixture():
    doc=deepcopy(document(LIBRARY));doc['statements']=[]
    from scripts.compose_qualified_utterance import closure
    doc['declarations']=closure(doc,['rxg'])
    return parse(format_graph(doc,'compact')+f'''
r jzcvariables[] j[a].r jzcequations[a {STATE}] c.r jzcfactor[] a.
r jzcpremise[{STATE}] c.r jzcchecked[{STATE}] c.r jzceffect[{STATE}] c.r jzcobserved[] {STATE}.
q[k rxg[k jzcvariables[] p jzcequations k jzcfactor[] p jzcpremise p jzcchecked p jzceffect k jzcobserved[]]].
''')


def equations(table=12,variant='baseline'):
    def equation(variable,state):
        if variant=='unknown_equation':raise ValueError('Unknown structural equation')
        if variable=='factor':return True
        if variable!='gain':return False
        if variant=='no_off_solution' and not state('factor'):return not state('gain')
        if variant=='no_on_solution' and state('factor'):return not state('gain')
        return bool(table&(1<<(2*int(state('factor'))+int(state('gain')))))
    return equation


def values(table=12,*,variant='baseline',memoize=True):
    def checked(state):
        if variant=='unknown_assessment':raise ValueError('Unknown assessment')
        return not (variant=='unchecked_off' and not state('factor') or variant=='unchecked_on' and state('factor'))
    def premise(state):
        if variant=='unknown_premise':raise ValueError('Unknown antecedent meaning')
        return not state('factor') if variant=='wrong_premise' else state('factor')
    def effect(state):
        if variant=='unknown_effect':raise ValueError('Unknown effect')
        return state('gain')
    variables=('factor','gain','factor') if variant=='duplicate' else ('gain',) if variant=='absent_factor' else VARIABLES
    observed=lambda x:x in (('gain',) if variant=='factor_absent_in_observation' else ('factor',) if variant=='no_observed_gain' else ('factor','gain','other') if variant=='external_true' else VARIABLES)
    p=dict(jzcvariables=lambda:SequenceValue(variables,'"individual"'),jzcequations=equations(table,variant),jzcfactor=lambda:'factor',
        jzcpremise=premise,jzcchecked=checked,jzceffect=effect,jzcobserved=lambda:FunctionValue(('individual',),'truth',observed))
    return evaluate(fixture(),p,VARIABLES+('other',),('now',),memoize=memoize)


@lru_cache(maxsize=1)
def source_fixture():
    doc=deepcopy(document(CORE));doc['statements']=[]
    return parse(format_graph(doc,'compact')+f'r jzcrest[{HIGH} a d d] c.'+'''
r jzcperson[] a.r jzcstart[] d.r jzcend[] d.
'''+f'r jzcoff[] {STATE}.'+'''
q[k iakcausal[r b[p iahinner] k jzcperson[] k jzcstart[] k jzcend[]]].
q[k iakchecked[k jzcperson[] k jzcstart[] k jzcend[] k iakobserved[k jzcperson[] k jzcstart[] k jzcend[]]]].
q[k iakeffect[k jzcperson[] k jzcstart[] k jzcend[] k iakobserved[k jzcperson[] k jzcstart[] k jzcend[]]]].
q[k iakschema[r b[p iahinner] p jzcrest]].
q[k iakschema[r b[p iahvocation] p jzcrest]].
q[k iakchecked[k jzcperson[] k jzcstart[] k jzcend[] k jzcoff[]]].
q[k iakeffect[k jzcperson[] k jzcstart[] k jzcend[] k jzcoff[]]].
''')


def source_values(*,table=12,variant='baseline',remaining=True,urge=True,assigned=True,indices=(0,1,2),memoize=True,calls=None):
    points=('end','middle','after','offstart','offmiddle','offafter','flatmiddle','flatend','offflatmiddle','offflatend')
    profiles=(1,3,7,1,3,7,1,1,1,1)
    methods=gradual.method_model(profiles,times=points)
    domain=thinking.DOMAIN+gradual.ACTIVITIES+gradual.PLANS+('unknownplan',)+VARIABLES
    scenes=thinking.SCENES+tuple(p for p in points if p not in thinking.SCENES)+('otherafter',)+gradual.HITS
    p=thinking.model(urge=urge,assigned=assigned)
    original=('end','middle','after')
    def path(state):
        on=state('factor');gain=state('gain')
        first='end' if on or variant=='wrong_off_premise' else 'offstart'
        if gain:return (first,'middle' if on else 'offmiddle','after' if on else 'offafter')
        return (first,'flatmiddle' if on else 'offflatmiddle','flatend' if on else 'offflatend')
    def oldhistory(person,anchor,start,point):
        return (person,anchor)==('person','end') and ((start=='end' and point in original) or (start=='outside' and point in ('outside','otherafter')))
    def oldorder(person,anchor,start,left,right):
        seq=original if start=='end' else ('outside','otherafter')
        return (person,anchor)==('person','end') and left in seq and right in seq and seq.index(left)<seq.index(right)
    def history(person,start,end,state,point):
        if variant=='unknown_world_history':raise ValueError('Unknown causal history')
        if variant=='wrong_observed_history' and state('factor') and state('gain') and point=='outside':return True
        return point in path(state)
    def order(person,start,end,state,left,right):
        seq=path(state)
        if variant=='wrong_observed_order' and state('factor') and state('gain') and left=='middle' and right=='after':return False
        return left in seq and right in seq and seq.index(left)<seq.index(right)
    def available(person,plan,point):
        if variant=='unassessed_off' and person=='person' and plan=='unknownplan' and point=='offstart':return True
        return methods['available'](person,plan,point)
    def selected(person,plan,point,end):
        if variant=='unknown_off_results' and point=='offstart':raise ValueError('Unknown counterfactual method result')
        return methods['evaluated'](person,plan,point,end)
    def rest(reading,person,start,end):
        if calls is not None:calls.append((reading,person,start,end))
        return remaining and (person,start,end)==('person','end','after') and any(thinking.code_is(reading,n,1) for n in ('iahinner','iahvocation'))
    observed=lambda variable:variable in VARIABLES
    p.update(iaipeople=lambda person,a:(person,a)==('person','end'),iaicases=lambda person,a,s:(person,a)==('person','end') and s in ('end','outside'),
        iaihistory=oldhistory,iaibefore=oldorder,jzcperson=lambda:'person',jzcstart=lambda:'end',jzcend=lambda:'after',jzcrest=rest,
        jzcoff=lambda:FunctionValue(('individual',),'truth',lambda variable:False),
        iajactivities=lambda person,start:SequenceValue(gradual.ACTIVITIES if start=='end' else (), '"individual"'),
        iajscope=lambda person,start,activity:(person,start)==('person','end') and activity in gradual.ACTIVITIES,
        iajbound=lambda person,start:Fraction(1 if start=='end' else 0),iajavailable=available,iajprospects=methods['prospects'],iajevaluated=selected,
        aa=lambda person:person=='person',dg=lambda activity,point:activity in gradual.ACTIVITIES and point==gradual.HITS[gradual.ACTIVITIES.index(activity)],
        iajperforms=methods['truth'],iakvariables=lambda person,start,end:SequenceValue(VARIABLES,'"individual"'),
        iakequations=lambda person,start,end,variable,state:equations(table)(variable,state),iakfactor=lambda person,start,end:'factor',
        iakobserved=lambda person,start,end:FunctionValue(('individual',),'truth',observed),
        iakbegin=lambda person,start,end,state:'end' if variant=='wrong_off_premise' and not state('factor') else 'offstart' if variant=='wrong_observed_start' and state('factor') else path(state)[0],
        iakend=lambda person,start,end,state:'flatend' if variant=='wrong_observed_end' and state('factor') else path(state)[-1],
        iakhistory=history,iakbefore=order)
    doc=deepcopy(source_fixture());doc['statements']=[doc['statements'][i] for i in indices]
    primitives={d['name']:p.get(d['name'],thinking.forbidden) for d in doc['declarations'] if d['kind']=='primitive'}
    return evaluate(doc,primitives,domain,scenes,memoize=memoize,budget=40_000_000)


def attribution(path=CORE,variant='baseline'):
    doc=deepcopy(document(path));doc['statements']=doc['statements'][-1:]
    p={d['name']:thinking.forbidden for d in doc['declarations'] if d['kind']=='primitive'}
    p.update(iagnode=lambda:'other' if variant=='node' else 'node',wa=lambda:'other' if variant=='author' else 'author',
        iagscope=lambda:'other' if variant=='scope' else 'scope',wh=lambda:'outside' if variant=='context' else 'end',
        iakreport=lambda node,author,code,scope,context:(node,author,scope,context)==('node','author','scope','end') and thinking.code_is(code,'iakschema',2))
    return [r['value'] for r in evaluate_document(doc,individuals=thinking.DOMAIN,situations=thinking.SCENES,primitives=p)]


CONTRASTS=('duplicate','absent_factor','factor_absent_in_observation','no_observed_gain','external_true','wrong_premise',
           'unchecked_off','unchecked_on','no_off_solution','no_on_solution')
UNKNOWNS=('unknown_equation','unknown_assessment','unknown_premise','unknown_effect')


def alignment():
    unit=next(u for u in json.loads((ROOT/UNITS).read_text(encoding='utf-8'))['units'] if u['id']=='kant-1784:u0017')
    return dict(unit=unit['id'],text_sha256=unit['text_sha256'],status='explicit_interpretive_annotation',
        definitions=['iakchecked','iakeffect','iakaligned','iakcausal','iakschema','iakattribution'],
        adds_new_text_coverage=False,semantic_completion=False,remaining_consequent_unfilled=True)


def build_report():
    documents={}
    for path,text in build().items():
        assert (ROOT/path).read_text(encoding='utf-8')==text
        doc=parse(text)
        for notation in ('full','compact'):
            form=format_graph(doc,notation);assert parse(form)==doc and parse(transcribe(form,alphabet='v2'))==doc
        documents[path]=dict(declarations=len(doc['declarations']),statements=len(doc['statements']),characters=len(text))
    assert json.loads((ROOT/BASIS).read_text(encoding='utf-8'))==basis()
    for table in range(16):assert values(table)==[table==12],table
    for variant in CONTRASTS:assert values(variant=variant)==[False],variant
    for variant in UNKNOWNS:
        try:values(variant=variant)
        except ValueError as error:assert 'Unknown' in str(error)
        else:raise AssertionError(variant)
    assert values(memoize=False)==values()
    assert source_values()==[True,True,True]
    assert source_values(variant='unassessed_off',indices=(0,))==[False]
    assert source_values(table=15,indices=(0,))==[False]
    assert source_values(indices=(3,4))==[True,True]
    for path in (CORE,SOURCE):
        assert attribution(path)==[True]
        for variant in ('node','author','scope','context'):assert attribution(path,variant)==[False]
    old,new=document(PARENT),document(SOURCE)
    assert new['declarations'][:len(old['declarations'])]==old['declarations'] and new['statements'][:-1]==old['statements'][:-1]
    paths=[PARENT,LIBRARY,SOURCE,CORE,BASIS,UNITS,'scripts/compose_caused_choice.py','scripts/check_caused_choice.py',
        'tests/test_caused_choice.py','noema/constructed.py','noema/constructed_semantics.py','noema/diagnostic_short_circuit.py',
        'noema/constructed_closure_semantics.py','tests/test_constructed_closure_cache.py']
    return dict(status='fixed_content_model_relative_causal_dependency',documents=documents,boolean_equation_tables=16,
        source_alignment=alignment(),roundtrips=True,uncached_generic_baseline_checked=True,source_uses_memoized_diagnostics=True,
        evaluation=dict(engine='noema.constructed_closure_semantics',memoize_closures=True,
            pure_extensional_callbacks_required=True,source_step_budget=40_000_000,
            historical_engine_exceeded_this_budget_on_false_development_case=True),
        limitations=basis()['limitations'],verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in paths})


def main():
    cli=argparse.ArgumentParser(description=__doc__);cli.add_argument('--verify-only',action='store_true');args=cli.parse_args()
    r=build_report()
    if args.verify_only:assert json.loads(REPORT.read_text(encoding='utf-8'))==r
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:json.dump(r,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print('Model-relative dependence verified; mediation and political consequence remain incomplete')


if __name__=='__main__':main()
