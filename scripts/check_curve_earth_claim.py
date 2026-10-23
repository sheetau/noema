"""Check the curve discourse and current-record Earth clock rate comparison."""
from copy import deepcopy
from functools import lru_cache
from fractions import Fraction as Q
from itertools import product
import json
from noema.grammar import parse,format_graph,number_word
from noema.extraction import extract_document
from noema.finite_semantics import FunctionValue,Content,evaluate_document
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.check_coordinate_correspondence import abstract
from scripts.check_moving_trip_geometry import NUM
from scripts.check_clock_site_time import relation,perturb,unknowns,forbidden
from scripts.check_clock_transfer_records import physical,phase_model
from scripts.check_curved_clock_records import norm_factory,relations,model as curve_model
from scripts.check_polygon_clock_claim import CONSTANTS as OLD_CONSTANTS,DOMAIN as OLD_DOMAIN,POINTS
from scripts.check_material_relative_frame import RS
from scripts.check_translated_light_trial import expose
from scripts.check_transverse_segment import refused
from scripts.compose_curve_earth_claim import ROOT,read,PARENT_BASIS,FULL,CORE,BASIS,ANNOTATIONS,INDICES,MEANINGS,PRIMITIVES,COMPARE,build

DOC='docs/curve-earth-claim-v1.md';SOURCE='data/einstein-curve-earth-claim-source-reading-v1.json'
INVENTORY='artifacts/written-units-v1/einstein-1905.json';PRIOR='data/einstein-polygon-clock-u0127-review-v1.json'
READING='data/einstein-curved-clock-records-source-reading-v1.json'
DEPENDENCIES=('reports/curved-clock-records-v1.json','reports/polygon-clock-claim-v1.json','reports/clock-transfer-records-v1.json')
CONSTANTS=OLD_CONSTANTS|{'zjd':'section','zje':'assumption','zjf':'curve','zjy':'earthclaim','zjr':'earth','zjs':'axis','zjt':'context','zjw':'scope','eisom':'elapsedname'}
DOMAIN=tuple(dict.fromkeys((*OLD_DOMAIN,*CONSTANTS.values())))
BOUNDS={'ejlz':{'se','ejj5','ejj6','ejkc'},'ejmc':{'syi','syj','syk','syl'},'ejmd':{'ejmc','ejlz'},'ejme':{'ejmd','ejmb'},'ejmf':{'ejme'},'ejmg':{'ejmf'},'ejmh':{'ejlq','ejlr','ejlu'}}

@lru_cache(None)
def core():return parse(read(CORE))

@lru_cache(None)
def fixture(name,mode='boundary'):
    doc=extract_document(core(),roots=[name],statement_indices=[]).document
    abstract(doc,NUM|{'sje','sjd','sky','zzbb','zzbd'}|BOUNDS.get(name,set()));doc=extract_document(doc,roots=[name],statement_indices=[]).document
    d=next(d for d in doc['declarations'] if d['name']==name)
    if mode=='instance':
        counts={'ejlz':1,'ejmb':2,'ejmf':8,'ejmh':len(COMPARE)}
        assert len(expose(d,{'forall','exists'},only_sort=None if name in ('ejmf','ejmh') else RS))==counts[name]
    slots=[]
    for i,p in enumerate(d['parameters']):
        n='jcec'+number_word(i);slots.append(n);doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']))
    expr=dict(kind='call',symbol=name,arguments=[dict(kind='call',symbol=n,arguments=[]) for n in slots])
    if d['result']=='content':
        doc['declarations'].append(dict(kind='primitive',name='jcecpoint',parameters=[],result='situation'));expr=dict(kind='evaluate',content=expr,situation=dict(kind='call',symbol='jcecpoint',arguments=[]))
    doc['statements']=[dict(kind='ask',body=expr)];return doc,slots

def run(name,args,m,mode='boundary',domain=DOMAIN):
    doc,slots=fixture(name,mode);assert len(args)==len(slots),(name,len(args),len(slots))
    mm={n:lambda x=x:x for n,x in CONSTANTS.items()}|{'jcecpoint':lambda:'discourse'}|m|{n:lambda x=x:x for n,x in zip(slots,args)}
    return evaluate_document(doc,individuals=domain,situations=POINTS,primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=700000,memoize_definitions=True,memoize_expressions=True)[0]['value']

