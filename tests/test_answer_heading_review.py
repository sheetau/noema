from scripts.register_answer_heading_review import audit_registration


def test_only_the_heading_unit_is_added_and_old_reviewed_meanings_are_unchanged():
    result=audit_registration()
    assert result['total_units']==8 and result['reviewed_nonblank_characters']==166
    assert result['title_question_and_body_still_unreviewed']
