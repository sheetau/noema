from scripts import check_deterrence_sentence as checks


def test_sentence_attribution_and_metaphors_do_not_assert_world_truth():
    r = checks.interface_checks()
    assert r['attribution_combinations'] == 64 and len(r['contrasts']) == 17
    assert r['independent_depiction_combinations'] == 8 and r['unknown_inputs_refused'] == 7


def test_component_evidence_still_binds_current_declarations_and_meaning_sources():
    assert len(checks.reused_checks()['reports']) == 5


def test_previous_sentences_keep_their_interpretation_after_reindexing():
    assert checks.preceding_checks()['reviewed_nonblank_characters'] == 1021


def test_source_partition_current_selection_and_three_notations():
    r = checks.structure_checks()
    assert r['paragraph_sentence_characters'] == 1211 and r['roundtrips']
