"""Check local dynamics and power at zero speed without assuming integral substitution."""
import argparse
from fractions import Fraction as F
from functools import lru_cache
from math import isqrt
import hashlib,json,subprocess,sys
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.finite_semantics import evaluate_document
from noema.meaning_basis import audit_basis
from noema.polynomial_proofs import verify_universal
from noema.script import transcribe
from scripts.compose_electron_power_law import ROOT,PARENT,SOURCE,LIBRARY,CORE,READING,PROFILES,CONSTANTS,NUMERIC,build
from scripts.compose_electron_axis_motion import ALL as MOTION
from scripts.compose_limits import call as k,both,op,v
from scripts.check_coordinate_correspondence import abstract
from scripts.check_described_appraisals import candidate
from scripts.check_electron_axis_motion import AxisModel,fixture as axis_fixture,PEOPLE,SCENES
from scripts.check_plane_waveforms import setup,OPS
from scripts.check_rod_setup import callbacks,guarded
from scripts.check_phi_normalization import number
from scripts.check_quantities import ARITHMETIC
from scripts.check_real_products import MEANINGS,assertion
from scripts.check_material_acceleration import unwrap,derivative,poly_value

REPORT=ROOT/'reports/electron-power-law-v1.json'
TIMES=(F(0),F(3,4),F(1))


@lru_cache(None)
def text(path):return (ROOT/path).read_text(encoding='utf-8')


def evaluate(doc,model):
    return [r['value'] for r in evaluate_document(doc,individuals=PEOPLE,situations=SCENES,
        primitives={d['name']:model[d['name']] for d in doc['declarations'] if d['kind']=='primitive'},max_steps=5_000_000)]


def numeric_checks():
    base=format_graph(extract_document(parse(text(LIBRARY)),roots=['sesa','sesc'],statement_indices=[]).document,'compact')
    cases={'moving':((5,3,F(5,4),2,2,F(125,32),2),[True,True]),
        'initial_rest':((5,0,1,2,2,2,2),[True,True]),'zero_speed_wrong_force':((5,0,1,2,2,3,2),[False,True]),
        'moving_wrong_force':((5,3,F(5,4),2,2,3,2),[False,False]),
        'negative_charge_and_field':((5,3,F(5,4),2,-2,F(-125,32),2),[True,True]),
        'negative_speed':((5,-3,F(5,4),2,2,F(125,32),2),[True,True])}
    rows={}
    for label,(numbers,expected) in cases.items():
        doc=parse(base+''.join('q['+k(name,*map(number,numbers))+'].' for name in ('sesa','sesc')))
        result=evaluate(doc,ARITHMETIC);assert result==expected,(label,result)
        for path in (LIBRARY,CORE):
            queries=''.join('q['+k(name,*(k('bb',number(x)) for x in numbers))+'].' for name in ('sesb','sesd'))
            doc=abstract(candidate(text(path),queries),OPS);_,model=setup(doc);model.update(ARITHMETIC)
            row=evaluate(doc,model);assert row==expected,(label,path,row);result+=row
        rows[label]=result
    return rows


def polynomial_checks():
    base=format_graph(extract_document(parse(text(LIBRARY)),roots=['sesa','sesc'],statement_indices=[]).document,'compact')
    terms=[v(n) for n in NUMERIC.split()];law=k('sesa',*terms);power=k('sesc',*terms)
    nonzero=op('u',op('e',v('speed'),number(0)))
    claims={'force_law_implies_power_equality':assertion(NUMERIC,op('y',law,power)),
        'nonzero_speed_permits_recovering_force_law':assertion(NUMERIC,op('y',both(power,nonzero),law)),
        'power_equality_alone_implies_force_law':assertion(NUMERIC,op('y',power,law))};rows={}
    for label,claim in claims.items():
        result=verify_universal(parse(base+claim),MEANINGS,timeout_ms=20000)[0]
        assert result['status']==('invalid' if label=='power_equality_alone_implies_force_law' else 'valid'),(label,result)
        rows[label]=result
    return rows


def fixture(path,whole=False):
    doc=axis_fixture(path)
    declarations=''.join('r jqz'+n+'[] '+sort+'.' for n,sort in PROFILES+CONSTANTS)
    fields=[k('jqz'+n) for n,_ in PROFILES+CONSTANTS]
    queries='q['+k('sesf',*[k('jqy'+n) for n,_ in MOTION],*fields)+'].' if whole else ''.join(
        'q['+k('sese',k('jqydomain'),k('jqycurve'),k('bb',number(t)),*fields)+'].' for t in TIMES)
    return candidate(format_graph(doc,'compact'),declarations+queries)


