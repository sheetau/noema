"""Check joint intervention separately from each contributor's necessity."""
import argparse
from copy import deepcopy
from functools import lru_cache
from itertools import product
import hashlib
import json
from noema.constructed import parse,format_graph
from noema.constructed_semantics import evaluate_document,SequenceValue,FunctionValue
from noema.script import transcribe
from scripts.compose_joint_development import ROOT,PARENT,LIBRARY,SOURCE,CORE,BASIS,HIGH,STATE,FIELDS,build,basis
from scripts.check_caused_choice import evaluate
from scripts.check_scoped_counts import arithmetic
from scripts.check_apparent_liberty import UNITS
from scripts import check_cohort_mediation as previous
from scripts import check_thinking_disposition as thinking

REPORT=ROOT/'reports/joint-development-v1.json'
PEOPLE=('person','other')
VARIABLES=('causeone','causetwo','mediator','gain')
BEGINS={(True,True):'end',(True,False):'onlyone',(False,True):'onlytwo',(False,False):'offstart'}


@lru_cache(maxsize=4)
def document(path):return parse((ROOT/path).read_text(encoding='utf-8'))


def equations(mtable=8,ytable=10,variant='baseline'):
    def equation(variable,state):
        if variant=='unknown_equation':raise ValueError('Unknown joint equation')
        one,two=state('causeone'),state('causetwo')
        if variable in VARIABLES[:2]:return True
        if variable=='mediator':return bool(mtable&(1<<(2*int(one)+int(two))))
        if variable=='gain':
            if variant=='no_single_solution' and one!=two:return not state('gain')
            return bool(ytable&(1<<(2*int(one and two)+int(state('mediator')))))
        return False
    return equation


@lru_cache(maxsize=1)
def fixture():
    from scripts.compose_restricted_utterance import primitive
    text=(ROOT/LIBRARY).read_text(encoding='utf-8');args=[]
    for name,sort in FIELDS:
        text+=primitive('jk'+name,sort if sort.startswith('h[') else 'h[] '+sort)
        args.append('p jk'+name if sort.startswith('h[') else 'k jk'+name+'[]')
    # observed is a nullary provider returning a state, not a state primitive.
    text=text.replace('r jkobserved[a] c.','r jkobserved[] '+STATE+'.')
    args[[n for n,t in FIELDS].index('observed')]='k jkobserved[]'
    return parse(text+''.join('q[k '+name+'['+' '.join(args)+']].' for name in ('rxr','rxs')))


def values(mtable=8,ytable=10,*,variant='baseline',indices=(0,1),memoize=True):
    people=PEOPLE[:1] if variant=='single_contributor' else PEOPLE
    catalogue=() if variant=='empty' else people+('person',) if variant=='duplicate' else people[:1] if variant=='omitted' else people
    def factor(person):
        if variant=='same_factor':return 'causeone'
        if variant=='factor_is_mediator':return 'mediator'
        if variant=='undeclared':return 'outside'
        return VARIABLES[PEOPLE.index(person)] if person in PEOPLE else 'outside'
    def premise(person,state):
        if variant=='unknown_single_premise' and state('causeone')!=state('causetwo'):raise ValueError('Unknown contributor premise')
        return state(VARIABLES[1-PEOPLE.index(person)] if variant=='swapped_premises' else factor(person)) if person in PEOPLE else False
    def reviewed(state):
        if variant=='unknown_single_review' and state('causeone')!=state('causetwo'):raise ValueError('Unknown single removal review')
        return not (variant=='unreviewed_single' and state('causeone')!=state('causetwo'))
    p=dict(arithmetic(),jkcontributors=lambda:SequenceValue(catalogue,'"individual"'),jkpeople=lambda p:p in people and variant!='empty',
        jkfactors=factor,jkvariables=lambda:SequenceValue(VARIABLES,'"individual"'),jkmediator=lambda:'mediator',
        jkequations=equations(mtable,ytable,variant),jkpremise=premise,jkchecked=lambda s:True,jkeffect=lambda s:s('gain'),
        jkobserved=lambda:FunctionValue(('individual',),'truth',lambda x:x in VARIABLES),jkmeaning=lambda s:s('mediator'),jkreviewed=reviewed)
    doc=deepcopy(fixture());doc['statements']=[doc['statements'][i] for i in indices]
    p={d['name']:p[d['name']] for d in doc['declarations'] if d['kind']=='primitive'}
    return evaluate(doc,p,PEOPLE+VARIABLES+('outside',),('now',),memoize=memoize,budget=8_000_000)


