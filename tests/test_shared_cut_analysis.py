from copy import deepcopy
import pytest

from scripts.check_shared_cut_analysis import *
from scripts.shared_cut_products import CUT
from scripts.cut_analysis_diagnostics import scalar_sorts,scalar_call
from scripts.visible_products_collection import decode_collection as decode_old
from scripts.visible_word_forms import symbol


def test_all_seventeen_analysis_definitions_retain_typed_source_bodies():
    c=catalog();targets={d['name']:d for d in composed()['declarations']};bridge=correspondence()
    assert len(bridge['rows'])==17 and len(MAPPING)==40
    assert all(r['source_meaning'] and r['shared_meaning'] for r in bridge['rows'])
    assert {r['source_symbol'] for r in bridge['rows'] if not r['statement_indices']}=={'sess','sest'}
    for old,new in MAPPING.items():assert renamed(c.entries[old]['declaration'],MAPPING)==targets[new]
    mapped=injective_mapping(c.document,MAPPING)
    assert renamed(mapped,{v:k for k,v in MAPPING.items()})==c.document
    assert not bridge['original_manuscript_modified'] and not bridge['quotation_names_merged']


def test_previous_words_meanings_and_arithmetic_are_unchanged():
    old=ProductsVocabulary();new=vocabulary()
    assert len(new._words)==416 and len(new._definitions)==393
    assert sum(new._plain_declaration(n)['kind']=='primitive' for n in new._words)==23
    for n in old._words:
        assert new.word(n)==old.word(n) and new.entry(n)==old.entry(n)
        assert new._plain_declaration(n)==old._plain_declaration(n)
    assert len({symbol(new.word(n),new) for n in new._words})==416
    bad=new.document();bad['compounds']['cutintegral']['roles'].reverse()
    with pytest.raises(ValueError,match='published meanings'):AnalysisVocabulary(bad)


def test_saved_geometry_restores_all_calculus_bodies_and_rejects_wrong_edition():
    result=restored()
    assert result['document']==example()
    assert len(result['document']['declarations'])==45 and len(result['document']['statements'])==10
    assert result['volumes']>=2
    with pytest.raises(ValueError,match='vocabulary'):decode_old(saved_pages())
    for bad in (saved_pages()[:-1],saved_pages()[::-1],saved_pages()+[saved_pages()[-1]]):
        with pytest.raises(ValueError):decode_collection(bad,vocabulary())


def test_native_neighborhood_interval_and_tagged_cell_embedding_laws():
    rows=native_proofs()
    assert len(rows)==10 and sum(r['status']=='valid' for r in rows)==6
    assert sum(r['status']=='invalid' for r in rows)==4


def test_rational_analogue_separates_limit_continuity_and_one_sided_approach():
    rows={r['name']:r for r in rational_diagnostics()}
    assert len(rows)==25
    for name in ('isolated_point_is_continuous','right_hand_limit_does_not_need_value_at_point','left_approach_from_negative','whole_domain_has_interior'):
        assert rows[name]['status']=='valid'
    for name in ('isolated_point_has_no_limit_under_accumulation_convention','continuity_requires_point_in_domain',
                 'right_domain_is_not_left_approach','isolated_point_not_interior','bounded_identity_does_not_diverge','empty_domain_does_not_diverge'):
        assert rows[name]['status']=='invalid'


def test_projection_is_explicit_and_keeps_quantifier_and_fold_structure():
    source={d['name']:d for d in restored()['document']['declarations']}
    for name in DEFINITIONS.values():
        projected=rational_projection(restored()['document'],[name])
        target=next(d for d in projected['declarations'] if d['name']==name)
        assert target==scalar_sorts(source[name])
        assert target!=source[name]
    derivative=rational_projection(restored()['document'],['cutderivative'])
    reciprocal=next(d for d in derivative['declarations'] if d['name']=='cutreciprocal')
    assert reciprocal['kind']=='primitive' and reciprocal['parameters']==['number']


def test_scalar_partition_diagnostics_preserve_order_tags_and_strict_mesh():
    rows={r['name']:r for r in finite_diagnostics()}
    assert len(rows)==28 and all(r['actual']==r['expected'] for r in rows.values())
    assert not rows['gap']['actual'] and not rows['overlap']['actual'] and not rows['reversed']['actual']
    assert not rows['empty']['actual'] and rows['empty_mesh_is_vacuous']['actual']
    assert not rows['mesh_equal_boundary']['actual'] and not rows['tag_changes_identity_sum']['actual']


@pytest.mark.parametrize('point,expected',[(-1,True),(0,False),(1,False)])
def test_native_empty_riemann_sum_is_the_open_zero_cut(point,expected):
    cell_sort=next(d for d in composed()['declarations'] if d['name']=='cutriemannsum')['parameters'][0]['sort']['element']
    empty=dict(kind='sequence',element=cell_sort,items=[])
    identity=lam([('x',CUT)],v('x'))
    doc=deepcopy(restored()['document'])
    doc['statements']=[dict(kind='ask',body=apply(call('cutriemannsum',empty,identity),num(point)))]
    handlers=dict(rationalbelow=lambda a,b:a<b,rationaladd=lambda a,b:a+b,rationalnegate=lambda a:-a,rationalmultiply=lambda a,b:a*b)
    assert evaluate_document(doc,individuals=('a','b'),situations=('now',),primitives=handlers)==[dict(kind='ask',value=expected)]


def test_infinite_cut_domain_is_not_evaluated_as_finite_samples():
    all_domain=lam([('x',CUT)],op('equal',num(0),num(0)))
    identity=lam([('x',CUT)],v('x'))
    doc=deepcopy(composed());doc['statements']=[dict(kind='ask',body=call('cutlimit',all_domain,identity,rational(num(0)),rational(num(0))))]
    handlers=dict(rationalbelow=lambda a,b:a<b,rationaladd=lambda a,b:a+b,rationalnegate=lambda a:-a,rationalmultiply=lambda a,b:a*b)
    with pytest.raises(ValueError,match='rational|number'):evaluate_document(doc,individuals=('a','b'),situations=('now',),primitives=handlers)


def test_reciprocal_is_not_removed_to_force_derivative_through_linear_prover():
    doc=rational_projection(restored()['document'],['cutderivative'])
    doc['statements']=[dict(kind='assert',body=op('equal',num(0),num(0)))]
    available={n:m for n,m in INTERPRETATIONS.items() if n in {d['name'] for d in doc['declarations']}}
    with pytest.raises(ValueError,match='explicitly'):verify(proof_view(doc),available)
