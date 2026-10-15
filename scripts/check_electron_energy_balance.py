"""Verify balance assumptions, quantity ownership and non-executing source claims."""
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
from scripts.compose_electron_energy_balance import ROOT,PARENT,SOURCE,LIBRARY,CORE,READING,CUT,BASE,VALUES,RELATIONS,NAMES,build
from scripts.compose_limits import call as k,both,op,v
from scripts.check_coordinate_correspondence import abstract
from scripts.check_described_appraisals import candidate
from scripts.check_plane_waveforms import setup,OPS
from scripts.check_rod_setup import callbacks,guarded
from scripts.check_phi_normalization import number
from scripts.check_quantities import ARITHMETIC
from scripts.check_real_products import MEANINGS,assertion
from scripts.check_material_acceleration import free,unwrap

REPORT=ROOT/'reports/electron-energy-balance-v1.json'
PEOPLE=('episode','particle','field','frame','start','end','unit','other')
SCENES=('actual','other')


@lru_cache(None)
def text(path):return (ROOT/path).read_text(encoding='utf-8')


def evaluate(doc,model):
    return [r['value'] for r in evaluate_document(doc,individuals=PEOPLE,situations=SCENES,
        primitives={d['name']:model[d['name']] for d in doc['declarations'] if d['kind']=='primitive'},max_steps=2_000_000)]


CASES={'baseline':((5,0,5,0),[True,True,True]),'radiation':((5,0,3,2),[True,False,False]),
    'initial_motion':((5,2,7,0),[True,False,False]),'equal_despite_both_nonzero':((5,2,5,2),[True,False,True]),
    'missing_balance':((5,0,6,0),[False,False,False]),'zero_exchange':((0,0,0,0),[True,True,True]),
    'negative_radiation':((5,0,6,-1),[False,False,False])}


def numeric_checks():
    base=format_graph(extract_document(parse(text(LIBRARY)),roots=['serk'],statement_indices=[]).document,'compact');rows={}
    for label,(numbers,expected) in CASES.items():
        doc=parse(base+'q['+k('serk',*map(number,numbers))+'].');result=evaluate(doc,ARITHMETIC)
        for path in (LIBRARY,CORE):
            queries=''.join('q['+k(name,*(k('bb',number(x)) for x in numbers))+'].' for name in ('serl','serm','sern'))
            doc=abstract(candidate(text(path),queries),OPS);_,model=setup(doc);model.update(ARITHMETIC)
            values=evaluate(doc,model);assert values==expected,(label,path,values);result+=values
        assert result[0]==expected[0];rows[label]=result
    return rows


def polynomial_checks():
    base=format_graph(extract_document(parse(text(LIBRARY)),roots=['serk'],statement_indices=[]).document,'compact')
    withdrawn,initial,final,radiated=map(v,NAMES.split());zero=number(0);eq=lambda a,b:op('e',a,b)
    balance=k('serk',withdrawn,initial,final,radiated)
    claims={
        'zero_initial_and_zero_radiation_imply_equality':assertion(NAMES,op('y',both(balance,eq(initial,zero),eq(radiated,zero)),eq(withdrawn,final))),
        'equality_with_balance_means_initial_equals_radiation':assertion(NAMES,op('y',balance,op('z',eq(withdrawn,final),eq(initial,radiated)))),
        'zero_radiation_alone_implies_equality':assertion(NAMES,op('y',both(balance,eq(radiated,zero)),eq(withdrawn,final))),
        'equality_alone_implies_zero_radiation':assertion(NAMES,op('y',both(balance,eq(withdrawn,final)),eq(radiated,zero))),
    };rows={}
    for label,claim in claims.items():
        result=verify_universal(parse(base+claim),{n:MEANINGS[n] for n in ('aa','ab','ac')},timeout_ms=20000)[0]
        expected='invalid' if label in ('zero_radiation_alone_implies_equality','equality_alone_implies_zero_radiation') else 'valid'
        assert result['status']==expected,(label,result);rows[label]=result
    return rows


