from copy import deepcopy
import json
import pytest
from noema.constructed import parse
from noema.constructed_discourse import normalize_document
from scripts.visible_evidence_vocabulary import EvidenceVocabulary,DeadlineVocabulary,check_quantity_extension,LIBRARIES
from scripts.visible_evidence_page import compile_page,decode_page,decode_document,PublicWriter
from scripts.visible_evidence_book import compile_book,decode_book,MAX_PAGES,main as book_main
from scripts.visible_deadline_page import decode_page as previous_decode_page
from scripts.visible_deadline_book import decode_book as previous_decode_book
from scripts.visible_syntax_geometry import render,to_svg,from_svg
from scripts.visible_word_forms import Word,symbol
from scripts.shared_reference import truth
from scripts.check_visible_evidence_library import (vocabulary,new_names,doc,case,cases,word_checks,SOURCES,ROOT,LIBRARIES,
    local,expected,scenes,model,evaluate,LABELS,number,ranks,ref,quote,eq)


def test_new_definitions_and_choice_keep_all_existing_words():
    vocab=vocabulary();parent=DeadlineVocabulary();data=vocab.document()
    assert (len(data['entries']),len(data['compounds']),len(data['definitions']),len(data['primitives']))==(30,282,289,7)
    assert len(new_names())==45 and check_quantity_extension(parent,vocab)
    for n in parent._order:
        assert vocab.word(n)==parent.word(n) and vocab.declaration(n)==parent.declaration(n)
        assert vocab.entry(n)==parent.entry(n)
    source={d['name']:d for spec in LIBRARIES for d in parse((ROOT/spec['library']).read_text(encoding='utf-8'))['declarations']}
    assert {n:vocab._plain_declaration(n) for n in source}==source
    imported={d['name']:d for d in doc(names=new_names())['declarations']}
    assert set(imported)==set(source)
    assert all(source[n]==d for n,d in imported.items())

def test_typed_calls_and_quotes_decode_all_45_words():
    rows=word_checks();assert len(rows)==45
    assert {r['name'] for r in rows}==set(new_names())
    assert all(r['quotation_rank'] in (0,1) and r['glyphs']<=768 and r['shapes']<=4096 for r in rows)
    assert sum(r['quotation_rank'] for r in rows)==16

@pytest.mark.parametrize('name',['beliefaccepted','evidenceentails','beliefcorpus','claimcontents','evidenceused'])
def test_rank_zero_cannot_quote_content_evaluation(name):
    quoted=quote(ref(vocabulary().declaration(name)['name']))
    with pytest.raises(ValueError,match='rank|Rank|evaluation|Evaluation'):
        normalize_document(dict(schema_version='0.16',lexicon_version='0.16',declarations=vocabulary().imports([name]),
            statements=[dict(kind='assert',body=eq(quoted,quoted))]))

@pytest.mark.parametrize('label',LABELS)
def test_complete_examples_recover_native_bodies_and_results(label):
    r=case(label)
    assert parse((ROOT/SOURCES[label]).read_text(encoding='utf-8'))==r['native']
    assert r['result']==expected(label) and len(r['result'])==14
    assert 1<len(r['pages'])<=MAX_PAGES and sum(p['rows'] for p in r['pages'])<=128
    assert all(p['glyphs']<=768 and len(p['shapes'])<=4096 for p in r['pages'])
    primitive_names={vocabulary()._by_symbol[d['name']] for d in r['encoded']['declarations'] if d['kind']=='primitive'}
    assert primitive_names==({'aki','nao','situationslot','claimchoice'} if label.startswith('revision-') else {'aki','nao','birdone','situationslot'})

@pytest.mark.parametrize('change',['old-meaning','old-body','new-meaning','new-body','primitive','spelling','signature','dependency'])
def test_edition_rejects_changed_meanings_and_spellings(change):
    data=vocabulary().document()
    if change=='old-meaning':data['entries']['home']['meaning']='different'
    elif change=='old-body':data['definitions']['deadlinevalid']['body']=truth(False)
    elif change=='new-meaning':data['compounds']['beliefaccepted']['meaning']='different'
    elif change=='new-body':data['definitions']['proofverified']['body']=truth(False)
    elif change=='primitive':data['primitives']['claimchoice']['result']='individual'
    elif change=='spelling':data['compounds']['beliefaccepted']['parts'].reverse()
    elif change=='signature':data['compounds']['beliefaccepted']['result']='individual'
    else:data['definitions']['proofverified']['body']=dict(kind='call',symbol='unknown',arguments=[])
    with pytest.raises(ValueError,match='published meanings'):EvidenceVocabulary(data)

