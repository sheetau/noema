"""Check native symmetry, appraisal, directed motion and scalar consequence."""
from functools import lru_cache
from fractions import Fraction as Q
from xml.etree import ElementTree as ET
import json,re
from noema.grammar import parse,format_graph,number_word
from noema.extraction import extract_document
from noema.finite_semantics import FunctionValue,evaluate_document
from noema.semantics import SemanticError
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.check_coordinate_correspondence import abstract
from scripts.check_moving_trip_geometry import NUM
from scripts.check_material_relative_frame import RS
from scripts.check_clock_site_time import relation,perturb,unknowns,forbidden
from scripts.check_calculation_discourse import symbol
from scripts.check_translated_light_trial import expose
from scripts.check_velocity_composition_claim import arithmetic
from scripts.compose_velocity_axial_claim import ROOT,read,PARENT_BASIS,FULL,CORE,BASIS,ANNOTATIONS,INDICES,MEANINGS,build

DOC='docs/velocity-axial-claim-v1.md';SOURCE='data/einstein-velocity-axial-source-reading-v1.json'
INVENTORY='artifacts/written-units-v1/einstein-1905.json';READING='data/einstein-velocity-composition-source-reading-v1.json'
PRIORS=tuple(f'data/einstein-velocity-composition-u{n:04d}-review-v1.json' for n in (139,140))
DEPENDENCIES=('reports/velocity-composition-claim-v1.json','reports/calculation-discourse-v1.json','reports/axial-composition-v1.json')
CONSTANTS={'rd':'author','eirf':'paper','ri':'discourse','eisoq':'fifth','zb6':'context','zkw':'formula','zky':'symmetry','zlf':'axial'}
DOMAIN=tuple(CONSTANTS.values())+('other',);POINTS=('context','discourse','other')

@lru_cache(None)
def core():return parse(read(CORE))

@lru_cache(None)
def fixture(name,mode='boundary'):
    doc=extract_document(core(),roots=[name],statement_indices=[]).document
    bounds=NUM|{'sjd','sjt','sky','ejpa'}
    if name in ('s3b','ejpl') and mode!='native':bounds.add('s3a')
    abstract(doc,bounds);doc=extract_document(doc,roots=[name],statement_indices=[]).document
    d=next(d for d in doc['declarations'] if d['name']==name)
    if name=='s3a' and mode=='instance':assert len(expose(d,{'forall'},only_sort=RS))==3
    slots=[]
    for i,p in enumerate(d['parameters']):
        n='jvac'+number_word(i);slots.append(n);doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']))
    expr=dict(kind='call',symbol=name,arguments=[dict(kind='call',symbol=n,arguments=[]) for n in slots])
    if d['result']=='content':
        doc['declarations'].append(dict(kind='primitive',name='jvacpoint',parameters=[],result='situation'));expr=dict(kind='evaluate',content=expr,situation=dict(kind='call',symbol='jvacpoint',arguments=[]))
    doc['statements']=[dict(kind='ask',body=expr)];return doc,slots

def run(name,args,m,mode='boundary'):
    doc,slots=fixture(name,mode);assert len(args)==len(slots)
    mm={n:lambda x=x:x for n,x in CONSTANTS.items()}|{'jvacpoint':lambda:'discourse'}|m|{n:lambda x=x:x for n,x in zip(slots,args)}
    return evaluate_document(doc,individuals=DOMAIN,situations=POINTS,primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=500000,memoize_definitions=True,memoize_expressions=True)[0]['value']

@lru_cache(None)
def numeric_checks():
    cases=((5,3,1,Q(25,7),True),(5,3,-1,Q(25,11),True),(5,1,-3,Q(-25,11),True),(5,1,-3,Q(25,11),False),(5,-3,-1,Q(-25,7),True),(5,3,-3,0,True),(5,0,3,3,True),(5,3,0,3,True),(5,0,0,0,True),(5,3,-25,11,True),(5,3,Q(-25,3),0,False),(5,5,1,5,True),(5,6,1,Q(175,31),True),(0,3,1,4,False),(-5,3,1,Q(25,7),False),(5,3,1,4,False))
    count=0
    for undefined in (0,17):
        cuts,m=arithmetic(undefined);c=lambda x:cuts.make(Q(x))
        for *values,expected in cases:
            assert run('s3g',list(map(c,values)),m)==expected,values;count+=1
        assert not run('s3g',list(map(c,(5,3,1,Q(25,7)))),m|{'ba':lambda *xs:False});count+=1
    unknowns(lambda mm:run('s3g',list(map(c,(5,3,1,Q(25,7)))),mm),m,('ba','sca','sjt','sjd'))
    for x,y,w,axis,direction in ((3,0,3,True,True),(-3,0,3,True,False),(0,0,0,True,False),(0,3,3,False,False),(3,4,5,False,False),(3,0,4,True,False),(3,0,-3,True,False)):
        assert run('s3h',list(map(c,(x,y))),m)==axis
        assert run('s3i',list(map(c,(x,y,w))),m)==direction;count+=2
    return dict(cases=count,signed_formula_native=True,zero_formula_inputs_not_a_direction=True,reverse_axis_motion_not_positive_direction=True,domain_guards_under_two_off_guard_values=True)

