from scripts.check_rod_geometry import axis_checks,motion_checks,history_checks,domain_checks,structure_checks

def test_axis_position_positive_length_and_thickness():assert axis_checks()['axis_on_line_not_merely_parallel']
def test_all_material_points_and_all_ordered_time_pairs():assert motion_checks()['internal_deformation_and_acceleration_distinguished']
def test_history_shape_metric_and_coordinate_bindings():assert history_checks()['all_outer_slots_bound']
def test_real_time_domains_and_unknown_cuts_not_sampled():assert domain_checks()['local_instantiations_not_domain_replacements']
def test_source_and_old_judgments_preserved():assert structure_checks()['no_new_author_assertion']
