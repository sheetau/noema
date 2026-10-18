"""Check recipient scope without conflating contact, audience and successful uptake."""
import argparse
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,selection_binding
from noema.script import transcribe
from scripts import check_thinking_disseminators as prior
from scripts.compose_relative_dissemination import ROOT,PARENT,PARENT_BASIS,FULL,CORE,LIBRARY,BASIS,MEANINGS,build

REPORT=ROOT/'reports/relative-dissemination-v1.json'


def generic_checks():
    text=(ROOT/LIBRARY).read_text(encoding='utf-8')+'''
r zorigin[] a.r zreference[] d.r zrelation[a a d] c.r ztransition[a] c.
q[w[k rqsz[k zorigin[] k zreference[]
i[center a target a point d][k rqth[v center v target v point p zrelation]] p aa]][
k rqsw[i[target a][k rqth[k zorigin[] v target k zreference[] p zrelation]] p ztransition p rqsx]]].
'''
    doc=parse(text);people=('origin','first','second');points=('base','later');count=0
    for flags in product((False,True),repeat=6):
        members={p for p,b in zip(people[1:],flags[:2]) if b}
        changed={p for p,b in zip(people[1:],flags[2:4]) if b}
        humans={p for p,b in zip(people[1:],flags[4:]) if b}|{'origin'}
        calls=[]
        def relation(origin,target,point):
            calls.append((origin,point))
            return (origin,point)==('origin','base') and target in members|{'origin'}
        values=dict(zorigin=lambda:'origin',zreference=lambda:'base',zrelation=relation,
            ztransition=lambda p:p in changed,aa=lambda p:p in humans,sa=lambda *args:False)
        expected=bool(members) and members<=humans and members<=changed
        assert prior.evaluate(doc,values,people,points,memoize=False)==[expected],flags
        assert calls and set(calls)=={('origin','base')};count+=1
    # A directed relation is not silently reversed or transitively closed.
    doc=parse((ROOT/LIBRARY).read_text(encoding='utf-8')+'''
r zrelation[a a d] c.r zorigin[] a.r zfirst[] a.r zsecond[] a.r zbase[] d.r zlater[] d.
q[k rqth[k zorigin[] k zfirst[] k zbase[] p zrelation]].
q[k rqth[k zfirst[] k zorigin[] k zbase[] p zrelation]].
q[k rqth[k zorigin[] k zsecond[] k zbase[] p zrelation]].
q[k rqth[k zorigin[] k zfirst[] k zlater[] p zrelation]].
q[k rqth[k zorigin[] k zorigin[] k zbase[] p zrelation]].
''')
    values=dict(zorigin=lambda:'origin',zfirst=lambda:'first',zsecond=lambda:'second',zbase=lambda:'base',zlater=lambda:'later',
        zrelation=lambda a,b,t:t=='base' and (a,b) in (('origin','first'),('first','second'),('origin','origin')),
        aa=lambda p:True,sa=lambda *args:False)
    actual=prior.evaluate(doc,values,people,points,memoize=False)
    assert actual==[True,False,False,False,False],actual
    return dict(scope_uptake_and_human_combinations=count,direction_context_and_self=actual,
        no_automatic_symmetry_or_transitivity=True,uncached=True)


def access_checks():
    doc=parse((ROOT/LIBRARY).read_text(encoding='utf-8')+'''
r za[] a.r zb[] a.r zbase[] d.
q[k rqth[k za[] k zb[] k zbase[] p hzom]].
q[k rqth[k za[] k za[] k zbase[] p hzom]].
''');count=0
    for forward,backward,firsthuman,secondhuman in product((False,True),repeat=4):
        values=dict(za=lambda:'first',zb=lambda:'second',zbase=lambda:'base',
            aa=lambda p:firsthuman if p=='first' else secondhuman,
            sa=lambda a,b,t:t=='base' and (forward if (a,b)==('first','second') else backward if (a,b)==('second','first') else False))
        assert prior.evaluate(doc,values,('first','second'),('base',),memoize=False)==[
            firsthuman and secondhuman and (forward or backward),False]
        count+=1
    return dict(human_and_bidirectional_access_combinations=count,
        existing_sa_relation_composed_without_new_primitive=True,not_a_universal_definition_of_surroundings=True)


