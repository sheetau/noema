"""Evaluate fixed public permissions and their native modal change binding."""
import argparse
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse,format_graph
from noema.constructed_semantics import evaluate_document
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts import check_collective_change as prior
from scripts.check_described_explanations import symbol
from scripts.compose_audience_liberty import ROOT,PARENT,PARENT_BASIS,FULL,CORE,LIBRARY,BASIS,build
from scripts.compose_subject_bound_departure import closure

REPORT=ROOT/'reports/audience-liberty-v1.json'
DOMAIN=('person','other','group','process','part','faculty','plan')
SCENES=('before','end','anchor')


@lru_cache(maxsize=4)
def document(kind):
    doc=parse((ROOT/CORE).read_text(encoding='utf-8'));doc['statements']=[]
    roots={'permission':['hzna'],'goal':['hznb'],'modal':['hznc','hznd']}[kind]
    doc['declarations']=closure(doc,roots)
    text=format_graph(doc,'compact')+'''
r zaudience[] a.r zreference[] d.r zsource[] a.r zpoint[] d.
r zextent[h[a] c h[a] c] c.r zcases[d] c.r zcomparison[d] c.
r zscale[a] c.r zless[a a] c.r znear[a] c.r zlow[] a.r zhigh[] a.r zdegree[] a.
'''
    if kind=='permission':text+='q[k hzna[k zaudience[] k zreference[] k zsource[] k zpoint[]]].'
    elif kind=='goal':text+='q[k hznb[k zaudience[] k zreference[] p zextent k zpoint[]]].'
    else:
        start='k zaudience[] k zreference[] k zsource[] p zextent p zcases '
        scale='p zscale p zless p znear k zlow[] k zhigh[] '
        text+='q[k hznc['+start+scale+'k zdegree[]]].'
        text+='q[k hznd['+start+'p zcomparison '+scale+'k zdegree[] k zlow[] k zdegree[]]].'
    return parse(text)


def model(doc,variant='baseline',point='anchor',observed=None):
    values=prior.source_model(doc,'one')
    def record(kind,*args):
        if observed is not None:observed.append((kind,*args))
    def audience(group,person,reference):
        record('audience',group,reference)
        if variant=='unknown_scope':return prior.unknown()
        if variant=='empty_audience':return False
        # At another evaluation point, the readership can differ. The new
        # composition must keep asking about the original reference point.
        people={'person'} if reference!='anchor' else {'person','other'}
        if variant=='nonhuman_audience':people.add('process')
        return group=='group' and person in people
    pairs={('person','process','faculty'),('other','part','plan')}
    if variant=='missing_activity':pairs={('person','process','faculty')}
    def classified(person,act,role,reference):
        record('classification',reference)
        if variant=='unknown_classification':return prior.unknown()
        if variant=='candidate_activity_shrink' and reference=='end':return (person,act,role)==('person','process','faculty')
        return reference=='anchor' and (person,act,role) in pairs
    def norm(source,person,role,act,description,sign,context,allow):
        record('norm',source,person,role,act,symbol(description),sign,context)
        if variant=='unknown_permission' and allow:return prior.unknown()
        expected_source='person' if variant=='other_source' else 'group'
        expected_description='hznb' if variant=='other_description' else 'zzq'
        expected={(p,r,a) for p,a,r in pairs}
        if variant=='other_person':expected={('person',r,a) for p,r,a in expected}
        if variant=='other_role':expected={(p,'group',a) for p,r,a in expected}
        if variant=='other_activity':expected={(p,r,'plan') for p,r,a in expected}
        match=source==expected_source and (person,role,act) in expected and symbol(description)==expected_description
        if allow:
            permit=match and sign and context in (('anchor',) if variant=='other_context' else ('end','anchor'))
            if variant in ('missing_second_permission','candidate_activity_shrink') and person=='other':permit=False
            if variant=='opposite_permission':permit=match and not sign
            if variant=='no_permission':permit=False
            if variant=='empty_condition':permit=False
            if variant=='condition_only_success':permit=permit and context=='anchor'
            if variant=='actual_permission':permit=match and sign
            return permit
        return match and (not sign if variant=='opposed_requirement' else sign if variant=='positive_requirement' else False)
    values.update(zaudience=lambda:'group',zreference=lambda:'anchor',zsource=lambda:'group',zpoint=lambda:point,
        zextent=lambda members,changed:True,zcomparison=lambda world:False,
        zcases=lambda world:world in ('end','anchor'),zscale=lambda value:value in ('group','faculty','plan'),
        zless=lambda a,b:a in ('group','faculty','plan') and b in ('group','faculty','plan') and
            ('group','faculty','plan').index(a)<('group','faculty','plan').index(b),
        znear=lambda value:value=='faculty',zlow=lambda:'group',zhigh=lambda:'plan',zdegree=lambda:'faculty',
        h6t=audience,aa=lambda who:who in ('person','other'),
        ca=lambda person,act,reference:any(classified(person,act,r,reference) for r in DOMAIN),
        cb=classified,cd=lambda role,reference:role in ('faculty','plan') and reference=='anchor',
        cc=lambda act,group,reference:act in ('process','part') and group==('plan' if variant=='distinct_public_destination' else 'group') and reference=='anchor',
        ce=lambda group,reference:group==('plan' if variant=='distinct_public_destination' else 'group') and reference=='anchor',
        h7a=lambda *args:norm(*args,False),h7b=lambda *args:norm(*args,True),cg=prior.unknown,
        mp=prior.unknown,h6e=prior.unknown,h6g=prior.unknown,h6n=prior.unknown)
    if variant=='missing_cause':values['g3']=lambda *args:False
    if variant=='unknown_goal':values['g3']=prior.unknown
    if variant=='unknown_degree':values['zdegree']=prior.unknown
    return values


