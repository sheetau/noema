from scripts.check_inverse_field_claim import binding_checks,path_checks,necessity_checks,conclusion_checks,presentation_checks,structure_checks

def test_bindings():assert binding_checks()['first_inverse_nonzero_without_positivity']
def test_paths():assert path_checks()['native_nonempty_ordered_paths']
def test_necessity():assert necessity_checks()['nonempty_all_selected_situations']
def test_conclusion():assert conclusion_checks()['negative_and_minus_one_allowed']
def test_presentation():assert presentation_checks()['necessity_and_conclusion_not_executed']
def test_structure():assert structure_checks()['full_domain_refusal_preserved']
