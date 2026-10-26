from copy import deepcopy
from itertools import product
from fractions import Fraction as Q
from functools import lru_cache
import json,re
import pytest
from noema.constructed_semantics import Content,FunctionValue,SequenceValue,DescriptionValue,QuestionValue,evaluate_document
from noema.meaning_catalog import _references
from scripts import check_einstein_arbitrary_start_visible as check
from scripts import arbitrary_start_visible_profile as profile
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


def forbidden(*args):raise ValueError('Unknown arbitrary-start-visible input')
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

@lru_cache(None)
def fixture(name,mode='boundary'):
    doc=deepcopy(check.restored()['document']);m=mapping()
    boundaries=NUM|set(CONSTANTS)|{d['name'] for d in check.source_excerpt()['declarations'] if d['kind']=='primitive'}
    boundaries|={'bj','sjd'}
    if name in ('ei26','ei27','ei3a'):boundaries|={'eiyx','shh'}
    if name=='ei3b':boundaries|={'ei3a','ei26','ei27'}
    if name=='ei3c':boundaries|={'ei3b','eiyf','eiyx','eiyg'}
    if name=='ei3d':boundaries|={'eivf','eivg','eivl','eiwn','eixs','eipw','eigy','eivv'}
    if name=='ei3e':boundaries|={'eifw','eior','eiyg','eiyi','eiyj'}
    if name=='ei3f':boundaries|={'eiz7','qo'}
    if name=='ei3g':boundaries|={'se'}
    if name in ('ei3h','ei3i'):boundaries.add('eiyx')
    if name=='ei3j':boundaries|={'ei3f','eizm','ei3i','ei3h','ei3g','ei3e'}
    if name=='ei3k':boundaries|={'ei3d','ei3c','eiyf','eios','ei3j'}
    if name=='ei3l':boundaries.add('eizm')
    if name=='ei3m':boundaries|={'ei3l','ei3k','skl'}
    if name=='ei3n':boundaries|={'ei3l','ei3m'}
    if name=='ei3o':boundaries|={'ei3c','ei3n'}
    if name=='ei3p':boundaries|={'ei2w','ei3o'}
    if name=='skk':boundaries.add('skc')
    if name=='skl':boundaries|={'skk','sjv','sjw'}
    if name=='skm':boundaries.add('sjw')
    if name=='skn':boundaries.add('skm')
    if name=='skv':boundaries.add('skn')
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
    if mode=='instance':
        if name in ('ei3b','ei3c'):assert len(expose(target,{'forall'}))=={'ei3b':2,'ei3c':5}[name]
        elif name in ('ei3k','ei3l'):assert len(expose(target,{'exists'}))=={'ei3k':4,'ei3l':1}[name]
        else:assert len(expose(target,{'forall','exists'},RS))=={'ei3o':3,'skl':3,'skm':2,'skn':3}[name]
    elif name=='ei3k' and mode.startswith('witness'):
        # Keep one native individual binder; instantiate the other witnesses.
        selected=int(mode[-1]);counter=[0];added=[]
        def witness(node):
            if isinstance(node,list):return [witness(x) for x in node]
            if not isinstance(node,dict):return node
            if node.get('kind')=='exists':
                index=counter[0];counter[0]+=1
                if index!=selected:
                    added.append(dict(name=node['variable'],sort=node['sort']))
                    return witness(node['body'])
            return {k:witness(v) for k,v in node.items()}
        target['body']=witness(target['body']);target['parameters']+=added
        assert counter[0]==4 and len(added)==3 and selected in (0,1,2)
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
        except ValueError as e:assert 'Unknown arbitrary-start-visible' in str(e),str(e)
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

def model():
    cuts,m=numbers();c=cuts.make;r=cuts.read
    fn=FunctionValue((RS,)*4,RS,lambda x,y,z,t:c(-r(x)/4+3*r(y)+7*r(z)+2*r(t)))
    m|={'tc':lambda:c(Q(3)),'zb7':lambda:c(Q(1)),'zd4':lambda:fn,'bj':lambda scale,val:c(scale*r(val))}
    def inverse(x):
        if r(x)<=0:forbidden()
        return c(1/r(x))
    m['sjd']=inverse
    m['qe']=lambda tr:'depart' if tr=='trial' else forbidden();m['zdz']=lambda e,f,ctx:'tuple' if (e,f,ctx)==('depart','frame','context') else forbidden();m['zc6']=lambda tup,role:c(Q(5)) if (tup,role)==('tuple','time') else forbidden()
    ordinary=norm_factory(cuts,())
    def norm(xs):return tuple(tuple(r(x(*(c(Q(a)) for a in point))) for point in ((0,0,0,5),(1,2,3,4))) if isinstance(x,FunctionValue) and len(x.parameters)==4 else ordinary((x,))[0] for x in xs)
    return cuts,m,fn,norm

def relations(m,rows,norm):return m|{n:lambda *xs,rs=rs:norm(xs) in rs for n,rs in rows.items()}

