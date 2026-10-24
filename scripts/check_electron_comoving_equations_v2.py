"""Check independent physical fields, initial remainders, and source presentation."""
from copy import deepcopy
from functools import lru_cache
from fractions import Fraction as Q
import json,re
from noema.grammar import parse,format_graph,number_word
from noema.extraction import extract_document
from noema.finite_semantics import Content,FunctionValue,evaluate_document
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts import check_electron_coordinate_normalization as base
from scripts import check_electron_coordinate_claim as prior
from scripts import check_material_acceleration as analytic
from scripts.check_clock_site_time import relation,perturb
from scripts.check_ninth_section_opening import lifted
from scripts.check_problem_series_reduction import collapse
from scripts.compose_electron_comoving_equations_v2 import *

DOC='docs/electron-comoving-equations-v2.md';SOURCE='data/einstein-electron-comoving-equations-reading-v2.json'
INVENTORY='artifacts/written-units-v1/einstein-1905.json';FACSIMILE='artifacts/written-facsimiles-v1/einstein-p918-0.jpg'
DEPENDENCIES=('reports/electron-coordinate-claim-v1.json','reports/electron-comoving-history-v1.json','reports/point-particle-dynamics-v1.json','reports/electron-rest-law-claim-v1.json','reports/field-transform-v1.json')
fn=base.old.fn;sort=base.old.sort;forbidden=base.forbidden
CONSTANTS=prior.CONSTANTS|{'ra':'frame','eiscg':'relativity','eisms':'third','zno':'sixth','eisx6':'tauname','eisx7':'newcoordinates','eisya':'newE1','eisyb':'newE2','eisyc':'newE3','eisyd':'initialintro','eisye':'equations','eisyf':'notation','eisyg':'originchoice','eisyh':'transformintro','eisyi':'transformdisplay','eisyj':'betaname','eisyk':'lightname'}
PEOPLE=tuple(dict.fromkeys([*prior.PEOPLE,*CONSTANTS.values(),'newrecord']))
BOUNDS={'ek6z':{'ek6n','ek6o','ek3v','ek3r'},'ek63':{'ek6z'},'ek64':{'ejs3'},'ek66':{'ek64','ek65','ejsj'},'ek7b':{'senz','sjr'},'ek7c':{'ek32','ek7b','ek74'},'ek74':{'ek32','ek7b'},'ek7d':{'ek3v'},'ek7k':{'ek7d','ek7e','ek7f','ek7g','ek7h','ek7i','ek7j','ek37','ek4b','ek4a'},'ek7l':{'ek63'},'ek7m':{'ek7l','ek63','ek7c'},'ek7n':{'ek35','eifj','ek6r','ek7l'},'ek7o':{'ek7n','ek7m','ek4f','eifj'},'ek7q':{'ek7p'},'ek7r':{'ek7k'},'ek7s':{'ek63','ek66'},'ek7t':{'ek7l','ek6k'},'ek7u':{'ek7l','ek7s','ejeh','ejvm'},'ek7v':{'ek7r','ek7t','ek7u'},'ek7x':{'ek7w'}}
BOUNDS.update(ek7z={'ejs3'},ek72={'ek66','ek7z'},ek73={'ek63','ek72'})
BOUNDS['ek7u'].add('ek73')
@lru_cache(None)
def core():return parse(read(CORE))
@lru_cache(None)
def boundary(root,mode='boundary'):
    doc=extract_document(core(),roots=[root],statement_indices=[]).document
    cuts=base.BOUNDS|BOUNDS.get(root,set())
    if mode=='native':cuts=cuts-{'sjr','senz'}
    for i,d in enumerate(doc['declarations']):
        if d['kind']=='definition' and d['name'] in cuts:doc['declarations'][i]=dict(kind='primitive',name=d['name'],parameters=[p['sort'] for p in d['parameters']],result=d['result'])
    return extract_document(doc,roots=[root],statement_indices=[]).document
