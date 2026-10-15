"""Exercise actual judgments and two-sided action methods in cohort mediation."""
import argparse
from copy import deepcopy
from fractions import Fraction
from functools import lru_cache
from itertools import product
import hashlib
import json
from noema.constructed import parse,format_graph
from noema.constructed_semantics import evaluate_document,SequenceValue
from noema.script import transcribe
from scripts.compose_cohort_mediation import ROOT,PARENT,LIBRARY,SOURCE,CORE,BASIS,HIGH,REST,STATE,FIELDS,build,basis
from scripts.check_caused_choice import evaluate
from scripts.check_scoped_counts import arithmetic
from scripts.check_apparent_liberty import UNITS
from scripts.check_cohort_response import expected
from scripts import check_reasoned_response as previous
from scripts import check_thinking_disposition as thinking

REPORT=ROOT/'reports/cohort-mediation-v1.json'
PEOPLE=('person','other')
HITS=('hitperson','hitother','idle')


@lru_cache(maxsize=4)
def document(path):return parse((ROOT/path).read_text(encoding='utf-8'))


def methods(profile,times,variant='baseline'):
    def available(person,plan,point):
        if variant=='unknown_available':raise ValueError('Unknown action method')
        if person not in PEOPLE or point not in times:return False
        if plan=='unknownplan':return variant=='unassessed_joint' and point=='flatmiddle' and person=='other'
        if plan=='skip':return variant!='no_skip'
        return plan=='doalpha' and bool(profile[times.index(point)]&(1<<PEOPLE.index(person)))
    def prospects(person,plan,point,result):
        if person not in PEOPLE or plan not in ('doalpha','skip') or point not in times:return False
        return result==('idle' if plan=='skip' else HITS[PEOPLE.index(person)])
    def evaluated(person,plan,point,result):
        if variant=='unknown_results':raise ValueError('Unknown method result')
        return prospects(person,plan,point,result)
    def performs(person,activity,point):
        if variant=='unknown_performance':raise ValueError('Unknown action content')
        return person in PEOPLE and activity=='alpha' and point==HITS[(1-PEOPLE.index(person)) if variant=='other_performer' else PEOPLE.index(person)]
    return dict(available=available,prospects=prospects,evaluated=evaluated,performs=performs)


@lru_cache(maxsize=1)
def fixture():
    from scripts.compose_restricted_utterance import primitive
    text=(ROOT/LIBRARY).read_text(encoding='utf-8')
    args=[]
    for name,sort in FIELDS:
        symbol='jj'+name
        if name=='goals':continue
        text+=primitive(symbol,sort if sort.startswith('h[') else 'h[] '+sort)
    text+='r jjperforms[a a d] c.d jjgoals[person a activity a] e[b point[k jjperforms[v person v activity v point]]].'
    for name,sort in FIELDS:args.append('p jj'+name if sort.startswith('h[') else 'k jj'+name+'[]')
    text+=''.join('q[k '+name+'['+' '.join(args)+']].' for name in ('rxo','rxp'))
    return parse(text)


def values(profile=(0,1,3),*,variant='baseline',memoize=True):
    times=('start','middle','finish');m=methods(profile,times,variant)
    p=dict(arithmetic(),jjpopulation=lambda:SequenceValue(PEOPLE,'"individual"'),jjpeople=lambda x:x in PEOPLE,
        jjtopics=lambda p:SequenceValue(('alpha',) if p in PEOPLE else (), '"individual"'),jjscope=lambda p,a:p in PEOPLE and a=='alpha',
        jjhistory=lambda t:t in times,jjbefore=lambda l,r:l in times and r in times and times.index(l)<times.index(r),
        jjstart=lambda:'start',jjend=lambda:'finish',jjbound=lambda:Fraction(1),
        **{'jj'+name:fn for name,fn in m.items()})
    doc=fixture();p={d['name']:p[d['name']] for d in doc['declarations'] if d['kind']=='primitive'}
    return evaluate(doc,p,PEOPLE+('alpha','doalpha','skip','unknownplan'),times+HITS,memoize=memoize,budget=10_000_000)


@lru_cache(maxsize=1)
def source_fixture():
    doc=deepcopy(document(CORE));doc['statements']=[]
    from scripts.compose_qualified_utterance import closure
    names={d['name'] for d in doc['declarations']}
    for d in closure(document(SOURCE),['iajgrowth']):
        if d['name'] not in names:doc['declarations'].append(d);names.add(d['name'])
    return parse(format_graph(doc,'compact')+f'r jjstate[] {STATE}.r jjrest[{HIGH} a a d d] c.'+'''
r jjperson[] a.r jjcommunity[] a.r jjstart[] d.r jjend[] d.r jjactivity[] a.
q[k iaocausal[r b[p iahinner] k jjperson[] k jjstart[] k jjend[]]].
q[k iaochecked[k jjcommunity[] k jjstart[] k jjend[] k jjstate[]]].
q[k iaoeffect[k jjcommunity[] k jjstart[] k jjend[] k jjstate[]]].
q[k ianreviewed[k jjcommunity[] k jjstart[] k jjend[] k jjstate[]]].
q[k ianchange[k jjcommunity[] k jjstart[] k jjend[] k jjstate[]]].
q[k iaoschema[r b[p iahinner] p jjrest]].
q[k iaoschema[r b[p iahvocation] p jjrest]].
q[k iajgrowth[k jjperson[] k jjstart[] k jjend[]]].
q[t[k iajexecution[k jjperson[] k jjactivity[]]][k jjstart[]]].
q[k iaomatched[k jjperson[] k jjstart[] k jjend[] k jjstate[]]].
''')


