"""Check same-history bindings, hypothetical stages and the method-tagged inquiry."""
from functools import lru_cache
from fractions import Fraction as Q
import json
from noema.grammar import parse,format_graph,number_word
from noema.extraction import extract_document
from noema.finite_semantics import DescriptionValue,SequenceValue,FunctionValue,QuestionValue,evaluate_document
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.check_coordinate_correspondence import abstract
from scripts.check_material_relative_frame import arithmetic,RS,FS
from scripts.compose_rod_experiment import ROOT,read,PARENT_BASIS,FULL,CORE,BASIS,ANNOTATIONS,INDICES,MEANINGS,PRIMITIVES,build
from scripts.review_rod_experiment import SOURCE,DOC,INVENTORY,DEPENDENCY,PRIORS,source_record

DOMAIN=('rod','ruler','frame','lengthunit','timeunit','xaxis','yaxis','zaxis','left','right','p','q','r','observer','author','paper','scope','initialnode','motionnode','questionnode','explanation','methoda','methodb','other')
POINTS=('initial','placed','moving','methodactx','methodbctx','context','other')
NUM={'ba','bb','bc','bg','bf','bd','shv','sah','sca','zzba','zzbc'}
BOUNDARIES={'eipe','eipd','eipg','eiah'}

def forbidden(*xs):raise ValueError('Unknown rod-experiment input')
def value(x):
    if isinstance(x,DescriptionValue):return json.loads(x.syntax)['symbol']
    if isinstance(x,SequenceValue):return tuple(value(i) for i in x.items)
    return x
def relation(rows):return lambda *xs:tuple(value(x) for x in xs) in rows


@lru_cache(None)
def fixture(name,mode='boundary'):
    doc=extract_document(parse(read(CORE)),roots=[name],statement_indices=[]).document
    boundaries=BOUNDARIES|({'sbi','sbk'} if name=='sbv' else set())
    if mode=='stages':boundaries|={'eipj','eipk'}
    if mode!='full':abstract(doc,NUM|boundaries)
    d=next(d for d in doc['declarations'] if d['name']==name);slots=[];args=[]
    for i,p in enumerate(d['parameters']):
        n='jrex'+number_word(i);slots.append(n);doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']));args.append(dict(kind='call',symbol=n,arguments=[]))
    body=dict(kind='call',symbol=name,arguments=args)
    if d['result']=='content':
        doc['declarations'].append(dict(kind='primitive',name='jrexcontext',parameters=[],result='situation'));body=dict(kind='evaluate',content=body,situation=dict(kind='call',symbol='jrexcontext',arguments=[]))
    elif d['result']!='truth':
        doc['declarations'].append(dict(kind='primitive',name='jrexcapture',parameters=[d['result']],result='truth'));body=dict(kind='call',symbol='jrexcapture',arguments=[body])
    doc['statements']=[dict(kind='ask',body=body)]
    return doc,slots


