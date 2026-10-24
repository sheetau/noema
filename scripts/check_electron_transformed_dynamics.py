"""Check actual two-frame derivatives, equation (A), and the same law candidate."""
from fractions import Fraction as Q
from functools import lru_cache
from copy import deepcopy
import json,re
from noema.grammar import parse,format_graph,number_word
from noema.extraction import extract_document
from noema.finite_semantics import FunctionValue,Content,evaluate_document
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts import check_electron_comoving_equations_v2 as prior
from scripts import check_material_acceleration as analytic
from scripts.check_clock_site_time import relation,perturb
from scripts.check_ninth_section_opening import lifted
from scripts.check_problem_series_reduction import collapse
from scripts.compose_electron_transformed_dynamics import *

DOC='docs/electron-transformed-dynamics-v1.md';SOURCE='data/einstein-electron-transformed-dynamics-reading-v1.json'
INVENTORY='artifacts/written-units-v1/einstein-1905.json';FACSIMILE='artifacts/written-facsimiles-v1/einstein-p918-0.jpg'
DEPENDENCIES=('reports/electron-comoving-equations-v2.json','reports/electron-moving-law-task-v1.json','reports/electron-comoving-history-v1.json','reports/material-acceleration-v1.json')
fn=prior.fn;sort=prior.sort;forbidden=prior.forbidden
CONSTANTS=prior.CONSTANTS|{'eisyl':'derive','eisym':'Adisplay','eisyn':'Alaw','eisyo':'Alabel'}
PEOPLE=tuple(dict.fromkeys([*prior.PEOPLE,*CONSTANTS.values(),'rep1','rep2']))
BOUNDS={'ek76':{'seob','senz','sjs','sepn'},'ek77':{'ek63','ek76','ek75'},'elb':{'ek74'},'elc':{'ek6f'},'eld':{'elb'},'ele':{'elc','eld'},'elf':{'elb','ek4w'},'elg':{'ek63','ek7c','ek66'},'elh':{'elg','ek75','elb'},'eli':{'ek7m','ek7s'},'elj':{'ek7l','ek63','ek75','elb'},'elk':{'ek63','elb'},'ell':{'ele','ek63','elf'},'elm':{'elk','ell'},'eln':{'eli','elj','elm','ek7s','ek7m','ek4y','elk'},'elp':{'elo'}}
@lru_cache(None)
def core():return parse(read(CORE))
@lru_cache(None)
def boundary(root,mode='boundary'):
    doc=extract_document(core(),roots=[root],statement_indices=[]).document
    cuts=prior.base.BOUNDS|BOUNDS.get(root,set())
    if mode=='native':cuts-= {'sjs','senz','sepn','seob'}
    for i,d in enumerate(doc['declarations']):
        if d['kind']=='definition' and d['name'] in cuts:doc['declarations'][i]=dict(kind='primitive',name=d['name'],parameters=[p['sort'] for p in d['parameters']],result=d['result'])
    return extract_document(doc,roots=[root],statement_indices=[]).document
@lru_cache(None)
def fixture(root,mode='boundary'):
    doc=deepcopy(boundary(root,mode));d=next(x for x in doc['declarations'] if x['name']==root);slots=[]
    for i,p in enumerate(d['parameters']):
        n='jdyn'+number_word(i);slots.append(n);doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']))
    expression=dict(kind='call',symbol=root,arguments=[dict(kind='call',symbol=n,arguments=[]) for n in slots])
    if d['result']=='content':
        doc['declarations'].append(dict(kind='primitive',name='jdynpoint',parameters=[],result='situation'));expression=dict(kind='evaluate',content=expression,situation=dict(kind='call',symbol='jdynpoint',arguments=[]))
    doc['declarations'].sort(key=lambda x:x['kind']!='primitive');doc['statements']=[dict(kind='ask',body=expression)];return doc,slots
def run(root,values,m,mode='boundary'):
    doc,slots=fixture(root,mode);assert len(slots)==len(values)
    mm={n:lambda x=x:x for n,x in CONSTANTS.items()}|{'jdynpoint':lambda:'case'}|m|{n:lambda x=x:x for n,x in zip(slots,values)}
    return evaluate_document(doc,individuals=PEOPLE,situations=('case','other'),primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=3000000,memoize_definitions=True,memoize_expressions=True)[0]['value']
