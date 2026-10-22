from scripts import check_political_quoted_speech as check


def test_same_two_contents_and_only_reservation():check.speech_checks()
def test_direct_or_authorized_representative_speech():check.representation_checks()
def test_political_ability_requires_policy_and_peace_but_not_compliance():check.ability_checks()
def test_all_goal_and_method_argument_slots():check.provider_checks()
def test_personal_qualification_is_necessary_not_sufficient():check.necessity_checks()
def test_preserved_meanings_quotation_ranks_and_provenance():check.structure_checks()
