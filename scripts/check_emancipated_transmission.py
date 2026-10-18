"""Check native self-achievement, first-send precedence and future recipients."""
import argparse
from copy import deepcopy
from functools import lru_cache
from itertools import permutations,product
import json
from noema.constructed import parse,format_graph
from noema.constructed_semantics import evaluate_document
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,selection_binding
from noema.script import transcribe
from scripts import check_transmitted_profiles as prior
from scripts.check_described_explanations import symbol
from scripts.compose_emancipated_transmission import ROOT,PARENT,PARENT_BASIS,FULL,CORE,LIBRARY,BASIS,MEANINGS,build

REPORT=ROOT/'reports/emancipated-transmission-v1.json'
ACTUAL=('prior','before','freed','first','second','now')
TEMPORAL=ACTUAL+('outside',)
POINTS=TEMPORAL+('trialbad','trialgood','exception')
DOMAIN=prior.relay.DOMAIN+('departure','faculty','plan')
NATIVE=tuple(dict.fromkeys(prior.PEOPLE+('departure','faculty','plan')))
EXTRA='r zdeparture[] a.r zprior[] d.r zattained[] d.r zframe[] a.r zinitial[] d.'


def unknown(*args):raise ValueError('Unknown departure interpretation')


def evaluate(doc,values,native=False,memoize=True):
    selected={d['name']:values[d['name']] for d in doc['declarations'] if d['kind']=='primitive'}
    return [row['value'] for row in evaluate_document(doc,individuals=NATIVE if native else DOMAIN,
        situations=POINTS if native else TEMPORAL,primitives=selected,max_steps=24000000,
        memoize_definitions=memoize,memoize_expressions=memoize)]


def generic_checks():
    doc=parse((ROOT/LIBRARY).read_text(encoding='utf-8')+'''
r zh[d] c.r zb[d d] c.r za[] d.r zs[] d.r zc[] d.
q[k rqtg[p zh p zb k za[] k zs[] k zc[]]].
''')
    points=('early','late','anchor');count=0
    def run(order,members,begun='late',cyclic=False,unknown_order=False):
        def before(a,b):
            if unknown_order:return unknown()
            return order.index(a)<order.index(b) or cyclic and (a,b)==('anchor','early')
        values=dict(zh=lambda point:point in members,zb=before,za=lambda:'early',zs=lambda:begun,zc=lambda:'anchor')
        result=evaluate_document(doc,individuals=('person',),situations=points,primitives=values,max_steps=100000,
            memoize_definitions=False,memoize_expressions=False)
        return [row['value'] for row in result]
    for order in permutations(points):
        for flags in product((False,True),repeat=3):
            members={p for p,yes in zip(points,flags) if yes}
            expected=all(flags) and order.index('early')<order.index('late')<=order.index('anchor')
            assert run(order,members)==[expected],(order,members);count+=1
    assert run(points,set(points),begun='anchor')==[True]
    assert run(points,set(points),begun='early')==[False]
    assert run(points,set(points),cyclic=True)==[False]
    try:run(points,set(points),unknown_order=True)
    except ValueError as error:assert 'Unknown' in str(error)
    else:raise AssertionError('Unknown order accepted')
    return dict(order_and_history_cases=count,same_time_completion_and_start_refused=True,
        start_at_anchor_allowed=True,cyclic_order_refused=True,unknown_order_refused=True,uncached=True)


