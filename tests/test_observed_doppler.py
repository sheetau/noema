from scripts.check_observed_doppler import model_checks,mapping_checks,physical_checks,binding_checks,universal_checks,presentation_checks,structure_checks

def test_source_and_observer_families():assert model_checks()['cases']>60
def test_inverse_coordinates_and_old_time():assert mapping_checks()['cases']>40
def test_physical_emission_and_reception():assert physical_checks()['cases']>50
def test_same_roles_through_hypothesis():assert binding_checks()['all_59_roles_bound']
def test_all_conditional_variable_positions():assert universal_checks()['quantified_slots']==55
def test_reference_and_conditional_presentation():assert presentation_checks()['quotes_not_evaluated_as_physical_truth']
def test_prefix_and_non_circular_hypothesis():assert structure_checks()['doppler_conclusion_not_assumed_in_hypothesis']