@pytest.mark.parametrize('name',['candidatenecessary','proofsupports'])
def test_reused_dependency_cannot_change_in_either_source(monkeypatch,name):
    from scripts import visible_evidence_vocabulary as module
    original=module.parse
    def modified(text):
        d=original(text)
        if any(x['name']=='informationexpanded' for x in d['declarations']):
            d=deepcopy(d);next(x for x in d['declarations'] if x['name']==name)['body']=truth(False)
        return d
    monkeypatch.setattr(module,'parse',modified)
    with pytest.raises(ValueError,match='dependency meaning'):EvidenceVocabulary()

@pytest.mark.parametrize('field',['meaning','role','context'])
def test_repeated_new_dependency_must_keep_its_contract(monkeypatch,field):
    from scripts import visible_evidence_vocabulary as module
    original=module.json.loads
    def modified(text,*a,**kw):
        d=original(text,*a,**kw)
        if isinstance(d,dict) and d.get('document')==LIBRARIES[1]['library']:
            if field=='meaning':d['definitions']['proofsupports']='different'
            else:d['public_contracts']['proofsupports']['arguments'][0]['role' if field=='role' else 'interpretation']='different'
        return d
    monkeypatch.setattr(module.json,'loads',modified)
    with pytest.raises(ValueError,match='Repeated dependency meaning'):EvidenceVocabulary()

def test_registration_order_does_not_change_words_or_meanings():
    data=vocabulary().document()
    for field in ('entries','compounds','definitions','primitives'):data[field]=dict(reversed(list(data[field].items())))
    changed=EvidenceVocabulary(data)
    assert changed.imports(list(reversed(new_names())))==vocabulary().imports(new_names())

@pytest.mark.parametrize('edition',range(1,11))
def test_old_headers_select_original_dictionary(edition):
    from scripts.visible_syntax_vocabulary import Vocabulary
    from scripts.visible_defined_vocabulary import DefinedVocabulary
    from scripts.visible_compound_vocabulary import CompoundVocabulary
    from scripts.visible_scope_vocabulary import ScopeVocabulary
    from scripts.visible_quantity_vocabulary import QuantityVocabulary
    from scripts.visible_selection_vocabulary import SelectionVocabulary
    from scripts.visible_generality_vocabulary import GeneralityVocabulary
    from scripts.visible_speech_vocabulary import SpeechVocabulary
    from scripts.visible_conversation_vocabulary import ConversationVocabulary
    constructors=[Vocabulary,DefinedVocabulary,CompoundVocabulary,ScopeVocabulary,QuantityVocabulary,SelectionVocabulary,
        GeneralityVocabulary,SpeechVocabulary,ConversationVocabulary,DeadlineVocabulary]
    vocab=constructors[edition-1]();ds=vocab.imports(['home']) if hasattr(vocab,'imports') else [vocab.declaration('home')]
    d=normalize_document(dict(schema_version='0.16',lexicon_version='0.16',declarations=ds,statements=[]))
    shapes=compile_page(d,vocab,max_width=6400.)['shapes']
    assert decode_page(shapes)['document']==decode_book([shapes])['document']==d

def test_wrong_and_unknown_editions_are_rejected():
    r=case('dictionary')
    with pytest.raises(ValueError,match='edition'):previous_decode_book([p['shapes'] for p in r['pages']])
    with pytest.raises(ValueError,match='edition'):decode_book([p['shapes'] for p in r['pages']],DeadlineVocabulary())
    w=PublicWriter(vocabulary());w.keyword('document');w.natural(16);w.natural(12);w.end();w.end()
    with pytest.raises(ValueError,match='edition'):decode_document(render(w.glyphs)['shapes'])

