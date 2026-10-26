"""Visible source preservation, cut embedding laws and labeled rational diagnostics."""
from copy import deepcopy
from functools import lru_cache
from fractions import Fraction
import json
import z3

from noema.constructed import parse,format_graph
from noema.grammar import parse as old_parse
from noema.meaning_catalog import load_catalog,_references
from noema.rational_proofs import verify
from noema.constructed_semantics import evaluate_document
from scripts.shared_cut_analysis import *
from scripts.shared_modality import call,v,op
from scripts.shared_reference import lam
from scripts.shared_time import q,allof
from scripts.visible_analysis_vocabulary import AnalysisVocabulary,MANIFEST
from scripts.visible_analysis_collection import compile_collection,decode_collection
from scripts.visible_word_forms import Word
from scripts.visible_syntax_geometry import to_svg,from_svg
from scripts.check_shared_real_cuts import proof_view,num,apply,rational,INTERPRETATIONS
from scripts.cut_analysis_diagnostics import rational_projection,partition_diagnostics

OUT=ROOT/'output/visible-cut-analysis-v1'
EXAMPLE='examples/v016/visible-cut-analysis-v1.noema'
LABEL=Word('proper',('round','red','book','above'))


def number(value):
    value=Fraction(value);return num(value.numerator,value.denominator)


def cell(lower,upper,tag):
    # Quadratic interpolation is only a total field selector. All uses here
    # substitute the literal indices 0, 1, 2 before rational proof expansion.
    i=v('index');a,b,c=map(Fraction,(lower,upper,tag))
    add=lambda x,y:call('rationaladd',x,y)
    mul=lambda x,y:call('rationalmultiply',x,y)
    field=add(number(a),add(mul(number(b-a),i),mul(number((c-2*b+a)/2),mul(i,add(i,num(-1))))))
    return lam([('index','number')],rational(field))


@lru_cache(maxsize=1)
def vocabulary():return AnalysisVocabulary()


@lru_cache(maxsize=1)
def claims():
    rows={};a,b,r=v('left'),v('right'),v('radius')
    lt=lambda x,y:call('rationalbelow',x,y)
    plus=lambda x,y:call('rationaladd',x,y)
    def universal(name,args,body):
        for arg in reversed(args):body=q('forall',arg,'number',body)
        rows[name]=(dict(kind='assert',body=body),True)
    universal('near_preserves_rational_embedding',['left','right','radius'],op('iff',call('cutnear',rational(a),rational(b),rational(r)),
        allof(lt(num(0),r),lt(a,plus(b,r)),lt(b,plus(a,r)))))
    universal('closed_interval_preserves_rational_embedding',['left','right','radius'],op('iff',call('cutclosedinterval',rational(a),rational(b),rational(r)),
        op('and',op('not',lt(r,a)),op('not',lt(b,r)))))
    universal('left_neighborhood_has_two_strict_boundaries',['left','right','radius'],op('iff',call('cutleftnear',rational(a),rational(r),rational(b)),
        allof(lt(num(0),r),lt(plus(a,call('rationalnegate',r)),b),lt(b,a))))
    for name,values,expected in [('left_tag',(0,1,0),True),('middle_tag',(0,1,Fraction(1,2)),True),('right_tag',(0,1,1),True),
        ('tag_below',(0,1,-1),False),('tag_above',(0,1,2),False),('zero_cell_width',(1,1,1),False),('negative_cell_width',(1,0,0),False)]:
        rows[name]=(dict(kind='assert',body=call('cuttaggedcell',cell(*values))),expected)
    return rows


@lru_cache(maxsize=1)
def example():
    doc=deepcopy(composed());doc['statements']=[s for s,valid in claims().values()]
    return normalize_document(doc)


@lru_cache(maxsize=1)
def compiled():return compile_collection(vocabulary().encode(example()),LABEL,vocabulary(),payload=768)


def saved_pages():return [from_svg(p.read_text(encoding='utf-8')) for p in sorted(OUT.glob('page-*.svg'))]


@lru_cache(maxsize=1)
def restored():
    result=decode_collection(saved_pages(),vocabulary(),public_names=True)
    require(result['document']==example(),'Visible analysis differs')
    return result


@lru_cache(maxsize=1)
def native_proofs():
    rows=[];base=restored()['document']
    for (name,(_,valid)),statement in zip(claims().items(),base['statements'],strict=True):
        doc=deepcopy(base);doc['statements']=[statement]
        result=verify(proof_view(doc),INTERPRETATIONS,timeout_ms=15000)[0]
        require(result['status']==('valid' if valid else 'invalid'),'Unexpected cut embedding result: '+name)
        rows.append(dict(name=name,expected_valid=valid,**result))
    return rows


