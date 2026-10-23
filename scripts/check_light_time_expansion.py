"""Check coordinate choices, complete paths, local times and tau substitutions."""
from functools import lru_cache
from fractions import Fraction as Q
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
from scripts.check_moving_trip_geometry import NUM,numbers,norm_factory
from scripts.check_clock_site_time import relation,perturb,unknowns,forbidden
from scripts.compose_light_time_expansion import ROOT,read,PARENT_BASIS,FULL,CORE,BASIS,ANNOTATIONS,INDEX,MEANINGS,LIMITS,build

DOC='docs/light-time-expansion-v1.md';SOURCE='data/einstein-light-time-expansion-source-reading-v1.json'
INVENTORY='artifacts/written-units-v1/einstein-1905.json'
PRIORS=('data/einstein-axial-time-condition-u0049-review-v1.json','data/einstein-axial-time-condition-u0050-review-v1.json')
DEPENDENCIES=('reports/axial-time-condition-v1.json','reports/light-time-arguments-v1.json','reports/moving-trip-geometry-v1.json','reports/second-principle-v1.json','reports/clock-site-time-v1.json')
LEGACY='examples/v014/einstein-light-time-arguments.noema'
RS=dict(kind='function',parameters=['number'],result='truth')
CONSTANTS={'ra':'frame','zbm':'moving','ta':'lengthunit','rb':'unit','rc':'reference','yn':'x','yo':'y','yp':'z','zc7':'time','zb6':'context','rd':'author','eirf':'paper','eisms':'section','ri':'discourse','zdq':'trial','zdx':'outward','zdy':'returning','zd2':'expansion','zdv':'previous'}
EVENTS=('depart','reflection','arrival');TUPLES=('tuplea','tupleb','tuplec');CLOCKS=('locala','localb','localc');PLACES=('placea','placeb','placec');ROLES=('x','y','z','time')
DOMAIN=tuple(dict.fromkeys([*EVENTS,*TUPLES,*CLOCKS,*PLACES,'origin','mirror','ray','axis','other',*[x for n,x in CONSTANTS.items() if n not in ('zb6','ri')]]))
POINTS=('context','discourse','other')

@lru_cache(None)
def fixture(name,mode='boundary'):
    doc=extract_document(parse(read(CORE)),roots=[name],statement_indices=[]).document
    boundaries=NUM|{'bj','sje'}
    if name in ('ei2k','ei2l'):boundaries.add('eiyx')
    if name=='ei2m':boundaries|={'eifw','eior','eiyg','eiyi','eiyj'}
    if name=='ei2n':boundaries|={'ei2m','se'} if mode=='paths' else {'ei2m','eiti'}
    if name=='ei2o':boundaries.add('eizz')
    if name=='ei2p':boundaries|={'ei2b','ei2l','eios','eiyf','ei2n','ei2o'}
    if name=='ei2q':boundaries.add('ei2p')
    abstract(doc,boundaries);doc=extract_document(doc,roots=[name],statement_indices=[]).document
    d=next(d for d in doc['declarations'] if d['name']==name);slots=[];args=[]
    for i,p in enumerate(d['parameters']):
        n='jlte'+number_word(i);slots.append(n);doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']));args.append(dict(kind='call',symbol=n,arguments=[]))
    expr=dict(kind='call',symbol=name,arguments=args)
    if d['result']=='content':
        doc['declarations'].append(dict(kind='primitive',name='jltepoint',parameters=[],result='situation'));expr=dict(kind='evaluate',content=expr,situation=dict(kind='call',symbol='jltepoint',arguments=[]))
    doc['statements']=[dict(kind='ask',body=expr)];return doc,slots

def run(name,args,m,mode='boundary'):
    doc,slots=fixture(name,mode);assert len(args)==len(slots)
    mm={n:lambda x=x:x for n,x in CONSTANTS.items()}|m|{n:lambda x=x:x for n,x in zip(slots,args)};mm.setdefault('jltepoint',lambda:'discourse')
    return evaluate_document(doc,individuals=DOMAIN,situations=POINTS,primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=500000,memoize_definitions=True,memoize_expressions=True)[0]['value']

