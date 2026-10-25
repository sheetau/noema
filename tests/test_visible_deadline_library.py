from copy import deepcopy
import json
import pytest
from noema.constructed import parse
from noema.constructed_semantics import evaluate_document
from scripts.visible_deadline_vocabulary import DeadlineVocabulary,ConversationVocabulary,check_quantity_extension,LIBRARIES
from scripts.visible_speech_vocabulary import SpeechVocabulary
from scripts.visible_generality_vocabulary import GeneralityVocabulary
from scripts.visible_selection_vocabulary import SelectionVocabulary
from scripts.visible_quantity_vocabulary import QuantityVocabulary
from scripts.visible_scope_vocabulary import ScopeVocabulary
from scripts.visible_compound_vocabulary import CompoundVocabulary
from scripts.visible_defined_vocabulary import DefinedVocabulary
from scripts.visible_syntax_vocabulary import Vocabulary
from scripts.visible_deadline_page import compile_page,decode_page,decode_document,PublicWriter,main
from scripts.visible_conversation_page import decode_page as edition_nine_decode
from scripts.visible_syntax_geometry import render,to_svg,from_svg
from scripts.visible_word_forms import Word,symbol
from scripts.shared_reference import truth
from scripts.check_visible_deadline_library import (vocabulary,new_names,doc,cases,word_checks,SOURCES,ROOT,model,
    local,expected,TIMES,RANK_ONE,slot,number)
from scripts.visible_deadline_book import compile_book,decode_book,MAX_PAGES,main as book_main


def row(label):return next(r for r in cases() if r['label']==label)
def evaluate(d):return evaluate_document(d,individuals=('a','b'),situations=TIMES,primitives=model(d),max_steps=2000000)
def changed_calls(d,name):
    found=[];target=vocabulary().declaration(name)['name']
    def walk(x):
        if isinstance(x,list):
            for y in x:walk(y)
        elif isinstance(x,dict):
            if x.get('kind')=='call' and x['symbol']==target:found.append(x)
            for y in x.values():walk(y)
    walk(d['statements']);return found


def test_fourteen_definitions_one_reference_and_all_old_words_are_preserved():
    vocab=vocabulary();parent=ConversationVocabulary();data=vocab.document()
    assert (len(data['entries']),len(data['compounds']),len(data['definitions']),len(data['primitives']))==(30,237,245,6)
    assert len(new_names())==15 and check_quantity_extension(parent,vocab)
    for n in parent._order:
        assert vocab.word(n)==parent.word(n) and vocab.declaration(n)==parent.declaration(n)
    source={d['name']:d for spec in LIBRARIES for d in parse((ROOT/spec['library']).read_text(encoding='utf-8'))['declarations']}
    assert {name:vocab._plain_declaration(name) for name in source}==source
    imported={d['name']:d for d in doc(names=new_names())['declarations']}
    assert set(source)-set(imported)=={'normwitness','groundedrule'}
    assert all(source[name]==d for name,d in imported.items())


def test_all_typed_calls_and_quotes_decode_at_the_required_rank():
    rows=word_checks();assert len(rows)==15
    assert {r['name'] for r in rows}==set(new_names())
    assert {r['name'] for r in rows if r['quotation_rank']==1}==RANK_ONE
    assert all(r['glyphs']<=768 and r['shapes']<=4096 for r in rows)


def test_complete_connected_history_recovers_all_native_bodies_and_meanings():
    assert len(cases())==2
    for r in cases():
        assert decode_book([p['shapes'] for p in r['pages']],public_names=True)['document']==r['native']
        assert all(p['glyphs']<=768 and len(p['shapes'])<=4096 for p in r['pages'])
        assert len(r['pages'])<=MAX_PAGES and sum(p['rows'] for p in r['pages'])<=128
        if r['label'] in SOURCES:
            assert parse((ROOT/SOURCES[r['label']]).read_text(encoding='utf-8'))==r['native']
            assert r['result']==expected(r['label'])


