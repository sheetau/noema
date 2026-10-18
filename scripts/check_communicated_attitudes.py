"""Check receipt, attitude acquisition, causal identity and the final relay."""
import argparse
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse,format_graph
from noema.constructed_semantics import Content,SequenceValue,evaluate_document
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.check_described_explanations import symbol
from scripts.compose_communicated_attitudes import ROOT,PARENT,PARENT_BASIS,FULL,CORE,LIBRARY,BASIS,MEANINGS,build

REPORT=ROOT/'reports/communicated-attitudes-v1.json'
DOMAIN=('sender','relay','reader','stepone','steptwo','process','topic','audience')
SCENES=('before','first','second','now')


def unknown(*args):raise ValueError('Unknown interpretation is required')


def evaluate(doc,model,people=DOMAIN,points=SCENES,memoize=False):
    model={d['name']:model[d['name']] for d in doc['declarations'] if d['kind']=='primitive'}
    return [r['value'] for r in evaluate_document(doc,individuals=people,situations=points,primitives=model,
        max_steps=8000000,memoize_definitions=memoize,memoize_expressions=memoize)]


def generic_checks():
    doc=parse((ROOT/LIBRARY).read_text(encoding='utf-8')+'''
r zhistory[d] c.r zbefore[d d] c.r ztarget[] a.r zprocess[] a.r zpart[] a.r zstart[] d.r zend[] d.
r zstate[a] e.r zother[a] e.r zchanges[a d d] c.r zaffected[a a d d] c.r zoccurs[a d] c.
r zpartof[a a d] c.r zproduces[a a i[h[a] e] d] c.
q[k rqte[p zhistory p zbefore k ztarget[] k zprocess[] k zpart[] k zstart[] k zend[]
r[p zstate] p zchanges p zaffected p zoccurs p zpartof p zproduces]].
''')
    points=('before','after');people=('target','process','part');count=0
    for flags in product((False,True),repeat=8):
        prior,after,changes,affected,process,part,partof,produces=flags
        model=dict(zhistory=lambda p:True,zbefore=lambda a,b:points.index(a)<points.index(b),
            ztarget=lambda:'target',zprocess=lambda:'process',zpart=lambda:'part',zstart=lambda:'before',zend=lambda:'after',
            zstate=lambda target:Content(points,(prior,after)),zother=unknown,
            zchanges=lambda p,a,b:changes and (p,a,b)==('process','before','after'),
            zaffected=lambda t,p,a,b:affected and (t,p,a,b)==('target','process','before','after'),
            zoccurs=lambda p,end:end=='after' and (process if p=='process' else part if p=='part' else False),
            zpartof=lambda a,p,end:partof and (a,p,end)==('part','process','after'),
            zproduces=lambda a,t,d,end:produces and (a,t,symbol(d),end)==('part','target','zstate','after'))
        assert evaluate(doc,model,people,points)==[not prior and all(flags[1:])],flags
        count+=1
    # The state denotation cannot be supplied independently of its description.
    model['zstate']=lambda target:Content(points,(False,True))
    assert evaluate(doc,model,people,points)==[True]
    model['zproduces']=lambda a,t,d,end:symbol(d)=='zother'
    assert evaluate(doc,model,people,points)==[False]
    for name in ('zstate','zchanges','zaffected','zproduces'):
        current=dict(model);current[name]=unknown
        try:evaluate(doc,current,people,points)
        except ValueError as error:assert 'Unknown' in str(error)
        else:raise AssertionError(name)
    return dict(state_and_causal_combinations=count,mismatched_causal_description_refused=True,
        state_function_derived_from_the_same_description=True,unknown_inputs_refused=4,uncached=True)


FIXTURE='''
r zorigin[] a.r ztarget[] a.r zlastsender[] a.r zlastact[] a.r zsubject[] a.r zprocess[] a.
r zfirst[] a.r zrest[] j[a].r zstart[] d.r zend[] d.r zanchor[] d.r zreference[] d.r zaudience[] a.
r zsender[a] a.r zrecipient[a] a.r zactivity[a] a.r zpoint[a] d.
r zfirsts[a] a.r ztails[a] j[a].r zprocesses[a] a.r zstarts[a] d.r zends[a] d.
r zcontent[a d] c.r zstatecontent[a d] c.r zanyextent[h[a] c h[a] c] c.
d zmessage[subject a] f[j s[b scene[k zcontent[v subject v scene]]]].
d zothermessage[subject a] f[j q[b scene[k zcontent[v subject v scene]]]].
d zproperty[person a] e[b scene[k zstatecontent[v person v scene]]].
d zotherproperty[person a] e[b scene[k zstatecontent[v person v scene]]].
'''


