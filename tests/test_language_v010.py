from dataclasses import replace
from pathlib import Path

import pytest

from noema.discourse import definition_audit
from noema.finite_semantics import Content, Message, evaluate_document
from noema.grammar import parse, format_graph
from noema.language import convert
from noema.meaning_basis import audit_basis
from noema.render import render
from noema.script import encode, decode
from noema.semantics import normalize


def evaluate(text, primitives=None, **kwargs):
    return evaluate_document(parse(text), individuals=['reader'], situations=['now', 'later'],
                             primitives=primitives or {}, **kwargs)


def test_force_is_not_truth_and_referencing_directive_does_not_perform_it():
    prefix = 'j:r aa[d] c.r ab[f] c.d ba[] e[b scene[k aa[v scene]]].'
    result = evaluate(prefix + 's[k ab[j m[k ba[]]]].l[j m[k ba[]]].l[j s[k ba[]]].l[j q[k ba[]]].',
                      {'aa': lambda s: s == 'later', 'ab': lambda message: message.force == 'direct'})
    assert result[0] == {'kind': 'assert', 'value': True}
    assert [x['kind'] for x in result] == ['assert', 'perform', 'perform', 'perform']
    assert [x['value'].force for x in result[1:]] == ['direct', 'assert', 'ask']
    assert all(x['value'].content == Content(('now', 'later'), (False, True)) for x in result[1:])


def test_shared_content_does_not_collapse_force_and_content_projection_does_not_execute():
    text = ('j:r aa[d] c.d ba[] e[b w[k aa[v w]]].'
            's[u[e[j s[k ba[]]][j m[k ba[]]]]].'
            's[e[o[j q[k ba[]]]][o[j m[k ba[]]]]].')
    assert evaluate(text, {'aa': lambda s: False}) == [
        {'kind': 'assert', 'value': True}, {'kind': 'assert', 'value': True}]


def test_every_message_has_one_of_three_forces_and_a_content():
    text = ('j:s[f message f[x[e[v message][j s[o[v message]]]]'
            '[x[e[v message][j q[o[v message]]]][e[v message][j m[o[v message]]]]]]].')
    assert evaluate(text) == [{'kind': 'assert', 'value': True}]
    # Exhaustive quantification must not silently replace the full content domain.
    with pytest.raises(ValueError, match='eight'):
        evaluate_document(parse(text), individuals=['reader'], situations=tuple(range(9)), primitives={})


def test_outer_parameters_are_captured_inside_message_content():
    a = 'j:r aa[a d] c.d ba[x a] f[j m[b w[k aa[v x v w]]]].r ab[] a.l[k ba[k ab[]]].'
    b = 'j:r aa[a d] c.d ba[actor a] f[j m[b scene[k aa[v actor v scene]]]].r ab[] a.l[k ba[k ab[]]].'
    assert parse(a) == parse(b)
    result = evaluate(a, {'aa': lambda a, s: a == 'reader' and s == 'later', 'ab': lambda: 'reader'})
    assert result[0]['value'] == Message('direct', Content(('now', 'later'), (False, True)))
    assert definition_audit(parse(a))['statement_primitive_dependencies'] == [['aa', 'ab']]


def test_assumptions_remain_nested_and_do_not_change_facts_or_leak_to_siblings():
    text = ('j:r aa[] c.r ab[] c.r ac[] c.'
            'a[k aa[]][s[k ab[]].a[k ab[]][q[k ac[]].].].s[k ac[]].')
    assert evaluate(text, {'aa': lambda: False, 'ab': lambda: True, 'ac': lambda: False}) == [
        {'kind': 'suppose', 'condition_value': False, 'statements': [
            {'kind': 'assert', 'value': True},
            {'kind': 'suppose', 'condition_value': True, 'statements': [{'kind': 'ask', 'value': False}]}]},
        {'kind': 'assert', 'value': False}]
    assert definition_audit(parse(text))['statement_primitive_dependencies'] == [['aa', 'ab', 'ac'], ['ac']]
    # A quantifier in a hypothesis does not introduce a witness outside itself.
    with pytest.raises(ValueError, match='Free variable'):
        parse('j:a[g x a[e[v x][v x]]][s[e[v x][v x]].].')


