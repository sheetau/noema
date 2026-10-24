from scripts.check_charge_constancy_claim import chain_checks,content_checks,presentation_checks,structure_checks

def test_native_easy_derivation():assert chain_checks()['native_nonempty_chain_and_same_nonnegative_total']
def test_same_context_and_theorem():assert content_checks()['importance_is_of_same_theorem_not_truth']
def test_full_note_and_quoted_resting_frame():assert presentation_checks()['quoted_content_not_evaluated']
def test_preserved_evidence_and_roundtrip():assert structure_checks()['all_412_prior_statements_and_meanings_preserved']
