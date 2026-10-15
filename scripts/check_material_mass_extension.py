"""Check scoped mass-law applications and the reported charging argument."""
import argparse
from fractions import Fraction as F
from functools import lru_cache
import hashlib,json,subprocess,sys
from noema.grammar import parse,format_graph
from noema.finite_semantics import evaluate_document
from noema.meaning_basis import audit_basis
from noema.script import transcribe
from scripts.compose_material_mass_extension import ROOT,PARENT,SOURCE,LIBRARY,CORE,READING,META,VALUES,RELATIONS,FIELDS,SCOPE,build
from scripts.compose_limits import call as k
from scripts.check_coordinate_correspondence import abstract
from scripts.check_described_appraisals import candidate
from scripts.check_plane_waveforms import setup,OPS
from scripts.check_rod_setup import callbacks,guarded
from scripts.check_quantities import ARITHMETIC

REPORT=ROOT/'reports/material-mass-extension-v1.json'
PEOPLE=('first','second','eventone','eventtwo','comoving','lab','massunit','forceunit','accunit')
SCENES=('actual','other')


@lru_cache(None)
def text(path):return (ROOT/path).read_text(encoding='utf-8')


def fixture(path,source=False):
    declarations=''.join('r jqw'+n+'[] '+sort+'.' for n,sort in FIELDS+SCOPE)
    declarations+='r jqwpoint[] a.r jqwevent[] a.r jqwcontext[] d.'
    fields=[k('jqw'+n) for n,_ in FIELDS]
    queries='q['+k('seqy',k('jqwpoint'),k('jqwevent'),k('jqwcontext'),*fields)+'].'
    queries+='q[t[k sera[]][k jqwcontext[]]].' if source else 'q['+k('seqz',k('jqwcontext'),*[k('jqw'+n) for n,_ in SCOPE],*fields)+'].'
    return abstract(candidate(text(path),declarations+queries),OPS)


