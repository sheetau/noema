from scripts.check_creed_opinions import identity_checks, expression_checks, unknown_checks, structure_checks


def test_same_thought_creed_qualification_scholar_and_public(): identity_checks()


def test_actual_own_expression_to_every_fixed_recipient(): expression_checks()


def test_required_unknown_relations_rejected(): unknown_checks()


def test_inheritance_evidence_roundtrip_and_nonexecuting_quote(): structure_checks()