@lru_cache(None)
def fixture(root,mode='boundary'):
    doc=deepcopy(boundary(root,mode));d=next(d for d in doc['declarations'] if d['name']==root);slots=[]
    for i,p in enumerate(d['parameters']):
        n='jcearg'+number_word(i);slots.append(n);doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']))
    expr=dict(kind='call',symbol=root,arguments=[dict(kind='call',symbol=n,arguments=[]) for n in slots])
    if d['result']=='content':
        doc['declarations'].append(dict(kind='primitive',name='jcepoint',parameters=[],result='situation'));expr=dict(kind='evaluate',content=expr,situation=dict(kind='call',symbol='jcepoint',arguments=[]))
    elif d['result']!='truth':
        doc['declarations'].append(dict(kind='primitive',name='jcecapture',parameters=[d['result']],result='truth'));expr=dict(kind='call',symbol='jcecapture',arguments=[expr])
    doc['declarations'].sort(key=lambda d:d['kind']!='primitive');doc['statements']=[dict(kind='ask',body=expr)];return doc,slots
def run(root,values,m,mode='boundary'):
    doc,slots=fixture(root,mode);assert len(values)==len(slots);captured=[]
    def capture(x):captured.append(x);return True
    mm={n:lambda x=x:x for n,x in CONSTANTS.items()}|{'jcepoint':lambda:'case','jcecapture':capture}|m|{n:lambda x=x:x for n,x in zip(slots,values)}
    out=evaluate_document(doc,individuals=PEOPLE,situations=('case','other'),primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=3000000,memoize_definitions=True,memoize_expressions=True)[0]['value']
    return captured[0] if captured else out

class Model:
    def __init__(self,speed=3,offset=(0,0,0,0)):
        by,_,_,_,_=base.old.setup();self.by=by.copy();self.c,self.r,self.m,self.point,self.pv=base.setup();c,r=self.c,self.r
        self.speed=Q(speed);self.offset=tuple(map(Q,offset));self.beta=Q(1) if not speed else Q(5,4)
        self.by.update(frame='frame',event='event',matter='matter',point=self.point((0,0,0,0)),newrecord='newrecord',electricconversion=c(1),magneticconversion=c(1),charge=c(-3),mass=c(2),domain=self.domain(-2,2),curve=fn(sort(CURVE),lambda t:self.point((speed*r(t),r(t)**2,-2*r(t)**2,r(t)))))
        for (n,t),u,a in zip(PROFILES,(speed,0,0),(0,2,-4)):self.by[n]=fn(sort(t),lambda x,u=u,a=a:c(u+a*r(x)))
        for (n,t),a in zip(ACCEL,(0,2,-4)):self.by[n]=c(a)
        for field,shift in [('electricfield',1),('magneticfield',7)]:self.by[field]=self.field(lambda axis,p,s=shift:s+{'x':p[0]+2*p[1]-p[3],'y':-p[0]+3*p[2]+p[3],'z':p[1]-2*p[2]+4*p[3]}.get(axis,0))
        self.by['region']=fn(sort(REGION),lambda x,y,z,t:-3<r(x)+2*r(y)-r(z)+r(t)<8)
        self.by['newelectric']=self.field(lambda axis,p:self.mixed(self.inverse(p))[('x','y','z').index(axis)] if axis in ('x','y','z') else 0)
        self.by['newmagnetic']=self.field(lambda axis,p:self.magnetic_mix(self.inverse(p))[('x','y','z').index(axis)] if axis in ('x','y','z') else 0)
        self.newdomain=self.domain(-2+offset[3],2+offset[3]);self.newcurve=fn(sort(CURVE),lambda t:self.point((offset[0],self.beta**2*(r(t)-offset[3])**2+offset[1],-2*self.beta**2*(r(t)-offset[3])**2+offset[2],r(t))))
        for (n,t),a in zip(PROFILES,(0,2*self.beta**2,-4*self.beta**2)):self.by['new'+n]=fn(sort(t),lambda x,a=a:c(a*(r(x)-offset[3])))
        for (n,t),a in zip(ACCEL,(0,2*self.beta**2,-4*self.beta**2)):self.by['new'+n]=c(a)
        self.m|={'tc':lambda:c(5),'eisxt':lambda:c(speed),'eisxz':lambda:self.point(offset),'eisx2':lambda:self.newdomain,'eisx3':lambda:self.newcurve}
    def domain(self,lo,hi):return fn(sort(DOMAIN),lambda t:lo<self.r(t)<hi)
    def field(self,f):return fn(sort(FIELD),lambda axis:fn(sort('h['+' '.join([R]*4)+'] '+R),lambda *xs:self.c(f(axis,tuple(map(self.r,xs))))))
    def inverse(self,p):
        x,y,z,t=(Q(a)-b for a,b in zip(p,self.offset));return (self.beta*(x+self.speed*t),y,z,self.beta*(t+self.speed*x/25))
    def mapped(self,p):
        x,y,z,t=map(Q,p);return tuple(a+b for a,b in zip((self.beta*(x-self.speed*t),y,z,self.beta*(t-self.speed*x/25)),self.offset))
    def mixed(self,p):
        e=[self.r(self.by['electricfield'](a)(*map(self.c,p))) for a in ('x','y','z')];b=[self.r(self.by['magneticfield'](a)(*map(self.c,p))) for a in ('x','y','z')]
        return e[0],self.beta*(e[1]-self.speed*b[2]/5),self.beta*(e[2]+self.speed*b[1]/5)
    def magnetic_mix(self,p):
        e=[self.r(self.by['electricfield'](a)(*map(self.c,p))) for a in ('x','y','z')];b=[self.r(self.by['magneticfield'](a)(*map(self.c,p))) for a in ('x','y','z')]
        return b[0],self.beta*(b[1]+self.speed*e[2]/5),self.beta*(b[2]-self.speed*e[1]/5)
    def values(self,fields=PAIR):return [self.by[n] for n,t in fields]
    def key(self,x):
        if isinstance(x,(tuple,list)):return tuple(self.key(y) for y in x)
        if not isinstance(x,FunctionValue):return x
        if x.parameters==('number',):return self.r(x)
        if x.parameters==('individual',) and x.result==sort(R):return self.pv(x)
        if x.parameters==(sort(R),):return tuple(self.key(x(self.c(t))) for t in (-1,0,1))
        if x.parameters==(sort(R),)*4:return tuple(self.key(x(*map(self.c,p))) for p in base.POINTS[:5])
        if x.parameters==('individual',):return tuple(self.key(x(a)) for a in ('x','y','z'))
        raise AssertionError(x.parameters)
    def new(self):
        by=self.by.copy();by.update(frame='comoving',chargerecord=by['newrecord'],electricfield=by['newelectric'],magneticfield=by['newmagnetic'],domain=self.newdomain,curve=self.newcurve,point=self.point(self.offset))
        by['region']=fn(sort(REGION),lambda *xs:self.by['region'](*map(self.c,self.inverse(tuple(map(self.r,xs))))))
        by.update({n:self.by['new'+n] for n,t in PROFILES+ACCEL});return by

