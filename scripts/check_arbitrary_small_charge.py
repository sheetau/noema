"""Check small additions without treating finite trials as arbitrary smallness."""
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
from scripts.compose_arbitrary_small_charge import ROOT,PARENT,SOURCE,LIBRARY,CORE,READING,FIELDS,SYMBOLS,build
from scripts.compose_limits import call as k,op,both,v
from scripts.check_coordinate_correspondence import abstract
from scripts.check_described_appraisals import candidate
from scripts.check_plane_waveforms import setup,OPS
from scripts.check_rod_setup import callbacks,guarded
from scripts.check_phi_normalization import number
from scripts.check_quantities import ARITHMETIC
from scripts.check_real_products import MEANINGS,assertion

REPORT=ROOT/'reports/arbitrary-small-charge-v1.json'
PEOPLE=('point','other','unit','otherunit','operation','otheroperation')
SCENES=('actual','possible','unrelated')


@lru_cache(None)
def text(path):return (ROOT/path).read_text(encoding='utf-8')


def fixture(path,bound=1,universal=False):
    declarations=''.join('r jqv'+n+'[] '+sort+'.' for n,sort in FIELDS)
    declarations+='r jqvpoint[] a.r jqvunit[] a.r jqvcontext[] d.'
    arguments=[k('jqvpoint'),k('jqvunit'),k('jqvcontext')]
    if not universal:arguments+=[number(bound)]
    arguments+=[k('jqv'+n) for n,_ in FIELDS]
    return abstract(candidate(text(path),declarations+'q['+k('seqv' if universal else 'sequ',*arguments)+'].'),OPS)


class ChargeModel:
    def __init__(self,doc,variant='baseline',amount=F(1,2)):
        self.doc=doc;self.cuts,self.model=setup(doc);make=self.cuts.make
        self.model.update(ARITHMETIC);self.calls=[]
        amount=F(amount)
        if variant=='negative':amount=-abs(amount)
        if variant=='zero':amount=F(0)
        before=F(1) if variant in ('already_charged','replacement') else -amount if variant=='cancellation' else F(0)
        after=amount if variant=='replacement' else before+amount
        def pointlike(point,scene):
            return point=='point' and not (variant=='not_initial_point' and scene=='actual') and not (variant=='not_final_point' and scene=='possible')
        def charge(point,unit,scene):
            if variant=='unknown_charge':raise ValueError('Charge assignment missing')
            return make(before if scene=='actual' else after if scene=='possible' else 0)
        def possible(operation,point,base,scene):
            self.calls.append((operation,point,base,scene))
            wanted=('otheroperation' if variant=='wrong_operation' else 'operation',
                'other' if variant=='wrong_point' else 'point',
                'unrelated' if variant=='wrong_base' else 'actual','possible')
            return variant!='impossible' and (operation,point,base,scene)==wanted
        def added(operation,point,unit,quantity,base,scene):
            wanted=('operation','point','otherunit' if variant=='wrong_unit' else 'unit',
                'actual','unrelated' if variant=='wrong_outcome' else 'possible')
            return variant!='no_addition' and (operation,point,unit,base,scene)==wanted and self.cuts.read(quantity)==amount
        entries={'pointlike':pointlike,'charge':charge,'amount':lambda *a:make(amount),'possible':possible,'added':added}
        callbacks(doc,self.model,{'jqv'+n:fn for n,fn in entries.items()})
        for n in entries:self.model[SYMBOLS[n]]=self.model['jqv'+n]
        self.model.update(jqvpoint=lambda:'point',jqvunit=lambda:'unit',jqvcontext=lambda:'actual')

    def evaluate(self):
        return evaluate_document(self.doc,individuals=PEOPLE,situations=SCENES,
            primitives={d['name']:self.model[d['name']] for d in self.doc['declarations'] if d['kind']=='primitive'},
            max_steps=2_000_000)[0]['value']


