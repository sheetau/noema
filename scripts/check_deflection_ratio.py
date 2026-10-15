"""Check transverse signs, nonzero denominators and common response calibration."""
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
from scripts.compose_deflection_ratio import ROOT,PARENT,SOURCE,LIBRARY,CORE,READING,COMPARE,RESPONSE,RATIO,build
from scripts.compose_limits import call as k,both,op,v
from scripts.check_coordinate_correspondence import abstract
from scripts.check_described_appraisals import candidate
from scripts.check_plane_waveforms import setup,OPS
from scripts.check_rod_setup import guarded
from scripts.check_phi_normalization import number
from scripts.check_quantities import ARITHMETIC
from scripts.check_real_products import MEANINGS,assertion

REPORT=ROOT/'reports/deflection-ratio-v1.json'


@lru_cache(None)
def text(path):return (ROOT/path).read_text(encoding='utf-8')


def evaluate(doc,model):
    return [r['value'] for r in evaluate_document(doc,individuals=('balance','ratio','reason','author','scope'),situations=('actual',),
        primitives={d['name']:model[d['name']] for d in doc['declarations'] if d['kind']=='primitive'},max_steps=2_000_000)]


def cut(x):return k('bb',number(x))


COMPARISONS={
    'balanced':((5,3,F(5,4),2,2,3,5,F(12,5),F(-12,5),0),[True,True]),
    'negative_charge':((5,3,F(5,4),2,-2,3,5,F(-12,5),F(12,5),0),[True,True]),
    'unbalanced':((5,3,F(5,4),2,2,4,5,F(16,5),F(-12,5),F(4,5)),[True,False]),
    'wrong_magnetic_sign':((5,3,F(5,4),2,2,3,5,F(12,5),F(12,5),0),[False,True]),
    'zero_fields':((5,3,F(5,4),2,2,0,0,0,0,0),[True,True]),
    'rest_with_magnetic_field':((5,0,1,2,2,0,5,0,0,0),[True,True]),
    'zero_charge_unbalanced_fields':((5,3,F(5,4),2,0,4,5,0,0,0),[True,False]),
    'comoving_force_coefficient_misused':((5,3,F(5,4),2,2,3,5,F(48,25),F(-48,25),0),[False,True]),
}
RESPONSES={
    'calibrated':((5,3,F(5,4),2,2,2,3,F(12,5),F(36,25)),[True,True]),
    'negative_charge':((5,3,F(5,4),2,-2,2,3,F(12,5),F(36,25)),[True,True]),
    'common_gain_doubled':((5,3,F(5,4),2,2,2,6,F(24,5),F(72,25)),[True,True]),
    'rest':((5,0,1,2,2,2,3,3,0),[True,True]),
    'zero_denominator':((5,3,F(5,4),2,2,2,3,0,0),[False,False]),
    'unequal_calibration':((5,3,F(5,4),2,2,2,3,F(12,5),F(18,25)),[False,False]),
    'zero_charge':((5,3,F(5,4),2,0,0,3,0,0),[False,False]),
    'wrong_magnitude':((5,3,F(5,4),2,-2,-2,3,F(-12,5),F(-36,25)),[False,False]),
    'light_boundary':((5,5,1,2,2,2,3,3,3),[False,False]),
}


def numeric_checks():
    rows={}
    for family,cases,names in [('comparison',COMPARISONS,('setl','setn','setm','seto')),('response',RESPONSES,('setp','setr','setq','sets'))]:
        base=format_graph(extract_document(parse(text(LIBRARY)),roots=list(names[:2]),statement_indices=[]).document,'compact')
        result={}
        for label,(numbers,expected) in cases.items():
            short=(numbers[0],numbers[1],numbers[5],numbers[6]) if family=='comparison' else (numbers[0],numbers[1],numbers[-2],numbers[-1])
            query='q['+k(names[0],*map(number,numbers))+'].q['+k(names[1],*map(number,short))+'].'
            actual=evaluate(parse(base+query),ARITHMETIC)
            for path in (LIBRARY,CORE):
                query='q['+k(names[2],*map(cut,numbers))+'].q['+k(names[3],*map(cut,short))+'].'
                doc=abstract(candidate(text(path),query),OPS);_,model=setup(doc);model.update(ARITHMETIC)
                actual+=evaluate(doc,model)
            assert actual==expected*3,(family,label,actual);result[label]=actual
        rows[family]=result
    # The inverse formula is checked only with a valid nonzero denominator.
    for label,V,Ae,Am,expected in [('moving',5,F(12,5),F(36,25),3),('rest',5,3,0,0),
                                 ('unequal_calibration_misleads',5,F(12,5),F(18,25),F(3,2))]:
        query='q['+k('sets',*map(cut,(V,expected,Ae,Am)))+'].q['+k('sca',k('sett',*map(cut,(V,Ae,Am))),cut(expected))+'].'
        doc=abstract(candidate(text(CORE),query),OPS);_,model=setup(doc);model.update(ARITHMETIC)
        assert evaluate(doc,model)==[True,True],label
    rows['inverse_values']={'moving':'3','rest':'0','unequal_calibration_misleads':'3/2'}
    return rows


