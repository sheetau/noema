from scripts.check_energy_frequency_law import numeric_checks,binding_checks,appraisal_checks,presentation_checks,structure_checks

def test_numeric():assert numeric_checks()['same_factor_for_distinct_energy_and_frequency_values']
def test_binding():assert binding_checks()['all_70_roles_and_65_universal_bindings_checked']
def test_appraisal():assert appraisal_checks()['same_law_description_and_context_for_value_and_standard']
def test_presentation():assert presentation_checks()['law_and_attention_appraisal_separately_attributed']
def test_structure():assert structure_checks()['all_393_statements_and_judgments_preserved']
