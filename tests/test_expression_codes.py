from copy import deepcopy

import pytest

from noema.constructed import parse, format_graph
from noema.constructed_discourse import function_sort, sequence_sort, question_sort, description_sort
from noema.constructed_semantics import evaluate_document
from noema.expression_codes import encode_expression, decode_expression, is_template_code
from noema.script import transcribe


def quote(body, rank=0): return {'kind': 'quote', 'body': body, **({'rank': rank} if rank else {})}
def ref(name): return {'kind': 'function_ref', 'symbol': name}
def call(name): return {'kind': 'call', 'symbol': name, 'arguments': []}


SIGNATURES = [
    ([], 'content'),
    (['individual'], 'content'),
    (['individual', 'individual'], 'truth'),
    (['individual', 'number', 'situation'], 'content'),
    ([function_sort(['individual'], 'content'), sequence_sort('number'), question_sort(['individual'])], 'message'),
    ([description_sort('content'), 'truth'], sequence_sort('individual')),
]


def fixture(parameters, result):
    return dict(schema_version='0.16', lexicon_version='0.16', declarations=[
        dict(kind='primitive', name='template', parameters=parameters, result=result)], statements=[])


@pytest.mark.parametrize('parameters,result', SIGNATURES)
def test_any_typed_function_arity_roundtrips_without_interpretation(parameters, result):
    doc = fixture(parameters, result); before = deepcopy(doc)
    type_ = function_sort(parameters, result); original = quote(ref('template'))
    code = encode_expression(doc, original, type_)
    assert decode_expression(doc, code) == (type_, original)
    assert is_template_code(doc, code)
    assert doc == before
    trial = {**doc, 'statements': [dict(kind='ask', body=dict(kind='equal', arguments=[code, code]))]}
    def forbidden(*args): raise AssertionError('Encoding executed a template')
    assert evaluate_document(trial, individuals=('person',), situations=('now',), primitives={'template': forbidden})[0]['value']
    for style in ('compact', 'full'):
        text = format_graph(trial, style)
        assert parse(text) == parse(transcribe(text, alphabet='v2'))


def test_all_types_can_be_encoded_but_only_functions_are_templates():
    doc = parse('p:r person[] a.r truth[] c.')
    for name, type_ in (('person', 'individual'), ('truth', 'truth')):
        code = encode_expression(doc, quote(call(name)), type_)
        assert decode_expression(doc, code) == (type_, quote(call(name)))
        assert not is_template_code(doc, code)
    assert not is_template_code(doc, quote({'kind': 'equal', 'arguments': [call('person'), call('person')]}))


def test_alpha_normalization_and_no_capture_or_beta_reduction():
    doc = parse('p:r person[] a.')
    first = quote(dict(kind='lambda', parameters=[dict(name='term', sort='individual')], body=dict(kind='variable', name='term')))
    second = quote(dict(kind='lambda', parameters=[dict(name='different', sort='individual')], body=dict(kind='variable', name='different')))
    type_ = function_sort(['individual'], 'individual')
    code = encode_expression(doc, first, type_)
    assert code == encode_expression(doc, second, type_)
    recovered_type, recovered = decode_expression(doc, code)
    assert recovered_type == type_ and recovered['body']['kind'] == 'lambda'
    assert recovered['body']['parameters'][0]['name'] == recovered['body']['body']['name']
    assert code['body']['function']['parameters'][0]['name'] != code['body']['arguments'][0]['parameters'][0]['name']
    assert code['body']['kind'] == 'apply'


def test_same_denotation_does_not_merge_codes_or_function_spellings():
    doc = parse('p:r first[a] c.r second[a] c.d alias[x a] c[k first[v x]].')
    type_ = function_sort(['individual'], 'truth')
    codes = [encode_expression(doc, quote(ref(name)), type_) for name in ('first', 'second', 'alias')]
    trial = {**doc, 'statements': [dict(kind='ask', body=dict(kind='equal', arguments=[codes[0], code])) for code in codes[1:]]}
    results = evaluate_document(trial, individuals=('person',), situations=('now',), primitives={'first': lambda x: True, 'second': lambda x: True})
    assert [r['value'] for r in results] == [False, False]


def test_rank_is_preserved_and_never_erased_by_the_common_type():
    doc = parse('p:d low[] i[c][r[e[n p a b][n p a b]]].d high[] c[s[k low[]]].')
    type_ = function_sort([], 'truth')
    original = quote(ref('high'), 1)
    code = encode_expression(doc, original, type_)
    assert code['rank'] == 1 and decode_expression(doc, code) == (type_, original)
    with pytest.raises(ValueError, match='strictly lower ranks'):
        encode_expression(doc, quote(ref('high')), type_)
    wrong = deepcopy(code); wrong.pop('rank')
    with pytest.raises(ValueError, match='strictly lower ranks'): decode_expression(doc, wrong)


@pytest.mark.parametrize('bad_type', ['truth', function_sort([], 'truth'), function_sort(['number'], 'truth')])
def test_wrong_supplied_type_is_rejected(bad_type):
    doc = parse('p:r template[a] c.')
    with pytest.raises(ValueError): encode_expression(doc, quote(ref('template')), bad_type)


@pytest.mark.parametrize('change', ['wrong_identity', 'duplicate_argument', 'nonlambda', 'metadata'])
def test_only_the_canonical_envelope_is_accepted(change):
    doc = parse('p:r template[a] c.')
    code = encode_expression(doc, quote(ref('template')), function_sort(['individual'], 'truth'))
    if change == 'wrong_identity': code['body']['function']['body'] = dict(kind='not', arguments=[code['body']['function']['body']])
    if change == 'duplicate_argument': code['body']['arguments'] *= 2
    if change == 'nonlambda': code['body']['function'] = ref('template')
    if change == 'metadata': code['extra'] = True
    with pytest.raises(ValueError): decode_expression(doc, code)


def test_open_unknown_and_wrong_edition_inputs_are_rejected():
    doc = parse('p:r template[a] c.')
    for body in (dict(kind='variable', name='free'), ref('missing')):
        with pytest.raises(ValueError): encode_expression(doc, quote(body), 'individual')
    old = deepcopy(doc); old['schema_version'] = old['lexicon_version'] = '0.15'
    with pytest.raises(ValueError, match='explicit edition'): encode_expression(old, quote(ref('template')), function_sort(['individual'], 'truth'))


@pytest.mark.parametrize('budget', [False, 0, -1, 2, 8])
def test_construction_and_decoding_budgets_are_enforced(budget):
    doc = parse('p:r template[a] c.'); type_ = function_sort(['individual'], 'truth')
    code = encode_expression(doc, quote(ref('template')), type_)
    with pytest.raises(ValueError): encode_expression(doc, quote(ref('template')), type_, max_nodes=budget)
    with pytest.raises(ValueError): decode_expression(doc, code, max_nodes=budget)


@pytest.mark.parametrize('invalid', [None, 7, []])
def test_nonquotation_inputs_fail_explicitly(invalid):
    doc = parse('p:r template[a] c.')
    with pytest.raises(ValueError): encode_expression(doc, invalid, 'truth')
    with pytest.raises(ValueError): decode_expression(doc, invalid)
