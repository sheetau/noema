"""Check full-history bindings and native derivatives with retained polynomials."""
from copy import deepcopy
from functools import lru_cache
from fractions import Fraction as Q
import json
from noema.grammar import parse,format_graph,number_word
from noema.extraction import extract_document
from noema.finite_semantics import evaluate_document
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts import check_electron_coordinate_normalization as base
from scripts import check_material_acceleration as analytic
from scripts.compose_electron_comoving_history import *

DOC='docs/electron-comoving-history-v1.md'
DEPENDENCIES=('reports/electron-coordinate-normalization-v1.json','reports/material-velocity-v1.json','reports/material-acceleration-v1.json')
AXES=('x','y','z','t');CONSTANTS=dict(zip(ROLES,AXES))
PEOPLE=tuple(dict.fromkeys([*AXES,*base.old.PEOPLE,'matter','first','second','event','before','after','length','duration','other']))
TIMES=tuple(map(Q,(-3,-2,-1,Q(-1,2),0,Q(1,5),Q(1,2),1,Q(9,5),2,3,4,5)))
TS=tuple('jcht'+number_word(i) for i in range(len(TIMES)))
BOUNDS=base.BOUNDS|{'eioj','seob','senz','sjs'}
EXTRA={'ek5t':{'ek5s'},'ek5v':{'ek5s'},'ek5w':{'ek4p','ek5t'},'ek5y':{'ek5w','ek5x'}}
FIELDS={'ek5n':FRAME,'ek5o':BOOST+[('oldcurve',CURVE),('time',R)],'ek5p':BOOST+[('newcurve',CURVE),('time',R)],'ek5q':MAPTRACK+[('time',R)],'ek5r':MAPTRACK+[('time',R)],'ek5s':HISTORY,'ek5t':EVENT,'ek5u':EVENT,'ek5v':EVENT,'ek5w':CURRENT,'ek5x':CURRENT,'ek5y':CURRENT}
fn=base.old.fn;sort=base.old.sort;forbidden=base.forbidden

@lru_cache(None)
def core():return parse(read(CORE))

@lru_cache(None)
def fixture(root,mode='sample'):
    doc=extract_document(core(),roots=[root],statement_indices=[]).document
    cuts=BOUNDS|EXTRA.get(root,set())
    if mode=='limits':cuts=cuts-{'sjs'}
    for i,d in enumerate(doc['declarations']):
        if d['kind']=='definition' and d['name'] in cuts:doc['declarations'][i]=dict(kind='primitive',name=d['name'],parameters=[p['sort'] for p in d['parameters']],result=d['result'])
    doc=extract_document(doc,roots=[root],statement_indices=[]).document
    d=next(d for d in doc['declarations'] if d['name']==root)
    if root=='ek5s' and mode=='sample':
        def sample(node):
            if isinstance(node,list):return [sample(x) for x in node]
            if not isinstance(node,dict):return node
            if node.get('kind')=='forall' and node['sort']==sort(R):
                probes=[sample(base.old.old.replace(node['body'],node['variable'],dict(kind='call',symbol=n,arguments=[]))) for n in TS]
                out=probes[-1]
                for p in reversed(probes[:-1]):out=dict(kind='and',arguments=[p,out])
                return out
            return {k:sample(x) for k,x in node.items()}
        d['body']=sample(d['body'])
    slots=[]
    for i,p in enumerate(d['parameters']):
        n='jcharg'+number_word(i);slots.append(n);doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']))
    doc['declarations'] += [dict(kind='primitive',name=n,parameters=[],result=sort(R)) for n in TS]
    expr=dict(kind='call',symbol=root,arguments=[dict(kind='call',symbol=n,arguments=[]) for n in slots])
    if d['result']!='truth':
        doc['declarations'].append(dict(kind='primitive',name='jchcapture',parameters=[d['result']],result='truth'));expr=dict(kind='call',symbol='jchcapture',arguments=[expr])
    doc['declarations'].sort(key=lambda d:d['kind']!='primitive');doc['statements']=[dict(kind='ask',body=expr)];return doc,slots

