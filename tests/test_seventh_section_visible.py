"""Validate actual recovered structure before finite reference diagnostics."""
from copy import deepcopy
from fractions import Fraction as Q
import pytest
from noema.constructed_semantics import DescriptionValue,evaluate_document
from noema.meaning_catalog import _references
from scripts.shared_modality import call,renamed
from scripts import check_einstein_seventh_section_visible as check


def forbidden(*args):
    raise ValueError('Unexpected execution of quoted physical content or unknown reference')


def test_recovered_parent_and_all_source_bodies():
    doc=check.restored()['document'];parent=check.previous.document()
    assert check.backprojection(doc)==check.source_excerpt()
    assert len(doc['statements'])==252 and doc['statements'][:224]==parent['statements']
    ds={d['name']:d for d in doc['declarations']}
    assert all(ds[d['name']]==d for d in parent['declarations'])
    mapping=check.mapping()
    for d in check.source_excerpt()['declarations']:
        if d['kind']=='definition':assert ds[mapping[d['name']]]==renamed(d,mapping)
    assert len(check.NEW_DEFINITIONS)==278 and len(check.vocabulary()._words)==953
    bridge=check.bridge()
    assert bridge['source_statement_indices']==[220,*range(199,220)]
    assert len(bridge['source_reviews'])==24 and bridge['document_integration_credit']==0
    assert bridge['new_reference_primitives']==bridge['new_core_words']==0
    assert bridge['total_annotations']==46


def source_text(number):
    return check.SOURCE_UNITS[f'einstein-1905:u{number:04}']['text']


def test_text_reconstruction_keeps_equations_sentences_and_abbreviations():
    check.text_boundaries()
    text=check.TEXT_SENTENCES
    expected_groups=[
        (['seventhwaveassumption','eissc'],range(179,182)),
        (['eissf','seventhwavetransform'],range(182,188)),
        (['seventhdopplerconsequence','seventhdoppleridentification','seventhdopplerspecialization','eisst'],range(188,193)),
        (['seventhaberrationpresentation','seventhaberrationidentification','seventhaberrationspecialization'],range(193,197)),
        (['seventhamplitudequestion','seventhamplitudepresentation'],range(197,201)),
        (['eistg'],[201]),
    ]
    for names,units in expected_groups:
        assert ' '.join(text[n] for n in names)==' '.join(source_text(i) for i in units)
    assert text['seventhamplitudepresentation'].count('bez.')==2
    assert check.SENTENCES['eisst']==[83,4] and check.SENTENCES['eistg']==[86,1]
    assert check.TOKENS['seventhwavetransform'][0]=='—'


def span_text(name):
    first,start,last,end=check.SPANS[name];names=list(check.SENTENCES)
    a=names.index(first);b=names.index(last)
    if a==b:return ' '.join(check.TOKENS[first][start-1:end])
    return ' '.join(check.TOKENS[first][start-1:]+[t for n in names[a+1:b] for t in check.TOKENS[n]]+check.TOKENS[last][:end])


def test_each_clause_and_formula_span_matches_its_source_unit():
    whole={'eisry':179,'eisrz':180,'eissm':188,'eissn':189,'eissq':190,'eissr':191,
        'eissv':193,'eissw':194,'eissz':195,'eiss2':196,'eiss5':197,'eiss6':198,'eistc':199,'eistd':200}
    for name,unit in whole.items():assert span_text(name)==source_text(unit)
    assert span_text('eissh')==source_text(182).split(' — ')[1]
    assert span_text('eissi')==' '.join(source_text(i) for i in [183,184])
    assert span_text('eissj')==' '.join(source_text(i) for i in [185,186,187])
    assert span_text('seventhparametersanchor')=='[M0327]'
    assert span_text('eissu')=='im Gegensatz zu der üblichen Auffassung'


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
    # New spans must not replace the preceding paragraph's reference table.
    for name,(node,start,end) in check.previous.SPANS.items():
        assert handlers['sentencetokenspanreference'](b['eirf'],b[node],Q(start),b[node],Q(end),b['ri'])==b[name]


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
        capture='seventhcapture'+chr(97+i//26)+chr(97+i%26)
        doc['declarations'].append(dict(kind='primitive',name=capture,parameters=['individual'],result='truth'))
        doc['statements'].append(dict(kind='ask',body=call(capture,call(check.names()[old]))))
        handlers[capture]=lambda x,old=old:x==b[old]
    results=evaluate_document(doc,individuals=tuple(set(b.values())|{'other'}),situations=check.SITUATIONS,
        primitives={d['name']:handlers.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},
        memoize_definitions=True,memoize_expressions=True)
    assert len(results)==len(targets) and all(r['value'] is True for r in results)


def test_shared_formula_anchor_keeps_phase_rate_and_axial_item_distinct():
    from scripts.temporal_discourse_profile import ROLE
    b=dict(check.BASE);model=check.reference_model(b)
    assert check.REFERENCE_ANCHORS['eisso']==check.REFERENCE_ANCHORS['eissy']
    found=[]
    for old in ('eisso','eissy','eisrx'):
        desc=DescriptionValue(check.canonical(dict(kind='function_ref',symbol=check.reference_roles()[old])),check.canonical(ROLE))
        args=[b['eirf'],b[check.reference_anchor(old)],desc,b['ri']]
        found.append(model.described(*args));assert found[-1]==b[old]
        for slot in (0,1,3):
            bad=args[:];bad[slot]='unknown'
            with pytest.raises(ValueError):model.described(*bad)
        bad=args[:];bad[2]=DescriptionValue(check.canonical(dict(kind='function_ref',symbol='unknown')),check.canonical(ROLE))
        with pytest.raises(ValueError):model.described(*bad)
    assert len(set(found))==3
