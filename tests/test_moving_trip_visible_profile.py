from copy import deepcopy
from fractions import Fraction as Q
from functools import lru_cache
import json
import pytest
from noema.constructed_semantics import FunctionValue,DescriptionValue,evaluate_document
from noema.meaning_catalog import _references
from scripts import check_einstein_moving_trip_visible as check
from scripts import moving_trip_visible_profile as profile
from scripts.shared_modality import call,op,renamed
from scripts.check_rod_geometry import instantiate

RS=profile.CUT
FS=dict(kind='function',parameters=[RS],result=RS)
NUM={'ba','bb','bc','bd','bf','bg','shv','sah','sca','zzba','zzbc','zzbg'}
DOMAIN=('firstend','lastend','ray','depart','reflection','arrival','frame','lengthunit','timeunit','carrieda','carriedb','observera','observerb','rod','recorda','recordb','recordc','placea','placeb','placec','locala','localb','localc','trial','x','y','z','other')
POINTS=('context','other')
DOMAIN+=('measurement','speedunit','author','paper','scope','clocks','trialnode','resultnode','sectionone','timeconvention','note','anchor','timename')
POINTS=('context','measurement','discourse','other')

def forbidden(*args):raise ValueError('Unknown moving-trip-visible input')
def value(x):
    if isinstance(x,DescriptionValue):
        node=renamed(json.loads(x.syntax),{v:k for k,v in mapping().items()})
        if node.get('kind') in ('call','function_ref'):return node['symbol']
        raise ValueError('Unexpected quoted form')
    return x
def relation(rows):return lambda *xs:tuple(value(x) for x in xs) in rows
def cut(n):return FunctionValue(('number',),'truth',lambda q:q<n)
def abstract(d):
    if d['kind']=='definition':d['parameters']=[p['sort'] for p in d['parameters']]
    d['kind']='primitive';d.pop('body',None)
def handlers(doc):return {d['name']:forbidden for d in doc['declarations'] if d['kind']=='primitive'}
@lru_cache(None)
def mapping():return check.names()|{old:check.vocabulary()._symbols[new] for old,new in check.RELATIONS.items()}|check.mapping()
def constants():
    return {n:lambda x=x:x for n,x in {'yd':'context','yf':'measurement','tb':'speedunit','rd':'author','eirf':'paper','ri':'discourse','xy':'scope','zal':'clocks','za2':'trialnode','za3':'resultnode','eisdy':'sectionone','eisjd':'timeconvention','eismk':'note','eisml':'anchor','eismm':'timename','ra':'frame','rb':'timeunit'}.items()}

@lru_cache(None)
def fixture(name,mode='boundary'):
    doc=deepcopy(check.restored()['document']);m=mapping()
    selected=NUM|set(constants())|{d['name'] for d in check.source_excerpt()['declarations'] if d['kind']=='primitive'}
    selected|={'se','eiq2','eiq4','eiqz','eipk'}
    if name!='eite':selected.add('eite')
    if name in ('eito','eitp','eitq','eitr','eits','eitt','eitx','eity','eitz'):
        selected|={'eitm','eitk','eip6'}
        if name!='eito':selected.add('eito')
    if name.startswith('triprole'):selected|={'eitl','eip6'}
    selected.discard(name)
    for d in doc['declarations']:
        if d['name'] in {m[n] for n in selected if n in m}:abstract(d)
    ds={d['name']:d for d in doc['declarations']};seen=set()
    if name=='eite' and mode=='instance':instantiate(ds[m[name]])
    def visit(n):
        if n in seen:return
        seen.add(n)
        for ref in _references(ds[n].get('body')):visit(ref)
    visit(m[name]);doc['declarations']=[d for d in doc['declarations'] if d['name'] in seen]
    target=ds[m[name]];slots=[]
    for i,p in enumerate(target['parameters']):
        slot='tripslot'+chr(97+i);slots.append(slot)
        doc['declarations'].append(dict(kind='primitive',name=slot,parameters=[],result=p['sort']))
    body=call(m[name],*[call(slot) for slot in slots])
    if target['result']=='content':
        doc['declarations'].append(dict(kind='primitive',name='tripcontext',parameters=[],result='situation'))
        body=dict(kind='evaluate',content=body,situation=call('tripcontext'))
    doc['statements']=[dict(kind='ask',body=body)];return doc,slots

def run(name,args,model,mode='boundary',domain=DOMAIN):
    doc,slots=fixture(name,mode);assert len(args)==len(slots),(name,len(args),len(slots))
    m=constants()|model|{'tripcontext':lambda:'discourse'}|{n:(lambda x=x:x) for n,x in zip(slots,args)}
    h=handlers(doc);h.update({mapping().get(n,n):f for n,f in m.items() if mapping().get(n,n) in h})
    return evaluate_document(doc,individuals=domain,situations=POINTS,primitives=h,max_steps=1000000,memoize_definitions=True,memoize_expressions=True)[0]['value']

