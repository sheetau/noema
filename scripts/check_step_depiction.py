"""Verify prior-stage extraction, full goal scope and nonliteral timed alignment."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.compose_step_depiction import ROOT,FULL,CORE,LIBRARY,BASIS,ANNOTATIONS,PARENT,PARENT_BASIS,MEANINGS,PRIMITIVES,LIMITS,parent,build,closure
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown,symbol
from scripts.check_confinement_depiction import target_model
from scripts.check_prevented_attempt import DOMAIN as TARGET_DOMAIN,SCENES as TARGET_SCENES,ref

INDEX='data/semantic-review-index-v72.json'
REPORT='reports/step-depiction-v1.json'
AUDIT='data/step-depiction-reading-v1.json'
DOC='docs/step-depiction-v1.md'
INVENTORY='artifacts/written-units-v1/kant-1784.json'
SELECTION=[9,35,36,46,47]


@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)


def fixture(roots,suffix):
    d=deepcopy(catalog().document);d.update(declarations=closure(d,roots),statements=[])
    return parse(format_graph(d,'compact')+suffix)


def assert_definition(name,expected):
    d=deepcopy(catalog().document);d.update(declarations=[x for x in closure(d,[name]) if x['name']!=name],statements=[])
    actual=next(x for x in catalog().document['declarations'] if x['name']==name)
    normalized=parse(format_graph(d,'compact')+expected)['declarations'][-1]
    assert actual==normalized,name


def embedding_checks():
    # Check the actual source definitions before using their conjunction law.
    assert_definition('hztp','''d hztp[group a anchor d first d prior d] c[
 w[k dd[v first v anchor]][w[k dd[v prior v anchor]][w[g person a[k dj[v person v anchor]]][
 f person a[y[k dj[v person v anchor]][w[k g4[v group v person v first]][t[k hzto[v group v person]][v prior]]]]
 ]]]].''')
    assert_definition('hztq','''d hztq[group a anchor d first d prior d] c[
 w[k hztp[v group v anchor v first v prior]][f person a[y[k dj[v person v anchor]][
 t[k hztc[v group v person k hztd[] r[p bb]]][v prior]
 ]]]].''')
    assert_definition('rqzw','''d rqzw[person a prior d anchor d] c[
 w[k dd[v prior v anchor]][w[t[k hzto[k db[] v person]][v prior]][t[k hztc[k db[] v person k hztd[] r[p bb]]][v prior]]]
 ].''')
    from noema.grammar import parse as parse_first_order
    from noema.first_order_proofs import verify
    proof=parse_first_order('''n:
r ja[] c.r jb[] c.r jd[a] c.r jg[a] c.r jh[a] c.r jn[a] c.
d jstage[] c[w[k ja[]][w[k jb[]][w[g person a[k jd[v person]]][f person a[y[k jd[v person]][w[k jg[v person]][k jh[v person]]]]]]]].
s[e[w[k jstage[]][f person a[y[k jd[v person]][k jn[v person]]]]][
 w[k jstage[]][f person a[y[k jd[v person]][w[k jb[]][w[k jh[v person]][k jn[v person]]]]]]
]].
''')
    result=verify(proof);assert len(result)==1 and result[0]['status']=='valid',result
    return dict(actual_stage_and_target_shapes_checked=True,abstract_conjunction_law=result,
        arbitrary_nonempty_individual_domains=True,source_group_fixed_to_db=True,
        claim_point_and_selected_person_preserved=True,
        proof_limit='The conjunction law embeds the extracted local relation in the checked stage shape. It does not prove the historical reading or truth of any primitive.')


@lru_cache(None)
def target_fixture():
    return fixture(['rqzw'],'r jp[] a.r jprior[] d.r janchor[] d.r jother[] d.'+
        'q[k rqzw[k jp[] k jprior[] k janchor[]]].q[k rqzw[k jp[] k jother[] k janchor[]]].')


def target_values(d,variant='baseline'):
    v=target_model(d,'actually_attempts' if variant=='actually_attempts' else 'baseline')
    def goal(g,b):return ref(g,'hztm') and b.items in (('person',),('other',))
    v.update(jp=lambda:'person',jprior=lambda:'prior',janchor=lambda:'actual',jother=lambda:'conditioning',
        hztd=lambda:'supervised',h7k=unknown,h7l=lambda *args:variant=='intellectual_permission',
        hztk=lambda group,act,g,b,aspect,scene:(group,act,scene)==('guards','blocking_act','prior') and
            goal(g,b) and aspect in ('detailone','detailtwo'),
        hztj=lambda actor,act,g,b,aspect,scene:(actor,act,scene)==('guardone' if aspect=='detailone' else 'guardtwo','blocking_act','prior') and
            goal(g,b) and aspect in ('detailone','detailtwo') and not(variant=='missing_detail' and aspect=='detailtwo'),
        hztl=lambda actor,act,g,b,scene:variant!='no_purpose' and actor in ('guardone','guardtwo') and
            (act,scene)==('blocking_act','prior') and goal(g,b))
    if variant=='no_cause':v['g3']=lambda *args:False
    if variant=='reverse_time':v['dd']=lambda a,b:(a,b)==('actual','prior')
    return v


def target_checks():
    d=target_fixture();rows={};domain=TARGET_DOMAIN+('supervised','detailone','detailtwo')
    for name in ('baseline','no_cause','actually_attempts','missing_detail','no_purpose','intellectual_permission','reverse_time'):
        actual=evaluate(d,target_values(d,name),domain,TARGET_SCENES,True)
        assert actual==[name=='baseline',False],(name,actual);rows[name]=actual
    joint=fixture(['rqzw','rqzx'],'r jp[] a.r jprior[] d.r janchor[] d.r jother[] d.'+
        'q[k rqzw[k jp[] k jprior[] k janchor[]]].q[k rqzx[k jp[] k jprior[] k janchor[]]].'+
        'q[k rqzw[k jp[] k jother[] k janchor[]]].q[k rqzx[k jp[] k jother[] k janchor[]]].')
    pairs={}
    for point in (None,'prior','conditioning'):
        v=target_values(joint)
        v['qs']=lambda person,anchor:'frame'
        v['h7l']=lambda source,person,role,description,bindings,polarity,scene:point is not None and ref(description,'rqzk') and \
            (source,person,role,bindings.items,polarity,scene)==(
                'guards','person','supervised',('person','frame','foot','process'),True,point)
        actual=evaluate(joint,v,domain+('frame','foot','process'),TARGET_SCENES,True)
        expected=[True,point!='prior',False,point!='conditioning']
        assert actual==expected,(point,actual);pairs[point or 'none']=actual
    split=pairs['prior']
    assert (split[0] or split[2]) and (split[1] or split[3]) and not ((split[0] and split[1]) or (split[2] and split[3]))
    return dict(contrasts=rows,joint_point_contrasts=pairs,separate_past_witnesses_do_not_form_a_shared_point=True,
        actual_cause_attention_and_undertaking_definitions_evaluated=True,
        other_prior_point_not_substituted=True,pure_memoization=True)


BODY_DOMAIN=('person','other','guards','role','frame','otherframe','foot','process')
BODY_TIMES=('prior','earlier','actual','elsewhere')


@lru_cache(None)
def body_fixture():
    return fixture(['rqzx'],'r jp[] a.r jprior[] d.r janchor[] d.r jother[] d.'+
        'q[k rqzx[k jp[] k jprior[] k janchor[]]].q[k rqzx[k jp[] k jother[] k janchor[]]].')


def body_values(d,allowed=(False,False,False,False),variant='baseline'):
    v={x['name']:unknown for x in d['declarations'] if x['kind']=='primitive'}
    targets={'rqzr':('person','frame'),'rqzs':('person','frame','foot'),
        'rqzt':('person','frame','process'),'rqzk':('person','frame','foot','process')}
    def permits(source,person,role,description,bindings,polarity,scene):
        name=symbol(description)
        if name not in targets:return False
        wanted=list(targets[name])
        if variant=='other_carrier':wanted[1]='otherframe'
        if variant=='other_subject':wanted[0]='other'
        return allowed[tuple(targets).index(name)] and bindings.items==tuple(wanted) and (source,person,role,polarity,scene)==(
            'other' if variant=='other_source' else 'guards','person','other' if variant=='other_role' else 'role',
            variant!='negative_polarity','earlier' if variant=='other_permission_point' else 'prior')
    v.update(jp=lambda:'person',jprior=lambda:'prior',jother=lambda:'earlier',janchor=lambda:'actual',
        db=lambda:'guards',hztd=lambda:'role',qs=lambda person,point:'frame' if (person,point)==('person','actual') else 'otherframe',
        dd=lambda a,b:(a,b) in (('prior','actual'),('earlier','actual')),
        h7l=permits)
    if variant=='reverse_time':v['dd']=lambda a,b:(a,b)==('actual','prior')
    if variant=='other_anchor':v['janchor']=lambda:'elsewhere'
    return v


def body_checks():
    d=body_fixture();rows=[]
    for flags in product((False,True),repeat=4):
        actual=evaluate(d,body_values(d,flags),BODY_DOMAIN,BODY_TIMES)
        assert actual==[not any(flags),True],(flags,actual)
        rows.append(dict(allowed=flags,values=actual))
    contrasts={}
    for name in ('other_carrier','other_subject','other_source','other_role','negative_polarity','other_permission_point','reverse_time','other_anchor'):
        actual=evaluate(d,body_values(d,(True,True,True,True),name),BODY_DOMAIN,BODY_TIMES)
        expected=[True,False] if name=='other_permission_point' else [False,False] if name in ('reverse_time','other_anchor') else [True,True]
        assert actual==expected,(name,actual,expected);contrasts[name]=actual
    # The person, foot and process need not currently occur or have physical
    # attributes known to evaluate this normative depiction.
    for name in ('qs','dd','h7l'):
        v=body_values(d);v[name]=unknown
        try:evaluate(d,v,BODY_DOMAIN,BODY_TIMES)
        except ValueError as error:assert 'Unknown' in str(error)
        else:raise AssertionError(name)
    return dict(combinations=rows,contrasts=contrasts,unknown_inputs_refused=3,
        all_referential_individuals_quantified_without_occurrence_filter=True,
        apparatus_selected_at_anchor_held_at_prior_point=True,
        actual_body_and_attempt_relations_unknown=True,ordinary_evaluation=True)


def attribution_values(d,variant='baseline'):
    v={x['name']:unknown for x in d['declarations'] if x['kind']=='primitive'}
    def aligned(node,author,claim,target,depiction,context):
        wanted=dict(kind='call',symbol='hztr',arguments=[dict(kind='call',symbol='db',arguments=[])])
        if variant=='other_claim':wanted['symbol']='hztf'
        if variant=='other_claim_group':wanted['arguments'][0]['symbol']='mv'
        return (variant!='missing_alignment' and (node,author,context)==(
            'relative' if variant=='other_node' else 'clause','other' if variant=='other_author' else 'author',
            'elsewhere' if variant=='other_context' else 'context') and json.loads(claim.syntax)==wanted and
            symbol(target)==('rqzx' if variant=='reversed' else 'rqzw') and symbol(depiction)==('rqzw' if variant=='reversed' else 'rqzx'))
    v.update(hzsq=lambda:'clause',wa=lambda:'author',wh=lambda:'context',hzyb=aligned,
        qp=lambda:'livestock',hzst=lambda:'relative',dq=lambda:'previous',
        qa=lambda n,a,t,b,s:(n,a,symbol(t),symbol(b),s) in (
            ('livestock','author','qj','qk','context'),('relative','author','hztt','zbf','context'),('clause','author','eu','rqy4','context')),
        uc=lambda n,a,c,s:(n,a,symbol(c),s)==('clause','author','hztr','context'),
        ue=lambda a,b,s:(a,b,s)==('previous','clause','context'))
    return v


def attribution_checks():
    d=fixture(['rqzy'],'q[k rqzy[]].');domain=('clause','relative','livestock','previous','author','other');times=('context','elsewhere')
    rows={}
    for name in ('baseline','missing_alignment','other_claim','other_claim_group','other_node','other_author','other_context','reversed'):
        actual=evaluate(d,attribution_values(d,name),domain,times)
        assert actual==[name=='baseline'],(name,actual);rows[name]=actual
    # No world facts are supplied even for the complete five-statement excerpt.
    core=parse((ROOT/CORE).read_text(encoding='utf-8'))
    assert evaluate(core,attribution_values(core),domain,times)==[True]*5
    same=fixture(['rqzv','rqzw','hztr'],'r jnode[] a.r jauthor[] a.r jcontext[] d.'+
        'q[k rqzv[k jnode[] k jauthor[] r[k hztr[k db[]]] r[p rqzw] r[p rqzw] k jcontext[]]].')
    v={x['name']:unknown for x in same['declarations'] if x['kind']=='primitive'}
    v.update(jnode=lambda:'clause',jauthor=lambda:'author',jcontext=lambda:'context',hzyb=lambda *args:True)
    assert evaluate(same,v,domain,times)==[False]
    v=attribution_values(d);v['hzyb']=unknown
    try:evaluate(d,v,domain,times)
    except ValueError as error:assert 'Unknown' in str(error)
    else:raise AssertionError('Unknown alignment became an attribution')
    return dict(contrasts=rows,same_description_rejected=True,unknown_alignment_refused=True,
        five_excerpt_statements_executed=True,all_world_contents_unknown=True,
        source_and_depiction_not_asserted_or_equated=True,ordinary_evaluation=True)


def reading():
    prior=json.loads((ROOT/'data/walking-warning-reading-v1.json').read_text(encoding='utf-8'))
    clauses=deepcopy(prior['clauses'])
    for c in clauses:
        if c['id']=='minimal_step':
            c.update(definitions=['rqzg','rqzk','rqzn','rqzo','rqzp','rqzr','rqzs','rqzt','rqzu','rqzx','rqzy'],
                interpretation_ja='通常の一回の接地更新と外部着地を目標にし、足・過程の指定と未指定の四形への試みの不許容を、同じ先行局面の描写へ結ぶ。全歩容や任意の同義な目標の同一化は確認していない。',status='partial')
        if c['id']=='daring_permission':
            c.update(definitions=['hzs4','hztc','rqzw','rqzx','rqzy'],
                interpretation_ja='知的側の取り組みへの許容欠如と、四形の身体目標への取り組みの許容欠如を、同じ本人・先行時点・基準時点の位置で対応させる。両内容の真理は独立。',status='partial')
    paths=(INDEX,PARENT,PARENT_BASIS,FULL,BASIS,ANNOTATIONS,INVENTORY,'data/walking-warning-reading-v1.json',
        'data/quantified-step-goals-reading-v1.json','data/grounded-step-evidence-v1.json',
        'artifacts/first-cause-reading-v1/page-482.jpg')
    return dict(status='bodily_step_permission_connected_to_same_prior_stage',reviewer='assistant_review',
        decision='partial_source_depiction_adopted_whole_sentence_not_verified',document=FULL,meaning_basis=BASIS,
        source=prior['source'],clauses=clauses,selection=selection_binding(catalog(),SELECTION),
        interpretation_limits=LIMITS,source_review=prior['source_review'],
        remaining=['ruhigenの描写','jaの強調','歩行と家畜の語義範囲を含む一文全体','第二段落末尾と段落全体','二作品全文'],
        whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,
        new_verified_sentence_characters=0,semantic_equivalence_automatically_proved=False,
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in paths})


def structure():
    old,new=parent(),catalog()
    assert new.document['declarations'][:-5]==old.document['declarations']
    assert new.document['statements'][:-1]==old.document['statements'] and len(new.document['statements'])==48
    assert all(new.entries[n]==e for n,e in old.entries.items())
    assert set(new.entries)-set(old.entries)==set(MEANINGS)|set(PRIMITIVES)
    idx=json.loads((ROOT/INDEX).read_text(encoding='utf-8'))
    active=load_catalog(ROOT,idx['works']['kant-1784']['meaning_basis'])
    assert selection_binding(active,list(range(47)))==selection_binding(new,list(range(47)))
    for p in idx['works']['kant-1784']['reviews']:
        r=json.loads((ROOT/p).read_text(encoding='utf-8'));ids=[x['index'] for x in r['selection']['statements']]
        assert 47 not in ids and r['selection']==selection_binding(new,ids)
    for path,body in build().items():assert (ROOT/path).read_text(encoding='utf-8')==body
    for path in (FULL,CORE,LIBRARY):
        d=parse((ROOT/path).read_text(encoding='utf-8'))
        for style in ('full','compact'):
            text=format_graph(d,style);assert parse(text)==parse(transcribe(text,alphabet='v2'))==d
    r=reading();assert r==json.loads((ROOT/AUDIT).read_text(encoding='utf-8'));validate_hashes(ROOT,r['source_sha256'])
    assert ''.join(c['text'] for c in r['clauses'])==r['source']['text']
    assert [c['id'] for c in r['clauses'] if c['status']=='unresolved']==['quiet_creatures','emphasis']
    return dict(preserved_statements=47,new_statements=[47],new_definitions=4,new_primitives=1,
        preserved_review_selections=11,roundtrips=True,whole_sentence_verified=False)


def prepare():
    from scripts.audit_opening_scope import write_exact,encoded
    write_exact(ROOT/AUDIT,encoded(reading()))


def build_report():
    results={}
    for name,fn in [('embedding',embedding_checks),('target',target_checks),('body',body_checks),('attribution',attribution_checks),('structure',structure)]:
        results[name]=fn();print(name+' checked',flush=True)
    r=reading();unit=next(u for u in json.loads((ROOT/INVENTORY).read_text(encoding='utf-8'))['units'] if u['id']==r['source']['unit'])
    span=[1035,1114]
    paths=set(build())|set(catalog().source_sha256)|set(r['source_sha256'])|{AUDIT,DOC,
        'scripts/compose_step_depiction.py','scripts/check_step_depiction.py','scripts/register_step_depiction.py','tests/test_step_depiction.py',
        'scripts/compose_grounded_step.py','scripts/compose_falling_depiction.py','scripts/check_confinement_depiction.py',
        'scripts/check_prevented_attempt.py','scripts/check_pastoral_roles.py','scripts/check_motive_causes.py',
        'noema/constructed.py','noema/constructed_semantics.py','noema/meaning_catalog.py','noema/semantic_reviews.py',
        'noema/script.py','noema/first_order_proofs.py','noema/discourse.py','noema/grammar.py'}
    return dict(status='partial_bodily_permission_depiction_at_same_prior_stage',document=FULL,**results,
        alignment=dict(unit=unit['id'],unit_sha256=unit['text_sha256'],range=span,text=unit['text'][span[0]:span[1]],
            definitions=list(MEANINGS),status='explicit_interpretive_annotation'),
        whole_sentence_semantically_verified=False,new_verified_sentence_characters=0,new_covered_characters=0,
        verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})


def main():
    from scripts.audit_opening_scope import write_exact,encoded
    prepare();write_exact(ROOT/REPORT,encoded(build_report()))


if __name__=='__main__':main()