class DynamicsModel(AxisModel):
    def __init__(self,doc,variant='baseline'):
        super().__init__(doc)
        make,read=self.cuts.make,self.cuts.read;light=F(5,2);mass=F(3);charge=F(-2 if variant=='negative_charge' else 2)
        velocity_poly=(F(0),F(-2 if variant=='wrong_velocity' else 2))
        def velocity(time):return make(poly_value(velocity_poly,read(time)))
        def acceleration(time):return make(3 if variant=='wrong_acceleration' else 2)
        def profile(position):
            if variant=='unknown_field':raise ValueError('Electrostatic profile missing')
            x=read(position);ratio=light**2/(light**2-4*x)
            numerator,denominator=isqrt(ratio.numerator),isqrt(ratio.denominator)
            if numerator*numerator!=ratio.numerator or denominator*denominator!=ratio.denominator:raise ValueError('Outside the registered rational-square fixture')
            beta=F(5,3) if variant=='fixed_terminal_beta' else F(numerator,denominator)
            value=mass*beta**3*2/charge
            if variant=='wrong_field' or (variant=='zero_speed_wrong_force' and x==0):value+=1
            return make(value)
        old_derivative=self.model['sjs']
        def differential(domain,function,time,value):
            if variant=='unknown_derivative':raise ValueError('Derivative interpretation missing')
            if unwrap(function).implementation is velocity:
                return domain(time) and read(value)==poly_value(derivative(velocity_poly),read(time))
            return old_derivative(domain,function,time,value)
        callbacks(doc,self.model,{'jqzvelocity':velocity,'jqzacceleration':acceleration,'jqzprofile':profile})
        self.model.update(jqzlight=lambda:make(light),jqzmass=lambda:make(mass),
            jqzcharge=lambda:make(3 if variant=='wrong_charge' else charge),sjs=differential)
        for source,name in {'zrivelocity':'velocity','zriacceleration':'acceleration','zrgprofile':'profile',
            'tc':'light','zramu':'mass','zrgcharge':'charge'}.items():self.model[source]=self.model['jqz'+name]
        self.model['zrhdrive']=lambda p,f,frame,start,end,fn,q,c:(p,f,frame,start,end,c)==('particle','field','frame','start','end','actual') and unwrap(fn).implementation is profile and read(q)==charge


EXPECTED={'baseline':[True]*3,'negative_charge':[True]*3,'fixed_terminal_beta':[False,False,True],
    'wrong_field':[False]*3,'zero_speed_wrong_force':[False,True,True],
    'wrong_velocity':[False]*3,'wrong_acceleration':[False]*3,'wrong_charge':[False]*3}


def local_checks():
    rows={}
    for path in (LIBRARY,CORE,SOURCE):
        doc=fixture(path);results={}
        for variant,expected in EXPECTED.items():
            model=DynamicsModel(doc,variant);values=evaluate(doc,model.model)
            assert values==expected,(path,variant,values);results[variant]=values
        rows[path]=results
    for variant in ('unknown_field','unknown_derivative'):
        try:evaluate(fixture(CORE),DynamicsModel(fixture(CORE),variant).model)
        except ValueError as exc:assert 'missing' in str(exc)
        else:raise AssertionError('Unknown interpretation invented')
    doc=fixture(CORE,whole=True)
    try:evaluate(doc,DynamicsModel(doc).model)
    except ValueError as exc:assert any(w in str(exc).lower() for w in ('domain','quantif','function','enumerat','rational')),str(exc)
    else:raise AssertionError('All motion times silently replaced by samples')
    return {'times':list(map(str,TIMES)),'cases':rows,'registered_derivatives_only':True,'all_real_time_domain_refused':True}


