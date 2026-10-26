from copy import deepcopy
from itertools import product
from fractions import Fraction as Q
from functools import lru_cache
import json,re
import pytest
from noema.constructed_semantics import Content,FunctionValue,SequenceValue,DescriptionValue,QuestionValue,evaluate_document
from noema.meaning_catalog import _references
from scripts import check_einstein_transverse_visible as check
from scripts import transverse_visible_profile as profile
from scripts.shared_modality import call,op,renamed

RS=profile.CUT
VS=dict(kind='function',parameters=['individual'],result=RS)
MS=dict(kind='function',parameters=['individual','individual'],result=RS)
NUM={'ba','bb','bc','bd','bf','bg','shv','sah','sca','zzba','zzbc','zzbg'}
ROLES=('x','y','z','time')
POINTS=('context','discourse','other')
CONSTANTS={'ra':'frame','zbm':'moving','ta':'lengthunit','rb':'unit','rc':'reference','yn':'x','yo':'y','yp':'z','zc7':'time','zb6':'context','rd':'author','eirf':'paper','eisms':'section','ri':'discourse','zdq':'trial','zdr':'firstclock','zds':'secondclock','zdu':'setup','zdv':'inference','zdp':'purpose','zdx':'outward','zdy':'returning','zd2':'expansion'}
EVENTS=('depart','reflection','arrival');TUPLES=('tuplea','tupleb','tuplec');CLOCKS=('locala','localb','localc');PLACES=('placea','placeb','placec')
DOMAIN=tuple(dict.fromkeys([*EVENTS,*TUPLES,*CLOCKS,*PLACES,'tuple','origin','mirror','ray','axis','other',*[x for n,x in CONSTANTS.items() if n not in ('zb6','ri')]]))
POINTS=('context','discourse','other')
CONSTANTS|={'zee':'actor','zeg':'notice','zeh':'consequence','zeb':'previous'}
DOMAIN=tuple(dict.fromkeys([*DOMAIN,'a','b','point','actor','notice','consequence','previous','firstclock','secondclock','history','moment']))


def forbidden(*args):raise ValueError('Unknown transverse-visible input')
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

def project(node,sorts):
    if any(node==s for s in sorts):return 'individual'
    if isinstance(node,dict):return {k:project(v,sorts) for k,v in node.items()}
    if isinstance(node,list):return [project(v,sorts) for v in node]
    return node

from math import isqrt
CONSTANTS|={'zen':'notice','zeo':'consequence','zeh':'previous','zea':'earlier'}
DOMAIN=tuple(dict.fromkeys([*DOMAIN,'notice','consequence','previous','earlier','c']))

@lru_cache(None)
def fixture(name,mode='boundary'):
    doc=deepcopy(check.restored()['document']);m=mapping()
    boundaries=NUM|set(CONSTANTS)|{d['name'] for d in check.source_excerpt()['declarations'] if d['kind']=='primitive'}
    boundaries|={'bj','sle','sje'}
    if name=='ei3w':boundaries|={'eiz7','qo'}
    if name=='ei3x':boundaries|={'eifw','eior','eiyg','eiyi','eiyj'}
    if name=='ei3z' and mode!='native_history':boundaries.add('se')
    if name=='ei32':boundaries|={'ei3w','eizm','ei3i','ei3h','ei3z','ei3x'}
    if name=='ei33':boundaries|={'ei3d','ei3c','eiyf','eios','ei32'}
    if name=='ei34':boundaries.add('ei32')
    if name=='ei35':boundaries|={'ei3d','ei3c','eiyf','eios','ei34'}
    if name=='ei36':boundaries.add('ei35')
    if name=='ei37':boundaries|={'ei35','sll'}
    if name=='slj':boundaries.add('slh')
    if name=='slk':boundaries.add('sjs')
    if name=='slh':boundaries|={'slg','sjv','sjw'}
    if name=='sll':boundaries.add('slj')
    if name=='slm':boundaries.add('slk')
    if name=='slv':boundaries.add('slm')
    boundaries.discard(name)
    for d in doc['declarations']:
        if d['name'] in {m[n] for n in boundaries if n in m}:abstract(d)
    ds={d['name']:d for d in doc['declarations']};seen=set()
    def visit(n):
        if n in seen:return
        seen.add(n)
        for ref in _references(ds[n].get('body')):visit(ref)
    visit(m[name]);doc['declarations']=[d for d in doc['declarations'] if d['name'] in seen]
    if mode=='projection':doc=project(doc,[RS])
    target=next(d for d in doc['declarations'] if d['name']==m[name]);slots=[]
    if mode=='instance':assert len(expose(target,{'forall','exists'}))=={'ei34':2,'slh':3,'sll':3,'slm':3}[name]
    for i,p in enumerate(target['parameters']):
        slot='auxiliaryslot'+chr(97+i);slots.append(slot)
        doc['declarations'].append(dict(kind='primitive',name=slot,parameters=[],result=p['sort']))
    body=call(m[name],*[call(slot) for slot in slots])
    if target['result']=='content':
        doc['declarations'].append(dict(kind='primitive',name='auxiliarycontext',parameters=[],result='situation'))
        body=dict(kind='evaluate',content=body,situation=call('auxiliarycontext'))
    elif target['result']!='truth':
        doc['declarations'].append(dict(kind='primitive',name='jatcapture',parameters=[target['result']],result='truth'))
        body=call('jatcapture',body)
    doc['statements']=[dict(kind='ask',body=body)];return doc,slots