class ConstructedCuts:
    """Only registered exact rational cuts are read; no probing unknown functions."""
    def __init__(self):self.table={}
    def make(self,value):
        value=Q(value);result=cut(value);self.table[result.implementation]=value;return result
    def read(self,value):
        while isinstance(value,FunctionValue):
            impl=value.implementation
            if impl in self.table:return self.table[impl]
            if isinstance(impl,FunctionValue):
                value=impl
                continue
            code=getattr(impl,'__code__',None)
            if code is None:break
            free=dict(zip(code.co_freevars,(c.cell_contents for c in (getattr(impl,'__closure__',None) or ()))))
            value=free.get('raw')
        raise ValueError('Cut was not constructed by this finite fixture')
def arithmetic():
    cuts=ConstructedCuts();r=cuts.read;c=cuts.make
    return cuts,dict(ba=lambda x:isinstance(r(x),Q),bb=c,bc=lambda a,b:r(a)<=r(b),bd=lambda a,b:c(r(a)+r(b)),bf=lambda a,b:c(r(a)-r(b)),shv=lambda a,b:c(r(a)*r(b)),sca=lambda a,b:r(a)==r(b),zzba=lambda x:isinstance(r(x),Q),zzbc=lambda a,b:r(a)<=r(b))

def numbers():
    cuts,m=arithmetic();c=cuts.make;r=cuts.read
    m|={'bg':lambda a,b:r(a)<r(b),'sah':lambda a,b:c(r(a)*r(b))}
    return cuts,m

def unknowns(check,m,names):
    for n in names:
        try:check(m|{n:forbidden})
        except ValueError as e:assert 'Unknown moving-trip-visible' in str(e),str(e)
        else:raise AssertionError(('Unknown input accepted',n))

def norm_factory(cuts,times):
    def norm(xs):
        def one(x):
            if not isinstance(x,FunctionValue):return value(x)
            if x.parameters==('number',):return cuts.read(x)
            if x.result==RS:return tuple(cuts.read(x(cuts.make(Q(t)))) for t in times)
            forbidden()
        return tuple(one(x) for x in xs)
    return norm

def perturb(check,m,rows,norm=lambda xs:tuple(value(x) for x in xs)):
    count=1;assert check(m)
    for n,rs in rows.items():
        for row in rs:
            assert not check(m|{n:lambda *xs,rs=rs-{row}:norm(xs) in rs}),(n,row);count+=1
            for i in range(len(row)):
                bad=tuple('other' if j==i else x for j,x in enumerate(row))
                assert not check(m|{n:lambda *xs,rs=(rs-{row})|{bad}:norm(xs) in rs}),(n,i);count+=1
    unknowns(check,m,rows);return count

@lru_cache(None)
def numeric_checks():
    cuts,m=numbers();c=cuts.make;count=0
    # Compare independently expressed intersections and elapsed-time equations.
    for origin in (-9,0,Q(5,2)):
        for length,light,speed,start in ((6,3,1,7),(4,5,0,-2),(Q(3,2),Q(7,2),Q(1,2),Q(1,3))):
            middle=Q(start)+Q(length)/(Q(light)-speed);last=middle+Q(length)/(Q(light)+speed)
            base=list(map(Q,(origin,length,light,speed,start,middle,last)))
            for slot in range(7):
                for delta in (0,Q(1,4)):
                    xs=list(base);xs[slot]+=delta
                    expected=(xs[1]>0 and 0<=xs[3]<xs[2] and xs[4]<xs[5]<xs[6] and (xs[2]-xs[3])*(xs[5]-xs[4])==xs[1] and (xs[2]+xs[3])*(xs[6]-xs[5])==xs[1])
                    assert run('eith',list(map(c,xs)),m)==expected;count+=1
                    assert run('sdb',list(map(c,xs[1:])),m)==expected;count+=1
    for xs in ((5,0,3,1,7,7,7),(5,6,3,3,7,10,12),(5,6,3,-1,7,10,12),(5,6,-3,1,7,10,12),(5,6,3,1,10,7,12),(5,6,3,1,7,10,9)):
        assert not run('eith',list(map(c,map(Q,xs))),m);count+=1
    good=list(map(c,map(Q,(5,6,3,1,7,10,Q(23,2)))))
    unknowns(lambda mm:run('eith',good,mm),m,('ba','bg','bc','bf','bd','shv','sca'))
    bad=list(good);bad[0]=FunctionValue(('number',),'truth',lambda x:x<5)
    try:run('eith',bad,m)
    except ValueError:pass
    else:raise AssertionError('Unknown cut decoded by sampling')
    return dict(cases=count,arbitrary_origin_and_initial_time=True,zero_speed_comparison_allowed_but_not_superluminal=True,two_intersections_match_existing_elapsed_equations_on_exact_rationals=True,unknown_cut_refused=True)

