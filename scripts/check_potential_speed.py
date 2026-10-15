"""Verify signed drops and the scope of their connection to electron energy."""
import argparse
from fractions import Fraction as F
from functools import lru_cache
import hashlib,json,subprocess,sys
from xml.etree import ElementTree as ET
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.finite_semantics import evaluate_document
from noema.meaning_basis import audit_basis
from noema.polynomial_proofs import verify_universal
from noema.script import transcribe
from scripts.compose_potential_speed import ROOT,PARENT,SOURCE,LIBRARY,CORE,READING,CUT,SCALAR,DOMAIN,NUMERIC,build
from scripts.compose_limits import call as k,app,both,op,v
from scripts.check_coordinate_correspondence import abstract
from scripts.check_described_appraisals import candidate
from scripts.check_plane_waveforms import setup,OPS
from scripts.check_rod_setup import callbacks,guarded
from scripts.check_phi_normalization import number
from scripts.check_quantities import ARITHMETIC
from scripts.check_real_products import MEANINGS,assertion
from scripts.check_integral_substitution import PolynomialIntegrals,integral
from scripts.check_material_acceleration import derivative,trim,poly_value

REPORT=ROOT/'reports/potential-speed-v1.json'
PEOPLE=('episode','particle','field','frame','start','end','unit','potentialunit','other')


@lru_cache(None)
def text(path):return (ROOT/path).read_text(encoding='utf-8')


def evaluate(doc,model):
    names={d['name'] for d in doc['declarations'] if d['kind']=='primitive'}
    return [r['value'] for r in evaluate_document(doc,individuals=PEOPLE,situations=('actual','other'),
        primitives={n:model[n] for n in names},max_steps=3_000_000,memoize_definitions=True,memoize_expressions=True)]


def numeric_checks():
    cases={
        'positive_charge':((5,3,F(5,4),2,2,F(25,4)),True),
        'negative_charge':((5,3,F(5,4),2,-2,F(-25,4)),True),
        'wrong_charge_sign':((5,3,F(5,4),2,-2,F(25,4)),False),
        'rest':((5,0,1,2,2,0),True),
        'zero_charge_at_rest':((5,0,1,2,0,0),False),
        'wrong_drop':((5,3,F(5,4),2,2,7),False),
        'negative_speed':((5,-3,F(5,4),2,2,F(25,4)),False),
        'negative_beta':((5,3,F(-5,4),2,2,F(-225,4)),False),
        'zero_mass':((5,3,F(5,4),0,2,0),False),
    };rows={}
    base=format_graph(extract_document(parse(text(LIBRARY)),roots=['seuq'],statement_indices=[]).document,'compact')
    for label,(values,expected) in cases.items():
        results=evaluate(parse(base+'q['+k('seuq',*map(number,values))+'].'),ARITHMETIC)
        for path in (LIBRARY,CORE):
            doc=abstract(candidate(text(path),'q['+k('seur',*(k('bb',number(x)) for x in values))+'].'),OPS)
            _,model=setup(doc);model.update(ARITHMETIC);results+=evaluate(doc,model)
        assert results==[expected]*3,(label,results);rows[label]=results
    return rows


def polynomial_checks():
    base=format_graph(extract_document(parse(text(SOURCE)),roots=['seuq','serk'],statement_indices=[]).document,'compact')
    V,speed,beta,mass,charge,drop=map(v,NUMERIC.split());zero=number(0)
    eq=lambda a,b:op('e',a,b);mul=lambda a,b:k('ad',a,b);add=lambda a,b:k('ab',a,b);sub=lambda a,b:add(a,k('ac',b))
    relation=k('seuq',V,speed,beta,mass,charge,drop)
    W,E,I,R=map(v,('work','energy','initial','radiated'))
    a,b,c,p=map(v,('initial','final','offset','drop'))
    claims={
        'balance_and_work_per_charge_imply_potential_relation':assertion(NUMERIC+' work energy initial radiated',op('y',both(
            k('serk',W,I,E,R),eq(I,zero),eq(R,zero),k('serb',V,speed,beta,mass,E),
            eq(W,mul(charge,drop)),op('u',eq(charge,zero))),relation)),
        'reversing_charge_and_drop_preserves_relation':assertion(NUMERIC,op('z',relation,k('seuq',V,speed,beta,mass,k('ac',charge),k('ac',drop)))),
        'common_potential_offset_preserves_drop':assertion('initial final offset drop',op('z',eq(p,sub(a,b)),eq(p,sub(add(a,c),add(b,c))))),
        'fixed_parameters_determine_one_nonnegative_speed':assertion(NUMERIC+' otherbeta otherspeed',op('y',both(relation,
            k('seuq',V,v('otherspeed'),v('otherbeta'),mass,charge,drop)),eq(speed,v('otherspeed')))),
        'charge_sign_can_be_discarded':assertion('',op('y',k('seuq',*map(number,(5,3,F(5,4),2,-2,F(-25,4)))),
            k('seuq',*map(number,(5,3,F(5,4),2,2,F(-25,4)))))),
    };rows={}
    for label,claim in claims.items():
        result=verify_universal(parse(base+claim),MEANINGS,timeout_ms=20000)[0]
        assert result['status']==('invalid' if label=='charge_sign_can_be_discarded' else 'valid'),(label,result)
        rows[label]=result
    return rows


