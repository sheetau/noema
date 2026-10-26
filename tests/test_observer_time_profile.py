from copy import deepcopy
from fractions import Fraction
import pytest
from noema.constructed_semantics import FunctionValue,evaluate_document
from scripts import check_einstein_observer_time as check
from scripts import observer_time_profile as profile
from scripts.temporal_discourse_profile import TemporalDiscourseVocabulary
from scripts.visible_vectors_vocabulary import VectorsVocabulary
from scripts.visible_collection import decode_collection
from scripts.visible_syntax_geometry import from_svg
from scripts.shared_modality import call,op


def forbidden(*args):raise AssertionError('Unrelated or quoted content executed')
def handlers(doc):return {d['name']:forbidden for d in doc['declarations'] if d['kind']=='primitive'}


def test_profile_preserves_previous_words_and_avoids_math_collisions():
    old=TemporalDiscourseVocabulary();new=check.vocabulary()
    assert len(old._words)==462 and len(new._words)==515
    for field in ('entries','compounds','definitions','primitives'):
        assert all(new.document()[field][n]==d for n,d in old.document()[field].items())
    assert not ({new._symbols[n] for n in profile.PARAMETERS}&set(VectorsVocabulary()._by_symbol))


def test_full_visible_document_and_backprojection_preserve_prior_evidence():
    doc=check.restored()['document'];assert doc==check.document()
    assert len(doc['declarations'])==377 and len(doc['statements'])==16
    old=check.previous.document();ds={d['name']:d for d in doc['declarations']}
    assert all(ds[d['name']]==d for d in old['declarations']) and doc['statements'][:11]==old['statements']
    assert check.backprojection(doc)==check.source_excerpt()
    assert len(check.source_excerpt()['declarations'])==182


def test_source_ranges_and_forward_anchors_do_not_assert_following_content():
    b=check.bridge();p,q=b['source_units']
    assert p['ranges']==[[0,200],[201,639]] and q['ranges']==[[0,309],[310,488],[489,569]]
    assert b['sentence_positions']['eish2']==[9,1] and b['sentence_positions']['rj']==[13,2]
    assert check.author.read(check.BRIDGE)==b
    assert b['forward_reference']==dict(begin='einstein-1905:u0013',end='einstein-1905:u0018',end_sentence=2,following_contents_asserted=False)


def test_context_roles_and_discourse_relations_preserve_their_exact_scope():
    rows=check.diagnostics();assert len(rows)==23 and rows[0]['values']==[True]*5
    assert all(not all(r['values']) for r in rows[1:])


def test_sixteen_role_references_and_common_clock_bind_without_executing_roles():
    doc=deepcopy(check.restored()['document']);n=check.names()
    doc['declarations'].append(dict(kind='primitive',name='expected',parameters=[],result='individual'))
    h=handlers(doc);h.update({check.vocabulary()._symbols[k]:f for k,f in check.context_handlers(check.BASE).items()})
    domain=tuple(set(check.BASE.values())|set(check.REFERENTS)|{'rc','other','setting','frame'})
    for old in (*check.REFERENTS,'rc'):
        doc['statements']=[dict(kind='ask',body=op('equal',call(n[old]),call('expected')))]
        h['expected']=lambda old=old:old
        assert evaluate_document(doc,individuals=domain,situations=('front','body'),primitives=h)[0]['value']
        h['expected']=lambda:'other'
        assert not evaluate_document(doc,individuals=domain,situations=('front','body'),primitives=h)[0]['value']


def test_same_unit_role_at_three_text_locations_does_not_merge_references():
    roles=check.reference_roles();assert roles['eisgb']==roles['eishf']==roles['rb']
    assert [check.reference_node(n) for n in ('eisgb','eishf','rb')]==['eisgc','eishg','rj']
    model=check.role_model(check.BASE);assert len(model)==16
    assert len(set(model.values()))==16


@pytest.mark.parametrize('field',[0,1,2,3])
def test_unknown_document_node_role_or_context_does_not_supply_a_reference(field):
    doc=deepcopy(check.document());n=check.names();roles=check.role_model(check.BASE)
    key=next(iter(roles));value=roles.pop(key);bad=list(key);bad[field]='wrong';roles[tuple(bad)]=value
    doc['statements']=[dict(kind='ask',body=op('equal',call(n['eisf5']),call(n['eisf5'])))]
    h=handlers(doc);h.update({check.vocabulary()._symbols[k]:f for k,f in check.context_handlers(check.BASE,roles).items()})
    with pytest.raises(ValueError,match='Unknown temporal reference'):
        evaluate_document(doc,individuals=tuple(set(check.BASE.values())|{'other'}),situations=('front','body'),primitives=h)