@lru_cache(None)
def comotion_checks():
    cuts,m=numbers();c=cuts.make;r=cuts.read;count=0
    def traces(profile):
        def xyz(side,a,t):
            base=(t*t,2*t,-t)[a]
            if side=='reference':return base
            offset=(2,3,4)[a]
            if profile=='drift':offset+=t if a==2 else 0
            if profile=='excursion':offset+=t*(2-t) if a==0 else 0
            if profile=='orbit':offset=((1-t*t)/(1+t*t),2*t/(1+t*t),0)[a]
            return base+offset
        return [FunctionValue((RS,),RS,lambda t,s=s,a=a:c(xyz(s,a,r(t)))) for s in ('target','reference') for a in range(3)]
    for profile in ('fixed','drift','excursion','orbit'):
        fs=traces(profile)
        for t,u in ((0,1),(0,2),(1,2),(1,1)):
            expected=profile=='fixed' or t==u or profile=='excursion' and (t,u)==(0,2)
            assert run('eitd',[c(Q(t)),c(Q(u)),*fs],m)==expected;count+=1
    # The excursion returns to the initial offset but fails at an interior time.
    fs=traces('fixed');times=(0,1,2);norm=norm_factory(cuts,times)
    args=['observera','carrieda','frame','context','lengthunit','timeunit',c(Q(0)),c(Q(2)),*fs]
    rows={'se':{norm([obj,*args[2:8],*fs[offset:offset+3]]) for obj,offset in (('observera',0),('carrieda',3))},'eisdd':{('frame','lengthunit','timeunit','context')}}
    mm=m|{n:lambda *xs,rs=rs:norm(xs) in rs for n,rs in rows.items()}
    check=lambda model:run('eite',args+[c(Q(0)),c(Q(1))],model,'instance')
    count+=perturb(check,mm,rows,norm)
    for lo,hi in ((2,0),(0,0)):
        bad=list(args);bad[6:8]=[c(Q(lo)),c(Q(hi))]
        assert not run('eite',bad+[c(Q(0)),c(Q(1))],mm|{'se':lambda *xs:True},'instance');count+=1
    same=list(args);same[0]=same[1];assert not run('eite',same+[c(Q(0)),c(Q(1))],mm|{'se':lambda *xs:True},'instance');count+=1
    try:run('eite',args,mm)
    except ValueError as e:assert 'rational number domain' in str(e) or 'Finite function domain' in str(e) or 'function domain' in str(e) or 'quantification' in str(e),str(e)
    else:raise AssertionError('Whole time domain replaced by samples')
    return dict(cases=count,constant_relative_vector_not_only_distance=True,common_curved_motion_allowed=True,interior_excursion_detected=True,both_complete_history_bindings_required=True,local_quantifier_instantiation_only=True,full_real_time_domain_refused=True)

def trip_model():
    cuts,m=numbers();c=cuts.make;r=cuts.read;times=(Q(7),Q(8),Q(10),Q(23,2));norm=norm_factory(cuts,times)
    scalar=list(map(Q,(5,6,3,1,7,10,Q(23,2))))
    args=['firstend','lastend','ray','depart','reflection','arrival','frame','context','lengthunit','timeunit',*map(c,scalar)]
    fn=lambda lo,x,v:FunctionValue((RS,),RS,lambda t:c(Q(x)+Q(v)*(r(t)-Q(lo))))
    zero=fn(0,0,0)
    histories=[['firstend','frame','context','lengthunit','timeunit',c(Q(7)),c(Q(23,2)),fn(7,5,1),zero,zero],['lastend','frame','context','lengthunit','timeunit',c(Q(7)),c(Q(23,2)),fn(7,11,1),zero,zero],['ray','frame','context','lengthunit','timeunit',c(Q(7)),c(Q(10)),fn(7,5,3),zero,zero],['ray','frame','context','lengthunit','timeunit',c(Q(10)),c(Q(23,2)),fn(10,14,-3),zero,zero]]
    rows={'se':{norm(xs) for xs in histories},'eisb5':{('ray','frame','context')},'cf':{('ray',)},'cg':{('ray','depart','reflection','frame'),('ray','reflection','arrival','frame')},'ch':{('ray','reflection','frame')},'eisca':{('ray','depart','reflection','frame','context'),('ray','reflection','arrival','frame','context')},'zzbu':set(),'zzbv':set()}
    for end,event,t,x in (('firstend','depart',Q(7),Q(5)),('lastend','reflection',Q(10),Q(14)),('firstend','arrival',Q(23,2),Q(19,2))):
        rows['zzbu'].add((event,'frame','context','lengthunit','timeunit',t,x,Q(0),Q(0)))
        for obj in (end,'ray'):rows['zzbv'].add((obj,event,'context'))
    m|={n:lambda *xs,rs=rs:norm(xs) in rs for n,rs in rows.items()}
    return cuts,m,args,rows,norm,histories,fn