@lru_cache(None)
def connection_checks():
    cuts,m,fn,norm=model();c=cuts.make;xyz=tuple(map(Q,(7,2,-3,5)));finger=norm((fn,))[0]
    rows={'ei3l':{('point',*xyz,ctx) for ctx in ('context','other')},'ei3k':{('trial','point',*xyz,'other')},'skl':{(finger,*xyz[:3],Q(3),Q(1),xyz[3])}}
    m=relations(m,rows,norm);args=['trial','point',*map(c,xyz),'context','other'];check=lambda mm:run('ei3m',args,mm)
    count=perturb(check,m,rows,norm)
    for slot in range(2,6):
        bad=args.copy();bad[slot]=c(cuts.read(bad[slot])+1);assert not run('ei3m',bad,m);count+=1
    assert not run('ei3m',args[:-2]+['other','context'],m);count+=1
    unknowns(check,m,('zd4','tc','zb7'))
    assert check(m|{'sko':forbidden,'skr':forbidden,'sio':forbidden,'shd':forbidden,'sgp':forbidden,'sbc':forbidden});count+=1
    return dict(cases=count,same_point_coordinates_time_and_function_in_both_contexts=True,current_full_trial_and_shifted_local_differentiability_required=True,old_physical_bindings_not_used=True)

@lru_cache(None)
def choice_checks():
    cuts,m,fn,norm=model();c=cuts.make;domain=('a','b');xyz1=tuple(map(Q,(2,3,4,5)));xyz2=tuple(map(Q,(7,-2,1,5)))
    places={('a',*xyz1,'context'),('b',*xyz2,'context')};available={('a','a','context'),('a','b','context')}
    outcomes={('a','a','context','other'),('a','b','context','discourse')};success={('a','a',*xyz1,'context','other'),('b','b',*xyz2,'context','discourse')}
    base=relations(m,{'ei3l':places,'zec':available,'zed':outcomes,'ei3m':success},norm)|{'zee':lambda:'a'}
    check=lambda mm:[run('ei3n',[*map(c,xyz),'context'],mm,domain=domain) for xyz in (xyz1,xyz2)]
    count=0
    scenarios={
      'baseline':({},[True,True]),
      'extra_failing_outcome':({'zed':lambda *xs:xs in outcomes|{('a','a','context','discourse')}},[True,True]),
      'no_available_trial':({'zec':lambda *xs:False},[False,False]),
      'no_possible_result':({'zed':lambda *xs:False},[False,False]),
      'only_first_point':({'ei3m':lambda *xs:norm(xs) in {('a','a',*xyz1,'context','other')}},[True,False]),
      'different_trial_success':({'ei3m':lambda *xs:norm(xs) in {('b','a',*xyz1,'context','other'),('a','b',*xyz2,'context','discourse')}},[False,False]),
      'different_point_success':({'ei3m':lambda *xs:norm(xs) in {('a','b',*xyz1,'context','other'),('b','a',*xyz2,'context','discourse')}},[False,False]),
      'wrong_actor':({'zee':lambda:'b'},[False,False]),
      'baseline_not_a_success':({'ei3m':lambda *xs:norm(xs) in {('a','a',*xyz1,'context','context'),('b','b',*xyz2,'context','context')}},[False,False]),
      'missing_baseline_point':({'ei3l':lambda *xs:norm(xs) in {('a',*xyz1,'context')}},[True,False]),
    }
    for patch,expected in scenarios.values():assert check(base|patch)==expected;count+=2
    unknowns(lambda mm:run('ei3n',[*map(c,xyz1),'context'],mm,domain=domain),base,('zee','zec','zed','ei3m','ei3l'))
    # Another available plan can serve the same point; no point-to-plan identity rule.
    swapped=relations(base,{'zed':{('a','b','context','other'),('a','a','context','discourse')},'ei3m':{('b','a',*xyz1,'context','other'),('a','b',*xyz2,'context','discourse')}},norm)
    assert check(swapped)==[True,True];count+=2
    return dict(cases=count,native_pointwise_existence_and_possible_outcome_binding=True,different_points_can_choose_different_trials=True,possibility_not_actual_execution_or_all_outcome_guarantee=True)

@lru_cache(None)
def shift_checks():
    cuts,m,fn,norm=model();c=cuts.make;r=cuts.read;count=0
    polynomial=FunctionValue((RS,)*4,RS,lambda x,y,z,t:c(r(x)**2+2*r(y)+3*r(z)+4*r(t)))
    probes=((0,0,0,5),(1,0,0,5),(0,1,0,5),(0,0,1,5),(0,0,0,6))
    def nearby(f,V,s,t,radius):return tuple(r(a) for a in (V,s,t,radius))==(3,1,5,Q(1,2)) and tuple(r(f(*(c(Q(a)) for a in p))) for p in probes)==(42,47,44,45,46)
    args=[polynomial,*map(c,map(Q,(2,3,4,3,1,5,Q(1,2))))];mm=m|{'skc':nearby}
    assert run('skk',args,mm);count+=1
    for slot in range(1,8):
        bad=args.copy();bad[slot]=c(r(bad[slot])+1);assert not run('skk',bad,mm);count+=1
    wrong=FunctionValue((RS,)*4,RS,lambda x,y,z,t:c(r(x)**2+2*r(y)+3*r(z)+4*r(t)+1))
    assert not run('skk',[wrong,*args[1:]],mm);count+=1
    unknowns(lambda mm:run('skk',args,mm),mm,('skc','bd'))
    return dict(cases=count,native_spatial_shift_preserves_time_and_function_values=True,all_three_offsets_and_local_neighborhood_arguments_distinguished=True,finite_fingerprints_not_neighborhood_proof=True)

