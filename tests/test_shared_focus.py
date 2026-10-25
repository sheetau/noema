from copy import deepcopy
import json
import pytest
from scripts.shared_focus import *
from scripts.check_shared_focus import (doc,values,model,query,claim,descriptions,wrapped,package,scalar,topical,contrast,ev,unknown,
    alternative_checks,projection_checks,scalar_checks,contrast_checks,binding_diagnostics,example,example_model,example_expected,EXAMPLES,EXAMPLE_SCENES,ACTION)


def test_inventory_keeps_old_definitions_and_meanings_without_new_primitives():
    d=composed();b=basis();byname={x['name']:x for x in d['declarations']}
    assert len(byname)==38 and len(MEANINGS)==16 and len(OLD_ROLES)==22 and not b['primitives']
    assert parse((ROOT/LIBRARY).read_text(encoding='utf-8'))==d==parse(format_graph(d))
    assert json.loads((ROOT/BASIS).read_text(encoding='utf-8'))==b
    assert set(b['definitions'])==set(b['public_contracts'])==set(byname)
    for source in SOURCES:
        old=parse((ROOT/source['document']).read_text(encoding='utf-8'));oldbasis=json.loads((ROOT/source['basis']).read_text(encoding='utf-8'))
        for declaration in old['declarations']:
            if declaration['name'] in source['renaming']:
                renamed_declaration=renamed(declaration,source['renaming'])
                assert byname[renamed_declaration['name']]==renamed_declaration
                assert b['definitions'][renamed_declaration['name']]==oldbasis['definitions'][declaration['name']]
    for declaration in d['declarations']:
        contract=b['public_contracts'][declaration['name']]
        assert [p['sort'] for p in declaration['parameters']]==[p['sort'] for p in contract['arguments']]
        assert declaration['result']==contract['result']
        assert len(set(p['role'] for p in contract['arguments']))==len(declaration['parameters'])

def test_relative_entailment_exclusion_and_addition():
    assert alternative_checks()==dict(models=128,situations=2,checks_per_model=8)

def test_foreground_and_background_projection_remain_distinct():
    assert projection_checks()==dict(models=16,independent_truths=4,checks_per_model=8)

def test_scalar_ranking_and_optional_additive_truth():
    assert scalar_checks()==dict(models=256,description_names=2,alternative_lists=4,checks_per_model=7)

def test_contrast_actual_truth_and_expectations():
    assert contrast_checks()==dict(models=128,situations=2,checks_per_model=4)

def test_all_attribution_topic_and_expectation_slots_with_other_witnesses_fixed():
    rows=binding_diagnostics()
    assert len(rows)==45 and not any(r['result'] for r in rows)

@pytest.mark.parametrize('mode',EXAMPLES)
def test_complete_native_information_structure(mode):
    d=example(mode)
    assert parse((ROOT/EXAMPLES[mode]).read_text(encoding='utf-8'))==d
    assert values(d,example_model(),EXAMPLE_SCENES)==example_expected(mode)

@pytest.mark.parametrize('names',[('weakform',),('focusalias',),('focusform',),('focusalias','focusalias')])
def test_weak_or_equivalent_alternatives_are_not_excluded_or_counted_as_new_additions(names):
    bodies=[call(n,package(p,names),call('context')) for p in ('focusonly','focusalso') for n in ('focusclaimtrue','focusbackgroundtrue')]
    assert values(doc(bodies),model())==[True,True,True,False]

def test_empty_alternatives_do_not_create_only_or_additional_background():
    bodies=[call(n,package(p,()),call('context')) for p in ('focusonly','focusalso') for n in ('focusclaimtrue','focusbackgroundtrue')]
    assert values(doc(bodies),model())==[False,True,True,False]

def test_outside_comparison_domain_does_not_silently_license_only_or_also():
    bodies=[call('focusclaimtrue',package('focusonly'),call('context')),call('focusbackgroundtrue',package(),call('context'))]
    assert values(doc(bodies),model(comparisons=lambda w:w=='later'))==[False,False]

def test_changing_comparison_scope_changes_entailment_not_description_identity():
    bodies=[call('focusentails',claim(),claim('alternativeform'),ref('comparisons')),eq(claim(),claim('alternativeform'))]
    m=model(payload=lambda i,w:w=='now' if i=='a' else True,comparisons=lambda w:True)
    assert values(doc(bodies),m)==[True,False]
    m=model(payload=lambda i,w:w=='now' if i=='a' else False,comparisons=lambda w:w=='later')
    assert values(doc(bodies),m)==[True,False]

