from fractions import Fraction
from itertools import product
from pathlib import Path

import pytest

from noema.discourse import definition_audit
from noema.grammar import parse, format_graph
from noema.semantics import normalize
from noema.script import encode, decode
from noema.render import render


def interpret(doc, domain, primitives):
    """Independent finite interpretation for scope tests, not a theorem prover."""
    defs = {d['name']: d for d in doc['declarations'] if d['kind'] == 'definition'}

    def expr(e, env):
        k = e['kind']
        if k == 'variable':
            return env[e['name']]
        if k == 'number':
            return Fraction(e['numerator'], e['denominator'])
        if k == 'call':
            args = [expr(a, env) for a in e['arguments']]
            if e['symbol'] in defs:
                d = defs[e['symbol']]
                return expr(d['body'], {p['name']: a for p, a in zip(d['parameters'], args, strict=True)})
            return primitives[e['symbol']](*args)
        if k in ('forall', 'exists'):
            values = [expr(e['body'], {**env, e['variable']: v}) for v in domain[e['sort']]]
            return all(values) if k == 'forall' else any(values)
        args = [expr(a, env) for a in e['arguments']]
        if k == 'not':
            return not args[0]
        a, b = args
        return {'and': lambda: a and b, 'or': lambda: a or b, 'implies': lambda: not a or b,
                'iff': lambda: a == b, 'equal': lambda: a == b}[k]()
    return [expr(s['body'], {}) for s in doc['statements']]


def test_open_definitions_roundtrip_without_models_or_registered_concepts():
    text = Path('examples/v08/definitions.noema').read_text(encoding='utf-8')
    doc = parse(text)
    assert doc == normalize(doc)
    assert definition_audit(doc) == {'primitive_symbols': ['aa', 'ab'],
        'definition_primitive_dependencies': {'ba': ['aa', 'ab'], 'bb': ['ab']},
        'statement_primitive_dependencies': [['aa', 'ab'], ['ab']]}
    for notation in ('full', 'compact'):
        assert parse(format_graph(doc, notation)) == doc
        assert parse(decode(encode(text, 'v2', notation))) == doc
        assert 'Noema 0.8' in render(text, alphabet='v2', notation=notation)


def test_quantifier_order_and_negation_have_different_truth_conditions():
    prefix = 'h:r aa[a a] c.'
    texts = ['s[f x a[g y a[k aa[v x v y]]]].', 's[g y a[f x a[k aa[v x v y]]]].',
             's[u[f x a[g y a[k aa[v x v y]]]]].']
    results = [interpret(parse(prefix + t), {'individual': [0, 1]}, {'aa': lambda x, y: x == y})[0] for t in texts]
    assert results == [True, False, False]


def test_shadowed_variable_and_alpha_renaming_preserve_scope():
    left = parse('h:s[f x a[g x a[e[v x][v x]]]].')
    right = parse('h:s[f outer a[g inner a[e[v inner][v inner]]]].')
    assert left == right
    assert interpret(left, {'individual': [0, 1]}, {}) == [True]
    assert left != parse('h:s[f x a[g y a[e[v x][v y]]]].')


def test_definition_application_agrees_with_expansion_for_every_small_relation():
    prefix = 'h:r aa[a a] c.d ab[x a y a] c[w[k aa[v x v y]][k aa[v y v x]]].'
    doc = parse(prefix + 's[f x a[f y a[z[k ab[v x v y]][w[k aa[v x v y]][k aa[v y v x]]]]]].')
    pairs = list(product([0, 1], repeat=2))
    for values in product([False, True], repeat=4):
        relation = dict(zip(pairs, values))
        assert interpret(doc, {'individual': [0, 1]}, {'aa': lambda a, b: relation[a, b]}) == [True]


