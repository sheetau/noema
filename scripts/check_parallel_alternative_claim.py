"""Check the same-point bridge, earlier method chains and their attribution."""
from functools import lru_cache
from fractions import Fraction as Q
from itertools import product
import json,re
from noema.grammar import parse,format_graph,number_word
from noema.extraction import extract_document
from noema.finite_semantics import Content,SequenceValue,evaluate_document
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.check_coordinate_correspondence import abstract
from scripts.check_moving_trip_geometry import NUM,norm_factory
from scripts.check_clock_site_time import relation,perturb,unknowns,forbidden
from scripts.check_velocity_composition_claim import arithmetic
from scripts.check_parallel_composition import transform
from scripts.check_derivation_modalities import install_program
from scripts.check_calculation_discourse import symbol
from scripts.compose_parallel_alternative_claim import ROOT,read,PARENT_BASIS,FULL,CORE,BASIS,ANNOTATIONS,INDEX,MEANINGS,build

DOC='docs/parallel-alternative-claim-v1.md';SOURCE='data/einstein-parallel-alternative-source-reading-v1.json'
INVENTORY='artifacts/written-units-v1/einstein-1905.json';READING='data/einstein-parallel-current-source-reading-v1.json'
PRIORS=tuple(f'data/einstein-velocity-light-u{n:04d}-review-v1.json' for n in (145,146))
DEPENDENCIES=('reports/parallel-current-records-v1.json','reports/derivation-modalities-v1.json','reports/velocity-axial-claim-v1.json','reports/point-motion-records-v1.json')
CONSTANTS={'ra':'K','zbm':'k','zlo':'third','zkb':'object','yn':'x','yo':'y','yp':'z','zc7':'time','zb6':'context','zln':'lightdisplay','zm2':'alternative','rd':'author','zlv':'old','zly':'earlier','eisoq':'fifth','eisms':'thirdsection','eirf':'paper','ri':'discourse'}
DOMAIN=tuple(dict.fromkeys(CONSTANTS.values()))+('new','unused','event','other','first','last','alias','origin')
POINTS=('context','earlier','discourse','other')
OLD=[('ejpb','ejpc'),('ejpc','ejpr')]
NEW=[('ejrc','ejq7'),('ejq7','ejq6'),('ejq6','ejre'),('ejre','ejpr')]

@lru_cache(None)
def core():return parse(read(CORE))

@lru_cache(None)
def fixture(name,program=''):
    doc=extract_document(core(),roots=[name],statement_indices=[]).document
    bounds=NUM|{'sjd','sjt','sky'}
    if name=='ejra':bounds|={'ejm3','eiyx'}
    if name=='ejrc':bounds|={'ejpp','ejq7','ejra'}
    if name=='ejrd':bounds|={'ejmv','ejoi','ejm3','ejqv','ejrb','syr'}
    if name=='ejre':bounds|={'ejrc','ejq6','ejrd','ejpq'}
    abstract(doc,bounds);doc=extract_document(doc,roots=[name],statement_indices=[]).document
    if name=='ejrf':
        doc=install_program(doc,'zlx',*json.loads(program))
        # New quoted contents occur after the inherited zlx declaration.
        # Place the fixture selector after those contents and before its only caller.
        replacements=[d for d in doc['declarations'] if d['name'] in ('jz','zlx')]
        doc['declarations']=[d for d in doc['declarations'] if d['name'] not in ('jz','zlx')]
        at=next(i for i,d in enumerate(doc['declarations']) if d['name']=='ejrf')
        doc['declarations'][at:at]=replacements
    d=next(d for d in doc['declarations'] if d['name']==name);slots=[]
    for i,p in enumerate(d['parameters']):
        n='jpac'+number_word(i);slots.append(n);doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']))
    expr=dict(kind='call',symbol=name,arguments=[dict(kind='call',symbol=n,arguments=[]) for n in slots])
    if d['result']=='content':
        doc['declarations'].append(dict(kind='primitive',name='jpacpoint',parameters=[],result='situation'));expr=dict(kind='evaluate',content=expr,situation=dict(kind='call',symbol='jpacpoint',arguments=[]))
    doc['statements']=[dict(kind='ask',body=expr)];return doc,slots

