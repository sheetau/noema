"""Whole observables argument and closed typed references, through recovered Native."""
from copy import deepcopy
from fractions import Fraction as Q
import pytest
from noema.constructed_discourse import function_sort,normalize_document
from noema.constructed_semantics import DescriptionValue,FunctionValue,evaluate_document
from noema.meaning_catalog import _references
from scripts.shared_modality import call,renamed
from scripts import check_einstein_tenth_observables_visible as check
from scripts.tenth_observables_reference_roles import build_roles


def forbidden(*args):
    raise ValueError('Quoted role, candidate function or unknown input executed')


def same_opaque_function(actual,expected):
    # Native deliberately returns a guarded wrapper on every named function
    # lookup. Inspect only this exact engine wrapper; never invoke the function.
    seen=set()
    while actual is not expected:
        if not isinstance(actual,FunctionValue):return False
        assert actual.parameters==expected.parameters and actual.result==expected.result
        assert id(actual) not in seen;seen.add(id(actual))
        implementation=actual.implementation
        if isinstance(implementation,FunctionValue):
            actual=implementation;continue
        if implementation is forbidden:return False
        assert implementation.__module__=='noema.constructed_semantics'
        assert implementation.__qualname__.endswith('.make_function.<locals>.guarded')
        cells=dict(zip(implementation.__code__.co_freevars,
                       (cell.cell_contents for cell in implementation.__closure__)))
        actual=cells['raw'];assert isinstance(actual,FunctionValue)
    return True


def values():
    result=dict(check.BASE)
    for i,(old,sort) in enumerate(check.REFERENCE_SORTS.items()):
        if isinstance(sort,dict):
            result[old]=FunctionValue(tuple(sort['parameters']),sort['result'],forbidden)
        elif sort=='number':result[old]=Q(i-26,3)
    return result


def test_parent_and_all_source_bodies_and_roles_are_preserved():
    doc=check.restored()['document'];parent=check.previous.document()
    assert len(doc['statements'])==359 and doc['statements'][:343]==parent['statements']
    ds={d['name']:d for d in doc['declarations']}
    assert all(ds[d['name']]==d for d in parent['declarations'])
    assert check.backprojection(doc)==check.source_excerpt()
    mapping=check.mapping()
    for d in check.source_excerpt()['declarations']:
        if d['kind']=='definition':assert ds[mapping[d['name']]]==renamed(d,mapping)
    assert len(check.NEW_DEFINITIONS)==139 and len(check.vocabulary()._words)==1061
    planned=build_roles(check.catalogs()['einstein-1905'].document)
    role_mapping=check.names()|{old:check.vocabulary()._symbols[new] for old,new in check.RELATIONS.items()}|mapping
    # The new closed bodies must be exactly the independently checked role builder.
    for role in renamed(list(planned.values()),role_mapping):
        interface=[]
        for symbol in sorted(_references(role['body'])):
            d=ds[symbol]
            types=[p['sort'] for p in d['parameters']] if d['kind']=='definition' else d['parameters']
            interface.append(dict(kind='primitive',name=symbol,parameters=types,result=d['result']))
        expected=normalize_document(dict(schema_version='0.16',lexicon_version='0.16',
            declarations=interface+[role],statements=[]))['declarations'][-1]
        assert ds[role['name']]==expected
    bridge=check.bridge()
    assert bridge['source_statement_indices']==[280,*range(268,277),281]
    assert len(bridge['source_reviews'])==11 and bridge['total_annotations']==94
    assert bridge['new_reference_primitives']==0 and bridge['new_core_words']==0
    assert bridge['document_integration_credit']==0 and bridge['total_source_assertions']==265


def test_complete_text_paragraphs_and_printed_formula_are_retained():
    check.text_boundaries()
    assert list(check.SENTENCES.values())==[[115,1],[116,1],[116,2],[117,1],[118,1],[119,1],[119,2],[120,1]]
    text=' '.join(check.TEXT_SENTENCES.values())
    source=' '.join(check.SOURCE_UNITS[f'einstein-1905:u{n:04}']['text'] for n in range(265,276))
    assert text.split()==source.split()
    def span(old):
        first,a,last,b=check.SPANS[old]
        order=list(check.SENTENCES);i=order.index(first);j=order.index(last)
        if i==j:return ' '.join(check.TOKENS[first][a-1:b])
        tokens=check.TOKENS[first][a-1:]
        for n in order[i+1:j]:tokens+=check.TOKENS[n]
        return ' '.join(tokens+check.TOKENS[last][:b])
    assert check.MULTI_SPANS=={'eis3x':['eis3y','eis3z']}
    assert span('eis32')=='[M0436]'
    assert span('eis4u')==check.SOURCE_UNITS['einstein-1905:u0271']['text']
    assert span('eis4r')=='[M0438]'
    assert [span(n) for n in ('eis4v','eis4w','eis4x')]==['[M0441]','oder','[M0442]']
    assert check.DESIGNATIONS=={'eis33':['tenthobservablesamtoken',1],
        'eis34':['tenthobservablesaetoken',1],'eis4s':['eis4r',1],
        'eis4y':['tenthobservablesrtoken',1],'eis4z':['tenthobservablesntoken',1]}
    assert check.FORMS=={'eis33':'A_m','eis34':'A_e','eis4s':'P','eis4y':'R','eis4z':'N'}
    annotations=check.annotations()
    assert set(annotations['entries'])=={'eis33','eis34'}
    assert set(annotations['new_visible_entries'])=={'eis4s','eis4y','eis4z'}
    assert annotations['source_formulas']=={'eis4s':'M0438','eis4y':'M0439','eis4z':'M0440'}
    assert not annotations['source_identifier_annotations_modified']


