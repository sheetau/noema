from copy import deepcopy
from itertools import product
from fractions import Fraction as Q
from functools import lru_cache
import json,re
import pytest
from noema.constructed_semantics import Content,FunctionValue,SequenceValue,DescriptionValue,QuestionValue,evaluate_document
from noema.meaning_catalog import _references
from scripts import check_einstein_affine_time_visible as check
from scripts import affine_time_visible_profile as profile
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


def forbidden(*args):raise ValueError('Unknown affine-time-visible input')
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

CONSTANTS|={'zeu':'inference','zev':'origin','zew':'unknown','zeo':'previous','zee':'agent','zes':'context'}
DOMAIN=tuple(dict.fromkeys([*DOMAIN,*CONSTANTS.values(),'event','other_event','origin','other_origin','first','second','other_tuple','inference','unknown','previous','agent']))

@lru_cache(None)
def fixture(name,mode='boundary'):
    doc=deepcopy(check.restored()['document']);m=mapping()
    boundaries=NUM|set(CONSTANTS)|{d['name'] for d in check.source_excerpt()['declarations'] if d['kind']=='primitive'}
    boundaries|={'sje'}
    if name in ('ei4g','ei4h','ei4i','ei4k'):boundaries.add('eiyx')
    if name=='ei4j':boundaries.add('ei4g')
    if name=='ei4l':boundaries|={'ei3c','ei4j','ei4k'}
    if name=='ei4n':boundaries|={'eizf','ei3c','smd'}
    if name=='ei4o':boundaries|={'ei4n','smr'}
    if name=='ei4p':boundaries|={'skn','slm','ei4o','ei4l'}
    if name=='ei4q':boundaries.add('ei4l')
    if name=='smr':boundaries|={'smd','sjw','sjs'}
    if name=='smp':boundaries|={'smq','smb'}
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
    if mode=='instance':assert len(expose(target,{'forall','exists'}))=={'ei4p':7,'smi':4,'smq':1,'smb':3,'smp':2,'smd':4,'affinecoefficientrole':1,'affinefamilyrole':2}[name]
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
        except ValueError as e:assert 'Unknown affine-time-visible' in str(e),str(e)
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

def relations(m,rows,norm):return m|{n:lambda *xs,rs=rs:norm(xs) in rs for n,rs in rows.items()}

def origin_model():
    cuts,m=numbers();c=cuts.make;coords={'first':[Q(7),Q(2),Q(-3),Q(0)],'second':[Q(0)]*4}
    def coordinate(tup,role):
        if tup not in coords or role not in ROLES:forbidden()
        return c(coords[tup][ROLES.index(role)])
    m|={'zc6':coordinate,'zb7':lambda:c(Q(3)),'zbn':lambda f,ctx:'origin' if (f,ctx)==('moving','context') else forbidden()}
    rows={'zc4':{('event',)},'zbv':{('moving','origin','context')},'cb':{('event','origin','moving')},'eiyx':{('event','first','frame','context'),('event','second','moving','context')}}
    norm=norm_factory(cuts,());return cuts,relations(m,rows,norm),coords,rows,norm

@lru_cache(None)
def binding_checks():
    cuts,m,coords,rows,norm=origin_model();c=cuts.make;args=['event','first','second','context'];count=perturb(lambda mm:run('ei4g',args,mm),m,rows,norm)
    for kt,tau in ((0,0),(3,0),(0,3),(3,7),(-2,-5)):
        coords['first'][3]=Q(kt);coords['second'][3]=Q(tau)
        assert run('ei4g',args,m);assert run('ei4h',args,m)==(tau==0);assert run('ei4i',args,m)==(kt==0 and tau==0);count+=3
    coords['first'][3]=coords['second'][3]=Q(0)
    assert not run('ei4k',args,m);count+=1  # Clock zeros alone do not choose spatial labels.
    coords['first'][:3]=[Q(0)]*3;assert run('ei4k',args,m);count+=1
    for axis in range(3):
        coords['first'][axis]=Q(1);assert not run('ei4k',args,m);coords['first'][axis]=Q(0);count+=1
    assert run('ei4i',args,m|{'shd':forbidden,'sio':forbidden,'smk':forbidden});count+=1
    unknowns(lambda mm:run('ei4k',args,mm),m,('zbn','zc6','zb7','sca','bf','shv'))
    return dict(cases=count,same_origin_event_and_both_current_coordinate_tuples_required=True,zero_tau_and_zero_t_cannot_be_taken_from_different_events=True,clock_condition_does_not_force_all_spatial_values_zero=True,spatial_gauge_separately_bound_to_current_auxiliary_coordinates=True)

