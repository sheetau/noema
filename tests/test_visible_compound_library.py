from copy import deepcopy
import json
import pytest

from noema.constructed import parse
from noema.constructed_discourse import normalize_document
from scripts.check_visible_compound_library import vocabulary,cases,word_checks,temporal_example,ROOT,SOURCE
from scripts.visible_compound_vocabulary import CompoundVocabulary,check_compound_extension,MODULES
from scripts.visible_defined_vocabulary import DefinedVocabulary
from scripts.visible_public_page import PublicWriter,compile_document,decode_document,compile_page,decode_page,main
from scripts.visible_word_forms import Word,symbol
from scripts.visible_syntax_geometry import render
from scripts.shared_reference import truth


def document(declarations,statements=()):
    return normalize_document(dict(schema_version='0.16',lexicon_version='0.16',
                                   declarations=declarations,statements=list(statements)))


def raw_writer(edition=3):
    w=PublicWriter(vocabulary());w.keyword('document');w.natural(16);w.natural(edition)
    return w


def test_every_shared_definition_is_the_original_native_body():
    v=vocabulary();data=v.document()
    assert len(data['entries'])==30 and len(data['compounds'])==50 and len(data['definitions'])==64
    assert check_compound_extension(DefinedVocabulary(),v)
    names=[]
    for module in MODULES:
        original=parse((ROOT/module['document']).read_text(encoding='utf-8'))
        for declaration in original['declarations']:
            name=declaration['name'];names.append(name)
            assert declaration==data['definitions'][name]
            imported=v.decode_names(document(v.imports([name])))
            assert next(d for d in imported['declarations'] if d['name']==name)==declaration
            assert all(d['kind']=='definition' for d in imported['declarations'])
    assert set(names)==set(data['compounds'])


def test_all_fifty_typed_calls_and_quoted_references_decode_from_svg_geometry():
    checks=word_checks()
    assert {r['name'] for r in checks}==set(vocabulary().document()['compounds'])
    assert max(r['glyphs'] for r in checks)<=768
    assert all(r['shapes']>r['glyphs'] for r in checks)


def test_complete_dictionary_and_three_semantic_pages_decode_and_evaluate():
    rows=cases()
    assert len(rows[0]['encoded']['declarations'])==80
    assert sum(d['kind']=='primitive' for d in rows[0]['encoded']['declarations'])==16
    assert [r['values'] for r in rows]==[[],[True],[True],[True,True]]
    for row in rows:
        assert decode_page(row['page']['shapes'],public_names=True)['document']==row['native']


def test_registration_order_changes_neither_spelling_nor_dependency_order():
    v=vocabulary();data=v.document()
    for field in ('entries','compounds','definitions'):data[field]=dict(reversed(list(data[field].items())))
    other=CompoundVocabulary(data)
    assert other.imports(other._order)==v.imports(v._order)
    assert all(other.word(n)==v.word(n) for n in data['compounds'])
    assert compile_page(v.encode(temporal_example()),other,max_width=3200.)==cases()[1]['page']


def test_unregistered_local_compound_can_use_shared_compound_in_body():
    v=vocabulary();name=symbol(Word('compound',('rain','treeone')),v)
    shared=v.declaration('referencemissing');params=deepcopy(shared['parameters'])
    local=dict(kind='definition',name=name,parameters=params,result=shared['result'],
        body=dict(kind='call',symbol=shared['name'],arguments=[dict(kind='variable',name=p['name']) for p in params]))
    doc=document(v.imports(['referencemissing'])+[local])
    assert decode_document(compile_document(doc)['shapes'])==doc


@pytest.mark.parametrize('replacement',['primitive','different-body'])
def test_shared_compound_cannot_be_replaced(replacement):
    v=vocabulary();d=v.declaration('chronology')
    if replacement=='primitive':
        d=dict(kind='primitive',name=d['name'],parameters=[p['sort'] for p in d['parameters']],result=d['result'])
    else:d['body']=truth(False)
    with pytest.raises(ValueError,match='public meaning'):compile_document(document([d]))


def test_visible_local_definition_cannot_shadow_shared_compound_even_with_same_body():
    v=vocabulary();d=v.declaration('chronology');w=raw_writer()
    w.keyword('definition');w.name(d['name']);w.parameters(d['parameters']);w.type(d['result'])
    w.expr(d['body'],tuple(p['name'] for p in d['parameters']));w.end();w.end()
    with pytest.raises(ValueError,match='shadows'):decode_document(render(w.glyphs)['shapes'])


