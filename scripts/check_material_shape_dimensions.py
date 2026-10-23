"""Check arbitrary occupancy, native shape substitution and actual body widths."""
from functools import lru_cache
from fractions import Fraction as Q
from itertools import product
import json
from noema.grammar import parse,format_graph,number_word
from noema.extraction import extract_document
from noema.finite_semantics import FunctionValue,evaluate_document
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.check_coordinate_correspondence import abstract
from scripts.check_moving_trip_geometry import NUM,numbers
from scripts.check_clock_site_time import perturb,unknowns,forbidden
from scripts.check_material_relative_frame import RS,FS
from scripts.check_translated_light_trial import expose
from scripts.check_transverse_segment import model as body_model,DOMAIN,refused,relations
from scripts.compose_material_shape_dimensions import ROOT,read,PARENT_BASIS,FULL,CORE,BASIS,ANNOTATIONS,MEANINGS,build

DOC='docs/material-shape-dimensions-v1.md'
PRIOR='data/einstein-moving-ellipsoid-u0114-review-v1.json'
DEPENDENCIES=('reports/moving-ellipsoid-v1.json','reports/solid-sphere-geometry-v1.json','reports/shape-contraction-v1.json')
CONSTANTS={'ra':'K','zbm':'k','ta':'length','rb':'duration','yn':'x','yo':'y','yp':'z','zb6':'context'}
SS={'kind':'function','parameters':[RS,RS,RS],'result':'truth'}
GRID=tuple(product((Q(-2),Q(-8,5),Q(0),Q(1),Q(7,5),Q(12,5),Q(3),Q(4),Q(22,5),Q(27,5),Q(6),Q(7),Q(42,5)),(Q(0),Q(1),Q(2)),(Q(0),Q(1))))

@lru_cache(None)
def fixture(name,mode='boundary'):
    doc=extract_document(parse(read(CORE)),roots=[name],statement_indices=[]).document
    bounds=NUM|{'soy','srd'}|{'ejgi':{'eigy','eiah','ejgh'},'ejgj':{'ejgi','eje7','eipf','eioj'},'ejgl':{'suk'},'ejgm':{'ejgh'},'ejgn':{'ejgl','stw'},'ejgo':{'ejgj','ejgm','ejgn'}}.get(name,set())
    abstract(doc,bounds);doc=extract_document(doc,roots=[name],statement_indices=[]).document
    d=next(d for d in doc['declarations'] if d['name']==name)
    if mode=='instance':
        sort=SS if name=='ejgo' else RS
        assert len(expose(d,{'forall'},only_sort=sort))=={'ejgh':3,'ejgi':1,'ejgm':1,'ejgn':7,'ejgo':1}[name]
    slots=[];args=[]
    def slot(sort):
        n='jmsd'+number_word(len(slots));slots.append(n);doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=sort));return dict(kind='call',symbol=n,arguments=[])
    for p in d['parameters']:args.append(slot(p['sort']))
    expr=dict(kind='call',symbol=name,arguments=args)
    if isinstance(d['result'],dict):expr=dict(kind='apply',function=expr,arguments=[slot(RS) for _ in range(3)])
    if d['result']=='content':
        doc['declarations'].append(dict(kind='primitive',name='jmsdpoint',parameters=[],result='situation'));expr=dict(kind='evaluate',content=expr,situation=dict(kind='call',symbol='jmsdpoint',arguments=[]))
    doc['statements']=[dict(kind='ask',body=expr)];return doc,slots

def run(name,args,m,mode='boundary',domain=DOMAIN):
    doc,slots=fixture(name,mode);assert len(args)==len(slots),(name,len(args),len(slots))
    mm={n:lambda x=x:x for n,x in CONSTANTS.items()}|{'jmsdpoint':lambda:'context'}|m|{n:lambda x=x:x for n,x in zip(slots,args)}
    return evaluate_document(doc,individuals=domain,situations=('context','other'),primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=500000,memoize_definitions=True,memoize_expressions=True)[0]['value']

def setup():
    cuts,m,pos,members,fs,pop,fields,base_norm=body_model();c=cuts.make;r=cuts.read
    members.clear();members.update(('p','q'));pos['p']=[Q(-2),Q(1),Q(0)];pos['q']=[Q(3),Q(2),Q(1)]
    support={tuple(pos[p]) for p in members}
    shape=FunctionValue((RS,RS,RS),'truth',lambda *xs:tuple(r(x) for x in xs) in support)
    def norm(xs):
        return tuple(tuple(x(*(c(n) for n in p)) for p in GRID) if isinstance(x,FunctionValue) and x.parameters==(RS,RS,RS) else base_norm([x])[0] for x in xs)
    return cuts,m,pos,members,fs,pop,fields,shape,norm,support