@lru_cache(None)
def path_checks():
    cuts,m,args,rows,norm,histories,fn=trip_model();c=cuts.make;count=0
    count+=perturb(lambda mm:run('eiti',args,mm),m,rows,norm)
    for slot in range(len(args)):
        bad=list(args);bad[slot]=c(cuts.read(bad[slot])+1) if isinstance(bad[slot],FunctionValue) else 'other'
        assert not run('eiti',bad,m),(slot,);count+=1
    # Native linear construction in all three axes, independent of the X-axis trip.
    linear=['observera','frame','context','lengthunit','timeunit',c(Q(2)),c(Q(5)),*map(c,map(Q,(4,-3,2,-2,3,1)))]
    expected=norm(linear[:7]+[fn(2,x,v) for x,v in ((4,-2),(-3,3),(2,1))])
    model=m|{'se':lambda *xs:norm(xs)==expected}
    assert run('eitf',linear,model);count+=1
    for slot in range(len(linear)):
        bad=list(linear);bad[slot]=c(cuts.read(bad[slot])+1) if isinstance(bad[slot],FunctionValue) else 'other'
        assert not run('eitf',bad,model),slot;count+=1
    unknowns(lambda mm:run('eitf',linear,mm),model,('se','ba','bf','bd','shv'))
    return dict(cases=count,native_linear_coordinates_in_all_axes=True,both_endpoint_histories_and_both_light_histories_bound=True,native_sde_and_sb_same_three_events=True,vacuum_reflection_and_physical_light_separate=True,finite_boundary_function_fingerprints_not_full_history_proof=True)

def joined_model():
    cuts,m,args,rows,norm,histories,fn=trip_model();c=cuts.make
    constants={'xn':'firstend','xo':'lastend','xi':'rod','zaj':'carrieda','zak':'carriedb','zax':'ray','ra':'frame','ta':'lengthunit','rb':'timeunit','zas':'recorda','zat':'recordb','zau':'recordc','zay':'observera','zaz':'observerb','zaw':'trial','yn':'x','yo':'y','yp':'z'}
    m|={n:lambda x=x:x for n,x in constants.items()};m|={'zav':lambda:c(Q(6)),'tc':lambda:c(Q(3)),'yb':lambda:c(Q(1)),'eisls':lambda *xs:c(Q(7)),'eislt':lambda *xs:c(Q(23,2))}
    data={'recorda':('carrieda','firstend','depart','placea','locala',Q(7)),'recordb':('carriedb','lastend','reflection','placeb','localb',Q(10)),'recordc':('carrieda','firstend','arrival','placec','localc',Q(23,2))}
    def selected(rec,slot):
        if rec not in data:forbidden()
        return data[rec][slot]
    m|={'zad':lambda rec:selected(rec,2),'zae':lambda rec:selected(rec,3),'zaf':lambda rec:selected(rec,4),'zag':lambda rec:c(selected(rec,5)),'zah':lambda rec:c(selected(rec,5))}
    rows|={'eipk':{('context',)},'eiq4':{('carrieda','firstend','context'),('carriedb','lastend','context')},'zac':set(),'eiq2':set(),'eiqz':{('carrieda','firstend','context'),('carriedb','lastend','context')},'xb':{('observera',),('observerb',)},'zap':{('observera','carrieda','context'),('observerb','carriedb','context')},'zaq':{('observera','carrieda','frame','context'),('observerb','carriedb','frame','context')},'eite':set(),'za4':{('trial','ray','depart','reflection','arrival','frame','context')},'zar':{(o,'carrieda','carriedb','trial','bi','context') for o in ('observera','observerb')}}
    for rec,(ck,end,event,place,local,t) in data.items():
        rows['zac'].add((rec,ck,'context'));rows['eiq2'].add((ck,end,event,place,local,t,t,'context'))
    tracks={}
    for end,x in (('firstend',5),('lastend',11)):
        tracks[end]=[fn(7,x,1),fn(0,0,0),fn(0,0,0)]
    def family(body,frame,lu,tu,axis,ctx):
        if (body,frame,lu,tu,ctx)!=('rod','frame','lengthunit','timeunit','context') or axis not in ('x','y','z'):forbidden()
        def get(end):
            if end not in tracks:forbidden()
            return tracks[end][('x','y','z').index(axis)]
        return FunctionValue(('individual',),FS,get)
    observers={o:[fn(7,x,1),fn(0,1,0),fn(0,0,0)] for o,x in (('observera',5),('observerb',11))}
    def observer(obj,frame,lu,tu,axis,ctx):
        if obj not in observers or (frame,lu,tu,ctx)!=('frame','lengthunit','timeunit','context') or axis not in ('x','y','z'):forbidden()
        return observers[obj][('x','y','z').index(axis)]
    for o,ck,end in (('observera','carrieda','firstend'),('observerb','carriedb','lastend')):
        rows['eite'].add(norm([o,ck,'frame','context','lengthunit','timeunit',c(Q(7)),c(Q(23,2)),*observers[o],*tracks[end]]))
    m|={'eislu':family,'eismh':observer}
    m|={n:lambda *xs,rs=rs:norm(xs) in rs for n,rs in rows.items()}
    return cuts,m,rows,norm

