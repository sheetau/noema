"""Check energy algebra while preserving the printed integral's missing mass factor."""
import argparse
from fractions import Fraction as F
from functools import lru_cache
import hashlib,json,subprocess,sys
import xml.etree.ElementTree as ET
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.finite_semantics import evaluate_document
from noema.meaning_basis import audit_basis
from noema.polynomial_proofs import verify_universal
from noema.script import transcribe
from scripts.compose_kinetic_energy_chain import ROOT,PARENT,SOURCE,LIBRARY,CORE,READING,build
from scripts.compose_limits import call as k,both,op,v
from scripts.check_coordinate_correspondence import abstract
from scripts.check_described_appraisals import candidate
from scripts.check_plane_waveforms import setup,OPS
from scripts.check_rod_setup import guarded
from scripts.check_phi_normalization import number
from scripts.check_quantities import ARITHMETIC
from scripts.check_real_products import MEANINGS,assertion

REPORT=ROOT/'reports/kinetic-energy-chain-v1.json'


@lru_cache(None)
def text(path):return (ROOT/path).read_text(encoding='utf-8')


def evaluate(doc,model):
    return [r['value'] for r in evaluate_document(doc,individuals=('object',),situations=('actual',),
        primitives={d['name']:model[d['name']] for d in doc['declarations'] if d['kind']=='primitive'},max_steps=2_000_000)]


def numeric_checks():
    base=format_graph(extract_document(parse(text(LIBRARY)),roots=['serb'],statement_indices=[]).document,'compact')
    cases={'moving':((5,3,F(5,4),2,F(25,2)),True),'at_rest':((5,0,1,2,0),True),
        'unit_mass':((5,3,F(5,4),1,F(25,4)),True),'negative_speed':((5,-3,F(5,4),2,F(25,2)),False),
        'light_boundary':((5,5,1,2,0),False),'negative_beta':((5,3,F(-5,4),2,F(-225,2)),False),
        'zero_mass':((5,3,F(5,4),0,0),False),'rest_energy_included':((5,3,F(5,4),2,F(125,2)),False),
        'mass_factor_omitted':((5,3,F(5,4),2,F(25,4)),False)}
    rows={}
    for name,(values,expected) in cases.items():
        doc=parse(base+'q['+k('serb',*map(number,values))+'].');result=evaluate(doc,ARITHMETIC)
        for path in (LIBRARY,CORE):
            doc=abstract(candidate(text(path),'q['+k('serc',*(k('bb',number(x)) for x in values))+'].'),OPS)
            _,model=setup(doc);model.update(ARITHMETIC);result+=evaluate(doc,model)
        assert result==[expected]*3,(name,result)
        rows[name]=result
    return rows


def integrand_checks():
    # Equality of cuts uses their values, not equality of function objects.
    query='q['+k('sca',k('serd',k('bb',number(5)),k('bb',number(3))),k('bb',number(F(375,64))))+'].'
    query+='q['+k('sca',k('sere',k('bb',number(5)),k('bb',number(2)),k('bb',number(3))),k('bb',number(F(375,32))))+'].'
    for path in (LIBRARY,CORE):
        doc=abstract(candidate(text(path),query),OPS);_,model=setup(doc);model.update(ARITHMETIC)
        assert evaluate(doc,model)==[True,True]
    doc=abstract(candidate(text(CORE),'q['+k('serf',*(k('bb',number(x)) for x in (5,2,3,F(25,2))))+'].'),OPS)
    _,model=setup(doc);model.update(ARITHMETIC)
    try:evaluate(doc,model)
    except ValueError as exc:
        message=str(exc);assert any(word in message.lower() for word in ('domain','enumerat','quantif','function','rational')),message
    else:raise AssertionError('Full integration silently approximated')
    return {'normalized_integrand':'375/64','mass_weighted_integrand':'375/32','full_integral_evaluation_refused':True}


def polynomial_checks():
    base=format_graph(extract_document(parse(text(LIBRARY)),roots=['serb'],statement_indices=[]).document,'compact')
    V,s,b,m,E,J,d=map(v,('light','speed','beta','mass','energy','normalized','derivative'))
    mul=lambda a,b:k('ad',a,b);sub=lambda a,b:k('ab',a,k('ac',b));eq=lambda a,b:op('e',a,b)
    sq=lambda a:mul(a,a);zero=number(0);one=number(1)
    relation=k('serb',V,s,b,m,E);normal=k('serb',V,s,b,one,J)
    differentiated=eq(mul(mul(b,d),sub(sq(V),sq(s))),mul(s,sq(b)))
    claims={
        'energy_scales_with_mass':assertion('light speed beta mass energy normalized',op('y',both(relation,normal),eq(E,mul(m,J)))),
        'zero_speed_has_zero_kinetic_energy':assertion('light speed beta mass energy',op('y',both(relation,eq(s,zero)),eq(E,zero))),
        'nonzero_speed_and_nonunit_mass_differ_from_normalized_value':assertion('light speed beta mass energy normalized',op('y',
            both(relation,normal,k('aa',zero,s),op('u',eq(m,one))),op('u',eq(E,J)))),
        'differentiated_normalization_gives_weighted_integrand':assertion('light speed beta mass energy derivative',op('y',
            both(relation,differentiated),eq(mul(m,mul(sq(V),d)),mul(m,mul(mul(sq(b),b),s))))),
    };rows={}
    for name,claim in claims.items():
        result=verify_universal(parse(base+claim),MEANINGS,timeout_ms=20000)[0]
        assert result['status']=='valid',(name,result)
        rows[name]=result
    return {'claims':rows,'normalization_derivative_assumed':True,'fundamental_theorem_of_calculus_proved':False,
        'conditional_values':{'light':5,'speed':3,'beta':'5/4','mass':2,'normalized_antiderivative_difference':'25/4','weighted_antiderivative_difference':'25/2'}}


