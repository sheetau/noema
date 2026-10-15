"""Check coefficient scales and the same object's rest-mass assignment."""
import argparse
from copy import deepcopy
from fractions import Fraction as F
from functools import lru_cache
import hashlib,json,subprocess,sys
from noema.grammar import parse,format_graph,number_word
from noema.extraction import extract_document
from noema.finite_semantics import evaluate_document
from noema.meaning_basis import audit_basis
from noema.polynomial_proofs import verify_universal
from noema.script import transcribe
from scripts.compose_force_mass_units import ROOT,PARENT,SOURCE,LIBRARY,CORE,ALL,INPUTS,MASS,NORMAL,NUMERIC,build
from scripts.compose_limits import call as k,op,both,v
from scripts.check_acceleration_units import UnitModel,SYMBOLS as OLD_SYMBOLS,DOMAIN as OLD_DOMAIN
from scripts.check_material_acceleration import ABSTRACT
from scripts.check_coordinate_correspondence import abstract
from scripts.check_described_appraisals import candidate
from scripts.check_plane_waveforms import setup,evaluate,OPS
from scripts.check_rod_setup import callbacks
from scripts.check_phi_normalization import number
from scripts.check_quantities import ARITHMETIC
from scripts.check_real_products import MEANINGS,assertion

REPORT=ROOT/'reports/force-mass-units-v1.json'
SYMBOLS={**OLD_SYMBOLS,**{n:'jqr'+number_word(i) for i,(n,_) in enumerate(MASS+NORMAL)}}
DOMAIN=OLD_DOMAIN+('massunit','massaxis')


@lru_cache(None)
def text(path):return (ROOT/path).read_text(encoding='utf-8')


def numerical_checks():
    beta=F(5,4);L,T=F(5625,32),F(1125,8)
    good=(5,3,beta,3,12,2,5,L,T)
    cases={'scaled':(good,True),'coherent_units':((5,3,beta,3,2,10,5,3*beta**3,3*beta**2),True),
        'mass_reading_only':((*good[:7],3*beta**3,3*beta**2),False),
        'force_scale_wrong_direction':((*good[:7],F(72,5)*beta**3,F(72,5)*beta**2),False),
        'same_mass_other_unit':((5,3,beta,6,6,2,5,L,T),True),
        'larger_force_unit':((5,3,beta,3,12,4,5,L/2,T/2),True),
        'larger_acceleration_unit':((5,3,beta,3,12,2,10,L*2,T*2),True),
        'zero_mass':((5,3,beta,0,12,2,5,0,0),True),
        'negative_scalar':((5,3,beta,-3,12,2,5,-L,-T),True),
        'zero_force_scale':((5,3,beta,0,12,0,5,0,0),False),
        'negative_mass_scale':((5,3,beta,-3,-12,2,5,L,T),False),
        'negative_acceleration_scale':((5,3,beta,-3,12,2,-5,L,T),False),
        'wrong_transverse_power':((*good[:8],90*beta),False),
        'negative_beta':((5,3,-beta,3,12,2,5,-L,T),False),
        'light_boundary':((5,5,1,3,12,2,5,90,90),False)}
    base=format_graph(extract_document(parse(text(LIBRARY)),roots=['sepz'],statement_indices=[]).document,'compact')
    rows={}
    for label,(args,expected) in cases.items():
        doc=parse(base+'q['+k('sepz',*map(number,args))+'].')
        result=[evaluate_document(doc,individuals=('object',),situations=('text',),primitives=ARITHMETIC)[0]['value']]
        for path in (LIBRARY,CORE):
            doc=abstract(candidate(text(path),'q['+k('seqa',*(k('bb',number(x)) for x in args))+'].'),OPS)
            _,model=setup(doc);result+=evaluate(doc,model)
        assert result==[expected]*3,(label,result)
        rows[label]=result
    return rows


