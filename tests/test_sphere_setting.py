from scripts.check_sphere_setting import surface_checks,content_checks,presentation_checks,structure_checks

def test_current_surface_equivalence_full_scope():assert surface_checks()['both_directions_and_nonempty_surface_required']
def test_same_body_and_rest_shape():assert content_checks()['rest_shape_allows_nonzero_center']
def test_setting_equation_and_attached_author_gloss():assert presentation_checks()['quoted_contents_not_executed']
def test_prior_whole_unit_judgments_preserved():assert structure_checks()['prior_whole_unit_judgments_preserved']