@lru_cache(maxsize=8)
def document(kind='route',property_name='zproperty',extent='rqsx'):
    text=(ROOT/CORE).read_text(encoding='utf-8')+FIXTURE
    if kind=='direct':
        query='k hznj[k zlastsender[] k ztarget[] k zlastact[] k zsubject[] r[p zmessage] r[p '+property_name+'] k zprocess[] k zstart[] k zend[] k zanchor[]]'
    elif kind=='route':
        query='k hznk[k zfirst[] k zrest[] k zorigin[] k ztarget[] k zsubject[] r[p zmessage] r[p '+property_name+'] k zprocess[] k zstart[] k zend[] k zanchor[] p zsender p zrecipient p zactivity p zpoint]'
    else:
        assert kind=='collective'
        query='k hznl[k zaudience[] k zreference[] k zorigin[] k zsubject[] r[p zmessage] r[p '+property_name+'] k zanchor[] p zfirsts p ztails p zprocesses p zstarts p zends p zsender p zrecipient p zactivity p zpoint p '+extent+']'
    return parse(text+'q['+query+'].')


def attitude_syntax(property_name):
    return dict(kind='apply',function=dict(kind='function_ref',symbol='hzni'),
        arguments=[dict(kind='quote',body=dict(kind='function_ref',symbol=property_name))])


def sequence(items):return SequenceValue(tuple(items),'"individual"')


def model(doc,variant='baseline',length=2,property_name='zproperty',seen=None):
    values={d['name']:unknown for d in doc['declarations'] if d['kind']=='primitive'}
    senders={'stepone':'sender','steptwo':'relay'};recipients={'stepone':'relay','steptwo':'reader'}
    times={'stepone':'first','steptwo':'second'}
    target='relay' if length==1 else 'reader';last='stepone' if length==1 else 'steptwo';end=times[last]
    if variant=='disconnected_relay':senders['steptwo']='sender'
    members={'reader'}
    if variant in ('both_acquire','one_of_two','lost_after'):members={'relay','reader'}
    if variant=='empty_audience':members=set()
    if variant=='nonhuman_audience':members.add('topic')
    def history(person,anchor,point):
        return person in ('sender','relay','reader') and anchor=='now' and not (
            variant=='missing_target_history' and person==target and point=='before' or
            variant=='missing_origin_history' and person=='sender' and point=='first')
    def before(a,b,anchor):return anchor=='now' and SCENES.index(a)<SCENES.index(b)
    def payload(act,recipient,subject,description,point):
        return act in times and (recipient,subject,symbol(description),point)==(recipients[act],
            'audience' if variant=='wrong_message_subject' and act==last else 'topic',
            'zothermessage' if variant=='wrong_message_force' and act==last else 'zmessage',times[act])
    def receipt(*args):return variant!='missing_receipt' and payload(*args)
    def understands(person,subject,description,point):
        return variant!='not_understood' and person in ('relay','reader') and (subject,symbol(description),point)==(
            'topic','zmessage','first' if person=='relay' else 'second')
    def accepts(person,description,point):
        if seen is not None:seen.add(('attitude',person,symbol(description),point))
        if symbol(description)!=property_name:return False
        if variant=='no_acquisition':return False
        if variant=='already_accepted' and person==target:return True
        if person==target:return SCENES.index(point)>=SCENES.index(end) and not (variant=='lost_after' and point=='now')
        return person=='relay' and variant in ('both_acquire','lost_after') and point!='before' and not (variant=='lost_after' and point=='now')
    def caused(act,person,description,point):
        expected=attitude_syntax('zotherproperty' if variant=='wrong_causal_property' else property_name)
        if seen is not None:seen.add(('cause',description.syntax))
        if json.loads(description.syntax)!=expected or variant=='no_cause':return False
        if variant=='first_step_cause':return (act,person,point)==('stepone',target,end)
        if variant=='unrelated_cause':return (act,person,point)==('topic',target,end)
        return act in times and (person,point)==(
            senders[act] if variant=='wrong_causal_person' else recipients[act],times[act])
    def affected(person,process,start,finish):
        return process=='process' and start=='before' and (person,finish) in (
            {('relay','second')} if variant=='wrong_affected_person' else {('relay','first'),('reader','second')})
    def audience(group,person,reference):
        if seen is not None:seen.add(('audience',reference))
        return group=='audience' and person in (members if reference=='before' else {'sender'})
    values.update(zorigin=lambda:'sender',ztarget=lambda:target,zlastsender=lambda:senders[last],zlastact=lambda:last,
        zsubject=lambda:'topic',zprocess=lambda:'process',zfirst=lambda:'stepone',zrest=lambda:sequence(()) if length==1 else sequence(('steptwo',)),
        zstart=lambda:'second' if variant=='late_start' else 'before',zend=lambda:end,
        zanchor=lambda:'first' if variant=='future_endpoint' else 'now',zreference=lambda:'before',zaudience=lambda:'audience',
        zsender=lambda step:senders.get(step,'sender'),zrecipient=lambda step:recipients.get(step,'reader'),
        zactivity=lambda step:step,zpoint=lambda step:times.get(step,'second'),
        zfirsts=lambda person:'stepone',ztails=lambda person:sequence(()) if person=='relay' else sequence(('steptwo',)),
        zprocesses=lambda person:'process',zstarts=lambda person:'before',zends=lambda person:'first' if person=='relay' else 'second',
        zanyextent=lambda members,changed:True,
        aa=lambda person:person in ('sender','relay','reader'),ia=history,ic=before,
        dg=lambda act,point:act=='process' and variant!='missing_process_occurrence' and point in ('first','second') or act in times and point==times[act],
        f3=lambda person,act,point:act in times and (person,point)==(senders[act],times[act]),f2=payload,h6e=receipt,
        h6f=lambda act,previous,person,subject,description,point:variant!='independent_message' and
            (act,previous,person,subject,symbol(description),point)==('steptwo','stepone','relay','topic','zmessage','second'),
        h6g=understands,id=accepts,
        ag=lambda process,start,finish:variant!='no_change' and process=='process' and start=='before' and finish in ('first','second'),
        la=affected,h6a=lambda act,process,point:process==('topic' if variant=='different_process_part' else 'process') and act in times and point==times[act],
        g3=caused,h6t=audience)
    return values


