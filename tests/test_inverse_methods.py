from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from scripts.check_inverse_methods import path_checks, scalar_checks, field_checks, source_binding_checks, source_paths, premise_checks, finite_refusal, attribution_checks, alignment
from scripts.compose_inverse_methods import ROOT, PARENT, generic_composed, composed


def test_two_calculations_keep_distinct_descriptions_and_connected_paths():
    result=path_checks();rows=result['cases'];assert len(rows)==9
    assert all(value==[name in ('baseline','intermediate_steps')] for name,value in rows.items())
    assert result['quoted_formula_contents_not_executed']


def test_a_nonzero_witness_compares_scales_but_a_zero_witness_does_not():
    result=scalar_checks();rows=result['cases'];assert len(rows)==5
    assert rows['positive']==rows['negative']==rows['zero_masks_mismatch']==[True,True]
    assert rows['mismatch']==[True,False] and rows['zero_divisor']==[False]
    assert result['nonzero_witness_algebra']['status']=='valid'


def test_solving_and_substitution_use_different_scale_sources_at_the_same_inverse_speed():
    result=field_checks();rows=result['cases'];assert len(rows)==12
    assert all(all(value)==(not name.endswith(':mismatch')) for name,value in rows.items())
    assert result['coefficient_function_evaluated_at_opposite_speed']
    assert result['zero_field_agreement_not_general_operator_agreement']


def test_source_inverse_formulas_restore_the_same_old_fields_and_domain():
    result=source_binding_checks();rows=result['cases'];assert len(rows)==5
    assert rows['positive']==rows['negative']==[True,True]
    assert rows['different_rule_scale']==[True,False]
    assert rows['wrong_context']==rows['different_domains']==[False,False]
    assert result['global_field_equality_and_domain_equality_are_explicit_fixture_oracles']


def test_source_paths_keep_their_formula_endpoints_and_context():
    result=source_paths();rows=result['cases'];assert len(rows)==5
    assert all(value==[name=='baseline'] for name,value in rows.items())
    assert result['steps_constructed_in_noema']
    assert result['quoted_source_formulas_not_executed']


def test_paths_formula_truth_and_general_agreement_are_independent_premises():
    rows=premise_checks();assert len(rows)==8
    assert all(r['result']==[r['paths'] and r['forward_formula'] and r['general_agreement']] for r in rows)


def test_arbitrary_real_inputs_are_not_replaced_by_finite_examples():
    result=finite_refusal();assert result['refused']
    assert 'Cannot finitely quantify the rational number domain' in result['reason']


def test_attribution_keeps_the_comparison_premise_and_product_conclusion():
    rows=attribution_checks();assert len(rows)==7
    assert all(value==[name=='-1'] for name,value in rows.items())


def test_alignment_is_partial_even_when_the_whole_paragraph_is_associated():
    result=alignment();assert len(result['segments'])==5
    assert result['segments'][0]['unit']=='einstein-1905:u0165'
    assert result['method_soundness_and_modal_force_unfinished']
    assert result['verified_full_units']==0


def test_library_source_parent_and_all_notations_are_preserved():
    for builder,counts in ((generic_composed,(2,5,0)),(composed,(553,902,163))):
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
