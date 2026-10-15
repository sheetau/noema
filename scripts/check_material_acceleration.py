"""Check derivative-field bindings with registered analytical polynomial models."""
import argparse
from copy import deepcopy
from fractions import Fraction as F
from functools import lru_cache
import hashlib,json,subprocess,sys
from noema.finite_semantics import FunctionValue,evaluate_document
from noema.grammar import parse,format_graph,number_word
from noema.meaning_basis import audit_basis
from noema.script import transcribe
from scripts.compose_material_acceleration import ROOT,PARENT,SOURCE,LIBRARY,CORE,CUT,SCALAR,DOMAIN,CURVE,AT,LAW,LOCAL,ROLES,PROFILES,ACCEL,build
from scripts.compose_limits import call as k,app
from scripts.check_coordinate_correspondence import abstract
from scripts.check_described_appraisals import candidate
from scripts.check_plane_waveforms import setup,OPS
from scripts.check_rod_setup import callbacks

REPORT=ROOT/'reports/material-acceleration-v1.json'
SYMBOLS={n:'jqa'+number_word(i) for i,(n,_) in enumerate(LAW)}
PEOPLE=('x','y','z','t','matter','frame','forceframe','event','forceunit','accelerationunit','record','electric','other')
AXES=dict(zip(ROLES,('x','y','z','t')))
ABSTRACT=OPS|{'sjs','sepn','seob','senz'}


@lru_cache(None)
def text(path):return (ROOT/path).read_text(encoding='utf-8')


def trim(coefficients):
    values=list(map(F,coefficients))
    while values and not values[-1]:values.pop()
    return tuple(values)


def derivative(coefficients):return trim(i*a for i,a in enumerate(coefficients) if i)


def poly_value(coefficients,time):return sum(a*time**i for i,a in enumerate(coefficients))


def free(function):
    impl=function.implementation;code=getattr(impl,'__code__',None)
    return dict(zip(code.co_freevars,(c.cell_contents for c in impl.__closure__ or ()))) if code else {}


def unwrap(function):
    while isinstance(function,FunctionValue) and 'raw' in free(function):function=free(function)['raw']
    return function


