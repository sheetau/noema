from copy import deepcopy
from itertools import permutations, product
from pathlib import Path

import pytest

from noema.constructed import parse, format_graph
from noema.constructed_semantics import evaluate_document
from scripts.visible_lexical_script import Lexicon, _translate, _shape_set
from scripts.visible_word_forms import (
    Word, canonical, symbol, read_symbol, compile_word, decode_word,
    NamingDocument, call, MAX_PARTS, SMALL, MEDIUM, LARGE, PITCH,
    to_svg, from_svg,
)

ROOT = Path(__file__).resolve().parents[1]
RAIN, HOME, TOWN = [Word('root',(name,)) for name in ('rain','home','town')]


def visible(word, **kwargs):
    return compile_word(word, **kwargs)['shapes']


@pytest.mark.parametrize('parts', list(product(('rain','home','town'), repeat=2)))
@pytest.mark.parametrize('kind', ['compound','proper'])
def test_names_are_composed_without_registering_the_whole_word(kind, parts):
    word = Word(kind, parts)
    assert decode_word(visible(word)) == word
    assert decode_word(from_svg(to_svg(visible(word)))) == word
    assert read_symbol(symbol(word)) == word


def test_name_order_kind_and_repetition_remain_distinct():
    words = [Word('compound', ('rain','home')), Word('compound', ('home','rain')),
             Word('proper', ('rain','home')), Word('proper', ('home',)),
             Word('compound', ('rain','rain','home')), Word('compound', ('rain','home','home'))]
    assert len({_shape_set(visible(w)) for w in words}) == len(words)
    assert len({symbol(w) for w in words}) == len(words)
    assert symbol(Word('proper',('home',))) != symbol(HOME)
    for word in words:
        assert decode_word(visible(word)) == word


def test_branching_and_sequential_trees_read_as_the_same_spelling():
    word = Word('compound', ('home','town','home','rain'))
    variants = [visible(word, branch=branch, first_rail=rail, gap=gap)
                for branch,rail,gap in product((True,False),(0,2),(80.,120.))]
    assert len({_shape_set(v) for v in variants}) > 1
    for v in variants:
        assert decode_word(v) == word
    # A real branch exists in the default visible lines.
    lines = [s for s in variants[0] if s['kind']=='line']
    endpoints = [(s[x],s[y]) for s in lines for x,y in (('x1','y1'),('x2','y2'))]
    assert any(endpoints.count(p)==3 for p in endpoints)


def test_independent_drawing_does_not_call_the_compiler(monkeypatch):
    # This layout was drawn from the published rules, with hand-chosen joints.
    rings = [(50.,32.,LARGE),(50.,32.,MEDIUM),
             (220.,0.,MEDIUM),(220.+MEDIUM,0.,SMALL),
             (390.,64.,MEDIUM),(390.,64.,SMALL),(500.,64.,SMALL)]
    strokes = [((50.,32.),(50.,32.-LARGE)),
               ((50.+LARGE,32.),(120.,32.)),
               ((120.,32.),(152.,0.)),((152.,0.),(220.-MEDIUM,0.)),
               ((120.,32.),(152.,64.)),((152.,64.),(390.-MEDIUM,64.)),
               ((390.+MEDIUM,64.),(500.-SMALL,64.))]
    shapes = [dict(kind='circle',x=x,y=y,r=r) for x,y,r in rings]
    shapes += [dict(kind='line',x1=a[0],y1=a[1],x2=b[0],y2=b[1]) for a,b in strokes]
    import scripts.visible_word_forms as module
    monkeypatch.setattr(module,'compile_word',lambda *a,**k:pytest.fail('Used renderer to decode'))
    assert decode_word(shapes) == Word('compound', ('home','town'))