@lru_cache(None)
def symmetry_checks():
    cuts,m=arithmetic();c=lambda x:cuts.make(Q(x));r=cuts.read;count=0
    # Expose only the three outer quantifiers, to test bindings, not universality.
    rel=FunctionValue((RS,RS,RS),'truth',lambda a,b,u:r(u)==2*r(a)+r(b))
    dom=FunctionValue((RS,RS),'truth',lambda a,b:r(a)>=0 and r(b)>=0)
    for a,b,u,expected in ((1,2,4,False),(1,2,5,False),(1,2,6,True),(2,1,5,False),(2,2,6,True),(-1,2,0,True),(1,-2,0,True)):
        assert run('s3a',[rel,dom,c(a),c(b),c(u)],{},'instance')==expected;count+=1
    samples=((5,1,0),(5,-1,0),(5,Q(3,5),Q(4,5)))
    for V,co,si in samples:
        angle=FunctionValue(('truth',),RS,lambda t:c(co if t else si))
        def sampled(relation,domain):
            nonlocal count
            for a,b in ((3,1),(1,3),(0,3),(-1,3),(3,-1),(128,1)):
                assert domain(c(a),c(b))==(a>=0 and b>=0);count+=1
            # Values are rational-square witnesses; comparison does not certify all reals.
            for a,b,u in ((3,5,5),(3,5,0),(3,5,20),(0,3,3),(0,3,4)):
                expected=run('s2t',list(map(c,(V,a,b,co,si,u))),m)
                assert relation(c(a),c(b),c(u))==expected
                assert relation(c(b),c(a),c(u))==expected;count+=2
            return True
        mm=m|{'tc':lambda:c(V),'zkt':lambda:angle,'s3a':sampled,'ejpa':lambda ctx:ctx=='context'}
        assert run('ejpl',[],mm);count+=1
        for patch in ({'ejpa':lambda ctx:False},{'zb6':lambda:'other'},{'s3a':lambda *xs:False}):
            # Avoid recounting callback probes for negative outer-guard checks.
            assert not run('ejpl',[],mm|{'s3a':lambda *xs:True}|patch);count+=1
    simple=m|{'tc':lambda:c(5),'zkt':lambda:FunctionValue(('truth',),RS,lambda t:c(1 if t else 0)),'ejpa':lambda ctx:ctx=='context','s3a':lambda *xs:True}
    for patch in ({'tc':lambda:c(0)},{'tc':lambda:c(-5)},{'zkt':lambda:FunctionValue(('truth',),RS,lambda t:c(1))}):
        assert not run('ejpl',[],simple|patch);count+=1
    unknowns(lambda mm:run('ejpl',[],mm),simple,('ejpa','s3a','tc','zkt'))
    for name in ('s3a','ejpl'):
        try:run(name,[rel,dom] if name=='s3a' else [],simple,'native')
        except SemanticError as e:assert 'Cannot finitely quantify the rational number domain'==str(e),str(e)
        else:raise AssertionError('All-real symmetry silently sampled')
    return dict(cases=count,all_three_universal_slots_tested=True,nonnegative_input_exchange_with_fixed_light_and_angle=True,current_quantities_bound=True,native_unbounded_real_enumeration_rejected=True,sampled_callback_not_a_universal_proof=True)

@lru_cache(None)
def appraisal_checks():
    m={'zld':lambda subject,ctx:Q(8 if (symbol(subject),ctx)==('ejpl','discourse') else 2),'zle':lambda degree,ctx:ctx=='discourse' and degree>=5}
    assert run('ejpm',[],m);count=1
    for patch in ({'zld':lambda subject,ctx:Q(2)},{'zld':lambda subject,ctx:Q(8 if symbol(subject)=='s3b' else 2)},{'zld':lambda subject,ctx:Q(8 if symbol(subject)=='ejpq' else 2)},{'zle':lambda degree,ctx:degree>=9},{'jvacpoint':lambda:'other'},{'zle':lambda degree,ctx:ctx=='other'}):
        assert not run('ejpm',[],m|patch);count+=1
    unknowns(lambda mm:run('ejpm',[],mm),m,('zld','zle'))
    assert run('ejpm',[],m|{n:forbidden for n in ('ejpl','ejpa','s3a','s3b','s2t')});count+=1
    return dict(cases=count,same_description_and_context_for_value_and_standard=True,no_fixed_threshold_or_actual_reader_reaction=True,quoted_symmetry_not_executed_as_truth=True)

