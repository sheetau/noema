"""Check seven equations, signed vectors, normal planes and shared settings."""
from copy import deepcopy
from functools import lru_cache
from fractions import Fraction as Q
from itertools import product
from math import isqrt
import json,re,xml.etree.ElementTree as ET
from noema.grammar import parse,format_graph,number_word
from noema.extraction import extract_document
from noema.finite_semantics import FunctionValue,evaluate_document
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.check_coordinate_correspondence import abstract
from scripts.check_clock_site_time import relation,perturb,unknowns,forbidden
from scripts.check_conductor_cases import sentinel,same_value
from scripts.check_material_relative_frame import NUM,RS
from scripts.check_distant_wave_source import numbers,CONSTANTS as OLD_CONSTANTS
from scripts.check_resting_charge_force import retag
from scripts.check_unipolar_machine import finite_reals
from scripts.compose_wave_display import ROOT,read,FULL,CORE,BASIS,ANNOTATIONS,PARENT_BASIS,INDICES,MEANINGS,PHASE,COORDS,DISPLAY,VECTORS,NORMAL,SETTING,WITNESSES,build

DOC='docs/wave-display-v1.md';SOURCE='data/einstein-wave-display-reading-v1.json'
INVENTORY='artifacts/written-units-v1/einstein-1905.json';FACSIMILE='artifacts/written-facsimiles-v1/einstein-1905-unlp-p910-0.jpg'
DEPENDENCIES=('reports/distant-wave-source-v1.json','reports/plane-waveforms-v1.json','reports/wave-amplitudes-v1.json')
CONSTANTS=OLD_CONSTANTS|{'eissc':'explanation'}
DOMAIN=tuple(dict.fromkeys((*CONSTANTS.values(),*(n for n,t in SETTING if t=='a'),'a','b','body','other')))

@lru_cache(None)
def base(name,mode):
    doc=extract_document(parse(read(CORE)),roots=[name],statement_indices=[]).document
    bounds=NUM|{'bg','lg','sjd','szi','sky'}
    if name=='ekbi':bounds|={'ekaz','ekbh'}
    if name=='ekbl':bounds|={'ekbi','ekbj'}
    if name in ('ekbm','ekbn'):bounds|={'ekbi','ekbl'}
    if mode=='finite':bounds|={'ekbg','ekbi','ekbj','ekbk','ekau','seag'}
    abstract(doc,bounds);doc=extract_document(doc,roots=[name],statement_indices=[]).document
    if mode=='finite':doc=finite_reals(doc)
    if mode=='slots':
        doc=retag(doc)
        for d in doc['declarations']:
            if d['kind']=='primitive':
                d['parameters']=['individual' if isinstance(t,dict) else t for t in d['parameters']]
                if isinstance(d['result'],dict):d['result']='individual'
            else:
                for p in d['parameters']:
                    if isinstance(p['sort'],dict):p['sort']='individual'
    return doc

@lru_cache(None)
def fixture(name,mode='native'):
    doc=deepcopy(base(name,'slots' if mode.startswith('slot:') else mode));d=next(d for d in doc['declarations'] if d['name']==name)
    if mode.startswith('slot:'):
        pivot=int(mode.split(':')[1]);body=d['body'];assert body['kind']=='content';node=body['body'];retained=None
        for i in range(len(WITNESSES)):
            assert node['kind']=='exists'
            if i==pivot:retained={k:node[k] for k in ('kind','variable','sort')}
            else:d['parameters'].append(dict(name=node['variable'],sort=node['sort']))
            node=node['body']
        body['body']=retained|{'body':node}
    slots=[]
    for i,p in enumerate(d['parameters']):
        n='jwd'+number_word(i);slots.append((n,p['sort']));doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']))
    if not any(d['name']=='ri' for d in doc['declarations']):doc['declarations'].append(dict(kind='primitive',name='ri',parameters=[],result='situation'))
    expr=dict(kind='call',symbol=name,arguments=[dict(kind='call',symbol=n,arguments=[]) for n,s in slots])
    if d['result']=='content':expr=dict(kind='evaluate',content=expr,situation=dict(kind='call',symbol='ri',arguments=[]))
    elif d['result']!='truth':
        doc['declarations'].append(dict(kind='primitive',name='jwdcapture',parameters=[d['result']],result='truth'));expr=dict(kind='call',symbol='jwdcapture',arguments=[expr])
    doc['statements']=[dict(kind='ask',body=expr)];return doc,slots

