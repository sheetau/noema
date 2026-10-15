from copy import deepcopy
import pytest

from noema.constructed import parse, format_graph
from noema.script import transcribe
from scripts.check_integrated_qualification import fixture, values
from scripts.compose_armed_readiness import ROOT, SOURCE


def test_stored_qualification_and_all_five_components_hold_in_one_interpretation():
    assert values(indices=tuple(range(7))) == [True] * 7


@pytest.mark.parametrize('option', ('ready', 'assigned', 'protected', 'owned', 'supported', 'mapped', 'remaining'))
def test_removing_one_required_component_breaks_the_combined_qualification(option):
    assert values(**{option: False}) == [False]


def test_no_utterance_is_not_evidence_that_all_qualifications_hold():
    # The source asserts a necessary condition (can -> eligible), not its converse.
    assert values(success=False, remaining=False) == [True]


@pytest.mark.parametrize('variant', ('different_members', 'different_assigned_community',
    'different_protected_community', 'different_commander'))
def test_identity_and_scope_mismatches_are_detected_across_components(variant):
    assert values(variant=variant) == [False]


@pytest.mark.parametrize('variant', ('unknown_mission', 'unknown_protection', 'unknown_remaining', 'unknown_mapping'))
def test_unknown_relevant_inputs_are_quotable_but_cannot_be_completed(variant):
    assert values(indices=(1,), variant=variant) == [True]
    with pytest.raises(ValueError, match='Unknown integrated input'):
        values(variant=variant)


def test_qualification_definitions_are_actual_stored_definitions_and_scripts_roundtrip():
    doc, _ = fixture()
    source = parse((ROOT / SOURCE).read_text(encoding='utf-8'))
    definitions = {d['name']: d for d in source['declarations']}
    replacements = {'rtx', 'rvy', 'hzxtasks', 'hzxcommandcodes',
                    'hztcontextfor', 'hzthearersfor', 'hztspeakerfor'}
    for decl in doc['declarations']:
        if decl['name'] in definitions and decl['name'] not in replacements:
            assert decl == definitions[decl['name']], decl['name']
    original = deepcopy(doc)
    for notation in ('full', 'compact'):
        text = format_graph(doc, notation)
        assert parse(text) == doc == original
        assert parse(transcribe(text, alphabet='v2')) == doc


def test_default_eager_interpreter_remains_explicitly_budget_limited():
    with pytest.raises(ValueError, match='step budget'):
        values(short_circuit=False)
