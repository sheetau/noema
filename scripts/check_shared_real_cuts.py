"""Exact source bridge, visible geometry and bounded rational proof evidence."""
from copy import deepcopy
from functools import lru_cache
import json
import z3
from noema.constructed import parse,format_graph
from noema.grammar import parse as old_parse
from noema.discourse import normalize_document as legacy_normalize
from noema.rational_proofs import verify
from noema.constructed_semantics import evaluate_document
from scripts.shared_real_cuts import *
from scripts.visible_cuts_vocabulary import CutsVocabulary,MANIFEST
from scripts.visible_cuts_collection import compile_collection,decode_collection
from scripts.visible_word_forms import Word
from scripts.visible_syntax_geometry import to_svg,from_svg
from scripts.check_real_cuts import LAWS,COUNTERCLAIMS
from scripts.shared_modality import call,v,op
from scripts.shared_time import q

OUT=ROOT/'output/visible-real-cuts-v1'
EXAMPLE='examples/v016/visible-real-cuts-v1.noema'
LABEL=Word('proper',('round','red','book'))
INTERPRETATIONS=dict(rationalbelow='less',rationaladd='add',rationalnegate='negate',rationalmultiply='multiply')


@lru_cache(maxsize=1)
def vocabulary():return CutsVocabulary()


def num(n,d=1):return dict(kind='number',numerator=n,denominator=d)
def apply(f,x):return dict(kind='apply',function=f,arguments=[x])
def rational(x):return call('rationalcut',x)


@lru_cache(maxsize=1)
def claims():
    text=(ROOT/OLD).read_text(encoding='utf-8');result={}
    for name,tail in {**LAWS,**COUNTERCLAIMS}.items():
        result[name]=(renamed(old_parse(text+tail)['statements'][-1],MAPPING),name in LAWS)
    for name,scale in [('half',num(1,2)),('double',num(2)),('threehalves',num(3,2))]:
        left=apply(call('cutpositivescale',scale,rational(v('value'))),v('point'))
        right=call('rationalbelow',v('point'),call('rationalmultiply',scale,v('value')))
        body=q('forall','value','number',q('forall','point','number',op('iff',left,right)))
        result['positive_scale_'+name]=(dict(kind='assert',body=body),True)
    for name,scale in [('zero',num(0)),('negative',num(-1))]:
        body=q('forall','value','number',q('forall','point','number',op('not',apply(call('cutpositivescale',scale,rational(v('value'))),v('point')))))
        result['nonpositive_scale_'+name]=(dict(kind='assert',body=body),True)
    left=call('cutincluded',rational(v('left')),rational(v('right')))
    right=op('not',call('rationalbelow',v('right'),v('left')))
    result['inclusion_preserves_embedding']=(dict(kind='assert',body=q('forall','left','number',q('forall','right','number',op('iff',left,right)))),True)
    return result


def proof_view(document):
    """Explicit payload-preserving projection to the unchanged proof frontend."""
    native=normalize_document(document);old=deepcopy(native)
    old['schema_version']=old['lexicon_version']='0.14';checked=legacy_normalize(old)
    require(checked['declarations']==native['declarations'] and checked['statements']==native['statements'],
            'Proof projection changes Native payload')
    return checked


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
    require(result['document']==example(),'Saved visible real-cut document differs')
    return result


@lru_cache(maxsize=1)
def proofs():
    rows=[];base=restored()['document']
    for (name,(_,valid)),statement in zip(claims().items(),base['statements'],strict=True):
        doc=deepcopy(base);doc['statements']=[statement]
        result=verify(proof_view(doc),INTERPRETATIONS)[0]
        require(result['status']==('valid' if valid else 'invalid'),'Unexpected proof result: '+name)
        rows.append(dict(name=name,expected_valid=valid,**result))
    return rows


def prepare():
    from scripts.shared_real_cuts import prepare as prepare_library
    prepare_library();write_new(EXAMPLE,format_graph(example())+'\n')
    OUT.mkdir(parents=True,exist_ok=True)
    for i,page in enumerate(compiled()['pages']):
        write_new((OUT/('page-'+str(i+1).zfill(5)+'.svg')).relative_to(ROOT).as_posix(),to_svg(page['shapes']))


def build_report():
    require(parse((ROOT/LIBRARY).read_text(encoding='utf-8'))==composed(),'Shared library differs')
    require(json.loads((ROOT/BASIS).read_text(encoding='utf-8'))==basis(),'Shared basis differs')
    require(json.loads((ROOT/BRIDGE).read_text(encoding='utf-8'))==correspondence(),'Source correspondence differs')
    require(load_catalog(ROOT,BASIS).document==composed(),'New meaning catalog differs')
    result=restored();checks=proofs();previous=json.loads((ROOT/'reports/visible-collection-v1.json').read_text(encoding='utf-8'))
    paths={LIBRARY,BASIS,BRIDGE,EXAMPLE,MANIFEST,OLD,OLD_BASIS,'scripts/shared_real_cuts.py',
        'scripts/visible_cuts_vocabulary.py','scripts/visible_cuts_collection.py','scripts/check_shared_real_cuts.py',
        'tests/test_shared_real_cuts.py','docs/shared-real-cuts-v1.md','noema/rational_proofs.py','noema/discourse.py',
        'scripts/check_real_cuts.py','data/work-state.json','data/semantic-review-index-v456.json',
        'reports/written-progress-v432.json','reports/visible-collection-v1.json',*previous['source_sha256'],*catalog().source_sha256}
    for p,stamp in previous['source_sha256'].items():require(digest((ROOT/p).read_bytes())==stamp,'Earlier visible evidence changed')
    return dict(schema='noema-shared-real-cuts-evidence-1',shared_definitions_added=9,new_primitives=0,
        reused_arithmetic_primitives=4,public_words=384,public_definitions=361,public_primitives=23,
        source_correspondences=correspondence()['rows'],source_mapping_injective=True,original_manuscript_modified=False,
        proof_frontend_projection=dict(from_edition='0.16',to_edition='0.14',payload_unchanged=True),
        linear_rational_results=checks,z3_version=z3.get_version_string(),
        visible=dict(vocabulary_edition=13,pages=result['pages'],volumes=result['volumes'],rows=result['rows'],
                     declarations=len(result['document']['declarations']),statements=len(result['document']['statements']),
                     body_glyphs=result['body_glyphs']),
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)},
        artifact_sha256={p.relative_to(ROOT).as_posix():digest(p.read_bytes()) for p in sorted(OUT.glob('*.svg'))},
        full_manuscript_visible_decoding=False,all_real_field_laws_proven=False,limits=LIMITS+[
            'The visible example includes both valid laws and deliberately false universal counterclaims; it is a proof test suite, not an asserted theory of all those claims.',
            'Only the explicitly selected 13 Einstein declarations have a reviewed lexical correspondence in this batch; no same-spelled Kant declaration is mapped by it.'])
