"""Check current coefficient identity, native formula and quoted source roles."""
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
from scripts.check_moving_trip_geometry import NUM
from scripts.check_clock_site_time import relation,perturb,unknowns,forbidden
from scripts.check_translated_light_trial import expose
from scripts.check_time_origin_affinity import affine_model,RS
from scripts.compose_affine_time_claim import ROOT,read,PARENT_BASIS,FULL,CORE,BASIS,ANNOTATIONS,INDEX,MEANINGS,build

DOC='docs/affine-time-claim-v1.md';SOURCE='data/einstein-affine-time-source-reading-v1.json'
INVENTORY='artifacts/written-units-v1/einstein-1905.json';PRIOR='data/einstein-transverse-derivative-u0059-review-v1.json'
DEPENDENCIES=('reports/time-origin-affinity-v1.json','reports/affine-time-form-v1.json','reports/transverse-derivative-claim-v1.json')
CONSTANTS={'rd':'author','eirf':'paper','eisms':'section','ri':'discourse','zb6':'context','zeu':'inference','zev':'origin','zew':'unknown','zeo':'previous','zee':'agent','zes':'context','zdq':'trial','ra':'frame','zc7':'time'}
DOMAIN=('author','paper','section','inference','origin','unknown','previous','agent','trial','event','other','x','y','z','time','frame','tuple')

@lru_cache(None)
def fixture(name,mode='boundary'):
    doc=extract_document(parse(read(CORE)),roots=[name],statement_indices=[]).document;boundaries=NUM|{'sje'}
    if name=='ei4o':boundaries|={'ei4n','smr'}
    if name=='ei4p':boundaries|={'skn','slm','ei4o','ei4l'}
    if name=='ei4q':boundaries.add('ei4l')
    if name=='smr':boundaries|={'smd','sjw','sjs'}
    if name=='smp':boundaries|={'smq','smb'}
    abstract(doc,boundaries);doc=extract_document(doc,roots=[name],statement_indices=[]).document
    d=next(d for d in doc['declarations'] if d['name']==name)
    if mode=='instance':assert len(expose(d,{'forall','exists'}))=={'ei4p':7,'smi':4,'smq':1,'smb':3,'smp':2}[name]
    slots=[];args=[]
    for i,p in enumerate(d['parameters']):
        n='jatc'+number_word(i);slots.append(n);doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']));args.append(dict(kind='call',symbol=n,arguments=[]))
    expr=dict(kind='call',symbol=name,arguments=args)
    if d['result']=='content':
        doc['declarations'].append(dict(kind='primitive',name='jatcpoint',parameters=[],result='situation'));expr=dict(kind='evaluate',content=expr,situation=dict(kind='call',symbol='jatcpoint',arguments=[]))
    doc['statements']=[dict(kind='ask',body=expr)];return doc,slots

def run(name,args,m,mode='boundary'):
    doc,slots=fixture(name,mode);assert len(args)==len(slots),(name,len(args),len(slots))
    mm={n:lambda x=x:x for n,x in CONSTANTS.items()}|m|{n:lambda x=x:x for n,x in zip(slots,args)};mm.setdefault('jatcpoint',lambda:'discourse')
    return evaluate_document(doc,individuals=DOMAIN,situations=('context','other','discourse'),primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=400000,memoize_definitions=True,memoize_expressions=True)[0]['value']

def model(offset=0):
    cuts,m,mat,off,matrix,vec,coeff,fn,oldnorm=affine_model(offset);c=cuts.make;r=cuts.read
    coeff[1]=coeff[2]=Q(0);mat['time','y']=mat['time','z']=Q(0)
    phi=FunctionValue((RS,),RS,lambda speed:c(Q(2)))
    def norm(xs):
        return tuple(tuple(r(x(c(Q(a)))) for a in (0,2,3,4)) if isinstance(x,FunctionValue) and x.parameters==(RS,) else oldnorm((x,))[0] for x in xs)
    m|={'sje':lambda a,b:c(r(a)/r(b)) if r(b)!=0 else forbidden(),'tc':lambda:c(Q(5)),'zeq':lambda:phi,'qe':lambda tr:'event' if tr=='trial' else forbidden(),'zdz':lambda e,f,ctx:'tuple' if (e,f,ctx)==('event','frame','context') else forbidden(),'zc6':lambda t,a:c(Q(5)) if (t,a)==('tuple','time') else forbidden()}
    return cuts,m,matrix,vec,coeff,fn,phi,norm

def relations(m,rows,norm):return m|{n:lambda *xs,rs=rs:norm(xs) in rs for n,rs in rows.items()}

