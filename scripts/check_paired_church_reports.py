"""Check shared ranked report instances and their same official utterance."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,validate_hashes
from noema.script import transcribe
from scripts.compose_paired_church_reports import ROOT,LIBRARY,BASIS,PRIMITIVES,MEANINGS,parents,build
from scripts.check_institutional_teaching_grounds import EXTRA,model as content_model
from scripts.check_motive_causes import unknown
from scripts.check_pastoral_roles import evaluate

DOC='docs/paired-church-reports-v1.md'
REPORT='reports/paired-church-reports-v1.json'
PRIOR='reports/institutional-teaching-grounds-v1.json'
DOMAIN=('person','role','church','judgment','subject','utterance','first','second','other','r1','r2','r3')
SCENES=('now','other')
LOCAL='r zperson[] a.r zrole[] a.r zutterance[] a.r zotherchurch[] a.r zaudience[a] c.'
FIRST='c[p r4r][k zchurch[] r[p zmessage]]'
SECOND='c[p r4s][k zchurch[] k zjudgment[] r[p zmessage] p zreasons]'
FIRST_CODE='k r4t[r[k zchurch[]] r[p zmessage]]'
SECOND_CODE='k r4u[r[k zchurch[]] r[k zjudgment[]] r[p zmessage] r[p zreasons]]'


def read(path):return json.loads((ROOT/path).read_text(encoding='utf-8'))
@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)


@lru_cache(None)
def fixture(query=None,church_name='zchurch'):
    doc=deepcopy(catalog().document);doc['statements']=[]
    if query is None:query='q[t[k r4w[k zperson[] k zrole[] k zchurch[] k zsubject[] k zutterance[] r[k '+church_name+'[]] r[k zjudgment[]] r[p zmessage] r[p zreasons] p zaudience]][k zpoint[]]].'
    return parse(format_graph(doc,'compact')+EXTRA+LOCAL+query)


@lru_cache(None)
def expected():
    doc=fixture('q[e[r b['+FIRST+']][r b['+SECOND+']]].')
    return tuple(q['body'] for q in doc['statements'][0]['body']['arguments'])


def model(doc,variant='baseline'):
    v={d['name']:unknown for d in doc['declarations'] if d['kind']=='primitive'}
    v.update(zperson=lambda:'person',zrole=lambda:'role',zchurch=lambda:'church',zotherchurch=lambda:'other',
        zsubject=lambda:'subject',zutterance=lambda:'utterance',zpoint=lambda:'now',zjudgment=lambda:'judgment')
    v['zaudience']=lambda p:p in (() if variant=='empty_audience' else ('first','second'))
    v['aa']=lambda p:p in ('person','first','second') and not(variant=='nonperson_recipient' and p=='second')
    v['cf']=lambda p,r,at:variant!='no_office' and (p,r,at)==('person','role','now')
    v['h246k']=lambda p,c,r,at:variant!='wrong_service' and (p,c,r,at)==('person','church','role','now')
    v['h247n']=lambda p,r,c,s,at:variant!='no_business_assignment' and (p,r,c,s,at)==('person','role','church','subject','now')
    v['cb']=lambda p,a,r,at:variant!='private_activity' and (p,a,r,at)==('person','utterance','role','now')
    v['dg']=lambda a,at:variant!='no_event' and (a,at)==('utterance','now')
    v['f3']=lambda p,a,at:variant!='other_speaker' and (p,a,at)==('person','utterance','now')
    first,second=expected()
    def conveys(a,recipient,s,code,at):
        syntax=json.loads(code.syntax)
        return (a,s,at)==('utterance','subject','now') and code.rank==1 and syntax in (first,second) and not(
            variant=='missing_second' and syntax==second or variant=='missed_recipient' and recipient=='second' and syntax==second)
    v['h234g']=conveys
    def order(a,p,recipient,s,left,right,at):
        return variant!='no_order' and (a,p,s,at)==('utterance','person','subject','now') and left.rank==right.rank==1 and (
            json.loads(left.syntax),json.loads(right.syntax))==((second,first) if variant=='reversed' else (first,second))
    v['h247x']=order
    v['h247y']=lambda a,p,c,at:variant!='no_our_reference' and (a,p,c,at)==('utterance',
        'other' if variant=='authors_we' else 'person','other' if variant=='other_our_church' else 'church','now')
    return v


def run(doc,v):return evaluate(doc,v,DOMAIN,SCENES,True)


@lru_cache(None)
def native_checks():
    doc=fixture();rows={}
    for variant in ('baseline','empty_audience','nonperson_recipient','no_office','wrong_service','no_business_assignment',
        'private_activity','no_event','other_speaker','missing_second','missed_recipient','no_order','reversed',
        'no_our_reference','authors_we','other_our_church'):
        result=run(doc,model(doc,variant));assert result==[variant=='baseline'],(variant,result);rows[variant]=result[0]
    other=fixture(church_name='zotherchurch');v=model(other)
    # Even permissive presentation relations cannot hide a different source church.
    v.update(h234g=lambda *a:True,h247x=lambda *a:True,h247y=lambda *a:True)
    assert run(other,v)==[False]
    for n in ('h234g','h247x','h247y','dg','f3','h247n'):
        v=model(doc);v[n]=unknown
        try:run(doc,v)
        except ValueError as error:assert 'Unknown' in str(error),str(error)
        else:raise AssertionError(n)
    return dict(contrasts=rows,source_church_matches_both_report_references=True,all_specified_recipients_receive_both=True,
        unknown_relations_refused=True,reported_facts_and_inner_truth_not_executed=True)


@lru_cache(None)
def construction_checks():
    doc=fixture('q[e['+FIRST_CODE+'][r b['+FIRST+']]].q[e['+SECOND_CODE+'][r b['+SECOND+']]].')
    v={d['name']:unknown for d in doc['declarations'] if d['kind']=='primitive'}
    assert run(doc,v)==[True,True]
    # Building a report requires no referent, judgment, reason or truth evaluation.
    rows={}
    replacements={'church':'r[k zotherchurch[]]','judgment':'r[k zsubject[]]',
        'message':'r[p zalias]','force':'r[p zquestion]','reasons':'r[p zaudience]'}
    for name,value in replacements.items():
        args=['r[k zchurch[]]','r[k zjudgment[]]','r[p zmessage]','r[p zreasons]']
        args[{'church':0,'judgment':1,'message':2,'force':2,'reasons':3}[name]]=value
        d=fixture('q[e[k r4u['+' '.join(args)+']][r b['+SECOND+']]].')
        assert run(d,v)==[False],name;rows[name]=False
    return dict(exact_application_descriptions=True,construction_does_not_evaluate_any_argument=True,
        distinct_description_inputs_preserved=rows,inner_message_is_quoted_as_value=True)


@lru_cache(None)
def content_checks():
    queries=''.join('q[t[o[c[s['+code+']][k zsubject[]]]][k zpoint[]]].' for code in (FIRST_CODE,SECOND_CODE))
    doc=fixture(queries)
    v=content_model(doc);assert run(doc,v)==[True,True]
    v=content_model(doc,bits=(True,True,True,False));assert run(doc,v)==[False,False]
    v=content_model(doc,used=());assert run(doc,v)==[True,False]
    v=content_model(doc,used=('r1','r2','r3'),epistemic=('r1','r2','r3'));assert run(doc,v)==[True,False]
    v=content_model(doc,used=('r1','r2','r3'));assert run(doc,v)==[True,True]
    for n in ('h247u','h247v','h247w','fb','hzv','fc'):
        v=content_model(doc);v[n]=unknown
        try:run(doc,v)
        except ValueError as error:assert 'Unknown' in str(error),str(error)
        else:raise AssertionError(n)
    return dict(exact_constructed_report_bodies_evaluated=True,teaching_and_grounds_distinguished=True,
        extra_argument_rejected_practical_motive_allowed=True,inner_truth_not_executed=True)


@lru_cache(None)
def structure_checks():
    old,dependency=parents();new=catalog()
    for n,e in new.entries.items():
        if n not in PRIMITIVES and n not in MEANINGS:
            prior=old.entries.get(n,dependency.entries.get(n));assert prior
            assert e['declaration']==prior['declaration'] and e['meaning_ja']==prior['meaning_ja'],n
    for path,body in build().items():assert (ROOT/path).read_text(encoding='utf-8')==body,path
    for notation in ('compact','full'):
        t=format_graph(new.document,notation);assert parse(t)==parse(transcribe(t,alphabet='v2'))==new.document
    validate_hashes(ROOT,read(PRIOR)['source_sha256'])
    return dict(unchanged_imports=True,roundtrips=True,new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),
        existing_rank_one_transmission_reused=True,no_source_sentence_added=True)


def prepare():
    from scripts.audit_opening_scope import write_exact
    for path,body in build().items():write_exact(ROOT/path,body)


def build_report():
    results={n:f() for n,f in [('native',native_checks),('construction',construction_checks),('content',content_checks),('structure',structure_checks)]}
    paths=set(build())|set(catalog().source_sha256)|{DOC,PRIOR,'scripts/compose_paired_church_reports.py',
        'scripts/check_paired_church_reports.py','tests/test_paired_church_reports.py',
        'scripts/check_institutional_teaching_grounds.py','scripts/check_pastoral_roles.py','scripts/check_motive_causes.py',
        'scripts/compose_grounded_step.py','scripts/compose_qualitative_influence.py','scripts/compose_confessional_teaching.py'}
    return dict(status='same_speaker_church_and_ranked_ordered_reports',document=LIBRARY,**results,
        whole_sentence_semantically_verified=False,verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