def run(name,args,m,program='',domain=DOMAIN):
    doc,slots=fixture(name,program);assert len(args)==len(slots)
    mm={n:lambda x=x:x for n,x in CONSTANTS.items()}|{'jpacpoint':lambda:'discourse'}|m|{n:lambda x=x:x for n,x in zip(slots,args)}
    return evaluate_document(doc,individuals=domain,situations=POINTS,primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=1000000,memoize_definitions=True,memoize_expressions=True)[0]['value']

@lru_cache(None)
def numeric_checks():
    cuts,m=arithmetic();c=lambda x:cuts.make(Q(x));count=0
    for speed,time in product((Q(-4),Q(-3),Q(0),Q(3),Q(4)),(Q(-2),Q(0),Q(2))):
        first=[speed*time,Q(0),Q(0),time];last=transform(first,speed)
        assert last[:3]==[0,0,0]
        coords={'first':first,'last':last};mm=m|{'zc5':lambda rec:rec in coords,'zc6':lambda rec,role:c(coords[rec][('x','y','z','time').index(role)])}
        assert run('ejrb',['first','last',c(5),c(speed)],mm);count+=1
        # The actual conclusion is separately checked, so a false implication premise is not a proof.
        assert run('syr',[c(speed),c(0),*map(c,first)],mm);count+=1
        for i in range(4):
            first[i]+=1
            expected=(i==3 and speed==0)
            assert run('syr',[c(speed),c(0),*map(c,first)],mm)==expected;count+=1
            first[i]-=1
        unknowns(lambda pp:run('ejrb',['first','last',c(5),c(speed)],pp),mm,('zc5','zc6','sky','sjd'))
    # Source and result speed domains are deliberately different.
    for moving,point_axial,frame_allowed in ((3,True,True),(5,True,False),(6,True,False),(0,False,True),(-3,False,True)):
        assert run('s3i',[c(moving),c(0),c(moving)],m)==point_axial
        assert run('s45',[c(5),c(moving)],m)==frame_allowed;count+=2
    return dict(cases=count,native_origin_transform_and_axis_trajectory_checked=True,time_coordinate_not_frozen_to_zero=True,signed_and_zero_algebraic_velocities=True,point_formula_domain_not_silently_restricted_to_frame_domain=True)

@lru_cache(None)
def origin_checks():
    cuts,m=arithmetic();c=lambda x:cuts.make(Q(x));count=0
    rows={'ejm3':{('object','event','K','context'),('object','other','k','context')},'zbv':{('third','origin','context')},'cb':{('event','origin','third'),('other','origin','third')},'eiyx':{('event','first','third','context'),('other','last','third','context'),('event','alias','third','context')}}
    coords={rec:[Q(0),Q(0),Q(0),Q(7)] for rec in ('first','last','alias')}
    base=m|{n:relation(rs) for n,rs in rows.items()}|{'zbn':lambda f,ctx:'origin' if (f,ctx)==('third','context') else forbidden(),'zc6':lambda rec,role:c(coords.get(rec,[0,0,0,7])[('x','y','z','time').index(role)])}
    args=['object','K','k','third','context'];check=lambda mm:run('ejra',args,mm)
    assert check(base);count+=1
    # Either frame's object scope counts; remove neither to make one frame mandatory.
    for field in ('zbv','cb'):
        for row in rows[field]:
            assert not check(base|{field:relation(rows[field]-{row})});count+=1
    for event in ('event','other'):
        assert not check(base|{'eiyx':lambda e,*xs,e0=event:e!=e0 and (e,*xs) in rows['eiyx']});count+=1
    for rec,i in product(coords,range(3)):
        coords[rec][i]=Q(1);assert not check(base);coords[rec][i]=Q(0);count+=1
    assert not check(base|{'ejm3':lambda *xs:False});count+=1
    assert check(base|{'ejm3':relation({('object','event','K','context')})});count+=1
    assert check(base|{'ejm3':relation({('object','other','k','context')})});count+=1
    for bad in (['other','K','k','third','context'],['object','K','k','third','other']):assert not run('ejra',bad,base|{'zbn':lambda *xs:'origin'});count+=1
    unknowns(check,base,('ejm3','eiyx','zbv','cb','zbn','zc6'))
    return dict(cases=count,nonempty_union_of_both_current_object_event_scopes=True,third_current_record_exists_for_every_event=True,every_candidate_spatial_coordinate_zero=True,nonzero_third_times_allowed=True)

