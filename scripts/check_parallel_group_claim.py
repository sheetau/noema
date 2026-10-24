"""Check noncircular necessity, signed group scope and the complete presentation."""
from functools import lru_cache
from fractions import Fraction as Q
from itertools import product
import json,re
from xml.etree import ElementTree as ET
from noema.grammar import parse,format_graph,number_word
from noema.extraction import extract_document
from noema.finite_semantics import Content,FunctionValue,evaluate_document
from noema.semantics import SemanticError
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.check_coordinate_correspondence import abstract
from scripts.check_moving_trip_geometry import NUM
from scripts.check_material_relative_frame import RS
from scripts.check_clock_site_time import relation,perturb,unknowns,forbidden
from scripts.check_velocity_composition_claim import arithmetic
from scripts.compose_parallel_group_claim import ROOT,read,PARENT_BASIS,FULL,CORE,BASIS,ANNOTATIONS,INDICES,MEANINGS,build

DOC='docs/parallel-group-claim-v1.md';SOURCE='data/einstein-parallel-group-source-reading-v1.json'
INVENTORY='artifacts/written-units-v1/einstein-1905.json';READING='data/einstein-parallel-current-source-reading-v1.json'
PRIORS=tuple(f'data/einstein-velocity-light-u{n:04d}-review-v1.json' for n in (145,146))
DEPENDENCIES=('reports/parallel-current-records-v1.json','reports/parallel-alternative-claim-v1.json','reports/transform-group-v1.json','reports/derivation-modalities-v1.json')
CONSTANTS={'yn':'x','yo':'y','yp':'z','zc7':'time','zb6':'context','ra':'K','zbm':'k','zlo':'third','zlr':'intro','zls':'substitution','zlu':'group','zm2':'alternative','zm3':'necessity','zcg':'oldnaming','eispa':'newname','eisnb':'Kname','eisna':'kname','eisne':'xname','eisnf':'yname','eisng':'zname','eism5':'tname','rd':'author','eirf':'paper','eisoq':'fifth','eisms':'thirdsection','ri':'discourse'}
DOMAIN=tuple(dict.fromkeys(CONSTANTS.values()))+('extra',);POINTS=('first','discourse','last')

@lru_cache(None)
def core():return parse(read(CORE))

@lru_cache(None)
def fixture(name,mode='boundary'):
    doc=extract_document(core(),roots=[name],statement_indices=[]).document;bounds=NUM|{'sjd','sjt','sky','szi'}
    if name=='ejrl' and mode!='native':bounds|={'ejrk','s5f'}
    if name=='ejro':bounds|={'ejq6','s5g'}
    abstract(doc,bounds);doc=extract_document(doc,roots=[name],statement_indices=[]).document
    d=next(d for d in doc['declarations'] if d['name']==name);slots=[]
    for i,p in enumerate(d['parameters']):
        n='jpgc'+number_word(i);slots.append(n);doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']))
    expr=dict(kind='call',symbol=name,arguments=[dict(kind='call',symbol=n,arguments=[]) for n in slots])
    if d['result']=='content':
        doc['declarations'].append(dict(kind='primitive',name='jpgcpoint',parameters=[],result='situation'));expr=dict(kind='evaluate',content=expr,situation=dict(kind='call',symbol='jpgcpoint',arguments=[]))
    doc['statements']=[dict(kind='ask',body=expr)];return doc,slots

def run(name,args,m,mode='boundary'):
    doc,slots=fixture(name,mode);assert len(args)==len(slots)
    mm={n:lambda x=x:x for n,x in CONSTANTS.items()}|{'jpgcpoint':lambda:'discourse'}|m|{n:lambda x=x:x for n,x in zip(slots,args)}
    return evaluate_document(doc,individuals=DOMAIN,situations=POINTS,primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=1000000,memoize_definitions=True,memoize_expressions=True)[0]['value']

@lru_cache(None)
def necessity_checks():
    count=0
    for bits in product((False,True),repeat=6):
        premises=bits[:3];conclusions=bits[3:];a=Content(POINTS,premises);b=Content(POINTS,conclusions)
        expected=any(premises) and all(not p or c for p,c in zip(premises,conclusions))
        assert run('ejrj',[a,b,'discourse'],{})==expected;count+=1
        assert run('ejrl',[],{'ejrk':lambda:a,'s5f':lambda:b})==expected;count+=1
    unknowns(lambda mm:run('ejrl',[],mm),{'ejrk':lambda:Content(POINTS,(True,False,True)),'s5f':lambda:Content(POINTS,(True,False,True))},('ejrk','s5f'))
    cuts,m=arithmetic();c=lambda x:cuts.make(Q(x));base=m|{'tc':lambda:c(5)}
    assert run('ejrk',[],base);count+=1
    for value in (0,-5):assert not run('ejrk',[],m|{'tc':lambda:c(value)});count+=1
    assert not run('ejrk',[],base|{'ba':lambda *xs:False});count+=1
    for a,b in ((a,b) for i,a in enumerate(('yn','yo','yp','zc7')) for b in ('yn','yo','yp','zc7')[i+1:]):
        assert not run('ejrk',[],base|{a:lambda b=b:CONSTANTS[b]});count+=1
    unknowns(lambda mm:run('ejrk',[],mm),base,('tc','ba','bg'))
    return dict(cases=count,candidates_selected_only_by_premise=True,empty_premise_scope_rejected=True,all_selected_situations_required=True,unselected_current_truth_not_required=True,native_positive_light_and_four_distinct_roles_checked=True,necessity_relative_to_fixed_interpretation_not_all_models=True)