@lru_cache(None)
def derivative_checks():
    cuts,m,fn,norm=model();c=cuts.make;r=cuts.read;finger=norm((fn,))[0]
    args=[fn,*map(c,map(Q,(7,2,-3,3,1,5,Q(1,2),Q(-1,4),2)))]
    point=(finger,Q(7),Q(2),Q(-3),Q(5),Q(-1,4),Q(2))
    rows={'skk':{(finger,Q(7),Q(2),Q(-3),Q(3),Q(1),Q(5),Q(1,2))},'sjv':{point},'sjw':{point}}
    mm=relations(m,rows,norm);count=perturb(lambda mm:run('skl',args,mm,'instance'),mm,rows,norm)
    # A quadratic solution of the local coefficient equation has different
    # derivatives at different points. This fixture is not a whole light model.
    quadratic=FunctionValue((RS,)*4,RS,lambda x,y,z,t:c((r(t)-r(x)/8)**2+3*r(y)+7*r(z)))
    values=[]
    for x,y,z,t in ((0,2,-3,5),(7,2,-3,5),(-2,1,4,3)):
        u=Q(t)-Q(x,8);px=-u/4;pt=2*u;values.append((px,pt))
        def partials(f,xx,yy,zz,tt,a,b):
            at=lambda h,k:r(f(c(r(xx)+h),yy,zz,c(r(tt)+k)))
            return r(a)==(at(1,0)-at(-1,0))/2 and r(b)==(at(0,1)-at(0,-1))/2
        qargs=[quadratic,*map(c,map(Q,(x,y,z,3,1,t,px,pt)))];qm=m|{'sjw':partials}
        assert run('skm',qargs,qm,'instance');count+=1
        bad=qargs.copy();bad[-2]=c(px+1);assert not run('skm',bad,qm,'instance');count+=1
        if x!=0:
            bad=qargs.copy();bad[-2:]=[c(values[0][0]),c(values[0][1])];assert not run('skm',bad,qm,'instance');count+=1
    assert len(set(values))==3
    return dict(cases=count,same_function_point_and_partials_in_neighborhood_and_derivative_conditions=True,each_point_has_its_own_derivative_values=True,origin_candidates_not_reused_as_global_constants=True,quadratic_central_differences_are_fixture_bindings_not_general_derivative_proofs=True)

@lru_cache(None)
def scope_checks():
    cuts,m,fn,norm=model();c=cuts.make;r=cuts.read;finger=norm((fn,))[0];xyz=tuple(map(Q,(7,2,-3)))
    rows={'ei3c':{(finger,'context')},'ei3n':{(*xyz,Q(5),'context')}};mm=relations(m,rows,norm)
    args=[c(Q(5)),'context',*map(c,xyz)];count=perturb(lambda mm:run('ei3o',args,mm,'instance'),mm,rows,norm)
    for speed in (0,-1,3,4):assert not run('ei3o',args,mm|{'zb7':lambda speed=speed:c(Q(speed))},'instance');count+=1
    whole={'ei2w':{()},'ei3o':{(Q(5),'context')}};mm=relations(m,whole,norm);count+=perturb(lambda mm:run('ei3p',[],mm),mm,whole,norm)
    unknowns(lambda mm:run('ei3p',[],mm),mm,('qe','zdz','zc6'))
    rows={'skm':{(finger,*xyz,Q(3),Q(1),Q(5))}};mm=relations(m,rows,norm)
    args=[fn,c(Q(3)),c(Q(1)),c(Q(5)),*map(c,xyz)];count+=perturb(lambda mm:run('skn',args,mm,'instance'),mm,rows,norm)
    rows={'skn':{(finger,Q(3),Q(1),Q(5))}};mm=relations(m,rows,norm);count+=perturb(lambda mm:run('skv',[],mm),mm,rows,norm)
    refusal={}
    for name,args in (('ei3o',[c(Q(5)),'context']),('skl',[fn,*map(c,map(Q,(7,2,-3,3,1,5)))]),('skm',[fn,*map(c,map(Q,(7,2,-3,3,1,5)))]),('skn',[fn,*map(c,map(Q,(3,1,5)))])):
        try:run(name,args,m|{'ei3c':lambda *xs:True})
        except ValueError as e:assert 'Cannot finitely quantify' in str(e);refusal[name]=str(e)
        else:raise AssertionError('Finite evaluation accepted all real spatial or derivative values')
    return dict(cases=count,all_three_spatial_axes_and_same_time_preserved=True,previous_origin_premise_and_same_full_tau_binding_retained=True,real_quantification_refused=refusal)

@lru_cache(None)
def presentation_checks():
    count=0
    for name,rows in (
     ('ei3q',{'uh':{('notice','author','ei3p','section','discourse')},'zei':{('notice','author','section','discourse')}}),
     ('ei3t',{'zc':{('consequence','author','ei3p','skv','section','discourse')}}),
     ('ei3s',{'eir3':{('notice','author','paper','ei3r','discourse')},'ue':{('previous','notice','discourse')}}),
     ('ei3v',{'eir3':{('consequence','author','paper','ei3u','discourse')},'ue':{('notice','consequence','discourse')}})):
        m={n:relation(rs) for n,rs in rows.items()};count+=perturb(lambda mm:run(name,[],mm),m,rows)
        assert run(name,[],m|{n:forbidden for n in ('ei3p','skv','ei3o','skn')});count+=1
    return dict(cases=count,notice_possible_choice_and_same_equation_consequence_connected=True,author_section_source_order_and_nonexecution_of_quoted_content_preserved=True)