@lru_cache(None)
def transform_checks():
    cases=0
    for speed in (0,3):
        for offset in ((0,0,0,0),(2,-1,4,3)):
            a=Model(speed,offset);c,r=a.c,a.r;vs=[c(5),c(speed),a.point(offset),a.by['electricfield'],a.by['magneticfield']]
            field=run('ek6x',vs,a.m);magnetic=run('ek7y',vs,a.m);region=run('ek6y',vs[:3]+[a.by['region']],a.m)
            for p in base.POINTS:
                for axis in ('x','y','z'):assert r(field(axis)(*map(c,p)))==r(a.by['newelectric'](axis)(*map(c,p)));cases+=1
                for axis in ('x','y','z'):assert r(magnetic(axis)(*map(c,p)))==r(a.by['newmagnetic'](axis)(*map(c,p)));cases+=1
                assert region(*map(c,p))==a.by['region'](*map(c,a.inverse(p)));cases+=1
                assert run('ek65',a.values()+[a.point(p)],a.m)==(offset==(0,0,0,0));cases+=1
            base.old.old.reject(lambda:run('ek6x',vs[:3]+[fn(sort(FIELD),forbidden),vs[4]],a.m)('x')(*map(c,(1,2,3,4))),unknown=True);cases+=1
            assert run('ek62',[],a.m)==(offset==(0,0,0,0));cases+=1
    a=Model()
    for i in range(4):
        offset=[0]*4;offset[i]=1;assert not run('ek62',[],a.m|{'eisxz':lambda:a.point(offset)});cases+=1
    for wrongaxis in ('x','y','z'):
        good=a.by['newelectric'];a.by['newelectric']=a.field(lambda axis,p:a.r(good(axis)(*map(a.c,p)))+(axis==wrongaxis))
        assert not run('ek65',a.values()+[a.point((1,2,3,4))],a.m);cases+=1;a.by['newelectric']=good
    return dict(cases=cases,nonuniform_fields_use_inverse_coordinates_and_correct_mixing_signs=True,all_four_origin_offsets_and_all_seven_equations_distinguished=True,zero_speed_and_free_offset_supported=True)