def reject(f):
    try:f()
    except ValueError as exc:assert 'Unknown' in str(exc) or 'Unregistered' in str(exc) or 'Cannot finitely quantify' in str(exc),str(exc)
    else:raise AssertionError('Unknown or full-domain input was accepted')

def add(a,b):return analytic.trim((a[i] if i<len(a) else 0)+(b[i] if i<len(b) else 0) for i in range(max(len(a),len(b))))
def mul(a,b):
    result=[Q(0)]*max(0,len(a)+len(b)-1)
    for i,x in enumerate(a):
        for j,y in enumerate(b):result[i+j]+=x*y
    return analytic.trim(result)
class Rational:
    """Retained coefficients, exact quotient differentiation, and known poles."""
    def __init__(self,numerator,denominator=(1,),poles=()):
        self.n=analytic.trim(numerator);self.d=analytic.trim(denominator);self.poles=tuple(map(Q,poles));assert self.d
    def value(self,t):return analytic.poly_value(self.n,t)/analytic.poly_value(self.d,t)
    def derivative(self):return Rational(add(mul(analytic.derivative(self.n),self.d),tuple(-x for x in mul(self.n,analytic.derivative(self.d)))),mul(self.d,self.d),self.poles)
    def same(self,other):return mul(self.n,other.d)==mul(other.n,self.d)
    def regular(self,lo,hi):return not any(lo<p<hi for p in self.poles)

class Model(prior.Model):
    def __init__(self,speed=3,A=1,B=2,C=-3):
        super().__init__(speed);c,r=self.c,self.r;beta=self.beta;speed=Q(speed);A,B,C=map(Q,(A,B,C));b=beta*beta*speed*A/25
        def inverse(value):
            if r(value)==0:raise ValueError('Unknown reciprocal outside the nonzero numerical domain')
            return c(1/r(value))
        self.m['sjd']=inverse
        self.polynomials={};self.curves={};self.domains={};self.derivative_calls=[]
        oldpole=() if not b else (-1/b,);newpole=() if not b else (1/(beta*b),)
        old=[Rational((0,speed,speed*b+A),(1,b),oldpole),Rational((0,0,B),(1,b),oldpole),Rational((0,0,C),(1,b),oldpole),Rational((0,1))]
        new=[Rational((0,0,beta**3*A),(1,-beta*b),newpole),Rational((0,0,beta**2*B),(1,-beta*b),newpole),Rational((0,0,beta**2*C),(1,-beta*b),newpole),Rational((0,1))]
        h=Q(1,1)/(1+4*abs(b));self.oldbounds=(-h,h);tau=lambda t:t/(beta*(1+b*t));self.newbounds=(tau(-h),tau(h))
        self.oldcoeff=old;self.newcoeff=new;self.b=b
        self.by.update(domain=self.register_domain(*self.oldbounds),curve=self.register_curve(old))
        self.newdomain=self.register_domain(*self.newbounds);self.newcurve=self.register_curve(new)
        for prefix,coefficients in (('',old),('new',new)):
            for (name,t),(acc,s),p in zip(PROFILES,ACCEL,coefficients):
                self.by[prefix+name]=self.register_function(p.derivative());self.by[prefix+acc]=c(p.derivative().derivative().value(0))
        self.m|={'eisx2':lambda:self.newdomain,'eisx3':lambda:self.newcurve,'seob':self.history,'senz':self.interior,'sjs':self.first,'sepn':self.derivative_field,'zpb':self.location}
        # Independently chosen fields with a baseline satisfying (A), plus
        # nonuniform spatial/time terms. Neither field is a language definition.
        acc=(2*A,2*B,2*C);mu=r(self.by['mass']);charge=r(self.by['charge']);mag=(7,11,13)
        electric=(mu/charge*beta**3*acc[0],mu/charge*beta*acc[1]+speed*mag[2]/5,mu/charge*beta*acc[2]-speed*mag[1]/5)
        self.by['electricfield']=self.field(lambda axis,p:electric[('x','y','z').index(axis)]+p[0]+2*p[1]-p[2]+p[3] if axis in ('x','y','z') else 0)
        self.by['magneticfield']=self.field(lambda axis,p:mag[('x','y','z').index(axis)]+2*p[0]-p[3] if axis in ('x','y','z') else 0)
    def register_domain(self,lo,hi):
        def f(t):return lo<self.r(t)<hi
        self.domains[f]=(lo,hi);return fn(sort(DOMAIN),f)
    def register_function(self,p):
        def f(t):return self.c(p.value(self.r(t)))
        self.polynomials[f]=p;return fn(sort(PROFILES[0][1]),f)
    def register_curve(self,coefficients):
        def f(t):return self.point([p.value(self.r(t)) for p in coefficients])
        self.curves[f]=coefficients;return fn(sort(CURVE),f)
    def rational(self,f):return analytic.PolynomialModel.polynomial(self,f)
    def bounds(self,domain):
        result=self.domains.get(analytic.unwrap(domain).implementation)
        if result is None:raise ValueError('Unknown rational-history domain')
        return result
    def interior(self,domain,time):lo,hi=self.bounds(domain);return lo<self.r(time)<hi
    def first(self,domain,function,time,value):
        p=self.rational(function);lo,hi=self.bounds(domain);self.derivative_calls.append((self.r(time),p.derivative().value(self.r(time))))
        return p.regular(lo,hi) and self.interior(domain,time) and p.derivative().value(self.r(time))==self.r(value)
    def derivative_field(self,domain,function,profile):
        p=self.rational(function);dp=self.rational(profile);lo,hi=self.bounds(domain)
        return p.regular(lo,hi) and dp.regular(lo,hi) and p.derivative().same(dp)
    def history(self,matter,frame,context,domain,curve):
        if (matter,context)!=('matter','case') or frame not in ('frame','comoving'):return False
        wanted=self.by if frame=='frame' else self.new()
        return all(analytic.unwrap(x).implementation==analytic.unwrap(wanted[n]).implementation for n,x in [('domain',domain),('curve',curve)])
    def location(self,matter,frame,event,point,context):return (matter,frame,event,context) in {('matter','frame','event','case'),('matter','comoving','event','case')} and self.pv(point)==(0,0,0,0)

