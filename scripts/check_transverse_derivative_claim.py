"""Check complete transverse scope, calculus slices and attributed inference."""
from fractions import Fraction as Q
from functools import lru_cache
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
from scripts.check_transverse_light_trial import model as trial_model,square_root,CONSTANTS as PRIOR_CONSTANTS,DOMAIN as PRIOR_DOMAIN
from scripts.compose_transverse_derivative_claim import ROOT,read,PARENT_BASIS,FULL,CORE,BASIS,ANNOTATIONS,INDEX,MEANINGS,build

DOC='docs/transverse-derivative-claim-v1.md';SOURCE='data/einstein-transverse-derivative-source-reading-v1.json'
INVENTORY='artifacts/written-units-v1/einstein-1905.json';PRIOR='data/einstein-arbitrary-start-claim-review-v1.json'
DEPENDENCIES=('reports/transverse-light-trial-v1.json','reports/transverse-time-v1.json','reports/arbitrary-start-claim-v1.json','reports/differential-step-v1.json')
LEGACY='examples/v014/einstein-transverse-time.noema'
RS=dict(kind='function',parameters=['number'],result='truth')
CONSTANTS=PRIOR_CONSTANTS|{'zen':'notice','zeo':'consequence','zeh':'previous','zea':'earlier'}
DOMAIN=tuple(dict.fromkeys([*PRIOR_DOMAIN,'notice','consequence','previous','earlier','a','b','c']))

@lru_cache(None)
def fixture(name,mode='boundary'):
    doc=extract_document(parse(read(CORE)),roots=[name],statement_indices=[]).document;boundaries=NUM|{'bj','sle','sje'}
    if name=='ei34':boundaries.add('ei32')
    if name=='ei35':boundaries|={'ei3d','ei3c','eiyf','eios','ei34'}
    if name=='ei36':boundaries.add('ei35')
    if name=='ei37':boundaries|={'ei35','sll'}
    if name=='slj':boundaries.add('slh')
    if name=='slk':boundaries.add('sjs')
    if name=='slh':boundaries|={'slg','sjv','sjw'}
    if name=='sll':boundaries.add('slj')
    if name=='slm':boundaries.add('slk')
    if name=='slv':boundaries.add('slm')
    abstract(doc,boundaries);doc=extract_document(doc,roots=[name],statement_indices=[]).document
    d=next(d for d in doc['declarations'] if d['name']==name)
    if mode=='instance':assert len(expose(d,{'forall','exists'}))=={'ei34':2,'slh':3,'sll':3,'slm':3}[name]
    slots=[];args=[]
    for i,p in enumerate(d['parameters']):
        n='jtdc'+number_word(i);slots.append(n);doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']));args.append(dict(kind='call',symbol=n,arguments=[]))
    expr=dict(kind='call',symbol=name,arguments=args)
    if d['result']=='content':
        doc['declarations'].append(dict(kind='primitive',name='jtdcpoint',parameters=[],result='situation'));expr=dict(kind='evaluate',content=expr,situation=dict(kind='call',symbol='jtdcpoint',arguments=[]))
    doc['statements']=[dict(kind='ask',body=expr)];return doc,slots

def run(name,args,m,mode='boundary',domain=DOMAIN):
    doc,slots=fixture(name,mode);assert len(args)==len(slots),(name,len(args),len(slots))
    mm={n:lambda x=x:x for n,x in CONSTANTS.items()}|m|{n:lambda x=x:x for n,x in zip(slots,args)};mm.setdefault('jtdcpoint',lambda:'discourse')
    return evaluate_document(doc,individuals=domain,situations=('context','other','discourse'),primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=500000,memoize_definitions=True,memoize_expressions=True)[0]['value']

def relations(m,rows,norm):return m|{n:lambda *xs,rs=rs:norm(xs) in rs for n,rs in rows.items()}

