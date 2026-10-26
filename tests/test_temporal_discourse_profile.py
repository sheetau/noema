from copy import deepcopy
from fractions import Fraction
import pytest

from noema.constructed_semantics import FunctionValue,evaluate_document
from scripts import check_einstein_temporal_discourse as check
from scripts import temporal_discourse_profile as profile
from scripts.physical_position_profile import PhysicalPositionVocabulary
from scripts.visible_vectors_vocabulary import VectorsVocabulary
from scripts.visible_collection import decode_collection
from scripts.visible_syntax_geometry import from_svg
from scripts.shared_modality import call,op


def forbidden(*args):raise AssertionError('Unrelated or quoted content executed')


def handlers(doc):return {d['name']:forbidden for d in doc['declarations'] if d['kind']=='primitive'}


def test_profile_preserves_previous_meanings_and_distinct_math_words():
    old=PhysicalPositionVocabulary();new=check.vocabulary()
    assert len(old._words)==409 and len(new._words)==462
    for field in ('entries','compounds','definitions','primitives'):
        assert all(new.document()[field][n]==d for n,d in old.document()[field].items())
    assert not ({new._symbols[n] for n in profile.PARAMETERS}&set(VectorsVocabulary()._by_symbol))


def test_visible_document_preserves_previous_selection_and_source_bodies():
    doc=check.restored()['document'];assert doc==check.document()
    assert len(doc['declarations'])==235 and len(doc['statements'])==11
    old=check.previous.document();ds={d['name']:d for d in doc['declarations']}
    assert doc['statements'][:6]==old['statements']
    assert all(ds[d['name']]==d for d in old['declarations'])
    assert check.backprojection(doc)==check.source_excerpt()
    assert len(check.source_excerpt()['declarations'])==148


def test_paragraph_and_attached_note_keep_their_distinct_source_locations():
    b=check.bridge();p,n=b['source_units']
    assert p['unit']=='einstein-1905:u0010' and p['ranges']==[[0,126],[127,337],[338,481],[482,666]]
    assert n['unit']=='einstein-1905:u0279' and n['ranges']==[[0,len(n['text'])]]
    ds={d['name']:d for d in check.document()['declarations']};names=check.names()
    body=ds[names['eisfn']]['body']
    assert body['symbol']==check.vocabulary()._symbols['footnotereference']
    assert body['arguments'][1]==call(names['eisfm']) and body['arguments'][2]==check.author.num(1)


def test_attribution_preserves_all_context_slots_and_relation_scopes():
    rows=check.diagnostics();assert len(rows)==15
    assert rows[0]['values']==[True]*5
    assert all(not all(r['values']) for r in rows[1:])


def role_model():
    roles={(check.BASE['eirf'],check.BASE['eisfn' if old=='eisfv' else 'eisfm'],
        check.canonical(dict(kind='function_ref',symbol=role)),check.BASE['ri']):old for old,role in check.reference_roles().items()}
    return roles


def test_all_eight_described_references_bind_without_executing_roles():
    doc=deepcopy(check.restored()['document']);names=check.names()
    doc['declarations'].append(dict(kind='primitive',name='expected',parameters=[],result='individual'))
    h=handlers(doc);h.update({check.vocabulary()._symbols[n]:f for n,f in check.context_handlers(check.BASE,role_model()).items()})
    for old in check.REFERENTS:
        doc['statements']=[dict(kind='ask',body=op('equal',call(names[old]),call('expected')))]
        h['expected']=lambda old=old:old
        assert evaluate_document(doc,individuals=(*check.DOMAIN,*check.REFERENTS),situations=('front','body'),primitives=h)[0]['value']
        h['expected']=lambda:'other'
        assert not evaluate_document(doc,individuals=(*check.DOMAIN,*check.REFERENTS),situations=('front','body'),primitives=h)[0]['value']


@pytest.mark.parametrize('change',['node','context','role'])
def test_role_references_reject_unregistered_node_context_or_description(change):
    doc=deepcopy(check.document());names=check.names();roles=role_model()
    key=next(iter(roles));value=roles.pop(key);bad=list(key)
    bad[{'node':1,'context':3,'role':2}[change]]='wrong';roles[tuple(bad)]=value
    doc['statements']=[dict(kind='ask',body=op('equal',call(names['eisff']),call(names['eisff'])))]
    h=handlers(doc);h.update({check.vocabulary()._symbols[n]:f for n,f in check.context_handlers(check.BASE,roles).items()})
    with pytest.raises(ValueError,match='Unknown temporal reference'):
        evaluate_document(doc,individuals=(*check.DOMAIN,*check.REFERENTS),situations=('front','body'),primitives=h)