@lru_cache(None)
def binding_checks():
    a=Model();oldkey=a.key(a.values(SETTING));new=a.new();newkey=a.key([new[n] for n,t in SETTING]);restkey=a.key([new[n] for n,t in REST]);cases=0
    mm=a.m|{'ek6n':lambda *xs:a.key(xs)==oldkey,'ek6o':lambda *xs:a.key(xs)==oldkey,'ek3v':lambda *xs:a.key(xs)==newkey,'ek3r':lambda *xs:a.key(xs)==restkey}
    assert run('ek6z',a.values(),mm);cases+=1
    for n in BOUNDS['ek6z']:
        assert not run('ek6z',a.values(),mm|{n:lambda *xs:False});cases+=1
        base.old.old.reject(lambda:run('ek6z',a.values(),mm|{n:forbidden}),unknown=True);cases+=1
    def different(t):
        if t==sort(R):return a.c(17)
        if t=='truth':return False
        return fn(t,lambda *xs:different(t['result']))
    for i,(name,t) in enumerate(PAIR):
        vs=a.values();vs[i]='other' if t in ('a','d') else Q(17) if t=='b' else different(sort(t))
        assert not run('ek6z',vs,mm);cases+=1
    for physical in (False,True):
        for offset in ((0,0,0,0),(0,0,0,2)):
            assert run('ek63',a.values(),a.m|{'ek6z':lambda *xs:physical,'eisxz':lambda:a.point(offset)})==(physical and offset==(0,0,0,0));cases+=1
    rows=[]
    def equality(actual,computed,region):rows.append((a.key(actual),a.key(computed),a.key(region)));return True
    assert run('ek64',a.values(),a.m|{'ejs3':equality});cases+=1
    assert rows==[(a.key(a.by['newelectric']),a.key(a.by['newelectric']),a.key(new['region']))];cases+=1
    rows.clear();assert run('ek7z',a.values(),a.m|{'ejs3':equality});cases+=1
    assert rows==[(a.key(a.by['newmagnetic']),a.key(a.by['newmagnetic']),a.key(new['region']))];cases+=1
    for electric in (False,True):
        for magnetic in (False,True):
            assert run('ek72',a.values(),{'ek66':lambda *xs:electric,'ek7z':lambda *xs:magnetic})==(electric and magnetic);cases+=1
    # Independent new fields and the equations must stay outside the setup.
    assert run('ek6z',a.values(),mm|{'ek3t':forbidden,'ejs3':forbidden});cases+=1
    return dict(cases=cases,all_42_roles_shared_with_independent_new_fields_and_native_setting=True,charge_mass_units_event_and_new_histories_preserved=True,neither_dynamics_nor_field_transform_assumed_by_physical_setup=True)