def run(name,args,m,mode='native',domain=DOMAIN):
    doc,slots=fixture(name,mode);assert len(args)==len(slots)
    mm={n:lambda x=x:x for n,x in CONSTANTS.items()}|m
    for (n,s),x in zip(slots,args):
        if isinstance(s,dict) and callable(x) and not isinstance(x,FunctionValue):x=FunctionValue(tuple(s['parameters']),s['result'],x)
        mm[n]=lambda x=x:x
    captured=[]
    def capture(x):captured.append(x);return True
    mm['jwdcapture']=capture
    answer=evaluate_document(doc,individuals=domain,situations=('case','other'),primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=500000,memoize_definitions=True,memoize_expressions=True)[0]['value']
    return captured[0] if captured else answer

def root_sqrt(cuts):
    def f(x):
        n=cuts.read(x);a,b=isqrt(n.numerator),isqrt(n.denominator)
        assert a*a==n.numerator and b*b==n.denominator,'Diagnostic uses rational square roots only'
        return cuts.make(Q(a,b))
    return f

@lru_cache(None)
def equation_checks():
    cuts,m=numbers();c,r=cuts.make,cuts.read;cases=0
    phasevalues=[c(n) for n in (10,2,Q(3,5),Q(4,5),0)]
    phi=run('ekbf',phasevalues,m);sine=FunctionValue((RS,),RS,lambda x:c(2*r(x)+1))
    amps=[3,-4,5,-6,7,-8]
    tau=dict(kind='function',parameters=[RS]*4,result=RS)
    def field(values,phasefun=phi,broken=None):
        return FunctionValue(('individual',),tau,lambda axis:FunctionValue((RS,)*4,RS,lambda *xs:c(values[('x','y','z').index(axis)]*(2*r(phasefun(*xs))+1)+(1 if axis==broken else 0)) if axis in ('x','y','z') else c(0)))
    E,H=field(amps[:3]),field(amps[3:])
    given=[sine,*phasevalues,*map(c,amps),E,H,phi]
    for xyz,t in product(((0,0,0),(1,2,3),(-2,5,-1)),(-1,0,2)):
        expected=2*(Q(t)-(Q(3,5)*xyz[0]+Q(4,5)*xyz[1])/10)
        assert r(phi(*map(c,(*xyz,t))))==expected;cases+=1
        values=given+list(map(c,(*xyz,t)));assert run('ekbg',values,m);cases+=1
        for side,offset in ((0,12),(1,13)):
            for axis in ('x','y','z'):
                bad=values[:];bad[offset]=field(amps[3*side:3*side+3],broken=axis)
                assert not run('ekbg',bad,m),(xyz,t,side,axis);cases+=1
        # Wrong phase with all six fields adjusted consistently still fails the seventh equation.
        wrong=FunctionValue((RS,)*4,RS,lambda *xs:c(r(phi(*xs))+1))
        bad=values[:];bad[12]=field(amps[:3],wrong);bad[13]=field(amps[3:],wrong);bad[14]=wrong
        assert not run('ekbg',bad,m);cases+=1
    # Propagation orientation: x advances V*n*dt while phase remains fixed.
    for dt in (-2,1,3):assert r(phi(c(10*Q(3,5)*dt),c(10*Q(4,5)*dt),c(0),c(dt)))==0;cases+=1
    unknowns(lambda mm:run('ekbg',values,mm),m,('sca','shv','sjd'))
    return dict(cases=cases,each_of_six_components_and_seventh_phase_equation_distinguished=True,one_shared_phase_full_spatial_dot_divided_by_V=True,diagnostic_profile_not_sine=True)

