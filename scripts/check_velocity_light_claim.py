"""Check printed quotient, fixed point and a sublight-frame physical application."""
from functools import lru_cache
from fractions import Fraction as Q
from xml.etree import ElementTree as ET
import json,re
from noema.grammar import parse,format_graph,number_word
from noema.extraction import extract_document
from noema.finite_semantics import Content,FunctionValue,evaluate_document
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
from scripts.check_written_math_corrections import reviewed_math
from scripts.compose_velocity_light_claim import ROOT,read,PARENT_BASIS,FULL,CORE,BASIS,ANNOTATIONS,INDICES,MEANINGS,build

DOC='docs/velocity-light-claim-v1.md';SOURCE='data/einstein-velocity-light-source-reading-v1.json'
INVENTORY='artifacts/written-units-v1/einstein-1905.json';READING='data/einstein-velocity-deficit-source-reading-v1.json'
PRIORS=tuple(f'data/einstein-velocity-deficit-u{n:04d}-review-v1.json' for n in (143,144))
DEPENDENCIES=('reports/velocity-deficit-claim-v1.json','reports/velocity-axial-claim-v1.json','reports/light-invariance-v1.json','reports/written-math-corrections-v1.json')
CONSTANTS={'rd':'author','eirf':'paper','ri':'discourse','eisoq':'fifth','zb6':'context','zll':'deficits','zlm':'invariance','zln':'display'}
DOMAIN=tuple(CONSTANTS.values())+('other',);POINTS=('context','discourse','other')

@lru_cache(None)
def core():return parse(read(CORE))

@lru_cache(None)
def fixture(name,mode='boundary'):
    doc=extract_document(core(),roots=[name],statement_indices=[]).document
    bounds=NUM|{'sjd','sjt','sky','ejpa','ejoi'}
    if mode=='acquisition':bounds.remove('ejpa');bounds|={'ejoj','ejow'}
    if name=='ejqi' and mode=='binding':bounds|={'s3j','ejqh'}
    if name=='ejqu' and mode!='native':bounds|={'ejqj','ejqt'}
    abstract(doc,bounds);doc=extract_document(doc,roots=[name],statement_indices=[]).document
    d=next(d for d in doc['declarations'] if d['name']==name)
    if mode=='instance' and name in ('s4f','s4i','ejqj','ejqt'):assert len(expose(d,{'forall'},only_sort=RS))==(2 if name=='ejqt' else 1)
    slots=[]
    for i,p in enumerate(d['parameters']):
        n='jvlc'+number_word(i);slots.append(n);doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']))
    expr=dict(kind='call',symbol=name,arguments=[dict(kind='call',symbol=n,arguments=[]) for n in slots])
    if d['result']=='content':
        doc['declarations'].append(dict(kind='primitive',name='jvlcpoint',parameters=[],result='situation'));expr=dict(kind='evaluate',content=expr,situation=dict(kind='call',symbol='jvlcpoint',arguments=[]))
    elif d['result']==RS:
        doc['declarations'].append(dict(kind='primitive',name='jvlcresult',parameters=[RS],result='truth'));expr=dict(kind='call',symbol='jvlcresult',arguments=[expr])
    doc['statements']=[dict(kind='ask',body=expr)];return doc,slots

def run(name,args,m,mode='boundary'):
    doc,slots=fixture(name,mode);assert len(args)==len(slots),(name,len(args),len(slots));values=[]
    def capture(x):values.append(x);return True
    mm={n:lambda x=x:x for n,x in CONSTANTS.items()}|{'jvlcpoint':lambda:'discourse','jvlcresult':capture}|m|{n:lambda x=x:x for n,x in zip(slots,args)}
    result=evaluate_document(doc,individuals=DOMAIN,situations=POINTS,primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=500000,memoize_definitions=True,memoize_expressions=True)[0]['value']
    return values[0] if values else result

