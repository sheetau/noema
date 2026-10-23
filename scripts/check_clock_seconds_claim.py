"""Check actual second conversion, all intervals and a quantified approximation."""
from functools import lru_cache
from fractions import Fraction as Q
from itertools import product
from xml.etree import ElementTree as ET
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
from scripts.check_clock_site_time import relation,perturb,unknowns,forbidden
from scripts.check_origin_clock_equations import model,RECORDS
from scripts.check_material_relative_frame import RS
from scripts.check_translated_light_trial import expose
from scripts.check_transverse_segment import refused
from scripts.compose_clock_seconds_claim import ROOT,read,PARENT_BASIS,FULL,CORE,BASIS,ANNOTATIONS,INDICES,MEANINGS,build

DOC='docs/clock-seconds-claim-v1.md';SOURCE='data/einstein-clock-seconds-claim-source-reading-v1.json'
INVENTORY='artifacts/written-units-v1/einstein-1905.json';PRIOR='data/einstein-origin-clock-time-u0124-review-v1.json'
DEPENDENCIES=('reports/origin-clock-time-v1.json','reports/origin-clock-question-v1.json','reports/clock-delay-v1.json')
CONSTANTS={'yn':'x','yo':'y','yp':'z','zc7':'time','rb':'duration','zik':'second','zb6':'context','rd':'author','eirf':'paper','eisn5':'section','zij':'derived','zim':'exact','zin':'approximation','zie':'clock','ri':'discourse'}
DOMAIN=tuple(dict.fromkeys((*CONSTANTS.values(),'a','b')));POINTS=('context','discourse','other')
BOUNDS={'ejjq':{'ejit'},'ejjs':{'svp','ejjq'},'ejjt':{'svp','ejjd','ejiu','ejjq','ejjs'},'ejju':{'ejjt'},'ejjv':{'ejju','swc'},'ejjw':{'ejjm','svp'},'ejiu':{'ejip','ejir','ejit'},'svx':{'sjo'},'svy':{'sjq','svx'},'swc':{'svy'}}

@lru_cache(None)
def core():return parse(read(CORE))

@lru_cache(None)
def fixture(name,mode='boundary'):
    doc=extract_document(core(),roots=[name],statement_indices=[]).document;bounds=NUM|{'sje','sjd','sky','zzbb','zzbd'}|BOUNDS.get(name,set())
    if mode=='integrated' and name=='ejjt':bounds=(bounds-{'ejjq','ejjs'})|{'ejit'}
    if mode=='binding' and name=='ejjs':bounds.add('ejjr')
    if mode=='full' and name=='swc':bounds.discard('svy')
    abstract(doc,bounds);doc=extract_document(doc,roots=[name],statement_indices=[]).document
    d=next(d for d in doc['declarations'] if d['name']==name)
    if mode=='instance':assert len(expose(d,{'forall','exists'},only_sort=RS))=={'ejju':1,'ejjw':1,'svx':1,'svy':2}[name]
    slots=[]
    for i,p in enumerate(d['parameters']):
        n='jcsc'+number_word(i);slots.append(n);doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']))
    expr=dict(kind='call',symbol=name,arguments=[dict(kind='call',symbol=n,arguments=[]) for n in slots])
    if d['result']=='content':
        doc['declarations'].append(dict(kind='primitive',name='jcscpoint',parameters=[],result='situation'));expr=dict(kind='evaluate',content=expr,situation=dict(kind='call',symbol='jcscpoint',arguments=[]))
    doc['statements']=[dict(kind='ask',body=expr)];return doc,slots

def run(name,args,m,mode='boundary',domain=DOMAIN):
    doc,slots=fixture(name,mode);assert len(args)==len(slots),(name,len(args),len(slots))
    mm={n:lambda x=x:x for n,x in CONSTANTS.items()}|{'jcscpoint':lambda:'discourse'}|m|{n:lambda x=x:x for n,x in zip(slots,args)}
    return evaluate_document(doc,individuals=domain,situations=POINTS,primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=800000,memoize_definitions=True,memoize_expressions=True)[0]['value']

