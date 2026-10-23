"""Check local limit conditions, fixed slices and attributed derivative equations."""
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
from scripts.check_rod_geometry import instantiate
from scripts.compose_differential_step import ROOT,read,PARENT_BASIS,FULL,CORE,BASIS,ANNOTATIONS,INDEX,MEANINGS,LIMITS,build

DOC='docs/differential-step-v1.md';SOURCE='data/einstein-differential-step-source-reading-v1.json'
INVENTORY='artifacts/written-units-v1/einstein-1905.json'
PRIORS=tuple(f'data/einstein-light-time-expansion-u{n:04d}-review-v1.json' for n in (51,52,53))
DEPENDENCIES=('reports/light-time-expansion-v1.json','reports/tau-differential-v1.json','reports/homogeneity-claim-v1.json')
LEGACY='examples/v014/einstein-tau-differential.noema'
RS=dict(kind='function',parameters=['number'],result='truth')
CONSTANTS={'ra':'frame','zc7':'time','zb6':'context','rd':'author','eirf':'paper','eisms':'section','ri':'discourse','zdq':'trial','zd2':'expansion','zea':'differential','zeb':'rewrite'}
DOMAIN=('frame','time','author','paper','section','trial','expansion','differential','rewrite','depart','tuple','other')

@lru_cache(None)
def fixture(name,mode='boundary'):
    doc=extract_document(parse(read(CORE)),roots=[name],statement_indices=[]).document
    boundaries=NUM|{'bj','sjd'}
    if name=='ei2v':boundaries|={'skc','sjv','sjw'}
    if name=='ei2w':boundaries|={'ei2p','ei2v'}
    if name=='ei2x':boundaries.add('ei2w')
    if name=='sjw' and mode!='native':boundaries.add('sjs')
    if name=='skc' and mode=='instance':boundaries.add('sjg')
    abstract(doc,boundaries);doc=extract_document(doc,roots=[name],statement_indices=[]).document
    d=next(d for d in doc['declarations'] if d['name']==name)
    if name=='skc' and mode=='instance':assert instantiate(d)==[RS]
    slots=[];args=[]
    for i,p in enumerate(d['parameters']):
        n='jdsp'+number_word(i);slots.append(n);doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']));args.append(dict(kind='call',symbol=n,arguments=[]))
    expr=dict(kind='call',symbol=name,arguments=args)
    if d['result']=='content':
        doc['declarations'].append(dict(kind='primitive',name='jdsppoint',parameters=[],result='situation'));expr=dict(kind='evaluate',content=expr,situation=dict(kind='call',symbol='jdsppoint',arguments=[]))
    doc['statements']=[dict(kind='ask',body=expr)];return doc,slots

def run(name,args,m,mode='boundary'):
    doc,slots=fixture(name,mode);assert len(args)==len(slots)
    mm={n:lambda x=x:x for n,x in CONSTANTS.items()}|m|{n:lambda x=x:x for n,x in zip(slots,args)};mm.setdefault('jdsppoint',lambda:'discourse')
    return evaluate_document(doc,individuals=DOMAIN,situations=('context','discourse','other'),primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=300000,memoize_definitions=True,memoize_expressions=True)[0]['value']

def model():
    cuts,m=numbers();c=cuts.make;r=cuts.read
    m['bj']=lambda scale,val:c(scale*r(val))
    def inverse(x):
        if r(x)<=0:forbidden()
        return c(1/r(x))
    m['sjd']=inverse
    fn=FunctionValue((RS,)*4,RS,lambda x,y,z,t:c(-r(x)/4+3*r(y)+7*r(z)+2*r(t)))
    for n,value in {'tc':3,'zb7':1,'zd5':Q(1,2),'zd6':Q(-1,4),'zd7':2}.items():m[n]=lambda value=value:c(Q(value))
    m['zd4']=lambda:fn;m['qe']=lambda tr:'depart' if tr=='trial' else forbidden()
    m['zdz']=lambda e,f,ctx:'tuple' if (e,f,ctx)==('depart','frame','context') else forbidden()
    m['zc6']=lambda tup,role:c(Q(5)) if (tup,role)==('tuple','time') else forbidden()
    ordinary=norm_factory(cuts,())
    def norm(xs):return tuple(tuple(r(x(*(c(Q(a)) for a in point))) for point in ((0,0,0,5),(1,2,3,4))) if isinstance(x,FunctionValue) and len(x.parameters)==4 else ordinary((x,))[0] for x in xs)
    return cuts,m,fn,norm

