"""Check profiles independently of current episodes and retain a caused receipt."""
import argparse
from copy import deepcopy
from fractions import Fraction
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse,format_graph
from noema.constructed_semantics import evaluate_document,SequenceValue
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,selection_binding
from noema.script import transcribe
from scripts import check_communicated_attitudes as relay
from scripts import check_reasoned_self_appraisal as appraisal
from scripts.compose_transmitted_profiles import ROOT,PARENT,PARENT_BASIS,FULL,CORE,LIBRARY,BASIS,MEANINGS,build

REPORT=ROOT/'reports/transmitted-profiles-v1.json'
POINTS=('before','first','second','now','trialbad','trialgood','exception')
PEOPLE=tuple(dict.fromkeys(tuple('reader' if p=='person' else p for p in appraisal.DOMAIN)+relay.DOMAIN))
PROVIDERS='r[p zpoints] r[p zcases] r[p zassessed] r[p zweights] r[p zthreshold]'
STATE='k hzny[r[k zcriterion[]] r[k zsubject[]] r[k zsource[]] r[k zrole[]] '+PROVIDERS+']'
ADDITIONS='''
r zcriterion[] a.r zsource[] a.r zrole[] a.r zothercriterion[] a.
r zpoints[a d] j[d].r zcases[a d d] c.r zassessed[a d d] c.r zweights[a d d] b.r zthreshold[a d] b.
'''


def unknown(*args):raise ValueError('Unknown profile interpretation')


def evaluate(doc,values,people=PEOPLE,points=POINTS,memoize=True):
    values={d['name']:values[d['name']] for d in doc['declarations'] if d['kind']=='primitive'}
    return [row['value'] for row in evaluate_document(doc,individuals=people,situations=points,primitives=values,
        max_steps=16000000,memoize_definitions=memoize,memoize_expressions=memoize)]


def arithmetic():
    return dict(ha=lambda a,b:a+b,hb=lambda a,b:a*b,hc=lambda a,b:a<b,hd=lambda truth:Fraction(int(truth)))


def sequence(items):return SequenceValue(tuple(items),'"situation"')


def generic_checks():
    doc=parse((ROOT/LIBRARY).read_text(encoding='utf-8')+'''
r zperson[] a.r zpoint[] d.r zrespond[a d] c.
d zresponse[person a] e[b scene[k zrespond[v person v scene]]].
'''+ADDITIONS+'''q[t[c[s[k hznx[r[p zresponse] '''+PROVIDERS+''']]][k zperson[]]][k zpoint[]]].''')
    scenes=('actual','left','right');rows={};count=0
    def model(flags=(True,False),threshold=Fraction(1,2),variant='baseline'):
        items=('left','right')
        if variant=='empty':items=()
        if variant=='duplicate':items=('left','left','right')
        if variant=='omitted':items=('left',)
        if variant=='extra':items=('left','right','actual')
        if variant=='permuted':items=('right','left')
        return dict(arithmetic(),zperson=lambda:'person',zpoint=lambda:'actual',
            zrespond=lambda person,scene:person=='person' and scene in ('left','right') and flags[('left','right').index(scene)],
            zpoints=lambda person,anchor:sequence(items),zcases=lambda person,anchor,scene:scene in ('left','right'),
            zassessed=lambda person,anchor,scene:not(variant=='unassessed' and scene=='right'),
            zweights=lambda person,anchor,scene:Fraction(0 if variant=='zero_weight' else -1 if variant=='negative_weight' else 1),
            zthreshold=lambda person,anchor:threshold,zcriterion=unknown,zsource=unknown,zrole=unknown,zothercriterion=unknown)
    for flags in product((False,True),repeat=2):
        for threshold in (Fraction(1,2),Fraction(1),Fraction(3,4)):
            actual=evaluate(doc,model(flags,threshold),('person','other'),scenes,False)
            assert actual==[Fraction(sum(flags),2)>=threshold],(flags,threshold,actual);count+=1
    for variant in ('baseline','empty','duplicate','omitted','extra','permuted','unassessed','zero_weight','negative_weight'):
        actual=evaluate(doc,model(variant=variant),('person','other'),scenes,False)
        assert actual==[variant in ('baseline','permuted')],(variant,actual);rows[variant]=actual
    for threshold in (Fraction(0),Fraction(-1),Fraction(3,2)):
        assert evaluate(doc,model((True,True),threshold),('person','other'),scenes,False)==[False]
    for name in ('zrespond','zcases','zassessed','zweights','zthreshold'):
        values=model();values[name]=unknown
        try:evaluate(doc,values,('person','other'),scenes)
        except ValueError as error:assert 'Unknown' in str(error)
        else:raise AssertionError(name)
    return dict(weighted_response_combinations=count,range_contrasts=rows,invalid_thresholds_refused=3,
        unknown_inputs_refused=5,current_episode_not_required=True,uncached=True)


