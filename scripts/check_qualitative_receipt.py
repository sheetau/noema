"""Execute native appraisal, causal acquisition and retention of one description."""
import argparse
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog,_references
from noema.semantic_reviews import digest,selection_binding
from noema.script import transcribe
from scripts import check_transmitted_profiles as profiles
from scripts import check_qualitative_thinkers as thinkers
from scripts.compose_subject_bound_departure import closure
from scripts.compose_qualitative_thinkers import PROVIDERS
from scripts.compose_qualitative_receipt import ROOT,PARENT,PARENT_BASIS,FULL,CORE,LIBRARY,BASIS,build

REPORT=ROOT/'reports/qualitative-receipt-v1.json'
STATE='k hzr2[r[k zcriterion[]] r[k zsubject[]] r[k zsource[]] r[k zrole[]] r[p zcases] r[p zpreferred]]'
UNKNOWN=profiles.unknown


def generic_checks():
    doc=parse((ROOT/LIBRARY).read_text(encoding='utf-8')+'''
r zperson[] a.r zanchor[] d.r zrespond[a d] c.r zcases[a d d] c.r zpreferred[a d d d] c.
d zresponse[person a] e[b scene[k zrespond[v person v scene]]].
q[t[c[s[k hzq7[r[p zresponse] r[p zcases] r[p zpreferred]]]][k zperson[]]][k zanchor[]]].
''')
    points=('actual','normal','exception');count=0
    def model(normal=True,exception=False,ranked=True,wrong=''):
        return dict(zperson=lambda:'person',zanchor=lambda:'actual',
            zrespond=lambda p,s:p=='person' and (s=='normal' and normal or s=='exception' and exception),
            zcases=lambda p,a,s:p==('other' if wrong=='person' else 'person') and a==('normal' if wrong=='anchor' else 'actual') and s in ('normal','exception'),
            zpreferred=lambda p,a,x,y:ranked and p=='person' and a=='actual' and (x,y)==('normal','exception'))
    for normal,exception,ranked in product((False,True),repeat=3):
        actual=profiles.evaluate(doc,model(normal,exception,ranked),('person','other'),points)
        assert actual==[normal and (ranked or exception)];count+=1
    for wrong in ('person','anchor'):assert profiles.evaluate(doc,model(wrong=wrong),('person','other'),points)==[False]
    for key in ('zrespond','zcases','zpreferred'):
        values=model();values[key]=UNKNOWN
        try:profiles.evaluate(doc,values,('person','other'),points)
        except ValueError as error:assert 'Unknown' in str(error)
        else:raise AssertionError(key)
    return dict(response_and_preference_combinations=count,same_person_and_anchor_required=True,
        unknown_inputs_refused=3,current_response_not_required=True,all_checks_eager=True)


@lru_cache(maxsize=5)
def document(kind='retained'):
    doc=parse((ROOT/CORE).read_text(encoding='utf-8'))
    text=profiles.relay.FIXTURE+profiles.ADDITIONS+'r zpreferred[a d d d] c.r zotherpreferred[a d d d] c.'
    args='k zfirst[] k zrest[] k zorigin[] k ztarget[] k zsubject[] r[p zmessage] '+STATE+' k zprocess[] k zstart[] k zend[] k zanchor[] p zsender p zrecipient p zactivity p zpoint'
    if kind in ('route','retained'):query='k '+('hzoa' if kind=='route' else 'hzob')+'['+args+']'
    elif kind=='profile':query='t[c[s['+STATE+']][k ztarget[]]][k zanchor[]]'
    else:
        assert kind=='episode';query='t[c[s[k hznv[r[k zcriterion[]] r[k zsubject[]] r[k zsource[]] r[k zrole[]]]]][k ztarget[]]][k zanchor[]]'
    return parse(format_graph(doc,'compact')+text+'q['+query+'].')


def described_state(variant='baseline'):
    response=profiles.appraisal.profile_syntax('zothercriterion' if variant=='wrong_causal_property' else 'zcriterion')
    preference='zotherpreferred' if variant=='wrong_causal_preference' else 'zpreferred'
    return dict(kind='apply',function=dict(kind='function_ref',symbol='hzq6'),arguments=[response,
        dict(kind='function_ref',symbol='zcases'),dict(kind='function_ref',symbol=preference)])