@lru_cache(None)
def coefficient_join_checks():
    cuts,m,matrix,vec,coeff,fn,phi,norm=model();c=cuts.make;args=[matrix,vec,*map(c,coeff)]
    rows={'ei4n':{norm((fn,*args))},'smr':{norm((fn,c(Q(5)),c(Q(3)),c(Q(5)),phi,*map(c,coeff)))}}
    mm=relations(m,rows,norm);count=perturb(lambda mm:run('ei4o',args,mm),mm,rows,norm)
    rows={'skn':{norm((fn,c(Q(5)),c(Q(3)),c(Q(5))))},'slm':{norm((fn,c(Q(5))))},'ei4o':{norm(args)},'ei4l':{('context',)}}
    mm=relations(m,rows,norm);count+=perturb(lambda mm:run('ei4p',args,mm,'instance'),mm,rows,norm)
    for n in ('zd4','tc','zb7','zeq','qe','zdz','zc6'):
        unknowns(lambda mm:run('ei4o',args,mm),relations(m,{'ei4n':{norm((fn,*args))},'smr':{norm((fn,c(Q(5)),c(Q(3)),c(Q(5)),phi,*map(c,coeff)))}},norm),(n,))
    for truth in (False,True):assert run('ei4q',[],m|{'ei4l':lambda ctx,truth=truth:ctx=='context' and truth})==truth;count+=1
    try:run('ei4p',[],mm)
    except ValueError as e:assert 'Cannot finitely quantify' in str(e)
    else:raise AssertionError('Real coefficient existence sampled')
    return dict(cases=count,same_tau_matrix_seven_witnesses_speed_time_and_phi_bound=True,origin_separate_from_derivative_premises=True,real_coefficient_existence_refused=True)

@lru_cache(None)
def native_coefficient_checks():
    count=0
    for offset in (0,7):
        cuts,m,matrix,vec,coeff,fn,phi,norm=model(offset);c=cuts.make;r=cuts.read;finger=norm((fn,))[0]
        rows={'smd':{norm((fn,*map(c,coeff)))},'sjw':{(finger,*map(Q,(0,0,0,5,Q(-3,8),2)))}}
        mm=relations(m,rows,norm)
        # Exact derivative oracle only for the supplied affine functions.
        mm['sjs']=lambda domain,f,p,d:domain(p) and r(f(c(r(p)+1)))-r(f(p))==r(d)
        args=[fn,c(Q(5)),c(Q(3)),c(Q(5)),phi,*map(c,coeff)]
        count+=perturb(lambda mm:run('smr',args,mm),mm,rows,norm)
        wrong=FunctionValue((RS,),RS,lambda speed:c(Q(3)));bad=args.copy();bad[4]=wrong;assert not run('smr',bad,mm);count+=1
        for i in range(5):
            bad=args.copy();bad[5+i]=c(coeff[i]+1);assert not run('smr',bad,mm);count+=1
        seen=[]
        def selected(speed):seen.append(r(speed));return c(Q(2))
        args[4]=FunctionValue((RS,),RS,selected);assert run('smr',args,mm) and set(seen)=={Q(3)};count+=1
    return dict(cases=count,native_smr_smf_sme_join_and_same_speed_phi_checked=True,nonzero_offset_still_allowed_before_origin_condition=True,affine_derivatives_are_explicit_fixture_oracles=True)

@lru_cache(None)
def formula_checks():
    count=0
    for speed,scale in ((3,2),(3,3),(0,2),(3,-2),(3,0)):
        cuts,m,matrix,vec,coeff,fn,phi,norm=model();c=cuts.make;r=cuts.read;coeff[:]=[Q(-scale*speed,25-speed*speed),Q(0),Q(0),Q(scale),Q(0)]
        for x,y,z,t in ((8,3,4,5),(-8,-4,9,5),(0,0,0,0),(Q(1,2),2,-3,Q(5,6))):
            args=[fn,c(Q(5)),c(Q(speed)),c(Q(scale)),*map(c,map(Q,(x,y,z,t)))]
            assert run('smi',args,m,'instance');count+=1
            coeff[4]=Q(7);assert not run('smi',args,m,'instance');coeff[4]=Q(0);count+=1
        for axis in (1,2):
            coeff[axis]=Q(1);args=[fn,c(Q(5)),c(Q(speed)),c(Q(scale)),*map(c,map(Q,(8,3,4,5)))];assert not run('smi',args,m,'instance');coeff[axis]=Q(0);count+=1
    cuts,m,matrix,vec,coeff,fn,phi,norm=model();c=cuts.make
    try:run('smn',[],m)
    except ValueError as e:assert 'Cannot finitely quantify' in str(e)
    else:raise AssertionError('Full formula reduced to sample points')
    return dict(cases=count,native_formula_all_four_inputs_and_offset_distinguished=True,zero_stationary_negative_and_nonunit_scale_not_arbitrarily_excluded=True,full_formula_real_domain_refused=True)