@lru_cache(None)
def bridge_checks():
    cuts,m=arithmetic();c=lambda x:cuts.make(Q(x));r=cuts.read;norm=norm_factory(cuts,());count=0
    for a,b,d in product((False,True),repeat=3):
        mm=m|{'ejpp':lambda:Content(POINTS,(a,)*4),'ejq7':lambda:Content(POINTS,(b,)*4),'ejra':lambda *xs:d and xs==('object','K','k','third','context'),'zlt':lambda:c(3),'zkq':lambda:c(3)}
        assert run('ejrc',[],mm)==(a and b and d);count+=1
    mm=m|{'ejpp':lambda:Content(POINTS,(True,)*4),'ejq7':lambda:Content(POINTS,(True,)*4),'ejra':lambda *xs:True,'zlt':lambda:c(3),'zkq':lambda:c(4)}
    assert not run('ejrc',[],mm);count+=1
    for bits in product((False,True),repeat=4):
        mm={n:lambda b=b:Content(POINTS,(b,)*4) for n,b in zip(('ejrc','ejq6','ejrd','ejpq'),bits)}
        assert run('ejre',[],mm)==(not(bits[0] and bits[1]) or (bits[2] and bits[3]));count+=1
    # Bind all event/first/middle/last slots on a two-value domain. Native arithmetic was checked above.
    small=('a','b');speed=Q(75,17)
    constants={'ra':'a','zbm':'b','zlo':'a','zkb':'a','yn':'a','yo':'b','yp':'a','zc7':'b'}
    for row in product(small,repeat=4):
        event,first,middle,last=row
        base=m|{n:lambda x=x:x for n,x in constants.items()}|{'tc':lambda:c(5),'zb7':lambda:c(3),'zlt':lambda:c(3),
            'ejmv':lambda *xs:norm(xs)==('a','a',speed,Q(0),Q(0),'context'),
            'ejoi':lambda val,ctx:r(val)==speed and ctx=='context',
            'ejm3':lambda obj,e,f,ctx:(obj,e,f,ctx)==('a',event,'a','context'),
            'ejqv':lambda *xs:xs==('a','b','a',*row,'context'),
            'ejrb':lambda a,b,V,U:(a,b,r(V),r(U))==(first,last,5,speed),
            'zc6':lambda rec,role:c(1 if role=='a' else 2),
            'syr':lambda *xs:tuple(r(x) for x in xs)==(speed,Q(0),Q(1),Q(2),Q(1),Q(2))}
        assert run('ejrd',[],base,domain=small);count+=1
        for name in ('ejmv','ejoi','ejrb','syr'):
            assert not run('ejrd',[],base|{name:lambda *xs:False},domain=small);count+=1
    unknowns(lambda mm:run('ejrd',[],mm,domain=small),base,('ejmv','ejoi','ejm3','ejqv','ejrb','syr','zc6'))
    return dict(cases=count,auxiliary_assumptions_and_same_point_speed_mapping_required=True,conditional_bridge_keeps_false_premise_distinct=True,all_current_record_slots_and_same_composed_speed_bound=True,full_trajectory_actual_derivative_norm_and_record_line_all_required=True)

