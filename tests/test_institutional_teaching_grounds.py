from scripts.check_institutional_teaching_grounds import teaching_checks,scope_checks,reference_checks,report_checks,structure_checks


def test_native_institutional_teaching():teaching_checks()


def test_exhaustive_used_arguments_exclude_practical_motives():scope_checks()


def test_same_judgment_subject_content_and_unknown_rejection():reference_checks()


def test_closed_reports_remain_nonfactive():report_checks()


def test_preserved_meanings_evidence_and_roundtrip():structure_checks()