@lru_cache(None)
def connection_checks():
    cuts,m,rows,norm=joined_model();count=0
    selected={n:rows[n] for n in ('eipk','eiq4','zac','eiq2')}
    count+=perturb(lambda mm:run('eitk',['context'],mm),m,selected,norm)
    selected={n:rows[n] for n in ('zac','eiq2','eiqz','xb','zap','zaq','eite','za4','zar')}
    count+=perturb(lambda mm:run('eitm',['context'],mm),m,selected,norm)
    # Applying the quoted test never runs its midpoint or a stationary-clock rule.
    assert run('eitm',['context'],m|{'bi':forbidden,'qo':forbidden});count+=1
    for n in ('zas','zat','zau'):
        replacement={'zas':'recordb','zat':'recordc','zau':'recorda'}[n]
        assert not run('eitk',['context'],m|{n:lambda x=replacement:x});count+=1
    assert not run('eitm',['context'],m|{'zaz':lambda:'observera'});count+=1
    unknowns(lambda mm:run('eitk',['context'],mm),m,('eislu','zad','zah','zag','se','eiq2'))
    unknowns(lambda mm:run('eitm',['context'],mm),m,('eismh','eislu','eisls','eislt','zar'))
    return dict(cases=count,three_records_same_current_local_comparisons=True,rod_and_carried_clock_whole_interval_conditions_preserved=True,observer_representatives_bound_to_same_clock_endpoints=True,criterion_application_does_not_execute_midpoint_or_qo=True)

@lru_cache(None)
def trial_checks():
    cuts,m,rows,norm=joined_model();rows['eitm']={('context',)};m['eitm']=relation(rows['eitm'])
    used={n:rows[n] for n in ('eitm','eipk','eiq4','eisb5','cf','cg','ch','eisca','zzbu')}
    used['zzbv']={x for x in rows['zzbv'] if x[0]=='ray'}
    # Endpoint/clock positions are already required through eiq2 in eitm;
    # this native body adds the light's membership of the same three events.
    mm=m|{'zzbv':lambda *xs:norm(xs) in used['zzbv']}
    count=perturb(lambda model:run('eito',['context'],model),mm,used,norm)
    assert run('eito',['context'],mm|{n:forbidden for n in ('tc','sdb','eith','eitk')});count+=1
    unknowns(lambda model:run('eito',['context'],model),mm,('eislu','zad','zah'))
    return dict(cases=count,native_light_membership_at_same_endpoint_events=True,no_elapsed_equations_or_constant_speed_in_initial_setting=True)

@lru_cache(None)
def result_checks():
    cuts,m,rows,norm=joined_model();c=cuts.make
    rows={'eito':{('context',)},'eitk':{('context',)},'eiscc':{('frame','lengthunit','timeunit','speedunit','context')},'ti':{('lengthunit',)},'tj':{('lengthunit','timeunit','speedunit')},'yx':{('context','measurement')},'eip6':{(Q(6),'measurement')}}
    m|=constants();m|={n:lambda *xs,rs=rs:norm(xs) in rs for n,rs in rows.items()}
    count=perturb(lambda mm:run('eitp',[],mm),m,rows,norm)
    for n in ('zav','tc','yb'):
        original=cuts.read(m[n]())
        assert not run('eitp',[],m|{n:lambda x=original:c(x+1)});count+=1
    for rec in ('recorda','recordb','recordc'):
        original=m['zag']
        assert not run('eitp',[],m|{'zag':lambda r,rec=rec:c(cuts.read(original(r))+(1 if r==rec else 0))});count+=1
    assert run('eitp',[],m|{n:forbidden for n in ('ya','sbd','sbk','eip2')});count+=1
    unknowns(lambda mm:run('eitp',[],mm),m,('zag','zav','tc','yb','sah','bc','bf'))
    return dict(cases=count,native_sdi_sdb_bind_both_elapsed_times=True,current_rest_frame_measurement_and_calibrated_units=True,initial_length_and_old_principle_not_substituted=True)

@lru_cache(None)
def note_checks():
    cuts,m,rows,norm=joined_model();c=cuts.make;count=0
    for rec,t in (('recorda',Q(7)),('recordb',Q(10)),('recordc',Q(23,2))):
        assert run('eitq',[rec,c(t),'context'],m);count+=1
        assert not run('eitq',[rec,c(t+1),'context'],m);count+=1
    selected={n:{row for row in rows[n] if (n=='zac' and row[0]=='recorda') or (n=='eiq2' and row[2]=='depart')} for n in ('zac','eiq2')}
    count+=perturb(lambda mm:run('eitq',['recorda',c(Q(7)),'context'],mm),m,selected,norm)
    for n in ('zag','zah'):
        assert not run('eitq',['recorda',c(Q(7)),'context'],m|{n:lambda rec:c(Q(8))});count+=1
    # A fourth eligible record is permitted; the gloss is not an enumeration
    # restricted to departure/reflection/arrival.
    extra=m|{'zad':lambda rec:'depart','zae':lambda rec:'placea','zaf':lambda rec:'locala','zag':lambda rec:c(Q(8)),'zah':lambda rec:c(Q(8)),
      'zac':lambda rec,clock,ctx:(rec,clock,ctx)==('other','carrieda','context'),
      'eiq2':lambda *xs:norm(xs)==('carrieda','firstend','depart','placea','locala',Q(8),Q(8),'context')}
    assert run('eitq',['other',c(Q(8)),'context'],extra);count+=1
    unknowns(lambda mm:run('eitq',['recorda',c(Q(7)),'context'],mm),m,('zac','eiq2','zad','zae','zaf','zag','zah'))
    return dict(cases=count,same_value_local_time_and_moving_clock_reading=True,same_current_place_event_and_local_comparison_required=True,arbitrary_eligible_record_not_only_three_trial_records=True)

