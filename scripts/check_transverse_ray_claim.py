"""Check full transverse paths, distinct measurements and native substitutions."""
from functools import lru_cache
from fractions import Fraction as Q
from math import isqrt
import json,re
from xml.etree import ElementTree as ET
from noema.grammar import parse,format_graph,number_word
from noema.extraction import extract_document
from noema.finite_semantics import FunctionValue,evaluate_document
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.check_coordinate_correspondence import abstract
from scripts.check_moving_trip_geometry import NUM,numbers
from scripts.check_clock_site_time import relation,perturb,unknowns,forbidden
from scripts.compose_transverse_ray_claim import ROOT,read,PARENT_BASIS,FULL,CORE,BASIS,ANNOTATIONS,INDEX,MEANINGS,GROUPS,SELECTIONS,build

DOC='docs/transverse-ray-claim-v1.md';SOURCE='data/einstein-transverse-ray-source-reading-v1.json'
INVENTORY='artifacts/written-units-v1/einstein-1905.json';PRIOR='data/einstein-longitudinal-elimination-u0072-review-v1.json'
DEPENDENCIES=('reports/longitudinal-elimination-v1.json','reports/origin-light-ray-v1.json','reports/frame-light-law-v1.json','reports/transverse-light-trial-v1.json','reports/transverse-space-v1.json')
RS=dict(kind='function',parameters=['number'],result='truth')
CONSTANTS={'ra':'K','zbm':'k','ta':'length','rb':'timeunit','zc7':'time','yn':'x','yo':'y','yp':'z','zb6':'context','rd':'author','eirf':'paper','eisms':'section','ri':'discourse','ze6':'previous','zfg':'consider','zfc':'chain','zfd':'conditions','zfe':'eta','zff':'zeta'}
DOMAIN=tuple(dict.fromkeys((*CONSTANTS.values(),'ry','my','rz','mz','y0','y1','z0','z1','rayy','rayz','K_y0','K_y1','k_y0','k_y1','K_z0','K_z1','k_z0','k_z1','axisy','axisz','other')))

@lru_cache(None)
def core_document():return parse(read(CORE))

@lru_cache(None)
def fixture(name,mode='boundary'):
    doc=extract_document(core_document(),roots=[name],statement_indices=[]).document
    boundaries=NUM|{'sje','sky'}
    if name=='ei6c':boundaries|={'ei44','se'}
    if name=='ei6d':boundaries|={'ei45','ei4l','ei46','smj','ei44','se'}|(set() if mode=='integrated' else {'ei6c'})
    if name in ('ei6e','ei6f','ei6g','ei6h','ei6i'):boundaries.add('ei6d')
    if name=='eitf' and mode!='full':boundaries.add('se')
    abstract(doc,boundaries);doc=extract_document(doc,roots=[name],statement_indices=[]).document
    d=next(d for d in doc['declarations'] if d['name']==name);slots=[];args=[]
    for i,p in enumerate(d['parameters']):
        n='jtrc'+number_word(i);slots.append(n);doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']));args.append(dict(kind='call',symbol=n,arguments=[]))
    expr=dict(kind='call',symbol=name,arguments=args)
    if d['result']=='content':
        doc['declarations'].append(dict(kind='primitive',name='jtrcpoint',parameters=[],result='situation'));expr=dict(kind='evaluate',content=expr,situation=dict(kind='call',symbol='jtrcpoint',arguments=[]))
    doc['statements']=[dict(kind='ask',body=expr)];return doc,slots

def run(name,args,m,mode='boundary'):
    doc,slots=fixture(name,mode);assert len(args)==len(slots),(name,len(args),len(slots))
    mm={n:lambda x=x:x for n,x in CONSTANTS.items()}|m|{n:lambda x=x:x for n,x in zip(slots,args)};mm.setdefault('jtrcpoint',lambda:'discourse')
    return evaluate_document(doc,individuals=DOMAIN,situations=('context','discourse','other'),primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=350000,memoize_definitions=True,memoize_expressions=True)[0]['value']