def capability_checks():
    variants={'baseline':True,'negative':True,'already_charged':True,'zero':False,
        'cancellation':False,'replacement':False,'not_initial_point':False,'not_final_point':False,
        'wrong_operation':False,'wrong_point':False,'wrong_base':False,'wrong_unit':False,
        'wrong_outcome':False,'impossible':False,'no_addition':False}
    rows={}
    for path in (LIBRARY,CORE,SOURCE):
        doc=fixture(path);results={}
        for variant,expected in variants.items():
            model=ChargeModel(doc,variant);value=model.evaluate()
            assert value==expected,(path,variant,value)
            results[variant]=value
        rows[path]=results
    return {'cases':rows,'possible_result_not_asserted_actual':True,'same_object_unit_operation_and_scenes_required':True}


def bound_checks():
    rows={}
    for bound in (F(1),F(1,10),F(1,1000),F(1,10**12)):
        doc=fixture(LIBRARY,bound)
        results={name:ChargeModel(doc,amount=value).evaluate() for name,value in {
            'half_bound':bound/2,'equal_bound':bound,'fixed_half':F(1,2),'zero':F(0)}.items()}
        assert results=={'half_bound':True,'equal_bound':False,'fixed_half':F(1,2)<bound,'zero':False}
        rows[str(bound)]=results
    for bound in (0,-1):assert ChargeModel(fixture(LIBRARY,bound)).evaluate() is False
    for path in (LIBRARY,CORE,SOURCE):
        try:ChargeModel(fixture(path,universal=True)).evaluate()
        except ValueError as exc:
            assert 'rational' in str(exc).lower() or 'number' in str(exc).lower(),str(exc)
        else:raise AssertionError('All rational bounds silently approximated')
    try:ChargeModel(fixture(LIBRARY),'unknown_charge').evaluate()
    except ValueError as exc:assert 'missing' in str(exc)
    else:raise AssertionError('Unknown charge invented')
    return {'finite_bound_instances':rows,'all_bounds_proved_by_finite_evaluation':False,
        'infinite_domain_refused':True,'unknown_charge_refused':True}


def polynomial_checks():
    # Multiplication is needed by the witness and unit-change claims, although
    # the smallness relation itself only uses order and negation.
    source=parse(text(SOURCE))
    base=format_graph(extract_document(source,roots=['seqx','ad'],statement_indices=[]).document,'compact')
    eps,q,scale=map(v,('epsilon','quantity','scale'));positive=lambda x:k('aa',number(0),x)
    mul=lambda a,b:k('ad',a,b);half=mul(eps,number(F(1,2)))
    claims={
        'half_of_any_positive_bound_is_a_witness':assertion('epsilon',op('y',positive(eps),k('seqx',half,eps))),
        'negative_half_is_also_a_witness':assertion('epsilon',op('y',positive(eps),k('seqx',k('ac',half),eps))),
        'positive_fixed_charge_fails_at_its_own_bound':assertion('quantity',op('y',positive(q),op('u',k('seqx',q,q)))),
        'negative_fixed_charge_fails_at_its_magnitude':assertion('quantity',op('y',k('aa',q,number(0)),op('u',k('seqx',q,k('ac',q))))),
        'positive_unit_rescaling_preserves_the_relation':assertion('epsilon quantity scale',op('y',positive(scale),
            op('z',k('seqx',q,eps),k('seqx',mul(q,scale),mul(eps,scale))))),
    };rows={}
    for name,claim in claims.items():
        result=verify_universal(parse(base+claim),{n:MEANINGS[n] for n in ('aa','ac','ad')},timeout_ms=20000)[0]
        assert result['status']=='valid',(name,result)
        rows[name]=result
    return {'claims':rows,'quantity_witnesses_only':True,'physical_operations_or_possible_outcomes_proved':False}


