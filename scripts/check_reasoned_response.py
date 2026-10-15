"""Diagnose a fixed-topic independent-response profile as a mediator candidate."""
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
from scripts.compose_reasoned_response import ROOT,PARENT,LIBRARY,SOURCE,CORE,BASIS,HIGH,TAIL,STATE,build,basis
from scripts.check_caused_choice import evaluate
from scripts.check_scoped_counts import arithmetic
from scripts.check_apparent_liberty import UNITS
from scripts.check_mediated_choice import VARIABLES,equations
from scripts import check_thinking_disposition as thinking
from scripts import check_gradual_choice as gradual

REPORT=ROOT/'reports/reasoned-response-v1.json'
TOPICS=('topicone','topictwo','topicthree')
JUDGMENTS=('judgmentone','judgmenttwo')
PROBES=('probe_none','probe_one','probe_two','probe_unreviewed')


@lru_cache(maxsize=4)
def document(path):return parse((ROOT/path).read_text(encoding='utf-8'))


@lru_cache(maxsize=1)
def fixture():
    text=(ROOT/LIBRARY).read_text(encoding='utf-8')+'''
r jrperson[] a.r jrtopics[] j[a].r jrscope[a] c.r jrbound[] b.
r jrstart[] d.r jrend[] d.r jrhistory[d] c.r jrbefore[d d] c.
r jrclassified[a a d] c.r jrresponse[a a d] c.
'''
    args='k jrperson[] k jrtopics[] p jrscope p jrhistory p jrbefore k jrstart[] k jrend[] k jrbound[] p jrclassified p jrresponse'
    return parse(text+''.join('q[k '+name+'['+args+']].' for name in ('rxi','rxj')))


def values(profile=(0,1,3),*,bound=1,variant='baseline',indices=(0,1),memoize=True):
    times=('start','middle','finish') if len(profile)==3 else ('start','middle','hold','finish')
    assert len(profile)==len(times)
    catalogue=() if variant=='empty' else TOPICS+('topicone',) if variant=='duplicate' else TOPICS[:2] if variant=='omitted' else TOPICS+('other',) if variant=='extra' else TOPICS
    if variant=='reordered':catalogue=tuple(reversed(catalogue))
    def scope(topic):
        if variant=='unknown_scope':raise ValueError('Unknown topic scope')
        return variant!='empty' and topic in TOPICS
    def history(point):
        if variant=='unknown_history':raise ValueError('Unknown history')
        return point in ((times[0],times[-1]) if variant=='hidden_middle' else times)
    def before(left,right):
        if variant=='unknown_order':raise ValueError('Unknown temporal order')
        if variant=='reflexive' and left==right:return True
        return left in times and right in times and times.index(left)<times.index(right)
    def classified(person,topic,point):
        if variant=='unknown_classification':raise ValueError('Unknown response assessment')
        return variant!='unclassified' and person=='person' and topic in TOPICS and point in times
    def response(person,topic,point):
        if variant=='unknown_response':raise ValueError('Unknown response')
        return person==('other' if variant=='other_person' else 'person') and topic in TOPICS and point in times and bool(profile[times.index(point)]&(1<<TOPICS.index(topic)))
    p=dict(arithmetic(variant=='bad_indicator'),jrperson=lambda:'person',jrtopics=lambda:SequenceValue(catalogue,'"individual"'),
        jrscope=scope,jrbound=lambda:Fraction(bound),jrstart=lambda:times[0],jrend=lambda:times[-1],jrhistory=history,
        jrbefore=before,jrclassified=classified,jrresponse=response)
    doc=deepcopy(fixture());doc['statements']=[doc['statements'][i] for i in indices]
    p={d['name']:p[d['name']] for d in doc['declarations'] if d['kind']=='primitive'}
    return evaluate(doc,p,('person','other')+TOPICS,times+('outside',),memoize=memoize,budget=8_000_000)


@lru_cache(maxsize=1)
def source_fixture():
    doc=deepcopy(document(CORE));doc['statements']=[]
    return parse(format_graph(doc,'compact')+f'r jrremaining[{HIGH} a d d] c.r jrstate[] {STATE}.'+'''
r jrperson[] a.r jrstart[] d.r jrend[] d.
q[k iamreviewed[k jrperson[] k jrstart[] k jrend[] k jrstate[]]].
q[k iamchange[k jrperson[] k jrstart[] k jrend[] k jrstate[]]].
q[k iamschema[r b[p iahinner] p jrremaining]].
q[k iamschema[r b[p iahvocation] p jrremaining]].
q[t[k iahthinking[k jrperson[]]][k jrstart[]]].
''')


