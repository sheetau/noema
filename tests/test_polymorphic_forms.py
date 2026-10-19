from scripts import check_polymorphic_forms as checks


def test_known_template_witnesses_preserve_arity_types_and_syntax():
    assert checks.template_checks()['original_contents_never_executed']


def test_explicit_legacy_adapter_and_quantification_limit():
    assert checks.bridge_checks()['quantified_classification_explicitly_refused']


def test_source_depiction_uses_the_widened_classification():
    assert checks.presentation_checks()['world_contents_not_executed_by_attribution']


def test_previous_meanings_and_reviews():
    assert checks.reused_checks()['first_sentence_review_preserved']


def test_source_replacement_and_notation_roundtrips():
    assert checks.structure_checks()['old_unary_classifier_removed_from_current_target']
