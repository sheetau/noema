"""Check pointwise possible choices, shifted derivatives and all-space scope."""
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
from scripts.check_translated_light_trial import expose
from scripts.compose_arbitrary_start_claim import ROOT,read,PARENT_BASIS,FULL,CORE,BASIS,ANNOTATIONS,INDEX,MEANINGS,LIMITS,build

DOC='docs/arbitrary-start-claim-v1.md';SOURCE='data/einstein-arbitrary-start-claim-source-reading-v1.json'
INVENTORY='artifacts/written-units-v1/einstein-1905.json';PRIOR='data/einstein-differential-step-u0057-review-v1.json'
DEPENDENCIES=('reports/translated-light-trial-v1.json','reports/differential-step-v1.json','reports/arbitrary-origins-v1.json')
LEGACY='examples/v014/einstein-arbitrary-origins.noema'
RS=dict(kind='function',parameters=['number'],result='truth')
CONSTANTS={'ra':'frame','zc7':'time','zb6':'context','rd':'author','eirf':'paper','eisms':'section','ri':'discourse','zdq':'trial','zee':'actor','zeg':'notice','zeh':'consequence','zeb':'previous'}
DOMAIN=('a','b','point','trial','actor','frame','time','author','paper','section','notice','consequence','previous','depart','tuple','other')
POINTS=('context','other','discourse')

@lru_cache(None)
def fixture(name,mode='boundary'):
    doc=extract_document(parse(read(CORE)),roots=[name],statement_indices=[]).document;boundaries=NUM|{'bj','sjd'}
    if name=='ei3m':boundaries|={'ei3l','ei3k','skl'}
    if name=='ei3n':boundaries|={'ei3l','ei3m'}
    if name=='ei3o':boundaries|={'ei3c','ei3n'}
    if name=='ei3p':boundaries|={'ei2w','ei3o'}
    if name=='skk':boundaries.add('skc')
    if name=='skl':boundaries|={'skk','sjv','sjw'}
    if name=='skm':boundaries.add('sjw')
    if name=='skn':boundaries.add('skm')
    if name=='skv':boundaries.add('skn')
    abstract(doc,boundaries);doc=extract_document(doc,roots=[name],statement_indices=[]).document
    d=next(d for d in doc['declarations'] if d['name']==name)
    if mode=='instance':
        expected={'ei3o':3,'skl':3,'skm':2,'skn':3}[name];assert len(expose(d,{'forall','exists'},RS))==expected
    slots=[];args=[]
    for i,p in enumerate(d['parameters']):
        n='jasc'+number_word(i);slots.append(n);doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']));args.append(dict(kind='call',symbol=n,arguments=[]))
    expr=dict(kind='call',symbol=name,arguments=args)
    if d['result']=='content':
        doc['declarations'].append(dict(kind='primitive',name='jascpoint',parameters=[],result='situation'));expr=dict(kind='evaluate',content=expr,situation=dict(kind='call',symbol='jascpoint',arguments=[]))
    doc['statements']=[dict(kind='ask',body=expr)];return doc,slots

def run(name,args,m,mode='boundary',domain=DOMAIN):
    doc,slots=fixture(name,mode);assert len(args)==len(slots),(name,len(args),len(slots))
    mm={n:lambda x=x:x for n,x in CONSTANTS.items()}|m|{n:lambda x=x:x for n,x in zip(slots,args)};mm.setdefault('jascpoint',lambda:'discourse')
    return evaluate_document(doc,individuals=domain,situations=POINTS,primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=400000,memoize_definitions=True,memoize_expressions=True)[0]['value']

def model():
    cuts,m=numbers();c=cuts.make;r=cuts.read
    fn=FunctionValue((RS,)*4,RS,lambda x,y,z,t:c(-r(x)/4+3*r(y)+7*r(z)+2*r(t)))
    m|={'tc':lambda:c(Q(3)),'zb7':lambda:c(Q(1)),'zd4':lambda:fn,'bj':lambda scale,val:c(scale*r(val))}
    def inverse(x):
        if r(x)<=0:forbidden()
        return c(1/r(x))
    m['sjd']=inverse
    m['qe']=lambda tr:'depart' if tr=='trial' else forbidden();m['zdz']=lambda e,f,ctx:'tuple' if (e,f,ctx)==('depart','frame','context') else forbidden();m['zc6']=lambda tup,role:c(Q(5)) if (tup,role)==('tuple','time') else forbidden()
    ordinary=norm_factory(cuts,())
    def norm(xs):return tuple(tuple(r(x(*(c(Q(a)) for a in point))) for point in ((0,0,0,5),(1,2,3,4))) if isinstance(x,FunctionValue) and len(x.parameters)==4 else ordinary((x,))[0] for x in xs)
    return cuts,m,fn,norm