@lru_cache(None)
def numeric_checks():
    cases=((5,1,5,True,True),(5,0,5,True,True),(1,Q(999,1000),1,True,True),(5,1,4,True,False),(5,-1,5,False,True),(1,Q(-999,1000),1,False,True),(5,5,5,False,True),(5,6,5,False,True),(5,-6,5,False,True),(5,-5,5,False,False),(0,0,0,False,False),(-5,1,-5,False,False))
    count=0
    for undefined in (0,17):
        cuts,m=arithmetic(undefined);c=lambda x:cuts.make(Q(x));r=cuts.read
        for V,w,U,domain,equal in cases:
            args=list(map(c,(V,w,U)))
            assert run('s3s',args[:2],m)==domain
            assert run('ejqh',args,m)==equal
            assert run('s4d',args,m)==equal
            assert run('s3g',[c(V),c(w),c(V),c(U)],m)==equal
            assert run('ejqi',args[:2],m);count+=5
            if V>0 and w!=-V:assert r(run('ejqg',args[:2],m))==V;count+=1
        assert not run('ejqh',list(map(c,(5,1,5))),m|{'ba':lambda *xs:False});count+=1
    unknowns(lambda mm:run('ejqh',list(map(c,(5,1,5))),mm),m,('ba','sca','sjd','sjt'))
    assert Q(5+1)/(1+Q(1,3))==Q(9,2) and not run('ejqh',list(map(c,(5,1,Q(9,2)))),m);count+=1
    # Independently isolate each of the two displayed equalities.
    base=m|{'s3j':lambda *xs:c(5),'ejqh':lambda *xs:True}
    assert run('ejqi',list(map(c,(5,1))),base,'binding');count+=1
    for patch in ({'s3j':lambda *xs:c(4)},{'ejqh':lambda *xs:False}):
        assert not run('ejqi',list(map(c,(5,1))),base|patch,'binding');count+=1
    unknowns(lambda mm:run('ejqi',list(map(c,(5,1))),mm,'binding'),base,('s3j','ejqh'))
    return dict(cases=count,printed_reduced_quotient_and_both_equalities_native=True,same_result_for_both_numeric_input_orders=True,source_sublight_domain_not_extended_to_algebraic_domain=True,singular_input_rejected_under_two_off_guard_values=True,raw_lowercase_denominator_counterexample='9/2 instead of 5')

@lru_cache(None)
def universal_checks():
    cuts,m=arithmetic();c=lambda x:cuts.make(Q(x));r=cuts.read;count=0
    for fn,point,expected in ((lambda x:x,3,True),(lambda x:c(r(x)+1),3,False),(lambda x:c(r(x)**2),0,True),(lambda x:c(r(x)**2),3,False)):
        assert run('s4b',[FunctionValue((RS,),RS,fn),c(point)],m)==expected;count+=1
    for V,w in ((5,1),(5,0),(5,-1),(5,5),(5,-5),(1,Q(999,1000)),(0,0),(-5,1)):
        mm=m|{'tc':lambda:c(V)}
        assert run('s4f',[c(V),c(w)],mm,'instance')==(V>0)
        assert run('s4i',[c(w)],mm,'instance')==(V>0)
        assert run('ejqj',[c(w)],mm,'instance')==(V>0);count+=3
    for a,b,expected in ((True,True,True),(False,True,False),(True,False,False),(False,False,False)):
        mm={'ejqj':lambda:Content(POINTS,(a,a,a)),'ejqt':lambda:Content(POINTS,(b,b,b))}
        assert run('ejqu',[],mm)==expected;count+=1
    unknowns(lambda mm:run('ejqu',[],mm),{'ejqj':lambda:Content(POINTS,(True,True,True)),'ejqt':lambda:Content(POINTS,(True,True,True))},('ejqj','ejqt'))
    for name,args in (('s4f',[c(5)]),('s4i',[]),('ejqj',[]),('ejqt',[]),('ejqu',[])):
        try:run(name,args,m|{'tc':lambda:c(5)},'native')
        except SemanticError as e:assert str(e)=='Cannot finitely quantify the rational number domain',str(e)
        else:raise AssertionError('All-real claim silently sampled')
    return dict(cases=count,generic_fixed_point_not_velocity_primitive=True,source_argument_slot_and_light_constant_bound=True,general_equation_and_current_application_both_retained=True,zero_algebraic_input_not_a_zero_direction=True,native_all_real_enumeration_refused=True)