class PolynomialModel:
    """Only retained polynomial callbacks and exact coordinate-projection ASTs.

    No values are inferred by probing unknown functions. The derivative oracle
    is an analytical interpretation, not a proof of the cut-limit definitions.
    """
    def __init__(self,doc,variant='baseline',quadratic=(1,-1,2),velocity=(3,0,0)):
        self.doc=doc;self.variant=variant;self.cuts,self.model=setup(doc)
        self.declarations={d['name']:d for d in doc['declarations']}
        self.polynomials={};self.curves={};self.domains={};self.calls=[]
        self.coefficients=[trim((i+1,velocity[i],quadratic[i])) for i in range(3)]+[(F(0),F(1))]
        if variant=='proper_parameter':
            self.coefficients=[tuple(a*2**i for i,a in enumerate(p)) for p in self.coefficients]
        self.accelerations=[F(2*q) for q in quadratic]
        self.velocities=[derivative(p) for p in self.coefficients[:3]]
        if variant=='fake_velocity_field':self.velocities[0]=trim((velocity[0],99))
        if variant=='sample_alias_field':
            # Difference t(t²-1)(t²-4) vanishes at five integer probes.
            self.velocities[0]=trim((velocity[0],2*quadratic[0]+4,0,-5,0,1))
            self.accelerations[0]+=4
        if variant=='wrong_velocity_value':self.velocities[0]=trim((velocity[0]+1,2*quadratic[0]))
        if variant=='wrong_acceleration':self.accelerations[1]+=1
        self.install()

    def register_polynomial(self,coefficients):
        coefficients=trim(coefficients)
        def function(time):return self.cuts.make(poly_value(coefficients,self.cuts.read(time)))
        self.polynomials[function]=coefficients
        return function

    def polynomial(self,function):
        function=unwrap(function);impl=function.implementation
        if impl in self.polynomials:return self.polynomials[impl]
        closure=free(function);node=closure.get('node');captured=closure.get('captured')
        if node is not None and captured is not None:
            # Accept exactly lambda time: curve(time)(named_axis).
            body=node.get('body',{});inner=body.get('function',{});ref=inner.get('function',{})
            parameters=node.get('parameters',[]);axes=body.get('arguments',[])
            if (body.get('kind')=='apply' and inner.get('kind')=='apply' and ref.get('kind')=='variable'
                and len(parameters)==1 and inner.get('arguments')==[dict(kind='variable',name=parameters[0]['name'])]
                and len(axes)==1 and axes[0].get('kind')=='call' and axes[0].get('arguments')==[] and axes[0]['symbol'] in AXES):
                curve=unwrap(captured[ref['name']]).implementation
                if curve in self.curves:return self.curves[curve][list(AXES).index(axes[0]['symbol'])]
        raise ValueError('Unregistered analytical polynomial or coordinate projection')

    def domain_kind(self,domain):
        result=self.domains.get(unwrap(domain).implementation)
        if result is None:raise ValueError('Unregistered time domain')
        return result

    def first(self,domain,function,time,result):
        if self.variant=='unknown_derivative':raise ValueError('Derivative interpretation missing')
        p=self.polynomial(function);t=self.cuts.read(time)
        actual=poly_value(derivative(p),t);self.calls.append((tuple(map(str,p)),str(t),str(actual)))
        return self.domain_kind(domain) not in ('empty','isolated') and domain(time) and self.cuts.read(result)==actual

    def field(self,domain,function,first):
        if self.variant=='unknown_field':raise ValueError('Derivative field interpretation missing')
        kind=self.domain_kind(domain)
        return kind=='empty' or derivative(self.polynomial(function))==self.polynomial(first)

    def interior(self,domain,time):
        return self.domain_kind(domain) in ('all','interval') and domain(time)

    def install(self):
        make,read=self.cuts.make,self.cuts.read
        constants={'matter':'matter','frame':'frame','context':'text','event':'event','forceframe':'forceframe',
            'forceunit':'forceunit','accelerationunit':'accelerationunit','forcerecord':'record','forcekind':'electric'}
        for name,value in constants.items():self.model[SYMBOLS[name]]=lambda name=name,value=value:'other' if self.variant=='wrong_'+name else value
        kind={'empty_domain':'empty','isolated':'isolated','one_sided':'one_sided','local_interval':'interval'}.get(self.variant,'all')
        def domain(time):
            t=read(time)
            return {'all':True,'interval':-1<t<1,'one_sided':t>=0,'isolated':t==0,'empty':False}[kind]
        self.domains[domain]=kind
        def curve(time):
            t=read(time);p=self.coefficients
            point_sort=self.declarations[SYMBOLS['point']]['result']
            return FunctionValue(tuple(point_sort['parameters']),point_sort['result'],
                lambda axis:make(poly_value(p[PEOPLE.index(axis)],t) if axis in AXES.values() else 0))
        self.curves[curve]=self.coefficients
        point=(F(1),F(2),F(3),F(0))
        if self.variant=='wrong_point':point=(F(2),*point[1:])
        def observed(axis):return make(point[PEOPLE.index(axis)] if axis in AXES.values() else 0)
        entries={SYMBOLS['domain']:domain,SYMBOLS['curve']:curve,SYMBOLS['point']:observed}
        for (name,_),polynomial in zip(PROFILES,self.velocities):entries[SYMBOLS[name]]=self.register_polynomial(polynomial)
        L,T=F(125,16),F(25,4)
        forces=(L*2, T*-2,T*4)
        if self.variant=='wrong_force_value':forces=(forces[0]+1,*forces[1:])
        entries[SYMBOLS['forcevector']]=lambda axis:make(forces[PEOPLE.index(axis)] if axis in ('x','y','z') else 0)
        callbacks(self.doc,self.model,entries)
        for (name,_),value in zip(ACCEL,self.accelerations):self.model[SYMBOLS[name]]=lambda value=value:make(value)
        for name,value in {'longitudinal':L,'transverse':5 if self.variant=='wrong_coefficient' else T}.items():self.model[SYMBOLS[name]]=lambda value=value:make(value)
        def location(matter,frame,event,point,context):
            if (matter,frame,event,context)!=('matter','frame','event','text'):return False
            return tuple(read(point(a)) for a in ('x','y','z','t'))==(1,2,3,0)
        def history(matter,frame,context,domain,curve):
            # Explicit physical premise: the registered trajectory is the complete
            # coordinate history. Its measurement/existence is not proved here.
            if self.variant=='unknown_history':raise ValueError('History interpretation missing')
            registered=self.curves.get(unwrap(curve).implementation)
            return (matter,frame,context)==('matter','frame','text') and registered is not None and registered[3]==(0,1) and self.domain_kind(domain)!='empty' and self.variant!='missing_history'
        self.model.update(sjs=self.first,sepn=self.field,senz=self.interior,seob=history,zpb=location,
            va=lambda frame:frame in ('frame','forceframe'),
            zpa=lambda *a:a==('matter','forceframe','event','text'),
            zraconvention=lambda *a:a==('matter','forceframe','frame','event','forceunit','accelerationunit','text'),
            zpc=lambda record,matter,kind,frame,event,unit,vector,context:
                (record,matter,kind,frame,event,unit,context)==('record','matter','electric','forceframe','event','forceunit','text')
                and tuple(read(vector(axis)) for axis in ('x','y','z'))==
                    (L*2+(1 if self.variant=='force_record_mismatch' else 0),T*-2,T*4))
        # Bind the existing source referents to the same fixture identities.
        for name,field in {'zramatter':'matter','ra':'frame','zbm':'forceframe','zraevent':'event',
            'zraforceunit':'forceunit','zraaccelerationunit':'accelerationunit','ri':'context'}.items():self.model[name]=self.model[SYMBOLS[field]]
        for name,value in {'tc':5,'zb7':3,'zramu':4}.items():self.model[name]=lambda value=value:make(value)
        for name,field in {'zralongitudinal':'longitudinal','zratransverse':'transverse'}.items():self.model[name]=self.model[SYMBOLS[field]]

    def evaluate(self):
        primitives={d['name']:self.model[d['name']] for d in self.doc['declarations'] if d['kind']=='primitive'}
        return [r['value'] for r in evaluate_document(self.doc,individuals=PEOPLE,situations=('text','other'),
            primitives=primitives,max_steps=5_000_000)]


