"""Check actual ninth-section bodies, source boundaries and local references."""
from copy import deepcopy
from fractions import Fraction as Q
import pytest
from noema.constructed_semantics import DescriptionValue, evaluate_document
from noema.meaning_catalog import _references
from scripts.shared_modality import call, renamed
from scripts import check_einstein_ninth_section_visible as check

def forbidden(*args):
    raise ValueError('Unexpected execution of quoted physical content or unknown reference')

def test_recovered_parent_and_all_source_bodies():
    doc = check.restored()['document']
    parent = check.previous.document()
    assert check.backprojection(doc) == check.source_excerpt()
    assert len(doc['statements']) == 304 and doc['statements'][:295] == parent['statements']
    ds = {d['name']: d for d in doc['declarations']}
    assert all((ds[d['name']] == d for d in parent['declarations']))
    mapping = check.mapping()
    for d in check.source_excerpt()['declarations']:
        if d['kind'] == 'definition':
            assert ds[mapping[d['name']]] == renamed(d, mapping)
    assert len(check.NEW_DEFINITIONS) == 145 and len(check.vocabulary()._words) == 990
    bridge = check.bridge()
    assert bridge['source_statement_indices'] == [245, 244, 246, 247, 248]
    assert len(bridge['source_reviews']) == 12 and bridge['document_integration_credit'] == 0
    assert bridge['new_reference_primitives'] == bridge['new_core_words'] == 0
    assert bridge['total_annotations'] == 70

def source_text(number):
    return check.SOURCE_UNITS[f'einstein-1905:u{number:04}']['text']

def span_text(name):
    first, start, last, end = check.SPANS[name]
    names = list(check.SENTENCES)
    a = names.index(first)
    b = names.index(last)
    if a == b:
        return ' '.join(check.TOKENS[first][start - 1:end])
    return ' '.join(check.TOKENS[first][start - 1:] + [t for n in names[a + 1:b] for t in check.TOKENS[n]] + check.TOKENS[last][:end])

def test_structural_reference_lookups_reject_unknown_positions():
    b = dict(check.BASE)
    handlers = check.context_handlers(b)
    for name, (first, start, last, end) in check.SPANS.items():
        args = [b['eirf'], b[first], Q(start), b[last], Q(end), b['ri']]
        assert handlers['sentencetokenspanreference'](*args) == b[name]
        for slot in range(6):
            bad = args[:]
            bad[slot] = Q(999) if slot in (2, 4) else 'unknown'
            with pytest.raises(ValueError):
                handlers['sentencetokenspanreference'](*bad)
    for name, (paragraph, sentence) in check.SENTENCES.items():
        assert handlers['sentencereference'](b['ri'], Q(paragraph), Q(sentence)) == b[name]
    for name, (node, index) in check.DESIGNATIONS.items():
        args = [b['eirf'], b[node], Q(index), b['ri']]
        assert handlers['designationreference'](*args) == b[name]
        for slot in range(4):
            bad = args[:]
            bad[slot] = Q(999) if slot == 2 else 'unknown'
            with pytest.raises(ValueError):
                handlers['designationreference'](*bad)
    for name, (first, start, last, end) in check.previous.SPANS.items():
        assert handlers['sentencetokenspanreference'](b['eirf'], b[first], Q(start), b[last], Q(end), b['ri']) == b[name]

