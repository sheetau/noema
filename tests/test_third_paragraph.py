from scripts import check_third_paragraph as checks


def test_comparison_population_contains_prior_people_without_identifying_the_domains():
    assert checks.population_checks()['broader_population_allowed']


def test_extrication_keeps_the_same_persons_causal_release():
    assert checks.release_checks()['removal_requires_agent_change_and_cause']


def test_attributed_extrication_and_count_keep_references_and_quote_world_contents():
    assert checks.attribution_checks()['world_and_bodily_contents_not_executed']


def test_existing_four_sentences_and_whole_unit_judgments_are_preserved():
    assert checks.structure_checks()['preserved_whole_unit_reviews'] == 12


def test_explicit_five_sentence_reading_covers_every_nonblank_source_position():
    assert checks.reading_checks()['all_nonblank_positions_covered']
