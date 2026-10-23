"""Distinguish one common solution from a different solution per difficulty."""
from itertools import product
from scripts.check_clock_definition_proposal import setup,relation,run


def test_all_success_patterns_with_two_fully_admissible_results():
    base,rows=setup()
    # Both results satisfy every requirement of the same proposed clock rule.
    # Only the difficulty-by-result success table varies below.
    for symbol in ('eisdf','eise6','eise7','eisdu','eisfw','eisfx'):
        rows[symbol]|={row[:-1]+('r2',) for row in tuple(rows[symbol])}
    rows['eisf2'].add(('proposal','task','paper','seen','r2'))
    base|={symbol:relation(values) for symbol,values in rows.items()}
    for result in ('r1','r2'):
        assert run('eijj',['proposal','author','task','clock','hand','frame','unit','paper',result],base)
    for bits in product((False,True),repeat=4):
        outcomes={("proposal",difficulty,"paper","seen",result)
                  for (result,difficulty),success in zip(product(('r1','r2'),('d1','d2')),bits)
                  if success}
        model=base|{'eisfz':relation(outcomes)}
        assert run('eijo',[],model)==((bits[0] and bits[1]) or (bits[2] and bits[3]))
