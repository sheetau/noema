from scripts import check_quoted_outcomes as check


def test_quoted_causal_evaluation_and_attribution_are_independent():
    result=check.checks()
    assert result['truth_and_attribution_cases']==136
    assert result['quoted_and_direct_evaluation_agree']
    rows=result['contrasts'][check.LIBRARY]
    assert rows['second_activity']==[True,False,False,True]


def test_constructing_and_recording_quotes_never_evaluates_their_contents():
    result=check.checks()
    assert result['construction_and_attribution_do_not_execute_content']
    assert result['unlowered_uncached_examples']==4


def test_equal_referents_do_not_license_substitution_of_attributed_syntax():
    rows=check.checks()['contrasts'][check.FULL]
    assert rows['alias_target']==[False,True,True,False]
    assert rows['swapped_results']==rows['other_result_description']==[False,False,True,False]


def test_report_coordinates_do_not_replace_the_modal_anchor():
    result=check.checks()
    assert result['report_context_distinct_from_modal_anchor']
    for name in ('wrong_node','wrong_author','wrong_scope','wrong_report_context'):
        assert result['contrasts'][check.FULL][name]==[True,True,True,False]


def test_unknown_content_and_unknown_attribution_are_separately_refused():
    assert set(check.checks()['unknown_inputs_refused'])=={'unknown_effect','unknown_cause','unknown_record'}


def test_types_quote_layers_and_legacy_entrypoint_remain_explicit():
    assert set(check.rejection_checks())=={'rank_zero_function','wrong_target_type','missing_nested_result_quote',
        'implicit_rank_promotion','legacy_parser_does_not_silently_adopt_016'}


def test_promotion_preserves_the_parent_and_documents_only_the_two_new_definitions():
    result=check.structure()
    assert result['inherited_basis_signature_coverage'] and result['inherited_declarations_and_15_statements_unchanged']
    assert result['new_definitions']==2 and result['new_primitives']==result['new_assertions']==0
    assert result['new_definition_signatures_documented']
