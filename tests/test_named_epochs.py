import hashlib
import json

import pytest

from noema.finite_semantics import Content
from noema.grammar import parse, format_graph
from scripts.check_rod_setup import guarded
from scripts.check_named_epochs import ROOT, REPORT, PARENT, SCENES, REFS, EPONYM, setup, source_setup, finish, generic_model, source_model, values
from scripts.compose_limits import call as k


def data(source=False):
    stem = 'named-epochs-core' if source else 'named-epochs'
    text = (ROOT / ('examples/v014/' + stem + '.noema')).read_text(encoding='utf-8')
    return source_setup(text) if source else setup(text)


def test_two_false_descriptions_can_still_be_used_as_labels():
    item = data()
    assert values(item, generic_model(item, (False, False, True, True))) == [True, True, True, False, False, False, False]


def test_a_label_does_not_transfer_a_future_classification_to_now():
    item = data(); model = generic_model(item)
    model['jsaspect'] = lambda person: Content(SCENES, (False, False, True))
    assert values(item, model) == [True, True, True, False, True, False, False]


def test_ambiguous_epoch_reference_does_not_choose_an_arbitrary_referent():
    item = data(); model = generic_model(item)
    model['jsreferent'] = lambda person: Content(SCENES, (person in ('epoch', 'other'),) * 3)
    assert values(item, model) == [True, True, False, False, True, True, False]


def test_the_claimed_epoch_must_belong_to_the_explicit_reference_scope():
    item = data(); model = generic_model(item)
    model['jsscope'] = lambda person: person == 'other'
    assert values(item, model) == [True, True, False, False, True, True, False]


@pytest.mark.parametrize('variant', ['ambiguous', 'empty_people'])
def test_nonunique_or_missing_persons_are_not_identified(variant):
    item = data()
    assert values(item, generic_model(item, variant=variant)) == [False, True, True, True, True, True, False]


def test_the_same_years_in_another_office_do_not_identify_this_person():
    item = data(); model = generic_model(item)
    model['jsoffice'] = lambda: 'other'
    assert values(item, model) == [False, True, True, True, False, True, False]


def test_matching_truth_values_do_not_transfer_a_naming_record_to_an_alias():
    original = data(); base = original['document']; base['statements'] = []
    base = parse(format_graph(base, 'compact') + 'd jsalias[] h[a] e[p jsaspect].')
    alias = finish(base, REFS, 'k jsalias[]', k('rmw', *(REFS[n] for n, _ in EPONYM)))
    assert values(alias, generic_model(original)) == [True, False, False, False, True, True, False]
    assert values(alias, generic_model(alias)) == [True] * 7


def test_repeating_one_description_is_not_two_distinct_descriptions():
    original = data(); base = original['document']; base['statements'] = []
    same = finish(base, REFS, 'p jsaspect', 'p jsaspect')
    assert values(same, generic_model(same)) == [True, False, False, False, True, True, False]


def test_another_authors_record_is_not_attributed_to_this_author():
    item = data(); model = generic_model(item)
    model['jsauthor'] = lambda: 'ruler'
    assert values(item, model) == [True, False, False, False, True, True, False]


def test_label_use_does_not_execute_the_unknown_descriptions():
    item = data(); model = generic_model(item)
    item['document']['statements'] = [item['document']['statements'][1]]
    limited = guarded(item['document'])
    for name in ('jsnode', 'jsauthor', 'jscontext', 'jspresents'):
        limited[name] = model[name]
    assert values(item, limited) == [True]


def test_unknown_person_records_are_refused_instead_of_assumed_unique():
    item = data(); model = generic_model(item)
    def unknown(*args): raise ValueError('Tenure record unknown')
    model['jstenures'] = unknown
    with pytest.raises(ValueError, match='Tenure record unknown'):
        values(item, model)


def test_an_eponym_does_not_require_an_exact_hundred_year_period():
    # The epoch is one model situation; no year duration is postulated.
    item = data()
    assert values(item, generic_model(item))[4] is True


def test_incorrect_tenure_years_do_not_identify_the_source_person():
    item = data(True)
    assert values(item, source_model(item, 'wrong_year')) == [False, True, True, True, True, True, False]


def test_a_reign_outside_the_epoch_does_not_make_the_eponym_description_true():
    item = data(True)
    assert values(item, source_model(item, 'no_overlap')) == [True, True, True, True, False, True, False]


def test_saved_evidence_keeps_editorial_identification_separate_from_the_author():
    report = json.loads(REPORT.read_text(encoding='utf-8'))
    for name, digest in report['source_sha256'].items():
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest, name
    parent = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    child = parse((ROOT / 'examples/v014/kant-named-epochs.noema').read_text(encoding='utf-8'))
    assert child['declarations'][:len(parent['declarations'])] == parent['declarations']
    assert len(child['declarations']) == len(parent['declarations']) + 10
    assert child['statements'] == parent['statements']
    assert report['new_primitives'] == report['new_author_statements'] == 0
    assert not report['alignment']['semantic_completion']
    assert report['verified_full_units'] == {'kant-1784': 0, 'einstein-1905': 0}
    assert report['reference_evidence']['status'].startswith('editorial_reference_profile')
