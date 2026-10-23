"""Check signed motion and a shared shape rule under exchanged frames."""
from functools import lru_cache
from fractions import Fraction as Q
from itertools import product
import json,re
from noema.grammar import parse,format_graph,number_word
from noema.extraction import extract_document
from noema.finite_semantics import FunctionValue,Content,evaluate_document
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.check_coordinate_correspondence import abstract
from scripts.check_moving_trip_geometry import NUM,numbers
from scripts.check_clock_site_time import relation,perturb,unknowns,forbidden
from scripts.check_rod_methods import value
from scripts.check_material_relative_frame import RS,FS
from scripts.check_translated_light_trial import expose
from scripts.check_transverse_segment import refused,relations,model as body_model,DOMAIN as BODY_DOMAIN
from scripts.check_material_shape_dimensions import SS
from scripts.check_transverse_time import square_root
from scripts.compose_reciprocal_shape_results import ROOT,read,PARENT_BASIS,FULL,CORE,BASIS,ANNOTATIONS,INDEX,MEANINGS,build

DOC='docs/reciprocal-shape-results-v1.md';SOURCE='data/einstein-reciprocal-shape-results-source-reading-v1.json'
INVENTORY='artifacts/written-units-v1/einstein-1905.json';PRIOR='data/einstein-shape-dimension-u0116-review-v1.json'
DEPENDENCIES=('reports/speed-boundary-forecast-v1.json','reports/planar-shape-limit-v1.json','reports/directional-contraction-claim-v1.json','reports/material-shape-dimensions-v1.json','reports/final-transform-claim-v1.json')
CONSTANTS={'ra':'K','zbm':'k','ta':'length','rb':'duration','yn':'x','yo':'y','yp':'z','zc7':'time','zb6':'context','rd':'author','eirf':'paper','eisn5':'section','zia':'previous','zib':'reciprocal','ri':'discourse'}
DOMAIN=tuple(dict.fromkeys((*BODY_DOMAIN,*CONSTANTS.values(),'a','b')));POINTS=('context','discourse','other')
GRID=tuple(product(sorted({Q(n) for n in (-2,0,3,10)}|{Q(4,5)*x+sign*3*t for x,sign,t in product((-2,3),(-1,1),(0,1,2,10,11,12))}),map(Q,(0,1,2)),map(Q,(0,1))))

@lru_cache(None)
def core():return parse(read(CORE))

@lru_cache(None)
def fixture(name,mode='boundary'):
    doc=extract_document(core(),roots=[name],statement_indices=[]).document
    bounds=NUM|{'sje','sjd','sky','zzbb','zzbd'}|{'ejhx':{'eiad'},'ejii':{'eiyx','sre'},'ejhy':{'ejgi','eje7','ejhx','eioj','ejii'},'ejhz':{'ejhy','ejgl'},'ejh2':{'ejgh'},'ejh3':{'ejgl'},'ejh4':{'ejh2','ejh3'},'ejh7':{'ejg6'},'ejia':{'suo','ejh7'},'ejib':{'ejh6','stv'},'ejic':{'ejh4','ejia','ejib'},'ejid':{'ejhz','ejic'},'ejie':{'ejid','ejgy'}}.get(name,set())
    abstract(doc,bounds);doc=extract_document(doc,roots=[name],statement_indices=[]).document;d=next(d for d in doc['declarations'] if d['name']==name)
    if mode=='instance':assert len(expose(d,{'forall','exists'},only_sort=SS if name=='ejid' else RS))=={'ejhx':2,'ejhz':3,'ejh2':1,'ejh3':3,'ejh6':1,'ejh7':3,'ejia':4,'ejib':4,'ejic':1,'ejid':1}[name]
    slots=[]
    def slot(sort):
        n='jrsr'+number_word(len(slots));slots.append(n);doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=sort));return dict(kind='call',symbol=n,arguments=[])
    expr=dict(kind='call',symbol=name,arguments=[slot(p['sort']) for p in d['parameters']])
    if name=='stv':expr=dict(kind='apply',function=expr,arguments=[slot(RS) for _ in range(3)])
    if d['result']=='content':
        doc['declarations'].append(dict(kind='primitive',name='jrsrpoint',parameters=[],result='situation'));expr=dict(kind='evaluate',content=expr,situation=dict(kind='call',symbol='jrsrpoint',arguments=[]))
    doc['statements']=[dict(kind='ask',body=expr)];return doc,slots

