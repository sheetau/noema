from copy import deepcopy
from itertools import permutations
import json
from pathlib import Path

import pytest

from noema.constructed import parse
from scripts.visible_lexical_script import (
    Lexicon, check_extension, compile_assertion, decode, to_svg, from_svg,
    SMALL, MEDIUM, LARGE, PITCH, _translate,
)

ROOT = Path(__file__).resolve().parents[1]


def assertion(argument='town', head='rain'):
    return {'kind': 'assert', 'body': {'kind': 'call', 'symbol': head,
            'arguments': [{'kind': 'call', 'symbol': argument, 'arguments': []}]}}


def shape(argument='town', **kwargs):
    return compile_assertion(assertion(argument), **kwargs)['shapes']


def extended():
    data = Lexicon().document()
    entry = deepcopy(data['entries']['rain'])
    entry['form']['ray'] = 'north'
    entry['meaning'] = '検査専用の別の一引数関係。降雨という意味は付与しない。'
    entry['contrast'] = ['rainとの同一視']
    data['entries']['probe'] = entry
    return Lexicon(data)


def test_original_sample_and_minimal_pair_are_recovered():
    doc = parse((ROOT/'examples/v016/branch-circle-samples.noema').read_text(encoding='utf-8'))
    assert assertion() == doc['statements'][0]
    assert shape('town') != shape('home')
    for argument in ('town', 'home'):
        assert decode(shape(argument)) == assertion(argument)
        assert decode(from_svg(to_svg(shape(argument)))) == assertion(argument)


def test_independently_drawn_shapes_are_read_without_the_compiler(monkeypatch):
    # Hand-built straight layout, not renderer output or a stored AST.
    visible = [
        dict(kind='circle', x=50., y=32., r=LARGE),
        dict(kind='line', x1=50., y1=32., x2=50., y2=32.+LARGE),
        dict(kind='circle', x=230., y=32., r=MEDIUM),
        dict(kind='circle', x=230., y=32., r=SMALL),
        dict(kind='line', x1=50.+LARGE, y1=32., x2=230.-MEDIUM, y2=32.),
    ]
    import scripts.visible_lexical_script as module
    monkeypatch.setattr(module, 'compile_assertion', lambda *a, **k: pytest.fail('Decoder used compiler'))
    assert decode(visible) == assertion('town')
    visible[3]['x'] += MEDIUM
    assert decode(visible) == assertion('home')


@pytest.mark.parametrize('argument', ['town', 'home'])
@pytest.mark.parametrize('rail', [0, 1, 2])
@pytest.mark.parametrize('separation', [140., 160., 210.])
def test_height_and_legal_routes_do_not_rename_words(argument, rail, separation):
    assert decode(shape(argument, argument_rail=rail, separation=separation)) == assertion(argument)


@pytest.mark.parametrize('factor,dx,dy', [(0.25, -100, 500), (3.7, 812.4, -321.5)])
def test_translation_scale_primitive_order_and_segment_storage(factor, dx, dy):
    visible = []
    for s in shape('home'):
        if s['kind'] == 'circle':
            visible.append(s)
        else:
            mx, my = (s['x1']+s['x2'])/2, (s['y1']+s['y2'])/2
            visible.extend([
                dict(kind='line', x1=mx, y1=my, x2=s['x1'], y2=s['y1']),
                dict(kind='line', x1=s['x2'], y1=s['y2'], x2=mx, y2=my)])
    visible = list(reversed(_translate(visible, dx, dy, factor)))
    assert decode(visible) == assertion('home')


def test_all_lexicon_orders_and_append_only_extension_preserve_forms():
    baseline = Lexicon()
    entries = baseline.document()['entries']
    expected = shape()
    for order in permutations(entries):
        data = baseline.document()
        data['entries'] = {name: entries[name] for name in order}
        lexicon = Lexicon(data)
        assert shape(lexicon=lexicon) == expected
        assert decode(expected, lexicon) == assertion()
    successor = extended()
    assert check_extension(baseline, successor)
    assert shape(lexicon=successor) == expected
    assert decode(expected, successor) == assertion()
    assert decode(compile_assertion(assertion(head='probe'), successor)['shapes'], successor) == assertion(head='probe')


