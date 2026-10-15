"""Check directional coefficients without identifying force conventions."""
import argparse
from copy import deepcopy
from fractions import Fraction as F
from functools import lru_cache
import hashlib,json,subprocess,sys
from noema.grammar import parse,format_graph
from noema.finite_semantics import evaluate_document
from noema.meaning_basis import audit_basis
from noema.polynomial_proofs import verify_universal
from noema.script import transcribe
from scripts.compose_mass_coefficients import ROOT,PARENT,SOURCE,LIBRARY,CORE,READING,CUT,FACTORS,COMPONENTS,build
from scripts.compose_limits import call as k,op,both,v
from scripts.check_phi_normalization import number
from scripts.check_quantities import ARITHMETIC
from scripts.check_real_products import MEANINGS,assertion
from scripts.check_coordinate_correspondence import abstract
from scripts.check_described_appraisals import candidate
from scripts.check_plane_waveforms import setup,evaluate,OPS
from scripts.check_rod_setup import guarded

REPORT=ROOT/'reports/mass-coefficients-v1.json'


@lru_cache(None)
def text(path):return (ROOT/path).read_text(encoding='utf-8')


def numeric_cases():
    good=(5,3,F(5,4),4,F(125,16),F(25,4))
    rows={
        'normalized':('sepb',good,True),
        'opposite_speed':('sepb',(5,-3,*good[2:]),True),
        'rest':('sepb',(5,0,1,4,4,4),True),
        'zero_mass':('sepb',(5,3,F(5,4),0,0,0),True),
        'negative_scalar':('sepb',(5,3,F(5,4),-4,-F(125,16),-F(25,4)),True),
        'wrong_transverse_power':('sepb',(*good[:5],5),False),
        'swapped_coefficients':('sepb',(*good[:4],good[5],good[4]),False),
        'negative_beta':('sepb',(5,3,-F(5,4),4,-F(125,16),F(25,4)),False),
        'light_boundary':('sepb',(5,5,1,4,4,4),False),
        'superluminal':('sepb',(5,6,1,4,4,4),False),
        'zero_light':('sepb',(0,0,1,4,4,4),False),
        'negative_light':('sepb',(-5,3,*good[2:]),False),
        'three_components':('sepc',(*good[:4],2,3,-4,F(125,8),F(75,4),-25),True),
        'shared_transverse':('sepd',(*good[4:],2,3,-4,F(125,8),F(75,4),-25),True),
        'wrong_third_force':('sepd',(*good[4:],2,3,-4,F(125,8),F(75,4),-24),False),
        'zero_input_underdetermined':('sepd',(123,456,0,0,0,0,0,0),True),
        'zero_input_does_not_fix_coefficients':('sepb',(*good[:4],123,456),False),
    }
    return rows


def numerical_checks(real=False):
    rows={};mapping=dict(zip(('sepa','sepb','sepc','sepd'),('sepe','sepf','sepg','seph')))
    for label,(symbol,args,expected) in numeric_cases().items():
        if real:
            query='q['+k(mapping[symbol],*(k('bb',number(a)) for a in args))+'].'
            doc=abstract(candidate(text(CORE),query),OPS)
            fixture,model=setup(doc);actual=evaluate(doc,model)[0]
        else:
            doc=parse(text(LIBRARY)+'q['+k(symbol,*map(number,args))+'].')
            actual=evaluate_document(doc,individuals=('object',),situations=('text',),primitives=ARITHMETIC)[0]['value']
        assert actual==expected,(label,actual)
        rows[label]=actual
    return rows


def polynomial_checks():
    factors=list(map(v,FACTORS.split()));components=list(map(v,COMPONENTS.split()))
    coeff=k('sepb',*factors);explicit=k('sepc',*factors[:4],*components)
    implicit=k('sepd',*factors[4:],*components)
    mul=lambda a,b:k('ad',a,b)
    beta,mu=factors[2:4];L=mul(mu,mul(mul(beta,beta),beta));T=mul(mu,mul(beta,beta))
    zero,one=number(0),number(1)
    probes=both(k('sepd',*factors[4:],one,zero,zero,L,zero,zero),
        k('sepd',*factors[4:],zero,one,zero,zero,T,zero))
    claims={
        'coefficient_equations_imply_component_equivalence':assertion(FACTORS+' '+COMPONENTS,op('y',coeff,op('z',explicit,implicit))),
        'two_independent_probes_identify_coefficients':assertion(FACTORS,op('y',both(k('sra',*factors[:3]),probes),coeff)),
        'opposite_speed_same_coefficients':assertion(FACTORS,op('z',coeff,k('sepb',factors[0],k('ac',factors[1]),*factors[2:]))),
        'zero_input_alone_identifies_coefficients':assertion(FACTORS,op('y',both(k('sra',*factors[:3]),k('sepd',*factors[4:],*[zero]*6)),coeff)),
    }
    rows={}
    for name,claim in claims.items():
        result=verify_universal(parse(text(LIBRARY)+claim),MEANINGS,timeout_ms=15000)[0]
        assert result['status']==('invalid' if name.startswith('zero_input') else 'valid'),(name,result)
        rows[name]=result
    return rows