@lru_cache(maxsize=12)
def document(kind='retained',native=False,extent='rqsx'):
    state=STATE if native else 'r[p zproperty]'
    base='k zfirst[] k zrest[] k zorigin[] k ztarget[] k zsubject[] r[p zmessage] '+state+' k zprocess[] k zstart[] k zend[] k zanchor[] p zsender p zrecipient p zactivity p zpoint'
    if kind in ('route','retained'):query='k '+('hzoa' if kind=='route' else 'hzob')+'['+base+']'
    elif kind=='profile':query='t[c[s['+state+']][k ztarget[]]][k zanchor[]]'
    elif kind=='episode':query='t[c[s[k hznv[r[k zcriterion[]] r[k zsubject[]] r[k zsource[]] r[k zrole[]]]]][k ztarget[]]][k zanchor[]]'
    else:
        assert kind=='collective'
        query='k hzoc[k zaudience[] k zreference[] k zorigin[] k zsubject[] r[p zmessage] '+state+' k zanchor[] p zfirsts p ztails p zprocesses p zstarts p zends p zsender p zrecipient p zactivity p zpoint p '+extent+']'
    return parse((ROOT/CORE).read_text(encoding='utf-8')+relay.FIXTURE+ADDITIONS+'q['+query+'].')


def described_state(variant='baseline'):
    response=appraisal.profile_syntax('zothercriterion' if variant=='wrong_causal_property' else 'zcriterion')
    return dict(kind='apply',function=dict(kind='function_ref',symbol='hznw'),arguments=[response]+[
        dict(kind='function_ref',symbol=name) for name in ('zpoints','zcases','zassessed','zweights','zthreshold')])


def model(doc,variant='baseline',native=False,length=2,seen=None):
    # Reuse the established native message-route fixture, not replaced definitions.
    values=relay.model(doc,variant,length=length,seen=seen)
    old_accepts=values['id'];old_cause=values['g3'];old_history=values['ia']
    def history(person,anchor,point):return point in relay.SCENES and old_history(person,anchor,point)
    values['ia']=history
    values['ic']=lambda a,b,anchor:anchor=='now' and a in relay.SCENES and b in relay.SCENES and relay.SCENES.index(a)<relay.SCENES.index(b)
    values['zstatecontent']=lambda person,point:point in relay.SCENES and old_accepts(person,type('D',(),{'syntax':'{"kind":"function_ref","symbol":"zproperty"}'})(),point)
    if variant=='lost_then_regained':
        ordinary=values['zstatecontent']
        values['zstatecontent']=lambda person,point:ordinary(person,point) and point!='second'
    def causes(act,person,description,point):
        expected=described_state(variant) if native else dict(kind='function_ref',symbol='zotherproperty' if variant=='wrong_causal_property' else 'zproperty')
        if seen is not None:seen.add(('newcause',description.syntax))
        if json.loads(description.syntax)!=expected:return False
        # Use the old fixture's recipient, final-activity and causal conditions.
        old_description=type('D',(),{'syntax':json.dumps(relay.attitude_syntax('zotherproperty' if variant=='wrong_causal_property' else 'zproperty'))})()
        return old_cause(act,person,old_description,point)
    values['g3']=causes;values['id']=unknown
    values.update(arithmetic())
    for name in ('zcriterion','zsource','zrole','zothercriterion'):
        values[name]=(lambda value:lambda:value)('criterion' if name in ('zcriterion','zothercriterion') else 'source' if name=='zsource' else 'role')
    def selected(person,anchor):
        good=anchor in relay.SCENES and old_accepts(person,type('D',(),{'syntax':'{"kind":"function_ref","symbol":"zproperty"}'})(),anchor)
        return ('trialgood' if good else 'trialbad','exception')
    values.update(zpoints=lambda person,anchor:sequence(selected(person,anchor)),
        zcases=lambda person,anchor,scene:scene in selected(person,anchor),
        zassessed=lambda person,anchor,scene:True,zweights=lambda person,anchor,scene:Fraction(1),
        zthreshold=lambda person,anchor:Fraction(1,2))
    if native:
        original=appraisal.model(doc,variant if variant in ('no_appraisal','no_assent','different_support','different_claim') else 'baseline')
        def translate(value):
            if value in ('reader','relay'):return 'person'
            if value in POINTS:return 'now' if value=='trialgood' else 'before'
            return value
        for name in ('fa','fb','fc','fd','hznm','hznn'):
            fn=original[name]
            values[name]=(lambda fn:lambda *args:fn(*(translate(value) if isinstance(value,str) else value for value in args)))(fn)
        if variant=='split_responses':
            # Both components succeed in half the opportunities, but never together.
            for name in ('fa','fb','fc','fd','hznm','hznn'):
                fn=original[name]
                def separated(*args,fn=fn,name=name):
                    converted=[translate(value) if isinstance(value,str) else value for value in args]
                    scene=args[-1]
                    converted[-1]='now' if scene in ('trialgood','exception') and (
                        name not in ('hznm','hznn') or scene==('trialgood' if name=='hznm' else 'exception')) else 'before'
                    return fn(*converted)
                values[name]=separated
        values['h7k']=unknown
    return values