@lru_cache(None)
def vector_checks():
    cuts,m=numbers();c=cuts.make;cases=0
    for first,second in product(((3,4,0),(-3,0,4),(0,0,0)),repeat=2):
        ev=run('ekbe',list(map(c,first)),m);hv=run('ekbe',list(map(c,second)),m)
        ae=5 if any(first) else 0;ah=5 if any(second) else 0
        args=[*map(c,first+second),ev,hv,c(ae),c(ah)];assert run('ekbj',args,m);cases+=1
        for i in range(6):
            bad=args[:];bad[i]=c((first+second)[i]+1);assert not run('ekbj',bad,m);cases+=1
        for i,x in ((8,ae+1),(9,ah+1),(8,-1),(9,-1)):
            bad=args[:];bad[i]=c(x);assert not run('ekbj',bad,m);cases+=1
        assert cuts.read(ev('t'))==0;cases+=1
    return dict(cases=cases,signed_three_component_vectors_and_nonnegative_norms=True,zero_vectors_allowed_and_time_not_amplitude_component=True)

@lru_cache(None)
def normal_checks():
    cuts,m=numbers();c,r=cuts.make,cuts.read;cases=0
    for n in ((1,0,0),(0,1,0),(0,0,-1),(Q(3,5),Q(4,5),0)):
        params=list(map(c,(10,2,*n)));phi=run('ekbf',params,m)
        for first,second,t in product(((0,0,0),(1,2,3)),((0,0,0),(1,-2,3)),(-1,2)):
            args=params+[phi]+list(map(c,(*first,*second,t)))
            assert run('ekbk',args,m);cases+=1
            samephase=r(phi(*map(c,(*first,t))))==r(phi(*map(c,(*second,t))))
            assert samephase==(sum(a*(b-c_) for a,b,c_ in zip(n,second,first))==0);cases+=1
        # A phase constant in space is not allowed to stand in for a plane wave normal.
        first=(0,0,0);second=n;args=params+[FunctionValue((RS,)*4,RS,lambda *xs:c(0))]+list(map(c,(*first,*second,0)))
        assert not run('ekbk',args,m);cases+=1
    params=list(map(c,(10,2,1,0,0)));phi=run('ekbf',params,m);args=params+[phi]+list(map(c,(0,0,0,0,0,0,0)))
    for i,x in ((0,0),(1,0),(2,2)):
        bad=args[:];bad[i]=c(x);assert not run('ekbk',bad,m);cases+=1
    return dict(cases=cases,equal_phase_at_same_time_iff_displacement_orthogonal_to_unit_normal=True,all_three_axes_and_wrong_phase_or_normal_diagnosed=True)

def finite_value(sort):
    if sort in ('individual','situation'):return 'a' if sort=='individual' else 'case'
    if sort=='truth':return True
    return FunctionValue(tuple(sort['parameters']),sort['result'],lambda *xs:finite_value(sort['result']))

@lru_cache(None)
def quantifier_checks():
    cases=0;truth=lambda *xs:True;domain=('a','b')
    for name,width,predicate in (('ekbh',4,'ekbg'),('ekbl',7,'ekbk')):
        values=[finite_value(s) for n,s in fixture(name,'finite')[1]]
        if name=='ekbh':values[-1]=FunctionValue(('individual',)*4,'truth',truth)
        m={'ba':truth,'bb':lambda x:'a','sky':lambda x:'a','seag':lambda *xs:'a','ekbi':truth,'ekbj':truth,'ekau':lambda *xs:FunctionValue(('individual',)*4,'truth',truth),predicate:truth}
        assert run(name,values,m,'finite',domain);cases+=1
        for i in range(width):
            bad=tuple('b' if j==i else 'a' for j in range(width))
            assert not run(name,values,m|{predicate:lambda *xs,bad=bad:tuple(xs[-width:])!=bad},'finite',domain);cases+=1
        # Outside-region failures are excluded, but inside failures cannot hide.
        m['ekau']=lambda *xs:FunctionValue(('individual',)*4,'truth',lambda *ys:all(y=='a' for y in ys))
        if name=='ekbh':values[-1]=FunctionValue(('individual',)*4,'truth',lambda *ys:all(y=='a' for y in ys))
        assert run(name,values,m|{predicate:lambda *xs:all(x=='a' for x in xs[-width:])},'finite',domain);cases+=1
    return dict(cases=cases,all_four_coordinates_and_all_seven_position_pair_slots_quantified=True,region_guard_kept_distinct_from_unrestricted_physical_field=True)