@lru_cache(maxsize=8)
def document(scope='zrelation',kind='single'):
    fixture=prior.profiles.relay.FIXTURE+prior.profiles.ADDITIONS+prior.departure.EXTRA+prior.GROUP_FIXTURE+prior.NATIVE_FIXTURE
    fixture+='r zrelation[a a d] c.'
    origins=('k zorigin[]','k zlastsender[]') if kind=='pair' else ('k zorigin[]',)
    queries=''.join('q['+prior.native_call(origin,'k zinitial[]')+'].' for origin in origins)
    doc=parse((ROOT/CORE).read_text(encoding='utf-8')+fixture+queries)
    old=deepcopy(doc['statements'])
    for statement in doc['statements']:
        body=statement['body'];args=body['arguments'];body['symbol']='hzol'
        body['arguments']=[*args[1:len(prior.FUTURE)],dict(kind='function_ref',symbol=scope),*args[len(prior.FUTURE):]]
    if kind=='joined':doc['statements']+=old
    return parse(format_graph(doc,'compact'))


def model(doc,variant='baseline',calls=None,legacy=False):
    mapped=variant if variant in ('no_sender_thinking','no_sender_transmission') else 'baseline'
    values=prior.native_model(doc,mapped)
    def relation(origin,target,point):
        if calls is not None:calls.add((origin,point))
        center='relay' if variant=='other_center' else 'sender'
        context='now' if variant=='other_reference' else 'before'
        members={'reader'}
        if variant=='empty':members=set()
        if variant=='self_only':members={'sender'}
        if variant=='include_self':members.add('sender')
        if variant in ('unreached_peer','late_success_only'):members.add('relay')
        if variant=='nonhuman':members.add('stepone')
        if variant=='late_success_only' and point=='now':return target=='reader'
        return (origin,point)==(center,context) and target in members
    values['zrelation']=relation
    values['sa']=lambda a,b,t:t=='before' and ((a,b)==('reader','sender') if variant=='reverse_access' else
        (a,b)==('sender','reader') and variant!='no_access')
    if not legacy:values['h6t']=prior.unknown
    return values


def source_checks():
    doc=document();rows={};expected_true={'baseline','include_self'}
    variants=('baseline','include_self','self_only','empty','other_center','other_reference',
        'unreached_peer','late_success_only','nonhuman','no_sender_thinking','no_sender_transmission')
    for variant in variants:
        calls=set();actual=prior.evaluate(doc,model(doc,variant,calls),diagnostic=True)
        assert actual==[variant in expected_true],(variant,actual)
        assert calls==(set() if variant=='no_sender_thinking' else {('sender','before')}),(variant,calls)
        rows[variant]=actual
    # The unchanged interpreter executes all semantic definitions for this
    # concrete profile; diagnostic results alone are not the native evidence.
    assert prior.evaluate(doc,model(doc))==rows['baseline']
    partial=deepcopy(doc)
    partial['statements'][0]['body']['arguments'][len(prior.FUTURE)-2]=dict(kind='function_ref',symbol='zanyextent')
    observed=[];values=model(partial,'unreached_peer')
    def any_extent(members,reached):
        population={p for p in prior.PEOPLE if members(p)}
        changed={p for p in prior.PEOPLE if reached(p)}
        observed.append((sorted(population),sorted(changed)))
        return bool(changed)
    values['zanyextent']=any_extent
    assert prior.evaluate(partial,values,diagnostic=True)==[True]
    assert observed==[(['reader','relay'],['reader'])],observed
    pair=document(kind='pair');calls=set()
    assert prior.evaluate(pair,model(pair,calls=calls),diagnostic=True)==[True,False]
    assert calls=={('sender','before'),('relay','before')}
    accessible=document('hzom');access={}
    for variant in ('baseline','reverse_access','no_access'):
        actual=prior.evaluate(accessible,model(accessible,variant),diagnostic=True)
        assert actual==[variant!='no_access'],(variant,actual);access[variant]=actual
    assert prior.evaluate(accessible,model(accessible))==[True]
    joined=document(kind='joined')
    assert prior.evaluate(joined,model(joined,legacy=True),diagnostic=True)==[True,True]
    values=model(joined,legacy=True);values['zrelation']=lambda *args:False
    assert prior.evaluate(joined,values,diagnostic=True)==[False,True]
    values=model(joined,legacy=True);values['h6t']=lambda *args:False
    assert prior.evaluate(joined,values,diagnostic=True)==[True,False]
    return dict(contrasts=rows,access_scope_contrasts=access,two_origin_results=[True,False],
        native_eager_comparisons=2,source_definitions_not_replaced_by_opaque_interpretations=True,
        contrasts_use_short_circuit_diagnostics=True,intended_audience_not_required_for_relative_scope=True,
        compatibility_only_when_scopes_agree=True,different_scopes_can_give_different_results=True,
        partial_reach_population=observed[0][0],partial_reach_acquired=observed[0][1],
        partial_reach_can_succeed_without_dropping_unreached_members=True)