def route_checks():
    rows={}
    variants=('baseline','missing_receipt','not_understood','no_acquisition','already_accepted','no_change',
        'no_cause','wrong_causal_property','wrong_causal_person','first_step_cause','unrelated_cause',
        'wrong_affected_person','different_process_part','missing_process_occurrence','wrong_message_subject',
        'wrong_message_force','independent_message','disconnected_relay','missing_target_history',
        'missing_origin_history','late_start','future_endpoint','lost_after')
    for variant in variants:
        doc=document();actual=evaluate(doc,model(doc,variant),relay.DOMAIN,relay.SCENES)
        assert actual==[variant=='baseline'],(variant,actual);rows[variant]=actual
    doc=document('route');assert evaluate(doc,model(doc,'lost_after'),relay.DOMAIN,relay.SCENES)==[True]
    for length in (1,2):
        doc=document();assert evaluate(doc,model(doc,length=length),relay.DOMAIN,relay.SCENES,memoize=False)==[True]
    doc=document();assert evaluate(doc,model(doc,'lost_after'),relay.DOMAIN,relay.SCENES,memoize=False)==[False]
    lapse={}
    for kind in ('route','retained'):
        doc=document(kind);actual=evaluate(doc,model(doc,'lost_then_regained',length=1),relay.DOMAIN,relay.SCENES)
        assert actual==[kind=='route'];lapse[kind]=actual
    return dict(contrasts=rows,acquisition_and_retention_distinct=True,uncached_direct_and_relay_agree=True,
        favorable_self_acceptance_not_evaluated=True,intermediate_loss_not_hidden_by_recovery=lapse)


def native_checks():
    doc=document('profile',True);joint=deepcopy(doc);joint['statements']+=document('episode',True)['statements']
    seen=set();actual=evaluate(joint,model(joint,native=True,seen=seen))
    assert actual==[True,False],actual
    rows={}
    for variant in ('baseline','no_appraisal','no_assent','different_support','different_claim','wrong_causal_property','lost_after','split_responses'):
        doc=document(native=True);seen=set();actual=evaluate(doc,model(doc,variant,native=True,seen=seen))
        assert actual==[variant=='baseline'],(variant,actual);rows[variant]=actual
        if variant=='baseline':assert any(row[0]=='newcause' and json.loads(row[1])==described_state() for row in seen)
    return dict(native_retained_route_contrasts=rows,profile_and_current_episode=[True,False],
        full_appraisal_and_assent_definitions_executed=True,norm_truth_and_task_execution_not_evaluated=True,
        same_constructed_profile_is_causal_target=True)


def quotation_checks():
    for rank in (0,1):
        doc=deepcopy(document());body=doc['statements'][0]['body']
        quoted=dict(kind='quote',body=body,**({'rank':rank} if rank else {}))
        doc['statements'][0]['body']=dict(kind='disquote',description=quoted)
        if rank:
            doc=parse(format_graph(doc,'compact'))
            assert evaluate(doc,model(doc),relay.DOMAIN,relay.SCENES)==[True]
        else:
            try:parse(format_graph(doc,'compact'))
            except ValueError as error:assert 'strictly lower ranks' in str(error)
            else:raise AssertionError('Same-rank quotation was accepted')
    return dict(rank_one_claim_evaluable=True,same_rank_claim_refused=True)