class MassExtensionModel:
    def __init__(self,doc,variant='baseline'):
        self.doc=doc;self.cuts,self.model=setup(doc);make=self.cuts.make
        self.model.update(ARITHMETIC)
        M,Fc,A=F(3),F(2),F(4)
        if variant=='coherent_units':Fc=M*A
        if variant=='mass_unit_rescaled':M*=2
        def expected_mass(point):
            mass=F(7 if point=='second' else 3)
            return mass/2 if variant=='mass_unit_rescaled' else mass
        def data(name,point,event,context):
            light,speed,beta=(F(13),F(5),F(13,12)) if point=='second' else (F(5),F(3),F(5,4))
            mu=expected_mass(point);factor=mu*M*A/Fc
            values=dict(light=light,speed=speed,beta=beta,restmass=mu,massscale=M,forcescale=Fc,accelerationscale=A,
                longitudinal=factor*beta**3,transverse=factor*beta**2)
            if variant in ('bad_second','unselected_bad') and point=='second':values['transverse']+=1
            if variant=='bad_second_event' and point=='first' and event=='eventtwo':values['transverse']+=1
            if variant=='wrong_transverse_power':values['transverse']=factor*beta
            if variant=='ignores_unit_scales':values['longitudinal']=mu*beta**3;values['transverse']=mu*beta**2
            if variant=='wrong_second_mass' and point=='second':values['restmass']*=2
            if variant=='light_boundary':values['speed']=light
            return make(values[name])
        meta={'forceframe':'lab' if variant=='wrong_forceframe' else 'comoving',
            'accelerationframe':'comoving' if variant=='wrong_accelerationframe' else 'lab',
            'massunit':'massunit','forceunit':'forceunit','accelerationunit':'accunit'}
        def assigned(point,event,unit,mu,context):
            if variant=='unknown_assignment':raise ValueError('Rest mass assignment missing')
            expected_events=('eventtwo',) if point=='second' or variant=='wrong_assignment_event' else (
                ('eventone','eventtwo') if variant in ('valid_second_event','bad_second_event') else ('eventone',))
            expected_unit='forceunit' if variant=='wrong_assignment_unit' else 'massunit'
            return event in expected_events and (unit,context)==(expected_unit,'actual') and self.cuts.read(mu)==expected_mass(point)
        def convention(point,forceframe,accframe,event,forceunit,accunit,context):
            return (forceframe,accframe,forceunit,accunit,context)==('comoving','lab','forceunit','accunit',
                'other' if variant=='wrong_convention_context' else 'actual')
        def calibrated(massunit,forceunit,accunit,massscale,forcescale,accscale,context):
            return variant!='missing_calibration' and (massunit,forceunit,accunit,context)==('massunit','forceunit','accunit','actual') and [
                self.cuts.read(x) for x in (massscale,forcescale,accscale)]==[M,Fc,A]
        def materials(point,context):
            selected=() if variant=='no_materials' else ('first',) if variant=='unselected_bad' else ('first','second')
            return context=='actual' and point in selected
        def cases(point,event,context):
            selected=set() if variant=='no_cases' else {('first','eventone'),('second','eventtwo')}
            if variant in ('valid_second_event','bad_second_event'):selected.add(('first','eventtwo'))
            return context=='actual' and (point,event) in selected
        entries={n:lambda p,e,c,n=n:meta[n] for n,_ in META}
        entries.update({n:lambda p,e,c,n=n:data(n,p,e,c) for n,_ in VALUES})
        entries.update(framevalid=lambda frame:frame in ('comoving','lab'),
            comoving=lambda p,frame,e,c:(frame,c)==('comoving','actual'),convention=convention,
            restmassassigned=assigned,calibrated=calibrated,materials=materials,cases=cases)
        callbacks(doc,self.model,{'jqw'+n:fn for n,fn in entries.items()})
        for n,_ in META+VALUES+[RELATIONS[-2],RELATIONS[-1],SCOPE[-1]]:self.model['zre'+n]=self.model['jqw'+n]
        self.model.update(va=entries['framevalid'],zpa=entries['comoving'],zraconvention=convention,zrdmaterial=materials,
            jqwpoint=lambda:'first',jqwevent=lambda:'eventone',jqwcontext=lambda:'actual')

    def evaluate(self):
        return [row['value'] for row in evaluate_document(self.doc,individuals=PEOPLE,situations=SCENES,
            primitives={d['name']:self.model[d['name']] for d in self.doc['declarations'] if d['kind']=='primitive'},
            max_steps=5_000_000,memoize_definitions=True,memoize_expressions=True)]


EXPECTED={
    'baseline':[True,True],'coherent_units':[True,True],'mass_unit_rescaled':[True,True],
    'bad_second':[True,False],'unselected_bad':[True,True],'valid_second_event':[True,True],'bad_second_event':[True,False],
    'wrong_transverse_power':[False,False],'ignores_unit_scales':[False,False],
    'wrong_second_mass':[True,False],'light_boundary':[False,False],
    'wrong_forceframe':[False,False],'wrong_accelerationframe':[False,False],
    'wrong_assignment_event':[False,False],'wrong_assignment_unit':[False,False],
    'wrong_convention_context':[False,False],'missing_calibration':[False,False],
    'no_materials':[True,True],'no_cases':[True,True],
}


def scope_checks():
    rows={}
    for path,source in ((LIBRARY,False),(CORE,True),(SOURCE,True)):
        doc=fixture(path,source);results={}
        for variant,expected in EXPECTED.items():
            value=MassExtensionModel(doc,variant).evaluate();assert value==expected,(path,variant,value)
            results[variant]=value
        rows[path]=results
    try:MassExtensionModel(fixture(LIBRARY),'unknown_assignment').evaluate()
    except ValueError as exc:assert 'missing' in str(exc)
    else:raise AssertionError('Mass assignment invented')
    return {'cases':rows,'unknown_assignments_refused':True,'existence_of_points_or_cases_inferred':False}


