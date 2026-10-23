"""Check physical bindings, native endpoint times, observations and method roles."""
from functools import lru_cache
from fractions import Fraction as Q
import json
from noema.grammar import parse,format_graph,number_word
from noema.extraction import extract_document
from noema.finite_semantics import DescriptionValue,SequenceValue,FunctionValue,evaluate_document
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.check_coordinate_correspondence import abstract
from scripts.check_material_relative_frame import arithmetic,RS,FS
from scripts.compose_rod_methods import ROOT,read,PARENT_BASIS,FULL,CORE,BASIS,ANNOTATIONS,INDICES,MEANINGS,PRIMITIVES,build
from scripts.review_rod_methods import SOURCE,DOC,INVENTORY,PRIORS,DEPENDENCIES,source_record

DOMAIN=('rod','ruler','observer','frame','movingframe','lengthunit','timeunit','xaxis','yaxis','zaxis','firstend','lastend','p','q','r','eventa','eventb','displaya','displayb','clocka','clockb','reference','placea','placeb','author','paper','scope','methoda','methodb','questionnode','lengthname','section','other')
POINTS=('methodactx','methodbctx','context','other')
NUM={'ba','bb','bc','bd','bf','bg','shv','sah','sca','zzba','zzbc','zzbg'}
BOUNDARIES={'eipk','eipf','eiah','eipe','eioj','sat','qo'}

def forbidden(*xs):raise ValueError('Unknown rod-methods input')
def value(x):
    if isinstance(x,DescriptionValue):return json.loads(x.syntax)['symbol']
    if isinstance(x,SequenceValue):return tuple(value(i) for i in x.items)
    return x
def relation(rows):return lambda *xs:tuple(value(x) for x in xs) in rows


@lru_cache(None)
def fixture(name,mode='boundary'):
    doc=extract_document(parse(read(CORE)),roots=[name],statement_indices=[]).document
    if mode!='full':abstract(doc,NUM|BOUNDARIES)
    d=next(d for d in doc['declarations'] if d['name']==name);slots=[];args=[]
    for i,p in enumerate(d['parameters']):
        n='jrmd'+number_word(i);slots.append(n);doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']));args.append(dict(kind='call',symbol=n,arguments=[]))
    body=dict(kind='call',symbol=name,arguments=args)
    if d['result']=='content':
        doc['declarations'].append(dict(kind='primitive',name='jrmdcontext',parameters=[],result='situation'));body=dict(kind='evaluate',content=body,situation=dict(kind='call',symbol='jrmdcontext',arguments=[]))
    doc['statements']=[dict(kind='ask',body=body)]
    return doc,slots


