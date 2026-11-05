from copy import deepcopy
import json
from pathlib import Path
import pytest
from scripts import concept2_geometry_v5 as g,concept2_composition as composition
from scripts.concept2_document import DocumentCodec,empty_document,full_name,complete_public_dictionary
from scripts.concept2_codec_v8 import Codec


def name(*parts):return full_name([composition.old.root_symbol(p) for p in parts])
def call(n,*args):return dict(kind='call',symbol=n,arguments=list(args))
def var(n='va'):return dict(kind='variable',name=n)
def eq(a,b):return dict(kind='equal',arguments=[a,b])
def assertion(body):return dict(kind='assert',body=body)
def primitive(n,parameters=(),result='individual'):
    return dict(kind='primitive',name=n,parameters=list(parameters),result=result)


def records():
    a,p,q=name('aki'),name('home'),name('book','round')
    return [primitive(a),primitive(p,['individual'],'truth'),
        dict(kind='definition',name=q,parameters=[dict(name='va',sort='individual')],result='truth',body=call(p,var())),
        dict(kind='spelling',name=q,parts=['round','round']),
        assertion(call(q,call(a)))]


def drawing(codec,record):
    tokens=codec.encode_record(record)
    return g.layout(codec.units(tokens))[0]


def test_incremental_record_svg_and_folded_document():
    writer=DocumentCodec();reader=DocumentCodec();drawings=[]
    for r in records():
        d=drawing(writer,r);drawings.append(d)
        assert reader.read_svg(composition.svg(d['shapes']))['native']==r
        writer.register(r)
    expected=dict(native=dict(empty_document(),declarations=records()[:3],statements=records()[4:]),spellings=records()[3:4])
    assert reader.result()==expected
    rows=g.fold(drawings,550);shapes=[]
    for i,row in enumerate(rows):shapes+=g.move(row['shapes'],80,80+170*i)
    assert DocumentCodec().read_document(composition.svg(shapes))==expected


def test_typed_definition_result_and_every_parameter():
    sorts=['number',dict(kind='sequence',element='truth'),dict(kind='function',parameters=['individual'],result='content')]
    for i,result in enumerate(sorts):
        r=dict(kind='definition',name=name('round','home'),parameters=[dict(name='v'+chr(97+j),sort=t) for j,t in enumerate(sorts)],result=result,body=var('v'+chr(97+i)))
        writer=DocumentCodec();reader=DocumentCodec()
        assert reader.read_svg(composition.svg(drawing(writer,r)['shapes']))['native']==r
        wrong=deepcopy(r);wrong['result']='situation'
        with pytest.raises(ValueError):writer.encode_record(wrong)


def test_empty_definition_and_inner_binders_do_not_change_names():
    body=dict(kind='lambda',parameters=[dict(name='va',sort='number')],body=var())
    r=dict(kind='definition',name=name('round','home'),parameters=[],result=dict(kind='function',parameters=['number'],result='number'),body=body)
    writer=DocumentCodec();reader=DocumentCodec()
    assert reader.read_svg(composition.svg(drawing(writer,r)['shapes']))['native']==r


def test_assumption_children_are_independent_and_nested():
    seed=dict(empty_document(),declarations=records()[:2])
    p=call(name('home'),call(name('aki')))
    s=dict(kind='suppose',condition=p,statements=[assertion(p),dict(kind='suppose',condition=p,statements=[assertion(p)])])
    writer=DocumentCodec(seed);reader=DocumentCodec(seed)
    assert reader.read_svg(composition.svg(drawing(writer,s)['shapes']))['native']==s
    assert reader.result()['native']['statements']==[s]
    bad=deepcopy(s);bad['statements']=[]
    with pytest.raises(ValueError):writer.encode_record(bad)


def test_unknown_future_recursive_duplicate_and_late_declarations():
    c=DocumentCodec()
    with pytest.raises(ValueError):c.encode_record(records()[2])
    for r in records():c.register(r)
    with pytest.raises(ValueError):c.register(primitive(name('rain')))
    before=c.result()
    with pytest.raises(ValueError):c.register(records()[0])
    assert c.result()==before
    c=DocumentCodec();r=records()[2];r=deepcopy(r);r['body']['symbol']=r['name']
    with pytest.raises(ValueError):c.register(r)


def test_spelling_collisions_and_full_name_reservation():
    c=DocumentCodec();c.register(records()[0])
    alias=dict(kind='spelling',name=name('aki'),parts=['round','book'])
    c.register(alias)
    with pytest.raises(ValueError):c.register(primitive(name('round','book')))
    with pytest.raises(ValueError):c.register(alias)
    with pytest.raises(ValueError):c.register(dict(alias,name=name('rain')))


def test_changed_or_missing_record_syntax_rejects_before_register():
    c=DocumentCodec();tokens=c.encode_record(records()[0])
    for bad in (tokens[:-1],tokens+[('root','rain')],[t for t in tokens if t!=('word-end',)]):
        reader=DocumentCodec()
        with pytest.raises((ValueError,KeyError)):reader.parse(bad)
        assert reader.result()['native']['declarations']==[]


def test_all_accepted_glyphs_preserved_and_new_grammar_is_legal():
    from scripts.concept2_codec_v7 import Codec as OldCodec
    dictionary=dict(native=dict(declarations=[]),selected_spellings={},aliases=[])
    old=OldCodec(dictionary);new=Codec(dictionary)
    assert all(old.forms[t]==new.forms[t] for t in old.forms)
    for t in set(new.forms)-set(old.forms):
        g.ink_check(new.forms[t]['shapes'])
        d=g.layout(new.units([t,('root','aki')]))[0]
        assert new.read_svg(composition.svg(d['shapes']),fragment=True)['tokens']==[t,('root','aki')]


def test_explicit_base_imports_cover_every_published_word():
    published=json.loads(Path('output/kant-presentation-spellings/dictionary.json').read_text(encoding='utf-8'))
    result=complete_public_dictionary(published)
    declarations={d['name']:d for d in result['native']['declarations']}
    assert set(a['symbol'] for a in result['aliases'])<=set(declarations)
    assert all(declarations[d['name']]==d for d in published['native']['declarations'])
    assert result['aliases']==published['aliases']
    assert result['selected_spellings']==published['selected_spellings']