@lru_cache(None)
def equation_checks():
    cases=0
    for speed in (0,3):
        for A in (0,1,Q(-1,2)):
            a=Model(speed,A);c,r=a.c,a.r
            assert run('ek75',a.values(),a.m);assert run('ela',a.values(SETTING),a.m);cases+=2
            assert prior.run('ek7c',a.values(),a.m|{'ek32':lambda *xs:True,'ek7b':lambda *xs:True,'ek74':lambda *xs:True});cases+=1
            for name,t in ACCEL:
                for prefix,root in (('new','ek75'),('','ela')):
                    fields=PAIR if prefix else SETTING;values=a.values(fields);i=[n for n,t in fields].index(prefix+name);values[i]=c(r(values[i])+1)
                    assert not run(root,values,a.m);cases+=1
            for axis in ('x','y','z'):
                old=a.by['electricfield'];a.by['electricfield']=a.field(lambda ax,p:a.r(old(ax)(*map(c,p)))+(ax==axis))
                assert not run('ela',a.values(SETTING),a.m);cases+=1;a.by['electricfield']=old
            if speed:
                for axis in ('y','z'):
                    old=a.by['magneticfield'];a.by['magneticfield']=a.field(lambda ax,p:a.r(old(ax)(*map(c,p)))+(ax==axis))
                    assert not run('ela',a.values(SETTING),a.m);cases+=1;a.by['magneticfield']=old
            for mass in (0,-1):
                values=a.values(SETTING);values[[n for n,t in SETTING].index('mass')]=c(mass)
                # The evaluator eagerly evaluates the displayed reciprocal.
                # Zero is outside its numerical domain, not a false example
                # whose undefined quotient may be silently assigned a value.
                if mass==0:reject(lambda:run('ela',values,a.m))
                else:assert not run('ela',values,a.m)
                cases+=1
            reject(lambda:run('ela',a.values(SETTING),a.m|{'soy':forbidden}));cases+=1
    return dict(cases=cases,all_three_equations_signs_and_denominators_distinguished=True,zero_speed_and_nonzero_longitudinal_acceleration=True,zero_mass_undefined_quotient_refused=True)