@lru_cache(None)
def occupation_checks():
    cuts,m,pos,members,fs,pop,fields,shape,norm,support=setup();c=cuts.make;r=cuts.read;count=0;snap=[pop,*fs,c(Q(1))]
    for p in GRID:
        assert run('ejgg',snap+[c(n) for n in p],m,domain=('p','q'))==(p in support);count+=1
        assert run('ejgh',snap+[shape]+[c(n) for n in p],m,'instance',('p','q'));count+=1
    # Filling the gap changes the shape; missing an occupied witness is rejected.
    support.add((Q(0),Q(1),Q(0)))
    assert not run('ejgh',snap+[shape,c(Q(0)),c(Q(1)),c(Q(0))],m,'instance',('p','q'));count+=1
    support.remove((Q(0),Q(1),Q(0)))
    members.remove('q');assert not run('ejgh',snap+[shape,c(Q(3)),c(Q(2)),c(Q(1))],m,'instance',('p','q'));count+=1;members.add('q')
    pos['q'][1]=Q(0);assert not run('ejgh',snap+[shape,c(Q(-2)),c(Q(1)),c(Q(0))],m,'instance',('p','q'));count+=1;pos['q'][1]=Q(2)
    # A hollow planar annulus permits its central hole, yet requires every ring position.
    ring=FunctionValue((RS,RS,RS),'truth',lambda x,y,z:r(z)==0 and 1<=r(x)**2+r(y)**2<=4)
    pos['p']=[Q(-1),Q(0),Q(0)];pos['q']=[Q(1),Q(0),Q(0)]
    for xyz,expected in (((0,0,0),True),((0,1,0),False),((1,0,0),True),((3,0,0),True)):
        assert run('ejgh',snap+[ring]+[c(Q(n)) for n in xyz],m,'instance',('p','q'))==expected;count+=1
    refused(lambda:run('ejgh',snap+[ring],m,domain=('p','q')))
    unknowns(lambda mm:run('ejgh',snap+[ring,c(Q(0)),c(Q(0)),c(Q(0))],mm,'instance',('p','q')),m,('ba','sca'))
    return dict(cases=count,disconnected_nonconvex_and_hollow_shapes_retained=True,containment_and_all_position_coverage_checked=True,native_same_point_three_coordinates=True,unbounded_position_quantifiers_refused=True)

@lru_cache(None)
def history_checks():
    cuts,m,pos,members,fs,pop,fields,shape,norm,support=setup();c=cuts.make;count=0
    rows={'eigy':{norm(fields)},'eiah':{norm(fields)},'ejgh':{norm([pop,*fs,c(Q(1)),shape])}}
    mm=relations(m,rows,norm);args=fields+[shape,c(Q(1))];count+=perturb(lambda mm:run('ejgi',args,mm,'instance'),mm,rows,norm)
    for t in (0,2):
        assert not run('ejgi',fields+[shape,c(Q(t))],mm,'instance');count+=1
    bad=fields[:];bad[6]=bad[5];assert not run('ejgi',bad+[shape,c(Q(0))],mm|{'eigy':lambda *xs:True,'eiah':lambda *xs:True,'ejgh':lambda *xs:True},'instance');count+=1
    refused(lambda:run('ejgi',fields+[shape],mm))
    moving=fields[:];moving[1]='K';moving[6]=c(Q(3))
    m|={'eisls':lambda f,u,s:c(Q(0)) if f in ('K','k') and (u,s)==('duration','context') else forbidden(),'eislt':lambda f,u,s:c(Q(3 if f=='K' else 2)) if f in ('K','k') and (u,s)==('duration','context') else forbidden(),'eislu':lambda b,f,lu,tu,a,s:fs[('x','y','z').index(a)] if b=='body' and f in ('K','k') and (lu,tu,s)==('length','duration','context') and a in ('x','y','z') else forbidden(),'zb7':lambda:c(Q(3)),'eislc':lambda f,g,lu,tu,a,s:c(Q(3 if a=='x' else 0)) if (f,g,lu,tu,s)==('K','k','length','duration','context') and a in ('x','y','z') else forbidden()}
    rows={'ejgi':{norm(fields+[shape])},'eje7':{('body',f,'context') for f in ('K','k')},'eipf':{norm(moving+[c(Q(3))])},'eioj':{('K','k','length','duration','context')}}
    mm=relations(m,rows,norm);check=lambda mm:run('ejgj',['body',shape,'context'],mm)
    count+=perturb(check,mm,rows,norm);unknowns(check,mm,('eirh','eislu','eisls','eislt','eislc'))
    assert check(mm|{'eje5':forbidden,'eipc':forbidden,'eipe':forbidden});count+=1
    return dict(cases=count,complete_rest_rigidity_and_two_current_histories=True,all_times_not_one_snapshot=True,no_ball_or_rod_restriction=True)