def run(name,args,model,mode='boundary',domain=DOMAIN):
    doc,slots=fixture(name,mode);assert len(args)==len(slots)
    m={n:lambda x=x:x for n,x in CONSTANTS.items()}|{'auxiliarycontext':lambda:'discourse'}|model|{n:lambda x=x:x for n,x in zip(slots,args)}
    h=handlers(doc);h.update({mapping().get(n,n):f for n,f in m.items() if mapping().get(n,n) in h})
    return evaluate_document(doc,individuals=domain,situations=POINTS,primitives=h,max_steps=1500000,memoize_definitions=True,memoize_expressions=True)[0]['value']

def unknowns(check,m,names):
    for n in names:
        try:check(m|{n:forbidden})
        except ValueError as e:assert 'Unknown transverse-visible' in str(e),str(e)
        else:raise AssertionError(('Unknown input accepted',n))

def perturb(check,m,rows,norm=lambda xs:tuple(value(x) for x in xs)):
    count=1;assert check(m)
    for n,rs in rows.items():
        for row in rs:
            assert not check(m|{n:lambda *xs,rs=rs-{row}:norm(xs) in rs}),(n,row);count+=1
            for i in range(len(row)):
                bad=tuple('wrong' if i==j else x for j,x in enumerate(row))
                assert not check(m|{n:lambda *xs,rs=(rs-{row})|{bad}:norm(xs) in rs}),(n,i);count+=1
    unknowns(check,m,rows);return count

def norm_factory(cuts,times):
    # Exact registered cuts only. History fingerprints are finite binding
    # diagnostics, not a proof of equality on all real inputs.
    def norm(xs):
        def one(x):
            if not isinstance(x,FunctionValue):return value(x)
            if x.parameters==('number',):return cuts.read(x)
            if list(x.parameters)==[RS] and x.result==RS:
                return tuple(cuts.read(x(cuts.make(Q(t)))) for t in times)
            forbidden()
        return tuple(one(x) for x in xs)
    return norm

def expose(d,kinds,only_sort=None):
    added=[]
    def walk(node):
        if isinstance(node,list):return [walk(x) for x in node]
        if not isinstance(node,dict):return node
        if node.get('kind') in kinds and (only_sort is None or node['sort']==only_sort):
            added.append(dict(name=node['variable'],sort=node['sort']));return walk(node['body'])
        return {k:walk(v) for k,v in node.items()}
    d['body']=walk(d['body']);d['parameters']+=added
    return added

def exact_numbers():
    cuts,m=numbers();m['bj']=lambda scale,val:cuts.make(scale*cuts.read(val));return cuts,m

def segments(cuts,m):
    c=cuts.make;norm=norm_factory(cuts,());data={'outward':(0,1,Q(18)),'returning':(1,2,Q(9))}
    values={}
    for seg,(a,b,path) in data.items():values[seg]={'wf':'ray','wi':EVENTS[a],'wj':EVENTS[b],'wk':CLOCKS[a],'wl':CLOCKS[b],'wm':PLACES[a],'wn':PLACES[b],'wo':c(Q((5,11,14)[a])),'wp':c(Q((5,11,14)[b])),'wq':c(path)}
    def getter(n):
        def get(seg):
            if seg not in values:forbidden()
            return values[seg][n]
        return get
    m=m|{n:getter(n) for n in values['outward']}
    def axis(f,a,ctx):
        if (f,a,ctx)!=('frame','x','context'):forbidden()
        return 'axis'
    def stamp(e,f,u,ctx):
        if e not in EVENTS or (f,u,ctx)!=('frame','unit','context'):forbidden()
        return c(Q((5,11,14)[EVENTS.index(e)]))
    m|={'zbo':axis,'zbe':stamp}
    rows={'eiscd':{(s,'frame','lengthunit','unit','context') for s in data},'eifw':{(s,'frame','reference',Q(3),'context') for s in data},'eior':{(s,'context') for s in data},'zbw':{('frame','axis','x','context')},'zdw':{('ray',EVENTS[a],EVENTS[b],'axis','frame','context') for a,b,_ in data.values()},'eiyg':{(e,cl,p,'frame',Q(t),'context') for e,cl,p,t in zip(EVENTS,CLOCKS,PLACES,(5,11,14))},'eiyi':{(e,p,'frame','context') for e,p in zip(EVENTS,PLACES)},'eiyj':{(e,'frame','context') for e in EVENTS}}
    m|={n:lambda *xs,rs=rs:norm(xs) in rs for n,rs in rows.items()}
    return m,rows,norm

