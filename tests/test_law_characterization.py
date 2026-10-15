from scripts import check_law_characterization as check


def test_characterization_requires_both_directions_in_every_finite_case():
    rows = check.truth_table_checks()['two_case_masks'][check.CORE]
    assert len(rows) == 16
    assert rows['1:3'] == [False, True, False, True, False, True]
    assert rows['3:1'] == [False, False, True, False, True, True]
    assert rows['0:0'] == [True, True, True, False, False, True]


def test_scope_coverage_and_simultaneous_conditions_remain_distinct():
    report = check.boundary_checks()
    rows = report['cases']
    assert rows['empty_scope'][0] is False
    assert rows['wrong_binding'][0] is False
    assert rows['expanded_scope'] == [False, False, True, False, True, True]
    assert rows['unconstrained_case'] == [True, True, True, False, False, False]
    assert rows['simultaneous'][4] is True
    assert len(report['unknown_interpretations_refused']) == 3


def test_all_three_source_relations_use_independent_case_and_theory_inputs():
    report = check.source_checks()
    rows = report['cases'][check.CORE]
    for name in ('bad_ratio', 'bad_potential_value', 'bad_potential_field', 'bad_radius'):
        assert rows[name] == [False, False, True, False, True, True]
    assert rows['theory_rejects_ratio'] == [False, True, False, True, False, True]
    assert rows['theory_agrees_bad_ratio'][0] is True
    assert rows['sample_scope'][0] is True
    assert rows['wrong_binding'][0] is False
    assert rows['duplicate_relation'] == [False, True, True, False, False, False]
    assert not report['actual_electron_theory_characterization_proved']


def test_catalogue_preserves_existing_formula_references_without_execution():
    row = check.catalogue_checks()
    assert row['source_contents'] == ['setw', 'seuz', 'sevn']
    assert row['projected_relations'] == ['sets', 'seur', 'seus', 'sevh']
    assert not row['quoted_bodies_executed']


def test_attributing_completeness_does_not_certify_it():
    row = check.attribution_check()
    assert row['quoted_targets'] == ['sewa']
    assert not row['completeness_claim_evaluated']