def universal_refusals():
    rows={}
    for real in (False,True):
        args=(5,3,F(5,4),4,F(125,16),F(25,4))
        if real:
            doc=abstract(candidate(text(CORE),'q['+k('sepi',*(k('bb',number(a)) for a in args))+'].'),OPS)
            _,model=setup(doc)
        else:
            doc=parse(text(LIBRARY)+'q['+k('sepj',*map(number,args))+'].');model=ARITHMETIC
        try:
            if real:evaluate(doc,model)
            else:evaluate_document(doc,individuals=('object',),situations=('text',),primitives=model)
        except ValueError as exc:
            assert 'domain' in str(exc),str(exc)
            rows['real' if real else 'rational']=str(exc)
        else:raise AssertionError('Universal coefficient identity was sampled')
    return rows


def convention_checks():
    doc=candidate(text(CORE),'q[k sepk[k ri[]]].')
    constants={'zramatter':'matter','zbm':'k','ra':'K','zraevent':'event',
        'zraforceunit':'forceunit','zraaccelerationunit':'accelerationunit','ri':'text'}
    domain=tuple(x for x in constants.values() if x!='text')+('other',)
    rows={}
    for changed in (None,*[n for n in constants if n!='ri'],'no_instantaneous_rest','unknown_convention'):
        model=guarded(doc)
        for name,value in constants.items():model[name]=lambda value=value,name=name:'other' if name==changed else value
        model['va']=lambda frame:frame in ('K','k')
        model['zpa']=lambda *args:changed!='no_instantaneous_rest' and args==('matter','k','event','text')
        if changed!='unknown_convention':
            model['zraconvention']=lambda *args:args==('matter','k','K','event','forceunit','accelerationunit','text')
        try:actual=evaluate_document(doc,individuals=domain,situations=('text',),primitives=model)[0]['value']
        except ValueError:
            if changed!='unknown_convention':raise
            rows[changed]='refused';continue
        assert changed!='unknown_convention' and actual==(changed is None),(changed,actual)
        rows[changed or 'baseline']=actual
    return rows


def attribution_check():
    doc=parse(text(CORE));model=guarded(doc)
    for name,value in {'zramassnode':'node','rd':'author','zramassscope':'scope','ri':'text'}.items():model[name]=lambda value=value:value
    def reported(node,author,premise,conclusion,scope,context):
        return (node,author,scope,context)==('node','author','scope','text') and [
            json.loads(x.syntax)['symbol'] for x in (premise,conclusion)]==['sepl','sepm']
    model['zc']=reported
    result=evaluate_document(doc,individuals=('node','author','scope'),situations=('text',),primitives=model)
    assert result[0]['value'] is True
    return {'quoted_premise':'sepl','quoted_conclusion':'sepm','numeric_or_physical_claim_executed':False}


def source_conclusion_checks():
    doc=abstract(candidate(text(CORE),'q[t[k sepm[]][k ri[]]].'),OPS)
    constants={'zramatter':'matter','zbm':'k','ra':'K','zraevent':'event',
        'zraforceunit':'forceunit','zraaccelerationunit':'accelerationunit','ri':'text'}
    domain=tuple(x for x in constants.values() if x!='text')
    rows={}
    for mode in ('baseline','wrong_coefficient','wrong_force_frame','wrong_acceleration_unit'):
        fixture,model=setup(doc)
        for name,value in constants.items():model[name]=lambda value=value:value
        for name,value in {'tc':5,'zb7':3,'zramu':4,'zralongitudinal':F(125,16),
                           'zratransverse':5 if mode=='wrong_coefficient' else F(25,4)}.items():
            model[name]=lambda value=value:fixture.make(value)
        model['va']=lambda frame:frame in ('K','k')
        model['zpa']=lambda *args:args==('matter','k','event','text')
        model['zraconvention']=lambda *args:args==('matter','K' if mode=='wrong_force_frame' else 'k','K',
            'event','forceunit','forceunit' if mode=='wrong_acceleration_unit' else 'accelerationunit','text')
        actual=evaluate_document(doc,individuals=domain,situations=('text',),primitives={
            d['name']:model[d['name']] for d in doc['declarations'] if d['kind']=='primitive'})[0]['value']
        assert actual==(mode=='baseline'),(mode,actual)
        rows[mode]=actual
    return rows