def test_conditional_directive_example_does_not_assert_compliance():
    text = Path('examples/v010/conditional-directive.noema').read_text(encoding='utf-8')
    for rain in (False, True):
        result = evaluate(text, {'aa': lambda s: rain, 'ab': lambda actor, s: False,
                                 'ac': lambda: 'reader', 'ad': lambda: 'now'})
        assert result == [
            {'kind': 'suppose', 'condition_value': rain, 'statements': [
                {'kind': 'perform', 'value': Message('direct', Content(('now', 'later'), (False, False)))}]},
            {'kind': 'ask', 'value': False}]


def test_kant_motto_mentions_goal_directed_courage_without_claiming_either_goal_is_met():
    import json
    text = Path('examples/v010/kant-motto-draft.noema').read_text(encoding='utf-8')
    audit = audit_basis(parse(text), json.loads(Path('data/kant-motto-basis-v1.json').read_text(encoding='utf-8')))
    assert audit['primitive_count'] == 7 and audit['definition_count'] == 3
    seen = []
    def courage(person, goal, scene):
        seen.append((person, goal))
        return False
    result = evaluate(text, {
        'ab': lambda faculty, person, scene: True,
        'ac': lambda person, faculty, act, scene: scene == 'later',
        'ad': lambda guide, person, act, scene: False,
        'al': courage,
        'am': lambda message, subject: message == Message('direct', Content(('now', 'later'), (False, False))),
        'an': lambda: 'reader', 'ao': lambda: 'reader'})
    assert result == [{'kind': 'assert', 'value': True}]
    assert seen and all(pair == ('reader', Content(('now', 'later'), (False, True))) for pair in seen)


@pytest.mark.parametrize('text', [
    'i:r aa[] f.',
    'i:l[j m[b w[e[v w][v w]]]].',
    'j:l[j x[b w[e[v w][v w]]]].',
    'j:l[j m[e[n p b b][n p b b]]].',
    'j:s[j m[b w[e[v w][v w]]]].',
    'j:l[b w[e[v w][v w]]].',
    'j:s[u[j m[b w[e[v w][v w]]]]].',
    'j:l[j m[o[b w[e[v w][v w]]]]].',
    'j:a[n p b b][s[e[n p b b][n p b b]].].',
    'j:a[e[n p b b][n p b b]][].',
    'j:a[e[n p b b][n p b b]][r aa[] c.].',
    'i:a[e[n p b b][n p b b]][s[e[n p b b][n p b b]].].',
    'j:l[j m["untranslated imperative"]].',
])
def test_message_and_scope_type_errors_rejected(text):
    with pytest.raises(ValueError):
        parse(text)


def test_primitive_message_interpretations_are_checked_recursively():
    good = Message('direct', Content(('now', 'later'), (False, True)))
    for bad in (False, replace(good, force='unknown'), replace(good, content=False),
                replace(good, content=Content(('elsewhere',), (True,))),
                replace(good, content=Content(('now', 'later'), (1, 0))),
                replace(good, content=Content(('now', 'later'), [False, True]))):
        with pytest.raises(ValueError, match='sort'):
            evaluate('j:r aa[] f.l[k aa[]].', {'aa': lambda: bad})


def test_roundtrip_native_glyphs_and_edition_conversion():
    for path in Path('examples/v010').glob('*.noema'):
        doc = parse(path.read_text(encoding='utf-8'))
        for notation in ('full', 'compact'):
            text = format_graph(doc, notation)
            assert parse(text) == doc
            for alphabet in ('v1', 'v2'):
                assert parse(decode(encode(text, alphabet))) == doc
                assert 'Noema 0.10' in render(text, alphabet=alphabet)
        for version in ('0.8', '0.9'):
            with pytest.raises(ValueError):
                convert(doc, version)
    for old in ('h:s[e[n p b b][n p b b]].', 'i:r aa[] e.r ab[] d.q[t[k aa[]][k ab[]]].'):
        doc = parse(old)
        assert convert(convert(doc, '0.10'), doc['schema_version']) == doc


def test_assumption_depth_and_extra_json_fields_are_rejected():
    truth = 'e[n p b b][n p b b]'
    with pytest.raises(ValueError, match='nesting'):
        parse('j:' + ('a[' + truth + '][') * 130 + 's[' + truth + '].' + '].' * 130)
    doc = parse('j:a[' + truth + '][s[' + truth + '].].')
    doc['statements'][0]['untranslated'] = 'hidden meaning'
    with pytest.raises(ValueError, match='fields'):
        normalize(doc)