@lru_cache(None)
def initial_checks():
    a=Model();c,r=a.c,a.r;cases=0;registry={};domain=a.domain(-3,3)
    def polynomial(coefficients):
        def value(t):return c(analytic.poly_value(coefficients,r(t)))
        registry[value]=tuple(map(Q,coefficients));return fn(sort(PROFILES[0][1]),value)
    ds={d['name']:d for d in core()['declarations']};rem=ds['ek7a'];small=ds['ek7b']
    def find(node,symbol):
        if isinstance(node,list):
            for x in node:
                found=find(x,symbol)
                if found:return found
        if isinstance(node,dict):
            if node.get('kind')=='call' and node.get('symbol')==symbol:return node
            return find(list(node.values()),symbol)
    domain_ast=find(small['body'],'sjr')['arguments'][0]
    def limit(dom,function,initial,value):
        dc=analytic.free(analytic.unwrap(dom));fc=analytic.free(analytic.unwrap(function))
        if dc.get('node')!=domain_ast or fc.get('node')!=rem['body']:forbidden()
        env=fc['captured'];vel=analytic.unwrap(env[rem['parameters'][0]['name']]).implementation
        if vel not in registry:forbidden()
        origin=r(env[rem['parameters'][1]['name']]);acc=r(env[rem['parameters'][2]['name']])
        denv=dc['captured'];original=analytic.unwrap(denv[small['parameters'][0]['name']])
        if original.implementation!=analytic.unwrap(domain).implementation:forbidden()
        assert r(denv[small['parameters'][2]['name']])==origin==r(initial)
        return -3<origin<3 and analytic.poly_value(analytic.derivative(registry[vel]),origin)-acc==r(value)
    mm=a.m|{'senz':lambda dom,t:analytic.unwrap(dom).implementation==analytic.unwrap(domain).implementation and -3<r(t)<3,'sjr':limit}
    for coefficients in ((2,3),(2,3,4),(-1,0,0,2)):
        velocity=polynomial(coefficients)
        for origin in (-1,0,1):
            acc=analytic.poly_value(analytic.derivative(coefficients),origin)
            for proposed,want in ((acc,True),(acc+1,False)):
                assert run('ek7b',[domain,velocity,c(origin),c(proposed)],mm)==want;cases+=1
            error=run('ek7a',[velocity,c(origin),c(acc)],a.m)
            for h in (Q(1,2),Q(1,10),Q(1,100)):
                expected=(analytic.poly_value(coefficients,origin+h)-analytic.poly_value(coefficients,origin)-acc*h)/h
                assert r(error(c(origin+h)))==expected;cases+=1
    base.old.old.reject(lambda:run('ek7b',[domain,fn(sort(PROFILES[0][1]),forbidden),c(0),c(1)],mm),unknown=True);cases+=1
    base.old.old.reject(lambda:run('ek7b',[domain,polynomial((0,1)),c(0),c(1)],mm,'native'));cases+=1
    # Native numeric three equations; only the previously checked derivative
    # and small-time relations are boundary interpretations here.
    a.by['newelectric']=a.field(lambda axis,p:{'x':0,'y':Q(-25,12),'z':Q(25,6)}.get(axis,0))
    new=a.new();future=a.key([new[n] for n,t in FUTURE]);smallrows={a.key([new['domain'],new[n],c(0),new[acc]]) for (n,t),(acc,s) in zip(PROFILES,ACCEL)}
    oldfuture=a.key(a.values(FUTURE));oldrows={a.key([a.by['domain'],a.by[n],c(0),a.by[acc]]) for (n,t),(acc,s) in zip(PROFILES,ACCEL)}
    oldmm=a.m|{'ek32':lambda *xs:a.key(xs)==oldfuture,'ek7b':lambda *xs:a.key(xs) in oldrows}
    assert run('ek74',a.values(SETTING),oldmm);cases+=1
    for relation in ('ek32','ek7b'):
        assert not run('ek74',a.values(SETTING),oldmm|{relation:lambda *xs:False});cases+=1
    for name in ('domain','velocityx','velocityy','velocityz','ax','ay','az'):
        values=a.values(SETTING);i=[n for n,t in SETTING].index(name);values[i]=a.new()[name] if name=='domain' else c(37) if name in ('ax','ay','az') else fn(sort(PROFILES[0][1]),lambda t:c(37))
        if name=='domain':values[i]=a.domain(10,12)
        assert not run('ek74',values,oldmm);cases+=1
    mm=a.m|{'ek32':lambda *xs:a.key(xs)==future,'ek7b':lambda *xs:a.key(xs) in smallrows,'ek74':lambda *xs:a.key(xs)==a.key(a.values(SETTING))}
    assert run('ek7c',a.values(),mm);cases+=1
    for n,t in ACCEL:
        vs=a.values();i=[name for name,t in PAIR].index('new'+n);vs[i]=c(r(vs[i])+1)
        assert not run('ek7c',vs,mm);cases+=1
    for relation in ('ek32','ek7b','ek74'):
        assert not run('ek7c',a.values(),mm|{relation:lambda *xs:False});cases+=1
    return dict(cases=cases,registered_polynomial_first_order_remainders_not_sample_fitted=True,nonzero_higher_order_terms_allowed=True,three_native_equations_and_future_derivatives_share_accelerations=True,original_small_t_and_comoving_tau_have_separate_initial_conditions=True,native_real_limit_enumeration_refused=True)