@lru_cache(None)
def mechanism_checks():
    count=0;domain=('a','b')
    for oscillator,axis,spring in product(domain,repeat=3):
        rows={'ca':{('a',)},'zjg':{(oscillator,'a','context'),(spring,oscillator,'context')},'zjh':{(oscillator,axis,spring,'context')},'zji':{('a',oscillator,'context')}}
        mm={n:relation(rs) for n,rs in rows.items()};check=lambda mm:run('syi',['a','context'],mm,domain=domain)
        if oscillator!=spring:count+=perturb(check,mm,rows)
        else:assert not check(mm);count+=1
    # A selected condition may be false for both clocks; omitted conditions do not count.
    for complete,selected,first,second in product((False,True),repeat=4):
        mm={'zjl':relation({('b','context')} if complete else set()),'zjk':relation({('a','b','context')} if selected else set()),'zjj':relation(({('a','a','context')} if first else set())|({('a','b','context')} if second else set()))}
        assert run('syj',['a','b','b','context'],mm,domain=domain)==(complete and selected and first==second);count+=1
    rows={'zjl':{('b','context')},'zjk':{('a','b','context')},'zjj':{('a','a','context'),('a','b','context')}}
    mm={n:relation(rs) for n,rs in rows.items()}
    count+=perturb(lambda mm:run('syj',['a','b','b','context'],mm,domain=domain),mm,{'zjl':rows['zjl'],'zjj':rows['zjj']})
    assert not run('syj',['a','b','b','context'],mm|{'zjk':relation(rows['zjk']|{('b','b','context')}),'zjj':relation(rows['zjj']|{('b','a','context')})},domain=domain);count+=1
    cuts,m,_,_,_=physical();c=cuts.make;a=['A','earth','axis','length','context']
    for axial,radius,surface in product((-1,0,1),(-1,0,1),(False,True)):
        def coordinate(*xs,n=0):
            if list(xs)!=a:forbidden()
            return c(Q(n))
        mm=m|{'zjo':lambda *xs:coordinate(*xs,n=axial),'zjp':lambda *xs:coordinate(*xs,n=radius),'zjq':relation({('A','earth','context')} if surface else set())}
        for name,expected in (('syk',surface and axial==0 and radius>0),('syl',surface and axial!=0 and radius==0)):
            assert run(name,a,mm)==expected;count+=1
        unknowns(lambda mm:run('syk',a,mm),mm,('zjo','zjp','zjq'))
    return dict(cases=count,all_three_mechanical_witnesses_and_part_roles_checked=True,complete_nonempty_other_conditions_include_joint_falsehood=True,both_poles_and_surface_axis_coordinates_checked=True)

@lru_cache(None)
def profile_checks():
    cuts,m,coords,fs,_,domain,base=phase_model();c=cuts.make;r=cuts.read;norm=norm_factory(cuts,domain);count=0
    # Curved/nonuniform clock progress is allowed by the profile alone.
    for origin in (-7,11):
        f=FunctionValue((RS,),RS,lambda t:c(Q(origin)+r(t)*r(t)))
        for at in (Q(0),Q(1,2),Q(1)):
            local=('a','b','a','b','b','context');hist=['a','a','context','b','b',c(Q(0)),c(Q(1)),*([fs['x']]*3)]
            rows=base|{'se':{norm(hist)},'ejj5':{local},'ejj6':{norm([*local[:-1],f(c(Q(1))),local[-1]])},'ejkc':{norm(['a',c(at),f(c(at)),'context'])}}
            mm=relations(m,rows,norm);a=['a',f,'context',c(at)];check=lambda mm:run('ejlz',a,mm,'instance',domain)
            count+=perturb(check,mm,{n:rs for n,rs in rows.items() if n!='ejj5'},norm)
            extra=('a','a','b','a','a','context');assert not check(mm|{'ejj5':relation({local,extra})});count+=1
            refused(lambda:run('ejlz',a[:-1],mm,domain=domain))
    return dict(cases=count,current_all_candidates_and_all_real_times_connected=True,no_constant_rate_or_initial_sync_in_profile=True)

