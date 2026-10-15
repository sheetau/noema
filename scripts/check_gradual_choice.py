"""Check staged two-sided choice using actual method and outcome definitions."""
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
from scripts.compose_gradual_choice import ROOT,PARENT,LIBRARY,SOURCE,CORE,BASIS,HIGH,TAIL,build,basis
from scripts.check_faculty_opportunities import evaluate
from scripts.check_scoped_counts import arithmetic
from scripts.check_apparent_liberty import UNITS
from scripts import check_thinking_disposition as previous

REPORT=ROOT/'reports/gradual-choice-v1.json'
ACTIVITIES=('alpha','beta','gamma')
PLANS=('doalpha','dobeta','dogamma','skip')
HITS=('hitalpha','hitbeta','hitgamma','idle')
TIMES=('start','middle','finish')
DOMAIN=('person','other')+ACTIVITIES+PLANS+('unknownplan',)
SCENES=TIMES+HITS+('outside',)


@lru_cache(maxsize=4)
def document(path):return parse((ROOT/path).read_text(encoding='utf-8'))


@lru_cache(maxsize=1)
def fixture():
    return parse((ROOT/LIBRARY).read_text(encoding='utf-8')+'''
r jgperson[] a.r jgactivities[] j[a].r jgscope[a] c.r jgbound[] b.
r jgstart[] d.r jgend[] d.r jghistory[d] c.r jgbefore[d d] c.
r jgavailable[a a d] c.r jgprospects[a a d d] c.r jgevaluated[a a d d] c.r jgtruth[a a d] c.r jgactivity[] a.
d jggoal[person a activity a] e[b point[k jgtruth[v person v activity v point]]].
q[k rxe[k jgperson[] k jgactivities[] p jgscope p jggoal p jghistory p jgbefore k jgstart[] k jgend[] k jgbound[] p jgavailable p jgprospects p jgevaluated]].
q[k rxc[k jgperson[] k jggoal[k jgperson[] k jgactivity[]] k jgstart[] p jgavailable p jgprospects p jgevaluated]].
q[k rxd[k jgperson[] k jggoal[k jgperson[] k jgactivity[]] k jgstart[] p jgavailable p jgprospects p jgevaluated]].
q[k rxc[k jgperson[] k jggoal[k jgperson[] k jgactivity[]] k jgend[] p jgavailable p jgprospects p jgevaluated]].
q[t[k jggoal[k jgperson[] k jgactivity[]]][k jgstart[]]].
''')


def method_model(profile=(1,3,7),*,times=TIMES,variant='baseline'):
    def available(person,plan,point):
        if variant=='unknown_available':raise ValueError('Unknown available methods')
        if person!='person' or point not in times:return False
        if plan=='unknownplan':return variant=='unassessed_method'
        if plan=='skip':return variant!='no_skip'
        return plan in PLANS[:3] and bool(profile[times.index(point)]&(1<<PLANS.index(plan)))
    def prospects(person,plan,point,end):
        if variant=='unknown_prospects':raise ValueError('Unknown prospective result')
        if person!='person' or point not in times or plan not in PLANS:return False
        if variant=='mixed_results' and plan in PLANS[:3]:return end in (HITS[PLANS.index(plan)],'idle')
        return end==HITS[PLANS.index(plan)]
    def selected(person,plan,point,end):
        if variant=='unknown_selected':raise ValueError('Unknown evaluated result')
        if variant=='empty_results':return False
        if variant=='outside_results':return person=='person' and plan in PLANS and point in times and end=='outside'
        return prospects(person,plan,point,end)
    def truth(person,activity,point):
        if variant=='unknown_execution':raise ValueError('Unknown execution')
        return person==('other' if variant=='other_performer' else 'person') and activity in ACTIVITIES and point==HITS[ACTIVITIES.index(activity)]
    return dict(available=available,prospects=prospects,evaluated=selected,truth=truth)


