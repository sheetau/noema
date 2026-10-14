import ast
import inspect

import pytest

from noema.grammar import parse as stable_parse
from noema.constructed import parse as constructed_parse, format_graph
from noema.script import transcribe
from scripts import audit_written_progress as legacy
from scripts import audit_written_progress_extended as extended


@pytest.mark.parametrize('text',('n:s[e[n p a b][n p a b]].','m:s[e[n p a b][n p a b]].'))
def test_stable_editions_still_use_their_existing_parser(text):
    assert extended.parse(text)==stable_parse(text)


@pytest.mark.parametrize('header',('o','p'))
@pytest.mark.parametrize('notation',('compact','full'))
@pytest.mark.parametrize('native',(False,True))
def test_explicit_experimental_editions_are_parsed_without_promotion(header,notation,native):
    text=header+':s[e[r b[e[n p a b][n p a b]]][r b[e[n p a b][n p a b]]]].'
    doc=constructed_parse(text)
    formatted=format_graph(doc,notation)
    if native: formatted=transcribe(formatted,alphabet='v2')
    assert extended.parse(formatted)==doc
    assert doc['schema_version']==('0.15' if header=='o' else '0.16')


def test_type_and_scope_errors_are_not_hidden_by_parser_fallback():
    with pytest.raises(ValueError): extended.parse('p:s[e[r b[v outside]][r b[v outside]]].')


@pytest.mark.parametrize('name',('digest','load_json','merge_ranges','collect_alignment','summarize'))
def test_coverage_and_semantic_completion_rules_remain_identical(name):
    old=ast.dump(ast.parse(inspect.getsource(getattr(legacy,name))))
    new=ast.dump(ast.parse(inspect.getsource(getattr(extended,name))))
    assert old==new