@lru_cache(None)
def conditional_scope_checks():
    cuts,m=numbers();c=cuts.make;domain=('a','b');count=0
    sets=[set(),{('a','a','a')},{('a','a','b')},{('b','b','a')},{('a','a','a'),('b','b','a')},{('a','a','a'),('b','a','b')},set(product(domain,repeat=3))]
    for ta,tb in ((0,7),(3,0),(0,0),(3,7)):
        times={'a':Q(ta),'b':Q(tb)}
        for selected in sets:
            def coord(t,role):
                if t not in times or role!='a':forbidden()
                return c(times[t])
            mm=m|{'zc7':lambda:'a','zc6':coord,'ei4g':lambda e,a,b,ctx:(e,a,b) in selected and ctx=='context'}
            expected=any(times[a]==times[b]==0 for e,a,b in selected) and all(times[b]!=0 or times[a]==0 for e,a,b in selected)
            assert run('ei4j',['context'],mm,domain=domain)==expected;count+=1
    mm=m|{'zc7':lambda:'a','zc6':lambda t,role:c(Q(0)) if t in domain and role=='a' else forbidden(),'ei4g':lambda e,a,b,ctx:(e,a,b,ctx)==('a','b','a','context')}
    unknowns(lambda mm:run('ei4j',['context'],mm,domain=domain),mm,('ei4g','zc6','sca'))
    return dict(cases=count,native_three_slot_exists_and_forall_checked_on_two_individuals=True,one_good_zero_event_does_not_hide_another_bad_zero_event=True,nonzero_tau_events_do_not_require_equal_times=True,nonempty_zero_anchor_required=True)

def affine_model(constant=7):
    cuts,m=numbers();c=cuts.make;r=cuts.read
    matrix_values={(a,b):Q((i+1)*(j+2)) for i,a in enumerate(ROLES) for j,b in enumerate(ROLES)}
    matrix_values.update({('time',a):Q(x) for a,x in zip(ROLES,(Q(-3,8),4,-2,Q(25,8)))})
    offsets=dict(zip(ROLES,map(Q,(11,13,17,constant))))
    def entry(a,b):
        if (a,b) not in matrix_values:forbidden()
        return c(matrix_values[a,b])
    def offset(a):
        if a not in offsets:forbidden()
        return c(offsets[a])
    matrix=FunctionValue(('individual','individual'),RS,entry);vec=FunctionValue(('individual',),RS,offset)
    coeff=list(map(Q,(Q(-3,8),4,-2,2,constant)))
    fn=FunctionValue((RS,)*4,RS,lambda x,y,z,t:c(coeff[0]*r(x)+coeff[1]*r(y)+coeff[2]*r(z)+coeff[3]*r(t)+coeff[4]))
    m|={'zb7':lambda:c(Q(3)),'zd4':lambda:fn}
    def norm(xs):
        def one(x):
            if not isinstance(x,FunctionValue):return x
            if x.parameters==('individual','individual'):return tuple(r(x(a,b)) for a in ROLES for b in ROLES)
            if x.parameters==('individual',):return tuple(r(x(a)) for a in ROLES)
            if len(x.parameters)==4:return tuple(r(x(*(c(Q(a)) for a in p))) for p in ((0,0,0,0),(7,2,-3,5)))
            return r(x)
        return tuple(one(x) for x in xs)
    return cuts,m,matrix_values,offsets,matrix,vec,coeff,fn,norm

