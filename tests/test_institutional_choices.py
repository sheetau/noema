import hashlib
import json

import pytest

from noema.grammar import parse, format_graph
from scripts.check_assessed_payments import description
from scripts.check_public_assessment import syntax
from scripts.check_institutional_choices import (
    ROOT, PARENT, REPORT, DOMAIN, SCENES, assemble, setup, model_for, values,
)


def core():
    return (ROOT / 'examples/v014/institutional-choices-core.noema').read_text(encoding='utf-8')


@pytest.mark.parametrize('bindings, expected', [
    (('alice', 'beta', 'old'), True),
    (('bob', 'beta', 'old'), True),
    (('beta', 'alice', 'old'), False),
    (('alice', 'old', 'beta'), False),
    (('old', 'old', 'old'), True),
    ((), False),
    (('beta', 'old'), False),
    (('alice', 'beta', 'old', 'new'), False),
])
def test_three_slots_preserve_order_repetition_and_exact_length(bindings, expected):
    data = assemble(core()); doc = data['document']
    sequence = 'l[a][' + ' '.join('k jnslot' + chr(97 + i) + '[]' for i in range(len(bindings))) + ']'
    declarations = ''.join('r jnslot' + chr(97 + i) + '[] a.' for i in range(len(bindings)))
    doc = parse(format_graph(doc, 'compact') + declarations +
        'q[t[c[' + data['base_text'] + '][' + sequence + ']][k jncontext[]]].')
    data['document'] = doc; model = model_for(data)
    model['jnstate'] = lambda community, institution, point: (community, institution) in (('beta', 'old'), ('old', 'old'))
    for i, item in enumerate(bindings): model['jnslot' + chr(97 + i)] = lambda item=item: item
    assert values(doc, model, DOMAIN, SCENES) == [expected]


def test_agreement_can_precede_implementation():
    data = setup(core(), True); model = model_for(data)
    assert not model['jnstate']('alpha', 'new', 'now')
    assert values(data['document'], model, DOMAIN, SCENES) == [True, True]


def test_unselected_community_members_need_not_join_the_agreement():
    data = setup(core(), True); model = model_for(data)
    model['jnmembers'] = lambda community, person, point: community == 'alpha' and person in ('alice', 'bob', 'plan')
    assert not model['jnparties']('plan', 'now')
    assert values(data['document'], model, DOMAIN, SCENES) == [True, True]
    model['aa'] = lambda person: person == 'alice'
    assert values(data['document'], model, DOMAIN, SCENES) == [False, False]


def test_equivalent_alias_cannot_replace_the_recorded_terms():
    data = setup(core(), True); model = model_for(data)
    alias = syntax(description(data['document'], 'k jnalias[]'))
    assert alias != data['terms_syntax']
    model['jnassigned'] = lambda agreement, desc, point: agreement == 'pact' and desc.syntax == alias
    assert values(data['document'], model, DOMAIN, SCENES) == [False, True]


def test_unknown_future_configuration_is_not_assumed_to_persist():
    data = assemble(core()); doc = data['document']
    doc = parse(format_graph(doc, 'compact') +
        'q[t[c[' + data['terms_text'] + '][l[a][k jnperson[] k jncommunity[] k jnolder[]]]][k jncontext[]]].')
    data['document'] = doc; model = model_for(data); state = model['jnstate']
    def unknown(community, institution, point):
        if point == 'later': raise ValueError('Unknown later configuration')
        return state(community, institution, point)
    model['jnstate'] = unknown
    with pytest.raises(ValueError, match='Unknown later configuration'):
        values(doc, model, DOMAIN, SCENES)


def test_history_and_evidence_do_not_claim_whole_source_completion():
    result = json.loads(REPORT.read_text(encoding='utf-8'))
    for name, digest in result['source_sha256'].items():
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest, name
    parent = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    child = parse((ROOT / 'examples/v014/kant-institutional-choices.noema').read_text(encoding='utf-8'))
    assert child['declarations'][:len(parent['declarations'])] == parent['declarations']
    assert len(child['declarations']) == len(parent['declarations']) + 10
    assert child['statements'] == parent['statements']
    assert result['new_primitives'] == result['new_author_statements'] == 0
    assert not result['alignment']['semantic_completion']
    assert result['verified_full_units'] == {'kant-1784': 0, 'einstein-1905': 0}