def development_primitives():
    """Two people can develop independently at one shared world-specific point."""
    base=thinking.model();result={}
    def anchor(person,point):
        if point not in BEGINS.values():return point
        bits=next(bits for bits,name in BEGINS.items() if name==point)
        return 'end' if person in PEOPLE and bits[PEOPLE.index(person)] else 'outside'
    def adapt(name,person_position,anchor_position=None):
        fn=base[name]
        def call(*args):
            args=list(args);person=args[person_position]
            if anchor_position is not None:args[anchor_position]=anchor(person,args[anchor_position])
            if person in PEOPLE:args[person_position]='person'
            return fn(*args)
        return call
    for name,person_position,anchor_position in (
        ('iahpoints',0,1),('iahscope',0,2),('iahclassified',0,2),('iahweights',0,2),
        ('iahfavor',0,None),('iahurge',0,None),('iahthreshold',0,2),('iahassigned',1,3),
        ('iahlatent',0,None),('iahaffected',1,3)):
        result[name]=adapt(name,person_position,anchor_position)
    def relative(person,at,point):
        if point==at:return anchor(person,point)
        return 'outside' if point in BEGINS.values() else point
    result['iahhistory']=lambda p,a,t:base['iahhistory']('person' if p in PEOPLE else p,anchor(p,a),relative(p,a,t))
    result['iahbefore']=lambda p,a,l,r:base['iahbefore']('person' if p in PEOPLE else p,anchor(p,a),relative(p,a,l),relative(p,a,r))
    result['iahtransitions']=lambda process,l,r:base['iahtransitions'](process,l,'end' if r in BEGINS.values() else r)
    return result


@lru_cache(maxsize=1)
def source_fixture():
    doc=deepcopy(document(CORE));doc['statements']=[]
    from scripts.compose_qualified_utterance import closure
    names={d['name'] for d in doc['declarations']}
    for d in closure(document(SOURCE),['iapjoint']):
        if d['name'] not in names:doc['declarations'].append(d);names.add(d['name'])
    return parse(format_graph(doc,'compact')+f'r jkstate[] {STATE}.'+'''
r jkcommunity[] a.r jkstart[] d.r jkend[] d.r jkperson[] a.r jkother[] a.
q[k iapjoint[r b[p iahinner] k jkcommunity[] k jkstart[] k jkend[]]].
q[k iapnecessary[r b[p iahinner] k jkcommunity[] k jkstart[] k jkend[]]].
q[k iapnecessary[r b[p iahvocation] k jkcommunity[] k jkstart[] k jkend[]]].
q[k ianreviewed[k jkcommunity[] k jkstart[] k jkend[] k jkstate[]]].
q[k ianchange[k jkcommunity[] k jkstart[] k jkend[] k jkstate[]]].
q[k iaochecked[k jkcommunity[] k jkstart[] k jkend[] k jkstate[]]].
q[k iaoeffect[k jkcommunity[] k jkstart[] k jkend[] k jkstate[]]].
q[t[k iahinner[k jkperson[]]][k ianbegin[k jkcommunity[] k jkstart[] k jkend[] k jkstate[]]]].
q[t[k iahinner[k jkother[]]][k ianbegin[k jkcommunity[] k jkstart[] k jkend[] k jkstate[]]]].
''')


def source_model(*,mtable=8,ytable=10,variant='baseline',state_bits=(True,True,True,True),calls=None):
    p,domain,scenes=previous.source_model()
    domain=domain+tuple(x for x in VARIABLES if x not in domain)
    scenes=scenes+('onlyone','onlytwo')
    points=tuple(BEGINS.values())+('middle','after','flatmiddle','flatend')
    m=previous.methods((0,0,0,0,1,3,0,0),points)
    def path(state):
        start=BEGINS[(state('causeone'),state('causetwo'))]
        return (start,'middle','after') if state('gain') else (start,'flatmiddle','flatend')
    def log(name,*args):
        if calls is not None:calls.append((name,*args))
    def contributors(community,start):
        log('contributors',community,start)
        return SequenceValue(PEOPLE if (community,start)==('community','end') else (), '"individual"')
    def factor(community,start,end,person):
        if person not in PEOPLE:return 'factor'
        return VARIABLES[(1-PEOPLE.index(person)) if variant=='swapped_people' else PEOPLE.index(person)]
    def probe(community,person,topic,point,state):
        bits=tuple(state(x) for x in VARIABLES);log('probe',community,person,topic,*bits)
        if variant in ('unreviewed_single','unknown_single') and bits[0]!=bits[1]:return 'probe_unreviewed'
        stage=path(state).index(point) if point in path(state) else 0
        return ('probe_none','probe_one','probe_two')[stage if state('mediator') else 0]
    oldclassified=p['iamclassified']
    def classified(person,topic,scene):
        if variant=='unknown_single' and scene=='probe_unreviewed':raise ValueError('Unknown individual-removal assessment')
        return oldclassified(person,topic,scene)
    p.update(development_primitives())
    p.update(jkcommunity=lambda:'community',jkstart=lambda:'end',jkend=lambda:'after',jkperson=lambda:'person',jkother=lambda:'other',
        jkstate=lambda:FunctionValue(('individual',),'truth',lambda x:x in VARIABLES and state_bits[VARIABLES.index(x)]),
        iapcontributors=contributors,iappeople=lambda c,p,s:(c,s)==('community','end') and p in PEOPLE,
        iapfactors=factor,iapvariables=lambda c,s,e:SequenceValue(VARIABLES,'"individual"'),iapmediator=lambda c,s,e:'mediator',
        iapequations=lambda c,s,e,x,state:equations(mtable,ytable,variant)(x,state),
        iapobserved=lambda c,s,e:FunctionValue(('individual',),'truth',lambda x:x in VARIABLES),
        ianbegin=lambda c,s,e,state:path(state)[0],ianend=lambda c,s,e,state:path(state)[-1],
        ianhistory=lambda c,s,e,state,t:t in path(state),
        ianbefore=lambda c,s,e,state,l,r:l in path(state) and r in path(state) and path(state).index(l)<path(state).index(r),
        ianprobe=probe,iamclassified=classified,iajavailable=m['available'],iajprospects=m['prospects'],
        iajevaluated=m['evaluated'],iajperforms=m['performs'])
    return p,domain,scenes