def test_three_description_order_rejects_a_missing_transitive_edge():
    sequence=descriptions(('focusform','alternativeform','weakform'))
    edges={('focusform','alternativeform'),('alternativeform','weakform')}
    from scripts.check_shared_focus import code_name
    d=doc([call('focusorder',sequence,call('author'),call('anchor'),ref('ranking'))])
    assert values(d,model(ranking=lambda o,a,b,s:(code_name(a),code_name(b)) in edges))==[False]
    edges.add(('focusform','weakform'))
    assert values(d,model(ranking=lambda o,a,b,s:(code_name(a),code_name(b)) in edges))==[True]

def test_repeated_valid_alternative_is_not_extra_weight_or_invalid_order():
    a=scalar('focusscalar',('alternativeform',));b=scalar('focusscalar',('alternativeform','alternativeform'))
    assert values(doc([call('focusbackgroundtrue',p,call('context')) for p in (a,b)]),model())==[True,True]

@pytest.mark.parametrize('body',[package(),package('focusonly'),scalar(),contrast(),topical(),call('focusnegate',package()),
    call('focusif',package(),topical()),call('focusfilteredif',package(),topical()),call('focusquestion',package()),
    query('focusattributepackage'),query('topicmarked'),query('contrastordered')])
def test_quotation_construction_and_attribution_leave_unknown_content_unevaluated(body):
    if body.get('symbol') in ('focusattributepackage','topicmarked','contrastordered'):assertion=body
    elif body.get('symbol')=='focusquestion':assertion=eq(body,body)
    else:
        assertion=allof(*(eq(call(n,body),call(n,body)) for n in ('focusclaim','focusbackground')))
    assert values(doc([assertion]),model(payload=unknown,ranking=unknown,expects=unknown))==[True]

@pytest.mark.parametrize('body',[call('focusclaimtrue',package(),call('context')),call('focusbackgroundtrue',package(),call('context')),
    call('focusclaimtrue',package('focusonly'),call('context')),call('focusbackgroundtrue',contrast(),call('context')),
    call('focusentails',claim(),claim('alternativeform'),ref('comparisons'))])
def test_truth_or_entailment_queries_reject_unknown_content(body):
    with pytest.raises(ValueError,match='Unknown'):values(doc([body]),model(payload=unknown))

def test_questionization_preserves_the_original_background_and_only_asks_the_foreground():
    pack=package();question=call('focusquestion',pack)
    expected=quoted(quote(lam([('main',C)],dict(kind='message',force='ask',content=v('main'))),2),call('focusclaim',pack))
    # Alpha-equivalent binders and exact quoted application are normalized by the evaluator.
    assert values(doc([eq(question,expected),eq(call('focusbackground',pack),call('focusbackground',call('focusnegate',pack)))]),model(payload=unknown))==[True,True]

def test_topic_is_not_inferred_from_a_true_claim_or_from_an_equivalent_frame():
    assert values(doc([query('topicmarked'),query('topicmarked',frame=quote(ref('otherframe'),2))]),model(about=lambda *a:False))==[False,False]
    assert values(doc([query('topicmarked',topic=call('second')),query('topicmarked',frame=quote(ref('otherframe'),2))]),model())==[False,False]

def test_topic_claim_retains_its_inner_negation_and_argument():
    first=call('topiccontent',quote(ref('topicframe'),2),quote(call('first')))
    second=call('topiccontent',quote(ref('topicframe'),2),quote(call('second')))
    assert values(doc([evaluate(first,call('context')),evaluate(second,call('context')),query('topicmarked')]),model())==[False,True,True]

def test_two_true_contents_do_not_by_themselves_supply_discourse_contrast():
    assert values(doc([query('contrastordered')]),model(payload=lambda *a:True,contrasts=lambda *a:False))==[False]
    assert values(doc([query('contrastordered')]),model(payload=lambda *a:True))==[True]

def test_empty_expectations_are_not_a_contrast_background():
    assert values(doc([call('focusbackgroundtrue',contrast(),call('context'))]),model(expects=lambda *a:False))==[False]

@pytest.mark.parametrize('relation',['about','reported','backgrounded','contrasts','before'])
def test_missing_attribution_input_is_not_inferred_from_other_components(relation):
    name='contrastordered' if relation in ('contrasts','before') else 'topicmarked'
    with pytest.raises(ValueError,match='Unknown'):values(doc([query(name)]),model(**{relation:unknown}))

def test_action_frame_is_shared_and_ordered_in_all_comparisons():
    frame=quote(ref('actionframe'),1);first=quote(ref('actionfirst'));second=quote(ref('actionsecond'))
    sequence=dict(kind='sequence',element=ACTION,items=[first,second,first])
    actual=call('focusactions',frame,sequence)
    expected=dict(kind='sequence',element=PC,items=[call('focusaction',frame,x) for x in (first,second,first)])
    assert values(doc([eq(actual,expected),eq(disquote(call('focusquotedlist',actual)),actual)]),model(payload=unknown))==[True,True]
