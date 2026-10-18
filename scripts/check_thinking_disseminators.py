"""Execute appointment, independent judgment and dissemination on shared witnesses."""
import argparse
from copy import deepcopy
from fractions import Fraction
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse,format_graph
from noema.constructed_semantics import evaluate_document,SequenceValue
from noema.diagnostic_short_circuit import lower
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,selection_binding
from noema.script import transcribe
from scripts import check_emancipated_transmission as departure
from scripts import check_transmitted_profiles as profiles
from scripts.check_described_explanations import symbol
from scripts.compose_thinking_disseminators import ROOT,PARENT,PARENT_BASIS,FULL,CORE,LIBRARY,BASIS,MEANINGS,FUTURE,THINKING,build

REPORT=ROOT/'reports/thinking-disseminators-v1.json'
SMALL=('p','q','r','authority','role','appointment','group')
TIMES=('past','first','second')
PEOPLE=tuple(dict.fromkeys(('sender','relay','authority','role','appointment','faculty','facultyrelay','senderjudge','relayjudge')+departure.NATIVE))
POINTS=departure.POINTS
GROUP_FIXTURE='''
r zgoverned[] a.r zcheck[] d.r zbase[] d.r zmembers[a d] c.r zappointed[a a a a d] c.r zguardian[a a d] c.
r zqualified[a d] c.r zhistory[d] c.r zbefore[d d] c.r zopportunities[d] c.
'''


def unknown(*args):raise ValueError('Unknown qualified sender interpretation')


def evaluate(doc,values,people=PEOPLE,points=POINTS,memoize=True,diagnostic=False):
    selected={d['name']:values[d['name']] for d in doc['declarations'] if d['kind']=='primitive'}
    if diagnostic:doc,selected=lower(doc,selected)
    return [row['value'] for row in evaluate_document(doc,individuals=people,situations=points,primitives=selected,
        max_steps=120000000,memoize_definitions=memoize,memoize_expressions=memoize)]


@lru_cache(maxsize=3)
def group_document(future=False):
    query='k hzoi[p zhistory p zbefore k zbase[] p zopportunities p zmembers k zgoverned[] p zappointed p zguardian p zqualified]' if future else 'k hzoh[k zcheck[] p zmembers k zgoverned[] p zappointed p zguardian p zqualified]'
    if future=='whole':query='k hzoj[p zhistory p zbefore k zbase[] p zmembers k zgoverned[] p zappointed p zguardian p zqualified]'
    return parse((ROOT/LIBRARY).read_text(encoding='utf-8')+GROUP_FIXTURE+'q['+query+'].')


def group_model(doc,members=('p','q'),appointed=('p','q'),qualified=('p','q'),variant='baseline'):
    values={d['name']:unknown for d in doc['declarations'] if d['kind']=='primitive'}
    def active(person,point):
        if variant=='turnover':return person in (('p','q') if point=='first' else ('q','r') if point=='second' else ('p','q','r'))
        return person in appointed
    values.update(zgoverned=lambda:'group',zcheck=lambda:'first',zbase=lambda:'past',
        zmembers=lambda person,point:person in members,zqualified=lambda person,point:person in qualified,
        zappointed=lambda event,issuer,person,role,point:(event,issuer,role,point)==('appointment','authority','role','past') and person in ('p','q','r'),
        zguardian=lambda role,group,point:(role,group)==('role','group'),
        aa=lambda person:person in ('p','q','r'),
        ia=lambda person,anchor,point:point in TIMES and TIMES.index(point)<=TIMES.index(anchor),
        ic=lambda a,b,anchor:TIMES.index(a)<TIMES.index(b),
        cf=lambda person,role,point:role=='role' and active(person,point),
        dg=lambda event,point:(event,point)==('appointment','past'),
        zhistory=lambda point:point in TIMES,zbefore=lambda a,b:TIMES.index(a)<TIMES.index(b),
        zopportunities=lambda point:point in (() if variant=='empty' else ('past','first') if variant=='not_future' else ('first','second')))
    if variant=='missing_late_qualification':values['zqualified']=lambda person,point:person in qualified and not(person=='q' and point=='second')
    if variant=='split_people':values['zqualified']=lambda person,point:person=='r'
    if variant=='nonhuman':values['zmembers']=lambda person,point:person in (*members,'role')
    if variant=='past_only_appointment':values['cf']=lambda person,role,point:person in appointed and role=='role' and point=='past'
    if variant=='no_appointment_event':values['zappointed']=lambda *args:False
    return values


