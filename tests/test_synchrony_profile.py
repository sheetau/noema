from copy import deepcopy
from fractions import Fraction
import pytest
from noema.constructed_semantics import FunctionValue,evaluate_document
from scripts import check_einstein_synchrony as check
from scripts import synchrony_profile as profile
from scripts.observer_time_profile import ObserverTimeVocabulary
from scripts.temporal_discourse_profile import LightTrialRecords
from scripts.visible_vectors_vocabulary import VectorsVocabulary
from scripts.shared_modality import call,op


def forbidden(*args):raise AssertionError('Unrelated or quoted content executed')
def handlers(doc):return {d['name']:forbidden for d in doc['declarations'] if d['kind']=='primitive'}
def cut(n):return FunctionValue(('number',),'truth',lambda q:q<n)


def test_profile_preserves_existing_words_and_reuses_assumption_contract():
    old=ObserverTimeVocabulary();new=check.vocabulary()
    assert len(old._words)==515 and len(new._words)==563
    for field in ('entries','compounds','definitions','primitives'):
        assert all(new.document()[field][n]==d for n,d in old.document()[field].items())
    assert profile.REUSED=={'adoptsassumption'}
    assert not ({new._symbols[n] for n in profile.PARAMETERS}&set(VectorsVocabulary()._by_symbol))


def test_visible_document_and_exact_backprojection_preserve_source_and_prior():
    doc=check.restored()['document'];assert doc==check.document()
    old=check.previous.document();ds={d['name']:d for d in doc['declarations']}
    assert all(ds[d['name']]==d for d in old['declarations']) and doc['statements'][:16]==old['statements']
    assert len(doc['statements'])==29
    assert len(check.source_excerpt()['declarations'])==251
    assert check.backprojection(doc)==check.source_excerpt()


def test_text_equation_attachment_list_numbering_and_forward_anchor_identity():
    b=check.bridge();assert check.author.read(check.BRIDGE)==b
    assert len(b['source_units'])==6 and len(b['source_statement_indices'])==11
    assert b['equation_attachment']==dict(node='eisjs',body=[1292,1347],equation_unit='einstein-1905:u0014',math='M0030',one_sentence=True)
    assert b['numbered_items']==dict(eiskd=1,eiske=2)
    for n in ('eish2','rj'):assert check.names()[n]==check.previous.names()[n]
    assert b['stages']==dict(eisiy='eisio',eisjg='eisjh')


def test_outer_attribution_keeps_every_context_and_discourse_relation():
    rows=check.diagnostics();assert len(rows)==36 and rows[0]['values']==[True]*11
    assert all(not all(r['values']) for r in rows[1:])


def test_described_roles_designations_and_stages_bind_without_executing_quotes():
    doc=deepcopy(check.restored()['document']);n=check.names()
    doc['declarations'].append(dict(kind='primitive',name='expected',parameters=[],result='individual'))
    h=handlers(doc);h.update({check.vocabulary()._symbols[k]:f for k,f in check.context_handlers(check.BASE).items()})
    domain=tuple(set(check.BASE.values())|{'other','setting','frame'})
    for old in (*check.ROLE_ASSIGNMENTS,*check.DESIGNATIONS,*check.STAGES):
        doc['statements']=[dict(kind='ask',body=op('equal',call(n[old]),call('expected')))]
        h['expected']=lambda old=old:old
        assert evaluate_document(doc,individuals=domain,situations=('front','body'),primitives=h)[0]['value']
        h['expected']=lambda:'other'
        assert not evaluate_document(doc,individuals=domain,situations=('front','body'),primitives=h)[0]['value']
    roles=check.reference_roles()
    assert roles['ziq']==roles['zir']==roles['eiskh']
    assert len({check.reference_node(x) for x in ('ziq','zir','eiskh')})==3


@pytest.mark.parametrize('field',[0,1,2,3])
def test_role_reference_rejects_unknown_document_node_role_and_context(field):
    doc=deepcopy(check.document());n=check.names();roles=check.role_model(check.BASE)
    key=(check.BASE['eirf'],check.BASE['eish2'],check.previous.previous.canonical(dict(kind='function_ref',symbol=check.reference_roles()['ziq'])),check.BASE['ri'])
    value=roles.pop(key);bad=list(key);bad[field]='wrong';roles[tuple(bad)]=value
    doc['statements']=[dict(kind='ask',body=op('equal',call(n['ziq']),call(n['ziq'])))]
    h=handlers(doc);h.update({check.vocabulary()._symbols[k]:f for k,f in check.context_handlers(check.BASE,roles).items()})
    with pytest.raises(ValueError,match='Unknown temporal reference'):
        evaluate_document(doc,individuals=tuple(set(check.BASE.values())|{'other'}),situations=('front','body'),primitives=h)


def native_record_document():
    doc=deepcopy(check.restored()['document'])
    for name,sort in [('x','individual'),('y','individual'),('s','situation')]:
        doc['declarations'].append(dict(kind='primitive',name=name,parameters=[],result=sort))
    h=handlers(doc)|dict(x=lambda:'x',y=lambda:'y',s=lambda:'s')
    return doc,h


def test_local_and_direction_entity_fields_vary_every_slot_through_native():
    # Binding diagnostics with a distinguishing two-value domain, not physics proofs.
    doc,h=native_record_document();m=check.mapping();num=check.author.num
    for old,size,base in [('eish5',2,1),('eisi6',6,0)]:
        for changed in (None,*range(size)):
            row=['x']*size
            if changed is not None:row[changed]='y'
            model=profile.SynchronyRecords(local={('x','x','s'):row} if size==2 else {},directions={('x','s'):row} if size==6 else {})
            h.update({check.vocabulary()._symbols[k]:f for k,f in model.handlers().items()})
            args=lambda i:[call('x'),call('x'),num(i+base),call('s')] if size==2 else [call('x'),num(i+base),call('s')]
            doc['statements']=[dict(kind='ask',body=op('equal',call(m[old],*args(i)),call('y'))) for i in range(size)]
            assert [r['value'] for r in evaluate_document(doc,individuals=('x','y'),situations=('s',),primitives=h)]==[i==changed for i in range(size)]