@lru_cache(None)
def presentation_checks():
    count=0
    scenarios={
      'eits':{'ug':{('trialnode','author','eitn','scope','discourse')},'zao':{('clocks','trialnode','scope','discourse')},'eismi':{('trialnode','author','sectionone','bi','paper','discourse')}},
      'eitt':{'eismj':{('resultnode','author','eitn','eiot','eitp','scope','paper','discourse')}},
      'eitr':{'eislo':{('timename','eitq','paper','discourse')},'eisku':{('timeconvention','eing','frame','timeunit','paper','discourse')}},
      'eitx':{'eir3':{('trialnode','author','paper','eitu','discourse')},'ue':{('clocks','trialnode','discourse')}},
      'eity':{'eir3':{('resultnode','author','paper','eitv','discourse')},'ue':{('trialnode','resultnode','discourse')}},
      'eitz':{'eir3':{('note','author','paper','eitw','discourse')},'eisfo':{('anchor','note','paper',Q(1),'discourse')},'eisa5':{('note','author','eitn','eitr','discourse')}}}
    for name,rows in scenarios.items():
        m=constants()|{n:relation(rs) for n,rs in rows.items()};count+=perturb(lambda mm:run(name,[],mm),m,rows)
        assert run(name,[],m|{n:forbidden for n in ('eito','eitk','eip6','bi','eitq','eing','se','eios')});count+=1
    assert not run('eitz',[],constants()|{n:lambda *xs:True for n in ('eir3','eisfo','eisa5')}|{'eisml':lambda:'note'});count+=1
    return dict(cases=count,additional_setting_section_one_criterion_and_present_results=True,current_principle_not_necessity_or_future_prediction=True,note_number_and_exact_anchor_supplement_connected=True,quotes_do_not_execute_physics_or_clock_readings=True)



def test_profile_and_source_backprojection():
    voc=check.vocabulary();old=check.previous.vocabulary()
    assert len(voc._words)==696 and len(old._words)==687
    for field in ('entries','compounds','definitions','primitives'):
        assert all(voc.document()[field][n]==d for n,d in old.document()[field].items())
    doc=check.restored()['document'];assert len(doc['declarations'])==1036 and len(doc['statements'])==59
    assert doc['statements'][:55]==check.previous.document()['statements']
    oldds={d['name']:d for d in check.previous.document()['declarations']};ds={d['name']:d for d in doc['declarations']}
    assert all(ds[n]==d for n,d in oldds.items())
    assert check.backprojection(doc)==check.source_excerpt()
    b=check.bridge();assert len(b['source_units'])==5 and len(b['math'])==8

def test_native_intersections_and_both_equations():assert numeric_checks()['unknown_cut_refused']
def test_relative_vector_and_complete_histories():assert comotion_checks()['full_real_time_domain_refused']
def test_same_light_endpoints_and_all_paths():assert path_checks()['native_sde_and_sb_same_three_events']
def test_records_observers_and_nonexecuted_criterion():assert connection_checks()['criterion_application_does_not_execute_midpoint_or_qo']
def test_initial_setting_does_not_assume_results():assert trial_checks()['no_elapsed_equations_or_constant_speed_in_initial_setting']
def test_both_results_and_current_measurement():assert result_checks()['native_sdi_sdb_bind_both_elapsed_times']
def test_local_time_gloss_all_eligible_records():assert note_checks()['arbitrary_eligible_record_not_only_three_trial_records']
def test_presentations_and_local_note_attachment():assert presentation_checks()['quotes_do_not_execute_physics_or_clock_readings']


def native_run(doc,h):
    domain=tuple(set(check.BASE.values())|{'other','setting','frame'})
    return [r['value'] for r in evaluate_document(doc,individuals=domain,situations=check.SITUATIONS,primitives=h)]


def context(doc,**options):return handlers(doc)|{check.vocabulary()._symbols[n]:f for n,f in check.context_handlers(check.BASE,**options).items()}


def test_all_reference_lookups_are_nonexecuting_and_acyclic():
    doc=deepcopy(check.restored()['document']);n=check.names()
    doc['declarations'].append(dict(kind='primitive',name='expected',parameters=[],result='individual'))
    for old in (*check.SENTENCES,*check.DESIGNATIONS,*check.ROLE_ASSIGNMENTS,'za2','eisml','eismk'):
        doc['statements']=[dict(kind='ask',body=op('equal',call(n[old]),call('expected')))]
        assert native_run(doc,context(doc)|dict(expected=lambda:check.BASE[old]))==[True]
        assert native_run(doc,context(doc)|dict(expected=lambda:'other'))==[False]
    # Read the cut's rational predicate without running its measurement role.
    doc['statements']=[dict(kind='ask',body=dict(kind='apply',function=call(n['zav']),arguments=[check.author.num(5)]))]
    assert native_run(doc,context(doc))==[True]
    ds={d['name']:d for d in doc['declarations']};done=set()
    def visit(name,stack):
        assert name not in stack,'Cyclic reference'
        if name in done:return
        for ref in _references(ds[name].get('body')):visit(ref,stack|{name})
        done.add(name)
    for old in check.LOCAL_NAMES:visit(n[old],set())