def fixture(path,source=False):
    declarations=''.join('r jqx'+n+'[] '+sort+'.' for n,sort in BASE+VALUES+RELATIONS)
    queries=''.join('q[t[k '+name+'[]][k jqxcontext[]]].' for name in ('serq','serr')) if source else 'q['+k('serp',*[k('jqx'+n) for n,_ in BASE+VALUES+RELATIONS])+'].'
    return abstract(candidate(text(path),declarations+queries),OPS)


class BalanceModel:
    def __init__(self,doc,variant='baseline'):
        self.doc=doc;self.cuts,self.model=setup(doc);make=self.cuts.make;self.model.update(ARITHMETIC)
        numbers=CASES.get(variant,CASES['baseline'])[0]
        for (name,_),value in zip(VALUES,numbers):self.model['jqx'+name]=lambda value=value:make(value)
        for name,_ in BASE:self.model['jqx'+name]=lambda name=name:'actual' if name=='context' else name
        def kinetic(p,frame,event,unit,value,context):
            return (p,frame,unit,context)==('particle','other' if variant=='wrong_state_frame' else 'frame','unit','actual') and (
                event,self.cuts.read(value)) in (('start',F(numbers[1])),('end',F(numbers[2])))
        def withdrawal(episode,p,field,frame,start,end,unit,value,context):
            expected=['episode','particle','field','frame','start','end','unit','actual']
            labels=('episode','particle','field','frame','start','end','unit','context')
            for i,label in enumerate(labels):
                if variant=='wrong_withdrawal_'+label:expected[i]='other'
            return [episode,p,field,frame,start,end,unit,context]==expected and self.cuts.read(value)==numbers[0]
        def radiation(episode,p,frame,start,end,unit,value,context):
            return (episode,p,frame,start,end,unit,context)==('episode','particle','frame','start','end',
                'other' if variant=='wrong_radiation_unit' else 'unit','actual') and self.cuts.read(value)==numbers[3]
        def closed(*refs):
            if variant=='unknown_closure':raise ValueError('Energy-transfer scope missing')
            return variant!='other_transfer' and refs==('episode','particle','field','frame','start','end','unit','actual')
        entries=dict(kinetic=kinetic,withdrawal=withdrawal,radiation=radiation,closed=closed)
        callbacks(doc,self.model,{'jqx'+n:fn for n,fn in entries.items()})
        for name in entries:self.model['zrg'+name]=self.model['jqx'+name]
        sources={'zrgepisode':'episode','zramatter':'particle','zrgfield':'field','ra':'frame',
            'zrgstart':'start','zraevent':'end','zrgunit':'unit','zrgwithdrawn':'withdrawn',
            'zrginitial':'initial','zrfenergy':'final','zrgradiated':'radiated'}
        for source,name in sources.items():self.model[source]=self.model['jqx'+name]

    def evaluate(self):return evaluate(self.doc,self.model)


def binding_checks():
    invalid=['wrong_state_frame','wrong_radiation_unit','other_transfer']+['wrong_withdrawal_'+n for n in ('episode','particle','field','frame','start','end','unit','context')]
    rows={}
    for path,source in ((LIBRARY,False),(CORE,True),(SOURCE,True)):
        doc=fixture(path,source);results={}
        for variant in list(CASES)+invalid:
            expected=[False]*2 if variant in invalid else CASES[variant][1][1:]
            if not source:expected=[variant not in invalid]
            actual=BalanceModel(doc,variant).evaluate();assert actual==expected,(path,variant,actual,expected)
            results[variant]=actual
        rows[path]=results
    try:BalanceModel(fixture(CORE,True),'unknown_closure').evaluate()
    except ValueError as exc:assert 'missing' in str(exc)
    else:raise AssertionError('Unknown closed transfer invented')
    return {'cases':rows,'unknown_scope_refused':True}


