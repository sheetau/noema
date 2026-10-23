"""Check local time bindings, universal comparison and interpretive norms."""
from functools import lru_cache
from fractions import Fraction as Q
from itertools import product
import json
from noema.grammar import parse,format_graph,number_word
from noema.extraction import extract_document
from noema.finite_semantics import Content,evaluate_document
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.check_coordinate_correspondence import abstract
from scripts.check_moving_trip_geometry import NUM,numbers,norm_factory
from scripts.check_rod_methods import value,relation
from scripts.check_rod_length_claims import replace_real_sort
from scripts.compose_simultaneity_conclusion import ROOT,read,PARENT_BASIS,FULL,CORE,BASIS,ANNOTATIONS,INDEX,MEANINGS,PRIMITIVES,build
from scripts.review_simultaneity_conclusion import DOC,SOURCE,INVENTORY,PRIORS,DEPENDENCIES,source_record

DOMAIN=('event','display','clock','reference','place','frame','otherframe','unit','lengthunit','x','y','z','author','paper','previous','conclusion','other')
POINTS=('comparison','discourse','other')
SMALL=('zero','one')

def forbidden(*xs):raise ValueError('Unknown simultaneity-conclusion input')
def constants():return {n:lambda x=x:x for n,x in {'rb':'unit','rd':'author','eirf':'paper','ri':'discourse','zbj':'comparison','zbb':'previous','zbk':'conclusion','yn':'x','yo':'y','yp':'z'}.items()}

@lru_cache(None)
def fixture(name,mode='boundary'):
    doc=extract_document(parse(read(CORE)),roots=[name],statement_indices=[]).document
    boundaries=NUM|{'qo','eiok'}
    if mode in ('projection','native_uniqueness'):boundaries|={'seg','eiuj'}
    elif name in ('eium','eiun'):boundaries|={'eiuk','eiul'}
    elif name=='eiuj':boundaries.add('eiui')
    elif name=='eiul':boundaries|={'seh','eiuj'}
    elif name in ('eiuq','eiur','eiut'):boundaries|={'eium','eiun','eiuo'}
    elif name=='eiuw':boundaries|={'eiur','eiut'}
    abstract(doc,boundaries);doc=extract_document(doc,roots=[name],statement_indices=[]).document
    if mode=='projection':doc=replace_real_sort(doc)
    d=next(d for d in doc['declarations'] if d['name']==name);slots=[];args=[]
    for i,p in enumerate(d['parameters']):
        n='jsc'+number_word(i);slots.append(n);doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']));args.append(dict(kind='call',symbol=n,arguments=[]))
    expr=dict(kind='call',symbol=name,arguments=args)
    if d['result']=='content':
        doc['declarations'].append(dict(kind='primitive',name='jsccontext',parameters=[],result='situation'));expr=dict(kind='evaluate',content=expr,situation=dict(kind='call',symbol='jsccontext',arguments=[]))
    doc['statements']=[dict(kind='ask',body=expr)];return doc,slots

def run(name,args,m,mode='boundary',domain=DOMAIN):
    doc,slots=fixture(name,mode);assert len(args)==len(slots)
    mm=constants()|m|{n:lambda x=x:x for n,x in zip(slots,args)};mm.setdefault('jsccontext',lambda:'discourse')
    return evaluate_document(doc,individuals=domain,situations=POINTS,primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=300000,memoize_definitions=True,memoize_expressions=True)[0]['value']

def unknowns(check,m,names):
    for n in names:
        try:check(m|{n:forbidden})
        except ValueError as e:assert 'Unknown simultaneity-conclusion' in str(e),str(e)
        else:raise AssertionError(('Unknown input accepted',n))

def perturb(check,m,rows,norm=lambda xs:tuple(value(x) for x in xs)):
    count=1;assert check(m)
    for n,rs in rows.items():
        for row in rs:
            assert not check(m|{n:lambda *xs,rs=rs-{row}:norm(xs) in rs}),(n,row);count+=1
            for i in range(len(row)):
                changed=tuple('other' if j==i else x for j,x in enumerate(row))
                assert not check(m|{n:lambda *xs,rs=(rs-{row})|{changed}:norm(xs) in rs}),(n,i);count+=1
    unknowns(check,m,rows);return count

