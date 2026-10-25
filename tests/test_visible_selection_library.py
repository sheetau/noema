from copy import deepcopy
import json
import pytest
from noema.constructed import parse
from noema.constructed_semantics import evaluate_document
from scripts.visible_selection_vocabulary import SelectionVocabulary,check_quantity_extension
from scripts.visible_quantity_vocabulary import QuantityVocabulary
from scripts.visible_selection_page import compile_page,decode_page,decode_document,main,PublicWriter
from scripts.visible_quantity_page import decode_page as edition_five_decode
from scripts.visible_syntax_geometry import render,from_svg,to_svg
from scripts.shared_reference import truth
from scripts.check_visible_selection_library import (
    vocabulary,doc,word_checks,cases,multipart_example,diagnostic_instance,model,ROOT,SOURCE,NEW_NAMES)


def test_previous_inventory_and_exact_selection_definitions():
    v=vocabulary();old=QuantityVocabulary();data=v.document()
    assert (len(data['entries']),len(data['compounds']),len(data['definitions']),len(data['primitives']))==(30,146,155,5)
    assert check_quantity_extension(old,v)
    for name in old._order:
        assert old.word(name)==v.word(name) and old.declaration(name)==v.declaration(name)
    source=parse((ROOT/'examples/v016/shared-selection-v1.noema').read_text(encoding='utf-8'))
    restored=doc(NEW_NAMES)
    assert {d['name']:d for d in restored['declarations']}=={d['name']:d for d in source['declarations']}


def test_five_calls_quotes_and_four_complete_documents_decode():
    words=word_checks();rows=cases()
    assert len(words)==5 and {r['name'] for r in words}==set(NEW_NAMES)
    assert [r['name'] for r in words if r['kind']=='primitive']==['truthindicator']
    assert len(rows)==4
    for row in rows:
        assert len(row['page']['shapes'])<=4096
        assert decode_page(row['page']['shapes'],public_names=True)['document']==row['native']
    for row in rows[1:]:assert row['result']==[dict(kind='assert',value=True)]
    for row in rows[2:]:
        assert len(row['diagnostics'])==5
        assert all(r['result']==[dict(kind='assert',value=True)] for r in row['diagnostics'])


@pytest.mark.parametrize('change',['old-meaning','old-body','new-meaning','new-body','primitive','spelling','collision','signature'])
def test_same_edition_cannot_redefine_meanings_or_spellings(change):
    data=vocabulary().document()
    if change=='old-meaning':data['entries']['home']['meaning']='different'
    elif change=='old-body':data['definitions']['memberof']['body']=truth(False)
    elif change=='new-meaning':data['compounds']['truthindicator']['meaning']='different'
    elif change=='new-body':data['definitions']['countselected']['body']=truth(True)
    elif change=='primitive':data['primitives']['truthindicator']['result']='truth'
    elif change=='spelling':data['compounds']['selectnumber']['parts'].reverse()
    elif change=='collision':data['compounds']['selectnumber']['parts']=data['compounds']['countselected']['parts']
    else:data['compounds']['selectnumber']['result']='truth'
    with pytest.raises(ValueError,match='published meanings'):SelectionVocabulary(data)


def test_registration_order_keeps_same_edition_and_imports():
    data=vocabulary().document()
    for field in ('entries','compounds','definitions','primitives'):data[field]=dict(reversed(list(data[field].items())))
    assert SelectionVocabulary(data).imports(list(reversed(NEW_NAMES)))==vocabulary().imports(NEW_NAMES)


def test_previous_header_and_explicit_wrong_dictionary():
    old=QuantityVocabulary();d=old.encode(doc(['rationaladd']))
    assert decode_page(compile_page(d,old,max_width=4800.)['shapes'])['document']==d
    with pytest.raises(ValueError,match='edition'):edition_five_decode(cases()[0]['page']['shapes'])
    with pytest.raises(ValueError,match='edition'):decode_page(cases()[0]['page']['shapes'],old)
    w=PublicWriter(vocabulary());w.keyword('document');w.natural(16);w.natural(7);w.end();w.end()
    with pytest.raises(ValueError,match='edition'):decode_document(render(w.glyphs)['shapes'])


def test_svg_order_does_not_supply_meaning():
    row=cases()[1]
    assert decode_page(from_svg(to_svg(list(reversed(row['page']['shapes'])))))['document']==row['encoded']


@pytest.mark.parametrize('left,right,delta',[(250,500,1),(400,600,-1),(0,0,1)])
def test_wrong_whole_amount_fails_native_body(left,right,delta):
    d=diagnostic_instance(vocabulary().encode(multipart_example(left,right,total_delta=delta)))
    assert evaluate_document(d,individuals=('a','b','c'),situations=('now',),primitives=model(d),max_steps=1000000)==[dict(kind='assert',value=False)]


def test_multipart_measurement_is_visible_not_a_host_callback():
    row=cases()[2]
    assert {d['name'] for d in row['native']['declarations'] if d['kind']=='primitive'}=={
        'rationaladd','rationalmultiply','rationalbelow','truthindicator'}
    assert len(model(row['encoded']))==4
    assert parse((ROOT/SOURCE).read_text(encoding='utf-8'))==row['native']


def test_cli_multipart_roundtrip(tmp_path,capsys):
    target=tmp_path/'parts.svg'
    assert main(['render',str(ROOT/SOURCE),str(target),'--width','4800','--public-names'])==0
    assert json.loads(capsys.readouterr().out)['rows']==cases()[2]['page']['rows']
    assert main(['decode',str(target),'--native','--public-names'])==0
    assert parse(capsys.readouterr().out)==multipart_example()