def work_integral_refusal():
    declarations='r jqxprofile[] h['+CUT+'] '+CUT+'.'
    query='q['+k('sero',*(k('bb',number(x)) for x in (0,2,3,6)),k('jqxprofile'))+'].'
    doc=abstract(candidate(text(CORE),declarations+query),OPS);cuts,model=setup(doc);model.update(ARITHMETIC)
    callbacks(doc,model,{'jqxprofile':lambda position:cuts.make(1)})
    try:evaluate(doc,model)
    except ValueError as exc:
        assert any(word in str(exc).lower() for word in ('domain','enumerat','quantif','function','rational')),str(exc)
    else:raise AssertionError('All integral partitions silently approximated')
    return {'full_integral_evaluation_refused':True,'numerical_quadrature_used_as_proof':False}


def oriented_work_checks():
    """Interpret positive integrals only for registered constant fields.

    This analytical fixture checks sero's bounds, sign and charge bindings.
    It neither samples arbitrary functions nor proves the cut integral law.
    """
    cases={'forward':(0,2,3,1,6,True),'reverse':(2,0,3,1,-6,True),
        'wrong_reverse_sign':(2,0,3,1,6,False),'zero_extent':(2,2,3,1,0,True),
        'nonzero_at_zero_extent':(2,2,3,1,1,False),'negative_charge':(0,2,-3,1,-6,True),
        'negative_field':(0,2,3,-2,-12,True),'zero_charge':(0,2,0,1,0,True)}
    rows={}
    for label,(lower,upper,charge,field,work,expected) in cases.items():
        declarations='r jqxprofile[] h['+CUT+'] '+CUT+'.'
        query='q['+k('sero',*(k('bb',number(x)) for x in (lower,upper,charge,work)),k('jqxprofile'))+'].'
        doc=abstract(candidate(text(CORE),declarations+query),OPS|{'sede'})
        cuts,model=setup(doc);model.update(ARITHMETIC)
        def profile(position):return cuts.make(field)
        callbacks(doc,model,{'jqxprofile':profile})
        def integral(a,b,function,value):
            lo,hi=cuts.read(a),cuts.read(b)
            if not lo<hi:return False
            closure=free(unwrap(function));node=closure.get('node',{});captured=closure.get('captured',{})
            body=node.get('body',{});parameters=node.get('parameters',[]);operands=body.get('arguments',[])
            if body.get('kind')!='call' or body.get('symbol')!='shv' or len(operands)!=2 or len(parameters)!=1:
                raise ValueError('Unregistered work integrand')
            coefficient,application=operands;reference=application.get('function',{})
            if coefficient.get('kind')!='variable' or application.get('kind')!='apply' or reference.get('kind')!='variable' or application.get('arguments')!=[dict(kind='variable',name=parameters[0]['name'])]:
                raise ValueError('Unregistered work integrand')
            if unwrap(captured[reference['name']]).implementation is not profile:raise ValueError('Unregistered field')
            return cuts.read(value)==cuts.read(captured[coefficient['name']])*field*(hi-lo)
        model['sede']=integral
        actual=evaluate(doc,model)[0];assert actual==expected,(label,actual);rows[label]=actual
    return {'registered_constant_field_cases':rows,'arbitrary_functions_sampled':False,'cut_integral_law_proved':False}