@lru_cache(None)
def history_checks():
    cases=0
    for speed in (0,3):
        for A in (0,1,Q(-1,2)):
            a=Model(speed,A);c,r=a.c,a.r
            assert run('ek76',a.values(),a.m);cases+=1
            assert len(a.derivative_calls)>=12
            # Exact derivative of the retained coordinate-time transformation.
            clock=Rational((0,1/a.beta),(1,a.b),() if not a.b else (-1/a.b,))
            derivative=Rational((1/a.beta,),mul((1,a.b),(1,a.b)),clock.poles)
            assert clock.derivative().same(derivative) and derivative.value(0)==1/a.beta;cases+=1
            for t in (a.oldbounds[0]/2,Q(0),a.oldbounds[1]/2):
                tau=clock.value(t);point=a.pv(a.by['curve'](c(t)));mapped=a.mapped(point)
                assert a.pv(a.newcurve(c(tau)))==mapped and a.inverse(mapped)==point;cases+=1
                shared=[c(5),c(speed),a.point((0,0,0,0)),a.by['domain'],a.by['curve'],a.newdomain,a.newcurve]
                assert run('ek5q',shared+[c(t)],a.m) and run('ek5r',shared+[c(tau)],a.m);cases+=2
            for prefix in ('','new'):
                for name,t in ACCEL:
                    values=a.values();i=[n for n,t in PAIR].index(prefix+name);values[i]=c(r(values[i])+1)
                    assert not run('ek76',values,a.m);cases+=1
                for name,t in PROFILES:
                    values=a.values();i=[n for n,t in PAIR].index(prefix+name)
                    p=a.rational(values[i]);alias=Rational((0,4,0,-5,0,1));bad=Rational(add(mul(p.n,alias.d),mul(alias.n,p.d)),mul(p.d,alias.d),p.poles)
                    values[i]=a.register_function(bad);assert not run('ek76',values,a.m);cases+=1
            for key in ('seob','sjs','sepn'):
                reject(lambda:run('ek76',a.values(),a.m|{key:forbidden}));cases+=1
    a=Model();reject(lambda:run('ek76',a.values(),a.m,'native'));cases+=1
    values=a.values();values[[n for n,t in PAIR].index('velocityx')]=fn(sort(PROFILES[0][1]),forbidden)
    reject(lambda:run('ek76',values,a.m));cases+=1
    return dict(cases=cases,retained_rational_histories_and_exact_quotient_derivatives=True,both_native_sepp_bodies_checked=True,sample_alias_velocity_fields_rejected=True,physical_history_is_explicit_model_input=True,full_real_limits_not_certified=True)

@lru_cache(None)
def connection_checks():
    a=Model();key=a.key;vs=a.values();old=key(a.values(SETTING));pair=key(vs);cases=0
    for root,relations in [('elg',('ek63','ek7c','ek66')),('elh',('elg','ek75','elb')),('ek77',('ek63','ek76','ek75'))]:
        mm={n:lambda *xs,n=n:key(xs)==(old if n=='elb' else pair) for n in relations}
        assert run(root,vs,a.m|mm);cases+=1
        for n in relations:
            result=run(root,vs,a.m|mm|{n:lambda *xs:False})
            expected=(root=='ek77' and n in ('ek63','ek76')) or (root=='elh' and n=='elg')
            assert result==expected,(root,n);cases+=1
            reject(lambda:run(root,vs,a.m|mm|{n:forbidden}));cases+=1
    def different(t):
        if t==sort(R):return a.c(37)
        if t=='truth':return False
        return fn(t,lambda *xs:different(t['result']))
    mm={n:lambda *xs:key(xs)==pair for n in ('ek63','ek7c','ek66')}
    for i,(name,t) in enumerate(PAIR):
        changed=vs.copy();changed[i]='other' if t in ('a','d') else Q(37) if t=='b' else different(sort(t))
        assert not run('elg',changed,a.m|mm),(name,'shared argument not distinguished');cases+=1
    for physical in (False,True):
        for speed,want in ((0,True),(3,True),(5,False),(-3,False)):
            assert run('elc',a.values(SETTING),a.m|{'eisxt':lambda:a.c(speed),'ek6f':lambda *xs:physical})==(physical and want);cases+=1
    new=a.new();rows={key(a.values(AT)),key([new[n] for n,t in AT])}
    # Independently inspect both native calls without assuming derivative truth.
    doc=boundary('ek76');calls=[]
    def walk(x):
        if isinstance(x,dict):
            if x.get('kind')=='call' and x.get('symbol')=='sepp':calls.append(x)
            for y in x.values():walk(y)
        elif isinstance(x,list):
            for y in x:walk(y)
    walk(next(d for d in doc['declarations'] if d['name']=='ek76')['body']);assert len(calls)==2;cases+=1
    for value in (False,True):
        assert run('elb',a.values(SETTING),a.m|{'ek74':lambda *xs:key(xs)==old and value})==value;cases+=1
        assert run('elf',a.values(SETTING)+['Alaw'],{'elb':lambda *xs:key(xs)==old,'ek4w':lambda *xs:key(xs)==old+('Alaw',) and value})==value;cases+=1
    return dict(cases=cases,shared_settings_and_native_derivative_direction=True,initial_condition_and_same_prior_law_candidate_required=True)