def prior_model():
    cuts,m=numbers();c=cuts.make;r=cuts.read;coords=dict(zip(TUPLES,((5,0,0,5),(23,0,0,11),(14,0,0,14))))
    def tupleof(e,f,ctx):
        if e not in EVENTS or (f,ctx)!=('frame','context'):forbidden()
        return TUPLES[EVENTS.index(e)]
    def coordinate(t,a):
        if t not in coords or a not in ROLES:forbidden()
        return c(Q(coords[t][ROLES.index(a)]))
    def selected(value):return lambda tr:value if tr=='trial' else forbidden()
    m|={'zb7':lambda:c(Q(1)),'tc':lambda:c(Q(3)),'zdt':lambda:c(Q(12)),'zdz':tupleof,'zc6':coordinate,'bj':lambda scale,val:c(scale*r(val))}
    def divide(a,b):
        if r(b)<=0:forbidden()
        return c(r(a)/r(b))
    m['sje']=divide
    m|={n:selected(value) for n,value in zip(('qc','qd','qh','qe','qf','qg'),('origin','mirror','ray',*EVENTS))}
    m|={n:selected(c(Q(value))) for n,value in zip(('qi','qj','qk'),(10,19,28))}
    fn=FunctionValue((RS,)*4,RS,lambda xp,y,z,t:c(2*r(t)-r(xp)/4));m['zd4']=lambda:fn
    return cuts,m,coords,fn

def relations(m,rows,norm):return m|{n:lambda *xs,rs=rs:norm(xs) in rs for n,rs in rows.items()}

def roundtrip_model():
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

def square_root(cuts):
    def root(light,speed):
        n=cuts.read(light)**2-cuts.read(speed)**2
        if n<0:forbidden()
        a,b=isqrt(n.numerator),isqrt(n.denominator)
        if a*a!=n.numerator or b*b!=n.denominator:forbidden()
        return cuts.make(Q(a,b))
    return root

@lru_cache(None)
def numeric_checks():
    cuts,m=numbers();c=cuts.make;m['sle']=square_root(cuts);count=0
    for V,s,w in ((5,3,4),(13,5,12),(5,0,5)):
        for origin,length,start in ((12,12,5),(-7,Q(3,2),Q(-2,3))):
            middle=Q(start)+Q(length,w);last=middle+Q(length,w);base=list(map(Q,(origin,length,V,s,start,middle,last,w)))
            for slot in (0,1,4,5,6,7):
                for delta in (0,Q(1,4)):
                    xs=base.copy();xs[slot]+=delta
                    expected=(xs[1]>0 and xs[4]<xs[5]<xs[6] and xs[3]>=0 and xs[3]<xs[2] and xs[7]>0 and xs[3]**2+xs[7]**2==xs[2]**2 and xs[7]*(xs[5]-xs[4])==xs[1] and xs[7]*(xs[6]-xs[5])==xs[1])
                    assert run('ei3y',list(map(c,xs)),m)==expected;count+=1
    for xs in ((12,12,5,-3,5,8,11,4),(12,12,5,5,5,8,11,4),(12,12,-5,3,5,8,11,4),(12,0,5,3,5,5,5,4),(12,12,5,3,5,8,11,5),(12,12,5,3,5,8,11,-4),(12,12,5,3,5,8,10,4)):
        assert not run('ei3y',list(map(c,map(Q,xs))),m);count+=1
    args=list(map(c,map(Q,(12,12,5,3,5,8,11,4))));unknowns(lambda mm:run('ei3y',args,mm),m,('sle','ba','bc','bg','bf','shv','sca'))
    unknown=args.copy();unknown[0]=FunctionValue(('number',),'truth',lambda x:x<12)
    try:run('ei3y',unknown,m)
    except ValueError:pass
    else:raise AssertionError('Unknown cut decoded by sampling')
    return dict(cases=count,both_positive_equal_transverse_travel_times_and_Pythagorean_components_checked=True,total_speed_not_transverse_speed=True,zero_speed_allowed_only_in_generic_numeric_comparison=True,unknown_cuts_refused=True,root_oracle_limited_to_exact_retained_rational_roots=True)

@lru_cache(None)
def transverse_trial_checks():
    count=0
    for axis in ('y','z'):
        cuts,m,rows,norm=roundtrip_model();rows.pop('zbv');rows['zef']=rows.pop('zdw');rows['zbw']={('moving','axis',axis,'context')}
        def selected(f,a,ctx):
            if (f,ctx)!=('moving','context') or a not in ('x','y','z'):forbidden()
            return 'axis'
        m=relations(m,rows,norm)|{'zbo':selected};args=['trial','firstclock','secondclock','context',axis]
        count+=perturb(lambda mm:run('ei3w',args,mm),m,rows,norm)
        for other in ('x','z' if axis=='y' else 'y'):assert not run('ei3w',args[:-1]+[other],m);count+=1
        for patch in ({'qd':lambda tr:'origin'},{'qg':lambda tr:'depart'},{'qj':lambda tr:cuts.make(Q(2))},{'yp':lambda:'y'}):assert not run('ei3w',args,m|patch);count+=1
        assert run('ei3w',args,m|{'zbn':forbidden,'zbv':forbidden,'zdw':forbidden,'sgp':forbidden});count+=1
        unknowns(lambda mm:run('ei3w',args,mm),m,('zbo','qc','qd','qe','qf','qg','qh','qi','qj','qk'))
    return dict(cases=count,both_transverse_axes_require_native_roundtrip_and_current_local_readings=True,both_full_parallel_k_paths_and_distinct_axes_required=True,old_origin_and_local_clock_rules_not_used=True)