def model():
    cuts,m,coords,fn=trial_model('y');m['zek']=lambda tr,ctx:cuts.make(Q(12)) if (tr,ctx)==('trial','context') else forbidden();m['zel']=lambda tr,ctx:cuts.make(Q(4)) if (tr,ctx)==('trial','context') else forbidden()
    ordinary=norm_factory(cuts,())
    def norm(xs):return tuple(tuple(cuts.read(x(*(cuts.make(Q(a)) for a in p))) for p in ((1,2,3,4),(2,-1,4,5))) if isinstance(x,FunctionValue) and len(x.parameters)==4 else ordinary((x,))[0] for x in xs)
    return cuts,m,coords,fn,norm

@lru_cache(None)
def trial_checks():
    cuts,m,coords,fn,norm=model();c=cuts.make;r=cuts.read;count=0
    for axis in ('y','z'):
        row=('trial',axis,'origin','outward','returning',*map(Q,(12,4,-3,2,-3,5)),'context');rows={'ei32':{row}};mm=relations(m,rows,norm);args=['trial',axis,'context','outward','returning']
        count+=perturb(lambda mm:run('ei34',args,mm,'instance'),mm,rows,norm)
        assert run('ei34',args[:3],mm);assert not run('ei34',args[:3],mm|{'ei32':lambda *xs:False});count+=2
        for n in ('zek','zel'):
            old=mm[n];assert not run('ei34',args,mm|{n:lambda tr,ctx,old=old:c(r(old(tr,ctx))+1)},'instance');count+=1
        for role in ('x','y','z','time'):
            old=mm['zc6'];assert not run('ei34',args,mm|{'zc6':lambda tup,a,old=old,role=role:c(r(old(tup,a))+(1 if a==role else 0))},'instance');count+=1
        unknowns(lambda mm:run('ei34',args,mm,'instance'),mm,('qc','qe','zdz','zc6','zek','zel','zb7','bf','shv'))
    return dict(cases=count,same_departure_point_coordinates_time_gap_and_component_bound=True,two_native_segment_witnesses_required=True,all_argument_slots_checked_on_exposed_body=True)

@lru_cache(None)
def scope_checks():
    cuts,m,coords,fn,norm=model();c=cuts.make;finger=norm((fn,))[0];domain=('a','b','c')
    rows={'ei3d':{('context','a')},'ei3c':{(finger,'context')},'eiyf':{('a','context')},'eios':{(Q(5),'context')},'zem':{('context',)},'zej':{('a','b','context'),('b','c','context')},'ei34':{('a','b','context'),('b','c','context')}}
    mm=relations(m,rows,norm)|{'ra':lambda:'a','yn':lambda:'a','yo':lambda:'b','yp':lambda:'c'};check=lambda mm:run('ei35',['context'],mm,domain=domain)
    count=perturb(check,mm,rows,norm)
    assert not check(mm|{'yp':lambda:'b'});count+=1
    # A third selected trial also has to pass; an unselected one is irrelevant.
    selected=rows['zej']|{('c','b','context')}
    assert not check(mm|{'zej':lambda *xs:xs in selected});count+=1
    assert check(mm|{'zej':lambda *xs:xs in selected,'ei34':lambda *xs:xs in selected});count+=1
    assert not check(mm|{'zej':lambda *xs:xs in rows['zej']|{('c','a','context')},'ei34':lambda *xs:True});count+=1
    assert not run('ei35',['other'],mm,domain=domain);count+=1
    assert check(mm|{'sbc':forbidden,'sio':forbidden,'sls':forbidden,'sfm':forbidden});count+=1
    unknowns(check,mm,('tc','zb7','sle','zd4'))
    return dict(cases=count,both_axes_nonempty_and_every_selected_trial_required=True,additional_bad_trial_rejected=True,complete_scope_and_current_global_clock_conditions_required=True,native_quantifiers_checked_on_three_distinguishable_individuals=True)