def run(name,args,m,mode='boundary',domain=DOMAIN):
    doc,slots=fixture(name,mode);assert len(args)==len(slots),(name,len(args),len(slots))
    mm={n:lambda x=x:x for n,x in CONSTANTS.items()}|{'jrsrpoint':lambda:'discourse'}|m|{n:lambda x=x:x for n,x in zip(slots,args)}
    return evaluate_document(doc,individuals=domain,situations=POINTS,primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=600000,memoize_definitions=True,memoize_expressions=True)[0]['value']

def model():
    cuts,m,pos,members,fs,pop,fields,base_norm=body_model();c=cuts.make;r=cuts.read
    members.clear();members.update(('p','q'));pos['p']=[Q(-2),Q(1),Q(0)];pos['q']=[Q(3),Q(2),Q(1)]
    support={tuple(pos[p]) for p in members};shape=FunctionValue((RS,RS,RS),'truth',lambda *xs:tuple(r(x) for x in xs) in support)
    m|={'sje':lambda a,b:c(r(a)/r(b)) if r(b) else forbidden(),'sjd':lambda a:c(1/r(a)) if r(a) else forbidden(),'sky':lambda x:square_root(cuts,x),'tc':lambda:c(Q(5)),'zb7':lambda:c(Q(3)),'zzbb':c,'zzbd':lambda a,b:c(r(a)+r(b)),'zzbg':lambda a,b:r(a)<r(b)}
    def norm(xs):
        def one(x):
            if not isinstance(x,FunctionValue):return value(x)
            if x.parameters==(RS,RS,RS):return tuple(x(*(c(n) for n in p)) for p in GRID)
            if x.parameters==(RS,) and x.result==RS:return tuple(r(x(c(Q(t)))) for t in (-1,0,1,2))
            return base_norm([x])[0]
        return tuple(one(x) for x in xs)
    return cuts,m,pos,members,fs,pop,fields,shape,support,norm

@lru_cache(None)
def motion_checks():
    cuts,m,pos,members,fs,pop,fields,shape,support,norm=model();c=cuts.make;r=cuts.read;count=0
    for speed,a,b in product((-3,0,3),(-1,0),(1,2)):
        args=[c(Q(n)) for n in (speed,a,b,7,7+speed*(b-a),2,2,4,4)]
        assert run('ejhw',args,m);count+=1
        for slot in (0,1,2,3,4,5,6,7,8):
            bad=args[:];bad[slot]=c(r(bad[slot])+Q(1,7));expected=slot in (1,2) and speed==0
            assert run('ejhw',bad,m)==expected;count+=1
    for speed in (-3,3):
        moving=[FunctionValue(('individual',),FS,lambda p,i=i:FunctionValue((RS,),RS,lambda t:c(pos[p][i]+(speed*r(t) if i==0 else 0)))) for i in range(3)]
        actual=fields[:];actual[1]='K';actual[-3:]=moving
        rows={'eiad':{norm(actual)},'eisdd':{('K','length','duration','context')}};mm=relations(m,rows,norm)
        check=lambda mm:run('ejhx',actual+[c(Q(speed)),c(Q(0)),c(Q(2))],mm,'instance',BODY_DOMAIN)
        count+=perturb(check,mm,rows,norm)
        # Corrupt only q, keeping p's trajectory and the complete-history boundary.
        for axis in range(3):
            bad=actual[:];bad[-3+axis]=FunctionValue(('individual',),FS,lambda p,axis=axis:FunctionValue((RS,),RS,lambda t:c(pos[p][axis]+(speed*r(t) if axis==0 else 0)+(r(t) if p=='q' else 0))))
            assert not run('ejhx',bad+[c(Q(speed)),c(Q(0)),c(Q(2))],mm|{'eiad':lambda *xs:True},'instance',BODY_DOMAIN);count+=1
        assert not run('ejhx',actual+[c(Q(-speed)),c(Q(0)),c(Q(2))],mm,'instance',BODY_DOMAIN);count+=1
        refused(lambda:run('ejhx',actual+[c(Q(speed))],mm,domain=BODY_DOMAIN))
    return dict(cases=count,signed_displacement_and_complete_material_history=True,all_members_not_just_center_or_endpoints=True)