def polynomial_checks():
    base=format_graph(extract_document(parse(text(LIBRARY)),roots=['setl','setn','setp','setr'],statement_indices=[]).document,'compact')
    terms=list(map(v,COMPARE.split()));V,s,b,m,q,Y,N,ae,am,total=terms
    eq=lambda a,b:op('e',a,b);mul=lambda a,b:k('ad',a,b);zero=number(0)
    comparison=k('setl',*terms);balance=k('setn',V,s,Y,N);strength=eq(mul(ae,ae),mul(am,am))
    responses=list(map(v,RESPONSE.split()));Ae,Am=responses[-2:];second=v('secondspeed')
    claims={
        'balance_means_opposite_accelerations_and_zero_sum':assertion(COMPARE,op('y',both(comparison,balance),both(eq(ae,k('ac',am)),eq(total,zero)))),
        'nonzero_charge_makes_strength_equivalent_to_balance':assertion(COMPARE,op('y',both(comparison,op('u',eq(q,zero)),op('u',k('aa',Y,zero)),op('u',k('aa',N,zero))),op('z',strength,balance))),
        'common_response_model_implies_ratio':assertion(RESPONSE,op('y',k('setp',*responses),k('setr',V,s,Ae,Am))),
        'ratio_identifies_unique_speed':assertion(RATIO+' secondspeed',op('y',both(k('setr',V,s,Ae,Am),k('setr',V,second,Ae,Am)),eq(s,second))),
        'equal_strength_means_same_signed_acceleration':assertion('',op('y',both(k('setl',*map(number,COMPARISONS['balanced'][0])),k('setn',*map(number,(5,3,3,5)))),eq(number(F(12,5)),number(F(-12,5))))),
        'zero_field_observation_determines_zero_speed':assertion('',op('y',k('setl',*map(number,COMPARISONS['zero_fields'][0])),eq(number(3),zero))),
    };rows={}
    for label,claim in claims.items():
        result=verify_universal(parse(base+claim),MEANINGS,timeout_ms=20000)[0]
        assert result['status']==('invalid' if label.startswith(('equal_strength','zero_field')) else 'valid'),(label,result)
        rows[label]=result
    return rows


def source_checks():
    rows={}
    variants={'baseline':([True,True,True,True],{}),
        'wrong_magnetic_sign':([False,True,True,True],{'zrlmagneticacc':F(12,5)}),
        'unequal_acceleration_strength':([False,False,True,True],{'zrlmagneticacc':F(-6,5)}),
        'unequal_response_gain':([True,True,False,False],{'zrlmagneticresponse':F(18,25)}),
        'zero_response_denominator':([True,True,False,False],{'zrlelectricresponse':0,'zrlmagneticresponse':0}),
        'negative_charge':([True,True,True,True],{'zrgcharge':-2,'zrlelectricacc':F(-12,5),'zrlmagneticacc':F(12,5)}),
    }
    for path in (CORE,SOURCE):
        query=''.join('q[t[k '+n+'[]][k ri[]]].' for n in ('setu','setv','setx','setw'))
        doc=abstract(candidate(text(path),query),OPS);cases={}
        for label,(expected,changes) in variants.items():
            cuts,model=setup(doc);model.update(ARITHMETIC);model['ri']=lambda:'actual'
            numbers=dict(tc=5,zb7=3,zramu=2,zrgcharge=2,zrlelectric=3,zrlmagnetic=5,zrlelectricacc=F(12,5),zrlmagneticacc=F(-12,5),
                         zrltotalacc=0,zrlmagnitude=2,zrlgain=3,zrlelectricresponse=F(12,5),zrlmagneticresponse=F(36,25))
            numbers.update(changes)
            for name,value in numbers.items():model[name]=lambda value=value:cuts.make(value)
            actual=evaluate(doc,model);assert actual==expected,(path,label,actual);cases[label]=actual
        rows[path]=cases
    return dict(cases=rows,instrument_or_measurement_capability_proved=False)


def attribution_check():
    doc=parse(text(CORE));model=guarded(doc);seen=[]
    for name,value in {'zrlbalancenode':'balance','zrlrationode':'ratio','zrlreasonnode':'reason','rd':'author','zrlscope':'scope','ri':'actual'}.items():model[name]=lambda value=value:value
    symbol=lambda x:json.loads(x.syntax)['symbol']
    def claim(node,author,content,scope,context):
        seen.append(['claim',symbol(content)])
        return (node,symbol(content)) in [('balance','setv'),('ratio','setw')] and (author,scope,context)==('author','scope','actual')
    def reason(node,author,premise,conclusion,scope,context):
        seen.append(['reason',symbol(premise),symbol(conclusion)])
        return (node,author,scope,context)==('reason','author','scope','actual') and (symbol(premise),symbol(conclusion))==('setu','setv')
    model.update(uh=claim,zc=reason);assert evaluate(doc,model)==[True]*3
    return dict(quoted_targets=seen,dynamics_or_measurements_executed=False,response_model_attributed_to_author=False)


