"""Check whole histories, auxiliary inputs, all local readings and task roles."""
from functools import lru_cache
from fractions import Fraction as Q
from itertools import product
import json,re
from xml.etree import ElementTree as ET
from noema.grammar import parse,format_graph,number_word
from noema.extraction import extract_document
from noema.finite_semantics import Content,FunctionValue,evaluate_document
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.check_coordinate_correspondence import abstract
from scripts.check_moving_trip_geometry import NUM,numbers,norm_factory
from scripts.check_clock_site_time import relation,perturb,unknowns,forbidden
from scripts.check_homogeneity_claim import project,reject_full
from scripts.compose_comoving_time_task import ROOT,read,PARENT_BASIS,FULL,CORE,BASIS,ANNOTATIONS,INDEX,MEANINGS,LIMITS,TAU,build

DOC='docs/comoving-time-task-v1.md';SOURCE='data/einstein-comoving-time-task-source-reading-v1.json'
INVENTORY='artifacts/written-units-v1/einstein-1905.json';PRIOR='data/einstein-homogeneity-claim-review-v1.json'
DEPENDENCIES=('reports/homogeneity-claim-v1.json','reports/comoving-labels-v1.json','reports/event-coordinate-task-v1.json','reports/clock-site-time-v1.json','reports/frame-motion-v1.json')
RS=dict(kind='function',parameters=['number'],result='truth');FS=dict(kind='function',parameters=[RS],result=RS)
CONSTANTS={'ra':'frame','zbm':'moving','ta':'lengthunit','rb':'unit','yn':'x','yo':'y','yp':'z','zc7':'time','zb6':'context','rd':'author','eirf':'paper','eisms':'section','ri':'discourse','zdf':'previous','zdb':'task','zdj':'introduction','zdk':'invariance','zdl':'tautask','zdp':'purpose','eisdy':'firstsection'}
DOMAIN=tuple(dict.fromkeys(['point','moment','othermoment','event','place','clock','other',*[x for n,x in CONSTANTS.items() if n not in ('zb6','ri')]]))
POINTS=('context','discourse','other')

@lru_cache(None)
def fixture(name,mode='boundary'):
    doc=extract_document(parse(read(CORE)),roots=[name],statement_indices=[]).document
    boundaries=NUM.copy()
    if name=='eizm':boundaries|={'eit2','eivw'}
    if name=='eizn':boundaries|={'sb','eixu','lg'}
    if name=='eizo':boundaries.add('eizn')
    if name=='eizp':boundaries|={'eivz','eizm','eizo','eiwi','sil','lg'}
    if name=='eizq':boundaries.add('eizp')
    if name in ('eizu','eizv'):boundaries|={'eiy3','eiyz','eiy2','eiyy'}
    if name=='eizz':boundaries|={'eizu','eiyf','eiyx','eiyg','sin'}
    abstract(doc,boundaries);doc=extract_document(doc,roots=[name],statement_indices=[]).document
    if mode=='projection':doc=project(doc,[RS])
    if name=='eizv':return parse(format_graph(doc,'compact')+'r jctcandidate[] '+TAU+'.q[h[k eizv[]][k jctcandidate[]]].'),['jctcandidate']
    d=next(d for d in doc['declarations'] if d['name']==name);slots=[];args=[]
    for i,p in enumerate(d['parameters']):
        n='jct'+number_word(i);slots.append(n);doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']));args.append(dict(kind='call',symbol=n,arguments=[]))
    expr=dict(kind='call',symbol=name,arguments=args)
    if d['result']=='content':
        doc['declarations'].append(dict(kind='primitive',name='jctpoint',parameters=[],result='situation'));expr=dict(kind='evaluate',content=expr,situation=dict(kind='call',symbol='jctpoint',arguments=[]))
    doc['statements']=[dict(kind='ask',body=expr)];return doc,slots