@lru_cache(None)
def correspondence_checks():
    # Two individuals distinguish every quantifier slot without a large product.
    domain=('a','b');ctx='other';base={'zc4':lambda e:e=='a','eiyx':lambda e,t,f,c:(e,t,f,c) in {('a','a','a',ctx),('a','b','b',ctx)},'shh':lambda a,b:a==b,'ra':lambda:'a','zbm':lambda:'b'}
    assert run('ei3a',[ctx],base,domain=domain);count=1
    for missing in (('a','a','a',ctx),('a','b','b',ctx)):
        good={('a','a','a',ctx),('a','b','b',ctx)}-{missing}
        assert not run('ei3a',[ctx],base|{'eiyx':lambda *xs:xs in good},domain=domain);count+=1
    assert not run('ei3a',['context'],base,domain=domain);count+=1
    assert not run('ei3a',[ctx],base|{'zc4':lambda e:False},domain=domain);count+=1
    assert not run('ei3a',[ctx],base|{'eiyx':lambda e,t,f,c:c==ctx},domain=domain);count+=1
    for first in domain:
        for second in domain:
            assert run('ei26',[first,second,ctx],base,domain=domain)==((first,second)==('a','b'));count+=1
    for frame in domain:
        for tup in domain:
            assert run('ei27',[tup,frame,ctx],base,domain=domain)==(tup==frame);count+=1
    return dict(cases=count,native_same_event_graph_and_both_complete_coordinate_ranges=True,alternative_context_not_fixed_to_baseline=True,missing_and_nonunique_coordinates_rejected=True)

def global_model():
    cuts,m=numbers();c=cuts.make;r=cuts.read;norm=norm_factory(cuts,());ctx='other'
    # Eager Boolean evaluation also visits explicitly known non-coordinate
    # fixture individuals before reaching the real-domain refusal. Only a/b
    # belong to eiyx; these extra cells do not assert coordinate validity.
    coords={t:(3,4,5,6) for t in DOMAIN};coords.update(a=(5,0,0,5),b=(8,1,2,10));roles=('x','y','z','time')
    def coordinate(t,a):
        if t not in coords or a not in roles:forbidden()
        return c(Q(coords[t][roles.index(a)]))
    fn=FunctionValue((RS,)*4,RS,lambda x,y,z,t:c(2*r(t)-r(x)/4))
    m|={'zb7':lambda:c(Q(1)),'zc6':coordinate,'zbi':lambda f,g,lu,tu,ct:c(Q(1)) if (f,g,lu,tu,ct)==('frame','moving','lengthunit','unit',ctx) else forbidden()}
    rows={'ei3a':{(ctx,)},'ei27':{('a','frame',ctx),('b','moving',ctx)},'ei26':{('a','b',ctx)}}
    return cuts,relations(m,rows,norm),fn,norm,rows

@lru_cache(None)
def global_clock_checks():
    cuts,m,fn,norm,rows=global_model();c=cuts.make;r=cuts.read;ctx='other';count=0
    # Expose the native quantified body; constants retain distinct typed values.
    # Correspondence scope itself is tested natively on two individuals above.
    for first in ('a','b'):
        for second in ('a','b'):
            assert run('ei3b',[fn,ctx,first,second],m,'instance');count+=1
    args=[fn,ctx,'a','b'];check=lambda mm:run('ei3b',args,mm,'instance')
    assert not check(m|{'zb7':lambda:c(Q(2))});count+=1
    assert not check(m|{'ei3a':lambda *xs:False});count+=1
    old=m['zc6'];assert not check(m|{'zc6':lambda tup,role:c(r(old(tup,role))+(1 if (tup,role)==('b','time') else 0))});count+=1
    unknowns(check,m,('zc6','zbi','zb7','ba','sca','bf','shv'))
    rows={'eiyf':{('moving',ctx)},'zc4':{('a',)},'eiyx':{('a','a','frame',ctx)},'zcz':{('a','moving',ctx)},'zbz':{('moving','b',ctx)},'cb':{('b','a','moving'),('a','a','moving')},'eiyg':{('a','b','a','moving',Q(10),ctx)}}
    mm=relations(m,rows,norm)|{'ei3b':lambda f,ct:ct==ctx and r(f(c(Q(1)),c(Q(0)),c(Q(0)),c(Q(5))))==Q(39,4)}
    local=lambda reading:[fn,ctx,'a','b','a','a',c(Q(reading))]
    for reading in (10,11):assert run('ei3c',local(reading),mm,'instance');count+=1
    assert not run('ei3c',local(11),mm|{'eiyg':lambda e,cl,p,f,val,ct:(e,cl,p,f,ct)==('a','b','a','moving',ctx) and r(val) in (10,11)},'instance');count+=1
    assert not run('ei3c',local(10),mm|{'eiyg':lambda *xs:False},'instance');count+=1
    assert not run('ei3c',local(10),mm|{'eiyf':lambda *xs:False},'instance');count+=1
    assert not run('ei3c',local(10),mm|{'ei3b':lambda *xs:False},'instance');count+=1
    for name,args in (('ei3c',[fn,ctx]),('ei3k',['a','b',*map(c,map(Q,(7,2,-3,5))),ctx])):
        try:run(name,args,mm)
        except ValueError as e:assert 'Cannot finitely quantify' in str(e)
        else:raise AssertionError('Full real-valued quantifier accepted by finite evaluator')
    return dict(cases=count,all_candidate_clock_values_required_and_spurious_readings_rejected=True,full_real_clock_and_trial_quantification_refused=True,instances_are_binding_checks_only=True)