@lru_cache(None)
def local_checks():
    cuts,m=numbers();c=cuts.make;norm=norm_factory(cuts,());count=0
    rows={'zbd':{('event',),('display',)},'va':{('frame',)},'eisb7':{('frame','reference','unit','comparison')},'ca':{('clock',),('reference',)},'cc':{('clock','frame'),('reference','frame')},'ci':{('unit',)},'cb':{('clock','place','frame'),('event','place','frame'),('display','place','frame')},'ce':{('clock',e,'frame','unit',Q(7)) for e in ('event','display')},'qo':{('clock','reference','frame','unit','comparison')},'eisgm':{('event','display','clock','frame','comparison')}}
    m|={n:lambda *xs,rs=rs:norm(xs) in rs for n,rs in rows.items()}
    m['zbh']=lambda f,ctx:'reference' if (f,ctx)==('frame','comparison') else 'other'
    args=['event','clock','place','frame','unit',c(Q(7)),'comparison']
    count+=perturb(lambda mm:run('eiui',args,mm),m,rows,norm)
    for i in range(len(args)):
        bad=list(args);bad[i]=c(Q(9)) if i==5 else 'other'
        assert not run('eiui',bad,m),(i,bad);count+=1
    assert not run('eiui',args,m|{'ba':lambda x:False});count+=1
    unknowns(lambda mm:run('eiui',args,mm),m,('zbh','ba'))
    # Test existential bindings on two values; native local-body evidence is above.
    for clock,place in product(SALL:=SMALL,repeat=2):
        args=['zero','one','zero',c(Q(7)),'comparison'];row=('zero',clock,place,'one','zero',Q(7),'comparison')
        mm={'eiui':lambda *xs,row=row:norm(xs)==row}
        assert run('eiuj',args,mm,domain=SMALL);count+=1
        assert not run('eiuj',args,{'eiui':lambda *xs:False},domain=SMALL);count+=1
        for i in (0,3,4,5,6):
            bad=list(row);bad[i]=Q(9) if i==5 else 'other' if i==6 else ('one' if row[i]=='zero' else 'zero')
            assert not run('eiuj',args,{'eiui':lambda *xs,bad=tuple(bad):norm(xs)==bad},domain=SMALL);count+=1
    unknowns(lambda mm:run('eiuj',['zero','one','zero',c(Q(7)),'comparison'],mm,domain=SMALL),{'eiui':lambda *xs:True},('eiui',))
    return dict(cases=count,native_saf_common_reference_and_same_local_display=True,two_value_existential_binding_all_slots=True,unknown_values_rejected=True)

