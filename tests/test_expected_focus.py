from copy import deepcopy
from scripts.check_expected_focus import preorder_checks,scalar_checks,native_and_unknown_checks,source_checks,structure,lambda_key


def test_predicate_comparison_ignores_only_bound_names():
    left=dict(kind='lambda',parameters=[dict(name='person',sort='individual')],
        body=dict(kind='call',symbol='property',arguments=[dict(kind='variable',name='person')]))
    right=deepcopy(left);right['parameters'][0]['name']='renamed';right['body']['arguments'][0]['name']='renamed'
    assert lambda_key(left)==lambda_key(right)
    right['body']['symbol']='different'
    assert lambda_key(left)!=lambda_key(right)


def test_all_three_content_preorders_are_checked_without_content_execution():
    assert preorder_checks()['accepted_preorders']==29


def test_expectation_ties_incomparability_and_complements_are_distinct():
    assert scalar_checks()['ties_and_incomparability_not_strict']


def test_native_guardian_comparison_uses_the_adopted_viewpoint_and_context():
    assert native_and_unknown_checks()['source_viewpoint_and_context_fixed']


def test_the_new_source_fragment_is_only_the_scalar_particle():
    assert source_checks()['new_nonblank_partial_characters']==5


def test_existing_content_and_seven_review_bindings_are_preserved():
    assert structure()['existing_statements']==34