@lru_cache(None)
def trial_checks():
    cuts,m,rows,norm=trial_model();rows.pop('zbv');rows['zef']=rows.pop('zdw');m=relations(m,rows,norm)
    check=lambda mm:run('ei3f',['trial','firstclock','secondclock','context'],mm)
    count=perturb(check,m,rows,norm)
    assert check(m|{'zbn':forbidden,'zbv':forbidden,'zdw':forbidden,'sgp':forbidden});count+=1
    for patch in ({'qg':lambda tr:'depart'},{'qd':lambda tr:'origin'},{'qj':lambda tr:cuts.make(Q(2))}):assert not check(m|patch);count+=1
    unknowns(check,m,('qc','qd','qe','qf','qg','qh','qi','qj','qk','zbo','bg'))
    return dict(cases=count,native_roundtrip_clock_roles_sync_scope_and_current_local_times_preserved=True,departure_not_required_to_be_frame_origin=True,both_full_parallel_paths_required=True)

def translated_model():
    cuts,m,coords,_=prior_model();c=cuts.make;r=cuts.read
    coords.update(tuplea=(12,2,-3,5),tupleb=(30,2,-3,11),tuplec=(21,2,-3,14))
    fn=FunctionValue((RS,)*4,RS,lambda x,y,z,t:c(2*r(t)-r(x)/4+3*r(y)+7*r(z)))
    m['zd4']=lambda:fn
    for n,val in zip(('qi','qj','qk'),(Q(-27,4),Q(9,4),Q(45,4))):m[n]=lambda tr,val=val:c(val) if tr=='trial' else forbidden()
    m['te']=lambda tr:'firstclock' if tr=='trial' else forbidden();m['tf']=lambda tr:'secondclock' if tr=='trial' else forbidden()
    return cuts,m,coords,fn

@lru_cache(None)
def selected_coordinate_checks():
    cuts,m,coords,fn=translated_model();c=cuts.make;r=cuts.read;norm=norm_factory(cuts,())
    events=('depart','reflection','arrival');tuples=('tuplea','tupleb','tuplec');labels=(7,19,7)
    rows={'eiyx':{(e,t,'frame','context') for e,t in zip(events,tuples)}};m=relations(m,rows,norm)
    checks=lambda mm:all(run('ei3h',[e,t,*map(c,map(Q,(x,2,-3))),'context'],mm) for e,t,x in zip(events,tuples,labels)) and run('ei3i',['trial','context'],mm)
    count=perturb(checks,m,rows,norm)
    for t in tuples:
        for axis in ('x','y','z','time'):
            old=m['zc6'];assert not checks(m|{'zc6':lambda rec,a,t=t,axis=axis:c(r(old(rec,a))+(1 if (rec,a)==(t,axis) else 0))});count+=1
    unknowns(checks,m,('zdz','zc6','qe','qf','qg','qi','qj','qk','zd4','zb7','bf','shv','sca','ba'))
    return dict(cases=count,three_current_K_tuples_and_actual_tau_readings_bound=True,nonzero_transverse_coordinates_and_auxiliary_origin_preserved=True)

@lru_cache(None)
def segment_checks():
    cuts,m,coords,fn=translated_model();c=cuts.make;m,rows,norm=segments(cuts,m);rows['zef']=rows.pop('zdw');m=relations(m,rows,norm)
    args=[['outward','ray','depart','reflection',c(Q(18)),'context'],['returning','ray','reflection','arrival',c(Q(9)),'context']]
    check=lambda mm:all(run('ei3e',xs,mm) for xs in args);count=perturb(check,m,rows,norm)
    assert check(m|{'zdw':forbidden,'sba':forbidden,'sbc':forbidden,'shd':forbidden});count+=1
    unknowns(check,m,('wf','wi','wj','wk','wl','wm','wn','wo','wp','wq','zbe','zbo','zdz','zc6'))
    return dict(cases=count,both_segments_current_K_clocks_geometric_length_and_principle_scope=True,parallel_support_line_not_original_axis_required=True)

@lru_cache(None)
def geometry_checks():
    cuts,m,coords,fn=translated_model();c=cuts.make;norm=norm_factory(cuts,(5,8,11,14))
    def linear(start,x,speed):return FunctionValue((RS,),RS,lambda t:c(Q(x)+Q(speed)*(cuts.read(t)-start)))
    y=linear(0,2,0);z=linear(0,-3,0)
    histories=[['origin','frame','context','lengthunit','unit',c(Q(5)),c(Q(14)),linear(5,12,1),y,z],['mirror','frame','context','lengthunit','unit',c(Q(5)),c(Q(14)),linear(5,24,1),y,z],['ray','frame','context','lengthunit','unit',c(Q(5)),c(Q(11)),linear(5,12,3),y,z],['ray','frame','context','lengthunit','unit',c(Q(11)),c(Q(14)),linear(11,30,-3),y,z]]
    rows={'se':{norm(h) for h in histories},'eisb5':{('ray','frame','context')},'cf':{('ray',)},'cg':{('ray','depart','reflection','frame'),('ray','reflection','arrival','frame')},'ch':{('ray','reflection','frame')},'eisca':{('ray','depart','reflection','frame','context'),('ray','reflection','arrival','frame','context')},'zzbu':set(),'zzbv':set()}
    for point,event,t,x in (('origin','depart',5,12),('mirror','reflection',11,30),('origin','arrival',14,21)):
        rows['zzbu'].add((event,'frame','context','lengthunit','unit',Q(t),Q(x),Q(2),Q(-3)))
        for obj in (point,'ray'):rows['zzbv'].add((obj,event,'context'))
    m=relations(m,rows,norm);args=['origin','mirror','ray','depart','reflection','arrival','frame','context','lengthunit','unit',*map(c,map(Q,(12,12,3,1,5,11,14,2,-3)))]
    count=perturb(lambda mm:run('ei3g',args,mm),m,rows,norm)
    for slot in range(10,19):
        bad=args.copy();bad[slot]=c(cuts.read(bad[slot])+1);assert not run('ei3g',bad,m);count+=1
    return dict(cases=count,native_four_complete_histories_and_six_same_event_meetings=True,arbitrary_constant_y_z_preserved_and_transverse_velocities_zero=True,history_fingerprints_not_full_real_trajectory_proofs=True)

