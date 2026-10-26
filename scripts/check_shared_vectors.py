"""Check the preserved vector library, visible geometry and explicit small models."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.constructed_semantics import evaluate_document
from scripts.shared_vectors import *
from scripts.shared_modality import call,v,op
from scripts.shared_time import q
from scripts.visible_analysis_vocabulary import AnalysisVocabulary
from scripts.visible_vectors_vocabulary import VectorsVocabulary,MANIFEST
from scripts.visible_vectors_collection import compile_collection,decode_collection
from scripts.visible_word_forms import Word
from scripts.visible_syntax_geometry import to_svg,from_svg
from scripts.vector_diagnostics import native_diagnostics,finite_diagnostics

OUT=ROOT/'output/visible-vectors-v1'
EXAMPLE='examples/v016/visible-vectors-v1.noema'
LABEL=Word('proper',('round','inside','book'))


def sequence(*items):return dict(kind='sequence',element='individual',items=list(items))


@lru_cache(maxsize=1)
def vocabulary():return VectorsVocabulary()


@lru_cache(maxsize=1)
def example():
    doc=deepcopy(composed())
    bodies=[call('vectorcomponents',sequence()),
        q('forall','x','individual',call('vectorcomponents',sequence(v('x')))),
        q('forall','x','individual',call('vectorcomponents',sequence(v('x'),v('x')))),
        q('forall','x','individual',q('forall','y','individual',op('implies',op('not',op('equal',v('x'),v('y'))),
            call('vectorcomponents',sequence(v('x'),v('y'))))))]
    doc['statements']=[dict(kind='ask',body=body) for body in bodies]
    return normalize_document(doc)


@lru_cache(maxsize=1)
def compiled():return compile_collection(vocabulary().encode(example()),LABEL,vocabulary(),payload=768)


def saved_pages():return [from_svg(p.read_text(encoding='utf-8')) for p in sorted(OUT.glob('page-*.svg'))]


@lru_cache(maxsize=1)
def restored():
    result=decode_collection(saved_pages(),vocabulary(),public_names=True)
    require(result['document']==example(),'Visible vector document differs')
    return result


@lru_cache(maxsize=1)
def examples_checked():
    rows=[]
    for domain in [('x',),('x','y')]:
        actual=evaluate_document(restored()['document'],individuals=domain,situations=('now',),primitives={})
        require([r['value'] for r in actual]==[False,True,False,True],'Component questions differ')
        rows.append(dict(individuals=list(domain),answers=actual))
    return rows


@lru_cache(maxsize=1)
def native_checks():return native_diagnostics(restored()['document'])


@lru_cache(maxsize=1)
def finite_checks():return finite_diagnostics(restored()['document'])


def prepare():
    from scripts.shared_vectors import prepare as prepare_library
    prepare_library();write_new(EXAMPLE,format_graph(example())+'\n');OUT.mkdir(parents=True,exist_ok=True)
    for i,page in enumerate(compiled()['pages']):
        write_new((OUT/('page-'+str(i+1).zfill(5)+'.svg')).relative_to(ROOT).as_posix(),to_svg(page['shapes']))


def build_report():
    require(parse((ROOT/LIBRARY).read_text(encoding='utf-8'))==composed(),'Vector library differs')
    require(json.loads((ROOT/BASIS).read_text(encoding='utf-8'))==basis(),'Vector basis differs')
    require(json.loads((ROOT/BRIDGE).read_text(encoding='utf-8'))==correspondence(),'Vector correspondence differs')
    require(load_catalog(ROOT,BASIS).document==composed(),'Vector catalog differs')
    result=restored();native=native_checks();finite=finite_checks();answers=examples_checked()
    previous_path='reports/shared-cut-analysis-v2.json';prior=json.loads((ROOT/previous_path).read_text(encoding='utf-8'))
    for path,stamp in (prior['source_sha256']|prior['artifact_sha256']).items():
        require(digest((ROOT/path).read_bytes())==stamp,'Previous evidence changed: '+path)
    paths={LIBRARY,BASIS,BRIDGE,EXAMPLE,MANIFEST,previous_path,*prior['source_sha256'],*prior['artifact_sha256'],
        'scripts/shared_vectors.py','scripts/vector_diagnostics.py','scripts/check_shared_vectors.py',
        'scripts/visible_vectors_vocabulary.py','scripts/visible_vectors_collection.py','tests/test_shared_vectors.py',
        'docs/shared-vectors-v1.md',*catalog().source_sha256}
    return dict(schema='noema-shared-vectors-evidence-1',shared_definitions_added=8,new_primitives=0,
        public_words=424,public_definitions=401,public_primitives=23,correspondence=BRIDGE,
        combined_injective_correspondences=len(MAPPING),original_manuscript_modified=False,
        source_declarations_without_statement_uses=[r['source_symbol'] for r in correspondence()['rows'] if not r['statement_indices']],
        native_parameter_diagnostics=native,finite_truth_value_models=finite,visible_question_answers=answers,
        finite_projection=dict(source_value_sort='fn[N]T',diagnostic_value_sort='truth',components=2,
            possible_vectors=4,universal_displacement_combinations=64,proof_over_all_real_vectors=False),
        visible=dict(vocabulary_edition=16,pages=result['pages'],volumes=result['volumes'],rows=result['rows'],
            body_glyphs=result['body_glyphs'],declarations=len(result['document']['declarations']),statements=len(result['document']['statements'])),
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)},
        artifact_sha256={p.relative_to(ROOT).as_posix():digest(p.read_bytes()) for p in sorted(OUT.glob('*.svg'))},
        full_manuscript_visible_decoding=False,uniformity_implies_affinity_proven=False,limits=LIMITS)