def source_model(*,variant='baseline',ytable=10,remaining=True,urge=True,assigned=True,state_bits=(True,True,True),calls=None):
    p,domain,scenes=previous.source_model(variant=variant,ytable=ytable,urge=urge,assigned=assigned,state_bits=state_bits)
    domain=domain+('community','othercommunity','otherfaculty')
    scenes=scenes+HITS[:2]
    points=('end','middle','after','offstart','offmiddle','offafter','flatmiddle','flatend','offflatmiddle','offflatend')
    m=methods((0,1,3,0,1,3,0,0,0,0),points,variant)
    oldprobe=p['iamprobe'];oldhistory=p['iakhistory'];oldbefore=p['iakbefore']
    def correct(community,anchor):return (community,anchor)==('community','end')
    def log(name,*args):
        if calls is not None:calls.append((name,*args))
    def population(community,anchor):
        log('population',community,anchor)
        return SequenceValue(PEOPLE[:1] if variant=='dropped_member' else PEOPLE if correct(community,anchor) else (), '"individual"')
    def members(community,person,anchor):
        return correct(community,anchor) and person in PEOPLE and not (variant=='actor_outside' and person=='person')
    def topics(community,person,anchor):
        log('topics',community,person,anchor)
        return SequenceValue(('topicone',) if correct(community,anchor) and person in PEOPLE else (), '"individual"')
    def activities(community,person,anchor):
        log('activities',community,person,anchor)
        return SequenceValue(('alpha',) if correct(community,anchor) and person in PEOPLE else (), '"individual"')
    def probe(community,person,topic,point,state):
        log('probe',community,person,topic,*(state(x) for x in previous.VARIABLES))
        return oldprobe(person,topic,point,state) if community=='community' else 'outside'
    def presented(person,topic,scene):return person in PEOPLE and topic=='topicone' and scene in previous.PROBES
    def classified(person,topic,scene):
        if variant=='unknown_joint' and scene=='probe_unreviewed':raise ValueError('Unknown joint cohort assessment')
        return presented(person,topic,scene) and scene!='probe_unreviewed'
    def judged(person,judgment,scene):
        if variant=='one_response_only' and person=='other':return False
        return ((person,judgment)==('person','judgmentone') and scene in ('probe_one','probe_two')
            or (person,judgment,scene)==('other','judgmenttwo','probe_two'))
    def joint(state):return state('factor') and not state('mediator')
    def history(community,start,end,state,point):
        if variant=='unknown_history' and joint(state):raise ValueError('Unknown cohort history')
        return oldhistory('person',start,end,state,point) or (variant=='different_joint_history' and joint(state) and point=='outside')
    def before(community,start,end,state,left,right):
        if variant=='different_joint_history' and joint(state) and right=='outside':return oldhistory('person',start,end,state,left)
        return oldbefore('person',start,end,state,left,right)
    def rest(reading,person,community,start,end):
        log('remaining',reading,person,community,start,end)
        return remaining and (person,community,start,end)==('person','community','end','after') and any(thinking.code_is(reading,n,1) for n in ('iahinner','iahvocation'))
    p.update(jjstate=p['jrstate'],jjperson=lambda:'person',jjcommunity=lambda:'community',jjstart=lambda:'end',jjend=lambda:'after',
        jjactivity=lambda:'alpha',jjrest=rest,iaocommunity=lambda person,anchor:'othercommunity' if variant=='other_community' else 'community',
        ianpopulation=population,ianmembers=members,iantopics=topics,ianscope=lambda c,p,a,t:correct(c,a) and p in PEOPLE and t=='topicone',
        ianbound=lambda c,a:Fraction(1 if correct(c,a) else 0),ianprobe=probe,
        ianbegin=p['iakbegin'],ianend=p['iakend'],ianhistory=history,ianbefore=before,
        iaoactivities=activities,iaoscope=lambda c,p,a,t:correct(c,a) and p in PEOPLE and t=='alpha',
        iaobound=lambda c,a:Fraction(1 if correct(c,a) else 0),
        aa=lambda person:person in PEOPLE and not (variant=='nonhuman_member' and person=='other'),
        iampresented=presented,iamclassified=classified,fa=judged,
        ab=lambda faculty,person,scene:(faculty,person) in (('faculty','person'),('otherfaculty','other')) and scene in previous.PROBES,
        ac=lambda person,faculty,judgment,scene:(person,faculty,judgment) in (('person','faculty','judgmentone'),('other','otherfaculty','judgmenttwo')) and scene in previous.PROBES,
        fb=lambda judgment,topic,scene:judgment in previous.JUDGMENTS and topic=='topicone' and scene in previous.PROBES,
        ad=lambda guide,person,judgment,scene:False,
        iajavailable=m['available'],iajprospects=m['prospects'],iajevaluated=m['evaluated'],iajperforms=m['performs'],
        dg=lambda activity,point:activity=='alpha' and point in HITS[:2])
    return p,domain,scenes