def polynomial_checks():
    base=format_graph(extract_document(parse(text(LIBRARY)),roots=['sepz'],statement_indices=[]).document,'compact')
    fields=NUMERIC.split();terms=list(map(v,fields));V,s,beta,mu,M,Fc,A,L,T=terms
    mul=lambda a,b:k('ad',a,b);positive=lambda x:k('aa',number(0),x);eq=lambda a,b:op('e',a,b)
    relation=k('sepz',*terms);native=both(eq(L,mul(mu,mul(mul(beta,beta),beta))),eq(T,mul(mu,mul(beta,beta))))
    r=v('ratio');newmu,newM=map(v,('newmu','newscale'));newL,newT=map(v,('newlongitudinal','newtransverse'))
    claims={
        'coherent_units_recover_native_coefficients':assertion(NUMERIC,op('y',both(relation,eq(Fc,mul(M,A))),native)),
        'same_mass_in_another_unit_preserves_coefficients':assertion(NUMERIC+' newmu newscale',op('y',
            both(relation,positive(newM),eq(mul(mu,M),mul(newmu,newM))),k('sepz',V,s,beta,newmu,newM,Fc,A,L,T))),
        'force_unit_rescaling_changes_coefficient_readings':assertion(NUMERIC+' ratio newlongitudinal newtransverse',op('y',
            both(relation,positive(r),eq(L,mul(r,newL)),eq(T,mul(r,newT))),k('sepz',V,s,beta,mu,M,mul(Fc,r),A,newL,newT))),
        'acceleration_unit_rescaling_changes_coefficients':assertion(NUMERIC+' ratio',op('y',both(relation,positive(r)),
            k('sepz',V,s,beta,mu,M,Fc,mul(A,r),mul(L,r),mul(T,r)))),
        'mass_number_alone_always_determines_coefficients':assertion(NUMERIC,op('y',relation,native)),
    };rows={}
    for name,claim in claims.items():
        result=verify_universal(parse(base+claim),MEANINGS,timeout_ms=20000)[0]
        assert result['status']==('invalid' if name.startswith('mass_number') else 'valid'),(name,result)
        rows[name]=result
    return rows


class MassModel(UnitModel):
    def __init__(self,doc,variant='baseline'):
        super().__init__(doc,variant)
        make,read=self.cuts.make,self.cuts.read
        scales={'massscale':F(11 if variant=='wrong_mass_scale' else 12),'forcescale':F(3 if variant=='wrong_force_scale' else 2)}
        for name,value in {'light':5,'speed':3,'beta':F(5,4),'restmass':3,**scales}.items():self.model[SYMBOLS[name]]=lambda value=value:make(value)
        self.model['zramu']=self.model[SYMBOLS['restmass']]
        self.model[SYMBOLS['massunit']]=lambda:'other' if variant=='wrong_massunit' else 'massunit'
        self.model[SYMBOLS['massaxis']]=lambda:'lengthaxis' if variant=='same_mass_axis' else 'massaxis'
        massdim=lambda axis:F(axis=='massaxis')
        forcedim=lambda axis:F(axis=='massaxis')+F(axis=='lengthaxis')-F(1 if variant=='momentum_dimension' else 2)*F(axis=='timeaxis')
        original=self.model[SYMBOLS['units']]()
        def units(unit,dimension,scale,context):
            if unit not in ('massunit','forceunit'):return original(unit,dimension,scale,context)
            if variant=='unknown_mass_calibration' and unit=='massunit':raise ValueError('Mass calibration interpretation missing')
            fn,key=(massdim,'massscale') if unit=='massunit' else (forcedim,'forcescale')
            expected=scales[key]+(1 if variant=='wrong_unit_record' and unit=='forceunit' else 0)
            return context=='text' and read(scale)==expected and all(dimension(a)==fn(a) for a in DOMAIN)
        def assigned(matter,event,unit,value,context):
            if variant=='unknown_mass_assignment':raise ValueError('Rest-mass assignment missing')
            expected=('other' if variant=='other_mass_owner' else 'matter','other' if variant=='other_mass_event' else 'event',
                'massunit',F(4 if variant=='different_mass_reading' else 3),'text')
            return (matter,event,unit,read(value),context)==expected
        callbacks(doc,self.model,{SYMBOLS['massdim']:massdim,SYMBOLS['forcedim']:forcedim,
            SYMBOLS['units']:units,SYMBOLS['restmassassigned']:assigned})

    def evaluate(self):
        return [r['value'] for r in evaluate_document(self.doc,individuals=DOMAIN,situations=('text','other'),
            primitives={d['name']:self.model[d['name']] for d in self.doc['declarations'] if d['kind']=='primitive'},max_steps=5_000_000)]


def fixture(path,source=False,abstracted=ABSTRACT|{'sepw'}):
    declarations=''.join('r '+SYMBOLS[n]+'[] '+sort+'.' for n,sort in ALL)
    body=k('seqc',*(k(SYMBOLS[n]) for n,_ in ALL))
    if source:body='t['+k('seqd',*(k(SYMBOLS[n]) for n,_ in INPUTS))+']['+k(SYMBOLS['context'])+']'
    return abstract(candidate(text(path),declarations+'q['+body+'].'),abstracted)


