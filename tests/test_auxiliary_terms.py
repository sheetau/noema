from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from scripts.check_auxiliary_terms import finite_extensions, defined_graphs, first_order_checks, vector_checks, rational_uniqueness, explanation_checks, explanation_identity, finite_refusal, attribution_checks, alignment
from scripts.compose_auxiliary_terms import ROOT, PARENT, composed, generic_composed


def test_state_preservation_and_unique_extra_value_are_distinct_requirements():
    result=finite_extensions();rows=result['cases'];assert len(rows)==8
    assert rows['baseline']==rows['different_states_same_value']==rows['empty_theory']==[True,True]
    assert rows['extra_freedom']==[True,False]
    assert rows['missing_base_state']==rows['leaks_forbidden_state']==rows['empty_theory_with_extension']==[False,False]
    assert result['conservativity_does_not_prove_consistency']


def test_total_function_graphs_preserve_every_subset_of_the_finite_fixture():
    rows=defined_graphs()['cases'];assert len(rows)==48
    assert all(value==[True] for value in rows.values())


def test_actual_noema_definition_has_a_general_first_order_proof():
    result=first_order_checks();assert len(result['claims'])==2
    assert all(value['status']=='valid' for value in result['claims'].values())
    assert result['actual_noema_definitions_expanded']
    assert result['arbitrary_nonempty_individual_domains']
    assert result['does_not_prove_real_vector_closure']


def test_vector_extension_compares_only_the_spatial_values():
    result=vector_checks();rows=result['cases'];assert len(rows)==20
    assert all(value==[':wrong_' not in name] for name,value in rows.items())
    assert result['uniqueness_is_spatial_component_equality_not_function_identity']


def test_nonzero_divisor_constructs_a_unique_rational_component():
    result=rational_uniqueness();assert len(result['claims'])==2
    assert all(value['status']=='valid' for value in result['claims'].values())


def test_true_contents_do_not_automatically_supply_an_introduction_reason():
    rows=explanation_checks();assert len(rows)==8
    assert all(r['result']==[r['determined'] and r['dependence'] and r['adopted']] for r in rows)


def test_reason_and_construction_descriptions_keep_author_scope_and_identity():
    result=explanation_identity();rows=result['cases'];assert len(rows)==6
    assert all(value==[name=='none',False] for name,value in rows.items())
    assert result['definitionally_equal_alias_not_automatically_substituted_inside_description']
    assert result['construction_not_executed']


def test_arbitrary_real_vector_claim_is_not_covered_by_the_individual_domain_proof():
    result=finite_refusal();assert result['refused']
    assert 'Cannot finitely quantify the rational number domain' in result['reason']


def test_attributed_role_and_explanation_do_not_execute_their_contents():
    result=attribution_checks();rows=result['cases'];assert len(rows)==6
    assert rows['none']==[True,True] and rows['role']==[False,True] and rows['explanation']==[True,False]
    assert rows['author']==rows['scope']==rows['context']==[False,False]
    assert result['quoted_contents_not_executed']


def test_source_role_remains_a_partial_reading_and_excludes_obviousness():
    result=alignment();assert len(result['segments'])==1
    assert result['segments'][0]['source'].startswith('daß in der entwickelten Theorie')
    assert 'Man sieht' not in result['segments'][0]['source']
    assert result['conservative_determined_extension_is_a_partial_role_reading']
    assert result['verified_full_units']==0


def test_parent_and_all_notation_roundtrips_are_preserved():
    for builder,counts in ((generic_composed,(7,27,0)),(composed,(595,940,173))):
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