@lru_cache(None)
def calculus_checks():
    cuts,m,coords,fn,norm=model();c=cuts.make;r=cuts.read;count=0
    # Native argument permutations feed both same-point regularity conditions.
    poly=FunctionValue((RS,)*4,RS,lambda x,y,z,t:c(2*r(x)+3*r(y)+5*r(z)+7*r(t)))
    expected=[]
    for axis in ('y','z'):
        values=[]
        for a,b,d,t in ((1,2,3,4),(2,-1,4,5)):
            x,y,z=(b,a,d) if axis=='y' else (d,b,a);values.append(Q(2*x+3*y+5*z+7*t))
        expected.append(tuple(values))
    rows={'slh':{(expected[0],Q(2),Q(7),Q(-3),Q(5),Q(4)),(expected[1],Q(-3),Q(2),Q(7),Q(5),Q(4))}}
    mm=relations(m,rows,norm);args=[poly,*map(c,map(Q,(7,2,-3,5,4)))];count+=perturb(lambda mm:run('slj',args,mm),mm,rows,norm)
    finger=norm((poly,))[0];point=(finger,*map(Q,(7,2,-3,5,2,7)))
    rows={'slg':{(finger,*map(Q,(7,2,-3,5,4,Q(1,2))))},'sjv':{point},'sjw':{point}};mm=relations(m,rows,norm)
    args=[poly,*map(c,map(Q,(7,2,-3,5,4,Q(1,2),2,7)))];count+=perturb(lambda mm:run('slh',args,mm,'instance'),mm,rows,norm)
    # For these explicitly quadratic fixtures central differences are exact
    # derivatives. This oracle is not a general real differentiation procedure.
    for by,bz,y,z in ((0,0,2,-3),(1,0,2,-3),(0,1,2,-3),(1,1,2,-3),(1,1,0,0)):
        qfn=FunctionValue((RS,)*4,RS,lambda x,y,z,t,by=by,bz=bz:c(r(x)**2+by*r(y)**2+bz*r(z)**2+2*r(t)**2))
        seen=[]
        def derivative(domain,f,p,value):
            seen.append((r(p),r(value)))
            return domain(p) and r(value)==(r(f(c(r(p)+1)))-r(f(c(r(p)-1))))/2
        args=[qfn,*map(c,map(Q,(7,y,z,5)))];actual=run('slk',args,m|{'sjs':derivative})
        assert actual==(by*y==0 and bz*z==0);assert seen==[(Q(y),Q(0)),(Q(z),Q(0))];count+=2
    return dict(cases=count,native_y_z_permutations_and_same_point_regularities_bound=True,zero_partial_is_not_local_constancy=True,both_same_tau_slices_and_zero_values_required=True,quadratic_derivative_oracle_is_not_general_calculus_proof=True)

@lru_cache(None)
def midpoint_checks():
    cuts,m,coords,fn,norm=model();c=cuts.make;r=cuts.read;count=0
    for axis in ('y','z'):
        for by,bz,curved in ((0,0,False),(1,0,False),(0,1,False),(0,0,True)):
            calls=[]
            def original(x,y,z,t):
                vals=tuple(map(r,(x,y,z,t)));calls.append(vals);a,b,d,tt=vals
                return c(2*(tt**2 if curved else tt)-3*a/8+by*b+bz*d)
            # Permutations themselves are tested natively in calculus_checks.
            f=FunctionValue((RS,)*4,RS,lambda a,b,d,t:original(b,a,d,t) if axis=='y' else original(d,b,a,t))
            args=[f,*map(c,map(Q,((2,7,-3,5,4,12) if axis=='y' else (-3,2,7,5,4,12))))]
            actual=run('slf',args,m);assert actual==(not curved and (by==0 if axis=='y' else bz==0));count+=1
            expected={(Q(7),Q(2),Q(-3),Q(5)),(Q(7),Q(14 if axis=='y' else 2),Q(-3 if axis=='y' else 9),Q(8)),(Q(7),Q(2),Q(-3),Q(11))}
            assert set(calls)==expected;count+=1
    return dict(cases=count,same_tau_three_arguments_and_equal_transverse_elapsed_times_checked=True,changed_y_or_z_and_nonlinear_time_not_silently_accepted=True)