@lru_cache(None)
def time_checks():
    count=0
    # Keep seh's quantification; project only the real carrier to two values.
    for available,candidate,display,equal in product((False,True),repeat=4):
        rows={'zero'} if available else set()
        if equal:rows.add('one')
        stamp='zero' if candidate else 'one'
        model={'zbe':lambda *xs,s=stamp:s,'seg':lambda e,f,u,t,c,sync,valid,rows=rows:t in rows and (e,f,u,c)==('zero','one','zero','comparison'),'eiuj':lambda e,f,u,t,c:display and (e,f,u,t,c)==('zero','one','zero',stamp,'comparison'),'sca':lambda a,b:a==b}
        expected=stamp in rows and len(rows)==1 and display
        assert run('eiuk',['zero','one','zero','comparison'],model,'projection',SMALL)==expected;count+=1
    # Distinct representations may denote the same time; numeric equality is used.
    model={'zbe':lambda *xs:'zero','seg':lambda *xs:True,'eiuj':lambda *xs:True,'sca':lambda a,b:True}
    assert run('eiuk',['zero','one','zero','comparison'],model,'projection',SMALL);count+=1
    unknowns(lambda mm:run('eiuk',['zero','one','zero','comparison'],mm,'projection',SMALL),model,('zbe','seg','eiuj','sca'))
    cuts,m=numbers();c=cuts.make
    try:run('eiuk',['event','frame','unit','comparison'],m|{'zbe':lambda *xs:c(Q(7)),'seg':lambda *xs:True,'eiuj':lambda *xs:True},'native_uniqueness')
    except ValueError as e:assert 'rational number domain' in str(e) or 'Finite function domain' in str(e),str(e)
    else:raise AssertionError('Real uniqueness silently sampled')
    norm=norm_factory(cuts,());rows={'va':{('frame',)},'zbd':{('event',),('display',)},'eisb7':{('frame','reference','unit','comparison')},'seh':{(e,'frame','unit','comparison') for e in ('event','display')},'eiuj':{(e,'frame','unit',Q(7),'comparison') for e in ('event','display')}}
    m|={n:lambda *xs,rs=rs:norm(xs) in rs for n,rs in rows.items() if n!='seh'}
    # seh's three passed functions are preserved in production; its full-real
    # body was checked with explicit projection above, not enumerated here.
    m['seh']=lambda e,f,u,ctx,*fs:(e,f,u,ctx) in rows['seh']
    m|={'zbh':lambda *xs:'reference','zbe':lambda *xs:c(Q(7))}
    count+=perturb(lambda mm:run('eiul',['event','display','frame','unit','comparison'],mm),m,{n:rs for n,rs in rows.items() if n!='seh'},norm)
    for e in ('event','display'):
        assert not run('eiul',['event','display','frame','unit','comparison'],m|{'seh':lambda event,*xs,e=e:event!=e});count+=1
        assert not run('eiul',['event','display','frame','unit','comparison'],m|{'zbe':lambda event,*xs,e=e:c(Q(9 if event==e else 7))});count+=1
    unknowns(lambda mm:run('eiul',['event','display','frame','unit','comparison'],mm),m,('seh','zbe','zbh','sca'))
    for root,target,args,row in [('eium','eiuk',['event','frame','comparison'],('event','frame','unit','comparison')),('eiun','eiul',['event','display','frame','comparison'],('event','display','frame','unit','comparison'))]:
        count+=perturb(lambda mm:run(root,args,mm),{target:relation({row})},{target:{row}})
    return dict(cases=count,all_real_uniqueness_preserved_and_native_domain_refused=True,candidate_existence_display_uniqueness_and_numeric_equality_separated=True,same_event_frame_unit_context_connected=True)

@lru_cache(None)
def motion_checks():
    cuts,m=numbers();c=cuts.make;count=0
    def speed(xs,components):
        f,g,lu,tu,axis,ctx=xs
        if (f,g,lu,tu,ctx)!=('frame','otherframe','lengthunit','unit','comparison') or axis not in ('x','y','z'):forbidden()
        return c(Q(components[('x','y','z').index(axis)]))
    model=m|{'eiok':relation({('frame','otherframe','comparison')}),'eisli':lambda *xs:'lengthunit','eislj':lambda *xs:'unit'}
    for components in ((0,0,0),(1,0,0),(0,-2,0),(0,0,3),(-3,4,5)):
        mm=model|{'eislc':lambda *xs,cs=components:speed(xs,cs)}
        assert run('eiuo',['frame','otherframe','comparison'],mm)==any(components);count+=1
    model|={'eislc':lambda *xs:speed(xs,(0,-2,0))}
    count+=perturb(lambda mm:run('eiuo',['frame','otherframe','comparison'],mm),model,{'eiok':{('frame','otherframe','comparison')}})
    assert not run('eiuo',['frame','otherframe','comparison'],model|{'ba':lambda x:False});count+=1
    unknowns(lambda mm:run('eiuo',['frame','otherframe','comparison'],mm),model,('eislc','eisli','eislj','ba','sca','bb'))
    return dict(cases=count,current_complete_uniform_translation_bound=True,nonzero_vector_any_axis_and_sign=True,no_position_gap_or_speed_limit_added=True)