@lru_cache(None)
def correspondence_checks():
    cuts,m,pos,members,fs,pop,fields,shape,support,norm=model();c=cuts.make;r=cuts.read;count=0
    ones=FunctionValue((RS,),RS,lambda t:c(Q(1)))
    for sign,event,first,second in product((-1,1),('a','b'),('a','b'),('a','b')):
        rows={'eiyx':{(event,first,'a','context'),(event,second,'b','context')},'sre':{norm([first,second,c(Q(5)),c(Q(sign*3)),ones])}}
        mm=relations(m,rows,norm);count+=perturb(lambda mm:run('ejii',['b','a',c(Q(sign*3)),'context'],mm,domain=('a','b')),mm,rows,norm)
    # Native four equations, including the inverse time equation.
    for speed in (-3,3):
        original=[Q(7),Q(11),Q(13),Q(2)];beta=Q(5,4);x,y,z,t=original;other=[beta*(x-speed*t),y,z,beta*(t-speed*x/25)]
        coords={'a':original,'b':other};roles=('x','y','z','time')
        mm=m|{'zc5':lambda rec:rec in coords,'zc6':lambda rec,axis:c(coords[rec][roles.index(axis)]) if rec in coords and axis in roles else forbidden()}
        assert run('sre',['a','b',c(Q(5)),c(Q(speed)),ones],mm);count+=1
        assert run('sre',['b','a',c(Q(5)),c(Q(-speed)),ones],mm);count+=1
        assert not run('sre',['b','a',c(Q(5)),c(Q(speed)),ones],mm);count+=1
        for i in range(4):
            coords['b'][i]+=1;assert not run('sre',['b','a',c(Q(5)),c(Q(-speed)),ones],mm);coords['b'][i]-=1;count+=1
    return dict(cases=count,record_order_and_signed_velocity_exchange_together=True,native_inverse_spatial_and_time_equations=True)

def physical_model():
    cuts,m,pos,members,fs,pop,fields,shape,support,norm=model();c=cuts.make
    def lower(f,u,ctx):
        if f not in ('K','k') or (u,ctx)!=('duration','context'):forbidden()
        return c(Q(0 if f=='K' else 10))
    def upper(f,u,ctx):return c(cuts.read(lower(f,u,ctx))+2)
    def family(b,f,lu,tu,axis,ctx):
        if b!='body' or f not in ('K','k') or (lu,tu,ctx)!=('length','duration','context') or axis not in ('x','y','z'):forbidden()
        return fs[('x','y','z').index(axis)]
    def velocity(observer,rest,lu,tu,axis,ctx):
        if (observer,rest) not in (('K','k'),('k','K')) or (lu,tu,ctx)!=('length','duration','context') or axis not in ('x','y','z'):forbidden()
        return c(Q((3 if observer=='K' else -3) if axis=='x' else 0))
    m|={'eisls':lower,'eislt':upper,'eislu':family,'eislc':velocity}
    def history(frame):return ['body',frame,'context','length','duration',lower(frame,'duration','context'),upper(frame,'duration','context'),pop,*fs]
    return cuts,m,pop,fs,shape,support,norm,history