def model(doc,variant='baseline',length=2,seen=None):
    values=profiles.model(doc,variant,native=True,length=length)
    # Fixture assumptions specify an initial and a later qualitative state. They
    # are not a production rule for choosing successful normal cases.
    def cases(person,anchor,scene):
        acquired=values['zstatecontent'](person,anchor)
        return scene in (('trialgood' if acquired else 'trialbad'),'exception')
    values.update(zcases=cases,zpreferred=lambda p,a,x,y:x in ('trialgood','trialbad') and y=='exception')
    for key in ('zpoints','zassessed','zweights','zthreshold'):values[key]=UNKNOWN
    times={'stepone':'first','steptwo':'second'};recipients={'stepone':'relay','steptwo':'reader'};senders={'stepone':'sender','steptwo':'relay'}
    end='first' if length==1 else 'second';target='relay' if length==1 else 'reader'
    def caused(act,person,description,point):
        code=json.loads(description.syntax)
        if seen is not None:seen.append((act,person,code,point))
        if code!=described_state(variant) or variant=='no_cause':return False
        if variant=='first_step_cause':return (act,person,point)==('stepone',target,end)
        if variant=='unrelated_cause':return (act,person,point)==('topic',target,end)
        return act in times and (person,point)==(senders[act] if variant=='wrong_causal_person' else recipients[act],times[act])
    values['g3']=caused
    return values


def response_checks():
    doc=deepcopy(document('profile'));doc['statements']+=document('episode')['statements']
    rows={}
    for variant in ('baseline','no_appraisal','no_assent','different_support','different_claim','split_responses'):
        actual=profiles.evaluate(doc,model(doc,variant))
        assert actual==([True,False] if variant=='baseline' else [False,False]),(variant,actual);rows[variant]=actual
    return dict(native_appraisal_and_assent=rows,full_existing_judgment_definitions_executed=True,
        both_responses_required_in_same_scene=True,norm_truth_and_task_execution_not_evaluated=True)


def route_checks():
    doc=document();rows={}
    for variant in ('baseline','missing_receipt','not_understood','no_acquisition','already_accepted','no_cause',
        'wrong_causal_property','wrong_causal_preference','wrong_causal_person','first_step_cause','unrelated_cause','lost_after'):
        seen=[];actual=profiles.evaluate(doc,model(doc,variant,seen=seen))
        assert actual==[variant=='baseline'],(variant,actual);rows[variant]=actual
        if variant=='baseline':assert any(code==described_state() for act,p,code,s in seen)
    # The alternate cause is positive for another well-typed state, rather than
    # merely removing all causal facts from the fixture.
    alternate=STATE.replace('r[p zpreferred]','r[p zotherpreferred]')
    contrasted=parse(format_graph(doc,'compact')+'q[k g3[k zlastact[] k ztarget[] '+alternate+' k zend[]]].')
    alternate_result=profiles.evaluate(contrasted,model(contrasted,'wrong_causal_preference'))
    assert alternate_result==[False,True],alternate_result
    lapse={}
    for kind in ('route','retained'):
        selected=document(kind);actual=profiles.evaluate(selected,model(selected,'lost_then_regained',length=1))
        assert actual==[kind=='route'];lapse[kind]=actual
    for key in ('hznm','hznn','zpreferred','g3','h6g'):
        values=model(doc);values[key]=UNKNOWN
        try:profiles.evaluate(doc,values)
        except ValueError as error:assert 'Unknown' in str(error)
        else:raise AssertionError(key)
    return dict(native_transmission_contrasts=rows,same_description_used_for_cause_and_state=True,
        valid_alternative_state_caused_but_requested_state_not_acquired=alternate_result,
        intermediate_loss_not_hidden_by_recovery=lapse,unknown_inputs_refused=5,all_checks_eager=True)