@lru_cache(None)
def presentation_checks():
    cases=0
    quantities={('tauname','ek7d','ek7e','paper','tenth','case'),('newE1','ek7d','ek7f','paper','tenth','case'),('newE2','ek7d','ek7g','paper','tenth','case'),('newE3','ek7d','ek7h','paper','tenth','case'),('charge_name','ek7d','ek37','paper','tenth','case'),('mass_name','ek7d','ek4b','paper','tenth','case'),('betaname','ek7d','ek7i','paper','tenth','case'),('lightname','ek7d','ek7j','paper','tenth','case')}
    groups=[('ek7k',{'eiswy':quantities,'eiswz':{('newcoordinates',('x','y','z'),'ek7d','ek4a','paper','tenth','case')},'eisd4':{('notation','author','kname','comoving','paper','case')}}),
     ('ek7o',{'zc':{('initialintro','author','ek7n','ek7m','tenth','case')},'uh':{('initialintro','author','ek7m','tenth','case')},'zdg':{('initialintro','author','ek7m','tenth','case')},'eisra':{('initialintro','author','paper','assumption','ek4f','ek7n','tenth','case')},'eisch':{('relativity','eifj','tenth','case')},'eisox':{('equations','ek7m','case')},'uf':{('author','initialintro','equations','case')},'ue':{('initialintro','equations','case')}}),
     ('ek7r',{'uf':{('author','notation','equations','case')},'ue':{('equations','notation','case')}}),
     ('ek7t',{'ug':{('originchoice','author','ek7l','tenth','case')},'eisra':{('originchoice','author','paper','choice','ek6k','ek7l','tenth','case')}}),
     ('ek7u',{'zc':{('transformintro','author','ek7l','ek73','tenth','case'),('transformintro','author','ek73','ek7s','tenth','case')},'uh':{('transformintro','author','ek73','tenth','case'),('transformintro','author','ek7s','tenth','case')},'eisov':{('transformintro','author','third','ejeh','paper','case'),('transformintro','author','sixth','ejvm','paper','case')},'eisox':{('transformdisplay','ek7s','case')},'uf':{('author','transformintro','transformdisplay','case')}}),
     ('ek7v',{'ue':{('notation','originchoice','case'),('originchoice','transformintro','case'),('transformintro','transformdisplay','case')}}),
     ('ek7q',{'eir3':{('initialintro','author','paper','ek7p','case')},'ue':{('restclaim','initialintro','case')}}),
     ('ek7x',{'eir3':{('notation','author','paper','ek7w','case')},'ue':{('equations','notation','case')}})]
    for root,rows in groups:
        evaluated={'ek7r':('ek7k',),'ek7v':('ek7r','ek7t','ek7u')}.get(root,())
        mm={n:relation(rs) for n,rs in rows.items()}|{n:lambda:Content(('case','other'),(True,False)) for n in evaluated}
        cases+=perturb(lambda patch:run(root,[],patch),mm,rows)
        assert run(root,[],mm|{n:forbidden for n in BOUNDS[root] if n not in evaluated});cases+=1
        for n in evaluated:assert not run(root,[],mm|{n:lambda:Content(('case','other'),(False,True))});cases+=1
    for n in ('ek35','eifj','ek6r','ek7l'):
        mm={x:lambda:Content(('case','other'),(True,False)) for x in ('ek35','eifj','ek6r','ek7l')}
        assert not run('ek7n',[],mm|{n:lambda:Content(('case','other'),(False,True))});cases+=1
    a=Model();new=a.new();values=[new[n] for n,t in SETTING]
    for root,axis in [('ek7f','x'),('ek7g','y'),('ek7h','z')]:assert a.r(run(root,values,a.m))==a.r(new['electricfield'](axis)(*map(a.c,a.offset)));cases+=1
    assert a.r(run('ek7e',values,a.m))==0 and a.r(run('ek7i',values,a.m))==Q(5,4) and a.r(run('ek7j',values,a.m))==5;cases+=3
    assert run('ek7d',values,a.m|{'ek3v':lambda *xs:True});cases+=1
    for name in ('frame','matter','event'):
        wrong=values.copy();wrong[[n for n,t in SETTING].index(name)]='other';assert not run('ek7d',wrong,a.m|{'ek3v':lambda *xs:True});cases+=1
    return dict(cases=cases,assumption_principle_clarity_display_and_source_sections_distinct=True,seven_new_notations_and_same_charge_mass_connected=True,quoted_laws_not_executed=True)

