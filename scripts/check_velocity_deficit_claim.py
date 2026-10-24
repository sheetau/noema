"""Check deficit arithmetic, universal scope and the same explanation chain."""
from functools import lru_cache
from fractions import Fraction as Q
from xml.etree import ElementTree as ET
import json,re
from noema.grammar import parse,format_graph,number_word
from noema.extraction import extract_document
from noema.finite_semantics import Content,evaluate_document
from noema.semantics import SemanticError
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.check_coordinate_correspondence import abstract
from scripts.check_moving_trip_geometry import NUM,norm_factory
from scripts.check_material_relative_frame import RS
from scripts.check_clock_site_time import relation,perturb,unknowns,forbidden
from scripts.check_translated_light_trial import expose
from scripts.check_velocity_composition_claim import arithmetic
from scripts.compose_velocity_deficit_claim import ROOT,read,PARENT_BASIS,FULL,CORE,BASIS,ANNOTATIONS,INDICES,MEANINGS,build

DOC='docs/velocity-deficit-claim-v1.md';SOURCE='data/einstein-velocity-deficit-source-reading-v1.json'
INVENTORY='artifacts/written-units-v1/einstein-1905.json';READING='data/einstein-velocity-axial-source-reading-v1.json'
PRIORS=tuple(f'data/einstein-velocity-axial-u{n:04d}-review-v1.json' for n in (141,142))
DEPENDENCIES=('reports/velocity-axial-claim-v1.json','reports/speed-deficits-v1.json')
CONSTANTS={'rd':'author','eirf':'paper','ri':'discourse','eisoq':'fifth','zb6':'context','zlf':'axial','zli':'general','zlj':'substitution','zlk':'local','zll':'argument'}
DOMAIN=tuple(CONSTANTS.values())+('other',);POINTS=('context','discourse','other')

@lru_cache(None)
def core():return parse(read(CORE))

@lru_cache(None)
def fixture(name,mode='boundary'):
    doc=extract_document(core(),roots=[name],statement_indices=[]).document
    bounds=NUM|{'sjd','sjt','sky','ejpa'}
    if name in ('ejpv','ejpw') and mode!='native':bounds|={'s4a','s3w'}
    if name=='s3u' and mode=='binding':bounds|={'s3t','s3g','s3s','s3j'}
    if name=='s3v' and mode=='binding':bounds.add('s3u')
    abstract(doc,bounds);doc=extract_document(doc,roots=[name],statement_indices=[]).document
    d=next(d for d in doc['declarations'] if d['name']==name)
    if name in ('s3v','s4a') and mode in ('instance','binding'):assert len(expose(d,{'forall'},only_sort=RS))==2
    slots=[]
    for i,p in enumerate(d['parameters']):
        n='jvdc'+number_word(i);slots.append(n);doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']))
    expr=dict(kind='call',symbol=name,arguments=[dict(kind='call',symbol=n,arguments=[]) for n in slots])
    if d['result']=='content':
        doc['declarations'].append(dict(kind='primitive',name='jvdcpoint',parameters=[],result='situation'));expr=dict(kind='evaluate',content=expr,situation=dict(kind='call',symbol='jvdcpoint',arguments=[]))
    doc['statements']=[dict(kind='ask',body=expr)];return doc,slots

def run(name,args,m,mode='boundary'):
    doc,slots=fixture(name,mode);assert len(args)==len(slots),(name,len(args),len(slots))
    mm={n:lambda x=x:x for n,x in CONSTANTS.items()}|{'jvdcpoint':lambda:'discourse'}|m|{n:lambda x=x:x for n,x in zip(slots,args)}
    return evaluate_document(doc,individuals=DOMAIN,situations=POINTS,primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=500000,memoize_definitions=True,memoize_expressions=True)[0]['value']

