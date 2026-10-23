"""Exercise the whole record method with its native physical dependency body."""
from scripts.check_reception_time_alternative import setup,run,relation,METHOD


def test_full_method_rejects_a_bad_second_arrival():
    _,model,rows,*rest=setup()
    fields=rest[-2]
    assert run('eike',METHOD,model)
    # Include another arrival, not just an isolated invocation of the rule.
    selected=rows['eisgw']|{('task','record2','observer','frame','now')}
    shaped=rows['eisgy']|{('record2','task','observer','frame','now')}
    expanded=model|{'eisgw':relation(selected),'eisgy':relation(shaped)}
    assert run('eike',METHOD,expanded)
    fields['record2','now']=('event','signal','departure','other','display')
    assert not run('eike',METHOD,expanded)
    # The bad row is outside the selected set in the original method.
    assert run('eike',METHOD,model)
