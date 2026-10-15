"""Verify calibrated energy applications and the reference to the charging argument."""
import argparse
from fractions import Fraction as F
from functools import lru_cache
import hashlib,json,subprocess,sys
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.finite_semantics import evaluate_document
from noema.meaning_basis import audit_basis
from noema.polynomial_proofs import verify_universal
from noema.script import transcribe
from scripts.compose_material_energy_extension import ROOT,PARENT,SOURCE,LIBRARY,CORE,READING,NUMERIC,META,VALUES,RELATIONS,FIELDS,SCOPE,SOURCE_SYMBOLS,build
from scripts.compose_limits import call as k,both,op,v
from scripts.check_coordinate_correspondence import abstract
from scripts.check_described_appraisals import candidate
from scripts.check_plane_waveforms import setup,OPS
from scripts.check_rod_setup import callbacks,guarded
from scripts.check_phi_normalization import number
from scripts.check_quantities import ARITHMETIC
from scripts.check_real_products import MEANINGS,assertion

REPORT=ROOT/'reports/material-energy-extension-v1.json'
PEOPLE=('first','second','eventone','eventtwo','lab','other','massunit','speedunit','energyunit')
SCENES=('actual','other')


@lru_cache(None)
def text(path): return (ROOT/path).read_text(encoding='utf-8')


def evaluate(doc,model):
    return [row['value'] for row in evaluate_document(doc,individuals=PEOPLE,situations=SCENES,
        primitives={d['name']:model[d['name']] for d in doc['declarations'] if d['kind']=='primitive'},
        max_steps=5_000_000,memoize_definitions=True,memoize_expressions=True)]


def numerical_checks():
    base=format_graph(extract_document(parse(text(LIBRARY)),roots=['sete'],statement_indices=[]).document,'compact')
    cases={
        'calibrated':((5,3,F(5,4),3,F(225,4),3,2,4),True),
        'coherent_units':((5,3,F(5,4),3,F(75,4),3,2,12),True),
        'mass_unit_rescaled':((5,3,F(5,4),F(3,2),F(225,4),6,2,4),True),
        'speed_unit_rescaled':((F(5,2),F(3,2),F(5,4),3,F(225,4),3,4,4),True),
        'energy_unit_rescaled':((5,3,F(5,4),3,F(225,8),3,2,8),True),
        'at_rest':((5,0,1,3,0,3,2,4),True),
        'ignores_unit_scales':((5,3,F(5,4),3,F(75,4),3,2,4),False),
        'energy_scale_wrong_direction':((5,3,F(5,4),3,900,3,2,4),False),
        'rest_energy_included':((5,3,F(5,4),3,F(1125,4),3,2,4),False),
        'light_boundary':((5,5,1,3,0,3,2,4),False),
        'zero_mass':((5,3,F(5,4),0,0,3,2,4),False),
        'zero_energy_scale':((5,3,F(5,4),3,0,3,2,0),False),
        'negative_speed_scale':((5,3,F(5,4),3,F(225,4),3,-2,4),False),
    };rows={}
    for label,(numbers,expected) in cases.items():
        doc=parse(base+'q['+k('sete',*map(number,numbers))+'].');result=evaluate(doc,ARITHMETIC)
        for path in (LIBRARY,CORE):
            query='q['+k('setf',*(k('bb',number(x)) for x in numbers))+'].'
            doc=abstract(candidate(text(path),query),OPS);_,model=setup(doc);model.update(ARITHMETIC)
            result+=evaluate(doc,model)
        assert result==[expected]*3,(label,result);rows[label]=result
    return rows