@lru_cache(None)
def rate_checks():
    cuts,m,_,_,_=physical();c=cuts.make;r=cuts.read;norm=norm_factory(cuts);count=0
    for origin,rate,lo,hi in product((-11,23),(Q(999,1000),Q(1)),(-3,5),(6,17)):
        f=FunctionValue((RS,),RS,lambda t:c(origin+rate*r(t)));a=[f,c(Q(lo)),c(Q(hi)),c(rate)]
        assert run('ejma',a,m);count+=1
        for wrong in (rate+1,Q(0),-rate):assert not run('ejma',a[:-1]+[c(wrong)],m);count+=1
        for end in (lo,lo-1):assert not run('ejma',[f,c(Q(lo)),c(Q(end)),c(rate)],m);count+=1
    for origin1,origin2,lo,hi in product((-20,100),(7,1000),(0,3),(5,10)):
        f=FunctionValue((RS,),RS,lambda t:c(origin1+Q(999,1000)*r(t)));g=FunctionValue((RS,),RS,lambda t:c(origin2+r(t)))
        a=[f,g,c(Q(lo)),c(Q(hi)),'scope','context',c(Q(999,1000)),c(Q(1))]
        rows={'zjv':{norm([c(Q(1,1000)),c(Q(1)),'scope','context'])}};mm=relations(m,rows,norm)
        count+=perturb(lambda mm:run('ejmb',a,mm,'instance'),mm,rows,norm)
        for slot in (6,7):
            bad=a[:];bad[slot]=c(r(bad[slot])+Q(1,100));assert not run('ejmb',bad,mm,'instance');count+=1
        assert not run('ejmb',[g,f,*a[2:6],a[7],a[6]],mm|{'zjv':lambda *xs:True},'instance');count+=1
        refused(lambda:run('ejmb',a[:-2],mm))
    # Constant or decreasing dials do not have positive running rates.
    for rate in (0,-1):
        f=FunctionValue((RS,),RS,lambda t:c(7+rate*r(t)));assert not run('ejma',[f,c(Q(0)),c(Q(1)),c(Q(rate))],m);count+=1
    unknowns(lambda mm:run('ejma',[g,c(Q(0)),c(Q(1)),c(Q(1))],mm),m,('bf','shv'))
    return dict(cases=count,mean_rates_from_actual_differences=True,independent_dial_origins_and_arbitrary_positive_windows=True,positive_rate_order_and_contextual_smallness_separate=True)

@lru_cache(None)
def binding_checks():
    cuts,m,_,_,_=physical();c=cuts.make;r=cuts.read;norm=norm_factory(cuts);count=0
    a=['clock','reference','A','B','context'];rows={'syi':{('clock','context'),('reference','context')},'cd':{('clock','reference')},'syj':{('clock','reference','scope','context')},'zjm':{('clock','A','earth','context'),('reference','B','earth','context')},'syk':{('A','earth','axis','length','context')},'syl':{('B','earth','axis','length','context')}}
    mm=relations(m,rows,norm);count+=perturb(lambda mm:run('ejmc',a,mm),mm,rows,norm)
    assert not run('ejmc',['clock','clock',*a[2:]],m|{n:lambda *xs:True for n in rows});count+=1
    f=FunctionValue((RS,),RS,lambda t:c(100+Q(999,1000)*r(t)));g=FunctionValue((RS,),RS,lambda t:c(-5+r(t)))
    observed=a[:-1]+[f,g,'context'];rows={'ejmc':{tuple(a)},'ejlz':{norm(['clock',f,'context']),norm(['reference',g,'context'])}}
    mm=relations(m,rows,norm);count+=perturb(lambda mm:run('ejmd',observed,mm),mm,rows,norm)
    window=observed[:-1]+[c(Q(3)),c(Q(7)),'context'];rows={'ejmd':{norm(observed)},'ejmb':{norm([f,g,c(Q(3)),c(Q(7)),'scope','context'])}}
    mm=relations(m,rows,norm);count+=perturb(lambda mm:run('ejme',window,mm),mm,{'ejmb':rows['ejmb']},norm)
    for setup,result in product((False,True),repeat=2):
        assert run('ejme',window,m|{'ejmd':lambda *xs:setup,'ejmb':lambda *xs:result})==(not setup or result);count+=1
    # Out-of-phase/nonpositive windows are excluded, not accidental Earth predictions.
    for lo,hi in ((-1,7),(3,21),(3,3),(7,3)):
        assert run('ejme',observed[:-1]+[c(Q(lo)),c(Q(hi)),'context'],m|{'ejmd':lambda *xs:True,'ejmb':lambda *xs:False});count+=1
    row=window[:-1]+['discourse'];rows={'ejme':{norm(row)}};mm=relations(m,rows,norm)
    count+=perturb(lambda mm:run('ejmf',window[:-1],mm,'instance'),mm,rows,norm)
    refused(lambda:run('ejmf',[],mm))
    unknowns(lambda mm:run('ejme',window,mm),relations(m,{'ejmd':{norm(observed)},'ejmb':{norm([f,g,*window[-3:-1],'scope','context'])}},norm),('eisls','eislt'))
    return dict(cases=count,mechanism_structure_conditions_places_and_current_profiles_bound=True,same_two_functions_window_scope_and_situation=True,unbounded_function_real_quantifiers_preserved=True)