@lru_cache(None)
def law_checks():
    a=Model();old=a.key(a.values(SETTING));cases=0
    for selected in ((),('rep1',),('rep1','rep2')):
        for conforms in ((),('rep1',),('rep1','rep2')):
            for result in (False,True):
                mm={'eisxo':lambda rep,*xs:rep in selected and a.key(xs)==old,'vi':lambda law,rep,ctx:law=='Alaw' and rep in conforms and ctx=='case','elb':lambda *xs:a.key(xs)==old and result}
                want=bool(selected) and all((rep in conforms)==result for rep in selected)
                assert run('eld',a.values(SETTING)+['Alaw'],mm)==want;cases+=1
    mm={'eisxo':lambda rep,*xs:rep in ('rep1','rep2') and a.key(xs)==old,'vi':lambda law,rep,ctx:law=='Alaw' and ctx=='case','elb':lambda *xs:a.key(xs)==old}
    assert not run('eld',a.values(SETTING)+['other'],mm);cases+=1
    for n in mm:reject(lambda:run('eld',a.values(SETTING)+['Alaw'],mm|{n:forbidden}));cases+=1
    reject(lambda:run('ele',['Alaw','case'],{'elc':lambda *xs:True,'eld':lambda *xs:True}));cases+=1
    return dict(cases=cases,nonempty_all_corresponding_representations=True,conformity_equivalent_to_actual_equations_including_false_cases=True,same_law_held_outside_all_settings=True)

@lru_cache(None)
def presentation_checks():
    rows={'zc':{('derive','author','eli','elj','tenth','case'),('derive','author','elj','elm','tenth','case')},'uh':{('derive','author','elm','tenth','case')},'eiswm':{('derive','author','transformdisplay','ek7s','paper','case'),('derive','author','equations','ek7m','paper','case')},'eisov':{('derive','author','transformdisplay','ek7s','paper','case')},'eisd4':{('derive','author','kname','comoving','paper','case'),('derive','author','Kname','frame','paper','case')},'eisra':{('derive','author','paper','task','ek4y','elm','tenth','case')},'eisox':{('Adisplay','elk','case')},'eisch':{('Alabel','elk','tenth','case')},'uf':{('author','derive','Adisplay','case')},'ue':{('derive','Adisplay','case')}}
    mm={n:relation(rs) for n,rs in rows.items()};cases=perturb(lambda m:run('eln',[],m),mm,rows)
    assert run('eln',[],mm|{n:forbidden for n in BOUNDS['eln']});cases+=1
    rows={'eir3':{('derive','author','paper','elo','case')},'ue':{('transformdisplay','derive','case')}};mm={n:relation(rs) for n,rs in rows.items()}
    cases+=perturb(lambda m:run('elp',[],m),mm,rows)
    for root,names in [('eli',('ek7m','ek7s')),('elm',('elk','ell'))]:
        mm={n:lambda:Content(('case','other'),(True,False)) for n in names};assert run(root,[],mm);cases+=1
        for n in names:assert not run(root,[],mm|{n:lambda:Content(('case','other'),(False,True))});cases+=1
    return dict(cases=cases,source_equations_method_and_target_display_distinct=True,formula_label_and_prior_law_question_connected=True,quoted_physics_not_executed=True)

