"""Separate a necessary mediator from a correlated intermediate variable."""
import argparse
from copy import deepcopy
from fractions import Fraction
from functools import lru_cache
from itertools import product
import hashlib
import json
from noema.constructed import parse,format_graph
from noema.constructed_semantics import evaluate_document,SequenceValue,FunctionValue
from noema.script import transcribe
from scripts.compose_mediated_choice import ROOT,PARENT,LIBRARY,SOURCE,CORE,BASIS,HIGH,TAIL,STATE,MEDIATOR,build,basis
from scripts.check_caused_choice import evaluate
from scripts.check_apparent_liberty import UNITS
from scripts import check_thinking_disposition as thinking
from scripts import check_gradual_choice as gradual

REPORT=ROOT/'reports/mediated-choice-v1.json'
VARIABLES=('factor','mediator','gain')


@lru_cache(maxsize=4)
def document(path):return parse((ROOT/path).read_text(encoding='utf-8'))


@lru_cache(maxsize=1)
def fixture():
    return parse((ROOT/LIBRARY).read_text(encoding='utf-8')+f'''
r jmv[] j[a].r jmeq[a {STATE}] c.r jmf[] a.r jmm[] a.r jmo[] {STATE}.
r jmp[{STATE}] c.r jmc[{STATE}] c.r jmy[{STATE}] c.r jmmc[{STATE}] c.r jmmr[{STATE}] c.
q[k rxh[k jmv[] p jmeq k jmf[] p jmp p jmc p jmy k jmo[] k jmm[] p jmmc p jmmr]].
q[k rxg[k jmv[] p jmeq k jmf[] p jmp p jmc p jmy k jmo[]]].
''')


def equations(mtable=2,ytable=10,variant='baseline'):
    def equation(variable,state):
        if variant=='unknown_equation':raise ValueError('Unknown structural equation')
        f=state('factor');m=state('mediator')
        if variable=='factor':return True
        if variable=='mediator':return m if variant=='free_mediator' else bool(mtable&(1<<int(f)))
        if variable=='gain':
            if variant=='no_joint_solution' and f and not m:return not state('gain')
            return bool(ytable&(1<<(2*int(f)+int(m))))
        return False
    return equation


def values(mtable=2,ytable=10,*,variant='baseline',indices=(0,1),memoize=True):
    variables=VARIABLES+('mediator',) if variant=='duplicate' else ('factor','gain') if variant=='missing_mediator' else VARIABLES
    def meaning(state):
        if variant=='unknown_meaning' and state('factor') and not state('mediator'):raise ValueError('Unknown mediator meaning')
        return state('factor') if variant=='coincidence_only_meaning' else not state('mediator') if variant=='wrong_meaning' else state('mediator')
    def reviewed(state):
        if variant=='unknown_review' and state('factor') and not state('mediator'):raise ValueError('Unknown mediator review')
        return not (variant=='unreviewed_joint' and state('factor') and not state('mediator'))
    def checked(state):return not (variant=='unchecked_joint' and state('factor') and not state('mediator'))
    def effect(state):
        if variant=='unknown_joint_result' and state('factor') and not state('mediator'):raise ValueError('Unknown joint result')
        return state('gain')
    p=dict(jmv=lambda:SequenceValue(variables,'"individual"'),jmeq=equations(mtable,ytable,variant),jmf=lambda:'factor',
        jmm=lambda:'factor' if variant=='same_variable' else 'mediator',
        jmo=lambda:FunctionValue(('individual',),'truth',lambda x:x in VARIABLES),jmp=lambda s:s('factor'),jmc=checked,jmy=effect,jmmc=meaning,jmmr=reviewed)
    doc=deepcopy(fixture());doc['statements']=[doc['statements'][i] for i in indices]
    return evaluate(doc,p,VARIABLES+('other',),('now',),memoize=memoize)


@lru_cache(maxsize=1)
def source_fixture():
    doc=deepcopy(document(CORE));doc['statements']=[]
    # The core deliberately omits the superseded iakcausal; keep its dependency
    # closure for a side-by-side diagnosis of total and mediated dependence.
    from scripts.compose_qualified_utterance import closure
    names={d['name'] for d in doc['declarations']}
    for d in closure(document(SOURCE),['iakcausal']):
        if d['name'] not in names:doc['declarations'].append(d);names.add(d['name'])
    return parse(format_graph(doc,'compact')+f'r jmmeaning[a d d {STATE}] c.r jmreview[a d d {STATE}] c.r jmrest[{HIGH} a d d] c.'+'''
r jmperson[] a.r jmstart[] d.r jmend[] d.
q[k ialcausal[r b[p iahinner] p jmmeaning p jmreview k jmperson[] k jmstart[] k jmend[]]].
q[k iakcausal[r b[p iahinner] k jmperson[] k jmstart[] k jmend[]]].
q[k ialschema[r b[p iahinner] p jmmeaning p jmreview p jmrest]].
q[k ialschema[r b[p iahvocation] p jmmeaning p jmreview p jmrest]].
''')


