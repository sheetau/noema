import hashlib
import json

from noema.grammar import parse
from noema.finite_semantics import evaluate_document
from scripts.check_public_deliberation import (REPORT, setup, model_for, values, DOMAIN, SCENES,
    EXTRA, REFS, candidate, k, continuation_setup, continuation_model)
from scripts.compose_public_deliberation import ROOT, PARENT, PROPOSAL


def core(): return (ROOT / 'examples/v014/public-deliberation-core.noema').read_text(encoding='utf-8')


def test_all_retained_warranted_information_needs_public_grounding():
    doc = setup(core(), 'review'); model = model_for(doc)
    model['jxdisclosed'] = lambda audience, claim, point: (audience, claim, point) == ('audience', 'q', 'after')
    assert values(doc, model, DOMAIN, SCENES) == [True, False]


def test_public_new_information_cannot_compensate_for_lost_old_information():
    doc = setup(core(), 'review'); model = model_for(doc)
    model['jxcorpus'] = lambda holder, claim, stage: holder == 'issuer' and (
        (claim, stage) == ('p', 'before') or (claim, stage) == ('q', 'after'))
    assert values(doc, model, DOMAIN, SCENES) == [True, False]


def test_a_second_method_can_guarantee_success_despite_first_methods_failure():
    doc = setup(core(), 'proposal'); model = model_for(doc, variant='mixed_outcomes')
    model['jxavailable'] = lambda group, plan, point: group == 'office' and plan in ('channel', 'topic') and point == 'after'
    model['jxoutcomes'] = lambda group, plan, start, end: group == 'office' and start == 'after' and (
        plan == 'channel' and end in ('success', 'failure') or plan == 'topic' and end == 'success')
    assert values(doc, model, DOMAIN, SCENES) == [True, True, True]


def test_proposal_description_is_not_replaced_by_an_alias_with_same_truth():
    refs = dict(REFS, proposal='r[k jxothergoal[]]')
    doc = candidate(core(), EXTRA + 'q[' + k('rko', *(refs[n] for n, _ in PROPOSAL)) + '].')
    assert values(doc, model_for(doc), DOMAIN, SCENES) == [False]


def test_another_result_cannot_reselect_the_people_who_must_participate():
    doc = setup(core(), 'proposal'); model = model_for(doc)
    original = model['jxmembers']
    model['jxmembers'] = lambda group, person, point: (group == 'office' and person in ('person', 'other', 'reader')) if point == 'after' else original(group, person, point)
    participation = model['jxparticipates']
    model['jxparticipates'] = lambda person, act, point: person != 'reader' and participation(person, act, point)
    assert values(doc, model, DOMAIN, SCENES) == [False] * 3


def test_same_population_can_itself_be_the_proposing_group():
    doc = continuation_setup(core()); model = continuation_model(doc)
    model['jxgroup'] = lambda: 'issuer'
    model['jxavailable'] = lambda group, plan, point: (group, plan, point) == ('issuer', 'channel', 'after')
    model['jxoutcomes'] = lambda group, plan, start, end: (group, plan, start, end) == ('issuer', 'channel', 'after', 'success')
    # Raw membership lists a third person; the continuation's own citizens
    # relation fixes the population when group and population are identical.
    participation = model['df']
    model['df'] = lambda person, act, point: person != 'reader' and participation(person, act, point)
    # The full public group causes this nested finite model to explore more
    # bindings than the shared eight-million-step fixture allowance.
    rows = evaluate_document(doc, primitives=model, individuals=DOMAIN, situations=SCENES,
        max_steps=24_000_000, memoize_definitions=True, memoize_expressions=True)
    assert [row['value'] for row in rows] == [True] * 3


def test_saved_evidence_pins_current_sources_without_changing_author_claims():
    result = json.loads(REPORT.read_text(encoding='utf-8'))
    for name, digest in result['source_sha256'].items():
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest, name
    parent = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    child = parse((ROOT / 'examples/v014/kant-public-deliberation.noema').read_text(encoding='utf-8'))
    assert child['declarations'][:len(parent['declarations'])] == parent['declarations']
    assert len(child['declarations']) == len(parent['declarations']) + 10
    assert child['statements'] == parent['statements'] and len(child['statements']) == 15
    assert result['new_primitives'] == result['new_author_statements'] == 0
    assert not result['alignment']['semantic_completion']
    assert result['verified_full_units'] == {'kant-1784': 0, 'einstein-1905': 0}