@lru_cache(None)
def setting_checks():
    cuts,m,pop,fs,shape,support,norm,history=physical_model();c=cuts.make;count=0
    for rest,observer,speed in (('k','K',3),('K','k',-3)):
        args=['body',shape,rest,observer,c(Q(speed)),'context']
        rows={'ejgi':{norm(history(rest)+[shape])},'eje7':{('body',rest,'context'),('body',observer,'context')},'ejhx':{norm(history(observer)+[c(Q(speed))])},'eioj':{(observer,rest,'length','duration','context')},'ejii':{norm([rest,observer,c(Q(speed)),'context'])}}
        mm=relations(m,rows,norm);count+=perturb(lambda mm:run('ejhy',args,mm),mm,rows,norm)
        for axis in ('x','y','z'):
            v=m['eislc'];assert not run('ejhy',args,mm|{'eislc':lambda *xs,axis=axis,v=v:c(Q(9)) if xs[-2]==axis else v(*xs)});count+=1
        unknowns(lambda mm:run('ejhy',args,mm),mm,('eirh','eislu','eisls','eislt','eislc'))
        rows={'ejhy':{norm(args)},'ejgl':{norm(['body',rest,'context',m['eisls'](rest,'duration','context'),axis,c(Q(w))]) for axis,w in zip(('x','y','z'),(5,1,1))}}
        mm=relations(m,rows,norm);count+=perturb(lambda mm:run('ejhz',args+[c(Q(n)) for n in (5,1,1)],mm,'instance'),mm,rows,norm)
        refused(lambda:run('ejhz',args,mm))
    return dict(cases=count,rest_and_observer_histories_frames_units_and_velocity_bound=True,all_current_records_and_finite_rest_widths_required=True)

@lru_cache(None)
def shape_width_checks():
    cuts,m,pop,fs,shape,support,norm,history=physical_model();c=cuts.make;r=cuts.read;count=0
    for rest,observer,speed,t in (('k','K',3,1),('K','k',-3,11)):
        args=['body',shape,rest,observer,c(Q(speed)),'context']
        transformed=FunctionValue((RS,RS,RS),'truth',lambda x,y,z:((r(x)-speed*t)*Q(5,4),r(y),r(z)) in support)
        rows={'ejgh':{norm([pop,*fs,c(Q(t)),transformed])}};mm=relations(m,rows,norm)
        count+=perturb(lambda mm:run('ejh2',args+[c(Q(t))],mm,'instance'),mm,rows,norm)
        refused(lambda:run('ejh2',args,mm))
        for axis in ('x','y','z'):
            for proper in (0,5):
                observed=Q(proper)*Q(4,5) if axis=='x' else Q(proper)
                rows={'ejgl':{norm(['body',rest,'context',m['eisls'](rest,'duration','context'),axis,c(Q(proper))]),norm(['body',observer,'context',c(Q(t)),axis,c(observed)])}}
                mm=relations(m,rows,norm);wargs=['body',rest,observer,c(Q(speed)),'context',axis,c(Q(proper)),c(Q(t)),c(observed)]
                count+=perturb(lambda mm:run('ejh3',wargs,mm,'instance'),mm,rows,norm)
                for wrong in (observed+1,-1):
                    bad=wargs[:];bad[-1]=c(Q(wrong));wrongrows={'ejgl':{norm(['body',rest,'context',m['eisls'](rest,'duration','context'),axis,c(Q(proper))]),norm(['body',observer,'context',c(Q(t)),axis,c(Q(wrong))])}}
                    assert not run('ejh3',bad,relations(m,wrongrows,norm),'instance');count+=1
                refused(lambda:run('ejh3',wargs[:6],mm))
        rows={'ejh2':{norm(args)},'ejh3':{norm(['body',rest,observer,c(Q(speed)),'context',a]) for a in ('x','y','z')}}
        mm=relations(m,rows,norm);count+=perturb(lambda mm:run('ejh4',args,mm),mm,rows,norm)
    # Arbitrary translated spheres: the entire inverse image is the same closed
    # ellipsoid, with positive semiaxes and a sign-sensitive moving center.
    for speed,t in product((-3,3),(-1,2)):
        center=(Q(2),Q(1),Q(-1));radius=Q(5);f=Q(4,5);target=(f*center[0]+speed*t,center[1],center[2])
        ball=FunctionValue((RS,RS,RS),'truth',lambda *xs:sum((r(x)-z)**2 for x,z in zip(xs,center))<=radius**2)
        for dx,dy,dz in ((0,0,0),(4,0,0),(0,5,0),(0,0,5),(3,3,0),(4,1,0),(0,6,0)):
            p=tuple(x+d for x,d in zip(target,(dx,dy,dz)));expected=Q(dx*dx,16)+Q(dy*dy+dz*dz,25)<=1
            assert run('stv',[ball,c(Q(5)),c(Q(speed)),c(Q(t)),*[c(x) for x in p]],m)==expected;count+=1
    return dict(cases=count,complete_shape_and_each_actual_width_in_observer_time=True,signed_center_and_unchanged_positive_semiaxes=True,zero_width_and_nonconvex_shape_preserved=True)