@lru_cache(None)
def binding_checks():
    cuts,m=numbers();c=cuts.make;slots=fixture('ekbi')[1]
    values=[n if t=='a' else 'case' if t=='d' else sentinel(s,i+1,cuts) for i,((n,t),(slot,s)) in enumerate(zip(SETTING,slots))];pos={n:i for i,(n,t) in enumerate(SETTING)}
    values[pos['light']]=c(10)
    gate=lambda xs:len(xs)==len(values) and all(same_value(x,y,s,cuts) for x,y,(slot,s) in zip(xs,values,slots))
    m|={'ekaz':lambda *xs:gate(xs),'ekbh':lambda *xs:True}
    assert run('ekbi',values,m);cases=1
    for name in ('ekaz','ekbh'):assert not run('ekbi',values,m|{name:lambda *xs:False});cases+=1
    for i,(n,t) in enumerate(SETTING):
        bad=values[:];bad[i]='other' if t in ('a','d') else sentinel(slots[i][1],100+i,cuts)
        assert not run('ekbi',bad,m),n;cases+=1
    unknowns(lambda mm:run('ekbi',values,mm),m,('ekaz','ekbh'))
    # Native all-real quantification is explicitly refused.
    raw=[sentinel(s,i+1,cuts) for i,(slot,s) in enumerate(fixture('ekbh')[1])]
    try:run('ekbh',raw,m)
    except ValueError as e:assert 'rational number domain' in str(e) or 'Finite function domain' in str(e)
    else:raise AssertionError('Full real coordinate domain was sampled')
    return dict(cases=cases,all_35_setting_slots_keep_prior_physical_approximation=True,whole_real_coordinate_domain_refused=True)

@lru_cache(None)
def witness_checks():
    cases=0
    for name,rule in (('ekbm','ekbi'),('ekbn','ekbl')):
        for pivot,(pn,pt) in enumerate(WITNESSES):
            mode='slot:'+str(pivot)
            for target in ('a','b','unavailable'):
                expected={n:'a' for n,t in SETTING};expected.update(frame='a',scope='b',context='case',light='a');expected[pn]=target
                args=[expected[n] for i,(n,t) in enumerate(WITNESSES) if i!=pivot];row=tuple(expected[n] for n,t in SETTING)
                m={'ra':lambda:'a','eisrx':lambda:'b','tc':lambda:'a',rule:lambda *xs,row=row:tuple(xs)==row}
                assert run(name,args,m,mode,('a','b'))==(target!='unavailable');cases+=1
                if target!='unavailable':assert not run(name,args,m|{rule:lambda *xs:False},mode,('a','b'));cases+=1
    return dict(cases=cases,witnesses_per_content=len(WITNESSES),same_complete_setting_for_display_and_explanation=True)

@lru_cache(None)
def presentation_checks():
    fixtures={'ekbo':{'eissb':{('display','sourceclaim','author','ekba','ekbm','scope','case')}},'ekbr':{'eissb':{('explanation','display','author','ekbm','ekbn','scope','case')}},'ekbq':{'eir3':{('display','author','paper','ekbp','case')},'ue':{('sourceclaim','display','case')}},'ekbt':{'eir3':{('explanation','author','paper','ekbs','case')},'ue':{('display','explanation','case')}}};cases=0
    for n,rs in fixtures.items():cases+=perturb(lambda mm:run(n,[],mm),{key:relation(rows) for key,rows in rs.items()},rs)
    for n,alias in (('ekbq',{'eisrz':lambda:'sourceclaim'}),('ekbt',{'eissc':lambda:'display'})):
        assert not run(n,[],{'eir3':lambda *xs:True,'ue':lambda *xs:True}|alias);cases+=1
    assert run('ekbr',[],{'eissb':relation(fixtures['ekbr']['eissb']),'ekbm':forbidden,'ekbn':forbidden});cases+=1
    return dict(cases=cases,display_and_hierbei_elaborate_same_hypothesis_not_new_experiments=True)