def integral_checks():
    cases={
        'forward':((F(5,4),),0,5,2,F(25,4),F(25,2),True),
        'reverse':((F(5,4),),5,0,2,F(-25,4),F(-25,2),True),
        'negative_charge':((F(-5,4),),0,5,-2,F(-25,4),F(25,2),True),
        'varying_field':((0,2),0,3,2,9,18,True),
        'wrong_sign':((1,),2,0,2,2,4,False),
        'zero_path':((1,),2,2,2,0,0,True),
        'zero_charge_work':((1,),0,2,0,2,0,True),
    };rows={}
    for label,(profile,lo,hi,charge,drop,work,wanted) in cases.items():
        query='r jpotprofile[] '+SCALAR+'.q['+k('seut',k('bb',number(lo)),k('bb',number(hi)),k('jpotprofile'),
            *(k('bb',number(x)) for x in (drop,charge,work)))+'].'
        doc=abstract(candidate(text(LIBRARY),query),OPS|{'sede'});model=PolynomialIntegrals(doc);model.register('jpotprofile',profile)
        actual=evaluate(doc,model.model);assert actual==[wanted],(label,actual);rows[label]=actual[0]
    return dict(registered_polynomial_cases=rows,all_cut_integral_linearity_proved=False)


def potential_checks():
    # Whole-polynomial derivative identity establishes the analytical model;
    # it does not replace the all-cut definition during ordinary evaluation.
    cases={'baseline':((3,0,-1),3,True,True),'offset':((103,0,-1),3,True,True),
        'wrong_sign':((3,0,1),3,False,False),'outside_domain':((3,0,-1),4,True,False),
        'same_endpoints_wrong_interior':((3,0,2,-1),3,False,False)}
    rows={}
    for name,(potential,hi,identity,wanted) in cases.items():
        declarations='r jpotdomain[] '+DOMAIN+'.r jpotpotential[] '+SCALAR+'.r jpotprofile[] '+SCALAR+'.'
        drop=poly_value(potential,F(0))-poly_value(potential,F(hi))
        args=[k('jpot'+n) for n in ('domain','potential','profile')]+[k('bb',number(x)) for x in (0,hi,drop)]
        query='q['+k('seuw',*args)+'].'
        doc=abstract(candidate(text(LIBRARY),declarations+query),OPS|{'seuv'})
        model=PolynomialIntegrals(doc);model.register('jpotpotential',potential);model.register('jpotprofile',(0,2))
        def domain(x):return 0<=model.cuts.read(x)<=3
        callbacks(doc,model.model,{'jpotdomain':domain})
        def global_potential(d,p,f):
            # Restrict this interpretation to the registered interval.
            from scripts.check_material_acceleration import unwrap
            if unwrap(d).implementation is not domain:raise ValueError('Unregistered domain')
            return derivative(model.polynomial(p))==trim(-x for x in model.polynomial(f))
        model.model['seuv']=global_potential
        actual=evaluate(doc,model.model);assert actual==[wanted],(name,actual)
        algebra=derivative(trim(potential))==trim((0,-2));assert algebra==identity
        rows[name]=dict(all_polynomial_coefficients_match=algebra,endpoint_relation=actual[0],drop=str(drop))
        if name=='same_endpoints_wrong_interior':assert drop==9
    # Do not certify the unrestricted definition by enumerating a finite grid.
    raw=abstract(candidate(text(LIBRARY),declarations+query),OPS)
    guarded_model=PolynomialIntegrals(raw);guarded_model.register('jpotpotential',(3,0,-1));guarded_model.register('jpotprofile',(0,2))
    callbacks(raw,guarded_model.model,{'jpotdomain':lambda x:0<=guarded_model.cuts.read(x)<=3})
    try:evaluate(raw,guarded_model.model)
    except ValueError as exc:assert any(s in str(exc).lower() for s in ('domain','enumerat','quantif','function','rational')),str(exc)
    else:raise AssertionError('All real points silently sampled')
    return dict(cases=rows,all_cut_domain_evaluation_refused=True)