@lru_cache(None)
def transform_checks():
    cuts,m,pos,members,fs,pop,fields,shape,norm,support=setup();c=cuts.make;r=cuts.read;count=0
    movingfs=[FunctionValue(('individual',),FS,lambda p,i=i:FunctionValue((RS,),RS,lambda t:c((Q(4,5)*pos[p][0]+3*r(t)) if i==0 else pos[p][i]))) for i in range(3)]
    m|={'tc':lambda:c(Q(5)),'zb7':lambda:c(Q(3)),'soy':lambda a,b:c(Q(5,4)) if (r(a),r(b))==(5,3) else forbidden(),'srd':lambda a,b,d:(r(a),r(b),r(d))==(5,3,Q(5,4)),'eisls':lambda f,u,s:c(Q(0)) if (f,u,s)==('K','duration','context') else forbidden(),'eislt':lambda f,u,s:c(Q(2)) if (f,u,s)==('K','duration','context') else forbidden(),'eislu':lambda b,f,lu,tu,a,s:movingfs[('x','y','z').index(a)] if (b,f,lu,tu,s)==('body','K','length','duration','context') and a in ('x','y','z') else forbidden()}
    for t in (0,1,2):
        transformed=FunctionValue((RS,RS,RS),'truth',lambda x,y,z,t=t:((r(x)-3*t)*Q(5,4),r(y),r(z)) in support)
        rows={'ejgh':{norm([pop,*movingfs,c(Q(t)),transformed])}};mm=relations(m,rows,norm)
        count+=perturb(lambda mm:run('ejgm',['body',shape,'context',c(Q(t))],mm,'instance'),mm,rows,norm)
        for xyz in GRID:
            expected=(xyz[0]*Q(5,4)-Q(15,4)*t,xyz[1],xyz[2]) in support
            assert run('ejgk',['body','K','context',c(Q(t)),*[c(n) for n in xyz]],m)==expected;count+=1
        unknowns(lambda mm:run('ejgm',['body',shape,'context',c(Q(t))],mm,'instance'),mm,('eislu','eirh','soy','srd','zb7'))
    refused(lambda:run('ejgm',['body',shape,'context'],mm))
    return dict(cases=count,native_affine_shape_substitution=True,actual_full_material_shape_not_surface_sample=True,different_observer_times_checked=True)

@lru_cache(None)
def width_checks():
    cuts,m,pos,members,fs,pop,fields,shape,norm,support=setup();c=cuts.make;r=cuts.read;count=0
    rows={'suk':{norm([shape,'x',c(Q(5))])}};mm=relations(m,rows,norm);args=['body','k','context',c(Q(1)),'x',c(Q(5))]
    count+=perturb(lambda mm:run('ejgl',args,mm),mm,rows,norm)
    for time in (-1,3):
        bad=args[:];bad[3]=c(Q(time));assert not run('ejgl',bad,mm);count+=1
    unknowns(lambda mm:run('ejgl',args,mm),mm,('eislu','eirh','eisls','eislt'))
    # Bind six actual widths, with unequal transverse sizes to catch axis exchange.
    m|={'tc':lambda:c(Q(5)),'zb7':lambda:c(Q(3)),'stw':lambda a,b:c(Q(4,5)) if (r(a),r(b))==(5,3) else forbidden(),'eisls':lambda f,u,s:c(Q(-1 if f=='k' else 0)) if f in ('k','K') and (u,s)==('duration','context') else forbidden(),'eislt':lambda f,u,s:c(Q(2)) if f in ('k','K') and (u,s)==('duration','context') else forbidden()}
    for t in (0,1,2):
        for widths,expected in (((5,2,1,4,2,1),True),((5,2,1,5,2,1),False),((5,2,1,4,1,2),False),((5,2,1,4,Q(8,5),Q(4,5)),False),((0,2,1,0,2,1),True)):
            rows={'ejgl':{('body',f,'context',Q(when),axis,Q(w)) for f,when,ws in (('k',-1,widths[:3]),('K',t,widths[3:])) for axis,w in zip(('x','y','z'),ws)}}
            mm=relations(m,rows,norm);args=['body','context',c(Q(t)),*[c(Q(w)) for w in widths]]
            assert run('ejgn',args,mm,'instance')==expected;count+=1
            if not expected:
                # Every width/slot is part of the antecedent. Moving it to another
                # body, frame, time, axis or value must make this instance vacuous.
                for row in rows['ejgl']:
                    for i in range(len(row)):
                        bad=tuple('wrong' if j==i else x for j,x in enumerate(row));altered=(rows['ejgl']-{row})|{bad}
                        assert run('ejgn',args,relations(m,{'ejgl':altered},norm),'instance');count+=1
        unknowns(lambda mm:run('ejgn',args,mm,'instance'),mm,('stw','ejgl','eisls','eislt'))
    refused(lambda:run('ejgn',['body','context'],mm))
    return dict(cases=count,native_occupied_shape_passed_to_tight_width=True,same_body_frame_time_and_axis_for_all_six_widths=True,zero_width_allowed=True,missing_finite_width_not_asserted_to_exist=True)

