"""Diagnose source distance, persistent patches and physical approximation bindings."""
from copy import deepcopy
from functools import lru_cache
from fractions import Fraction as Q
from itertools import product
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
from scripts.check_material_relative_frame import arithmetic,NUM,RS
from scripts.check_resting_charge_force import retag
from scripts.compose_distant_wave_source import ROOT,read,FULL,CORE,BASIS,ANNOTATIONS,PARENT_BASIS,INDEX,MEANINGS,PATCH,SOURCE as SOURCE_FIELDS,EMISSION,NUMERIC,SETTING,WITNESSES,PHYSICAL,build

DOC='docs/distant-wave-source-v1.md';SOURCE='data/einstein-distant-wave-source-reading-v1.json'
INVENTORY='artifacts/written-units-v1/einstein-1905.json';FACSIMILE='artifacts/written-facsimiles-v1/einstein-1905-unlp-p910-0.jpg'
DEPENDENCIES=('reports/wave-approximation-v1.json','reports/plane-waveforms-v1.json','reports/vacuum-field-domain-v1.json')
CONSTANTS={'ri':'case','rd':'author','eirf':'paper','ra':'frame','tb':'speedunit','eisrx':'scope','eisry':'sourceclaim','eisrz':'display','eisrs':'previous','yn':'x','yo':'y','yp':'z','zc7':'t'}
DOMAIN=tuple(dict.fromkeys((*CONSTANTS.values(),*(n for n,t in SETTING if t=='a'),'a','b','body','other')))
PS=dict(kind='function',parameters=['individual'],result=RS)

@lru_cache(None)
def base(name,mode):
    doc=extract_document(parse(read(CORE)),roots=[name],statement_indices=[]).document
    bounds=NUM|{'bg','lg','sjd','szi','sd24','seat'}
    if name=='ekaz':bounds|={'ekav','ekax','ejsn','ekay'}
    if name=='ekba':bounds|={'ekaz'}
    if mode=='patch':bounds|={'ekat'}
    if mode=='support':bounds|={'ekaw'}
    abstract(doc,bounds);doc=extract_document(doc,roots=[name],statement_indices=[]).document
    if mode in ('patch','support'):
        doc=retag(doc)
        for d in doc['declarations']:
            if d['name']=='ekat':d['parameters'][-3:]=['individual']*3
            if d['name']=='eisrt':d['parameters'][-1]='individual'
            if d['name']=='ekaw':d['parameters'][0]='individual'
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
        n='jdws'+number_word(i);slots.append((n,p['sort']));doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']))
    if not any(d['name']=='ri' for d in doc['declarations']):doc['declarations'].append(dict(kind='primitive',name='ri',parameters=[],result='situation'))
    expr=dict(kind='call',symbol=name,arguments=[dict(kind='call',symbol=n,arguments=[]) for n,_ in slots])
    if d['result']=='content':expr=dict(kind='evaluate',content=expr,situation=dict(kind='call',symbol='ri',arguments=[]))
    elif d['result']!='truth':
        doc['declarations'].append(dict(kind='primitive',name='jdwscapture',parameters=[d['result']],result='truth'));expr=dict(kind='call',symbol='jdwscapture',arguments=[expr])
    doc['statements']=[dict(kind='ask',body=expr)];return doc,slots

def run(name,args,m,mode='native',domain=DOMAIN):
    doc,slots=fixture(name,mode);assert len(args)==len(slots)
    mm={n:lambda x=x:x for n,x in CONSTANTS.items()}|m
    for (n,s),x in zip(slots,args):
        if isinstance(s,dict) and callable(x) and not isinstance(x,FunctionValue):x=FunctionValue(tuple(s['parameters']),s['result'],x)
        mm[n]=lambda x=x:x
    captured=[]
    def capture(x):captured.append(x);return True
    mm['jdwscapture']=capture
    answer=evaluate_document(doc,individuals=domain,situations=('case','other'),primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=500000,memoize_definitions=True,memoize_expressions=True)[0]['value']
    return captured[0] if captured else answer

