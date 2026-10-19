from scripts import check_assessed_difficulty as checks


def test_non_ease_and_success_paths():
    result = checks.generic_checks()
    assert result['contrasts']['mixed_cheap_success'] == [False, True, False, True]
    assert result['contrasts']['mixed_missing_success_cost'] == [False, False, False, False]


def test_native_self_development():
    assert checks.source_checks()['no_achievement_presupposed']


def test_revised_attribution():
    assert checks.discourse_checks()['quote_uses_revised_content']


def test_preserved_meanings_and_reviews():
    assert checks.structure_checks()['scope_and_attribution_exactly_rebound']
