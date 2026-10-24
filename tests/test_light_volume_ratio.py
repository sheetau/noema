from scripts.check_light_volume_ratio import numeric_checks,binding_checks,chain_checks,polynomial_checks,presentation_checks,structure_checks

def test_numeric():assert numeric_checks()['printed_quotient_direction_root_and_cosine_preserved']
def test_binding():assert binding_checks()['all_63_shared_context_roles_and_62_name_witnesses_checked']
def test_chain():assert chain_checks()['native_connected_nonempty_chain_and_nonnegative_total']
def test_polynomial():assert polynomial_checks()['rational_polynomial_only']
def test_presentation():assert presentation_checks()['names_claim_easy_calculation_colon_display_and_back_reference_preserved']
def test_structure():assert structure_checks()['all_391_statements_and_judgments_preserved']
