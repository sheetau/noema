"""Whole opening arguments and their individual references, through recovered Native."""
from copy import deepcopy
from fractions import Fraction as Q
import pytest
from noema.constructed_discourse import function_sort,normalize_document
from noema.constructed_semantics import DescriptionValue,FunctionValue,evaluate_document
from noema.meaning_catalog import _references
from scripts.shared_modality import call,renamed
from scripts import check_einstein_early_visible as check
from scripts.early_individual_reference_roles import build_roles


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
    assert len(doc['statements'])==379 and doc['statements'][:364]==parent['statements']
    ds={d['name']:d for d in doc['declarations']}
    assert all(ds[d['name']]==d for d in parent['declarations'])
    assert check.backprojection(doc)==check.source_excerpt()
    mapping=check.mapping()
    for d in check.source_excerpt()['declarations']:
        if d['kind']=='definition':assert ds[mapping[d['name']]]==renamed(d,mapping)
    assert len(check.REUSED_DEFINITIONS)==166
    assert len(check.NEW_DEFINITIONS)==112 and len(check.vocabulary()._words)==1134
    planned=build_roles()
    role_mapping=dict(check.vocabulary()._symbols)|check.names()
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
    assert bridge['source_statement_indices']==[48,47,43,44,45,46,49,50,51,52,53,54,55,56]
    assert len(bridge['source_reviews'])==6 and bridge['total_annotations']==97
    assert bridge['new_reference_primitives']==1 and bridge['new_core_words']==0
    assert bridge['document_integration_credit']==0 and bridge['total_source_assertions']==282


def test_complete_text_paragraphs_and_printed_formula_are_retained():
    check.text_boundaries()
    anchors=check.author.read('data/early-text-anchors-v1.json')
    assert list(check.SENTENCES.values())==[[1,2],[1,4],[1,5],[2,1],[2,2],[2,3],[2,4],[3,1],[3,2]]
    assert ' '.join(check.TEXT_SENTENCES.values())==' '.join(check.SOURCE_UNITS[f'einstein-1905:u{n:04}']['text'] for n in (3,4,5))
    assert anchors['frontmatter']['eisbc']['text']==check.SOURCE_UNITS['einstein-1905:u0001']['text']
    assert all(row['text']==check.SOURCE_UNITS[row['unit']]['text'] for row in anchors['headings'].values())
    assert anchors['span_text']=={'earlyearthtoken':'Erde','earlymediumtoken':'„Lichtmedium“',
        'earlyfirstordertoken':'Größen erster Ordnung','earlyethertoken':'„Lichtäthers“'}
    assert check.FORMS=={'earlyearthdesignation':'Erde'}
    annotations=check.annotations()
    assert annotations['entries']=={} and set(annotations['new_visible_entries'])=={'earlyearthdesignation'}
    assert not annotations['source_identifier_annotations_modified']


def test_structural_lookups_preserve_parent_and_reject_each_wrong_slot():
    b=values();handlers=check.context_handlers(b)
    assert b['eirg']!=b['ri'] and b['eirg'] in check.SITUATIONS
    assert len(check.SITUATIONS)==len(set(check.SITUATIONS))
    assert check.SITUATIONS[:len(check.previous.SITUATIONS)]==check.previous.SITUATIONS
    assert handlers['textpresentation']()==b['eirg']
    assert handlers['frontmatterreference'](b['eirg'],Q(1))==b['eisbc']
    for context,item in ((b['ri'],Q(1)),(b['eirg'],Q(0)),(b['eirg'],Q(2))):
        with pytest.raises(ValueError):handlers['frontmatterreference'](context,item)
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


def test_native_reference_lookup_does_not_execute_quoted_claims_or_candidate_functions():
    b=values();doc=deepcopy(check.restored()['document']);ds={d['name']:d for d in doc['declarations']}
    targets=('eisbc',*check.HEADINGS)+tuple(check.SENTENCES)+tuple(check.SPANS)+tuple(check.MULTI_SPANS)+tuple(check.DESIGNATIONS)+tuple(check.ROLE_ASSIGNMENTS)
    pending=[check.names()[n] for n in targets];needed=set()
    while pending:
        name=pending.pop()
        if name in needed:continue
        needed.add(name);pending.extend(_references(ds[name].get('body'))-needed)
    doc['declarations']=[d for d in doc['declarations'] if d['name'] in needed];doc['statements']=[]
    handlers={check.vocabulary()._symbols[n]:fn for n,fn in check.context_handlers(b).items()}
    for i,old in enumerate(targets):
        capture='earlycapture'+chr(97+i//26)+chr(97+i%26);sort=check.REFERENCE_SORTS.get(old,'individual')
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


def test_public_cli_uses_the_matching_profile_for_new_contracts():
    from scripts import visible_early_visible_collection as cli
    from scripts.visible_syntax_geometry import to_svg,from_svg
    assert cli.EarlyReferenceVisibleVocabulary is type(check.vocabulary())
    contracts={'contentconsideration','frontmatterreference','signalvelocityratioparameter','hypothesizedpropagationmedium'}
    doc=normalize_document(dict(schema_version='0.16',lexicon_version='0.16',
        declarations=check.vocabulary().imports(contracts),statements=[]))
    compiled=cli.compile_collection(doc,check.LABEL,payload=768)
    recovered=cli.decode_collection([from_svg(to_svg(p['shapes'])) for p in compiled['pages']])
    assert recovered['document']==doc
    complete={d['name']:d for d in check.restored()['document']['declarations']}
    assert all(complete[d['name']]==d for d in doc['declarations'])
