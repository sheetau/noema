import pytest

from noema.grammar import parse
from noema.meaning_basis import audit_basis
from scripts.check_conditional_release import values
from scripts.check_described_appraisals import candidate
from scripts.check_referenced_kinds import profile_checks, profile_laws, native_checks, native_model, attribution_checks, alignment
from scripts.compose_referenced_kinds import ROOT, PARENT, generic_composed, source_composed


def test_feature_profiles_use_exactly_the_nonempty_selected_scope_and_eligible_objects():
    result = profile_checks()
    assert result == {'cases': 256, 'eligible_matches': 20}


def test_profile_equivalence_has_fixed_scope_laws_without_identity_or_context_independence():
    rows = profile_laws()
    assert sum(row['status'] == 'valid' for row in rows.values()) == 5
    assert all(rows[key]['countermodel_found'] for key in (
        'same_profile_implies_same_individual', 'profiles_are_independent_of_context', 'profile_alone_implies_eligibility'))


def test_reference_coherence_is_required_before_positive_or_negative_familiarity():
    rows = native_checks()
    assert len(rows) == 15
    for key in ('no_reference', 'no_features', 'wrong_reference_person', 'wrong_reference_anchor',
                'wrong_reference_case', 'wrong_reference_ditch', 'reference_not_unsteady', 'inconsistent_references'):
        assert rows[key] == [False] * 6
    assert rows['multiple_coherent_references'] == rows['baseline']
    assert rows['different_selected_feature'][:2] == [False, True]
    assert rows['only_broad_activity_familiar'][2:4] == [False, True]
    assert rows['familiar_without_current_candidate'][:4] == [False, True, True, False]
    assert rows['old_broad_reason'][-2:] == [False, False]


def test_unknown_features_do_not_become_false_or_negative_familiarity():
    doc = candidate(source_composed()[0], '''r za[] a.r zb[] d.r zc[] d.r zd[] a.r ze[] d.
q[t[k h4b[k za[]]][k zb[]]].''')
    model = native_model(doc, 'baseline')
    def unknown(*args):
        raise ValueError('Unknown feature interpretation')
    model['h3v'] = unknown
    with pytest.raises(ValueError, match='Unknown feature interpretation'):
        values(doc, model, ('person', 'shackle', 'release', 'limb', 'movement', 'small', 'jump', 'experience', 'other', 'feature'),
            ('before', 'case', 'anchor'))


def test_new_attribution_rejects_old_broad_content_without_executing_either():
    result = attribution_checks()
    assert result['content_unexecuted']
    assert len(result['cases']) == 6
    assert [key for key, row in result['cases'].items() if row[0]] == ['baseline']


def test_existing_source_range_is_refined_without_claiming_semantic_completion():
    row = alignment()
    assert row['source'] == 'weil er zu dergleichen freier Bewegung nicht gewöhnt ist.'
    assert not row['full_semantic_equivalence']
    assert 'which features and prior depictions dergleichen selects' in row['remaining']


def test_broad_attribution_is_replaced_and_all_earlier_statements_and_definitions_survive():
    parent = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    for builder, expected in ((generic_composed, (0, 2)), (source_composed, (213, 325))):
        text, basis = builder()
        doc = parse(text)
        result = audit_basis(doc, basis)
        assert (result['primitive_count'], result['definition_count']) == expected
        assert (ROOT / basis['document']).read_text(encoding='utf-8') == text
    assert doc['declarations'][:len(parent['declarations'])] == parent['declarations']
    assert doc['statements'][:-1] == parent['statements'][:-1]
    assert len(doc['statements']) == len(parent['statements']) == 13
    assert parent['statements'][-1]['body']['symbol'] == 'h3t'
    assert doc['statements'][-1]['body']['symbol'] == 'h4f'
