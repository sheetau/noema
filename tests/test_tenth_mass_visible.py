"""Whole recovered mass group, source continuity and closed reference lookups."""
from copy import deepcopy
from fractions import Fraction as Q
import pytest
from noema.constructed_discourse import function_sort
from noema.constructed_semantics import DescriptionValue,evaluate_document
from noema.meaning_catalog import _references
from scripts.shared_modality import call,renamed
from scripts import check_einstein_tenth_mass_visible as check
from scripts.tenth_mass_reference_roles import definitions as planned_role_definitions

def forbidden(*args):raise ValueError('Unexpected execution of quoted physical content or unknown reference')
def values():return dict(check.BASE)
def fingerprint(value,sort):
    assert sort=='individual'
    return value

def test_parent_and_every_source_body_are_preserved():
    assert list(check.ROLE_DEFINITIONS.values())==planned_role_definitions()
    doc=check.restored()['document'];parent=check.previous.document()
    assert check.backprojection(doc)==check.source_excerpt()
    assert len(doc['statements'])==338 and doc['statements'][:329]==parent['statements']
    ds={d['name']:d for d in doc['declarations']}
    assert all(ds[d['name']]==d for d in parent['declarations'])
    mapping=check.mapping()
    for d in check.source_excerpt()['declarations']:
        if d['kind']=='definition':assert ds[mapping[d['name']]]==renamed(d,mapping)
    assert len(check.NEW_DEFINITIONS)==93 and len(check.vocabulary()._words)==1039
    bridge=check.bridge()
    assert bridge['source_statement_indices']==[259,258,*range(260,264)]
    assert len(bridge['source_reviews'])==9 and bridge['total_annotations']==88
    assert bridge['new_reference_primitives']==0 and bridge['new_core_words']==0 and bridge['document_integration_credit']==0
    assert check.FORWARD_MAPS=={'zza':'rationalbelow','zzd':'rationalmultiply'}
    assert all(ds[d['name']]==d for d in check.forwarder_definitions())


def test_original_paragraphs_formula_continuations_and_source_fragments():
    check.text_boundaries()
    assert check.HEADINGS=={}
    assert list(check.SENTENCES.values())==[[109,1],[109,2],[109,3],[109,4],[110,1],[111,1]]
    source=lambda n:check.SOURCE_UNITS[f'einstein-1905:u{n:04}']['text']
    for name,parts in check.SOURCE_FRAGMENTS.items():
        assert check.TEXT_SENTENCES[name]==' '.join(source(n)[a:b] for n,a,b in parts)
    for unit in range(252,261):
        ranges=sorted((a,b) for parts in check.SOURCE_FRAGMENTS.values() for n,a,b in parts if n==unit)
        assert ranges and ranges[0][0]==0 and ranges[-1][1]==len(source(unit))
        for (_,end),(start,_) in zip(ranges,ranges[1:]):assert end<=start and not source(unit)[end:start].strip()
    def span(name):
        first,start,last,end=check.SPANS[name];assert first==last
        return ' '.join(check.TOKENS[first][start-1:end])
    for old,unit in {'eisyq':253,'eisy4':255,'eisy5':257,'eisy6':258}.items():assert span(old)==source(unit)
    assert span('eisyp').startswith('Wir schreiben') and span('eisyz').startswith('und bemerken')
    assert check.TEXT_SENTENCES['eisy2'].startswith('(Diese Kraft') and check.TEXT_SENTENCES['eisy2'].endswith('werden.)')
    assert check.TEXT_SENTENCES['eisy3'].startswith('Wenn wir nun') and check.TEXT_SENTENCES['eisy3'].endswith(source(258))
    assert span('eiszl').endswith(';') and span('eiszm').startswith('man ersieht')
    assert span('eiszq').endswith(';') and span('eiszr').startswith('denn ein') and span('eiszs')=='(in unserem Sinne)'
    assert check.DESIGNATIONS=={'eisy7':['tenthunqualifiedforcephrase',1],'eisza':['eisy5',1],'eiszb':['eisy6',1]}


def test_structural_reference_lookups_reject_each_wrong_slot():
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

def test_actual_native_lookup_does_not_execute_quoted_physics():
    b=values();doc=deepcopy(check.restored()['document']);ds={d['name']:d for d in doc['declarations']}
    targets=tuple(check.HEADINGS)+tuple(check.SENTENCES)+tuple(check.SPANS)+tuple(check.DESIGNATIONS)+tuple(check.ROLE_ASSIGNMENTS)
    pending=[check.names()[n] for n in targets];needed=set()
    while pending:
        n=pending.pop()
        if n in needed:continue
        needed.add(n);pending.extend(_references(ds[n].get('body'))-needed)
    doc['declarations']=[d for d in doc['declarations'] if d['name'] in needed];doc['statements']=[]
    handlers={check.vocabulary()._symbols[n]:fn for n,fn in check.context_handlers(b).items()}
    for i,old in enumerate(targets):
        capture='tenthcapture'+chr(97+i//26)+chr(97+i%26);sort=check.REFERENCE_SORTS.get(old,'individual')
        doc['declarations'].append(dict(kind='primitive',name=capture,parameters=[sort],result='truth'))
        doc['statements'].append(dict(kind='ask',body=call(capture,call(check.names()[old]))))
        handlers[capture]=lambda x,old=old,sort=sort:fingerprint(x,sort)==fingerprint(b[old],sort)
    individuals=tuple({x for x in b.values() if isinstance(x,str)}|{'left','right','other'})
    result=evaluate_document(doc,individuals=individuals,situations=check.SITUATIONS,
        primitives={d['name']:handlers.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},
        memoize_definitions=True,memoize_expressions=True)
    assert len(result)==len(targets) and all(r['value'] is True for r in result)

def test_closed_roles_are_nonrecursive_and_reject_unknown_reference_keys():
    b=values();ds={d['name']:d for d in check.restored()['document']['declarations']}
    for old in check.ROLE_ASSIGNMENTS:
        sort=check.REFERENCE_SORTS[old];kind=check.reference_kind(old)
        description=DescriptionValue(check.canonical(dict(kind='function_ref',symbol=check.reference_roles()[old])),
            check.canonical(function_sort([sort,'situation'],'truth')))
        lookup=check.reference_model(b,kind)
        args=[b['eirf'],b[check.reference_anchor(old)],description,b['ri']]
        assert lookup.described(*args) is b[old]
        for slot in range(4):
            bad=args[:];bad[slot]=DescriptionValue(check.canonical(dict(kind='function_ref',symbol='unknown')),description.result_type) if slot==2 else 'unknown'
            with pytest.raises(ValueError):lookup.described(*bad)
        pending=[check.reference_roles()[old]];seen=set()
        while pending:
            name=pending.pop()
            if name in seen:continue
            seen.add(name);pending.extend(_references(ds[name].get('body'))-seen)
        assert check.names()[old] not in seen
