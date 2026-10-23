"""Check current local readings, a single axial pulse and the necessary equation."""
from functools import lru_cache
from fractions import Fraction as Q
from itertools import product
import json,re
from xml.etree import ElementTree as ET
from noema.grammar import parse,format_graph,number_word
from noema.extraction import extract_document
from noema.finite_semantics import Content,evaluate_document
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.check_coordinate_correspondence import abstract
from scripts.check_moving_trip_geometry import NUM,numbers,norm_factory
from scripts.check_clock_site_time import relation,perturb,unknowns,forbidden
from scripts.compose_axial_time_condition import ROOT,read,PARENT_BASIS,FULL,CORE,BASIS,ANNOTATIONS,INDEX,MEANINGS,LIMITS,build

DOC='docs/axial-time-condition-v1.md';SOURCE='data/einstein-axial-time-condition-source-reading-v1.json'
INVENTORY='artifacts/written-units-v1/einstein-1905.json';PRIOR='data/einstein-comoving-time-task-review-v1.json'
DEPENDENCIES=('reports/comoving-time-task-v1.json','reports/axial-clock-trip-v1.json','reports/clock-site-time-v1.json','reports/parallel-choice-v1.json')
LEGACY='examples/v014/einstein-axial-clock-trip.noema'
CONSTANTS={'ra':'frame','zbm':'moving','ta':'lengthunit','rb':'unit','yn':'x','yo':'y','yp':'z','zc7':'time','zb6':'context','rd':'author','eirf':'paper','eisms':'section','ri':'discourse','zdq':'trial','zdr':'firstclock','zds':'secondclock','zdu':'setup','zdv':'inference','zdp':'purpose'}
DOMAIN=tuple(dict.fromkeys(['depart','reflection','arrival','tuple','origin','mirror','ray','axis','other',*[x for n,x in CONSTANTS.items() if n not in ('zb6','ri')]]))
POINTS=('context','discourse','other')

@lru_cache(None)
def fixture(name):
    doc=extract_document(parse(read(LEGACY if name=='sis' else CORE)),roots=[name],statement_indices=[]).document
    boundaries=NUM|{'bj'}
    if name=='eiz5':boundaries.add('eiyx')
    if name=='eiz6':boundaries.add('eiz5')
    if name=='eiz7':boundaries|={'eiyg','eiyi','eiyj'}
    if name=='ei2a':boundaries|={'eiz7','qo'}
    if name=='ei2b':boundaries|={'eixt','eiyf','eiy3','ei2a','eizm','eiz6'}
    if name=='ei2c':boundaries.add('ei2b')
    if name=='qo':boundaries|={'da','bi'}
    abstract(doc,boundaries);doc=extract_document(doc,roots=[name],statement_indices=[]).document
    d=next(d for d in doc['declarations'] if d['name']==name);slots=[];args=[]
    for i,p in enumerate(d['parameters']):
        n='jatc'+number_word(i);slots.append(n);doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']));args.append(dict(kind='call',symbol=n,arguments=[]))
    expr=dict(kind='call',symbol=name,arguments=args)
    if d['result']=='content':
        doc['declarations'].append(dict(kind='primitive',name='jatcpoint',parameters=[],result='situation'));expr=dict(kind='evaluate',content=expr,situation=dict(kind='call',symbol='jatcpoint',arguments=[]))
    doc['statements']=[dict(kind='ask',body=expr)];return doc,slots

def run(name,args,m,domain=DOMAIN):
    doc,slots=fixture(name);assert len(args)==len(slots)
    mm={n:lambda x=x:x for n,x in CONSTANTS.items()}|m|{n:lambda x=x:x for n,x in zip(slots,args)};mm.setdefault('jatcpoint',lambda:'discourse')
    return evaluate_document(doc,individuals=domain,situations=POINTS,primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=500000,memoize_definitions=True,memoize_expressions=True)[0]['value']

