from copy import deepcopy
import json
import pytest
from noema.constructed import parse
from noema.constructed_semantics import evaluate_document
from scripts.visible_conversation_vocabulary import ConversationVocabulary,SpeechVocabulary,check_quantity_extension,LIBRARIES
from scripts.visible_generality_vocabulary import GeneralityVocabulary
from scripts.visible_selection_vocabulary import SelectionVocabulary
from scripts.visible_quantity_vocabulary import QuantityVocabulary
from scripts.visible_scope_vocabulary import ScopeVocabulary
from scripts.visible_compound_vocabulary import CompoundVocabulary
from scripts.visible_defined_vocabulary import DefinedVocabulary
from scripts.visible_syntax_vocabulary import Vocabulary
from scripts.visible_conversation_page import compile_page,decode_page,decode_document,PublicWriter,main
from scripts.visible_speech_page import decode_page as edition_eight_decode
from scripts.visible_syntax_geometry import render,to_svg,from_svg
from scripts.visible_word_forms import Word,symbol
from scripts.shared_reference import truth
from scripts.check_visible_conversation_library import (vocabulary,new_names,doc,cases,word_checks,SOURCES,ROOT,model,
    local,form_names,unary_definitions,pair_definitions)


def row(label):return next(r for r in cases() if r['label']==label)
def evaluate(d):return evaluate_document(d,individuals=('a','b'),situations=('start','middle','end'),primitives=model(d),max_steps=1000000)
def changed_calls(d,name):
    found=[];target=vocabulary().declaration(name)['name']
    def walk(x):
        if isinstance(x,list):
            for y in x:walk(y)
        elif isinstance(x,dict):
            if x.get('kind')=='call' and x['symbol']==target:found.append(x)
            for y in x.values():walk(y)
    walk(d['statements']);return found


def test_thirty_four_new_definitions_and_all_old_words_are_preserved():
    vocab=vocabulary();parent=SpeechVocabulary();data=vocab.document()
    assert (len(data['entries']),len(data['compounds']),len(data['definitions']),len(data['primitives']))==(30,222,231,5)
    assert len(new_names())==34 and check_quantity_extension(parent,vocab)
    for n in parent._order:
        assert vocab.word(n)==parent.word(n) and vocab.declaration(n)==parent.declaration(n)
    source={d['name']:d for spec in LIBRARIES for d in parse((ROOT/spec['library']).read_text(encoding='utf-8'))['declarations']}
    assert {d['name']:d for d in doc(names=new_names())['declarations']}==source


def test_all_typed_calls_and_quotes_decode_at_the_required_rank():
    rows=word_checks();assert len(rows)==34
    assert {r['name'] for r in rows}==set(new_names())
    assert {r['name'] for r in rows if r['quotation_rank']==1}=={'commitmentaccepted'}
    assert all(r['glyphs']<=768 and r['shapes']<=4096 for r in rows)


def test_ten_documents_recover_all_native_bodies_and_meanings():
    assert len(cases())==10
    for r in cases():
        assert decode_page(r['page']['shapes'],public_names=True)['document']==r['native']
        assert r['glyphs']<=768 and len(r['page']['shapes'])<=4096
        if r['label'] in SOURCES:
            assert parse((ROOT/SOURCES[r['label']]).read_text(encoding='utf-8'))==r['native']
            assert r['result']==[dict(kind='assert',value=True)]


@pytest.mark.parametrize('change',['old-meaning','old-body','new-meaning','new-body','primitive','spelling','collision','signature','dependency'])
def test_frozen_edition_rejects_changed_meanings_and_spellings(change):
    data=vocabulary().document()
    if change=='old-meaning':data['entries']['home']['meaning']='different'
    elif change=='old-body':data['definitions']['speechaccepted']['body']=truth(False)
    elif change=='new-meaning':data['compounds']['answerpartial']['meaning']='different'
    elif change=='new-body':data['definitions']['commitmenthas']['body']=truth(True)
    elif change=='primitive':data['definitions']['utteranceinstance']['kind']='primitive'
    elif change=='spelling':data['compounds']['answerconsistent']['parts'].reverse()
    elif change=='collision':data['compounds']['answerconsistent']['parts']=data['compounds']['answerpartial']['parts']
    elif change=='signature':data['compounds']['answerpartial']['result']='individual'
    else:data['definitions']['answerpartial']['body']=dict(kind='call',symbol='unknown',arguments=[])
    with pytest.raises(ValueError,match='published meanings'):ConversationVocabulary(data)


