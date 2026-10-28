"""Whole energy argument and closed typed references, through recovered Native."""
from copy import deepcopy
from fractions import Fraction as Q
import pytest
from noema.constructed_discourse import function_sort,normalize_document
from noema.constructed_semantics import DescriptionValue,FunctionValue,evaluate_document
from noema.meaning_catalog import _references
from scripts.shared_modality import call,renamed
from scripts import check_einstein_tenth_energy_visible as check
from scripts.tenth_energy_reference_roles import build_roles


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
    assert len(doc['statements'])==343 and doc['statements'][:338]==parent['statements']
    ds={d['name']:d for d in doc['declarations']}
    assert all(ds[d['name']]==d for d in parent['declarations'])
    assert check.backprojection(doc)==check.source_excerpt()
    mapping=check.mapping()
    for d in check.source_excerpt()['declarations']:
        if d['kind']=='definition':assert ds[mapping[d['name']]]==renamed(d,mapping)
    assert len(check.NEW_DEFINITIONS)==70 and len(check.vocabulary()._words)==1048
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
    assert bridge['source_statement_indices']==[264,265,266,267]
    assert len(bridge['source_reviews'])==4 and bridge['total_annotations']==89
    assert bridge['new_reference_primitives']==1 and bridge['new_core_words']==0
    assert bridge['document_integration_credit']==0 and bridge['total_source_assertions']==254
    assert 'serg' in check.NEW_DEFINITIONS and 'serh' not in mapping


def test_complete_text_paragraphs_and_printed_formula_are_retained():
    check.text_boundaries()
    assert list(check.SENTENCES.values())==[[112,1],[112,2],[112,3],[112,4],[113,1],[113,2],[114,1]]
    text=list(check.TEXT_SENTENCES.values())
    source=lambda n:check.SOURCE_UNITS[f'einstein-1905:u{n:04}']['text']
    assert ' '.join(text[:4])==source(261)+' '+source(262)
    assert ' '.join(text[4:6])==source(263) and text[6]==source(264)
    def span(old):
        first,a,last,b=check.SPANS[old];assert first==last
        return ' '.join(check.TOKENS[first][a-1:b])
    assert span('eis3f')=='[M0425]' and span('eis3h')=='[M0427]'
    assert span('eis3g')=='Bewegungsenergie [M0426]'
    assert span('eis3o')=='wie bei unseren früheren Resultaten'
    assert span('eis3q')=='dem oben angeführten Argument zufolge'
    assert check.DESIGNATIONS=={'eis3j':['tenthenergywtoken',1]} and check.FORMS=={'eis3j':'W'}
    annotations=check.annotations()
    assert annotations['entries']=={} and set(annotations['new_visible_entries'])=={'eis3j'}
    assert annotations['source_formula']=='M0426' and not annotations['source_identifier_annotations_modified']


def test_structural_lookups_preserve_parent_and_reject_each_wrong_slot():
    b=values();handlers=check.context_handlers(b)
    for name,(first,start,last,end) in check.SPANS.items():
        args=[b['eirf'],b[first],Q(start),b[last],Q(end),b['ri']]
        assert handlers['sentencetokenspanreference'](*args)==b[name]
        for slot in range(6):
            bad=args[:];bad[slot]=Q(999) if slot in (2,4) else 'unknown'
            with pytest.raises(ValueError):handlers['sentencetokenspanreference'](*bad)
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
    targets=tuple(check.SENTENCES)+tuple(check.SPANS)+tuple(check.DESIGNATIONS)+tuple(check.ROLE_ASSIGNMENTS)
    pending=[check.names()[n] for n in targets];needed=set()
    while pending:
        name=pending.pop()
        if name in needed:continue
        needed.add(name);pending.extend(_references(ds[name].get('body'))-needed)
    doc['declarations']=[d for d in doc['declarations'] if d['name'] in needed];doc['statements']=[]
    handlers={check.vocabulary()._symbols[n]:fn for n,fn in check.context_handlers(b).items()}
    for i,old in enumerate(targets):
        capture='energycapture'+chr(97+i//26)+chr(97+i%26);sort=check.REFERENCE_SORTS.get(old,'individual')
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
