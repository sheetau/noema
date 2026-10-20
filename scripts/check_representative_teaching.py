"""Evaluate delegated teaching, representative presentation and full conformity."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,validate_hashes
from noema.script import transcribe
from scripts.compose_representative_teaching import ROOT,LIBRARY,BASIS,NAMES,PRIMITIVES,MEANINGS,parent,build,closure
from scripts.check_teaching_policy import EXTRA_LOCAL,PROVIDERS,SMALL,SCENES,local_model
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown,symbol

REPORT='reports/representative-teaching-v1.json'
DOC='docs/representative-teaching-v1.md'
EVIDENCE='data/representative-teaching-evidence-v1.json'
PRIOR='reports/teaching-policy-v1.json'
TARGETS=('r37z','r372','r373','r374')


def read(path):return json.loads((ROOT/path).read_text(encoding='utf-8'))
@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)


@lru_cache(None)
def fixture():
    doc=deepcopy(catalog().document);doc.update(declarations=closure(doc,list(TARGETS)),statements=[])
    prefix=parse('p:'+EXTRA_LOCAL+PROVIDERS)
    providers={d['name']:d for d in prefix['declarations'] if d['name'] in ('h246e','h246j')}
    doc['declarations']=[d for d in prefix['declarations'] if d['name'] not in providers]+[
        deepcopy(providers.get(d['name'],d)) for d in doc['declarations']]
    args=' '.join('k z'+n+'[]' for n in NAMES)+' k zref[] k zoccasion[] k zactivity[] r[p zmessage]'
    query='q[k r37z[k zperson[] k zrole[] k zchurch[] k zsubject[] k zpoint[]]].'
    query+=''.join('q[t[k '+n+'['+args+']][k zpoint[]]].' for n in TARGETS[1:])
    return parse(format_graph(doc,'compact')+query)


def model(variant='baseline',bits=(True,True,True)):
    agent,named,conforms=bits
    doc=fixture();v=local_model(doc,'criterion_failed' if not conforms else variant)
    def business(*args):
        expected=['person','role','church','subject','outcome']
        for i,n in enumerate(('person','role','principal','subject','point')):
            if variant=='business_'+n:expected[i]='other'
        return agent and args==tuple(expected)
    def presented(activity,principal,subject,code,point):
        expected=['activity','church','subject','zmessage',0,'outcome']
        for i,n in enumerate(('activity','principal','subject','message','rank','point')):
            if variant=='name_'+n:expected[i]=1 if n=='rank' else 'other'
        return named and (activity,principal,subject,symbol(code),code.rank,point)==tuple(expected)
    v.update(h247n=business,h247o=presented)
    if variant=='one_recipient_only':
        original=v['f2'];v['f2']=lambda act,recipient,subject,code,point:recipient=='learner' and original(act,recipient,subject,code,point)
    return v


@lru_cache(None)
def independence_checks():
    rows=[]
    for bits in product((False,True),repeat=3):
        a,n,c=bits;v=model(bits=bits)
        assert v['zbelief'] is unknown and v['zmeaning'] is unknown
        actual=evaluate(fixture(),v,SMALL,SCENES,True)
        assert actual==[a,a,a and n,a and n and c],(bits,actual)
        rows.append(dict(business= a,speaks_for_principal=n,conforms=c,results=actual))
    return dict(truth_table=rows,delegation_representation_and_conformity_independent=True,
        no_creed_truth_message_truth_or_personal_assent_required=True,definitions_replaced_by_primitives=False)


@lru_cache(None)
def actual_checks():
    rows={}
    specs=[('baseline',[True]*4),('congregation_task',[True]*4),('no_event',[True,False,False,False]),
        ('other_presenter',[True,False,False,False]),('not_exposition',[True,False,False,False]),
        ('no_recipient_reached',[True,False,False,False]),('one_recipient_only',[True,True,True,False]),
        ('other_task_activity',[True,False,False,False]),('position_role',[True,False,False,False]),
        ('not_entrusted',[False]*4),('no_current_service',[False]*4),('served_church',[False]*4),
        ('service_role',[False]*4),('empty_allocation',[True,False,False,False]),
        ('foreign_recipient',[True,False,False,False]),('no_current_adoption',[True,True,True,False]),
        ('equivalent_alias',[True,False,False,False])]
    for variant,expected in specs:
        actual=evaluate(fixture(),model(variant),SMALL,SCENES,True)
        assert actual==expected,(variant,actual);rows[variant]=actual
    return dict(contrasts=rows,native_r35t_r357_r356_and_criteria_used=True,
        bare_office_or_utterance_name_not_sufficient=True,reference_standard_alias_invalidates_the_underlying_teaching_case=True,
        full_assigned_audience_only_required_for_complete_conforming_exposition=True)


@lru_cache(None)
def identity_checks():
    rows={}
    for prefix,fields in [('business',('person','role','principal','subject','point')),
        ('name',('activity','principal','subject','message','rank','point'))]:
        for field in fields:
            variant=prefix+'_'+field;actual=evaluate(fixture(),model(variant),SMALL,SCENES,True)
            assert actual==([False]*4 if prefix=='business' else [True,True,False,False]),(variant,actual)
            rows[variant]=actual
    # Require another principal even when all primitive interpretations agree.
    doc=deepcopy(catalog().document);doc.update(declarations=closure(doc,['r37z']),statements=[])
    doc=parse(format_graph(doc,'compact')+'r zx[] a.r zpoint[] d.q[k r37z[k zx[] k zx[] k zx[] k zx[] k zpoint[]]].')
    v={d['name']:(lambda *a:True) for d in doc['declarations'] if d['kind']=='primitive'}
    v.update(zx=lambda:'x',zpoint=lambda:'outcome')
    assert evaluate(doc,v,('x',),SCENES,True)==[False]
    return dict(contrasts=rows,principal_distinct_from_person=True,exact_closed_message_and_evaluation_point=True)


@lru_cache(None)
def structure_checks():
    new,old=catalog(),parent()
    for n,e in new.entries.items():
        if n not in PRIMITIVES and n not in MEANINGS:
            assert e['declaration']==old.entries[n]['declaration'] and e['meaning_ja']==old.entries[n]['meaning_ja'],n
    for path,body in build().items():assert (ROOT/path).read_text(encoding='utf-8')==body,path
    validate_hashes(ROOT,read(BASIS)['import_source_sha256']);validate_hashes(ROOT,read(PRIOR)['source_sha256'])
    evidence=read(EVIDENCE)
    for page in evidence['pages']:
        assert page['visually_inspected'] and digest((ROOT/page['path']).read_bytes())==page['sha256']
    inventory=read(evidence['source_inventory']);unit=next(u for u in inventory['units'] if u['id']==evidence['source']['unit'])
    start,end=evidence['source']['range']
    assert unit['text_sha256']==evidence['source']['unit_sha256'] and unit['text'][start:end]==evidence['source']['text']
    for notation in ('compact','full'):
        text=format_graph(new.document,notation);assert parse(text)==parse(transcribe(text,alphabet='v2'))==new.document
    rejected=[]
    for n in ('h247n','h247o','cf','cb','h246k','h246l','dg','f3','f2','h246o','zjudge'):
        v=model();v[n]=unknown
        try:evaluate(fixture(),v,SMALL,SCENES,True)
        except ValueError as error:assert 'Unknown' in str(error),str(error)
        else:raise AssertionError(n)
        rejected.append(n)
    doc=deepcopy(new.document);doc['statements']=[]
    doc=parse(format_graph(doc,'compact')+'q[e[r b[p r374]][r b[p r374]]].')
    assert evaluate(doc,{d['name']:unknown for d in doc['declarations'] if d['kind']=='primitive'},SMALL,SCENES,True)==[True]
    return dict(new_primitives=len(PRIMITIVES),new_definitions=len(MEANINGS),inherited_meanings_preserved=True,
        roundtrips=True,unknown_relations_rejected=rejected,closed_complete_exposition_quote_does_not_execute=True,new_semantic_reviews=0)


def prepare():
    from scripts.audit_opening_scope import write_exact
    for path,body in build().items():write_exact(ROOT/path,body)


def build_report():
    results={}
    for name,fn in [('independence',independence_checks),('actual',actual_checks),('identity',identity_checks),('structure',structure_checks)]:
        results[name]=fn();print(name+' checked',flush=True)
    paths=set(build())|set(parent().source_sha256)|{DOC,EVIDENCE,PRIOR,
        *[p['path'] for p in read(EVIDENCE)['pages']],read(EVIDENCE)['source_inventory'],
        'scripts/compose_representative_teaching.py','scripts/check_representative_teaching.py','tests/test_representative_teaching.py',
        'scripts/check_teaching_policy.py','scripts/check_confessional_teaching.py','scripts/check_clerical_audiences.py',
        'scripts/compose_confessional_teaching.py','scripts/compose_grounded_step.py','scripts/compose_qualitative_influence.py',
        'scripts/check_pastoral_roles.py','scripts/check_motive_causes.py'}
    return dict(status='delegated_business_representative_exposition_and_conformity',document=LIBRARY,**results,
        whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