def run(root,by,m,mode='sample'):
    doc,slots=fixture(root,mode);captured=[]
    def capture(x):captured.append(x);return True
    mm={n:lambda x=x:x for n,x in CONSTANTS.items()}|m|{slot:lambda x=by[name]:x for slot,(name,t) in zip(slots,FIELDS[root])}|{'jchcapture':capture}
    out=evaluate_document(doc,individuals=PEOPLE,situations=('case','other'),primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=3000000,memoize_definitions=True,memoize_expressions=True)[0]['value']
    return captured[0] if captured else out

class Model:
    def __init__(self,speed=3,offset=(2,-1,3,1),quadratic=(1,-2)):
        self.c,self.r,self.m,self.point,self.pv=base.setup();c,r=self.c,self.r
        self.speed=Q(speed);self.beta=r(self.m['soy'](c(5),c(speed)));self.offset=tuple(map(Q,offset));self.curves={};self.domains={};self.calls=[]
        self.oldcoeff=((0,Q(speed)),(0,0,Q(quadratic[0])),(0,0,Q(quadratic[1])),(0,1))
        b=self.beta;o=self.offset
        self.newcoeff=((o[0],),(o[1]+quadratic[0]*b*b*o[3]**2,-2*quadratic[0]*b*b*o[3],quadratic[0]*b*b),(o[2]+quadratic[1]*b*b*o[3]**2,-2*quadratic[1]*b*b*o[3],quadratic[1]*b*b),(0,1))
        oldcurve=self.curve(self.oldcoeff);newcurve=self.curve(self.newcoeff)
        olddomain=self.domain(-2,2);newdomain=self.domain(o[3]-2/b,o[3]+2/b)
        self.by=dict(matter='matter',first='first',second='second',lengthunit='length',timeunit='duration',context='case',light=c(5),speed=c(speed),offset=self.point(o),olddomain=olddomain,oldcurve=oldcurve,newdomain=newdomain,newcurve=newcurve,event='event',point=self.point((0,0,0,0)),velocity=self.point((speed,0,0,0)),time=c(0))
        self.m|={n:lambda t=t:c(t) for n,t in zip(TS,TIMES)}
        # Other named frames have a known, different candidate speed; unknown
        # interpretations are tested separately, not used as negative values.
        self.m|={'eioj':lambda *xs:xs==('first','second','length','duration','case'),'ejsl':lambda *xs:xs in {('first','length','duration','case'),('second','length','duration','case')},'eislc':lambda first,second,lu,tu,axis,ctx:c(speed if axis=='x' else 0) if (first,second,lu,tu,ctx)==('first','second','length','duration','case') else c(17),'eisqt':self.mapping,'seob':self.history,'senz':self.interior,'sjs':self.derivative,'zpb':self.location,'eisqd':self.calibrated,'ek5s':lambda *xs:self.history_key(xs)==self.history_key([self.by[n] for n,t in HISTORY])}
    def curve(self,coefficients):
        coeff=tuple(analytic.trim(p) for p in coefficients)
        def body(t):return self.point(tuple(analytic.poly_value(p,self.r(t)) for p in coeff))
        self.curves[body]=coeff;return fn(sort(CURVE),body)
    def domain(self,lo,hi):
        def body(t):return lo<self.r(t)<hi
        self.domains[body]=(Q(lo),Q(hi));return fn(sort(DOMAIN),body)
    def history_key(self,xs):
        def key(x):
            if not isinstance(x,base.old.old.FunctionValue):return x
            raw=analytic.unwrap(x)
            if raw.parameters==('number',):return self.r(x)
            if raw.parameters==('individual',):return self.pv(x)
            return raw.implementation
        return tuple(key(x) for x in xs)
    def mapping(self,first,second,lu,tu,mapping,ctx):
        if (first,second,lu,tu,ctx)!=('first','second','length','duration','case'):return False
        b=self.beta;s=self.speed;o=self.offset
        for x,y,z,t in base.POINTS:
            actual=self.pv(mapping(self.point((x,y,z,t))))
            if actual!=(b*(x-s*t)+o[0],Q(y)+o[1],Q(z)+o[2],b*(t-s*Q(x)/25)+o[3]):return False
        return True
    def history(self,matter,frame,ctx,domain,curve):
        prefix={'first':'old','second':'new'}.get(frame)
        return prefix is not None and (matter,ctx)==('matter','case') and analytic.unwrap(curve).implementation==analytic.unwrap(self.by[prefix+'curve']).implementation and analytic.unwrap(domain).implementation==analytic.unwrap(self.by[prefix+'domain']).implementation
    def interior(self,domain,time):
        bounds=self.domains.get(analytic.unwrap(domain).implementation)
        if bounds is None:raise ValueError('Unknown attached-charge input: domain')
        return bounds[0]<self.r(time)<bounds[1]
    def derivative(self,domain,function,time,result):
        # Reuse the exact registered coordinate-projection recognizer, not samples.
        poly=analytic.PolynomialModel.polynomial(self,function)
        value=analytic.poly_value(analytic.derivative(poly),self.r(time));self.calls.append((poly,self.r(time),value,self.r(result)))
        return self.interior(domain,time) and value==self.r(result)
    polynomials={}
    def location(self,matter,frame,event,point,ctx):
        if (matter,ctx)!=('matter','case') or frame not in ('first','second') or event not in ('before','event','after'):return False
        t={'before':Q(-1),'event':Q(0),'after':Q(1)}[event]
        prefix='old' if frame=='first' else 'new';at=t if frame=='first' else t/self.beta+self.offset[3]
        return self.pv(point)==self.pv(self.by[prefix+'curve'](self.c(at)))
    def calibrated(self,matter,frame,event,lu,tu,point,ctx):
        return (lu,tu)==('length','duration') and self.location(matter,frame,event,point,ctx)

