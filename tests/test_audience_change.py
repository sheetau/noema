from scripts.check_audience_change import generic_checks,source_checks,structure


def test_scope_uses_one_reference_and_checks_all_members():
    assert generic_checks()['scope_eligibility_combinations']==16


def test_native_changes_preserve_the_intended_audience():
    result=source_checks()
    assert result['audience_contrasts']['unreached_reader']['values']==[True,True,False]
    assert result['primitive_receipt_understanding_access_and_list_not_evaluated']


def test_source_extension_preserves_existing_meanings_without_list_dependencies():
    assert structure()['list_and_receipt_dependencies_absent']
