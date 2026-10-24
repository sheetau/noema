from scripts.review_eighth_section_heading import record,build_report

def test_whole_heading():
    r=record();assert r['reviewed_prose_characters']==103 and r['unresolved']==[]

def test_review_provenance():assert build_report()['whole_units_semantically_verified']