def generic_checks():
    doc=parse((ROOT/LIBRARY).read_text(encoding='utf-8')+'''
r zmembers[a] c.r zeligible[a] c.r zactivities[a a a] c.
r zrequired[a a a a i[h[a a] e] c d] c.r zallowed[a a a a i[h[a a] e] c d] c.
r zsource[] a.r zpoint[] d.r zexecution[a a d] c.
d zdescription[person a act a] e[b point[k zexecution[v person v act v point]]].
q[k rqta[p zmembers p zeligible p zactivities i[act a][r[p zdescription]] k zsource[] k zpoint[] p zrequired p zallowed]].
''')
    domain=('p','q','source','role','act');cases=0
    for member_flags,permission_flags in product(product((False,True),repeat=2),product((False,True),repeat=4)):
        members={p for p,flag in zip(('p','q'),member_flags) if flag}
        allowed={p for p,flag in zip(('p','q'),permission_flags[:2]) if flag}
        forbidden={p for p,flag in zip(('p','q'),permission_flags[2:]) if flag}
        def norm(source,person,role,act,description,sign,point,permit):
            match=(source,role,act,symbol(description),point)==('source','role','act','zdescription','now')
            return match and (sign and person in allowed if permit else not sign and person in forbidden)
        values=dict(zmembers=lambda p:p in members,zeligible=lambda p:p in ('p','q'),
            zactivities=lambda p,a,r:p in ('p','q') and (a,r)==('act','role'),
            zrequired=lambda *args:norm(*args,False),zallowed=lambda *args:norm(*args,True),
            zsource=lambda:'source',zpoint=lambda:'now',zexecution=prior.unknown)
        actual=prior.evaluate(doc,values,domain,('now',))
        assert actual==[bool(members) and members<=allowed and not members&forbidden]
        cases+=1
    return dict(membership_permission_and_opposition_combinations=cases,execution_not_evaluated=True,uncached=True)