@pytest.mark.parametrize('field',range(4))
def test_each_described_reference_key_is_required(field):
    doc=deepcopy(check.restored()['document']);n=check.names()
    for old,(anchor,_) in check.ROLE_ASSIGNMENTS.items():
        roles=check.role_model(check.BASE)
        key=(check.BASE['eirf'],check.BASE[anchor],check.canonical(dict(kind='function_ref',symbol=check.reference_roles()[old])),check.BASE['ri'])
        found=roles.pop(key);bad=list(key);bad[field]='unknown';roles[tuple(bad)]=found
        doc['statements']=[dict(kind='ask',body=op('equal',call(n[old]),call(n[old])))]
        with pytest.raises(ValueError,match='Unknown temporal reference'):native_run(doc,context(doc,roles=roles))
    key=(check.BASE['eirf'],check.BASE['za3'],check.canonical(dict(kind='function_ref',symbol=n['triprolelength'])),check.BASE['ri'])
    bad=list(key);bad[field]='unknown'
    doc['statements']=[dict(kind='ask',body=dict(kind='apply',function=call(n['zav']),arguments=[check.author.num(5)]))]
    with pytest.raises(ValueError,match='Unknown cut reference'):native_run(doc,context(doc,cuts={tuple(bad):cut(6)}))


def test_text_span_and_local_marker_keys_do_not_collapse_locations():
    spans={('doc','first','second','body'):'span'}
    attachments={('doc','second',1,1,'body'):'marker',('doc','second',1,2,'body'):'latermarker',('doc','first',1,1,'body'):'earliermarker'}
    refs=profile.MovingTextReferences(spans,attachments)
    assert refs.span('doc','first','second','body')=='span'
    assert refs.attachment('doc','second',1,1,'body')=='marker'
    assert refs.attachment('doc','second',1,2,'body')=='latermarker'
    assert refs.attachment('doc','first',1,1,'body')=='earliermarker'
    for method,key in ((refs.span,('doc','first','second','body')),(refs.attachment,('doc','second',1,1,'body'))):
        for i,x in enumerate(key):
            bad=list(key);bad[i]=99 if isinstance(x,int) else 'unknown'
            with pytest.raises(ValueError):method(*bad)
    with pytest.raises(ValueError):refs.span('doc','second','first','body')
    for invalid in (0,-1,Q(1,2),True,'1'):
        with pytest.raises(ValueError):refs.attachment('doc','second',invalid,1,'body')
        with pytest.raises(ValueError):refs.attachment('doc','second',1,invalid,'body')
    bridge=check.bridge();assert bridge['span']['za2']==['tripfirst','tripsecond']
    assert bridge['attachment']['eisml']==dict(sentence='tripsecond',printed_number=1,occurrence=1,after='Zur Zeit',before='M0054')


def test_connected_attribution_and_zeit_printed_form():
    from scripts.name_presentation_profile import scalar_text
    rows=dict(eir3={('za2','author','doc','eitu','body'),('za3','author','doc','eitv','body'),('eismk','author','doc','eitw','body')},
        ue={('zal','za2','body'),('za2','za3','body')},eisfo={('eisml','eismk','doc',Q(1),'body')},eisa5={('eismk','author','eitn','eitr','body')})
    doc=deepcopy(check.restored()['document']);doc['statements']=doc['statements'][55:58]
    h=context(doc)|{check.mapping()[old]:relation(facts) for old,facts in rows.items()}
    assert native_run(doc,h)==[True,True,True]
    for old in rows:
        assert not all(native_run(doc,h|{check.mapping()[old]:lambda *xs:False}))
    doc['statements']=check.restored()['document']['statements'][-1:]
    printed=lambda name,language,text,ctx:(name,scalar_text(language),scalar_text(text),ctx)==('eismm','de','Zeit','body')
    assert native_run(doc,context(doc)|{check.vocabulary()._symbols['printedform']:printed})==[True]