def test_cut_candidates_and_shared_configuration_history_through_native():
    doc,h=native_record_document();m=check.mapping();num=check.author.num
    for changed in (None,*range(6)):
        readings=[cut(0)]*6
        if changed is not None:readings[changed]=cut(1)
        model=profile.SynchronyRecords(local_readings={('x','x','x','s'):cut(1)},
            direction_readings={('x','x','x','x','s'):readings},clocks={('x','x'):'y'},histories={('x','y','x','x','x','s'):cut(1)})
        h.update({check.vocabulary()._symbols[k]:f for k,f in model.handlers().items()})
        apply=lambda fn:dict(kind='apply',function=fn,arguments=[num(0)])
        doc['statements']=[dict(kind='ask',body=apply(call(m['eisi7'],call('x'),num(i),call('x'),call('x'),call('x'),call('s')))) for i in range(6)]
        doc['statements'] += [dict(kind='ask',body=apply(call(m['eish6'],call('x'),call('x'),call('x'),call('s')))),
            dict(kind='ask',body=apply(call(m['eisjy'],call('x'),call(m['eisjx'],call('x'),call('x')),call('x'),call('x'),call('x'),call('s'))))]
        assert [r['value'] for r in evaluate_document(doc,individuals=('x','y'),situations=('s',),primitives=h)]==[i==changed for i in range(6)]+[True,True]


def test_named_trial_entities_and_readings_reuse_exact_same_trial_record():
    doc,h=native_record_document();n=check.names();h.update({check.vocabulary()._symbols[k]:f for k,f in check.context_handlers(check.BASE).items()})
    entities=('x','x','y','x','y','x');readings=(cut(1),cut(0),cut(1))
    h.update({check.vocabulary()._symbols[k]:f for k,f in LightTrialRecords({'eisjj':entities},{'eisjj':readings}).handlers().items()})
    doc['statements']=[dict(kind='ask',body=op('equal',call(n[old]),call('y'))) for old in ('eisjk','eisjl','eisjm','eisjn')]
    doc['statements'] += [dict(kind='ask',body=dict(kind='apply',function=call(n[old]),arguments=[check.author.num(0)])) for old in ('eisjo','eisjp','eisjq')]
    assert [r['value'] for r in evaluate_document(doc,individuals=tuple(set(check.BASE.values())|{'x','y','other','setting','frame'}),situations=('front','body','s'),primitives=h)]==[True,False,True,False,True,False,True]


@pytest.mark.parametrize('slot',[-1,6,True,0.0,Fraction(1,2)])
def test_bad_direction_slots_rejected(slot):
    h=profile.SynchronyRecords(directions={('p','s'):['x']*6},direction_readings={('p','t','f','u','s'):[cut(0)]*6}).handlers()
    with pytest.raises(ValueError):h['directioncomponent']('p',slot,'s')
    with pytest.raises(ValueError):h['directionreading']('p',slot,'t','f','u','s')


def test_every_context_key_is_required_and_records_do_not_alias_mutable_inputs():
    f=cut(0);row=['x','y'];model=profile.SynchronyRecords(local={('e','c','s'):row},local_readings={('e','c','u','s'):f},
        directions={('p','s'):['x']*6},direction_readings={('p','t','f','u','s'):[f]*6},clocks={('k','p'):'c'},
        histories={('k','c','e','f','u','s'):f},stages={('d','n','s'):'stage'})
    h=model.handlers();row[0]='changed';assert h['localcomponent']('e','c',1,'s')=='x'
    examples={'localcomponent':(['e','c',1,'s'],[0,1,3]),'localreading':(['e','c','u','s'],range(4)),
        'directioncomponent':(['p',0,'s'],[0,2]),'directionreading':(['p',0,'t','f','u','s'],[0,2,3,4,5]),
        'configurationclock':(['k','p'],range(2)),'configurationreading':(['k','c','e','f','u','s'],range(6)),
        'discoursestageafter':(['d','n','s'],range(3))}
    for name,(args,slots) in examples.items():
        for slot in slots:
            bad=list(args);bad[slot]='unknown'
            with pytest.raises(ValueError,match='Unknown synchrony record'):h[name](*bad)
    for slot in (0,3,True,1.0,Fraction(3,2)):
        with pytest.raises(ValueError):h['localcomponent']('e','c',slot,'s')
    assert h['localcomponent']('e','c',Fraction(2),'s')=='y'


def test_wrong_record_shapes_and_non_cut_values_are_rejected():
    for kwargs in [dict(local={('e','c','s'):['x']}),dict(directions={('p','s'):['x']*5}),
        dict(local_readings={('e','c','u','s'):False}),dict(direction_readings={('p','t','f','u','s'):[False]*6}),
        dict(histories={('k','c','e','f','u','s'):FunctionValue(('individual',),'truth',lambda x:True)})]:
        with pytest.raises(ValueError):profile.SynchronyRecords(**kwargs)


def test_changed_shared_stage_trial_or_law_cannot_reuse_old_evidence():
    for old in ('eisiy','eisjg','eisjo','eimz','eina','einb','eiskh','syncroleproposal'):
        doc=deepcopy(check.document());ds={d['name']:d for d in doc['declarations']};ds[check.names()[old]]['body']=dict(kind='truth',value=True)
        with pytest.raises(ValueError,match='Changed migration'):check.backprojection(doc)