@lru_cache(None)
def scope_checks():
    cuts,m,pos,members,fs,pop,fields,shape,norm,support=setup();count=0
    for bits in product((False,True),repeat=6):
        allowed={p for p,b in zip(('p','q'),bits[:2]) if b};shapes={p for p,b in zip(('p','q'),bits[2:4]) if b};widths={p for p,b in zip(('p','q'),bits[4:]) if b}
        mm={'ejgj':lambda b,s,c:b in allowed and norm([s])==norm([shape]) and c=='context','ejgm':lambda b,s,c:b in shapes and norm([s])==norm([shape]) and c=='context','ejgn':lambda b,c:b in widths and c=='context'}
        expected=all(p not in allowed or p in shapes and p in widths for p in ('p','q'))
        assert run('ejgo',[shape],mm,'instance',('p','q'))==expected;count+=1
    refused(lambda:run('ejgo',[],mm,domain=('p','q')))
    return dict(cases=count,all_bodies_and_all_shape_functions=True,shape_and_width_consequences_both_required=True,native_shape_domain_not_finitely_enumerated=True)

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert new.document['statements']==old.document['statements'] and len(new.document['statements'])==332
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations'];assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    prior=json.loads(read(PRIOR));validate_hashes(ROOT,prior['source_sha256']);assert selection_binding(new,[331])==prior['selection']
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    load_annotations(ROOT,BASIS,ANNOTATIONS);doc=parse(read(CORE));names={d['name'] for d in doc['declarations']}
    assert {'eje2','eje7','eipf','eigy','eiah','stv','sui','suj','suk'}<=names
    assert not names&{'eje5','ejf7','eipc','eipe','sua','sub','sue','shd','zhu','zhw','zhx'}
    for style in ('compact','full'):
        body=format_graph(doc,style);assert parse(body)==parse(transcribe(body,alphabet='v2'))==doc
    return dict(new_definitions=len(MEANINGS),new_primitives=0,preserved_statements=332,prior_whole_unit_judgments_preserved=True)

def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)

@lru_cache(None)
def build_report():
    results={n:f() for n,f in [('occupation',occupation_checks),('history',history_checks),('transform',transform_checks),('width',width_checks),('scope',scope_checks),('structure',structure_checks)]}
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|{DOC,PRIOR,*DEPENDENCIES,'scripts/compose_material_shape_dimensions.py','scripts/check_material_shape_dimensions.py','tests/test_material_shape_dimensions.py','scripts/check_coordinate_correspondence.py','scripts/check_moving_trip_geometry.py','scripts/check_clock_site_time.py','scripts/check_material_relative_frame.py','scripts/check_translated_light_trial.py','scripts/check_transverse_segment.py','scripts/compose_solid_sphere_geometry.py','scripts/compose_shape_contraction.py','scripts/compose_material_body_motion.py','scripts/compose_rod_methods.py','scripts/compose_material_relative_frame.py','scripts/compose_relativity_conjecture.py','scripts/compose_limits.py'}
    return dict(status='arbitrary_occupied_shapes_and_actual_body_widths_connected',document=FULL,**results,verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,remaining=['u0116第一文の対照・帰結・速度比較と著者への本文接続','u0116後半の極限・適用限界・後続への予告と全単位判断'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