def evaluate(doc,m):
    return evaluate_document(doc,individuals=DOMAIN,situations=POINTS,primitives={d['name']:m.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=500000,memoize_definitions=True,memoize_expressions=True)[0]['value']


def run(name,args,m,mode='boundary'):
    doc,slots=fixture(name,mode);assert len(args)==len(slots);captured=[]
    def capture(x):captured.append(x);return True
    result=evaluate(doc,m|{'jrexcontext':lambda:'context','jrexcapture':capture}|{n:(lambda x=x:x) for n,x in zip(slots,args)})
    return captured[0] if captured else result


def constants():
    return {n:lambda x=x:x for n,x in {'xi':'rod','xj':'ruler','ra':'frame','ta':'lengthunit','rb':'timeunit','yn':'xaxis','yo':'yaxis','yp':'zaxis','yc':'initial','eislr':'placed','yd':'moving','ye':'methodactx','yf':'methodbctx','y2':'initialnode','eisly':'motionnode','y3':'questionnode','xw':'methoda','xx':'methodb','rd':'author','eirf':'paper','xy':'scope','ri':'context','eisll':'explanation'}.items()}


def setup():
    cuts,m=arithmetic();c=cuts.make;r=cuts.read
    m|=constants();m|={'bg':lambda a,b:r(a)<r(b),'sah':lambda a,b:c(r(a)*r(b)),'ya':lambda:c(Q(5)),'yb':lambda:c(Q(2))}
    spans={'initial':(0,2),'placed':(4,6),'moving':(8,10),'other':(12,14)}
    bodies=('rod','ruler');roles=('xaxis','yaxis','zaxis');points=('p','q','r','left','right')
    members={'rod':{'p','q'},'ruler':{'q','r'}}
    def coordinate(b,ctx,axis,p,t):
        if b not in bodies or ctx not in spans or axis not in roles or p not in DOMAIN:forbidden()
        return Q(100*bodies.index(b)+10*list(spans).index(ctx)+3*roles.index(axis)+DOMAIN.index(p))+t
    families={(b,ctx,a):FunctionValue(('individual',),FS,lambda p,b=b,ctx=ctx,a=a:FunctionValue((RS,),RS,lambda t:c(coordinate(b,ctx,a,p,r(t))))) for b in bodies for ctx in spans for a in roles}
    def endpoint(b,f,ctx,last=False):
        if b not in bodies or f!='frame' or ctx not in spans:forbidden()
        return 'right' if last else 'left'
    def bound(f,tu,ctx,i):
        if (f,tu)!=('frame','timeunit') or ctx not in spans:forbidden()
        return c(Q(spans[ctx][i]))
    def family(b,f,lu,tu,a,ctx):
        if (f,lu,tu)!=('frame','lengthunit','timeunit') or (b,ctx,a) not in families:forbidden()
        return families[b,ctx,a]
    m|={'eisls':lambda f,tu,ctx:bound(f,tu,ctx,0),'eislt':lambda f,tu,ctx:bound(f,tu,ctx,1),'eislu':family,'eislv':endpoint,'eislw':lambda b,f,ctx:endpoint(b,f,ctx,True),'eirh':lambda b,p,ctx:b in members and p in members[b] and ctx in spans}
    def normalize(xs):
        def item(x):
            if not isinstance(x,FunctionValue):return value(x)
            if x.parameters==('number',):return r(x)
            if x.result=='truth':return tuple(p for p in DOMAIN if x(p))
            if x.result==FS:return tuple(r(x(p)(c(Q(t)))) for p in points for t in (0,1))
            forbidden()
        return tuple(item(x) for x in xs)
    def expected(body,ctx,axis=False,extra=None):
        row=(body,'frame',ctx,'lengthunit','timeunit',*map(Q,spans[ctx]),tuple(p for p in DOMAIN if p in members[body]),*(tuple(coordinate(body,ctx,a,p,Q(t)) for p in points for t in (0,1)) for a in roles))
        if axis:row+=('left','right')
        if extra is not None:row+=(Q(extra),)
        return row
    expected_rows={'eipe':{expected('rod',ctx,True,5) for ctx in ('initial','placed')},'eipd':{expected('rod','placed',True)},'eipg':{expected('rod','moving',True,2)},'eiah':{expected(b,'initial') for b in bodies}}
    m|={n:(lambda *xs,rows=rows:normalize(xs) in rows) for n,rows in expected_rows.items()}
    rows={'xa':{('rod',)},'xc':{('ruler',)},'yt':{('rod','initial')},'ti':{('lengthunit',)},'x4':{('rod','frame','initial'),('ruler','frame','initial')},'xd':{('ruler','rod','frame','initial')},'xb':{('observer',)},'xe':{('observer','ruler','rod','frame','lengthunit',Q(5),'initial')},'eislx':{('rod','initial','placed')},'yv':{('rod','placed','moving')},'yx':{('moving','methodactx'),('moving','methodbctx')}}
    m|={n:(lambda *xs,rs=rs:normalize(xs) in rs) for n,rs in rows.items()}
    return cuts,m,rows,expected_rows,normalize


def reject_unknown(check,m,names):
    for n in names:
        try:check(m|{n:forbidden})
        except ValueError as e:assert 'Unknown rod-experiment' in str(e)
        else:raise AssertionError(('Unknown input accepted',n))


@lru_cache(None)
def history_checks():
    cuts,m,rows,expected,normalize=setup();count=0
    for name,ctx,symbols in (('eipi','initial',('eipe','eiah')),('eipj','placed',('eipe','eipd')),('eipk','moving',('eipg',))):
        calls={n:[] for n in symbols};mm=dict(m)
        for n in symbols:
            def observe(*xs,n=n):calls[n].append(normalize(xs));return m[n](*xs)
            mm[n]=observe
        assert run(name,[ctx],mm);count+=1
        for n in symbols:
            assert len(calls[n])==1 and calls[n][0] in expected[n]
            row=calls[n][0]
            for slot in range(len(row)):
                bad=list(row);bad[slot]='other'
                assert not run(name,[ctx],m|{n:lambda *xs,bad=tuple(bad):normalize(xs)==bad});count+=1
        for n in ('eisls','eislt','eislu','eislv','eislw','eirh'):
            reject_unknown(lambda mm:run(name,[ctx],mm),m,(n,))
        reject_unknown(lambda mm:run(name,[ctx],mm),m,symbols)
    assert run('eiph',['ruler','initial'],m);count+=1
    # Selector mistakes must affect the complete-history condition.
    for n,fn in (('eisls',lambda *xs:cuts.make(Q(99))),('eislt',lambda *xs:cuts.make(Q(99))),('eislv',lambda *xs:'right'),('eislw',lambda *xs:'left'),('eirh',lambda *xs:False)):
        assert not run('eipi',['initial'],m|{n:fn});count+=1
    def swap_axes(b,f,l,t,a,ctx):return m['eislu'](b,f,l,t,{'xaxis':'yaxis','yaxis':'xaxis','zaxis':'zaxis'}[a],ctx)
    assert not run('eipi',['initial'],m|{'eislu':swap_axes});count+=1
    assert not run('eipi',['initial'],m|{'eiah':lambda *xs:False});count+=1
    for end in (0,-1):
        assert not run('eiph',['ruler','initial'],m|{'eislt':lambda *xs,end=end:cuts.make(Q(end)),'eiah':lambda *xs:True});count+=1
    # There is no required dwell time in the placed state.
    assert run('eipj',['placed'],m|{'eislt':m['eisls'],'eipe':lambda *xs:True,'eipd':lambda *xs:True});count+=1
    assert run('eipk',['moving'],m|{'ya':forbidden});count+=1
    assert not run('eipk',['moving'],m|{'yb':lambda:cuts.make(Q(5))});count+=1
    return dict(cases=count,all_history_slots_and_three_axes_bound=True,common_interval_for_rod_and_ruler=True,initial_length_not_fixed_after_motion=True,placement_dwell_time_not_required=True,boundary_interpretations_are_explicit_finite_inputs=True)


@lru_cache(None)
def measurement_checks():
    cuts,m,rows,_,normalize=setup();check=lambda mm:run('eipi',['initial'],mm);count=1;assert check(m)
    for n in ('xa','xc','yt','ti','x4','xd','xb','xe'):
        for row in rows[n]:
            assert not check(m|{n:lambda *xs,rs=rows[n]-{row}:normalize(xs) in rs});count+=1
            for slot in range(len(row)):
                bad=tuple('other' if i==slot else x for i,x in enumerate(row))
                assert not check(m|{n:lambda *xs,rs=(rows[n]-{row})|{bad}:normalize(xs) in rs});count+=1
    reject_unknown(check,m,('xd','xe','x4','xb'))
    # The observer exists but is not required to be the later observer or stationary.
    assert check(m|{'xk':forbidden});count+=1
    assert not check(m|{'ya':lambda:cuts.make(Q(6))});count+=1
    return dict(cases=count,same_ruler_rod_frame_unit_and_length=True,no_initial_observer_stationarity_or_identity_added=True,reading_required_not_inferred_from_geometry=True)


@lru_cache(None)
def stage_checks():
    cuts,m,rows,_,normalize=setup();check=lambda mm:run('eipm',[],mm);count=1;assert check(m)
    for n in ('eislx','yv','yx'):
        for row in rows[n]:
            assert not check(m|{n:lambda *xs,rs=rows[n]-{row}:normalize(xs) in rs});count+=1
            for slot in range(len(row)):
                bad=tuple('other' if i==slot else x for i,x in enumerate(row))
                assert not check(m|{n:lambda *xs,rs=(rows[n]-{row})|{bad}:normalize(xs) in rs});count+=1
    reject_unknown(check,m,('eislx','yv','yx','eipe','eipd','eipg'))
    for name,target in (('eislr','initial'),('yd','initial'),('yd','placed'),('yf','methodactx')):
        broad=m|{n:lambda *xs:True for n in ('eipj','eipk','eislx','yv','yx')}
        assert not run('eipm',[],broad|{name:lambda target=target:target},'stages');count+=1
    return dict(cases=count,initial_placed_moving_and_two_method_contexts_distinct=True,placement_then_motion_then_two_method_inheritance=True,unknown_stage_inputs_refused=True)


@lru_cache(None)
def question_checks():
    cuts,m,_,_,_=setup();count=0
    for va,vb in ((5,5),(5,4),(None,None)):
        mm=m|{'sbi':lambda x,ctx:ctx=='methodactx' and va is not None and cuts.read(x)==va,'sbk':lambda x,ctx:ctx=='methodbctx' and vb is not None and cuts.read(x)==vb}
        question=run('sbv',[],mm);assert isinstance(question,QuestionValue)
        for method in ('methoda','methodb','other'):
            for val in (4,5,6):
                want=(method=='methoda' and va==val) or (method=='methodb' and vb==val)
                assert question.function(method,cuts.make(Q(val)))==want;count+=1
    unknown=FunctionValue(('number',),'truth',lambda x:x<5)
    try:run('sbv',[],m|{'sbi':lambda x,ctx:cuts.read(x)==5,'sbk':lambda x,ctx:False}).function('methoda',unknown)
    except ValueError:pass
    else:raise AssertionError('Unknown question value sampled')
    try:run('eiph',['ruler','initial'],m,'full')
    except ValueError as e:assert 'rational number domain' in str(e) or 'Finite function domain' in str(e)
    else:raise AssertionError('Complete history finitely sampled')
    return dict(cases=count,same_different_and_absent_answers_allowed=True,method_tags_and_contexts_separate=True,unknown_values_and_full_histories_refused=True)


def perturb(check,m,rows):
    count=1;assert check(m)
    for n,rs in rows.items():
        for row in rs:
            assert not check(m|{n:relation(rs-{row})});count+=1
            for i in range(len(row)):
                bad=tuple('other' if j==i else x for j,x in enumerate(row))
                assert not check(m|{n:relation((rs-{row})|{bad})});count+=1
    reject_unknown(check,m,tuple(rows));return count


@lru_cache(None)
def presentation_checks():
    base=constants();count=0
    rows={'eisd3':{('initialnode','rod','paper','context'),('initialnode','ruler','paper','context')},'ug':{('initialnode','author','eipl','scope','context')}}
    m=base|{n:relation(rs) for n,rs in rows.items()};count+=perturb(lambda mm:run('eipn',[],mm),m,rows)
    rows={'eislz':{('motionnode','author','eipm','scope','context')},'ug':{('motionnode','author','eipm','scope','context')}}
    m=base|{n:relation(rs) for n,rs in rows.items()};count+=perturb(lambda mm:run('eipq',[],mm),m,rows)
    rows={'yz':{('questionnode','author','sbv','scope','context')},'eiskw':{('questionnode','th','context')},'eisl2':{('questionnode','author','rod','frame','moving','eipk','sbv',('methoda','methodb'),'scope','paper','context')},'eiskj':{('methoda','questionnode',Q(1),'paper','context'),('methodb','questionnode',Q(2),'paper','context')},'ue':{('questionnode','methoda','context'),('methoda','methodb','context')}}
    m=base|{n:relation(rs) for n,rs in rows.items()};count+=perturb(lambda mm:run('eipt',[],mm),m,rows)
    assert run('eipt',[],m|{n:forbidden for n in ('sbi','sbk','eipg','eislu','xe')});count+=1
    for path in (CORE,FULL):
        original=parse(read(path))
        for index,(node,prior,msg) in enumerate((('initialnode','explanation','eipo'),('motionnode','initialnode','eipr'),('questionnode','motionnode','eipu'))):
            doc=dict(original,statements=[original['statements'][-3+index]])
            rows={'eir3':{(node,'author','paper',msg,'context')},'ue':{(prior,node,'context')}}
            m=base|{n:relation(rs) for n,rs in rows.items()};count+=perturb(lambda mm:evaluate(doc,mm),m,rows)
            assert evaluate(doc,m|{n:forbidden for n in ('eislu','xe','eipe','eipg','ug','yz','eislz','eisl2')});count+=1
    return dict(cases=count,setup_instruction_imagination_and_inquiry_distinct=True,ordered_two_method_forward_reference=True,quotations_do_not_execute_physics_or_answers=True)


@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert new.document['statements'][:-3]==old.document['statements'] and len(new.document['statements'])==255
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations']
    assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    for path,indices in zip(PRIORS,([250,251],[251],[251])):
        prior=json.loads(read(path));validate_hashes(ROOT,prior['source_sha256']);assert selection_binding(new,indices)==prior['selection']
    dep=json.loads(read(DEPENDENCY));validate_hashes(ROOT,dep['source_sha256'])
    load_annotations(ROOT,BASIS,ANNOTATIONS);assert json.loads(read(ANNOTATIONS))['entries']==json.loads(read('data/rod-geometry-identifiers-v1.json'))['entries']
    doc=parse(read(CORE));ds={d['name']:d for d in doc['declarations']}
    assert {'eipe','eipd','eipg','eiah','eigy','sbq','sbv','sbi','sbk','se'}<=set(ds)
    assert ds['eipo']['body']['force']=='direct'
    assert ds['eipr']['body']['force']==ds['eipu']['body']['force']=='assert'
    def calls(node):
        if isinstance(node,dict):
            if node.get('kind')=='call':yield node
            for child in node.values():yield from calls(child)
        elif isinstance(node,list):
            for child in node:yield from calls(child)
    bound=[x for x in calls(ds['eipk']['body']) if x['symbol']=='eipg'];assert len(bound)==1
    assert bound[0]['arguments'][-1]==dict(kind='call',symbol='yb',arguments=[])
    assert not any(x['symbol']=='ya' for x in calls(ds['eipk']['body']))
    for style in ('compact','full'):
        text=format_graph(doc,style);assert parse(text)==parse(transcribe(text,alphabet='v2'))==doc
    source=json.loads(read(SOURCE));assert source==source_record();validate_hashes(ROOT,source['source_sha256'])
    return dict(new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),preserved_statements=252,prior_judgments_and_geometry_checks_preserved=True,three_sentences_and_five_math_roles=True)