def trial_model(axis):
    cuts,m,coords,_=prior_model();c=cuts.make;r=cuts.read
    points=((12,2,-3,5),(21,14 if axis=='y' else 2,-3 if axis=='y' else 9,8),(30,2,-3,11));coords.update(zip(TUPLES,points))
    fn=FunctionValue((RS,)*4,RS,lambda x,y,z,t:c(2*r(t)-3*r(x)/8))
    m|={'tc':lambda:c(Q(5)),'zb7':lambda:c(Q(3)),'zd4':lambda:fn,'sle':square_root(cuts)}
    m['te']=lambda tr:'firstclock' if tr=='trial' else forbidden();m['tf']=lambda tr:'secondclock' if tr=='trial' else forbidden()
    for n,t in zip(('qi','qj','qk'),(5,8,11)):m[n]=lambda tr,t=t:c(2*Q(t)+Q(9,8)) if tr=='trial' else forbidden()
    return cuts,m,coords,fn

@lru_cache(None)
def segment_checks():
    cuts,m,coords,fn=trial_model('y');c=cuts.make;r=cuts.read;m,rows,norm=segments(cuts,m);rows.pop('zbw');rows.pop('zdw')
    rows['eifw']={(s,'frame','reference',Q(5),'context') for s in ('outward','returning')}
    rows['eiyg']={(e,cl,p,'frame',Q(t),'context') for e,cl,p,t in zip(EVENTS,CLOCKS,PLACES,(5,8,11))}
    for n,vals in (('wo',{'outward':5,'returning':8}),('wp',{'outward':8,'returning':11}),('wq',{'outward':15,'returning':15})):
        m[n]=lambda seg,vals=vals:c(Q(vals[seg])) if seg in vals else forbidden()
    m['zbe']=lambda e,f,u,ctx:c(Q((5,8,11)[EVENTS.index(e)])) if e in EVENTS and (f,u,ctx)==('frame','unit','context') else forbidden()
    m=relations(m,rows,norm);args=[['outward','ray','depart','reflection',c(Q(15)),'context'],['returning','ray','reflection','arrival',c(Q(15)),'context']]
    check=lambda mm:all(run('ei3x',a,mm) for a in args);count=perturb(check,m,rows,norm)
    for slot in ('wo','wp','wq'):
        for seg in ('outward','returning'):
            old=m[slot];assert not check(m|{slot:lambda s,old=old,seg=seg:c(r(old(s))+(1 if s==seg else 0))});count+=1
    assert check(m|{'zbo':forbidden,'zdw':forbidden,'zef':forbidden,'sbc':forbidden,'shd':forbidden});count+=1
    unknowns(check,m,('wf','wi','wj','wk','wl','wm','wn','wo','wp','wq','zbe','zdz','zc6','tc'))
    return dict(cases=count,both_diagonal_K_segments_keep_geometric_lengths_and_current_local_times=True,K_paths_not_required_parallel_to_k_axes=True,full_path_length_differs_from_transverse_distance=True)

def geometry_model(axis):
    cuts,m,coords,fn=trial_model(axis);c=cuts.make;r=cuts.read;norm=norm_factory(cuts,(5,6,8,11))
    linear=lambda start,x,s:FunctionValue((RS,),RS,lambda t:c(Q(x)+Q(s)*(r(t)-start)))
    y,z=2,-3;my,mz=(14,-3) if axis=='y' else (2,9);vy,vz=(4,0) if axis=='y' else (0,4)
    def history(obj,lo,hi,x,yy,zz,sy,sz):return [obj,'frame','context','lengthunit','unit',c(Q(lo)),c(Q(hi)),linear(lo,x,3),linear(lo,yy,sy),linear(lo,zz,sz)]
    histories=[history('origin',5,11,12,y,z,0,0),history('mirror',5,11,12,my,mz,0,0),history('ray',5,8,12,y,z,vy,vz),history('ray',8,11,21,my,mz,-vy,-vz)]
    rows={'se':{norm(h) for h in histories},'eisb5':{('ray','frame','context')},'cf':{('ray',)},'cg':{('ray','depart','reflection','frame'),('ray','reflection','arrival','frame')},'ch':{('ray','reflection','frame')},'eisca':{('ray','depart','reflection','frame','context'),('ray','reflection','arrival','frame','context')},'zzbu':set(),'zzbv':set()}
    for endpoint,event,t,x,yy,zz in (('origin','depart',5,12,y,z),('mirror','reflection',8,21,my,mz),('origin','arrival',11,30,y,z)):
        rows['zzbu'].add((event,'frame','context','lengthunit','unit',*map(Q,(t,x,yy,zz))))
        for obj in (endpoint,'ray'):rows['zzbv'].add((obj,event,'context'))
    args=['origin','mirror','ray',*EVENTS,'frame','context','lengthunit','unit',*map(c,map(Q,(12,12,5,3,5,8,11,2,-3,4))),axis]
    return cuts,relations(m,rows,norm),rows,norm,args