@pytest.mark.parametrize('change',['old-meaning','old-body','new-meaning','new-body','primitive','spelling','collision','signature','dependency'])
def test_frozen_edition_rejects_changed_meanings_and_spellings(change):
    data=vocabulary().document()
    if change=='old-meaning':data['entries']['home']['meaning']='different'
    elif change=='old-body':data['definitions']['normrequired']['body']=truth(False)
    elif change=='new-meaning':data['compounds']['deadlinepending']['meaning']='different'
    elif change=='new-body':data['definitions']['deadlinevalid']['body']=truth(True)
    elif change=='primitive':data['definitions']['deadlinewindow']['kind']='primitive'
    elif change=='spelling':data['compounds']['deadlinevalid']['parts'].reverse()
    elif change=='collision':data['compounds']['deadlinevalid']['parts']=data['compounds']['deadlinepending']['parts']
    elif change=='signature':data['compounds']['deadlinepending']['result']='individual'
    else:data['definitions']['deadlinepending']['body']=dict(kind='call',symbol='unknown',arguments=[])
    with pytest.raises(ValueError,match='published meanings'):DeadlineVocabulary(data)


def test_source_dependency_body_cannot_replace_existing_speech_definition(monkeypatch):
    from scripts import visible_deadline_vocabulary as module
    original=module.parse
    def modified(text):
        d=original(text)
        if any(x['name']=='deadlinevalid' for x in d['declarations']):
            d=deepcopy(d);next(x for x in d['declarations'] if x['name']=='normrequired')['body']=truth(False)
        return d
    monkeypatch.setattr(module,'parse',modified)
    with pytest.raises(ValueError,match='dependency meaning'):DeadlineVocabulary()


@pytest.mark.parametrize('field',['meaning','role'])
def test_source_dependency_contract_must_match_previous_edition(monkeypatch,field):
    from scripts import visible_deadline_vocabulary as module
    original=module.json.loads
    def modified(text,*a,**kw):
        d=original(text,*a,**kw)
        if isinstance(d,dict) and d.get('document')==LIBRARIES[0]['library']:
            if field=='meaning':d['definitions']['normrequired']='different'
            else:d['public_contracts']['normrequired']['arguments'][0]['role']='different'
        return d
    monkeypatch.setattr(module.json,'loads',modified)
    with pytest.raises(ValueError,match='dependency meaning'):DeadlineVocabulary()


def test_registration_order_does_not_change_geometry():
    data=vocabulary().document()
    for field in ('entries','compounds','definitions','primitives'):data[field]=dict(reversed(list(data[field].items())))
    changed=DeadlineVocabulary(data)
    assert changed.imports(list(reversed(new_names())))==vocabulary().imports(new_names())
    assert changed.document()==vocabulary().document()


@pytest.mark.parametrize('constructor,name',[(Vocabulary,'home'),(DefinedVocabulary,'candidateexists'),
    (CompoundVocabulary,'chronology'),(ScopeVocabulary,'referentat'),(QuantityVocabulary,'rationaladd'),
    (SelectionVocabulary,'selectnumber'),(GeneralityVocabulary,'casegeneric'),(SpeechVocabulary,'speechaccepted'),(ConversationVocabulary,'answerpartial')])
def test_old_headers_select_the_original_dictionary(constructor,name):
    from noema.constructed_discourse import normalize_document
    vocab=constructor();ds=vocab.imports([name]) if hasattr(vocab,'imports') else [vocab.declaration(name)]
    d=normalize_document(dict(schema_version='0.16',lexicon_version='0.16',declarations=ds,statements=[]))
    assert decode_page(compile_page(d,vocab,max_width=4800.)['shapes'])['document']==d


def test_wrong_and_unknown_editions_are_rejected():
    shapes=row('dictionary')['pages'][0]['shapes']
    with pytest.raises(ValueError,match='edition'):edition_nine_decode(shapes)
    with pytest.raises(ValueError,match='edition'):decode_page(shapes,ConversationVocabulary())
    w=PublicWriter(vocabulary());w.keyword('document');w.natural(16);w.natural(11);w.end();w.end()
    with pytest.raises(ValueError,match='edition'):decode_document(render(w.glyphs)['shapes'])


def test_old_local_spelling_is_not_reinterpreted_as_new_public_word():
    from noema.constructed_discourse import normalize_document
    old=ConversationVocabulary();name=symbol(Word('compound',('book','above','assessmentvalid')),old)
    d=normalize_document(dict(schema_version='0.16',lexicon_version='0.16',declarations=[
        dict(kind='definition',name=name,parameters=[],result='truth',body=truth(True))],statements=[]))
    assert decode_page(compile_page(d,old,max_width=4800.)['shapes'])['document']==d
    with pytest.raises(ValueError,match='public meaning'):compile_page(d)