def group_checks():
    doc=group_document();count=0
    for flags in product((False,True),repeat=6):
        members={p for p,flag in zip(('p','q'),flags[:2]) if flag}
        appointed={p for p,flag in zip(('p','q'),flags[2:4]) if flag}
        qualified={p for p,flag in zip(('p','q'),flags[4:]) if flag}
        actual=evaluate(doc,group_model(doc,members,appointed,qualified),SMALL,TIMES)
        assert actual==[len(members&appointed&qualified)>=2],(flags,actual);count+=1
    rows={}
    for variant in ('baseline','split_people','nonhuman','past_only_appointment','no_appointment_event'):
        actual=evaluate(doc,group_model(doc,members=('p','q','r'),variant=variant),SMALL,TIMES)
        assert actual==[variant=='baseline'],(variant,actual);rows[variant]=actual
    return dict(membership_appointment_and_joint_condition_combinations=count,contrasts=rows,
        native_appointment_definitions_executed=True,qualified_condition_supplied_only_in_this_generic_test=True)


def future_checks():
    doc=group_document(True);rows={}
    for variant in ('baseline','turnover','empty','not_future','missing_late_qualification','split_people'):
        values=group_model(doc,members=('p','q','r'),qualified=('p','q','r'),variant=variant)
        actual=evaluate(doc,values,SMALL,TIMES)
        assert evaluate(doc,values,SMALL,TIMES,diagnostic=True)==actual
        assert actual==[variant in ('baseline','turnover')],(variant,actual);rows[variant]=actual
    joined=deepcopy(doc);joined['statements']+=group_document('whole')['statements']
    values=group_model(joined,variant='missing_late_qualification');values['zopportunities']=lambda point:point=='first'
    assert evaluate(joined,values,SMALL,TIMES)==[True,False]
    assert evaluate(joined,values,SMALL,TIMES,diagnostic=True)==[True,False]
    whole=group_document('whole')
    assert evaluate(whole,group_model(whole,members=('p','q','r'),qualified=('p','q','r'),variant='turnover'),SMALL,TIMES)==[True]
    values=group_model(whole);values['zhistory']=lambda point:point=='past'
    assert evaluate(whole,values,SMALL,TIMES)==[False]
    return dict(contrasts=rows,different_people_at_different_points_allowed=True,empty_scope_refused=True,
        selected_scope_vs_whole_future=[True,False],unsuccessful_future_points_cannot_be_omitted=True,
        eager_and_diagnostic_comparisons=7)


NATIVE_FIXTURE='''
r zfirstfor[a] a.r zendfor[a] d.
r zthinkpoints[a d] j[d].r zthinkcases[a d d] c.r zthinkassessed[a d d] c.r zthinkweights[a d d] b.
r zthinkthreshold[a d] b.r zthinktopics[a d d] a.r zthinkpresented[a a d] c.
r zsurveyhistory[d] c.
'''


def native_call(origin='v origin',point='v opportunity'):
    args={name:'k z'+name+'[]' for name,sort in FUTURE}
    args.update(audience='k zaudience[]',reference='k zreference[]',origin=origin,subject='k zsubject[]',message='r[p zmessage]',
        state=profiles.STATE,initial=point,prior='k zprior[]',
        firsts='i[target a][k zfirstfor['+origin+']]',tails='i[target a][l[a][]]',
        processes='p zprocesses',starts='p zstarts',ends='i[target a][k zendfor['+origin+']]',
        sender='p zsender',recipient='p zrecipient',activity='p zactivity',point='p zpoint',extent='p rqsx')
    return 'k hzog['+' '.join(args[n] for n,t in FUTURE)+' '+' '.join('p z'+n for n,t in THINKING)+']'