@lru_cache(None)
def geometry_checks():
    count=0
    for axis in ('y','z'):
        cuts,m,rows,norm,args=geometry_model(axis);c=cuts.make;r=cuts.read
        count+=perturb(lambda mm:run('ei3z',args,mm),m,rows,norm)
        for slot in (10,11,14,15,16,17,18,19):
            bad=args.copy();bad[slot]=c(r(bad[slot])+1);assert not run('ei3z',bad,m);count+=1
        for role in ('x','z' if axis=='y' else 'y'):assert not run('ei3z',args[:-1]+[role],m);count+=1
        for patch in ({'yp':lambda:'y'},{'yn':lambda:axis}):assert not run('ei3z',args,m|patch);count+=1
        try:run('ei3z',args,m|{'zzbg':lambda a,b:r(a)<r(b)},'native_history')
        except ValueError as e:assert 'Cannot finitely quantify' in str(e) or 'Finite function domain' in str(e),str(e)
        else:raise AssertionError('Full trajectories accepted by finite sampling')
    return dict(cases=count,both_axes_native_four_complete_histories_and_six_meetings_bound=True,outbound_and_returning_K_longitudinal_velocity_same_v=True,selected_transverse_velocity_reverses_and_other_component_zero=True,full_real_histories_refused=2,finite_fingerprints_are_only_binding_checks=True)

@lru_cache(None)
def connection_checks():
    count=0
    for axis in ('y','z'):
        cuts,m,coords,fn=trial_model(axis);c=cuts.make;r=cuts.read;norm=norm_factory(cuts,())
        triples=((-3,2,-3),(-3,14 if axis=='y' else 2,-3 if axis=='y' else 9),(-3,2,-3))
        rows={'ei3w':{('trial','firstclock','secondclock','context',axis)},'eizm':{('origin','context'),('mirror','context')},'ei3i':{('trial','context')},'ei3h':{(e,t,*map(Q,xyz),'context') for e,t,xyz in zip(EVENTS,TUPLES,triples)},'ei3z':{('origin','mirror','ray',*EVENTS,'frame','context','lengthunit','unit',*map(Q,(12,12,5,3,5,8,11,2,-3,4)),axis)},'ei3x':{('outward','ray','depart','reflection',Q(15),'context'),('returning','ray','reflection','arrival',Q(15),'context')}}
        args=['trial',axis,'origin','outward','returning',*map(c,map(Q,(12,4,-3,2,-3,5))),'context'];m=relations(m,rows,norm)
        count+=perturb(lambda mm:run('ei32',args,mm),m,rows,norm)
        for slot in range(5,11):
            bad=args.copy();bad[slot]=c(r(bad[slot])+1);assert not run('ei32',bad,m);count+=1
        assert not run('ei32',args[:1]+['x']+args[2:],m);count+=1
        unknowns(lambda mm:run('ei32',args,mm),m,('te','tf','qc','qd','qh','qe','qf','qg','zdz','zc6','tc','zb7','shv','bf','sca'))
    return dict(cases=count,same_trial_point_axis_and_current_coordinates_bound=True,two_geometric_paths_use_total_speed_times_elapsed_time=True)

def model():
    cuts,m,coords,fn=trial_model('y');m['zek']=lambda tr,ctx:cuts.make(Q(12)) if (tr,ctx)==('trial','context') else forbidden();m['zel']=lambda tr,ctx:cuts.make(Q(4)) if (tr,ctx)==('trial','context') else forbidden()
    ordinary=norm_factory(cuts,())
    def norm(xs):return tuple(tuple(cuts.read(x(*(cuts.make(Q(a)) for a in p))) for p in ((1,2,3,4),(2,-1,4,5))) if isinstance(x,FunctionValue) and len(x.parameters)==4 else ordinary((x,))[0] for x in xs)
    return cuts,m,coords,fn,norm

@lru_cache(None)
def trial_checks():
    cuts,m,coords,fn,norm=model();c=cuts.make;r=cuts.read;count=0
    for axis in ('y','z'):
        row=('trial',axis,'origin','outward','returning',*map(Q,(12,4,-3,2,-3,5)),'context');rows={'ei32':{row}};mm=relations(m,rows,norm);args=['trial',axis,'context','outward','returning']
        count+=perturb(lambda mm:run('ei34',args,mm,'instance'),mm,rows,norm)
        for n in ('zek','zel'):
            old=mm[n];assert not run('ei34',args,mm|{n:lambda tr,ctx,old=old:c(r(old(tr,ctx))+1)},'instance');count+=1
        for role in ('x','y','z','time'):
            old=mm['zc6'];assert not run('ei34',args,mm|{'zc6':lambda tup,a,old=old,role=role:c(r(old(tup,a))+(1 if a==role else 0))},'instance');count+=1
        unknowns(lambda mm:run('ei34',args,mm,'instance'),mm,('qc','qe','zdz','zc6','zek','zel','zb7','bf','shv'))
    return dict(cases=count,same_departure_point_coordinates_time_gap_and_component_bound=True,segment_slots_checked_in_exposed_body=True,all_argument_slots_checked_on_exposed_body=True)