def model():
    cuts,m=numbers();c=cuts.make;r=cuts.read;coords=dict(zip(TUPLES,((5,0,0,5),(23,0,0,11),(14,0,0,14))))
    def tupleof(e,f,ctx):
        if e not in EVENTS or (f,ctx)!=('frame','context'):forbidden()
        return TUPLES[EVENTS.index(e)]
    def coordinate(t,a):
        if t not in coords or a not in ROLES:forbidden()
        return c(Q(coords[t][ROLES.index(a)]))
    def selected(value):return lambda tr:value if tr=='trial' else forbidden()
    m|={'zb7':lambda:c(Q(1)),'tc':lambda:c(Q(3)),'zdt':lambda:c(Q(12)),'zdz':tupleof,'zc6':coordinate,'bj':lambda scale,val:c(scale*r(val))}
    def divide(a,b):
        if r(b)<=0:forbidden()
        return c(r(a)/r(b))
    m['sje']=divide
    m|={n:selected(value) for n,value in zip(('qc','qd','qh','qe','qf','qg'),('origin','mirror','ray',*EVENTS))}
    m|={n:selected(c(Q(value))) for n,value in zip(('qi','qj','qk'),(10,19,28))}
    fn=FunctionValue((RS,)*4,RS,lambda xp,y,z,t:c(2*r(t)-r(xp)/4));m['zd4']=lambda:fn
    return cuts,m,coords,fn

@lru_cache(None)
def coordinate_checks():
    cuts,m,coords,fn=model();c=cuts.make;r=cuts.read
    rows={'eiyx':{(e,t,'frame','context') for e,t in zip(EVENTS,TUPLES)}};m|={n:relation(rs) for n,rs in rows.items()}
    check=lambda mm:run('ei2l',['context'],mm);count=perturb(check,m,rows)
    for t in TUPLES:
        for axis in ROLES:
            old=m['zc6'];assert not check(m|{'zc6':lambda rec,a,t=t,axis=axis:c(r(old(rec,a))+(1 if (rec,a)==(t,axis) else 0))});count+=1
    for symbol,val in (('zdt',0),('zdt',-12),('zdt',13),('zb7',0),('zb7',-1),('tc',1),('tc',0)):
        assert not check(m|{symbol:lambda val=val:c(Q(val))});count+=1
    unknowns(check,m,('zdz','zc6','zb7','zdt','tc','ba','bg','sca','bf','shv'))
    return dict(cases=count,all_three_current_K_tuples_and_zero_auxiliary_origin_bound=True,both_transverse_zero_components_required=True,positive_direction_and_strict_subluminal_conditions_preserved=True,nonzero_departure_K_position_and_time_allowed=True)

def segments(cuts,m):
    c=cuts.make;norm=norm_factory(cuts,());data={'outward':(0,1,Q(18)),'returning':(1,2,Q(9))}
    values={}
    for seg,(a,b,path) in data.items():values[seg]={'wf':'ray','wi':EVENTS[a],'wj':EVENTS[b],'wk':CLOCKS[a],'wl':CLOCKS[b],'wm':PLACES[a],'wn':PLACES[b],'wo':c(Q((5,11,14)[a])),'wp':c(Q((5,11,14)[b])),'wq':c(path)}
    def getter(n):
        def get(seg):
            if seg not in values:forbidden()
            return values[seg][n]
        return get
    m=m|{n:getter(n) for n in values['outward']}
    def axis(f,a,ctx):
        if (f,a,ctx)!=('frame','x','context'):forbidden()
        return 'axis'
    def stamp(e,f,u,ctx):
        if e not in EVENTS or (f,u,ctx)!=('frame','unit','context'):forbidden()
        return c(Q((5,11,14)[EVENTS.index(e)]))
    m|={'zbo':axis,'zbe':stamp}
    rows={'eiscd':{(s,'frame','lengthunit','unit','context') for s in data},'eifw':{(s,'frame','reference',Q(3),'context') for s in data},'eior':{(s,'context') for s in data},'zbw':{('frame','axis','x','context')},'zdw':{('ray',EVENTS[a],EVENTS[b],'axis','frame','context') for a,b,_ in data.values()},'eiyg':{(e,cl,p,'frame',Q(t),'context') for e,cl,p,t in zip(EVENTS,CLOCKS,PLACES,(5,11,14))},'eiyi':{(e,p,'frame','context') for e,p in zip(EVENTS,PLACES)},'eiyj':{(e,'frame','context') for e in EVENTS}}
    m|={n:lambda *xs,rs=rs:norm(xs) in rs for n,rs in rows.items()}
    return m,rows,norm