def test_structural_lookups_preserve_parent_and_reject_each_wrong_slot():
    b=values();handlers=check.context_handlers(b)
    for name,(first,start,last,end) in check.SPANS.items():
        args=[b['eirf'],b[first],Q(start),b[last],Q(end),b['ri']]
        assert handlers['sentencetokenspanreference'](*args)==b[name]
        for slot in range(6):
            bad=args[:];bad[slot]=Q(999) if slot in (2,4) else 'unknown'
            with pytest.raises(ValueError):handlers['sentencetokenspanreference'](*bad)
    for name,(first,last) in check.MULTI_SPANS.items():
        args=[b['eirf'],b[first],b[last],b['ri']]
        assert handlers['sentencespanreference'](*args)==b[name]
        for slot in range(4):
            bad=args[:];bad[slot]='unknown'
            with pytest.raises(ValueError):handlers['sentencespanreference'](*bad)
    for name,(paragraph,sentence) in check.SENTENCES.items():
        assert handlers['sentencereference'](b['ri'],Q(paragraph),Q(sentence))==b[name]
    for name,(node,index) in check.DESIGNATIONS.items():
        args=[b['eirf'],b[node],Q(index),b['ri']]
        assert handlers['designationreference'](*args)==b[name]
        for slot in range(4):
            bad=args[:];bad[slot]=Q(999) if slot==2 else 'unknown'
            with pytest.raises(ValueError):handlers['designationreference'](*bad)
    for name,(first,start,last,end) in check.previous.SPANS.items():
        assert handlers['sentencetokenspanreference'](b['eirf'],b[first],Q(start),b[last],Q(end),b['ri'])==b[name]


def test_native_reference_lookup_does_not_execute_physics_or_candidate_functions():
    b=values();doc=deepcopy(check.restored()['document']);ds={d['name']:d for d in doc['declarations']}
    targets=tuple(check.SENTENCES)+tuple(check.SPANS)+tuple(check.MULTI_SPANS)+tuple(check.DESIGNATIONS)+tuple(check.ROLE_ASSIGNMENTS)
    pending=[check.names()[n] for n in targets];needed=set()
    while pending:
        name=pending.pop()
        if name in needed:continue
        needed.add(name);pending.extend(_references(ds[name].get('body'))-needed)
    doc['declarations']=[d for d in doc['declarations'] if d['name'] in needed];doc['statements']=[]
    handlers={check.vocabulary()._symbols[n]:fn for n,fn in check.context_handlers(b).items()}
    for i,old in enumerate(targets):
        capture='observablescapture'+chr(97+i//26)+chr(97+i%26);sort=check.REFERENCE_SORTS.get(old,'individual')
        doc['declarations'].append(dict(kind='primitive',name=capture,parameters=[sort],result='truth'))
        doc['statements'].append(dict(kind='ask',body=call(capture,call(check.names()[old]))))
        def captured(x,old=old,sort=sort):
            if not isinstance(sort,dict):return x==b[old]
            assert same_opaque_function(x,b[old]),old
            other=FunctionValue(tuple(sort['parameters']),sort['result'],forbidden)
            assert not same_opaque_function(x,other),('Wrong candidate accepted',old)
            return True
        handlers[capture]=captured
    result=evaluate_document(doc,individuals=tuple({x for x in b.values() if isinstance(x,str)}),
        situations=check.SITUATIONS,primitives={d['name']:handlers.get(d['name'],forbidden)
            for d in doc['declarations'] if d['kind']=='primitive'},memoize_definitions=True,memoize_expressions=True)
    assert len(result)==len(targets)
    assert all(r['value'] is True for r in result),[(n,r) for n,r in zip(targets,result) if r['value'] is not True]


def test_closed_roles_reject_unknown_keys_and_keep_an_acyclic_dependency_graph():
    b=values();ds={d['name']:d for d in check.restored()['document']['declarations']}
    for old in check.ROLE_ASSIGNMENTS:
        sort=check.REFERENCE_SORTS[old];kind=check.reference_kind(old)
        description=DescriptionValue(check.canonical(dict(kind='function_ref',symbol=check.reference_roles()[old])),
            check.canonical(function_sort([sort,'situation'],'truth')))
        lookup=check.reference_model(b,kind)
        args=[b['eirf'],b[check.reference_anchor(old)],description,b['ri']]
        result=lookup.described(*args)
        assert result is b[old] if isinstance(sort,dict) else result==b[old]
        for slot in range(4):
            bad=args[:];bad[slot]=DescriptionValue(check.canonical(dict(kind='function_ref',symbol='unknown')),description.result_type) if slot==2 else 'unknown'
            with pytest.raises(ValueError):lookup.described(*bad)
        pending=[check.reference_roles()[old]];seen=set()
        while pending:
            name=pending.pop()
            if name in seen:continue
            seen.add(name);pending.extend(_references(ds[name].get('body'))-seen)
        assert check.names()[old] not in seen
