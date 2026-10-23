"""Check exact components, a common small parameter, and native derivative bindings."""
from functools import lru_cache
from fractions import Fraction as Q
from itertools import product
import json,re
from noema.grammar import parse,format_graph,number_word
from noema.extraction import extract_document
from noema.finite_semantics import Content,FunctionValue,evaluate_document
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.check_coordinate_correspondence import abstract
from scripts.check_moving_trip_geometry import NUM
from scripts.check_clock_site_time import perturb,unknowns,forbidden
from scripts.check_point_motion_transform import model,CONSTANTS,DOMAIN,POINTS
from scripts.check_material_relative_frame import RS
from scripts.check_translated_light_trial import expose
from scripts.check_transverse_segment import refused
from scripts.compose_velocity_first_order import ROOT,read,PARENT_BASIS,FULL,CORE,BASIS,ANNOTATIONS,MEANINGS,build

DOC='docs/velocity-first-order-v1.md';SOURCE='data/einstein-velocity-first-order-source-reading-v1.json'
INVENTORY='artifacts/written-units-v1/einstein-1905.json'
PRIORS=tuple(f'data/einstein-point-motion-u{n:04d}-review-v1.json' for n in (133,134))
DEPENDENCIES=('reports/point-motion-transform-v1.json','reports/point-motion-records-v1.json','reports/point-motion-claim-v1.json','reports/tau-differential-v1.json')
BOUNDS={'ejny':{'ejnl','eivz','ejmw','ejmv'},'ejn4':{'sjs'},'ejn5':{'ejn4'},'ejoa':{'ejn6'},'ejob':{'ejn5','ejoa'},'ejoc':{'ejnp','ejny','ejob'},'sjs':{'sjo','sjr'}}

@lru_cache(None)
def core():return parse(read(CORE))

@lru_cache(None)
def fixture(name,mode='boundary'):
    doc=extract_document(core(),roots=[name],statement_indices=[]).document
    bounds=NUM|{'sje','sjd','sjt','sky','zzbb','zzbd'}
    if mode!='native':bounds|=BOUNDS.get(name,set())
    abstract(doc,bounds);doc=extract_document(doc,roots=[name],statement_indices=[]).document
    d=next(d for d in doc['declarations'] if d['name']==name)
    if mode=='instance':assert len(expose(d,{'forall','exists'},only_sort=RS))=={'ejoa':5,'ejob':3,'ejoc':2}[name]
    slots=[]
    for i,p in enumerate(d['parameters']):
        n='jvfo'+number_word(i);slots.append(n);doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']))
    expr=dict(kind='call',symbol=name,arguments=[dict(kind='call',symbol=n,arguments=[]) for n in slots])
    if d['result']=='content':
        doc['declarations'].append(dict(kind='primitive',name='jvfopoint',parameters=[],result='situation'));expr=dict(kind='evaluate',content=expr,situation=dict(kind='call',symbol='jvfopoint',arguments=[]))
    elif d['result']==RS:
        doc['declarations'].append(dict(kind='primitive',name='jvforesult',parameters=[RS],result='truth'));expr=dict(kind='call',symbol='jvforesult',arguments=[expr])
    doc['statements']=[dict(kind='ask',body=expr)];return doc,slots


def run(name,args,m,mode='boundary'):
    doc,slots=fixture(name,mode);assert len(args)==len(slots),(name,len(args),len(slots))
    values=[]
    def capture(value):values.append(value);return True
    mm={n:lambda x=x:x for n,x in CONSTANTS.items()}|{'jvfopoint':lambda:'discourse','jvforesult':capture}|m|{n:lambda x=x:x for n,x in zip(slots,args)}
    result=evaluate_document(doc,individuals=DOMAIN,situations=POINTS,primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=500000,memoize_definitions=True,memoize_expressions=True)[0]['value']
    return values[0] if values else result


def relations(m,rows,norm):return m|{n:lambda *xs,rs=rs:norm(xs) in rs for n,rs in rows.items()}