@lru_cache(None)
def necessity_checks():
    count=0
    for baseline,extra,rotation,truth0,truth1 in product((False,True),repeat=5):
        subject=Content(POINTS,tuple(truth0 if p=='context' else truth1 if p=='other' else False for p in POINTS))
        candidates=({'context'} if baseline else set())|({'other'} if extra else set())
        def selected(s,reference,candidate):
            if candidate not in POINTS or reference not in POINTS or not isinstance(s,Content):forbidden()
            return s==subject and reference=='context' and candidate in candidates
        mm={'ejmf':lambda:subject,'eisol':selected,'zjn':relation({('earth','axis','K','context')}|({('earth','axis','K','other')} if rotation else set()))}
        assert run('ejmg',[],mm)==(baseline and truth0 and (not(extra and rotation) or truth1));count+=1
    subject=Content(POINTS,(True,)*len(POINTS));mm={'ejmf':lambda:subject,'eisol':lambda s,ref,at:s==subject and ref=='context' and at=='context','zjn':relation({('earth','axis','K','context')})}
    assert run('ejmg',[],mm);count+=1
    for ref in ('other','discourse'):
        assert not run('ejmg',[],mm|{'eisol':lambda s,r,at:s==subject and r==ref and at=='context'});count+=1
    assert not run('ejmg',[],mm|{'eisol':lambda s,r,at:s==Content(POINTS,(False,)*len(POINTS)) and r=='context'});count+=1
    rows={'zjn':{('earth','axis','K','context')}};count+=perturb(lambda mm:run('ejmg',[],mm),mm,rows)
    unknowns(lambda mm:run('ejmg',[],mm),mm,('eisol',))
    cuts,m,coords,a,compare,norm,t=curve_model()
    for setup,closed,law in product((False,True),repeat=3):
        assert run('ejmh',compare,m|{'ejlq':lambda *xs:setup,'ejlr':lambda *xs:closed,'ejlu':lambda *xs:law},'instance')==(not(setup and closed) or law);count+=1
    rows={'ejlq':{norm(compare)},'ejlr':{norm(a)},'ejlu':{norm(compare)}};mm=relations(m,rows,norm)
    count+=perturb(lambda mm:run('ejmh',compare,mm,'instance'),mm,{'ejlu':rows['ejlu']},norm)
    for key in ('ejlq','ejlr'):
        row=next(iter(rows[key]))
        for i in range(len(row)):
            bad=tuple('wrong' if i==j else x for j,x in enumerate(row));assert run('ejmh',compare,mm|{key:lambda *xs,bad=bad:norm(xs)==bad,'ejlu':lambda *xs:False},'instance');count+=1
    refused(lambda:run('ejmh',[],mm))
    return dict(cases=count,native_nonempty_necessity_includes_reference=True,all_selected_candidates_and_rotation_restriction_checked=True,additional_curve_law_scope_separate=True)

@lru_cache(None)
def presentation_checks():
    count=0
    table=(('ejmi',{'ui':{('author','polygon','discourse')},'ug':{('assumption','author','ejlx','section','discourse')}}),('ejmj',{'uh':{('curve','author','ejlw','section','discourse')},'zc':{('curve','author','ejly','ejlw','section','discourse')},'ue':{('assumption','curve','discourse')},'eison':{('elapsedname','ejlt','paper','discourse')}}),('ejmk',{'zc':{('earthclaim','author','ejlw','ejmg','section','discourse')},'uh':{('earthclaim','author','ejmg','section','discourse')}}),('ejml',{'zfl':{('curve','author','ejmh','ejlw','section','discourse')}}),('ejmn',{'eir3':{('assumption','author','paper','ejmm','discourse')},'ue':{('return','assumption','discourse')}}),('ejmp',{'zfl':{('curve','author','ejmh','ejlw','section','discourse')},'eir3':{('curve','author','paper','ejmo','discourse')},'ue':{('assumption','curve','discourse')}}),('ejmr',{'eir3':{('earthclaim','author','paper','ejmq','discourse')},'ue':{('curve','earthclaim','discourse')}}))
    for name,rows in table:
        mm={n:relation(rs) for n,rs in rows.items()};count+=perturb(lambda mm:run(name,[],mm),mm,rows)
        assert run(name,[],mm|{n:forbidden for n in ('ejlx','ejlw','ejly','ejlt','ejmh','ejmg')});count+=1
    return dict(cases=count,assumption_proved_status_inference_order_and_typed_elapsed_time_bound=True,earth_must_claim_uses_same_curve_conclusion=True,quoted_physical_claims_not_executed=True)