def source_values(*,indices=(0,1,2,3,4,7,8),**options):
    p,domain,scenes=source_model(**options)
    doc=deepcopy(source_fixture());doc['statements']=[doc['statements'][i] for i in indices]
    primitives={d['name']:p.get(d['name'],thinking.forbidden) for d in doc['declarations'] if d['kind']=='primitive'}
    return evaluate(doc,primitives,domain,scenes,budget=40_000_000)


def attribution(path=CORE,variant='baseline'):
    doc=deepcopy(document(path));doc['statements']=doc['statements'][-1:]
    p={d['name']:thinking.forbidden for d in doc['declarations'] if d['kind']=='primitive'}
    p.update(iagnode=lambda:'other' if variant=='node' else 'node',wa=lambda:'other' if variant=='author' else 'author',
        iagscope=lambda:'other' if variant=='scope' else 'scope',wh=lambda:'outside' if variant=='context' else 'end',
        iaoreport=lambda node,author,code,scope,context:(node,author,scope,context)==('node','author','scope','end') and thinking.code_is(code,'iaoschema',2))
    return [r['value'] for r in evaluate_document(doc,individuals=thinking.DOMAIN,situations=thinking.SCENES,primitives=p)]


CONTRASTS=('dropped_member','actor_outside','other_community','nonhuman_member','no_skip','other_performer','one_response_only',
    'unreviewed_joint','unassessed_joint','different_joint_history','no_joint_solution')
UNKNOWNS=('unknown_joint','unknown_history','unknown_available','unknown_results','unknown_performance')


def alignment():
    unit=next(u for u in json.loads((ROOT/UNITS).read_text(encoding='utf-8'))['units'] if u['id']=='kant-1784:u0017')
    return dict(unit=unit['id'],text_sha256=unit['text_sha256'],status='explicit_interpretive_annotation',
        definitions=['iaochecked','iaoeffect','iaomatched','iaocausal','iaoschema','iaoattribution'],
        adds_new_text_coverage=False,semantic_completion=False,collective_effect_causal_integration=True,collective_cause_unresolved=True)


def build_report():
    documents={}
    for path,text in build().items():
        assert (ROOT/path).read_text(encoding='utf-8')==text
        doc=parse(text)
        for notation in ('full','compact'):
            form=format_graph(doc,notation);assert parse(form)==doc and parse(transcribe(form,alphabet='v2'))==doc
        documents[path]=dict(declarations=len(doc['declarations']),statements=len(doc['statements']),characters=len(text))
    assert json.loads((ROOT/BASIS).read_text(encoding='utf-8'))==basis()
    for profile in product(range(4),repeat=3):assert values(profile)==[True,expected(profile)],profile
    assert values(memoize=False)==values()
    assert source_values()==[True,True,True,True,True,False,False]
    assert source_values(indices=(5,6))==[True,True]
    assert source_values(ytable=12,indices=(0,))==[False]
    assert source_values(variant='different_joint_history',indices=(0,))==[False]
    for path in (CORE,SOURCE):
        assert attribution(path)==[True]
        for variant in ('node','author','scope','context'):assert attribution(path,variant)==[False]
    old,new=document(PARENT),document(SOURCE)
    assert new['declarations'][:len(old['declarations'])]==old['declarations'] and new['statements'][:-1]==old['statements'][:-1]
    paths=[PARENT,LIBRARY,SOURCE,CORE,BASIS,UNITS,'scripts/compose_cohort_mediation.py','scripts/check_cohort_mediation.py',
        'tests/test_cohort_mediation.py','scripts/check_cohort_response.py','scripts/check_reasoned_response.py','scripts/check_caused_choice.py',
        'noema/constructed.py','noema/constructed_semantics.py','noema/constructed_closure_semantics.py','noema/diagnostic_short_circuit.py']
    return dict(status='member_to_cohort_mediation_checked_collective_cause_unresolved',documents=documents,cohort_capacity_profiles=64,
        source_alignment=alignment(),roundtrips=True,uncached_generic_baseline_checked=True,source_uses_closure_cache=True,
        limitations=basis()['limitations'],verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in paths})


def main():
    cli=argparse.ArgumentParser(description=__doc__);cli.add_argument('--verify-only',action='store_true');args=cli.parse_args()
    r=build_report()
    if args.verify_only:assert json.loads(REPORT.read_text(encoding='utf-8'))==r
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:json.dump(r,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print('Member-to-cohort mediation verified; collective cause and full source semantics remain unresolved')


if __name__=='__main__':main()