def polynomial_checks():
    base=format_graph(extract_document(parse(text(LIBRARY)),roots=['sete'],statement_indices=[]).document,'compact')
    terms=list(map(v,NUMERIC.split()));V,s,b,m,W,M,S,E=terms
    mul=lambda a,b:k('ad',a,b);eq=lambda a,b:op('e',a,b);positive=lambda a:k('aa',number(0),a)
    relation=k('sete',*terms);newmass,newM,newW,newE,newV,news,newS=map(v,('newmass','newmassscale','newenergy','newenergyscale','newlight','newspeed','newspeedscale'))
    claims={
        'coherent_units_recover_original_expression':assertion(NUMERIC,op('y',
            both(relation,eq(E,mul(M,mul(S,S)))),k('serb',V,s,b,m,W))),
        'same_mass_under_new_unit':assertion(NUMERIC+' newmass newmassscale',op('y',
            both(relation,positive(newM),eq(mul(m,M),mul(newmass,newM))),k('sete',V,s,b,newmass,W,newM,S,E))),
        'same_energy_under_new_unit':assertion(NUMERIC+' newenergy newenergyscale',op('y',
            both(relation,positive(newE),eq(mul(W,E),mul(newW,newE))),k('sete',V,s,b,m,newW,M,S,newE))),
        'same_light_and_speed_under_new_unit':assertion(NUMERIC+' newlight newspeed newspeedscale',op('y',
            both(relation,positive(newS),eq(mul(V,S),mul(newV,newS)),eq(mul(s,S),mul(news,newS))),k('sete',newV,news,b,m,W,M,newS,E))),
        'raw_numbers_always_obey_unscaled_expression':assertion('',op('y',
            k('sete',*map(number,(5,3,F(5,4),3,F(225,4),3,2,4))),
            k('serb',*map(number,(5,3,F(5,4),3,F(225,4)))))),
    };rows={}
    for name,claim in claims.items():
        result=verify_universal(parse(base+claim),MEANINGS,timeout_ms=20000)[0]
        assert result['status']==('invalid' if name.startswith('raw_') else 'valid'),(name,result)
        rows[name]=result
    return rows


def fixture(path,source=False):
    declarations=''.join('r jmat'+n+'[] '+sort+'.' for n,sort in FIELDS+SCOPE)
    declarations+='r jmatpoint[] a.r jmatevent[] a.r jmatcontext[] d.'
    fields=[k('jmat'+n) for n,_ in FIELDS]
    queries='q['+k('setg',k('jmatpoint'),k('jmatevent'),k('jmatcontext'),*fields)+'].'
    queries+='q[t[k seti[]][k jmatcontext[]]].' if source else 'q['+k('seth',k('jmatcontext'),*[k('jmat'+n) for n,_ in SCOPE],*fields)+'].'
    return abstract(candidate(text(path),declarations+queries),OPS)