def test_observer_and_length_reference_roles_bind_same_setting():
    cuts,m,rows,norm=joined_model();m|=constants();c=cuts.make
    for role,clock,end in [('observera','carrieda','firstend'),('observerb','carriedb','lastend')]:
        wanted={('observera',clock,end,'context')}
        h=m|{'eitl':lambda *xs:tuple(xs) in wanted}
        assert run('triprole'+role,['observera','discourse'],h)
        assert not run('triprole'+role,['observerb','discourse'],h)
        for i in range(4):
            bad=list(next(iter(wanted)));bad[i]='other'
            assert not run('triprole'+role,['observera','discourse'],h|{'eitl':lambda *xs:tuple(xs)==tuple(bad)})
    h=m|{'yx':relation({('context','measurement')}),'eip6':lambda val,ctx:cuts.read(val)==6 and ctx=='measurement'}
    assert run('triprolelength',[c(6),'discourse'],h)
    assert not run('triprolelength',[c(7),'discourse'],h)
    assert not run('triprolelength',[c(6),'discourse'],h|{'yx':lambda *xs:False})
    assert not run('triprolelength',[c(6),'discourse'],h|{'yf':lambda:'other'})


def test_record_roles_bind_every_event_and_clock_field():
    cuts,m,rows,norm=joined_model();m|=constants()
    entities=('placea','placeb','depart','reflection','arrival','ray')
    lookup=lambda trial,index:entities[int(index)] if trial=='trial' and index in (2,3,4) else forbidden()
    h=m|{'roundtripentity':lookup}
    # The profile name is already a public symbol, outside the old-name mapping.
    h[check.vocabulary()._symbols['roundtripentity']]=h.pop('roundtripentity')
    for role,record in [('depart','recorda'),('reflect','recordb'),('return','recordc')]:
        assert run('triprole'+role,[record,'discourse'],h)
        for other in {'recorda','recordb','recordc'}-{record}:assert not run('triprole'+role,[other,'discourse'],h)
        for field in ('zad','zae','zaf'):
            assert not run('triprole'+role,[record,'discourse'],h|{field:lambda rec:'other'})
        for field in ('zag','zah'):
            assert not run('triprole'+role,[record,'discourse'],h|{field:lambda rec:cuts.make(99)})
        assert not run('triprole'+role,[record,'discourse'],h|{'zac':lambda *xs:False})
        with pytest.raises(ValueError):run('triprole'+role,[record,'discourse'],h|{check.vocabulary()._symbols['roundtripentity']:forbidden})


def test_changed_content_cannot_reuse_source_projection():
    doc=deepcopy(check.restored()['document']);doc['statements'][55]['body']=dict(kind='truth',value=True)
    with pytest.raises(ValueError,match='Changed migration'):check.backprojection(doc)


def test_trial_role_witness_binding_one_binder_at_a_time():
    doc,slots=fixture('triproletrial');target=mapping()['triproletrial']
    # Keep one actual existential binder, instantiate its two peers. This is
    # a binding diagnostic, not exhaustive evaluation of the threefold domain.
    values={'vc':'depart','vd':'reflection','ve':'arrival'}
    base={'zax':lambda:'ray','ra':lambda:'frame','yd':lambda:'context',
        'za4':relation({('trial','ray','depart','reflection','arrival','frame','context')}),
        'cf':relation({('ray',)}),'cg':relation({('ray','depart','reflection','frame'),('ray','reflection','arrival','frame')}),
        'ch':relation({('ray','reflection','frame')}),slots[0]:lambda:'trial',slots[1]:lambda:'discourse'}
    domain=('trial','ray','depart','reflection','arrival','frame','other')
    for kept in values:
        projected=deepcopy(doc)
        def walk(node):
            if isinstance(node,list):return [walk(x) for x in node]
            if not isinstance(node,dict):return node
            if node.get('kind')=='exists' and node['variable']!=kept:return walk(node['body'])
            if node.get('kind')=='variable' and node['name'] in values and node['name']!=kept:return call('fixed'+node['name'])
            return {k:walk(v) for k,v in node.items()}
        declaration=next(d for d in projected['declarations'] if d['name']==target);declaration['body']=walk(declaration['body'])
        projected['declarations']=[dict(kind='primitive',name='fixed'+name,parameters=[],result='individual') for name in sorted(set(values)-{kept})]+projected['declarations']
        def evaluate(model):
            h=handlers(projected);h.update({mapping().get(n,n):f for n,f in model.items() if mapping().get(n,n) in h})
            h.update({'fixed'+n:(lambda x=x:x) for n,x in values.items() if n!=kept})
            return evaluate_document(projected,individuals=domain,situations=POINTS,primitives=h)[0]['value']
        assert evaluate(base)
        for field in ('za4','cf','cg','ch'):assert not evaluate(base|{field:lambda *xs:False})
        # za4 and the actual sde body must agree on this witness's event slot.
        wanted=['trial','ray','depart','reflection','arrival','frame','context'];wanted[2+list(values).index(kept)]='other'
        assert not evaluate(base|{'za4':relation({tuple(wanted)})})


def test_ray_reference_role_binds_candidate_frame_and_setting():
    base=constants()|{'ra':lambda:'frame','yd':lambda:'context','eisb5':relation({('ray','frame','context')})}
    assert run('triproleray',['ray','discourse'],base)
    assert not run('triproleray',['other','discourse'],base)
    assert not run('triproleray',['ray','discourse'],base|{'ra':lambda:'other'})
    assert not run('triproleray',['ray','discourse'],base|{'yd':lambda:'other'})
