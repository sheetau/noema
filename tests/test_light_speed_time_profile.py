from copy import deepcopy
import json
import pytest
from noema.constructed_semantics import FunctionValue,DescriptionValue,evaluate_document
from scripts import check_einstein_light_speed_time as check
from scripts import light_speed_time_profile as profile
from scripts.synchrony_profile import SynchronyVocabulary
from scripts.visible_vectors_vocabulary import VectorsVocabulary
from scripts.shared_modality import call,op


def forbidden(*args):raise AssertionError('Unrelated or quoted content executed')
def handlers(doc):return {d['name']:forbidden for d in doc['declarations'] if d['kind']=='primitive'}
def cut(n):return FunctionValue(('number',),'truth',lambda q:q<n)
def ask(body):return dict(kind='ask',body=body)
def apply(fn,n=0):return dict(kind='apply',function=fn,arguments=[check.author.num(n)])
def domain():return tuple(set(check.BASE.values())|{'other','setting','frame'})


def test_profile_preserves_previous_meanings_and_distinct_math_words():
    old=SynchronyVocabulary();new=check.vocabulary()
    assert len(old._words)==563 and len(new._words)==579
    for field in ('entries','compounds','definitions','primitives'):
        assert all(new.document()[field][n]==d for n,d in old.document()[field].items())
    assert not ({new._symbols[n] for n in profile.PARAMETERS}&set(VectorsVocabulary()._by_symbol))


def test_visible_document_and_backprojection_preserve_all_source_bodies():
    doc=check.restored()['document'];assert doc==check.document()
    old=check.previous.document();ds={d['name']:d for d in doc['declarations']}
    assert all(ds[d['name']]==d for d in old['declarations']) and doc['statements'][:29]==old['statements']
    assert len(doc['statements'])==32 and len(check.source_excerpt()['declarations'])==119
    assert check.backprojection(doc)==check.source_excerpt()


def test_actual_paragraphs_keep_equation_and_page_break_inside_their_sentences():
    b=check.bridge();assert check.author.read(check.BRIDGE)==b
    assert b['sentence_positions']==dict(tm=[14,1],eiskt=[15,1])
    assert b['source_statement_indices']==[81,82] and len(b['source_units'])==4
    eq=b['equation_attachment'];assert eq['one_sentence'] and eq['one_paragraph']
    assert eq['units']==['einstein-1905:u0019','einstein-1905:u0020','einstein-1905:u0021']
    assert eq['math']['bindings']['return']=='eisjq' and eq['math']['bindings']['departure']=='eisjo'
    assert b['page_continuation']['pages']==['894','895'] and b['page_continuation']['one_sentence']
    assert b['cut_reference']==dict(value='tc',node='tm',role='san',numeric_value_supplied=False)
    assert check.names()['rj']==check.previous.names()['rj']


def test_outer_attribution_preserves_every_context_and_relation():
    rows=check.diagnostics();assert len(rows)==13 and rows[0]['values']==[True,True]
    assert all(not all(r['values']) for r in rows[1:])


def test_units_experience_and_designation_bind_without_executing_roles():
    doc=deepcopy(check.restored()['document']);n=check.names()
    doc['declarations'].append(dict(kind='primitive',name='expected',parameters=[],result='individual'))
    h=handlers(doc);h.update({check.vocabulary()._symbols[k]:f for k,f in check.context_handlers(check.BASE).items()})
    for old in (*check.ROLE_ASSIGNMENTS,'eisks'):
        doc['statements']=[ask(op('equal',call(n[old]),call('expected')))]
        h['expected']=lambda old=old:old
        assert evaluate_document(doc,individuals=domain(),situations=('front','body'),primitives=h)[0]['value']
        h['expected']=lambda:'other'
        assert not evaluate_document(doc,individuals=domain(),situations=('front','body'),primitives=h)[0]['value']


def cut_key():return (check.BASE['eirf'],check.BASE['tm'],check.canonical(dict(kind='function_ref',symbol=check.names()['san'])),check.BASE['ri'])


def test_cut_reference_uses_a_shared_role_without_evaluating_it_or_inventing_a_value():
    doc=deepcopy(check.restored()['document']);doc['statements']=[ask(apply(call(check.names()['tc']),q)) for q in (0,1)]
    for value,expected in [(cut(0),[False,False]),(cut(1),[True,False]),(cut(2),[True,True])]:
        h=handlers(doc);h.update({check.vocabulary()._symbols[k]:f for k,f in check.context_handlers(check.BASE,cut_roles={cut_key():value}).items()})
        assert [r['value'] for r in evaluate_document(doc,individuals=domain(),situations=('front','body'),primitives=h)]==expected
    # san describes the shared value; its body must not recursively refer to tc.
    ds={d['name']:d for d in doc['declarations']};seen=set()
    def visit(name):
        if name in seen:return
        seen.add(name)
        for ref in check._references(ds[name].get('body')):visit(ref)
    visit(check.names()['san']);assert check.names()['tc'] not in seen