@lru_cache(maxsize=4)
def native_document(kind='individual'):
    fixture=profiles.relay.FIXTURE+profiles.ADDITIONS+departure.EXTRA+GROUP_FIXTURE+NATIVE_FIXTURE
    joint='i[origin a opportunity d]['+native_call()+']'
    if kind=='individual':queries='q['+native_call('k zorigin[]','k zinitial[]')+'].'
    elif kind=='pair':queries='q['+native_call('k zorigin[]','k zinitial[]')+'].q['+native_call('k zlastsender[]','k zinitial[]')+'].'
    elif kind=='group':queries='q[k hzoh[k zinitial[] p zmembers k zgoverned[] p zappointed p zguardian '+joint+']].'
    else:
        assert kind=='future'
        queries='q[k hzoj[p zsurveyhistory p zbefore k zbase[] p zmembers k zgoverned[] p zappointed p zguardian '+joint+']].'
    return parse((ROOT/CORE).read_text(encoding='utf-8')+fixture+queries)


def native_model(doc,variant='baseline',seen=None):
    values=departure.model(doc,native=True)
    originals={name:values[name] for name in ('fa','fb','fc','fd','hznm','hznn','g3')}
    actors=('sender','relay');faculty={'sender':'faculty','relay':'facultyrelay'};judgment={'sender':'senderjudge','relay':'relayjudge'}
    steps={'stepone':('sender','first'),'steptwo':('relay','second')}
    def source_judgment(person,act,scene):
        return person in actors and act==judgment[person] and scene==('freed' if variant=='actual_episode_only' else 'trialgood') and not(
            variant in ('no_sender_thinking','split_people') and person=='sender' or variant=='no_relay_thinking' and person=='relay')
    def about(act,topic,scene):return topic=='topic' and any(source_judgment(p,act,scene) for p in actors)
    def available(person,plan,point):return person in actors and plan=='plan' and point in departure.ACTUAL and departure.ACTUAL.index(point)>=departure.ACTUAL.index('freed')
    def payload(act,target,subject,description,point):
        return act in steps and (target,subject,symbol(description),point)==('reader','topic','zmessage',steps[act][1])
    def produced(act,person,description,point):
        if act=='departure':return person in actors and symbol(description)=='h4l' and point=='freed'
        if seen is not None:seen.add(('cause',act,person,description.syntax,point))
        return act in steps and (person,point)==('reader',steps[act][1]) and json.loads(description.syntax)==profiles.described_state() and not(
            variant in ('no_relay_transmission','split_people') and steps[act][0]=='relay' or
            variant=='no_sender_transmission' and steps[act][0]=='sender')
    values.update(zgoverned=lambda:'audience',zcheck=lambda:'freed',zbase=lambda:'before',zlastsender=lambda:'relay',
        zfirstfor=lambda person:'steptwo' if person=='relay' else 'stepone',zendfor=lambda person:'second' if person=='relay' else 'first',
        zmembers=lambda person,point:person in actors,
        zappointed=lambda event,issuer,person,role,point:(event,issuer,role,point)==('appointment','authority','role','before') and person in actors,
        zguardian=lambda role,group,point:(role,group)==('role','audience'),
        zhistory=lambda point:point in departure.ACTUAL,zbefore=lambda a,b:a in departure.ACTUAL and b in departure.ACTUAL and departure.ACTUAL.index(a)<departure.ACTUAL.index(b),
        zopportunities=lambda point:point=='freed',zsurveyhistory=lambda point:point in ('before','freed'),zqualified=unknown,
        zrecipient=lambda step:'reader',
        zthinkpoints=lambda person,anchor:profiles.sequence(('trialgood',)),
        zthinkcases=lambda person,anchor,scene:scene=='trialgood',zthinkassessed=lambda person,anchor,scene:variant!='unassessed_thinking',
        zthinkweights=lambda person,anchor,scene:Fraction(1),zthinkthreshold=lambda person,anchor:Fraction(1),
        zthinktopics=lambda person,anchor,scene:'criterion' if variant=='wrong_thinking_topic' else 'topic',
        zthinkpresented=lambda person,topic,scene:person in actors and topic=='topic' and scene=='trialgood',
        ia=lambda person,anchor,point:person in (*actors,'reader') and anchor in departure.ACTUAL and point in departure.ACTUAL and departure.ACTUAL.index(point)<=departure.ACTUAL.index(anchor),
        ic=lambda a,b,anchor:a in departure.ACTUAL and b in departure.ACTUAL and departure.ACTUAL.index(a)<departure.ACTUAL.index(b),
        cf=lambda person,role,point:person in actors and role=='role' and point in ('before','freed','first','second','now'),
        ae=available,af=lambda person,plan,start,end:available(person,plan,start) and end=='freed',
        ap=lambda person,plan,start,end:available(person,plan,start) and end=='freed',
        ab=lambda f,person,scene:person in actors and f==faculty[person] and scene in ('freed','trialgood'),
        ac=lambda person,f,act,scene:person in actors and f==faculty[person] and ((act,scene)==('departure','freed') or source_judgment(person,act,scene)),
        ad=lambda guide,person,act,scene:variant=='guided_thinking' and guide=='authority' and source_judgment(person,act,scene),
        fa=lambda person,act,scene:originals['fa'](person,act,scene) or source_judgment(person,act,scene),
        fb=lambda act,topic,scene:originals['fb'](act,topic,scene) or about(act,topic,scene),
        fc=lambda act,reason,scene:originals['fc'](act,reason,scene) or reason=='reason' and any(source_judgment(p,act,scene) for p in actors),
        fd=lambda reason,act,scene:originals['fd'](reason,act,scene) or variant!='unsupported_thinking' and reason=='reason' and any(source_judgment(p,act,scene) for p in actors),
        ag=lambda process,start,end:(process,start,end)==('departure','prior','freed') or process=='process' and start=='before' and end in ('first','second'),
        la=lambda person,process,start,end:person in actors and (process,start,end)==('departure','prior','freed') or person=='reader' and process=='process' and start=='before' and end in ('first','second'),
        dg=lambda act,point:(act,point) in (('appointment','before'),('departure','freed'),('stepone','first'),('steptwo','second'),('process','first'),('process','second')),
        df=lambda person,act,point:person in actors and (act,point)==('departure','freed'),
        h4m=lambda part,person,point:person in actors and part==faculty[person] and point=='freed',
        h4n=lambda person,part,act,point:person in actors and part==faculty[person] and (act,point)==('departure','freed'),
        f3=lambda person,act,point:act in steps and (person,point)==steps[act],f2=payload,h6e=payload,
        h6g=lambda person,subject,description,point:(person,subject,symbol(description))==('reader','topic','zmessage') and point in ('first','second'),
        g3=produced)
    # Preserve two different acquisition endpoints for the same content. The
    # process starts before both; both sender acts can contribute to the result.
    oldpoints,oldcases=values['zpoints'],values['zcases']
    values['zpoints']=lambda person,anchor:profiles.sequence(('trialgood','exception')) if person=='reader' and anchor in ('first','second','now') else oldpoints(person,anchor)
    values['zcases']=lambda person,anchor,scene:scene in ('trialgood','exception') if person=='reader' and anchor in ('first','second','now') else oldcases(person,anchor,scene)
    return values


