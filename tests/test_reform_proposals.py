from scripts.check_reform_proposals import comparison_checks,binding_checks,public_checks,unknown_checks,structure_checks


def test_strict_improvement_and_realization_are_separate():comparison_checks()


def test_exact_four_place_goal_binding():binding_checks()


def test_same_public_proposal_does_not_execute_its_content():public_checks()


def test_required_unknown_inputs_rejected():unknown_checks()


def test_unchanged_inheritance_evidence_and_roundtrip():structure_checks()