@lru_cache(None)
def premise_checks():
    cuts,m,fn,norm=model();c=cuts.make
    args=[fn,*map(c,map(Q,(3,1,5,Q(1,2),Q(-1,4),2)))];finger=norm((fn,))[0]
    point=(finger,Q(0),Q(0),Q(0),Q(5),Q(-1,4),Q(2))
    rows={'skc':{(finger,Q(3),Q(1),Q(5),Q(1,2))},'sjv':{point},'sjw':{point}}
    m|={n:lambda *xs,rs=rs:norm(xs) in rs for n,rs in rows.items()}
    check=lambda mm:run('ei2v',args,mm);count=perturb(check,m,rows,norm)
    for slot in range(1,7):
        bad=args.copy();bad[slot]=c(cuts.read(bad[slot])+1);assert not run('ei2v',bad,m);count+=1
    for speed in (0,-1,3,4):
        bad=args.copy();bad[2]=c(Q(speed));assert not run('ei2v',bad,m);count+=1
    unknowns(check,m,('ba','bg','bb'))
    whole={'ei2p':{()},'ei2v':{norm(args)}};mm=m|{n:lambda *xs,rs=rs:norm(xs) in rs for n,rs in whole.items()}
    count+=perturb(lambda mm:run('ei2w',[],mm),mm,whole,norm)
    unknowns(lambda mm:run('ei2w',[],mm),mm,('zd4','tc','zb7','zd5','zd6','zd7','qe','zdz','zc6'))
    assert run('ei2w',[],mm|{'sjl':forbidden,'skd':forbidden});count+=1
    for truth in (False,True):assert run('ei2x',[],{'ei2w':lambda truth=truth:truth})==truth;count+=1
    return dict(cases=count,current_physical_premise_and_same_tau_time_radius_and_partials_bound=True,separate_partials_not_substituted_for_total_differentiability=True,old_sjl_and_skd_not_used=True)

@lru_cache(None)
def neighborhood_checks():
    cuts,m,fn,norm=model();c=cuts.make;count=0
    for h in (Q(-1),Q(0),Q(1,8),Q(1,4),Q(1,2),Q(3,4)):
        xs=[fn,c(Q(3)),c(Q(1)),c(Q(5)),c(Q(1,2)),c(h)]
        for truth in (False,True):
            seen=[]
            def midpoint(*args):seen.append(norm(args));return truth
            assert run('skc',xs,m|{'sjg':midpoint},'instance')==(truth or not 0<h<Q(1,2));count+=1
            assert seen==[(norm((fn,))[0],h,Q(3),Q(1),Q(5))]
    for radius in (0,-1):
        assert not run('skc',[fn,*map(c,map(Q,(3,1,5,radius,Q(1,4))))],m|{'sjg':lambda *xs:True},'instance');count+=1
    args=[fn,*map(c,map(Q,(3,1,5,Q(1,2),Q(1,4))))]
    row=norm([fn,*map(c,map(Q,(Q(1,4),3,1,5)))])
    mm=m|{'sjg':lambda *xs:norm(xs)==row}
    count+=perturb(lambda mm:run('skc',args,mm,'instance'),mm,{'sjg':{row}},norm)
    return dict(cases=count,strict_positive_radius_and_all_interior_positive_steps_preserved=True,instances_check_scope_not_the_full_neighborhood=True,same_midpoint_function_and_all_five_arguments_bound=True)

@lru_cache(None)
def slice_checks():
    cuts,m,fn,norm=model();c=cuts.make;r=cuts.read;observed=[];count=0
    # Fingerprints distinguish the two native slice closures; they do not prove limits.
    def derivative(domain,f,point,result):
        p=r(point);d=r(result);samples=tuple(r(f(c(p+h))) for h in (Q(-1),Q(0),Q(2)))
        observed.append((p,d,samples))
        return domain(point) and (p,d,samples) in {(Q(0),Q(-1,4),(Q(41,4),Q(10),Q(19,2))),(Q(5),Q(2),(Q(8),Q(10),Q(14)))}
    args=[fn,*map(c,map(Q,(0,0,0,5,Q(-1,4),2)))];mm=m|{'sjs':derivative}
    assert run('sjw',args,mm);count+=1;assert len(observed)==2
    for slot in range(1,7):
        bad=args.copy();bad[slot]=c(r(bad[slot])+1);assert not run('sjw',bad,mm);count+=1
    wrong=FunctionValue((RS,)*4,RS,lambda x,y,z,t:c(r(x)/4+3*r(y)+7*r(z)+2*r(t)))
    assert not run('sjw',[wrong,*args[1:]],mm);count+=1
    unknowns(lambda m:run('sjw',args,m),mm,('sjs','ba'))
    return dict(cases=count,both_native_slices_fix_the_other_three_coordinates=True,both_values_belong_to_the_same_function_and_point=True,finite_affine_fingerprints_not_limit_proofs=True)