def model():
    cuts,m=numbers();c=cuts.make;r=cuts.read;coords={};records={};rows={}
    def norm(xs):
        def one(x):
            if not isinstance(x,FunctionValue):return x
            if x.parameters==(RS,):return tuple(r(x(c(Q(t)))) for t in (0,1,2,3,4,6))
            if x.parameters==(RS,)*4:return tuple(r(x(*(c(Q(a)) for a in p))) for p in ((0,0,0,0),(1,2,3,4)))
            return r(x)
        return tuple(one(x) for x in xs)
    def add(n,*xs):rows.setdefault(n,set()).add(norm(xs))
    def sqrt(x):
        n=r(x)
        if n<0:forbidden()
        a=isqrt(n.numerator);b=isqrt(n.denominator)
        if a*a!=n.numerator or b*b!=n.denominator:forbidden()
        return c(Q(a,b))
    m|={'sje':lambda a,b:c(r(a)/r(b)) if r(b) else forbidden(),'sky':sqrt,'zzbg':m['bg'],'tc':lambda:c(Q(5)),'zb7':lambda:c(Q(3)),'zeq':lambda:FunctionValue((RS,),RS,lambda speed:c(Q(2))),'zd4':lambda:FunctionValue((RS,)*4,RS,lambda x,y,z,t:c(2*r(t)-Q(3,8)*r(x)))}
    linear=lambda speed:FunctionValue((RS,),RS,lambda t:c(Q(speed)*r(t)))
    for axis,tm in (('y',2),('z',3)):
        start,end=axis+'0',axis+'1';ray='ray'+axis
        for frame,prefix,duration,vx,vt in (('K','r',tm,3,4),('k','m',2*tm,0,5)):
            seg=prefix+axis;xyz=[Q(vx*duration),Q(vt*duration if axis=='y' else 0),Q(vt*duration if axis=='z' else 0)]
            coords[frame+'_'+start]=[Q(0)]*4;coords[frame+'_'+end]=[*xyz,Q(duration)]
            records[seg]=dict(wf=ray,wi=start,wj=end,wh=start,wq=Q(5*duration))
            add('ei44',seg,ray,start,end,c(Q(5*duration)),frame,c(Q(5)),'context')
            add('ei6c',seg,frame,axis,c(Q(vx)),c(Q(vt)),'context')
            add('se',ray,frame,'context','length','timeunit',c(Q(0)),c(Q(duration)),linear(vx),linear(vt if axis=='y' else 0),linear(vt if axis=='z' else 0))
            for event,t,position in ((start,0,[0,0,0]),(end,duration,xyz)):
                add('zzbu',event,frame,'context','length','timeunit',c(Q(t)),*(c(Q(x)) for x in position));add('zzbv',ray,event,'context')
        add('ei45','r'+axis,'m'+axis,'context');add('ei46',start,'K_'+start,'k_'+start,'context')
        add('zbw','k','axis'+axis,axis,'context');add('zdw',ray,start,end,'axis'+axis,'k','context')
        add('ei6d','r'+axis,'m'+axis,axis,'context')
    add('ei4l','context');add('smj',m['zd4'](),m['zeq'](),c(Q(5)),c(Q(3)))
    for field in ('wf','wi','wj','wh','wq'):
        def get(seg,field=field):
            if seg not in records:forbidden()
            value=records[seg][field];return c(value) if isinstance(value,Q) else value
        m[field]=get
    m['zdz']=lambda e,f,ctx:f+'_'+e if f+'_'+e in coords and ctx=='context' else forbidden()
    m['zc6']=lambda t,a:c(coords[t][('x','y','z','time').index(a)]) if t in coords and a in ('x','y','z','time') else forbidden()
    m['zbo']=lambda f,a,ctx:'axis'+a if f=='k' and a in ('y','z') and ctx=='context' else forbidden()
    m['zfa']=lambda a:'r'+a if a in ('y','z') else forbidden();m['zfb']=lambda a:'m'+a if a in ('y','z') else forbidden()
    m|={n:lambda *xs,rs=rs:norm(xs) in rs for n,rs in rows.items()}
    return cuts,m,rows,norm,records,coords