@lru_cache(None)
def numeric_checks():
    cuts,m,coords,norm,beta,den=model();c=lambda x:cuts.make(Q(x));r=cuts.read;count=0;negative=0
    for first,second in product(((0,0,0),(1,-2,3),(-2,4,-6)),repeat=2):
        result=tuple(a+b for a,b in zip(first,second));args=list(map(c,(*first,*second,*result)))
        assert run('ejnw',args,m);count+=1
        for slot in range(9):
            bad=args[:];bad[slot]=c(r(bad[slot])+1);assert not run('ejnw',bad,m);count+=1
    for speed,u,w in product((-3,0,3),(-10,-3,0,2),(-1,0,2)):
        cuts,m,coords,norm,beta,den=model(speed,u,w,1);c=lambda x:cuts.make(Q(x));r=cuts.read
        X,Y=(Q(speed+u)/den,Q(w)/(beta*den));args=list(map(c,(5,speed,u,w,X,Y)))
        assert run('ejnx',args,m);count+=1
        if den<0:negative+=1
        assert run('ejn6',args,m)==(speed>0 and (X,Y)!=(speed+u,w));count+=1
        for slot in (4,5):
            bad=args[:];bad[slot]=c(r(bad[slot])+1);assert not run('ejnx',bad,m);count+=1
    assert negative
    cuts,m,coords,norm,beta,den=model();c=lambda x:cuts.make(Q(x));r=cuts.read
    args=list(map(c,(5,3,2,-1,Q(125,31),Q(-20,31))))
    unknowns(lambda mm:run('ejnx',args,mm),m,('sky','sje','sca','ba'))
    # Domain checks are separate from partial division/root evaluations.
    for a,b,w,scale in ((Q(3,5),Q(2,5),Q(-1,5),0),(1,-2,7,1),(1,-2,7,Q(4,5)),(0,-10,-2,-7)):
        expected=(scale*a)**2<1 and 1+scale**2*a*b>0
        assert run('ejnz',list(map(c,(a,b,w,scale))),m)==expected;count+=1
    for a,b,w,scale in product((Q(3,5),Q(-3,5)),(Q(-2,5),Q(2,5)),(Q(-1,5),0),(Q(-1),Q(0),Q(1))):
        d=1+scale**2*a*b;root=Q(1) if not scale else Q(4,5)
        x=scale*(a+b)/d;y=scale*w*root/d
        assert r(run('ejn2',list(map(c,(a,b,scale))),m))==x;count+=1
        assert r(run('ejn3',list(map(c,(a,b,w,scale))),m))==y;count+=1
        assert run('ejnx',list(map(c,(5,5*scale*a,5*scale*b,5*scale*w,5*x,5*y))),m);count+=1
    return dict(cases=count,negative_denominator_examples=negative,native_parallelogram_all_nine_slots=True,native_exact_components_and_common_scaling=True,special_exact_cases_preserved=True)


@lru_cache(None)
def derivative_checks():
    cuts,m,coords,norm,beta,den=model();c=lambda x:cuts.make(Q(x));r=cuts.read;count=0
    a,b,w=Q(3,5),Q(2,5),Q(-1,5);samples=(Q(-1),Q(0),Q(1));captured=[]
    def capture(*xs):captured.append(xs);return True
    args=list(map(c,(a,b,w)));assert run('ejn4',args,m|{'sjs':capture});assert len(captured)==2;count+=1
    expected=((Q(-25,31),Q(0),Q(25,31)),(Q(4,31),Q(0),Q(-4,31)))
    def fingerprint(xs):
        domain,function,point,slope=xs
        return (tuple(domain(c(t)) for t in samples),tuple(r(function(c(t))) for t in samples),r(point),r(slope))
    rows={'sjs':{((True,True,True),expected[0],Q(0),a+b),((True,True,True),expected[1],Q(0),w)}}
    mm=m|{'sjs':lambda *xs:fingerprint(xs) in rows['sjs']}
    count+=perturb(lambda mm:run('ejn4',args,mm),mm,rows,fingerprint)
    # Extensional equality of real cuts itself quantifies rationals. Inspect
    # this native puncture structurally, and require its finite refusal.
    declaration=next(d for d in core()['declarations'] if d['name']=='sjs')
    def calls(node,symbol):
        if isinstance(node,list):return [x for child in node for x in calls(child,symbol)]
        if not isinstance(node,dict):return []
        return ([node] if node.get('kind')=='call' and node['symbol']==symbol else [])+[x for child in node.values() for x in calls(child,symbol)]
    limit_call,=calls(declaration['body'],'sjr');puncture=limit_call['arguments'][0]
    var=lambda name:dict(kind='variable',name=name)
    t=var(puncture['parameters'][0]['name']);dp,fp,pp,sp=(var(p['name']) for p in declaration['parameters'])
    assert puncture['body']==dict(kind='and',arguments=[dict(kind='apply',function=dp,arguments=[t]),dict(kind='not',arguments=[dict(kind='equal',arguments=[t,pp])])]);count+=1
    for axis,(domain,function,point,slope) in enumerate(captured):
        assert fingerprint((domain,function,point,slope)) in rows['sjs'];count+=1
        for scale in (-2,2):assert not domain(c(scale));count+=1
        # Inspect the actual sjs body: same domain/function, punctured domain,
        # true difference quotient, base point and slope go into the limit.
        seen=[]
        def limit(*xs):seen.append(xs);return True
        native=m|{'sjt':lambda x:c(1/r(x)) if r(x) else forbidden(),'sjo':lambda d,f:tuple(d(c(t)) for t in samples)==(True,True,True) and tuple(r(f(c(t))) for t in samples)==expected[axis],'sjr':limit}
        assert run('sjs',[domain,function,point,slope],native);assert len(seen)==1;count+=1
        punctured,quotient,base,derivative=seen[0]
        refused(lambda:punctured(c(0)))
        assert r(base)==0 and r(derivative)==(a+b if axis==0 else w);count+=1
        for scale in (-1,1):
            assert domain(c(scale)) and r(quotient(c(scale)))==(r(function(c(scale)))-r(function(c(0))))/scale;count+=1
        assert not run('sjs',[domain,function,point,slope],native|{'sjo':lambda *xs:False});count+=1
        assert not run('sjs',[domain,function,point,slope],native|{'sjr':lambda *xs:False});count+=1
        unknowns(lambda mm:run('sjs',[domain,function,point,slope],mm),native,('sjo','sjr'))
        refused(lambda:run('sjs',[domain,function,point,slope],native,'native'))
        # Rational points with exact positive roots approach zero from both sides.
        errors=[]
        for n in (5,10,20,40):
            t=Q(1,n);scale=(2*t/(1+t*t))/a
            for sign in (-1,1):
                h=sign*scale;assert domain(c(h));assert r(quotient(c(h)))==r(function(c(h)))/h;count+=2
            errors.append(abs(r(quotient(c(scale)))-r(slope)))
        assert all(x>y>0 for x,y in zip(errors,errors[1:]));count+=1
    refused(lambda:run('ejn4',args,m,'native'))
    unknowns(lambda mm:run('ejn4',args,mm),mm,('sjs','sje','sky'))
    return dict(cases=count,native_two_derivatives_share_local_domain_base_and_common_scale=True,native_difference_quotient_evaluated_and_puncture_structure_checked=True,cut_equality_in_puncture_refuses_finite_enumeration=True,finite_error_samples_are_not_a_real_limit_proof=True,unbounded_real_derivative_refuses_finite_enumeration=True)