def source_alignment():
    source=json.loads(text('artifacts/written-units-v1/einstein-1905.json'));rows=[]
    for uid,mid,names in (('u0255',None,['sepa','sepe','sepi']),('u0257','M0420',['sepf']),('u0258','M0421',['sepf'])):
        unit=next(u for u in source['units'] if u['id']=='einstein-1905:'+uid)
        row=dict(unit=unit['id'],unit_sha256=unit['text_sha256'],definitions=names,status='partial')
        if mid:
            math=next(m for m in source['math'] if m['id']==mid)
            assert mid in unit['math_ids']
            row.update(math_id=mid,math_sha256=hashlib.sha256(math['mathml'].encode('utf-8')).hexdigest())
        else:row.update(range=[0,len(unit['text'])],text=unit['text'])
        rows.append(row)
    return {'segments':rows}


def build_report():
    files=build();audits={}
    for p,value in files.items():assert text(p)==value,p
    parent=parse(text(PARENT));doc=parse(text(SOURCE))
    assert doc['statements'][:-1]==parent['statements'] and len(parent['statements'])==175
    for p in (SOURCE,LIBRARY,CORE):
        current=parse(text(p))
        for notation in ('full','compact'):
            rendered=format_graph(current,notation)
            assert parse(rendered)==parse(transcribe(rendered,alphabet='v2'))==current
        basispath=next(q for q,value in files.items() if q.endswith('.json') and json.loads(value)['document']==p)
        audits[p]=audit_basis(current,json.loads(files[basispath]))
        result=subprocess.run([sys.executable,'-X','utf8','-m','noema','parse','-i',str(ROOT/p)],check=True,capture_output=True,encoding='utf-8')
        assert json.loads(result.stdout)==current
    reading=json.loads(text(READING))
    assert hashlib.sha256((ROOT/reading['facsimile_path']).read_bytes()).hexdigest()==reading['facsimile_sha256']
    paths=set(files)|{PARENT,READING,'data/einstein-reconciled-basis-v1.json',
        'scripts/compose_mass_coefficients.py','scripts/check_mass_coefficients.py','tests/test_mass_coefficients.py',
        'docs/mass-coefficients-v1.md','reports/written-units-v1.json',reading['facsimile_path'],
        'artifacts/written-units-v1/einstein-1905.json'}
    paths.update('noema/'+name+'.py' for name in ('grammar','language','discourse','semantics','finite_semantics','polynomial_proofs','rational_proofs','extraction','meaning_basis','script'))
    paths.update('scripts/'+name+'.py' for name in ('check_phi_normalization','check_quantities','check_real_products',
        'check_coordinate_correspondence','check_described_appraisals','check_plane_waveforms','check_rod_setup',
        'check_tau_differential','check_angle_composition','check_transverse_time','check_comoving_labels','compose_limits','compose_origin_clock','compose_situated_criticism'))
    return dict(status='partial_directional_mass_coefficients',document=SOURCE,basis_audits=audits,
        rational_cases=numerical_checks(),rational_embedding_real_cases=numerical_checks(True),
        polynomial_checks=polynomial_checks(),universal_refusals=universal_refusals(),
        convention_checks=convention_checks(),attribution=attribution_check(),source_conclusion=source_conclusion_checks(),
        prior_statements_preserved=175,roundtrips=True,cli_parse=True,alignment=source_alignment(),
        general_real_cut_proof=False,physical_acceleration_constructed=False,
        verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sorted(paths)})


def main():
    cli=argparse.ArgumentParser();cli.add_argument('--verify-only',action='store_true');args=cli.parse_args()
    report=build_report()
    if args.verify_only:assert json.loads(REPORT.read_text(encoding='utf-8'))==report
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:stream.write(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print('Directional coefficients checked; full source meaning remains partial',flush=True)


if __name__=='__main__':main()
