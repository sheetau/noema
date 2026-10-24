"""Check identity by initial data and transport, then the whole source sentence."""
from functools import lru_cache
from fractions import Fraction as Q
from itertools import product
import json
from noema.grammar import parse,format_graph,number_word
from noema.extraction import extract_document
from noema.finite_semantics import evaluate_document,Content,FunctionValue
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.semantic_reviews import digest,validate_hashes,selection_binding
from noema.script import transcribe
from scripts.check_coordinate_correspondence import abstract
from scripts.check_clock_site_time import relation,perturb,unknowns,forbidden
from scripts.check_conductor_cases import sentinel,same_value
from scripts.check_resting_charge_force import retag
from scripts.check_material_relative_frame import NUM,RS
from scripts.check_light_region_slices import setup
from scripts.check_volume_denial import CONSTANTS as PRIOR,DOMAIN as PREVIOUS_DOMAIN
from scripts.check_wave_cycle_frequency import refused
from scripts.compose_same_light_portion import *
from scripts.read_same_light_portion import DOC,SOURCE,INVENTORY,READING,PREVIOUS,build_reading
from scripts.check_moving_ball_transport import plane,surface_fields

CONSTANTS=PRIOR|{'eistp':'noflowclause','eistq':'enclosureclause','eistr':'enclosuresentence'}
DOMAIN=tuple(dict.fromkeys([*PREVIOUS_DOMAIN,*CONSTANTS.values(),*[n for n,t in TOTAL if t=='a']]))
DEPENDENCIES=('reports/moving-ball-transport-v1.json','reports/volume-denial-v1.json','reports/equal-volume-supposition-v1.json','reports/density-unit-scope-v1.json')
BOUNDS={'eknw':{'ekno','eknv'},'eknx':{'eknw'},'ekny':{'eknp','eknk'},'eknz':{'eknp','eknx'}}

@lru_cache(None)
def core():return parse(read(CORE))

@lru_cache(None)
def fixture(name,mode='native'):
    doc=extract_document(core(),roots=[name],statement_indices=[]).document
    bounds=NUM|{'bg','be','sjd','sky','soy','szi','shu','sedi'}|BOUNDS.get(name,set())
    if name in ('ekn2','ekn3','ekn5'):bounds|={'ekny','eknz','ekn2'}-({name})
    if mode=='allpoints':bounds|={'ba','bg','sca','seag','eknu'}
    abstract(doc,bounds);doc=extract_document(doc,roots=[name],statement_indices=[]).document
    if mode.startswith('slot:') or mode=='allpoints':
        doc=retag(doc)
        for d in doc['declarations']:
            if d['kind']=='primitive':
                d['parameters']=['individual' if isinstance(s,dict) and s.get('kind')=='function' else s for s in d['parameters']]
                if isinstance(d['result'],dict) and d['result'].get('kind')=='function':d['result']='individual'
            else:
                for p in d['parameters']:
                    if isinstance(p['sort'],dict) and p['sort'].get('kind')=='function':p['sort']='individual'
        if mode!='allpoints':
            d=next(d for d in doc['declarations'] if d['name']==name);body=d['body']['body'];pivot=int(mode.split(':')[1]);retained=None
            fields=VARIABLES
            for i,(n,t) in enumerate(fields):
                assert body['kind']=='forall'
                if i==pivot:retained={k:body[k] for k in ('kind','variable','sort')}
                else:d['parameters'].append(dict(name=body['variable'],sort=body['sort']))
                body=body['body']
            d['body']['body']=retained|{'body':body}
    d=next(d for d in doc['declarations'] if d['name']==name);slots=[]
    for i,p in enumerate(d['parameters']):
        n='jslp'+number_word(i);slots.append((n,p['sort']));doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']))
    expr=dict(kind='call',symbol=name,arguments=[dict(kind='call',symbol=n,arguments=[]) for n,s in slots])
    if d['result']=='content':
        if not any(x['name']=='ri' for x in doc['declarations']):doc['declarations'].append(dict(kind='primitive',name='ri',parameters=[],result='situation'))
        expr=dict(kind='evaluate',content=expr,situation=dict(kind='call',symbol='ri',arguments=[]))
    elif isinstance(d['result'],dict):
        doc['declarations'].append(dict(kind='primitive',name='jslpcapture',parameters=[d['result']],result='truth'));expr=dict(kind='call',symbol='jslpcapture',arguments=[expr])
    doc['statements']=[dict(kind='ask',body=expr)];return doc,slots

