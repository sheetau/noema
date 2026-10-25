from copy import deepcopy
import json
import pytest
from noema.constructed import parse
from noema.constructed_discourse import normalize_document
from scripts.visible_scope_vocabulary import ScopeVocabulary,MODULES
from scripts.visible_compound_vocabulary import CompoundVocabulary,check_compound_extension
from scripts.visible_defined_vocabulary import DefinedVocabulary
from scripts.visible_syntax_vocabulary import Vocabulary
from scripts.visible_language_page import PublicWriter,compile_document,decode_document,compile_page,decode_page,main
from scripts.visible_public_page import decode_page as edition_three_decode
from scripts.visible_word_forms import Word,symbol
from scripts.visible_syntax_geometry import render,from_svg,to_svg
from scripts.visible_page import packet,vertical_bounds,split_rows
from scripts.visible_lexical_script import _translate
from scripts.shared_reference import truth
from scripts.check_visible_scope_library import vocabulary,new_names,word_checks,cases,scope_example,questions_example,ROOT,SOURCE


def document(declarations,statements=()):
    return normalize_document(dict(schema_version='0.16',lexicon_version='0.16',declarations=declarations,statements=list(statements)))


def test_old_eighty_words_and_all_new_bodies_are_preserved():
    v=vocabulary();data=v.document();parent=CompoundVocabulary()
    assert (len(data['entries']),len(data['compounds']),len(data['definitions']))==(30,90,104)
    assert data['edition']==4 and check_compound_extension(parent,v)
    for name in parent._order:
        assert parent.word(name)==v.word(name)
        assert parent.declaration(name)==v.declaration(name)
    for module in MODULES:
        original=parse((ROOT/module['document']).read_text(encoding='utf-8'))
        for declaration in original['declarations']:
            name=declaration['name']
            assert data['definitions'][name]==declaration
            restored=v.decode_names(document(v.imports([name])))
            assert next(d for d in restored['declarations'] if d['name']==name)==declaration
            assert all(d['kind']=='definition' for d in restored['declarations'])


def test_all_forty_typed_calls_and_quoted_references_decode_from_svg():
    rows=word_checks()
    assert len(rows)==40 and {r['name'] for r in rows}==set(new_names())
    assert max(r['glyphs'] for r in rows)<=768 and max(r['shapes'] for r in rows)<=4096
    assert {r['name'] for r in rows if r['quote_rank']==1}=={'normviolated','normfulfilled','counterfactualsupported'}


def test_dictionary_inventory_and_five_meaning_examples_decode():
    rows=cases();v=vocabulary()
    assert len(rows)==7
    inventory={d['name'] for row in rows[:2] for d in row['native']['declarations']}
    assert inventory==set(v._order) and len(inventory)==120
    assert [len(row['native']['declarations']) for row in rows[:2]]==[80,40]
    for row in rows:
        assert decode_page(row['page']['shapes'],public_names=True)['document']==row['native']
    assert [r['result'] for r in rows[2:6]]==[[dict(kind='assert',value=True)]]*4
    assert rows[6]['result']==[dict(kind='ask',answers=[[p,w] for p in ('a','b') for w in ('now','left','right')])]


def test_registration_order_changes_neither_spelling_imports_nor_geometry():
    data=vocabulary().document()
    for field in ('entries','compounds','definitions'):data[field]=dict(reversed(list(data[field].items())))
    changed=ScopeVocabulary(data)
    assert changed.imports(list(reversed(new_names())))==vocabulary().imports(new_names())
    for n in new_names():assert changed.word(n)==vocabulary().word(n)
    assert compile_page(vocabulary().encode(questions_example()),changed,max_width=3200.)==cases()[-1]['page']


@pytest.mark.parametrize('change',['old-root','old-compound','old-body','new-collision','unknown-part','primitive','dependency','cycle','signature'])
def test_invalid_dictionary_extension_is_rejected(change):
    data=vocabulary().document()
    if change=='old-root':data['entries']['home']['meaning']='別の意味'
    elif change=='old-compound':data['compounds']['chronology']['parts']=['rain','treeone']
    elif change=='old-body':data['definitions']['chronology']['body']=truth(False)
    elif change=='new-collision':data['compounds']['referentat']['parts']=data['compounds']['chronology']['parts']
    elif change=='unknown-part':data['compounds']['referentat']['parts']=['rain','unknown']
    elif change=='primitive':data['definitions']['referentat']['kind']='primitive'
    elif change in ('dependency','cycle'):
        data['definitions']['referentat']['body']=dict(kind='call',symbol='unknown' if change=='dependency' else 'referentat',arguments=[])
    else:data['compounds']['referentat']['result']='individual'
    with pytest.raises(ValueError):ScopeVocabulary(data)


def test_changed_new_definition_is_not_a_compatible_extension():
    data=vocabulary().document();data['definitions']['referentat']['body']=truth(False)
    fork=ScopeVocabulary(data)
    with pytest.raises(ValueError,match='definition'):check_compound_extension(vocabulary(),fork)