def relations(m,rows,norm):return m|{n:lambda *xs,rs=rs:norm(xs) in rs for n,rs in rows.items()}

@lru_cache(None)
def connection_checks():
    cuts,m,fn,norm=model();c=cuts.make;xyz=tuple(map(Q,(7,2,-3,5)));finger=norm((fn,))[0]
    rows={'ei3l':{('point',*xyz,ctx) for ctx in ('context','other')},'ei3k':{('trial','point',*xyz,'other')},'skl':{(finger,*xyz[:3],Q(3),Q(1),xyz[3])}}
    m=relations(m,rows,norm);args=['trial','point',*map(c,xyz),'context','other'];check=lambda mm:run('ei3m',args,mm)
    count=perturb(check,m,rows,norm)
    for slot in range(2,6):
        bad=args.copy();bad[slot]=c(cuts.read(bad[slot])+1);assert not run('ei3m',bad,m);count+=1
    assert not run('ei3m',args[:-2]+['other','context'],m);count+=1
    unknowns(check,m,('zd4','tc','zb7'))
    assert check(m|{'sko':forbidden,'skr':forbidden,'sio':forbidden,'shd':forbidden,'sgp':forbidden,'sbc':forbidden});count+=1
    return dict(cases=count,same_point_coordinates_time_and_function_in_both_contexts=True,current_full_trial_and_shifted_local_differentiability_required=True,old_physical_bindings_not_used=True)

@lru_cache(None)
def choice_checks():
    cuts,m,fn,norm=model();c=cuts.make;domain=('a','b');xyz1=tuple(map(Q,(2,3,4,5)));xyz2=tuple(map(Q,(7,-2,1,5)))
    places={('a',*xyz1,'context'),('b',*xyz2,'context')};available={('a','a','context'),('a','b','context')}
    outcomes={('a','a','context','other'),('a','b','context','discourse')};success={('a','a',*xyz1,'context','other'),('b','b',*xyz2,'context','discourse')}
    base=relations(m,{'ei3l':places,'zec':available,'zed':outcomes,'ei3m':success},norm)|{'zee':lambda:'a'}
    check=lambda mm:[run('ei3n',[*map(c,xyz),'context'],mm,domain=domain) for xyz in (xyz1,xyz2)]
    count=0
    scenarios={
      'baseline':({},[True,True]),
      'extra_failing_outcome':({'zed':lambda *xs:xs in outcomes|{('a','a','context','discourse')}},[True,True]),
      'no_available_trial':({'zec':lambda *xs:False},[False,False]),
      'no_possible_result':({'zed':lambda *xs:False},[False,False]),
      'only_first_point':({'ei3m':lambda *xs:norm(xs) in {('a','a',*xyz1,'context','other')}},[True,False]),
      'different_trial_success':({'ei3m':lambda *xs:norm(xs) in {('b','a',*xyz1,'context','other'),('a','b',*xyz2,'context','discourse')}},[False,False]),
      'different_point_success':({'ei3m':lambda *xs:norm(xs) in {('a','b',*xyz1,'context','other'),('b','a',*xyz2,'context','discourse')}},[False,False]),
      'wrong_actor':({'zee':lambda:'b'},[False,False]),
      'baseline_not_a_success':({'ei3m':lambda *xs:norm(xs) in {('a','a',*xyz1,'context','context'),('b','b',*xyz2,'context','context')}},[False,False]),
      'missing_baseline_point':({'ei3l':lambda *xs:norm(xs) in {('a',*xyz1,'context')}},[True,False]),
    }
    for patch,expected in scenarios.values():assert check(base|patch)==expected;count+=2
    unknowns(lambda mm:run('ei3n',[*map(c,xyz1),'context'],mm,domain=domain),base,('zee','zec','zed','ei3m','ei3l'))
    # Another available plan can serve the same point; no point-to-plan identity rule.
    swapped=relations(base,{'zed':{('a','b','context','other'),('a','a','context','discourse')},'ei3m':{('b','a',*xyz1,'context','other'),('a','b',*xyz2,'context','discourse')}},norm)
    assert check(swapped)==[True,True];count+=2
    return dict(cases=count,native_pointwise_existence_and_possible_outcome_binding=True,different_points_can_choose_different_trials=True,possibility_not_actual_execution_or_all_outcome_guarantee=True)