def native_checks():
    doc=document();rows={}
    variants=('baseline','missing_receipt','not_understood','no_acquisition','already_accepted','no_change',
        'no_cause','wrong_causal_property','wrong_causal_person','first_step_cause','unrelated_cause',
        'wrong_affected_person','different_process_part','missing_process_occurrence','wrong_message_subject',
        'wrong_message_force','independent_message','disconnected_relay','missing_target_history',
        'missing_origin_history','late_start','future_endpoint','lost_after')
    for variant in variants:
        actual=evaluate(doc,model(doc,variant),memoize=True)
        assert actual==[variant in ('baseline','lost_after')],(variant,actual)
        rows[variant]=actual
    for length in (1,2):
        for kind in ('direct','route'):
            item=document(kind);assert evaluate(item,model(item,length=length),memoize=True)==[True]
    assert evaluate(doc,model(doc))==[True]
    assert evaluate(doc,model(doc,'no_cause'))==[False]
    builtin=document(property_name='bb');seen=set()
    assert evaluate(builtin,model(builtin,property_name='bb',seen=seen),memoize=True)==[True]
    assert ('attitude','reader','bb','second') in seen
    assert all(json.loads(row[1])==attitude_syntax('bb') for row in seen if row[0]=='cause')
    return dict(route_contrasts=rows,direct_and_relay_lengths=[1,2],uncached_positive_and_negative_agree=True,
        native_understanding_use_attitude_checked=True,attitude_target_and_message_content_not_evaluated=True,
        causal_property_matches_constructed_attitude_syntax=True,intermediary_and_origin_acceptance_not_required=True,
        acquisition_does_not_require_later_persistence=True,source_definitions_not_replaced_or_lowered=True)


def collective_checks():
    rows={}
    for extent in ('zanyextent','rqsy','rqsx'):
        for variant in ('baseline','both_acquire','one_of_two','empty_audience','nonhuman_audience','lost_after'):
            doc=document('collective',extent=extent);seen=set()
            actual=evaluate(doc,model(doc,variant,seen=seen),memoize=True)
            expected=variant not in ('empty_audience','nonhuman_audience') and (
                extent=='zanyextent' or variant in ('both_acquire','lost_after') or extent=='rqsx' and variant=='baseline')
            assert actual==[expected],(extent,variant,actual)
            assert {row[1] for row in seen if row[0]=='audience'}=={'before'}
            rows[extent+':'+variant]=actual
    return dict(contrasts=rows,fixed_audience_reference=True,external_intermediary_allowed=True,
        separate_personal_process_endpoints_allowed=True)