def test_old_local_spelling_is_not_reinterpreted_as_a_new_shared_word():
    old=DeadlineVocabulary();name=symbol(Word('compound',('book','rain','inside')),old)
    d=normalize_document(dict(schema_version='0.16',lexicon_version='0.16',declarations=[
        dict(kind='definition',name=name,parameters=[],result='truth',body=truth(True))],statements=[]))
    assert decode_page(compile_page(d,old,max_width=6400.)['shapes'])['document']==d
    with pytest.raises(ValueError,match='public meaning'):compile_page(d)

def test_missing_dependencies_and_shadowed_definitions_are_rejected():
    w=PublicWriter(vocabulary());w.keyword('document');w.natural(16);w.natural(11)
    w.keyword('import');w.name(vocabulary().declaration('evidenceused')['name']);w.end();w.end()
    with pytest.raises(ValueError,match='Unknown'):decode_document(render(w.glyphs)['shapes'])
    w=PublicWriter(vocabulary());w.keyword('document');w.natural(16);w.natural(11)
    w.keyword('definition');w.name(vocabulary().declaration('beliefupdated')['name'])
    w.parameters([]);w.type('truth');w.expr(truth(True),());w.end();w.end()
    with pytest.raises(ValueError,match='shadows'):decode_document(render(w.glyphs)['shapes'])

def test_shape_list_order_is_not_visible_reading_order():
    r=case('dictionary')
    assert decode_book([from_svg(to_svg(list(reversed(p['shapes'])))) for p in r['pages']])['document']==r['encoded']

@pytest.mark.parametrize('change',['reordered','duplicated','missing-first','truncated'])
def test_visible_continuity_rejects_bad_page_sequences(change):
    pages=[p['shapes'] for p in case('revision-filter')['pages']]
    if change=='reordered':pages[0],pages[1]=pages[1],pages[0]
    elif change=='duplicated':pages.insert(1,pages[0])
    elif change=='missing-first':pages=pages[1:]
    else:pages=pages[:1]
    with pytest.raises(ValueError,match='book row|reordered row|final marker|document header'):decode_book(pages)

def test_transport_keeps_original_budgets():
    r=case('revision-filter')
    with pytest.raises(ValueError,match='Payload glyph budget'):compile_page(r['encoded'])
    with pytest.raises(ValueError,match='page count'):decode_book([[]]*(MAX_PAGES+1))
    with pytest.raises(ValueError,match='primitive budget'):decode_book([r['pages'][0]['shapes']*2])

@pytest.mark.parametrize('label',['revision-filter','evidence-inference'])
def test_situation_address_numbers_are_not_time_or_truth(label):
    d=case(label)['encoded']
    assert evaluate(d,label,assignment=tuple(reversed(scenes(label))))==expected(label)

@pytest.mark.parametrize('field',['received','adopts','available','aware'])
def test_missing_relation_does_not_create_a_supported_update(field):
    label='revision-filter';d=deepcopy(case(label)['encoded'])
    next(x for x in d['declarations'] if x['name']==local(field))['body']=truth(False)
    result=[r['value'] for r in evaluate(d,label)]
    assert result[1:5]==[False]*4
    assert result[0] is (field not in ('received','available'))

def test_missing_observation_invalidates_the_relay_certificate():
    label='evidence-relay';d=deepcopy(case(label)['encoded'])
    next(x for x in d['declarations'] if x['name']==local('observed'))['body']=truth(False)
    result=[r['value'] for r in evaluate(d,label)]
    assert result[:5]==[False]*5 and result[5:8]==[True,False,False]

def test_missing_inference_dependency_cannot_silently_weaken_its_premise_list():
    label='evidence-inference';d=deepcopy(case(label)['encoded'])
    next(x for x in d['declarations'] if x['name']==local('parents'))['body']=truth(False)
    assert [r['value'] for r in evaluate(d,label)][:2]==[False,False]

def test_claim_choice_does_not_make_a_false_supported_update_true():
    result=case('revision-misleading')['result']
    assert [result[i]['value'] for i in (0,1,2,4,7,10)]==[True,True,True,True,False,False]

def test_book_cli_decodes_only_svg_without_a_document_sidecar(tmp_path,capsys):
    r=case('revision-filter');paths=[]
    for i,svg in enumerate(r['svgs']):
        path=tmp_path/(str(i)+'.svg');path.write_text(svg,encoding='utf-8');paths.append(str(path))
    assert book_main(['decode',*paths,'--native','--public-names'])==0
    assert parse(capsys.readouterr().out)==r['native']