def source_values(*,ytable=10,variant='baseline',remaining=True,urge=True,assigned=True,indices=(0,1),memoize=True,calls=None):
    points=('end','middle','after','offstart','offmiddle','offafter','flatmiddle','flatend','offflatmiddle','offflatend')
    methods=gradual.method_model((1,3,7,1,3,7,1,1,1,1),times=points)
    domain=thinking.DOMAIN+gradual.ACTIVITIES+gradual.PLANS+('unknownplan',)+VARIABLES
    scenes=thinking.SCENES+tuple(p for p in points if p not in thinking.SCENES)+('otherafter',)+gradual.HITS
    p=thinking.model(urge=urge,assigned=assigned)
    original=('end','middle','after')
    def path(state):
        on=state('factor');gain=state('gain');first='end' if on else 'offstart'
        if gain:return (first,'middle' if on else 'offmiddle','after' if on else 'offafter')
        return (first,'flatmiddle' if on else 'offflatmiddle','flatend' if on else 'offflatend')
    def oldhistory(person,anchor,start,point):
        return (person,anchor)==('person','end') and ((start=='end' and point in original) or (start=='outside' and point in ('outside','otherafter')))
    def oldorder(person,anchor,start,left,right):
        seq=original if start=='end' else ('outside','otherafter')
        return (person,anchor)==('person','end') and left in seq and right in seq and seq.index(left)<seq.index(right)
    def history(person,start,end,state,point):return point in path(state)
    def order(person,start,end,state,left,right):
        seq=path(state);return left in seq and right in seq and seq.index(left)<seq.index(right)
    def meaning(person,start,end,state):
        if calls is not None:calls.append(('meaning',person,start,end,state('factor'),state('mediator'),state('gain')))
        if variant=='unknown_joint_meaning' and state('factor') and not state('mediator'):raise ValueError('Unknown joint mediator content')
        correct=(person,start,end)==('other' if variant=='other_person' else 'person','end','after')
        return correct and (state('factor') if variant=='coincidence_only_meaning' else state('mediator'))
    def reviewed(person,start,end,state):
        return (person,start,end)==('person','end','after') and not (variant=='unreviewed_joint' and state('factor') and not state('mediator'))
    def rest(reading,person,start,end):
        if calls is not None:calls.append(('remaining',reading,person,start,end))
        return remaining and (person,start,end)==('person','end','after') and any(thinking.code_is(reading,n,1) for n in ('iahinner','iahvocation'))
    p.update(iaipeople=lambda person,a:(person,a)==('person','end'),iaicases=lambda person,a,s:(person,a)==('person','end') and s in ('end','outside'),
        iaihistory=oldhistory,iaibefore=oldorder,jmperson=lambda:'person',jmstart=lambda:'end',jmend=lambda:'after',jmrest=rest,jmmeaning=meaning,jmreview=reviewed,
        iajactivities=lambda person,start:SequenceValue(gradual.ACTIVITIES if start=='end' else (), '"individual"'),
        iajscope=lambda person,start,activity:(person,start)==('person','end') and activity in gradual.ACTIVITIES,
        iajbound=lambda person,start:Fraction(1 if start=='end' else 0),iajavailable=methods['available'],iajprospects=methods['prospects'],iajevaluated=methods['evaluated'],
        aa=lambda person:person=='person',dg=lambda activity,point:activity in gradual.ACTIVITIES and point==gradual.HITS[gradual.ACTIVITIES.index(activity)],
        iajperforms=methods['truth'],iakvariables=lambda person,start,end:SequenceValue(VARIABLES,'"individual"'),
        iakequations=lambda person,start,end,variable,state:equations(2,ytable,variant)(variable,state),iakfactor=lambda person,start,end:'factor',
        iakobserved=lambda person,start,end:FunctionValue(('individual',),'truth',lambda variable:variable in VARIABLES),
        iakbegin=lambda person,start,end,state:path(state)[0],iakend=lambda person,start,end,state:path(state)[-1],
        iakhistory=history,iakbefore=order,ialmediator=lambda person,start,end:'mediator')
    doc=deepcopy(source_fixture());doc['statements']=[doc['statements'][i] for i in indices]
    primitives={d['name']:p.get(d['name'],thinking.forbidden) for d in doc['declarations'] if d['kind']=='primitive'}
    return evaluate(doc,primitives,domain,scenes,memoize=memoize,budget=40_000_000)