def collective_checks():
    rows={}
    for extent in ('zanyextent','rqsy','rqsx'):
        for variant in ('baseline','both_acquire','one_of_two','empty_audience','nonhuman_audience','lost_after'):
            doc=document('collective',extent=extent);seen=set()
            actual=evaluate(doc,model(doc,variant,seen=seen),relay.DOMAIN,relay.SCENES)
            expected=variant not in ('empty_audience','nonhuman_audience','lost_after') and (
                extent=='zanyextent' or variant=='both_acquire' or extent=='rqsx' and variant=='baseline')
            assert actual==[expected],(extent,variant,actual)
            assert {row[1] for row in seen if row[0]=='audience'}=={'before'}
            rows[extent+':'+variant]=actual
    return dict(contrasts=rows,acquired_but_lost_people_not_counted=True,fixed_audience_reference=True)


def unknown_checks():
    cases=[(False,name) for name in ('zstatecontent','g3','h6e','h6f','h6g')]+[(True,name) for name in ('hznm','hznn','zassessed','zweights')]
    for native,name in cases:
        doc=document(native=native);values=model(doc,native=native);values[name]=unknown
        try:evaluate(doc,values,PEOPLE if native else relay.DOMAIN,POINTS if native else relay.SCENES)
        except ValueError as error:assert 'Unknown' in str(error),(name,error)
        else:raise AssertionError(name)
    return dict(unknown_native_inputs_refused=len(cases))


def structure():
    old,new=load_catalog(ROOT,PARENT_BASIS),load_catalog(ROOT,BASIS)
    assert new.document['statements']==old.document['statements'] and len(new.document['statements'])==32
    assert new.document['declarations'][:-7]==old.document['declarations']
    for name,entry in old.entries.items():assert new.entries[name]==entry,name
    for index in (16,17,27,28,29,30,31):assert selection_binding(old,[index])==selection_binding(new,[index])
    return dict(new_definitions=7,new_primitives=0,existing_statements=32,seven_review_bindings_preserved=True,
        generic_characters=len((ROOT/LIBRARY).read_text(encoding='utf-8')),
        added_characters=len((ROOT/FULL).read_text(encoding='utf-8'))-len((ROOT/PARENT).read_text(encoding='utf-8')))


def build_report():
    outputs=build()
    for name,body in outputs.items():assert (ROOT/name).read_text(encoding='utf-8')==body,name
    for name in (FULL,CORE,LIBRARY):
        doc=parse((ROOT/name).read_text(encoding='utf-8'))
        for notation in ('compact','full'):
            text=format_graph(doc,notation);assert parse(text)==parse(transcribe(text,alphabet='v2'))==doc
    previous=json.loads((ROOT/'reports/reasoned-self-appraisal-v1.json').read_text(encoding='utf-8'))
    route=json.loads((ROOT/'reports/communicated-attitudes-v1.json').read_text(encoding='utf-8'))
    paths=set(load_catalog(ROOT,BASIS).source_sha256)|set(outputs)|set(previous['source_sha256'])|set(route['source_sha256'])|{
        'reports/reasoned-self-appraisal-v1.json','reports/communicated-attitudes-v1.json',
        'scripts/compose_transmitted_profiles.py','scripts/check_transmitted_profiles.py',
        'tests/test_transmitted_profiles.py','docs/transmitted-profiles-v1.md'}
    for record in (previous,route):
        for path,sha in record['source_sha256'].items():assert digest((ROOT/path).read_bytes())==sha,path
    alignment=deepcopy(previous['alignment']);alignment.update(definitions=list(MEANINGS),status='partial_assessed_disposition_and_transmission',
        remaining=['source-appropriate opportunities, criteria and psychological disposition','surrounding social scope and future author-attributed claim'])
    return dict(status='assessed_disposition_causal_receipt_and_retention_partial_reading',document=FULL,
        generic=generic_checks(),routes=route_checks(),native=native_checks(),collective=collective_checks(),
        unknowns=unknown_checks(),quotation=quotation_checks(),structure=structure(),roundtrips=True,alignment=alignment,new_source_assertions=0,
        verified_full_units={'kant-1784':0,'einstein-1905':0},active_review_index_unchanged='data/semantic-review-index-v22.json',
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})


def main():
    cli=argparse.ArgumentParser();cli.add_argument('--verify-only',action='store_true');args=cli.parse_args();report=build_report()
    if args.verify_only:assert json.loads(REPORT.read_text(encoding='utf-8'))==report
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:stream.write(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print('Response profiles, causal receipt and retained recipient scope checked',flush=True)


if __name__=='__main__':main()
