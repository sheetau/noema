"""Check endpoint identity and all-interval axial geometry with registered polynomials."""
import argparse
from fractions import Fraction as F
from functools import lru_cache
import hashlib,json,subprocess,sys
from noema.grammar import parse,format_graph
from noema.finite_semantics import Content,FunctionValue,evaluate_document
from noema.meaning_basis import audit_basis
from noema.script import transcribe
from scripts.compose_electron_axis_motion import ROOT,PARENT,SOURCE,LIBRARY,CORE,READING,CUT,ALL,ROLES,build
from scripts.compose_limits import call as k
from scripts.check_coordinate_correspondence import abstract
from scripts.check_described_appraisals import candidate
from scripts.check_plane_waveforms import setup,OPS
from scripts.check_rod_setup import callbacks,guarded
from scripts.check_phi_normalization import number
from scripts.check_quantities import ARITHMETIC
from scripts.check_material_acceleration import free,unwrap,trim,derivative,poly_value

REPORT=ROOT/'reports/electron-axis-motion-v1.json'
AXES=dict(zip(ROLES,('x','y','z','t')))
PEOPLE=('x','y','z','t','particle','frame','start','end','field','other')
SCENES=('actual','other')
ABSTRACT=OPS|{'seob','senz','sjs','serv'}


@lru_cache(None)
def text(path):return (ROOT/path).read_text(encoding='utf-8')


def fixture(path,source=False,whole_interval=False):
    declarations=''.join('r jqy'+n+'[] '+sort+'.' for n,sort in ALL)
    declarations+='r jqyprofile[] h['+CUT+'] '+CUT+'.'
    main='t[k serx[]][k jqycontext[]]' if source else k('serw',*[k('jqy'+n) for n,_ in ALL])
    queries='q['+main+'].'+''.join('q['+k('seru',k('jqycurve'),k('bb',number(t)))+'].' for t in (0,F(1,2),1))
    return abstract(candidate(text(path),declarations+queries),ABSTRACT-({'serv'} if whole_interval else set()))


class AxisModel:
    def __init__(self,doc,variant='baseline'):
        self.doc=doc;self.variant=variant;self.cuts,self.model=setup(doc);self.model.update(ARITHMETIC)
        make,read=self.cuts.make,self.cuts.read
        x=(0,0,1);y=();z=();clock=(0,1)
        if variant=='shifted_origin':x=(1,0,1)
        if variant=='initial_motion':x=(0,1,1)
        if variant=='axis_excursion':y=(0,0,1,-2,1)
        if variant=='sample_alias_excursion':y=(0,0,F(1,4),F(-3,2),F(13,4),-3,1)
        if variant=='wrong_clock':clock=(0,2)
        self.coefficients=tuple(map(trim,(x,y,z,clock)))
        declarations={d['name']:d for d in doc['declarations']}
        point_sort=declarations['jqystartpoint']['result']
        def point(row):return FunctionValue(tuple(point_sort['parameters']),point_sort['result'],lambda axis:make(row[('x','y','z','t').index(axis)] if axis in ('x','y','z','t') else 0))
        def row(t):return tuple(poly_value(p,t) for p in self.coefficients)
        def curve(t):return point(row(read(t)))
        def domain(t):return variant!='empty_domain' and not (variant=='domain_gap' and read(t)==F(1,2))
        def profile(position):return make(3)
        callbacks(doc,self.model,{'jqycurve':curve,'jqydomain':domain,'jqystartpoint':lambda axis:point(row(0))(axis),
            'jqyendpoint':lambda axis:point(row(1))(axis),'jqyprofile':profile})
        self.model.update(jqymatter=lambda:'other' if variant=='wrong_matter' else 'particle',
            jqyframe=lambda:'other' if variant=='wrong_frame' else 'frame',jqycontext=lambda:'actual',
            jqystart=lambda:'other' if variant=='wrong_start' else 'start',jqyend=lambda:'other' if variant=='wrong_end' else 'end',
            jqyfinalposition=lambda:make(row(1)[0]+(variant=='wrong_final_position')),
            jqyfinalspeed=lambda:make(poly_value(derivative(x),1)+(variant=='wrong_final_speed')))
        def registered(d,c):return unwrap(d).implementation is domain and unwrap(c).implementation is curve
        def location(matter,frame,event,p,context):
            if variant=='unknown_location':raise ValueError('Coordinate assignment missing')
            return (matter,frame,context)==('particle','frame','actual') and event in ('start','end') and tuple(read(p(a)) for a in ('x','y','z','t'))==row(0 if event=='start' else 1)
        def history(matter,frame,context,d,c):
            if variant=='unknown_history':raise ValueError('Whole history missing')
            return variant!='missing_history' and (matter,frame,context)==('particle','frame','actual') and registered(d,c) and variant!='empty_domain' and self.coefficients[3]==(F(0),F(1))
        def field_polynomial(function):
            closure=free(unwrap(function));node=closure.get('node',{});captured=closure.get('captured',{})
            body=node.get('body',{});inner=body.get('function',{});ref=inner.get('function',{})
            parameters=node.get('parameters',[]);axes=body.get('arguments',[])
            if not (body.get('kind')=='apply' and inner.get('kind')=='apply' and ref.get('kind')=='variable' and len(parameters)==1 and
                inner.get('arguments')==[dict(kind='variable',name=parameters[0]['name'])] and len(axes)==1 and axes[0].get('kind')=='call' and axes[0].get('arguments')==[] and axes[0]['symbol'] in AXES):
                raise ValueError('Unregistered coordinate projection')
            if unwrap(captured[ref['name']]).implementation is not curve:raise ValueError('Unregistered curve')
            return self.coefficients[list(AXES).index(axes[0]['symbol'])]
        def differential(d,fn,t,value):
            return unwrap(d).implementation is domain and domain(t) and read(value)==poly_value(derivative(field_polynomial(fn)),read(t))
        def axial(d,c,lower,upper):
            if variant=='unknown_interval':raise ValueError('Full interval interpretation missing')
            lo,hi=read(lower),read(upper)
            return registered(d,c) and lo<hi and variant!='empty_domain' and not (variant=='domain_gap' and lo<=F(1,2)<=hi) and self.coefficients[1:3]==((),()) and self.coefficients[3]==(F(0),F(1))
        self.model.update(va=lambda frame:frame=='frame',zpb=location,seob=history,
            senz=lambda d,t:unwrap(d).implementation is domain and domain(t),sjs=differential,serv=axial)
        sources={'zramatter':'matter','ra':'frame','zrhdomain':'domain','zrhcurve':'curve',
            'zrgstart':'start','zraevent':'end','zrhstartpoint':'startpoint','zrhendpoint':'endpoint',
            'zrgposition':'finalposition','zb7':'finalspeed','zrgprofile':'profile'}
        for source,name in sources.items():self.model[source]=self.model['jqy'+name]
        self.model.update(zrgfield=lambda:'field',zrgcharge=lambda:make(2))
        def drive(p,field,frame,start,end,f,charge,context):
            if variant=='unknown_drive':raise ValueError('Electrostatic setup missing')
            return (p,field,frame,start,end,context)==('particle','other' if variant=='wrong_field' else 'field','frame','start','end','actual') and unwrap(f).implementation is profile and read(charge)==(3 if variant=='wrong_charge' else 2)
        self.model['zrhdrive']=drive

    def evaluate(self):
        return [r['value'] for r in evaluate_document(self.doc,individuals=PEOPLE,situations=SCENES,
            primitives={d['name']:self.model[d['name']] for d in self.doc['declarations'] if d['kind']=='primitive'},max_steps=5_000_000)]