def run(name,args,m,mode='boundary',domain=DOMAIN):
    doc,slots=fixture(name,mode);assert len(args)==len(slots)
    mm={n:lambda x=x:x for n,x in CONSTANTS.items()}|m|{n:lambda x=x:x for n,x in zip(slots,args)};mm.setdefault('jctpoint',lambda:'discourse')
    return evaluate_document(doc,individuals=domain,situations=POINTS,primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=1000000,memoize_definitions=True,memoize_expressions=True)[0]['value']

@lru_cache(None)
def history_checks():
    cuts,m=numbers();c=cuts.make;r=cuts.read;norm=norm_factory(cuts,(0,2));axes=('x','y','z')
    tracks={a:FunctionValue((RS,),RS,lambda t,i=i:c(Q(7+i))) for i,a in enumerate(axes)}
    def raw(p,f,lu,tu,a,ctx):
        if (p,f,lu,tu,ctx)!=('point','moving','lengthunit','unit','context') or a not in tracks:forbidden()
        return tracks[a]
    rows={'eit2':{norm(['point','moving','context','lengthunit','unit',c(Q(4)),c(Q(6)),*tracks.values()])},'eivw':{('point','context')}}
    m|={n:lambda *xs,rs=rs:norm(xs) in rs for n,rs in rows.items()};m|={'eismh':raw,'eisls':lambda *xs:c(Q(4)),'eislt':lambda *xs:c(Q(6))}
    check=lambda mm:run('eizm',['point','context'],mm);count=perturb(check,m,rows,norm)
    unknowns(check,m,('eismh','eisls','eislt'));assert check(m|{'eipw':forbidden});count+=1
    return dict(cases=count,own_frame_static_and_same_K_translation_both_required=True,complete_representative_not_material_internals=True)

@lru_cache(None)
def event_checks():
    cuts,m=numbers();c=cuts.make;r=cuts.read;norm=norm_factory(cuts,());axes=('x','y','z')
    times={'frame':Q(1),'moving':Q(5)};values={'frame':(4,5,6),'moving':(7,8,9)}
    bounds={'frame':(0,2),'moving':(4,6)}
    def raw(p,f,lu,tu,a,ctx):
        if (p,lu,tu,ctx)!=('point','lengthunit','unit','context') or f not in times or a not in axes:forbidden()
        val=values[f][axes.index(a)]
        return FunctionValue((RS,),RS,lambda t:c(Q(val)+(2*(r(t)-1) if f=='frame' and a=='x' else 0)))
    rows={'zce':{('point','moment','frame','lengthunit','context')},'zcf':{('moment','frame','unit','context'),('othermoment','moving','unit','context')},'zbd':{('event',)},'cb':{('event','place','frame')},'eisnk':{('event','moment','frame','context'),('event','othermoment','moving','context')},'sb':{('point','event',f,'context','lengthunit','unit',t,*map(Q,values[f])) for f,t in times.items()},'eixu':{('place','frame',a,Q(values['frame'][i]),'context') for i,a in enumerate(axes)},'lg':{(*map(Q,bounds[f]),t) for f,t in times.items()}}
    m|={n:lambda *xs,rs=rs:norm(xs) in rs for n,rs in rows.items()}
    m|={'eismh':raw,'eisls':lambda f,*xs:c(Q(bounds[f][0])),'eislt':lambda f,*xs:c(Q(bounds[f][1])),'yl':lambda mo,f,u,ctx:c(times[f]),'ym':lambda p,mo,f,u,a,ctx:c(Q(values[f][axes.index(a)]))}
    args=['point','moment','event','place','othermoment','context'];check=lambda mm:run('eizn',args,mm)
    count=perturb(check,m,rows,norm);unknowns(check,m,('eismh','ym','yl','eisls','eislt','ba','sca'))
    for axis in axes:
        assert not check(m|{'ym':lambda p,mo,f,u,a,ctx,axis=axis:c(Q(values[f][axes.index(a)]+(1 if a==axis else 0)))});count+=1
    assert check(m|{'eiyi':forbidden,'eiyg':forbidden});count+=1
    return dict(cases=count,same_point_event_and_frame_specific_moments_bound=True,all_three_actual_spatial_measurements_and_tracks_required=True,unequal_t_and_tau_allowed_without_K_clock_at_every_point=True)