def run(name,values,model,mode='native',domain=DOMAIN):
    doc,slots=fixture(name,mode);assert len(values)==len(slots),(name,len(values),len(slots));captured=[]
    mm={n:lambda x=x:x for n,x in CONSTANTS.items()}|model|{n:lambda x=x:x for (n,s),x in zip(slots,values)}
    def capture(x):captured.append(x);return True
    mm['jslpcapture']=capture
    result=evaluate_document(doc,individuals=domain,situations=('case','other'),primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=700000,memoize_definitions=True,memoize_expressions=True)[0]['value']
    return captured[0] if captured else result


def gate(xs,ys,slots,cuts):return len(xs)==len(ys) and all(same_value(x,y,s,cuts) for x,y,(_,s) in zip(xs,ys,slots))
def scalar(cuts,fn):return FunctionValue((RS,RS,RS,RS),RS,lambda *xs:cuts.make(fn(*map(cuts.read,xs))))
def region(cuts,fn):return FunctionValue((RS,RS,RS,RS),'truth',lambda *xs:fn(*map(cuts.read,xs)))


@lru_cache(None)
def transport_checks():
    cuts,m=setup();c,r=cuts.make,cuts.read;cases=0
    for n in ((0,1,0),(Q(3,5),Q(4,5),0)):
        pv=plane(cuts,n);sf=surface_fields(cuts,m,pv);rho=sf[1];ball=run('eklw',list(map(c,(5,*n,2))),m)
        values=[ball,rho,*map(c,(5,*n))];advected=run('eknt',values,m);masked=run('ekns',values[:2],m)
        for initial,time in product(((0,0,0),(1,-1,Q(1,3)),(2,0,0),(3,0,0)),(-1,0,Q(2,3))):
            point=tuple(Q(x)+5*Q(a)*time for x,a in zip(initial,n))+(time,)
            back=run('eknr',list(map(c,(5,*n,*point))),m)
            assert tuple(r(back(axis)) for axis in ('x','y','z'))==tuple(map(Q,initial));cases+=1
            assert run('eknu',values+list(map(c,point)),m);cases+=1
            expected=r(rho(*map(c,(*initial,0)))) if sum(Q(x)**2 for x in initial)<=4 else 0
            assert r(advected(*map(c,point)))==r(masked(*map(c,point)))==expected;cases+=1
        refused(lambda:run('eknv',values,m));cases+=1
    # The initial slice, rather than later data supplied to the constructor, is used.
    later=scalar(cuts,lambda x,y,z,t:2+Q(1,4)*x*t/(1+t*t));initial=scalar(cuts,lambda *p:2)
    ball=run('eklw',list(map(c,(5,0,1,0,2))),m);old=[ball,initial,*map(c,(5,0,1,0))];changed=[ball,later,*map(c,(5,0,1,0))]
    first=run('eknt',old,m);second=run('eknt',changed,m)
    for x in (-1,0,1):
        p=(x,5,0,1)
        assert r(first(*map(c,p)))==r(second(*map(c,p)))==2;cases+=1
        assert run('eknu',changed+list(map(c,p)),m)==(x==0);cases+=1
    # The perturbation is odd in x, so opposite point pairs preserve their sum.
    assert r(later(*map(c,(1,5,0,1))))+r(later(*map(c,(-1,5,0,1))))==4;cases+=1
    # With zero density, membership still has to follow the initial region.
    shifted=region(cuts,lambda x,y,z,t:(x-(0 if t==0 else 1))**2+(y-5*t)**2+z*z<=4)
    zero=scalar(cuts,lambda *p:0);values=[shifted,zero,*map(c,(5,0,1,0))]
    assert not run('eknu',values+list(map(c,(Q(5,2),5,0,1))),m);cases+=1
    unknowns(lambda model:run('eknu',old+list(map(c,(1,5,0,1))),model),m,('shv','sca','szi'))
    return dict(cases=cases,forward_and_inverse_position_components_checked=True,same_initial_slice_used_at_every_time=True,pointwise_density_not_only_total_preserved=True,zero_density_does_not_erase_geometric_membership=True,whole_real_domain_refused=True)