def permission_checks():
    doc=document('permission');rows={}
    variants=('baseline','empty_audience','nonhuman_audience','missing_activity','other_source','other_description',
        'other_person','other_role','other_activity','missing_second_permission','candidate_activity_shrink',
        'opposite_permission','no_permission','opposed_requirement','positive_requirement','actual_permission',
        'distinct_public_destination','other_context')
    for variant in variants:
        seen=[];actual=prior.evaluate(doc,model(doc,variant,'end',seen),DOMAIN,SCENES,memoize=True)
        assert actual==[variant in ('baseline','positive_requirement','actual_permission','distinct_public_destination')],(variant,actual)
        assert all(row[-1]=='anchor' for row in seen if row[0] in ('audience','classification'))
        rows[variant]=actual
    assert prior.evaluate(doc,model(doc,point='before'),DOMAIN,SCENES)==[False]
    assert prior.evaluate(doc,model(doc),DOMAIN,SCENES)==[True]
    for variant in ('unknown_scope','unknown_classification','unknown_permission'):
        try:prior.evaluate(doc,model(doc,variant),DOMAIN,SCENES,memoize=True)
        except ValueError as e:assert 'Unknown' in str(e)
        else:raise AssertionError(variant)
    return dict(contrasts=rows,unknown_inputs_refused=3,fixed_population_and_activity_reference=True,
        permission_does_not_evaluate_execution=True,uncached_baseline_agrees=True)


def joint_document(missing_cause=False):
    doc=deepcopy(document('modal'));doc['statements']=[]
    text=format_graph(doc,'compact')+'r zempty[] a.r zsuccess[] a.r zactual[] a.r zbefore[] d.r zend[] d.'
    fields='k zaudience[] k zreference[] '
    expressions=['k hzna['+fields+'k zsource[] k zbefore[]]',
        'k hzna['+fields+'k zsource[] k zreference[]]']
    expressions+=['k hznb['+fields+'v extent '+point+']' for point in ('k zbefore[]','k zend[]','k zreference[]')]
    for source in ('zsource','zempty','zsuccess','zactual'):
        start=fields+'k '+source+'[] v extent p zcases '
        scale='p zscale p zless p znear k zlow[] k zhigh[] '
        expressions+=['k hznc['+start+scale+'k zdegree[]]',
            'k hznd['+start+'p zcomparison '+scale+'k zdegree[] k zlow[] k zdegree[]]']
    expected=[False,True,False,False,not missing_cause]+([False]*8 if missing_cause else [True,True,False,False,False,False,True,True])
    truth='e[k zaudience[]][k zaudience[]]'
    wanted='l[c]['+' '.join(truth if value else 'u['+truth+']' for value in expected)+']'
    # One shared extent value lets ordinary definition memoization reuse the
    # same native goal across judgments. The assertion compares the complete
    # result vector, rather than accepting one true member of a conjunction.
    text+='q[e[c[i[extent h[h[a] c h[a] c] c][l[c]['+' '.join(expressions)+']]][p zextent]]['+wanted+']].'
    return parse(text),expected


def joint_model(doc,missing_cause=False,seen=None):
    values=model(doc,'missing_cause' if missing_cause else 'baseline',observed=seen)
    values.update(zempty=lambda:'person',zsuccess=lambda:'other',zactual=lambda:'faculty',
        zbefore=lambda:'before',zend=lambda:'end')
    def allowed(source,person,role,act,description,sign,point):
        if seen is not None:seen.append(('norm',source,person,role,act,symbol(description),sign,point))
        pair=(person,act,role) in {('person','process','faculty'),('other','part','plan')}
        policies={'group':{'end','anchor'},'person':set(),'other':{'anchor'},'faculty':set(SCENES)}
        return pair and symbol(description)=='zzq' and sign and point in policies.get(source,set())
    values['h7b']=allowed;values['h7a']=lambda *args:False
    return values


