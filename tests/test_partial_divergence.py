import hashlib
import json
import pytest
from noema.grammar import parse
from scripts.check_partial_divergence import ROOT, REPORT, PARENT, setup, select, model_for, values
from scripts.check_rod_setup import guarded


def data(indices=None, source=True):
    stem = 'partial-divergence-core' if source else 'partial-divergence'
    item = setup((ROOT / ('examples/v014/' + stem + '.noema')).read_text(encoding='utf-8'), source)
    return select(item, indices) if indices is not None else item


def test_local_difference_does_not_establish_incompatibility_or_wholesale_disagreement():
    item = data((0, 2, 4, 5, 6))
    assert values(item, model_for(item)) == [True, False, True, False, True]


def test_some_difference_does_not_require_agreement_elsewhere():
    item = data((4, 5, 6))
    assert values(item, model_for(item, (False, True, True, True, False, True))) == [True, True, False]


def test_individual_judgment_does_not_establish_institutional_adoption():
    item = data((3, 4, 5, 6))
    assert values(item, model_for(item, adopted=False)) == [True, False, False, False]


def test_adoption_does_not_establish_the_individual_judgment():
    item = data((0, 3, 4))
    assert values(item, model_for(item, judged_a=False)) == [True, False, False]


def test_the_individual_judgment_need_not_be_true_now():
    item = data((3, 7))
    assert values(item, model_for(item)) == [True, False]


def test_individually_satisfiable_opposites_have_no_common_witness():
    item = data((0, 1, 2))
    assert values(item, model_for(item, (True, False, False, True, True, True))) == [True, False, True]


def test_an_unsatisfiable_side_is_not_evidence_of_opposition():
    item = data((0, 2))
    assert values(item, model_for(item, (False, False, False, True, True, True))) == [True, False]


def test_empty_comparisons_establish_neither_difference_agreement_nor_opposition():
    item = data((0, 1, 2, 4, 6))
    assert values(item, model_for(item, variant='empty_comparisons')) == [False] * 5


def test_empty_issues_do_not_establish_universal_disagreement():
    item = data((4, 5, 6))
    assert values(item, model_for(item, variant='empty_issues')) == [False] * 3


def test_difference_outside_the_selected_comparisons_is_not_counted():
    item = data((0, 1, 2, 4))
    assert values(item, model_for(item, (True,) * 6, variant='outside_difference')) == [False, True, False, False]


@pytest.mark.parametrize('variant', ('other_person', 'other_subject', 'wrong_binding', 'wrong_judgment_description', 'empty_candidates'))
def test_personal_judgments_require_the_same_person_issue_description_and_nonempty_candidates(variant):
    item = data((3, 4, 6))
    assert values(item, model_for(item, variant=variant)) == [False] * 3


@pytest.mark.parametrize('variant', ('other_organization', 'other_adoption_time', 'other_adopted_description'))
def test_adoption_is_not_transferred_between_organizations_times_or_equal_valued_descriptions(variant):
    item = data((3, 4))
    assert values(item, model_for(item, variant=variant)) == [True, False]


def test_closed_quotation_does_not_execute_judgment_or_adoption():
    item = data((8,))
    assert item['disquotations_removed'] > 0
    assert values(item, guarded(item['document'])) == [True]


def test_unknown_standard_content_is_not_filled_with_false():
    item = data((0,)); model = model_for(item)
    model['jystandard'] = guarded(item['document'])['jystandard']
    with pytest.raises(ValueError, match='Unrelated primitive'): values(item, model)


def test_agreement_within_the_range_does_not_compare_description_spellings():
    item = data((0, 1))
    assert item['own_syntax'] != item['standard_syntax']
    assert values(item, model_for(item, (True,) * 6)) == [False, True]


def test_saved_evidence_preserves_history_and_does_not_claim_a_completed_unit():
    report = json.loads(REPORT.read_text(encoding='utf-8'))
    for name, digest in report['source_sha256'].items(): assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest, name
    parent = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    child = parse((ROOT / 'examples/v014/kant-partial-divergence.noema').read_text(encoding='utf-8'))
    assert child['declarations'][:len(parent['declarations'])] == parent['declarations']
    assert len(child['declarations']) == len(parent['declarations']) + 9
    assert child['statements'] == parent['statements']
    assert report['new_primitives'] == report['new_author_statements'] == 0
    assert not report['alignment']['semantic_completion']
    assert report['verified_full_units'] == {'kant-1784': 0, 'einstein-1905': 0}
    segment = report['alignment']['segments'][0]
    unit = next(u for u in json.loads((ROOT / 'artifacts/written-units-v1/kant-1784.json').read_text(encoding='utf-8'))['units'] if u['id'] == segment['unit'])
    start, end = segment['range']
    assert unit['text'][start:end] == segment['text'] == 'vom angenommenen Symbol hier oder da abweichenden Urtheile'