def numbers():
    cuts,m=arithmetic();c,r=cuts.make,cuts.read
    m|={'bg':lambda x,y:r(x)<r(y),'lg':lambda lo,hi,t:r(lo)<=r(t)<=r(hi),'sjd':lambda x:c(1/r(x)),'szi':lambda yes,x,y:x if yes else y}
    return cuts,m

@lru_cache(None)
def geometry_checks():
    cuts,m=numbers();c,r=cuts.make,cuts.read;cases=0
    for xyz in product((-2,0,1),repeat=3):
        norm=sum(t*t for t in xyz)
        for included in (False,True):
            space=lambda *xs,yes=included:yes
            assert run('ekat',[space,c(1),c(2),*map(c,xyz)],m)==((not included or norm<=4) and (not norm<1 or included));cases+=1
    region=run('ekau',[lambda x,y,z:r(x)**2+r(y)**2+r(z)**2<=4,c(0),c(2)],m)
    for xyz,t in product(((0,0,0),(2,0,0),(3,0,0)),(-1,0,1,2,3)):
        assert region(*map(c,(*xyz,t)))==(sum(x*x for x in xyz)<=4 and 0<=t<=2);cases+=1
    for xyz,t in product(((3,4,0),(-3,-4,0),(0,0,4),(0,5,0)),(-100,0,100)):
        point=FunctionValue(('individual',),RS,lambda a,vals=dict(zip(('x','y','z','t'),(*xyz,t))):c(vals.get(a,0)))
        assert run('ekaw',[point,c(1),c(5)],m)==(sum(x*x for x in xyz)>=25);cases+=1
    point=FunctionValue(('individual',),RS,lambda a:c(10 if a=='x' else 0))
    for outer,multiple in ((0,5),(-1,5),(1,1),(1,0)):
        assert not run('ekaw',[point,c(outer),c(multiple)],m);cases+=1
    # Quantifier connections over two coordinates; numerical point body above is native.
    args=[lambda *xs:True,c(1),c(2),c(0),c(2)]
    assert run('ekav',args,m|{'ekat':lambda *xs:True},'patch',('a','b'));cases+=1
    for failed in product(('a','b'),repeat=3):
        assert not run('ekav',args,m|{'ekat':lambda *xs,failed=failed:tuple(xs[-3:])!=failed},'patch',('a','b'));cases+=1
    for slot,num in ((1,0),(1,3),(2,0),(4,0),(4,-1)):
        bad=args[:];bad[slot]=c(num);assert not run('ekav',bad,m|{'ekat':lambda *xs:True},'patch',('a','b'));cases+=1
    try:run('ekav',args,m)
    except ValueError as e:assert 'rational number domain' in str(e) or 'Finite function domain' in str(e)
    else:raise AssertionError('Whole real space was sampled')
    return dict(cases=cases,origin_neighborhood_outer_bound_and_persistent_time_interval=True,source_distance_uses_three_spatial_coordinates_only=True,full_real_space_refused=True)

@lru_cache(None)
def support_checks():
    cuts,m=numbers();c=cuts.make;cases=0
    args=['source','process','frame','lengthunit','timeunit','case',c(2),c(5),'scope']
    subsets=[{x for x,yes in zip(('a','b'),bits) if yes} for bits in product((False,True),repeat=2)]
    for support,far,criterion in product(subsets,subsets,(False,True)):
        mm=m|{'eisrt':lambda *xs:xs[-1] in support and tuple(xs[:-1])==tuple(args[:6]),'ekaw':lambda p,o,t:p in far and cuts.read(o)==2 and cuts.read(t)==5,'eisrv':lambda t,s,ctx:criterion and cuts.read(t)==5 and (s,ctx)==('scope','case')}
        assert run('ekax',args,mm,'support')==bool(support and support<=far and criterion);cases+=1
    mm=m|{'eisrt':lambda *xs:tuple(xs[:-1])==tuple(args[:6]) and xs[-1]=='a','ekaw':lambda *xs:True,'eisrv':lambda *xs:True}
    for i in range(6):
        bad=args[:];bad[i]='other';assert not run('ekax',bad,mm,'support');cases+=1
    unknowns(lambda model:run('ekax',args,model,'support'),mm,('eisrt','ekaw','eisrv'))
    try:run('ekax',args,mm)
    except ValueError as e:assert 'rational number domain' in str(e) or 'Finite function domain' in str(e)
    else:raise AssertionError('Full source-point domain was sampled')
    return dict(cases=cases,nonempty_all_physical_source_points_and_same_context=True,largeness_criterion_not_distance_or_approximation_success=True)

