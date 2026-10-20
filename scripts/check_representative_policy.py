"""Check all representative tasks, extra utterances and the same appointment."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.constructed_semantics import Content
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,validate_hashes
from noema.script import transcribe
from scripts.compose_representative_policy import ROOT,LIBRARY,BASIS,NAMES,MEANINGS,parents,build,closure
from scripts.check_teaching_policy import EXTRA_LOCAL,SMALL,TIMES,two_messages,period_model as original_period_model,base
from scripts.check_ranked_appointment import model as appointment_model,SCENES as PAST_SCENES
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown,symbol

DOC='docs/representative-policy-v1.md'
REPORT='reports/representative-policy-v1.json'
PRIOR=('reports/teaching-policy-v1.json','reports/representative-teaching-v1.json','reports/ranked-appointment-v1.json')
BOUNDARIES=('r355','r374','r357','r36a','r373')


def read(path):return json.loads((ROOT/path).read_text(encoding='utf-8'))
@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)


@lru_cache(None)
def fixture(target,boundaries=(),finite=False,bindings=()):
    doc=deepcopy(catalog().document)
    for d in doc['declarations']:
        if d['name'] in boundaries:
            d.update(kind='primitive',parameters=[p['sort'] for p in d['parameters']]);d.pop('body')
    doc.update(declarations=closure(doc,[target]),statements=[])
    doc['declarations']=parse('p:'+EXTRA_LOCAL)['declarations']+doc['declarations']
    args=' '.join('k z'+n+'[]' for n in NAMES)+' k zref[]'
    if target in ('r375','r376'):args+=' k zoccasion[]'
    if target=='r4a':args='l[a]['+' '.join('k z'+n+'[]' for n in bindings)+'] k zref[]'
    doc=parse(format_graph(doc,'compact')+'q[t[k '+target+'['+args+']][k zpoint[]]].')
    return parse(format_graph(two_messages(doc),'compact')) if finite else doc


def period_model(doc,variant='baseline'):
    inherited=variant if variant in ('baseline','different_method','no_execution','outside_window','extra_bad_message','extra_bad_activity',
        'extra_bad_later','invalid_task','empty_window','gapped_window') else 'baseline'
    v=original_period_model(doc,inherited);old_actual=v['r357'];old_complete=v['r356']
    fixed=(*NAMES,'reference','occasion')
    def actual(*args):
        values=list(old_actual(*args).values)
        if variant in ('extra_own_voice','extra_wrong_principal','extra_later_own_voice') and args[:-2]==fixed and args[-2]=='secondactivity' and symbol(args[-1])=='zbadmessage':
            values[TIMES.index('two' if variant=='extra_later_own_voice' else 'one')]=True
        return Content(TIMES,tuple(values))
    def representation(*args):
        values=list(actual(*args).values)
        if variant=='no_representative_delivery':values=[False]*len(TIMES)
        if variant.startswith('extra_') and args[-2]=='secondactivity' and symbol(args[-1])=='zbadmessage':values=[False]*len(TIMES)
        return Content(TIMES,tuple(values))
    def complete(*args):
        return Content(TIMES,tuple(a and b for a,b in zip(old_complete(*args).values,representation(*args).values)))
    v.update(r357=actual,r373=representation,r374=complete)
    if variant in ('extra_own_voice','extra_wrong_principal','extra_later_own_voice'):
        # Extra teaching meets the prescription; only representative voice fails.
        v['r36a']=lambda *args:Content(TIMES,(args[:-2]==(*NAMES,'reference'),)*len(TIMES))
    return v


@lru_cache(None)
def period_checks():
    doc=fixture('r376',BOUNDARIES,True);rows={}
    variants=('baseline','different_method','no_execution','outside_window','extra_bad_message','extra_bad_activity','extra_bad_later',
        'no_representative_delivery','extra_own_voice','extra_wrong_principal','extra_later_own_voice','invalid_task','empty_window','gapped_window')
    for variant in variants:
        actual=evaluate(doc,period_model(doc,variant),SMALL,TIMES,True)
        assert actual==[variant in ('baseline','different_method')],(variant,actual);rows[variant]=actual[0]
    complete=fixture('r376',BOUNDARIES)
    try:evaluate(complete,period_model(complete),SMALL,TIMES,True)
    except ValueError as error:assert 'Cannot finitely quantify the description domain' in str(error);refusal=str(error)
    else:raise AssertionError('Production policy reduced the message domain')
    for n in ('h7q','h7r','ic','r374','r373','r36a','r357'):
        v=period_model(doc);v[n]=unknown
        try:evaluate(doc,v,SMALL,TIMES,True)
        except ValueError as error:assert 'Unknown' in str(error),str(error)
        else:raise AssertionError(n)
    return dict(contrasts=rows,all_period_expositions_must_conform_and_represent=True,at_least_one_full_delivery_required=True,
        no_all_method_or_all_time_execution_requirement=True,full_domain_refused=refusal,
        boundaries=list(BOUNDARIES),bounded_message_diagnostic_only=['zmessage','zbadmessage'],boundary_evidence=list(PRIOR))


@lru_cache(None)
def coverage_checks():
    doc=fixture('r377',('r35t','r376'));rows={}
    for variant in ('baseline','no_tasks','unassigned_member','failed_second_task','shared_recipient'):
        v=base(doc,'last');v['r35t']=lambda *args:args==(*NAMES,'reference')
        v['h246n']=lambda *args:variant!='no_tasks' and args[:4]==('person','role','church','subject') and args[4] in ('occasion','secondoccasion') and args[5]=='reference'
        v['h6t']=lambda group,recipient,ref:ref=='reference' and (group,recipient) in (('students','learner'),('members','member'))
        v['h246o']=lambda occasion,recipient,ref:ref=='reference' and ((occasion,recipient)==('occasion','learner') or
            variant!='unassigned_member' and (occasion,recipient)==('secondoccasion','member') or variant=='shared_recipient' and (occasion,recipient)==('secondoccasion','learner'))
        v['r376']=lambda *args:Content(TIMES,tuple(args[:-1]==(*NAMES,'reference') and not(variant=='failed_second_task' and args[-1]=='secondoccasion') for _ in TIMES))
        actual=evaluate(doc,v,SMALL,TIMES,True)
        assert actual==[variant in ('baseline','shared_recipient')],(variant,actual);rows[variant]=actual[0]
    return dict(contrasts=rows,all_tasks_and_all_original_recipients_covered=True,boundaries=['r35t','r376'])


@lru_cache(None)
def binding_checks():
    for position in range(9):
        names=tuple('person' if i==position else 'other' for i in range(9))
        expected=tuple('x' if i==position else 'y' for i in range(9))+('reference',)
        doc=fixture('r4a',('r377',),bindings=names);v=base(doc,'last')
        v.update(zperson=lambda:'x',zother=lambda:'y',r377=lambda *args:Content(TIMES,(args==expected,)*len(TIMES)))
        assert evaluate(doc,v,('x','y'),TIMES,True)==[True],position
    for count in (0,8,10):
        doc=fixture('r4a',('r377',),bindings=('person',)*count);v=base(doc,'last')
        v.update(zperson=lambda:'x',r377=lambda *args:Content(TIMES,(True,)*len(TIMES)))
        assert evaluate(doc,v,('x','y'),TIMES,True)==[False],count
    return dict(independent_positions=list(NAMES),wrong_lengths_rejected=[0,8,10],boundary='r377')


def appointment_values(doc,variant):
    v=appointment_model(doc,variant);v.update({n:f for n,f in base(doc,'now').items() if f is not unknown})
    past_cf=v['cf']
    v['cf']=lambda p,r,at:(variant!='missing_past_delegation' and past_cf(p,r,at)) or (variant!='missing_current_delegation' and (p,r,at)==('person','role','now'))
    v['aa']=lambda p:p=='person'
    v['h246k']=lambda p,c,r,at:variant!='missing_current_service' and (p,c,r,at)==('person','church','role','now')
    v['h247n']=lambda p,r,c,s,at:variant!='missing_current_business' and (p,r,c,s,at)==('person','role','church','subject','now')
    when='now' if variant=='present_only' else 'future' if variant=='future_only' else 'past'
    def terms(event,code,bindings,ref,sign,at):
        target='r36e' if variant=='other_target' else 'r4a'
        values=tuple('other' if variant=='binding_'+n else n for n in NAMES)
        return variant!='absent_terms' and (event,symbol(code),code.rank,tuple(bindings.items),ref,sign,at)==(
            'other' if variant=='split_event' else 'event',target,0 if variant=='wrong_rank' else 1,values,
            'past' if variant=='other_reference' else 'reference',variant!='opposite_sign','middle' if variant=='split_time' else when)
    v['h246m']=terms
    return v


@lru_cache(None)
def appointment_checks():
    rows={}
    variants=('baseline','absent_terms','other_target','wrong_rank','other_reference','opposite_sign','split_event','split_time',
        'present_only','future_only','missing_past_delegation','missing_current_delegation','missing_current_service','missing_current_business',
        *('binding_'+n for n in NAMES))
    for variant in variants:
        actual=[]
        for target in ('r4b','r4c'):
            doc=fixture(target);v=appointment_values(doc,variant)
            # Actual representative teaching and all policy scope remain unknown.
            assert v['h247o'] is unknown and v['h246n'] is unknown and v['f2'] is unknown
            actual+=evaluate(doc,v,SMALL,PAST_SCENES,True)
        expected=[True,True] if variant=='baseline' else [True,False] if variant.startswith('missing_current_') else [False,False]
        assert actual==expected,(variant,actual);rows[variant]=actual
    return dict(contrasts=rows,same_event_past_time_target_nine_bindings_reference_and_sign=True,
        past_appointment_does_not_establish_current_office=True,quoted_policy_and_delivery_not_executed=True)


@lru_cache(None)
def structure_checks():
    new=catalog();old={n:e for p in parents() for n,e in p.entries.items()}
    assert not new.document['statements']
    for n,e in new.entries.items():
        if n not in MEANINGS:assert e['declaration']==old[n]['declaration'] and e['meaning_ja']==old[n]['meaning_ja'],n
    for path,body in build().items():assert (ROOT/path).read_text(encoding='utf-8')==body,path
    validate_hashes(ROOT,read(BASIS)['import_source_sha256'])
    for path in PRIOR:validate_hashes(ROOT,read(path)['source_sha256'])
    for notation in ('compact','full'):
        text=format_graph(new.document,notation);assert parse(text)==parse(transcribe(text,alphabet='v2'))==new.document
    doc=parse(format_graph(new.document,'compact')+'q[e[r b[p r4a]][r b[p r4a]]].')
    assert evaluate(doc,{d['name']:unknown for d in doc['declarations'] if d['kind']=='primitive'},SMALL,TIMES,True)==[True]
    try:parse(format_graph(new.document,'compact')+'q[e[r[p r4a]][r[p r4a]]].')
    except ValueError as error:rank_error=str(error)
    else:raise AssertionError('Insufficient quote rank accepted')
    return dict(new_primitives=0,new_definitions=len(MEANINGS),inherited_meanings_preserved=True,roundtrips=True,
        policy_quote_without_execution=True,insufficient_quote_rank_rejected=rank_error,new_semantic_reviews=0)


def prepare():
    from scripts.audit_opening_scope import write_exact
    for path,body in build().items():write_exact(ROOT/path,body)


def build_report():
    results={}
    for name,fn in [('period',period_checks),('coverage',coverage_checks),('bindings',binding_checks),('appointment',appointment_checks),('structure',structure_checks)]:
        results[name]=fn();print(name+' checked',flush=True)
    paths=set(build())|set().union(*(set(p.source_sha256) for p in parents()))|{DOC,*PRIOR,
        'scripts/compose_representative_policy.py','scripts/check_representative_policy.py','tests/test_representative_policy.py',
        'scripts/check_teaching_policy.py','scripts/check_ranked_appointment.py','scripts/compose_confessional_teaching.py',
        'scripts/compose_grounded_step.py','scripts/compose_qualitative_influence.py','scripts/check_pastoral_roles.py','scripts/check_motive_causes.py'}
    return dict(status='complete_representative_policy_and_current_appointment',document=LIBRARY,**results,
        whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