@lru_cache(None)
def physical_checks():
    cuts,m=setup();c,r=cuts.make,cuts.read;cases=0;slots=fixture('eknw')[1]
    values=[n if t=='a' else 'case' if t=='d' else sentinel(s,i+1,cuts) for i,((n,t),(_,s)) in enumerate(zip(FRAME,slots))]
    pos={n:i for i,(n,t) in enumerate(FRAME)};pv=plane(cuts)
    for (n,t),value in zip(PLANE,pv):values[pos[n]]=value
    sf=surface_fields(cuts,m,pv);ball=run('eklw',[values[pos[n]] for n,t in OLD],m);rho=sf[1]
    expected=[ball,rho,*[values[pos[n]] for n,t in DIRECTION]];probes=((0,0,0,0),(3,0,0,0),(0,5,0,1),(1,5,0,1),(-1,-5,0,-1))
    def transport(*xs):
        if not gate(xs,expected,fixture('eknv')[1],cuts):return False
        return all(xs[0](*map(c,p))==ball(*map(c,p)) and r(xs[1](*map(c,p)))==r(rho(*map(c,p))) for p in probes)
    mm=m|{'ekno':lambda *xs:gate(xs,values,slots,cuts),'eknv':transport}
    assert run('eknw',values,mm);cases+=1
    for i,(_,sort) in enumerate(slots):
        bad=values[:];bad[i]=sentinel(sort,100+i,cuts);assert not run('eknw',bad,mm),(i,FRAME[i]);cases+=1
    for name in ('ekno','eknv'):
        assert not run('eknw',values,mm|{name:lambda *xs:False});cases+=1
    unknowns(lambda model:run('eknw',values,model),mm,('ekno','eknv'))
    # The adapter chooses the same rest-frame portion from the 70-role context.
    slots=fixture('eknx')[1];values=[n if t=='a' else 'case' if t=='d' else sentinel(s,i+1,cuts) for i,((n,t),(_,s)) in enumerate(zip(TOTAL,slots))]
    actual=dict(zip((n for n,t in TOTAL),values))|{'scope':CONSTANTS['eistk']};frame=[actual[n] for n,t in FRAME]
    mm={'eknw':lambda *xs:gate(xs,frame,fixture('eknw')[1],cuts)}
    assert run('eknx',values,mm);cases+=1
    for i,(_,sort) in enumerate(slots):
        bad=values[:];bad[i]=sentinel(sort,100+i,cuts);used=TOTAL[i][0] in {n for n,t in FRAME}-{'scope'}
        assert run('eknx',bad,mm)==(not used);cases+=1
    unknowns(lambda model:run('eknx',values,model),mm,('eknw',))
    return dict(cases=cases,all_26_physical_roles_shared=True,same_ball_density_initial_portion_and_section_scope=True,identity_condition_not_inferred_from_allocation_alone=True)