class EnergyExtensionModel:
    def __init__(self,doc,variant='baseline'):
        self.doc=doc;self.cuts,self.model=setup(doc);make=self.cuts.make;read=self.cuts.read;self.model.update(ARITHMETIC)
        M,S,E=F(3),F(2),F(4)
        if variant=='coherent_units':E=M*S*S
        if variant=='mass_unit_rescaled':M*=2
        if variant=='speed_unit_rescaled':S*=2
        if variant=='energy_unit_rescaled':E*=2
        def readings(point,event):
            light,speed,beta=(F(5),F(4),F(5,3)) if point=='second' else (F(5),F(3),F(5,4))
            if point=='first' and event=='eventtwo':speed,beta=F(0),F(1)
            mu=F(7 if point=='second' else 3)
            energy=mu*3*(light*2)**2*(beta-1)/E
            if variant=='mass_unit_rescaled':mu/=2
            if variant=='speed_unit_rescaled':light/=2;speed/=2
            if variant in ('bad_second','unselected_bad') and point=='second':energy+=1
            if variant=='bad_second_event' and point=='first' and event=='eventtwo':energy+=1
            return dict(light=light,speed=speed,beta=beta,restmass=mu,energy=energy,massscale=M,speedscale=S,energyscale=E)
        def data(name,point,event,context):
            row=readings(point,event)
            if variant=='ignores_unit_scales':row['energy']=row['restmass']*row['light']**2*(row['beta']-1)
            if variant=='wrong_mass_value' and point=='second':row['restmass']*=2
            if variant=='wrong_light_value' and point=='second':row['light']=F(20,3)
            if variant=='light_boundary':row['speed']=row['light']
            return make(row[name])
        units=dict(frame='other' if variant=='wrong_frame' else 'lab',massunit='massunit',speedunit='speedunit',energyunit='energyunit')
        def restmass(point,event,unit,value,context):
            if variant=='unknown_assignment':raise ValueError('Rest-mass assignment missing')
            return (unit,context)==('massunit','actual') and read(value)==readings(point,event)['restmass']
        def speedassigned(point,frame,event,unit,value,context):
            return (frame,unit,context)==('lab','other' if variant=='wrong_speed_unit' else 'speedunit','actual') and read(value)==readings(point,event)['speed']
        def lightassigned(frame,event,unit,value,context):
            expected=readings('first',event)['light']
            return (frame,unit,context)==('lab','other' if variant=='wrong_light_unit' else 'speedunit','actual') and read(value)==expected
        def kinetic(point,frame,event,unit,value,context):
            expected=['first' if point=='first' else 'second','lab',event,'energyunit','actual']
            for i,key in enumerate(('particle','frame','event','unit','context')):
                if variant=='wrong_kinetic_'+key:expected[i]='other'
            return [point,frame,event,unit,context]==expected and read(value)==readings(point,event)['energy']
        def calibrated(massunit,speedunit,energyunit,massscale,speedscale,energyscale,context):
            return variant!='missing_calibration' and (massunit,speedunit,energyunit,context)==('massunit','speedunit','energyunit','actual') and [read(x) for x in (massscale,speedscale,energyscale)]==[M,S,E]
        def materials(point,context):
            selected=() if variant=='no_materials' else ('first',) if variant=='unselected_bad' else ('first','second')
            return context=='actual' and point in selected
        def cases(point,event,context):
            selected=set() if variant=='no_cases' else {('first','eventone'),('second','eventtwo')}
            if variant in ('valid_second_event','bad_second_event'):selected.add(('first','eventtwo'))
            return context=='actual' and (point,event) in selected
        entries={n:lambda p,e,c,n=n:units[n] for n,_ in META}
        entries.update({n:lambda p,e,c,n=n:data(n,p,e,c) for n,_ in VALUES})
        entries.update(framevalid=lambda f:f in ('lab','other'),restmassassigned=restmass,speedassigned=speedassigned,
                       lightassigned=lightassigned,kinetic=kinetic,calibrated=calibrated,materials=materials,cases=cases)
        callbacks(doc,self.model,{'jmat'+n:fn for n,fn in entries.items()})
        for name,_ in FIELDS+SCOPE:
            if name not in ('framevalid','materials'):self.model[SOURCE_SYMBOLS.get(name,'zrk'+name)]=self.model['jmat'+name]
        self.model.update(va=entries['framevalid'],zrdmaterial=materials,jmatpoint=lambda:'first',jmatevent=lambda:'eventone',jmatcontext=lambda:'actual')

    def evaluate(self):return evaluate(self.doc,self.model)


EXPECTED={
    'baseline':[True,True],'coherent_units':[True,True],'mass_unit_rescaled':[True,True],
    'speed_unit_rescaled':[True,True],'energy_unit_rescaled':[True,True],
    'bad_second':[True,False],'unselected_bad':[True,True],'valid_second_event':[True,True],'bad_second_event':[True,False],
    'wrong_mass_value':[True,False],'wrong_light_value':[True,False],'ignores_unit_scales':[False,False],'light_boundary':[False,False],
    'wrong_frame':[False,False],'wrong_speed_unit':[False,False],'wrong_light_unit':[False,False],
    'missing_calibration':[False,False],'no_materials':[True,True],'no_cases':[True,True],
    **{'wrong_kinetic_'+n:[False,False] for n in ('particle','frame','event','unit','context')},
}


def scope_checks():
    rows={}
    for path,source in ((LIBRARY,False),(CORE,True),(SOURCE,True)):
        doc=fixture(path,source);results={}
        for variant,expected in EXPECTED.items():
            actual=EnergyExtensionModel(doc,variant).evaluate();assert actual==expected,(path,variant,actual)
            results[variant]=actual
        rows[path]=results
    try:EnergyExtensionModel(fixture(LIBRARY),'unknown_assignment').evaluate()
    except ValueError as exc:assert 'missing' in str(exc)
    else:raise AssertionError('Mass assignment silently invented')
    return dict(cases=rows,unknown_assignment_refused=True,existence_of_materials_or_cases_inferred=False)


