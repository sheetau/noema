from scripts.check_moving_unit_charge import amount_checks,premise_checks,presentation_checks,structure_checks

def test_amount():assert amount_checks()['separate_moving_record_required']
def test_premise():assert premise_checks()['premise_and_conclusion_not_conflated']
def test_presentation():assert presentation_checks()['quoted_inference_not_evaluated_as_proof']
def test_structure():assert structure_checks()['whole_unit_review_not_claimed']
