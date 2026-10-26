"""Source-preserving arithmetic, visible decoding and explicit binding diagnostics."""
from copy import deepcopy
from functools import lru_cache
from fractions import Fraction
import json
import z3

from noema.constructed import parse,format_graph
from noema.grammar import parse as old_parse
from noema.meaning_catalog import load_catalog,_references
from noema.polynomial_proofs import verify_universal
from noema.constructed_semantics import evaluate_document,FunctionValue
from scripts.shared_cut_products import *
from scripts.visible_products_vocabulary import ProductsVocabulary,MANIFEST
from scripts.visible_products_collection import compile_collection,decode_collection
from scripts.visible_word_forms import Word
from scripts.visible_syntax_geometry import to_svg,from_svg
from scripts.check_shared_real_cuts import proof_view,num,apply,rational,INTERPRETATIONS
from scripts.check_real_products import claims as old_claims
from scripts.shared_reference import lam
from scripts.shared_time import q

OUT=ROOT/'output/visible-cut-products-v1'
EXAMPLE='examples/v016/visible-cut-products-v1.noema'
LABEL=Word('proper',('round','red','give','book'))


@lru_cache(maxsize=1)
def vocabulary():return ProductsVocabulary()


@lru_cache(maxsize=1)
def claims():
    old=(ROOT/'examples/v011/real-products.noema').read_text(encoding='utf-8');lemmas,_=old_claims()
    selected=['sqrt_of_nonnegative_rational_square','positive_product_witness_is_below_product',
        'positive_product_given_gap_certifies_witness','positive_reciprocal_witness_is_below_inverse',
        'sqrt_gap_formula_certifies_larger_member']
    mapping=previous.MAPPING|{'cj':'cutsqrtcandidate'};result={}
    for name in selected:result[name]=(renamed(old_parse(old+lemmas[name])['statements'][-1],mapping),True)
    point=v('point');value=v('value')
    def member(x):return apply(call('cutsqrtcandidate',rational(x)),point)
    def below(x):return call('rationalbelow',point,x)
    for name,n in [('zero',0),('negative',-1)]:
        result[name+'_input_candidate_is_zero']=(dict(kind='assert',body=q('forall','point','number',op('iff',member(num(n)),below(num(0))))),True)
    unguarded=op('iff',member(call('rationalmultiply',value,value)),below(value))
    result['square_root_without_sign_condition']=(dict(kind='assert',body=q('forall','value','number',q('forall','point','number',unguarded))),False)
    closed=op('or',below(num(2)),op('equal',point,num(2)))
    for name,right in [('closed_square_root_boundary',closed),('negative_square_root_branch',below(num(-2)))]:
        result[name]=(dict(kind='assert',body=q('forall','point','number',op('iff',member(num(4)),right))),False)
    return result


@lru_cache(maxsize=1)
def example():
    doc=deepcopy(composed());doc['statements']=[s for s,expected in claims().values()]
    return normalize_document(doc)


@lru_cache(maxsize=1)
def compiled():return compile_collection(vocabulary().encode(example()),LABEL,vocabulary(),payload=768)


def saved_pages():return [from_svg(p.read_text(encoding='utf-8')) for p in sorted(OUT.glob('page-*.svg'))]


@lru_cache(maxsize=1)
def restored():
    result=decode_collection(saved_pages(),vocabulary(),public_names=True)
    require(result['document']==example(),'Visible cut arithmetic differs')
    return result


@lru_cache(maxsize=1)
def proofs():
    rows=[];base=restored()['document']
    for (name,(_,valid)),statement in zip(claims().items(),base['statements'],strict=True):
        doc=deepcopy(base);doc['statements']=[statement]
        result=verify_universal(proof_view(doc),INTERPRETATIONS)[0]
        require(result['status']==('valid' if valid else 'invalid'),'Unexpected polynomial result: '+name)
        rows.append(dict(name=name,expected_valid=valid,**result))
    return rows


def diagnostic_case(target,arguments,*,invalid=(),nonnegative=True,operands=None):
    """Preserve the target body; replace direct callees by typed test doubles.

    Tags are rational predicates with a single member, NOT Dedekind cuts.
    Only the wrapper's argument plumbing and guard logic are under test.
    """
    declarations={d['name']:d for d in restored()['document']['declarations']}
    body=declarations[target];refs=_references(body)-{target}
    stubs=[]
    for name in sorted(refs):
        d=declarations[name]
        stubs.append(dict(kind='primitive',name=name,parameters=[p['sort'] for p in d['parameters']],result=d['result']))
    def tag(f):
        matches=[i for i in range(6) if f(Fraction(i))]
        require(len(matches)==1,'Diagnostic predicate lacks a unique tag')
        return matches[0]
    def token(i):return FunctionValue(('number',),'truth',lambda x:x==i)
    expected=tuple(operands if operands is not None else arguments[:-1])
    def candidate(*args):return token(3 if tuple(tag(f) for f in args)==expected else 5)
    handlers=dict(cutvalid=lambda f:tag(f) not in invalid,cutvalueequal=lambda a,b:tag(a)==tag(b),
        rationalcut=lambda n:token(0) if n==0 else token(5),cutnonnegative=lambda f:nonnegative and tag(f)==expected[0],
        cutproduct=candidate,cutreciprocal=candidate,cutquotient=candidate,cutsqrtcandidate=candidate)
    if target=='cutquotient':
        handlers['cutreciprocal']=lambda f:token(4 if tag(f)==2 else 5)
        handlers['cutproduct']=lambda a,b:token(3 if (tag(a),tag(b))==(1,4) else 5)
    args=[lam([('point','number')],op('equal',v('point'),num(i))) for i in arguments]
    expression=call(target,*args)
    if body['result']==CUT:expression=apply(expression,num(3))
    doc=dict(schema_version='0.16',lexicon_version='0.16',declarations=stubs+[deepcopy(body)],
             statements=[dict(kind='ask',body=expression)])
    return evaluate_document(doc,individuals=('a','b'),situations=('now',),primitives={n:handlers[n] for n in refs})[0]['value']


