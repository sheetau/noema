"""Keep scandal assessment, sanction execution, possibility and permission distinct."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.constructed_semantics import Content
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,validate_hashes
from noema.script import transcribe
from scripts.compose_scandal_sanction import ROOT,LIBRARY,BASIS,NAMES,PRIMITIVES,MEANINGS,parent,build,closure
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown,symbol

REPORT='reports/scandal-sanction-v1.json'
DOC='docs/scandal-sanction-v1.md'
EVIDENCE='data/scandal-reading-v1.json'
PRIOR='reports/general-resistance-v1.json'
DOMAIN=(*NAMES,'source','role','other')
SCENES=('reference','possible','other')
EXTRA=''.join('r z'+n+'[] a.' for n in DOMAIN)+'r zref[] d.r zpoint[] d.'


def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))


@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)


@lru_cache(None)
def fixture(kind,bindings=()):
    target=dict(assessment='r34j',sanction='r34k',bindings='r34l',possible='r34m',permission='r34n',eligible='r34o')[kind]
    doc=deepcopy(catalog().document)
    if kind=='bindings':
        d=next(d for d in doc['declarations'] if d['name']=='r34k')
        d.update(kind='primitive',parameters=[p['sort'] for p in d['parameters']]);d.pop('body')
    doc.update(declarations=closure(doc,[target]),statements=[])
    if kind=='bindings':args='l[a]['+' '.join('k z'+n+'[]' for n in bindings)+'] k zref[]'
    else:
        names=dict(assessment=('criticism','community','standard'),sanction=NAMES,possible=('role',*NAMES),
            permission=('source','role',*NAMES),eligible=('source','person','criticism','community','standard'))[kind]
        args=' '.join('k z'+n+'[]' for n in names)+' k zref[]'
    return parse(format_graph(doc,'compact')+EXTRA+'q[t[k '+target+'['+args+']][k zpoint[]]].')


def base(doc):
    v={d['name']:unknown for d in doc['declarations'] if d['kind']=='primitive'}
    for n in DOMAIN:v['z'+n]=lambda n=n:n
    v.update(zref=lambda:'reference',zpoint=lambda:'reference')
    return v


def assessment_model(doc,variant='baseline'):
    v=base(doc)
    v.update(h244u=lambda act,community,ref,point:variant!='not_public' and (act,community,ref,point)==(
        'criticism','other' if variant=='other_public_community' else 'community','reference','reference'),
        h244v=lambda standard,community,ref:variant!='not_strict_duty' and (standard,community,ref)==('standard','community','reference'),
        h244w=lambda act,standard,ref,point:variant!='no_disregard' and (act,standard,ref,point)==(
            'other' if variant=='other_disregarding_act' else 'criticism',
            'other' if variant=='other_disregarded_standard' else 'standard',
            'other' if variant=='other_disregard_reference' else 'reference',
            'other' if variant=='other_disregard_point' else 'reference'))
    return v


@lru_cache(None)
def assessment_checks():
    doc,rows=fixture('assessment'),{}
    for variant in ('baseline','not_public','other_public_community','not_strict_duty','no_disregard',
        'other_disregarding_act','other_disregarded_standard','other_disregard_reference','other_disregard_point'):
        actual=evaluate(doc,assessment_model(doc,variant),DOMAIN,SCENES,True)
        assert actual==[variant=='baseline'],(variant,actual);rows[variant]=actual[0]
    return dict(contrasts=rows,native_public_example_and_duty_disregard=True,
        no_resistance_or_sanction_required=True)


def sanction_model(doc,variant='baseline',point='reference'):
    v=base(doc)
    v.update(cg=lambda authority,measure,scene:variant!='not_enacted' and (authority,measure,scene)==('authority','measure',point),
        h244x=lambda measure,person,scene:variant!='no_adverse_effect' and (measure,person,scene)==(
            'other' if variant=='other_adverse_measure' else 'measure','person',point),
        h244y=lambda authority,measure,person,scene:variant!='no_intention' and (authority,measure,person,scene)==(
            'authority','measure','other' if variant=='other_intended_person' else 'person',point))
    def responds(authority,measure,person,offense,community,standard,code,ref,scene):
        return variant!='unrelated_response' and (authority,measure,person,offense,community,standard,symbol(code),code.rank,ref,scene)==(
            'other' if variant=='other_responding_authority' else 'authority','measure','person',
            'other' if variant=='other_offense' else 'criticism',
            'other' if variant=='other_assessed_community' else 'community',
            'other' if variant=='other_assessed_standard' else 'standard','r34j',0,
            'other' if variant=='other_assessment_reference' else 'reference',
            'other' if variant=='other_response_point' else point)
    v['h244z']=responds
    if variant=='false_assessment':
        v.update(h244u=lambda *a:False,h244v=lambda *a:False,h244w=lambda *a:False)
    return v


@lru_cache(None)
def sanction_checks():
    doc,rows=fixture('sanction'),{}
    for variant in ('baseline','false_assessment','not_enacted','no_adverse_effect','other_adverse_measure','no_intention',
        'other_intended_person','unrelated_response','other_responding_authority','other_offense','other_assessed_community',
        'other_assessed_standard','other_assessment_reference','other_response_point'):
        v=sanction_model(doc,variant)
        if variant!='false_assessment':assert all(v[n] is unknown for n in ('h244u','h244v','h244w'))
        actual=evaluate(doc,v,DOMAIN,SCENES,True)
        assert actual==[variant in ('baseline','false_assessment')],(variant,actual);rows[variant]=actual[0]
    return dict(contrasts=rows,native_enactment_adversity_intention_and_assessed_response=True,
        assessment_truth_not_required=True)


@lru_cache(None)
def binding_checks():
    for special in range(6):
        names=tuple('person' if i==special else 'other' for i in range(6))
        expected=tuple('x' if i==special else 'y' for i in range(6))+('reference',)
        doc=fixture('bindings',names);v=base(doc);v.update(zperson=lambda:'x',zother=lambda:'y')
        v['r34k']=lambda *args:Content(SCENES,tuple(args==expected for _ in SCENES))
        assert evaluate(doc,v,('x','y'),SCENES,True)==[True],special
    for size in (0,5,7):
        doc=fixture('bindings',('person',)*size);v=base(doc);v['zperson']=lambda:'x'
        v['r34k']=lambda *args:Content(SCENES,(True,True,True))
        assert evaluate(doc,v,('x','y'),SCENES,True)==[False],size
    return dict(independently_checked_positions=6,invalid_lengths_refused=[0,5,7],
        boundaries=['r34k is a typed boundary for exact binding checks; sanction checks evaluate its native definition.'])


def possible_model(doc,variant='baseline'):
    v=sanction_model(doc,variant,point='possible')
    v['h245a']=lambda authority,role,community,ref:variant!='private_revenge' and (
        authority,role,community,ref)==('authority','role','community','reference')
    v['h245b']=lambda act,community,evaluation,outcome:variant!='no_candidates' and (
        act,community,evaluation)==('measure','other' if variant=='other_candidate_community' else 'community',
            'other' if variant=='other_evaluation' else 'reference') and outcome in (
            ('possible','other') if variant=='mixed_candidates' else ('possible',))
    return v


@lru_cache(None)
def possible_checks():
    doc,rows=fixture('possible'),{}
    for variant in ('baseline','mixed_candidates','false_assessment','private_revenge','no_candidates',
        'other_candidate_community','other_evaluation','not_enacted','no_adverse_effect','no_intention','other_response_point'):
        actual=evaluate(doc,possible_model(doc,variant),DOMAIN,SCENES,True)
        assert actual==[variant in ('baseline','mixed_candidates','false_assessment')],(variant,actual);rows[variant]=actual[0]
    assert evaluate(fixture('sanction'),sanction_model(fixture('sanction'),point='possible'),DOMAIN,SCENES,True)==[False]
    return dict(contrasts=rows,native_possible_sanction=True,actual_sanction_not_required=True,
        permission_not_required_by_execution_possibility=True)


def permission_model(doc,variant='baseline'):
    v=base(doc)
    def norm(source,authority,role,code,bindings,ref,sign,point):
        return variant!='no_permission' and (source,authority,role,symbol(code),code.rank,tuple(bindings.items),ref,sign,point)==(
            'other' if variant=='other_source' else 'source','authority','other' if variant=='other_role' else 'role','r34l',1,
            tuple('other' if variant=='other_binding_'+n else n for n in NAMES),
            'other' if variant=='other_reference' else 'reference',variant!='negative_permission',
            'other' if variant=='other_point' else 'reference')
    v['h245c']=norm
    v['h237z']=lambda source,authority,role,code,bindings,ref,sign,point:variant=='opposed_requirement' and (
        source,authority,role,symbol(code),code.rank,tuple(bindings.items),ref,sign,point)==(
            'source','authority','role','r34l',1,NAMES,'reference',False,'reference')
    v['h245a']=lambda authority,role,community,ref:variant!='private_revenge' and (
        authority,role,community,ref)==('authority','role','community','reference')
    return v


@lru_cache(None)
def permission_checks():
    doc,rows=fixture('permission'),{}
    for variant in ('baseline','no_permission','other_source','other_role','other_reference','negative_permission','other_point',
        'opposed_requirement')+tuple('other_binding_'+n for n in NAMES):
        v=permission_model(doc,variant)
        assert all(v[n] is unknown for n in ('cg','h244x','h244y','h244z','h244u'))
        actual=evaluate(doc,v,DOMAIN,SCENES,True)
        assert actual==[variant=='baseline'],(variant,actual);rows[variant]=actual[0]
    return dict(contrasts=rows,native_positive_permission_and_same_source_nonprohibition=True,
        quoted_assessment_and_sanction_not_evaluated=True,permission_does_not_establish_execution_possibility=True)


@lru_cache(None)
def eligibility_checks():
    doc,rows=fixture('eligible'),{}
    for variant in ('baseline','no_permission','private_revenge','opposed_requirement','other_binding_person','other_binding_community'):
        actual=evaluate(doc,permission_model(doc,variant),DOMAIN,SCENES,True)
        assert actual==[variant=='baseline'],(variant,actual);rows[variant]=actual[0]
    return dict(contrasts=rows,native_existential_institutional_authority_role_and_measure=True,
        some_permitted_sanction_not_all_measures_or_duty=True)


@lru_cache(None)
def unknown_checks():
    rows=[]
    for kind,model,names in (('assessment',assessment_model,('h244u','h244v','h244w')),
        ('sanction',sanction_model,('h244x','h244y','h244z')),
        ('possible',possible_model,('h245a','h245b')),('permission',permission_model,('h245c','h237z'))):
        doc=fixture(kind)
        for name in names:
            v=model(doc);v[name]=unknown
            try:evaluate(doc,v,DOMAIN,SCENES,True)
            except ValueError as error:assert 'Unknown' in str(error)
            else:raise AssertionError(name)
            rows.append(name)
    return dict(unknown_inputs_refused=rows)


@lru_cache(None)
def structure_checks():
    old,new=parent(),catalog();assert not new.document['statements']
    for n,e in new.entries.items():
        if n not in PRIMITIVES and n not in MEANINGS:
            assert e['declaration']==old.entries[n]['declaration'] and e['meaning_ja']==old.entries[n]['meaning_ja'],n
    validate_hashes(ROOT,read(PRIOR)['source_sha256'])
    for p,s in build().items():assert (ROOT/p).read_text(encoding='utf-8')==s,p
    for notation in ('compact','full'):
        text=format_graph(new.document,notation)
        assert parse(text)==parse(transcribe(text,alphabet='v2'))==new.document
    validate_hashes(ROOT,{s['raw_archive']:s['raw_sha256'] for s in read(EVIDENCE)['sources']})
    return dict(new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),new_semantic_reviews=0,
        active_manuscript_unchanged=True,roundtrips=True,supplementary_primary_source_hash_verified=True)


def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,s in build().items():write_exact(ROOT/p,s)


def build_report():
    results={}
    for name,fn in [('assessment',assessment_checks),('sanction',sanction_checks),('bindings',binding_checks),
        ('possible',possible_checks),('permission',permission_checks),('eligibility',eligibility_checks),
        ('unknown',unknown_checks),('structure',structure_checks)]:
        results[name]=fn();print(name+' checked',flush=True)
    paths=set(build())|set(parent().source_sha256)|{
        DOC,PRIOR,EVIDENCE,'scripts/compose_scandal_sanction.py','scripts/check_scandal_sanction.py','tests/test_scandal_sanction.py',
        'scripts/compose_protected_remarks.py','scripts/compose_grounded_step.py','scripts/compose_qualitative_influence.py',
        'scripts/check_pastoral_roles.py','scripts/check_motive_causes.py'}
    return dict(status='scandal_assessment_execution_possibility_and_normative_availability',document=LIBRARY,**results,
        whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