@lru_cache(None)
def quantifier_checks():
    small=('a','b');count=0
    for row in product(small,repeat=5):
        check=lambda mm:run('eizo',[*row[:2],'context'],mm,domain=small)
        m={'eizn':relation({(*row,'context')})};assert check(m);count+=1
        assert not check({'eizn':lambda *xs:False});count+=1
        for i in (0,1):
            wrong=list(row[:2]);wrong[i]='a' if wrong[i]=='b' else 'b'
            assert not run('eizo',[*wrong,'context'],m,domain=small);count+=1
        assert not run('eizo',[*row[:2],'other'],m,domain=small);count+=1
    rows={'eivz':{('context',)},'eizm':{(p,'context') for p in small},'eizo':{(p,t,'context') for p,t in product(small,repeat=2)},'eiwi':{(t,'context') for t in small},'sil':{('context',)}}
    m={n:relation(rs) for n,rs in rows.items()}|{'ra':lambda:'a','zbm':lambda:'b','rb':lambda:'b','zdi':lambda p,ctx:ctx=='context','x4':lambda p,f,ctx:(f,ctx)==('b','context'),'eisk7':lambda f,p,ctx:(f,ctx)==('b','context'),'ys':lambda t,ctx:ctx=='context','eisla':lambda f,g,t,ctx:(f,g,ctx)==('a','b','context'),'eisls':lambda *xs:'a','eislt':lambda *xs:'b','lg':lambda lo,hi,t:(lo,hi)==('a','b')}
    check=lambda mm:run('eizp',['context'],mm,'projection',small);count+=perturb(check,m,rows)
    for p in small:
        for name,fn in [('zdi',lambda x,ctx,p=p:x!=p),('x4',lambda x,f,ctx,p=p:x!=p),('eisk7',lambda f,x,ctx,p=p:x!=p),('ys',lambda x,ctx,p=p:x!=p),('eisla',lambda f,g,x,ctx,p=p:x!=p)]:
            assert not check(m|{name:fn});count+=1
    unknowns(check,m,('zdi','x4','eisk7','ys','eisla','lg','eisls','eislt'))
    cuts,n=numbers();native=m|n|{'eisls':lambda *xs:cuts.make(Q(0)),'eislt':lambda *xs:cuts.make(Q(2)),'lg':lambda *xs:True}
    reject_full(lambda:run('eizp',['context'],native,domain=small));count+=1
    return dict(cases=count,existential_every_slot_checked_on_two_individuals=True,all_points_times_and_real_time_coverage_preserved=True,native_infinite_time_domain_refused=True)

