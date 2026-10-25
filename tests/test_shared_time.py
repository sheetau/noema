from copy import deepcopy
import json
import pytest
from noema.constructed import parse,format_graph
from noema.constructed_discourse import normalize_document
from noema.constructed_semantics import evaluate_document
from scripts.shared_time import ROOT,LIBRARY,BASIS,ROLES,composed,basis,op,v,call,lam,S
from scripts.check_shared_time import (POINTS,interpret,harness,source_checks,window_checks,
                                     aspect_checks,recurrence_checks,contexts,binding_diagnostics,
                                     anchor_document,anchor_examples,EXAMPLE)


def test_source_bodies_public_types_and_native_round_trip():
    doc=composed()
    assert len(source_checks())==5
    assert len(doc['declarations'])==14 and all(d['kind']=='definition' for d in doc['declarations'])
    assert parse((ROOT/LIBRARY).read_text(encoding='utf-8'))==doc==parse(format_graph(doc))
    assert json.loads((ROOT/BASIS).read_text(encoding='utf-8'))==basis()
    assert set(basis()['definitions'])==set(basis()['public_contracts'])==set(ROLES)
    for d in doc['declarations']:
        args=basis()['public_contracts'][d['name']]['arguments']
        assert [a['sort'] for a in args]==[p['sort'] for p in d['parameters']]
        assert len(set(a['role'] for a in args))==len(args)
        assert all(a['interpretation'] for a in args)


def test_order_window_anchor_and_overlap_models():
    data=window_checks()
    assert data['order_models']==64 and data['accepted_orders']==6
    assert len(data['anchor_cases'])==24 and data['window_pairs']==64


@pytest.mark.parametrize('changed',[
    {'history':()}, {'order':{('early','early')}}, {'history':('early','middle')},
    {'order':{('early','middle'),('middle','late'),('late','early')}}])
def test_invalid_history_cannot_validate_an_event_or_anchor(changed):
    values=interpret(('timewindow','eventunderway','eventcompleteby'),
                     culmination={('first','late')},anchor='late',**changed)
    assert not any(values.values())


def test_anchor_outside_history_is_rejected_even_with_arbitrary_edges():
    kwargs=dict(history=('early','middle'),window=('early',),anchor='late',
                trace={'first':('early','middle')},culmination={('first','middle')})
    assert not any(interpret(('windowbefore','windowafter','windowat','eventcompleteby'),**kwargs).values())


def test_all_small_extent_completion_and_anchor_combinations():
    assert aspect_checks()['models']==192


def test_progress_does_not_require_future_completion_and_stopping_does_not_imply_it():
    rows={r['name']:r for r in contexts()}
    assert {r['topic'] for r in rows.values()}=={'走行','文書作成'}
    assert rows['running_interrupted']['values']==rows['running_in_progress']['values']
    assert rows['running_finished']['values']=={'eventunderway':False,'eventcompleteby':True}
    assert rows['drafting_before_report']['values']['eventunderway']
    assert not rows['drafting_at_utterance']['values']['eventunderway']
    assert not rows['other_event_completed']['values']['eventcompleteby']


def test_endpoint_is_attainment_in_same_event_not_an_interior_mark_or_only_a_stop():
    name=('eventcompleteby',)
    assert not interpret(name,anchor='late',culmination={('first','middle')})['eventcompleteby']
    assert not interpret(name,anchor='late',trace={'first':('early','middle')})['eventcompleteby']
    assert interpret(name,anchor='late',trace={'first':('early','middle')},
                     culmination={('first','middle')})['eventcompleteby']


def test_once_and_each_period_against_independent_set_conditions():
    data=recurrence_checks()
    assert data['unique_event_models']==64 and data['period_models']==256


def test_empty_periods_or_one_long_event_do_not_mean_each_period():
    assert not interpret(('eventevery',),periods=())['eventevery']
    args=dict(periods=('first','second'),windows={'first':('early',),'second':('late',)},events=('first',))
    assert not interpret(('eventevery',),**args)['eventevery']
    assert interpret(('eventevery',),periods=('first','second'),
        windows={'first':('early',),'second':('late',)},trace={'first':('early',),'second':('late',)})['eventevery']


def test_multiple_time_points_are_not_multiple_events_and_invalid_trace_is_not_discarded():
    assert interpret(('eventonce',),events=('first',))['eventonce']
    assert not interpret(('eventonce',),trace={'first':POINTS,'second':POINTS})['eventonce']
    assert not interpret(('eventonce',),trace={'first':POINTS,'second':('early','late')})['eventonce']


def test_selected_actor_and_object_are_not_replaced_by_other_events():
    # The event-selection relation includes actor and object. Varying it leaves
    # the same times but changes whose event is counted.
    traces={'first':('early',),'second':('late',)}
    assert interpret(('eventonce',),events=('first',),window=('early',),trace=traces)['eventonce']
    assert not interpret(('eventonce',),events=('second',),window=('early',),trace=traces)['eventonce']


def test_every_process_trace_and_culmination_slot_is_distinguished():
    rows=binding_diagnostics()
    assert len(rows)==10 and sum(r['value'] for r in rows)==3


def test_persistence_negation_and_absence_throughout_have_different_scope():
    name='holdsall'; base=deepcopy(harness((name,)))
    positive=base['statements'][0]['body']
    negative=deepcopy(positive)
    negative['arguments'][1]['body']=op('not',negative['arguments'][1]['body'])
    base['statements']=[dict(kind='ask',body=op('not',positive)),dict(kind='ask',body=negative)]
    model={d['name']:(lambda *args:False) for d in base['declarations'] if d['kind']=='primitive'}
    model.update(inputwindow=lambda p:True,inputstate=lambda p:p=='early')
    values=evaluate_document(normalize_document(base),individuals=('first',),situations=POINTS,primitives=model)
    assert [r['value'] for r in values]==[True,False]


def test_becoming_requires_same_process_and_both_changed_truth_values():
    name=('becomes',)
    assert interpret(name,process={('first','early','late')},state=('late',))['becomes']
    assert not interpret(name,process={('second','early','late')},state=('late',))['becomes']
    assert not interpret(name,process={('first','early','late')},state=POINTS)['becomes']
    assert not interpret(name,process={('first','early','late')},state=())['becomes']


def test_absent_input_is_not_silently_interpreted_as_empty_time():
    with pytest.raises(ValueError,match='Missing interpretation'):interpret(('timewindow',),window=None)


def test_one_native_document_retains_report_and_utterance_anchors_independently():
    doc=anchor_document()
    assert parse((ROOT/EXAMPLE).read_text(encoding='utf-8'))==doc==parse(format_graph(doc))
    rows={r['name']:r['values'] for r in anchor_examples()}
    assert list(rows['interrupted'].values())==[True,False,False]
    assert list(rows['finished_later'].values())==[True,False,True]
    assert list(rows['reference_reversed'].values())==[False,True,False]