@lru_cache(None)
def scope_checks():
    cuts,m,coords,fn,norm=model();c=cuts.make;finger=norm((fn,))[0];domain=('a','b','c')
    rows={'ei3d':{('context','a')},'ei3c':{(finger,'context')},'eiyf':{('a','context')},'eios':{(Q(5),'context')},'zem':{('context',)},'zej':{('a','b','context'),('b','c','context')},'ei34':{('a','b','context'),('b','c','context')}}
    mm=relations(m,rows,norm)|{'ra':lambda:'a','yn':lambda:'a','yo':lambda:'b','yp':lambda:'c'};check=lambda mm:run('ei35',['context'],mm,domain=domain)
    count=perturb(check,mm,rows,norm)
    assert not check(mm|{'yp':lambda:'b'});count+=1
    # A third selected trial also has to pass; an unselected one is irrelevant.
    selected=rows['zej']|{('c','b','context')}
    assert not check(mm|{'zej':lambda *xs:xs in selected});count+=1
    assert check(mm|{'zej':lambda *xs:xs in selected,'ei34':lambda *xs:xs in selected});count+=1
    assert not check(mm|{'zej':lambda *xs:xs in rows['zej']|{('c','a','context')},'ei34':lambda *xs:True});count+=1
    assert not run('ei35',['other'],mm,domain=domain);count+=1
    assert check(mm|{'sbc':forbidden,'sio':forbidden,'sls':forbidden,'sfm':forbidden});count+=1
    unknowns(check,mm,('tc','zb7','sle','zd4'))
    return dict(cases=count,both_axes_nonempty_and_every_selected_trial_required=True,additional_bad_trial_rejected=True,complete_scope_and_current_global_clock_conditions_required=True,native_quantifiers_checked_on_three_distinguishable_individuals=True)

@lru_cache(None)
def calculus_checks():
    cuts,m,coords,fn,norm=model();c=cuts.make;r=cuts.read;count=0
    # Native argument permutations feed both same-point regularity conditions.
    poly=FunctionValue((RS,)*4,RS,lambda x,y,z,t:c(2*r(x)+3*r(y)+5*r(z)+7*r(t)))
    expected=[]
    for axis in ('y','z'):
        values=[]
        for a,b,d,t in ((1,2,3,4),(2,-1,4,5)):
            x,y,z=(b,a,d) if axis=='y' else (d,b,a);values.append(Q(2*x+3*y+5*z+7*t))
        expected.append(tuple(values))
    rows={'slh':{(expected[0],Q(2),Q(7),Q(-3),Q(5),Q(4)),(expected[1],Q(-3),Q(2),Q(7),Q(5),Q(4))}}
    mm=relations(m,rows,norm);args=[poly,*map(c,map(Q,(7,2,-3,5,4)))];count+=perturb(lambda mm:run('slj',args,mm),mm,rows,norm)
    finger=norm((poly,))[0];point=(finger,*map(Q,(7,2,-3,5,2,7)))
    rows={'slg':{(finger,*map(Q,(7,2,-3,5,4,Q(1,2))))},'sjv':{point},'sjw':{point}};mm=relations(m,rows,norm)
    args=[poly,*map(c,map(Q,(7,2,-3,5,4,Q(1,2),2,7)))];count+=perturb(lambda mm:run('slh',args,mm,'instance'),mm,rows,norm)
    # For these explicitly quadratic fixtures central differences are exact
    # derivatives. This oracle is not a general real differentiation procedure.
    for by,bz,y,z in ((0,0,2,-3),(1,0,2,-3),(0,1,2,-3),(1,1,2,-3),(1,1,0,0)):
        qfn=FunctionValue((RS,)*4,RS,lambda x,y,z,t,by=by,bz=bz:c(r(x)**2+by*r(y)**2+bz*r(z)**2+2*r(t)**2))
        seen=[]
        def derivative(domain,f,p,value):
            seen.append((r(p),r(value)))
            return domain(p) and r(value)==(r(f(c(r(p)+1)))-r(f(c(r(p)-1))))/2
        args=[qfn,*map(c,map(Q,(7,y,z,5)))];actual=run('slk',args,m|{'sjs':derivative})
        assert actual==(by*y==0 and bz*z==0);assert seen==[(Q(y),Q(0)),(Q(z),Q(0))];count+=2
    return dict(cases=count,native_y_z_permutations_and_same_point_regularities_bound=True,zero_partial_is_not_local_constancy=True,both_same_tau_slices_and_zero_values_required=True,quadratic_derivative_oracle_is_not_general_calculus_proof=True)

@lru_cache(None)
def midpoint_checks():
    cuts,m,coords,fn,norm=model();c=cuts.make;r=cuts.read;count=0
    for axis in ('y','z'):
        for by,bz,curved in ((0,0,False),(1,0,False),(0,1,False),(0,0,True)):
            calls=[]
            def original(x,y,z,t):
                vals=tuple(map(r,(x,y,z,t)));calls.append(vals);a,b,d,tt=vals
                return c(2*(tt**2 if curved else tt)-3*a/8+by*b+bz*d)
            # Permutations themselves are tested natively in calculus_checks.
            f=FunctionValue((RS,)*4,RS,lambda a,b,d,t:original(b,a,d,t) if axis=='y' else original(d,b,a,t))
            args=[f,*map(c,map(Q,((2,7,-3,5,4,12) if axis=='y' else (-3,2,7,5,4,12))))]
            actual=run('slf',args,m);assert actual==(not curved and (by==0 if axis=='y' else bz==0));count+=1
            expected={(Q(7),Q(2),Q(-3),Q(5)),(Q(7),Q(14 if axis=='y' else 2),Q(-3 if axis=='y' else 9),Q(8)),(Q(7),Q(2),Q(-3),Q(11))}
            assert set(calls)==expected;count+=1
    return dict(cases=count,same_tau_three_arguments_and_equal_transverse_elapsed_times_checked=True,changed_y_or_z_and_nonlinear_time_not_silently_accepted=True)