def source_values(*,indices=(0,1),**options):
    p,domain,scenes=source_model(**options)
    doc=deepcopy(source_fixture());doc['statements']=[doc['statements'][i] for i in indices]
    primitives={d['name']:p.get(d['name'],thinking.forbidden) for d in doc['declarations'] if d['kind']=='primitive'}
    return evaluate(doc,primitives,domain,scenes,budget=40_000_000)


def attribution(path=CORE,variant='baseline'):
    doc=deepcopy(document(path));doc['statements']=doc['statements'][-1:]
    p={d['name']:thinking.forbidden for d in doc['declarations'] if d['kind']=='primitive'}
    def match(n,a,c,s,t,name):return (n,a,s,t)==('node','author','scope','end') and thinking.code_is(c,name,2)
    p.update(iagnode=lambda:'other' if variant=='node' else 'node',wa=lambda:'other' if variant=='author' else 'author',
        iagscope=lambda:'other' if variant=='scope' else 'scope',wh=lambda:'outside' if variant=='context' else 'end',
        iaoreport=lambda n,a,c,s,t:variant!='missing_member' and match(n,a,c,s,t,'iaoschema'),
        iapreport=lambda n,a,c,s,t:variant!='missing_joint' and match(n,a,c,s,t,'iapnecessary'))
    return [r['value'] for r in evaluate_document(doc,individuals=thinking.DOMAIN,situations=thinking.SCENES,primitives=p)]


CONTRASTS=('empty','duplicate','omitted','same_factor','factor_is_mediator','undeclared')
UNKNOWNS=('unknown_equation','unknown_single_premise','unknown_single_review')


def alignment():
    unit=next(u for u in json.loads((ROOT/UNITS).read_text(encoding='utf-8'))['units'] if u['id']=='kant-1784:u0017')
    return dict(unit=unit['id'],text_sha256=unit['text_sha256'],status='explicit_interpretive_annotation',
        definitions=['iapjoint','iapnecessary','iapattribution'],adds_new_text_coverage=False,semantic_completion=False,collective_conditional_unfilled=True)


def build_report():
    documents={}
    for path,text in build().items():
        assert (ROOT/path).read_text(encoding='utf-8')==text
        doc=parse(text)
        for notation in ('full','compact'):
            form=format_graph(doc,notation);assert parse(form)==doc and parse(transcribe(form,alphabet='v2'))==doc
        documents[path]=dict(declarations=len(doc['declarations']),statements=len(doc['statements']),characters=len(text))
    assert json.loads((ROOT/BASIS).read_text(encoding='utf-8'))==basis()
    for m,y in product(range(16),range(16)):
        assert values(m,y)==[m in (8,10,12,14) and y in (8,10),m==8 and y in (8,10)],(m,y)
    assert values(memoize=False)==values()
    assert source_values()==[True,True]
    assert source_values(mtable=14)==[True,False]
    assert source_values(variant='swapped_people')==[True,False]
    for path in (CORE,SOURCE):
        assert attribution(path)==[True]
        for variant in ('node','author','scope','context','missing_member','missing_joint'):assert attribution(path,variant)==[False]
    old,new=document(PARENT),document(SOURCE)
    assert new['declarations'][:len(old['declarations'])]==old['declarations'] and new['statements'][:-1]==old['statements'][:-1]
    assert new['statements'][-1]['body']['arguments'][0]==old['statements'][-1]['body']
    paths=[PARENT,LIBRARY,SOURCE,CORE,BASIS,UNITS,'scripts/compose_joint_development.py','scripts/check_joint_development.py',
        'tests/test_joint_development.py','scripts/check_cohort_mediation.py','scripts/check_thinking_disposition.py','scripts/check_caused_choice.py',
        'noema/constructed.py','noema/constructed_semantics.py','noema/constructed_closure_semantics.py','noema/diagnostic_short_circuit.py']
    return dict(status='joint_and_individually_necessary_development_checked',documents=documents,equation_combinations=256,
        source_alignment=alignment(),roundtrips=True,uncached_generic_baseline_checked=True,source_uses_closure_cache=True,
        limitations=basis()['limitations'],verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in paths})


def main():
    cli=argparse.ArgumentParser(description=__doc__);cli.add_argument('--verify-only',action='store_true');args=cli.parse_args()
    r=build_report()
    if args.verify_only:assert json.loads(REPORT.read_text(encoding='utf-8'))==r
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:json.dump(r,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print('Joint development verified; collective conditional and full semantics remain unresolved')


if __name__=='__main__':main()
