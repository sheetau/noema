from scripts.check_self_directed_choice import goal_checks,liberty_checks,opportunity_checks,standing_checks,growth_checks,structure_checks

def test_positive_goals():assert goal_checks()
def test_liberty_background():assert liberty_checks()
def test_choice_opportunities():assert opportunity_checks()
def test_standing_capacity():assert standing_checks()
def test_aggregate_growth():assert growth_checks()
def test_structure():assert structure_checks()