def individual_checks():
    doc=native_document();rows={}
    variants=('baseline','no_sender_thinking','actual_episode_only','unassessed_thinking','wrong_thinking_topic','guided_thinking','unsupported_thinking')
    for variant in variants:
        actual=evaluate(doc,native_model(doc,variant));assert actual==[variant=='baseline'],(variant,actual);rows[variant]=actual
    pair=native_document('pair');actual=evaluate(pair,native_model(pair,'split_people'))
    assert actual==[False,False],actual
    return dict(contrasts=rows,split_thinkers_and_transmitters=[False,False],
        native_independent_judgment_and_self_departure_executed=True)


def composite_checks():
    results={}
    for kind in ('group','future'):
        doc=native_document(kind);seen=set();before=deepcopy(doc)
        actual=evaluate(doc,native_model(doc,seen=seen),diagnostic=kind=='future')
        assert actual==[True],(kind,actual)
        assert doc==before
        assert {row[1] for row in seen if row[0]=='cause'}>={'stepone','steptwo'}
        results[kind]=actual
        if kind=='group':assert evaluate(doc,native_model(doc),diagnostic=True)==actual
    return dict(results=results,two_distinct_senders_with_distinct_transmission_acts=True,
        appointment_judgment_departure_and_concrete_profile_evaluated_in_one_graph=True,
        group_evaluated_without_lowering_or_replacement=True,group_eager_matches_diagnostic=True,
        future_uses_explicit_short_circuit_diagnostic=True,
        future_eager_limit='Exceeded 120000000 steps; no eager result claimed',
        no_semantic_definition_replaced_by_an_opaque_interpretation=True,
        scope_is_one_explicit_future_opportunity=True)


