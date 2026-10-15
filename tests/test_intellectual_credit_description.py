from scripts.check_intellectual_credit import description_checks


def test_equivalent_contents_do_not_make_criterion_descriptions_identical():
    result=description_checks()
    assert not result['description_equality']
    assert result['content_equality_in_supplied_model']
