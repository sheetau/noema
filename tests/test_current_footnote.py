from scripts.check_current_footnote import joint_checks, scope_checks, audit_checks


def test_active_title_and_all_footnote_assertions_share_references():
    assert len(joint_checks()['cases']) == 12


def test_selected_graph_roundtrips_and_preserves_registered_meanings():
    assert scope_checks()['preserved_review_selections'] == 10


def test_current_source_audit_covers_every_clause_without_claiming_completion():
    assert audit_checks()['open_clauses'] == 2