@pytest.mark.parametrize('kind', ['compound','proper'])
def test_runtime_bound_is_not_a_list_of_allowed_compounds(kind):
    word = Word(kind, ('home','town','rain')*(MAX_PARTS//3))
    assert len(word.parts)==MAX_PARTS
    assert decode_word(visible(word)) == word
    with pytest.raises(ValueError, match='count'):
        compile_word(Word(kind,word.parts+('home',)))


def test_scale_translation_order_and_line_subdivision_do_not_change_reading():
    word = Word('proper', ('rain','home','town'))
    parts = []
    for s in visible(word):
        if s['kind']=='circle':
            parts.append(s)
        else:
            mid = ((s['x1']+s['x2'])/2,(s['y1']+s['y2'])/2)
            parts += [dict(kind='line',x1=mid[0],y1=mid[1],x2=s['x1'],y2=s['y1']),
                      dict(kind='line',x1=s['x2'],y1=s['y2'],x2=mid[0],y2=mid[1])]
    moved = list(reversed(_translate(parts,-230.,418.,1.37)))
    assert decode_word(moved) == word


def test_lexicon_order_and_new_root_do_not_rename_an_existing_word():
    word = Word('compound',('home','town'))
    data = Lexicon().document()
    expected = visible(word)
    for order in permutations(data['entries']):
        changed = deepcopy(data)
        changed['entries'] = {name:changed['entries'][name] for name in order}
        lexicon = Lexicon(changed)
        assert visible(word,lexicon=lexicon)==expected
        assert decode_word(expected,lexicon)==word
    changed = deepcopy(data)
    changed['entries']['probe'] = deepcopy(changed['entries']['rain'])
    changed['entries']['probe']['form']['ray']='north'
    changed['entries']['probe']['meaning']='検査用の別関係'
    lexicon=Lexicon(changed)
    assert visible(word,lexicon=lexicon)==expected
    assert decode_word(expected,lexicon)==word


def test_internal_spelling_is_reversible_even_when_root_names_contain_delimiters():
    data = Lexicon().document()
    for name,direction in [('z','north'),('zq','west'),('rainzqhome','east')]:
        data['entries'][name]=deepcopy(data['entries']['rain'])
        data['entries'][name]['form']['ray']=direction
        data['entries'][name]['meaning']='検査用の別関係'
    lexicon=Lexicon(data)
    words=[Word('compound',('rain','home')),Word('proper',('rainzqhome',)),
           Word('compound',('z','zq')),Word('compound',('zq','z'))]
    assert len({symbol(w,lexicon) for w in words})==len(words)
    for word in words:
        assert read_symbol(symbol(word,lexicon),lexicon)==word


@pytest.mark.parametrize('value', ['wc', 'wchomezq', 'wphomez', 'wphome',
                                 'wrhomezqrainzq', 'wphomezx', 'wpzq', 'qqhomezq'])
def test_invalid_internal_spellings_are_rejected(value):
    with pytest.raises(ValueError):
        read_symbol(value)


@pytest.mark.parametrize('mutation', ['cut', 'end', 'part', 'extra-circle', 'extra-line',
                                     'reverse', 'metadata', 'untyped-primitive'])
def test_unknown_or_incomplete_visible_names_are_rejected(mutation):
    shapes=visible(Word('compound',('home','town')))
    if mutation=='cut':
        shapes.pop()
    elif mutation=='end':
        right=max(s['x'] for s in shapes if s['kind']=='circle')
        shapes=[s for s in shapes if s['kind']!='circle' or s['x']!=right]
    elif mutation=='part':
        # Removing a member of the home glyph makes it an unknown public word.
        shapes=[s for s in shapes if not (s['kind']=='circle' and s['r']==SMALL and s['y']==0)]
    elif mutation=='extra-circle':
        shapes.append(dict(kind='circle',x=1700.,y=32.,r=SMALL))
    elif mutation=='extra-line':
        shapes.append(dict(kind='line',x1=1700.,y1=32.,x2=1750.,y2=32.))
    elif mutation=='reverse':
        for s in shapes:
            for key in ('x','x1','x2'):
                if key in s:s[key]=-s[key]
    elif mutation=='metadata':
        shapes[0]['word']='home'
    else:
        shapes.append(dict(kind='path',points=[]))
    with pytest.raises(ValueError):
        decode_word(shapes)


def naming_document():
    document=NamingDocument()
    compound=Word('compound',('rain','home'))
    proper=Word('proper',('rain','home'))
    other=Word('proper',('home','town'))
    reusable=Word('compound',('rain','rain'))
    document.define(compound, [], 'truth', call(RAIN,[call(HOME)]))
    document.define(proper, [], 'individual', call(HOME))
    document.define(other, [], 'individual', call(HOME))
    document.define(reusable, [dict(name='x',sort='individual')], 'truth',
                    call(RAIN,[dict(kind='variable',name='x')]))
    document.append(dict(kind='assert',body=dict(kind='equal',arguments=[call(proper),call(other)])))
    document.append(dict(kind='ask',body=call(compound)))
    document.append(dict(kind='ask',body=call(reusable,[call(TOWN)])))
    return document.document()


def test_native_example_uses_definitions_and_retains_the_three_shared_primitives():
    actual=naming_document()
    expected=parse((ROOT/'examples/v016/visible-word-definitions-v1.noema').read_text(encoding='utf-8'))
    assert actual==expected
    assert parse(format_graph(actual))==actual
    assert [d['kind'] for d in actual['declarations']].count('primitive')==3
    assert [d['kind'] for d in actual['declarations']].count('definition')==4


@pytest.mark.parametrize('rain_home,rain_town', list(product((False,True),repeat=2)))
def test_names_and_aliases_do_not_assert_properties_of_their_spelling(rain_home,rain_town):
    document=naming_document()
    model={symbol(HOME):lambda:'home',symbol(TOWN):lambda:'town',
           symbol(RAIN):lambda who:rain_home if who=='home' else rain_town}
    values=evaluate_document(document,individuals=('home','town'),situations=('now',),primitives=model)
    assert [v['value'] for v in values]==[True,rain_home,rain_town]
    # Different name spellings remain distinct in declarations even though
    # the first assertion establishes their referents' equality in this model.
    a,b=Word('proper',('rain','home')),Word('proper',('home','town'))
    assert symbol(a)!=symbol(b) and visible(a)!=visible(b)


def test_failed_definition_does_not_mutate_the_naming_document():
    document=NamingDocument()
    word=Word('compound',('rain','home'))
    before=document.document()
    with pytest.raises(ValueError):
        document.define(word,[],'truth',call(word))
    assert document.document()==before
    with pytest.raises(ValueError):
        document.append(dict(kind='assert',body=call(word)))
    assert document.document()==before
    document.define(word,[],'truth',call(RAIN,[call(HOME)]))
    after=document.document()
    with pytest.raises(ValueError):
        document.define(word,[],'truth',call(RAIN,[call(TOWN)]))
    assert document.document()==after


def test_a_name_read_from_visible_ink_resolves_only_after_its_definition():
    introduced=Word('proper',('rain','home'))
    recovered=decode_word(from_svg(to_svg(visible(introduced))))
    document=NamingDocument()
    statement=dict(kind='assert',body=dict(kind='equal',arguments=[call(recovered),call(HOME)]))
    with pytest.raises(ValueError):
        document.append(statement)
    document.define(introduced,[],'individual',call(HOME))
    document.append(statement)
    values=evaluate_document(document.document(),individuals=('home','town'),situations=('now',),primitives={
        symbol(HOME):lambda:'home',symbol(TOWN):lambda:'town',symbol(RAIN):lambda who:False})
    assert [v['value'] for v in values]==[True]


@pytest.mark.parametrize('mutation', ['wrong-result','proper-predicate','proper-parameter','root','unknown'])
def test_types_and_scope_are_checked_by_the_existing_native_language(mutation):
    document=NamingDocument()
    with pytest.raises(ValueError):
        if mutation=='wrong-result':
            document.define(Word('compound',('rain','home')),[],'individual',call(RAIN,[call(HOME)]))
        elif mutation=='proper-predicate':
            document.define(Word('proper',('rain','home')),[],'truth',call(RAIN,[call(HOME)]))
        elif mutation=='proper-parameter':
            document.define(Word('proper',('rain','home')),[dict(name='x',sort='individual')],
                            'individual',dict(kind='variable',name='x'))
        elif mutation=='root':
            document.define(HOME,[],'individual',call(TOWN))
        else:
            document.define(Word('compound',('missing','home')),[],'individual',call(HOME))