def values(profile=(1,3,7),*,bound=1,variant='baseline',indices=(0,1,2,3,4),memoize=True):
    times=TIMES if len(profile)==3 else ('start','middle','hold','finish')
    assert len(profile)==len(times)
    methods=method_model(profile,times=times,variant=variant)
    catalogue=() if variant=='empty_scope' else ACTIVITIES+('alpha',) if variant=='duplicate' else ACTIVITIES[:2] if variant=='omitted' else ACTIVITIES
    if variant=='reordered':catalogue=tuple(reversed(catalogue))
    def scope(activity):
        if variant=='unknown_scope':raise ValueError('Unknown activity scope')
        return variant!='empty_scope' and activity in ACTIVITIES
    def history(point):
        if variant=='unknown_history':raise ValueError('Unknown history')
        return point in ((times[0],times[-1]) if variant=='hidden_middle' else times)
    def before(left,right):
        if variant=='unknown_order':raise ValueError('Unknown temporal order')
        if variant=='reflexive' and left==right:return True
        return left in times and right in times and times.index(left)<times.index(right)
    p=dict(arithmetic(variant=='bad_indicator'),jgperson=lambda:'person',jgactivities=lambda:SequenceValue(catalogue,'"individual"'),
        jgscope=scope,jgbound=lambda:Fraction(bound),jgstart=lambda:'start',jgend=lambda:'finish',jghistory=history,jgbefore=before,
        jgactivity=lambda:'alpha',jgavailable=methods['available'],jgprospects=methods['prospects'],jgevaluated=methods['evaluated'],jgtruth=methods['truth'])
    doc=deepcopy(fixture());doc['statements']=[doc['statements'][i] for i in indices]
    p={d['name']:p[d['name']] for d in doc['declarations'] if d['kind']=='primitive'}
    return evaluate(doc,p,DOMAIN,times+HITS+('outside',),memoize=memoize,budget=8_000_000)


@lru_cache(maxsize=1)
def source_fixture():
    doc=deepcopy(document(CORE));doc['statements']=[]
    return parse(format_graph(doc,'compact')+f'r jgremaining[{HIGH} a d d] c.'+'''
r jgperson[] a.r jgend[] d.r jgactivity[] a.
q[k iajschema[r b[p iahinner] p jgremaining]].
q[k iajschema[r b[p iahvocation] p jgremaining]].
q[k iajgrowth[k jgperson[] k wh[] k jgend[]]].
q[t[k iajexecution[k jgperson[] k jgactivity[]]][k wh[]]].
''')


def source_values(profile=(1,3,7),*,urge=True,assigned=True,remaining=True,variant='baseline',indices=(0,1,2,3),memoize=True,calls=None):
    times=('end','middle','after')
    methods=method_model(profile,times=times,variant=variant)
    scenarios=previous.SCENES+('middle','after','otherafter')+HITS
    people=previous.DOMAIN+ACTIVITIES+PLANS+('unknownplan',)
    p=previous.model(urge=urge,assigned=assigned)
    def history(person,anchor,scene,point):
        return (person,anchor)==('person','end') and ((scene=='end' and point in times) or (scene=='outside' and point in ('outside','otherafter')))
    def order(person,anchor,scene,left,right):
        points=times if scene=='end' else ('outside','otherafter')
        return (person,anchor)==('person','end') and left in points and right in points and points.index(left)<points.index(right)
    def rest(reading,person,start,end):
        if calls is not None:calls.append((reading,person,start,end))
        if variant=='unknown_remaining':raise ValueError('Unknown remaining consequence')
        names=('iahvocation',) if variant=='vocation_only' else ('iahinner','iahvocation')
        return remaining and any(previous.code_is(reading,n,1) for n in names) and (person,start,end)==('person','end','after')
    p.update(iaipeople=lambda p,a:(p,a)==('person','end'),iaicases=lambda p,a,s:(p,a)==('person','end') and s in ('end','outside'),
        iaihistory=history,iaibefore=order,jgperson=lambda:'person',jgend=lambda:'after',jgactivity=lambda:'alpha',jgremaining=rest,
        iajactivities=lambda p,s:SequenceValue(ACTIVITIES,'"individual"'),iajscope=lambda p,s,a:a in ACTIVITIES,
        iajbound=lambda p,s:Fraction(1),iajavailable=methods['available'],iajprospects=methods['prospects'],iajevaluated=methods['evaluated'],
        aa=lambda p:p=='person' and variant!='nonhuman',dg=lambda activity,point:activity in ACTIVITIES and point==HITS[ACTIVITIES.index(activity)],
        iajperforms=methods['truth'])
    doc=deepcopy(source_fixture());doc['statements']=[doc['statements'][i] for i in indices]
    primitives={d['name']:p.get(d['name'],previous.forbidden) for d in doc['declarations'] if d['kind']=='primitive'}
    return evaluate(doc,primitives,people,scenarios,memoize=memoize,budget=15_000_000)