@lru_cache(None)
def global_checks():
    cuts,m,coords,fn,norm=model();c=cuts.make;finger=norm((fn,))[0];count=0
    rows={'ei35':{('context',)},'sll':{(finger,Q(5),Q(4))}};mm=relations(m,rows,norm);count+=perturb(lambda mm:run('ei37',[],mm),mm,rows,norm)
    for truth in (False,True):assert run('ei36',[],m|{'ei35':lambda ctx,truth=truth:truth})==truth;count+=1
    for name,inner,extra in (('sll','slj',[c(Q(4))]),('slm','slk',[])):
        row=(finger,Q(7),Q(2),Q(-3),Q(5),*([Q(4)] if extra else []));rows={inner:{row}};mm=relations(m,rows,norm)
        args=[fn,c(Q(5)),*extra,*map(c,map(Q,(7,2,-3)))];count+=perturb(lambda mm:run(name,args,mm,'instance'),mm,rows,norm)
    rows={'slm':{(finger,Q(5))}};mm=relations(m,rows,norm);count+=perturb(lambda mm:run('slv',[],mm),mm,rows,norm)
    refusal={}
    for name,args in (('sll',[fn,c(Q(5)),c(Q(4))]),('slm',[fn,c(Q(5))]),('slh',[fn,*map(c,map(Q,(7,2,-3,5,4)))]),('slg',[fn,*map(c,map(Q,(7,2,-3,5,4,1)))])):
        try:run(name,args,m)
        except ValueError as e:assert 'Cannot finitely quantify' in str(e),str(e);refusal[name]=str(e)
        else:raise AssertionError('Real neighborhood or all-space scope sampled')
    return dict(cases=count,same_candidate_departure_time_and_transverse_root_in_premise=True,all_three_spatial_axes_and_both_partials_retained=True,real_quantification_refused=refusal)

@lru_cache(None)
def presentation_checks():
    count=0
    for name,rows in (
      ('ei4a',{'uh':{('notice','author','ei36','section','discourse')},'zei':{('notice','author','section','discourse')}}),
      ('ei4d',{'zc':{('consequence','author','ei37','slv','section','discourse')},'zep':{('consequence','author','earlier','section','discourse')}}),
      ('ei4c',{'eir3':{('notice','author','paper','ei4b','discourse')},'ue':{('previous','notice','discourse')}}),
      ('ei4f',{'eir3':{('consequence','author','paper','ei4e','discourse')},'ue':{('notice','consequence','discourse')}})):
        m={n:relation(rs) for n,rs in rows.items()};count+=perturb(lambda mm:run(name,[],mm),m,rows)
        assert run(name,[],m|{n:forbidden for n in ('ei35','ei36','ei37','slv','slm')});count+=1
    return dict(cases=count,attention_condition_analogy_and_two_partial_consequence_attributed=True,same_author_section_paper_and_source_order_preserved=True,quoted_claim_not_executed_as_proof=True)