@lru_cache(None)
def path_checks():
    cuts,m,rows,norm,records,coords=model();c=cuts.make;count=0
    for axis,tm in (('y',2),('z',3)):
        for frame,seg,vx,vt in (('K','r'+axis,3,4),('k','m'+axis,0,5)):
            args=[seg,frame,axis,c(Q(vx)),c(Q(vt)),'context'];start=axis+'0';end=axis+'1';ray='ray'+axis
            selected={n:{r for r in rows[n] if (ray in r if n in ('se','zzbv') else (seg in r if n=='ei44' else end in r or start in r)) and (frame in r or n=='zzbv')} for n in ('ei44','se','zzbu','zzbv')}
            count+=perturb(lambda mm:run('ei6c',args,mm),m,selected,norm)
            for event in (start,end):
                for slot in range(4):
                    coords[frame+'_'+event][slot]+=1;assert not run('ei6c',args,m);coords[frame+'_'+event][slot]-=1;count+=1
            for field,value in (('wh',end),('wq',Q(-records[seg]['wq'])),('wq',Q(4*tm))):
                old=records[seg][field];records[seg][field]=value;assert not run('ei6c',args,m);records[seg][field]=old;count+=1
            for i,value in ((2,'z' if axis=='y' else 'y'),(2,'x'),(3,c(Q(vx+1))),(4,c(Q(5 if vt==4 else 4)))):
                bad=args.copy();bad[i]=value;assert not run('ei6c',bad,m);count+=1
            unknowns(lambda mm:run('ei6c',args,mm),m,('ei44','se','zzbu','zzbv','zdz','zc6','wh','wq'))
    return dict(cases=count,native_complete_K_diagonal_and_k_transverse_paths_checked=True,all_origin_and_endpoint_coordinates_checked=True,diagonal_arc_length_not_transverse_distance=True)

@lru_cache(None)
def trace_checks():
    cuts,m,rows,norm,records,coords=model();c=cuts.make;r=cuts.read;count=0
    for axis,tm in (('y',2),('z',3)):
        for frame,duration,vx,vt in (('K',tm,3,4),('k',2*tm,0,5)):
            velocity=[vx,vt if axis=='y' else 0,vt if axis=='z' else 0]
            args=['ray'+axis,frame,'context','length','timeunit',c(Q(0)),c(Q(duration)),*map(c,map(Q,(0,0,0,*velocity)))]
            assert run('eitf',args,m);count+=1
            for i in range(len(args)):
                bad=args.copy();bad[i]=c(r(bad[i])+1) if isinstance(bad[i],FunctionValue) else 'other'
                assert not run('eitf',bad,m);count+=1
            fs=[FunctionValue((RS,),RS,lambda t,s=s:c(Q(s)*r(t))) for s in velocity]
            slot=1 if axis=='y' else 2;old=fs[slot]
            fs[slot]=FunctionValue((RS,),RS,lambda t,old=old:c(r(old(t))+r(t)*(duration-r(t))))
            curved=norm(args[:7]+fs)
            assert not run('eitf',args,m|{'se':lambda *xs:norm(xs)==curved});count+=1
            try:run('eitf',args,m,'full')
            except ValueError as e:assert 'Cannot finitely quantify' in str(e),str(e)
            else:raise AssertionError('Full real paths replaced by finite samples')
    return dict(cases=count,all_three_velocity_components_and_intervals_checked=True,same_endpoint_curved_path_rejected=True,full_real_history_refused=True,finite_fingerprints_not_general_function_equality=True)

@lru_cache(None)
def connection_checks():
    cuts,m,rows,norm,records,coords=model();count=0
    for axis in ('y','z'):
        args=['r'+axis,'m'+axis,axis,'context']
        selected={n:{r for r in rows[n] if n in ('ei4l','smj') or any(a in r for a in ('r'+axis,'m'+axis,axis+'0','ray'+axis,'axis'+axis))} for n in ('ei45','ei4l','ei46','ei6c','smj','zbw','zdw')}
        count+=perturb(lambda mm:run('ei6d',args,mm),m,selected,norm)
        assert run('ei6d',args,m,'integrated');count+=1
        for event in (axis+'0',axis+'1'):
            for tup,slot in (('K_'+event,0),('K_'+event,3),('k_'+event,3)):
                coords[tup][slot]+=1;assert not run('ei6d',args,m);coords[tup][slot]-=1;count+=1
        unknowns(lambda mm:run('ei6d',args,mm),m,('zd4','zeq','tc','zb7','sky','zbo','zdz','zc6','ei45','ei6c'))
    for name,args in (('ei6e',['y','context']),('ei6e',['z','context']),('ei6f',[]),('ei6g',[]),('ei6h',[]),('ei6i',[])):
        assert run(name,args,m);count+=1
    for axis in ('y','z'):
        filtered=rows['ei6d']-{('r'+axis,'m'+axis,axis,'context')}
        assert not run('ei6f',[],m|{'ei6d':lambda *xs:xs in filtered});count+=1
    changed=m|{'zfa':lambda a:'ry','zfb':lambda a:'my'}
    assert not run('ei6f',[],changed);assert not run('ei6i',[],changed);count+=2
    return dict(cases=count,current_two_frame_measurements_origin_tau_phi_and_both_axes_required=True,whole_join_with_native_both_paths_passed=True,axis_records_not_interchangeable=True)