def exact_numbers():
    cuts,m=numbers();m['bj']=lambda scale,val:cuts.make(scale*cuts.read(val));return cuts,m

@lru_cache(None)
def label_checks():
    cuts,m=exact_numbers();c=cuts.make;r=cuts.read;rows={'eiyx':{('reflection','tuple','frame','context')}}
    m|={n:relation(rs) for n,rs in rows.items()};m['zb7']=lambda:c(Q(2));coords={'x':Q(7),'y':Q(5),'z':Q(-4),'time':Q(3)}
    def coordinate(t,a):
        if t!='tuple' or a not in coords:forbidden()
        return c(coords[a])
    m['zc6']=coordinate;args=['reflection','tuple',c(Q(1)),'context'];check=lambda mm:run('eiz5',args,mm)
    count=perturb(check,m,rows);unknowns(check,m,('zc6','zb7','ba','sca','bf','shv'))
    for label in (-3,0,1,4):
        expected=Q(label);mm=m|{'zc6':lambda t,a,label=label:c(Q(label+6) if a=='x' else coords[a])}
        assert run('eiz5',['reflection','tuple',c(expected),'context'],mm);count+=1
    for patch in ({'zb7':lambda:c(Q(3))},{'zc6':lambda t,a:c(coords[a]+(1 if a=='time' else 0))},{'zc6':lambda t,a:c(Q(80) if a=='x' else coords[a])},{'ba':lambda x:False}):assert not check(m|patch);count+=1
    # y,z are not zeroed merely because the trial is longitudinal.
    assert check(m|{'zc6':lambda t,a:c(Q(100) if a in ('y','z') else coords[a])});count+=1
    small=('a','b')
    for event,tup,label in product(small,small,(0,1)):
        norm=norm_factory(cuts,());target=(event,tup,Q(label),'context')
        mm={'eiz5':lambda *xs,target=target:norm(xs)==target}
        assert run('eiz6',[event,c(Q(label)),'context'],mm,small);count+=1
        assert not run('eiz6',[event,c(Q(1-label)),'context'],mm,small);count+=1
        assert not run('eiz6',['a' if event=='b' else 'b',c(Q(label)),'context'],mm,small);count+=1
        assert not run('eiz6',[event,c(Q(label)),'other'],mm,small);count+=1
        assert not run('eiz6',[event,c(Q(label)),'context'],{'eiz5':lambda *xs:False},small);count+=1
    return dict(cases=count,same_event_K_tuple_and_x_minus_vt_required=True,negative_zero_and_nonzero_labels_allowed_without_origin_choice=True,existential_all_slots_distinguished_on_two_individuals=True)

@lru_cache(None)
def local_checks():
    cuts,m=exact_numbers();c=cuts.make;norm=norm_factory(cuts,())
    rows={'zc4':{('reflection',)},'zcz':{('reflection','moving','context')},'eiyg':{('reflection','secondclock','mirror','moving',Q(4),'context')},'eiyi':{('reflection','mirror','moving','context')},'eiyj':{('reflection','moving','context')}}
    m|={n:lambda *xs,rs=rs:norm(xs) in rs for n,rs in rows.items()}
    def stamp(e,f,u,ctx):
        if (e,f,u,ctx)!=('reflection','moving','unit','context'):forbidden()
        return c(Q(4))
    m['zbe']=stamp;args=['reflection','secondclock','mirror',c(Q(4)),'context'];check=lambda mm:run('eiz7',args,mm)
    count=perturb(check,m,rows,norm);unknowns(check,m,('zbe','sca'))
    assert not run('eiz7',args[:3]+[c(Q(3)),'context'],m);count+=1
    assert not check(m|{'zbe':lambda *xs:c(Q(3))});count+=1
    return dict(cases=count,same_local_display_unique_time_and_frame_moment_required=True,stationary_time_cannot_replace_tau=True)