@lru_cache(None)
def numeric_checks():
    count=0
    shortfalls=((5,3,2,True,True),(5,0,5,False,True),(5,5,0,False,False),(5,-1,6,False,False),(5,6,-1,False,False),(5,3,1,False,True),(1,Q(99,100),Q(1,100),True,True),(0,0,0,False,False))
    quotients=((5,2,4,Q(25,7),True,True),(5,4,2,Q(25,7),True,True),(5,1,1,Q(200,41),True,True),(1,Q(1,100),Q(1,100),Q(19800,19801),True,True),(5,2,4,1,False,True),(5,2,4,5,False,False),(5,0,4,5,False,False),(5,5,4,1,False,True),(5,5,5,0,False,True),(5,-1,4,Q(175,31),False,False),(0,0,0,0,False,False),(-5,2,4,0,False,False))
    for undefined in (0,17):
        cuts,m=arithmetic(undefined);c=lambda x:cuts.make(Q(x))
        for V,a,g,gap,bound in shortfalls:
            assert run('s3o',list(map(c,(V,a,g))),m)==gap
            assert run('s3s',list(map(c,(V,a))),m)==bound;count+=2
        for V,g,h,U,equal,below in quotients:
            assert run('s3r',list(map(c,(V,g,h,U))),m)==equal
            # The native source content must retain BOTH the equation and U<V.
            mm=m|{n:lambda x=x:c(x) for n,x in zip(('tc','zlg','zlh','zkp'),(V,g,h,U))}
            assert run('s3y',[],mm)==(equal and below);count+=2
        assert not run('s3o',list(map(c,(5,3,2))),m|{'ba':lambda *xs:False})
        assert not run('s3r',list(map(c,(5,2,4,Q(25,7)))),m|{'ba':lambda *xs:False});count+=2
    unknowns(lambda mm:run('s3r',list(map(c,(5,2,4,Q(25,7)))),mm),m,('ba','sca','sjd','sjt'))
    return dict(cases=count,native_strict_shortfalls_and_substituted_quotient=True,zero_velocity_not_in_strict_deficit_argument=True,equation_not_replaced_by_upper_bound=True,invalid_domain_under_two_off_guard_values=True)

@lru_cache(None)
def universal_checks():
    cuts,m=arithmetic();c=lambda x:cuts.make(Q(x));norm=norm_factory(cuts,());count=0
    cases=((5,3,1,True),(5,0,1,True),(5,1,0,True),(5,0,0,True),(1,Q(99,100),Q(99,100),True),(5,5,1,False),(5,6,1,False),(5,-1,3,False),(0,0,0,False))
    for V,a,b,domain in cases:
        mm=m|{'tc':lambda:c(V)}
        assert run('s3t',list(map(c,(V,a,b))),mm)==domain
        assert run('s3u',list(map(c,(V,a,b))),mm)
        assert run('s3v',list(map(c,(V,a,b))),mm,'instance')==(V>0)
        assert run('s4a',list(map(c,(a,b))),mm,'instance')==(V>0);count+=4
    rows={'s3t':{(Q(5),Q(3),Q(1))},'s3g':{(Q(5),Q(3),Q(1),Q(25,7))},'s3s':{(Q(5),Q(25,7))}}
    mm=m|{n:lambda *xs,rs=rs:norm(xs) in rs for n,rs in rows.items()}|{'s3j':lambda V,a,b:c(Q(25,7))}
    assert run('s3u',list(map(c,(5,3,1))),mm,'binding');count+=1
    # A false domain makes implication true; missing output validity/bound must fail.
    for n in ('s3g','s3s'):
        count+=perturb(lambda pp:run('s3u',list(map(c,(5,3,1))),pp,'binding'),mm,{n:rows[n]},norm)
    assert run('s3u',list(map(c,(5,3,1))),mm|{'s3t':lambda *xs:False},'binding');count+=1
    assert not run('s3u',list(map(c,(5,3,1))),mm|{'s3j':lambda *xs:c(0)},'binding');count+=1
    unknowns(lambda pp:run('s3u',list(map(c,(5,3,1))),pp,'binding'),mm,('s3t','s3g','s3s','s3j'))
    rows={'s3u':{(Q(5),Q(3),Q(1))}};mm=m|{'s3u':lambda *xs:norm(xs) in rows['s3u']}
    count+=perturb(lambda pp:run('s3v',list(map(c,(5,3,1))),pp,'binding'),mm,rows,norm)
    for name,boundary in (('ejpv','s4a'),('ejpw','s3w')):
        mm=m|{'ejpa':lambda ctx:ctx=='context',boundary:lambda:Content(POINTS,(True,True,True))}
        assert run(name,[],mm);count+=1
        for patch in ({'ejpa':lambda ctx:False},{'zb6':lambda:'other'},{boundary:lambda:Content(POINTS,(True,False,True))}):
            assert not run(name,[],mm|patch);count+=1
        unknowns(lambda pp:run(name,[],pp),mm,('ejpa',boundary))
    mm=m|{'tc':lambda:c(5),'ejpa':lambda ctx:ctx=='context'}
    for name,args in (('s3v',[c(5)]),('s4a',[]),('ejpv',[]),('ejpw',[])):
        try:run(name,args,mm,'native')
        except SemanticError as e:assert str(e)=='Cannot finitely quantify the rational number domain',str(e)
        else:raise AssertionError('Universal real inputs silently sampled')
    return dict(cases=count,both_real_input_slots_and_light_bound=True,constructed_result_must_satisfy_relation_and_strict_bound=True,zero_input_boundary_separate_from_strict_deficits=True,outer_current_reference_does_not_restrict_quantification=True,native_all_real_enumeration_refused=True)