@lru_cache(None)
def binder_checks():
    def transform(node):
        if node=='number':return 'individual'
        if isinstance(node,list):return [transform(x) for x in node]
        if not isinstance(node,dict):return node
        if node.get('kind')=='call' and node.get('symbol')=='bb':return dict(kind='call',symbol='jceunit',arguments=[])
        return {k:transform(x) for k,x in node.items()}
    cases=0
    for root,kind,target in [('ek7l','exists',None),('ek7m','forall','ek7c'),('ek7s','forall','ek66'),('ek73','forall','ek72')]:
        doc=collapse(transform(boundary(root)));doc['declarations'].append(dict(kind='primitive',name='jceunit',parameters=[],result='individual'));doc['declarations'].sort(key=lambda d:d['kind']!='primitive');doc=extract_document(doc,roots=[root],statement_indices=[]).document
        decl=next(d for d in doc['declarations'] if d['name']==root);binding=decl['body'];original=binding['body'];subtree=None
        if root=='ek7m':
            original=original['arguments'][1];subtree=(original,[dict(name=binding['variable'],sort='situation')])
        body=original;names=[]
        while body['kind'] in ('exists','forall'):names.append(body['variable']);body=body['body']
        assert len(names)==len(BOUND);mapping=dict(zip((n for n,t in BOUND),names))
        expected=[dict(kind='call',symbol='ra',arguments=[]) if n=='frame' else dict(kind='variable',name=binding['variable']) if n=='context' else dict(kind='call',symbol='jceunit',arguments=[]) if n=='electricconversion' else dict(kind='call',symbol='eisxv',arguments=[]) if n=='event' else dict(kind='variable',name=mapping['oldpoint' if n=='point' else n]) for n,t in PAIR]
        assert (body if kind=='exists' else body['arguments'][0])['arguments']==expected
        if target:assert body['arguments'][1]['arguments']==expected
        for pivot in range(len(BOUND)):
            f,d,slots,var,b=lifted(doc,root,pivot,len(BOUND),kind,subtree=subtree)
            env={p['name']:'case' if p['sort']=='situation' else 'a' for p in d['parameters']};call=b if kind=='exists' else b['arguments'][0]
            def rows(picks):return {tuple((env|{var:p})[x['name']] if x['kind']=='variable' else 'a' for x in call['arguments']) for p in picks}
            scenarios=[((),(),False),(('a',),(),True),(('b',),(),True)] if kind=='exists' else [(('a','b'),('a','b'),True),(('a','b'),('a',),False),(('b',),('a',),False),((),(),True)]
            for selected,accepted,want in scenarios:
                mm={n:lambda x=env[p['name']]:x for n,p in zip(slots,d['parameters'])}|{'ra':lambda:'a','eisxv':lambda:'a','jceunit':lambda:'a','ek63':lambda *xs:xs in rows(selected)}
                if target:mm[target]=lambda *xs:xs in rows(accepted)
                meanings={x['name']:mm.get(x['name'],forbidden) for x in f['declarations'] if x['kind']=='primitive'}
                assert evaluate_document(f,individuals=('a','b'),situations=('case','other'),primitives=meanings,max_steps=25000)[0]['value']==want;cases+=1
    for root in ('ek7l','ek7m','ek7s','ek73'):
        base.old.old.reject(lambda:run(root,[],{'ek7l':lambda:Content(('case','other'),(True,False))}));cases+=1
    # One complete finite diagnostic of the all-location scope, with abstract
    # points and fixed settings; no finite sampling of the actual point domain.
    doc=collapse(transform(boundary('ek66')));d=next(x for x in doc['declarations'] if x['name']=='ek66')
    slots=['jcebind'+number_word(i) for i in range(len(d['parameters']))];doc['declarations'] += [dict(kind='primitive',name=n,parameters=[],result=p['sort']) for n,p in zip(slots,d['parameters'])];doc['declarations'].sort(key=lambda d:d['kind']!='primitive')
    doc['statements']=[dict(kind='ask',body=dict(kind='call',symbol='ek66',arguments=[dict(kind='call',symbol=n,arguments=[]) for n in slots]))]
    for selected,good,want in [(('a','b'),('a','b'),True),(('a','b'),('a',),False),(('b',),('a',),False),((),(),True)]:
        mm={n:lambda x=('case' if p['sort']=='situation' else 'a'):x for n,p in zip(slots,d['parameters'])}|{'ek64':lambda *xs:True,'ejsj':lambda point,region:point in selected,'ek65':lambda *xs:xs[-1] in good}
        assert evaluate_document(doc,individuals=('a','b'),situations=('case','other'),primitives=mm,max_steps=25000)[0]['value']==want;cases+=1
    return dict(cases=cases,all_38_witness_slots_and_42_shared_roles_checked=True,all_location_scope_not_only_particle_origin=True,two_value_binding_diagnostics_not_full_function_proofs=True)