def trial_model():
    cuts,m=exact_numbers();c=cuts.make;norm=norm_factory(cuts,());events=('depart','reflection','arrival');readings=(Q(2),Q(4),Q(6))
    locations={('firstclock','origin','moving'),('secondclock','mirror','moving'),('depart','origin','moving'),('reflection','mirror','moving'),('arrival','origin','moving')}
    legs={('ray','depart','reflection','moving'),('ray','reflection','arrival','moving')}
    rows={'qb':{('firstclock','secondclock','moving','unit','context','trial')},'zbv':{('moving','origin','context')},'zbw':{('moving','axis','x','context')},'zbz':{('moving',cl,'context') for cl in ('firstclock','secondclock')},'zcu':{(p,'moving','context') for p in ('origin','mirror')},'ca':{('firstclock',),('secondclock',)},'cd':{('firstclock','secondclock')},'cc':{(cl,'moving') for cl in ('firstclock','secondclock')},'cb':locations,'ci':{('unit',)},'cf':{('ray',)},'cg':legs,'ch':{('ray','reflection','moving')},'ce':{(cl,e,'moving','unit',val) for e,cl,val in zip(events,('firstclock','secondclock','firstclock'),readings)},'qo':{('firstclock','secondclock','moving','unit','context')},'zdw':{(ray,a,b,'axis',f,'context') for ray,a,b,f in legs},'eiz7':{(e,cl,p,val,'context') for e,cl,p,val in zip(events,('firstclock','secondclock','firstclock'),('origin','mirror','origin'),readings)}}
    m|={n:lambda *xs,rs=rs:norm(xs) in rs for n,rs in rows.items()}
    values={'qc':'origin','qd':'mirror','qe':'depart','qf':'reflection','qg':'arrival','qh':'ray','qi':c(Q(2)),'qj':c(Q(4)),'qk':c(Q(6))}
    def getter(name):
        def get(trial):
            if trial!='trial':forbidden()
            return values[name]
        return get
    m|={n:getter(n) for n in values}
    def origin(f,ctx):
        if (f,ctx)!=('moving','context'):forbidden()
        return 'origin'
    def axis(f,a,ctx):
        if (f,a,ctx)!=('moving','x','context'):forbidden()
        return 'axis'
    m|={'zbn':origin,'zbo':axis}
    return cuts,m,rows,norm

@lru_cache(None)
def trip_checks():
    cuts,m,rows,norm=trial_model();c=cuts.make;args=['trial','firstclock','secondclock','context'];check=lambda mm:run('ei2a',args,mm)
    count=perturb(check,m,rows,norm)
    unknowns(check,m,('qc','qd','qe','qf','qg','qh','qi','qj','qk','zbn','zbo','bg'))
    for patch in ({'qg':lambda tr:'depart'},{'qd':lambda tr:'origin'},{'zbn':lambda *xs:'mirror'},{'qk':lambda tr:c(Q(1))},{'qj':lambda tr:c(Q(2))}):assert not check(m|patch);count+=1
    assert check(m|{'sgp':forbidden,'shc':forbidden,'siw':forbidden});count+=1
    return dict(cases=count,native_da_sde_same_ray_three_events_and_A_B_A_clock_roles=True,both_complete_axial_paths_required=True,selected_trial_sync_scope_and_strict_reading_order_preserved=True,legacy_local_time_and_origin_zero_rules_not_used=True)

