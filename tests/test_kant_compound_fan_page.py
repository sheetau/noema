from scripts.check_kant_compound_fan_page import checked


def test_actual_first_sentence_keeps_multiple_branches():
    row=checked(0)
    assert row['multiple_owners']>=1
    assert row['maximum_sides']>=2
    assert row['svg_changed']