@pytest.mark.parametrize('field',range(4))
def test_cut_reference_rejects_each_unknown_document_node_role_or_context(field):
    doc=deepcopy(check.document());doc['statements']=[ask(apply(call(check.names()['tc'])))]
    bad=list(cut_key());bad[field]='unknown'
    h=handlers(doc);h.update({check.vocabulary()._symbols[k]:f for k,f in check.context_handlers(check.BASE,cut_roles={tuple(bad):cut(1)}).items()})
    with pytest.raises(ValueError,match='Unknown cut reference'):
        evaluate_document(doc,individuals=domain(),situations=('front','body'),primitives=h)


@pytest.mark.parametrize('field',range(4))
def test_unit_roles_reject_each_unknown_key(field):
    doc=deepcopy(check.document());n=check.names();roles=check.role_model(check.BASE)
    key=(check.BASE['eirf'],check.BASE['tm'],check.canonical(dict(kind='function_ref',symbol=check.reference_roles()['ta'])),check.BASE['ri'])
    value=roles.pop(key);bad=list(key);bad[field]='unknown';roles[tuple(bad)]=value
    doc['statements']=[ask(op('equal',call(n['ta']),call(n['ta'])))]
    h=handlers(doc);h.update({check.vocabulary()._symbols[k]:f for k,f in check.context_handlers(check.BASE,roles).items()})
    with pytest.raises(ValueError,match='Unknown temporal reference'):
        evaluate_document(doc,individuals=domain(),situations=('front','body'),primitives=h)


def test_cut_reference_rejects_non_cut_results_and_wrong_role_types():
    for value in (False,1,FunctionValue(('individual',),'truth',forbidden),FunctionValue(('number',),'individual',forbidden)):
        with pytest.raises(ValueError,match='cut-shaped'):profile.CutReferences({('d','n','r','s'):value})
    h=profile.CutReferences({}).handlers()['describedcutreference']
    for role in (False,DescriptionValue('{}',json.dumps('truth'),0),DescriptionValue('{}',json.dumps(profile.ROLE),1)):
        with pytest.raises(ValueError,match='checked cut role'):h('d','n',role,'s')


def test_native_trial_clock_and_distance_fields_keep_trial_identity():
    # Two distinguishable trials, varying each field separately: binding diagnostics.
    doc=deepcopy(check.restored()['document']);m=check.mapping()
    doc['declarations'] += [dict(kind='primitive',name=n,parameters=[],result='individual') for n in ('x','y')]
    doc['statements']=[ask(op('equal',call(m[old],call(t)),call('y'))) for t in ('x','y') for old in ('te','tf')]
    doc['statements'] += [ask(apply(call(m['tg'],call(t)))) for t in ('x','y')]
    h=handlers(doc)|dict(x=lambda:'x',y=lambda:'y')
    for changed in (None,0,1,2):
        row=['x','x',cut(0)]
        if changed is not None:row[changed]='y' if changed<2 else cut(1)
        model=profile.SpeedTrialRecords({'x':row,'y':['y','y',cut(1)]})
        h.update({check.vocabulary()._symbols[k]:f for k,f in model.handlers().items()})
        assert [r['value'] for r in evaluate_document(doc,individuals=('x','y'),situations=('s',),primitives=h)]==[changed==0,changed==1,True,True,changed==2,True]


def test_trial_records_reject_unknown_keys_bad_shape_and_non_cut_distance():
    row=['a','b',cut(1)];h=profile.SpeedTrialRecords({'trial':row}).handlers();row[0]='changed'
    assert h['departureclock']('trial')=='a' and h['reflectionclock']('trial')=='b'
    for handler in h.values():
        with pytest.raises(ValueError,match='Unknown speed trial'):handler('unknown')
    for bad in (['a','b'],['a','b',False],['a','b',FunctionValue(('individual',),'truth',forbidden)]):
        with pytest.raises(ValueError):profile.SpeedTrialRecords({'trial':bad})


def test_changed_value_role_formula_or_time_naming_cannot_reuse_old_evidence():
    for old in ('tc','san','sai','sal','eins','einy','ein4','eisks','speedroleexperience'):
        doc=deepcopy(check.document());ds={d['name']:d for d in doc['declarations']}
        ds[check.names()[old]]['body']=dict(kind='truth',value=True)
        with pytest.raises(ValueError,match='Changed migration'):check.backprojection(doc)