@lru_cache(None)
def quantifier_checks():
    cases=0
    for name,conclusion,fields in [('ekny','eknk',PLANE),('eknz','eknx',TOTAL)]:
        for pivot,(var,sort) in enumerate(VARIABLES):
            mode=f'slot:{pivot}';base={n:'a' if i%2==0 else 'b' for i,(n,t) in enumerate(VARIABLES)}
            values=[base[n] for i,(n,t) in enumerate(VARIABLES) if i!=pivot]
            for target in ('a','b'):
                assigned=base|{var:target,'frame':'a','light':'a','scope':'b','context':'case','portion':'b'}
                row=tuple(assigned[n] for n,t in TOTAL);result=tuple(assigned[n] for n,t in fields)
                mm={'ra':lambda:'a','tc':lambda:'a','eisrx':lambda:'b','zvaa':lambda:'b','eknp':lambda *xs,row=row:xs==row,conclusion:lambda *xs,row=result:xs==row}
                assert run(name,values,mm,mode,('a','b'));cases+=1
                assert not run(name,values,mm|{conclusion:lambda *xs:False},mode,('a','b'));cases+=1
                bad=assigned|{var:'b' if target=='a' else 'a'};wrong=tuple(bad[n] for n,t in fields)
                assert run(name,values,mm|{conclusion:lambda *xs,row=wrong:xs==row},mode,('a','b'))==(var not in {n for n,t in fields});cases+=1
            assert run(name,values,mm|{'eknp':lambda *xs:False,conclusion:lambda *xs:False},mode,('a','b'));cases+=1
            unknowns(lambda model:run(name,values,model,mode,('a','b')),mm,('eknp',conclusion))
        refused(lambda:run(name,[],{'eknp':lambda *xs:False,conclusion:lambda *xs:True,'tc':lambda:'a'}));cases+=1
    values=['a','b','a','b','a','b'];mm={'bb':lambda n:'a','ba':lambda x:True,'bg':lambda *xs:True,'sca':lambda *xs:True,'seag':lambda *xs:'a','eknu':lambda *xs:xs[:6]==tuple(values)}
    assert run('eknv',values,mm,'allpoints',('a','b'));cases+=1
    for point in product(('a','b'),repeat=4):
        row=tuple(values)+point
        assert not run('eknv',values,mm|{'eknu':lambda *xs,row=row:xs!=row},'allpoints',('a','b'));cases+=1
    unknowns(lambda model:run('eknv',values,model,'allpoints',('a','b')),mm,('ba','bg','sca','eknu'))
    return dict(cases=cases,all_65_context_roles_bound=True,only_same_plane_selected_for_surface_result=True,all_four_position_time_roles_bound=True,native_infinite_domains_refused=True)


@lru_cache(None)
def presentation_checks():
    rows={'eisqo':{('enclosureclause','ekny','eknz','section8','case')}}
    mm={n:relation(rs) for n,rs in rows.items()};cases=perturb(lambda model:run('ekn2',[],model),mm,rows)
    rows={'uh':{('noflowclause','author','ekny','section8','case'),('enclosureclause','author','ekn2','section8','case')},'eisra':{('enclosureclause','author','paper','noflowclause','ekny','eknz','section8','case')}}
    def consequence(author,nodes,conclusion,ctx):return (author,conclusion,ctx)==('author','enclosureclause','case') and all(nodes(x)==(x=='noflowclause') for x in DOMAIN)
    mm={n:relation(rs) for n,rs in rows.items()}|{'ud':consequence}
    cases+=perturb(lambda model:run('ekn3',[],model),mm,rows)
    assert not run('ekn3',[],mm|{'ud':lambda *xs:False});cases+=1
    unknowns(lambda model:run('ekn3',[],model),mm,('ud',))
    # Treating the interpretation as an unqualified truth changes the quoted claim.
    wrong={('noflowclause','author','ekny','section8','case'),('enclosureclause','author','eknz','section8','case')}
    assert not run('ekn3',[],mm|{'uh':relation(wrong)});cases+=1
    outer={'eir3':{('enclosuresentence','author','paper','ekn4','case')},'ue':{('denialsentence','enclosuresentence','case')}}
    mm={n:relation(rs) for n,rs in outer.items()};cases+=perturb(lambda model:run('ekn5',[],model),mm,outer)
    for name,value in [('eistr','denialsentence'),('eistp','enclosureclause')]:
        assert not run('ekn5',[],{n:lambda *xs:True for n in outer}|{name:lambda:value});cases+=1
    return dict(cases=cases,can_describe_distinct_from_must_follow_and_unqualified_truth=True,therefore_grounds_select_only_the_preceding_clause=True,same_surface_back_reference_and_author_order=True,quoted_physical_contents_not_executed=True)