def unknown_checks():
    doc=document()
    for name in ('id','g3','h6e','h6f','h6g'):
        values=model(doc);values[name]=unknown
        try:evaluate(doc,values,memoize=True)
        except ValueError as error:assert 'Unknown' in str(error)
        else:raise AssertionError(name)
    doc=document('collective');values=model(doc);values['h6t']=unknown
    try:evaluate(doc,values,memoize=True)
    except ValueError as error:assert 'Unknown' in str(error)
    else:raise AssertionError('h6t')
    return dict(unknown_native_inputs_refused=6)


def quotation_checks():
    for rank in (0,1):
        doc=deepcopy(document());body=doc['statements'][0]['body']
        quoted=dict(kind='quote',body=body,**({'rank':rank} if rank else {}))
        doc['statements'][0]['body']=dict(kind='disquote',description=quoted)
        if rank:
            doc=parse(format_graph(doc,'compact'))
            assert evaluate(doc,model(doc),memoize=True)==[True]
        else:
            try:parse(format_graph(doc,'compact'))
            except ValueError as error:assert 'strictly lower ranks' in str(error)
            else:raise AssertionError('Same-rank quotation was accepted')
    return dict(rank_one_quoted_claim_evaluable=True,same_rank_quotation_rejected_statically=True)


def structure():
    old,new=load_catalog(ROOT,PARENT_BASIS),load_catalog(ROOT,BASIS)
    assert new.document['statements']==old.document['statements'] and len(new.document['statements'])==32
    assert new.document['declarations'][:-5]==old.document['declarations']
    for name,entry in old.entries.items():assert new.entries[name]==entry,name
    for index in (16,17,27,28,29,30,31):assert selection_binding(old,[index])==selection_binding(new,[index])
    assert next(d for d in new.document['declarations'] if d['name']=='rqte')['parameters'][7]['sort']['kind']=='description'
    return dict(new_definitions=5,new_primitives=0,existing_statements=32,seven_review_bindings_preserved=True,
        generic_characters=len((ROOT/LIBRARY).read_text(encoding='utf-8')),
        added_characters=len((ROOT/FULL).read_text(encoding='utf-8'))-len((ROOT/PARENT).read_text(encoding='utf-8')))


def build_report():
    outputs=build()
    for name,body in outputs.items():assert (ROOT/name).read_text(encoding='utf-8')==body,name
    for name in (FULL,CORE,LIBRARY):
        doc=parse((ROOT/name).read_text(encoding='utf-8'))
        for notation in ('compact','full'):
            form=format_graph(doc,notation);assert parse(form)==parse(transcribe(form,alphabet='v2'))==doc
    catalog=load_catalog(ROOT,BASIS)
    previous=json.loads((ROOT/'reports/message-relays-v1.json').read_text(encoding='utf-8'))
    validate_hashes(ROOT,previous['source_sha256'])
    alignment=deepcopy(previous['alignment']);alignment.update(definitions=list(MEANINGS),remaining=[
        'reasoned self-appraisal and vocation of independent thought',
        'attitudes beyond favorable self-acceptance and their reinforcement',
        'future modality, surrounding audience and public enlightenment'])
    paths=set(catalog.source_sha256)|set(outputs)|set(previous['source_sha256'])|{
        'reports/message-relays-v1.json','scripts/compose_communicated_attitudes.py','scripts/check_communicated_attitudes.py',
        'tests/test_communicated_attitudes.py','docs/communicated-attitudes-v1.md',
        'scripts/compose_subject_bound_departure.py','scripts/check_described_explanations.py',
        'noema/constructed_semantics.py','noema/constructed.py','noema/constructed_discourse.py',
        'noema/script.py','noema/semantics.py','noema/meaning_catalog.py'}
    return dict(status='communicated_attitude_acquisition_partial_reading',document=FULL,
        generic=generic_checks(),native=native_checks(),collective=collective_checks(),unknowns=unknown_checks(),
        quotation=quotation_checks(),structure=structure(),roundtrips=True,alignment=alignment,new_source_assertions=0,
        verified_full_units={'kant-1784':0,'einstein-1905':0},active_review_index_unchanged='data/semantic-review-index-v22.json',
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})


def main():
    cli=argparse.ArgumentParser();cli.add_argument('--verify-only',action='store_true');args=cli.parse_args();report=build_report()
    if args.verify_only:assert json.loads(REPORT.read_text(encoding='utf-8'))==report
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:stream.write(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print('Received routes, described attitudes and exact causal targets checked')


if __name__=='__main__':main()