@lru_cache(maxsize=1)
def diagnostic_claims():
    from scripts.check_limits import claim_document,claims as old_claims
    old=old_parse(claim_document());rows={}
    mapping=dict(previous.previous.ARITHMETIC,ka='cutnear',kb='cutaccumulation',kc='cutlimit',kd='cutcontinuousat',ke='cutcontinuous',kf='cutclosedinterval')
    for (name,(_,expected)),statement in zip(old_claims().items(),old['statements'],strict=True):
        if 'kg' in _references(statement):continue
        rows[name]=(renamed(statement,mapping),expected=='valid')
    x=v('point');all_domain=lam([('point','number')],op('equal',x,x))
    empty=lam([('point','number')],op('not',op('equal',x,x)))
    isolated=lam([('point','number')],op('equal',x,num(0)))
    positive=lam([('point','number')],call('rationalbelow',num(0),x))
    negative=lam([('point','number')],call('rationalbelow',x,num(0)))
    identity=lam([('point','number')],x)
    for name,body,valid in [
        ('left_approach_from_negative',call('cutleftaccumulation',negative,num(0)),True),
        ('right_domain_is_not_left_approach',call('cutleftaccumulation',positive,num(0)),False),
        ('empty_left_approach_rejected',call('cutleftaccumulation',empty,num(0)),False),
        ('isolated_left_approach_rejected',call('cutleftaccumulation',isolated,num(0)),False),
        ('whole_domain_has_interior',call('cutinterior',all_domain,num(0)),True),
        ('isolated_point_not_interior',call('cutinterior',isolated,num(0)),False),
        ('excluded_endpoint_not_interior',call('cutinterior',positive,num(0)),False),
        ('bounded_identity_does_not_diverge',call('cutleftdivergespositive',negative,identity,num(0)),False),
        ('empty_domain_does_not_diverge',call('cutleftdivergespositive',empty,identity,num(0)),False)]:
        rows[name]=(dict(kind='assert',body=body),valid)
    return rows


@lru_cache(maxsize=1)
def rational_diagnostics():
    rows=[]
    for name,(statement,valid) in diagnostic_claims().items():
        doc=rational_projection(restored()['document'],_references(statement));doc['statements']=[statement]
        names={d['name'] for d in doc['declarations'] if d['kind']=='primitive'}
        result=verify(proof_view(doc),{n:INTERPRETATIONS[n] for n in names},timeout_ms=15000)[0]
        require(result['status']==('valid' if valid else 'invalid'),'Rational analysis diagnostic differs: '+name)
        rows.append(dict(name=name,expected_valid=valid,**result))
    return rows


@lru_cache(maxsize=1)
def finite_diagnostics():return partition_diagnostics(restored()['document'])


def prepare():
    from scripts.shared_cut_analysis import prepare as prepare_library
    prepare_library();write_new(EXAMPLE,format_graph(example())+'\n');OUT.mkdir(parents=True,exist_ok=True)
    for i,page in enumerate(compiled()['pages']):
        write_new((OUT/('page-'+str(i+1).zfill(5)+'.svg')).relative_to(ROOT).as_posix(),to_svg(page['shapes']))


def build_report():
    require(parse((ROOT/LIBRARY).read_text(encoding='utf-8'))==composed(),'Analysis library differs')
    require(json.loads((ROOT/BASIS).read_text(encoding='utf-8'))==basis(),'Analysis basis differs')
    require(json.loads((ROOT/BRIDGE).read_text(encoding='utf-8'))==correspondence(),'Analysis correspondence differs')
    require(load_catalog(ROOT,BASIS).document==composed(),'Analysis catalog differs')
    result=restored();native=native_proofs();rational_checks=rational_diagnostics();finite=finite_diagnostics()
    prior_path='reports/shared-cut-products-v1.json';prior=json.loads((ROOT/prior_path).read_text(encoding='utf-8'))
    for p,stamp in (prior['source_sha256']|prior['artifact_sha256']).items():
        require(digest((ROOT/p).read_bytes())==stamp,'Preserved arithmetic evidence changed: '+p)
    paths={LIBRARY,BASIS,BRIDGE,EXAMPLE,MANIFEST,prior_path,*prior['source_sha256'],*prior['artifact_sha256'],
        'scripts/shared_cut_analysis.py','scripts/cut_analysis_diagnostics.py','scripts/check_shared_cut_analysis.py',
        'scripts/visible_analysis_vocabulary.py','scripts/visible_analysis_collection.py','tests/test_shared_cut_analysis.py',
        'docs/shared-cut-analysis-v1.md','scripts/check_limits.py','scripts/compose_limits.py',*catalog().source_sha256}
    return dict(schema='noema-shared-cut-analysis-evidence-1',shared_definitions_added=17,new_primitives=0,
        public_words=416,public_definitions=393,public_primitives=23,correspondence=BRIDGE,
        combined_injective_correspondences=len(MAPPING),original_manuscript_modified=False,
        source_declarations_without_statement_uses=[r['source_symbol'] for r in correspondence()['rows'] if not r['statement_indices']],
        native_cut_embedding_results=native,rational_analogue_results=rational_checks,finite_rational_partition_diagnostics=finite,
        rational_projection=dict(cut_sort='fn[N]T',diagnostic_sort='number',lower_arithmetic='exact rational',
            quantifiers_remain_infinite=True,proof_of_all_real_cuts=False,reciprocal_not_silently_removed=True),
        z3_version=z3.get_version_string(),visible=dict(vocabulary_edition=15,pages=result['pages'],volumes=result['volumes'],
            rows=result['rows'],body_glyphs=result['body_glyphs'],declarations=len(result['document']['declarations']),
            statements=len(result['document']['statements'])),
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)},
        artifact_sha256={p.relative_to(ROOT).as_posix():digest(p.read_bytes()) for p in sorted(OUT.glob('*.svg'))},
        full_manuscript_visible_decoding=False,all_real_analysis_theorems_proven=False,limits=LIMITS+[
            'The visible document is a test suite including four deliberately false tagged-cell assertions.',
            'Native payload preservation, exact rational embedding checks, rational analogue diagnostics and finite sums are separate evidence.'])
