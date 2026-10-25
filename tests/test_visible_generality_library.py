from copy import deepcopy
import json
import pytest
from noema.constructed import parse
from noema.constructed_semantics import evaluate_document
from scripts.visible_generality_vocabulary import GeneralityVocabulary,SelectionVocabulary,check_quantity_extension
from scripts.visible_quantity_vocabulary import QuantityVocabulary
from scripts.visible_scope_vocabulary import ScopeVocabulary
from scripts.visible_compound_vocabulary import CompoundVocabulary
from scripts.visible_defined_vocabulary import DefinedVocabulary
from scripts.visible_syntax_vocabulary import Vocabulary
from scripts.visible_generality_page import compile_page,decode_page,decode_document,PublicWriter,main
from scripts.visible_selection_page import decode_page as edition_six_decode
from scripts.visible_syntax_geometry import render,to_svg,from_svg
from scripts.visible_word_forms import Word,symbol
from scripts.shared_reference import truth
from scripts.check_visible_generality_library import vocabulary,new_names,doc,cases,word_checks,SOURCES,ROOT


def test_twenty_three_exact_definitions_and_previous_inventory_are_preserved():
    vocab=vocabulary();parent=SelectionVocabulary();data=vocab.document()
    assert (len(data['entries']),len(data['compounds']),len(data['definitions']),len(data['primitives']))==(30,169,178,5)
    assert check_quantity_extension(parent,vocab)
    for n in parent._order:
        assert vocab.word(n)==parent.word(n) and vocab.declaration(n)==parent.declaration(n)
    source=parse((ROOT/'examples/v016/shared-generality-v1.noema').read_text(encoding='utf-8'))
    assert {d['name']:d for d in doc(new_names())['declarations']}=={d['name']:d for d in source['declarations']}


def test_every_new_typed_call_and_quotation_decodes():
    rows=word_checks()
    assert len(rows)==23 and {r['name'] for r in rows}==set(new_names())
    assert all(r['glyphs']<=768 and r['shapes']<=4096 for r in rows)


def test_five_documents_recover_native_functions_and_scopes():
    rows=cases();assert len(rows)==5
    for row in rows:
        assert decode_page(row['page']['shapes'],public_names=True)['document']==row['native']
        assert row['glyphs']<=768 and len(row['page']['shapes'])<=4096
        assert all(d['kind']=='definition' for d in row['native']['declarations'])
        if row['label'] in SOURCES:
            assert parse((ROOT/SOURCES[row['label']]).read_text(encoding='utf-8'))==row['native']
            assert row['result']==[dict(kind='assert',value=True)]
    assert {d['name'] for d in rows[0]['native']['declarations']}==set(new_names())


@pytest.mark.parametrize('change',['old-meaning','old-body','new-meaning','new-body','primitive','spelling','collision','signature','dependency'])
def test_same_edition_rejects_changed_meanings_and_spellings(change):
    data=vocabulary().document()
    if change=='old-meaning':data['entries']['home']['meaning']='different'
    elif change=='old-body':data['definitions']['caseuniversal']['body']=truth(False)
    elif change=='new-meaning':data['compounds']['casegeneric']['meaning']='different'
    elif change=='new-body':data['definitions']['degreeborderline']['body']=truth(True)
    elif change=='primitive':data['definitions']['normalcase']['kind']='primitive'
    elif change=='spelling':data['compounds']['normalcase']['parts'].reverse()
    elif change=='collision':data['compounds']['normalcase']['parts']=data['compounds']['casegeneric']['parts']
    elif change=='signature':data['compounds']['normalcase']['result']='individual'
    else:data['definitions']['normalcase']['body']=dict(kind='call',symbol='unknown',arguments=[])
    with pytest.raises(ValueError,match='published meanings'):GeneralityVocabulary(data)


def test_registration_order_does_not_change_imports_or_geometry():
    data=vocabulary().document()
    for field in ('entries','compounds','definitions','primitives'):data[field]=dict(reversed(list(data[field].items())))
    changed=GeneralityVocabulary(data)
    assert changed.imports(list(reversed(new_names())))==vocabulary().imports(new_names())
    assert compile_page(cases()[1]['encoded'],changed,max_width=4800.)==cases()[1]['page']