def native_checks(progress=None):
    vectors={}
    for missing in (False,True):
        doc,expected=joint_document(missing);seen=[]
        values=joint_model(doc,missing,seen)
        values={d['name']:values[d['name']] for d in doc['declarations'] if d['kind']=='primitive'}
        result=[r['value'] for r in evaluate_document(doc,individuals=DOMAIN,situations=SCENES,
            primitives=values,max_steps=180000000,memoize_definitions=True,memoize_expressions=True)]
        assert result==[True],('native vector',missing,expected,result)
        assert all(row[-1]=='anchor' for row in seen if row[0] in ('audience','classification'))
        vectors['missing_cause' if missing else 'baseline']=expected
        if progress:progress('native shared judgment vector '+str(missing)+' checked')
    modal=document('modal');modal=deepcopy(modal);modal['statements']=modal['statements'][:1]
    for variant in ('unknown_goal','unknown_degree'):
        try:prior.evaluate(modal,model(modal,variant),DOMAIN,SCENES,memoize=True)
        except ValueError as e:assert 'Unknown' in str(e)
        else:raise AssertionError(variant)
    return dict(verified_native_result_vectors=vectors,
        vector_order=['current_permission','candidate_permission','goal_before','goal_end','goal_anchor',
            'conditional','comparison_and_conditional','empty_condition','empty_comparison',
            'success_only_condition','success_only_comparison','actual_permission_conditional','actual_permission_comparison'],
        unknown_inputs_refused=2,current_permission_and_change_not_implied=True,
        source_definitions_not_replaced_or_lowered=True,native_change_and_modality_evaluated_together=True,
        shared_extent_binding=True,memoized=True,max_steps_per_native_model=180000000)


def structure():
    old,new=load_catalog(ROOT,PARENT_BASIS),load_catalog(ROOT,BASIS)
    assert new.document['statements']==old.document['statements'] and len(new.document['statements'])==32
    assert new.document['declarations'][:-5]==old.document['declarations']
    for name,entry in old.entries.items():assert new.entries[name]==entry,name
    for index in (16,17,27,28,29,30,31):assert selection_binding(old,[index])==selection_binding(new,[index])
    core=load_catalog(ROOT,BASIS,document_path=CORE)
    assert {'h6t','zzo','zzq','h7a','h7b','hzmy','rqsu','rqsv'}<=set(core.entries)
    assert not {'mp','h6e','h6g','h6n'}&set(core.entries)
    return dict(existing_statements=32,new_definitions=5,new_primitives=0,seven_review_bindings_preserved=True,
        generic_characters=len((ROOT/LIBRARY).read_text(encoding='utf-8')),
        added_characters=len((ROOT/FULL).read_text(encoding='utf-8'))-len((ROOT/PARENT).read_text(encoding='utf-8')))


def build_report(progress=None):
    outputs=build()
    for name,body in outputs.items():assert (ROOT/name).read_text(encoding='utf-8')==body
    for name in (FULL,CORE,LIBRARY):
        doc=parse((ROOT/name).read_text(encoding='utf-8'))
        for notation in ('compact','full'):
            text=format_graph(doc,notation);assert parse(text)==parse(transcribe(text,alphabet='v2'))==doc
    cat=load_catalog(ROOT,BASIS)
    previous=json.loads((ROOT/'reports/audience-change-v1.json').read_text(encoding='utf-8'));validate_hashes(ROOT,previous['source_sha256'])
    alignment=deepcopy(previous['alignment']);alignment.update(definitions=['rqta','hzna','hznb','hznc','hznd'],remaining=[
        'public self-enlightenment beyond individual capacity transitions','liberty beyond the stated normative reading',
        'comparison baseline, source-appropriate extent and social audience scope','reinforcement and author attribution'])
    paths=set(cat.source_sha256)|set(outputs)|set(previous['source_sha256'])|{
        'reports/audience-change-v1.json','scripts/compose_audience_liberty.py','scripts/check_audience_liberty.py',
        'tests/test_audience_liberty.py','docs/audience-liberty-v1.md','docs/scoped-liberty-v1.md'}
    return dict(status='normative_liberty_condition_bound_to_native_modal_change_partial_reading',document=FULL,
        generic=generic_checks(),permission=permission_checks(),native=native_checks(progress),structure=structure(),roundtrips=True,
        alignment=alignment,new_source_assertions=0,verified_full_units={'kant-1784':0,'einstein-1905':0},
        active_review_index_unchanged='data/semantic-review-index-v22.json',source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})


def main():
    cli=argparse.ArgumentParser();cli.add_argument('--verify-only',action='store_true');args=cli.parse_args();report=build_report(lambda message:print(message,flush=True))
    if args.verify_only:assert json.loads(REPORT.read_text(encoding='utf-8'))==report
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:stream.write(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print('Fixed public permissions and native conditional changes checked')


if __name__=='__main__':main()