@lru_cache(None)
def bridge_checks():
    cuts,m,coords,norm,beta,den=model();c=lambda x:cuts.make(Q(x));count=0;X,Y=Q(125,31),Q(-20,31)
    rows={'ejnl':{('clock','context')},'eivz':{('context',)},'ejmw':{('clock','k',Q(2),Q(-1),'context')},'ejmv':{('clock','K',X,Y,Q(0),'context')}}
    mm=relations(m,rows,norm);args=['clock','context',c(X),c(Y)]
    count+=perturb(lambda mm:run('ejny',args,mm),mm,rows,norm)
    for slot in (2,3):
        bad=args[:];bad[slot]=c(cuts.read(bad[slot])+1);assert not run('ejny',bad,mm);count+=1
    unknowns(lambda mm:run('ejny',args,mm),mm,('tc','zb7','zkc','zkd','sky','sje'))
    rows={'ejn4':{(Q(3,5),Q(2,5),Q(-1,5))}};mm=relations(m,rows,norm);args=list(map(c,(5,3,2,-1)))
    count+=perturb(lambda mm:run('ejn5',args,mm),mm,rows,norm)
    assert not run('ejn5',list(map(c,(-5,3,2,-1))),m|{'ejn4':lambda *xs:True});count+=1
    return dict(cases=count,same_point_frames_full_current_histories_and_actual_velocities=True,all_normalized_components_use_same_positive_light_speed=True)


@lru_cache(None)
def quantifier_checks():
    cuts,m,coords,norm,beta,den=model();c=lambda x:cuts.make(Q(x));count=0
    args=list(map(c,(5,3,2,-1,Q(125,31),Q(-20,31))))
    rows={'ejn6':{tuple(cuts.read(x) for x in args)}};mm=relations(m,rows,norm)
    count+=perturb(lambda mm:run('ejoa',args,mm,'instance'),mm,rows,norm)
    refused(lambda:run('ejoa',args[:1],mm))
    rows={'ejn5':{(Q(5),Q(3),Q(2),Q(-1))},'ejoa':{(Q(5),)}};mm=relations(m,rows,norm)
    count+=perturb(lambda mm:run('ejob',args[:4],mm,'instance'),mm,rows,norm)
    for speed,u,w in ((3,10,-20),(3,-10,20),(0,2,-1),(-3,2,-1),(5,2,-1),(6,2,-1)):
        inside=0<speed<5
        patch=m|{'ejn5':lambda *xs:False,'ejoa':lambda *xs:True}
        assert run('ejob',list(map(c,(5,speed,u,w))),patch,'instance')==(not inside);count+=1
    refused(lambda:run('ejob',args[:1],mm))
    X,Y=Q(125,31),Q(-20,31);content_args=list(map(c,(X,Y)))
    rows={'ejny':{('clock','context',X,Y)},'ejob':{(Q(5),)}}
    mm=relations(m,rows,norm)|{'ejnp':lambda:Content(POINTS,(False,True,False))}
    count+=perturb(lambda mm:run('ejoc',content_args,mm,'instance'),mm,rows,norm)
    for first,second,third in product((False,True),repeat=3):
        patch=m|{'ejnp':lambda:Content(POINTS,(not first,first,not first)),'ejny':lambda *xs:second and norm(xs)==('clock','context',X,Y),'ejob':lambda x:third and cuts.read(x)==5}
        assert run('ejoc',content_args,patch,'instance')==(first and second and third);count+=1
    unknowns(lambda mm:run('ejoc',content_args,mm,'instance'),mm,('ejnp','tc','zkb','zb6'))
    refused(lambda:run('ejoc',[],mm))
    return dict(cases=count,counterexample_same_five_witnesses_and_same_light_speed=True,universal_all_valid_point_components_no_added_speed_limit=True,same_content_point_and_current_physical_context=True,native_real_existential_and_universal_quantifiers_refuse_enumeration=True)