def evaluate(doc,m):return evaluate_document(doc,individuals=DOMAIN,situations=POINTS,primitives={d['name']:m.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=700000,memoize_definitions=True,memoize_expressions=True)[0]['value']
def run(name,args,m,mode='boundary'):
    doc,slots=fixture(name,mode);assert len(args)==len(slots)
    return evaluate(doc,m|{'jrmdcontext':lambda:'context'}|{n:(lambda x=x:x) for n,x in zip(slots,args)})


def constants():
    return {n:lambda x=x:x for n,x in {'xi':'rod','xj':'ruler','xk':'observer','ra':'frame','xl':'movingframe','ta':'lengthunit','rb':'timeunit','yn':'xaxis','yo':'yaxis','yp':'zaxis','xn':'firstend','xo':'lastend','xp':'eventa','xq':'eventb','xr':'clocka','xs':'clockb','xt':'placea','xu':'placeb','rc':'reference','ye':'methodactx','yf':'methodbctx','xw':'methoda','xx':'methodb','y3':'questionnode','rd':'author','eirf':'paper','xy':'scope','ri':'context','eisl6':'lengthname','eisdy':'section'}.items()}


def setup(length_a=5,length_b=4,time_a=7,time_b=7,target=7):
    cuts,m=arithmetic();c=cuts.make;r=cuts.read;m|=constants()
    m|={'bg':lambda a,b:r(a)<r(b),'sah':lambda a,b:c(r(a)*r(b)),'zzbg':lambda a,b:r(a)<r(b),'yb':lambda:c(Q(2)),'x2':lambda:c(Q(time_a)),'x3':lambda:c(Q(time_b)),'xv':lambda:c(Q(target))}
    contexts=('methodactx','methodbctx');frames=('frame','movingframe');bodies=('rod','ruler','observer');roles=('xaxis','yaxis','zaxis');probes=('firstend','lastend','p','q','r')
    members={'rod':{'p','q'},'ruler':{'q','r'},'observer':{'p','r'}}
    def span(f):
        if f not in frames:forbidden()
        return (6,8) if f=='frame' else (16,18)
    def position(b,f,a,p,t):
        if b not in bodies or f not in frames or a not in roles or p not in DOMAIN:forbidden()
        length=Q(length_b if f=='frame' else length_a)
        x=length if p in ('lastend','q') else Q(0)
        if f=='frame':x+=2*(t-7)
        return (x,Q(0),Q(0))[roles.index(a)]+100*bodies.index(b)
    families={(b,f,ctx,a):FunctionValue(('individual',),FS,lambda p,b=b,f=f,a=a:FunctionValue((RS,),RS,lambda t:c(position(b,f,a,p,r(t))))) for b in bodies for f in frames for ctx in contexts for a in roles}
    def family(b,f,l,tu,a,ctx):
        if (l,tu)!=('lengthunit','timeunit') or (b,f,ctx,a) not in families:forbidden()
        return families[b,f,ctx,a]
    def bounds(f,tu,ctx,i):
        if tu!='timeunit' or ctx not in contexts:forbidden()
        return c(Q(span(f)[i]))
    def endpoint(b,f,ctx,last=False):
        if b!='rod' or f not in frames or ctx not in contexts:forbidden()
        return 'lastend' if last else 'firstend'
    def velocity(f,g,l,tu,a,ctx):
        if (f,g,l,tu)!=('frame','movingframe','lengthunit','timeunit') or a not in roles or ctx not in contexts:forbidden()
        return c(Q(2 if a=='xaxis' else 0))
    m|={'eisls':lambda f,t,ctx:bounds(f,t,ctx,0),'eislt':lambda f,t,ctx:bounds(f,t,ctx,1),'eislu':family,'eislv':endpoint,'eislw':lambda b,f,ctx:endpoint(b,f,ctx,True),'eislc':velocity,'eirh':lambda b,p,ctx:b in members and p in members[b] and ctx in contexts}
    def norm(xs):
        def normalize(x):
            if not isinstance(x,FunctionValue):return value(x)
            if x.parameters==('number',):return r(x)
            if x.result=='truth':return tuple(p for p in DOMAIN if x(p))
            if x.result==FS:return tuple(r(x(p)(c(Q(t)))) for p in probes for t in (7,8))
            forbidden()
        return tuple(normalize(x) for x in xs)
    def history(b,f,ctx):return (b,f,ctx,'lengthunit','timeunit',*map(Q,span(f)),tuple(p for p in DOMAIN if p in members[b]),*(tuple(position(b,f,a,p,Q(t)) for p in probes for t in (7,8)) for a in roles))
    expected={'eiah':{history(b,'movingframe','methodactx') for b in bodies}|{history('ruler','frame','methodbctx')},'eipf':{history(b,'frame','methodactx')+(Q(2),) for b in ('ruler','observer')},'eipe':{history('rod','movingframe','methodactx')+('firstend','lastend',Q(length_a))}}
    m|={n:(lambda *xs,rows=rows:norm(xs) in rows) for n,rows in expected.items()}
    rows={'eipk':{('methodactx',),('methodbctx',)},'eioj':{('frame','movingframe','lengthunit','timeunit','methodactx')},'sat':{('frame','movingframe','methodactx')},'xa':{('rod',)},'xb':{('observer',)},'xc':{('ruler',)},'ti':{('lengthunit',)},'ci':{('timeunit',)},'xm':{('rod','frame',ctx) for ctx in contexts},'x4':{(b,'movingframe','methodactx') for b in bodies}|{('ruler','frame','methodbctx')},'xd':{('ruler','rod','movingframe','methodactx')},'xe':{('observer','ruler','rod','movingframe','lengthunit',Q(length_a),'methodactx')},'xf':{(p,'rod','frame','methodbctx') for p in ('firstend','lastend')},'xg':{(p,e,place,'frame','methodbctx') for p,e,place in (('firstend','eventa','placea'),('lastend','eventb','placeb'))},'xh':{('observer','ruler','placea','placeb','frame','lengthunit',Q(length_b),'methodbctx')},'th':{('placea','placeb','frame','lengthunit',Q(length_b))},'ca':{(x,) for x in ('clocka','clockb','reference')},'cc':{(x,'frame') for x in ('clocka','clockb','reference')},'cb':{(x,place,'frame') for xs,place in ((('eventa','displaya','clocka'),'placea'),(('eventb','displayb','clockb'),'placeb')) for x in xs},'zbd':{(x,) for x in ('eventa','eventb','displaya','displayb')},'eisgm':{(e,d,clock,'frame','methodbctx') for e,d,clock in (('eventa','displaya','clocka'),('eventb','displayb','clockb'))},'ce':{(clock,e,'frame','timeunit',Q(t)) for clock,es,t in (('clocka',('eventa','displaya'),time_a),('clockb',('eventb','displayb'),time_b)) for e in es},'qo':{(clock,'reference','frame','timeunit','methodbctx') for clock in ('clocka','clockb')},'zzbv':{(p,e,'methodbctx') for p,e in (('firstend','eventa'),('lastend','eventb'))},'eisl4':{('observer',p,e,clock,place,'frame','timeunit',Q(target),'methodbctx') for p,e,clock,place in (('firstend','eventa','clocka','placea'),('lastend','eventb','clockb','placeb'))}}
    # Native sb/sa binds the same endpoint event to the calibrated coordinates.
    rows['zzbu']={(e,'frame','methodbctx','lengthunit','timeunit',Q(target),*(position('rod','frame',a,p,Q(target)) for a in roles)) for p,e in (('firstend','eventa'),('lastend','eventb'))}
    m|={n:(lambda *xs,rs=rs:norm(xs) in rs) for n,rs in rows.items()}
    return cuts,m,rows,expected,norm


def unknowns(check,m,names):
    for n in names:
        try:check(m|{n:forbidden})
        except ValueError as e:assert 'Unknown rod-methods' in str(e)
        else:raise AssertionError(('Unknown input accepted',n))


def alter_rows(check,m,rows,norm,names):
    count=1;assert check(m)
    for n in names:
        for row in rows[n]:
            assert not check(m|{n:lambda *xs,rs=rows[n]-{row}:norm(xs) in rs});count+=1
            for i in range(len(row)):
                changed=tuple('other' if j==i else x for j,x in enumerate(row))
                assert not check(m|{n:lambda *xs,rs=(rows[n]-{row})|{changed}:norm(xs) in rs});count+=1
    return count


@lru_cache(None)
def comoving_checks():
    cuts,m,rows,expected,norm=setup();c=cuts.make;count=0
    check=lambda mm:run('eip2',[c(Q(5)),'methodactx'],mm)
    assert check(m)
    for n in ('eiah','eipf','eipe'):
        for row in expected[n]:
            # The method-b ruler rest row is unrelated to method a.
            if row[2]!='methodactx':continue
            assert not check(m|{n:lambda *xs,rs=expected[n]-{row}:norm(xs) in rs});count+=1
            for i in range(len(row)):
                changed=tuple('other' if j==i else x for j,x in enumerate(row))
                assert not check(m|{n:lambda *xs,rs=(expected[n]-{row})|{changed}:norm(xs) in rs});count+=1
    count+=alter_rows(check,m,rows,norm,('eioj','sat','xd','xe'))
    # Require all three same-speed components, including the zero transverse ones.
    for role in ('xaxis','yaxis','zaxis'):
        def wrong(*xs,role=role):return c(Q(3)) if xs[4]==role else m['eislc'](*xs)
        assert not check(m|{'eislc':wrong});count+=1
    for n in ('eirh','eislu','eisls','eislt','eislv','eislw','eislc','eiah','eipf','eipe','eioj'):unknowns(check,m,(n,))
    assert check(m|{'ya':forbidden});count+=1
    assert not run('eip3',[c(Q(5)),'methodactx'],m);count+=1
    assert not run('eip2',[c(Q(4)),'methodactx'],m);count+=1
    return dict(cases=count,all_three_bodies_comove_and_rest_in_same_moving_frame=True,shared_positive_velocity_and_no_transverse_drift=True,initial_length_and_actual_comparison_rest_not_assumed=True,history_boundaries_are_explicit_finite_inputs=True)


@lru_cache(None)
def endpoint_checks():
    cuts,m,rows,_,norm=setup();check=lambda mm:run('eip4',['methodbctx'],mm)
    count=alter_rows(check,m,rows,norm,('xf','xg','zzbv','zzbu','eisgm','ce','qo','cc','cb'))
    for name in ('eislv','eislw'):
        assert not check(m|{name:lambda *xs:'other'});count+=1
    for ta,tb,target,expected in ((7,8,7,False),(7,7,8,False),(7,7,7,True),(9,9,9,False),(6,6,6,True),(8,8,8,True)):
        _,mm,_,_,_=setup(time_a=ta,time_b=tb,target=target)
        assert run('eip4',['methodbctx'],mm)==expected;count+=1
    # Equal numeric displays alone cannot replace local coincidence or one reference.
    assert not check(m|{'eisgm':lambda *xs:False});count+=1
    assert not check(m|{'rc':lambda:'clocka'});count+=1
    unknowns(check,m,('eislu','eisls','eislt','eislv','eislw','xf','xg','zzbv','zzbu','eisgm','ce','qo'))
    return dict(cases=count,native_sbf_eing_saf_sae_and_sb_connected=True,same_two_endpoints_events_places_and_clock_displays=True,same_time_inside_motion_interval=True,same_section_one_reference=True)


@lru_cache(None)
def measurement_checks():
    cuts,m,rows,expected,norm=setup();c=cuts.make
    check=lambda mm:run('eip6',[c(Q(4)),'methodbctx'],mm)
    count=alter_rows(check,m,rows,norm,('eisl4','xh','th'))
    row=next(x for x in expected['eiah'] if x[2]=='methodbctx')
    assert not check(m|{'eiah':lambda *xs,rs=expected['eiah']-{row}:norm(xs) in rs});count+=1
    # No observer-rest condition appears in method b, and no direct contact is used.
    assert check(m|{'xd':forbidden,'xe':forbidden});count+=1
    assert check(m|{'ya':forbidden});count+=1
    assert not run('eip6',[c(Q(5)),'methodbctx'],m);count+=1
    # Both equal and unequal lengths are admissible across separately specified cases.
    for length_a,length_b in ((5,4),(5,5),(4,5)):
        cuts,mm,_,_,_=setup(length_a,length_b)
        assert run('eip2',[cuts.make(Q(length_a)),'methodactx'],mm)
        assert run('eip6',[cuts.make(Q(length_b)),'methodbctx'],mm);count+=2
    # A wrong geometrical distance cannot be hidden by making the ruler report it.
    cuts,m,rows,_,norm=setup();c=cuts.make
    altered={n:{tuple(Q(5) if x==Q(4) else x for x in row) for row in rows[n]} for n in ('th','xh')}
    assert not run('eip6',[c(Q(5)),'methodbctx'],m|{n:lambda *xs,rs=rs:norm(xs) in rs for n,rs in altered.items()});count+=1
    unknowns(lambda mm:run('eip6',[c(Q(4)),'methodbctx'],mm),m,('eisl4','xh','th','eiah','eipk'))
    unknown=FunctionValue(('number',),'truth',lambda x:x<4)
    try:run('eip6',[unknown,'methodbctx'],m)
    except ValueError:pass
    else:raise AssertionError('Unknown length decoded by sampling')
    return dict(cases=count,observer_localization_and_distance_measurement_required=True,same_ruler_now_stationary_in_rest_frame=True,no_method_b_observer_stationarity=True,equal_or_unequal_method_lengths_allowed=True,native_axis_distance_matches_measured_value=True)


def perturb(check,m,rows):
    count=1;assert check(m)
    for n,rs in rows.items():
        for row in rs:
            assert not check(m|{n:relation(rs-{row})});count+=1
            for i in range(len(row)):
                bad=tuple('other' if j==i else x for j,x in enumerate(row))
                assert not check(m|{n:relation((rs-{row})|{bad})});count+=1
    unknowns(check,m,tuple(rows));return count


@lru_cache(None)
def presentation_checks():
    base=constants();count=0
    rows={'xz':{('methoda','author','eip2','scope','context')},'eisl3':{('methoda','author','eipz','movingframe','frame','eip2','eip3','scope','paper','context')}}
    m=base|{n:relation(rs) for n,rs in rows.items()};count+=perturb(lambda mm:run('eip7',[],mm),m,rows)
    assert run('eip7',[],m|{n:forbidden for n in ('xe','eiah','eipf','eislu','ya')});count+=1
    rows={'xz':{('methodb','author','eip6','scope','context')},'eislp':{('methodb','author','section','eing','paper','context')},'eisl5':{('methodb','author','rod','lengthname',('eip2','eip6'),'scope','paper','context')}}
    m=base|{n:relation(rs) for n,rs in rows.items()};count+=perturb(lambda mm:run('eiqc',[],mm),m,rows)
    assert run('eiqc',[],m|{n:forbidden for n in ('ce','qo','xh','eisl4','xv')});count+=1
    for path in (CORE,FULL):
        original=parse(read(path))
        for i,(node,previous,msg,ordinal) in enumerate((('methoda','questionnode','eiqa',1),('methodb','methoda','eiqd',2))):
            doc=dict(original,statements=[original['statements'][-2+i]])
            rows={'eir3':{(node,'author','paper',msg,'context')},'eiskj':{(node,'questionnode',Q(ordinal),'paper','context')},'ue':{(previous,node,'context')}}
            m=base|{n:relation(rs) for n,rs in rows.items()};count+=perturb(lambda mm:evaluate(doc,mm),m,rows)
            assert evaluate(doc,m|{n:forbidden for n in ('xz','eisl3','eisl5','eislu','eisl4','xe','xh')});count+=1
    return dict(cases=count,procedure_comparison_not_value_equality=True,permissive_additive_naming_of_two_methods=True,ordered_a_b_and_section_reference=True,quotes_do_not_execute_measurements=True)


@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert new.document['statements'][:-2]==old.document['statements'] and len(new.document['statements'])==257
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations']
    assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    for path,indices in zip(PRIORS,([252,253,254],[243,244])):
        prior=json.loads(read(path));validate_hashes(ROOT,prior['source_sha256']);assert selection_binding(new,indices)==prior['selection']
    for path in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(path))['source_sha256'])
    load_annotations(ROOT,BASIS,ANNOTATIONS);ann=json.loads(read(ANNOTATIONS))['entries'];assert ann[:-1]==json.loads(read('data/rod-experiment-identifiers-v1.json'))['entries']
    assert ann[-1]['symbol']=='eisl6' and ann[-1]['forms'][0]['text']=='Länge des Stabes'
    doc=parse(read(CORE));ds={d['name']:d for d in doc['declarations']}
    assert {'eipe','eipd','eipf','eipg','eiah','eioj','sbe','sbf','sbi','sbk','eing','sb','saf','sae','eipa'}<=set(ds)
    def calls(node):
        if isinstance(node,dict):
            if node.get('kind')=='call':yield node
            for child in node.values():yield from calls(child)
        elif isinstance(node,list):
            for child in node:yield from calls(child)
    assert {'sbi','eipy','eipz'}<={x['symbol'] for x in calls(ds['eip2']['body'])}
    assert {'sbk','eip5','eipw','eipa'}<={x['symbol'] for x in calls(ds['eip6']['body'])}
    for n in ('eip2','eip3','eip6'):assert not any(x['symbol']=='ya' for x in calls(ds[n]['body']))
    for style in ('compact','full'):
        text=format_graph(doc,style);assert parse(text)==parse(transcribe(text,alphabet='v2'))==doc
    source=json.loads(read(SOURCE));assert source==source_record();validate_hashes(ROOT,source['source_sha256'])
    return dict(new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),preserved_statements=255,prior_question_clock_and_rod_judgments_preserved=True,two_original_pages_and_t_checked=True)


