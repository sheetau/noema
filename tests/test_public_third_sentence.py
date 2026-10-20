from scripts import check_public_third_sentence as checks


def test_integrated_sentence_needs_every_attribution_with_world_truth_unknown():
    result = checks.attribution_checks()
    assert result['required_relations'] == result['omitted_relations_refused'] == 18
    assert result['world_inputs_unknown_and_unexecuted']
    assert not result['replaced_definitions']


def test_every_source_phrase_has_a_reachable_meaning_and_an_explicit_reading():
    result = checks.source_checks()
    assert result['reviewed_nonblank_characters'] == 337
    assert result['all_named_definitions_reachable']


def test_old_reviews_and_local_evidence_are_preserved():
    result = checks.preservation_checks()
    assert result['preserved_whole_unit_reviews'] == 13
    assert result['whole_unit_count_not_increased']
