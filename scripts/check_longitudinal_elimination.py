"""Check K-time relative tracks, native elimination and the quoted calculation."""
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
from scripts.check_origin_light_ray import model as base_model,RS,CONSTANTS as BASE_CONSTANTS,DOMAIN as BASE_DOMAIN
from scripts.compose_longitudinal_elimination import ROOT,read,PARENT_BASIS,FULL,CORE,BASIS,ANNOTATIONS,INDEX,MEANINGS,GROUPS,build

DOC='docs/longitudinal-elimination-v1.md';SOURCE='data/einstein-longitudinal-elimination-source-reading-v1.json'
INVENTORY='artifacts/written-units-v1/einstein-1905.json';PRIOR='data/einstein-spatial-method-u0068-review-v1.json'
DEPENDENCIES=('reports/spatial-method-claim-v1.json','reports/origin-light-ray-v1.json','reports/frame-motion-v1.json','reports/comoving-time-task-v1.json','reports/longitudinal-light-v1.json')
CONSTANTS=BASE_CONSTANTS|{'rd':'author','eirf':'paper','eisms':'section','ri':'discourse','zb6':'context','zez':'s','zey':'t','ze2':'principles','ze4':'previous','ze5':'timeclaim','ze6':'elimination'}
DOMAIN=tuple(dict.fromkeys((*BASE_DOMAIN,*CONSTANTS.values(),'originpoint','other')))
POINTS=('context','discourse','other')

@lru_cache(None)
def core_document():return parse(read(CORE))

@lru_cache(None)
def fixture(name,mode='boundary'):
    doc=extract_document(core_document(),roots=[name],statement_indices=[]).document
    boundaries=NUM|{'sje'}
    if name in ('ei5y','ei5z'):boundaries|={'ei5a','eivx','eizm','ei5x','se'}
    if name=='ei55':boundaries.add('ei5y')
    if name=='ei6b':boundaries.add('ei45')
    abstract(doc,boundaries);doc=extract_document(doc,roots=[name],statement_indices=[]).document
    d=next(d for d in doc['declarations'] if d['name']==name)
    if name=='ei5x' and mode=='instance':assert len(expose(d,{'forall'}))==2
    slots=[];args=[]
    for i,p in enumerate(d['parameters']):
        n='jlel'+number_word(i);slots.append(n);doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']));args.append(dict(kind='call',symbol=n,arguments=[]))
    expr=dict(kind='call',symbol=name,arguments=args)
    if d['result']=='content':
        doc['declarations'].append(dict(kind='primitive',name='jlelpoint',parameters=[],result='situation'));expr=dict(kind='evaluate',content=expr,situation=dict(kind='call',symbol='jlelpoint',arguments=[]))
    doc['statements']=[dict(kind='ask',body=expr)];return doc,slots

def run(name,args,m,mode='boundary'):
    doc,slots=fixture(name,mode);assert len(args)==len(slots),(name,len(args),len(slots))
    mm={n:lambda x=x:x for n,x in CONSTANTS.items()}|m|{n:lambda x=x:x for n,x in zip(slots,args)};mm.setdefault('jlelpoint',lambda:'discourse')
    return evaluate_document(doc,individuals=DOMAIN,situations=POINTS,primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=350000,memoize_definitions=True,memoize_expressions=True)[0]['value']

def model():
    cuts,m,rows,norm,records,coords=base_model();c=cuts.make;r=cuts.read
    linear=lambda speed:FunctionValue((RS,),RS,lambda time:c(Q(speed)*r(time)))
    tracks={'x':linear(3),'y':linear(0),'z':linear(0)}
    m|={'zbn':lambda frame,ctx:'originpoint' if (frame,ctx)==('moving','context') else 'other','eismh':lambda obj,frame,lu,tu,axis,ctx:tracks[axis] if (obj,frame,lu,tu,ctx)==('originpoint','frame','lengthunit','timeunit','context') and axis in tracks else forbidden(),'eisls':lambda frame,tu,ctx:c(Q(-1)),'eislt':lambda frame,tu,ctx:c(Q(8))}
    additions={'ei5a':{('s','t','context')},'eivx':{('context',)},'zbv':{('moving','originpoint','context')},'eizm':{('originpoint','context')},'ei5y':{('s','t','context')},'ei5x':{norm((c(Q(0)),c(Q(4)),c(Q(2)),linear(5),linear(3)))},'se':{norm(('originpoint','frame','context','lengthunit','timeunit',c(Q(0)),c(Q(4)),linear(3),linear(0),linear(0)))},'zzbv':{('originpoint','start','context')}}
    for n,rs in additions.items():rows.setdefault(n,set()).update(rs)
    m|={n:lambda *xs,rs=rs:norm(xs) in rs for n,rs in rows.items()}
    return cuts,m,rows,norm,records,coords,tracks,additions