@lru_cache(None)
def equation_checks():
    cuts,m,fn,norm=model();c=cuts.make;count=0
    for V,s,px,pt,expected in ((3,1,Q(-1,4),2,True),(3,1,-1,8,True),(5,2,Q(-2,21),1,True),(3,0,0,8,True),(3,1,1,8,False),(3,1,-1,4,False),(3,1,8,-1,False),(3,-1,-1,8,False)):
        args=list(map(c,map(Q,(V,s,px,pt))))
        for name in ('sjx','sjy'):assert run(name,args,m)==expected;count+=1
    for name in ('skf','skg'):
        assert run(name,[],m);assert not run(name,[],m|{'zd6':lambda:c(Q(1,4))});count+=2
    assert not run('skf',[],m|{'bj':lambda scale,val:val});count+=1
    for name in ('sjx','sjy'):
        for speed in (3,4):
            try:run(name,list(map(c,map(Q,(3,speed,-1,8)))),m)
            except ValueError as e:assert 'Unknown clock-site-time' in str(e)
            else:raise AssertionError('Invalid reciprocal silently fabricated')
            count+=1
    unknowns(lambda mm:run('skf',[],mm),m,('tc','zb7','zd6','zd7','sjd','bj','bd','bf','shv','sca','ba','bc','bg'))
    unknowns(lambda mm:run('skg',[],mm),m,('sjd','bf','shv','sca'))
    return dict(cases=count,native_both_equations_and_same_partials_preserved=True,denominator_signs_half_and_speed_factor_checked=True,invalid_reciprocal_rejected=True)

@lru_cache(None)
def finite_refusals():
    cuts,m,fn,norm=model();c=cuts.make;results={}
    for name,args in (('skc',[fn,*map(c,map(Q,(3,1,5,Q(1,2))))]),('sjv',[fn,*map(c,map(Q,(0,0,0,5,Q(-1,4),2)))]),('sjw',[fn,*map(c,map(Q,(0,0,0,5,Q(-1,4),2)))])):
        try:run(name,args,m,'native')
        except ValueError as e:assert 'Cannot finitely quantify' in str(e);results[name]=str(e)
        else:raise AssertionError('Finite evaluator accepted a full real limit')
    return dict(full_real_neighborhood_and_derivatives_refused=True,reasons=results)

@lru_cache(None)
def presentation_checks():
    count=0
    for name,rows in (
      ('ei2y',{'zc':{('differential','author','ei2x','skf','section','discourse')}}),
      ('ei23',{'zd3':{('rewrite','author','ei2x','skf','skg','section','discourse')}}),
      ('ei22',{'eir3':{('differential','author','paper','ei2z','discourse')},'ue':{('expansion','differential','discourse')}}),
      ('ei25',{'eir3':{('rewrite','author','paper','ei24','discourse')},'ue':{('differential','rewrite','discourse')}})):
        m={n:relation(rs) for n,rs in rows.items()};count+=perturb(lambda mm:run(name,[],mm),m,rows)
        assert run(name,[],m|{n:forbidden for n in ('ei2x','skf','skg','ei2w','ei2p')});count+=1
    return dict(cases=count,same_premise_and_two_equations_in_inference_and_reexpression=True,author_section_and_order_preserved=True,quoted_inference_not_executed_as_truth=True)