def setting_model():
    cuts,m=numbers();c=cuts.make;slots=fixture('ekaz')[1]
    supplied=[n if t=='a' else 'case' if t=='d' else sentinel(sort,i+2,cuts) for i,((n,t),(_,sort)) in enumerate(zip(SETTING,slots))];pos={n:i for i,(n,_) in enumerate(SETTING)}
    for n,x in [('lower',0),('upper',2),('inner',1),('outer',2),('multiple',5),('light',10)]:supplied[pos[n]]=c(x)
    supplied[pos['space']]=FunctionValue((RS,RS,RS),'truth',lambda x,y,z:sum(cuts.read(t)**2 for t in (x,y,z))<=4)
    region=run('ekau',[supplied[pos['space']],c(0),c(2)],m)
    region_sort=next(d['result'] for d in base('ekau','native')['declarations'] if d['name']=='ekau')
    def gate(names,xs):
        for n,x in zip(names,xs,strict=True):
            if n=='region':
                if not same_value(x,region,region_sort,cuts):return False
            elif n=='electricconversion':
                if cuts.read(x)!=1:return False
            elif n=='magneticconversion':
                if cuts.read(x)!=Q(1,10):return False
            elif n=='speedunit':
                if x!='speedunit':return False
            elif not same_value(x,supplied[pos[n]],slots[pos[n]][1],cuts):return False
        return True
    groups={'ekav':[n for n,t in PATCH],'ekax':[n for n,t in SOURCE_FIELDS]+['outer','multiple','scope'],'ejsn':[n for n,t in PHYSICAL],'eiscc':['frame','lengthunit','timeunit','speedunit','context'],'eispn':['process','frame','electricfield','magneticfield','region','context'],'eisru':[n for n,t in EMISSION],'ekay':[n for n,t in NUMERIC],'eisrw':['wave','frame','region','scope','electricbound','magneticbound','electricunit','magneticunit','context']}
    m|={n:lambda *xs,ns=ns:gate(ns,xs) for n,ns in groups.items()}
    return cuts,m,slots,supplied,pos,groups

@lru_cache(None)
def binding_checks():
    cuts,m,slots,supplied,pos,groups=setting_model();cases=1;assert run('ekaz',supplied,m)
    for n in groups:assert not run('ekaz',supplied,m|{n:lambda *xs:False});cases+=1
    # Every input has a downstream gate with its own type retained.
    for i,(n,t) in enumerate(SETTING):
        bad=supplied[:];bad[i]='other' if t in ('a','d') else sentinel(slots[i][1],100+i,cuts)
        assert not run('ekaz',bad,m),n;cases+=1
    unknowns(lambda mm:run('ekaz',supplied,mm),m,groups)
    return dict(cases=cases,source_wave_process_fields_units_region_and_tolerance_shared=True,distance_not_a_substitute_for_approximation_or_sufficiency=True)

