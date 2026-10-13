from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from scripts.check_field_common_scale import vector_checks, point_checks, source_checks, counterexample_checks, attribution_checks, finite_refusal, alignment
from scripts.compose_field_common_scale import ROOT, PARENT, composed, generic_composed


def test_one_scalar_is_shared_by_all_selected_components():
    result=vector_checks();rows=result['cases'];assert len(rows)==10
    assert rows['positive']==rows['negative']==rows['zero_factor']==[True]
    assert rows['zero_vectors_factor_one']==rows['zero_vectors_factor_two']==[True]
    assert rows['different_component_factors']==rows['nonproportional_vectors']==rows['empty_axes']==rows['duplicate_axes']==[False]
    assert result['uniqueness_not_assumed_for_zero_vectors']


def test_electric_and_magnetic_components_cannot_select_separate_factors():
    rows=point_checks()['cases'];assert len(rows)==9
    assert all(value==[name in ('baseline','second_point_same_factor')] for name,value in rows.items())


def test_speed_argument_and_inverse_coordinate_pullback_are_preserved():
    result=source_checks();rows=result['cases'];assert len(rows)==15
    assert all(value==[name.endswith(':baseline')] for name,value in rows.items())
    assert result['actual_mixed_fields_and_inverse_coordinates_evaluated']
    assert result['global_proportionality_and_domain_equality_are_explicit_oracles']
    assert not result['arbitrary_real_field_proof']


def test_shared_equations_alone_do_not_determine_a_common_factor():
    result=counterexample_checks()
    assert result['eight_algebraic_balances']==[True]
    assert result['no_common_rational_scalar']['status']=='valid'
    assert result['first_electric']!=result['second_electric']
    assert result['does_not_refute_unformalized_physical_identification_premises']


def test_claim_attribution_does_not_assert_its_mathematical_truth():
    result=attribution_checks();rows=result['cases'];assert len(rows)==6
    assert all(value==[name=='-1'] for name,value in rows.items())
    assert result['claim_not_evaluated_as_truth']


def test_global_domain_is_not_silently_replaced_by_sample_points():
    result=finite_refusal();assert result['refused']
    assert 'Cannot finitely quantify the rational number domain' in result['reason']


def test_local_facsimile_correction_retains_the_original_transcription():
    result=alignment();assert len(result['segments'])==6
    raw=result['raw_math_cells'];normalized=result['facsimile_corrected_math_cells']
    assert raw[7]=='=ψ(v)β(M+vVz),'
    assert normalized[7]=='=ψ(v)β(M+vVZ),'
    assert all(a==b for i,(a,b) in enumerate(zip(raw,normalized)) if i!=7)
    assert result['inference_before_conclusion_clause_unwritten']
    assert result['verified_full_units']==0


def test_dependency_library_and_source_preserve_prior_text_and_all_notations():
    for builder,counts in ((generic_composed,(3,13,0)),(composed,(543,866,156))):
        text,basis=builder();doc=parse(text);audit=audit_basis(doc,basis)
        assert (audit['primitive_count'],audit['definition_count'],len(doc['statements']))==counts
        assert (ROOT/basis['document']).read_text(encoding='utf-8')==text
        for notation in ('compact','full'):
            form=format_graph(doc,notation)
            assert parse(form)==parse(decode(encode(form,'v2')))==doc
    parent=parse((ROOT/PARENT).read_text(encoding='utf-8'))
    assert doc['declarations'][:len(parent['declarations'])]==parent['declarations']
    assert doc['statements'][:-1]==parent['statements']
    byname={d['name']:d for d in doc['declarations']}
    assert all(d==byname[d['name']] for d in parse(generic_composed()[0])['declarations'])