@lru_cache(None)
def source_record():
    old=json.loads(read(READING));validate_hashes(ROOT,old['source_sha256']);rec=deepcopy(old)
    retrieval='artifacts/einstein-curve-earth-claim-v1/retrieval.json';rr=json.loads(read(retrieval));validate_hashes(ROOT,{x['path']:x['sha256'] for x in rr['sources']})
    paths={READING,DOC,retrieval,*(x['path'] for x in rr['sources'])}
    rec.update(version='einstein-curve-earth-claim-source-reading-v1',observations=old['observations'][:2]+['後半のUnruhuhrの機構、同構造とその他同条件、赤道と両極、非常に小さい歩度差、darausとmußを同じ著者の推論として保持する。Patek Philippeの用語集のBalance and spring assemblyとBalance-springを参照し、回転振動体・復元ばね・調速機能という機構上の読みを照合した。','仮定採用・証明済みという位置付け・帰結・所要時間t・地球比較を三つの順序付きメッセージへ接続した。新しい局所検査と、二文全体の意味判断は別記録にする。'],source_sha256=old['source_sha256']|{p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
    return rec

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert new.document['statements'][:-3]==old.document['statements'] and len(new.document['statements'])==350
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations'];assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    prior=json.loads(read(PRIOR));validate_hashes(ROOT,prior['source_sha256']);assert selection_binding(new,[345,346])==prior['selection']
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    load_annotations(ROOT,BASIS,ANNOTATIONS);doc=core();names=lambda root:{d['name'] for d in extract_document(doc,roots=[root],statement_indices=[]).document['declarations']}
    assert {'sxv','ejj5','ejj6','ejlo','ejk2','ejla','swy'}<=names('ejlw')
    assert not {'ejlu','ejmh'}&names('ejlw') and 'ejml' not in names('ejmo') and 'ejmh' in names('ejmp')
    assert {'ejj5','ejj6','ejlz','ejma','ejmb','syi','syj','syk','syl','s5k','eisol','zjn'}<=names('ejmg')
    assert not {'zju','syn','syo','sym','ejkb','ejke'}&names('ejmg')
    assert len([d for d in new.document['declarations'][len(old.document['declarations']):] if d['kind']=='primitive'])==3
    for style in ('compact','full'):
        body=format_graph(doc,style);assert parse(body)==parse(transcribe(body,alphabet='v2'))==doc
    assert source_record()==json.loads(read(SOURCE))
    return dict(new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),preserved_statements=347,prior_judgments_preserved=True,additional_interval_laws_outside_author_message=True,earth_rates_use_current_displays_not_old_rate_oracle=True)

def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/SOURCE,json.dumps(source_record(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    results={n:f() for n,f in [('mechanism',mechanism_checks),('profile',profile_checks),('rate',rate_checks),('binding',binding_checks),('necessity',necessity_checks),('presentation',presentation_checks),('structure',structure_checks)]}
    helpers=('compose_curved_clock_records','compose_clock_transfer_records','compose_rod_methods','compose_solid_sphere_geometry','compose_material_relative_frame','compose_relativity_conjecture','compose_two_postulates','compose_limits','check_curved_clock_records','check_polygon_clock_claim','check_clock_transfer_records','check_clock_site_time','check_coordinate_correspondence','check_moving_trip_geometry','check_material_relative_frame','check_translated_light_trial','check_transverse_segment','check_rod_methods','audit_opening_scope')
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(source_record()['source_sha256'])|{SOURCE,DOC,PRIOR,*DEPENDENCIES,'scripts/compose_curve_earth_claim.py','scripts/check_curve_earth_claim.py','tests/test_curve_earth_claim.py',*(f'scripts/{n}.py' for n in helpers)}
    alignment=dict(segments=[dict(unit=s['unit'],unit_sha256=s['unit_sha256'],range=s['range'],source=s['text'],statements=list(INDICES),definitions=list(MEANINGS),status='explicit_interpretive_annotation') for s in source_record()['segments']])
    return dict(status='assumed_curve_extension_and_current_earth_rate_claim_connected',document=FULL,**results,alignment=alignment,verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,remaining=['u0128二文全体の意味判断'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