@lru_cache(None)
def physical_checks():
    cuts,m=arithmetic();c=lambda x:cuts.make(Q(x));count=0
    rows={'ejpa':{('context',)}}
    base=m|{'tc':lambda:c(5),'zb7':lambda:c(3),'zkc':lambda:c(1),'zkd':lambda:c(0),'zkq':lambda:c(1),'zkp':lambda:c(Q(25,7)),'ejpa':lambda ctx:ctx=='context'}
    for name in ('ejpp','ejpq'):
        count+=perturb(lambda mm:run(name,[],mm),base,rows)
        assert not run(name,[],base|{'zb6':lambda:'other'});count+=1
    # Boundary ejpa witnesses are not assertions that off-setting physical worlds exist.
    cases=(({},True,True,True),({'zkc':lambda:c(-1)},False,True,True),({'zkc':lambda:c(0),'zkq':lambda:c(0),'zkp':lambda:c(3)},False,True,True),({'zkd':lambda:c(1)},False,True,True),({'zkp':lambda:c(4)},True,False,False),({'zkq':lambda:c(2)},False,False,True),({'ejpa':lambda ctx:False},False,False,True))
    for patch,premise,result,conditional in cases:
        mm=base|patch
        assert run('ejpp',[],mm)==premise
        assert run('ejpq',[],mm)==result
        assert run('ejpr',[],mm)==conditional;count+=3
    for n in ('tc','zb7','zkq','zkp'):
        assert not run('ejpq',[],base|{n:lambda:c(0)});count+=1
    unknowns(lambda mm:run('ejpp',[],mm),base,('ejpa','zkc','zkd','zkq'))
    unknowns(lambda mm:run('ejpq',[],mm),base,('ejpa','tc','zb7','zkq','zkp'))
    return dict(cases=count,same_current_context_and_four_scalar_arguments=True,native_positive_direction_separate_from_signed_formula=True,false_premise_implication_not_an_actual_derivation=True,current_physical_acquisition_boundary_checked_in_pinned_prior=True)

@lru_cache(None)
def presentation_checks():
    count=0
    for name,rows in (('ejpn',{'uh':{('symmetry','author','ejpl','fifth','discourse')},'ue':{('formula','symmetry','discourse')}}),('ejpo',{'uh':{('symmetry','author','ejpm','fifth','discourse')}}),('ejps',{'zc':{('axial','author','ejpp','ejpq','fifth','discourse')}}),('ejpu',{'eir3':{('axial','author','paper','ejpt','discourse')},'ue':{('symmetry','axial','discourse')}})):
        mm={n:relation(rs) for n,rs in rows.items()};count+=perturb(lambda mm:run(name,[],mm),mm,rows)
        assert run(name,[],mm|{n:forbidden for n in ('ejpl','ejpm','ejpp','ejpq','ejpr','ejpa','s3a','s3g')});count+=1
    for name,patch in (('ejpn',{'zky':lambda:'formula'}),('ejpu',{'zlf':lambda:'symmetry'})):
        assert not run(name,[],{n:lambda *xs:True for n in ('uh','ue','eir3')}|patch);count+=1
    return dict(cases=count,same_author_scope_content_context=True,order_formula_symmetry_conditional_display=True,premise_and_conclusion_not_reversed=True,quoted_consequence_not_certified_true=True)