@lru_cache(None)
def origin_premise_checks():
    cuts,m,mat,off,matrix,vec,coeff,fn,norm=affine_model(0);c=cuts.make;finger=norm((fn,))[0];domain=('a','b')
    rows={'ei3c':{(finger,'context')},'ei4j':{('context',)},'ei4k':{('a','b','a','context')}};m=relations(m,rows,norm)
    count=perturb(lambda mm:run('ei4l',['context'],mm,domain=domain),m,rows,norm)
    shifted=FunctionValue((RS,)*4,RS,lambda *xs:c(cuts.read(fn(*xs))+7))
    mm=m|{'zd4':lambda:shifted,'ei3c':lambda f,ctx:ctx=='context'}
    assert not run('ei4l',['context'],mm,domain=domain);count+=1
    assert run('smg',[fn],m);assert not run('smg',[shifted],m);count+=2
    unknowns(lambda mm:run('ei4l',['context'],mm,domain=domain),m,('zd4','ba','sca'))
    return dict(cases=count,current_global_tau_binding_conditional_clock_rule_and_same_spatial_anchor_required=True,nonzero_additive_constant_rejected_only_by_separate_zero_condition=True)

@lru_cache(None)
def coefficient_checks():
    cuts,m,mat,off,matrix,vec,coeff,fn,norm=affine_model();c=cuts.make;r=cuts.read;args=[matrix,vec,*map(c,coeff)];count=0
    assert run('ei4m',args,m);count+=1
    for i in range(5):
        bad=args.copy();bad[i+2]=c(coeff[i]+1);assert not run('ei4m',bad,m);count+=1
    for role in ROLES:
        old=mat['time',role];mat['time',role]=old+1;assert not run('ei4m',args,m);mat['time',role]=old;count+=1
    off['time']+=1;assert not run('ei4m',args,m);off['time']-=1;count+=1
    mat['x','y']+=1;assert run('ei4m',args,m);mat['x','y']-=1;count+=1
    off['x']+=1;assert run('ei4m',args,m);off['x']-=1;count+=1
    assert not run('ei4m',args,m|{'zb7':lambda:c(Q(2))});count+=1
    unknowns(lambda mm:run('ei4m',args,mm),m,('zb7','ba','bd','shv','sca'))
    # Independently substitute x=xprime+v*t in the source matrix row.
    for x,y,z,t in ((0,0,0,0),(7,2,-3,5),(-4,3,9,-2),(Q(1,2),Q(-2,3),Q(3,4),Q(5,6))):
        values=list(map(Q,(x,y,z,t)));xx,yy,zz,tt=values
        expected=mat['time','x']*(xx+3*tt)+mat['time','y']*yy+mat['time','z']*zz+mat['time','time']*tt+off['time']
        assert run('smc',[*map(c,coeff),*map(c,values)],m|{'jatcapture':lambda got,expected=expected:r(got)==expected});count+=1
        assert r(fn(*map(c,values)))==expected;count+=1
    return dict(cases=count,same_time_row_and_offset_bound=True,auxiliary_time_coefficient_is_D_plus_vA=True,all_five_coefficients_distinguished=True,nonzero_transverse_coefficients_and_offset_allowed_before_later_constraints=True,exact_rational_pullback_agrees_with_native_affine_expression=True)

