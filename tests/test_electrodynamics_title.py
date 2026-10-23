from scripts.check_electrodynamics_title import topic_checks,presentation_checks,structure_checks

def test_shared_topic_and_motion():assert topic_checks()['four_quoted_physical_schemas_preserved']
def test_title_roles_without_physical_assertion():assert presentation_checks()['topic_not_executed']
def test_preserved_paragraph_and_scope():assert structure_checks()['prior_reviews_preserved']
