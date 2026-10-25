from copy import deepcopy
import json
import pytest
from scripts.shared_senses import *
from scripts.check_shared_senses import (seq,number,argument,meaning,cases,entry,entries,frame,ev,unknown,base,doc,query,model,values,
    candidate_checks,meaning_checks,classification_checks,replacement_checks,binding_diagnostics,example,example_model,example_expected,EXAMPLES)
from scripts.shared_reference import content


def test_inventory_preserves_existing_meanings_and_definitions_without_primitives():
    d=composed();b=basis();byname={x['name']:x for x in d['declarations']}
    assert len(byname)==29 and len(MEANINGS)==25 and not b['primitives']
    assert parse((ROOT/LIBRARY).read_text(encoding='utf-8'))==d==parse(format_graph(d))
    assert json.loads((ROOT/BASIS).read_text(encoding='utf-8'))==b
    assert set(b['definitions'])==set(b['public_contracts'])==set(byname)
    for source in SOURCES:
        old=parse((ROOT/source['document']).read_text(encoding='utf-8'));oldbasis=json.loads((ROOT/source['basis']).read_text(encoding='utf-8'))
        for declaration in old['declarations']:
            if declaration['name'] in source['names']:
                assert byname[declaration['name']]==declaration
                assert b['definitions'][declaration['name']]==oldbasis['definitions'][declaration['name']]
    for declaration in d['declarations']:
        contract=b['public_contracts'][declaration['name']]
        assert [p['sort'] for p in declaration['parameters']]==[p['sort'] for p in contract['arguments']]
        assert declaration['result']==contract['result']

def test_candidates_completeness_and_selection_are_independent():
    assert candidate_checks()==dict(models=16,senses=2,checks_per_model=7)

def test_scoped_meaning_entailment_and_equivalence():
    assert meaning_checks()==dict(models=1024,argument_cases=2,situations=2,checks_per_model=2)

def test_polysemy_and_homonymy_require_exclusive_positive_evidence():
    assert classification_checks()==dict(models=64,independent_conditions=6,checks_per_model=2)

def test_synonym_convention_permission_and_actual_frame_agreement():
    assert replacement_checks()==dict(models=16,frames=3,checks_per_model=4)

def test_all_selection_classification_and_replacement_slots():
    rows=binding_diagnostics()
    assert len(rows)==36 and not any(row['result'] for row in rows)

@pytest.mark.parametrize('mode',EXAMPLES)
def test_complete_native_example(mode):
    assert parse((ROOT/EXAMPLES[mode]).read_text(encoding='utf-8'))==example(mode)
    assert values(example(mode),example_model())==example_expected(mode)
    assert all(not d['parameters'] for d in example(mode)['declarations'] if d['kind']=='primitive')

@pytest.mark.parametrize('bad',[entry(body='secondmeaning'),entry(arity=2,roles=('agentrole','patientrole')),entry(roles=('patientrole',))])
def test_conflicting_six_field_records_cannot_share_a_key(bad):
    assert values(doc([query('sensecatalog',entries=entries(entry(),bad)),query('entrysame',right=bad)]),model())==[False,False]

@pytest.mark.parametrize('bad',[entry(word='wordb'),entry(context='contextb')])
def test_catalog_can_mix_contexts_and_words_but_a_candidate_pool_cannot(bad):
    assert values(doc([query(n,entries=entries(entry(),bad)) for n in ('sensecatalog','sensecandidates','sensechosen')]),model())==[True,False,False]

def test_empty_pool_does_not_resolve_or_select_a_sense():
    names=('sensecatalog','sensecandidates','sensepossible','senseunique','senseresolved','sensemultiple','sensechosen')
    assert values(doc([query(n,entries=entries()) for n in names]),model())==[True,True,False,False,False,False,False]

def test_duplicate_entry_does_not_add_an_alternative():
    assert values(doc([query(n,entries=entries(entry(),entry())) for n in ('sensecatalog','senseunique','senseresolved','sensemultiple')]),model())==[True,True,True,False]

@pytest.mark.parametrize('arity,roles,valid',[(0,(),True),(1,(),False),(2,('agentrole','patientrole'),True),(2,('agentrole','agentrole'),False),(-1,(),False)])
def test_arity_and_distinct_ordered_roles(arity,roles,valid):
    assert values(doc([query('entryvalid',entry=entry(arity=arity,roles=roles))]),model())==[valid]