@lru_cache(None)
def extension_checks():
    cuts,m,mat,off,matrix,vec,coeff,fn,norm=affine_model();c=cuts.make;args=[fn,matrix,vec,*map(c,coeff)]
    rows={'eizf':{norm((matrix,vec))},'ei3c':{(*norm((fn,)),'context')},'smd':{norm((fn,*map(c,coeff)))}}
    mm=relations(m,rows,norm);count=perturb(lambda mm:run('ei4n',args,mm),mm,rows,norm)
    assert run('ei4n',args,mm|{'sio':forbidden,'shd':forbidden,'sid':forbidden});count+=1
    # The extension is a separately required all-input condition. Test the
    # native body at distinct points, then retain the real-domain refusal.
    for point in ((0,0,0,0),(7,2,-3,5),(-4,3,9,-2)):
        inputs=[fn,*map(c,coeff),*map(c,map(Q,point))]
        assert run('smd',inputs,m,'instance');count+=1
        bad=inputs.copy();bad[5]=c(coeff[4]+1);assert not run('smd',bad,m,'instance');count+=1
    try:run('smd',[fn,*map(c,coeff)],m)
    except ValueError as e:assert 'Cannot finitely quantify' in str(e),str(e)
    else:raise AssertionError('All real inputs replaced with measured samples')
    return dict(cases=count,current_measured_affinity_and_current_tau_binding_both_required=True,same_coefficients_explicitly_extend_to_all_real_inputs=True,all_real_extension_refused=True,finite_fingerprints_not_equality_of_functions=True)

def model(offset=0):
    cuts,m,mat,off,matrix,vec,coeff,fn,oldnorm=affine_model(offset);c=cuts.make;r=cuts.read
    coeff[1]=coeff[2]=Q(0);mat['time','y']=mat['time','z']=Q(0)
    phi=FunctionValue((RS,),RS,lambda speed:c(Q(2)))
    def norm(xs):
        return tuple(tuple(r(x(c(Q(a)))) for a in (0,2,3,4)) if isinstance(x,FunctionValue) and x.parameters==(RS,) else oldnorm((x,))[0] for x in xs)
    m|={'sje':lambda a,b:c(r(a)/r(b)) if r(b)!=0 else forbidden(),'tc':lambda:c(Q(5)),'zeq':lambda:phi,'qe':lambda tr:'event' if tr=='trial' else forbidden(),'zdz':lambda e,f,ctx:'tuple' if (e,f,ctx)==('event','frame','context') else forbidden(),'zc6':lambda t,a:c(Q(5)) if (t,a)==('tuple','time') else forbidden()}
    return cuts,m,matrix,vec,coeff,fn,phi,norm

@lru_cache(None)
def coefficient_join_checks():
    cuts,m,matrix,vec,coeff,fn,phi,norm=model();c=cuts.make;args=[matrix,vec,*map(c,coeff)]
    rows={'ei4n':{norm((fn,*args))},'smr':{norm((fn,c(Q(5)),c(Q(3)),c(Q(5)),phi,*map(c,coeff)))}}
    mm=relations(m,rows,norm);count=perturb(lambda mm:run('ei4o',args,mm),mm,rows,norm)
    rows={'skn':{norm((fn,c(Q(5)),c(Q(3)),c(Q(5))))},'slm':{norm((fn,c(Q(5))))},'ei4o':{norm(args)},'ei4l':{('context',)}}
    mm=relations(m,rows,norm);count+=perturb(lambda mm:run('ei4p',args,mm,'instance'),mm,rows,norm)
    for n in ('zd4','tc','zb7','zeq','qe','zdz','zc6'):
        unknowns(lambda mm:run('ei4o',args,mm),relations(m,{'ei4n':{norm((fn,*args))},'smr':{norm((fn,c(Q(5)),c(Q(3)),c(Q(5)),phi,*map(c,coeff)))}},norm),(n,))
    for truth in (False,True):assert run('ei4q',[],m|{'ei4l':lambda ctx,truth=truth:ctx=='context' and truth})==truth;count+=1
    try:run('ei4p',[],mm)
    except ValueError as e:assert 'Cannot finitely quantify' in str(e)
    else:raise AssertionError('Real coefficient existence sampled')
    return dict(cases=count,same_tau_matrix_seven_witnesses_speed_time_and_phi_bound=True,origin_separate_from_derivative_premises=True,real_coefficient_existence_refused=True)

