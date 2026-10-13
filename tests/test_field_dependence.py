from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from scripts.check_field_dependence import dual_checks, response_checks, presence_checks, witness_checks, field_transform_checks, polynomial_checks, finite_refusal, source_checks, attribution_checks, alignment
from scripts.compose_field_dependence import ROOT, PARENT, composed, generic_composed


def test_magnetic_additional_term_preserves_the_minus_sign():
    result=dual_checks();rows=result['cases'];assert len(rows)==10
    assert rows['x:correct']==[True,True,True]
    assert rows['x:wrong_sign']==[True,False,True]
    assert rows['parallel:wrong_sign']==rows['zero:wrong_sign']==[True,True,True]
    assert result['zero_or_parallel_cases_do_not_detect_sign_errors_alone']


def test_exact_magnetic_response_is_distinct_from_first_order():
    rows=response_checks()['cases'];assert len(rows)==10
    assert rows['0:linear']==[True,True,True]
    assert rows['3/5:linear']==rows['-3/5:linear']==[True,False,False]
    assert all(value==[True,True,True] for name,value in rows.items() if name.endswith(':exact'))


def test_presence_change_is_not_just_a_change_of_value_sign_or_direction():
    result=presence_checks();rows=result['cases'];assert len(rows)==7
    assert rows['appears']==[False,True,True] and rows['disappears']==[True,False,True]
    assert rows['both_zero']==[False,False,False]
    for name in ('same_nonzero','value_changes','sign_changes','direction_changes'):assert rows[name]==[True,True,False]
    assert result['does_not_define_general_existence']


def test_two_distinct_input_configurations_witness_dependence_without_a_universal_change_claim():
    result=witness_checks();rows=result['cases'];assert len(rows)==5
    assert all(value==[name!='0'] for name,value in rows.items())
    assert result['two_witnesses_have_different_input_configurations']
    assert result['nonzero_longitudinal_counterexample']==[False,False]


def test_same_event_magnetic_response_matches_the_existing_full_field_transform():
    result=field_transform_checks();assert len(result['cases'])==9
    assert all(value==[True] for value in result['cases'].values())
    assert result['same_event_uses_transformed_coordinates']


def test_dual_signs_reuse_the_fixed_field_rational_remainder_argument():
    result=polynomial_checks();assert len(result['claims'])==3
    assert all(value['status']=='valid' for value in result['claims'].values())
    assert result['reused_remainder_report']=='reports/force-wordings-v1.json'
    assert result['full_real_cut_proof'] is False


def test_existential_real_witness_and_asymptotic_quantification_are_not_finite_domains():
    result=finite_refusal();assert set(result)=={'existential_witness','magnetic_asymptotic'}
    assert all('Cannot finitely quantify the rational number domain' in value for value in result.values())


def test_magnetic_analogy_keeps_field_point_event_and_context():
    result=source_checks();rows=result['cases'];assert len(rows)==9
    assert all(value==[name=='baseline'] for name,value in rows.items())
    assert result['asymptotic_truth_is_an_explicit_source_wiring_oracle']
    assert result['no_magnetic_pole_measurement_asserted']


def test_two_claims_keep_their_quoted_contents_without_evaluating_them():
    result=attribution_checks();rows=result['cases'];assert len(rows)==6
    assert rows['none']==[True,True]
    assert rows['dual']==[False,True] and rows['dependence']==[True,False]
    assert rows['author']==rows['scope']==rows['context']==[False,False]
    assert result['quoted_contents_not_executed']


def test_partial_alignment_excludes_auxiliary_role_and_its_explanation():
    result=alignment();rows=result['segments'];assert len(rows)==2
    assert all(r['unit']=='einstein-1905:u0176' for r in rows)
    assert rows[0]['source'].startswith('Analoges gilt')
    assert rows[1]['source'].startswith('daß die elektrischen')
    assert result['auxiliary_role_and_explanation_of_introduction_unwritten']
    assert result['verified_full_units']==0


def test_parent_and_all_notation_roundtrips_are_preserved():
    for builder,counts in ((generic_composed,(7,43,0)),(composed,(592,932,171))):
        text,basis=builder();doc=parse(text);audit=audit_basis(doc,basis)
        assert (audit['primitive_count'],audit['definition_count'],len(doc['statements']))==counts
        assert (ROOT/basis['document']).read_text(encoding='utf-8')==text
        for notation in ('compact','full'):
            form=format_graph(doc,notation)
            assert parse(form)==parse(decode(encode(form,'v2')))==doc
    parent=parse((ROOT/PARENT).read_text(encoding='utf-8'))
    assert doc['declarations'][:len(parent['declarations'])]==parent['declarations']
    assert doc['statements'][:-2]==parent['statements']
    byname={d['name']:d for d in doc['declarations']}
    assert all(d==byname[d['name']] for d in parse(generic_composed()[0])['declarations'])
