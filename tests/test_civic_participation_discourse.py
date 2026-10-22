from scripts.check_civic_participation_discourse import focus_checks,binding_checks,explanation_checks,participation_checks,discourse_checks,structure_checks


def test_clerical_focus_does_not_remove_other_citizens_freedom():
    r=focus_checks();assert r['candidate_focus_individual_and_all_citizen_freedom']['only_cleric_free']==[True,True,True,False]


def test_exact_criticism_and_proposal_binding_lengths_and_positions():
    r=binding_checks();assert r['wrong_lengths_rejected']


def test_written_explanation_uses_same_person_notes_activities_and_public():
    r=explanation_checks();assert r['public_and_written_facets_are_distinct']


def test_partial_participation_is_neither_required_nor_sufficient():
    r=participation_checks();assert r['native_plural_membership_full_and_partial_ranges']['full']==[True,False,True,True]
    assert r['native_plural_membership_full_and_partial_ranges']['unavailable']==[True,True,False,False]


def test_presentation_preserves_whole_content_without_executing_it():
    r=discourse_checks();assert r['quoted_citizenship_permission_and_proposal_not_executed']


def test_preserved_meanings_reports_and_manuscript():
    r=structure_checks();assert (r['new_definitions'],r['new_primitives'],r['preserved_manuscript_statements'])==(12,3,102)
