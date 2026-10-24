from scripts.check_observed_amplitude import numeric_checks,binding_checks,quantifier_checks,presentation_checks,structure_checks

def test_selected_magnitudes_and_printed_ratio():assert numeric_checks()['facsimile_denominator_distinguished']

def test_same_physical_setting_and_question():assert binding_checks()['all_63_setting_roles_bound']

def test_every_naming_and_universal_slot():assert quantifier_checks()['naming_witnesses_each']==56

def test_task_names_consequence_and_display():assert presentation_checks()['closed_quotes_not_executed']

def test_source_and_old_evidence():assert structure_checks()['old_379_statements_and_judgments_preserved']