@lru_cache(None)
def limit_checks():
    cuts,m,pos,members,fs,pop,fields,shape,support,norm=model();c=cuts.make;r=cuts.read;count=0
    for direction,t,magnitude in product((-1,1),(-2,2),(0,3,4)):
        factor={0:Q(1),3:Q(4,5),4:Q(3,5)}[magnitude]
        for x,y,z in sorted(support):
            p=(factor*x+direction*magnitude*t,y,z);args=[shape,*[c(Q(n)) for n in (5,t,direction,magnitude)],*[c(n) for n in p],c(x)]
            assert run('ejh6',args,m,'instance');assert run('stv',[shape,c(Q(5)),c(Q(direction*magnitude)),c(Q(t)),*[c(n) for n in p]],m);count+=2
            for i in range(3):
                bad=args[:];bad[5+i]=c(p[i]+Q(1,7));assert not run('ejh6',bad,m,'instance');count+=1
    for direction,t in product((-1,1),(-2,2)):
        n=100;mag=Q(5*(n*n-1),n*n+1);plane=Q(direction*5*t);epsilon=Q(1)
        rows={'ejg6':{norm([shape,c(plane),c(plane),c(y),c(z)]) for _,y,z in support}};mm=relations(m,rows,norm)
        for p in support:
            args=[shape,c(Q(5)),c(Q(t)),c(Q(direction)),c(epsilon),c(mag),*[c(x) for x in p]]
            assert run('ejh7',args,mm,'instance');count+=1
            assert not run('ejh7',args,mm|{'ejg6':lambda *xs:False},'instance');count+=1
            distance=abs(Q(2*n,n*n+1)*p[0]+direction*mag*t-plane);bad=args[:];bad[4]=c(distance/2);assert not run('ejh7',bad,mm,'instance');count+=1
        args=[shape,*[c(Q(n)) for n in (5,t,direction,Q(1,100),1,Q(1,10),Q(4999,1000))]]
        rows={'suo':{(Q(5),Q(1,100))},'ejh7':{norm([shape,*[c(Q(n)) for n in (5,t,direction,1,Q(4999,1000))]])}}
        mm=relations(m,rows,norm);count+=perturb(lambda mm:run('ejia',args,mm,'instance'),mm,rows,norm)
        refused(lambda:run('ejia',args[:4],mm))
    # Each slot of the signed inverse family is distinguished from forward image.
    args=[shape,*[c(Q(n)) for n in (5,2,-1,3,-5,1,0)]];row=norm(args)
    def inverse(*xs):
        good=norm(xs)==norm([shape,c(Q(5)),c(Q(-3)),c(Q(2))])
        return FunctionValue((RS,RS,RS),'truth',lambda x,y,z:good and (r(x),r(y),r(z))==(-5,1,0))
    mm=m|{'ejh6':lambda *xs:norm(xs)==row,'stv':inverse}
    assert run('ejib',args,mm,'instance');count+=1
    for patch in ({'ejh6':lambda *xs:False},{'stv':lambda *xs:FunctionValue((RS,RS,RS),'truth',lambda *xs:False)}):assert not run('ejib',args,mm|patch,'instance');count+=1
    for d in (-2,0,2):assert not run('ejh5',[c(Q(d))],m);count+=1
    refused(lambda:run('ejib',args[:4],mm))
    refused(lambda:run('ejh6',[shape,*[c(Q(n)) for n in (5,2,-1,3,-5,1,0)]],m))
    return dict(cases=count,both_signed_whole_shape_limits_and_transverse_projection=True,negative_limit_plane_and_regular_inverse_image_agree=True,full_real_quantifiers_retained=True)