def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/SOURCE,json.dumps(source_record(),ensure_ascii=False,indent=2)+'\n')


@lru_cache(None)
def build_report():
    results={n:fn() for n,fn in [('history',history_checks),('measurement',measurement_checks),('stages',stage_checks),('question',question_checks),('presentation',presentation_checks),('structure',structure_checks)]}
    source=source_record();s=source['segments'][0]
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(source['source_sha256'])|{SOURCE,DOC,INVENTORY,DEPENDENCY,*PRIORS,'scripts/compose_rod_experiment.py','scripts/check_rod_experiment.py','scripts/review_rod_experiment.py','tests/test_rod_experiment.py','scripts/check_coordinate_correspondence.py','scripts/check_material_relative_frame.py','scripts/check_tau_differential.py','scripts/compose_material_body_motion.py','scripts/compose_material_relative_frame.py','scripts/compose_two_postulates.py','scripts/compose_relativity_conjecture.py','scripts/compose_limits.py'}
    return dict(status='rod_experiment_three_sentences_connected_and_checked',document=FULL,**results,alignment=dict(segments=[dict(unit=s['unit'],unit_sha256=s['unit_sha256'],range=s['range'],source=s['text'],definitions=list(MEANINGS),status='explicit_interpretive_annotation')]),verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,remaining=['u0029全単位判断の登録','u0030/u0031の二測定方法の詳述と後続の比較・導出'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
