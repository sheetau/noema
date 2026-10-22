from scripts import check_military_peace_guarantee as check


def test_four_interventions_nonempty_solutions_and_same_contents():check.causal_checks()
def test_native_public_peace_and_every_provider_binding():check.content_binding_checks()
def test_all_relevant_threats_and_backgrounds():check.scope_checks()
def test_same_institution_and_army_witnesses():check.witness_checks()
def test_same_person_complete_conditions_and_closed_profile():check.person_checks()
def test_preserved_meanings_and_source_provenance():check.structure_checks()
