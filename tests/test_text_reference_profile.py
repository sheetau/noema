from copy import deepcopy
from fractions import Fraction
import pytest
from noema.constructed_semantics import evaluate_document
from scripts.text_reference_profile import TextReferenceVocabulary,TextPresentation,PARAMETERS
from scripts.check_kant_text_reference import (
    vocabulary,document,source_excerpt,backprojection,bridge,restored,diagnostics,names,interpret)
from scripts.visible_senses_vocabulary import SensesVocabulary
from scripts.visible_vectors_vocabulary import VectorsVocabulary
from scripts.visible_collection import decode_collection
from scripts.visible_syntax_geometry import from_svg
from scripts.check_kant_text_reference import OUT


def test_profile_keeps_common_core_and_all_previously_published_spellings():
    core=SensesVocabulary();profile=vocabulary();earlier=VectorsVocabulary()
    assert len(core._words)==375 and len(profile._words)==378
    for field in ('entries','compounds','definitions','primitives'):
        assert all(profile.document()[field][n]==d for n,d in core.document()[field].items())
    assert not ({profile._symbols[n] for n in PARAMETERS}&set(earlier._by_symbol))
    assert len(set(profile._symbols.values()))==378


def test_original_assertion_has_explicit_reference_definitions_and_no_open_parameters():
    doc=restored()['document'];assert doc==document()
    assert len(doc['declarations'])==7 and len(doc['statements'])==1
    assert all(not d['parameters'] for d in doc['declarations'] if d['kind']=='definition')
    assert backprojection(doc)==source_excerpt()
    assert bridge()['closed_source_assertions']==1
    assert bridge()['full_sentence_contents_migrated'] is False
    assert [r['range'] for r in bridge()['sentence_locations']]==[[0,125],[126,292]]


def test_source_and_visible_assertion_use_same_context_and_keep_reference_identity():
    assert len(diagnostics())==4


def test_other_context_changes_order_without_changing_the_word_meanings():
    model=TextPresentation('now',{'now':{(3,1):'x',(3,2):'y'},'other':{(3,1):'y',(3,2):'x'}})
    assert model.before('x','y','now') is True
    assert model.before('x','y','other') is False
    assert model.before('x','x','now') is False
    assert model.reference('now',Fraction(3),Fraction(2))=='y'
    assert model.reference('other',Fraction(3),Fraction(2))=='x'


@pytest.mark.parametrize('value',[0,-1,Fraction(1,2),True,3.0,'3'])
def test_invalid_sentence_positions_are_rejected(value):
    model=TextPresentation('now',{'now':{(3,1):'x'}})
    with pytest.raises(ValueError):model.reference('now',value,1)
    with pytest.raises(ValueError):model.reference('now',3,value)


def test_unknown_context_occurrence_and_position_never_become_false_or_default():
    model=TextPresentation('now',{'now':{(3,1):'x'}})
    for request in [lambda:model.reference('now',3,2),lambda:model.reference('other',3,1),
                    lambda:model.before('x','y','now'),lambda:model.before('x','x','other')]:
        with pytest.raises(ValueError,match='Unknown'):request()
    with pytest.raises(ValueError):interpret(document(),model)
    with pytest.raises(ValueError,match='Unknown'):TextPresentation('other',{'now':{}})


def test_two_sentence_occurrences_cannot_silently_be_one_node():
    with pytest.raises(ValueError,match='Ambiguous'):TextPresentation('now',{'now':{(3,1):'x',(3,2):'x'}})


def test_changed_reference_definition_is_not_backprojected_as_old_evidence():
    doc=deepcopy(document());target=next(d for d in doc['declarations'] if d['name']==names()['hzzr'])
    target['body']['arguments'][-1]['numerator']=1
    with pytest.raises(ValueError,match='Changed migration'):backprojection(doc)


def test_common_core_reader_rejects_an_unselected_optional_profile():
    pages=[from_svg(p.read_text(encoding='utf-8')) for p in sorted(OUT.glob('*.svg'))]
    with pytest.raises(ValueError):decode_collection(pages,SensesVocabulary())


def test_native_assertion_calls_the_relation_instead_of_replacing_it_with_true():
    # Wiring diagnostic deliberately overrides the public order interpretation;
    # it is not presented as a valid reading of these two sentence positions.
    model=TextPresentation('now',{'now':{(3,1):'x',(3,2):'y'}})
    handlers=model.handlers();handlers['textbefore']=lambda *args:False
    mapped={vocabulary()._symbols[n]:f for n,f in handlers.items()}
    result=evaluate_document(document(),individuals=('x','y'),situations=('now',),primitives=mapped)
    assert result[0]['value'] is False