def unknown_checks():
    for scope,name in (('zrelation','zrelation'),('zrelation','aa'),('zrelation','g3'),('hzom','sa')):
        doc=document(scope);values=model(doc);values[name]=prior.unknown
        try:prior.evaluate(doc,values)
        except ValueError as error:assert 'Unknown' in str(error),(name,error)
        else:raise AssertionError(name)
    return dict(unknown_inputs_refused=4,eager=True)


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
    previous=json.loads((ROOT/'reports/thinking-disseminators-v1.json').read_text(encoding='utf-8'))
    for path,sha in previous['source_sha256'].items():assert digest((ROOT/path).read_bytes())==sha,path
    alignment=deepcopy(json.loads((ROOT/'reports/message-relays-v1.json').read_text(encoding='utf-8'))['alignment'])
    unit=next(u for u in json.loads((ROOT/'artifacts/written-units-v1/kant-1784.json').read_text(encoding='utf-8'))['units'] if u['id']==alignment['unit'])
    assert digest(unit['text'].encode('utf-8'))==alignment['unit_sha256']
    assert unit['text'][alignment['start']:alignment['end']]==alignment['source']
    alignment.update(definitions=list(MEANINGS),status='partial_origin_relative_dissemination_scope',
        remaining=['source-appropriate social scope and extent','metaphor, discourse and future modality','author attribution and whole-unit meaning'])
    paths=set(load_catalog(ROOT,BASIS).source_sha256)|set(outputs)|set(previous['source_sha256'])|{
        'reports/thinking-disseminators-v1.json','reports/message-relays-v1.json','scripts/compose_relative_dissemination.py',
        'scripts/check_relative_dissemination.py','tests/test_relative_dissemination.py','docs/relative-dissemination-v1.md'}
    return dict(status='relative_recipient_scope_without_audience_conflation_partial_reading',document=FULL,
        generic=generic_checks(),access=access_checks(),source=source_checks(),unknowns=unknown_checks(),structure=structure(),
        roundtrips=True,alignment=alignment,new_source_assertions=0,
        verified_full_units={'kant-1784':0,'einstein-1905':0},active_review_index_unchanged='data/semantic-review-index-v22.json',
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})


def main():
    cli=argparse.ArgumentParser();cli.add_argument('--verify-only',action='store_true');args=cli.parse_args();report=build_report()
    if args.verify_only:assert json.loads(REPORT.read_text(encoding='utf-8'))==report
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:stream.write(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print('Origin-relative recipients and retained uptake checked separately from intended audience',flush=True)


if __name__=='__main__':main()
