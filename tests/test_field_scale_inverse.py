from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from scripts.check_field_scale_inverse import polynomial_checks, inverse_field_checks, coefficient_checks, final_premise_checks, normalized_binding_checks, attribution_checks, alignment
from scripts.compose_field_scale_inverse import ROOT, PARENT, generic_composed, composed


def test_inverse_algebra_keeps_nonzero_and_positive_conditions_distinct():
    result=polynomial_checks();rows=result['claims'];assert len(rows)==8
    assert all(r['status']=='valid' for r in rows.values())
    assert result['positive_branch_not_added_to_author_premise']
    assert result['rational_polynomial_claims_only']


def test_scaled_six_component_transform_recovers_fields_with_reciprocal_scales():
    result=inverse_field_checks();rows=result['cases'];assert len(rows)==12
    assert all(all(values)==name.endswith('_reciprocal') for name,values in rows.items())
    assert result['actual_six_component_and_inverse_coordinate_definitions_evaluated']
    assert result['zero_forward_not_invertible']


def test_negative_branch_satisfies_the_recorded_premise_but_not_the_conclusion():
    result=coefficient_checks();rows=result['cases'];assert len(rows)==8
    assert rows['positive_unit']==rows['zero_speed_unit']==[True,True,True,True]
    assert rows['negative_unit']==[True,True,True,False]
    assert rows['reciprocal_unequal']==[True,False,False,False]
    assert rows['equal_two']==rows['both_zero']==[False,True,False,False]
    assert rows['light_speed_excluded']==rows['negative_light_speed_excluded']==[False]*4
    assert result['physical_symmetry_argument_not_evaluated']


def test_normalization_requires_both_the_common_scale_equations_and_unit_value():
    rows=final_premise_checks();assert len(rows)==4
    assert all(r['result']==[r['common_scale'] and r['unit']] for r in rows)
    result=normalized_binding_checks();assert len(result['cases'])==4
    assert all(v==[k=='baseline'] for k,v in result['cases'].items())
    assert result['global_domain_and_proportionality_are_fixture_oracles']


def test_four_attributions_preserve_claims_and_the_two_inference_directions():
    result=attribution_checks();rows=result['cases'];assert len(rows)==20
    assert all(v==[k.endswith(':baseline')] for k,v in rows.items())
    assert result['claims_and_inferences_do_not_execute_quoted_truth']


def test_source_glyph_change_is_retained_without_importing_the_earlier_phi():
    result=alignment();assert len(result['segments'])==7
    assert result['source_math_text']['M0311']=='φ(v).φ(−v)=1'
    assert result['notation_reading']['page_908']=='ψ(v)'
    assert result['notation_reading']['page_909']=='φ(v)'
    assert result['two_inverse_constructions_and_symmetry_reason_unwritten']
    assert result['positive_branch_justification_unwritten']
    assert result['verified_full_units']==0


def test_parent_is_preserved_and_all_notations_roundtrip():
    for builder,counts in ((generic_composed,(4,5,0)),(composed,(547,879,160))):
        text,basis=builder();doc=parse(text);audit=audit_basis(doc,basis)
        assert (audit['primitive_count'],audit['definition_count'],len(doc['statements']))==counts
        assert (ROOT/basis['document']).read_text(encoding='utf-8')==text
        for notation in ('compact','full'):
            form=format_graph(doc,notation)
            assert parse(form)==parse(decode(encode(form,'v2')))==doc
    parent=parse((ROOT/PARENT).read_text(encoding='utf-8'))
    assert doc['declarations'][:len(parent['declarations'])]==parent['declarations']
    assert doc['statements'][:-4]==parent['statements']
    byname={d['name']:d for d in doc['declarations']}
    assert all(d==byname[d['name']] for d in parse(generic_composed()[0])['declarations'])