@lru_cache(None)
def physical_checks():
    cuts,m=arithmetic();c=lambda x:cuts.make(Q(x));r=cuts.read;norm=norm_factory(cuts,());count=0
    base=m|{n:lambda x=x:c(x) for n,x in zip(('tc','zb7','zkq','zkp','zkc','zkd','eiso4'),(5,3,5,5,5,0,0))}|{'ejpa':lambda ctx:ctx=='context','ejoi':lambda U,ctx:r(U)==5 and ctx=='context'}
    rows={'ejpa':{('context',)},'ejoi':{(Q(5),'context')}}
    for name,args,rs in (('ejqk',[c(3),'context'],{'ejpa':rows['ejpa']}),('ejql',[c(3),c(5),'context'],rows),('ejqm',[c(3),c(5),'context'],rows)):
        count+=perturb(lambda mm:run(name,args,mm),base,rs,norm)
        assert not run(name,args[:-1]+['other'],base);count+=1
    for patch in ({'zkq':lambda:c(3)},{'zkc':lambda:c(-5)},{'zkd':lambda:c(1)},{'zb7':lambda:c(5)},{'tc':lambda:c(6)}):
        assert not run('ejqk',[c(3),'context'],base|patch);count+=1
    for other in (0,5,6,-1):
        assert not run('ejqk',[c(other),'context'],base|{'zb7':lambda:c(other)});count+=1
    assert not run('ejql',[c(3),c(4),'context'],base);count+=1
    assert not run('ejqm',[c(3),c(4),'context'],base|{'ejoi':lambda U,ctx:r(U)==4 and ctx=='context'});count+=1
    for other,U,expected in ((3,5,True),(1,5,True),(3,4,True)):
        assert run('ejqt',[c(other),c(U)],base,'instance')==expected;count+=1
    assert not run('ejqt',[c(3),c(4)],base|{'ejoi':lambda U,ctx:r(U)==4 and ctx=='context'},'instance');count+=1
    # Inspect the native ejpa conjunction separately: all three current quantities share context.
    mm=base|{'ejoj':lambda U,ctx:r(U)==5 and ctx=='context','ejow':lambda angle,ctx:r(angle)==0 and ctx=='context'}
    for name,args in (('ejqk',[c(3),'context']),('ejqm',[c(3),c(5),'context'])):
        assert run(name,args,mm,'acquisition');count+=1
        for n in ('zkp','zkq','eiso4'):
            assert not run(name,args,mm|{n:lambda:c(2)},'acquisition');count+=1
        unknowns(lambda pp:run(name,args,pp,'acquisition'),mm,('ejoi','ejoj','ejow'))
    unknowns(lambda mm:run('ejqm',[c(3),c(5),'context'],mm),base,('ejpa','ejoi','tc','zb7','zkq','zkc','zkd'))
    return dict(cases=count,light_speed_point_with_sublight_frame=True,frame_speed_not_set_to_light=True,same_current_point_derivative_norm_and_context=True,physical_and_swapped_formula_input_orders_bound=True,native_acquisition_conjunction_tested=True,false_premise_not_claimed_as_a_physical_instance=True)