@lru_cache(None)
def connection_checks():
    cuts,m=exact_numbers();c=cuts.make;norm=norm_factory(cuts,())
    rows={'eixt':{('context',)},'eiyf':{('moving','context')},'ei2a':{('trial','firstclock','secondclock','context')},'eizm':{('origin','context'),('mirror','context')},'eiz6':{('reflection',Q(-2),'context')}}
    m|={n:lambda *xs,rs=rs:norm(xs) in rs for n,rs in rows.items()}
    def selected(value):
        return lambda tr:value if tr=='trial' else forbidden()
    m|={'eiy3':lambda:Content(POINTS,(True,True,True)),'qc':selected('origin'),'qd':selected('mirror'),'qf':selected('reflection'),'zdt':lambda:c(Q(-2))}
    check=lambda mm:run('ei2b',[],mm);count=perturb(check,m,rows,norm)
    assert not check(m|{'eiy3':lambda:Content(POINTS,(False,True,True))});count+=1
    unknowns(check,m,('eiy3','qc','qd','qf','zdt'))
    for truth in (False,True):assert run('ei2c',[],{'ei2b':lambda truth=truth:truth})==truth;count+=1
    return dict(cases=count,current_geometry_all_clocks_and_same_event_coordinate_graph_required=True,both_endpoints_own_rest_and_same_K_translation_required=True,assumed_content_and_setup_agree=True)

@lru_cache(None)
def midpoint_checks():
    cuts,m=exact_numbers();c=cuts.make;r=cuts.read;count=0;out={}
    for name,vals,want in [('ordinary',(2,4,6),True),('shifted',(-4,-2,0),True),('fractional',(Q(1,3),Q(2,3),1),True),('wrong_middle',(2,3,6),False),('wrong_return',(2,4,7),False),('reversed',(6,4,2),True),('coincident',(4,4,4),True)]:
        args=[c(Q(v)) for v in vals];assert run('sit',args,m)==want;assert run('sis',args,m)==want;count+=2
        mm=m|{n:lambda tr,val=Q(val):c(val) if tr=='trial' else forbidden() for n,val in zip(('qi','qj','qk'),vals)}
        assert run('ei2d',[],mm)==want;count+=1;out[name]=want
    args=[c(Q(v)) for v in (2,4,6)];assert not run('sit',args,m|{'ba':lambda x:r(x)!=4});count+=1
    unknowns(lambda mm:run('sit',args,mm),m,('ba','sca','bd','bj'))
    # Both occurrences of the reflection value in the doubled form remain the
    # same value. The displayed form has a literal 1/2, not an inferred order.
    assert not run('sit',args,m|{'bj':lambda scale,val:c(r(val))});count+=1
    return dict(cases=count,outcomes=out,native_displayed_half_sum_and_doubled_middle_agree_on_exact_rationals=True,formula_reuses_selected_trial_readings=True,midpoint_alone_does_not_imply_chronology=True)

@lru_cache(None)
def synchrony_checks():
    small=('a','b');out={};count=0
    for name in ('baseline','selected_fails','other_fails','selected_outside','incomplete_scope','empty_scope','invalid_other'):
        cuts,m=exact_numbers();c=cuts.make;r=cuts.read
        reads={'a':(0,3 if name in ('selected_fails','selected_outside') else 2,4),'b':(7,10 if name=='other_fails' else 99 if name=='invalid_other' else 9,11)}
        selected=set() if name=='empty_scope' else {'b'} if name=='selected_outside' else set(small)
        m|={'qa':lambda cl,f,ctx:cl in small and (f,ctx)==('a','context'),'ca':lambda cl:cl in small,'cc':lambda cl,f:cl in small and f=='a','cb':lambda cl,p,f:cl==p and f=='a','ci':lambda u:u=='b','ql':lambda a,b,f,u,ctx:name!='incomplete_scope' and (a,b,f,u,ctx)==('a','b','a','b','context'),'qb':lambda a,b,f,u,ctx,tr:(a,b,f,u,ctx)==('a','b','a','b','context') and tr in selected,'da':lambda *xs:True,'bi':lambda a,b,last:r(b)-r(a)==r(last)-r(b),'ba':lambda x:r(x)!=99}
        m|={n:lambda tr:tr for n in ('qc','qd','qe','qf','qg','qh')}
        m|={n:lambda tr,i=i:c(Q(reads[tr][i])) for i,n in enumerate(('qi','qj','qk'))}
        actual=run('qo',['a','b','a','b','context'],m,small);equation=run('sit',[c(Q(x)) for x in reads['a']],m,small)
        assert actual==(name in ('baseline','selected_outside'));assert equation==(name not in ('selected_fails','selected_outside'));count+=2
        out[name]=dict(all_trials_synchronized=actual,selected_trial_in_scope='a' in selected,selected_equation=equation)
    return dict(cases=count,outcomes=out,native_complete_nonempty_all_trial_quantifier_evaluated=True,a_single_passing_trial_is_not_synchrony=True,trial_membership_needed_to_apply_sync_to_selected_equation=True,physical_protocol_and_real_extensional_equality_boundaries_explicit=True)