def attribution(path=CORE,variant='baseline'):
    doc=deepcopy(document(path));doc['statements']=doc['statements'][-1:]
    p={d['name']:thinking.forbidden for d in doc['declarations'] if d['kind']=='primitive'}
    p.update(iagnode=lambda:'other' if variant=='node' else 'node',wa=lambda:'other' if variant=='author' else 'author',
        iagscope=lambda:'other' if variant=='scope' else 'scope',wh=lambda:'outside' if variant=='context' else 'end',
        ialreport=lambda node,author,code,scope,context:(node,author,scope,context)==('node','author','scope','end') and thinking.code_is(code,'ialschema',2))
    return [r['value'] for r in evaluate_document(doc,individuals=thinking.DOMAIN,situations=thinking.SCENES,primitives=p)]


CONTRASTS=('duplicate','missing_mediator','same_variable','wrong_meaning','coincidence_only_meaning','unreviewed_joint','unchecked_joint','no_joint_solution','free_mediator')
UNKNOWNS=('unknown_equation','unknown_meaning','unknown_review','unknown_joint_result')


def alignment():
    unit=next(u for u in json.loads((ROOT/UNITS).read_text(encoding='utf-8'))['units'] if u['id']=='kant-1784:u0017')
    return dict(unit=unit['id'],text_sha256=unit['text_sha256'],status='explicit_interpretive_annotation',
        definitions=['ialcausal','ialschema','ialattribution'],adds_new_text_coverage=False,semantic_completion=False,mediator_content_unfilled=True)


def build_report():
    documents={}
    for path,text in build().items():
        assert (ROOT/path).read_text(encoding='utf-8')==text
        doc=parse(text)
        for notation in ('full','compact'):
            form=format_graph(doc,notation);assert parse(form)==doc and parse(transcribe(form,alphabet='v2'))==doc
        documents[path]=dict(declarations=len(doc['declarations']),statements=len(doc['statements']),characters=len(text))
    assert json.loads((ROOT/BASIS).read_text(encoding='utf-8'))==basis()
    for mtable,ytable in product(range(4),range(16)):
        assert values(mtable,ytable,indices=(0,))==[mtable==2 and ytable in (8,10)],(mtable,ytable)
    for variant in CONTRASTS:assert values(variant=variant,indices=(0,))==[False],variant
    for variant in UNKNOWNS:
        try:values(variant=variant,indices=(0,))
        except ValueError as error:assert 'Unknown' in str(error)
        else:raise AssertionError(variant)
    assert values(memoize=False)==values()
    assert source_values()==[True,True]
    assert source_values(ytable=12)==[False,True]
    assert source_values(variant='unreviewed_joint')==[False,True]
    assert source_values(indices=(2,3))==[True,True]
    for path in (CORE,SOURCE):
        assert attribution(path)==[True]
        for variant in ('node','author','scope','context'):assert attribution(path,variant)==[False]
    old,new=document(PARENT),document(SOURCE)
    assert new['declarations'][:len(old['declarations'])]==old['declarations'] and new['statements'][:-1]==old['statements'][:-1]
    review=json.loads((ROOT/'data/mediator-reading-review-v1.json').read_text(encoding='utf-8'))
    for row in review['sources']:assert hashlib.sha256((ROOT/row['artifact']).read_bytes()).hexdigest()==row['artifact_sha256']
    paths=[PARENT,LIBRARY,SOURCE,CORE,BASIS,UNITS,'scripts/compose_mediated_choice.py','scripts/check_mediated_choice.py',
        'tests/test_mediated_choice.py','noema/constructed.py','noema/constructed_semantics.py',
        'noema/constructed_closure_semantics.py','noema/diagnostic_short_circuit.py',
        'data/mediator-reading-review-v1.json',*[row['artifact'] for row in review['sources']]]
    return dict(status='controlled_mediation_checked_content_unfilled',documents=documents,response_equation_combinations=64,
        source_alignment=alignment(),roundtrips=True,uncached_generic_baseline_checked=True,source_uses_closure_cache=True,
        limitations=basis()['limitations'],verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in paths})


def main():
    cli=argparse.ArgumentParser(description=__doc__);cli.add_argument('--verify-only',action='store_true');args=cli.parse_args()
    r=build_report()
    if args.verify_only:assert json.loads(REPORT.read_text(encoding='utf-8'))==r
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:json.dump(r,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print('Controlled mediation verified; psychological mediator content remains unfilled')


if __name__=='__main__':main()