def test_alias_is_canonicalized_without_allocating_another_shape():
    data = Lexicon().document()
    data['entries']['home']['aliases'] = ['residence']
    successor = Lexicon(data)
    assert check_extension(Lexicon(), successor)
    assert compile_assertion(assertion('residence'), successor)['shapes'] == shape('home')
    assert decode(shape('home'), successor) == assertion('home')


@pytest.mark.parametrize('direction', ['east', 'south', 'west', 'north'])
def test_radial_mark_is_preserved_when_it_meets_the_connection(direction):
    data = Lexicon().document()
    data['entries']['rain']['form']['ray'] = direction
    lexicon = Lexicon(data)
    visible = shape(lexicon=lexicon, argument_rail=1)
    assert decode(visible, lexicon) == assertion()
    assert decode(from_svg(to_svg(visible)), lexicon) == assertion()


def test_same_visible_form_cannot_be_registered_twice():
    data = Lexicon().document()
    data['entries']['other'] = deepcopy(data['entries']['home'])
    with pytest.raises(ValueError, match='Ambiguous'):
        Lexicon(data)


@pytest.mark.parametrize('mutation', ['meaning', 'form', 'remove', 'alias'])
def test_extension_cannot_silently_change_an_existing_word(mutation):
    data = Lexicon().document()
    if mutation == 'meaning':
        data['entries']['rain']['meaning'] = '別の意味'
    elif mutation == 'form':
        data['entries']['rain']['form']['ray'] = 'north'
    elif mutation == 'remove':
        del data['entries']['rain']
    else:
        data['entries']['town']['aliases'] = ['home']
        with pytest.raises(ValueError, match='alias'):
            Lexicon(data)
        return
    with pytest.raises(ValueError, match='Extension'):
        check_extension(Lexicon(), Lexicon(data))


@pytest.mark.parametrize('mutation', ['cut', 'extra-circle', 'extra-line', 'unknown-word',
                                     'metadata', 'nonfinite', 'wrong-order', 'reflection'])
def test_malformed_or_unsupported_visible_input_is_rejected(mutation):
    visible = shape()
    if mutation == 'cut':
        visible.pop()
    elif mutation == 'extra-circle':
        visible.append(dict(kind='circle', x=450., y=32., r=SMALL))
    elif mutation == 'extra-line':
        visible.append(dict(kind='line', x1=450., y1=32., x2=480., y2=32.))
    elif mutation == 'unknown-word':
        visible = [s for s in visible if s['kind'] != 'circle' or s['r'] != SMALL]
    elif mutation == 'metadata':
        visible[0]['source'] = assertion()
    elif mutation == 'nonfinite':
        visible[0]['x'] = float('nan')
    else:
        visible = shape('home' if mutation == 'reflection' else 'town', argument_rail=1)
        for s in visible:
            for k in ('x', 'x1', 'x2'):
                if k in s:
                    s[k] = -s[k]
    with pytest.raises(ValueError):
        decode(visible)


@pytest.mark.parametrize('statement', [
    {'kind': 'ask', 'body': assertion()['body']},
    {'kind': 'assert', 'body': {'kind': 'not', 'body': assertion()['body']}},
    assertion(head='missing'), assertion('rain'), assertion('town', 'home'),
    {'kind': 'assert', 'body': {'kind': 'call', 'symbol': 'rain', 'arguments': []}},
    {'kind': 'assert', 'body': {'kind': 'call', 'symbol': 'rain', 'arguments': [assertion()['body']]}},
])
def test_unknown_syntax_or_types_are_not_guessed(statement):
    with pytest.raises(ValueError):
        compile_assertion(statement)


@pytest.mark.parametrize('mutation', ['hide', 'text', 'transform', 'clip', 'doctype'])
def test_svg_reader_rejects_nonvisible_or_unsupported_content(mutation):
    svg = to_svg(shape())
    if mutation == 'hide':
        svg = svg.replace('<circle ', '<circle opacity="0" ', 1)
    elif mutation == 'text':
        svg = svg.replace('</svg>', '<text>rain(home)</text></svg>')
    elif mutation == 'transform':
        svg = svg.replace('<circle ', '<circle transform="translate(30,0)" ', 1)
    elif mutation == 'clip':
        import re
        svg = re.sub('viewBox="[^"]+"', 'viewBox="0 0 10 10"', svg)
    else:
        svg = '<!DOCTYPE svg>' + svg
    with pytest.raises(ValueError):
        from_svg(svg)
