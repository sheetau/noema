from scripts.check_electron_moving_law_task import speed_checks,setting_checks,candidate_checks,question_checks,presentation_checks,binder_checks,structure_checks
def test_speed():assert speed_checks()
def test_setting():assert setting_checks()
def test_candidate():assert candidate_checks()
def test_question():assert question_checks()
def test_presentation():assert presentation_checks()
def test_binders():assert binder_checks()
def test_structure():assert structure_checks()