@lru_cache(None)
def native_coefficient_checks():
    count=0
    for offset in (0,7):
        cuts,m,matrix,vec,coeff,fn,phi,norm=model(offset);c=cuts.make;r=cuts.read;finger=norm((fn,))[0]
        rows={'smd':{norm((fn,*map(c,coeff)))},'sjw':{(finger,*map(Q,(0,0,0,5,Q(-3,8),2)))}}
        mm=relations(m,rows,norm)
        # Exact derivative oracle only for the supplied affine functions.
        mm['sjs']=lambda domain,f,p,d:domain(p) and r(f(c(r(p)+1)))-r(f(p))==r(d)
        args=[fn,c(Q(5)),c(Q(3)),c(Q(5)),phi,*map(c,coeff)]
        count+=perturb(lambda mm:run('smr',args,mm),mm,rows,norm)
        wrong=FunctionValue((RS,),RS,lambda speed:c(Q(3)));bad=args.copy();bad[4]=wrong;assert not run('smr',bad,mm);count+=1
        for i in range(5):
            bad=args.copy();bad[5+i]=c(coeff[i]+1);assert not run('smr',bad,mm);count+=1
        seen=[]
        def selected(speed):seen.append(r(speed));return c(Q(2))
        args[4]=FunctionValue((RS,),RS,selected);assert run('smr',args,mm) and set(seen)=={Q(3)};count+=1
    return dict(cases=count,native_smr_smf_sme_join_and_same_speed_phi_checked=True,nonzero_offset_still_allowed_before_origin_condition=True,affine_derivatives_are_explicit_fixture_oracles=True)

@lru_cache(None)
def formula_checks():
    count=0
    for speed,scale in ((3,2),(3,3),(0,2),(3,-2),(3,0)):
        cuts,m,matrix,vec,coeff,fn,phi,norm=model();c=cuts.make;r=cuts.read;coeff[:]=[Q(-scale*speed,25-speed*speed),Q(0),Q(0),Q(scale),Q(0)]
        for x,y,z,t in ((8,3,4,5),(-8,-4,9,5),(0,0,0,0),(Q(1,2),2,-3,Q(5,6))):
            args=[fn,c(Q(5)),c(Q(speed)),c(Q(scale)),*map(c,map(Q,(x,y,z,t)))]
            assert run('smi',args,m,'instance');count+=1
            coeff[4]=Q(7);assert not run('smi',args,m,'instance');coeff[4]=Q(0);count+=1
        for axis in (1,2):
            coeff[axis]=Q(1);args=[fn,c(Q(5)),c(Q(speed)),c(Q(scale)),*map(c,map(Q,(8,3,4,5)))];assert not run('smi',args,m,'instance');coeff[axis]=Q(0);count+=1
    cuts,m,matrix,vec,coeff,fn,phi,norm=model();c=cuts.make
    try:run('smn',[],m)
    except ValueError as e:assert 'Cannot finitely quantify' in str(e)
    else:raise AssertionError('Full formula reduced to sample points')
    return dict(cases=count,native_formula_all_four_inputs_and_offset_distinguished=True,zero_stationary_negative_and_nonunit_scale_not_arbitrarily_excluded=True,full_formula_real_domain_refused=True)