def source_model(*,ytable=10,variant='baseline',remaining=True,urge=True,assigned=True,state_bits=(True,True,True),calls=None):
    """Pure finite interpretation; hypothetical probe judgments supply the mediator."""
    points=('end','middle','after','offstart','offmiddle','offafter','flatmiddle','flatend','offflatmiddle','offflatend')
    methods=gradual.method_model((1,3,7,1,3,7,1,1,1,1),times=points)
    domain=thinking.DOMAIN+gradual.ACTIVITIES+gradual.PLANS+('unknownplan',)+VARIABLES+TOPICS+JUDGMENTS
    scenes=thinking.SCENES+tuple(t for t in points if t not in thinking.SCENES)+('otherafter',)+gradual.HITS+PROBES
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
    def order(person,start,end,state,left,right):
        seq=path(state);return left in seq and right in seq and seq.index(left)<seq.index(right)
    def rest(reading,person,start,end):
        if calls is not None:calls.append(('remaining',reading,person,start,end))
        return remaining and (person,start,end)==('person','end','after') and any(thinking.code_is(reading,n,1) for n in ('iahinner','iahvocation'))
    def probe(person,topic,point,state):
        if calls is not None:calls.append(('probe',person,topic,point,*(state(x) for x in VARIABLES)))
        if variant=='unknown_probe':raise ValueError('Unknown probe situation')
        if variant in ('unreviewed_joint','unknown_joint') and state('factor') and not state('mediator'):return 'probe_unreviewed'
        stage=path(state).index(point) if point in path(state) else 0
        if not state('mediator'):stage=0
        if variant=='single_response':stage=min(stage,1)
        return PROBES[stage]
    def presented(person,topic,scene):
        return variant!='not_presented' and person=='person' and topic in TOPICS[:2] and scene in PROBES
    def classified(person,topic,scene):
        if variant=='unknown_joint' and scene=='probe_unreviewed':raise ValueError('Unknown joint assessment')
        return scene!='probe_unreviewed' and presented(person,topic,scene)
    def judged(person,judgment,scene):
        return person==('other' if variant=='other_person' else 'person') and judgment in JUDGMENTS and scene in PROBES[:3] and JUDGMENTS.index(judgment)<PROBES.index(scene)
    def about(judgment,topic,scene):
        return judgment in JUDGMENTS and scene in PROBES and topic==(TOPICS[2] if variant=='wrong_topic' else TOPICS[JUDGMENTS.index(judgment)])
    def topics(person,start):
        if calls is not None:calls.append(('topics',person,start))
        return SequenceValue(TOPICS[:2] if (person,start)==('person','end') else (), '"individual"')
    def bound(person,start):
        if calls is not None:calls.append(('bound',person,start))
        return Fraction(1 if (person,start)==('person','end') else 0)
    p.update(iaipeople=lambda person,a:(person,a)==('person','end'),iaicases=lambda person,a,s:(person,a)==('person','end') and s in ('end','outside'),
        iaihistory=oldhistory,iaibefore=oldorder,jrperson=lambda:'person',jrstart=lambda:'end',jrend=lambda:'after',jrremaining=rest,
        jrstate=lambda:FunctionValue(('individual',),'truth',lambda x:x in VARIABLES and state_bits[VARIABLES.index(x)]),
        iajactivities=lambda person,start:SequenceValue(gradual.ACTIVITIES if start=='end' else (), '"individual"'),
        iajscope=lambda person,start,activity:(person,start)==('person','end') and activity in gradual.ACTIVITIES,
        iajbound=lambda person,start:Fraction(1 if start=='end' else 0),iajavailable=methods['available'],iajprospects=methods['prospects'],iajevaluated=methods['evaluated'],
        aa=lambda person:person=='person' and variant!='nonhuman',dg=lambda activity,point:activity in gradual.ACTIVITIES and point==gradual.HITS[gradual.ACTIVITIES.index(activity)],
        iajperforms=methods['truth'],iakvariables=lambda person,start,end:SequenceValue(VARIABLES,'"individual"'),
        iakequations=lambda person,start,end,variable,state:equations(2,ytable,variant)(variable,state),iakfactor=lambda person,start,end:'factor',
        iakobserved=lambda person,start,end:FunctionValue(('individual',),'truth',lambda variable:variable in VARIABLES),
        iakbegin=lambda person,start,end,state:path(state)[0],iakend=lambda person,start,end,state:path(state)[-1],
        iakhistory=lambda person,start,end,state,point:point in path(state),iakbefore=order,ialmediator=lambda person,start,end:'mediator',
        iamtopics=topics,iamscope=lambda person,start,topic:(person,start)==('person','end') and topic in TOPICS[:2],iambound=bound,
        iamprobe=probe,iampresented=presented,iamclassified=classified,
        fa=judged,fb=about,
        ab=lambda faculty,person,scene:(faculty,person)==('faculty','other' if variant=='other_owner' else 'person') and scene in PROBES,
        ac=lambda person,faculty,judgment,scene:(person,faculty)==('person','faculty') and judgment in JUDGMENTS and scene in PROBES,
        fc=lambda judgment,reason,scene:judgment in JUDGMENTS and reason=='reason' and scene in PROBES,
        fd=lambda reason,judgment,scene:variant!='unsupported' and reason=='reason' and judgment in JUDGMENTS and scene in PROBES,
        ad=lambda other,person,judgment,scene:variant=='guided' and (other,person)==('other','person') and judgment in JUDGMENTS and scene in PROBES)
    return p,domain,scenes