@lru_cache(None)
def group_checks():
    cuts,m=arithmetic();c=lambda x:cuts.make(Q(x));r=cuts.read;count=0;m['szi']=lambda choose,a,b:a if choose else b
    for speed,moving in product((-3,0,3),(-3,0,4)):
        for row in ((7,3,4,2),(0,0,0,0),(0,0,0,1)):
            vector=FunctionValue(('individual',),RS,lambda role,row=row:c(row[('x','y','z','time').index(role)] if role in ('x','y','z','time') else 99))
            for name,args in (('s5a',[c(5),c(speed),c(moving),vector]),('s5b',[c(5),vector]),('s5c',[c(5),c(speed),vector])):
                assert run(name,args,m);count+=1
    for value,expected in ((-6,False),(-5,False),(-3,True),(0,True),(3,True),(5,False),(6,False)):
        assert run('s45',[c(5),c(value)],m)==expected;count+=1
    for name,args,mode in (('s5f',[],'boundary'),('s5g',[],'boundary'),('ejrl',[],'native')):
        try:run(name,args,m|{'tc':lambda:c(5)},mode)
        except SemanticError as e:assert str(e)=='Cannot finitely quantify the rational number domain',str(e)
        else:raise AssertionError('Full real transform family was finitely sampled')
    for a,b in product((False,True),repeat=2):
        mm={'ejq6':lambda:Content(POINTS,(a,)*3),'s5g':lambda:Content(POINTS,(b,)*3)}
        assert run('ejro',[],mm)==(a and b);count+=1
    return dict(cases=count,native_composition_identity_and_both_inverse_instances=True,negative_and_zero_velocities_kept=True,whole_real_family_and_function_domain_not_finitely_enumerated=True,physical_current_result_and_mathematical_full_domain_distinguished=True)

@lru_cache(None)
def presentation_checks():
    groups=(
      ('ejrm',{'eisd3':{('intro','third','paper','discourse')},'ug':{('intro','author','ejq4','fifth','discourse')},'eisd4':{('intro','author','newname','third','paper','discourse'),('oldnaming','author','Kname','K','paper','discourse'),('oldnaming','author','kname','k','paper','discourse')},'eisov':{('intro','author','thirdsection','eiwv','paper','discourse')}}),
      ('ejrn',{'zc':{('substitution','author','ejq7','ejq6','fifth','discourse')},'eisov':{('substitution','author','thirdsection','ejeh','paper','discourse')},'eislo':{(sign,rule,'paper','discourse') for sign,rule in (('xname','eixv'),('yname','eixw'),('zname','eixx'),('tname','eiwt'))}}),
      ('ejrp',{'zc':{('group','author','ejro','s5f','fifth','discourse')}}),
      ('ejrq',{'uh':{('necessity','author','ejrl','fifth','discourse')},'eisa5':{('necessity','author','s5f','ejrl','discourse')}}),
      ('ejrv',{'eir3':{('intro','author','paper','ejrr','discourse')},'ue':{('alternative','intro','discourse')}}),
      ('ejrw',{'eir3':{('substitution','author','paper','ejrs','discourse')},'ue':{('intro','substitution','discourse')}}),
      ('ejrx',{'eir3':{('group','author','paper','ejrt','discourse')},'ue':{('substitution','group','discourse')}}),
      ('ejry',{'eir3':{('necessity','author','paper','ejru','discourse')}}),
    );count=0
    for name,rows in groups:
        mm={n:relation(rs) for n,rs in rows.items()};count+=perturb(lambda pp:run(name,[],pp),mm,rows)
    for name,where,previous in (('ejrv','zlr','alternative'),('ejrw','zls','intro'),('ejrx','zlu','substitution')):
        assert not run(name,[],{'eir3':lambda *xs:True,'ue':lambda *xs:True,where:lambda previous=previous:previous});count+=1
    return dict(cases=count,new_third_frame_distinct_from_prior_inverse_frame_naming=True,section_three_frames_and_current_quantities_referenced=True,same_form_equations_and_group_consequence_not_conflated=True,parenthetical_necessity_targets_same_group=True,ordered_presentation_and_quoted_contents_not_executed=True)

