from copy import deepcopy
import pytest

from scripts.check_shared_real_cuts import *
from scripts.visible_senses_vocabulary import SensesVocabulary
from scripts.visible_collection import decode_collection as decode_old
from scripts.visible_word_forms import symbol


def test_all_source_declarations_and_meanings_are_explicitly_connected():
    row=correspondence()
    assert row['work']=='einstein-1905' and len(row['rows'])==13
    assert {r['source_symbol'] for r in row['rows']}==set(MAPPING)
    assert not row['original_manuscript_modified'] and not row['quotation_names_merged']
    assert all(r['source_meaning'] and r['shared_meaning'] and r['statement_indices'] for r in row['rows'])
    assert sum(r['kind']=='primitive' for r in row['rows'])==4
    assert all(r['judgment']=='same_exact_rational_convention_and_ordered_roles'
               for r in row['rows'] if r['kind']=='primitive')


def test_shared_library_retains_all_nine_bodies_and_original_order():
    c=catalog();doc=composed()
    assert [d['name'] for d in doc['declarations']]==[MAPPING[d['name']] for d in c.document['declarations'] if d['name'] in MAPPING]
    for d in doc['declarations']:
        old=next(n for n,target in MAPPING.items() if target==d['name'])
        assert d==renamed(c.entries[old]['declaration'],MAPPING)


def test_injective_renaming_retains_distinct_quoted_names():
    d=deepcopy(composed());d['statements']=[dict(kind='ask',body=op('equal',
        dict(kind='quote',body=dict(kind='function_ref',symbol='cutincluded')),
        dict(kind='quote',body=dict(kind='function_ref',symbol='cutless'))))]
    mapped=injective_mapping(d,{'cutincluded':'leftrelation','cutless':'rightrelation'})
    assert mapped['statements'][0]['body']['arguments'][0]['body']['symbol']=='leftrelation'
    assert mapped['statements'][0]['body']['arguments'][1]['body']['symbol']=='rightrelation'
    for bad in ({'cutincluded':'same','cutless':'same'},{'cutincluded':'cutless'},{'missing':'new'}):
        with pytest.raises(ValueError):injective_mapping(d,bad)


def test_public_extension_preserves_old_words_and_primitive_count():
    old=SensesVocabulary();new=vocabulary()
    assert len(new._words)==384 and len(new._definitions)==361
    assert sum(new._plain_declaration(n)['kind']=='primitive' for n in new._words)==23
    for name in old._words:
        assert old.word(name)==new.word(name)
        assert old.entry(name)==new.entry(name)
        assert old._plain_declaration(name)==new._plain_declaration(name)
    assert len({symbol(new.word(n),new) for n in new._words})==384


def test_changed_published_vocabulary_is_rejected():
    data=vocabulary().document();data['compounds']['cutless']['meaning']='different'
    with pytest.raises(ValueError,match='published meanings'):CutsVocabulary(data)


def test_saved_visible_document_decodes_without_original_ast():
    result=restored()
    assert result['document']==example()
    assert len(result['document']['declarations'])==13 and len(result['document']['statements'])==16
    assert result['volumes']>=2
    with pytest.raises(ValueError,match='vocabulary'):
        decode_old(saved_pages())
    for bad in (saved_pages()[:-1],saved_pages()[::-1],saved_pages()+[saved_pages()[-1]]):
        with pytest.raises(ValueError):decode_collection(bad,vocabulary())


def test_proof_projection_only_changes_explicit_version_headers():
    doc=restored()['document'];view=proof_view(doc)
    assert view['schema_version']=='0.14' and doc['schema_version']=='0.16'
    assert view['declarations']==doc['declarations'] and view['statements']==doc['statements']


def test_all_rational_laws_and_counterclaims_from_restored_geometry():
    checks=proofs()
    assert len(checks)==16
    assert sum(r['status']=='valid' for r in checks)==12
    assert sum(r['status']=='invalid' for r in checks)==4
    assert all(r['reason'] is None for r in checks)


def test_numeric_quantification_is_not_finite_sampling():
    doc=deepcopy(composed());doc['statements']=[dict(kind='ask',body=call('cutvalid',rational(num(0))))]
    handlers=dict(rationalbelow=lambda a,b:a<b,rationaladd=lambda a,b:a+b,
                  rationalnegate=lambda a:-a,rationalmultiply=lambda a,b:a*b)
    with pytest.raises(ValueError,match='rational|number'):
        evaluate_document(doc,individuals=('a','b'),situations=('now',),primitives=handlers)


def test_linear_proof_checker_rejects_nonlinear_rational_replacement():
    doc=deepcopy(composed());doc['statements']=[dict(kind='assert',body=q('exists','x','number',
        op('equal',call('rationalmultiply',v('x'),v('x')),num(2))))]
    with pytest.raises(ValueError,match='Nonlinear'):verify(proof_view(doc),INTERPRETATIONS)
    with pytest.raises(ValueError,match='explicitly'):verify(proof_view(example()),{})


@pytest.mark.parametrize('name,point,value,expected',[
    ('lower',-1,0,True),('boundary',0,0,False),('upper',1,0,False),
    ('negativeboundary',-2,-2,False),('negativebelow',-3,-2,True)])
def test_rational_cut_uses_exact_open_boundary(name,point,value,expected):
    doc=deepcopy(composed());doc['statements']=[dict(kind='ask',body=apply(rational(num(value)),num(point)))]
    result=evaluate_document(doc,individuals=('a',),situations=('now',),primitives=dict(
        rationalbelow=lambda a,b:a<b,rationaladd=lambda a,b:a+b,rationalnegate=lambda a:-a,rationalmultiply=lambda a,b:a*b))
    assert result==[dict(kind='ask',value=expected)]