@lru_cache(None)
def uncertainty_checks():
    cuts,m,matrix,vec,coeff,fn,phi,norm=model();c=cuts.make;r=cuts.read;count=0
    def family(stage):
        if stage not in ('context','other','discourse'):forbidden()
        return FunctionValue((RS,),RS,lambda speed:c(Q(2)+(r(speed)-3)**2 if stage=='other' else Q(2)))
    fam=FunctionValue(('situation',),dict(kind='function',parameters=[RS],result=RS),family)
    alternatives=lambda agent,stage,alt:agent=='agent' and stage=='context' and alt in ('context','other')
    domain=FunctionValue((RS,),'truth',lambda speed:0<=r(speed)<5)
    same=FunctionValue((RS,RS),'truth',lambda a,b:r(a)==r(b))
    alt=FunctionValue(('individual','situation','situation'),'truth',alternatives)
    mm=m|{'zer':lambda:fam,'zet':alternatives}
    for speed,expected in ((3,False),(2,True),(5,False),(-1,False)):
        args=['agent','context',domain,alt,fam,same,'context','other',c(Q(speed))]
        assert run('smb',args,mm,'instance')==expected;count+=1
        for slot,value in ((0,'other'),(1,'other'),(7,'context')):
            bad=args.copy();bad[slot]=value;assert not run('smb',bad,mm,'instance');count+=1
    for speed in (0,2,3,4):
        args=[phi,fam,'context',domain,c(Q(speed))];assert run('smq',args,mm,'instance');count+=1
        bad=args.copy();bad[2]='other';assert run('smq',bad,mm,'instance')==(speed==3);count+=1
    # Native smp maintains current-candidate membership and validity of each
    # selected alternative at each allowed speed. smq/smb boundaries are tested above.
    mm|={'smq':lambda *xs:True,'smb':lambda *xs:True}
    for stage in ('context','other','discourse'):
        assert run('smp',[stage,c(Q(2))],mm,'instance');count+=1
    assert not run('smp',['other',c(Q(2))],mm|{'zet':lambda a,s,t:t=='other'},'instance');count+=1
    for n in ('smq','smb'):
        assert not run('smp',['other',c(Q(2))],mm|{n:lambda *xs:False},'instance');count+=1
    try:run('smp',[],mm)
    except ValueError as e:assert 'Cannot finitely quantify' in str(e)
    else:raise AssertionError('Candidate validity on all speeds sampled')
    return dict(cases=count,current_function_same_stage_same_speed_domain_preserved=True,equal_at_one_speed_does_not_identify_functions=True,native_candidate_membership_and_real_scope_retained=True,knowledge_in_general_not_claimed=True)

@lru_cache(None)
def presentation_checks():
    count=0
    for name,rows in (
      ('ei4r',{'zc':{('inference','author','ei4p','smn','section','discourse')}}),
      ('ei4u',{'uh':{('unknown','author','smp','section','discourse')}}),
      ('ei4x',{'ug':{('origin','author','ei4q','section','discourse')},'zex':{('origin','author','section','discourse')}}),
      ('ei4t',{'eir3':{('inference','author','paper','ei4s','discourse')},'ue':{('previous','inference','discourse')}}),
      ('ei4w',{'eir3':{('unknown','author','paper','ei4v','discourse')},'ue':{('inference','unknown','discourse')}}),
      ('ei4z',{'eir3':{('origin','author','paper','ei4y','discourse')},'ue':{('unknown','origin','discourse')}})):
        m={n:relation(rs) for n,rs in rows.items()};count+=perturb(lambda mm:run(name,[],mm),m,rows)
        assert run(name,[],m|{n:forbidden for n in ('ei4p','ei4q','smn','smp','zd4')});count+=1
    return dict(cases=count,consequence_unknown_and_assumption_with_brevity_are_distinct=True,same_author_section_paper_and_source_order_preserved=True,quoted_contents_not_executed=True)