@pytest.mark.parametrize('constructor,name',[(Vocabulary,'home'),(DefinedVocabulary,'candidateexists'),
    (CompoundVocabulary,'chronology'),(ScopeVocabulary,'referentat'),(QuantityVocabulary,'rationaladd'),
    (SelectionVocabulary,'selectnumber')])
def test_old_headers_continue_to_select_old_dictionaries(constructor,name):
    vocab=constructor();declarations=vocab.imports([name]) if hasattr(vocab,'imports') else [vocab.declaration(name)]
    from noema.constructed_discourse import normalize_document
    d=normalize_document(dict(schema_version='0.16',lexicon_version='0.16',declarations=declarations,statements=[]))
    assert decode_page(compile_page(d,vocab,max_width=4800.)['shapes'])['document']==d


def test_wrong_and_unknown_editions_are_rejected():
    shapes=cases()[0]['page']['shapes']
    with pytest.raises(ValueError,match='edition'):edition_six_decode(shapes)
    with pytest.raises(ValueError,match='edition'):decode_page(shapes,SelectionVocabulary())
    w=PublicWriter(vocabulary());w.keyword('document');w.natural(16);w.natural(8);w.end();w.end()
    with pytest.raises(ValueError,match='edition'):decode_document(render(w.glyphs)['shapes'])


def test_old_local_spelling_is_not_reinterpreted_as_new_shared_word():
    from noema.constructed_discourse import normalize_document
    old=SelectionVocabulary();name=symbol(Word('compound',('above','above')),old)
    d=normalize_document(dict(schema_version='0.16',lexicon_version='0.16',declarations=[
        dict(kind='definition',name=name,parameters=[],result='truth',body=truth(True))],statements=[]))
    assert decode_page(compile_page(d,old,max_width=4800.)['shapes'])['document']==d
    with pytest.raises(ValueError,match='public meaning'):compile_page(d)


def test_missing_dependency_and_shadowing_are_rejected():
    w=PublicWriter(vocabulary());w.keyword('document');w.natural(16);w.natural(7)
    w.keyword('import');w.name(vocabulary().declaration('casegeneric')['name']);w.end();w.end()
    with pytest.raises(ValueError,match='Unknown'):decode_document(render(w.glyphs)['shapes'])
    w=PublicWriter(vocabulary());w.keyword('document');w.natural(16);w.natural(7)
    w.keyword('definition');w.name(vocabulary().declaration('casegeneric')['name'])
    w.parameters([]);w.type('truth');w.expr(truth(True),());w.end();w.end()
    with pytest.raises(ValueError,match='shadows'):decode_document(render(w.glyphs)['shapes'])


def test_svg_element_order_does_not_supply_semantics():
    row=cases()[2]
    assert decode_page(from_svg(to_svg(list(reversed(row['page']['shapes'])))))['document']==row['encoded']


@pytest.mark.parametrize('label',['generic-exception','kindwise-generic','degree-standards','modal-degree'])
def test_reversing_the_visible_order_changes_the_evaluated_assertion(label):
    row=next(r for r in cases() if r['label']==label);d=deepcopy(row['encoded'])
    changed=[]
    def reverse(x):
        if isinstance(x,list):
            for y in x:reverse(y)
        elif isinstance(x,dict):
            if x.get('kind')=='lambda' and len(x['parameters'])==2:
                x['parameters'].reverse();changed.append(True)
            for y in x.values():reverse(y)
    reverse(d['statements'])
    assert len(changed)==1
    # The full three-individual domain has assignments satisfying the guards;
    # these are not merely vacuous true results on too small a domain.
    assert evaluate_document(d,individuals=('a','b','c'),situations=('now','later'),primitives={},max_steps=1000000)==[
        dict(kind='assert',value=False)]


def test_cli_degree_page_roundtrip(tmp_path,capsys):
    target=tmp_path/'degree.svg'
    assert main(['render',str(ROOT/SOURCES['degree-standards']),str(target),'--width','4800','--public-names'])==0
    assert json.loads(capsys.readouterr().out)['rows']==cases()[3]['page']['rows']
    assert main(['decode',str(target),'--native','--public-names'])==0
    assert parse(capsys.readouterr().out)==cases()[3]['native']
