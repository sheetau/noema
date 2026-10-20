from scripts.check_responsible_exposition import exposition_checks,possibility_checks,reference_checks,generic_checks,binding_checks,structure_checks


def test_native_same_doctrinal_exposition():exposition_checks()


def test_practical_possibility_occurrence_and_admissibility():possibility_checks()


def test_same_actor_act_goal_and_fixed_reference():reference_checks()


def test_generic_undertaking_keeps_first_person_and_closed_goal():generic_checks()


def test_exact_binding_and_goal_existentials():binding_checks()


def test_preserved_imports_and_evidence():structure_checks()
