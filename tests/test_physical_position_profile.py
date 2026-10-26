from copy import deepcopy
from fractions import Fraction
import pytest

from noema.constructed_semantics import FunctionValue,evaluate_document
from scripts import check_einstein_physical_position as check
from scripts import physical_position_profile as profile
from scripts import check_einstein_designation_purpose as previous
from scripts.designation_purpose_profile import DesignationPurposeVocabulary
from scripts.visible_vectors_vocabulary import VectorsVocabulary
from scripts.visible_collection import decode_collection
from scripts.visible_syntax_geometry import from_svg
from scripts.shared_modality import call,op


def test_profile_preserves_all_previous_meanings_and_uses_distinct_words():
    old=DesignationPurposeVocabulary();new=check.vocabulary();math=VectorsVocabulary()
    assert len(old._words)==397 and len(new._words)==409
    for field in ('entries','compounds','definitions','primitives'):
        assert all(new.document()[field][n]==d for n,d in old.document()[field].items())
    assert not ({new._symbols[n] for n in profile.PARAMETERS}&set(math._by_symbol))


def test_full_visible_selection_preserves_existing_statements_and_source_bodies():
    doc=check.restored()['document'];assert doc==check.document()
    assert len(doc['declarations'])==109 and len(doc['statements'])==6
    assert doc['statements'][:5]==previous.document()['statements']
    ds={d['name']:d for d in doc['declarations']}
    assert all(ds[d['name']]==d for d in previous.document()['declarations'])
    assert check.backprojection(doc)==check.source_excerpt()
    b=check.bridge();assert len(b['inline_mathematics'])==15
    assert sum(r['kind']=='definition' for r in b['inline_mathematics'])==11
    assert all(r['visible_name'] not in check.vocabulary()._by_symbol for r in b['inline_mathematics'] if r['kind']=='definition')


def test_attribution_preserves_each_context_slot_and_never_evaluates_quoted_physics():
    rows=check.presentation_diagnostics();assert len(rows)==8
    assert [r['value'] for r in rows]==[True]+[False]*7


def test_rational_alias_has_same_values_but_distinct_quoted_name():
    doc=deepcopy(check.restored()['document']);m=check.mapping()
    def number(x):
        x=Fraction(x);return dict(kind='number',numerator=x.numerator,denominator=x.denominator)
    pairs=[(-1,0),(0,0),(1,0),(Fraction(1,3),Fraction(1,2))]
    doc['statements']=[dict(kind='ask',body=op('equal',call(m['zz4'],number(a),number(b)),call(m['aa'],number(a),number(b)))) for a,b in pairs]
    doc['statements'].append(dict(kind='ask',body=op('equal',
        dict(kind='quote',body=dict(kind='function_ref',symbol=m['zz4'])),
        dict(kind='quote',body=dict(kind='function_ref',symbol=m['aa'])))))
    def forbidden(*args):raise AssertionError('Unrelated declaration evaluated')
    handlers={d['name']:forbidden for d in doc['declarations'] if d['kind']=='primitive'}
    handlers[m['aa']]=lambda a,b:a<b
    assert [r['value'] for r in evaluate_document(doc,individuals=('x','y'),situations=('now',),primitives=handlers)]==[True]*4+[False]


def test_real_domain_is_refused_instead_of_replaced_by_sampled_truth_values():
    # eiia starts with individual witnesses and then genuine real-cut and
    # real-trajectory witnesses. Native cannot enumerate the rational domain.
    doc=deepcopy(check.restored()['document']);n=check.names()
    doc['statements']=[dict(kind='ask',body=call(n['eiia'],call(n['rd']),call(n['ra']),call(n['ri'])))]
    def forbidden(*args):raise AssertionError('Continuum should be rejected before inner evaluation')
    handlers={d['name']:forbidden for d in doc['declarations'] if d['kind']=='primitive'}
    # Reuse the author/frame reference chain, with every relevant position explicit.
    from scripts.name_presentation_profile import NamePresentation
    from scripts.discourse_setting_profile import DiscourseReferences
    names=NamePresentation('front',{('front',2):('x','x','y','y')},presented={},applied={},authors={},forms={})
    refs=DiscourseReferences({'y':'body'},{},{('body',4,1):'y'},{('y','y',1,'body'):'x'})
    handlers.update({check.vocabulary()._symbols[k]:f for k,f in (names.handlers()|refs.handlers()).items()})
    with pytest.raises(ValueError,match='rational number domain'):
        evaluate_document(doc,individuals=('x','y'),situations=('front','body'),primitives=handlers)


def components():return [FunctionValue(('number',),'truth',lambda q,i=i:q<i) for i in range(18)]


def test_all_eighteen_components_are_preserved_without_validation_or_zero_defaults():
    values=components();records=profile.GeometryRecords({'record':values})
    for i in range(18):assert records.component('record',Fraction(i)) is values[i]
    values[0]=values[1]
    assert records.component('record',0) is not values[0]
    with pytest.raises(ValueError,match='Unknown geometry record'):records.component('unknown',0)


@pytest.mark.parametrize('slot',[-1,18,True,0.0,Fraction(1,2)])
def test_invalid_component_positions_are_rejected(slot):
    with pytest.raises(ValueError):profile.GeometryRecords({'record':components()}).component('record',slot)


def test_wrong_record_length_or_component_type_is_rejected():
    with pytest.raises(ValueError):profile.GeometryRecords({'record':components()[:-1]})
    with pytest.raises(ValueError):profile.GeometryRecords({'record':[False]*18})


def test_geometry_definition_preserves_all_positions_and_same_record():
    ds={d['name']:d for d in check.document()['declarations']};m=check.mapping()
    body=ds[m['eiic']]['body'];args=body['arguments'][1]['arguments']
    assert len(args)==18
    assert all(a['symbol']==m['eiseh'] and a['arguments'][0]==dict(kind='variable',name='va') for a in args)
    assert [a['arguments'][1]['numerator'] for a in args]==list(range(18))


def test_changed_real_domain_or_physical_binding_cannot_reuse_old_evidence():
    doc=deepcopy(check.document());ds={d['name']:d for d in doc['declarations']};m=check.mapping()
    ds[m['eiif']]['body']['body']['kind']='exists'
    with pytest.raises(ValueError,match='Changed migration'):check.backprojection(doc)
    doc=deepcopy(check.document());ds={d['name']:d for d in doc['declarations']}
    ds[m['eisel']]['body']['arguments'][1]['numerator']=4
    with pytest.raises(ValueError,match='Changed migration'):check.backprojection(doc)


def test_old_profile_cannot_silently_decode_new_profile():
    pages=[from_svg(p.read_text(encoding='utf-8')) for p in sorted(check.OUT.glob('*.svg'))]
    with pytest.raises(ValueError):decode_collection(pages,DesignationPurposeVocabulary())