@lru_cache(None)
def uncertainty_checks():
    cuts,m,matrix,vec,coeff,fn,phi,norm=model();c=cuts.make;r=cuts.read;count=0
    def family(stage):
        if stage not in ('context','other','discourse'):forbidden()
        return FunctionValue((RS,),RS,lambda speed:c(Q(2)+(r(speed)-3)**2 if stage=='other' else Q(2)))
    fam=FunctionValue(('situation',),dict(kind='function',parameters=[RS],result=RS),family)
    alternatives=lambda agent,stage,alt:agent=='agent' and stage=='context' and alt in ('context','other')
    domain=FunctionValue((RS,),'truth',lambda speed:0<=r(speed)<5)
    same=FunctionValue((RS,RS),'truth',lambda a,b:r(a)==r(b))
    alt=FunctionValue(('individual','situation','situation'),'truth',alternatives)
    mm=m|{'zer':lambda:fam,'zet':alternatives}
    for speed,expected in ((3,False),(2,True),(5,False),(-1,False)):
        args=['agent','context',domain,alt,fam,same,'context','other',c(Q(speed))]
        assert run('smb',args,mm,'instance')==expected;count+=1
        for slot,value in ((0,'other'),(1,'other'),(7,'context')):
            bad=args.copy();bad[slot]=value;assert not run('smb',bad,mm,'instance');count+=1
    for speed in (0,2,3,4):
        args=[phi,fam,'context',domain,c(Q(speed))];assert run('smq',args,mm,'instance');count+=1
        bad=args.copy();bad[2]='other';assert run('smq',bad,mm,'instance')==(speed==3);count+=1
    # Native smp maintains current-candidate membership and validity of each
    # selected alternative at each allowed speed. smq/smb boundaries are tested above.
    mm|={'smq':lambda *xs:True,'smb':lambda *xs:True}
    for stage in ('context','other','discourse'):
        assert run('smp',[stage,c(Q(2))],mm,'instance');count+=1
    assert not run('smp',['other',c(Q(2))],mm|{'zet':lambda a,s,t:t=='other'},'instance');count+=1
    for n in ('smq','smb'):
        assert not run('smp',['other',c(Q(2))],mm|{n:lambda *xs:False},'instance');count+=1
    try:run('smp',[],mm)
    except ValueError as e:assert 'Cannot finitely quantify' in str(e)
    else:raise AssertionError('Candidate validity on all speeds sampled')
    return dict(cases=count,current_function_same_stage_same_speed_domain_preserved=True,equal_at_one_speed_does_not_identify_functions=True,native_candidate_membership_and_real_scope_retained=True,knowledge_in_general_not_claimed=True)

@lru_cache(None)
def presentation_checks():
    count=0
    for name,rows in (
      ('ei4r',{'zc':{('inference','author','ei4p','smn','section','discourse')}}),
      ('ei4u',{'uh':{('unknown','author','smp','section','discourse')}}),
      ('ei4x',{'ug':{('origin','author','ei4q','section','discourse')},'zex':{('origin','author','section','discourse')}}),
      ('ei4t',{'eir3':{('inference','author','paper','ei4s','discourse')},'ue':{('previous','inference','discourse')}}),
      ('ei4w',{'eir3':{('unknown','author','paper','ei4v','discourse')},'ue':{('inference','unknown','discourse')}}),
      ('ei4z',{'eir3':{('origin','author','paper','ei4y','discourse')},'ue':{('unknown','origin','discourse')}})):
        m={n:relation(rs) for n,rs in rows.items()};count+=perturb(lambda mm:run(name,[],mm),m,rows)
        assert run(name,[],m|{n:forbidden for n in ('ei4p','ei4q','smn','smp','zd4')});count+=1
    return dict(cases=count,consequence_unknown_and_assumption_with_brevity_are_distinct=True,same_author_section_paper_and_source_order_preserved=True,quoted_contents_not_executed=True)

def test_binding_checks():
    assert binding_checks()['cases']>0


def test_conditional_scope_checks():
    assert conditional_scope_checks()['cases']>0


def test_origin_premise_checks():
    assert origin_premise_checks()['cases']>0


def test_coefficient_checks():
    assert coefficient_checks()['cases']>0


def test_extension_checks():
    assert extension_checks()['cases']>0


def test_coefficient_join_checks():
    assert coefficient_join_checks()['cases']>0


def test_native_coefficient_checks():
    assert native_coefficient_checks()['cases']>0


def test_formula_checks():
    assert formula_checks()['cases']>0


def test_uncertainty_checks():
    assert uncertainty_checks()['cases']>0


def test_presentation_checks():
    assert presentation_checks()['cases']>0


def native_run(doc,h):
    return [r['value'] for r in evaluate_document(doc,individuals=tuple(set(check.BASE.values())|{'other'}),situations=check.SITUATIONS,primitives=h)]