@lru_cache(None)
def physical_checks():
    cuts,m=arithmetic();c=lambda x:cuts.make(Q(x));count=0
    base=m|{n:lambda x=x:c(x) for n,x in zip(('tc','zb7','zkq','zlg','zlh','zkp','zkc','zkd'),(5,3,1,2,4,Q(25,7),1,0))}|{'ejpa':lambda ctx:ctx=='context'}
    rows={'ejpa':{('context',)}}
    for name in ('ejpx','ejpy','ejpz'):
        count+=perturb(lambda pp:run(name,[],pp),base,rows)
        assert not run(name,[],base|{'zb6':lambda:'other'});count+=1
    cases=(({},(True,True,True)),({'zlg':4,'zlh':2},(False,False,True)),({'zkq':2},(False,False,True)),({'zkp':1},(True,False,False)),({'zb7':0,'zlg':5,'zkp':1},(False,False,False)),({'zb7':5,'zlg':0,'zkp':5},(False,False,False)),({'tc':6},(False,False,False)),({'zkc':-1},(True,False,True)),({'zkd':1},(True,False,True)))
    for patch,expected in cases:
        mm=base|{n:lambda x=x:c(x) for n,x in patch.items()}
        actual=tuple(run(n,[],mm) for n in ('ejpx','ejpy','ejpz'));assert actual==expected,(patch,actual);count+=3
    unknowns(lambda pp:run('ejpy',[],pp),base,('ejpa','tc','zb7','zkq','zlg','zlh','zkp','zkc','zkd'))
    unknowns(lambda pp:run('ejpz',[],pp),base,('ejpa','tc','zlg','zlh','zkp'))
    return dict(cases=count,same_physical_acquisition_context_and_scalar_references=True,swapped_deficits_not_accepted_as_same_substitution=True,preceding_positive_direction_and_equation_preserved=True,source_equation_and_inequality_both_required=True,current_derivative_acquisition_is_pinned_prior_boundary=True)

@lru_cache(None)
def presentation_checks():
    groups=(('ejp2',{'zc':{('general','author','ejpv','ejpw','fifth','discourse')}}),('ejp3',{'ug':{('substitution','author','ejpx','local','discourse')}}),('ejp4',{'zc':{('argument','author','ejpy','ejpz','local','discourse')}}),('ejp5',{'zfr':{('argument','author','ejpw','discourse','fifth')}}),('ejqc',{'eir3':{('general','author','paper','ejp6','discourse')},'ue':{('axial','general','discourse')}}),('ejqd',{'eir3':{('substitution','author','paper','ejp7','discourse')},'ue':{('general','substitution','discourse')}}),('ejqe',{'eir3':{('argument','author','paper','ejqa','discourse')},'ue':{('substitution','argument','discourse')}}),('ejqf',{'eir3':{('argument','author','paper','ejqb','discourse')}}))
    count=0
    for name,rows in groups:
        mm={n:relation(rs) for n,rs in rows.items()};count+=perturb(lambda pp:run(name,[],pp),mm,rows)
        assert run(name,[],mm|{n:forbidden for n in ('ejpv','ejpw','ejpx','ejpy','ejpz','ejpa','s3v','s3r')});count+=1
    for name,patch in (('ejqc',{'zli':lambda:'axial'}),('ejqd',{'zlj':lambda:'general'}),('ejqe',{'zll':lambda:'substitution'})):
        assert not run(name,[],{'eir3':lambda *xs:True,'ue':lambda *xs:True}|patch);count+=1
    return dict(cases=count,general_inference_local_assumption_and_explanation_distinct=True,namely_targets_same_general_claim=True,same_author_paper_scope_and_stage=True,ordered_previous_equation_claim_assumption_display=True,quoted_argument_not_certified_valid=True)