@lru_cache(None)
def scope_checks():
    cuts,m,pop,fs,shape,support,norm,history=physical_model();c=cuts.make;count=0
    for rest,observer,speed,direction,t in (('k','K',3,1,1),('K','k',-3,-1,11)):
        args=['body',shape,rest,observer,c(Q(speed)),'context',c(Q(direction)),c(Q(t))]
        rows={'ejh4':{norm(args[:6])},'ejia':{norm([shape,c(Q(5)),c(Q(t)),c(Q(direction))])},'ejib':{norm([shape,c(Q(5)),c(Q(t)),c(Q(direction))])}}
        mm=relations(m,rows,norm);count+=perturb(lambda mm:run('ejic',args,mm,'instance'),mm,rows,norm)
        bad=args[:];bad[6]=c(Q(-direction));assert not run('ejic',bad,m|{n:lambda *xs:True for n in rows},'instance');count+=1
        refused(lambda:run('ejic',args[:7],mm))
    for direction,qa,qb,ca,cb in product((-1,1),(False,True),(False,True),(False,True),(False,True)):
        eligible={b for b,t in zip(('a','b'),(qa,qb)) if t};conclusions={b for b,t in zip(('a','b'),(ca,cb)) if t}
        def qualified(b,s,rest,observer,speed,ctx):return b in eligible and norm([s])==norm([shape]) and (rest,observer,ctx)==('a','b','context') and cuts.read(speed)==direction*3
        def conclusion(b,s,rest,observer,speed,ctx,d):return b in conclusions and norm([s])==norm([shape]) and (rest,observer,ctx)==('a','b','context') and (cuts.read(speed),cuts.read(d))==(direction*3,direction)
        mm=m|{'ejhz':qualified,'ejic':conclusion};args=['a','b',c(Q(direction)),'context',shape]
        assert run('ejid',args,mm,'instance',('a','b'))==((not qa or ca) and (not qb or cb));count+=1
    refused(lambda:run('ejid',args[:4],mm,domain=('a','b')))
    rows={('k','K',Q(1),'context'),('K','k',Q(-1),'context')}
    def content_rows(rs):return lambda *xs:Content(POINTS,(norm(xs) in rs,)*len(POINTS))
    mm=m|{'ejid':content_rows(rows),'ejgy':lambda:Content(POINTS,(True,)*len(POINTS))}
    assert run('ejie',[],mm);count+=1
    for row in rows:
        assert not run('ejie',[],mm|{'ejid':content_rows(rows-{row})});count+=1
        for i in range(4):
            bad=tuple('wrong' if i==j else x for j,x in enumerate(row));assert not run('ejie',[],mm|{'ejid':content_rows((rows-{row})|{bad})});count+=1
    assert not run('ejie',[],mm|{'ejgy':lambda:Content(POINTS,(False,)*len(POINTS))});count+=1
    unknowns(lambda mm:run('ejie',[],mm),mm,('ejid','ejgy'))
    return dict(cases=count,same_rule_two_distinct_frame_roles_and_opposite_velocity=True,all_eligible_bodies_shapes_and_observer_times=True,speed_order_retained_as_comparison_not_acceleration=True)

@lru_cache(None)
def presentation_checks():
    count=0
    for name,rows in (('ejif',{'uh':{('reciprocal','author','ejie','section','discourse')},'zdg':{('reciprocal','author','ejie','section','discourse')}}),('ejih',{'eir3':{('reciprocal','author','paper','ejig','discourse')},'ue':{('previous','reciprocal','discourse')}})):
        mm={n:relation(rs) for n,rs in rows.items()};count+=perturb(lambda mm:run(name,[],mm),mm,rows)
        assert run(name,[],mm|{'ejie':forbidden,'ejig':forbidden});count+=1
    return dict(cases=count,author_assertion_clarity_and_source_order=True,quotation_not_automatic_physical_proof=True)

