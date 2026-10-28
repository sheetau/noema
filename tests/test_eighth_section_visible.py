"""Check recovered source structure and distinct local references."""
from copy import deepcopy
from fractions import Fraction as Q
import pytest
from noema.constructed_semantics import DescriptionValue,evaluate_document
from noema.meaning_catalog import _references
from scripts.shared_modality import call,renamed
from scripts import check_einstein_eighth_section_visible as check


def forbidden(*args):
    raise ValueError('Unexpected execution of quoted physical content or unknown reference')


def test_recovered_parent_and_all_source_bodies():
    doc=check.restored()['document'];parent=check.previous.document()
    assert check.backprojection(doc)==check.source_excerpt()
    assert len(doc['statements'])==295 and doc['statements'][:252]==parent['statements']
    ds={d['name']:d for d in doc['declarations']}
    assert all(ds[d['name']]==d for d in parent['declarations'])
    mapping=check.mapping()
    for d in check.source_excerpt()['declarations']:
        if d['kind']=='definition':assert ds[mapping[d['name']]]==renamed(d,mapping)
    assert len(check.NEW_DEFINITIONS)==376 and len(check.vocabulary()._words)==975
    bridge=check.bridge()
    assert bridge['source_statement_indices']==[243,*range(221,243)]
    assert len(bridge['source_reviews'])==25 and bridge['document_integration_credit']==0
    assert bridge['new_reference_primitives']==bridge['new_core_words']==0
    assert bridge['total_annotations']==66


def source_text(number):return check.SOURCE_UNITS[f'einstein-1905:u{number:04}']['text']


def test_source_sentences_preserve_all_fragments_and_original_naming():
    check.text_boundaries()
    for name,parts in check.SOURCE_FRAGMENTS.items():
        assert check.TEXT_SENTENCES[name]==' '.join(source_text(unit)[a:b] for unit,a,b in parts)
    for unit in range(203,227):
        text=source_text(unit)
        ranges=sorted((a,b) for pieces in check.SOURCE_FRAGMENTS.values() for u,a,b in pieces if u==unit)
        assert ranges[0][0]==0 and ranges[-1][1]==len(text)
        for (_,end),(start,_) in zip(ranges,ranges[1:]):
            assert end<=start and not text[end:start].strip()
    original=source_text(4)
    assert check.TEXT_SENTENCES['eighthoriginalprinciplename']==original[original.index('Wir wollen diese Vermutung'):original.index(' Diese beiden Voraussetzungen')]
    assert check.SENTENCES['eighthoriginalprinciplename']==[2,2]
    assert check.DESIGNATIONS['eiscg']==['eighthoriginalprinciplename',1]
    assert check.FORMS['eiscg']=='Prinzip der Relativität' and check.FORMS['ekll']=='Relativitätsprinzip'
    assert 'd. h.' in check.TEXT_SENTENCES['eistt']
    assert check.SENTENCES['eisvs']==[98,1] and check.SENTENCES['eisvu']==[98,3]


def span_text(name):
    first,start,last,end=check.SPANS[name];names=list(check.SENTENCES)
    a=names.index(first);b=names.index(last)
    if a==b:return ' '.join(check.TOKENS[first][start-1:end])
    return ' '.join(check.TOKENS[first][start-1:]+[t for n in names[a+1:b] for t in check.TOKENS[n]]+check.TOKENS[last][:end])


def test_clause_formula_and_local_quantity_anchors():
    whole={'eistu':206,'eistv':207,'eistw':208,'eistx':209,'eist2':210,'eist3':211,
        'eist4':212,'eist5':213,'eisui':217,'eisuj':218,'eisuk':219,'eisuu':220,
        'eisuv':221,'eisu7':223,'eisvg':224,'eisvh':225}
    for name,unit in whole.items():assert span_text(name)==source_text(unit)
    assert span_text('eistp')==' '.join([source_text(203)[422:],source_text(204),source_text(205)[:23]])
    assert span_text('eistq')==source_text(205)[23:107].strip()
    assert span_text('eisuh')==source_text(216)
    assert span_text('eisu6')==source_text(222)[source_text(222).index('Setzt man '):]
    for names,node in [(('eisul','eisuo','eisur'),'eighthincidentdesignation'),
        (('eisum','eisup','eisus'),'eisui'),(('eisun','eisuq','eisut'),'eisuk'),
        (('eisuw','eisux','eisuy'),'eisuv')]:
        assert [check.DESIGNATIONS[n] for n in names]==[[node,1],[node,2],[node,3]]


def test_structural_reference_lookups_reject_unknown_positions():
    b=dict(check.BASE);handlers=check.context_handlers(b)
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


def test_actual_native_references_do_not_execute_their_quoted_roles():
    b=dict(check.BASE);doc=deepcopy(check.restored()['document']);ds={d['name']:d for d in doc['declarations']}
    targets=tuple(check.HEADINGS)+tuple(check.SENTENCES)+tuple(check.SPANS)+tuple(check.DESIGNATIONS)+tuple(check.ROLE_ASSIGNMENTS)
    needed=set();pending=[check.names()[n] for n in targets]
    while pending:
        n=pending.pop()
        if n in needed:continue
        needed.add(n);pending.extend(_references(ds[n].get('body'))-needed)
    doc['declarations']=[d for d in doc['declarations'] if d['name'] in needed];doc['statements']=[]
    handlers={check.vocabulary()._symbols[n]:fn for n,fn in check.context_handlers(b).items()}
    for i,old in enumerate(targets):
        capture='eighthcapture'+chr(97+i//26)+chr(97+i%26)
        doc['declarations'].append(dict(kind='primitive',name=capture,parameters=['individual'],result='truth'))
        doc['statements'].append(dict(kind='ask',body=call(capture,call(check.names()[old]))))
        handlers[capture]=lambda x,old=old:x==b[old]
    results=evaluate_document(doc,individuals=tuple(set(b.values())|{'other'}),situations=check.SITUATIONS,
        primitives={d['name']:handlers.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},
        memoize_definitions=True,memoize_expressions=True)
    assert len(results)==len(targets) and all(r['value'] is True for r in results)


def test_shared_approximation_anchor_distinguishes_source_and_parameter():
    from scripts.temporal_discourse_profile import ROLE
    b=dict(check.BASE);model=check.reference_model(b)
    assert check.REFERENCE_ANCHORS['eisve']==check.REFERENCE_ANCHORS['eisvf']
    found=[]
    for old in check.ROLE_ASSIGNMENTS:
        desc=DescriptionValue(check.canonical(dict(kind='function_ref',symbol=check.reference_roles()[old])),check.canonical(ROLE))
        args=[b['eirf'],b[check.reference_anchor(old)],desc,b['ri']]
        found.append(model.described(*args));assert found[-1]==b[old]
        for slot in (0,1,3):
            bad=args[:];bad[slot]='unknown'
            with pytest.raises(ValueError):model.described(*bad)
        bad=args[:];bad[2]=DescriptionValue(check.canonical(dict(kind='function_ref',symbol='unknown')),check.canonical(ROLE))
        with pytest.raises(ValueError):model.described(*bad)
    assert len(set(found))==5