def geometry_checks():
    variants=['baseline','shifted_origin','initial_motion','axis_excursion','sample_alias_excursion','wrong_clock','domain_gap','empty_domain',
        'missing_history','wrong_matter','wrong_frame','wrong_start','wrong_end','wrong_final_position','wrong_final_speed','wrong_field','wrong_charge']
    rows={}
    for path,source in ((LIBRARY,False),(CORE,True),(SOURCE,True)):
        doc=fixture(path,source);results={}
        for variant in variants:
            actual=AxisModel(doc,variant).evaluate()
            main=variant=='baseline' or (not source and variant in ('wrong_field','wrong_charge'))
            geometry=[True,variant!='axis_excursion',variant!='wrong_clock']
            if variant=='wrong_clock':geometry=[True,False,False]
            expected=[main,*geometry]
            assert actual==expected,(path,variant,actual,expected);results[variant]=actual
        rows[path]=results
    for variant in ('unknown_history','unknown_location','unknown_interval','unknown_drive'):
        try:AxisModel(fixture(CORE,True),variant).evaluate()
        except ValueError as exc:assert 'missing' in str(exc)
        else:raise AssertionError('Unknown premise invented')
    try:AxisModel(fixture(CORE,True,whole_interval=True)).evaluate()
    except ValueError as exc:assert any(w in str(exc).lower() for w in ('domain','quantif','function','enumerat','rational')),str(exc)
    else:raise AssertionError('All real times silently approximated')
    return {'cases':rows,'registered_polynomials_only':True,'history_is_explicit_model_premise':True,'full_cut_quantifier_refused':True,
        'whole_real_history_or_limit_law_proved':False}


def conditional_checks():
    doc=abstract(candidate(text(CORE),'r jqycontext[] d.q[t[k sery[]][k jqycontext[]]].'),{'serx','sert'})
    rows={}
    for before in (False,True):
        for after in (False,True):
            model=guarded(doc);model.update(jqycontext=lambda:'actual',serx=lambda:Content(SCENES,(before,before)),sert=lambda:Content(SCENES,(after,after)))
            value=evaluate_document(doc,individuals=PEOPLE,situations=SCENES,primitives=model)[0]['value']
            assert value==((not before) or after);rows[str((before,after))]=value
    return {'truth_table':rows,'component_contents_are_explicit_model_inputs':True,'actual_motion_inferred':False}