def test_missing_dependencies_and_shadowed_public_meanings_are_rejected():
    w=PublicWriter(vocabulary());w.keyword('document');w.natural(16);w.natural(10)
    w.keyword('import');w.name(vocabulary().declaration('promisedeadline')['name']);w.end();w.end()
    with pytest.raises(ValueError,match='Unknown'):decode_document(render(w.glyphs)['shapes'])
    w=PublicWriter(vocabulary());w.keyword('document');w.natural(16);w.natural(10)
    w.keyword('definition');w.name(vocabulary().declaration('deadlinepending')['name'])
    w.parameters([]);w.type('truth');w.expr(truth(True),());w.end();w.end()
    with pytest.raises(ValueError,match='shadows'):decode_document(render(w.glyphs)['shapes'])


def test_svg_element_order_is_not_the_word_order():
    r=row('dictionary')
    assert decode_book([from_svg(to_svg(list(reversed(r['pages'][0]['shapes']))))])['document']==r['encoded']


def test_reference_basis_matches_the_native_primitive():
    from noema.meaning_catalog import load_catalog
    from scripts.shared_situation_reference import document,basis,BASIS
    assert load_catalog(ROOT,BASIS).document==document()
    assert json.loads((ROOT/BASIS).read_text(encoding='utf-8'))==basis()


@pytest.mark.parametrize('change',['wrong-context','missing-address'])
def test_unknown_situation_reference_is_not_given_a_default(change):
    d=deepcopy(row('history')['encoded']);target=next(x for x in d['declarations'] if x['name']==local('issued'))['body']
    target['arguments'][0 if change=='wrong-context' else 1]=(
        dict(kind='call',symbol=vocabulary().declaration('nao')['name'],arguments=[]) if change=='wrong-context' else number(100))
    with pytest.raises(ValueError,match='Unknown situation address'):evaluate(d)


@pytest.mark.parametrize('assignment',[tuple(reversed(TIMES)),TIMES[1:]+TIMES[:1]])
def test_address_numbers_do_not_impose_the_host_time_order(assignment):
    d=row('history')['encoded']
    assert evaluate_document(d,individuals=('a','b'),situations=TIMES,primitives=model(d,assignment=assignment),max_steps=2000000)==expected('history')


def test_performance_at_deadline_changes_compliance_but_not_the_promise():
    d=deepcopy(row('history')['encoded'])
    body=next(x for x in d['declarations'] if x['name']==local('actform'))['body']['body']
    body['arguments'][1]['arguments'][1]['symbol']=local('due')
    assert [r['value'] for r in evaluate(d)]==[True,True,False,False,True,True,False,False,False,False,True]


@pytest.mark.parametrize('name',['recognized','applicable','supports'])
def test_missing_ground_blocks_the_requirement_without_changing_actual_action(name):
    d=deepcopy(row('history')['encoded']);next(x for x in d['declarations'] if x['name']==local(name))['body']=truth(False)
    assert [r['value'] for r in evaluate(d)]==[False]*9+[True,False]


@pytest.mark.parametrize('name',['authorized','releases'])
def test_both_release_components_are_required(name):
    d=deepcopy(row('history')['encoded']);next(x for x in d['declarations'] if x['name']==local(name))['body']=truth(False)
    wanted=expected('history');wanted[5]['value']=False
    assert evaluate(d)==wanted


@pytest.mark.parametrize('change',['reordered','duplicated','missing-first','truncated'])
def test_visible_continuity_rejects_missing_or_repeated_pages(change):
    pages=[p['shapes'] for p in row('history')['pages']];assert len(pages)>2
    if change=='reordered':pages[0],pages[1]=pages[1],pages[0]
    elif change=='duplicated':pages.insert(1,pages[0])
    elif change=='missing-first':pages=pages[1:]
    else:pages=pages[:1]
    with pytest.raises(ValueError,match='book row|final marker'):decode_book(pages)


def test_book_does_not_relax_single_page_or_document_budgets():
    r=row('history')
    with pytest.raises(ValueError,match='Payload glyph budget'):compile_page(r['encoded'])
    with pytest.raises(ValueError,match='page count'):decode_book([[]]*(MAX_PAGES+1))
    with pytest.raises(ValueError,match='primitive budget'):decode_book([r['pages'][0]['shapes']*2])


def test_book_cli_decodes_using_only_svg_pages(tmp_path,capsys):
    r=row('history');paths=[]
    for i,svg in enumerate(r['svgs']):
        path=tmp_path/(str(i)+'.svg');path.write_text(svg,encoding='utf-8');paths.append(str(path))
    assert book_main(['decode',*paths,'--native','--public-names'])==0
    assert parse(capsys.readouterr().out)==r['native']