@lru_cache(maxsize=12)
def document(kind='route',native=False,extent='rqsx'):
    state=prior.STATE if native else 'r[p zproperty]'
    if kind=='departure':query='k hzod[k zorigin[] k zdeparture[] k zprior[] k zattained[] k zpoint[k zfirst[]] k zanchor[]]'
    elif kind=='achievement':query='k h4p[k zorigin[] k zdeparture[] k zprior[] k zattained[] k zanchor[]]'
    elif kind=='route':query='k hzoe[k zfirst[] k zrest[] k zorigin[] k ztarget[] k zsubject[] r[p zmessage] '+state+' k zprocess[] k zstart[] k zend[] k zanchor[] p zsender p zrecipient p zactivity p zpoint k zdeparture[] k zprior[] k zattained[]]'
    else:
        assert kind=='future'
        query='k hzof[k zaudience[] k zreference[] k zorigin[] k zsubject[] r[p zmessage] '+state+' k zframe[] k zinitial[] k zanchor[] k zdeparture[] k zprior[] k zattained[] p zfirsts p ztails p zprocesses p zstarts p zends p zsender p zrecipient p zactivity p zpoint p '+extent+']'
    return parse((ROOT/CORE).read_text(encoding='utf-8')+prior.relay.FIXTURE+prior.ADDITIONS+EXTRA+'q['+query+'].')


def model(doc,variant='baseline',native=False,seen=None):
    mapped='both_acquire' if variant in ('both_acquire','one_past') else variant
    values=prior.model(doc,mapped,native=native,seen=seen)
    endpoint='first' if variant=='coincident_departure' else 'second' if variant=='late_departure' else 'freed'
    old={name:values[name] for name in ('ag','la','dg','g3','ia','ab','ac','ad') if name in values}
    def history(person,anchor,point):
        return person in ('sender','relay','reader') and anchor=='now' and point in ACTUAL and not (
            variant=='missing_departure_history' and person=='sender' and point==endpoint or
            variant=='missing_first_send_history' and person=='sender' and point=='first')
    def order(a,b,anchor):return anchor=='now' and a in ACTUAL and b in ACTUAL and ACTUAL.index(a)<ACTUAL.index(b)
    def available(person,plan,point):
        return (person,plan)==('sender','plan') and point in ACTUAL and (
            variant=='already_capable' or ACTUAL.index(point)>=ACTUAL.index(endpoint))
    def outcome(person,plan,start,end):return available(person,plan,start) and end==endpoint
    def assessed(person,plan,start,end):return outcome(person,plan,start,end) and variant!='unassessed_departure'
    def cause(act,person,description,point):
        if act=='departure':
            if seen is not None:seen.add(('departure_cause',person,symbol(description),point))
            return variant!='no_departure_cause' and (person,symbol(description),point)==(
                'relay' if variant=='other_departure_target' else 'sender',
                'bf' if variant=='wrong_departure_result' else 'h4l',endpoint)
        return old['g3'](act,person,description,point)
    values.update(zdeparture=lambda:'departure',zprior=lambda:'prior',zattained=lambda:endpoint,zframe=lambda:'audience',
        zinitial=lambda:'now' if variant=='no_future' else 'second' if variant=='completed_at_initial' else
            'first' if variant in ('started_before_initial','one_past') else 'outside' if variant=='initial_outside_frame' else 'freed',
        ia=history,ic=order,ae=available,af=outcome,ap=assessed,
        ab=lambda faculty,person,point:(faculty,person,point)==('faculty','sender',endpoint),
        ac=lambda person,faculty,act,point:(person,faculty,act,point)==('sender','faculty','departure',endpoint),
        ad=lambda guide,person,act,point:variant=='guided_result' and (guide,person,act,point)==('relay','sender','departure',endpoint),
        ag=lambda process,start,end:old['ag'](process,start,end) or variant!='no_departure_change' and (process,start,end)==('departure','prior',endpoint),
        la=lambda person,process,start,end:old['la'](person,process,start,end) or (person,process,start,end)==(
            'relay' if variant=='other_departure_subject' else 'sender','departure','prior',endpoint),
        dg=lambda act,point:old['dg'](act,point) or (act,point)==('departure',endpoint),
        df=lambda person,act,point:(person,act,point)==('relay' if variant=='other_departure_actor' else 'sender','departure',endpoint),
        h4m=lambda part,person,point:(part,person,point)==('faculty','relay' if variant=='other_mind' else 'sender',endpoint),
        h4n=lambda person,part,act,point:variant!='no_self_work' and (person,part,act,point)==('sender','faculty','departure',endpoint),
        g3=cause,
        h7q=lambda frame,anchor,point:frame=='audience' and anchor=='now' and point in ACTUAL and not (
            variant=='departure_outside_frame' and point==endpoint or variant=='first_send_outside_frame' and point=='first' or
            variant=='recipient_start_outside_frame' and point=='before' or variant=='recipient_end_outside_frame' and point=='second'))
    if variant=='other_origin':values['zorigin']=lambda:'relay'
    if variant=='different_context':values['zanchor']=lambda:'second'
    if seen is not None:
        def extent(scope,changed):
            domain=NATIVE if native else DOMAIN
            seen.add(('extent',tuple(sorted(p for p in domain if scope(p))),tuple(sorted(p for p in domain if changed(p)))))
            return True
        values['zanyextent']=extent
    return values