def unknown_checks():
    for name in ('zappointed','cf','zqualified'):
        doc=group_document();values=group_model(doc);values[name]=unknown
        try:evaluate(doc,values,SMALL,TIMES)
        except ValueError as error:assert 'Unknown' in str(error),(name,error)
        else:raise AssertionError(name)
    for name in ('zthinkassessed','zthinkpresented','fd','hznn'):
        doc=native_document();values=native_model(doc);values[name]=unknown
        try:evaluate(doc,values)
        except ValueError as error:assert 'Unknown' in str(error),(name,error)
        else:raise AssertionError(name)
    return dict(unknown_inputs_refused=7)


def structure():
    old,new=load_catalog(ROOT,PARENT_BASIS),load_catalog(ROOT,BASIS)
    assert new.document['statements']==old.document['statements'] and len(new.document['statements'])==32
    assert new.document['declarations'][:-4]==old.document['declarations']
    for name,entry in old.entries.items():assert new.entries[name]==entry,name
    for index in (16,17,27,28,29,30,31):assert selection_binding(old,[index])==selection_binding(new,[index])
    return dict(new_definitions=4,new_primitives=0,existing_statements=32,seven_review_bindings_preserved=True,
        generic_characters=len((ROOT/LIBRARY).read_text(encoding='utf-8')),
        added_characters=len((ROOT/FULL).read_text(encoding='utf-8'))-len((ROOT/PARENT).read_text(encoding='utf-8')))


def build_report():
    outputs=build()
    for name,body in outputs.items():assert (ROOT/name).read_text(encoding='utf-8')==body,name
    for name in (FULL,CORE,LIBRARY):
        doc=parse((ROOT/name).read_text(encoding='utf-8'))
        for notation in ('compact','full'):
            text=format_graph(doc,notation);assert parse(text)==parse(transcribe(text,alphabet='v2'))==doc
    previous=json.loads((ROOT/'reports/emancipated-transmission-v1.json').read_text(encoding='utf-8'))
    for path,sha in previous['source_sha256'].items():assert digest((ROOT/path).read_bytes())==sha,path
    appointed=json.loads((ROOT/'reports/appointed-thinkers-v1.json').read_text(encoding='utf-8'))
    alignment=deepcopy(appointed['alignment'])
    unit=next(u for u in json.loads((ROOT/'artifacts/written-units-v1/kant-1784.json').read_text(encoding='utf-8'))['units'] if u['id']=='kant-1784:u0011')
    for row in alignment['segments']:
        assert digest(unit['text'].encode('utf-8'))==row['unit_sha256']
        assert unit['text'][row['start']:row['end']]==row['source']
        row.update(definitions=list(MEANINGS),status='partial_same_appointed_thinking_disseminators',
            remaining=['source-appropriate independent profiles and social scopes','scalar contrast and causal discourse','unbounded future, freedom and author attribution'])
    paths=set(load_catalog(ROOT,BASIS).source_sha256)|set(outputs)|set(previous['source_sha256'])|{
        'reports/emancipated-transmission-v1.json','reports/appointed-thinkers-v1.json','scripts/compose_thinking_disseminators.py',
        'noema/diagnostic_short_circuit.py','tests/test_diagnostic_short_circuit.py',
        'scripts/check_thinking_disseminators.py','tests/test_thinking_disseminators.py','docs/thinking-disseminators-v1.md'}
    return dict(status='same_people_appointed_independent_and_disseminating_partial_reading',document=FULL,
        groups=group_checks(),future=future_checks(),individuals=individual_checks(),composite=composite_checks(),
        unknowns=unknown_checks(),structure=structure(),roundtrips=True,alignment=alignment,new_source_assertions=0,
        verified_full_units={'kant-1784':0,'einstein-1905':0},active_review_index_unchanged='data/semantic-review-index-v22.json',
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})


def main():
    cli=argparse.ArgumentParser();cli.add_argument('--verify-only',action='store_true');args=cli.parse_args();report=build_report()
    if args.verify_only:assert json.loads(REPORT.read_text(encoding='utf-8'))==report
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:stream.write(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print('Same appointed thinkers execute departure and dissemination with native definitions',flush=True)


if __name__=='__main__':main()
