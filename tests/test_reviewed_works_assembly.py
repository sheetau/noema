from copy import deepcopy
import pytest
from scripts.assemble_reviewed_works import select_statements, assembly_checks


def test_selection_preserves_occurrences_scopes_and_original_input():
    nested = dict(kind='assume', condition={'x': 1}, statements=[{'kind': 'assert', 'body': {'x': 2}}])
    doc = dict(declarations=[{'name': 'aa'}], statements=[nested, {'kind': 'assert'}, nested])
    before = deepcopy(doc)
    bindings = [dict(review='first', statements=[0, 2]), dict(review='shared', statements=[2])]
    selected, rebound, remap = select_statements(doc, bindings)
    assert doc == before and selected['declarations'] == doc['declarations']
    assert selected['statements'] == [nested, nested]
    assert remap == {0: 0, 2: 1} and rebound[1]['statements'] == [1]
    selected['statements'][0]['condition']['x'] = 99
    assert doc == before and selected['statements'][1] == nested


@pytest.mark.parametrize('indices', [[], [-1], [3], [True], [2, 0], [0, 0]])
def test_invalid_selection_is_rejected(indices):
    with pytest.raises(ValueError):
        select_statements(dict(declarations=[], statements=[{}, {}, {}]),
                          [dict(review='bad', statements=indices)])


def test_all_registered_judgments_survive_in_complete_editions():
    results, _ = assembly_checks()
    assert results['kant-1784']['units'] == 20
    assert results['einstein-1905']['units'] == 282
