"""Check same congregational use, actual commission and complete case scope."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,validate_hashes
from noema.script import transcribe
from scripts.compose_congregational_private_use import ROOT,LIBRARY,BASIS,NAMES,PRIMITIVES,MEANINGS,parent,build,closure
from scripts.check_teaching_policy import EXTRA_LOCAL,PROVIDERS,SMALL,SCENES,local_model
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown

REPORT='reports/congregational-private-use-v1.json'
DOC='docs/congregational-private-use-v1.md'
EVIDENCE='data/congregational-private-use-evidence-v1.json'
PRIORS=('reports/representative-teaching-v1.json','reports/clerical-resignation-condition-v1.json')
ARGS=' '.join('k z'+n+'[]' for n in NAMES)+' k zref[] k zoccasion[] k zactivity[] r[p zmessage]'
GROUP='k zcongregation[] k zchurch[] k zsubject[] k zref[]'


def read(path):return json.loads((ROOT/path).read_text(encoding='utf-8'))
@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)


@lru_cache(None)
def fixture(targets=('r44a','r44b','r44c','r44f'),extra=''):
    doc=deepcopy(catalog().document);doc.update(declarations=closure(doc,list(targets)),statements=[])
    prefix=parse('p:'+EXTRA_LOCAL+PROVIDERS)
    providers={d['name']:d for d in prefix['declarations'] if d['name'] in ('h246e','h246j')}
    doc['declarations']=[d for d in prefix['declarations'] if d['name'] not in providers]+[
        deepcopy(providers.get(d['name'],d)) for d in doc['declarations']]
    query=''
    for name in targets:
        args=GROUP+(' k zpoint[]' if name=='r44e' else '') if name in ('r44d','r44e') else ARGS
        call='k '+name+'['+args+']'
        if name!='r44e':call='t['+call+'][k zpoint[]]'
        query+='q['+call+'].'
    return parse(format_graph(doc,'compact')+query+extra)


def model(doc,variant='baseline'):
    v=local_model(doc,variant)
    def matches(actual,wanted,category,fields):return tuple(actual)==tuple('other' if variant==category+'_'+name else x for name,x in zip(fields,wanted))
    v.update(h247n=lambda *a:matches(a,('person','role','church','subject','outcome'),'business',('person','role','church','subject','point')),
        ca=lambda *a:matches(a,('person','activity','outcome'),'reason',('person','activity','point')),
        cc=lambda *a:matches(a,('activity','congregation','outcome'),'audience',('activity','congregation','point')),
        cd=lambda role,point:variant=='public_same_role' and (role,point)==('role','outcome'),
        ce=lambda group,point:variant=='public_same_role' and (group,point)==('congregation','outcome'),
        h253b=lambda *a:variant!='no_commission_execution' and matches(a,('activity','role','church','subject','reference','outcome'),
            'commission',('activity','role','church','subject','reference','point')),
        h253c=lambda *a:variant!='not_assembly' and matches(a,('congregation','church','subject','reference',a[-1]),
            'assembly',('group','church','subject','reference','point')),
        h253d=lambda *a:variant!='not_internal' and matches(a,('congregation','church','reference',a[-1]),
            'internal',('group','church','reference','point')),
        h253e=lambda *a:variant!='empty_cases' and matches(a,('congregation','church','subject','reference','outcome',a[-1]),
            'selection',('group','church','subject','reference','actual','candidate')))
    if variant in ('only_pupil_reached','only_member_reached'):
        old=v['f2'];wanted='learner' if variant=='only_pupil_reached' else 'overlap'
        v['f2']=lambda act,recipient,subject,code,point:recipient==wanted and old(act,recipient,subject,code,point)
    return v


def run(doc,v,scenes=SCENES):return evaluate(doc,v,SMALL,scenes,True)


@lru_cache(None)
def actual_checks():
    doc=fixture();rows={}
    variants=('baseline','congregation_task','only_member_reached','only_pupil_reached','no_event','other_presenter','not_exposition',
        'no_recipient_reached','not_entrusted','no_current_service','position_role','other_task_activity',
        'reason_person','reason_activity','reason_point','audience_activity','audience_congregation','audience_point',
        'no_commission_execution','not_assembly','not_internal','empty_cases','public_same_role')
    for variant in variants:
        v=model(doc,variant);result=run(doc,v)
        expected=[True]*4 if variant in ('baseline','congregation_task','only_member_reached') else (
            [True,True,False,False] if variant=='no_commission_execution' else
            [True,True,True,False] if variant in ('not_assembly','not_internal','empty_cases') else
            [True,False,True,False] if variant=='public_same_role' else [False]*4)
        assert result==expected,(variant,result);rows[variant]=result
    # r372 may hold for a pupil-only presentation; the new congregation witness
    # must fail without making the underlying exposition fail.
    old=fixture(('r372','r44a'));v=model(old,'only_pupil_reached');assert run(old,v)==[True,False]
    # No belief content, doctrine truth, or conformity test is executed here.
    v=model(doc)
    for name in ('zbelief','zotherbelief','zmeaning','zjudge','zpass','h247o'):v[name]=unknown
    assert run(doc,v)==[True]*4
    return dict(contrasts=rows,native_r372_r35t_and_private_public_classifications=True,
        pupil_only_presentation_distinguished=True,one_congregational_member_suffices=True,
        no_truth_assent_or_conformity_inference=True)


@lru_cache(None)
def identity_checks():
    doc=fixture();rows={}
    specs={'business':('person','role','church','subject','point'),
        'commission':('activity','role','church','subject','reference','point'),
        'assembly':('group','church','subject','reference'),
        'internal':('group','church','reference'),
        'selection':('group','church','subject','reference','actual')}
    for category,fields in specs.items():
        for field in fields:
            variant=category+'_'+field;result=run(doc,model(doc,variant))
            expected=[False]*4 if category=='business' else [True,True,False,False] if category=='commission' else [True,True,True,False]
            assert result==expected,(variant,result);rows[variant]=result
    # The same activity may also be considered under another scholarly capacity;
    # exclusion in r44b concerns this given office, not all roles of the person.
    extra='q[k r2zi[k zperson[] k zactivity[] k zother[] k zpoint[]]].'
    other=fixture(('r44b',),extra);v=model(other);cb=v['cb'];cc=v['cc']
    v['cb']=lambda person,act,role,point:cb(person,act,role,point) or (person,act,role,point)==('person','activity','other','outcome')
    v['cd']=lambda role,point:(role,point)==('other','outcome')
    v['cc']=lambda act,group,point:cc(act,group,point) or (act,group,point)==('activity','other','outcome')
    v['ce']=lambda group,point:(group,point)==('other','outcome')
    assert run(other,v)==[True,True]
    return dict(contrasts=rows,one_institution_subject_reference_and_activity=True,other_scholarly_capacity_not_excluded=True)


@lru_cache(None)
def scope_checks():
    d=fixture(('r44d',));table=[]
    for assembly,internal,world in product((False,True),repeat=3):
        v=model(d);v.update(h253c=lambda *a:assembly,h253d=lambda *a:internal,ce=lambda *a:world)
        result=run(d,v);assert result==[assembly and internal and not world]
        table.append([assembly,internal,world,result[0]])
    d=fixture(('r44e',));cases=[]
    # Situations stand for an actual occasion, a larger-scale variant, and
    # another relevant occasion. No finite sample is claimed to exhaust reality.
    for bits in product((False,True),repeat=6):
        selected={p for p,b in zip(SCENES,bits[:3]) if b};internal={p for p,b in zip(SCENES,bits[3:]) if b}
        v=model(d);v['h253e']=lambda group,church,subject,ref,actual,candidate:candidate in selected
        v['h253d']=lambda group,church,ref,point:point in internal
        result=run(d,v);wanted='outcome' in selected and selected<=internal
        assert result==[wanted],(bits,result);cases.append([*bits,result[0]])
    # Even if other candidates are domestic, omission of the actual one fails.
    v=model(d);v['h253e']=lambda *a:a[-1]!='outcome';assert run(d,v)==[False]
    for name in ('h253c','h253d','ce','h253e'):
        v=model(d);v[name]=unknown
        try:run(d,v)
        except ValueError as error:assert 'Unknown' in str(error),str(error)
        else:raise AssertionError(name)
    return dict(assembly_internal_world_table=table,selection_and_internal_scope_table=cases,
        all_selected_size_and_occasion_variants_required=True,actual_must_be_included=True,unknown_refused=True,
        finite_models_do_not_certify_complete_case_range=True)


@lru_cache(None)
def quotation_checks():
    doc=deepcopy(catalog().document);doc['statements']=[]
    # The target family includes quoted descriptions in the inherited case;
    # rank 2 supports it without evaluating the presentations or case range.
    doc=parse(format_graph(doc,'compact')+'r zshown[i c[h['+' '.join('a' for _ in NAMES)+' d a a i[h[a] f]] e]] c.q[k zshown[r c[p r44f]]].')
    v={d['name']:unknown for d in doc['declarations'] if d['kind']=='primitive'}
    v['zshown']=lambda code:code.rank==2 and json.loads(code.syntax)['symbol']=='r44f'
    assert run(doc,v)==[True]
    return dict(rank_two_family_quotation=True,contents_not_executed=True)


@lru_cache(None)
def structure_checks():
    new,old=catalog(),parent()
    for n,e in new.entries.items():
        if n not in PRIMITIVES and n not in MEANINGS:assert e['declaration']==old.entries[n]['declaration'] and e['meaning_ja']==old.entries[n]['meaning_ja'],n
    for path,body in build().items():assert (ROOT/path).read_text(encoding='utf-8')==body,path
    for notation in ('compact','full'):
        t=format_graph(new.document,notation);assert parse(t)==parse(transcribe(t,alphabet='v2'))==new.document
    for path in PRIORS:validate_hashes(ROOT,read(path)['source_sha256'])
    evidence=read(EVIDENCE)
    for p in (*evidence['pages'],*evidence['lexical_pages']):assert digest((ROOT/p['path']).read_bytes())==p['sha256']
    unit=next(u for u in read(evidence['source_inventory'])['units'] if u['id']==evidence['source']['unit'])
    source=evidence['source'];assert unit['text_sha256']==source['unit_sha256'] and unit['text'][slice(*source['range'])]==source['text']
    return dict(unchanged_imports=True,roundtrips=True,new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),
        primary_evidence_pinned=True,no_source_sentence_added=True)


def prepare():
    from scripts.audit_opening_scope import write_exact
    for path,body in build().items():write_exact(ROOT/path,body)


def build_report():
    results={}
    for name,fn in [('actual',actual_checks),('identity',identity_checks),('scope',scope_checks),('quotation',quotation_checks),('structure',structure_checks)]:
        results[name]=fn();print(name+' checked',flush=True)
    evidence=read(EVIDENCE)
    paths=set(build())|set(catalog().source_sha256)|set(PRIORS)|{DOC,EVIDENCE,evidence['source_inventory'],
        *[p['path'] for p in (*evidence['pages'],*evidence['lexical_pages'])],
        'scripts/compose_congregational_private_use.py','scripts/check_congregational_private_use.py','tests/test_congregational_private_use.py',
        'scripts/check_teaching_policy.py','scripts/check_confessional_teaching.py','scripts/check_clerical_audiences.py',
        'scripts/check_pastoral_roles.py','scripts/check_motive_causes.py','scripts/compose_representative_teaching.py',
        'scripts/compose_grounded_step.py','scripts/compose_qualitative_influence.py'}
    return dict(status='actual_congregational_private_use_and_size_independent_internal_assembly',document=LIBRARY,**results,
        whole_sentence_semantically_verified=False,verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