@lru_cache(None)
def source_record():
    inv=json.loads(read(INVENTORY));units=inv['units'][245:249];assert [u['id'] for u in units]==[f'einstein-1905:u{i:04}' for i in range(246,250)]
    rows=[]
    for u in units:
        assert digest(u['text'].encode())==u['text_sha256'];ms=[m for m in inv['math'] if m['id'] in u['math_ids']]
        for m in ms:assert digest(m['mathml'].encode())==m['sha256']
        rows.append(dict(unit=u['id'],text=u['text'],unit_sha256=u['text_sha256'],range=[0,len(u['text'])],math=ms,source_nonblank_characters=len(re.sub(r'\s|\[M\d+\]','',u['text']))))
    previous='data/einstein-electron-comoving-equations-reading-v1.json'
    return dict(version='einstein-electron-comoving-equations-reading-v2',units=rows,
        collation=[dict(math='M0406',transcription='t',facsimile='t',reading='原刊もt。v1の原刊τという記録を撤回する'),dict(math='M0409',transcription='ξ,η,ζ,X′,Y′,Z′',facsimile='ξ,η,ζ,τ,X′,Y′,Z′',reading='原刊のτを含む七記号を採る')],
        correction=dict(supersedes=previous,reason='原刊918頁とPDF第28頁を視認し、M0406のtを再確認した。旧記録・旧判断は保存し、四単位を訂正版で再判断する。',source_time='t',comoving_derivative_time='τ'),
        observations=LIMITS,source_sha256={p:digest((ROOT/p).read_bytes()) for p in (INVENTORY,FACSIMILE,'artifacts/written-facsimiles-v1/einstein-1905-unlp.pdf',DOC,previous)})

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    before=load_catalog(ROOT,PARENT_BASIS);after=load_catalog(ROOT,BASIS)
    assert len(after.document['statements'])==421 and after.document['statements'][:419]==before.document['statements']
    assert after.document['declarations'][:len(before.document['declarations'])]==before.document['declarations']
    assert all(after.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in before.entries.items())
    assert selection_binding(after,[417,418])==selection_binding(before,[417,418]);load_annotations(ROOT,BASIS,ANNOTATIONS)
    assert json.loads(read(ANNOTATIONS))['entries'][:-7]==json.loads(read('data/electron-coordinate-claim-identifiers-v1.json'))['entries']
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    for style in ('compact','full'):
        body=format_graph(core(),style);assert parse(body)==parse(transcribe(body,alphabet='v2'))==core()
    assert json.loads(read(SOURCE))==source_record()
    return dict(new_definitions=len(MEANINGS),new_general_relations=0,new_reference_constants=len(REFERENCES),new_statements=2,all_419_prior_statements_and_meanings_preserved=True)
def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/SOURCE,json.dumps(source_record(),ensure_ascii=False,indent=2)+'\n')
@lru_cache(None)
def build_report():
    results={n:f() for n,f in [('transforms',transform_checks),('connections',binding_checks),('initial',initial_checks),('presentation',presentation_checks),('binders',binder_checks),('structure',structure_checks)]}
    helpers=('compose_electron_comoving_equations','compose_limits','compose_material_relative_frame','compose_point_particle_dynamics','compose_electron_rest_law_claim','compose_material_velocity','compose_field_equations','compose_doppler_infinity','compose_relativity_conjecture','compose_two_postulates','check_electron_coordinate_normalization','check_electron_coordinate_claim','check_material_acceleration','check_point_particle_dynamics','check_attached_material_charge','check_clock_site_time','check_rod_methods','check_ninth_section_opening','check_problem_series_reduction','audit_opening_scope')
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(source_record()['source_sha256'])|{SOURCE,*DEPENDENCIES,'scripts/compose_electron_comoving_equations_v2.py','scripts/check_electron_comoving_equations_v2.py','tests/test_electron_comoving_equations_v2.py',*(f'scripts/{n}.py' for n in helpers)}
    return dict(status='original_small_t_corrected_with_separate_comoving_tau_initial_equations',document=FULL,**results,verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