@lru_cache(None)
def candidate_checks():
    cuts,m=numbers();c=cuts.make;r=cuts.read;axes=('x','y','z','time');domain=('a','b','c','d','frame','moving','lengthunit','unit',*axes)
    # Nonmember tuples have explicitly known irrelevant values because logical
    # implication is eager; this is not a fallback for unknown external input.
    values={t:(0,0,0,0) for t in domain}|{'a':(7,2,3,1),'b':(11,-2,4,3),'c':(80,90,100,17),'d':(110,120,130,10)}
    graph={('a','c'),('b','d')};speed=Q(2)
    m|={'eiy3':lambda:Content(POINTS,(True,True,True)),'eiyz':lambda t:t in ('a','b'),'eiy2':lambda t:t in ('c','d'),'eiyy':lambda a,b:(a,b) in graph,'zc6':lambda t,a:c(Q(values[t][axes.index(a)])),'zb7':lambda:c(speed),'zbi':lambda *xs:c(speed)}
    # Both tuples have x'=5, but different y,z,t. All four arguments matter.
    formula=lambda xp,y,z,t:xp+2*y+3*z-t
    good=FunctionValue((RS,)*4,RS,lambda *xs:c(formula(*map(r,xs))))
    count=0
    for name in ('eizu','eizv'):
        check=lambda mm:run(name,[good],mm,domain=domain)
        assert check(m);count+=1
        for patch in ({'eiy3':lambda:Content(POINTS,(False,True,True))},{'zbi':lambda *xs:c(Q(3))},{'ba':lambda x:r(x)!=10}):assert not check(m|patch);count+=1
        for role in axes:
            changed=dict(values);changed['d']=tuple(x+(1 if a==role else 0) for x,a in zip(changed['d'],axes))
            actual=check(m|{'zc6':lambda t,a,vs=changed:c(Q(vs[t][axes.index(a)]))})
            assert actual==(role!='time');count+=1
        for slot in range(4):
            wrong=FunctionValue((RS,)*4,RS,lambda *xs,slot=slot:c(formula(*(r(x)+(1 if i==slot else 0) for i,x in enumerate(xs)))))
            assert not run(name,[wrong],m,domain=domain);count+=1
        # Swapping source x with the moving measured xi cannot satisfy this example.
        assert not check(m|{'zc6':lambda t,a:c(Q(80 if t=='a' and a=='x' else values[t][axes.index(a)]))});count+=1
        unknowns(check,m,('eiy3','eiyz','eiy2','eiyy','zc6','zb7','zbi','ba','sca','bf','shv'))
    return dict(cases=count,native_x_minus_vt_and_all_four_arguments_checked=True,current_same_event_coordinate_graph_and_both_tuples_required=True,moving_xi_not_substituted_for_auxiliary_x=True,question_has_same_candidate_condition=True)

@lru_cache(None)
def clock_totality_checks():
    small=('a','b');candidate=FunctionValue(('individual',)*4,'individual',lambda xp,y,z,t:xp)
    # Explicit sort projection for the quantifier skeleton only. Numeric inputs
    # and the native clock body are checked separately and pinned dependencies.
    m={'ra':lambda:'a','zbm':lambda:'b','yn':lambda:'a','yo':lambda:'b','yp':lambda:'b','zc7':lambda:'a','zb7':lambda:'b','sin':lambda speed,x,t:x,'zc6':lambda first,role:first,'eizu':lambda f:all(f(x,'b','b','a')==x for x in small),'eiyf':lambda f,ctx:(f,ctx)==('b','context'),'zc4':lambda e:e in small,'eiyx':lambda e,t,f,ctx:e==t and (f,ctx)==('a','context'),'zcz':lambda e,f,ctx:(f,ctx)==('b','context'),'zbz':lambda f,cl,ctx:(f,ctx)==('b','context'),'cb':lambda obj,p,f:p=='a' and f=='b','ba':lambda x:x in small,'sca':lambda a,b:a==b,'eiyg':lambda e,cl,p,f,val,ctx:val==e and (p,f,ctx)==('a','b','context')}
    check=lambda mm:run('eizz',[candidate],mm,'projection',small);assert check(m);count=1
    for e,cl in product(small,repeat=2):
        base=m['eiyg']
        assert not check(m|{'eiyg':lambda ev,clock,p,f,val,ctx,e=e,cl=cl:base(ev,clock,p,f,val,ctx) and (ev,clock)!=(e,cl)});count+=1
        assert not check(m|{'eiyg':lambda ev,clock,p,f,val,ctx,e=e,cl=cl:base(ev,clock,p,f,val,ctx) or ((ev,clock)==(e,cl) and val!=e)});count+=1
    for name in ('eizu','eiyf'):
        assert not check(m|{name:lambda *xs:False});count+=1
    # Include both places: failure at the added place must now count.
    assert not check(m|{'cb':lambda obj,p,f:f=='b'});count+=1
    # No claim at a place with no deployed local clock; nonmembers are excluded.
    assert check(m|{'zbz':lambda f,cl,ctx:cl=='a' and (f,ctx)==('b','context'),'eiyg':lambda e,cl,p,f,val,ctx:cl=='a' and m['eiyg'](e,cl,p,f,val,ctx)});count+=1
    unknowns(check,m,('eizu','eiyf','zc4','eiyx','zcz','zbz','cb','eiyg','zc6','sin','ba','sca'))
    cuts,n=numbers();c=cuts.make
    native=m|n|{'zb7':lambda:c(Q(1)),'zc6':lambda *xs:c(Q(1)),'sin':lambda *xs:c(Q(1)),'eizu':lambda f:True,'eiyg':lambda *xs:True}
    fn=FunctionValue((RS,)*4,RS,lambda *xs:c(Q(1)))
    reject_full(lambda:run('eizz',[fn],native,domain=small));count+=1
    return dict(cases=count,all_events_local_clocks_and_values_required=True,extra_readings_rejected_not_only_candidate_existence=True,unclocked_places_and_nonmembers_not_added=True,projection_not_a_finite_semantic_judgment_of_all_reals=True)