@lru_cache(None)
def shift_checks():
    cuts,m,fn,norm=model();c=cuts.make;r=cuts.read;count=0
    polynomial=FunctionValue((RS,)*4,RS,lambda x,y,z,t:c(r(x)**2+2*r(y)+3*r(z)+4*r(t)))
    probes=((0,0,0,5),(1,0,0,5),(0,1,0,5),(0,0,1,5),(0,0,0,6))
    def nearby(f,V,s,t,radius):return tuple(r(a) for a in (V,s,t,radius))==(3,1,5,Q(1,2)) and tuple(r(f(*(c(Q(a)) for a in p))) for p in probes)==(42,47,44,45,46)
    args=[polynomial,*map(c,map(Q,(2,3,4,3,1,5,Q(1,2))))];mm=m|{'skc':nearby}
    assert run('skk',args,mm);count+=1
    for slot in range(1,8):
        bad=args.copy();bad[slot]=c(r(bad[slot])+1);assert not run('skk',bad,mm);count+=1
    wrong=FunctionValue((RS,)*4,RS,lambda x,y,z,t:c(r(x)**2+2*r(y)+3*r(z)+4*r(t)+1))
    assert not run('skk',[wrong,*args[1:]],mm);count+=1
    unknowns(lambda mm:run('skk',args,mm),mm,('skc','bd'))
    return dict(cases=count,native_spatial_shift_preserves_time_and_function_values=True,all_three_offsets_and_local_neighborhood_arguments_distinguished=True,finite_fingerprints_not_neighborhood_proof=True)

@lru_cache(None)
def derivative_checks():
    cuts,m,fn,norm=model();c=cuts.make;r=cuts.read;finger=norm((fn,))[0]
    args=[fn,*map(c,map(Q,(7,2,-3,3,1,5,Q(1,2),Q(-1,4),2)))]
    point=(finger,Q(7),Q(2),Q(-3),Q(5),Q(-1,4),Q(2))
    rows={'skk':{(finger,Q(7),Q(2),Q(-3),Q(3),Q(1),Q(5),Q(1,2))},'sjv':{point},'sjw':{point}}
    mm=relations(m,rows,norm);count=perturb(lambda mm:run('skl',args,mm,'instance'),mm,rows,norm)
    # A quadratic solution of the local coefficient equation has different
    # derivatives at different points. This fixture is not a whole light model.
    quadratic=FunctionValue((RS,)*4,RS,lambda x,y,z,t:c((r(t)-r(x)/8)**2+3*r(y)+7*r(z)))
    values=[]
    for x,y,z,t in ((0,2,-3,5),(7,2,-3,5),(-2,1,4,3)):
        u=Q(t)-Q(x,8);px=-u/4;pt=2*u;values.append((px,pt))
        def partials(f,xx,yy,zz,tt,a,b):
            at=lambda h,k:r(f(c(r(xx)+h),yy,zz,c(r(tt)+k)))
            return r(a)==(at(1,0)-at(-1,0))/2 and r(b)==(at(0,1)-at(0,-1))/2
        qargs=[quadratic,*map(c,map(Q,(x,y,z,3,1,t,px,pt)))];qm=m|{'sjw':partials}
        assert run('skm',qargs,qm,'instance');count+=1
        bad=qargs.copy();bad[-2]=c(px+1);assert not run('skm',bad,qm,'instance');count+=1
        if x!=0:
            bad=qargs.copy();bad[-2:]=[c(values[0][0]),c(values[0][1])];assert not run('skm',bad,qm,'instance');count+=1
    assert len(set(values))==3
    return dict(cases=count,same_function_point_and_partials_in_neighborhood_and_derivative_conditions=True,each_point_has_its_own_derivative_values=True,origin_candidates_not_reused_as_global_constants=True,quadratic_central_differences_are_fixture_bindings_not_general_derivative_proofs=True)

