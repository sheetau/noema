from copy import deepcopy
import json
import pytest
from noema.constructed import parse
from noema.constructed_semantics import evaluate_document
from scripts.visible_speech_vocabulary import SpeechVocabulary,GeneralityVocabulary,check_quantity_extension
from scripts.visible_selection_vocabulary import SelectionVocabulary
from scripts.visible_quantity_vocabulary import QuantityVocabulary
from scripts.visible_scope_vocabulary import ScopeVocabulary
from scripts.visible_compound_vocabulary import CompoundVocabulary
from scripts.visible_defined_vocabulary import DefinedVocabulary
from scripts.visible_syntax_vocabulary import Vocabulary
from scripts.visible_speech_page import compile_page,decode_page,decode_document,PublicWriter,main
from scripts.visible_generality_page import decode_page as edition_seven_decode
from scripts.visible_syntax_geometry import render,to_svg,from_svg
from scripts.visible_word_forms import Word,symbol
from scripts.shared_reference import truth
from scripts.check_visible_speech_library import vocabulary,new_names,doc,cases,word_checks,SOURCES,ROOT,model,local


def test_nineteen_exact_definitions_and_previous_inventory_are_preserved():
    vocab=vocabulary();parent=GeneralityVocabulary();data=vocab.document()
    assert (len(data['entries']),len(data['compounds']),len(data['definitions']),len(data['primitives']))==(30,188,197,5)
    assert check_quantity_extension(parent,vocab)
    for n in parent._order:
        assert vocab.word(n)==parent.word(n) and vocab.declaration(n)==parent.declaration(n)
    source=parse((ROOT/'examples/v016/shared-speech-v1.noema').read_text(encoding='utf-8'))
    assert {d['name']:d for d in doc(new_names())['declarations']}=={d['name']:d for d in source['declarations']}


def test_every_new_typed_call_and_quotation_decodes():
    rows=word_checks()
    assert len(rows)==19 and {r['name'] for r in rows}==set(new_names())
    assert all(r['glyphs']<=768 and r['shapes']<=4096 for r in rows)
    assert {r['name'] for r in rows if r['quotation_rank']==1}=={'requestrealized','promiserealized'}


def test_nine_documents_recover_native_functions_and_scopes():
    rows=cases();assert len(rows)==9
    for row in rows:
        assert decode_page(row['page']['shapes'],public_names=True)['document']==row['native']
        assert row['glyphs']<=768 and len(row['page']['shapes'])<=4096
        if row['label'] in SOURCES:
            assert parse((ROOT/SOURCES[row['label']]).read_text(encoding='utf-8'))==row['native']
            assert row['result']==[dict(kind='assert',value=True)]
    assert {d['name'] for d in rows[0]['native']['declarations']}==set(new_names())


@pytest.mark.parametrize('change',['old-meaning','old-body','new-meaning','new-body','primitive','spelling','collision','signature','dependency'])
def test_same_edition_rejects_changed_meanings_and_spellings(change):
    data=vocabulary().document()
    if change=='old-meaning':data['entries']['home']['meaning']='different'
    elif change=='old-body':data['definitions']['caseuniversal']['body']=truth(False)
    elif change=='new-meaning':data['compounds']['speechrequest']['meaning']='different'
    elif change=='new-body':data['definitions']['speechto']['body']=truth(True)
    elif change=='primitive':data['definitions']['speechpromise']['kind']='primitive'
    elif change=='spelling':data['compounds']['speechpromise']['parts'].reverse()
    elif change=='collision':data['compounds']['speechpromise']['parts']=data['compounds']['speechrequest']['parts']
    elif change=='signature':data['compounds']['speechpromise']['result']='individual'
    else:data['definitions']['speechpromise']['body']=dict(kind='call',symbol='unknown',arguments=[])
    with pytest.raises(ValueError,match='published meanings'):SpeechVocabulary(data)


def test_registration_order_does_not_change_imports_or_geometry():
    data=vocabulary().document()
    for field in ('entries','compounds','definitions','primitives'):data[field]=dict(reversed(list(data[field].items())))
    changed=SpeechVocabulary(data)
    assert changed.imports(list(reversed(new_names())))==vocabulary().imports(new_names())
    assert compile_page(cases()[1]['encoded'],changed,max_width=4800.)==cases()[1]['page']


@pytest.mark.parametrize('constructor,name',[(Vocabulary,'home'),(DefinedVocabulary,'candidateexists'),
    (CompoundVocabulary,'chronology'),(ScopeVocabulary,'referentat'),(QuantityVocabulary,'rationaladd'),
    (SelectionVocabulary,'selectnumber'),(GeneralityVocabulary,'casegeneric')])