@lru_cache(None)
def exact_checks():
    count=0
    for speed,duration in product((-4,-3,0,3,4),(Q(1,5),1,5,11)):
        cuts,m,coords,norm=model(speed);c=cuts.make;r=cuts.read;f=Q(3,5) if abs(speed)==4 else Q(4,5) if abs(speed)==3 else Q(1)
        vals=[Q(duration),Q(duration)*f,Q(duration)*(1-f)];args=[c(n) for n in vals]
        assert run('ejjr',args,m);count+=1
        for i in range(3):
            bad=args[:];bad[i]=c(vals[i]+Q(1,7));assert not run('ejjr',bad,m);count+=1
        for t in (0,-1):
            assert not run('ejjr',[c(Q(t)),c(Q(t)*f),c(Q(t)*(1-f))],m);count+=1
        if speed and duration!=1:
            assert not run('ejjr',[args[0],args[1],c(1-f)],m);count+=1
        unknowns(lambda mm:run('ejjr',args,mm),m,('tc','zb7','sky','sje'))
    # A scale is attached to two time units in one situation, not just a number.
    cuts,m,coords,norm=model();c=cuts.make
    for scale in (Q(1,5),Q(1),Q(2)):
        rows={'ci':{('duration',),('second',)},'zil':{norm(['duration','second',c(scale),'context'])}}
        mm=m|{n:lambda *xs,rs=rs:norm(xs) in rs for n,rs in rows.items()}
        count+=perturb(lambda mm:run('svp',[c(scale),'context'],mm),mm,rows,norm)
    for scale in (0,-1):assert not run('svp',[c(Q(scale)),'context'],m|{'ci':lambda *xs:True,'zil':lambda *xs:True});count+=1
    return dict(cases=count,positive_elapsed_seconds_and_exact_loss=True,total_loss_distinct_from_per_second_coefficient=True,positive_common_conversion_bound_to_units_and_context=True)

@lru_cache(None)
def pair_checks():
    cuts,m,coords,norm=model();c=cuts.make;count=0;domain=('a','b')
    def coordinate(rec,axis):
        if rec not in domain or axis!='a':forbidden()
        return c(Q(domain.index(rec)))
    small=m|{'zc7':lambda:'a','zc6':coordinate}
    for own1,own2 in product(domain,repeat=2):
        rows={'ejit':{('a',own1,'a','context'),('a',own2,'b','context')}};mm=small|{'ejit':relation(rows['ejit'])};args=['a',own1,'a',own2,'b','context']
        count+=perturb(lambda mm:run('ejjq',args,mm,domain=domain),mm,rows)
        for first,last in (('a','a'),('b','a'),('b','b')):
            bad=args[:];bad[2]=first;bad[4]=last;assert not run('ejjq',bad,small|{'ejit':lambda *xs:True},domain=domain);count+=1
    for scale in (Q(1,5),Q(1),Q(2)):
        T=5*scale;E=4*scale;L=scale;args=['clock','y','x','time','z',c(scale),c(T),c(E),c(L),'context']
        rows={'svp':{norm([c(scale),'context'])},'ejjq':{('clock','y','x','time','z','context')}}
        mm=m|{n:lambda *xs,rs=rs:norm(xs) in rs for n,rs in rows.items()};check=lambda mm:run('ejjs',args,mm)
        count+=perturb(check,mm,rows,norm)
        for i in (5,6,7,8):
            bad=args[:];bad[i]=c(cuts.read(args[i])+Q(1,7));assert not run('ejjs',bad,mm);count+=1
        for rec in RECORDS:
            coords[rec][3]+=1;assert not check(mm);coords[rec][3]-=1;count+=1
        unknowns(check,mm,('zc6',))
    return dict(cases=count,same_clock_both_event_pairs_and_positive_time_order=True,same_scale_on_actual_lab_and_clock_differences=True)

