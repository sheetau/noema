"""Visible contracts and opaque state descriptions preserve candidate binding."""
from copy import deepcopy
import json
import pytest
from noema.constructed_discourse import normalize_document
from noema.constructed_semantics import evaluate_document
from scripts import convenience_assessment_visible_profile as profile
from scripts.shared_modality import call,v
from scripts.shared_reference import definition
from scripts.visible_collection import compile_collection,decode_collection
from scripts.visible_syntax_geometry import to_svg,from_svg
from scripts.visible_word_forms import Word


def test_all_contracts_survive_actual_svg():
    vocabulary=profile.ConvenienceAssessmentVisibleVocabulary()
    document=normalize_document(dict(schema_version='0.16',lexicon_version='0.16',
        declarations=vocabulary.imports(set(profile.ALL_CONTRACTS)),statements=[]))
    pages=compile_collection(document,Word('proper',('book','home','round','give')),vocabulary,payload=768)['pages']
    restored=decode_collection([from_svg(to_svg(p['shapes'])) for p in pages],vocabulary)['document']
    assert restored==document and len(restored['declarations'])==4


def fixture(property_name='bf'):
    declarations=profile.library()['declarations']
    for name,parameters,result in [('jperson',[],'individual'),('jcontext',[],'situation'),('jcase',[],'situation'),
            ('jstate',['individual','situation'],'truth'),('jother',['individual','situation'],'truth')]:
        declarations.append(dict(kind='primitive',name=name,parameters=parameters,result=result))
    for name,predicate in [('bf','jstate'),('anotherproperty','jother')]:
        declarations.append(definition(name,[('person','individual')],'content',
            dict(kind='content',variable='point',body=call(predicate,v('person'),v('point')))))
    declarations.append(profile.case_specialization('uj',property_name))
    return normalize_document(dict(schema_version='0.16',lexicon_version='0.16',declarations=declarations,
        statements=[dict(kind='ask',body=call('uj',call('jperson'),call('jcontext'),call('jcase')))]))


def test_specialization_preserves_each_slot_without_executing_state():
    def forbidden(*args):raise ValueError('Quoted state must not execute')
    def values(truth=True):
        def candidate(person,description,context,case):
            syntax=json.loads(description.syntax)
            key=(person,syntax.get('symbol'),context,case)
            if syntax.get('kind')!='function_ref' or key!=('first','bf','first','second'):
                raise ValueError('Unknown state candidate')
            return truth
        return dict(jperson=lambda:'first',jcontext=lambda:'first',jcase=lambda:'second',jstate=forbidden,jother=forbidden,
            stateconveniencecandidate=candidate,practicalgoalattainment=forbidden,
            contextualconvenienceburden=forbidden,convenienceassessmentperson=forbidden)
    def run(doc,model):return [r['value'] for r in evaluate_document(doc,individuals=('first','second'),
        situations=('first','second'),primitives=model,memoize_definitions=False,memoize_expressions=False)]
    for truth in (False,True):assert run(fixture(),values(truth))==[truth]
    for name,other in [('jperson','second'),('jcontext','second'),('jcase','first')]:
        with pytest.raises(ValueError,match='Unknown state candidate'):run(fixture(),values()|{name:lambda:other})
    with pytest.raises(ValueError,match='Unknown state candidate'):run(fixture('anotherproperty'),values())


def test_state_content_is_not_a_state_description():
    doc=fixture();row=next(d for d in doc['declarations'] if d['name']=='uj')
    assert row['body']['arguments'][1]['kind']=='quote'
    row['body']['arguments'][1]=call('bf',v(row['parameters'][0]['name']))
    with pytest.raises(ValueError):normalize_document(doc)


def test_specialization_keeps_source_parameter_order():
    from noema.meaning_catalog import load_catalog
    state=json.loads((profile.ROOT/'data/work-state.json').read_text(encoding='utf-8'))
    active=json.loads((profile.ROOT/state['review_index']).read_text(encoding='utf-8'))['works']['kant-1784']
    catalog=load_catalog(profile.ROOT,active['meaning_basis'],document_path=active['document'])
    source=catalog.entries['uj']['declaration'];specialized=profile.case_specialization()
    assert [p['sort'] for p in specialized['parameters']]==source['parameters']
    assert specialized['result']==source['result']=='truth'
    assert [arg['name'] for i,arg in enumerate(specialized['body']['arguments']) if i!=1]==[p['name'] for p in specialized['parameters']]
    assert specialized['body']['arguments'][1]==dict(kind='quote',body=dict(kind='function_ref',symbol='bf'))
