from copy import deepcopy
import json
import pytest
from noema.constructed import parse,format_graph
from noema.constructed_discourse import normalize_document
from scripts.shared_readings import ROOT,LIBRARY,BASIS,D,READINGS,composed,basis,call,op,truth
from scripts.check_shared_readings import (EXAMPLE,HISTORY,base,example,history,result,literal,negative,seq,doc,
    values,evaluate,licensed,revision,candidate_checks,topic_checks,revision_checks,binding_diagnostics,quote,ref)


def test_published_native_sources_and_public_contracts_match():
    for path,d in ((LIBRARY,composed()),(EXAMPLE,example()),(HISTORY,history())):
        assert parse((ROOT/path).read_text(encoding='utf-8'))==d==parse(format_graph(d))
    assert json.loads((ROOT/BASIS).read_text(encoding='utf-8'))==basis()
    definitions=composed()['declarations']
    assert len(definitions)==14 and all(d['kind']=='definition' for d in definitions)
    assert set(basis()['definitions'])=={d['name'] for d in definitions}
    for d in definitions:
        c=basis()['public_contracts'][d['name']]
        assert [p['sort'] for p in d['parameters']]==[p['sort'] for p in c['arguments']]
        assert d['result']==c['result'] and all(p['interpretation'] for p in c['arguments'])


def test_construction_and_candidate_comparison_do_not_execute_unknown_content():
    assert values(example())==[True,True,True,False,True,True]*2
    with pytest.raises(ValueError,match='Unknown quoted content'):values(doc([evaluate(result())]))


def test_candidate_records_do_not_confuse_repetition_empty_or_incomplete_lists():
    assert len(candidate_checks())==15
    a=result()
    tests=[call('readingsambiguous',seq(a,a)),call('readingsresolved',seq(a,a),truth(True)),
           call('readingsresolved',seq(a),truth(False)),call('readingsabsence',seq(),truth(False)),
           call('readingsabsence',seq(),truth(True))]
    assert values(doc(tests))==[False,True,False,False,True]


def test_two_topics_have_distinct_strict_and_sloppy_readings_even_with_equal_truth():
    rows=topic_checks()
    assert len(rows)==8 and {r['topic'] for r in rows}=={'praising','revising'}
    assert all(r['values'][0] is False for r in rows)
    assert any(r['values'][1:]==[True,False] for r in rows)
    assert any(r['values'][1:]==[False,True] for r in rows)
    assert any(r['values'][1:]==[True,True] for r in rows)


def test_two_readings_are_not_one_disjunctive_assertion():
    a=result();b=result(related='nao')
    # The disjunction is itself a single quoted message, not a candidate list.
    issue=lambda owner:dict(kind='evaluate',content=dict(kind='message_content',message=dict(kind='apply',
        function=ref('praising'),arguments=[call('nao'),call(owner),call('now')])),situation=dict(kind='variable',name='world'))
    disjunction=quote(dict(kind='message',force='assert',content=dict(kind='content',variable='world',
        body=op('or',issue('aki'),issue('nao')))))
    d=doc([call('readingsambiguous',seq(a,b)),call('readingsambiguous',seq(disjunction)),
           call('readingssame',seq(a,b),seq(disjunction))])
    assert values(d)==[True,False,False]


def test_negation_is_kept_inside_each_reading_without_committing_to_either():
    d=doc([call('readingsambiguous',seq(result(),negative())),
           call('readingsresolved',seq(negative()),truth(False)),
           call('readingcontains',seq(result()),negative())])
    assert values(d)==[True,False,False]


def test_membership_and_narrowing_ignore_order_but_not_new_candidates():
    a,b=result(),result(related='nao')
    expressions=[call('readingssame',seq(a,b),seq(b,a,a)),
        call('readingssubset',seq(),seq(a)),call('readingnarrowing',seq(a,b),seq(a)),
        call('readingnarrowing',seq(a),seq(a,b)),call('readingnarrowing',seq(a),seq())]
    assert values(doc(expressions))==[True,True,True,False,False]


