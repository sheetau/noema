"""Replay retained motto diagnostics on exact recovered paragraph definitions."""
from copy import deepcopy
from functools import lru_cache
from types import FunctionType
import pytest
from noema.meaning_catalog import _references
from noema.constructed_semantics import evaluate_document
from scripts import check_contextual_motto as original
from scripts import check_kant_first_paragraph_visible as check

RESULTS={}
RECOVERED_DEFINITIONS_SEEN=set()
HISTORICAL_COMPARISON_DEFINITIONS=set()


@lru_cache(None)
def recovered():return {d['name']:d for d in check.backprojection(check.restored()['document'])['declarations'] if d['kind']=='definition'}


def evaluated(doc,*,primitives,**options):
    ds={d['name']:d for d in doc['declarations']};needed=set();pending=_references(doc['statements'])
    while pending:
        name=pending.pop()
        if name not in needed:needed.add(name);pending.update(_references(ds[name].get('body')))
    actual=deepcopy(doc);actual['declarations']=[d for d in actual['declarations'] if d['name'] in needed]
    for index,d in enumerate(actual['declarations']):
        if d['kind']!='definition':continue
        if d['name'] in recovered():
            assert recovered()[d['name']]==d,('Changed current paragraph body',d['name'])
            actual['declarations'][index]=deepcopy(recovered()[d['name']]);RECOVERED_DEFINITIONS_SEEN.add(d['name'])
        else:HISTORICAL_COMPARISON_DEFINITIONS.add(d['name'])
    selected={d['name']:primitives[d['name']] for d in actual['declarations'] if d['kind']=='primitive'}
    return evaluate_document(actual,primitives=selected,**options)


@lru_cache(None)
def namespace():
    ns=dict(vars(original))
    for name,wrapped in vars(original).items():
        fn=getattr(wrapped,'__wrapped__',wrapped)
        if isinstance(fn,FunctionType) and fn.__module__==original.__name__:
            copied=FunctionType(fn.__code__,ns,name,fn.__defaults__,fn.__closure__);copied.__kwdefaults__=fn.__kwdefaults__
            ns[name]=lru_cache(None)(copied) if hasattr(wrapped,'cache_info') else copied
    ns['evaluate_document']=evaluated
    return ns


@pytest.mark.parametrize('function,key',[('directive_checks','directives'),('presentation_checks','presentation'),('integrated_conditions','integrated_conditions')])
def test_retained_motto_diagnostics_on_recovered_definitions(function,key):
    result=namespace()[function]()
    assert result==check.read('reports/contextual-motto-v1.json')[key]
    RESULTS[key]=result
