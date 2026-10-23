"""Distinguish selector inputs and rule out per-event possible-world swapping."""
from fractions import Fraction
from scripts.check_local_clock_valuation import setup,run,relation,BASE,METHOD


def test_exact_candidate_record_keys_and_value_binding():
    cuts,model,*_=setup()
    seen=[]
    def fields(event,clock,slot,context):
        assert (event,clock,context)==('event','clock','possible')
        assert slot in (Fraction(1),Fraction(2))
        seen.append(slot)
        return {Fraction(1):'near',Fraction(2):'display'}[slot]
    def reading(event,clock,unit,context):
        assert (event,clock,unit,context)==('event','clock','unit','possible')
        return cuts.make(Fraction(9))
    strict=model|{'eish5':fields,'eish6':reading}
    assert run('eik4',BASE+['event'],strict)
    assert set(seen)=={Fraction(1),Fraction(2)}
    # Keep all physical readings unchanged; a mismatched assigned value must fail.
    assert not run('eik4',BASE+['event'],strict|{'eish4':lambda *xs:False})


def test_two_events_cannot_choose_different_success_candidates():
    _,model,*_=setup()
    two=('now','possible')
    valid={tuple(BASE[:-1]+['now','event']),tuple(BASE+['event2'])}
    mixed=model|{
        'eisia':relation({tuple(METHOD+[s]) for s in two}),
        'eik2':relation({tuple(BASE[:-1]+[s]) for s in two}),
        'eikz':relation({(e,'place','frame','now') for e in ('event','event2')}),
        'eik4':relation(valid),
    }
    assert not run('eik6',METHOD,mixed,'method')
    assert run('eik6',METHOD,mixed|{'eik4':relation(valid|{tuple(BASE+['event'])})},'method')