@lru_cache(None)
def segment_checks():
    cuts,m,coords,fn=model();c=cuts.make;r=cuts.read;m,rows,norm=segments(cuts,m)
    args=[['outward','ray','depart','reflection',c(Q(18)),'context'],['returning','ray','reflection','arrival',c(Q(9)),'context']]
    check=lambda mm:all(run('ei2m',xs,mm) for xs in args);count=perturb(check,m,rows,norm)
    unknowns(check,m,('wf','wi','wj','wk','wl','wm','wn','wo','wp','wq','zbo','zbe','zdz','zc6','tc','sca'))
    for name in ('wo','wp','wq'):
        for seg in ('outward','returning'):
            old=m[name];assert not check(m|{name:lambda s,old=old,seg=seg:c(r(old(s))+(1 if s==seg else 0))});count+=1
    assert check(m|{'sba':forbidden,'sbc':forbidden,'shd':forbidden});count+=1
    return dict(cases=count,both_segments_same_ray_events_law_scope_and_geometric_length_bound=True,current_K_local_readings_unique_times_and_coordinate_times_agree=True,old_segment_and_coordinate_rules_not_used=True)

@lru_cache(None)
def geometry_checks():
    cuts,m,coords,fn=model();c=cuts.make;norm=norm_factory(cuts,())
    row=('origin','mirror','ray',*EVENTS,'frame','context','lengthunit','unit',*map(Q,(5,12,3,1,5,11,14)))
    rows={'eiti':{row},'ei2m':{('outward','ray','depart','reflection',Q(18),'context'),('returning','ray','reflection','arrival',Q(9),'context')}}
    m|={n:lambda *xs,rs=rs:norm(xs) in rs for n,rs in rows.items()};check=lambda mm:run('ei2n',['context'],mm)
    count=perturb(check,m,rows,norm);unknowns(check,m,('qc','qd','qh','qe','qf','qg','zdz','zc6','zb7','tc','zdt','bf'))
    # Evaluate the native complete-path wrapper, with se as the explicit infinite
    # history boundary. Probe fingerprints only distinguish argument functions.
    times=(5,8,11,14);norm=norm_factory(cuts,times)
    def linear(start,x,speed):return FunctionValue((RS,),RS,lambda t:c(Q(x)+Q(speed)*(cuts.read(t)-start)))
    zero=linear(0,0,0)
    histories=[['origin','frame','context','lengthunit','unit',c(Q(5)),c(Q(14)),linear(5,5,1),zero,zero],['mirror','frame','context','lengthunit','unit',c(Q(5)),c(Q(14)),linear(5,17,1),zero,zero],['ray','frame','context','lengthunit','unit',c(Q(5)),c(Q(11)),linear(5,5,3),zero,zero],['ray','frame','context','lengthunit','unit',c(Q(11)),c(Q(14)),linear(11,23,-3),zero,zero]]
    native={'se':{norm(xs) for xs in histories},'eisb5':{('ray','frame','context')},'cf':{('ray',)},'cg':{('ray','depart','reflection','frame'),('ray','reflection','arrival','frame')},'ch':{('ray','reflection','frame')},'eisca':{('ray','depart','reflection','frame','context'),('ray','reflection','arrival','frame','context')},'zzbu':set(),'zzbv':set(),'ei2m':rows['ei2m']}
    for point,event,t,x in (('origin','depart',5,5),('mirror','reflection',11,23),('origin','arrival',14,14)):
        native['zzbu'].add((event,'frame','context','lengthunit','unit',Q(t),Q(x),Q(0),Q(0)))
        for obj in (point,'ray'):native['zzbv'].add((obj,event,'context'))
    mm=m|{n:lambda *xs,rs=rs:norm(xs) in rs for n,rs in native.items()}
    count+=perturb(lambda model:run('ei2n',['context'],model,'paths'),mm,native,norm)
    return dict(cases=count,native_two_endpoint_and_two_light_histories_and_same_event_meetings=True,nonzero_K_origin_is_actual_v_times_departure_time=True,both_signed_path_lengths_and_all_parameters_bound=True,finite_function_fingerprints_are_not_whole_real_history_proofs=True)