@lru_cache(None)
def presentation_checks():
    count=0
    cases=[('ei2e',{'ug':{('setup','author','ei2c','section','discourse')},'zao':{('purpose','setup','section','discourse')}}),('ei2h',{'zc':{('inference','author','ei2c','ei2d','section','discourse')},'ue':{('setup','inference','discourse')}})]
    for name,rows in cases:
        m={n:relation(rs) for n,rs in rows.items()};count+=perturb(lambda mm:run(name,[],mm),m,rows)
        assert run(name,[],m|{n:forbidden for n in ('ei2b','ei2c','ei2d','sit')});count+=1
    for name,node,message,previous in (('ei2g','setup','ei2f','purpose'),('ei2j','inference','ei2i','setup')):
        rows={'eir3':{(node,'author','paper',message,'discourse')},'ue':{(previous,node,'discourse')}};m={n:relation(rs) for n,rs in rows.items()};count+=perturb(lambda mm:run(name,[],mm),m,rows)
    return dict(cases=count,hypothetical_setup_and_conditional_necessity_not_actual_experiment=True,same_premise_conclusion_author_scope_and_order=True,quoted_physical_content_not_executed=True)

@lru_cache(None)
def source_record():
    inv=json.loads(read(INVENTORY));units=inv['units'][48:50]
    assert [(u['id'],len(u['text'])) for u in units]==[('einstein-1905:u0049',245),('einstein-1905:u0050',7)]
    assert [u['text_sha256'] for u in units]==['1138727944105c1b0671ae116c45b78bb597cbf9c6899f358b925cacab781b96','ba635f46d0bbf84bfb67385be8910cd65f1d33686d93b744ef84b95e2d28d538']
    forms=('k','τ0','X','x′','τ1','τ2','12(τ0+τ2)=τ1');bindings=('zbm','qi/zdq/eiz7','zbo/zbm/yn/zdw/eixt','zdt/eiz6/sin','qj/zdq/eiz7','qk/zdq/eiz7','sit/ei2d');entries=[]
    ids=units[0]['math_ids']+units[1]['math_ids'];maths={m['id']:m for m in inv['math']}
    for mid,form,binding in zip(ids,forms,bindings,strict=True):
        node=ET.fromstring(maths[mid]['mathml']);assert ''.join(node.itertext())==form
        if mid=='M0098':
            fractions=[n for n in node.iter() if n.tag.split('}')[-1]=='mfrac'];assert len(fractions)==1
            assert [''.join(n.itertext()) for n in fractions[0]]==['1','2']
            assert [''.join(n.itertext()) for n in node.iter() if n.tag.split('}')[-1]=='msub']==['τ0','τ2','τ1']
        entries.append(dict(id=mid,sha256=maths[mid]['sha256'],reading='½(τ₀+τ₂)=τ₁' if mid=='M0098' else form,binding=binding))
    prior='data/einstein-comoving-time-task-source-reading-v1.json';old=json.loads(read(prior));validate_hashes(ROOT,old['source_sha256'])
    paths={INVENTORY,DOC,prior,'artifacts/einstein-frame-coordinates-v1/page-898.jpg','artifacts/einstein-frame-coordinates-v1/page-898.html','artifacts/einstein-frame-coordinates-v1/retrieval.json'}
    segments=[dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[0,len(u['text'])],text=u['text'],source_nonblank_characters=len(re.sub(r'\s|\[M\d+\]','',u['text'])),math=[m for m in entries if m['id'] in u['math_ids']]) for u in units]
    assert [s['source_nonblank_characters'] for s in segments]==[167,0]
    return dict(version='einstein-axial-time-condition-source-reading-v1',reviewer='assistant_visual_and_text_review',pages=['898'],segments=segments,observations=['原刊898頁のVom Anfangspunktからso muß dann seinまでと、直後の半分の和の表示式を照合した。','Xは大文字、目的地はξではなく補助座標x′。時計の三読みはτ₀,τ₁,τ₂である。','帰着は同じKoordinatenursprungであり、反射後のerは同じ光線を指す。','M0098の分子1・分母2と添字の順序0,2,1をMathML木と照合した。文末の必要性がこの式を導く。','この文には原点を零とする数値がない。続くoderからの式の零座標とは判断を分ける。'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert new.document['statements'][:-2]==old.document['statements'] and len(new.document['statements'])==279
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations']
    assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    prior=json.loads(read(PRIOR));validate_hashes(ROOT,prior['source_sha256']);assert selection_binding(new,[274,275,276])==prior['selection']
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    load_annotations(ROOT,BASIS,ANNOTATIONS);assert json.loads(read(ANNOTATIONS))['entries']==json.loads(read('data/comoving-time-task-identifiers-v1.json'))['entries']
    doc=parse(read(CORE));ds={d['name']:d for d in doc['declarations']}
    assert ds['sit']==next(d for d in parse(read(LEGACY))['declarations'] if d['name']=='sit')
    assert all(ds[n]['body']['force']=='assert' for n in ('ei2f','ei2i'))
    for style in ('compact','full'):
        body=format_graph(doc,style);assert parse(body)==parse(transcribe(body,alphabet='v2'))==doc
    assert json.loads(read(SOURCE))==source_record()
    return dict(new_definitions=len(MEANINGS),new_primitives=0,preserved_statements=277,prior_comoving_time_review_preserved=True,old_midpoint_and_protocol_definitions_unchanged=True)

def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/SOURCE,json.dumps(source_record(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    results={n:fn() for n,fn in [('labels',label_checks),('local_readings',local_checks),('trial',trip_checks),('connections',connection_checks),('midpoint',midpoint_checks),('synchrony',synchrony_checks),('presentation',presentation_checks),('structure',structure_checks)]}
    source=source_record();paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(source['source_sha256'])|{SOURCE,DOC,PRIOR,LEGACY,*DEPENDENCIES,'scripts/compose_axial_time_condition.py','scripts/check_axial_time_condition.py','tests/test_axial_time_condition.py','scripts/check_coordinate_correspondence.py','scripts/check_moving_trip_geometry.py','scripts/check_material_relative_frame.py','scripts/check_clock_site_time.py','scripts/check_rod_methods.py','scripts/compose_limits.py','scripts/compose_relativity_conjecture.py','scripts/compose_material_relative_frame.py','scripts/compose_two_postulates.py'}
    alignment=[dict(unit=s['unit'],unit_sha256=s['unit_sha256'],range=s['range'],source=s['text'],statements=[INDEX,INDEX+1] if i==0 else [INDEX+1],definitions=list(MEANINGS),status='explicit_interpretive_annotation') for i,s in enumerate(source['segments'])]
    return dict(status='axial_trial_current_tau_readings_and_midpoint_connected',document=FULL,**results,alignment=dict(segments=alignment),verified_full_units={'kant-1784':0,'einstein-1905':0},general_physical_derivation_proved=False,concrete_tau_transformation_derived=False,semantic_equivalence_automatically_proved=False,remaining=['u0049–u0050全体の通読判断登録','u0051以降と二作品全体の目標'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