def attribution_check():
    doc=parse(text(CORE));model=guarded(doc);seen=[]
    for name,value in {'zrknode':'claim','zrklink':'reason','rd':'author','zrkscope':'scope','ri':'actual'}.items():model[name]=lambda value=value:value
    symbol=lambda x:json.loads(x.syntax)['symbol']
    def claim(node,author,content,scope,context):
        seen.append(['claim',symbol(content)])
        return (node,author,scope,context)==('claim','author','scope','actual') and symbol(content)=='seti'
    def reason(node,author,premise,conclusion,scope,context):
        seen.append(['reason',symbol(premise),symbol(conclusion)])
        return (node,author,scope,context)==('reason','author','scope','actual') and (symbol(premise),symbol(conclusion))==('seqw','seti')
    model.update(uh=claim,zc=reason)
    result=evaluate_document(doc,individuals=('claim','reason','author','scope'),situations=('actual',),primitives=model)
    assert [row['value'] for row in result]==[True,True]
    return dict(quoted_targets=seen,charging_or_energy_conditions_executed=False,energy_law_derived_from_charge_capability=False)


def alignment():
    source=json.loads(text('artifacts/written-units-v1/einstein-1905.json'))
    unit=next(u for u in source['units'] if u['id']=='einstein-1905:u0264')
    return {'segments':[dict(unit=unit['id'],unit_sha256=unit['text_sha256'],range=[0,len(unit['text'])],text=unit['text'],
        status='partial_scoped_energy_extension_and_reported_reason',definitions=['sete','setf','setg','seth','seti','seqw'])]}


def build_report():
    files=build();audits={}
    for p,body in files.items():assert text(p)==body,p
    old=parse(text(PARENT));current=parse(text(SOURCE))
    assert current['statements'][:-2]==old['statements'] and len(old['statements'])==189
    assert current['declarations'][:len(old['declarations'])]==old['declarations']
    for path in (SOURCE,LIBRARY,CORE):
        doc=parse(text(path));basis=next(json.loads(body) for p,body in files.items() if p.endswith('.json') and json.loads(body)['document']==path)
        audits[path]={k:v for k,v in audit_basis(doc,basis).items() if k!='definition_dependencies'}
        for notation in ('full','compact'):
            rendered=format_graph(doc,notation);assert parse(rendered)==parse(transcribe(rendered,alphabet='v2'))==doc
        output=subprocess.run([sys.executable,'-X','utf8','-m','noema','parse','-i',str(ROOT/path)],check=True,capture_output=True,encoding='utf-8')
        assert json.loads(output.stdout)==doc
    reading=json.loads(text(READING));assert reading['segments']==alignment()['segments']
    assert hashlib.sha256((ROOT/reading['facsimile_path']).read_bytes()).hexdigest()==reading['facsimile_sha256']
    paths=set(files)|{PARENT,READING,reading['facsimile_path'],'data/einstein-energy-boundary-basis-v1.json',
        'artifacts/written-units-v1/einstein-1905.json','reports/written-units-v1.json',
        'scripts/compose_material_energy_extension.py','scripts/check_material_energy_extension.py','tests/test_material_energy_extension.py','docs/material-energy-extension-v1.md',
        'scripts/compose_convention_comparison.py','scripts/compose_force_mass_units.py','scripts/compose_origin_clock.py','scripts/compose_limits.py','scripts/compose_situated_criticism.py',
        'scripts/check_coordinate_correspondence.py','scripts/check_described_appraisals.py','scripts/check_plane_waveforms.py','scripts/check_rod_setup.py',
        'scripts/check_phi_normalization.py','scripts/check_quantities.py','scripts/check_real_products.py','scripts/check_tau_differential.py','scripts/check_angle_composition.py'}
    paths.update('noema/'+n+'.py' for n in ('grammar','language','discourse','semantics','finite_semantics','extraction','meaning_basis','script','polynomial_proofs'))
    return dict(status='partial_calibrated_material_energy_extension',document=SOURCE,basis_audits=audits,
        numeric=numerical_checks(),polynomial=polynomial_checks(),scope=scope_checks(),attribution=attribution_check(),
        statements_preserved=189,new_author_attributions=2,roundtrips=True,cli_parse=True,alignment=alignment(),
        physical_extension_argument_proved=False,verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sorted(paths)})


def main():
    cli=argparse.ArgumentParser();cli.add_argument('--verify-only',action='store_true');options=cli.parse_args()
    report=build_report()
    if options.verify_only:assert json.loads(REPORT.read_text(encoding='utf-8'))==report
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:stream.write(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print('Material energy scope and unit scales checked; charging argument remains attributed',flush=True)


if __name__=='__main__': main()