def source_instance_checks():
    rows={}
    for path in (CORE,SOURCE):
        outcomes={}
        for variant in ('baseline','fixed_terminal_beta','zero_speed_wrong_force'):
            values=[]
            for t in TIMES:
                doc=fixture(path);definition=next(d for d in doc['declarations'] if d['name']=='sesf');replaced=[]
                literal={'kind':'call','symbol':'bb','arguments':[{'kind':'number','numerator':t.numerator,'denominator':t.denominator}]}
                def substitute(node,name):
                    if isinstance(node,list):return [substitute(x,name) for x in node]
                    if not isinstance(node,dict):return node
                    if node=={'kind':'variable','name':name}:return literal
                    return {key:substitute(value,name) for key,value in node.items()}
                def instantiate(node):
                    if isinstance(node,list):return [instantiate(x) for x in node]
                    if not isinstance(node,dict):return node
                    if node.get('kind')=='forall':replaced.append(node['variable']);return substitute(node['body'],node['variable'])
                    return {key:instantiate(value) for key,value in node.items()}
                definition['body']=instantiate(definition['body']);assert len(replaced)==1
                doc=candidate(format_graph(doc,'compact'),'q[t[k sesg[]][k jqycontext[]]].')
                values+=evaluate(doc,DynamicsModel(doc,variant).model)
            assert values==EXPECTED[variant],(path,variant,values);outcomes[variant]=values
        rows[path]=outcomes
    return {'single_time_source_instances':rows,'full_interval_claim_proved':False}


def attribution_check():
    doc=parse(text(CORE));model=guarded(doc)
    for name,value in {'zrinode':'node','rd':'author','zrgscope':'scope','ri':'actual'}.items():model[name]=lambda value=value:value
    model['uh']=lambda n,a,c,s,t:(n,a,s,t)==('node','author','scope','actual') and json.loads(c.syntax)['symbol']=='sesg'
    assert evaluate_document(doc,individuals=('node','author','scope'),situations=('actual',),primitives=model)[0]['value'] is True
    return {'content':'sesg','dynamics_or_work_integrals_executed':False}


def alignment():
    work=json.loads(text('artifacts/written-units-v1/einstein-1905.json'));unit=next(u for u in work['units'] if u['id']=='einstein-1905:u0261');body=unit['text']
    start=body.index('während des ganzen');end=body.index(' gilt:',start)+len(' gilt')
    return {'segments':[dict(unit=unit['id'],unit_sha256=unit['text_sha256'],range=[start,end],text=body[start:end],
        status='partial_longitudinal_equation_on_full_motion_interval',definitions=['sesb','sese','sesf','sesg'])]}


def build_report():
    files=build();audits={}
    for p,body in files.items():assert text(p)==body,p
    old=parse(text(PARENT));current=parse(text(SOURCE))
    assert current['statements'][:-1]==old['statements'] and len(old['statements'])==186
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
    assert hashlib.sha256((ROOT/reading['facsimile_path']).read_bytes()).hexdigest()==reading['facsimile_sha256']
    paths=set(files)|{PARENT,READING,reading['facsimile_path'],'data/einstein-electron-axis-motion-basis-v1.json',
        'artifacts/written-units-v1/einstein-1905.json','reports/written-units-v1.json',
        'scripts/compose_electron_power_law.py','scripts/check_electron_power_law.py','tests/test_electron_power_law.py','docs/electron-power-law-v1.md',
        'scripts/compose_convention_comparison.py','scripts/compose_electron_axis_motion.py','scripts/compose_origin_clock.py','scripts/compose_limits.py','scripts/compose_situated_criticism.py',
        'scripts/check_coordinate_correspondence.py','scripts/check_described_appraisals.py','scripts/check_electron_axis_motion.py','scripts/check_plane_waveforms.py','scripts/check_rod_setup.py',
        'scripts/check_angle_composition.py','scripts/check_tau_differential.py','scripts/check_transverse_time.py',
        'scripts/check_phi_normalization.py','scripts/check_quantities.py','scripts/check_real_products.py','scripts/check_material_acceleration.py'}
    paths.update('noema/'+n+'.py' for n in ('grammar','language','discourse','semantics','finite_semantics','extraction','meaning_basis','script','polynomial_proofs'))
    return dict(status='partial_longitudinal_dynamics_and_power_on_same_trajectory',document=SOURCE,basis_audits=audits,
        numeric=numeric_checks(),polynomial=polynomial_checks(),local=local_checks(),source_instances=source_instance_checks(),attribution=attribution_check(),
        statements_preserved=186,new_author_attributions=1,roundtrips=True,cli_parse=True,alignment=alignment(),
        integral_substitution_completed=False,physical_force_explanation_completed=False,
        verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sorted(paths)})


def main():
    cli=argparse.ArgumentParser();cli.add_argument('--verify-only',action='store_true');options=cli.parse_args()
    report=build_report()
    if options.verify_only:assert json.loads(REPORT.read_text(encoding='utf-8'))==report
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:stream.write(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print('Local longitudinal dynamics and power checked; no division by zero or full integral derivation claimed',flush=True)


if __name__=='__main__':main()