@lru_cache(None)
def presentation_checks():
    rows={'zdm':{('introduction','author','sin','section','discourse')},'uh':{('invariance','author','eizq','section','discourse')},'zdg':{('invariance','author','eizq','section','discourse')},'ue':{('introduction','invariance','discourse')}}
    m={n:relation(rs) for n,rs in rows.items()};count=perturb(lambda mm:run('eizr',[],mm),m,rows)
    assert run('eizr',[],m|{n:forbidden for n in ('sin','eizq','eizp','sil')});count+=1
    rows={'zdn':{('tautask','author','task','eizv','section','discourse')}};m={n:relation(rs) for n,rs in rows.items()};count+=perturb(lambda mm:run('eizw',[],mm),m,rows)
    rows={'zdo':{('purpose','author','eizz','tautask','section','discourse')},'eislp':{('purpose','author','firstsection','eiyo','paper','discourse')}};m={n:relation(rs) for n,rs in rows.items()};count+=perturb(lambda mm:run('eiz2',[],mm),m,rows)
    assert run('eiz2',[],m|{n:forbidden for n in ('eizz','eiyg','eiyf','eiyo')});count+=1
    for name,node,message,previous in (('eizt','introduction','eizs','previous'),('eizy','tautask','eizx','invariance'),('eiz4','purpose','eiz3','tautask')):
        rows={'eir3':{(node,'author','paper',message,'discourse')},'ue':{(previous,node,'discourse')}};m={n:relation(rs) for n,rs in rows.items()};count+=perturb(lambda mm:run(name,[],mm),m,rows)
    return dict(cases=count,adoption_obviousness_first_subtask_purpose_and_section_one_bound=True,quoted_physical_content_and_questions_not_executed=True,three_sentence_author_order_preserved=True)