def test_exact_rationals_and_functions_preserve_large_values():
    text = 'h:d aa[] b[n u c e].s[e[k aa[]][n u b c]].'
    doc = parse(text)
    assert doc['declarations'][0]['body'] == {'kind': 'number', 'numerator': -1, 'denominator': 2}
    assert interpret(doc, {}, {}) == [True]
    from noema.grammar import number_word
    large = 2 ** 100 + 1
    value = f'n p {number_word(large)} b'
    doc = parse('h:s[e[' + value + '][' + value + ']].')
    assert doc['statements'][0]['body']['arguments'][0]['numerator'] == large
    assert parse(format_graph(doc)) == doc


@pytest.mark.parametrize('text', [
    'h:s[k unknown[]].', 'h:s[e[v x][v x]].',
    'h:r aa[a] c.s[k aa[]].', 'h:r aa[a] c.s[k aa[n p b b]].',
    'h:r aa[] a.s[k aa[]].', 'h:d aa[x a] c[k aa[v x]].',
    'h:d aa[x a] c[k ab[v x]].r ab[a] c.',
    'h:r aa[a] c.r aa[a] c.', 'h:d aa[x a x a] a[v x].',
    'h:s[e[n p b a][n p b b]].', 'h:s[u[n p b b]].',
    'h:r aa[] a.s[e[k aa[]][n p b b]].',
    'h:s[e[n p b b][n p b b]].r aa[] a.',
    'h:s["untranslated source sentence"].', 'h:s[f x a[e[v x][v x]]]. trailing',
])
def test_invalid_definitions_and_scopes_are_rejected(text):
    with pytest.raises(ValueError):
        parse(text)


def test_definition_names_are_not_alpha_renamed_and_primitives_are_not_definitions():
    doc = parse('h:r aa[] a.d bb[] a[k aa[]].d cc[] a[k bb[]].s[e[k cc[]][k aa[]]].')
    assert [d['name'] for d in doc['declarations']] == ['aa', 'bb', 'cc']
    assert definition_audit(doc)['definition_primitive_dependencies']['cc'] == ['aa']


def test_deep_expressions_rejected_and_json_unknown_fields_rejected():
    with pytest.raises(ValueError, match='nesting'):
        parse('h:s[' + 'u[' * 130 + 'e[n p a b][n p a b]' + ']' * 130 + '].')
    doc = parse('h:s[e[n p a b][n p a b]].')
    doc['statements'][0]['body']['untranslated'] = 'hidden meaning'
    with pytest.raises(ValueError, match='fields'):
        normalize(doc)


def test_unsupported_edition_conversion_and_reverse_translation_reject_explicitly():
    from noema.language import convert
    from noema.translation import Translator
    text = 'h:s[e[n p b b][n p b b]].'
    doc = parse(text)
    assert convert(doc, '0.8') == doc
    for version in ('0.1', '0.5', '0.7'):
        with pytest.raises(ValueError, match='0.8'):
            convert(doc, version)
    with pytest.raises(ValueError, match='0.8'):
        convert(parse('g:po mu.'), '0.8')
    assert Translator().translate({'direction': 'from_noema', 'language': 'ja', 'text': text})['status'] == 'unsupported'


def test_synchrony_draft_preserves_two_distinct_relation_constraints():
    doc = parse(Path('examples/v08/einstein-synchrony-draft.noema').read_text(encoding='utf-8'))
    clocks = {'a', 'b', 'c'}
    domain = {'individual': ['a', 'b', 'c', 'frame']}
    identity = {(x, x) for x in clocks}
    path = {('a', 'b'), ('b', 'a'), ('b', 'c'), ('c', 'b')}
    for relation, expected in ((identity, [True, True]), (path, [True, False])):
        assert interpret(doc, domain, {'aa': lambda x: x in clocks,
            'ab': lambda x, y, frame: frame == 'frame' and (x, y) in relation,
            'ac': lambda: 'frame'}) == expected
    assert parse(format_graph(doc, 'compact')) == doc
    assert parse(decode(encode(format_graph(doc), 'v2'))) == doc