def source_checks():
    variants=('baseline','already_capable','unassessed_departure','guided_result','no_departure_change',
        'other_departure_subject','other_departure_actor','other_mind','no_self_work','no_departure_cause',
        'other_departure_target','wrong_departure_result','coincident_departure','late_departure',
        'missing_departure_history','missing_first_send_history','other_origin','different_context',
        'missing_receipt','wrong_causal_property','independent_message','lost_after')
    doc=document();rows={}
    for variant in variants:
        seen=set();actual=evaluate(doc,model(doc,variant,seen=seen))
        assert actual==[variant=='baseline'],(variant,actual);rows[variant]=actual
        if variant=='baseline':assert ('departure_cause','sender','h4l','freed') in seen
    # The rejected chronology is not a rejected achievement: compare in one graph.
    joined=deepcopy(document('achievement'));joined['statements']+=document()['statements']
    temporal={}
    for variant in ('baseline','coincident_departure','late_departure'):
        actual=evaluate(joined,model(joined,variant));assert actual==[True,variant=='baseline'],(variant,actual)
        temporal[variant]=actual
    doc=document('departure')
    for variant in ('baseline','no_self_work'):
        assert evaluate(doc,model(doc,variant),memoize=False)==[variant=='baseline']
    return dict(native_route_contrasts=rows,achievement_and_first_send_order=temporal,
        uncached_native_departure_agrees=True,source_definitions_not_replaced=True)


def future_checks():
    rows={}
    for extent in ('zanyextent','rqsy','rqsx'):
        for variant in ('baseline','both_acquire','one_past','empty_audience','nonhuman_audience'):
            doc=document('future',extent=extent);seen=set();actual=evaluate(doc,model(doc,variant,seen=seen))
            expected=variant not in ('empty_audience','nonhuman_audience') and (
                extent=='zanyextent' or variant=='both_acquire' or extent=='rqsx' and variant=='baseline')
            assert actual==[expected],(extent,variant,actual);rows[extent+':'+variant]=actual
            if extent=='zanyextent' and variant=='one_past':
                assert ('extent',('reader','relay'),('reader',)) in seen
    for variant in ('no_future','completed_at_initial','started_before_initial','initial_outside_frame',
        'departure_outside_frame','first_send_outside_frame','recipient_start_outside_frame','recipient_end_outside_frame'):
        doc=document('future');actual=evaluate(doc,model(doc,variant))
        assert actual==[variant=='started_before_initial'],(variant,actual);rows[variant]=actual
    return dict(contrasts=rows,future_applies_to_recipient_completion=True,
        transmission_can_start_at_or_before_initial=True,departures_and_routes_in_same_period_frame=True)


def native_profile_checks():
    doc=document('future',True);rows={}
    for variant in ('baseline','no_self_work','wrong_causal_property','no_assent'):
        actual=evaluate(doc,model(doc,variant,native=True),native=True)
        assert actual==[variant=='baseline'],(variant,actual);rows[variant]=actual
    return dict(contrasts=rows,departure_and_assessed_recipient_profile_executed_together=True)


