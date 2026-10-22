from scripts import check_eighth_paragraph as check


def test_five_sentences_cover_the_entire_paragraph_once():check.coverage_checks()
def test_shared_rulers_examples_references_and_final_generalization():check.transition_checks()
def test_prior_judgments_and_meanings_remain_bound():check.preservation_checks()