def test_actual_native_references_do_not_execute_their_quoted_roles():
    b = dict(check.BASE)
    doc = deepcopy(check.restored()['document'])
    ds = {d['name']: d for d in doc['declarations']}
    targets = tuple(check.HEADINGS) + tuple(check.SENTENCES) + tuple(check.SPANS) + tuple(check.DESIGNATIONS) + tuple(check.ROLE_ASSIGNMENTS)
    needed = set()
    pending = [check.names()[n] for n in targets]
    while pending:
        n = pending.pop()
        if n in needed:
            continue
        needed.add(n)
        pending.extend(_references(ds[n].get('body')) - needed)
    doc['declarations'] = [d for d in doc['declarations'] if d['name'] in needed]
    doc['statements'] = []
    handlers = {check.vocabulary()._symbols[n]: fn for n, fn in check.context_handlers(b).items()}
    for i, old in enumerate(targets):
        capture = 'ninthcapture' + chr(97 + i // 26) + chr(97 + i % 26)
        doc['declarations'].append(dict(kind='primitive', name=capture, parameters=['individual'], result='truth'))
        doc['statements'].append(dict(kind='ask', body=call(capture, call(check.names()[old]))))
        handlers[capture] = lambda x, old=old: x == b[old]
    results = evaluate_document(doc, individuals=tuple(set(b.values()) | {'other'}), situations=check.SITUATIONS, primitives={d['name']: handlers.get(d['name'], forbidden) for d in doc['declarations'] if d['kind'] == 'primitive'}, memoize_definitions=True, memoize_expressions=True)
    assert len(results) == len(targets) and all((r['value'] is True for r in results))


def test_source_sentences_and_paragraphs_preserve_all_fragments():
    check.text_boundaries()
    assert check.HEADINGS=={'eiswl':11}
    assert list(check.SENTENCES.values())==[[99,1],[99,2],[100,1],[101,1],[102,1]]
    for name,parts in check.SOURCE_FRAGMENTS.items():
        assert check.TEXT_SENTENCES[name]==' '.join(source_text(unit)[a:b] for unit,a,b in parts)
    for unit in range(228,239):
        text=source_text(unit)
        ranges=sorted((a,b) for parts in check.SOURCE_FRAGMENTS.values() for u,a,b in parts if u==unit)
        assert ranges and ranges[0][0]==0 and ranges[-1][1]==len(text)
        for (_,end),(start,_) in zip(ranges,ranges[1:]):
            assert end<=start and not text[end:start].strip()
    assert check.TEXT_SENTENCES['ninthconstancysentence']==source_text(238)
    assert 'kann: Bewegt sich' in source_text(238)
    assert check.TEXT_SENTENCES['eiswk']==source_text(232)[source_text(232).index('Denkt man'):]


def test_clause_formula_quantity_and_theory_anchors():
    for name,unit in {'eiswf':228,'eiswg':229,'eiswh':230,'eiswi':231,'eiswn':233,'zqa':234,'eiswo':235,'zqb':236}.items():
        assert span_text(name)==source_text(unit)
    first=source_text(232).split(' Denkt man',1)[0]
    assert span_text('eiswj')==first
    assert span_text('ninthquantitydefinitions')==source_text(231)+' '+first
    split=source_text(238).index('Bewegt sich')
    assert span_text('eiswu')==source_text(238)[:split].strip()
    assert span_text('eiswv')==source_text(238)[split:]
    assert span_text('ninthlorentztheoryanchor')=='der Lorentzschen Elektrodynamik und Optik bewegter Körper.'
    assert check.DESIGNATIONS=={'eisv3':['eiswk',1],'eisv4':['eiswk',2],
        'eiswb':['ninthquantitydefinitions',1],'eiswc':['ninthquantitydefinitions',2]}
    assert check.FORMS=={'eisv3':'Ionen','eisv4':'Elektronen','eiswb':'ϱ','eiswc':'(u_x,u_y,u_z)'}
    assert check.REFERENCE_ANCHORS=={'eisv5':'ninthlorentztheoryanchor','eisv6':'eiswl'}


def test_described_theory_and_section_roles_reject_crossed_references():
    from scripts.temporal_discourse_profile import ROLE
    b=dict(check.BASE);model=check.reference_model(b);found=[]
    descriptions={old:DescriptionValue(check.canonical(dict(kind='function_ref',symbol=check.reference_roles()[old])),
        check.canonical(ROLE)) for old in check.ROLE_ASSIGNMENTS}
    for old in check.ROLE_ASSIGNMENTS:
        args=[b['eirf'],b[check.reference_anchor(old)],descriptions[old],b['ri']]
        found.append(model.described(*args));assert found[-1]==b[old]
        for slot in (0,1,3):
            bad=args[:];bad[slot]='unknown'
            with pytest.raises(ValueError):model.described(*bad)
        other=next(n for n in descriptions if n!=old)
        bad=args[:];bad[2]=descriptions[other]
        with pytest.raises(ValueError):model.described(*bad)
        bad=args[:];bad[2]=DescriptionValue(check.canonical(dict(kind='function_ref',symbol='unknown')),check.canonical(ROLE))
        with pytest.raises(ValueError):model.described(*bad)
    assert len(set(found))==2