@lru_cache(None)
def candidate_checks():
    cuts,m,coords,fn=model();c=cuts.make;r=cuts.read;probe=(Q(1),Q(2),Q(3),Q(4))
    m['eizz']=lambda f:r(f(*(c(x) for x in probe)))==Q(31,4)
    check=lambda mm:run('ei2o',[fn],mm);assert check(m);count=1
    for n in ('qi','qj','qk'):
        old=m[n];assert not check(m|{n:lambda tr,old=old:c(r(old(tr))+1)});count+=1
    assert not check(m|{'eizz':lambda f:False});count+=1
    wrong=FunctionValue((RS,)*4,RS,lambda xp,y,z,t:c(2*r(t)+r(xp)/4))
    assert not run('ei2o',[wrong],m);count+=1
    unknowns(check,m,('eizz','qe','qf','qg','qi','qj','qk','zdq','zdt','zdz','zc6','ba','sca'))
    # Tie the same function and all physical conditions into the closed premise.
    norm0=norm_factory(cuts,())
    def norm(xs):return tuple((r(x(c(Q(0)),c(Q(0)),c(Q(0)),c(Q(5)))),r(x(c(Q(12)),c(Q(0)),c(Q(0)),c(Q(11))))) if isinstance(x,FunctionValue) and len(x.parameters)==4 else norm0((x,))[0] for x in xs)
    rows={'ei2b':{()},'ei2l':{('context',)},'eios':{(Q(3),'context')},'eiyf':{('frame','context')},'ei2n':{('context',)},'ei2o':{((Q(10),Q(19)),)}}
    mm=m|{n:lambda *xs,rs=rs:norm(xs) in rs for n,rs in rows.items()};count+=perturb(lambda model:run('ei2p',[],model),mm,rows,norm)
    unknowns(lambda model:run('ei2p',[],model),mm,('zd4','tc'))
    for truth in (False,True):assert run('ei2q',[],{'ei2p':lambda truth=truth:truth})==truth;count+=1
    return dict(cases=count,same_candidate_function_used_for_global_clock_condition_and_three_actual_readings=True,current_prior_trip_K_clocks_light_principle_geometry_and_candidate_all_required=True,quoted_premise_does_not_find_a_tau_solution=True)

