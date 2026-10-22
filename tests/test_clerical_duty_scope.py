from scripts import check_clerical_duty_scope as check

def test_direct_requirements_and_complete_ledger_equivalence():check.direct_checks()
def test_unbounded_domains_are_rejected():check.domain_checks()
def test_no_restriction_includes_every_selected_office():check.all_office_checks()
def test_same_clerical_office_source_and_public_target():check.source_checks()
def test_inherited_meanings_and_rank():check.structure_checks()