@lru_cache(None)
def presentation_checks():
    groups=(('ejqn',{'zc':{('invariance','author','s4i','s4g','fifth','discourse')}}),('ejqo',{'zc':{('display','author','s4i','ejqu','fifth','discourse')}}),('ejqr',{'eir3':{('invariance','author','paper','ejqp','discourse')},'ue':{('deficits','invariance','discourse')}}),('ejqs',{'eir3':{('display','author','paper','ejqq','discourse')},'ue':{('invariance','display','discourse')}}))
    count=0
    for name,rows in groups:
        mm={n:relation(rs) for n,rs in rows.items()};count+=perturb(lambda pp:run(name,[],pp),mm,rows)
        assert run(name,[],mm|{n:forbidden for n in ('s4i','s4g','ejqu','ejqj','ejqt','ejoi','ejpa')});count+=1
    for name,patch in (('ejqr',{'zlm':lambda:'deficits'}),('ejqs',{'zln':lambda:'invariance'})):
        assert not run(name,[],{'eir3':lambda *xs:True,'ue':lambda *xs:True}|patch);count+=1
    return dict(cases=count,further_consequence_and_this_case_display_same_author_scope=True,ordered_deficit_argument_invariance_display=True,source_case_keeps_same_specialization=True,quoted_derivation_not_certified_true=True)