def source_fixture(path):
    return abstract(candidate(text(path),''.join('q[t[k '+n+'[]][k ri[]]].' for n in ('seux','seuy','seuz','seva'))),OPS|{'sede'})


class SourceModel(PolynomialIntegrals):
    def __init__(self,doc,variant):
        super().__init__(doc);make=self.cuts.make;read=self.cuts.read
        charge=F(-2 if variant in ('negative_charge','wrong_charge_sign') else 0 if variant=='zero_charge' else 2)
        speed=F(0 if variant in ('rest','zero_charge') else 3)
        energy=F(0 if speed==0 else F(25,2));drop=energy/charge if charge else F(0)
        if variant=='wrong_charge_sign':drop=-drop
        profile=drop/5
        if variant=='wrong_drop':drop+=1
        withdrawn=energy+(variant=='wrong_balance')
        initial=F(2 if variant=='initial_motion' else 0);radiated=F(2 if variant=='radiation' else 0)
        final=energy+initial-radiated
        for name,val in {'tc':5,'zb7':speed,'zramu':2,'zrgcharge':charge,'zrndrop':drop,'zrgposition':5,
            'zrfenergy':final,'zrgwithdrawn':withdrawn,'zrginitial':initial,'zrgradiated':radiated}.items():self.model[name]=lambda val=val:make(val)
        refs={'zrgepisode':'episode','zramatter':'particle','zrgfield':'field','ra':'frame','zrgstart':'start','zraevent':'end','zrgunit':'unit','zrnunit':'potentialunit','ri':'actual'}
        for name,val in refs.items():self.model[name]=lambda val=val:val
        self.register('zrgprofile',(profile,))
        def assigned(episode,field,frame,start,end,unit,value,context):
            expected=['episode','field','frame','start','end','potentialunit','actual']
            for i,n in enumerate(('episode','field','frame','start','end','unit','context')):
                if variant=='wrong_potential_'+n:expected[i]='other'
            return [episode,field,frame,start,end,unit,context]==expected and read(value)==drop
        def kinetic(p,frame,event,unit,value,context):
            return (p,frame,unit,context)==('particle','frame','other' if variant=='wrong_energy_unit' else 'unit','actual') and (event,read(value)) in [('start',initial),('end',final)]
        def withdrawal(episode,p,field,frame,start,end,unit,value,context):
            return (episode,p,field,frame,start,end,unit,context)==('episode','particle','field','frame','start','end','unit','actual') and read(value)==withdrawn
        def radiation(episode,p,frame,start,end,unit,value,context):
            return (episode,p,frame,start,end,unit,context)==('episode','particle','frame','start','end','unit','actual') and read(value)==radiated
        def closed(*refs):return refs==('episode','particle','field','frame','start','end','unit','actual') and variant!='other_transfer'
        callbacks(doc,self.model,{'zrnassigned':assigned,'zrgkinetic':kinetic,'zrgwithdrawal':withdrawal,'zrgradiation':radiation,'zrgclosed':closed})


def source_checks():
    cases={'baseline':[True]*4,'negative_charge':[True]*4,'rest':[True]*4,
        'wrong_charge_sign':[True,False,False,False],'zero_charge':[True,False,False,False],
        'wrong_drop':[False]*4,**{n:[True,True,True,False] for n in ('initial_motion','radiation','wrong_balance','wrong_energy_unit','other_transfer')},
        **{'wrong_potential_'+n:[False,True,False,False] for n in ('episode','field','frame','start','end','unit','context')}}
    rows={}
    for path in (CORE,SOURCE):
        doc=source_fixture(path);results={}
        for name,wanted in cases.items():
            actual=evaluate(doc,SourceModel(doc,name).model);assert actual==wanted,(path,name,actual,wanted);results[name]=actual
        rows[path]=results
    return dict(cases=rows,source_premises_not_inferred_from_numerical_formula=True)


def attribution_check():
    doc=parse(text(CORE));model=guarded(doc);seen=[]
    for n,value in {'zrnclaimnode':'claim','zrnreasonnode':'reason','rd':'author','zrnscope':'scope','ri':'actual'}.items():model[n]=lambda value=value:value
    symbol=lambda x:json.loads(x.syntax)['symbol']
    def claim(node,author,content,scope,context):
        seen.append(['claim',symbol(content)]);return (node,author,symbol(content),scope,context)==('claim','author','seuz','scope','actual')
    def reason(node,author,premise,conclusion,scope,context):
        seen.append(['reason',symbol(premise),symbol(conclusion)])
        return (node,author,symbol(premise),symbol(conclusion),scope,context)==('reason','author','seva','seuz','scope','actual')
    model.update(uh=claim,zc=reason)
    result=evaluate_document(doc,individuals=('claim','reason','author','scope'),situations=('actual',),primitives=model)
    assert [row['value'] for row in result]==[True]*2
    return dict(quoted_targets=seen,physical_quantities_and_integrals_executed=False)


