from scripts import check_guarded_walking_reading as checks


def test_seven_statement_interfaces_reject_mixed_attribution_and_missing_components():
    result=checks.interface_checks()
    assert len(result['contrasts'])==17 and result['unknown_inputs_refused']==5


def test_reused_finite_evidence_still_describes_current_dependencies():
    assert len(checks.reused_checks()['reports'])==8


def test_complete_source_partition_and_unchanged_active_selection():
    result=checks.structure_checks()
    assert result['clause_partition']==12 and result['reviewed_sentence_characters']==244


def test_previous_five_readings_keep_their_meanings_after_catalog_relocation():
    result=checks.preceding_checks()
    assert result['reviewed_nonblank_characters']==777 and len(result['reviews'])==5