def test_missing_dependencies_are_rejected_and_spelling_parts_do_not_import_functions():
    v=vocabulary();w=raw_writer()
    w.keyword('import');w.name(v.declaration('readingsresolved')['name']);w.end();w.end()
    with pytest.raises(ValueError,match='Unknown'):decode_document(render(w.glyphs)['shapes'])
    selected=v.imports(['chronology'])
    assert len(selected)==1 and selected[0]['name']==v.declaration('chronology')['name']


def test_unknown_compound_import_is_rejected():
    w=raw_writer();w.keyword('import');w.name(symbol(Word('compound',('rain','treeone')),vocabulary()));w.end();w.end()
    with pytest.raises(ValueError,match='Unknown shared word'):decode_document(render(w.glyphs)['shapes'])


@pytest.mark.parametrize('change',['cycle','unknown','primitive','signature','old-meaning','old-shape',
                                  'old-body','collision','unknown-part','too-long'])
def test_invalid_shared_vocabulary_is_rejected(change):
    data=vocabulary().document();d=data['definitions']['chronology'];entry=data['compounds']['chronology']
    if change in ('cycle','unknown'):
        d['body']=dict(kind='call',symbol='chronology' if change=='cycle' else 'unregistered',arguments=[])
    elif change=='primitive':d['kind']='primitive'
    elif change=='signature':entry['parameters']=[];entry['roles']=[]
    elif change=='old-meaning':data['entries']['rain']['meaning']='別の意味'
    elif change=='old-shape':data['entries']['rain']['form']=data['entries']['book']['form']
    elif change=='old-body':data['definitions']['candidateexists']['body']=truth(False)
    elif change=='collision':entry['parts']=data['compounds']['timewindow']['parts']
    elif change=='unknown-part':entry['parts']=['rain','unregistered']
    else:entry['parts']=['rain']*25
    with pytest.raises(ValueError):CompoundVocabulary(data)


@pytest.mark.parametrize('change',['body','spelling','meaning'])
def test_extension_rejects_valid_but_incompatible_changes(change):
    data=vocabulary().document()
    if change=='body':data['definitions']['chronology']['body']=truth(False)
    elif change=='spelling':data['compounds']['chronology']['parts']=['rain','treeone']
    else:data['compounds']['chronology']['meaning']='別の意味'
    changed=CompoundVocabulary(data)
    with pytest.raises(ValueError,match='changed'):check_compound_extension(vocabulary(),changed)


def test_visible_header_selects_original_edition_one_and_two():
    from scripts.check_visible_syntax import integrated_document
    from scripts.visible_shared_page import compile_page as old_compile
    from scripts.visible_library import compile_page as second_compile
    first=integrated_document()
    assert decode_page(old_compile(first,max_width=3200.)['shapes'])['document']==first
    second=document(DefinedVocabulary().imports(['candidateexists']))
    assert decode_page(second_compile(second,max_width=3200.)['shapes'])['document']==second


def test_old_local_name_collision_keeps_its_original_meaning_and_name():
    from scripts.visible_library import compile_page as old_compile
    v=DefinedVocabulary();name=symbol(Word('compound',('necessaryactual','above')),v)
    old=document([dict(kind='definition',name=name,parameters=[],result='truth',body=truth(True))])
    page=old_compile(old,max_width=3200.)
    assert decode_page(page['shapes'])['document']==old
    assert decode_page(page['shapes'],public_names=True)['document']==old
    with pytest.raises(ValueError,match='public meaning'):compile_page(old)
    with pytest.raises(ValueError,match='edition'):decode_page(page['shapes'],vocabulary())


def test_unknown_edition_is_rejected():
    w=raw_writer(4);w.end();w.end()
    with pytest.raises(ValueError,match='edition'):decode_document(render(w.glyphs)['shapes'])


def test_compound_words_remain_indivisible_across_rows_and_paragraphs():
    doc=cases()[2]['encoded']
    page=compile_page(doc,max_width=1800.,paragraph_starts=[0])
    assert decode_page(page['shapes'])==dict(document=doc,paragraph_starts=[0])
    with pytest.raises(ValueError,match='indivisible'):compile_page(doc,max_width=150.)


def test_cli_preserves_public_native_names_and_meanings(tmp_path,capsys):
    target=tmp_path/'public.svg'
    assert main(['render',str(ROOT/SOURCE),str(target),'--width','3200','--public-names'])==0
    assert json.loads(capsys.readouterr().out)['rows']>1
    assert main(['decode',str(target),'--native','--public-names'])==0
    assert parse(capsys.readouterr().out)==temporal_example()