@lru_cache(None)
def source_record():
    inv=json.loads(read(INVENTORY));math={m['id']:m for m in inv['math']};segments=[]
    hashes=('e42a253701532e6f8c87f38848b7f107fccbac56eeaebda094e79121df420f46','14cf34cc3a3e271592c19a2c088158fba3b6874f9aad6e6d157095504559d736','455386cb6d175dbebc5e9af9e0d92e0b89275302718e55827d95cee5a99ed3a2')
    readings={'M0106':'H（運動系のη方向の軸表記として読む）','M0107':'Z（運動系のζ方向）','M0108':'√(V²−v²)','M0109':'∂τ/∂y=0','M0110':'∂τ/∂z=0。'}
    flat=('H','Z','V2−v2','∂τ∂y=0','∂τ∂z=0.')
    for name,expected in zip(readings,flat):assert ''.join(ET.fromstring(math[name]['mathml']).itertext())==expected
    root=ET.fromstring(math['M0108']['mathml']);assert len(root.findall('.//{*}msqrt'))==1 and len(root.findall('.//{*}msup'))==2
    for i,u in enumerate(inv['units'][58:61]):
        assert u['id']==f'einstein-1905:u{59+i:04d}' and u['text_sha256']==hashes[i] and len(u['text'])==(225 if i==0 else 7)
        n=len(re.sub(r'\s|\[M\d+\]','',u['text']));assert n==(172 if i==0 else 0)
        segments.append(dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[0,len(u['text'])],text=u['text'],source_nonblank_characters=n,math=[dict(id=name,sha256=math[name]['sha256'],reading=readings[name]) for name in u['math_ids']]))
    prior='data/einstein-arbitrary-start-claim-source-reading-v1.json';validate_hashes(ROOT,json.loads(read(prior))['source_sha256'])
    paths={INVENTORY,DOC,prior,'artifacts/einstein-differential-step-v1/page-899.html','artifacts/einstein-differential-step-v1/page-899.jpg','artifacts/einstein-differential-step-v1/retrieval.json'}
    return dict(version='einstein-transverse-derivative-source-reading-v1',reviewer='assistant_visual_and_text_review',pages=['899'],segments=segments,observations=['原刊899頁のEine analoge Überlegungから二つの零偏微分までを前後とともに照合した。','固定抽出M0106はH。原刊の対応する字形を保存し、運動系のη方向の軸表記として明示的に読む。Zはζ方向であり、既出の平行関係を通じてy,zへ対応する。','√の範囲はV²−v²全体。Kでの光の全速さVと、運動する横軸に沿う成分速度を区別する。','stetsの全試行範囲、wenn man beachtetの注意条件、analoge Überlegungの先行論法への参照を保持する。','M0109/10は同じτのy,z偏微分が各々零。後続の線形性による具体的τ解はこの三単位に含めない。'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert new.document['statements'][:-2]==old.document['statements'] and len(new.document['statements'])==286
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations']
    assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    prior=json.loads(read(PRIOR));validate_hashes(ROOT,prior['source_sha256']);assert selection_binding(new,[282,283])==prior['selection']
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    load_annotations(ROOT,BASIS,ANNOTATIONS);assert json.loads(read(ANNOTATIONS))['entries']==json.loads(read('data/transverse-light-trial-identifiers-v1.json'))['entries']
    doc=parse(read(CORE));ds={d['name']:d for d in doc['declarations']};legacy={d['name']:d for d in parse(read(LEGACY))['declarations']}
    assert all(ds[n]==legacy[n] for n in ('skw','skx','sky','sle','skz','slf','slg','slh','sli','slj','slk','sll','slm','slv'))
    assert all(ds[n]['body']['force']=='assert' for n in ('ei4b','ei4e'))
    for style in ('compact','full'):
        body=format_graph(doc,style);assert parse(body)==parse(transcribe(body,alphabet='v2'))==doc
    assert json.loads(read(SOURCE))==source_record()
    return dict(new_definitions=len(MEANINGS),new_primitives=0,preserved_statements=INDEX,previous_whole_unit_judgment_preserved=True,existing_permutations_root_calculus_and_global_zero_claim_unchanged=True)

def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/SOURCE,json.dumps(source_record(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    results={n:f() for n,f in [('trial',trial_checks),('scope',scope_checks),('calculus',calculus_checks),('midpoint',midpoint_checks),('global',global_checks),('presentation',presentation_checks),('structure',structure_checks)]}
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(source_record()['source_sha256'])|{SOURCE,DOC,PRIOR,*DEPENDENCIES,LEGACY,'scripts/compose_transverse_derivative_claim.py','scripts/check_transverse_derivative_claim.py','tests/test_transverse_derivative_claim.py','scripts/check_coordinate_correspondence.py','scripts/check_moving_trip_geometry.py','scripts/check_material_relative_frame.py','scripts/check_clock_site_time.py','scripts/check_rod_methods.py','scripts/check_transverse_light_trial.py','scripts/check_light_time_expansion.py','scripts/check_translated_light_trial.py','scripts/compose_limits.py','scripts/compose_relativity_conjecture.py','scripts/compose_material_relative_frame.py','scripts/compose_two_postulates.py'}
    alignment=dict(segments=[dict(unit=s['unit'],unit_sha256=s['unit_sha256'],range=s['range'],source=s['text'],statements=[INDEX,INDEX+1] if i==0 else [INDEX+1],definitions=list(MEANINGS),status='explicit_interpretive_annotation') for i,s in enumerate(source_record()['segments'])])
    return dict(status='all_current_transverse_trials_and_zero_partial_conclusion_connected',document=FULL,**results,alignment=alignment,verified_full_units={'kant-1784':0,'einstein-1905':0},general_real_physical_derivation_proved=False,semantic_equivalence_automatically_proved=False,remaining=['u0059–u0061の全文通読判断登録','u0062以降と二作品全体の目標'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