def test_source_dependency_body_cannot_replace_existing_speech_definition(monkeypatch):
    from scripts import visible_conversation_vocabulary as module
    original=module.parse
    def modified(text):
        d=original(text)
        if any(x['name']=='commitmentvalid' for x in d['declarations']):
            d=deepcopy(d);next(x for x in d['declarations'] if x['name']=='speechaccepted')['body']=truth(False)
        return d
    monkeypatch.setattr(module,'parse',modified)
    with pytest.raises(ValueError,match='dependency meaning'):ConversationVocabulary()


@pytest.mark.parametrize('field',['meaning','role'])
def test_source_dependency_contract_must_match_previous_edition(monkeypatch,field):
    from scripts import visible_conversation_vocabulary as module
    original=module.json.loads
    def modified(text,*a,**kw):
        d=original(text,*a,**kw)
        if isinstance(d,dict) and d.get('document')==LIBRARIES[1]['library']:
            if field=='meaning':d['definitions']['speechaccepted']='different'
            else:d['public_contracts']['speechaccepted']['arguments'][0]['role']='different'
        return d
    monkeypatch.setattr(module.json,'loads',modified)
    with pytest.raises(ValueError,match='dependency meaning'):ConversationVocabulary()


def test_registration_order_does_not_change_geometry():
    data=vocabulary().document()
    for field in ('entries','compounds','definitions','primitives'):data[field]=dict(reversed(list(data[field].items())))
    changed=ConversationVocabulary(data)
    assert changed.imports(list(reversed(new_names())))==vocabulary().imports(new_names())
    r=row('partial-answer');assert compile_page(r['encoded'],changed,max_width=4800.)==r['page']


@pytest.mark.parametrize('constructor,name',[(Vocabulary,'home'),(DefinedVocabulary,'candidateexists'),
    (CompoundVocabulary,'chronology'),(ScopeVocabulary,'referentat'),(QuantityVocabulary,'rationaladd'),
    (SelectionVocabulary,'selectnumber'),(GeneralityVocabulary,'casegeneric'),(SpeechVocabulary,'speechaccepted')])
def test_old_headers_select_the_original_dictionary(constructor,name):
    from noema.constructed_discourse import normalize_document
    vocab=constructor();ds=vocab.imports([name]) if hasattr(vocab,'imports') else [vocab.declaration(name)]
    d=normalize_document(dict(schema_version='0.16',lexicon_version='0.16',declarations=ds,statements=[]))
    assert decode_page(compile_page(d,vocab,max_width=4800.)['shapes'])['document']==d


def test_wrong_and_unknown_editions_are_rejected():
    shapes=row('dictionary')['page']['shapes']
    with pytest.raises(ValueError,match='edition'):edition_eight_decode(shapes)
    with pytest.raises(ValueError,match='edition'):decode_page(shapes,SpeechVocabulary())
    w=PublicWriter(vocabulary());w.keyword('document');w.natural(16);w.natural(10);w.end();w.end()
    with pytest.raises(ValueError,match='edition'):decode_document(render(w.glyphs)['shapes'])


def test_old_local_spelling_is_not_reinterpreted_as_new_public_word():
    from noema.constructed_discourse import normalize_document
    old=SpeechVocabulary();name=symbol(Word('compound',('book','aki','assessmentvalid')),old)
    d=normalize_document(dict(schema_version='0.16',lexicon_version='0.16',declarations=[
        dict(kind='definition',name=name,parameters=[],result='truth',body=truth(True))],statements=[]))
    assert decode_page(compile_page(d,old,max_width=4800.)['shapes'])['document']==d
    with pytest.raises(ValueError,match='public meaning'):compile_page(d)