def printed_structure():
    work=json.loads(text('artifacts/written-units-v1/einstein-1905.json'))
    math=next(m for m in work['math'] if m['id']=='M0427')
    tokens=[e.text for e in ET.fromstring(math['mathml']).iter() if e.tag.rsplit('}',1)[-1] in ('mi','mo','mn')]
    equalities=[i for i,t in enumerate(tokens) if t=='='];middle=tokens[equalities[1]+1:equalities[2]]
    assert 'μ' not in middle and 'β' in middle and 'v' in middle
    doc=parse(text(CORE));defs={d['name']:d for d in doc['declarations']}
    def integral_call(node):
        if isinstance(node,dict):
            if node.get('kind')=='call' and node.get('symbol')=='serf':return node
            for value in node.values():
                result=integral_call(value)
                if result:return result
        if isinstance(node,list):
            for value in node:
                result=integral_call(value)
                if result:return result
    printed=integral_call(defs['serg']['body'])['arguments'][1]
    corrected=integral_call(defs['serh']['body'])['arguments'][1]
    assert printed=={'kind':'call','symbol':'bb','arguments':[{'kind':'number','numerator':1,'denominator':1}]}
    assert corrected=={'kind':'variable','name':defs['serh']['parameters'][1]['name']}
    return {'source_middle_tokens':middle,'printed_mass_factor':False,'candidate_mass_factor':True,'source_silently_corrected':False}


def attribution_check():
    doc=parse(text(CORE));model=guarded(doc)
    for name,value in {'zrfnode':'node','rd':'author','zrfscope':'scope','ri':'actual'}.items():model[name]=lambda value=value:value
    model['uh']=lambda n,a,c,s,t:(n,a,s,t)==('node','author','scope','actual') and json.loads(c.syntax)['symbol']=='seri'
    assert evaluate_document(doc,individuals=('node','author','scope'),situations=('actual',),primitives=model)[0]['value'] is True
    return {'author_content':'seri','corrected_content_attributed_to_author':False,'integrals_executed':False}


def alignment():
    work=json.loads(text('artifacts/written-units-v1/einstein-1905.json'));unit=next(u for u in work['units'] if u['id']=='einstein-1905:u0262')
    return {'segments':[dict(unit=unit['id'],unit_sha256=unit['text_sha256'],math_id='M0427',
        status='partial_printed_middle_integral_and_final_value',definitions=['serg','seri'])]}


def build_report():
    files=build();audits={}
    for p,body in files.items():assert text(p)==body,p
    old=parse(text(PARENT));current=parse(text(SOURCE))
    assert current['statements'][:-1]==old['statements'] and len(old['statements'])==181
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
    paths=set(files)|{PARENT,READING,reading['facsimile_path'],'data/einstein-material-mass-extension-basis-v1.json',
        'artifacts/written-units-v1/einstein-1905.json','reports/written-units-v1.json',
        'scripts/compose_kinetic_energy_chain.py','scripts/check_kinetic_energy_chain.py','tests/test_kinetic_energy_chain.py','docs/kinetic-energy-chain-v1.md',
        'scripts/compose_convention_comparison.py','scripts/compose_origin_clock.py','scripts/compose_limits.py','scripts/compose_situated_criticism.py',
        'scripts/check_coordinate_correspondence.py','scripts/check_described_appraisals.py','scripts/check_plane_waveforms.py','scripts/check_rod_setup.py',
        'scripts/check_angle_composition.py','scripts/check_tau_differential.py','scripts/check_transverse_time.py',
        'scripts/check_phi_normalization.py','scripts/check_quantities.py','scripts/check_real_products.py'}
    paths.update('noema/'+n+'.py' for n in ('grammar','language','discourse','semantics','finite_semantics','extraction','meaning_basis','script','polynomial_proofs'))
    return dict(status='partial_printed_kinetic_energy_chain_with_separate_candidate',document=SOURCE,basis_audits=audits,
        numeric=numeric_checks(),integrands=integrand_checks(),polynomial=polynomial_checks(),printed_structure=printed_structure(),attribution=attribution_check(),
        statements_preserved=181,new_author_attributions=1,roundtrips=True,cli_parse=True,alignment=alignment(),
        work_integral_connected=False,physical_energy_assignment_completed=False,full_integral_proved=False,
        verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sorted(paths)})


def main():
    cli=argparse.ArgumentParser();cli.add_argument('--verify-only',action='store_true');options=cli.parse_args()
    report=build_report()
    if options.verify_only:assert json.loads(REPORT.read_text(encoding='utf-8'))==report
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:stream.write(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print('Printed and mass-weighted energy expressions checked separately; integration and physical connection remain open',flush=True)


if __name__=='__main__':main()