@lru_cache(None)
def binder_checks():
    def transform(node):
        if node=='number':return 'individual'
        if isinstance(node,list):return [transform(x) for x in node]
        if not isinstance(node,dict):return node
        if node.get('kind')=='call' and node.get('symbol')=='bb':return dict(kind='call',symbol='jdynunit',arguments=[])
        return {k:transform(x) for k,x in node.items()}
    cases=0
    for root,count,targets in [('ele',len(SETTING)-1,('elc','eld')),('elj',len(BOUND),('ek63','ek75','elb')),('elk',len(BOUND),('ek63','elb')),('ell',len(BOUND),('ek63','elf'))]:
        doc=collapse(transform(boundary(root)));doc['declarations'].append(dict(kind='primitive',name='jdynunit',parameters=[],result='individual'));doc['declarations'].sort(key=lambda x:x['kind']!='primitive');doc=extract_document(doc,roots=[root],statement_indices=[]).document
        d=next(x for x in doc['declarations'] if x['name']==root);sub=None
        if root in ('elj','ell'):binding=d['body'];sub=(binding['body']['arguments'][1],[dict(name=binding['variable'],sort='situation')])
        # Contract is derived from the public role lists, not the calls being
        # tested. Compact formatting may rename variables, so map by position.
        body=sub[0] if sub else d['body'] if root=='ele' else d['body']['body'];names=[]
        for _ in range(count):names.append(body['variable']);body=body['body']
        variable=lambda name:dict(kind='variable',name=name)
        constant=lambda name:dict(kind='call',symbol=name,arguments=[])
        if root=='ele':
            mapping=dict(zip((n for n,t in SETTING if n!='context'),names))
            expected=[variable(d['parameters'][1]['name'] if n=='context' else mapping[n]) for n,t in SETTING]
            contracts={'elc':expected,'eld':expected+[variable(d['parameters'][0]['name'])]}
        else:
            mapping=dict(zip((n for n,t in BOUND),names));context=d['body']['variable']
            fixed={'frame':constant('ra'),'event':constant('eisxv'),'electricconversion':constant('jdynunit'),'context':variable(context)}
            expected=[fixed[n] if n in fixed else variable(mapping['oldpoint' if n=='point' else n]) for n,t in PAIR]
            contracts={'ek63':expected,'ek75':expected,'elb':expected[:len(SETTING)],'elf':expected[:len(SETTING)]+[constant('eisyn')]}
        checked=set()
        def contract(node):
            if isinstance(node,dict):
                if node.get('kind')=='call' and node.get('symbol') in targets:
                    assert node['arguments']==contracts[node['symbol']],(root,node['symbol'],'role contract');checked.add(node['symbol'])
                for child in node.values():contract(child)
            elif isinstance(node,list):
                for child in node:contract(child)
        contract(body);assert checked==set(targets);cases+=1
        for pivot in range(count):
            f,d,slots,var,b=lifted(doc,root,pivot,count,'forall',sub)
            env={p['name']:'case' if p['sort']=='situation' else 'a' for p in d['parameters']}
            calls={}
            def walk(x):
                if isinstance(x,dict):
                    if x.get('kind')=='call' and x.get('symbol') in targets:calls[x['symbol']]=x['arguments']
                    for y in x.values():walk(y)
                elif isinstance(x,list):
                    for y in x:walk(y)
            walk(b);assert set(calls)==set(targets)
            def row(call,value):return tuple((env|{var:value})[x['name']] if x['kind']=='variable' else 'a' for x in call)
            for accepted,want in [(('a','b'),True),(('a',),False)]:
                mm={n:lambda x=env[p['name']]:x for n,p in zip(slots,d['parameters'])}|{n:lambda:'a' for n in ('ra','eisxv','eisyn','jdynunit')}
                mm|={n:lambda *xs,n=n:xs in {row(calls[n],value) for value in (('a','b') if n==targets[0] else accepted)} for n in targets}
                primitives={x['name']:mm.get(x['name'],forbidden) for x in f['declarations'] if x['kind']=='primitive'}
                # Some extra new-frame witnesses do not occur in the old-only
                # target; varying them cannot distinguish that target.
                depends=any(any(x.get('kind')=='variable' and x['name']==var for x in calls[n]) for n in targets[1:])
                expected=want if depends else True
                assert evaluate_document(f,individuals=('a','b'),situations=('case','other'),primitives=primitives,max_steps=25000)[0]['value']==expected,(root,pivot,accepted);cases+=1
    for root in ('elj','elk','ell'):reject(lambda:run(root,[],{'ek7l':lambda:Content(('case','other'),(True,False)),'ele':lambda *xs:True}));cases+=1
    return dict(cases=cases,all_32_law_scope_and_38_pair_binders_checked=True,old_and_new_roles_share_the_actual_binders=True,two_value_diagnostics_not_full_domain_proofs=True)