@lru_cache(None)
def trial_connection_checks():
    cuts,m,coords,fn=translated_model();c=cuts.make;norm=norm_factory(cuts,())
    rows={'ei3f':{('trial','firstclock','secondclock','context')},'eizm':{('origin','context'),('mirror','context')},'ei3i':{('trial','context')},'ei3h':{(e,t,Q(x),Q(2),Q(-3),'context') for e,t,x in zip(('depart','reflection','arrival'),('tuplea','tupleb','tuplec'),(7,19,7))},'ei3g':{('origin','mirror','ray','depart','reflection','arrival','frame','context','lengthunit','unit',*map(Q,(12,12,3,1,5,11,14,2,-3)))},'ei3e':{('outward','ray','depart','reflection',Q(18),'context'),('returning','ray','reflection','arrival',Q(9),'context')}}
    m=relations(m,rows,norm);args=['trial','origin','outward','returning',*map(c,map(Q,(12,7,2,-3,5))),'context']
    count=perturb(lambda mm:run('ei3j',args,mm),m,rows,norm)
    for slot in range(4,9):
        bad=args.copy();bad[slot]=c(cuts.read(bad[slot])+1);assert not run('ei3j',bad,m);count+=1
    unknowns(lambda mm:run('ei3j',args,mm),m,('te','tf','qc','qd','qh','qe','qf','qg','zdz','zc6','tc','zb7','bd','bf','sca'))
    # Exposed witnesses test every binding, without replacing existential real scope.
    def normfn(xs):return tuple((cuts.read(x(c(Q(0)),c(Q(0)),c(Q(0)),c(Q(5)))),) if isinstance(x,FunctionValue) and len(x.parameters)==4 else norm((x,))[0] for x in xs)
    outer={'ei3d':{('context','history')},'ei3c':{((Q(10),),'context')},'eiyf':{('frame','context')},'eios':{(Q(3),'context')},'ei3j':{norm(args)}}
    mm=relations(m,outer,normfn);outerargs=['trial','origin',*map(c,map(Q,(7,2,-3,5))),'context','history','outward','returning',c(Q(12))]
    count+=perturb(lambda mm:run('ei3k',outerargs,mm,'instance'),mm,outer,normfn)
    return dict(cases=count,all_trial_geometry_coordinates_two_segments_and_global_conditions_bound=True,all_witness_slots_checked_without_claiming_finite_real_existence=True)

@lru_cache(None)
def point_checks():
    cuts,m=numbers();c=cuts.make;r=cuts.read;norm=norm_factory(cuts,());ctx='other';domain=('a','b')
    rows={'zdi':{('a',ctx)},'zcu':{('a','moving',ctx)},'x4':{('a','moving',ctx)},'eizm':{('a',ctx)},'ys':{('b',ctx)},'zce':{('a','b','frame','lengthunit',ctx)},'zcf':{('b','frame','unit',ctx)}}
    def moment(mo,f,u,ct):
        if mo not in domain or (f,u,ct)!=('frame','unit',ctx):forbidden()
        return c(Q(5 if mo=='b' else 8))
    def track(p,f,lu,tu,a,ct):
        if (p,f,lu,tu,ct)!=('a','frame','lengthunit','unit',ctx) or a not in ('x','y','z'):forbidden()
        return FunctionValue((RS,),RS,lambda t:c(7+r(t) if a=='x' else 2 if a=='y' else -3))
    def position(p,mo,f,lu,a,ct):return track(p,f,lu,'unit',a,ct)(moment(mo,f,'unit',ct))
    m=relations(m,rows,norm)|{'yl':moment,'ym':position,'eismh':track,'zb7':lambda:c(Q(1))}
    args=['a',*map(c,map(Q,(7,2,-3,5))),ctx,'b'];check=lambda mm:run('ei3l',args,mm,'instance')
    count=perturb(check,m,rows,norm)
    for slot in range(1,5):
        bad=args.copy();bad[slot]=c(r(bad[slot])+1);assert not run('ei3l',bad,m,'instance');count+=1
    assert not run('ei3l',args[:-1]+['a'],m,'instance');count+=1
    assert check(m|{'eiyg':forbidden,'zbe':forbidden,'eiyx':forbidden});count+=1
    unknowns(check,m,('yl','ym','eismh','zb7','ba','sca','bf','shv'))
    return dict(cases=count,same_measured_point_time_and_representative_trajectory_bound=True,baseline_point_not_required_to_already_have_local_clock_reading=True)