@pytest.mark.parametrize('change',['body','primitive'])
def test_document_cannot_replace_a_public_definition(change):
    d=vocabulary().declaration('referentat')
    if change=='body':d['body']=truth(False)
    else:d=dict(kind='primitive',name=d['name'],parameters=[p['sort'] for p in d['parameters']],result=d['result'])
    with pytest.raises(ValueError,match='public meaning'):compile_document(document([d]))


def test_reader_rejects_shared_local_shadow_and_missing_dependency():
    v=vocabulary();d=v.declaration('referentat');w=PublicWriter(v)
    w.keyword('document');w.natural(16);w.natural(4);w.keyword('definition');w.name(d['name'])
    w.parameters(d['parameters']);w.type(d['result']);w.expr(d['body'],tuple(p['name'] for p in d['parameters']));w.end();w.end()
    with pytest.raises(ValueError,match='shadows'):decode_document(render(w.glyphs)['shapes'])
    w=PublicWriter(v);w.keyword('document');w.natural(16);w.natural(4)
    w.keyword('import');w.name(v.declaration('discourseunique')['name']);w.end();w.end()
    with pytest.raises(ValueError,match='Unknown'):decode_document(render(w.glyphs)['shapes'])


def test_local_compound_can_use_the_new_reference_definition():
    v=vocabulary();public=v.declaration('referentat');params=deepcopy(public['parameters'])
    local=dict(kind='definition',name=symbol(Word('compound',('rain','treeone')),v),parameters=params,result='truth',
        body=dict(kind='call',symbol=public['name'],arguments=[dict(kind='variable',name=p['name']) for p in params]))
    d=document(v.imports(['referentat'])+[local])
    assert decode_document(compile_document(d)['shapes'])==d


@pytest.mark.parametrize('constructor',[Vocabulary,DefinedVocabulary,CompoundVocabulary])
def test_old_local_spelling_collision_keeps_old_meaning_and_public_name(constructor):
    old=constructor();name=symbol(Word('compound',('inside','home')),old)
    d=document([dict(kind='definition',name=name,parameters=[],result='truth',body=truth(True))])
    page=compile_page(d,old,max_width=1800.)
    assert decode_page(page['shapes'])['document']==d
    assert decode_page(page['shapes'],public_names=True)['document']==d
    with pytest.raises(ValueError,match='public meaning'):compile_page(d)


def test_old_dictionaries_are_selected_by_their_visible_headers():
    for vocab,names in ((Vocabulary(),['home']),(DefinedVocabulary(),['candidateexists']),(CompoundVocabulary(),['chronology'])):
        declarations=vocab.imports(names) if hasattr(vocab,'imports') else [vocab.declaration(n) for n in names]
        d=document(declarations)
        assert decode_page(compile_page(d,vocab,max_width=1800.)['shapes'])['document']==d


def test_unknown_edition_and_wrong_explicit_dictionary_are_rejected():
    w=PublicWriter(vocabulary());w.keyword('document');w.natural(16);w.natural(5);w.end();w.end()
    with pytest.raises(ValueError,match='edition'):decode_document(render(w.glyphs)['shapes'])
    page=cases()[-1]['page']
    with pytest.raises(ValueError,match='edition'):decode_page(page['shapes'],CompoundVocabulary())
    with pytest.raises(ValueError,match='edition'):edition_three_decode(page['shapes'])


def test_header_can_span_rows_without_bypassing_frame_checks():
    d=document([],[dict(kind='assert',body=truth(True))]);v=vocabulary();w=PublicWriter(v);w.document(d)
    # A keyword is a two-glyph atom. Split after it, before the Noema edition.
    first=render(packet(w.glyphs[:2],0,final=False,vocabulary=v))['shapes']
    second=render(packet(w.glyphs[2:],1,final=True,vocabulary=v))['shapes']
    shift=vertical_bounds(first)[1]+64-vertical_bounds(second)[0]
    shapes=first+_translate(second,0,shift)
    assert decode_page(shapes)['document']==d
    with pytest.raises(ValueError,match='row'):decode_page(_translate(second,0,shift))


def test_paragraphs_and_scrambled_svg_element_order_keep_question_structure():
    v=vocabulary();d=v.encode(questions_example());page=compile_page(d,v,max_width=1800.,paragraph_starts=[0])
    shapes=from_svg(to_svg(list(reversed(page['shapes']))))
    assert decode_page(shapes)==dict(document=d,paragraph_starts=[0])


def test_cli_renders_and_recovers_public_names_and_scoped_reference(tmp_path,capsys):
    target=tmp_path/'scoped.svg'
    assert main(['render',str(ROOT/SOURCE),str(target),'--width','3200','--public-names'])==0
    assert json.loads(capsys.readouterr().out)['rows']>1
    assert main(['decode',str(target),'--native','--public-names'])==0
    assert parse(capsys.readouterr().out)==scope_example()