def test_argument_order_is_preserved_and_content_is_not_executed_by_interpretation():
    first=argument(('first','second'));second=argument(('second','first'))
    result=call('senseapplication',meaning(),first)
    bodies=[query('senseinstantiated',arguments=first,arity=number(2),result=result),
        query('senseinstantiated',arguments=second,arity=number(2),result=result),eq(result,call('senseapplication',meaning(),second))]
    assert values(doc(bodies),model(payload=unknown))==[True,False,False]

def test_zero_unary_and_binary_meaning_functions_share_application_without_new_primitives():
    d=deepcopy(base());ds=d['declarations'];bodies=[]
    for name,names in [('nullary',()),('unary',('first',)),('binary',('first','second'))]:
        ds.append(definition(name,[('items',MEMBERS)],C,content(eq(v('items'),seq(call(n) for n in names)))))
        m=meaning(name);a=argument(names)
        bodies += [query('senseinstantiated',meaning=m,arguments=a,arity=number(len(names)),result=call('senseapplication',m,a)),
            ev(disquote(call('senseapplication',m,a))),ev(disquote(call('senseapplication',m,argument(('second',)))))]
    d['statements']=[dict(kind='ask',body=b) for b in bodies]
    assert values(normalize_document(d),model(payload=unknown))==[True,True,False]*3

@pytest.mark.parametrize('body',[query('sensechosen'),query('senseinterpreted'),query('senseunique'),query('sensepolysemous',right=entry(sense='senseb',body='secondmeaning')),
    eq(call('senseapplication',meaning(),argument()),call('senseapplication',meaning(),argument()))])
def test_registration_selection_and_classification_do_not_assert_content_truth(body):
    assert values(doc([body]),model(payload=unknown))==[True]

@pytest.mark.parametrize('body',[query('senseequivalent'),query('sensesynonymous'),query('sensereplaceable'),ev(disquote(call('senseapplication',meaning(),argument())))])
def test_actual_semantic_comparison_rejects_unknown_content(body):
    with pytest.raises(ValueError,match='Unknown'):values(doc([body]),model(payload=unknown))

@pytest.mark.parametrize('relation,name',[('selected','sensechosen'),('licensed','sensesynonymous'),('permitted','sensereplaceable')])
def test_missing_interpretive_relation_is_not_derived_from_truth(relation,name):
    with pytest.raises(ValueError,match='Unknown'):values(doc([query(name)]),model(**{relation:unknown}))

def test_roles_and_their_order_are_part_of_equivalence():
    left=entry(arity=2,roles=('agentrole','patientrole'))
    right=entry(word='wordb',body='aliasmeaning',arity=2,roles=('patientrole','agentrole'))
    assert values(doc([query('senseequivalent',left=left,right=right,cases=cases((('first','second'),)))]),model())==[False]

def test_scoped_coincidence_cannot_prove_universal_synonymy():
    body=query('meaningequivalent',left=meaning(),right=meaning('secondmeaning'),cases=cases((('first',),)))
    payload=lambda i,a,w:i=='a' or (a.items[0]=='a' and w=='now')
    assert values(doc([body]),model(payload=payload,worlds=lambda w:w=='now'))==[True]
    assert values(doc([body]),model(payload=payload))==[False]
    expanded=query('meaningequivalent',left=meaning(),right=meaning('secondmeaning'))
    assert values(doc([expanded]),model(payload=payload,worlds=lambda w:w=='now'))==[False]

def test_empty_comparison_cases_or_worlds_do_not_create_equivalence():
    bodies=[query('meaningequivalent',left=meaning(),right=meaning(),cases=cases(())),
        query('meaningequivalent',left=meaning(),right=meaning(),cases=cases(((),)))]
    assert values(doc(bodies),model())==[False,False]
    assert values(doc([query('senseequivalent')]),model(worlds=lambda w:False))==[False]

def test_identical_meaning_definition_with_two_word_forms_still_blocks_word_quotation_replacement():
    other=entry(word='wordb');body=query('sensereplaceable',right=other,frame=frame('wordframe'))
    assert values(doc([query('sensesynonymous',right=other),body]),model())==[True,False]

def test_a_lie_about_replacement_permission_does_not_override_frame_disagreement():
    bodies=[query('sensereplaceable',frame=frame(n)) for n in ('wordframe','descriptionframe')]
    assert values(doc(bodies),model(permitted=lambda *a:True))==[False,False]

def test_meaning_description_identity_is_not_extensional_identity():
    bodies=[eq(meaning(),meaning('aliasmeaning')),query('meaningequivalent',left=meaning(),right=meaning('aliasmeaning')),
        query('entrysame',right=entry(body='aliasmeaning'))]
    assert values(doc(bodies),model())==[False,True,False]
