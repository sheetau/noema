"""Keep typed agency relations and ranked questions distinct in actual SVG."""
from copy import deepcopy
import pytest
from noema.constructed_discourse import normalize_document
from scripts import agency_inquiry_visible_profile as profile
from scripts.visible_collection import compile_collection,decode_collection
from scripts.visible_syntax_geometry import to_svg,from_svg
from scripts.visible_word_forms import Word


def test_all_agency_inquiry_contracts_survive_actual_svg():
    vocabulary=profile.AgencyInquiryVisibleVocabulary()
    document=normalize_document(dict(schema_version='0.16',lexicon_version='0.16',
        declarations=vocabulary.imports(set(profile.CONTRACTS)),statements=[]))
    pages=compile_collection(document,Word('proper',('book','home','aki')),vocabulary,payload=768)['pages']
    restored=decode_collection([from_svg(to_svg(p['shapes'])) for p in pages],vocabulary)['document']
    assert restored==document
    assert len({d['name'] for d in restored['declarations']})==19


def test_property_question_keeps_its_rank_and_candidate_type():
    # Rank zero is a valid type in its own right. A value of that type must
    # not silently satisfy this source relation's rank-one argument.
    vocabulary=profile.AgencyInquiryVisibleVocabulary()
    declaration=deepcopy(vocabulary.declaration('presentspropertyquestion'))
    question=declaration['parameters'][2]
    assert question['rank']==1 and question['result']['kind']=='question'
    assert question['result']['parameters']==[profile.CONTRACTS['conceptualconditionexplanation']['parameters'][0]]
    parameters=[dict(name=name,sort=deepcopy(sort)) for name,sort in
        zip(('va','vb','vc','vd'),declaration['parameters'],strict=True)]
    parameters[2]['sort']['rank']=0
    invalid=dict(kind='definition',name='rankprobe',parameters=parameters,result='truth',
        body=dict(kind='call',symbol=declaration['name'],arguments=[
            dict(kind='variable',name=p['name']) for p in parameters]))
    with pytest.raises(ValueError):
        normalize_document(dict(schema_version='0.16',lexicon_version='0.16',declarations=[declaration,invalid],statements=[]))