@lru_cache(None)
def relative_checks():
    cuts,m,rows,norm,records,coords,tracks,added=model();c=cuts.make;r=cuts.read;count=0
    make=lambda a,b:FunctionValue((RS,),RS,lambda t:c(Q(a)*r(t)+Q(b)))
    target=make(5,7);reference=make(3,-2)
    for first,second in ((0,1),(1,4),(4,1),(2,2),(-1,3)):
        args=[c(Q(first)),c(Q(second)),c(Q(2)),target,reference]
        assert run('ei5w',args,m);count+=1
        for speed in (3,5,-2):
            bad=args.copy();bad[2]=c(Q(speed));assert run('ei5w',bad,m)==(first==second);count+=1
        bad=args.copy();bad[3],bad[4]=reference,target
        assert run('ei5w',bad,m)==(first==second);count+=1
    # Matching endpoints alone cannot make the intervening relative motion constant.
    curved=FunctionValue((RS,),RS,lambda t:c(5*r(t)+7+r(t)*(4-r(t))))
    assert run('ei5w',[c(Q(0)),c(Q(4)),c(Q(2)),curved,reference],m)
    assert not run('ei5w',[c(Q(0)),c(Q(1)),c(Q(2)),curved,reference],m);count+=2
    args=[c(Q(0)),c(Q(4)),c(Q(2)),target,reference]
    for a,b in ((0,4),(1,3),(4,1),(0,0),(-1,3),(1,5)):
        assert run('ei5x',args+[c(Q(a)),c(Q(b))],m,'instance');count+=1
    assert not run('ei5x',args[:3]+[curved,reference,c(Q(0)),c(Q(1))],m,'instance');count+=1
    bad=args.copy();bad[1]=c(Q(0));assert not run('ei5x',bad+[c(Q(0)),c(Q(0))],m,'instance');count+=1
    unknowns(lambda mm:run('ei5w',[c(Q(0)),c(Q(1)),c(Q(2)),target,reference],mm),m,('ba','bf','sca','shv'))
    try:run('ei5x',args,m)
    except ValueError as e:assert 'Cannot finitely quantify' in str(e),str(e)
    else:raise AssertionError('All real time pairs replaced by samples')
    return dict(cases=count,native_relative_difference_uses_same_two_K_times=True,curved_same_endpoints_rejected_at_interior_pair=True,full_real_time_pair_quantification_refused=True)

@lru_cache(None)
def origin_join_checks():
    cuts,m,rows,norm,records,coords,tracks,added=model();c=cuts.make;r=cuts.read
    selected={n:added[n] for n in ('ei5a','eivx','zbv','eizm','ei5x','se','zzbv')}
    selected['zzbu']={('start','frame','context','lengthunit','timeunit',Q(0),Q(0),Q(0),Q(0))}
    count=perturb(lambda mm:run('ei5y',['s','t','context'],mm),m,selected,norm)
    for axis in ('x','y','z'):
        old=tracks[axis]
        for delta in (1,-1):
            tracks[axis]=FunctionValue((RS,),RS,lambda t,old=old,delta=delta:c(r(old(t))+delta))
            assert not run('ei5y',['s','t','context'],m);count+=1
        tracks[axis]=old
    for n,val in (('zbn','other'),):
        # Supply the other object's own, equally shaped trajectory so the
        # rejection tests origin identity, not an absent trajectory input.
        other_tracks=lambda obj,*xs:m['eismh']('originpoint' if obj=='other' else obj,*xs)
        assert not run('ei5y',['s','t','context'],m|{n:lambda *xs,val=val:val,'eismh':other_tracks});count+=1
    for n,val in (('eisls',1),('eislt',3)):
        assert not run('ei5y',['s','t','context'],m|{n:lambda *xs,val=val:c(Q(val))});count+=1
    # The origin and the ray share the emission event, not the later ray event.
    assert not run('ei5y',['s','t','context'],m|{'zzbv':lambda obj,event,ctx:(obj,event,ctx)==('originpoint','end','context')});count+=1
    coords['lasttuple'][3]=Q(5);assert not run('ei5y',['s','t','context'],m);coords['lasttuple'][3]=Q(4);count+=1
    unknowns(lambda mm:run('ei5y',['s','t','context'],mm),m,('eismh','zbn','eisls','eislt','tc','zb7','zdz','zc6','se','ei5x'))
    assert run('ei5z',[],m);count+=1
    for segment,expected in (('s',True),('t',True),('other',False)):
        assert run('ei6b',[segment],m)==expected;count+=1
    return dict(cases=count,same_origin_full_motion_emission_and_K_interval_required=True,current_origin_position_vt_and_auxiliary_ray_coordinate_bound=True,moving_clock_time_not_used_for_relative_speed=True)