@lru_cache(None)
def equation_checks():
    cuts,m,rows,norm,records,coords=model();c=cuts.make;count=0
    for axis in ('y','z'):
        names=('soe','sof','sog');args=[axis+'1',axis,'context']
        assert tuple(run(n,args,m) for n in names)==(True,True,True);count+=3
        slot=1 if axis=='y' else 2
        for tup,i,expected in (('K_'+axis+'1',0,(False,False,True)),('K_'+axis+'1',3,(False,False,True)),('K_'+axis+'1',slot,(True,False,False)),('k_'+axis+'1',slot,(False,True,False)),('k_'+axis+'1',3,(False,True,True))):
            coords[tup][i]+=1;actual=tuple(run(n,args,m) for n in names);assert actual==expected,(axis,tup,i,actual);count+=3;coords[tup][i]-=1
        for scale in (Q(0),Q(1),Q(3,2),Q(3)):
            old=coords['k_'+axis+'1'][:];tm=coords['K_'+axis+'1'][3]
            coords['k_'+axis+'1'][slot]=5*scale*tm;coords['k_'+axis+'1'][3]=scale*tm
            changed=m|{'zeq':lambda scale=scale:FunctionValue((RS,),RS,lambda speed:c(scale))}
            assert tuple(run(n,args,changed) for n in names)==(True,True,True);count+=3;coords['k_'+axis+'1'][:]=old
        unknowns(lambda mm:run('sog',args,mm),m,('tc','zb7','zeq','sky','sje','zdz','zc6'))
    # A y measurement cannot replace the different z arrival distance or time.
    old=coords['k_z1'][:];coords['k_z1']=[Q(0),Q(0),Q(20),Q(4)]
    assert tuple(run(n,['z1','z','context'],m) for n in ('soe','sof','sog'))==(False,True,False);count+=3;coords['k_z1'][:]=old
    for name in ('ei6h','ei6i'):
        assert not run(name,[],m|{'ei6d':lambda *xs:False});count+=1
    report=json.loads(read('reports/transverse-space-v1.json'));validate_hashes(ROOT,report['source_sha256'])
    return dict(cases=count,native_eta_tau_time_condition_and_eta_zeta_results_checked=True,distinct_y_z_arrival_values_required=True,free_phi_retained=True,existing_rational_polynomial_evidence_preserved=True)

@lru_cache(None)
def presentation_checks():
    rows=[('ei6j',{'ug':{('consider','author','ei6f','section','discourse')},'zep':{('consider','author','previous','section','discourse')}}),('ei6m',{'zc':{('chain','author','ei6g','sol','section','discourse')}}),('ei6p',{'zc':{('conditions','author','ei6g','som','section','discourse')}}),('ei6s',{'zd3':{('eta','author','ei6h','sol','soo','section','discourse')}}),('ei6v',{'zc':{('zeta','author','ei6i','soq','section','discourse')},'zep':{('zeta','author','eta','section','discourse')}})]
    for body,message,author,node,previous in GROUPS:rows.append((author,{'eir3':{(CONSTANTS[node],'author','paper',message,'discourse')},'ue':{(CONSTANTS[previous],CONSTANTS[node],'discourse')}}))
    count=0
    for name,relations in rows:
        m={n:relation(rs) for n,rs in relations.items()};count+=perturb(lambda mm:run(name,[],mm),m,relations)
        assert run(name,[],m|{n:forbidden for n in ('ei6f','ei6g','ei6h','ei6i','sol','som','soo','soq')});count+=1
    return dict(cases=count,analogy_conditions_substitution_and_parallel_result_preserved=True,same_author_paper_section_order_required=True,quoted_contents_not_executed=True)

