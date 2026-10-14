from copy import deepcopy

import pytest

from noema.grammar import parse
from noema.integration_audit import audit_integration, dependency_path
from noema.semantics import SemanticError


def test_library_availability_is_not_manuscript_use():
    doc = parse('n:r aa[] c.d ab[] c[k aa[]].')
    result = audit_integration(doc)
    assert result['statement_count'] == 0
    assert result['statement_reachable_symbols'] == []
    assert result['unreferenced_definitions'] == ['ab']
    assert not result['semantic_equivalence_verified']


def test_quoted_function_references_count_without_execution_or_alias_substitution():
    doc = parse('n:r aa[] a.d ab[] a[k aa[]].d ac[] a[k aa[]].'
                'r ad[i[h[] a]] c.q[k ad[r[p ab]]].')
    before = deepcopy(doc)
    result = audit_integration(doc)
    assert result['statement_reachable_symbols'] == ['aa', 'ab', 'ad']
    assert result['unreferenced_definitions'] == ['ac']
    assert dependency_path(doc, 0, 'aa') == ['ab', 'aa']
    assert dependency_path(doc, 0, 'ac') is None
    assert doc == before
    assert result['quoted_references_included']
    assert result['structural_audit_only']


def test_nested_statements_keep_both_assumption_and_body():
    doc = parse('n:r aa[] c.r ab[] c.r ac[] c.a[k aa[]][q[k ab[]].].q[k ac[]].')
    result = audit_integration(doc)
    assert result['statements'][0]['reachable_symbols'] == ['aa', 'ab']
    assert result['statements'][1]['reachable_symbols'] == ['ac']
    assert dependency_path(doc, 0, 'ac') is None


def test_external_function_value_does_not_imply_a_definition_reference():
    doc = parse('n:r aa[] h[] c.r ab[] c.d ac[] c[k ab[]].q[c[k aa[]][]].')
    result = audit_integration(doc)
    assert result['statement_reachable_symbols'] == ['aa']
    assert result['unreferenced_definitions'] == ['ac']


def test_references_under_fold_and_nested_quote_are_traversed():
    doc = parse('n:r aa[] c.r ab[] c.d ac[] j[c][l[c][k aa[]]].'
        'd ad[] c[q[k ac[]][k aa[]][i[value c item c][x[v value][v item]]]].'
        'q[e[r[r[p ad]]][r[r[p ad]]]].')
    assert audit_integration(doc)['statement_reachable_symbols'] == ['aa', 'ac', 'ad']
    assert dependency_path(doc, 0, 'aa') == ['ad', 'aa']


@pytest.mark.parametrize('index,target', [(True, 'aa'), (-1, 'aa'), (1, 'aa'), (0, 'missing'), (0, [])])
def test_invalid_requests_are_rejected(index, target):
    with pytest.raises(SemanticError):
        dependency_path(parse('n:r aa[] c.q[k aa[]].'), index, target)


def test_invalid_unused_definition_is_not_ignored():
    doc = parse('n:r aa[] c.d ab[] c[k aa[]].q[k aa[]].')
    doc['declarations'][1]['body']['symbol'] = 'missing'
    with pytest.raises(SemanticError):
        audit_integration(doc)