@lru_cache(None)
def source_record():
    inventory=json.loads(read(INVENTORY));rows=[]
    for unit in inventory['units'][249:251]:
        assert digest(unit['text'].encode())==unit['text_sha256'];math=[m for m in inventory['math'] if m['id'] in unit['math_ids']]
        for m in math:assert digest(m['mathml'].encode())==m['sha256']
        rows.append(dict(unit=unit['id'],text=unit['text'],unit_sha256=unit['text_sha256'],range=[0,len(unit['text'])],math=math,source_nonblank_characters=len(re.sub(r'\s|\[M\d+\]','',unit['text']))))
    assert [r['unit'] for r in rows]==['einstein-1905:u0250','einstein-1905:u0251']
    return dict(version='einstein-electron-transformed-dynamics-reading-v1',units=rows,observations=LIMITS,source_sha256={p:digest((ROOT/p).read_bytes()) for p in (INVENTORY,FACSIMILE,DOC,'data/einstein-electron-comoving-equations-reading-v2.json')})
@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    before=load_catalog(ROOT,PARENT_BASIS);after=load_catalog(ROOT,BASIS)
    assert len(after.document['statements'])==422 and after.document['statements'][:421]==before.document['statements']
    assert after.document['declarations'][:len(before.document['declarations'])]==before.document['declarations']
    assert all(after.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in before.entries.items())
    assert selection_binding(after,[419,420])==selection_binding(before,[419,420]);load_annotations(ROOT,BASIS,ANNOTATIONS)
    assert json.loads(read(ANNOTATIONS))['entries'][:-1]==json.loads(read('data/electron-comoving-equations-identifiers-v2.json'))['entries']
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    for style in ('compact','full'):
        body=format_graph(core(),style);assert parse(body)==parse(transcribe(body,alphabet='v2'))==core()
    assert json.loads(read(SOURCE))==source_record()
    return dict(new_definitions=len(MEANINGS),new_general_relations=0,new_reference_constants=len(REFERENCES),new_statements=1,all_421_prior_statements_and_meanings_preserved=True)
def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/SOURCE,json.dumps(source_record(),ensure_ascii=False,indent=2)+'\n')
@lru_cache(None)
def build_report():
    results={n:f() for n,f in [('equations',equation_checks),('histories',history_checks),('connections',connection_checks),('law',law_checks),('presentation',presentation_checks),('binders',binder_checks),('structure',structure_checks)]}
    helpers=('compose_electron_comoving_equations_v2','compose_electron_comoving_equations','compose_material_acceleration','compose_limits','compose_material_relative_frame','compose_point_particle_dynamics','compose_electron_rest_law_claim','compose_material_velocity','compose_field_equations','compose_doppler_infinity','compose_relativity_conjecture','compose_two_postulates','check_electron_comoving_equations_v2','check_electron_coordinate_normalization','check_electron_coordinate_claim','check_material_acceleration','check_point_particle_dynamics','check_attached_material_charge','check_clock_site_time','check_rod_methods','check_ninth_section_opening','check_problem_series_reduction','audit_opening_scope')
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(source_record()['source_sha256'])|{SOURCE,*DEPENDENCIES,'scripts/compose_electron_transformed_dynamics.py','scripts/check_electron_transformed_dynamics.py','tests/test_electron_transformed_dynamics.py',*(f'scripts/{n}.py' for n in helpers)}
    return dict(status='same_electron_transformed_initial_dynamics_and_law_candidate_connected',document=FULL,**results,verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