def test_old_headers_continue_to_select_old_dictionaries(constructor,name):
    vocab=constructor();declarations=vocab.imports([name]) if hasattr(vocab,'imports') else [vocab.declaration(name)]
    from noema.constructed_discourse import normalize_document
    d=normalize_document(dict(schema_version='0.16',lexicon_version='0.16',declarations=declarations,statements=[]))
    assert decode_page(compile_page(d,vocab,max_width=4800.)['shapes'])['document']==d


def test_wrong_and_unknown_editions_are_rejected():
    shapes=cases()[0]['page']['shapes']
    with pytest.raises(ValueError,match='edition'):edition_seven_decode(shapes)
    with pytest.raises(ValueError,match='edition'):decode_page(shapes,GeneralityVocabulary())
    w=PublicWriter(vocabulary());w.keyword('document');w.natural(16);w.natural(9);w.end();w.end()
    with pytest.raises(ValueError,match='edition'):decode_document(render(w.glyphs)['shapes'])


def test_old_local_spelling_is_not_reinterpreted_as_new_shared_word():
    from noema.constructed_discourse import normalize_document
    old=GeneralityVocabulary();name=symbol(Word('compound',('book','fly')),old)
    d=normalize_document(dict(schema_version='0.16',lexicon_version='0.16',declarations=[
        dict(kind='definition',name=name,parameters=[],result='truth',body=truth(True))],statements=[]))
    assert decode_page(compile_page(d,old,max_width=4800.)['shapes'])['document']==d
    with pytest.raises(ValueError,match='public meaning'):compile_page(d)


def test_missing_dependency_and_shadowing_are_rejected():
    w=PublicWriter(vocabulary());w.keyword('document');w.natural(16);w.natural(8)
    w.keyword('import');w.name(vocabulary().declaration('speechrequest')['name']);w.end();w.end()
    with pytest.raises(ValueError,match='Unknown'):decode_document(render(w.glyphs)['shapes'])
    w=PublicWriter(vocabulary());w.keyword('document');w.natural(16);w.natural(8)
    w.keyword('definition');w.name(vocabulary().declaration('speechrequest')['name'])
    w.parameters([]);w.type('truth');w.expr(truth(True),());w.end();w.end()
    with pytest.raises(ValueError,match='shadows'):decode_document(render(w.glyphs)['shapes'])


def test_svg_element_order_does_not_supply_semantics():
    row=cases()[2]
    assert decode_page(from_svg(to_svg(list(reversed(row['page']['shapes'])))))['document']==row['encoded']


@pytest.mark.parametrize('label,expected',[('request',True),('promise',True),('accepted',True),('advice',True),('request-outcome',False),('promise-outcome',False)])
def test_quoted_content_changes_only_realization(label,expected):
    row=next(r for r in cases() if r['label']==label);d=deepcopy(row['encoded'])
    action=next(x for x in d['declarations'] if x['name']==local(('book','fly','fly')))
    body=action['body']['body']
    action['body']['body']=dict(kind='not',arguments=[body])
    assert evaluate_document(d,individuals=('a','b'),situations=('now','later'),primitives=model(),max_steps=1000000)==[dict(kind='assert',value=expected)]


def test_reversing_temporal_roles_rejects_promise_realization():
    row=next(r for r in cases() if r['label']=='promise-outcome');d=deepcopy(row['encoded']);changed=[]
    def reverse(x):
        if isinstance(x,list):
            for y in x:reverse(y)
        elif isinstance(x,dict):
            if x.get('kind')=='lambda' and [p['sort'] for p in x['parameters']]==['situation','situation']:
                x['parameters'].reverse();changed.append(True)
            for y in x.values():reverse(y)
    reverse(d['statements']);assert len(changed)==1
    assert evaluate_document(d,individuals=('a','b'),situations=('now','later'),primitives=model(),max_steps=1000000)==[dict(kind='assert',value=False)]


def test_cli_speech_page_roundtrip(tmp_path,capsys):
    target=tmp_path/'speech.svg'
    assert main(['render',str(ROOT/SOURCES['promise-outcome']),str(target),'--width','4800','--public-names'])==0
    row=next(r for r in cases() if r['label']=='promise-outcome')
    assert json.loads(capsys.readouterr().out)['rows']==row['page']['rows']
    assert main(['decode',str(target),'--native','--public-names'])==0
    assert parse(capsys.readouterr().out)==row['native']