def context(doc,b):return handlers(doc)|{check.vocabulary()._symbols[n]:f for n,f in check.context_handlers(b).items()}


def test_source_backprojection_and_preserved_contracts():
    assert check.backprojection(check.restored()['document'])==check.source_excerpt()
    b=check.bridge();assert b['source_statement_indices']==[122,123,124]
    assert list(b['source_units'])==['einstein-1905:u0062','einstein-1905:u0063','einstein-1905:u0064']
    assert [r['id'] for r in b['math']]==['M'+str(i).zfill(4) for i in range(111,118)]
    assert len(b['text_boundaries']['sentences']['affinetimesentence']['tokens'])==34
    assert b['text_boundaries']['spans']=={'zeu':['affinetimesentence',1,11],'zew':['affinetimesentence',12,19],'zev':['affinetimesentence',20,34],'affinecoefficientanchor':['affinetimesentence',18,18]}
    assert len(check.NEW_DEFINITIONS)==35
    assert check.document()['statements'][:92]==check.previous.document()['statements']
    prior=check.previous.vocabulary().document();current=check.vocabulary().document()
    for field in ('entries','compounds','definitions','primitives'):
        assert all(current[field][n]==d for n,d in prior[field].items())
    assert len(check.vocabulary()._words)==769
    ds={d['name']:d for d in check.source_excerpt()['declarations']}
    for old,new in profile.SOURCE_RELATIONS.items():
        assert profile.CONTRACTS[new]['parameters']==ds[old]['parameters']
        assert profile.CONTRACTS[new]['result']==ds[old]['result']


def opaque_reference_values():
    def forbidden_call(*xs):raise AssertionError('Reference lookup executed a candidate')
    return check.BASE|{'zeq':FunctionValue(tuple(profile.PHI['parameters']),profile.PHI['result'],forbidden_call),
                       'zer':FunctionValue(tuple(profile.FAMILY['parameters']),profile.FAMILY['result'],forbidden_call)}


def test_references_do_not_execute_candidates_or_infinite_roles():
    doc=deepcopy(check.restored()['document']);b=opaque_reference_values();n=check.names()
    for old in (*check.SENTENCES,*check.SPANS,*check.ROLE_ASSIGNMENTS):
        sort=profile.PHI if old=='zeq' else profile.FAMILY if old=='zer' else 'situation' if old=='zes' else 'individual'
        trial=deepcopy(doc)
        trial['declarations'].append(dict(kind='primitive',name='affinecapture',parameters=[sort],result='truth'))
        trial['statements']=[dict(kind='ask',body=call('affinecapture',call(n[old])))]
        def capture(x):
            return isinstance(x,FunctionValue) and list(x.parameters)==sort['parameters'] and x.result==sort['result'] if isinstance(sort,dict) else x==b[old]
        assert native_run(trial,context(trial,b)|dict(affinecapture=capture))==[True]
    ds={d['name']:d for d in doc['declarations']};done=set()
    def visit(name,stack):
        assert name not in stack,'Cyclic reference'
        if name in done:return
        for ref in _references(ds[name].get('body')):visit(ref,stack|{name})
        done.add(name)
    for old in check.LOCAL_NAMES:visit(n[old],set())


def test_reference_types_scopes_and_unknown_inputs_are_rejected():
    b=opaque_reference_values();h=check.context_handlers(b)
    for old,name,sort in (('zes','describedsettingreference','situation'),('zeq','describedcutfunctionreference',profile.PHI),('zer','describedsituationcutfunctionfamilyreference',profile.FAMILY)):
        role=check.reference_roles()[old]
        description=DescriptionValue(check.canonical(dict(kind='function_ref',symbol=role)),check.canonical(dict(kind='function',parameters=[sort,'situation'],result='truth')))
        key=[b['eirf'],b[check.reference_anchor(old)],description,b['ri']]
        assert h[name](*key) is b[old]
        for slot in range(4):
            bad=key.copy();bad[slot]='unknown'
            with pytest.raises(ValueError):h[name](*bad)
        for bad in (DescriptionValue('{}',description.result_type),DescriptionValue(description.syntax,'"individual"'),DescriptionValue(description.syntax,description.result_type,1)):
            with pytest.raises(ValueError):h[name](*key[:2],bad,key[3])
    for old,(node,first,last) in check.SPANS.items():
        key=[b['eirf'],b[node],first,b[node],last,b['ri']]
        assert h['sentencetokenspanreference'](*key)==b[old]
        for slot in range(6):
            bad=key.copy();bad[slot]='unknown'
            with pytest.raises(ValueError):h['sentencetokenspanreference'](*bad)
    assert h['sentencetokenspanreference'](b['eirf'],b['zeo'],13,b['zeo'],33,b['ri'])==b['zen']