def test_missing_dependencies_and_shadowed_public_meanings_are_rejected():
    w=PublicWriter(vocabulary());w.keyword('document');w.natural(16);w.natural(9)
    w.keyword('import');w.name(vocabulary().declaration('commitmentaccepted')['name']);w.end();w.end()
    with pytest.raises(ValueError,match='Unknown'):decode_document(render(w.glyphs)['shapes'])
    w=PublicWriter(vocabulary());w.keyword('document');w.natural(16);w.natural(9)
    w.keyword('definition');w.name(vocabulary().declaration('answerpartial')['name'])
    w.parameters([]);w.type('truth');w.expr(truth(True),());w.end();w.end()
    with pytest.raises(ValueError,match='shadows'):decode_document(render(w.glyphs)['shapes'])


def test_svg_element_order_is_not_the_word_order():
    r=row('corrected')
    assert decode_page(from_svg(to_svg(list(reversed(r['page']['shapes'])))))['document']==r['encoded']


@pytest.mark.parametrize('label,index',[('partial-answer',0),('complete-answer',2),('paired-answer',0),('paired-projection',1)])
def test_changed_answer_relation_changes_the_decoded_assertion(label,index):
    d=deepcopy(row(label)['encoded']);names=(unary_definitions() if label in ('partial-answer','complete-answer') else pair_definitions())[0]
    next(x for x in d['declarations'] if x['name']==names[index])['body']=truth(True)
    assert evaluate(d)==[dict(kind='assert',value=False)]


@pytest.mark.parametrize('label,name,index',[('accepted','commitmentaccepted',2),('corrected','commitmentcorrected',2),
    ('withdrawn','commitmentwithdrawn',2),('linked','conversationlinked',4)])
def test_owner_column_cannot_change_while_description_column_stays_fixed(label,name,index):
    d=deepcopy(row(label)['encoded']);body=changed_calls(d,name)[0]
    target=body['arguments'][index]['items'][-1]
    a=vocabulary().declaration('aki')['name'];b=vocabulary().declaration('nao')['name']
    target['symbol']=a if target['symbol']==b else b
    assert evaluate(d)==[dict(kind='assert',value=False)]


@pytest.mark.parametrize('label,expected',[('accepted',True),('corrected',True),('withdrawn',True),('linked',True),('claim-truths',False)])
def test_record_updates_do_not_evaluate_quoted_answer_truth(label,expected):
    d=deepcopy(row(label)['encoded']);form=next(x for x in d['declarations'] if x['name']==form_names()[0])
    form['body']['content']['body']=truth(True)
    assert evaluate(d)==[dict(kind='assert',value=expected)]


def test_subject_description_requires_matching_denotation():
    d=deepcopy(row('accepted')['encoded']);body=changed_calls(d,'commitmentaccepted')[0]
    name=vocabulary().declaration('nao')['name']
    body['arguments'][-1]['body']['symbol']=name
    # Keep the new stored description equal to the proposed quoted application;
    # only its denotation disagrees with the presented subject.
    body['arguments'][3]['items'][1]['arguments'][1]['body']['symbol']=name
    assert evaluate(d)==[dict(kind='assert',value=False)]


def test_reversing_three_point_order_breaks_history_links():
    d=deepcopy(row('linked')['encoded']);calls=changed_calls(d,'conversationlinked');assert len(calls)==2
    for body in calls:body['arguments'][-1]['parameters'].reverse()
    assert evaluate(d)==[dict(kind='assert',value=False)]


def test_cli_conversation_page_roundtrip(tmp_path,capsys):
    target=tmp_path/'conversation.svg';r=row('accepted')
    assert main(['render',str(ROOT/SOURCES['accepted']),str(target),'--width','4800','--public-names'])==0
    assert json.loads(capsys.readouterr().out)['rows']==r['page']['rows']
    assert main(['decode',str(target),'--native','--public-names'])==0
    assert parse(capsys.readouterr().out)==r['native']
