from copy import deepcopy
import pytest
from scripts.check_shared_vectors import *
from scripts.visible_analysis_collection import decode_collection as decode_old
from scripts.visible_word_forms import symbol
from scripts.vector_diagnostics import Model,truth_sorts,vector,identity,valid,equal,xor


def test_eight_source_definitions_and_all_earlier_names_are_injective():
    c=catalog();targets={d['name']:d for d in composed()['declarations']};bridge=correspondence()
    assert len(bridge['rows'])==8 and len(MAPPING)==48
    for old,new in DEFINITIONS.items():assert renamed(c.entries[old]['declaration'],DEFINITIONS)==targets[new]
    mapped=injective_mapping(c.document,MAPPING)
    assert renamed(mapped,{v:k for k,v in MAPPING.items()})==c.document
    assert all(r['source_meaning'] and r['shared_meaning'] and isinstance(r['statement_indices'],list) for r in bridge['rows'])
    assert not bridge['original_manuscript_modified'] and not bridge['quotation_names_merged']
    assert all(d['kind']=='definition' for d in composed()['declarations'])


def test_existing_416_words_and_23_primitives_are_preserved():
    old=AnalysisVocabulary();new=vocabulary()
    assert len(new._words)==424 and len(new._definitions)==401
    assert sum(new._plain_declaration(n)['kind']=='primitive' for n in new._words)==23
    for n in old._words:
        assert new.word(n)==old.word(n) and new.entry(n)==old.entry(n)
        assert new._plain_declaration(n)==old._plain_declaration(n)
    assert len({symbol(new.word(n),new) for n in new._words})==424
    bad=new.document();bad['compounds']['vectoraffinevalue']['roles'][1:3]=['offset','matrix']
    with pytest.raises(ValueError,match='published meanings'):VectorsVocabulary(bad)


def test_all_eight_bodies_are_restored_from_saved_geometry():
    result=restored()
    assert result['document']==example()
    assert len(result['document']['declarations'])==8 and len(result['document']['statements'])==4
    with pytest.raises(ValueError,match='vocabulary'):decode_old(saved_pages())
    with pytest.raises(ValueError):decode_collection(saved_pages()+[saved_pages()[-1]],vocabulary())
    assert [r['value'] for r in examples_checked()[1]['answers']]==[False,True,False,True]


def test_native_parameter_models_detect_operand_order_and_component_errors():
    rows={r['name']:r for r in native_checks()}
    assert len(rows)==26 and all(r['expected']==r['actual'] for r in rows.values())
    assert rows['same_values_different_functions']['actual']
    assert not rows['different_x']['actual'] and not rows['different_y']['actual']
    assert not rows['declared_fold_order']['actual'] and rows['reversed_fold_order']['actual']
    assert rows['coefficient_precedes_input']['actual']
    assert not rows['nonlinear_increments_differ']['actual']


def test_selected_components_do_not_claim_to_compare_unselected_values():
    model=Model(restored()['document'],individuals=('x','y','z'))
    left=lambda c:c=='x';right=lambda c:c in ('x','z')
    assert model.check('vectorcompare',[('x','y'),left,right,equal])
    assert not model.check('vectorcompare',[('x','y','z'),left,right,equal])


def test_finite_projection_uses_one_fixed_matrix_and_nonempty_scope():
    rows={r['name']:r for r in finite_checks()}
    assert len(rows)==20 and all(r['expected']==r['actual'] for r in rows.values())
    assert rows['three_points_fit_same_matrix']['actual']
    assert not rows['fourth_point_breaks_same_matrix']['actual']
    assert not rows['empty_not_affine']['actual'] and not rows['empty_not_uniform']['actual']
    assert rows['no_valid_displacement_is_vacuous']['actual']
    assert all(not r['actual'] for n,r in rows.items() if n.startswith(('invalid_matrix_','invalid_offset_')))


def test_truth_projection_preserves_operations_and_binding_order_explicitly():
    native=restored()['document'];projected=Model(native,finite=True).document
    assert projected==normalize_document(truth_sorts(native)) and projected!=native
    assert [d['name'] for d in projected['declarations']]==[d['name'] for d in native['declarations']]


def test_native_vector_domain_is_not_silently_enumerated_over_numeric_samples():
    model=Model(restored()['document'])
    with pytest.raises(ValueError,match='number|rational'):
        model.check('vectoruniform',[('x','y'),lambda p:True,identity,valid,equal,xor,xor])