@lru_cache(None)
def elimination_checks():
    cuts,m,rows,norm,records,coords,tracks,added=model();c=cuts.make;count=0
    for name in ('sni','snh','snj'):assert run(name,['end','context'],m);count+=1
    assert run('ei55',[],m);count+=1
    for tup,slot,expected in (('lasttuple',0,(False,False,False)),('lasttuple',3,(False,False,False)),('movinglasttuple',0,(True,False,False)),('movinglasttuple',3,(True,True,True))):
        coords[tup][slot]+=1
        got=tuple(run(n,['end','context'],m) for n in ('sni','snh','snj'));assert got==expected,(tup,slot,got);count+=3
        assert run('ei55',[],m)==(tup=='movinglasttuple' and slot==3);count+=1
        coords[tup][slot]-=1
    for scale in (Q(0),Q(1),Q(3,2),Q(3)):
        coords['movinglasttuple'][0]=Q(25)*scale/2
        changed=m|{'zeq':lambda scale=scale:FunctionValue((RS,),RS,lambda speed:c(scale))}
        for n in ('sni','snh','snj'):assert run(n,['end','context'],changed);count+=1
    coords['movinglasttuple'][0]=Q(25)
    assert not run('sni',['end','context'],m|{'tc':lambda:c(Q(2))});count+=1
    assert not run('ei55',[],m|{'ei5y':lambda *xs:False});count+=1
    unknowns(lambda mm:run('snj',['end','context'],mm),m,('zeq','tc','zb7','zdz','zc6','sje'))
    report=json.loads(read('reports/longitudinal-light-v1.json'));validate_hashes(ROOT,report['source_sha256'])
    return dict(cases=count,native_sni_snh_snj_and_same_event_elimination_checked=True,K_t_not_k_tau_and_xprime_not_xi=True,free_phi_coefficient_not_fixed_to_one=True,existing_rational_algebra_evidence_preserved=True)

@lru_cache(None)
def presentation_checks():
    rows=[('ei52',{'eisnp':{('timeclaim','author','principles','ei5e','timeclaim','ei5z','ei6b','discourse')},'uh':{('timeclaim','author','ei5z','section','discourse')},'zc':{('timeclaim','author','ei5z','snt','section','discourse')}}),('ei56',{'zd3':{('elimination','author','ei55','sns','snu','section','discourse')}})]
    for body,message,author,node,previous in GROUPS:rows.append((author,{'eir3':{(CONSTANTS[node],'author','paper',message,'discourse')},'ue':{(CONSTANTS[previous],CONSTANTS[node],'discourse')}}))
    count=0
    for name,relations in rows:
        m={n:relation(rs) for n,rs in relations.items()};count+=perturb(lambda mm:run(name,[],mm),m,relations)
        assert run(name,[],m|{n:forbidden for n in ('ei5e','ei5z','ei6b','ei55','snt','sns','snu')});count+=1
    return dict(cases=count,contrast_preserves_common_ray_and_different_measurement_perspectives=True,relative_motion_claim_consequence_and_substitution_are_distinct=True,same_author_section_paper_source_order_preserved=True,quoted_contents_not_executed=True)