@lru_cache(None)
def source_record():
    inv=json.loads(read(INVENTORY));math={m['id']:m for m in inv['math']};old=json.loads(read(READING));validate_hashes(ROOT,old['source_sha256'])
    flat=lambda xml:re.sub(r'\s','',''.join(ET.fromstring(xml).itertext()))
    expected=dict(zip((f'M{n:04d}' for n in range(264,272)),('V','V','v=V−ϰ','w=V−λ','ϰ','λ','V','U=V2V−ϰ−λ2V−ϰ−λ+ϰλV<V.')))
    segments=[]
    for u in inv['units'][142:144]:
        assert digest(u['text'].encode())==u['text_sha256'];entries=[]
        for n in u['math_ids']:
            e=math[n];assert digest(e['mathml'].encode())==e['sha256'] and flat(e['mathml'])==expected[n]
            entries.append(dict(id=n,sha256=e['sha256'],mathml_flat=flat(e['mathml'])))
        segments.append(dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[0,len(u['text'])],text=u['text'],source_nonblank_characters=len(re.sub(r'\s|\[M\d+\]','',u['text'])),math=entries))
    ns='{http://www.w3.org/1998/Math/MathML}';root=ET.fromstring(math['M0271']['mathml']);fr=list(root.iter(ns+'mfrac'))
    assert len(fr)==2 and flat(ET.tostring(fr[0][0],encoding='unicode'))=='2V−ϰ−λ' and flat(ET.tostring(fr[1][0],encoding='unicode'))=='ϰλ' and flat(ET.tostring(fr[1][1],encoding='unicode'))=='V'
    assert segments[0]['text'].startswith('Aus dieser Gleichung folgt, daß ') and 'stets' in segments[0]['text'] and 'Setzt man nämlich' in segments[0]['text'] and segments[0]['text'].endswith('so ist:')
    paths={INVENTORY,DOC,READING,*old['source_sha256'],'reports/written-units-v1.json','artifacts/written-facsimiles-v1/einstein-1905-p906.jpg'}
    return dict(version='einstein-velocity-deficit-source-reading-v1',reviewer='assistant_visual_and_text_review',pages=['906'],segments=segments,observations=['原刊906頁の前の式からの帰結、常にという全称、Setzt man nämlichの仮定と説明、双方の不足量の正性と厳密上限を通読した。','v=V−κ、w=V−λ、V*(2V−κ−λ)/(2V−κ−λ+κλ/V)とU<Vを、係数・符号・分数・等号と不等号・句点まで照合した。電子転記のϰは同じ不足量への既存参照を使い、原データを訂正しない。','一般主張は0≤v,w<Vという既存の読みを維持するが、原文の厳密な不足条件は零速度を含めない。その差を残した論証の著者帰属である。','同じ点の現在量と同方向の式を保持し、局所の仮定・帰結・先の一般主張への論証提示を区別した。'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert len(new.document['statements'])==len(old.document['statements'])==356
    assert [i for i,(a,b) in enumerate(zip(old.document['statements'],new.document['statements'])) if a!=b]==list(INDICES)
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations'];assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    for p,selection in zip(PRIORS,([136,137,138],[138])):
        prior=json.loads(read(p));validate_hashes(ROOT,prior['source_sha256']);assert selection_binding(new,selection)==prior['selection']
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    load_annotations(ROOT,BASIS,ANNOTATIONS);assert json.loads(read(ANNOTATIONS))['entries']==json.loads(read('data/velocity-axial-claim-identifiers-v1.json'))['entries']
    names={d['name'] for d in core()['declarations']}
    assert {'s3o','s3q','s3r','s3s','s3t','s3u','s3v','s3w','s3x','s3y','s4a','s3g','s3j','ejpa','ejpp','ejpq','ejoi','ejoj','ejow','ejny','ejm2','sede','sedi'}<=names
    assert not {'s3c','s3k','s3l','s3m','s3z','syw','szs','szt','zke'}&names
    assert not [d for d in new.document['declarations'][len(old.document['declarations']):] if d['kind']=='primitive']
    for style in ('compact','full'):
        body=format_graph(core(),style);assert parse(body)==parse(transcribe(body,alphabet='v2'))==core()
    assert source_record()==json.loads(read(SOURCE))
    return dict(new_definitions=len(MEANINGS),new_primitives=0,replaced_partial_statements=list(INDICES),other_statements_preserved=352,prior_judgments_preserved=True,old_arithmetic_and_meanings_unchanged=True,current_explanation_no_legacy_physical_premise=True,later_s5m_update_deferred_to_u0147=True)

def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/SOURCE,json.dumps(source_record(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    results={n:f() for n,f in [('numeric',numeric_checks),('universal',universal_checks),('physical',physical_checks),('presentation',presentation_checks),('structure',structure_checks)]}
    helpers=('compose_velocity_axial_claim','compose_material_relative_frame','compose_relativity_conjecture','compose_two_postulates','compose_limits','check_clock_site_time','check_moving_trip_geometry','check_material_relative_frame','check_coordinate_correspondence','check_velocity_composition_claim','check_translated_light_trial','check_rod_methods','audit_opening_scope')
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(source_record()['source_sha256'])|{SOURCE,DOC,*PRIORS,*DEPENDENCIES,'scripts/compose_velocity_deficit_claim.py','scripts/check_velocity_deficit_claim.py','tests/test_velocity_deficit_claim.py',*(f'scripts/{n}.py' for n in helpers)}
    alignment=dict(segments=[dict(unit=s['unit'],unit_sha256=s['unit_sha256'],range=s['range'],source=s['text'],statements=selection,definitions=list(MEANINGS),status='explicit_interpretive_annotation') for s,selection in zip(source_record()['segments'],([139,140,141,142],[140,141,142]))])
    return dict(status='universal_sublight_consequence_and_strict_deficit_explanation_connected',document=FULL,**results,alignment=alignment,verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,remaining=['u0143–u0144の全単位意味判断','u0145以降とu0147の旧前提の更新'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