@lru_cache(None)
def source_record():
    inv=json.loads(read(INVENTORY));u=inv['units'][116];assert u['id']=='einstein-1905:u0117'
    assert u['text']=='Es ist klar, daß die gleichen Resultate von im „ruhenden“ System ruhenden Körpern gelten, welche von einem gleichförmig bewegten System aus betrachtet werden. —'
    retrieval='artifacts/einstein-sphere-setting-v1/retrieval.json';rr=json.loads(read(retrieval));validate_hashes(ROOT,{x['path']:x['sha256'] for x in rr['sources']});paths={INVENTORY,DOC,retrieval,*(x['path'] for x in rr['sources'])}
    return dict(version='einstein-reciprocal-shape-results-source-reading-v1',reviewer='assistant_visual_and_text_review',pages=['903'],segments=[dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[0,len(u['text'])],text=u['text'],source_nonblank_characters=len(re.sub(r'\s|\[M\d+\]','',u['text'])),math=[])],observations=['原刊903頁で直前の三文と、Es ist klarからwerden. —までを再読した。ruheは物体が属する静止系、gleichförmig bewegtは観測する系の一様運動を指す。','die gleichen Resultateは直前の形状・寸法・速度の程度と明示した光速極限へ参照する。後続で示すとの予告をここで実証済みに替えず、次の時計の議論を先取りしない。','二系を交換した同じ規則の適用と読み、各観測系の同時刻と同じ全物質点を保持する。対象を両系に同時に静止させず、符号付き速度−vと負方向の極限平面を保持する。','末尾のダッシュは時計への話題移行を区切る句読法として保持し、別の未記述の命題とは読まない。明白さは著者への提示の帰属である。'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert new.document['statements'][:-1]==old.document['statements'] and len(new.document['statements'])==337
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations'];assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    prior=json.loads(read(PRIOR));validate_hashes(ROOT,prior['source_sha256']);assert selection_binding(new,[332,333,334,335])==prior['selection']
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    load_annotations(ROOT,BASIS,ANNOTATIONS);doc=core();ds={d['name']:d for d in doc['declarations']}
    assert ds['ejig']['body']['force']=='assert'
    assert not [d for d in new.document['declarations'][len(old.document['declarations']):] if d['kind']=='primitive']
    assert {'ejhw','ejhx','ejii','ejgi','eje7','ejgk','ejgl','stv','ejh6','ejh7','ejia','ejib'}<={d['name'] for d in extract_document(doc,roots=['ejid'],statement_indices=[]).document['declarations']}
    for style in ('compact','full'):
        body=format_graph(doc,style);assert parse(body)==parse(transcribe(body,alphabet='v2'))==doc
    assert source_record()==json.loads(read(SOURCE))
    return dict(new_definitions=len(MEANINGS),new_primitives=0,preserved_statements=336,prior_whole_unit_judgments_preserved=True)

def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/SOURCE,json.dumps(source_record(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    results={n:f() for n,f in [('motion',motion_checks),('correspondence',correspondence_checks),('setting',setting_checks),('shape_width',shape_width_checks),('limit',limit_checks),('scope',scope_checks),('presentation',presentation_checks),('structure',structure_checks)]}
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(source_record()['source_sha256'])|{SOURCE,DOC,PRIOR,*DEPENDENCIES,'scripts/compose_reciprocal_shape_results.py','scripts/check_reciprocal_shape_results.py','tests/test_reciprocal_shape_results.py','scripts/check_coordinate_correspondence.py','scripts/check_moving_trip_geometry.py','scripts/check_clock_site_time.py','scripts/check_rod_methods.py','scripts/check_material_relative_frame.py','scripts/check_translated_light_trial.py','scripts/check_transverse_segment.py','scripts/check_material_shape_dimensions.py','scripts/check_transverse_time.py','scripts/compose_speed_boundary_forecast.py','scripts/compose_material_body_motion.py','scripts/compose_material_shape_dimensions.py','scripts/compose_solid_sphere_geometry.py','scripts/compose_shape_contraction.py','scripts/compose_rod_methods.py','scripts/compose_material_relative_frame.py','scripts/compose_relativity_conjecture.py','scripts/compose_two_postulates.py','scripts/compose_limits.py'}
    alignment=dict(segments=[dict(unit=s['unit'],unit_sha256=s['unit_sha256'],range=s['range'],source=s['text'],statements=[INDEX],definitions=list(MEANINGS),status='explicit_interpretive_annotation') for s in source_record()['segments']])
    return dict(status='reciprocal_full_material_shapes_widths_and_signed_limits_connected',document=FULL,**results,alignment=alignment,verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,remaining=['u0117全体の通読判断と登録'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
