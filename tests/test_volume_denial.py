from scripts.check_volume_denial import denial_checks,quantifier_checks,counterexample_checks,presentation_checks,reading_checks,structure_checks


def test_denial():assert denial_checks()['actual_volume_equality_negated']
def test_quantifiers():assert quantifier_checks()['forall_not_distinguished_from_not_forall_in_mixed_scope']
def test_counterexample():assert counterexample_checks()['nonzero_transverse_wave_at_nonzero_speed']
def test_presentation():assert presentation_checks()['weaker_reading_not_silently_substituted']
def test_reading():assert reading_checks()['first_three_sentences_prose_characters']==327
def test_structure():assert structure_checks()['all_387_statements_and_judgments_preserved']
