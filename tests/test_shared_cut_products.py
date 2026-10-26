from copy import deepcopy
from itertools import product
import pytest

from scripts.check_shared_cut_products import *
from scripts.visible_cuts_collection import decode_collection as decode_old
from scripts.visible_word_forms import symbol


def test_preserved_source_definitions_have_explicit_injective_correspondence():
    bridge=correspondence();c=catalog();targets={d['name']:d for d in composed()['declarations']}
    assert len(bridge['rows'])==10 and len(MAPPING)==23
    assert all(r['source_meaning'] and r['shared_meaning'] and r['statement_indices'] for r in bridge['rows'])
    assert not bridge['original_manuscript_modified'] and not bridge['quotation_names_merged']
    for old,new in MAPPING.items():assert renamed(c.entries[old]['declaration'],MAPPING)==targets[new]
    renamed_document=injective_mapping(c.document,MAPPING)
    assert renamed(renamed_document,{v:k for k,v in MAPPING.items()})==c.document
    assert len(bridge['new_compositions'])==5


def test_public_extension_preserves_previous_meanings_and_distinct_words():
    old=CutsVocabulary();new=vocabulary()
    assert len(new._words)==399 and len(new._definitions)==376
    assert sum(new._plain_declaration(n)['kind']=='primitive' for n in new._words)==23
    for n in old._words:
        assert old.word(n)==new.word(n) and old.entry(n)==new.entry(n)
        assert old._plain_declaration(n)==new._plain_declaration(n)
    assert len({symbol(new.word(n),new) for n in new._words})==399
    bad=new.document();bad['compounds']['cutreciprocal']['meaning']='changed'
    with pytest.raises(ValueError,match='published meanings'):ProductsVocabulary(bad)


def test_visible_geometry_preserves_complete_mathematical_payload():
    result=restored()
    assert result['document']==example()
    assert len(result['document']['declarations'])==28 and len(result['document']['statements'])==10
    assert result['volumes']>=2
    with pytest.raises(ValueError,match='vocabulary'):decode_old(saved_pages())
    for bad in (saved_pages()[:-1],saved_pages()[::-1],saved_pages()+[saved_pages()[-1]]):
        with pytest.raises(ValueError):decode_collection(bad,vocabulary())


def test_seven_rational_lemmas_and_three_exact_rational_counterexamples():
    rows=proofs()
    assert len(rows)==10 and sum(r['status']=='valid' for r in rows)==7
    assert all(r['reason']=='Exact rational counterexample' for r in rows if not r['expected_valid'])
    view=proof_view(restored()['document'])
    assert view['declarations']==example()['declarations'] and view['statements']==example()['statements']


def test_wrapper_binding_and_every_domain_slot_are_diagnosed():
    rows=diagnostics()
    assert len(rows)==28
    assert sum('invalid_slot' in row['name'] for row in rows)==10
    assert all(r['value']==r['expected'] for r in rows)


@pytest.mark.parametrize('forward,backward',list(product([False,True],repeat=2)))
def test_native_mutual_relation_checks_both_ordered_pairs(forward,backward):
    d=next(d for d in restored()['document']['declarations'] if d['name']=='cutmutualrelation')
    relation=dict(kind='primitive',name='diagnosticrelation',parameters=[CUT,CUT],result='truth')
    first=lam([('x','number')],op('equal',v('x'),num(1)))
    second=lam([('x','number')],op('equal',v('x'),num(2)))
    body=call('cutmutualrelation',first,second,dict(kind='function_ref',symbol='diagnosticrelation'))
    def handler(a,b):
        if a(Fraction(1)) and b(Fraction(2)):return forward
        if a(Fraction(2)) and b(Fraction(1)):return backward
        raise ValueError('Unexpected relation arguments')
    doc=dict(schema_version='0.16',lexicon_version='0.16',declarations=[relation,d],statements=[dict(kind='ask',body=body)])
    assert evaluate_document(doc,individuals=('a','b'),situations=('now',),primitives=dict(diagnosticrelation=handler))==[dict(kind='ask',value=forward and backward)]


@pytest.mark.parametrize('value,point,expected',[(4,-3,True),(4,0,True),(4,1,True),(4,2,False),(4,3,False),(0,0,False),(-1,-1,True),(-1,0,False)])
def test_native_sqrt_candidate_has_open_positive_boundary(value,point,expected):
    doc=deepcopy(restored()['document'])
    doc['statements']=[dict(kind='ask',body=apply(call('cutsqrtcandidate',rational(num(value))),num(point)))]
    handlers=dict(rationalbelow=lambda a,b:a<b,rationaladd=lambda a,b:a+b,rationalnegate=lambda a:-a,rationalmultiply=lambda a,b:a*b)
    assert evaluate_document(doc,individuals=('a',),situations=('now',),primitives=handlers)==[dict(kind='ask',value=expected)]


def test_nonlinear_existentials_and_unknown_interpretations_are_not_silently_accepted():
    doc=deepcopy(composed())
    doc['statements']=[dict(kind='assert',body=q('exists','x','number',op('equal',call('rationalmultiply',v('x'),v('x')),num(2))))]
    with pytest.raises(ValueError,match='quantifier-free'):verify_universal(proof_view(doc),INTERPRETATIONS)
    with pytest.raises(ValueError,match='explicitly'):verify_universal(proof_view(example()),{})
    doc['statements'][0]['body']=q('forall','x','number',op('not',op('equal',call('rationalmultiply',v('x'),v('x')),num(2))))
    assert verify_universal(proof_view(doc),INTERPRETATIONS)[0]['status']=='unknown'


def test_number_quantification_is_not_replaced_by_finite_tag_diagnostics():
    doc=deepcopy(composed());doc['statements']=[dict(kind='ask',body=call('cutnonnegative',rational(num(1))))]
    handlers=dict(rationalbelow=lambda a,b:a<b,rationaladd=lambda a,b:a+b,rationalnegate=lambda a:-a,rationalmultiply=lambda a,b:a*b)
    with pytest.raises(ValueError,match='rational|number'):evaluate_document(doc,individuals=('a','b'),situations=('now',),primitives=handlers)
