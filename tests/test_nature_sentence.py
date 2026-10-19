from scripts import check_nature_sentence as checks


def test_native_acquisition_without_prescribed_origin():
    assert checks.source_checks()['contrasts']['prior_deliberated_contribution'] == [False, True]


def test_first_sentence_attribution():
    assert checks.discourse_checks()['quote_uses_revised_content']


def test_unchanged_component_evidence():
    assert checks.reused_checks()['finite_evidence_reused_without_claiming_new_execution']


def test_complete_sentence_partition_and_preserved_reviews():
    assert checks.structure_checks()['nonblank_source_partition_complete']