@lru_cache(None)
def all_interval_checks():
    cuts,m,coords,norm=model();c=cuts.make;count=0;domain=('a','b')
    # Two individual values suffice for every slot of the four-variable binding.
    for fo,fl,lo,ll in product(domain,repeat=4):
        times={'a':Q(0),'b':Q(1)}
        mm=m|{'zc7':lambda:'a','zc6':lambda rec,axis:c(times[rec]) if rec in times and axis=='a' else forbidden()}
        pair=('a',fo,fl,lo,ll,'context');T=times[ll]-times[fl];E=times[lo]-times[fo]
        rows={'svp':{norm([c(Q(1)),'context'])},'ejjd':{('a','context')},'ejiu':{norm(['a',c(Q(4,5)),'context'])},'ejjq':{pair},'ejjs':{norm(['a',fo,fl,lo,ll,c(Q(1)),c(T),c(E),c(T-E),'context'])}}
        mm|={n:lambda *xs,rs=rs:norm(xs) in rs for n,rs in rows.items()};check=lambda mm:run('ejjt',['a',c(Q(1)),'context'],mm,domain=domain)
        assert check(mm);count+=1
        for n in ('svp','ejjd','ejiu','ejjs'):
            for row in rows[n]:
                assert not check(mm|{n:lambda *xs:False});count+=1
                for i in range(len(row)):
                    bad=tuple('other' if i==j else x for j,x in enumerate(row));assert not check(mm|{n:lambda *xs,bad=bad:norm(xs)==bad});count+=1
    pairs={('x','y','x','context'),('x','time','z','context')}
    for scale in (Q(1,5),Q(1),Q(2)):
        rows={'svp':{norm([c(scale),'context'])},'ejjd':{('x','context')},'ejiu':{norm(['x',c(Q(4,5)),'context'])},'ejit':pairs}
        mm=m|{n:lambda *xs,rs=rs:norm(xs) in rs for n,rs in rows.items()};args=['x',c(scale),'context']
        assert run('ejjt',args,mm,'integrated',RECORDS);count+=1
        coords['time'][3]+=1;assert not run('ejjt',args,mm,'integrated',RECORDS);coords['time'][3]-=1;count+=1
        assert not run('ejjt',args,mm|{'ejiu':lambda *xs:False},'integrated',RECORDS);count+=1
    # Check the reused native all-pairs rate, with the same current record table.
    mm=m|{'ejip':relation({('x','context')}),'ejir':relation({('x','context')}),'ejit':relation(pairs)}
    assert run('ejiu',['x',c(Q(4,5)),'context'],mm,domain=RECORDS);count+=1
    assert not run('ejiu',['x',c(Q(1)),'context'],mm,domain=RECORDS);count+=1
    assert not run('ejiu',['x',c(Q(4,5)),'context'],mm|{'ejit':relation({('x','y','x','context')})},domain=RECORDS);count+=1
    return dict(cases=count,all_four_record_slots_and_one_scale_for_every_interval=True,native_seconds_relations_across_all_current_pairs=True,native_rate_requires_nonzero_time_width=True)

@lru_cache(None)
def approximation_checks():
    count=0
    for speed in (-4,-3,0,3,4):
        cuts,m,coords,norm=model(speed);c=cuts.make;f=Q(3,5) if abs(speed)==4 else Q(4,5) if abs(speed)==3 else Q(1);lag=1-f;a=Q(speed*speed,50);err=lag-a
        vals=[Q(5),Q(speed),f,lag,a,err];args=[c(n) for n in vals]
        assert run('svq',args,m);count+=1
        for i in (2,3,4,5):
            bad=args[:];bad[i]=c(vals[i]+Q(1,100));assert not run('svq',bad,m);count+=1
        if speed:
            bad=args[:];bad[3]=c(a);bad[5]=c(Q(0));assert not run('svq',bad,m);count+=1
        for exact,bound in product((False,True),repeat=2):
            mm=m|{'ejju':lambda:Content(POINTS,(exact,)*len(POINTS)),'swc':lambda:bound}
            assert run('ejjv',[],mm)==(exact and bound);count+=1
    return dict(cases=count,exact_lag_second_order_value_and_residual_distinct=True,approximate_claim_requires_same_exact_clock_and_fourth_order_qualification=True)

def function_norm(cuts):
    samples=(Q(-3,5),Q(0),Q(3,5),Q(4,5))
    def norm(xs):
        def one(x):
            if not isinstance(x,FunctionValue):return x
            if x.parameters==('number',):return cuts.read(x)
            return tuple((cuts.read(x(cuts.make(t))) if x.result==RS else x(cuts.make(t))) for t in samples)
        return tuple(one(x) for x in xs)
    return norm