def attribution_check():
    doc=parse(text(CORE));model=guarded(doc);seen=[]
    for name,value in {'zrenode':'claim','zrelink':'reason','rd':'author','zrescope':'scope','ri':'actual'}.items():model[name]=lambda value=value:value
    symbol=lambda value:json.loads(value.syntax)['symbol']
    def claim(node,author,content,scope,context):
        seen.append(('claim',symbol(content)))
        return (node,author,scope,context)==('claim','author','scope','actual') and symbol(content)=='sera'
    def reason(node,author,premise,conclusion,scope,context):
        seen.append(('reason',symbol(premise),symbol(conclusion)))
        return (node,author,scope,context)==('reason','author','scope','actual') and (symbol(premise),symbol(conclusion))==('seqw','sera')
    model.update(uh=claim,zc=reason)
    values=evaluate_document(doc,individuals=('claim','reason','author','scope'),situations=('actual',),primitives=model)
    assert [row['value'] for row in values]==[True,True]
    return {'quoted_targets':[list(x) for x in seen],'premise_or_conclusion_executed':False,
        'mass_law_derived_from_charge_capability':False}


def alignment():
    source=json.loads(text('artifacts/written-units-v1/einstein-1905.json'))
    unit=next(u for u in source['units'] if u['id']=='einstein-1905:u0260');body=unit['text'];end=body.index('ein ponderabler')
    return {'segments':[dict(unit=unit['id'],unit_sha256=unit['text_sha256'],range=[0,end],text=body[:end],
        status='partial_scoped_mass_extension_and_reported_reason',definitions=['seqy','seqz','sera','seqw'])]}


def build_report():
    files=build();audits={}
    for p,body in files.items():assert text(p)==body,p
    old=parse(text(PARENT));current=parse(text(SOURCE))
    assert current['statements'][:-2]==old['statements'] and len(old['statements'])==179
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
    paths=set(files)|{PARENT,READING,reading['facsimile_path'],'data/einstein-arbitrary-small-charge-basis-v1.json',
        'artifacts/written-units-v1/einstein-1905.json','reports/written-units-v1.json','reports/force-mass-units-v1.json',
        'scripts/compose_material_mass_extension.py','scripts/check_material_mass_extension.py','tests/test_material_mass_extension.py','docs/material-mass-extension-v1.md',
        'scripts/compose_convention_comparison.py','scripts/compose_force_mass_units.py','scripts/compose_origin_clock.py','scripts/compose_limits.py','scripts/compose_situated_criticism.py',
        'scripts/check_coordinate_correspondence.py','scripts/check_described_appraisals.py','scripts/check_plane_waveforms.py','scripts/check_rod_setup.py',
        'scripts/check_angle_composition.py','scripts/check_tau_differential.py','scripts/check_transverse_time.py','scripts/check_quantities.py'}
    paths.update('noema/'+n+'.py' for n in ('grammar','language','discourse','semantics','finite_semantics','extraction','meaning_basis','script'))
    return dict(status='partial_material_mass_extension_and_reported_reason',document=SOURCE,basis_audits=audits,
        scope=scope_checks(),attribution=attribution_check(),statements_preserved=179,new_author_attributions=2,
        roundtrips=True,cli_parse=True,alignment=alignment(),physical_transfer_proved=False,scope_completeness_verified=False,
        verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sorted(paths)})


def main():
    cli=argparse.ArgumentParser();cli.add_argument('--verify-only',action='store_true');options=cli.parse_args()
    report=build_report()
    if options.verify_only:assert json.loads(REPORT.read_text(encoding='utf-8'))==report
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:stream.write(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print('Scoped mass-law applications and reported charging reason checked; physical transfer remains open',flush=True)


if __name__=='__main__':main()