@lru_cache(None)
def source_record():
    inv=json.loads(read(INVENTORY));math={m['id']:m for m in inv['math']};segments=[]
    hashes=('c2c9f28feab40584b4e0bb6f5d3048d629228c9f68eb4d01748abb20d0a28a7d','9fb3b0a74ad53e1ea92bcacbffca829131c7d546a13170fae1b910193dc73dba','7fa94b491da65dd0b7546e50842ecfd4c684a4e2162104cfcfeb7b1cbdb9de4e')
    readings=dict(zip((f'M{n:04d}' for n in range(111,118)),('τ','τ=a(t−v*x′/(V²−v²))','a','φ(v)','k','τ=0','t=0')))
    for n,flat in zip(readings,('τ','τ=a(t−vV2−v2x′)','a','φ(v)','k','τ=0','t=0')):assert ''.join(ET.fromstring(math[n]['mathml']).itertext())==flat
    root=ET.fromstring(math['M0112']['mathml']);assert len(root.findall('.//{*}mfrac'))==1
    assert [''.join(e.itertext()) for e in root.findall('.//{*}msup')]==['V2','v2','x′']
    for i,u in enumerate(inv['units'][61:64]):
        assert u['id']==f'einstein-1905:u{62+i:04d}' and u['text_sha256']==hashes[i]
        segments.append(dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[0,len(u['text'])],text=u['text'],source_nonblank_characters=len(re.sub(r'\s|\[M\d+\]','',u['text'])),math=[dict(id=n,sha256=math[n]['sha256'],reading=readings[n],mathml_flat=''.join(ET.fromstring(math[n]['mathml']).itertext())) for n in u['math_ids']]))
    prior='data/einstein-transverse-derivative-source-reading-v1.json';validate_hashes(ROOT,json.loads(read(prior))['source_sha256'])
    paths={INVENTORY,DOC,prior,'artifacts/einstein-differential-step-v1/page-899.html','artifacts/einstein-differential-step-v1/page-899.jpg','artifacts/einstein-differential-step-v1/retrieval.json'}
    return dict(version='einstein-affine-time-source-reading-v1',reviewer='assistant_visual_and_text_review',pages=['899'],segments=segments,observations=['原刊899頁のAus diesen Gleichungenからt=0 seiまでを前後とともに視認した。','式はτ=a(t−v*x′/(V²−v²))。aは括弧全体へ掛かり、分母はV²−v²、xはダッシュ付きである。','daはτの線形性を理由に加え、diesen Gleichungenは先行する縦横偏微分条件を参照する。','aは暫定的に未知のφ(v)。現在段階の未決定性として読み、a=1や後続の確定係数を加えない。','der Kürze halberは原点仮定の理由。k原点でτ=0のときt=0であり、全時刻での一致とはしない。','本文順序は帰結・式、未知係数、原点仮定。次の空間座標の導出を混ぜない。'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert new.document['statements'][:-3]==old.document['statements'] and len(new.document['statements'])==289
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations']
    assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    prior=json.loads(read(PRIOR));validate_hashes(ROOT,prior['source_sha256']);assert selection_binding(new,[284,285])==prior['selection']
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    load_annotations(ROOT,BASIS,ANNOTATIONS)
    doc=parse(read(CORE));ds={d['name']:d for d in doc['declarations']};legacy={d['name']:d for d in parse(read('examples/v014/einstein-affine-time-form.noema'))['declarations']}
    assert all(ds[n]==legacy[n] for n in ('smc','smd','sme','smf','smg','smh','smi','smj','smn','sma','smb','smq','smr','sms','smp'))
    assert all(ds[n]['body']['force']=='assert' for n in ('ei4s','ei4v','ei4y'))
    for style in ('compact','full'):
        body=format_graph(doc,style);assert parse(body)==parse(transcribe(body,alphabet='v2'))==doc
    assert json.loads(read(SOURCE))==source_record()
    return dict(new_definitions=len(MEANINGS),new_primitives=0,preserved_statements=INDEX,prior_whole_unit_judgment_preserved=True,old_affine_formula_and_uncertainty_definitions_unchanged=True)

def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/SOURCE,json.dumps(source_record(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    results={n:f() for n,f in [('join',coefficient_join_checks),('coefficients',native_coefficient_checks),('formula',formula_checks),('uncertainty',uncertainty_checks),('presentation',presentation_checks),('structure',structure_checks)]}
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(source_record()['source_sha256'])|{SOURCE,DOC,PRIOR,*DEPENDENCIES,'examples/v014/einstein-affine-time-form.noema','scripts/compose_affine_time_claim.py','scripts/check_affine_time_claim.py','tests/test_affine_time_claim.py','scripts/check_time_origin_affinity.py','scripts/check_coordinate_correspondence.py','scripts/check_moving_trip_geometry.py','scripts/check_clock_site_time.py','scripts/check_rod_methods.py','scripts/check_translated_light_trial.py','scripts/compose_time_origin_affinity.py','scripts/compose_limits.py','scripts/compose_relativity_conjecture.py','scripts/compose_material_relative_frame.py','scripts/compose_two_postulates.py'}
    alignment=dict(segments=[dict(unit=s['unit'],unit_sha256=s['unit_sha256'],range=s['range'],source=s['text'],statements=[INDEX] if i<2 else [INDEX,INDEX+1,INDEX+2],definitions=list(MEANINGS),status='explicit_interpretive_annotation') for i,s in enumerate(source_record()['segments'])])
    return dict(status='current_affine_tau_formula_unfixed_scale_and_origin_connected',document=FULL,**results,alignment=alignment,verified_full_units={'kant-1784':0,'einstein-1905':0},general_real_physical_derivation_proved=False,semantic_equivalence_automatically_proved=False,remaining=['u0062–u0064の全文通読判断登録','u0065以降と二作品全体の目標'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
