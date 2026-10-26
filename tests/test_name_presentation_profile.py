from copy import deepcopy
from fractions import Fraction
import pytest
from noema.constructed_semantics import FunctionValue
from scripts.name_presentation_profile import NamePresentation,scalar_text,text_expression,PARAMETERS,FIELDS
from scripts.check_einstein_name_presentation import (
    vocabulary,document,source_excerpt,backprojection,bridge,restored,diagnostics,accessor_diagnostics,
    model_for,interpret,visible_form,names,OUT)
from scripts.text_reference_profile import TextReferenceVocabulary
from scripts.visible_vectors_vocabulary import VectorsVocabulary
from scripts.visible_collection import decode_collection
from scripts.visible_syntax_geometry import from_svg


def test_optional_profile_preserves_all_prior_entries_and_spelling_identity():
    prior=TextReferenceVocabulary();current=vocabulary();math=VectorsVocabulary()
    assert len(prior._words)==378 and len(current._words)==383
    for field in ('entries','compounds','definitions','primitives'):
        assert all(current.document()[field][n]==d for n,d in prior.document()[field].items())
    assert not ({current._symbols[n] for n in PARAMETERS}&set(math._by_symbol))
    assert len(set(current._symbols.values()))==383


def test_real_author_statement_and_visible_identifier_survive_geometry():
    doc=restored()['document'];assert doc==document()
    assert len(doc['declarations'])==19 and len(doc['statements'])==2
    assert backprojection(doc)==source_excerpt()
    assert visible_form(doc)==dict(designation=names()['eird'],language='de',text='A. Einstein',context=names()['eirg'])
    assert bridge()['closed_source_assertions']==1 and bridge()['orthographic_annotation_assertions']==1


def test_all_source_relationships_remain_independent_and_each_role_is_distinguished():
    rows=diagnostics();assert len(rows)==22
    assert all(r['source'][0]==r['visible'][0] for r in rows)
    assert rows[-1]['visible'][0]['value'] is True and rows[-1]['visible'][1]['value'] is False


def test_native_tuple_projection_checks_each_slot_with_small_distinguishing_values():
    rows=accessor_diagnostics();assert len(rows)==20 and all(r['answer'] for r in rows)


def test_runtime_record_uses_four_fields_in_order_and_does_not_assert_their_relations():
    model=model_for(mask=0);record=model.record('now',2)
    for i,field in enumerate(FIELDS):
        selector=FunctionValue(('individual',)*4,'individual',lambda *values,index=i:values[index])
        assert record(selector)==('x','x','y','y')[i]
    assert [r['value'] for r in interpret(document(),model)]==[False,True]


@pytest.mark.parametrize('values',[[],[Fraction(1,2)],[-1],[0x110000],[0xd800],[True],[3.0],[32]])
def test_invalid_unicode_data_is_rejected(values):
    with pytest.raises(ValueError):scalar_text(values)


def test_unicode_forms_are_exact_without_identity_inference_or_normalization():
    for text in ['A. Einstein','a. Einstein','\u00e9','e\u0301','\U0001f600']:
        expression=text_expression(text)
        assert scalar_text([Fraction(x['numerator'],x['denominator']) for x in expression['items']])==text
    assert scalar_text([0xe9])!=scalar_text([101,0x301])
    model=model_for();name='x';form=[ord(c) for c in 'A. Einstein']
    assert model.form(name,[100,101],form,'now') is True
    # Equal spelling may belong to distinct designation objects; the model
    # records both explicitly and never merges them or their target people.
    assert model.form('y',[100,101],form,'now') is True
    with pytest.raises(ValueError,match='Unknown'):model.form(name,[100,101],[ord(c) for c in 'a. Einstein'],'now')


def test_unknown_records_and_facts_are_not_filled_with_default_truth():
    model=model_for()
    for operation in [lambda:model.record('now',1),lambda:model.record('unknown',2),lambda:model.record('now',0),
                      lambda:model.handlers()['presentationholds']('unknown','now')]:
        with pytest.raises(ValueError):operation()
    missing=model_for();missing.applied.clear()
    with pytest.raises(ValueError,match='Unknown'):interpret(document(),missing)
    missing=model_for();missing.forms.clear()
    with pytest.raises(ValueError,match='Unknown'):interpret(document(),missing)


def test_malformed_record_and_non_boolean_fact_are_rejected():
    kwargs=dict(presented={},applied={},authors={},forms={})
    with pytest.raises(ValueError):NamePresentation('now',{('now',2):('x',)*3},**kwargs)
    with pytest.raises(ValueError):NamePresentation('other',{('now',2):('x',)*4},**kwargs)
    kwargs['presented']={('x','now'):1}
    with pytest.raises(ValueError):NamePresentation('now',{('now',2):('x',)*4},**kwargs)


def test_changed_identifier_or_context_cannot_be_rebound_to_old_evidence():
    doc=deepcopy(document());doc['statements'][1]['body']['arguments'][2]['items'][0]['numerator']=97
    with pytest.raises(ValueError,match='Changed migration'):backprojection(doc)
    doc=deepcopy(document());target=next(d for d in doc['declarations'] if d['name']==names()['packet'])
    target['body']['arguments'][-1]['numerator']=1
    with pytest.raises(ValueError,match='Changed migration'):backprojection(doc)


def test_extractor_does_not_silently_drop_nonliteral_name_codepoints():
    doc=deepcopy(document());doc['statements'][1]['body']['arguments'][2]['items'][0]=dict(
        kind='length',sequence=dict(kind='sequence',element='individual',items=[]))
    with pytest.raises(ValueError,match='not literal'):visible_form(doc)


def test_previous_profile_rejects_a_new_profile_header():
    pages=[from_svg(p.read_text(encoding='utf-8')) for p in sorted(OUT.glob('*.svg'))]
    with pytest.raises(ValueError):decode_collection(pages,TextReferenceVocabulary())