def alignment():
    work=json.loads(text('artifacts/written-units-v1/einstein-1905.json'));units={u['id']:u for u in work['units']}
    first=units['einstein-1905:u0266'];end=first['text'].index('. Man ersieht')+1
    common=dict(unit=first['id'],unit_sha256=first['text_sha256'],status='partial_transverse_balance_and_response_ratio')
    rows=[dict(common,range=[0,end],text=first['text'][:end],definitions=['setk','setm','seto','setu','setv'])]
    rows += [dict(common,math_id=m,definitions=['setu','setv'] if m in ('M0430','M0431','M0432','M0433') else ['setw']) for m in first['math_ids']]
    unit=units['einstein-1905:u0267'];rows.append(dict(unit=unit['id'],unit_sha256=unit['text_sha256'],math_id='M0436',
        status='partial_response_ratio_with_nonzero_denominator',definitions=['sets','setw']))
    return {'segments':rows}


def source_equation_check():
    work=json.loads(text('artifacts/written-units-v1/einstein-1905.json'))
    reading=json.loads(text(READING));reference=reading['auxiliary_equation']
    item=next(m for m in work['math'] if m['id']==reference['math_id'])
    assert item['sha256']==reference['math_sha256']
    unit=next(u for u in work['units'] if u['id']==reference['unit'])
    assert item['id'] in unit['math_ids']
    row=ET.fromstring(item['mathml']).findall('.//{*}mtr')[1]
    tokens=lambda node:[x.text for x in node.iter() if x.tag.rsplit('}',1)[-1] in ('mi','mn','mo')]
    fractions=[[tokens(list(f)[0]),tokens(list(f)[1])] for f in row.findall('.//{*}mfrac')]
    assert fractions==[[['d','2','y'],['d','t','2']],[['ϵ'],['μ']],[['1'],['β']],[['v'],['V']]]
    assert tokens(row)==['d','2','y','d','t','2','=','ϵ','μ','1','β','(','Y','−','v','V','N',')',',']
    return dict(math_id=item['id'],row=2,fractions=fractions,magnetic_sign='minus',source='electronic_mathml')


def build_report():
    files=build();audits={}
    for path,body in files.items():assert text(path)==body,path
    old=parse(text(PARENT));current=parse(text(SOURCE));assert current['statements'][:-3]==old['statements'] and len(old['statements'])==191
    assert current['declarations'][:len(old['declarations'])]==old['declarations']
    for path in (SOURCE,LIBRARY,CORE):
        doc=parse(text(path));basis=next(json.loads(body) for p,body in files.items() if p.endswith('.json') and json.loads(body)['document']==path)
        audits[path]={k:v for k,v in audit_basis(doc,basis).items() if k!='definition_dependencies'}
        for notation in ('full','compact'):
            rendered=format_graph(doc,notation);assert parse(rendered)==parse(transcribe(rendered,alphabet='v2'))==doc
        cli=subprocess.run([sys.executable,'-X','utf8','-m','noema','parse','-i',str(ROOT/path)],check=True,capture_output=True,encoding='utf-8');assert json.loads(cli.stdout)==doc
    reading=json.loads(text(READING));assert reading['segments']==alignment()['segments']
    assert hashlib.sha256((ROOT/reading['facsimile_path']).read_bytes()).hexdigest()==reading['facsimile_sha256']
    paths=set(files)|{PARENT,READING,reading['facsimile_path'],'data/einstein-material-energy-extension-basis-v1.json',
        'artifacts/written-units-v1/einstein-1905.json','reports/written-units-v1.json',
        'scripts/compose_deflection_ratio.py','scripts/check_deflection_ratio.py','tests/test_deflection_ratio.py','docs/deflection-ratio-v1.md',
        'scripts/compose_convention_comparison.py','scripts/compose_origin_clock.py','scripts/compose_limits.py','scripts/compose_situated_criticism.py',
        'scripts/check_coordinate_correspondence.py','scripts/check_described_appraisals.py','scripts/check_plane_waveforms.py','scripts/check_rod_setup.py',
        'scripts/check_phi_normalization.py','scripts/check_quantities.py','scripts/check_real_products.py','scripts/check_tau_differential.py','scripts/check_angle_composition.py'}
    paths.update('noema/'+n+'.py' for n in ('grammar','language','discourse','semantics','finite_semantics','extraction','meaning_basis','script','polynomial_proofs'))
    return dict(status='partial_transverse_deflection_and_response_ratio',document=SOURCE,basis_audits=audits,
        numeric=numeric_checks(),polynomial=polynomial_checks(),source=source_checks(),attribution=attribution_check(),source_equation=source_equation_check(),
        statements_preserved=191,new_author_attributions=3,roundtrips=True,cli_parse=True,alignment=alignment(),
        physical_deflectability_and_measurement_method_completed=False,verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sorted(paths)})


def main():
    cli=argparse.ArgumentParser();cli.add_argument('--verify-only',action='store_true');options=cli.parse_args();report=build_report()
    if options.verify_only:assert json.loads(REPORT.read_text(encoding='utf-8'))==report
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:stream.write(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print('Transverse signs and calibrated response ratios checked; measurement construction remains open',flush=True)


if __name__=='__main__':main()