@lru_cache(None)
def reading_checks():
    reading=json.loads(read(READING));assert reading==build_reading();validate_hashes(ROOT,reading['source_sha256'])
    assert reading['selection']==selection_binding(load_catalog(ROOT,BASIS),[INDEX])
    assert reading['reviewed_prose_characters']==94 and reading['cross_unit_reviewed_prose_characters']==242
    assert [s['range'] for s in reading['cross_unit_segments']]==[[422,597],[0,7],[0,107]]
    assert reading['cross_unit_reviewed_math_elements']==2 and reading['verified_full_units']==0
    for p in PREVIOUS:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    return dict(cross_unit_prose_characters=242,cross_unit_math_elements=2,u0205_additional_prose_characters=94,source_crossing_display_and_semicolon_preserved=True,whole_unit_reviews_separate=True)


@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert len(new.document['statements'])==389 and new.document['statements'][:388]==old.document['statements']
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations']
    assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    for index in (385,386,387):assert selection_binding(new,[index])==selection_binding(old,[index])
    load_annotations(ROOT,BASIS,ANNOTATIONS)
    assert json.loads(read(ANNOTATIONS))['entries']==json.loads(read('data/moving-ball-transport-identifiers-v1.json'))['entries']
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    names=set(selection_binding(new,[INDEX])['dependencies'])
    assert set(MEANINGS)|{'eistj','eistf','eiste','eistm','eisqo','ud','uh','eisra','eknp','ekno'}<=names
    assert not {'segi','sefa','sefb'}&names
    for style in ('compact','full'):
        body=format_graph(core(),style);assert parse(body)==parse(transcribe(body,alphabet='v2'))==core()
    return dict(new_definitions=len(MEANINGS),new_general_relations=0,new_reference_individuals=3,all_388_statements_and_judgments_preserved=True,one_new_sentence_statement=True)


def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/READING,json.dumps(build_reading(),ensure_ascii=False,indent=2)+'\n')


@lru_cache(None)
def build_report():
    results={n:f() for n,f in [('transport',transport_checks),('physical',physical_checks),('quantifiers',quantifier_checks),('presentation',presentation_checks),('reading',reading_checks),('structure',structure_checks)]}
    helpers=('compose_moving_ball_transport','compose_equal_volume_supposition','compose_field_equations','compose_material_relative_frame','compose_relativity_conjecture','compose_two_postulates','compose_doppler_infinity','compose_limits','check_coordinate_correspondence','check_clock_site_time','check_conductor_cases','check_resting_charge_force','check_material_relative_frame','check_light_region_slices','check_volume_denial','check_wave_cycle_frequency','check_moving_ball_transport','audit_opening_scope')
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(json.loads(read(READING))['source_sha256'])|{DOC,SOURCE,INVENTORY,READING,*DEPENDENCIES,'scripts/compose_same_light_portion.py','scripts/check_same_light_portion.py','scripts/read_same_light_portion.py','tests/test_same_light_portion.py',*(f'scripts/{n}.py' for n in helpers)}
    return dict(status='same_initial_light_portion_enclosure_sentence_checked',document=FULL,**results,alignment=dict(segments=json.loads(read(READING))['cross_unit_segments']),verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