@lru_cache(None)
def numeric_checks():
    cuts,m=numbers();c,r=cuts.make,cuts.read;slots=fixture('ekay')[1];values=[sentinel(s,i+1,cuts) for i,(_,s) in enumerate(slots)];pos={n:i for i,(n,_) in enumerate(NUMERIC)}
    for n,x in [('light',10),('rate',2),('ax',1),('ay',0),('az',0),('electricbound',1),('magneticbound',2),*zip(('ex','ey','ez','hx','hy','hz'),range(1,7))]:values[pos[n]]=c(x)
    values[pos['sine']]=FunctionValue((RS,),RS,lambda t:c(2*r(t)))
    def waveform(field,offset):
        return all(r(field(axis)(*map(c,(x,y,z,t))))==Q(offset+i)*2*2*(Q(t)-Q(x,10)) for i,axis in enumerate(('x','y','z')) for x,y,z,t in ((0,0,0,0),(1,2,3,1),(2,-1,4,3)))
    def pair(e,h,ae,ah,be,bh,region):
        return same_value(e,values[pos['electricfield']],slots[pos['electricfield']][1],cuts) and same_value(h,values[pos['magneticfield']],slots[pos['magneticfield']][1],cuts) and waveform(ae,1) and waveform(ah,4) and r(be)==1 and r(bh)==2 and same_value(region,values[pos['region']],slots[pos['region']][1],cuts)
    expected=[values[pos[n]] for n in ('sine','cosine','light')]+[c(0)]+[values[pos[n]] for n in ('rate','ax','ay','az','ex','ey','ez','hx','hy','hz')]
    sorts=next(d['parameters'] for d in base('ekay','native')['declarations'] if d['name']=='sd24')
    m|={'sd24':lambda *xs:len(xs)==14 and all(same_value(x,y,t,cuts) for x,y,t in zip(xs,expected,sorts)),'seat':pair}
    assert run('ekay',values,m);cases=1
    for n in ('sd24','seat'):assert not run('ekay',values,m|{n:lambda *xs:False});cases+=1
    for n in ('light','rate','ax','ay','az','ex','ey','ez','hx','hy','hz','electricbound','magneticbound'):
        bad=values[:];bad[pos[n]]=c(r(bad[pos[n]])+1);assert not run('ekay',bad,m),n;cases+=1
    unknowns(lambda mm:run('ekay',values,mm),m,('sd24','seat'))
    return dict(cases=cases,six_component_shared_phase_and_two_bounds_connected=True,profile_diagnostic_not_claimed_to_be_sine=True)

@lru_cache(None)
def witness_checks():
    cases=0
    for pivot,(pn,pt) in enumerate(WITNESSES):
        mode='slot:'+str(pivot)
        for target in ('a','b','unavailable'):
            expected={n:'a' for n,t in SETTING};expected.update(frame='a',scope='b',context='case',light='a');expected[pn]=target
            args=[expected[n] for i,(n,t) in enumerate(WITNESSES) if i!=pivot];row=tuple(expected[n] for n,t in SETTING)
            mm={'ra':lambda:'a','eisrx':lambda:'b','tc':lambda:'a','ekaz':lambda *xs,row=row:tuple(xs)==row}
            assert run('ekba',args,mm,mode,('a','b'))==(target!='unavailable');cases+=1
            if target!='unavailable':
                assert not run('ekba',args,mm|{'ekaz':lambda *xs:False},mode,('a','b'));cases+=1
    cuts,m=numbers()
    try:run('ekba',[],m|{'tc':lambda:cuts.make(10),'ekaz':lambda *xs:True})
    except ValueError as e:assert 'rational number domain' in str(e) or 'Finite function domain' in str(e)
    else:raise AssertionError('Whole setting function domains were sampled')
    return dict(cases=cases,witnesses=len(WITNESSES),one_complete_setting_not_independent_fragment_witnesses=True,full_function_domains_refused=True)

