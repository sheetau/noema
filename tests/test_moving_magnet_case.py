from scripts.check_moving_magnet_case import binding_checks,local_checks,pointwise_checks,structure_checks

def test_case_bindings():assert binding_checks()['all_case_slots_used']
def test_local_witnesses():assert local_checks()['unknown_energy_refused']
def test_quantified_bodies():assert pointwise_checks()['full_real_time_quantification_refused']
def test_structure_and_discourse():assert structure_checks()['quoted_physics_not_executed']
