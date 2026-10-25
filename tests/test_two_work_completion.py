from scripts.audit_two_work_completion import evidence_checks,build_report

def test_all_author_units_and_no_unreviewed_statements():
    works,_=evidence_checks()
    assert sum(w['reviewed_units'] for w in works.values())==302
    assert sum(w['nonblank_text_characters'] for w in works.values())==51127
    assert all(w['unreviewed_statements']==0 and w['unresolved_source_items']==0 for w in works.values())

def test_six_deliverables_with_scope_and_limits():
    r=build_report()
    assert len(r['completion_criteria'])==6 and not r['unresolved_completion_items']
    assert r['reviewer']=='assistant_review' and not r['semantic_equivalence_automatically_proved']