@lru_cache(maxsize=1)
def diagnostics():
    rows=[]
    def check(name,target,args,expected,**options):
        value=diagnostic_case(target,args,**options)
        require(value==expected,'Binding diagnostic failed: '+name)
        rows.append(dict(name=name,target=target,arguments=args,options=options,expected=expected,value=value))
    for target,args in [('cutproductrelation',[1,2,3]),('cutreciprocalrelation',[1,3]),
                        ('cutquotientrelation',[1,2,3]),('cutsqrtrelation',[1,3])]:
        check(target+'_matching_result',target,args,True)
        for slot,tag in enumerate(args):check(target+'_invalid_slot_'+str(slot),target,args,False,invalid=(tag,))
        check(target+'_wrong_result',target,args[:-1]+[4],False)
        if len(args)==3:check(target+'_reversed_operands',target,[2,1,3],False,operands=(1,2))
        else:check(target+'_input_result_swapped',target,[3,1],False,operands=(1,))
    check('zero_inverse_rejected','cutreciprocalrelation',[0,3],False)
    check('zero_denominator_rejected','cutquotientrelation',[1,0,3],False)
    check('zero_numerator_allowed','cutquotientrelation',[0,2,3],True)
    check('negative_sqrt_input_rejected','cutsqrtrelation',[1,3],False,nonnegative=False)
    check('quotient_composes_denominator_reciprocal','cutquotient',[1,2],True)
    check('quotient_reversed_inputs_differ','cutquotient',[2,1],False)
    return rows


def prepare():
    from scripts.shared_cut_products import prepare as prepare_library
    prepare_library();write_new(EXAMPLE,format_graph(example())+'\n');OUT.mkdir(parents=True,exist_ok=True)
    for i,page in enumerate(compiled()['pages']):
        write_new((OUT/('page-'+str(i+1).zfill(5)+'.svg')).relative_to(ROOT).as_posix(),to_svg(page['shapes']))


def build_report():
    require(parse((ROOT/LIBRARY).read_text(encoding='utf-8'))==composed(),'Library differs')
    require(json.loads((ROOT/BASIS).read_text(encoding='utf-8'))==basis(),'Basis differs')
    require(json.loads((ROOT/BRIDGE).read_text(encoding='utf-8'))==correspondence(),'Correspondence differs')
    require(load_catalog(ROOT,BASIS).document==composed(),'Catalog differs')
    result=restored();checks=proofs();bindings=diagnostics()
    prior_path='reports/shared-real-cuts-v1.json';prior=json.loads((ROOT/prior_path).read_text(encoding='utf-8'))
    for p,stamp in (prior['source_sha256']|prior['artifact_sha256']).items():
        require(digest((ROOT/p).read_bytes())==stamp,'Preserved cut evidence changed: '+p)
    paths={LIBRARY,BASIS,BRIDGE,EXAMPLE,MANIFEST,prior_path,*prior['source_sha256'],*prior['artifact_sha256'],
        'scripts/shared_cut_products.py','scripts/visible_products_vocabulary.py','scripts/visible_products_collection.py',
        'scripts/check_shared_cut_products.py','tests/test_shared_cut_products.py','docs/shared-cut-products-v1.md',
        'scripts/check_real_products.py','examples/v011/real-products.noema','noema/polynomial_proofs.py',
        'noema/constructed_semantics.py',*catalog().source_sha256}
    return dict(schema='noema-shared-cut-products-evidence-1',shared_definitions_added=15,
        preserved_definitions_connected=10,new_compositions=5,new_primitives=0,
        public_words=399,public_definitions=376,public_primitives=23,
        correspondence=BRIDGE,combined_injective_correspondences=len(MAPPING),original_manuscript_modified=False,
        proof_frontend_projection=dict(from_edition='0.16',to_edition='0.14',payload_unchanged=True),
        polynomial_rational_results=checks,binding_diagnostics=bindings,binding_diagnostics_are_real_cut_models=False,
        z3_version=z3.get_version_string(),visible=dict(vocabulary_edition=14,pages=result['pages'],
            volumes=result['volumes'],rows=result['rows'],body_glyphs=result['body_glyphs'],
            declarations=len(result['document']['declarations']),statements=len(result['document']['statements'])),
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)},
        artifact_sha256={p.relative_to(ROOT).as_posix():digest(p.read_bytes()) for p in sorted(OUT.glob('*.svg'))},
        full_manuscript_visible_decoding=False,all_real_field_laws_proven=False,limits=LIMITS+[
            'The visible example is a proof test suite with three deliberately false universal claims.',
            'Ten selected source definitions are preserved by injective renaming; the five new compositions are not attributed to the original manuscript.'])