@lru_cache(None)
def frame_checks():
    model=Model();by,m=model.by,model.m;cases=0
    assert run('ek5n',by,m);cases+=1
    for name in ('first','second','lengthunit','timeunit','context'):
        assert not run('ek5n',by|{name:'other'},m);cases+=1
    for name in ('eioj','ejsl','eisqt'):
        assert not run('ek5n',by,m|{name:lambda *xs:False});cases+=1
        base.old.old.reject(lambda:run('ek5n',by,m|{name:forbidden}),unknown=True);cases+=1
    for i in range(3):
        assert not run('ek5n',by,m|{'eislc':lambda *xs,i=i:model.c((model.speed if xs[4]=='x' else 0)+(1 if xs[4]==AXES[i] else 0))});cases+=1
    for i in range(4):
        changed=tuple(x+1 if i==j else x for j,x in enumerate(model.offset))
        assert not run('ek5n',by|{'offset':model.point(changed)},m);cases+=1
    return dict(cases=cases,complete_frame_translation_and_same_units_are_explicit_premises=True,all_three_constant_velocity_components_and_four_offsets_bound=True)

@lru_cache(None)
def map_checks():
    cases=0
    for speed in (0,3,4):
        for offset in ((0,0,0,0),(2,-1,3,1),(-2,5,4,-1)):
            a=Model(speed,offset);by,m=a.by,a.m
            for t in (Q(-3),Q(-1),Q(-1,2),Q(0),Q(1,2),Q(1),Q(3)):
                tau=t/a.beta+a.offset[3]
                assert a.r(run('ek5o',by|{'time':a.c(t)},m))==tau;cases+=1
                assert a.r(run('ek5p',by|{'time':a.c(tau)},m))==t;cases+=1
                assert run('ek5q',by|{'time':a.c(t)},m);cases+=1
                assert run('ek5r',by|{'time':a.c(tau)},m);cases+=1
            # A gap in only one domain must be seen in the other direction.
            assert not run('ek5q',by|{'newdomain':a.domain(10,11)},m);cases+=1
            assert not run('ek5r',by|{'time':a.c(a.offset[3]),'olddomain':a.domain(10,11)},m);cases+=1
            for axis in range(4):
                coeff=[list(p) for p in a.newcoeff];coeff[axis][0]+=1
                wrong=by|{'newcurve':a.curve(coeff)}
                assert not run('ek5q',wrong,m);cases+=1
                assert not run('ek5r',wrong|{'time':a.c(a.offset[3])},m);cases+=1
    return dict(cases=cases,forward_and_reverse_time_domains_and_all_four_coordinates=True,zero_and_nonzero_speed_with_free_origins=True)