@lru_cache(None)
def expression_checks():
    cuts,m,coords,fn=model();c=cuts.make;r=cuts.read;count=0;out={}
    for name,label,start,wrong in [('baseline',12,5,False),('shifted_time_origin',12,-3,False),('negative_label_algebra_only',-12,5,False),('zero_label_algebra_only',0,5,False),('wrong_space_sign',12,5,True)]:
        calls=[]
        def function(x,y,z,t):
            vals=tuple(map(r,(x,y,z,t)));calls.append(vals)
            return c(2*vals[3]+(1 if wrong else -1)*vals[0]/4)
        f=FunctionValue((RS,)*4,RS,function);args=[f,c(Q(label)),c(Q(3)),c(Q(1)),c(Q(start))]
        actual=run('sjg',args,m);assert actual==(not wrong);count+=1
        expected={(Q(0),Q(0),Q(0),Q(start)),(Q(label),Q(0),Q(0),Q(start)+Q(label,2)),(Q(0),Q(0),Q(0),Q(start)+Q(3*label,4))}
        assert set(calls)==expected;count+=1;out[name]=actual
    assert run('ei2r',[],m);count+=1
    assert not run('ei2r',[],m|{'sje':lambda a,b:c(r(a)/(4 if r(b)==2 else 2))});count+=1
    assert not run('ei2r',[],m|{'bj':lambda scale,val:c(r(val))});count+=1
    assert not run('ei2r',[],m|{'ba':lambda value:r(value)!=12});count+=1
    unknowns(lambda mm:run('ei2r',[],mm),m,('zd4','zdt','tc','zb7','zdz','zc6','ba','bg','bd','bf','sje','bj','sca'))
    # Invalid denominator is rejected, even when the Boolean guard is false.
    for speed in (3,4):
        try:run('sjg',[fn,c(Q(12)),c(Q(3)),c(Q(speed)),c(Q(5))],m)
        except ValueError as e:assert 'Unknown clock-site-time' in str(e)
        else:raise AssertionError('Invalid reciprocal input silently fabricated')
        count+=1
    return dict(cases=count,outcomes=out,native_sjf_sjg_all_four_argument_tuples_and_half_sum_checked=True,denominator_signs_and_reflection_return_order_preserved=True,invalid_division_rejected=True,negative_or_zero_label_algebra_not_claimed_as_physical_trip=True)

@lru_cache(None)
def presentation_checks():
    rows={'zd3':{('expansion','author','ei2q','ei2d','ei2r','section','discourse')}};m={n:relation(rs) for n,rs in rows.items()}
    count=perturb(lambda mm:run('ei2s',[],mm),m,rows)
    assert run('ei2s',[],m|{n:forbidden for n in ('ei2q','ei2d','ei2r','ei2p','sjg')});count+=1
    rows={'eir3':{('expansion','author','paper','ei2t','discourse')},'ue':{('previous','expansion','discourse')}};m={n:relation(rs) for n,rs in rows.items()};count+=perturb(lambda mm:run('ei2u',[],mm),m,rows)
    return dict(cases=count,same_current_midpoint_premise_and_expanded_formula_bound=True,conditional_reexpression_not_an_automatic_equivalence_proof=True,author_scope_and_source_order_preserved=True)

