from scripts.check_paired_church_reports import native_checks,construction_checks,content_checks,structure_checks


def test_same_official_utterance_speaker_and_all_recipients():native_checks()


def test_exact_ranked_report_construction_without_evaluation():construction_checks()


def test_constructed_reports_preserve_their_content():content_checks()


def test_preserved_meanings_and_roundtrip():structure_checks()