def test_footnote_reference_does_not_merge_reused_numbers_or_unknown_contexts():
    refs=profile.TemporalReferences({}, {('doc','s4',1,'body'):'note',('doc','s8',1,'body'):'other'})
    assert refs.footnote('doc','s4',Fraction(1),'body')=='note'
    assert refs.footnote('doc','s8',1,'body')=='other'
    for args in [('doc','s4',1,'front'),('other','s4',1,'body'),('doc','s4',2,'body')]:
        with pytest.raises(ValueError):refs.footnote(*args)
    for number in (0,-1,True,1.0,Fraction(1,2)):
        with pytest.raises(ValueError):refs.footnote('doc','s4',number,'body')


def test_each_trial_entity_and_reading_slot_through_native_forwarding_definitions():
    # Binding diagnostics: vary one slot on a small distinguishing domain.
    # Constant predicates here are deliberately not claimed to be real cuts.
    doc=deepcopy(check.restored()['document']);m=check.mapping();voc=check.vocabulary()
    doc['declarations'] += [dict(kind='primitive',name=n,parameters=[],result='individual') for n in ('trial','expected')]
    h=handlers(doc);h['trial']=lambda:'x';h['expected']=lambda:'y'
    for changed in (None,*range(6)):
        entities=['x']*6
        if changed is not None:entities[changed]='y'
        records=profile.LightTrialRecords({'x':entities},{})
        h.update({voc._symbols[n]:f for n,f in records.handlers().items()})
        doc['statements']=[dict(kind='ask',body=op('equal',call(m[old],call('trial')),call('expected'))) for old in check.FIELDS[:6]]
        answers=evaluate_document(doc,individuals=('x','y'),situations=('now',),primitives=h)
        assert [r['value'] for r in answers]==[i==changed for i in range(6)]
    for changed in (None,*range(3)):
        readings=[FunctionValue(('number',),'truth',lambda q,i=i:i==changed) for i in range(3)]
        records=profile.LightTrialRecords({}, {'x':readings})
        h.update({voc._symbols[n]:f for n,f in records.handlers().items()})
        doc['statements']=[dict(kind='ask',body=dict(kind='apply',function=call(m[old],call('trial')),arguments=[check.author.num(0)])) for old in check.FIELDS[6:]]
        answers=evaluate_document(doc,individuals=('x','y'),situations=('now',),primitives=h)
        assert [r['value'] for r in answers]==[i==changed for i in range(3)]
    doc['statements']=[dict(kind='ask',body=op('equal',check.quote_function(m['qc']),check.quote_function(m['qd'])))]
    assert not evaluate_document(doc,individuals=('x','y'),situations=('now',),primitives=h)[0]['value']


@pytest.mark.parametrize('slot',[-1,6,True,0.0,Fraction(1,2)])
def test_invalid_entity_slot_rejected(slot):
    with pytest.raises(ValueError):profile.LightTrialRecords({'trial':['x']*6},{}).handlers()['roundtripentity']('trial',slot)


def test_unknown_trials_and_invalid_reading_records_rejected():
    f=FunctionValue(('number',),'truth',lambda q:False)
    model=profile.LightTrialRecords({'trial':['x']*6},{'trial':[f]*3}).handlers()
    for name in model:
        with pytest.raises(ValueError):model[name]('unknown',0)
    for slot in (-1,3,True,0.0,Fraction(1,2)):
        with pytest.raises(ValueError):model['roundtripreading']('trial',slot)
    for entities,readings in [({'trial':['x']*5},{}),({}, {'trial':[f]*2}),({}, {'trial':[False]*3})]:
        with pytest.raises(ValueError):profile.LightTrialRecords(entities,readings)


def test_changed_role_attachment_or_message_cannot_reuse_old_evidence():
    for old in ('rolearrival','eisfn','eijb'):
        doc=deepcopy(check.document());ds={d['name']:d for d in doc['declarations']}
        ds[check.names()[old]]['body']=dict(kind='truth',value=True)
        with pytest.raises(ValueError,match='Changed migration'):check.backprojection(doc)


def test_old_profile_cannot_decode_new_header():
    pages=[from_svg(p.read_text(encoding='utf-8')) for p in sorted(check.OUT.glob('*.svg'))]
    with pytest.raises(ValueError):decode_collection(pages,PhysicalPositionVocabulary())