@lru_cache(None)
def scope_checks():
    cuts,m,fn,norm=model();c=cuts.make;r=cuts.read;finger=norm((fn,))[0];xyz=tuple(map(Q,(7,2,-3)))
    rows={'ei3c':{(finger,'context')},'ei3n':{(*xyz,Q(5),'context')}};mm=relations(m,rows,norm)
    args=[c(Q(5)),'context',*map(c,xyz)];count=perturb(lambda mm:run('ei3o',args,mm,'instance'),mm,rows,norm)
    for speed in (0,-1,3,4):assert not run('ei3o',args,mm|{'zb7':lambda speed=speed:c(Q(speed))},'instance');count+=1
    whole={'ei2w':{()},'ei3o':{(Q(5),'context')}};mm=relations(m,whole,norm);count+=perturb(lambda mm:run('ei3p',[],mm),mm,whole,norm)
    unknowns(lambda mm:run('ei3p',[],mm),mm,('qe','zdz','zc6'))
    rows={'skm':{(finger,*xyz,Q(3),Q(1),Q(5))}};mm=relations(m,rows,norm)
    args=[fn,c(Q(3)),c(Q(1)),c(Q(5)),*map(c,xyz)];count+=perturb(lambda mm:run('skn',args,mm,'instance'),mm,rows,norm)
    rows={'skn':{(finger,Q(3),Q(1),Q(5))}};mm=relations(m,rows,norm);count+=perturb(lambda mm:run('skv',[],mm),mm,rows,norm)
    refusal={}
    for name,args in (('ei3o',[c(Q(5)),'context']),('skl',[fn,*map(c,map(Q,(7,2,-3,3,1,5)))]),('skm',[fn,*map(c,map(Q,(7,2,-3,3,1,5)))]),('skn',[fn,*map(c,map(Q,(3,1,5)))])):
        try:run(name,args,m|{'ei3c':lambda *xs:True})
        except ValueError as e:assert 'Cannot finitely quantify' in str(e);refusal[name]=str(e)
        else:raise AssertionError('Finite evaluation accepted all real spatial or derivative values')
    return dict(cases=count,all_three_spatial_axes_and_same_time_preserved=True,previous_origin_premise_and_same_full_tau_binding_retained=True,real_quantification_refused=refusal)

@lru_cache(None)
def presentation_checks():
    count=0
    for name,rows in (
     ('ei3q',{'uh':{('notice','author','ei3p','section','discourse')},'zei':{('notice','author','section','discourse')}}),
     ('ei3t',{'zc':{('consequence','author','ei3p','skv','section','discourse')}}),
     ('ei3s',{'eir3':{('notice','author','paper','ei3r','discourse')},'ue':{('previous','notice','discourse')}}),
     ('ei3v',{'eir3':{('consequence','author','paper','ei3u','discourse')},'ue':{('notice','consequence','discourse')}})):
        m={n:relation(rs) for n,rs in rows.items()};count+=perturb(lambda mm:run(name,[],mm),m,rows)
        assert run(name,[],m|{n:forbidden for n in ('ei3p','skv','ei3o','skn')});count+=1
    return dict(cases=count,notice_possible_choice_and_same_equation_consequence_connected=True,author_section_source_order_and_nonexecution_of_quoted_content_preserved=True)

