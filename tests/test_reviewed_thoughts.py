from scripts.check_reviewed_thoughts import native_checks, binding_checks, unknown_checks, structure_checks


def test_native_care_completion_and_same_judgment_goodwill(): native_checks()


def test_exact_bindings_and_independent_conditions(): binding_checks()


def test_unknown_relations_rejected(): unknown_checks()


def test_legacy_projection_meanings_evidence_and_roundtrips(): structure_checks()