def test_connection_checks():
    assert connection_checks()['cases']>0


def test_choice_checks():
    assert choice_checks()['cases']>0


def test_shift_checks():
    assert shift_checks()['cases']>0


def test_derivative_checks():
    assert derivative_checks()['cases']>0


def test_scope_checks():
    assert scope_checks()['cases']>0


def test_presentation_checks():
    assert presentation_checks()['cases']>0


def test_correspondence_checks():
    assert correspondence_checks()['cases']>0


def test_global_clock_checks():
    assert global_clock_checks()['cases']>0


def test_trial_checks():
    assert trial_checks()['cases']>0


def test_selected_coordinate_checks():
    assert selected_coordinate_checks()['cases']>0


def test_segment_checks():
    assert segment_checks()['cases']>0


def test_geometry_checks():
    assert geometry_checks()['cases']>0


def test_trial_connection_checks():
    assert trial_connection_checks()['cases']>0


def test_point_checks():
    assert point_checks()['cases']>0


def native_run(doc,h):
    return [r['value'] for r in evaluate_document(doc,individuals=tuple(set(check.BASE.values())|{'other'}),situations=check.SITUATIONS,primitives=h)]

def context(doc,b):return handlers(doc)|{check.vocabulary()._symbols[n]:f for n,f in check.context_handlers(b).items()}


def test_source_backprojection_preserves_old_contracts_and_all_31_definitions():
    assert check.backprojection(check.restored()['document'])==check.source_excerpt()
    b=check.bridge();assert b['source_statement_indices']==[118,119]
    assert list(b['source_units'])==['einstein-1905:u0058']
    assert len(b['math'])==1 and b['math'][0]['id']=='M0105'
    assert len(b['text_boundaries']['sentences']['zeg']['tokens'])==32
    assert b['text_boundaries']['spans']=={'zeh':['zeg',21,32],'arbitraryweanchor':['zeg',6,6]}
    assert len(check.NEW_DEFINITIONS)==31
    assert check.document()['statements'][:88]==check.previous.document()['statements']
    prior=check.previous.vocabulary().document();current=check.vocabulary().document()
    for field in ('entries','compounds','definitions','primitives'):
        assert all(current[field][n]==d for n,d in prior[field].items())
    assert len(check.vocabulary()._words)==760
    ds={d['name']:d for d in check.source_excerpt()['declarations']}
    for old,new in profile.SOURCE_RELATIONS.items():
        assert profile.CONTRACTS[new]['parameters']==ds[old]['parameters']
        assert profile.CONTRACTS[new]['result']==ds[old]['result']


def test_history_and_parallel_path_adaptations_preserve_other_native_conditions():
    ds={d['name']:deepcopy(d) for d in check.restored()['document']['declarations']}
    m=mapping()
    for old,new in (('eixt','ei3d'),('ei2m','ei3e')):
        original=ds[m[old]];adapted=ds[m[new]]
        oldparams=original['parameters'];params=adapted['parameters']
        hist=params[-1]['name'] if new=='ei3d' else None
        assert len(params)==len(oldparams)+(1 if hist else 0)
        rename={p['name']:q['name'] for p,q in zip(params,oldparams)}
        def undo(n):
            if isinstance(n,list):return [undo(x) for x in n]
            if not isinstance(n,dict):return n
            if hist and n.get('kind')=='variable' and n['name']==hist:return call(m['zcj'])
            if n.get('kind')=='variable' and n['name'] in rename:return dict(n,name=rename[n['name']])
            n={k:undo(v) for k,v in n.items()}
            if new=='ei3e' and n.get('symbol')==m['zef']:n['symbol']=m['zdw']
            return n
        adapted['body']=undo(adapted['body']);adapted['parameters']=oldparams
        def alpha(d):
            counter=[0]
            def fresh():counter[0]+=1;return 'bound'+str(counter[0])
            env={p['name']:fresh() for p in d['parameters']}
            def walk(node,scope):
                if isinstance(node,list):return [walk(x,scope) for x in node]
                if not isinstance(node,dict):return node
                if node.get('kind')=='variable':return dict(node,name=scope[node['name']])
                if node.get('kind') in ('forall','exists','content'):
                    local=scope|{node['variable']:fresh()}
                    return dict(node,variable=local[node['variable']],body=walk(node['body'],local))
                if node.get('kind')=='lambda':
                    local=scope|{p['name']:fresh() for p in node['parameters']}
                    return dict(node,parameters=[dict(p,name=local[p['name']]) for p in node['parameters']],body=walk(node['body'],local))
                return {k:walk(v,scope) for k,v in node.items()}
            return walk(d['body'],env)
        assert alpha(adapted)==alpha(original)


def test_actor_reference_does_not_execute_role_or_identify_author():
    doc=deepcopy(check.restored()['document']);b=check.BASE;n=check.names()
    assert b['zee']!=b['rd']
    for old in (*check.SENTENCES,*check.SPANS,*check.ROLE_ASSIGNMENTS):
        trial=deepcopy(doc)
        trial['declarations'].append(dict(kind='primitive',name='arbitrarycapture',parameters=['individual'],result='truth'))
        trial['statements']=[dict(kind='ask',body=call('arbitrarycapture',call(n[old])))]
        assert native_run(trial,context(trial,b)|dict(arbitrarycapture=lambda x:x==b[old]))==[True]
    ds={d['name']:d for d in doc['declarations']};done=set()
    def visit(name,stack):
        assert name not in stack,'Cyclic reference'
        if name in done:return
        for ref in _references(ds[name].get('body')):visit(ref,stack|{name})
        done.add(name)
    for old in check.LOCAL_NAMES:visit(n[old],set())


