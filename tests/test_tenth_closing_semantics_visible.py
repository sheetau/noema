"""Replay retained closing fixtures against checked recovered Native bodies.

Only the obsolete dynamic etp baseline is evaluated by the original legacy
engine. It is a cross-engine comparator, never a recovered Native definition.
"""
from copy import deepcopy
from functools import lru_cache
from types import FunctionType
from fractions import Fraction
import json
import pytest
from noema import finite_semantics as legacy
from noema import constructed_semantics as native
from noema.constructed_discourse import normalize_document
from noema.extraction import extract_document
from scripts.shared_modality import renamed
from scripts import check_einstein_tenth_closing_visible as check

RECOVERED_DEFINITIONS_SEEN = set()
LEGACY_COMPARISONS = []
RESULTS = {}
CHECKS = ('credit_checks','support_checks','date_checks','presentation_checks')


@lru_cache(None)
def mapping():
    return check.names()|{old:check.vocabulary()._symbols[new] for old,new in check.RELATIONS.items()}|check.mapping()


@lru_cache(None)
def recovered(): return {d['name']:d for d in check.restored()['document']['declarations']}


def checked_extract(document, *, roots=(), statement_indices=()):
    result=extract_document(document,roots=roots,statement_indices=statement_indices)
    mapped=normalize_document(renamed(result.document,mapping()))
    inverse={v:k for k,v in mapping().items()}
    for i,(original,expected) in enumerate(zip(result.document['declarations'],mapped['declarations'],strict=True)):
        if original['kind']!='definition':continue
        actual=recovered().get(expected['name'])
        assert actual==expected,('Unrecovered or changed closing source definition',original['name'])
        RECOVERED_DEFINITIONS_SEEN.add(original['name'])
        result.document['declarations'][i]=renamed(deepcopy(actual),inverse)
    return result


class RuntimeBoundary:
    """Identity-preserving wrappers; never evaluate quoted syntax."""
    def __init__(self, symbols):
        self.forward=symbols;self.reverse={v:k for k,v in symbols.items()}
        self.to_native={};self.to_legacy={}

    def convert(self,value,to_native):
        if type(value) in (str,bool,int,Fraction) or value is None:return value
        src,dst=(legacy,native) if to_native else (native,legacy)
        cache,back=(self.to_native,self.to_legacy) if to_native else (self.to_legacy,self.to_native)
        found=cache.get(id(value))
        if found is not None:
            assert found[0] is value
            return found[1]
        if isinstance(value,src.FunctionValue):
            converted=dst.FunctionValue(value.parameters,deepcopy(value.result),
                lambda *args:self.convert(value(*(self.convert(x,not to_native) for x in args)),to_native))
        elif isinstance(value,src.SequenceValue):
            converted=dst.SequenceValue(tuple(self.convert(x,to_native) for x in value.items),value.element_type)
        elif isinstance(value,src.DescriptionValue):
            if not to_native and value.rank!=0:raise ValueError('Historical fixture cannot consume a ranked description')
            syntax=renamed(json.loads(value.syntax),self.forward if to_native else self.reverse)
            converted=dst.DescriptionValue(json.dumps(syntax,sort_keys=True),value.result_type)
        elif isinstance(value,src.Content):
            converted=dst.Content(value.situations,tuple(self.convert(x,to_native) for x in value.values))
        elif isinstance(value,src.Message):
            converted=dst.Message(value.force,self.convert(value.content,to_native))
        elif isinstance(value,src.QuestionValue):
            converted=dst.QuestionValue(self.convert(value.function,to_native))
        else:raise ValueError('Unsupported diagnostic runtime wrapper')
        cache[id(value)]=(value,converted);back[id(converted)]=(converted,value)
        return converted

    def handler(self,callback):
        def wrapped(*args):
            return self.convert(callback(*(self.convert(x,False) for x in args)),True)
        return wrapped


def native_evaluate(document, *, primitives, **options):
    boundary=RuntimeBoundary(mapping())
    return native.evaluate_document(normalize_document(renamed(document,mapping())),
        primitives={mapping().get(n,n):boundary.handler(fn) for n,fn in primitives.items()},**options)


@lru_cache(None)
def namespace():
    from scripts import check_closing_acknowledgment as original
    ns=dict(vars(original))
    for name,wrapped in vars(original).items():
        fn=getattr(wrapped,'__wrapped__',wrapped)
        if isinstance(fn,FunctionType) and fn.__module__==original.__name__:
            copied=FunctionType(fn.__code__,ns,name,fn.__defaults__,fn.__closure__)
            copied.__kwdefaults__=fn.__kwdefaults__
            ns[name]=lru_cache(None)(copied) if hasattr(wrapped,'cache_info') else copied
    ns['extract_document']=checked_extract
    ns['evaluate_document']=native_evaluate
    run=ns['run']
    def recorded_run(root,values,model,*args,**kwargs):
        if root=='etp':
            # Preserve the actual historical dynamic comparator. It is absent
            # from Native and remains explicitly outside recovered coverage.
            result=original.run(root,values,model,*args,**kwargs)
            LEGACY_COMPARISONS.append(dict(root=root,engine='noema.finite_semantics',result=result))
            return result
        return run(root,values,model,*args,**kwargs)
    ns['run']=recorded_run
    return ns


@pytest.mark.parametrize('name',CHECKS)
def test_retained_finite_closing_checks_on_recovered_native(name):
    # Full source closure first, including quoted message/content dependencies.
    checked_extract(check.catalogs()['einstein-1905'].document,statement_indices=check.SOURCE_ORDER)
    result=namespace()[name]()
    assert result['cases']>0
    RESULTS[name]=result
    assert set(check.NEW_DEFINITIONS)<=RECOVERED_DEFINITIONS_SEEN
    assert 'etp' not in RECOVERED_DEFINITIONS_SEEN


def test_runtime_boundary_preserves_identity_order_and_opaque_descriptions():
    boundary=RuntimeBoundary({'sourcegoal':'visiblegoal'})
    description=native.DescriptionValue(json.dumps(dict(kind='call',symbol='visiblegoal',arguments=[])),json.dumps('content'))
    old=boundary.convert(description,False)
    assert json.loads(old.syntax)==dict(kind='call',symbol='sourcegoal',arguments=[])
    assert boundary.convert(old,True) is description
    seen=[]
    function=legacy.FunctionValue(('individual','individual','situation'),'truth',
        lambda *xs:seen.append(xs) or xs==('first','second','context'))
    converted=boundary.convert(function,True)
    assert boundary.convert(function,True) is converted
    assert boundary.convert(converted,False) is function
    assert seen==[]
    assert converted('first','second','context')
    assert not converted('second','first','context')
    assert seen==[('first','second','context'),('second','first','context')]
    sequence=legacy.SequenceValue(('second','first'),json.dumps('individual'))
    assert boundary.convert(sequence,True).items==('second','first')
    with pytest.raises(ValueError,match='ranked'):
        boundary.convert(native.DescriptionValue(description.syntax,description.result_type,1),False)
    with pytest.raises(ValueError,match='Unsupported'):
        boundary.convert(object(),True)