def physical_checks():
    rows={}
    variants=('baseline','wrong_mass_scale','wrong_force_scale','same_mass_axis','momentum_dimension','wrong_massunit',
        'other_mass_owner','other_mass_event','different_mass_reading','wrong_unit_record','wrong_forceunit',
        'wrong_accelerationunit','wrong_coefficient','force_record_mismatch','fake_velocity_field','unconverted_reading')
    for path,source in ((CORE,False),(CORE,True),(SOURCE,True)):
        doc=fixture(path,source);result={}
        for variant in variants:
            actual=MassModel(doc,variant).evaluate();assert actual==[variant=='baseline'],(path,source,variant,actual)
            result[variant]=actual[0]
        if rows:assert result==next(iter(rows.values()))
        rows[path+':'+str(source)]=result
    return {'cases':rows,'same_mass_assignment_in_actual_constructor':True,
        'registered_rational_values_only':True,'observation_and_calibration_are_explicit_premises':True}


def refusal_checks():
    rows={};doc=fixture(CORE)
    for variant in ('unknown_mass_calibration','unknown_mass_assignment','unknown_bridge'):
        try:MassModel(doc,variant).evaluate()
        except ValueError as exc:
            assert 'missing' in str(exc);rows[variant]=str(exc)
        else:raise AssertionError('Missing physical premise invented')
    doc=fixture(CORE,abstracted=ABSTRACT)
    try:MassModel(doc).evaluate()
    except ValueError as exc:
        assert 'Cannot finitely quantify the rational number domain' in str(exc);rows['whole_history']=str(exc)
    else:raise AssertionError('All-real unit history inferred from finite samples')
    return rows


def build_report():
    files=build();audits={}
    for p,body in files.items():assert text(p)==body,p
    old=parse(text(PARENT));current=parse(text(SOURCE))
    assert current['statements']==old['statements'] and len(current['statements'])==176
    assert current['declarations'][:len(old['declarations'])]==old['declarations']
    assert all(d['kind']=='definition' for d in current['declarations'][len(old['declarations']):])
    for p in (SOURCE,LIBRARY,CORE):
        doc=parse(text(p))
        for notation in ('full','compact'):
            rendered=format_graph(doc,notation);assert parse(rendered)==parse(transcribe(rendered,alphabet='v2'))==doc
        basis=next(json.loads(body) for q,body in files.items() if q.endswith('.json') and json.loads(body)['document']==p)
        audits[p]={k:v for k,v in audit_basis(doc,basis).items() if k!='definition_dependencies'}
        result=subprocess.run([sys.executable,'-X','utf8','-m','noema','parse','-i',str(ROOT/p)],check=True,capture_output=True,encoding='utf-8')
        assert json.loads(result.stdout)==doc
    previous=json.loads(text('reports/acceleration-units-v1.json'));segment=deepcopy(previous['alignment']['segments'][0])
    segment['definitions']=['sepz','seqa','seqb','seqc','seqd']
    paths=set(files)|{PARENT,'data/einstein-acceleration-units-basis-v1.json','reports/acceleration-units-v1.json',
        'scripts/compose_force_mass_units.py','scripts/check_force_mass_units.py','tests/test_force_mass_units.py','docs/force-mass-units-v1.md',
        'scripts/compose_acceleration_units.py','scripts/check_acceleration_units.py','scripts/compose_material_acceleration.py',
        'scripts/check_material_acceleration.py','scripts/compose_origin_clock.py','scripts/compose_limits.py','scripts/compose_situated_criticism.py',
        'scripts/check_coordinate_correspondence.py','scripts/check_described_appraisals.py','scripts/check_plane_waveforms.py',
        'scripts/check_rod_setup.py','scripts/check_phi_normalization.py','scripts/check_quantities.py','scripts/check_real_products.py',
        'scripts/check_angle_composition.py','scripts/check_tau_differential.py','scripts/check_transverse_time.py','reports/written-units-v1.json'}
    paths.update('noema/'+n+'.py' for n in ('grammar','language','discourse','semantics','finite_semantics','polynomial_proofs','rational_proofs','extraction','meaning_basis','script'))
    return dict(status='partial_force_mass_and_acceleration_scale_binding',document=SOURCE,basis_audits=audits,
        numerical_checks=numerical_checks(),polynomial_checks=polynomial_checks(),physical_checks=physical_checks(),refusals=refusal_checks(),
        statements_preserved=176,new_primitives=0,roundtrips=True,cli_parse=True,alignment={'segments':[segment]},
        adds_new_text_coverage=False,physical_definitions_compared=False,unit_calibration_constructed=False,
        verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sorted(paths)})


def main():
    cli=argparse.ArgumentParser();cli.add_argument('--verify-only',action='store_true');options=cli.parse_args()
    report=build_report()
    if options.verify_only:assert json.loads(REPORT.read_text(encoding='utf-8'))==report
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:stream.write(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print('Force/mass scales and same-object mass assignment checked; full semantic review remains open',flush=True)


if __name__=='__main__':main()
