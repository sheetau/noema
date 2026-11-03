from copy import deepcopy

import pytest

from scripts.check_kant_public_fragment import cases, checked, canonical
from scripts.kant_public_fragment import (
    compile_statement, decode, events, forms, table, words, GRAMMAR, feature, reserved_forms, root_words,
)
from scripts.kant_geometry_reader import read_geometry
from scripts.visible_syntax_geometry import to_svg, from_svg
from scripts.check_visible_syntax import call, logic, quant, variable, quote


@pytest.mark.parametrize('index', range(len(cases())))
@pytest.mark.parametrize('branch', [True, False])
def test_actual_svg_to_exact_native_syntax(index, branch):
    row = checked(index, branch)
    assert row['compiled']['shapes']
    if not branch:
        assert all(g['side'] is None for g in row['compiled']['groups'])


@pytest.mark.parametrize('a,b', [
    ('rain-town','rain-home'), ('above','above-reversed'), ('give','give-reversed'),
    ('and-left','and-right'), ('equal','equal-reversed'), ('quote-inner-not','quote-outer-not'),
    ('not-all','all-not'), ('binding-outer-inner','binding-inner-outer'),
    ('binding-outer-inner','binding-inner-inner'), ('binding-outer-outer','binding-inner-inner'),
])
def test_distinguishing_geometry(a, b):
    indices = {row[0]:i for i,row in enumerate(cases())}
    left, right = checked(indices[a]), checked(indices[b])
    assert left['svg'] != right['svg']
    assert left['source'] != right['source']


def test_every_public_allograph_is_unique_and_legal():
    for token in (*root_words(), *GRAMMAR):
        for form in forms(token):
            geometry = read_geometry(from_svg(to_svg(form['shapes'])))
            assert table()[feature(geometry, range(len(geometry['circles'])))] == token


def test_other_published_roots_are_reserved_not_reassigned_to_grammar():
    from scripts.visible_lexical_script import _glyph
    assert len(root_words()) == 30
    for form in reserved_forms().values():
        geometry = read_geometry(_glyph(form)['shapes'])
        assert table()[feature(geometry, range(len(geometry['circles'])))] in root_words()


def test_reader_does_not_use_writer_or_svg_element_order(monkeypatch):
    row = checked(4)
    def fail(*args, **kwargs):
        raise AssertionError('Writer is not an inverse oracle')
    monkeypatch.setattr('scripts.kant_public_fragment.compile_statement', fail)
    shapes = []
    for s in reversed(from_svg(row['svg'])):
        if s['kind'] == 'circle':
            shapes.append(s)
        else:
            x, y = (s['x1']+s['x2'])/2, (s['y1']+s['y2'])/2
            shapes += [dict(kind='line',x1=s['x2'],y1=s['y2'],x2=x,y2=y),
                       dict(kind='line',x1=x,y1=y,x2=s['x1'],y2=s['y1'])]
    assert decode(shapes) == row['source']


def test_quote_can_use_visible_or_silent_entry():
    index = next(i for i,c in enumerate(cases()) if c[0] == 'quote')
    assert checked(index, True, False)['source'] == checked(index)['source']
    assert checked(index, True, False)['svg'] != checked(index)['svg']


def test_source_scope_and_type_errors_are_rejected():
    invalid = [
        dict(kind='assert',body=quant('forall','x',logic('equal',quote(variable('x')),quote(call('home'))))),
        dict(kind='assert',body=call('rain',call('rain',call('home')))),
        dict(kind='assert',body=call('rain',variable('missing'))),
        canonical(quant('forall','x',quant('exists','y',quant('forall','z',call('rain',variable('z')))))),
    ]
    for source in invalid:
        with pytest.raises(ValueError):
            compile_statement(source)


def test_unknown_words_and_trailing_ink_are_rejected():
    shapes = deepcopy(checked(0)['compiled']['shapes'])
    shapes.append(dict(kind='line',x1=2000.,y1=32.,x2=2040.,y2=32.))
    with pytest.raises(ValueError):
        decode(shapes)
    bad = deepcopy(checked(0)['source'])
    bad['body']['symbol'] = 'unknown'
    with pytest.raises(ValueError):
        compile_statement(bad)


def test_branch_slot_is_public_not_the_middle_of_leaf_candidates():
    # Three arguments: the middle slot alone is eligible, and the parser knows
    # that slot from the public arity before reading the child expressions.
    from scripts.check_visible_syntax import assertion
    source = assertion(call('give',call('home'),call('town'),call('book')))
    event = events(source)[0]
    assert event['side'] == source['body']['arguments'][1]['symbol']


def test_cached_and_uncached_small_corpus_agree():
    for index in (0, 1, 18, 23):
        assert checked.__wrapped__(index) == checked(index)