@lru_cache(None)
def history_checks():
    a=Model();by,m=a.by,a.m;cases=0
    assert run('ek5s',by,m);cases+=1
    for side in ('first','second'):
        assert not run('ek5s',by,m|{'seob':lambda matter,frame,*xs,side=side:False if frame==side else a.history(matter,frame,*xs)});cases+=1
        assert not run('ek5s',by,m|{'eisqd':lambda matter,frame,*xs,side=side:False if frame==side else a.calibrated(matter,frame,*xs)});cases+=1
    for event in ('before','event','after'):
        assert not run('ek5s',by,m|{'eisqd':lambda matter,frame,e,*xs,event=event:False if e==event else a.calibrated(matter,frame,e,*xs)});cases+=1
        for side in ('first','second'):
            assert not run('ek5s',by,m|{'zpb':lambda matter,frame,e,*xs,event=event,side=side:False if (frame,e)==(side,event) else a.location(matter,frame,e,*xs)});cases+=1
    for name in ('seob','eisqd','zpb'):
        base.old.old.reject(lambda:run('ek5s',by,m|{name:forbidden}),unknown=True);cases+=1
    base.old.old.reject(lambda:run('ek5s',by,m,'native'));cases+=1
    return dict(cases=cases,both_complete_histories_and_all_event_calibrations_bound=True,real_quantifiers_instantiated_only_for_diagnostics=True,native_unbounded_quantification_refused=True)

@lru_cache(None)
def derivative_checks():
    cases=0;observed=[]
    for speed in (0,3,4):
        for offset in ((0,0,0,0),(2,-1,3,1)):
            a=Model(speed,offset);by,m=a.by,a.m
            for event,t in (('before',Q(-1)),('event',Q(0)),('after',Q(1))):
                velocity=(speed,2*t,-4*t,0);b=by|{'event':event,'point':by['oldcurve'](a.c(t)),'velocity':a.point(velocity)}
                assert run('ek5t',b,m);cases+=1
                assert run('ek5u',b,m);cases+=1
                assert run('ek5v',b,m);cases+=1
                # Rest is only at t=0; the transformed transverse acceleration is nonzero.
                vals=[a.beta*x for x in velocity[1:3]]
                assert (vals==[0,0])==(t==0);cases+=1
                for axis in range(3):
                    wrong=list(velocity);wrong[axis]+=1
                    assert not run('ek5t',b|{'velocity':a.point(wrong)},m);cases+=1
                    assert not run('ek5u',b|{'velocity':a.point(wrong)},m);cases+=1
                for name in ('matter','event','context'):
                    assert not run('ek5u',b|{name:'other'},m);cases+=1
            assert not run('ek5t',by,m|{'ek5s':lambda *xs:False});cases+=1
            for name in ('sjs','seob','senz','zpb'):
                assert not run('ek5u',by,m|{name:lambda *xs:False});cases+=1
                base.old.old.reject(lambda:run('ek5u',by,m|{name:forbidden}),unknown=True);cases+=1
            base.old.old.reject(lambda:run('ek5u',by,m,'limits'));cases+=1
            observed.append(dict(speed=speed,offset=list(offset),native_coordinate_derivatives=len(a.calls)))
    return dict(cases=cases,models=observed,registered_polynomial_derivatives_not_sample_fits=True,new_time_is_shifted_and_rescaled_not_old_time_or_proper_time=True,native_old_and_new_seoc_checked=True,full_chain_rule_proved=False)