@lru_cache(None)
def source_record():
    inv=json.loads(read(INVENTORY));units=inv['units'][53:57];maths={m['id']:m for m in inv['math']}
    assert [(u['id'],len(u['text'])) for u in units]==[(f'einstein-1905:u{n:04d}',length) for n,length in ((54,54),(55,7),(56,4),(57,7))]
    forms={'M0102':'x′','M0103':'12(1V−v+1V+v)∂τ∂t=∂τ∂x′+1V−v∂τ∂t,','M0104':'∂τ∂x′+vV2−v2∂τ∂t=0.'}
    fractions={'M0102':[],'M0103':[['1','2'],['1','V−v'],['1','V+v'],['∂τ','∂t'],['∂τ','∂x′'],['1','V−v'],['∂τ','∂t']],'M0104':[['∂τ','∂x′'],['v','V2−v2'],['∂τ','∂t']]}
    entries={}
    for mid,form in forms.items():
        node=ET.fromstring(maths[mid]['mathml']);assert ''.join(node.itertext())==form
        assert [[''.join(c.itertext()) for c in n] for n in node.iter() if n.tag.split('}')[-1]=='mfrac']==fractions[mid]
        entries[mid]=dict(id=mid,sha256=maths[mid]['sha256'],reading=form)
    segments=[dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[0,len(u['text'])],text=u['text'],source_nonblank_characters=len(re.sub(r'\s|\[M\d+\]','',u['text'])),math=[entries[n] for n in u['math_ids']]) for u in units]
    assert [s['source_nonblank_characters'] for s in segments]==[40,0,4,0]
    paths={INVENTORY,DOC,'artifacts/einstein-differential-step-v1/page-899.html','artifacts/einstein-differential-step-v1/page-899.jpg','artifacts/einstein-differential-step-v1/retrieval.json','data/einstein-light-time-expansion-source-reading-v1.json'}
    return dict(version='einstein-differential-step-source-reading-v1',reviewer='assistant_visual_and_text_review',pages=['899'],segments=segments,observations=['原刊899頁冒頭のHieraus folgtから最初の表示式、oder、整理後の式の句点までを照合した。','無限小に選ぶ量はx′である。二式の∂τ/∂x′と∂τ/∂tは同じ候補の同じ評価点の二偏微分であり、係数のみの任意の二数へ替えない。','M0103の半分と二逆数、M0104の分子vと分母V²-v²、各加号と等号を保持する。','直後は任意の出発点への一般化であり、ここでその全位置への結論を先取りしない。'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert new.document['statements'][:-2]==old.document['statements'] and len(new.document['statements'])==282
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations']
    assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    for path in PRIORS:
        prior=json.loads(read(path));validate_hashes(ROOT,prior['source_sha256']);assert selection_binding(new,[279])==prior['selection']
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    load_annotations(ROOT,BASIS,ANNOTATIONS);assert json.loads(read(ANNOTATIONS))['entries']==json.loads(read('data/light-time-expansion-identifiers-v1.json'))['entries']
    doc=parse(read(CORE));ds={d['name']:d for d in doc['declarations']};legacy={d['name']:d for d in parse(read(LEGACY))['declarations']}
    reused=('sjd','sjt','sjo','sjp','sjq','sjr','sjs','sjv','sjw','sjx','sjy','skc','skf','skg')
    assert all(ds[n]==legacy[n] for n in reused)
    assert all(ds[n]['body']['force']=='assert' for n in ('ei2z','ei24'))
    for style in ('compact','full'):
        body=format_graph(doc,style);assert parse(body)==parse(transcribe(body,alphabet='v2'))==doc
    assert json.loads(read(SOURCE))==source_record()
    return dict(new_definitions=len(MEANINGS),new_primitives=0,preserved_statements=280,all_prior_expansion_reviews_preserved=True,limits_derivatives_and_equations_unchanged=True)

def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/SOURCE,json.dumps(source_record(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    results={n:f() for n,f in [('premise',premise_checks),('neighborhood',neighborhood_checks),('slices',slice_checks),('equations',equation_checks),('refusals',finite_refusals),('presentation',presentation_checks),('structure',structure_checks)]}
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(source_record()['source_sha256'])|{SOURCE,DOC,*PRIORS,*DEPENDENCIES,LEGACY,'scripts/compose_differential_step.py','scripts/check_differential_step.py','tests/test_differential_step.py','scripts/check_coordinate_correspondence.py','scripts/check_moving_trip_geometry.py','scripts/check_material_relative_frame.py','scripts/check_clock_site_time.py','scripts/check_rod_methods.py','scripts/check_rod_geometry.py','scripts/compose_limits.py','scripts/compose_relativity_conjecture.py','scripts/compose_material_relative_frame.py','scripts/compose_two_postulates.py'}
    alignment=[dict(unit=s['unit'],unit_sha256=s['unit_sha256'],range=s['range'],source=s['text'],statements=[INDEX+(i//2)],definitions=list(MEANINGS),status='explicit_interpretive_annotation') for i,s in enumerate(source_record()['segments'])]
    return dict(status='same_tau_local_limit_and_differential_equations_connected',document=FULL,**results,alignment=dict(segments=alignment),verified_full_units={'kant-1784':0,'einstein-1905':0},general_real_chain_rule_proved=False,affine_coordinate_claim_automatically_extended_to_full_neighborhood=False,concrete_tau_transformation_derived=False,semantic_equivalence_automatically_proved=False,remaining=['u0054–u0057の通読判断登録','u0058以降と二作品全体の目標'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