@lru_cache(None)
def asymptotic_checks():
    cuts,m,coords,_=model();c=cuts.make;r=cuts.read;norm=function_norm(cuts);count=0
    dom=FunctionValue((RS,),'truth',lambda x:abs(r(x))<1);fun=FunctionValue((RS,),RS,lambda x:c(3*r(x)));approx=FunctionValue((RS,),RS,lambda x:c(2*r(x)));scale=FunctionValue((RS,),RS,lambda x:c(abs(r(x))))
    args=[dom,fun,approx,scale,c(Q(0)),c(Q(1)),c(Q(1))]
    rows={'sjo':{norm([dom,f]) for f in (fun,approx,scale)}};mm=m|{'sjo':lambda *xs:norm(xs) in rows['sjo']}
    for x in (Q(-3,5),Q(0),Q(3,5),Q(4,5)):
        assert run('svx',args+[c(x)],mm,'instance');count+=1
        if x:
            bad=args[:];bad[5]=c(Q(1,2));assert not run('svx',bad+[c(x)],mm,'instance');count+=1
            bad=args[:];bad[3]=FunctionValue((RS,),RS,lambda x:c(-abs(r(x))));assert not run('svx',bad+[c(x)],mm|{'sjo':lambda *xs:True},'instance');count+=1
    for slot in (5,6):
        bad=args[:];bad[slot]=c(Q(0));assert not run('svx',bad+[c(Q(3,5))],mm,'instance');count+=1
    for f in (fun,approx,scale):
        assert not run('svx',args+[c(Q(3,5))],mm|{'sjo':lambda *xs,missing=norm([dom,f]):norm(xs) in rows['sjo']-{missing}},'instance');count+=1
    refused(lambda:run('svx',args,mm))
    rows={'sjq':{norm(args[:1]+[args[4]])},'svx':{norm(args)}};mm=m|{n:lambda *xs,rs=rs:norm(xs) in rs for n,rs in rows.items()}
    count+=perturb(lambda mm:run('svy',args,mm,'instance'),mm,rows,norm)
    refused(lambda:run('svy',args[:5],mm))
    # Capture the actual domain and three functions used by the source claim.
    seen=[]
    def capture(*xs):seen.append(xs);return True
    assert run('swc',[],m|{'svy':capture});count+=1
    domain,exact,estimate,fourth,point=seen[0];assert r(point)==0
    for x in (Q(-4,5),Q(-3,5),Q(0),Q(3,5),Q(4,5)):
        f=Q(3,5) if abs(x)==Q(4,5) else Q(4,5) if abs(x)==Q(3,5) else Q(1)
        assert domain(c(x)) and r(exact(c(x)))==1-f and r(estimate(c(x)))==x*x/2 and r(fourth(c(x)))==x**4;count+=1
    for x in (-2,-1,1,2):assert not domain(c(Q(x)));count+=1
    refused(lambda:run('swc',[],m,'full'))
    return dict(cases=count,positive_common_bound_and_punctured_neighborhood=True,all_function_validity_and_accumulation_required=True,actual_zero_ratio_domain_and_three_error_functions=True,native_real_quantifiers_not_finitely_sampled=True)

@lru_cache(None)
def presentation_checks():
    cuts,m,coords,norm=model();c=cuts.make;count=0
    rows={'ejjt':{norm(['clock',c(Q(2)),'context'])}};mm=m|{'ejjt':lambda *xs:norm(xs) in rows['ejjt']}
    count+=perturb(lambda mm:run('ejju',[c(Q(2))],mm,'instance'),mm,rows,norm);refused(lambda:run('ejju',[],mm))
    for prior,convert in product((False,True),repeat=2):
        mm=m|{'ejjm':lambda:Content(POINTS,(not prior,prior,not prior)),'svp':lambda s,ctx:convert and (cuts.read(s),ctx)==(2,'context')}
        assert run('ejjw',[c(Q(2))],mm,'instance')==(prior and convert);count+=1
    refused(lambda:run('ejjw',[],mm))
    for name,rows in (
        ('ejjx',{'zc':{('exact','author','ejjw','ejju','section','discourse')}}),
        ('ejjy',{'uh':{('approximation','author','ejjv','section','discourse')}}),
        ('ejj3',{'eir3':{('exact','author','paper','ejjz','discourse')},'ue':{('derived','exact','discourse')}}),
        ('ejj4',{'eir3':{('approximation','author','paper','ejj2','discourse')},'ue':{('exact','approximation','discourse')}})):
        mm={n:relation(rs) for n,rs in rows.items()};count+=perturb(lambda mm:run(name,[],mm),mm,rows)
    return dict(cases=count,same_time_formula_and_common_second_conversion_as_premise=True,exact_consequence_and_qualified_reexpression_attributed_in_order=True)