@lru_cache(None)
def method_checks():
    labels=['baseline','unavailable','wrong_actor','wrong_stage','wrong_rule_stage','not_earlier','same_stage','empty_old','wrong_old_end','missing_angle','empty_new','broken_chain','wrong_new_end','only_old_available','unapproved_step','steps_in_other_method']
    labels += ['skip_'+str(i) for i in range(4)]
    count=0
    for label in labels:
        old=list(OLD);new=list(NEW)
        if label=='empty_old':old=[]
        if label=='wrong_old_end':old[-1]=('ejpc','ejpq')
        if label=='missing_angle':old=[('ejpb','ejpr')]
        if label=='empty_new':new=[]
        if label=='broken_chain':new[2]=('ejq7','ejre')
        if label=='wrong_new_end':new[-1]=('ejre','ejpq')
        if label.startswith('skip_'):
            i=int(label[-1]);nodes=['ejrc','ejq7','ejq6','ejre','ejpr'];nodes.pop(i+1 if i<3 else i);new=list(zip(nodes,nodes[1:]))
        program=json.dumps([old,new]);selected_stage='discourse' if label=='same_stage' else 'earlier'
        allowed=set(old+new)
        if label=='unapproved_step':allowed.remove(('ejre','ejpr'))
        def choose(method,stage,oldseq,newseq):
            assert stage==selected_stage
            if label=='steps_in_other_method':
                return oldseq if method=='old' else newseq if method=='unused' else SequenceValue((),newseq.element_type)
            return oldseq if method=='old' else newseq if method=='new' else SequenceValue((),newseq.element_type)
        mm={'zly':lambda:selected_stage,'zm4':lambda a,b:(a,b)==('earlier','discourse') and label!='not_earlier','jz':choose,
            'zlw':lambda who,method,stage:label!='unavailable' and (who,method,stage)==('other' if label=='wrong_actor' else 'author','old' if label=='only_old_available' else 'new','discourse' if label=='wrong_stage' else selected_stage),
            'zla':lambda a,b,stage:(symbol(a),symbol(b)) in allowed and stage==('discourse' if label=='wrong_rule_stage' else selected_stage)}
        assert run('ejrf',[],mm,program)==(label=='baseline'),label;count+=1
    # Baseline contains quoted formulas only: physical contents have no test interpretations.
    return dict(cases=count,same_previous_and_alternative_conclusion=True,earlier_same_stage_actor_method_and_rules_required=True,old_angle_specialization_and_all_new_bridge_steps_required=True,quoted_contents_not_executed=True,finite_program_not_a_historical_or_general_physics_proof=True)

@lru_cache(None)
def presentation_checks():
    count=0
    for name,rows in (('ejrg',{'uh':{('alternative','author','ejrf','fifth','discourse')},'eisov':{('alternative','author','thirdsection','ejeh','paper','discourse')}}),('ejri',{'eir3':{('alternative','author','paper','ejrh','discourse')},'ue':{('lightdisplay','alternative','discourse')}})):
        mm={n:relation(rs) for n,rs in rows.items()};count+=perturb(lambda pp:run(name,[],pp),mm,rows)
    assert not run('ejri',[],{'eir3':lambda *xs:True,'ue':lambda *xs:True,'zm2':lambda:'lightdisplay'});count+=1
    return dict(cases=count,same_author_fifth_section_and_section_three_reference=True,ordered_after_light_specialization=True,possibility_not_replaced_by_result_or_execution=True)

