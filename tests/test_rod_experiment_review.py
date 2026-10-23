from scripts.review_rod_experiment import build_report

def test_complete_rod_setup_and_prospective_two_method_question():
    assert build_report()['whole_units_semantically_verified']
