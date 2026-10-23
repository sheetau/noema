from scripts.review_kinematics_headings import records,build_report

def test_two_complete_headings_keep_their_distinct_roles():
    rs=records();assert len(rs)==2 and all(not r['unresolved'] for r in rs)

def test_two_source_unit_judgments_with_pinned_evidence():
    r=build_report();assert r['whole_units_semantically_verified'] and r['verified_full_units']['einstein-1905']==2
