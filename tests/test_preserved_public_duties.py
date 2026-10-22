from scripts import check_preserved_public_duties as check

def test_same_signed_requirements_and_fulfillment():check.preservation_checks()
def test_complete_coverage_and_full_domain_rejection():check.coverage_checks()
def test_nonexemption_joint_compatibility_and_no_restriction():check.compatibility_checks()
def test_same_public_target_for_freedom_and_comparison():check.source_checks()
def test_inherited_structure_and_quote_rank():check.structure_checks()
