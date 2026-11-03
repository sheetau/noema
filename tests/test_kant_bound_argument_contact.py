from functools import lru_cache
from scripts.check_kant_bound_argument_contact import build_report, RAILS

report=lru_cache(maxsize=1)(build_report)


def test_all_four_legal_medium_small_contacts_recover_actual_syntax():
    rows=report()['cases']
    for i,rail in enumerate(RAILS):
        row=rows['inventory-'+str(i)]
        assert row['exact'] and row['contacts']
        assert (row['medium_rail'],row['small_rail'])==rail
        assert any((r['medium'][1],r['small'][1])==rail for r in row['contacts'])
        assert all(r['medium'][0]==r['small'][0] for r in row['contacts'])


def test_order_type_nested_binding_and_quote_are_preserved():
    rows=report()['cases']
    for key in ('situation-first','situation-last','nested-inner','quoted','individual'):
        assert rows[key]['exact'] and rows[key]['contacts']
        assert rows[key]['branches']>0
    assert rows['situation-first']['syntax_sha256']!=rows['situation-last']['syntax_sha256']
    assert rows['nested-inner']['syntax_sha256']!=rows['nested-outer']['syntax_sha256']
    assert rows['nested-outer']['exact'] and not rows['nested-outer']['contacts']
    assert len(rows['quoted']['contacts'])==2


def test_contact_does_not_bypass_scope_or_argument_role():
    rows=report()['cases']
    assert rows['unbound']['error']==rows['quote-escape']['error']=='Unbound visible variable'
    assert rows['main-flow']['error'].startswith('Contact must join')
    assert all(rows[k]['rejected'] for k in ('unbound','quote-escape','main-flow'))


def test_current_and_saved_source_drawings_recover_the_same_native_statements():
    for number in (5,9):
        row=report()['cases']['statement-'+str(number)]
        assert row['exact'] and row['previous_svg_exact']
        assert row['statement']==number