def unknown_checks():
    doc=document('future')
    for name in ('ae','ap','h4m','h4n','df','g3','h7q','h6e'):
        values=model(doc);values[name]=unknown
        try:evaluate(doc,values)
        except ValueError as error:assert 'Unknown' in str(error),(name,error)
        else:raise AssertionError(name)
    return dict(unknown_inputs_refused=8)


def structure():
    old,new=load_catalog(ROOT,PARENT_BASIS),load_catalog(ROOT,BASIS)
    assert new.document['statements']==old.document['statements'] and len(new.document['statements'])==32
    assert new.document['declarations'][:-4]==old.document['declarations']
    for name,entry in old.entries.items():assert new.entries[name]==entry,name
    for index in (16,17,27,28,29,30,31):assert selection_binding(old,[index])==selection_binding(new,[index])
    return dict(new_definitions=4,new_primitives=0,existing_statements=32,seven_review_bindings_preserved=True,
        generic_characters=len((ROOT/LIBRARY).read_text(encoding='utf-8')),
        added_characters=len((ROOT/FULL).read_text(encoding='utf-8'))-len((ROOT/PARENT).read_text(encoding='utf-8')))


def alignment():
    path=ROOT/'artifacts/written-units-v1/kant-1784.json'
    inventory=json.loads((ROOT/'reports/written-units-v1.json').read_text(encoding='utf-8'))
    assert digest(path.read_bytes())==inventory['works']['kant-1784']['units_sha256']
    unit=next(u for u in json.loads(path.read_text(encoding='utf-8'))['units'] if u['id']=='kant-1784:u0011')
    text=unit['text'];assert digest(text.encode('utf-8'))==unit['text_sha256']
    start=text.index('nachdem sie');end=text.index('abgeworfen haben',start)+len('abgeworfen haben')
    return dict(unit=unit['id'],unit_sha256=unit['text_sha256'],start=start,end=end,source=text[start:end],
        definitions=list(MEANINGS),status='partial_self_departure_before_transmission',full_semantic_equivalence=False,
        remaining=['yoke metaphor and scope of self-emancipation','surrounding social scope and continuing self-thinking',
            'modal future and author attribution of the whole sentence'])


def build_report():
    outputs=build()
    for name,body in outputs.items():assert (ROOT/name).read_text(encoding='utf-8')==body,name
    for name in (FULL,CORE,LIBRARY):
        doc=parse((ROOT/name).read_text(encoding='utf-8'))
        for notation in ('compact','full'):
            text=format_graph(doc,notation);assert parse(text)==parse(transcribe(text,alphabet='v2'))==doc
    previous=json.loads((ROOT/'reports/transmitted-profiles-v1.json').read_text(encoding='utf-8'))
    for path,sha in previous['source_sha256'].items():assert digest((ROOT/path).read_bytes())==sha,path
    paths=set(load_catalog(ROOT,BASIS).source_sha256)|set(outputs)|set(previous['source_sha256'])|{
        'reports/transmitted-profiles-v1.json','scripts/compose_emancipated_transmission.py',
        'scripts/check_emancipated_transmission.py','tests/test_emancipated_transmission.py','docs/emancipated-transmission-v1.md'}
    return dict(status='origin_self_departure_and_future_recipient_completion_partial_reading',document=FULL,
        generic=generic_checks(),source=source_checks(),future=future_checks(),native_profile=native_profile_checks(),
        unknowns=unknown_checks(),structure=structure(),roundtrips=True,alignment=alignment(),new_source_assertions=0,
        verified_full_units={'kant-1784':0,'einstein-1905':0},active_review_index_unchanged='data/semantic-review-index-v22.json',
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})


def main():
    cli=argparse.ArgumentParser();cli.add_argument('--verify-only',action='store_true');args=cli.parse_args();report=build_report()
    if args.verify_only:assert json.loads(REPORT.read_text(encoding='utf-8'))==report
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:stream.write(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print('Origin self-departure, first-send precedence and future recipient scope checked',flush=True)


if __name__=='__main__':main()
