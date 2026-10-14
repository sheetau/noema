from copy import deepcopy
from functools import lru_cache
import hashlib
import json
import pytest
from noema.grammar import parse, format_graph
from scripts.check_public_divergent_judgments import ROOT, REPORT, PARENT, setup, select, model_for, values, bind_presentation
from scripts.check_rod_setup import guarded


@lru_cache(maxsize=1)
def base():
    return setup((ROOT / 'examples/v014/public-divergent-judgments-core.noema').read_text(encoding='utf-8'))


def data(indices=None):
    return select(base(), indices if indices is not None else tuple(range(9)))


def test_permission_does_not_assert_speech_review_or_truth():
    item = data((1, 2, 3, 4, 6, 7))
    assert values(item, model_for(item, (False, False, True, False, False))) == [False, True, True, False, False, False]


def test_permission_does_not_require_an_existing_personal_judgment():
    item = data((0, 1, 2, 3, 4))
    assert values(item, model_for(item, judged=False)) == [False, False, True, True, False]


def test_permitted_presentation_does_not_waive_its_office_duty():
    item = data((1, 2, 3, 4, 5))
    assert values(item, model_for(item, (True, True, True, False, True))) == [True, True, False, False, False]


def test_preserved_duties_are_not_necessarily_fulfilled():
    item = data((1, 3, 4, 5))
    assert values(item, model_for(item, (True, True, True, True, False))) == [True, True, True, False]


def test_speech_can_occur_without_permission():
    item = data((1, 2, 3, 5))
    assert values(item, model_for(item, (True, True, False, True, True))) == [True, False, False, True]


def test_aiming_for_review_does_not_imply_its_achievement():
    item = data((1, 6))
    assert values(item, model_for(item)) == [True, False]
    assert values(item, model_for(item, reviewed=True)) == [True, True]


def test_public_review_does_not_prove_that_this_speech_was_performed():
    item = data((1, 6))
    assert values(item, model_for(item, (False, False, True, True, True), reviewed=True)) == [False, True]


@pytest.mark.parametrize('variant', ('other_judge', 'other_issue', 'other_standard', 'empty_candidates'))
def test_the_presented_issue_must_be_the_subject_of_this_persons_divergent_judgment(variant):
    item = data((0, 1, 2))
    assert values(item, model_for(item, variant=variant)) == [False, False, True]


@pytest.mark.parametrize('variant', ('other_message', 'other_goal', 'other_voice', 'outsider', 'not_scholar'))
def test_message_review_goal_self_attribution_and_public_role_stay_bound(variant):
    item = data((0, 1, 2))
    assert values(item, model_for(item, variant=variant)) == [True, False, True]


@pytest.mark.parametrize('variant', ('other_permitted_target', 'public_prohibited'))
def test_another_target_or_opposed_requirement_does_not_authorize_this_speech(variant):
    item = data((1, 2, 3))
    assert values(item, model_for(item, variant=variant)) == [True, False, False]


def test_quotation_never_executes_the_speech_or_its_claim():
    item = data((8,))
    assert item['disquotations_removed'] == 5
    assert values(item, guarded(item['document'])) == [True]


def test_permission_query_does_not_execute_the_quoted_target():
    item = data((2,)); model = model_for(item); forbidden = guarded(item['document'])
    for name in ('fa', 'fb', 'dg', 'f2', 'hzu', 'hzv', 'jzown', 'jzstandard', 'jzduty'): model[name] = forbidden[name]
    assert values(item, model) == [True]


def test_unknown_personal_content_is_not_silently_substituted():
    item = data((1,)); model = model_for(item)
    model['jzown'] = guarded(item['document'])['jzown']
    with pytest.raises(ValueError, match='Unrelated primitive'): values(item, model)


def test_the_derived_message_asserts_the_personal_content_and_is_not_a_question():
    item = data(())
    text = format_graph(item['document'], 'compact')
    actual = 'c[s[' + item['message'] + ']][k jzsubject[]]'
    content = 'c[p jzown][l[a][k jzsubject[]]]'
    item['document'] = parse(text + 'q[e[' + actual + '][j s[' + content + ']]].q[u[e[' + actual + '][j q[' + content + ']]]].')
    assert values(item, model_for(item)) == [True, True]


def test_bindings_cannot_supply_an_independently_chosen_goal_or_message():
    for key in ('message', 'goal'):
        with pytest.raises(ValueError, match='exactly'):
            bind_presentation(base()['document'], base()['bindings'] | {key: base()[key]})


def test_free_variables_are_not_captured_in_a_bound_presentation():
    with pytest.raises(ValueError):
        bind_presentation(base()['document'], base()['bindings'] | {'subject': 'v outside'})


def test_binding_preserves_the_original_document_and_criterion_description():
    original = deepcopy(base()['document'])
    bound = bind_presentation(original, base()['bindings'], message_name='jzsecondmessage', target_name='jzsecondtarget')
    assert original == base()['document']
    assert len(bound['document']['declarations']) == len(original['declarations']) + 2
    # Different generated names do not create a silent equivalence between descriptions.
    assert bound['message'] != base()['message']
    assert parse(format_graph(bound['document'], 'compact')) == bound['document']


def test_saved_evidence_preserves_history_and_leaves_full_meaning_unverified():
    report = json.loads(REPORT.read_text(encoding='utf-8'))
    for name, digest in report['source_sha256'].items(): assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest, name
    parent = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    child = parse((ROOT / 'examples/v014/kant-public-divergent-judgments.noema').read_text(encoding='utf-8'))
    assert child['declarations'][:len(parent['declarations'])] == parent['declarations']
    assert len(child['declarations']) == len(parent['declarations']) + 5
    assert child['statements'] == parent['statements']
    assert report['new_primitives'] == report['new_author_statements'] == 0
    assert not report['alignment']['semantic_completion']
    assert report['verified_full_units'] == {'kant-1784': 0, 'einstein-1905': 0}