@lru_cache(None)
def source_record():
    inv=json.loads(read(INVENTORY));u=inv['units'][124];assert u['id']=='einstein-1905:u0125';table={m['id']:m for m in inv['math']};math=[]
    for mid,flat in (('M0217','(1−1−(v/V)2)'),('M0218','12(v/V)2')):
        e=table[mid];root=ET.fromstring(e['mathml']);assert re.sub(r'\s','',''.join(root.itertext()))==flat
        ns='{http://www.w3.org/1998/Math/MathML}';assert len(root.findall('.//'+ns+'msqrt'))==(1 if mid=='M0217' else 0)
        math.append(dict(id=mid,sha256=e['sha256'],mathml_flat=flat))
    retrieval='artifacts/einstein-origin-clock-setting-v1/retrieval.json';rr=json.loads(read(retrieval));validate_hashes(ROOT,{x['path']:x['sha256'] for x in rr['sources']});paths={INVENTORY,DOC,retrieval,*(x['path'] for x in rr['sources'])}
    return dict(version='einstein-clock-seconds-claim-source-reading-v1',reviewer='assistant_visual_and_text_review',pages=['904'],segments=[dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[0,len(u['text'])],text=u['text'],source_nonblank_characters=len(re.sub(r'\s|\[M\d+\]','',u['text'])),math=math)],observations=['原刊904頁で比例式末尾のコンマからworaus folgt、同じ時計の指示、Kから見た比較、一秒当たりの厳密な遅れ、oder以下の二次近似と四次以上の留保、zurückbleibt.まで通読した。','M0217は1から正の平方根を引く無次元の一秒当たりの係数で、続くSek.が秒を示す。M0218は速度比の二乗の半分であり、厳密値へ等置する表示ではない。','四次以上の留保を速度比の零近傍のO(u⁴)という明示した読みへ接続する。原文に具体的な残差係数の上下限はなく、次のAからBへの運搬の帰結は別の段落である。'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert new.document['statements'][:-2]==old.document['statements'] and len(new.document['statements'])==343
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations'];assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    prior=json.loads(read(PRIOR));validate_hashes(ROOT,prior['source_sha256']);assert selection_binding(new,[340])==prior['selection']
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    load_annotations(ROOT,BASIS,ANNOTATIONS);doc=core();ds={d['name']:d for d in doc['declarations']};assert ds['ejjz']['body']['force']==ds['ejj2']['body']['force']=='assert'
    assert not [d for d in new.document['declarations'][len(old.document['declarations']):] if d['kind']=='primitive']
    names={d['name'] for d in extract_document(doc,roots=['ejjv'],statement_indices=[]).document['declarations']}
    assert {'ejjd','ejit','ejiu','svp','svq','svy','swc'}<=names and not {'zac','zdz','svc','swd','swe','svr','swh'}&names
    for style in ('compact','full'):
        body=format_graph(doc,style);assert parse(body)==parse(transcribe(body,alphabet='v2'))==doc
    assert source_record()==json.loads(read(SOURCE))
    return dict(new_definitions=len(MEANINGS),new_primitives=0,preserved_statements=341,prior_whole_unit_judgments_preserved=True)

def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/SOURCE,json.dumps(source_record(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    results={n:f() for n,f in [('exact',exact_checks),('pair',pair_checks),('all_intervals',all_interval_checks),('approximation',approximation_checks),('asymptotic',asymptotic_checks),('presentation',presentation_checks),('structure',structure_checks)]}
    helpers=('check_origin_clock_equations','check_coordinate_correspondence','check_moving_trip_geometry','check_clock_site_time','check_transverse_time','check_material_relative_frame','check_rod_methods','check_translated_light_trial','check_transverse_segment','compose_origin_clock_time','compose_solid_sphere_geometry','compose_material_relative_frame','compose_relativity_conjecture','compose_two_postulates','compose_limits','audit_opening_scope')
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(source_record()['source_sha256'])|{SOURCE,DOC,PRIOR,*DEPENDENCIES,'scripts/compose_clock_seconds_claim.py','scripts/check_clock_seconds_claim.py','tests/test_clock_seconds_claim.py',*(f'scripts/{n}.py' for n in helpers)}
    alignment=dict(segments=[dict(unit=s['unit'],unit_sha256=s['unit_sha256'],range=s['range'],source=s['text'],statements=list(INDICES),definitions=list(MEANINGS),status='explicit_interpretive_annotation') for s in source_record()['segments']])
    return dict(status='current_clock_exact_second_loss_and_fourth_order_qualified_approximation_connected',document=FULL,**results,alignment=alignment,verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,remaining=['u0125全体の通読判断と登録'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