def fixture(path,query='acceleration',abstracted=ABSTRACT):
    declarations=''.join('r '+SYMBOLS[n]+'[] '+sort+'.' for n,sort in LAW)
    arguments=lambda items:[k(SYMBOLS[n]) for n,_ in items]
    body=k('sepp',*arguments(AT)) if query=='acceleration' else k('sepq',*arguments(LAW))
    if query=='source':body='t['+k('sepr',*arguments(LOCAL))+']['+k(SYMBOLS['context'])+']'
    return abstract(candidate(text(path),declarations+'q['+body+'].'),abstracted)


def acceleration_checks():
    cases={};variants=('baseline','local_interval','wrong_velocity_value','fake_velocity_field','sample_alias_field','wrong_acceleration',
        'wrong_point','proper_parameter','missing_history','isolated','one_sided','empty_domain',
        'wrong_matter','wrong_frame','wrong_event','wrong_context')
    for path in (LIBRARY,CORE):
        doc=fixture(path)
        result={}
        for mode in variants:
            model=PolynomialModel(doc,mode);actual=model.evaluate()
            assert actual==[mode in ('baseline','local_interval')],(mode,actual)
            result[mode]=actual[0]
        for label,velocity,quadratic in (('uniform',(3,0,0),(0,0,0)),('initial_rest',(0,0,0),(1,-1,2))):
            actual=PolynomialModel(doc,velocity=velocity,quadratic=quadratic).evaluate()
            assert actual==[True];result[label]=True
        if cases:assert result==cases
        cases=result
    return {'cases':cases,'standalone_agrees':True,'history_is_explicit_premise':True,
        'derivatives_of_registered_polynomials_are_analytical':True,'general_cut_limits_proved':False}


def law_checks():
    rows={}
    variants=('baseline','fake_velocity_field','wrong_acceleration','wrong_force_value','force_record_mismatch','wrong_coefficient',
        'wrong_matter','wrong_frame','wrong_event','wrong_forceframe','wrong_forceunit','wrong_accelerationunit',
        'wrong_forcerecord','wrong_forcekind','proper_parameter')
    for query,path in (('law',CORE),('source',CORE),('source',SOURCE)):
        doc=fixture(path,query);results={}
        for mode in variants:
            actual=PolynomialModel(doc,mode).evaluate()
            assert actual==[mode=='baseline'],(query,path,mode,actual)
            results[mode]=actual[0]
        if rows:assert results==next(iter(rows.values()))
        rows[query+':'+path]=results
    return rows


def field_probe_checks():
    doc=fixture(LIBRARY,abstracted=OPS|{'sjs','seob','senz'})
    declaration=next(d for d in doc['declarations'] if d['name']=='sepn')
    quantified=declaration['body'];assert quantified['kind']=='forall'
    helper=dict(kind='definition',name='jqprobe',parameters=deepcopy(declaration['parameters'])+[
        dict(name=quantified['variable'],sort=quantified['sort'])],result='truth',body=deepcopy(quantified['body']))
    doc['declarations'].append(helper);doc['statements']=[]
    prefix=format_graph(doc,'compact');rows={}
    for t in (-2,-1,0,1,2,F(1,2)):
        from scripts.check_phi_normalization import number
        function=app('i[trajectory '+CURVE+'][i[moment '+CUT+']['+app(app('v trajectory','v moment'),k(ROLES[0]))+']]',k(SYMBOLS['curve']))
        query=k('jqprobe',k(SYMBOLS['domain']),function,k(SYMBOLS['velocityx']),k('bb',number(t)))
        current=parse(prefix+'q['+query+'].')
        for variant in ('baseline','fake_velocity_field','sample_alias_field'):
            actual=PolynomialModel(current,variant).evaluate()[0]
            expected=variant=='baseline' or (variant=='fake_velocity_field' and t==0) or (variant=='sample_alias_field' and t!=F(1,2))
            assert actual==expected,(variant,t,actual)
            rows[variant+':'+str(t)]=actual
    return {'actual_universal_body_instantiated':True,'cases':rows,'whole_real_domain_not_enumerated':True}