def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/SOURCE,json.dumps(source_record(),ensure_ascii=False,indent=2)+'\n')


@lru_cache(None)
def build_report():
    results={n:fn() for n,fn in [('comoving',comoving_checks),('endpoints',endpoint_checks),('measurement',measurement_checks),('presentation',presentation_checks),('structure',structure_checks)]}
    source=source_record();paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(source['source_sha256'])|{SOURCE,DOC,INVENTORY,*PRIORS,*DEPENDENCIES,'scripts/compose_rod_methods.py','scripts/check_rod_methods.py','scripts/review_rod_methods.py','tests/test_rod_methods.py','scripts/check_coordinate_correspondence.py','scripts/check_material_relative_frame.py','scripts/check_tau_differential.py','scripts/compose_material_relative_frame.py','scripts/compose_two_postulates.py','scripts/compose_relativity_conjecture.py','scripts/compose_limits.py'}
    return dict(status='two_length_measurement_methods_connected_and_checked',document=FULL,**results,alignment=dict(segments=[dict(unit=s['unit'],unit_sha256=s['unit_sha256'],range=s['range'],source=s['text'],definitions=list(MEANINGS),status='explicit_interpretive_annotation') for s in source['segments']]),verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,remaining=['二方法の全単位判断登録','u0032以降の長さの比較・導出'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
