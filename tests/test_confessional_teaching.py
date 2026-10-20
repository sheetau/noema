from scripts.check_confessional_teaching import (
    profession_checks, standard_checks, teaching_checks, quote_domain_checks, unknown_checks, structure_checks)


def test_same_church_avows_the_same_confessional_content_without_truth_export(): profession_checks()


def test_adopted_standard_keeps_closed_description_identity(): standard_checks()


def test_actual_exposition_obeys_the_adopted_standard_for_both_audiences(): teaching_checks()


def test_ranked_quotation_does_not_execute_or_finitely_approximate_message_domain(): quote_domain_checks()


def test_unknown_profession_criteria_and_teaching_inputs_are_rejected(): unknown_checks()


def test_preserved_meanings_archived_evidence_and_roundtrips(): structure_checks()