@lru_cache(None)
def source_record():
    inv=json.loads(read(INVENTORY));math={m['id']:m for m in inv['math']};old=json.loads(read(READING));validate_hashes(ROOT,old['source_sha256'])
    flat=lambda xml:re.sub(r'\s','',''.join(ET.fromstring(xml).itertext()))
    expected=dict(zip(('M0258','M0259','M0260','M0261','M0262','M0263'),('v','w','w','X','Ξ','U=v+w1+vwV2.')))
    segments=[]
    for u in inv['units'][140:142]:
        assert digest(u['text'].encode())==u['text_sha256'];entries=[]
        for n in u['math_ids']:
            e=math[n];assert digest(e['mathml'].encode())==e['sha256'];assert flat(e['mathml'])==expected[n]
            entries.append(dict(id=n,sha256=e['sha256'],mathml_flat=flat(e['mathml'])))
        segments.append(dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[0,len(u['text'])],text=u['text'],source_nonblank_characters=len(re.sub(r'\s|\[M\d+\]','',u['text'])),math=entries))
    ns='{http://www.w3.org/1998/Math/MathML}';root=ET.fromstring(math['M0263']['mathml']);fractions=list(root.iter(ns+'mfrac'))
    assert len(fractions)==2 and flat(ET.tostring(fractions[0][0],encoding='unicode'))=='v+w' and flat(ET.tostring(fractions[1][0],encoding='unicode'))=='vw' and flat(ET.tostring(fractions[1][1],encoding='unicode'))=='V2'
    assert segments[0]['text'].startswith('Es ist bemerkenswert, daß ') and '. Hat auch ' in segments[0]['text'] and segments[0]['text'].endswith('so erhalten wir:')
    paths={INVENTORY,DOC,READING,*old['source_sha256'],'reports/written-units-v1.json','artifacts/written-facsimiles-v1/einstein-1905-p906.jpg'}
    return dict(version='einstein-velocity-axial-source-reading-v1',reviewer='assistant_visual_and_text_review',pages=['906'],segments=segments,observations=['原刊906頁で対称性と注目価値の文、Hat auchの正方向条件、括弧内のΞ軸、コロンと表示式を通読した。','M0258–M0262のv/w/w/X/ΞとM0263の二重分数、分子v+w、内側分子vw、Vの二乗、等号と句点を照合した。M0263には転記訂正を加えない。','対称性は数値入力の交換、bemerkenswertは同じ性質への注意価値、Richtungは既存の正方向への非零運動の読みを明示する。','式だけの零入力と物理的な方向条件を区別し、点の光速上限を先取りしない。帰結の著者帰属と無条件な真理を同一視しない。'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert len(new.document['statements'])==len(old.document['statements'])==356
    assert [i for i,(a,b) in enumerate(zip(old.document['statements'],new.document['statements'])) if a!=b]==list(INDICES)
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations'];assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    for p,selection in zip(PRIORS,([132,133,134,135],[133,134,135])):
        prior=json.loads(read(p));validate_hashes(ROOT,prior['source_sha256']);assert selection_binding(new,selection)==prior['selection']
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    load_annotations(ROOT,BASIS,ANNOTATIONS);assert json.loads(read(ANNOTATIONS))['entries']==json.loads(read('data/velocity-composition-claim-identifiers-v1.json'))['entries']
    names={d['name'] for d in core()['declarations']}
    assert {'s3a','s3b','s2z','s3g','s3i','s3j','ejpa','ejoi','ejoj','ejow','ejny','ejm2','sede','sedi'}<=names
    assert not {'s3c','s3e','s3k','s3l','s3m','syw','szs','szt','zke'}&names
    assert not [d for d in new.document['declarations'][len(old.document['declarations']):] if d['kind']=='primitive']
    for style in ('compact','full'):
        body=format_graph(core(),style);assert parse(body)==parse(transcribe(body,alphabet='v2'))==core()
    assert source_record()==json.loads(read(SOURCE))
    return dict(new_definitions=len(MEANINGS),new_primitives=0,replaced_partial_statements=list(INDICES),other_statements_preserved=353,prior_judgments_preserved=True,legacy_math_and_meanings_unchanged=True,current_selection_has_no_legacy_physical_premise=True,later_s5m_update_deferred_to_u0147=True)

def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/SOURCE,json.dumps(source_record(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    results={n:f() for n,f in [('numeric',numeric_checks),('symmetry',symmetry_checks),('appraisal',appraisal_checks),('physical',physical_checks),('presentation',presentation_checks),('structure',structure_checks)]}
    helpers=('compose_velocity_composition_claim','compose_material_relative_frame','compose_relativity_conjecture','compose_two_postulates','compose_limits','check_clock_site_time','check_moving_trip_geometry','check_material_relative_frame','check_coordinate_correspondence','check_calculation_discourse','check_velocity_composition_claim','check_translated_light_trial','check_rod_methods','audit_opening_scope')
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(source_record()['source_sha256'])|{SOURCE,DOC,*PRIORS,*DEPENDENCIES,'scripts/compose_velocity_axial_claim.py','scripts/check_velocity_axial_claim.py','tests/test_velocity_axial_claim.py',*(f'scripts/{n}.py' for n in helpers)}
    alignment=dict(segments=[dict(unit=s['unit'],unit_sha256=s['unit_sha256'],range=s['range'],source=s['text'],statements=selection,definitions=list(MEANINGS),status='explicit_interpretive_annotation') for s,selection in zip(source_record()['segments'],([136,137,138],[138]))])
    return dict(status='symmetry_appraisal_and_directed_axial_consequence_connected',document=FULL,**results,alignment=alignment,verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,remaining=['u0141–u0142の全単位意味判断','u0143以降とu0147の旧前提の更新'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