def test_actor_reference_and_token_spans_reject_unknown_inputs():
    b=check.BASE;h=check.context_handlers(b)
    role=check.reference_roles()['zee']
    description=DescriptionValue(check.canonical(dict(kind='function_ref',symbol=role)),check.canonical(dict(kind='function',parameters=['individual','situation'],result='truth')))
    key=[b['eirf'],b['arbitraryweanchor'],description,b['ri']]
    assert h['describedreference'](*key)==b['zee']
    for slot in range(4):
        bad=key.copy();bad[slot]='unknown'
        with pytest.raises(ValueError):h['describedreference'](*bad)
    for bad in (DescriptionValue('{}',description.result_type),DescriptionValue(description.syntax,'"individual"'),DescriptionValue(description.syntax,description.result_type,1)):
        with pytest.raises(ValueError):h['describedreference'](*key[:2],bad,key[3])
    for old,(node,first,last) in check.SPANS.items():
        key=[b['eirf'],b[node],first,b[node],last,b['ri']]
        assert h['sentencetokenspanreference'](*key)==b[old]
        for slot in range(6):
            bad=key.copy();bad[slot]='unknown'
            with pytest.raises(ValueError):h['sentencetokenspanreference'](*bad)
    assert h['sentencetokenspanreference'](b['eirf'],b['zea'],10,b['zea'],11,b['ri'])==b['zeb']


def test_actor_role_binds_candidate_trial_and_shared_setting():
    for actor in ('a','b'):
        for trial in ('a','b'):
            row=(actor,trial,'context');m={'zec':lambda *xs:xs==row}
            assert run('arbitrarystartrole',[actor,'discourse'],m,domain=('a','b'))
            assert not run('arbitrarystartrole',['b' if actor=='a' else 'a','discourse'],m,domain=('a','b'))
            assert not run('arbitrarystartrole',[actor,'discourse'],m|{'zb6':lambda:'other'},domain=('a','b'))
    assert not run('arbitrarystartrole',['a','discourse'],{'zec':lambda *xs:False},domain=('a','b'))
    with pytest.raises(ValueError):run('arbitrarystartrole',['a','discourse'],{'zec':forbidden},domain=('a','b'))


def test_whole_attribution_keeps_attention_consequence_and_source_order():
    doc=deepcopy(check.restored()['document']);doc['statements']=doc['statements'][88:90];b=check.BASE
    rows={'eir3':{(b[node],b['rd'],b['eirf'],message,b['ri']) for node,message in (('zeg','ei3r'),('zeh','ei3u'))},
          'ue':{(b[first],b[last],b['ri']) for first,last in (('zeb','zeg'),('zeg','zeh'))}}
    h=context(doc,b)|{mapping()[n]:relation(rs) for n,rs in rows.items()}
    assert native_run(doc,h)==[True,True]
    for n,rs in rows.items():
        for row in rs:
            result=native_run(doc,h|{mapping()[n]:relation(rs-{row})})
            assert result.count(False)==1 and result.count(True)==1


def test_unregistered_cut_is_not_inferred_from_finite_samples():
    cuts,m=numbers()
    with pytest.raises(ValueError,match='not constructed'):cuts.read(cut(Q(3)))


def test_trial_individual_witnesses_bind_natively_one_at_a_time():
    cuts,m,coords,fn=translated_model();c=cuts.make;norm=norm_factory(cuts,())
    def normfn(xs):
        return tuple((cuts.read(x(c(0),c(0),c(0),c(5))),) if isinstance(x,FunctionValue) and len(x.parameters)==4 else norm((x,))[0] for x in xs)
    # Three independent existential slots, two values each. Other witnesses
    # are instantiated; this is a binding diagnostic, not a full-domain proof.
    for selected in range(3):
        for chosen in ('a','b'):
            witnesses=['a','a','b'];witnesses[selected]=chosen
            hist,outward,returning=witnesses
            inner=('a','b',outward,returning,*map(Q,(12,7,2,-3,5)),'context')
            rows={'ei3d':{('context',hist)},'ei3c':{((Q(10),),'context')},'eiyf':{('a','context')},'eios':{(Q(3),'context')},'ei3j':{inner}}
            mm=relations(m,rows,normfn)|{'ra':lambda:'a'}
            args=['a','b',*map(c,map(Q,(7,2,-3,5))),'context',*[w for i,w in enumerate(witnesses) if i!=selected],c(12)]
            mode='witness'+str(selected)
            assert run('ei3k',args,mm,mode,domain=('a','b'))
            bound='ei3d' if selected==0 else 'ei3j'
            assert not run('ei3k',args,mm|{bound:lambda *xs:False},mode,domain=('a','b'))
            row=list(next(iter(rows[bound])));row[1 if selected==0 else selected+1]='absent'
            missing=mm|{bound:lambda *xs,row=tuple(row):normfn(xs)==row}
            assert not run('ei3k',args,missing,mode,domain=('a','b'))