@lru_cache(None)
def source_record():
    inv=json.loads(read(INVENTORY));math={m['id']:m for m in inv['math']};segments=[]
    root=ET.fromstring(math['M0320']['mathml']);tokens=[x.text for x in root.iter() if x.text]
    assert tokens.count('=')==7 and tokens.count('sin')==6 and tokens.count('Φ')==7
    frac=root.find('.//{*}mfrac');assert ''.join(frac[1].itertext())=='V' and ''.join(frac[0].itertext())=='ax+by+cz'
    readings={'M0320':'X=X0 sin Φ; Y=Y0 sin Φ; Z=Z0 sin Φ; L=L0 sin Φ; M=M0 sin Φ; N=N0 sin Φ; Φ=ω(t−(ax+by+cz)/V).','M0321':'X0,Y0,Z0','M0322':'L0,M0,N0','M0323':'a,b,c'}
    for i in (179,180):
        u=inv['units'][i];text=u['text'];assert digest(text.encode())==u['text_sha256']
        segments.append(dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[0,len(text)],text=text,math=[dict(id=n,sha256=math[n]['sha256'],reading=readings[n]) for n in u['math_ids']],source_nonblank_characters=len(re.sub(r'\s|\[M\d+\]','',text))))
    return dict(status='seven_equations_and_vector_normal_explanation_collated',segments=segments,observations=['原刊910頁の七等式と続くHierbeiの説明を照合した。六係数の下付き0、共通Φ、三項全体をVで割る分数、ωの掛かる括弧を保持する。','表示式は直前の近似設定の表現場として、振幅と法線はその同じ表現の説明として読む。'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in (INVENTORY,FACSIMILE,DOC)})

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert len(new.document['statements'])==366 and new.document['statements'][:INDICES[0]]==old.document['statements']
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations']
    assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    load_annotations(ROOT,BASIS,ANNOTATIONS)
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    names=set(selection_binding(new,INDICES)['dependencies']);assert set(MEANINGS)|{'ekaz','seat','sd24','sdx2','sds2','seal','eissb'}<=names
    assert not names&{'cf','seaj'}
    core=parse(read(CORE))
    for style in ('compact','full'):
        b=format_graph(core,style);assert parse(b)==parse(transcribe(b,alphabet='v2'))==core
    assert json.loads(read(SOURCE))==source_record()
    return dict(new_definitions=len(MEANINGS),new_general_relations=1,new_references=1,old_364_statements_preserved=True,semantic_judgment_separate=True)

def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/SOURCE,json.dumps(source_record(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    results={n:f() for n,f in [('equations',equation_checks),('vectors',vector_checks),('normal',normal_checks),('quantifier',quantifier_checks),('binding',binding_checks),('witness',witness_checks),('presentation',presentation_checks),('structure',structure_checks)]}
    helpers=('check_coordinate_correspondence','check_clock_site_time','check_rod_methods','check_conductor_cases','check_material_relative_frame','check_distant_wave_source','check_resting_charge_force','check_unipolar_machine','compose_distant_wave_source','compose_material_relative_frame','compose_field_equations','compose_relativity_conjecture','compose_two_postulates','compose_electromotive_wording','compose_limits','audit_opening_scope')
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(source_record()['source_sha256'])|{SOURCE,DOC,*DEPENDENCIES,'scripts/compose_wave_display.py','scripts/check_wave_display.py','tests/test_wave_display.py',*(f'scripts/{n}.py' for n in helpers)}
    alignment=dict(segments=[dict(unit=s['unit'],unit_sha256=s['unit_sha256'],range=s['range'],source=s['text'],statements=[i],definitions=list(MEANINGS),status='explicit_interpretive_annotation') for i,s in zip(INDICES,source_record()['segments'])])
    return dict(status='seven_equations_amplitude_vectors_and_wavefront_normals_connected',document=FULL,**results,alignment=alignment,verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