@lru_cache(None)
def logic_checks():
    # The carrier can overlap object roles; no huge event/frame product is needed.
    count=0
    for bits in product((False,True),repeat=7):
        available={pair for pair,yes in zip(product(SMALL,SMALL),bits[:4]) if yes}
        first,second,comparable=bits[4:]
        model={'zbd':lambda e:True,'va':lambda f:True,'eiuo':lambda f,g,c:comparable and (f,g,c)==('zero','one','comparison'),'eium':lambda e,f,c:(e,f) in available and c=='comparison','eiun':lambda a,b,f,c:(first if f=='zero' else second) if a!=b else True}
        valid=all(bits[:4]) and comparable
        assert run('eiuq',[],model,domain=SMALL)==(not valid or first==second)
        assert run('eiur',[],model,domain=SMALL)==(not valid or not first or not second);count+=2
    domain=('zero','one','two')
    model={'zbd':lambda e:True,'va':lambda f:True,'eiuo':lambda f,g,c:(f,g,c)==('zero','one','comparison'),'eium':lambda *xs:True,'eiun':lambda a,b,f,c:f=='zero' or 'two' in (a,b)}
    assert not run('eiuq',[],model,domain=domain)
    assert not run('eiur',[],model,domain=domain);count+=2
    assert model['eiun']('zero','one','zero','comparison') and not model['eiun']('zero','one','one','comparison')
    assert model['eiun']('zero','two','zero','comparison') and model['eiun']('zero','two','one','comparison')
    unknowns(lambda mm:run('eiur',[],mm,domain=domain),model,('zbd','va','eiuo','eium','eiun'))
    return dict(cases=count,all_four_availability_bits_checked=True,changed_and_preserved_pairs_do_not_satisfy_universal=True,empty_comparison_truth_not_nonabsoluteness_evidence=True,actual_current_adapters_and_native_sdx_sea_sed=True)

@lru_cache(None)
def norm_checks():
    rows={'eismo':{('author','eiul','eiuq',False,'paper','discourse')}}
    m={n:relation(rs) for n,rs in rows.items()};count=perturb(lambda mm:run('eius',[],mm),m,rows)
    assert run('eius',[],m|{n:forbidden for n in ('eiuq','eiul','eiun','eiok')});count+=1
    # Norms quantify the very same four time-availability slots as the claim.
    base={'rd':lambda:'zero','rb':lambda:'zero','eirf':lambda:'one','zbd':lambda e:True,'va':lambda f:True,'eiuo':lambda f,g,c:(f,g,c)==('zero','one','comparison'),'eiun':lambda a,b,f,c:a!=b and f=='zero'}
    normrows={('zero',a,b,'one','zero','eiul',False,'one','comparison') for a,b in (('zero','one'),('one','zero'))}
    for bits in product((False,True),repeat=4):
        available={p for p,yes in zip(product(SMALL,SMALL),bits) if yes}
        m=base|{'eium':lambda e,f,c:(e,f) in available,'eismp':relation(normrows)}
        assert run('eiut',[],m,domain=SMALL);count+=1
        assert run('eiut',[],m|{'eismp':lambda *xs:False},domain=SMALL)==(not all(bits));count+=1
    m=base|{'eium':lambda *xs:True,'eismp':relation(normrows)}
    count+=perturb(lambda mm:run('eiut',[],mm,domain=SMALL),m,{'eismp':normrows})
    unknowns(lambda mm:run('eiut',[],mm,domain=SMALL),m,('eium','eiuo','eiun'))
    return dict(cases=count,prohibition_not_missing_permission_or_physical_truth=True,negative_epistemic_requirement_same_events_target_frame_unit_and_rule=True,norm_requires_all_four_times_and_universal_scope=True)