def source_binding_checks():
    """Instantiate exactly one rational bound; retain the outer object scope."""
    rows={}
    for path in (CORE,SOURCE):
        doc=fixture(path)
        definition=next(d for d in doc['declarations'] if d['name']=='seqv')
        universal=definition['body']
        assert universal['kind']=='forall' and universal['sort']=='number'
        variable=universal['variable']
        def replace(node):
            if isinstance(node,list):return [replace(x) for x in node]
            if not isinstance(node,dict):return node
            if node=={'kind':'variable','name':variable}:return {'kind':'number','numerator':1,'denominator':1}
            return {key:replace(value) for key,value in node.items()}
        definition['body']=replace(universal['body'])
        doc=candidate(format_graph(doc,'compact'),'q[t[k seqw[]][k jqvcontext[]]].')
        results={}
        for variant,expected in {'baseline':True,'second_selected_point':False,'no_points':True,'wrong_source_unit':False}.items():
            model=ChargeModel(doc)
            model.model['zqk']=lambda variant=variant:'otherunit' if variant=='wrong_source_unit' else 'unit'
            model.model['zrdmaterial']=lambda point,scene,variant=variant:scene=='actual' and point in (
                () if variant=='no_points' else ('point','other') if variant=='second_selected_point' else ('point',))
            results[variant]=model.evaluate()
            assert results[variant]==expected,(path,variant,results[variant])
        rows[path]=results
    return {'one_bound_source_instances':rows,'all_bounds_claim_verified':False,'existence_of_material_points_inferred':False}


def attribution_check():
    doc=parse(text(CORE));model=guarded(doc)
    for name,value in {'zrdnode':'node','rd':'author','zrdscope':'scope','ri':'actual'}.items():model[name]=lambda value=value:value
    def reports(node,author,content,scope,context):
        return (node,author,scope,context)==('node','author','scope','actual') and json.loads(content.syntax)['symbol']=='seqw'
    model['uh']=reports
    assert evaluate_document(doc,individuals=('node','author','scope'),situations=('actual',),primitives=model)[0]['value'] is True
    return {'content':'seqw','physical_capability_executed_or_proved':False}


def alignment():
    source=json.loads(text('artifacts/written-units-v1/einstein-1905.json'))
    unit=next(u for u in source['units'] if u['id']=='einstein-1905:u0260');body=unit['text'];start=body.index('ein ponderabler')
    return {'segments':[dict(unit=unit['id'],unit_sha256=unit['text_sha256'],range=[start,len(body)],text=body[start:],
        status='partial_arbitrary_small_charge_capability',definitions=['seqr','seqs','seqt','sequ','seqv','seqw'])]}


def build_report():
    files=build();audits={}
    for p,body in files.items():assert text(p)==body,p
    old=parse(text(PARENT));current=parse(text(SOURCE))
    assert current['statements'][:-1]==old['statements'] and len(old['statements'])==178
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
    paths=set(files)|{PARENT,READING,reading['facsimile_path'],'data/einstein-theory-comparison-caution-basis-v1.json',
        'artifacts/written-units-v1/einstein-1905.json','reports/written-units-v1.json',
        'scripts/compose_arbitrary_small_charge.py','scripts/check_arbitrary_small_charge.py','tests/test_arbitrary_small_charge.py','docs/arbitrary-small-charge-v1.md',
        'scripts/compose_convention_comparison.py','scripts/compose_origin_clock.py','scripts/compose_limits.py','scripts/compose_situated_criticism.py',
        'scripts/check_coordinate_correspondence.py','scripts/check_described_appraisals.py','scripts/check_plane_waveforms.py','scripts/check_rod_setup.py',
        'scripts/check_angle_composition.py','scripts/check_tau_differential.py','scripts/check_transverse_time.py',
        'scripts/check_phi_normalization.py','scripts/check_quantities.py','scripts/check_real_products.py'}
    paths.update('noema/'+n+'.py' for n in ('grammar','language','discourse','semantics','finite_semantics','extraction','meaning_basis','script','polynomial_proofs'))
    return dict(status='partial_arbitrary_small_addition_and_possible_outcome',document=SOURCE,basis_audits=audits,
        capabilities=capability_checks(),bounds=bound_checks(),polynomial=polynomial_checks(),
        source_binding=source_binding_checks(),attribution=attribution_check(),
        statements_preserved=178,new_author_attributions=1,roundtrips=True,cli_parse=True,alignment=alignment(),
        mass_result_extension_completed=False,physical_operation_semantics_completed=False,
        verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sorted(paths)})


def main():
    cli=argparse.ArgumentParser();cli.add_argument('--verify-only',action='store_true');options=cli.parse_args()
    report=build_report()
    if options.verify_only:assert json.loads(REPORT.read_text(encoding='utf-8'))==report
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:stream.write(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print('Arbitrary-small quantity witnesses, bounded capabilities and attribution checked; physical generality remains open',flush=True)


if __name__=='__main__':main()