def attribution_check():
    doc=parse(text(CORE));model=guarded(doc)
    for name,value in {'zrhnode':'node','rd':'author','zrgscope':'scope','ri':'actual'}.items():model[name]=lambda value=value:value
    model['uh']=lambda n,a,c,s,t:(n,a,s,t)==('node','author','scope','actual') and json.loads(c.syntax)['symbol']=='sery'
    result=evaluate_document(doc,individuals=('node','author','scope'),situations=('actual',),primitives=model)
    assert result[0]['value'] is True
    return {'conditional_content':'sery','trajectory_or_work_integral_executed':False}


def alignment():
    work=json.loads(text('artifacts/written-units-v1/einstein-1905.json'));unit=next(u for u in work['units'] if u['id']=='einstein-1905:u0261');body=unit['text']
    start=body.index('Bewegt sich');end=body.index(' , so ist klar')
    common=dict(unit=unit['id'],unit_sha256=unit['text_sha256'],status='partial_origin_rest_axial_motion_and_work_conditional')
    return {'segments':[dict(common,range=[start,end],text=body[start:end],definitions=['seru','serv','serw','serx','sery'])]+
        [dict(common,math_id=mid,definitions=['serx']) for mid in ('M0422','M0423','M0424')]}


def build_report():
    files=build();audits={}
    for p,body in files.items():assert text(p)==body,p
    old=parse(text(PARENT));current=parse(text(SOURCE))
    assert current['statements'][:-1]==old['statements'] and len(old['statements'])==185
    assert current['declarations'][:len(old['declarations'])]==old['declarations']
    for p in (SOURCE,LIBRARY,CORE):
        doc=parse(text(p))
        for notation in ('full','compact'):
            rendered=format_graph(doc,notation);assert parse(rendered)==parse(transcribe(rendered,alphabet='v2'))==doc
        basis=next(json.loads(body) for q,body in files.items() if q.endswith('.json') and json.loads(body)['document']==p)
        audits[p]={k:v for k,v in audit_basis(doc,basis).items() if k!='definition_dependencies'}
        output=subprocess.run([sys.executable,'-X','utf8','-m','noema','parse','-i',str(ROOT/p)],check=True,capture_output=True,encoding='utf-8')
        assert json.loads(output.stdout)==doc
    reading=json.loads(text(READING));assert reading['segments']==alignment()['segments']
    for page in reading['facsimiles']:assert hashlib.sha256((ROOT/page['path']).read_bytes()).hexdigest()==page['sha256']
    paths=set(files)|{PARENT,READING,'data/einstein-electron-energy-balance-basis-v1.json','artifacts/written-units-v1/einstein-1905.json','reports/written-units-v1.json',
        'scripts/compose_electron_axis_motion.py','scripts/check_electron_axis_motion.py','tests/test_electron_axis_motion.py','docs/electron-axis-motion-v1.md',
        'scripts/compose_convention_comparison.py','scripts/compose_material_velocity.py','scripts/compose_origin_clock.py','scripts/compose_limits.py','scripts/compose_situated_criticism.py',
        'scripts/check_coordinate_correspondence.py','scripts/check_described_appraisals.py','scripts/check_plane_waveforms.py','scripts/check_rod_setup.py',
        'scripts/check_angle_composition.py','scripts/check_tau_differential.py','scripts/check_transverse_time.py',
        'scripts/check_phi_normalization.py','scripts/check_quantities.py','scripts/check_material_acceleration.py'}
    paths.update(p['path'] for p in reading['facsimiles'])
    paths.update('noema/'+n+'.py' for n in ('grammar','language','discourse','semantics','finite_semantics','extraction','meaning_basis','script'))
    return dict(status='partial_axial_motion_and_work_conditional',document=SOURCE,basis_audits=audits,
        geometry=geometry_checks(),conditional=conditional_checks(),attribution=attribution_check(),
        statements_preserved=185,new_author_attributions=1,roundtrips=True,cli_parse=True,alignment=alignment(),
        electrostatic_force_explained=False,slow_acceleration_explained=False,work_velocity_substitution_completed=False,
        verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sorted(paths)})


def main():
    cli=argparse.ArgumentParser();cli.add_argument('--verify-only',action='store_true');options=cli.parse_args()
    report=build_report()
    if options.verify_only:assert json.loads(REPORT.read_text(encoding='utf-8'))==report
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:stream.write(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print('Origin, rest, interval geometry and conditional attribution checked; force and physical derivation remain open',flush=True)


if __name__=='__main__':main()