@lru_cache(None)
def source_record():
    u=json.loads(read(INVENTORY))['units'][134];assert u['id']=='einstein-1905:u0135'
    assert digest(u['text'].encode())==u['text_sha256']
    sentence='Das Gesetz vom Parallelogramm der Geschwindigkeiten gilt also nach unserer Theorie nur in erster Annäherung.'
    assert u['text']==sentence+' Wir setzen:'
    prior=json.loads(read('data/einstein-point-motion-claim-source-reading-v1.json'));validate_hashes(ROOT,prior['source_sha256'])
    paths={INVENTORY,DOC,'data/einstein-point-motion-claim-source-reading-v1.json',*prior['source_sha256']}
    return dict(version='einstein-velocity-first-order-source-reading-v1',reviewer='assistant_visual_and_text_review',pages=['905'],segments=[dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[0,len(sentence)],text=sentence,source_nonblank_characters=len(re.sub(r'\s','',sentence)),math=[])],observations=['原刊905頁のK三運動式、直後の平行四辺形則と第一近似の一文、Wir setzen以下の定義導入を画像と固定本文で再照合した。','小量を全速度の共通倍率とする解釈を採る。原文が倍率や誤差次数を逐語的に指定しているとはしない。','第一近似の成分内容のみの依存群。alsoの帰結、nach unserer Theorieの限定、著者の提示と後続の定義導入は未接続で、文・全単位の完了判断はしない。'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})


@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert new.document['statements']==old.document['statements'] and len(new.document['statements'])==354
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations'];assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    for p,selection in zip(PRIORS,([352,353],[353])):
        prior=json.loads(read(p));validate_hashes(ROOT,prior['source_sha256']);assert selection_binding(new,selection)==prior['selection']
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    load_annotations(ROOT,BASIS,ANNOTATIONS);doc=core();names=lambda root:{d['name'] for d in extract_document(doc,roots=[root],statement_indices=[]).document['declarations']}
    assert {'ejmu','eiyw','ejmv','ejmw','ejnl','syt','sjs','sjr','ejnw','ejoa'}<=names('ejoc')
    assert not {'zka','shd','zke','syu'}&names('ejoc')
    assert not [d for d in new.document['declarations'][len(old.document['declarations']):] if d['kind']=='primitive'] and not doc['statements']
    for style in ('compact','full'):
        body=format_graph(doc,style);assert parse(body)==parse(transcribe(body,alphabet='v2'))==doc
    assert source_record()==json.loads(read(SOURCE))
    return dict(new_definitions=len(MEANINGS),new_primitives=0,preserved_statements=354,prior_judgments_preserved=True)


def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/SOURCE,json.dumps(source_record(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    results={n:f() for n,f in [('numeric',numeric_checks),('derivative',derivative_checks),('bridge',bridge_checks),('quantifiers',quantifier_checks),('structure',structure_checks)]}
    helpers=('compose_point_motion_claim','compose_solid_sphere_geometry','compose_material_relative_frame','compose_relativity_conjecture','compose_limits','check_point_motion_transform','check_origin_clock_equations','check_transverse_time','check_clock_site_time','check_coordinate_correspondence','check_moving_trip_geometry','check_material_relative_frame','check_translated_light_trial','check_transverse_segment','audit_opening_scope')
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(source_record()['source_sha256'])|{SOURCE,DOC,*PRIORS,*DEPENDENCIES,'scripts/compose_velocity_first_order.py','scripts/check_velocity_first_order.py','tests/test_velocity_first_order.py',*(f'scripts/{n}.py' for n in helpers)}
    return dict(status='same_point_velocity_parallelogram_first_order_dependency_checked',document=FULL,**results,verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,remaining=['u0135第一文の帰結・我々の理論という限定と著者の提示','Wir setzen以下の速さ・角度の導入と全単位の意味判断'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