def attribution(path=CORE,variant='baseline'):
    doc=deepcopy(document(path));doc['statements']=doc['statements'][-1:]
    p={d['name']:previous.forbidden for d in doc['declarations'] if d['kind']=='primitive'}
    p.update(iagnode=lambda:'other' if variant=='node' else 'node',wa=lambda:'other' if variant=='author' else 'author',
        iagscope=lambda:'other' if variant=='scope' else 'scope',wh=lambda:'outside' if variant=='context' else 'end',
        iajreport=lambda node,author,code,scope,context:(node,author,scope,context)==('node','author','scope','end') and previous.code_is(code,'iajschema',2))
    return [r['value'] for r in evaluate_document(doc,individuals=previous.DOMAIN,situations=previous.SCENES,primitives=p)]


CONTRASTS=('empty_scope','duplicate','omitted','hidden_middle','reflexive','bad_indicator','empty_results','outside_results','mixed_results','unassessed_method','other_performer')
UNKNOWNS=('unknown_scope','unknown_history','unknown_order','unknown_available','unknown_prospects','unknown_selected','unknown_execution')


def alignment():
    unit=next(u for u in json.loads((ROOT/UNITS).read_text(encoding='utf-8'))['units'] if u['id']=='kant-1784:u0017')
    return dict(unit=unit['id'],text_sha256=unit['text_sha256'],status='explicit_interpretive_annotation',
        definitions=['iajexecution','iajgrowth','iajschema','iajattribution'],
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
    for counts in product(range(4),repeat=3):
        expected=counts[0]<counts[1]<counts[2] and counts[1]-counts[0]<=1 and counts[2]-counts[1]<=1
        assert values(tuple((1<<n)-1 for n in counts),indices=(0,))==[expected],counts
    for variant in CONTRASTS:assert values(variant=variant,indices=(0,))==[False],variant
    assert values(memoize=False)==values()
    for variant in UNKNOWNS:
        try:values(variant=variant,indices=(0,))
        except ValueError as error:assert 'Unknown' in str(error)
        else:raise AssertionError(variant)
    assert source_values()==[True,True,True,False]
    assert source_values(profile=(1,1,7))==[False,False,False,False]
    assert source_values(remaining=False)==[False,False,True,False]
    assert source_values(memoize=False,indices=(2,))==[True]
    for path in (CORE,SOURCE):
        assert attribution(path)==[True]
        for variant in ('node','author','scope','context'):assert attribution(path,variant)==[False]
    old,new=document(PARENT),document(SOURCE)
    assert new['declarations'][:len(old['declarations'])]==old['declarations'] and new['statements'][:-1]==old['statements'][:-1]
    paths=[PARENT,LIBRARY,SOURCE,CORE,BASIS,UNITS,'scripts/compose_gradual_choice.py','scripts/check_gradual_choice.py',
        'tests/test_gradual_choice.py','noema/constructed.py','noema/constructed_semantics.py','noema/diagnostic_short_circuit.py']
    return dict(status='partial_gradual_two_sided_choice_capacity',documents=documents,three_point_count_profiles=64,
        source_alignment=alignment(),roundtrips=True,uncached_generic_and_source_growth_checked=True,
        limitations=basis()['limitations'],verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in paths})


def main():
    cli=argparse.ArgumentParser(description=__doc__);cli.add_argument('--verify-only',action='store_true');args=cli.parse_args()
    r=build_report()
    if args.verify_only:assert json.loads(REPORT.read_text(encoding='utf-8'))==r
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:json.dump(r,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print('Gradual choice capacity verified; social and causal remainder is still unfilled')


if __name__=='__main__':main()