@lru_cache(None)
def source_record():
    inv=json.loads(read(INVENTORY));units=inv['units'][50:53]
    assert [(u['id'],len(u['text'])) for u in units]==[('einstein-1905:u0051',142),('einstein-1905:u0052',7),('einstein-1905:u0053',7)]
    maths={m['id']:m for m in inv['math']};ids=[m for u in units for m in u['math_ids']]
    forms=('τ','12[τ(0,0,0,t)+τ(0,0,0,{t+x′V−v+x′V+v})]','=τ(x′,0,0,t+x′V−v).');bindings=('zd4/ei2o','sjg/ei2r/left','sjg/ei2r/right');entries=[]
    for mid,form,binding in zip(ids,forms,bindings,strict=True):
        node=ET.fromstring(maths[mid]['mathml']);assert ''.join(node.itertext())==form
        fractions=[[''.join(child.itertext()) for child in n] for n in node.iter() if n.tag.split('}')[-1]=='mfrac']
        assert fractions==([] if mid=='M0099' else [['1','2'],['x′','V−v'],['x′','V+v']] if mid=='M0100' else [['x′','V−v']])
        entries.append(dict(id=mid,sha256=maths[mid]['sha256'],reading=form,binding=binding))
    prior='data/einstein-axial-time-condition-source-reading-v1.json';old=json.loads(read(prior));validate_hashes(ROOT,old['source_sha256'])
    paths={INVENTORY,DOC,prior,'artifacts/einstein-frame-coordinates-v1/page-898.jpg','artifacts/einstein-frame-coordinates-v1/page-898.html','artifacts/einstein-frame-coordinates-v1/retrieval.json'}
    segments=[dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[0,len(u['text'])],text=u['text'],source_nonblank_characters=len(re.sub(r'\s|\[M\d+\]','',u['text'])),math=[m for m in entries if m['id'] in u['math_ids']]) for u in units]
    assert [s['source_nonblank_characters'] for s in segments]==[116,0,0]
    return dict(version='einstein-light-time-expansion-source-reading-v1',reviewer='assistant_visual_and_text_review',pages=['898'],segments=segments,observations=['原刊898頁末のoderからanwendetまでと、直後の二行に分かれた同じ等式を照合した。','M0100は半和の左辺、M0101は等号から始まる反射値の右辺であり、別々の独立した式ではない。','三回のτは四引数を持ち、出発と帰着の三位置は零、反射位置はx′,0,0。tは同じ出発時刻である。','左辺の帰着時刻にはV-vとV+vの二分数、右辺の反射時刻にはV-vの分数がある。半分の係数と分母符号をMathMLの木でも照合した。','後続の無限小による微分条件はここへ含めない。'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert new.document['statements'][:-1]==old.document['statements'] and len(new.document['statements'])==280
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations']
    assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    for path,indices in zip(PRIORS,([277,278],[278])):
        prior=json.loads(read(path));validate_hashes(ROOT,prior['source_sha256']);assert selection_binding(new,indices)==prior['selection']
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    load_annotations(ROOT,BASIS,ANNOTATIONS);assert json.loads(read(ANNOTATIONS))['entries']==json.loads(read('data/axial-time-condition-identifiers-v1.json'))['entries']
    doc=parse(read(CORE));ds={d['name']:d for d in doc['declarations']};legacy={d['name']:d for d in parse(read(LEGACY))['declarations']}
    assert all(ds[n]==legacy[n] for n in ('sjd','sje','sjf','sjg','sjh','sji','sjk'));assert ds['ei2t']['body']['force']=='assert'
    for style in ('compact','full'):
        body=format_graph(doc,style);assert parse(body)==parse(transcribe(body,alphabet='v2'))==doc
    assert json.loads(read(SOURCE))==source_record()
    return dict(new_definitions=len(MEANINGS),new_primitives=0,preserved_statements=279,both_prior_trial_and_midpoint_reviews_preserved=True,old_reciprocal_expansion_and_time_accessors_unchanged=True)

def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/SOURCE,json.dumps(source_record(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    results={n:fn() for n,fn in [('coordinates',coordinate_checks),('segments',segment_checks),('geometry',geometry_checks),('candidate',candidate_checks),('expression',expression_checks),('presentation',presentation_checks),('structure',structure_checks)]}
    source=source_record();paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(source['source_sha256'])|{SOURCE,DOC,*PRIORS,*DEPENDENCIES,LEGACY,'scripts/compose_light_time_expansion.py','scripts/check_light_time_expansion.py','tests/test_light_time_expansion.py','scripts/check_coordinate_correspondence.py','scripts/check_moving_trip_geometry.py','scripts/check_material_relative_frame.py','scripts/check_clock_site_time.py','scripts/check_rod_methods.py','scripts/compose_limits.py','scripts/compose_relativity_conjecture.py','scripts/compose_material_relative_frame.py','scripts/compose_two_postulates.py'}
    alignment=[dict(unit=s['unit'],unit_sha256=s['unit_sha256'],range=s['range'],source=s['text'],statements=[INDEX],definitions=list(MEANINGS),status='explicit_interpretive_annotation') for s in source['segments']]
    return dict(status='same_trial_light_paths_and_tau_argument_expansion_connected',document=FULL,**results,alignment=dict(segments=alignment),verified_full_units={'kant-1784':0,'einstein-1905':0},general_real_field_laws_proved=False,general_physical_derivation_proved=False,concrete_tau_transformation_derived=False,semantic_equivalence_automatically_proved=False,remaining=['u0051–u0053全体の通読判断登録','u0054以降と二作品全体の目標'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