@lru_cache(None)
def source_record():
    inv=json.loads(read(INVENTORY));math={m['id']:m for m in inv['math']};old=json.loads(read(READING));validate_hashes(ROOT,old['source_sha256']);segments=[]
    for u in inv['units'][146:149]:
        assert digest(u['text'].encode())==u['text_sha256'];entries=[]
        for n in u['math_ids']:
            e=math[n];assert digest(e['mathml'].encode())==e['sha256'];entries.append(dict(id=n,sha256=e['sha256'],mathml_flat=''.join(ET.fromstring(e['mathml']).itertext())))
        segments.append(dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[0,len(u['text'])],text=u['text'],math=entries,source_nonblank_characters=len(re.sub(r'\s|\[M\d+\]','',u['text']))))
    assert segments[0]['text'].endswith('die Größe') and segments[1]['math'][0]['mathml_flat']=='v+w1+vwV2'
    assert segments[2]['text']=='tritt; man sieht daraus, daß solche Paralleltransformationen — wie dies sein muß — eine Gruppe bilden.'
    paths={INVENTORY,READING,DOC,*old['source_sha256'],'data/einstein-parallel-alternative-source-reading-v1.json'}
    return dict(version='einstein-parallel-group-source-reading-v1',reviewer='assistant_visual_and_text_review',pages=['906','907'],segments=segments,observations=['過去の別導出、第三系k′の導入、K/kの§3参照、Ξ軸上の原点とw、x/y/z/tと第三系の対応、vだけの置換を同じ文脈で照合した。','M0285の分子v+wと分母1+vw/V²を、前頁のdie Größeと次頁のtrittの間に置いて読んだ。','man sieht darausの根拠、solcheの同じ変換族、群、同じ内容に挿入されたwie dies sein mußを省かず読んだ。','数学的前提に相対的な非空全称の必要性を採用し、群命題の真偽を使わない候補条件を明示した。'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert len(new.document['statements'])==len(old.document['statements'])==356
    assert [i for i,(a,b) in enumerate(zip(old.document['statements'],new.document['statements'])) if a!=b]==list(INDICES)
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations']
    assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    for p,selection in zip(PRIORS,([143,144],[144])):
        prior=json.loads(read(p));validate_hashes(ROOT,prior['source_sha256']);assert selection_binding(new,selection)==prior['selection']
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    load_annotations(ROOT,BASIS,ANNOTATIONS)
    assert json.loads(read(ANNOTATIONS))['entries'][-1]['forms'][0]['text']=='k′'
    names=set(selection_binding(new,[145,146,147,148,149])['dependencies'])
    assert set(MEANINGS)|{'ejri','ejrf','ejra','ejpr','ejq4','ejq7','ejq6','s5e','s5g','s5k','eisa5','ejeh','eiwv'}<=names
    assert not names&{'s5m','s5n','zlz','s4p','s4q','s4r','s4s'}
    premise_names={d['name'] for d in extract_document(core(),roots=['ejrk'],statement_indices=[]).document['declarations']}
    assert not premise_names&{'s5f','s5e','s5g','ejq6','zlz'}
    assert [d['name'] for d in new.document['declarations'][len(old.document['declarations']):] if d['kind']=='primitive']==['eispa']
    for style in ('compact','full'):
        body=format_graph(core(),style);assert parse(body)==parse(transcribe(body,alphabet='v2'))==core()
    assert source_record()==json.loads(read(SOURCE))
    return dict(new_definitions=len(MEANINGS),new_primitives=1,new_primitive_is_designation_only=True,replaced_partial_statements=list(INDICES),other_statements_preserved=352,prior_judgments_preserved=True,all_current_physics_and_modality_transitively_connected=True,necessity_premise_does_not_depend_on_conclusion=True)

def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/SOURCE,json.dumps(source_record(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    results={n:f() for n,f in [('necessity',necessity_checks),('group',group_checks),('presentation',presentation_checks),('structure',structure_checks)]}
    helpers=('compose_parallel_alternative_claim','compose_material_relative_frame','compose_relativity_conjecture','compose_two_postulates','compose_limits','check_clock_site_time','check_moving_trip_geometry','check_coordinate_correspondence','check_material_relative_frame','check_velocity_composition_claim','audit_opening_scope')
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(source_record()['source_sha256'])|{SOURCE,DOC,*PRIORS,*DEPENDENCIES,'scripts/compose_parallel_group_claim.py','scripts/check_parallel_group_claim.py','tests/test_parallel_group_claim.py',*(f'scripts/{n}.py' for n in helpers)}
    alignment=dict(segments=[dict(unit=s['unit'],unit_sha256=s['unit_sha256'],range=s['range'],source=s['text'],statements=selection,definitions=list(MEANINGS),status='explicit_interpretive_annotation') for s,selection in zip(source_record()['segments'],([145,146,148],[146],[146,147,149]))])
    return dict(status='third_frame_same_form_substitution_and_group_necessity_connected',document=FULL,**results,alignment=alignment,verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,remaining=['u0147–u0149の全単位意味判断'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