@lru_cache(None)
def source_record():
    inv=json.loads(read(INVENTORY));math={m['id']:m for m in inv['math']};segments=[]
    readings={'M0130':'η=Vτ=aV(t−v*x′/(V²−v²))','M0131':'y/√(V²−v²)=t; x′=0','M0132':'η=a*V*y/√(V²−v²)','M0133':'ζ=a*V*z/√(V²−v²)'}
    for n,flat in zip(readings,('η=Vτ=aV(t−vV2−v2x′),','yV2−v2=t;\u00a0x′=0;','η=aVV2−v2y','ζ=aVV2−v2z.')):assert ''.join(ET.fromstring(math[n]['mathml']).itertext())==flat
    for i,u in enumerate(inv['units'][72:80]):
        assert u['id']==f'einstein-1905:u{73+i:04d}'
        segments.append(dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[0,len(u['text'])],text=u['text'],source_nonblank_characters=len(re.sub(r'\s|\[M\d+\]','',u['text'])),math=[dict(id=n,sha256=math[n]['sha256'],reading=readings[n],mathml_flat=''.join(ET.fromstring(math[n]['mathml']).itertext())) for n in u['math_ids']]))
    retrieval='artifacts/einstein-longitudinal-elimination-v1/retrieval.json';retrieved=json.loads(read(retrieval));validate_hashes(ROOT,{r['path']:r['sha256'] for r in retrieved['sources']})
    paths={INVENTORY,DOC,retrieval,*(r['path'] for r in retrieved['sources'])}
    return dict(version='einstein-transverse-ray-source-reading-v1',reviewer='assistant_visual_and_text_review',pages=['900'],segments=segments,observations=['原刊900頁のAuf analoge Weiseからζの表示までを前の縦光線の結果と続けて読んだ。','両方の他の軸に沿う光線の考察、η=Vτの連鎖、wobeiの二条件、alsoのη、undのζを保持する。','時刻条件とη/ζの分母は√(V²−v²)。最初のτ代入式の分母はV²−v²であり、平方根を混ぜない。','yとzの類推は別々の光線上の式として読む。前の原点放出・正方向を共通に適用する採用解釈を明示する。','M0130のコンマ、M0131の二つのセミコロン、M0133の句点は数式内部に固定され、非数式本文文字には加算しない。'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert new.document['statements'][:-5]==old.document['statements'] and len(new.document['statements'])==300
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations']
    assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    prior=json.loads(read(PRIOR));validate_hashes(ROOT,prior['source_sha256']);assert selection_binding(new,[293,294])==prior['selection']
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    load_annotations(ROOT,BASIS,ANNOTATIONS);doc=core_document();ds={d['name']:d for d in doc['declarations']}
    assert all(ds[m]['body']['force']=='assert' for _,m,_,_,_ in GROUPS)
    for n in ('ei6d','ei6f','ei6h','ei6i'):
        extracted=extract_document(doc,roots=[n],statement_indices=[])
        assert not set(extracted.retained_symbols)&{'soc','sod','soh','soi','soj','sok','son','sop','shd','smk','sfm','sbc'},n
    for style in ('compact','full'):
        body=format_graph(doc,style);assert parse(body)==parse(transcribe(body,alphabet='v2'))==doc
    assert json.loads(read(SOURCE))==source_record()
    return dict(new_definitions=len(MEANINGS),new_primitives=0,preserved_statements=INDEX,prior_whole_unit_judgment_preserved=True,obsolete_coordinate_dependencies_not_reintroduced=True)

def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/SOURCE,json.dumps(source_record(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    results={n:f() for n,f in [('paths',path_checks),('traces',trace_checks),('connections',connection_checks),('equations',equation_checks),('presentation',presentation_checks),('structure',structure_checks)]}
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(source_record()['source_sha256'])|{SOURCE,DOC,PRIOR,*DEPENDENCIES,'scripts/compose_transverse_ray_claim.py','scripts/check_transverse_ray_claim.py','tests/test_transverse_ray_claim.py','scripts/check_coordinate_correspondence.py','scripts/check_moving_trip_geometry.py','scripts/check_material_relative_frame.py','scripts/check_clock_site_time.py','scripts/check_rod_methods.py','scripts/compose_limits.py','scripts/compose_material_relative_frame.py','scripts/compose_relativity_conjecture.py','scripts/compose_two_postulates.py'}
    alignment=dict(segments=[dict(unit=s['unit'],unit_sha256=s['unit_sha256'],range=s['range'],source=s['text'],statements=list(SELECTIONS[i]),definitions=list(MEANINGS),status='explicit_interpretive_annotation') for i,s in enumerate(source_record()['segments'])])
    return dict(status='both_current_transverse_paths_and_spatial_calculations_connected',document=FULL,**results,alignment=alignment,verified_full_units={'kant-1784':0,'einstein-1905':0},general_real_physical_derivation_proved=False,semantic_equivalence_automatically_proved=False,remaining=['u0073–u0080の全文通読判断登録','u0081以降と二作品全体の目標'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