@lru_cache(None)
def source_record():
    inv=json.loads(read(INVENTORY));u=inv['units'][146];assert u['text_sha256']=='a5afd9f3d9303b85f2c3087f21c22c91bed58468fbe6476cecba17c20f531edb';assert digest(u['text'].encode())==u['text_sha256']
    old=json.loads(read(READING));validate_hashes(ROOT,old['source_sha256']);end=u['text'].index('Führen wir');text=u['text'][:end]
    assert text.startswith('Wir hätten') and 'gleiche Richtung besitzen' in text and 'Zusammensetzen zweier Transformationen gemäß § 3' in text and text.rstrip().endswith('erhalten können.')
    paths={INVENTORY,READING,DOC,*old['source_sha256']}
    return dict(version='einstein-parallel-alternative-source-reading-v1',status='first_sentence_connected_not_whole_unit_judgment',segments=[dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[0,end],text=text)],observations=['同方向の場合の同じUの式、過去の別方法の利用可能性、二変換の合成、§3の参照を保持する。','第三系原点を同じ点へ合わせる補助設定と、全現在記録・全履歴・実際の速さへの接続を明示した。','物理的な系速度と前段の点速度の領域差を保持し、元の結論を狭めない。著者の一般的な導出の妥当性はこの記述から認定しない。','後続の第三系導入と群・必要性までが同じ関連群であり、単位全体の意味判断は未完。'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert len(new.document['statements'])==len(old.document['statements'])==356
    assert [i for i,(a,b) in enumerate(zip(old.document['statements'],new.document['statements'])) if a!=b]==[INDEX]
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations']
    assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    for p,selection in zip(PRIORS,([143,144],[144])):
        prior=json.loads(read(p));validate_hashes(ROOT,prior['source_sha256']);assert selection_binding(new,selection)==prior['selection']
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    load_annotations(ROOT,BASIS,ANNOTATIONS)
    names=set(selection_binding(new,[INDEX])['dependencies'])
    assert set(MEANINGS)|{'ejpb','ejpc','ejpr','ejpp','ejpq','ejq7','ejq6','ejm3','ejmv','ejoi','eiyx','ejeh','s5h','s5i','s2w'}<=names
    assert not names&{'s5m','s3c','s3m','s4s','s4r','zka','zke'}
    assert not [d for d in new.document['declarations'][len(old.document['declarations']):] if d['kind']=='primitive']
    for style in ('compact','full'):
        body=format_graph(core(),style);assert parse(body)==parse(transcribe(body,alphabet='v2'))==core()
    assert source_record()==json.loads(read(SOURCE))
    return dict(new_definitions=len(MEANINGS),new_primitives=0,replaced_partial_statements=[INDEX],other_statements_preserved=355,prior_judgments_preserved=True,same_current_conclusion_and_physical_bridge_transitively_connected=True,whole_unit_review_not_claimed=True)

def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/SOURCE,json.dumps(source_record(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    results={n:f() for n,f in [('numeric',numeric_checks),('origin',origin_checks),('bridge',bridge_checks),('methods',method_checks),('presentation',presentation_checks),('structure',structure_checks)]}
    helpers=('compose_parallel_current_records','compose_material_relative_frame','compose_relativity_conjecture','compose_two_postulates','compose_limits','compose_calculation_discourse','check_clock_site_time','check_moving_trip_geometry','check_coordinate_correspondence','check_velocity_composition_claim','check_parallel_composition','check_derivation_modalities','check_calculation_discourse','audit_opening_scope')
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(source_record()['source_sha256'])|{SOURCE,DOC,*PRIORS,*DEPENDENCIES,'scripts/compose_parallel_alternative_claim.py','scripts/check_parallel_alternative_claim.py','tests/test_parallel_alternative_claim.py',*(f'scripts/{n}.py' for n in helpers)}
    alignment=dict(segments=[dict(unit=s['unit'],unit_sha256=s['unit_sha256'],range=s['range'],source=s['text'],statements=[INDEX],definitions=list(MEANINGS),status='explicit_interpretive_annotation') for s in source_record()['segments']])
    return dict(status='past_alternative_connected_to_current_point_and_axial_conclusion',document=FULL,**results,alignment=alignment,verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,remaining=['第三系の命名・§3参照・本文順序と同形式の提示','全許容速度の群の主張と必要性の候補選定','u0147–u0149の全単位意味判断'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
