from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from scripts.check_theory_transition import generic_checks, source_checks, attribution_checks, alignment
from scripts.compose_theory_transition import ROOT, composed, generic_composed


def test_required_results_are_exact_nonempty_and_relative_to_one_task():
    result=generic_checks();rows=result['cases']
    assert len(rows)==18 and rows['baseline']==[True,True,False,True]
    for name in ('extra_required','extra_selected','empty_selected','wrong_task','wrong_need_actor','wrong_need_stage'):
        assert not rows[name][0]
    assert rows['extra_required'][1] and rows['empty_selected']==[False]*4
    assert result['necessary_for_task_not_logical_necessity']


def test_derivation_and_application_share_contents_without_asserting_truth():
    result=generic_checks();rows=result['cases']
    for name in ('missing_derivation','wrong_derived_actor','wrong_derived_stage','wrong_description'):
        assert not rows[name][1]
    assert rows['wrong_description']==[True,False,False,False]
    assert result['claim_descriptions_not_evaluated_as_truth']


def test_application_requires_same_example_and_actor_but_not_distinct_examples():
    result=generic_checks();rows=result['cases']
    for name in ('missing_application','unshown_application','wrong_field','wrong_showing_actor','different_example_shown'):
        assert rows[name]==[True,True,False,False]
    assert rows['same_example_for_both']==[True,True,False,True]
    assert rows['current_goal_achieved']==[True]*4
    assert result['same_example_must_be_application_and_shown']


def test_source_summary_keeps_both_principles_and_same_proof_scope():
    result=source_checks();rows=result['cases'];assert len(rows)==14
    assert rows['baseline']==[True,False,True]
    for name in ('extra_required','missing_proof','wrong_proof_content','wrong_proof_scope','future_proof_only',
        'wrong_framework','first_principle_missing','second_principle_missing'):
        assert rows[name]==[False,False,True]
    assert rows['wrong_description']==[False]*3
    assert result['proof_presentation_not_proof_validity']
    assert result['representative_two_result_fixture_not_exhaustive_source_inventory']


def test_attributed_task_start_does_not_assert_goal_achievement():
    result=attribution_checks();rows=result['cases'];assert len(rows)==8
    assert rows['baseline']==[True,True]
    assert rows['wrong_task']==rows['wrong_stage']==[True,False]
    assert rows['goal_replaces_summary']==[False,True]
    assert rows['summary_replaces_goal']==[True,False]
    for name in ('wrong_author','wrong_scope','wrong_context'):assert rows[name]==[False,False]
    assert result['quoted_goal_not_evaluated_as_current_achievement']


def test_alignment_excludes_field_names_without_concept_definitions():
    result=alignment();rows=result['segments'];assert len(rows)==3
    assert {r['unit'] for r in rows}=={'einstein-1905:u0150'}
    assert result['unwritten_field_terms']==['Kinematik','Elektrodynamik']
    assert all(word not in r['source'] for word in result['unwritten_field_terms'] for r in rows)
    assert all(not r['full_semantic_equivalence'] for r in rows)
    assert result['field_references_not_counted_as_concept_definitions']
    assert result['verified_full_units']==0 and result['following_electrodynamic_headings_unwritten']


def test_parent_preserved_and_both_notations_and_glyphs_roundtrip():
    for compose,counts in ((generic_composed,(0,3,0)),(composed,(526,790,152))):
        text,basis=compose();doc=parse(text);audit=audit_basis(doc,basis)
        assert (audit['primitive_count'],audit['definition_count'],len(doc['statements']))==counts
        assert (ROOT/basis['document']).read_text(encoding='utf-8')==text
        for notation in ('compact','full'):
            form=format_graph(doc,notation)
            assert parse(form)==parse(decode(encode(form,'v2')))==doc
    parent=parse((ROOT/'examples/v014/einstein-derivation-modalities.noema').read_text(encoding='utf-8'))
    assert doc['declarations'][:len(parent['declarations'])]==parent['declarations']
    assert doc['statements'][:-2]==parent['statements']