@lru_cache(None)
def source_checks():
    by,m,c,r,key=base.old.setup();by=by.copy();cases=0
    by.update(second='other',light=c(5),offset=base.old.old.point(c,(2,-1,3,1)),newdomain=by['domain'],newcurve=by['curve'],point=base.old.old.point(c,(0,0,0,0)))
    for (n,t),value in zip(PROFILES,(3,0,0)):by[n]=fn(sort(t),lambda time,value=value:c(value))
    m=m|{'eisxt':lambda:c(3)}
    axial=base.old.old.point(c,(3,0,0,0));shared=by|dict(first=by['frame'],speed=c(3),olddomain=by['domain'],oldcurve=by['curve'],velocity=axial)
    rows={'ek4p':key([by[n] for n,t in SETTING]),'ek5t':key([shared[n] for n,t in EVENT])}
    mm=m|{n:lambda *xs,row=row:key(xs)==row for n,row in rows.items()}
    assert run('ek5w',by,mm);cases+=1
    for n,row in rows.items():
        for i in range(len(row)):
            wrong=list(row);wrong[i]=('distinct',i)
            assert not run('ek5w',by,mm|{n:lambda *xs,wrong=tuple(wrong):key(xs)==wrong});cases+=1
        base.old.old.reject(lambda:run('ek5w',by,mm|{n:forbidden}),unknown=True);cases+=1
    for axis in range(4):
        assert not run('ek5w',by|{'point':base.old.old.point(c,tuple(1 if i==axis else 0 for i in range(4)))},mm);cases+=1
    for (n,t),value in zip(PROFILES,(3,0,0)):
        wrong=by|{n:fn(sort(t),lambda time,value=value:c(value+1))}
        assert not run('ek5w',wrong,mm);cases+=1
    # Check the native rest body with both physical histories and three derivatives.
    a=Model();rest=by|{n:a.by[n] for n,t in CURRENT if n in a.by};rest.update(frame='first',domain=a.by['olddomain'],curve=a.by['oldcurve'])
    assert run('ek5x',rest,a.m|{'eisxt':lambda:a.c(3)});cases+=1
    for flag in (True,False):
        for answer in (True,False):
            assert run('ek5y',by,m|{'ek5w':lambda *xs:flag,'ek5x':lambda *xs:answer})==(not flag or answer);cases+=1
    return dict(cases=cases,same_prior_setting_and_speed_all_argument_slots_checked=True,zero_old_coordinates_and_all_three_profiles_checked=True,native_comoving_rest_at_nonzero_offset_checked=True,conditional_premise_and_conclusion_distinct=True)

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    before=load_catalog(ROOT,PARENT_BASIS);after=load_catalog(ROOT,BASIS)
    assert after.document['statements']==before.document['statements'] and len(after.document['statements'])==417
    assert after.document['declarations'][:len(before.document['declarations'])]==before.document['declarations']
    assert all(after.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in before.entries.items())
    assert selection_binding(after,[415,416])==selection_binding(before,[415,416]);load_annotations(ROOT,BASIS,ANNOTATIONS)
    assert json.loads(read(ANNOTATIONS))['entries']==json.loads(read('data/electron-coordinate-normalization-identifiers-v1.json'))['entries']
    assert len(MEANINGS)==12
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    for style in ('compact','full'):
        body=format_graph(core(),style);assert parse(body)==parse(transcribe(body,alphabet='v2'))==core()
    return dict(new_definitions=12,new_primitives=0,new_statements=0,all_417_prior_statements_and_meanings_preserved=True)

def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)

@lru_cache(None)
def build_report():
    results={n:f() for n,f in [('frame',frame_checks),('map',map_checks),('history',history_checks),('derivatives',derivative_checks),('source',source_checks),('structure',structure_checks)]}
    helpers=('compose_limits','compose_material_relative_frame','compose_material_velocity','compose_point_particle_dynamics','compose_field_transform','check_electron_coordinate_normalization','check_material_acceleration','check_point_particle_dynamics','check_attached_material_charge','check_body_rest_field_method','check_tau_differential','audit_opening_scope')
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|{DOC,*DEPENDENCIES,'data/einstein-electron-coordinate-obligations-v1.json','scripts/compose_electron_comoving_history.py','scripts/check_electron_comoving_history.py','tests/test_electron_comoving_history.py',*(f'scripts/{n}.py' for n in helpers)}
    return dict(status='same_electron_comoving_histories_and_native_coordinate_derivatives_checked',document=FULL,**results,verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