@lru_cache(None)
def source_record():
    inv=json.loads(read(INVENTORY));u=inv['units'][57];m=next(m for m in inv['math'] if m['id']=='M0105')
    assert u['id']=='einstein-1905:u0058' and len(u['text'])==213 and u['math_ids']==['M0105']
    assert u['text_sha256']=='aaf3e6f0074746f5214ec50f0cc7db0c57dca4aaa4b21a7e41a69bb989b539a3'
    node=ET.fromstring(m['mathml']);assert ''.join(node.itertext())=='x′,y,z'
    prior='data/einstein-differential-step-source-reading-v1.json';validate_hashes(ROOT,json.loads(read(prior))['source_sha256'])
    paths={INVENTORY,DOC,prior,'artifacts/einstein-differential-step-v1/page-899.html','artifacts/einstein-differential-step-v1/page-899.jpg','artifacts/einstein-differential-step-v1/retrieval.json'}
    segment=dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[0,len(u['text'])],text=u['text'],source_nonblank_characters=len(re.sub(r'\s|\[M\d+\]','',u['text'])),math=[dict(id=m['id'],sha256=m['sha256'],reading='x′,y,z')]);assert segment['source_nonblank_characters']==175
    return dict(version='einstein-arbitrary-start-claim-source-reading-v1',reviewer='assistant_visual_and_text_review',pages=['899'],segments=[segment],observations=['原刊899頁のEs ist zu bemerkenから全てのx′,y,zで式が成り立つという文末までを照合した。','hätten wählen könnenは原点の代わりの出発点の選択可能性であり、実際に全地点から光を発したことではない。','eben erhaltene Gleichungは直前のτx′+v/(V²-v²)τt=0を指す。後続のY/Z方向の式ではない。','M0105はx′,y,zの三空間値でありtを含まない。次の類似議論の横軸と混ぜない。'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert new.document['statements'][:-2]==old.document['statements'] and len(new.document['statements'])==284
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations']
    assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    prior=json.loads(read(PRIOR));validate_hashes(ROOT,prior['source_sha256']);assert selection_binding(new,[281])==prior['selection']
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    load_annotations(ROOT,BASIS,ANNOTATIONS);assert json.loads(read(ANNOTATIONS))['entries']==json.loads(read('data/translated-light-trial-identifiers-v1.json'))['entries']
    doc=parse(read(CORE));ds={d['name']:d for d in doc['declarations']};legacy={d['name']:d for d in parse(read(LEGACY))['declarations']}
    assert all(ds[n]==legacy[n] for n in ('ski','skj','skk','skl','skm','skn','skv'))
    assert all(ds[n]['body']['force']=='assert' for n in ('ei3r','ei3u'))
    for style in ('compact','full'):
        body=format_graph(doc,style);assert parse(body)==parse(transcribe(body,alphabet='v2'))==doc
    assert json.loads(read(SOURCE))==source_record()
    return dict(new_definitions=len(MEANINGS),new_primitives=0,preserved_statements=INDEX,previous_differential_judgment_preserved=True,spatial_shifts_possible_choices_and_local_global_derivative_definitions_unchanged=True)

def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/SOURCE,json.dumps(source_record(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    results={n:f() for n,f in [('connection',connection_checks),('choice',choice_checks),('shift',shift_checks),('derivatives',derivative_checks),('scope',scope_checks),('presentation',presentation_checks),('structure',structure_checks)]}
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(source_record()['source_sha256'])|{SOURCE,DOC,PRIOR,*DEPENDENCIES,LEGACY,'scripts/compose_arbitrary_start_claim.py','scripts/check_arbitrary_start_claim.py','tests/test_arbitrary_start_claim.py','scripts/check_coordinate_correspondence.py','scripts/check_moving_trip_geometry.py','scripts/check_material_relative_frame.py','scripts/check_clock_site_time.py','scripts/check_rod_methods.py','scripts/check_translated_light_trial.py','scripts/compose_limits.py','scripts/compose_relativity_conjecture.py','scripts/compose_material_relative_frame.py','scripts/compose_two_postulates.py'}
    s=source_record()['segments'][0];alignment=dict(segments=[dict(unit=s['unit'],unit_sha256=s['unit_sha256'],range=s['range'],source=s['text'],statements=[INDEX,INDEX+1],definitions=list(MEANINGS),status='explicit_interpretive_annotation')])
    return dict(status='pointwise_possible_starts_and_all_space_differential_claim_connected',document=FULL,**results,alignment=alignment,verified_full_units={'kant-1784':0,'einstein-1905':0},all_spatial_trial_choices_exist_proved=False,general_real_physical_derivation_proved=False,semantic_equivalence_automatically_proved=False,remaining=['u0058の一文全体の通読判断登録','u0059以降と二作品全体の目標'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
