from scripts.check_material_axes import numeric_checks,line_checks,history_checks,support_checks,triad_checks,structure_checks

def test_geometric_kernels():assert numeric_checks()['opposite_directions_and_nonunit_vectors_supported']
def test_all_material_members_and_origin():assert line_checks()['all_members_not_only_two_markers_checked']
def test_complete_histories_and_unsampled_domain():assert history_checks()['all_real_history_refused']
def test_physical_support_lines():assert support_checks()['shifted_origins_and_reversed_directions_allowed']
def test_three_axes_and_two_frames():assert triad_checks()['exact_three_axis_roles_and_unique_origin']
def test_preservation_and_incomplete_source_status():assert not structure_checks()['whole_unit_completion']