def test_all_reception_and_case_slots_through_native_with_one_changed_slot():
    # Small-domain binding diagnostics, not a proof of physical record validity.
    doc=deepcopy(check.restored()['document']);m=check.mapping()
    doc['declarations'] += [dict(kind='primitive',name=n,parameters=[],result=t) for n,t in [('record','individual'),('expected','individual'),('context','situation')]]
    h=handlers(doc);h.update(record=lambda:'x',expected=lambda:'y',context=lambda:'reference')
    for name,size in [('eisgx',5),('eishi',7)]:
        for changed in (None,*range(size)):
            row=['x']*size
            if changed is not None:row[changed]='y'
            model=profile.ReceptionRecords({('x','reference'):row} if size==5 else {},{}, {('x','reference'):row} if size==7 else {},{})
            h.update({check.vocabulary()._symbols[k]:f for k,f in model.handlers().items()})
            doc['statements']=[dict(kind='ask',body=op('equal',call(m[name],call('record'),check.author.num(i+1),call('context')),call('expected'))) for i in range(size)]
            answers=evaluate_document(doc,individuals=('x','y'),situations=('reference','case'),primitives=h)
            assert [r['value'] for r in answers]==[i==changed for i in range(size)]


def test_reading_and_case_context_preserve_all_key_slots_and_native_types():
    f=FunctionValue(('number',),'truth',lambda q:q<7)
    model=profile.ReceptionRecords({}, {('r','c','u','reference'):f},{},{('case','reference'):'evaluation'})
    h=model.handlers();assert h['receptionreading']('r','c','u','reference') is f
    for i in range(4):
        args=['r','c','u','reference'];args[i]='other'
        with pytest.raises(ValueError):h['receptionreading'](*args)
    assert h['casecontext']('case','reference')=='evaluation'
    for args in [('other','reference'),('case','evaluation')]:
        with pytest.raises(ValueError):h['casecontext'](*args)
    doc=deepcopy(check.restored()['document']);m=check.mapping()
    for n,t in [('r','individual'),('c','individual'),('u','individual'),('case','individual'),('reference','situation'),('evaluation','situation')]:
        doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=t))
    hs=handlers(doc)|{check.vocabulary()._symbols[k]:v for k,v in h.items()}
    hs.update({n:(lambda n=n:n) for n in ('r','c','u','case','reference','evaluation')})
    doc['statements']=[dict(kind='ask',body=dict(kind='apply',function=call(m['eisgz'],call('r'),call('c'),call('u'),call('reference')),arguments=[check.author.num(q)])) for q in (6,7)]
    doc['statements'].append(dict(kind='ask',body=op('equal',call(m['eishj'],call('case'),call('reference')),call('evaluation'))))
    assert [r['value'] for r in evaluate_document(doc,individuals=('r','c','u','case'),situations=('reference','evaluation'),primitives=hs)]==[True,False,True]


@pytest.mark.parametrize('slot',[0,-1,8,True,1.0,Fraction(1,2)])
def test_invalid_slot_rejected(slot):
    model=profile.ReceptionRecords({('r','s'):['x']*5},{},{('r','s'):['x']*7},{})
    for function in ('receptioncomponent','casecomponent'):
        with pytest.raises(ValueError):model.handlers()[function]('r',slot,'s')


def test_records_reject_unknown_keys_wrong_sizes_and_non_cut_readings():
    model=profile.ReceptionRecords({('r','s'):['x']*5},{},{('r','s'):['x']*7},{})
    for function in ('receptioncomponent','casecomponent'):
        for record,ctx in [('unknown','s'),('r','other')]:
            with pytest.raises(ValueError):model.handlers()[function](record,1,ctx)
    with pytest.raises(ValueError):model.handlers()['receptioncomponent']('r',6,'s')
    for receptions,readings,cases in [({('r','s'):['x']*4},{},{}),({}, {},{('r','s'):['x']*6}),({}, {('r','c','u','s'):False},{})]:
        with pytest.raises(ValueError):profile.ReceptionRecords(receptions,readings,cases,{})


def test_changed_proposal_roles_forward_anchor_or_modality_cannot_reuse_evidence():
    for old in ('roleproposal','roleconsideration','rj','eijo','eikh'):
        doc=deepcopy(check.document());ds={d['name']:d for d in doc['declarations']}
        ds[check.names()[old]]['body']=dict(kind='truth',value=True)
        with pytest.raises(ValueError,match='Changed migration'):check.backprojection(doc)


def test_previous_profile_cannot_decode_new_header():
    pages=[from_svg(p.read_text(encoding='utf-8')) for p in sorted(check.OUT.glob('*.svg'))]
    with pytest.raises(ValueError):decode_collection(pages,TemporalDiscourseVocabulary())
