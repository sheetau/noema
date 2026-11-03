import pytest
from scripts.check_kant_type_reference_declaration import cases,checked,records


@pytest.mark.parametrize('index',range(len(cases())))
def test_changed_saved_declaration_recovers_exactly(index):
    row=checked(index)
    assert row['current_events']<row['previous_events']
    assert row['circles']<row['previous_circles']
    assert not row['branch_limits'] and not row['unbranched_paths']


def test_unaffected_declarations_are_not_regenerated():
    assert [r['key'] for r in records() if not r['changed']]==['aa','hztb','ev','va']