@lru_cache(None)
def source_record():
    inv=json.loads(read(INVENTORY));u=inv['units'][47];assert u['id']=='einstein-1905:u0048' and len(u['text'])==437
    assert u['text_sha256']=='3c5d2ae9509876ee9f0bfb7f87bb80d968071fbf6b82d1aa365ffb062113ac95'
    assert sum(not c.isspace() for c in re.sub(r'\[M\d+\]','',u['text']))==314
    maths={m['id']:m for m in inv['math'] if m['id'] in u['math_ids']};entries=[]
    for mid,form,binding in zip(u['math_ids'],('x′=x−vt','k','x′,y,z','τ','x′,y,z','t','τ','k'),('sin/zb7/yl','zbm','sil/eizp','eizu/eizv','sin/zc6','zc6/zc7/ra','eizz/eiyg','zbm/eiyf'),strict=True):
        assert ''.join(ET.fromstring(maths[mid]['mathml']).itertext())==form
        entries.append(dict(id=mid,sha256=maths[mid]['sha256'],reading=form,binding=binding))
    prior='data/einstein-homogeneity-claim-source-reading-v1.json';old=json.loads(read(prior));validate_hashes(ROOT,old['source_sha256'])
    paths={INVENTORY,DOC,prior,'artifacts/einstein-frame-coordinates-v1/page-898.jpg','artifacts/einstein-frame-coordinates-v1/page-898.html','artifacts/einstein-frame-coordinates-v1/retrieval.json'}
    return dict(version='einstein-comoving-time-task-source-reading-v1',reviewer='assistant_visual_and_text_review',pages=['898'],unit=u['id'],unit_sha256=u['text_sha256'],range=[0,437],text=u['text'],source_nonblank_characters=314,math=entries,observations=['原刊898頁のSetzen wirからworden sindまで三文を視認し、八つの数式置換要素と照合した。','x′はx-vtと置く補助量で、ξではない。tとτは異なる系の時刻である。','so ist klar、zuerst、Zu diesem Zwecke、in Gleichungen auszudrücken、nichts anderes、Inbegriff、§1の参照と同期済みの限定を保持する。','後続の原点からの光往復はこの三文ではまだ指定されておらず、課題の具体化として次単位へ残す。'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert new.document['statements'][:-3]==old.document['statements'] and len(new.document['statements'])==277
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations']
    assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    prior=json.loads(read(PRIOR));validate_hashes(ROOT,prior['source_sha256']);assert selection_binding(new,[273])==prior['selection']
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    load_annotations(ROOT,BASIS,ANNOTATIONS);assert json.loads(read(ANNOTATIONS))['entries']==json.loads(read('data/homogeneity-claim-identifiers-v1.json'))['entries']
    doc=parse(read(CORE));ds={d['name']:d for d in doc['declarations']}
    assert all(ds[n]['body']['force']=='assert' for n in ('eizs','eizx','eiz3'))
    assert ds['eizv']['body']['kind']=='question'
    for style in ('compact','full'):
        body=format_graph(doc,style);assert parse(body)==parse(transcribe(body,alphabet='v2'))==doc
    assert json.loads(read(SOURCE))==source_record()
    return dict(new_definitions=len(MEANINGS),new_primitives=0,preserved_statements=274,prior_homogeneity_review_preserved=True,all_prior_meanings_and_old_mathematical_kernels_preserved=True)

def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/SOURCE,json.dumps(source_record(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    results={n:fn() for n,fn in [('history',history_checks),('events',event_checks),('quantifiers',quantifier_checks),('candidates',candidate_checks),('clocks',clock_totality_checks),('presentation',presentation_checks),('structure',structure_checks)]}
    source=source_record();paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(source['source_sha256'])|{SOURCE,DOC,PRIOR,*DEPENDENCIES,'scripts/compose_comoving_time_task.py','scripts/check_comoving_time_task.py','tests/test_comoving_time_task.py','scripts/check_homogeneity_claim.py','scripts/check_coordinate_correspondence.py','scripts/check_moving_trip_geometry.py','scripts/check_material_relative_frame.py','scripts/check_clock_site_time.py','scripts/check_rod_methods.py','scripts/compose_comoving_labels.py','scripts/compose_material_axes.py','scripts/compose_limits.py','scripts/compose_relativity_conjecture.py','scripts/compose_material_relative_frame.py','scripts/compose_two_postulates.py'}
    return dict(status='auxiliary_invariance_and_complete_clock_time_task_connected',document=FULL,**results,alignment=dict(segments=[dict(unit=source['unit'],unit_sha256=source['unit_sha256'],range=source['range'],source=source['text'],statements=list(range(INDEX,INDEX+3)),definitions=list(MEANINGS),status='explicit_interpretive_annotation')]),verified_full_units={'kant-1784':0,'einstein-1905':0},general_physical_invariance_proved=False,concrete_tau_transformation_derived=False,semantic_equivalence_automatically_proved=False,remaining=['u0048三文全体の通読判断登録','u0049以降と二作品全体の目標'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