def test_every_combination_of_candidate_changes_and_coverage_permission():
    assert revision_checks()['models']==256


def test_every_removed_and_added_candidate_needs_its_own_permission():
    a,b=result(),result(related='nao')
    def only_first(source,context,reading,reason,adding):
        return json.loads(reading.syntax)['arguments'][1]['symbol']=='aki'
    removed=doc([revision(seq(a,b),seq())])
    added=doc([revision(seq(),seq(a,b))])
    assert values(removed,overrides={'change':only_first})==[False]
    assert values(added,overrides={'change':only_first})==[False]
    assert values(removed)==values(added)==[True]


def test_closing_reopening_and_new_closed_state_require_coverage_evidence():
    a,b=result(),result(related='nao')
    d=doc([revision(seq(a),seq(a),False,True),revision(seq(a),seq(a),True,False),
           revision(seq(a,b),seq(a),True,True),revision(seq(a,b),seq(a),False,False)])
    assert values(d,coverage=False)==[False,False,False,True]
    assert values(d)==[True]*4
    assert values(doc([revision(seq(a,b),seq(b,a,a),False,False)]))==[False]


def test_revision_history_preserves_old_readings_and_rejects_a_stale_link():
    d=history()
    assert values(d)==[True,True,True,True,False,False]
    assert {'original','selected','reopened'}<={x['name'] for x in d['declarations']}
    assert d['statements'][0]['body']['arguments'][6]['symbol']=='reason'
    assert d['statements'][1]['body']['arguments'][6]['symbol']=='nextreason'
    changed=deepcopy(d)
    changed['statements'][2]['body']['arguments'][6]=call('original')
    assert values(changed)[2] is False
    changed=deepcopy(d);changed['statements'][2]['body']['arguments'][7]=truth(False)
    assert values(changed)[2] is False
    changed=deepcopy(d);changed['statements'][2]['body']['arguments'][4]=call('target')
    assert values(changed)[2] is False
    changed=deepcopy(d);changed['statements'][2]['body']['arguments'][5]=call('target')
    assert values(changed)[2] is False


def test_ellipsis_provenance_covers_every_argument_and_needs_both_license_and_exact_result():
    rows=binding_diagnostics()
    assert len(rows)==9 and sum(r['value'] for r in rows)==1
    assert values(doc([licensed()]),license=False)==[False]
    assert values(doc([licensed(result_value=result(related='nao'))]))==[False]
    assert values(doc([licensed()]),overrides={'target':lambda:'first'})==[False]


@pytest.mark.parametrize('change',['subject','anchor','template'])
def test_ellipsis_result_does_not_ignore_different_typed_arguments(change):
    kwargs={'subject':{'subject':'aki'},'anchor':{'anchor':'then'},'template':{'topic':'revising'}}[change]
    assert values(doc([op('equal',result(),result(**kwargs))]))==[False]


def test_wrong_argument_type_and_higher_rank_are_not_silently_lowered():
    for bad in (quote(call('now')),quote(call('nao'),rank=1)):
        expression=call('ellipsisresult',quote(ref('praising')),bad,quote(call('aki')),quote(call('now')))
        with pytest.raises(ValueError):doc([op('equal',expression,expression)])


def test_change_and_coverage_use_the_same_source_context_reason_and_polarity():
    a,b=result(),result(related='nao')
    d=doc([revision(seq(a,b),seq(a),False,True)])
    def change(source,context,reading,reason,adding):
        return (source,context,reason,adding)==('first','first','second',False)
    def coverage(source,context,readings,closed,reason):
        return (source,context,closed,reason)==('first','first',True,'second') and len(readings.items)==1
    assert values(d,overrides={'change':change,'coverage':coverage})==[True]
    for field in ('source','context','reason'):
        replacement='first' if field=='reason' else 'second'
        assert values(d,overrides={'change':change,'coverage':coverage,field:lambda x=replacement:x})==[False]
    added=doc([revision(seq(a),seq(a,b),False,True)])
    assert values(added,overrides={'change':change,'coverage':coverage})==[False]