def refusal_checks():
    rows={}
    for retained in ('sepn','seob','senz','sjs'):
        doc=fixture(LIBRARY,abstracted=ABSTRACT-{retained});model=PolynomialModel(doc)
        try:model.evaluate()
        except ValueError as exc:
            assert 'Cannot finitely quantify the rational number domain' in str(exc),(retained,str(exc))
            rows[retained]=str(exc)
        else:raise AssertionError('All-real condition certified by a finite model: '+retained)
    doc=fixture(LIBRARY)
    for variant in ('unknown_derivative','unknown_field','unknown_history'):
        try:PolynomialModel(doc,variant).evaluate()
        except ValueError as exc:
            assert 'missing' in str(exc);rows[variant]=str(exc)
        else:raise AssertionError('Missing interpretation invented')
    model=PolynomialModel(doc)
    sort=model.declarations[SYMBOLS['velocityx']]['result']
    unknown=FunctionValue(tuple(sort['parameters']),sort['result'],lambda time:time)
    try:model.polynomial(unknown)
    except ValueError as exc:rows['unregistered_function']=str(exc)
    else:raise AssertionError('Unknown function inferred by finite probes')
    return rows


def build_report():
    files=build();audits={}
    for p,body in files.items():assert text(p)==body,p
    doc=parse(text(SOURCE));parent=parse(text(PARENT))
    assert doc['declarations'][:len(parent['declarations'])]==parent['declarations']
    assert doc['statements']==parent['statements'] and len(doc['statements'])==176
    for path in (SOURCE,LIBRARY,CORE):
        current=parse(text(path))
        for notation in ('full','compact'):
            rendered=format_graph(current,notation)
            assert parse(rendered)==parse(transcribe(rendered,alphabet='v2'))==current
        basis=next(json.loads(value) for p,value in files.items() if p.endswith('.json') and json.loads(value)['document']==path)
        audit=audit_basis(current,basis)
        audits[path]={name:value for name,value in audit.items() if name!='definition_dependencies'}
        completed=subprocess.run([sys.executable,'-X','utf8','-m','noema','parse','-i',str(ROOT/path)],
            check=True,capture_output=True,encoding='utf-8')
        assert json.loads(completed.stdout)==current
    previous=json.loads(text('reports/mass-coefficients-v1.json'))
    alignment=deepcopy(previous['alignment']['segments'][0])
    alignment.update(definitions=['sepn','sepo','sepp','sepq','sepr'],status='explicit_interpretive_annotation')
    paths=set(files)|{PARENT,'data/einstein-mass-coefficients-basis-v1.json','reports/mass-coefficients-v1.json',
        'scripts/compose_material_acceleration.py','scripts/check_material_acceleration.py','tests/test_material_acceleration.py',
        'docs/material-acceleration-v1.md','scripts/compose_material_velocity.py','scripts/compose_mass_coefficients.py',
        'scripts/compose_origin_clock.py','scripts/compose_limits.py','scripts/compose_situated_criticism.py',
        'scripts/check_coordinate_correspondence.py','scripts/check_described_appraisals.py','scripts/check_plane_waveforms.py',
        'scripts/check_rod_setup.py','scripts/check_angle_composition.py','scripts/check_tau_differential.py',
        'scripts/check_transverse_time.py','scripts/check_phi_normalization.py','reports/written-units-v1.json'}
    paths.update('noema/'+n+'.py' for n in ('grammar','semantics','language','discourse','script','finite_semantics','meaning_basis','extraction'))
    return dict(status='partial_coordinate_acceleration_construction',document=SOURCE,basis_audits=audits,
        acceleration=acceleration_checks(),physical_law_bindings=law_checks(),field_probes=field_probe_checks(),
        refusals=refusal_checks(),statements_preserved=176,new_primitives=0,new_author_assertions=0,
        roundtrips=True,cli_parse=True,alignment={'segments':[alignment]},adds_new_text_coverage=False,
        coordinate_unit_conversion_constructed=False,force_measurement_constructed=False,
        verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sorted(paths)})


def main():
    cli=argparse.ArgumentParser();cli.add_argument('--verify-only',action='store_true');options=cli.parse_args()
    report=build_report()
    if options.verify_only:assert json.loads(REPORT.read_text(encoding='utf-8'))==report
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:stream.write(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print('Coordinate acceleration, derivative fields and force bindings checked; full semantic review remains open',flush=True)


if __name__=='__main__':main()
