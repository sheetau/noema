from scripts.check_electrodynamics_title_review import build_report

def test_whole_title_review():assert build_report()['whole_unit_semantically_verified']