def attribution_checks():
    doc=parse((ROOT/CORE).read_text(encoding='utf-8'));old=thinkers.native_document()
    existing={d['name']:d for d in doc['declarations']}
    for d in old['declarations']:
        if d['name'] in existing:assert d==existing[d['name']]
        else:doc['declarations'].append(deepcopy(d))
    # Names of the recipient-state metadata already come from the prior fixture.
    assert all(n in {d['name'] for d in doc['declarations']} for n in ('zcriterion','zsubject','zsource','zrole','zcases','zpreferred'))
    doc=parse(format_graph(doc,'compact')+'r zresponsepreferred[a d d d] c.')
    recipient_state=STATE.replace('r[p zpreferred]','r[p zresponsepreferred]')
    values,_=thinkers.prior.conditional.closed.arguments();values.update(state=recipient_state,thinkpreferred='p zpreferred',
        members='i[person a point d][k zbranchmembers[v branch v person v point]]')
    supplied=' '.join('i[branch d]['+values[n]+']' for n,t in PROVIDERS)
    frame='r b[k rqt6['+thinkers.prior.attributed.previous.prior.CONDITION_ARGS+' '+supplied+']]'
    doc=parse(format_graph(doc,'compact')+'q[k hzpy['+frame+' r[k zgoverned[]] r[p zappointed] r[p zguardian]]].')
    rows={}
    for reported,backgrounded in product((False,True),repeat=2):
        seen=[];model=thinkers.prior.attributed.previous.unknown_values(doc)
        model.update(hzp5=lambda:'person',wa=lambda:'authority',hzpz=lambda:'person',hzq2=lambda:'authority',hzp3=lambda:'outside')
        model.update(thinkers.prior.attributed.relation_values(reported,backgrounded,seen))
        actual=thinkers.prior.attributed.evaluate(doc,model);assert actual==[reported and backgrounded]
        assert {'rqt6','hzr2','zcases','zpreferred','zresponsepreferred'}<=_references(seen[0][3]);assert seen[0][3]==seen[1][3]
        assert {'hzr2','rqts','hzpt'}<=_references(seen[1][4]);rows[str((reported,backgrounded))]=actual
    return dict(closed_qualitative_state_in_shared_frame=rows,world_and_norm_truth_not_executed=True,
        sender_and_recipient_preference_conditions_distinct=True,
        unrestricted_collective_dissemination_truth_not_claimed=True)


def structure():
    old,new=load_catalog(ROOT,PARENT_BASIS),load_catalog(ROOT,BASIS)
    assert new.document['declarations'][:-3]==old.document['declarations']
    assert new.document['statements']==old.document['statements'] and len(new.document['statements'])==34
    for name,entry in old.entries.items():assert new.entries[name]==entry
    for index in (16,17,27,28,29,30,31):assert selection_binding(old,[index])==selection_binding(new,[index])
    names={d['name'] for d in closure(new.document,['hzr2'])}
    assert {'hznv','hznu','rqt4'}<=names and not names&{'hznw','hznx','hzny','rqa','rqb','rd4','rd5'}
    return dict(new_compositions=3,new_primitives=0,qualitative_state_has_no_scoring_dependency=True,
        original_acquisition_causality_and_retention_unchanged=True,existing_statements=34,seven_review_bindings_preserved=True,
        added_characters=len((ROOT/FULL).read_text(encoding='utf-8'))-len((ROOT/PARENT).read_text(encoding='utf-8')))


def build_report():
    outputs=build()
    for p,body in outputs.items():assert (ROOT/p).read_text(encoding='utf-8')==body
    for p in (FULL,CORE,LIBRARY):
        doc=parse((ROOT/p).read_text(encoding='utf-8'))
        for notation in ('compact','full'):
            text=format_graph(doc,notation);assert parse(text)==parse(transcribe(text,alphabet='v2'))==doc
    previous=json.loads((ROOT/'reports/qualitative-thinkers-v1.json').read_text(encoding='utf-8'))
    for p,sha in previous['source_sha256'].items():assert digest((ROOT/p).read_bytes())==sha
    paths=set(outputs)|set(load_catalog(ROOT,BASIS).source_sha256)|set(previous['source_sha256'])|{
        'reports/qualitative-thinkers-v1.json','scripts/compose_qualitative_receipt.py','scripts/check_qualitative_receipt.py',
        'tests/test_qualitative_receipt.py','docs/qualitative-receipt-v1.md'}
    results={}
    for name,fn in [('generic',generic_checks),('responses',response_checks),('routes',route_checks),('attribution',attribution_checks),('structure',structure)]:
        results[name]=fn();print(name+' checked',flush=True)
    source=thinkers.prior.attributed.previous.source_checks()
    unit=next(u for u in json.loads((ROOT/'artifacts/written-units-v1/kant-1784.json').read_text(encoding='utf-8'))['units'] if u['id']==source['source_unit'])
    return dict(status='qualitative_state_acquired_and_retained_using_same_description',document=FULL,**results,roundtrips=True,
        new_source_assertions=0,new_covered_characters=0,
        alignment=dict(unit=unit['id'],unit_sha256=unit['text_sha256'],start=333,end=421,source=unit['text'][333:421],
            definitions=['hzr2'],status='partial_qualitative_acquired_disposition',full_semantic_equivalence=False),
        verified_full_units={'kant-1784':0,'einstein-1905':0},active_review_index_unchanged='data/semantic-review-index-v22.json',
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})


def main():
    cli=argparse.ArgumentParser();cli.add_argument('--verify-only',action='store_true');args=cli.parse_args();result=build_report()
    if args.verify_only:assert json.loads(REPORT.read_text(encoding='utf-8'))==result
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:stream.write(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print('Qualitative response receipt and retention checked',flush=True)


if __name__=='__main__':main()