@lru_cache(None)
def global_checks():
    cuts,m,coords,fn,norm=model();c=cuts.make;finger=norm((fn,))[0];count=0
    rows={'ei35':{('context',)},'sll':{(finger,Q(5),Q(4))}};mm=relations(m,rows,norm);count+=perturb(lambda mm:run('ei37',[],mm),mm,rows,norm)
    for truth in (False,True):assert run('ei36',[],m|{'ei35':lambda ctx,truth=truth:truth})==truth;count+=1
    for name,inner,extra in (('sll','slj',[c(Q(4))]),('slm','slk',[])):
        row=(finger,Q(7),Q(2),Q(-3),Q(5),*([Q(4)] if extra else []));rows={inner:{row}};mm=relations(m,rows,norm)
        args=[fn,c(Q(5)),*extra,*map(c,map(Q,(7,2,-3)))];count+=perturb(lambda mm:run(name,args,mm,'instance'),mm,rows,norm)
    rows={'slm':{(finger,Q(5))}};mm=relations(m,rows,norm);count+=perturb(lambda mm:run('slv',[],mm),mm,rows,norm)
    refusal={}
    for name,args in (('sll',[fn,c(Q(5)),c(Q(4))]),('slm',[fn,c(Q(5))]),('slh',[fn,*map(c,map(Q,(7,2,-3,5,4)))]),('slg',[fn,*map(c,map(Q,(7,2,-3,5,4,1)))])):
        try:run(name,args,m)
        except ValueError as e:assert 'Cannot finitely quantify' in str(e),str(e);refusal[name]=str(e)
        else:raise AssertionError('Real neighborhood or all-space scope sampled')
    return dict(cases=count,same_candidate_departure_time_and_transverse_root_in_premise=True,all_three_spatial_axes_and_both_partials_retained=True,real_quantification_refused=refusal)

@lru_cache(None)
def presentation_checks():
    count=0
    for name,rows in (
      ('ei4a',{'uh':{('notice','author','ei36','section','discourse')},'zei':{('notice','author','section','discourse')}}),
      ('ei4d',{'zc':{('consequence','author','ei37','slv','section','discourse')},'zep':{('consequence','author','earlier','section','discourse')}}),
      ('ei4c',{'eir3':{('notice','author','paper','ei4b','discourse')},'ue':{('previous','notice','discourse')}}),
      ('ei4f',{'eir3':{('consequence','author','paper','ei4e','discourse')},'ue':{('notice','consequence','discourse')}})):
        m={n:relation(rs) for n,rs in rows.items()};count+=perturb(lambda mm:run(name,[],mm),m,rows)
        assert run(name,[],m|{n:forbidden for n in ('ei35','ei36','ei37','slv','slm')});count+=1
    return dict(cases=count,attention_condition_analogy_and_two_partial_consequence_attributed=True,same_author_section_paper_and_source_order_preserved=True,quoted_claim_not_executed_as_proof=True)

def test_numeric_checks():
    assert numeric_checks()['cases']>0


def test_transverse_trial_checks():
    assert transverse_trial_checks()['cases']>0


def test_segment_checks():
    assert segment_checks()['cases']>0


def test_geometry_checks():
    assert geometry_checks()['cases']>0


def test_connection_checks():
    assert connection_checks()['cases']>0


def test_trial_checks():
    assert trial_checks()['cases']>0


def test_scope_checks():
    assert scope_checks()['cases']>0


def test_calculus_checks():
    assert calculus_checks()['cases']>0


def test_midpoint_checks():
    assert midpoint_checks()['cases']>0


def test_global_checks():
    assert global_checks()['cases']>0


def test_presentation_checks():
    assert presentation_checks()['cases']>0


def native_run(doc,h):
    return [r['value'] for r in evaluate_document(doc,individuals=tuple(set(check.BASE.values())|{'other'}),situations=check.SITUATIONS,primitives=h)]

def context(doc,b):return handlers(doc)|{check.vocabulary()._symbols[n]:f for n,f in check.context_handlers(b).items()}


def test_source_backprojection_and_preserved_specialist_contracts():
    assert check.backprojection(check.restored()['document'])==check.source_excerpt()
    b=check.bridge();assert b['source_statement_indices']==[120,121]
    assert list(b['source_units'])==['einstein-1905:u0059','einstein-1905:u0060','einstein-1905:u0061']
    assert [r['id'] for r in b['math']]==['M0106','M0107','M0108','M0109','M0110']
    assert len(b['text_boundaries']['sentences']['zeo']['tokens'])==35
    assert b['text_boundaries']['spans']=={'zen':['zeo',13,33]}
    assert len(check.NEW_DEFINITIONS)==28
    assert check.document()['statements'][:90]==check.previous.document()['statements']
    prior=check.previous.vocabulary().document();current=check.vocabulary().document()
    for field in ('entries','compounds','definitions','primitives'):
        assert all(current[field][n]==d for n,d in prior[field].items())
    assert len(check.vocabulary()._words)==765
    ds={d['name']:d for d in check.source_excerpt()['declarations']}
    for old,new in profile.SOURCE_RELATIONS.items():
        assert profile.CONTRACTS[new]['parameters']==ds[old]['parameters']
        assert profile.CONTRACTS[new]['result']==ds[old]['result']