@lru_cache(None)
def presentation_checks():
    rows={'eismo':{('author','eiul','eiuq',False,'paper','discourse')},'eismq':{('conclusion','author','eius','eiuu','paper','discourse')},'eisdk':{('paper','eiue','eiuv','discourse')}}
    truth=lambda:Content(POINTS,(True,)*len(POINTS));false=lambda:Content(POINTS,(False,)*len(POINTS))
    m={n:relation(rs) for n,rs in rows.items()}|{'eiur':truth,'eiut':truth}
    count=perturb(lambda mm:run('eiuw',[],mm),m,rows)
    for n in ('eiur','eiut'):
        assert not run('eiuw',[],m|{n:false});count+=1
    assert run('eiuw',[],m|{n:forbidden for n in ('eiue','eiuq','eiul')});count+=1
    rows={'eir3':{('conclusion','author','paper','eiux','discourse')},'ue':{('previous','conclusion','discourse')}}
    m={n:relation(rs) for n,rs in rows.items()};count+=perturb(lambda mm:run('eiuy',[],mm),m,rows)
    assert run('eiuy',[],m|{n:forbidden for n in ('eiur','eiut','eismo','eismq','eisdk','eiun','eiok')});count+=1
    assert run('eiuy',[],m|{'eiun':lambda *xs:True,'eiur':false});count+=1
    return dict(cases=count,corrective_contrast_and_previous_reason_preserved=True,assertion_content_contains_claim_and_norm=True,author_attribution_does_not_require_claim_truth=True)

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert new.document['statements'][:-1]==old.document['statements'] and len(new.document['statements'])==266
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations']
    assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    prior=json.loads(read(PRIORS[0]));validate_hashes(ROOT,prior['source_sha256']);assert selection_binding(new,[264])==prior['selection']
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    load_annotations(ROOT,BASIS,ANNOTATIONS);assert json.loads(read(ANNOTATIONS))['entries']==json.loads(read('data/observer-contrast-identifiers-v1.json'))['entries']
    doc=parse(read(CORE));ds={d['name']:d for d in doc['declarations']};assert len(doc['statements'])==1
    assert ds['eiux']['body']['force']=='assert' and ds['eiux']['body']['content']['symbol']=='eiuw'
    for style in ('compact','full'):
        body=format_graph(doc,style);assert parse(body)==parse(transcribe(body,alphabet='v2'))==doc
    assert json.loads(read(SOURCE))==source_record()
    return dict(new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),preserved_statements=265,prior_meanings_and_reviews_preserved=True)

def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/SOURCE,json.dumps(source_record(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    results={n:fn() for n,fn in [('local',local_checks),('time',time_checks),('motion',motion_checks),('logic',logic_checks),('norms',norm_checks),('presentation',presentation_checks),('structure',structure_checks)]}
    source=source_record();paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(source['source_sha256'])|{SOURCE,DOC,INVENTORY,*PRIORS,*DEPENDENCIES,'scripts/compose_simultaneity_conclusion.py','scripts/check_simultaneity_conclusion.py','scripts/review_simultaneity_conclusion.py','tests/test_simultaneity_conclusion.py','scripts/check_moving_trip_geometry.py','scripts/check_coordinate_correspondence.py','scripts/check_rod_methods.py','scripts/check_rod_length_claims.py','scripts/check_material_relative_frame.py','scripts/check_tau_differential.py','scripts/compose_observer_contrast.py','scripts/compose_kinematics_headings.py','scripts/compose_material_relative_frame.py','scripts/compose_two_postulates.py','scripts/compose_relativity_conjecture.py','scripts/compose_limits.py'}
    return dict(status='simultaneity_comparison_and_interpretive_conclusion_connected_and_checked',document=FULL,**results,alignment=dict(segments=[dict(unit=s['unit'],unit_sha256=s['unit_sha256'],range=s['range'],source=s['text'],definitions=list(MEANINGS),status='explicit_interpretive_annotation') for s in source['segments']]),verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,remaining=['u0041の全単位判断登録','u0042以降と二作品全体の目標'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
