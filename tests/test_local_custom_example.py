from scripts.check_local_custom_example import contrasts,build_report

def test_obligation_scope_convention_and_performance():assert contrasts()['cases']==33
def test_meaning_catalog_and_roundtrips():assert not build_report()['language_syntax_added']