def test_axis_adaptation_and_diagonal_segments_preserve_other_native_conditions():
    ds={d['name']:deepcopy(d) for d in check.restored()['document']['declarations']};m=mapping()
    before=ds[m['ei3f']];after=ds[m['ei3w']]
    axis=after['parameters'][-1]['name']
    def undo(n):
        if isinstance(n,list):return [undo(x) for x in n]
        if not isinstance(n,dict):return n
        if n.get('kind')=='variable' and n['name']==axis:return call(m['yn'])
        return {k:undo(v) for k,v in n.items()}
    assert after['parameters'][:-1]==before['parameters']
    assert undo(after['body']['arguments'][1])==before['body']
    def conjuncts(n):
        return [x for a in n['arguments'] for x in conjuncts(a)] if n['kind']=='and' else [n]
    before=ds[m['ei2m']];after=ds[m['ei3x']]
    removed=[n for n in conjuncts(before['body']) if n.get('symbol') in (m['zbw'],m['zdw'])]
    assert len(removed)==2
    assert after['parameters']==before['parameters']
    assert conjuncts(after['body'])==[n for n in conjuncts(before['body']) if n not in removed]


def test_two_native_segment_witnesses_distinguish_each_slot():
    cuts,m=numbers();c=cuts.make;norm=norm_factory(cuts,())
    # Small domain for the two binders. Physical relations remain boundaries;
    # this checks binding only, not the possibility of a complete trial.
    m|={n:lambda:'a' for n in ('ra','yn','yo','yp','zc7')}
    m|={'zb7':lambda:c(3),'qc':lambda trial:'b','qe':lambda trial:'a',
        'zdz':lambda e,f,ctx:'a','zc6':lambda tup,axis:c(2),
        'zek':lambda trial,ctx:c(12),'zel':lambda trial,ctx:c(4)}
    for outward in ('a','b'):
        for returning in ('a','b'):
            row=('a','b','b',outward,returning,*map(Q,(12,4,-4,2,2,2)),'context')
            mm=m|{'ei32':lambda *xs,row=row:norm(xs)==row}
            assert run('ei34',['a','b','context'],mm,domain=('a','b'))
            for slot in (3,4):
                wrong=list(row);wrong[slot]='absent'
                assert not run('ei34',['a','b','context'],m|{'ei32':lambda *xs,row=tuple(wrong):norm(xs)==row},domain=('a','b'))
    with pytest.raises(ValueError):run('ei34',['a','b','context'],m|{'ei32':forbidden},domain=('a','b'))


def test_sentence_and_attention_span_references_preserve_scope():
    doc=deepcopy(check.restored()['document']);b=check.BASE;n=check.names()
    for old in (*check.SENTENCES,*check.SPANS):
        trial=deepcopy(doc)
        trial['declarations'].append(dict(kind='primitive',name='transversecapture',parameters=['individual'],result='truth'))
        trial['statements']=[dict(kind='ask',body=call('transversecapture',call(n[old])))]
        assert native_run(trial,context(trial,b)|dict(transversecapture=lambda x:x==b[old]))==[True]
    h=check.context_handlers(b);key=[b['eirf'],b['zeo'],13,b['zeo'],33,b['ri']]
    assert h['sentencetokenspanreference'](*key)==b['zen']
    for slot in range(6):
        bad=key.copy();bad[slot]='unknown'
        with pytest.raises(ValueError):h['sentencetokenspanreference'](*bad)
    assert h['sentencetokenspanreference'](b['eirf'],b['zeg'],21,b['zeg'],32,b['ri'])==b['zeh']


def test_whole_attribution_keeps_condition_analogy_and_two_formulas():
    doc=deepcopy(check.restored()['document']);doc['statements']=doc['statements'][90:92];b=check.BASE
    rows={'eir3':{(b[node],b['rd'],b['eirf'],message,b['ri']) for node,message in (('zen','ei4b'),('zeo','ei4e'))},
          'ue':{(b[first],b[last],b['ri']) for first,last in (('zeh','zen'),('zen','zeo'))}}
    h=context(doc,b)|{mapping()[n]:relation(rs) for n,rs in rows.items()}
    assert native_run(doc,h)==[True,True]
    for n,rs in rows.items():
        for row in rs:
            result=native_run(doc,h|{mapping()[n]:relation(rs-{row})})
            assert result.count(False)==1 and result.count(True)==1


def test_root_fixture_refuses_unregistered_cuts_and_irrational_results():
    cuts,m=numbers();c=cuts.make;root=square_root(cuts)
    with pytest.raises(ValueError):root(c(2),c(1))
    with pytest.raises(ValueError):root(c(1),c(2))
    with pytest.raises(ValueError,match='not constructed'):root(cut(5),c(3))