def source_values(*,indices=(0,1,4),memoize=True,**options):
    p,domain,scenes=source_model(**options)
    doc=deepcopy(source_fixture());doc['statements']=[doc['statements'][i] for i in indices]
    primitives={d['name']:p.get(d['name'],thinking.forbidden) for d in doc['declarations'] if d['kind']=='primitive'}
    return evaluate(doc,primitives,domain,scenes,memoize=memoize,budget=40_000_000)


def attribution(path=CORE,variant='baseline'):
    doc=deepcopy(document(path));doc['statements']=doc['statements'][-1:]
    p={d['name']:thinking.forbidden for d in doc['declarations'] if d['kind']=='primitive'}
    p.update(iagnode=lambda:'other' if variant=='node' else 'node',wa=lambda:'other' if variant=='author' else 'author',
        iagscope=lambda:'other' if variant=='scope' else 'scope',wh=lambda:'outside' if variant=='context' else 'end',
        iamreport=lambda node,author,code,scope,context:(node,author,scope,context)==('node','author','scope','end') and thinking.code_is(code,'iamschema',2))
    return [r['value'] for r in evaluate_document(doc,individuals=thinking.DOMAIN,situations=thinking.SCENES,primitives=p)]


CONTRASTS=('empty','duplicate','omitted','extra','hidden_middle','reflexive','unclassified','other_person','bad_indicator')
UNKNOWNS=('unknown_scope','unknown_history','unknown_order','unknown_classification','unknown_response')
SOURCE_CONTRASTS=('single_response','other_person','wrong_topic','other_owner','unsupported','guided','not_presented','nonhuman')


def alignment():
    unit=next(u for u in json.loads((ROOT/UNITS).read_text(encoding='utf-8'))['units'] if u['id']=='kant-1784:u0017')
    return dict(unit=unit['id'],text_sha256=unit['text_sha256'],status='explicit_interpretive_annotation',
        definitions=['iamresponse','iamassessed','iamchange','iamreviewed','iamschema','iamattribution'],
        adds_new_text_coverage=False,semantic_completion=False,mediator_content_unfilled=False,mediator_reading_unresolved=True)


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
        expected=counts[1]==counts[0]+1 and counts[2]==counts[1]+1
        assert values(tuple((1<<c)-1 for c in counts))==[True,expected],counts
    for variant in CONTRASTS:assert values(variant=variant,indices=(1,))==[False],variant
    for variant in UNKNOWNS:
        try:values(variant=variant,indices=(1,))
        except ValueError as error:assert 'Unknown' in str(error)
        else:raise AssertionError(variant)
    assert values(memoize=False)==values()
    assert source_values()==[True,True,False]
    assert source_values(indices=(2,3))==[True,True]
    assert source_values(ytable=12,indices=(2,))==[False]
    assert source_values(variant='unreviewed_joint',indices=(2,))==[False]
    for path in (CORE,SOURCE):
        assert attribution(path)==[True]
        for variant in ('node','author','scope','context'):assert attribution(path,variant)==[False]
    old,new=document(PARENT),document(SOURCE)
    assert new['declarations'][:len(old['declarations'])]==old['declarations'] and new['statements'][:-1]==old['statements'][:-1]
    paths=[PARENT,LIBRARY,SOURCE,CORE,BASIS,UNITS,'scripts/compose_reasoned_response.py','scripts/check_reasoned_response.py',
        'tests/test_reasoned_response.py','scripts/check_mediated_choice.py','scripts/check_thinking_disposition.py','scripts/check_gradual_choice.py',
        'scripts/check_caused_choice.py','noema/constructed.py','noema/constructed_semantics.py',
        'noema/constructed_closure_semantics.py','noema/diagnostic_short_circuit.py','data/mediator-reading-review-v1.json']
    return dict(status='reasoned_response_mediator_candidate_checked',documents=documents,count_profile_combinations=64,
        source_alignment=alignment(),roundtrips=True,uncached_generic_baseline_checked=True,source_uses_closure_cache=True,
        limitations=basis()['limitations'],verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in paths})


def main():
    cli=argparse.ArgumentParser(description=__doc__);cli.add_argument('--verify-only',action='store_true');args=cli.parse_args()
    r=build_report()
    if args.verify_only:assert json.loads(REPORT.read_text(encoding='utf-8'))==r
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:json.dump(r,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print('Reasoned-response candidate verified; source reading and full semantics remain unresolved')


if __name__=='__main__':main()