def test_function_reference_declarations_are_checked_without_probing():
    b=opaque_reference_values()
    for name,old in (('describedcutfunctionreference','zeq'),('describedsituationcutfunctionfamilyreference','zer')):
        assert profile.TypedFunctionReferences(name,{('doc','node','role','context'):b[old]})
        for bad in ('not a function',b['zer' if old=='zeq' else 'zeq'],FunctionValue((),'truth',lambda:True),FunctionValue(b[old].parameters,b[old].result,None)):
            with pytest.raises(ValueError):profile.TypedFunctionReferences(name,{('doc','node','role','context'):bad})
    with pytest.raises(ValueError):profile.TypedFunctionReferences('unknown',{})


def test_reference_roles_keep_stage_and_same_admissible_speed_range():
    cuts,m=numbers();c=cuts.make;r=cuts.read
    m|={'tc':lambda:c(5),'zet':lambda agent,stage,alt:agent=='agent' and stage=='context' and alt in ('context','other')}
    assert run('affinestagerole',['context','discourse'],m)
    assert not run('affinestagerole',['other','discourse'],m)
    with pytest.raises(ValueError):run('affinestagerole',['context','discourse'],m|{'zet':forbidden})
    phi=FunctionValue((RS,),RS,lambda speed:c(2))
    invalid=FunctionValue((RS,),RS,lambda speed:c(9))
    valid=m['ba'];mm=m|{'ba':lambda x:valid(x) and r(x)!=9}
    for speed in (-1,0,2,5):
        assert run('affinecoefficientrole',[phi,'discourse',c(speed)],mm,'instance')
        assert run('affinecoefficientrole',[invalid,'discourse',c(speed)],mm,'instance')==(not 0<=speed<5)
    fam=FunctionValue(('situation',),profile.PHI,lambda stage:invalid if stage=='other' else phi)
    for stage in POINTS:
        assert run('affinefamilyrole',[fam,'discourse',stage,c(2)],mm,'instance')==(stage!='other')
    assert run('affinefamilyrole',[fam,'discourse','other',c(2)],mm|{'zet':lambda a,s,t:t=='context'},'instance')
    for name,args in (('affinecoefficientrole',[phi,'discourse']),('affinefamilyrole',[fam,'discourse'])):
        with pytest.raises(ValueError,match='Cannot finitely quantify'):run(name,args,mm)


def test_whole_attribution_preserves_formula_uncertainty_and_assumption_order():
    doc=deepcopy(check.restored()['document']);doc['statements']=doc['statements'][92:95];b=opaque_reference_values()
    rows={'eir3':{(b[node],b['rd'],b['eirf'],message,b['ri']) for node,message in (('zeu','ei4s'),('zew','ei4v'),('zev','ei4y'))},
          'ue':{(b[first],b[last],b['ri']) for first,last in (('zeo','zeu'),('zeu','zew'),('zew','zev'))}}
    h=context(doc,b)|{mapping()[n]:relation(rs) for n,rs in rows.items()}
    assert native_run(doc,h)==[True]*3
    for n,rs in rows.items():
        for row in rs:
            result=native_run(doc,h|{mapping()[n]:relation(rs-{row})})
            assert result.count(False)==1 and result.count(True)==2