def attribution_check():
    doc=parse(text(CORE));model=guarded(doc);seen=[]
    for name,value in {'zrgworknode':'work','zrgclaimnode':'equal','zrgreasonnode':'reason','rd':'author','zrgscope':'scope','ri':'actual'}.items():model[name]=lambda value=value:value
    symbol=lambda value:json.loads(value.syntax)['symbol']
    def claim(node,author,content,scope,context):
        target=symbol(content);seen.append([node,target])
        return (author,scope,context)==('author','scope','actual') and (node,target) in (('work','sert'),('equal','serr'))
    def reason(node,author,premise,conclusion,scope,context):
        pair=[symbol(premise),symbol(conclusion)];seen.append([node,*pair])
        return (node,author,scope,context)==('reason','author','scope','actual') and pair==['serq','serr']
    model.update(uh=claim,zc=reason)
    results=evaluate_document(doc,individuals=('work','equal','reason','author','scope'),situations=('actual',),primitives=model)
    assert [row['value'] for row in results]==[True]*3
    return {'quoted_targets':seen,'physical_assignments_or_integrals_executed':False}


def alignment():
    work=json.loads(text('artifacts/written-units-v1/einstein-1905.json'));unit=next(u for u in work['units'] if u['id']=='einstein-1905:u0261');body=unit['text']
    ranges=[(body.index('die dem elektrostatischen Felde entzogene Energie'),body.index(' hat.')+5),
        (body.index('keine Energie'),body.index('abgeben möge')+len('abgeben möge')),
        (body.index('so muß die'),body.index('gesetzt werden.')+len('gesetzt werden.'))]
    common=dict(unit=unit['id'],unit_sha256=unit['text_sha256'],status='partial_work_and_nonradiating_energy_balance')
    return {'segments':[dict(common,range=[a,b],text=body[a:b],definitions=['sero','serp','serq','serr','sert']) for a,b in ranges]+
        [dict(common,math_id=mid,definitions=names) for mid,names in [('M0425',['sero','sert']),('M0426',['serr'])]]}


def build_report():
    files=build();audits={}
    for p,body in files.items():assert text(p)==body,p
    old=parse(text(PARENT));current=parse(text(SOURCE))
    assert current['statements'][:-3]==old['statements'] and len(old['statements'])==182
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
    paths=set(files)|{PARENT,READING,reading['facsimile_path'],'data/einstein-kinetic-energy-chain-basis-v1.json',
        'artifacts/written-units-v1/einstein-1905.json','reports/written-units-v1.json',
        'scripts/compose_electron_energy_balance.py','scripts/check_electron_energy_balance.py','tests/test_electron_energy_balance.py','docs/electron-energy-balance-v1.md',
        'scripts/compose_convention_comparison.py','scripts/compose_origin_clock.py','scripts/compose_limits.py','scripts/compose_situated_criticism.py',
        'scripts/check_coordinate_correspondence.py','scripts/check_described_appraisals.py','scripts/check_plane_waveforms.py','scripts/check_rod_setup.py',
        'scripts/check_angle_composition.py','scripts/check_tau_differential.py','scripts/check_transverse_time.py',
        'scripts/check_phi_normalization.py','scripts/check_quantities.py','scripts/check_real_products.py','scripts/check_material_acceleration.py'}
    paths.update('noema/'+n+'.py' for n in ('grammar','language','discourse','semantics','finite_semantics','extraction','meaning_basis','script','polynomial_proofs'))
    return dict(status='partial_work_integral_and_nonradiating_energy_balance',document=SOURCE,basis_audits=audits,
        numeric=numeric_checks(),polynomial=polynomial_checks(),bindings=binding_checks(),integrals=work_integral_refusal(),
        oriented_work=oriented_work_checks(),attribution=attribution_check(),
        statements_preserved=182,new_author_attributions=3,roundtrips=True,cli_parse=True,alignment=alignment(),
        slow_acceleration_implies_no_radiation_proved=False,trajectory_and_units_completed=False,integral_substitution_completed=False,
        verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sorted(paths)})


def main():
    cli=argparse.ArgumentParser();cli.add_argument('--verify-only',action='store_true');options=cli.parse_args()
    report=build_report()
    if options.verify_only:assert json.loads(REPORT.read_text(encoding='utf-8'))==report
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:stream.write(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print('Work, balance assumptions and quantity bindings checked; trajectory and physical derivation remain open',flush=True)


if __name__=='__main__':main()
