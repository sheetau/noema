from scripts.audit_observer import summarize


def test_observed_ordinal_is_only_phase_progress():
    registry = {'works': {'a': {'reviews': [{'review': 'first'}]},
                          'b': {'reviews': [{'review': 'second'}, {'review': 'third'}]}}}
    snapshot = [{'frames': [{'name': 'validate_binding', 'filename': r'C:\repo\noema\review_registry.py',
                            'locals': [{'name': 'work', 'repr': '"b"'}, {'name': 'name', 'repr': '"second"'}]}]}]
    result = summarize(snapshot, registry)
    assert (result['completed'], result['total']) == (1, 3)
    assert result['whole_audit_percent'] is None and result['remaining_seconds'] is None
    snapshot[0]['frames'][0]['locals'][1]['repr'] = '?'
    assert summarize(snapshot, registry)['stage'] == 'unknown_from_this_sample'