@lru_cache(None)
def source_record():
    inv=json.loads(read(INVENTORY));math={m['id']:m for m in inv['math']};old=json.loads(read(READING));validate_hashes(ROOT,old['source_sha256'])
    reviewed=reviewed_math()['M0273'];flat=lambda xml:re.sub(r'\s','',''.join(ET.fromstring(xml).itertext()))
    assert flat(reviewed['snapshot_mathml'])=='U=V+w1+wv=V.' and flat(reviewed['reviewed_mathml'])=='U=V+w1+wV=V.'
    ns='{http://www.w3.org/1998/Math/MathML}';root=ET.fromstring(reviewed['reviewed_mathml']);fr=list(root.iter(ns+'mfrac'))
    assert len(fr)==2 and flat(ET.tostring(fr[0][0],encoding='unicode'))=='V+w' and flat(ET.tostring(fr[1][1],encoding='unicode'))=='V'
    assert [x.text for x in root.iter(ns+'mo')].count('=')==2
    segments=[]
    for u in inv['units'][144:146]:
        assert digest(u['text'].encode())==u['text_sha256'];entries=[]
        for n in u['math_ids']:
            e=math[n];assert digest(e['mathml'].encode())==e['sha256'];item=dict(id=n,sha256=e['sha256'],mathml_flat=flat(e['mathml']))
            if n=='M0273':item.update(correction_id=reviewed['correction_id'],reviewed_math_sha256=reviewed['reviewed_math_sha256'],reviewed_mathml=reviewed['reviewed_mathml'],reviewed_mathml_flat=flat(reviewed['reviewed_mathml']))
            else:assert item['mathml_flat']=='V'
            entries.append(item)
        segments.append(dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[0,len(u['text'])],text=u['text'],source_nonblank_characters=len(re.sub(r'\s|\[M\d+\]','',u['text'])),math=entries))
    assert segments[0]['text'].startswith('Es folgt ferner, daß ') and 'nicht geändert werden kann.' in segments[0]['text'] and segments[0]['text'].endswith('Man erhält für diesen Fall:')
    paths={INVENTORY,DOC,READING,*old['source_sha256'],'data/written-math-corrections-v1.json','scripts/check_written_math_corrections.py','reports/written-units-v1.json','artifacts/written-facsimiles-v1/einstein-1905-p906.jpg'}
    return dict(version='einstein-velocity-light-source-reading-v1',reviewer='assistant_visual_and_text_review',pages=['906'],segments=segments,observations=['原刊906頁のferner、光速度V、引用符付きUnterlichtgeschwindigkeit、変化し得ないという全称、この場合に得るという第二文とコロンを照合した。','M0273のU=商=Vの二つの等号、分子V+w、分母1+w/V、句点を照合した。原刊の大文字Vを既存訂正層で明示し、固定転記の小文字vを保存する。','この段落を同じ速度合成則の一般的な特殊化として読み、表示式のw/Uを合成相手と同じ結果の局所的な変数として束縛する。','物理的な適用は同じ点のk速度をV、実際の系速度を光速未満の相手に置く対応で保持する。数値入力交換から光速の座標系や観測上の役割交換を導かない。','一般式の零入力と、現在の正の相対運動への条件付き適用を区別する。特殊化した場合の存在や全実数上の導出の真理を帰属から認定しない。'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert len(new.document['statements'])==len(old.document['statements'])==356
    assert [i for i,(a,b) in enumerate(zip(old.document['statements'],new.document['statements'])) if a!=b]==list(INDICES)
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations'];assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    for p,selection in zip(PRIORS,([139,140,141,142],[140,141,142])):
        prior=json.loads(read(p));validate_hashes(ROOT,prior['source_sha256']);assert selection_binding(new,selection)==prior['selection']
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    load_annotations(ROOT,BASIS,ANNOTATIONS);assert json.loads(read(ANNOTATIONS))['entries']==json.loads(read('data/velocity-deficit-claim-identifiers-v1.json'))['entries']
    names={d['name'] for d in core()['declarations']}
    assert {'s3g','s3j','s4b','s4d','s4e','s4f','s4g','s4i','ejpa','ejoi','ejoj','ejow','ejny','ejm2','sede','sedi'}<=names
    assert not {'s4h','s3c','s3k','s3l','s3m','syw','szs','szt','zke'}&names
    # The display's transitive graph contains the physical application, not just an unused helper.
    selected=selection_binding(new,[144]);assert {'ejqj','ejqt','ejqk','ejql','ejqm','ejoi','ejpa'}<=set(selected['dependencies'])
    assert not [d for d in new.document['declarations'][len(old.document['declarations']):] if d['kind']=='primitive']
    for style in ('compact','full'):
        body=format_graph(core(),style);assert parse(body)==parse(transcribe(body,alphabet='v2'))==core()
    assert source_record()==json.loads(read(SOURCE))
    return dict(new_definitions=len(MEANINGS),new_primitives=0,replaced_partial_statements=list(INDICES),other_statements_preserved=354,prior_judgments_preserved=True,old_math_and_quantity_conventions_unchanged=True,current_display_includes_physical_application=True,no_legacy_special_case_speed_binding=True,later_s5m_update_deferred_to_u0147=True)

def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/SOURCE,json.dumps(source_record(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    results={n:f() for n,f in [('numeric',numeric_checks),('universal',universal_checks),('physical',physical_checks),('presentation',presentation_checks),('structure',structure_checks)]}
    helpers=('compose_velocity_deficit_claim','compose_material_relative_frame','compose_relativity_conjecture','compose_two_postulates','compose_limits','check_clock_site_time','check_moving_trip_geometry','check_material_relative_frame','check_coordinate_correspondence','check_velocity_composition_claim','check_translated_light_trial','check_rod_methods','audit_opening_scope')
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(source_record()['source_sha256'])|{SOURCE,DOC,*PRIORS,*DEPENDENCIES,'scripts/compose_velocity_light_claim.py','scripts/check_velocity_light_claim.py','tests/test_velocity_light_claim.py',*(f'scripts/{n}.py' for n in helpers)}
    alignment=dict(segments=[dict(unit=s['unit'],unit_sha256=s['unit_sha256'],range=s['range'],source=s['text'],statements=selection,definitions=list(MEANINGS),status='explicit_interpretive_annotation') for s,selection in zip(source_record()['segments'],([143,144],[144]))])
    return dict(status='light_speed_specialization_and_same_point_application_connected',document=FULL,**results,alignment=alignment,reviewed_math_layer=reviewed_math()['M0273'],verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,remaining=['u0145–u0146の全単位意味判断','u0147以降とs5mの旧前提の更新'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