@lru_cache(None)
def presentation_checks():
    fixtures={'ekbb':{'ug':{('sourceclaim','author','ekba','scope','case')},'eissa':{('sourceclaim','display','ekay','paper','case')}},'ekbd':{'eir3':{('sourceclaim','author','paper','ekbc','case')},'ue':{('previous','sourceclaim','case')}}};cases=0
    for n,rs in fixtures.items():cases+=perturb(lambda mm:run(n,[],mm),{key:relation(rows) for key,rows in rs.items()},rs)
    assert run('ekbb',[],{key:relation(rows) for key,rows in fixtures['ekbb'].items()}|{'ekba':forbidden,'ekay':forbidden});cases+=1
    assert not run('ekbd',[],{'eir3':lambda *xs:True,'ue':lambda *xs:True,'eisry':lambda:'previous'});cases+=1
    return dict(cases=cases,hypothesis_not_actual_experiment_and_following_display_bound=True)

@lru_cache(None)
def source_record():
    inv=json.loads(read(INVENTORY));u=inv['units'][178];text=u['text'];assert u['id']=='einstein-1905:u0179' and digest(text.encode())==u['text_sha256']
    math=next(m for m in inv['math'] if m['id']=='M0319');assert ''.join(ET.fromstring(math['mathml']).itertext()).strip()=='K'
    points=[0,text.index('befinde'),text.index('welche'),text.index('mit genügender'),len(text)]
    return dict(status='distant_source_assumption_composed_whole_judgment_separate',unit=u['id'],unit_sha256=u['text_sha256'],range=[0,len(text)],text=text,math=[dict(id='M0319',sha256=math['sha256'],reading='K')],clauses=[dict(range=[a,b],text=text[a:b]) for a,b in zip(points,points[1:])],source_nonblank_characters=len(re.sub(r'\s|\[M\d+\]','',text)),observations=['原刊910頁の系K、遠方の源、原点を含む空間部分、十分な近似、コロンの表示式参照を照合する。','同じ仮定設定として読み、実験の実施や源の静止を追加しない。原点の近傍を一定の有限時間範囲で固定して扱う明示的な局所理想化を採る。'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in (INVENTORY,FACSIMILE,DOC)})

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert len(new.document['statements'])==364 and new.document['statements'][:INDEX]==old.document['statements']
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations']
    assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    load_annotations(ROOT,BASIS,ANNOTATIONS)
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    names=set(selection_binding(new,[INDEX])['dependencies']);assert set(MEANINGS)|{'ejsn','seat','sd24','sdx2','eispn','ug'}<=names
    assert not names&{'cf','seaj'}
    core=parse(read(CORE))
    for style in ('compact','full'):
        b=format_graph(core,style);assert parse(b)==parse(transcribe(b,alphabet='v2'))==core
    assert json.loads(read(SOURCE))==source_record()
    return dict(new_definitions=len(MEANINGS),new_general_relations=5,new_references=3,old_363_statements_preserved=True,semantic_judgment_separate=True)

def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/SOURCE,json.dumps(source_record(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    results={n:f() for n,f in [('geometry',geometry_checks),('support',support_checks),('binding',binding_checks),('numeric',numeric_checks),('witness',witness_checks),('presentation',presentation_checks),('structure',structure_checks)]}
    helpers=('check_coordinate_correspondence','check_clock_site_time','check_rod_methods','check_conductor_cases','check_material_relative_frame','check_resting_charge_force','compose_vacuum_field_domain','compose_material_relative_frame','compose_field_equations','compose_plane_waveforms','compose_relativity_conjecture','compose_two_postulates','compose_electromotive_wording','compose_limits','audit_opening_scope')
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(source_record()['source_sha256'])|{SOURCE,DOC,*DEPENDENCIES,'scripts/compose_distant_wave_source.py','scripts/check_distant_wave_source.py','tests/test_distant_wave_source.py',*(f'scripts/{n}.py' for n in helpers)}
    s=source_record();row=dict(unit=s['unit'],unit_sha256=s['unit_sha256'],range=s['range'],source=s['text'],statements=[INDEX],definitions=list(MEANINGS),status='explicit_interpretive_annotation')
    return dict(status='distant_physical_wave_source_patch_and_sufficient_approximation_connected',document=FULL,**results,alignment=dict(segments=[row]),verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