def alignment():
    w=json.loads(text('artifacts/written-units-v1/einstein-1905.json'));units={u['id']:u for u in w['units']};segments=[]
    for suffix in ('u0269','u0270'):
        unit=units['einstein-1905:'+suffix];base=dict(unit=unit['id'],unit_sha256=unit['text_sha256'],status='partial_signed_potential_drop_and_speed_relation',definitions=['seux','seuy','seuz','seva'])
        if suffix=='u0269':segments.append(dict(base,range=[0,len(unit['text'])],text=unit['text']))
        segments.extend(dict(base,math_id=mid) for mid in unit['math_ids'])
    return dict(segments=segments)


def printed_equation_check():
    w=json.loads(text('artifacts/written-units-v1/einstein-1905.json'));m=next(x for x in w['math'] if x['id']=='M0438');root=ET.fromstring(m['mathml'])
    leaves=[(x.tag.rsplit('}',1)[-1],(x.text or '').strip()) for x in root.iter() if not len(x) and (x.text or '').strip()]
    expected=['P','=','∫','X','d','x','=','μ','ϵ','V','2','{','1','1','−','(','v','V',')','2','−','1','}','.']
    assert [value for _,value in leaves]==expected,leaves
    assert len(list(root.iter('{http://www.w3.org/1998/Math/MathML}msqrt')))==1
    return dict(math_id=m['id'],math_sha256=m['sha256'],leaf_sequence=leaves,printed_integral_bounds_present=False,facsimile_page_921_inspected=True)


def build_report():
    files=build();audits={}
    for p,body in files.items():assert text(p)==body,p
    old=parse(text(PARENT));current=parse(text(SOURCE));assert len(old['statements'])==197 and current['statements'][:-2]==old['statements']
    assert current['declarations'][:len(old['declarations'])]==old['declarations']
    for p in (SOURCE,LIBRARY,CORE):
        doc=parse(text(p));basis=next(json.loads(body) for q,body in files.items() if q.endswith('.json') and json.loads(body)['document']==p)
        audits[p]={k:v for k,v in audit_basis(doc,basis).items() if k!='definition_dependencies'}
        for notation in ('full','compact'):
            output=format_graph(doc,notation);assert parse(output)==parse(transcribe(output,alphabet='v2'))==doc
        result=subprocess.run([sys.executable,'-X','utf8','-m','noema','parse','-i',str(ROOT/p)],check=True,capture_output=True,encoding='utf-8');assert json.loads(result.stdout)==doc
    reading=json.loads(text(READING));assert reading['segments']==alignment()['segments']
    paths=set(files)|{PARENT,READING,'data/einstein-experimental-comparison-basis-v1.json',
        'artifacts/written-units-v1/einstein-1905.json','reports/written-units-v1.json',
        'tests/test_potential_speed.py','docs/potential-speed-v1.md'}
    for page in reading['facsimiles']:
        assert hashlib.sha256((ROOT/page['path']).read_bytes()).hexdigest()==page['sha256'];paths.add(page['path'])
    paths.update('scripts/'+n+'.py' for n in ('compose_potential_speed','check_potential_speed','compose_convention_comparison','compose_origin_clock','compose_limits','compose_situated_criticism','check_coordinate_correspondence','check_described_appraisals','check_plane_waveforms','check_rod_setup','check_phi_normalization','check_quantities','check_real_products','check_integral_substitution','check_material_acceleration','check_tau_differential','check_angle_composition'))
    paths.update('noema/'+n+'.py' for n in ('grammar','language','discourse','semantics','finite_semantics','extraction','meaning_basis','script','polynomial_proofs'))
    return dict(status='partial_signed_potential_drop_and_speed_relation',document=SOURCE,basis_audits=audits,
        numeric=numeric_checks(),polynomial=polynomial_checks(),integrals=integral_checks(),potential=potential_checks(),
        source=source_checks(),attribution=attribution_check(),printed_equation=printed_equation_check(),
        statements_preserved=197,new_author_attributions=2,roundtrips=True,cli_parse=True,alignment=alignment(),
        verified_full_units={'kant-1784':0,'einstein-1905':0},source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sorted(paths)})


def main():
    cli=argparse.ArgumentParser();cli.add_argument('--verify-only',action='store_true');options=cli.parse_args();report=build_report()
    if options.verify_only:assert json.loads(REPORT.read_text(encoding='utf-8'))==report
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as f:f.write(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print('Signed potential drops and their scoped energy connection checked',flush=True)


if __name__=='__main__':main()