@lru_cache(None)
def source_record():
    inv=json.loads(read(INVENTORY));math={m['id']:m for m in inv['math']};segments=[]
    readings=dict(zip((f'M{n:04d}' for n in range(124,130)),('k','V−v','x′/(V−v)=t','t','ξ','ξ=a*V²*x′/(V²−v²)')))
    for n,flat in zip(readings,('k','V−v','x′V−v=t.','t','ξ','ξ=aV2V2−v2x′.')):assert ''.join(ET.fromstring(math[n]['mathml']).itertext())==flat
    for i,u in enumerate(inv['units'][68:72]):
        assert u['id']==f'einstein-1905:u{69+i:04d}'
        segments.append(dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[0,len(u['text'])],text=u['text'],source_nonblank_characters=len(re.sub(r'\s|\[M\d+\]','',u['text'])),math=[dict(id=n,sha256=math[n]['sha256'],reading=readings[n],mathml_flat=''.join(ET.fromstring(math[n]['mathml']).itertext())) for n in u['math_ids']]))
    prior='data/einstein-spatial-method-source-reading-v1.json';validate_hashes(ROOT,json.loads(read(prior))['source_sha256'])
    retrieved=json.loads(read('artifacts/einstein-longitudinal-elimination-v1/retrieval.json'))
    validate_hashes(ROOT,{r['path']:r['sha256'] for r in retrieved['sources']})
    paths={INVENTORY,DOC,prior,'artifacts/einstein-differential-step-v1/page-899.jpg','artifacts/einstein-differential-step-v1/page-899.html','artifacts/einstein-longitudinal-elimination-v1/retrieval.json',*(r['path'] for r in retrieved['sources'])}
    return dict(version='einstein-longitudinal-elimination-source-reading-v1',reviewer='assistant_visual_and_text_review',pages=['899','900'],segments=segments,observations=['899頁末のNun bewegt sich aber der Lichtstrahl relativ zum Anfangs-から900頁冒頭punkt von kまでを接続して読んだ。','V−vは静止系で測った光とk原点の相対速度である。次の式はx′/(V−v)=t。','同じtの値を先のξの式に入れ、ξ=a*V²*x′/(V²−v²)を得る。二つの分数の分母、Vの二乗、x′を原刊で確認した。','u0070/u0072の句点は固定MathMLに含まれるため、数式以外の本文文字には加算しない。','Nun ... aberは同じ光を測る観点の対照、Setzen wir ... einは同じ値の計算上の代入という明示的な読みとする。横方向の類推は次の単位に残す。'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert new.document['statements'][:-2]==old.document['statements'] and len(new.document['statements'])==295
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations']
    assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    prior=json.loads(read(PRIOR));validate_hashes(ROOT,prior['source_sha256']);assert selection_binding(new,[291,292])==prior['selection']
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    load_annotations(ROOT,BASIS,ANNOTATIONS)
    doc=core_document();ds={d['name']:d for d in doc['declarations']}
    assert all(ds[m]['body']['force']=='assert' for _,m,_,_,_ in GROUPS)
    for n in ('ei5y','ei5z','ei55'):
        extracted=extract_document(doc,roots=[n],statement_indices=[])
        assert not set(extracted.retained_symbols)&{'snq','snk','snc','snv','shd','smk','sfm','sbc'},n
    for style in ('compact','full'):
        body=format_graph(doc,style);assert parse(body)==parse(transcribe(body,alphabet='v2'))==doc
    assert json.loads(read(SOURCE))==source_record()
    return dict(new_definitions=len(MEANINGS),new_primitives=1,preserved_statements=INDEX,prior_whole_unit_judgment_preserved=True,obsolete_ray_and_coordinate_dependencies_not_reintroduced=True)

def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/SOURCE,json.dumps(source_record(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    results={n:f() for n,f in [('relative',relative_checks),('origin',origin_join_checks),('elimination',elimination_checks),('presentation',presentation_checks),('structure',structure_checks)]}
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(source_record()['source_sha256'])|{SOURCE,DOC,PRIOR,*DEPENDENCIES,'scripts/compose_longitudinal_elimination.py','scripts/check_longitudinal_elimination.py','tests/test_longitudinal_elimination.py','scripts/check_coordinate_correspondence.py','scripts/check_moving_trip_geometry.py','scripts/check_clock_site_time.py','scripts/check_origin_light_ray.py','scripts/check_translated_light_trial.py','scripts/check_frame_light_law.py','scripts/compose_material_axes.py','scripts/compose_moving_trip_geometry.py','scripts/compose_public_first_sentence.py','scripts/compose_limits.py','scripts/compose_material_relative_frame.py','scripts/compose_relativity_conjecture.py','scripts/compose_two_postulates.py'}
    alignment=dict(segments=[dict(unit=s['unit'],unit_sha256=s['unit_sha256'],range=s['range'],source=s['text'],statements=[INDEX] if i<2 else [INDEX,INDEX+1],definitions=list(MEANINGS),status='explicit_interpretive_annotation') for i,s in enumerate(source_record()['segments'])])
    return dict(status='K_time_relative_light_motion_and_longitudinal_elimination_connected',document=FULL,**results,alignment=alignment,verified_full_units={'kant-1784':0,'einstein-1905':0},general_real_physical_derivation_proved=False,semantic_equivalence_automatically_proved=False,remaining=['u0069–u0072の全文通読判断登録','u0073以降と二作品全体の目標'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
