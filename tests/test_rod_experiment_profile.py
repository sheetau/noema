from copy import deepcopy
from fractions import Fraction
import json
import pytest
from noema.constructed_semantics import FunctionValue,DescriptionValue,evaluate_document
from scripts import check_einstein_rod_experiment as check
from scripts import rod_experiment_profile as profile
from scripts.two_principles_profile import TwoPrinciplesVocabulary
from scripts.shared_modality import call,op


def forbidden(*args):raise AssertionError('Unrelated or quoted content executed')
def handlers(doc):return {d['name']:forbidden for d in doc['declarations'] if d['kind']=='primitive'}
def cut(n):return FunctionValue(('number',),'truth',lambda q:q<n)
def ask(body):return dict(kind='ask',body=body)
def apply(fn,*args):return dict(kind='apply',function=fn,arguments=list(args))
def domain():return tuple(set(check.BASE.values())|{'other','setting','frame','rb'})
def context(doc,**kwargs):return handlers(doc)|{check.vocabulary()._symbols[k]:f for k,f in check.context_handlers(check.BASE,**kwargs).items()}
def run(doc,h):return [r['value'] for r in evaluate_document(doc,individuals=domain(),situations=check.SITUATIONS,primitives=h)]


def test_profile_preserves_all_previous_contracts_and_exposes_role_label_alias():
    old=TwoPrinciplesVocabulary();new=check.vocabulary()
    assert len(old._words)==632 and len(new._words)==660
    for field in ('entries','compounds','definitions','primitives'):
        assert all(new.document()[field][n]==d for n,d in old.document()[field].items())
    assert len(profile.CONTRACTS)==26 and len(profile.ALL_CONTRACTS)==28
    assert profile.REUSED=={'introducesreferent'}
    assert profile.CONTRACTS['introducesreferent']['arguments'][-1]=='reference'
    assert profile.REUSED_ARGUMENTS['introducesreferent'][-1]=='context'
    assert new._symbols['introducesreferent']==old._symbols['introducesreferent']


def test_visible_document_preserves_source_and_previous_document():
    doc=check.restored()['document'];assert doc==check.document()
    old=check.previous.document();ds={d['name']:d for d in doc['declarations']}
    assert all(ds[d['name']]==d for d in old['declarations']) and doc['statements'][:40]==old['statements']
    assert (len(doc['declarations']),len(doc['statements']),len(check.source_excerpt()['declarations']))==(865,43,179)
    assert check.backprojection(doc)==check.source_excerpt()


def test_three_sentences_and_forward_methods_use_actual_text_coordinates():
    b=check.bridge();assert check.author.read(check.BRIDGE)==b
    assert b['source_statement_indices']==[88,89,90]
    assert b['sentence_positions']==dict(y2=[19,1],eisly=[19,2],y3=[19,3],xw=[20,1],xx=[21,1])
    assert b['sentence_ranges']==[[0,126],[127,380],[381,496]]
    assert [r['id'] for r in b['math']]==['M0043','M0044','M0045','M0046','M0047']
    assert len(b['setting_roles'])==5 and len(b['cut_roles'])==2 and len(b['endpoint_fields'])==11


def test_outer_and_inner_discourse_preserve_every_role_and_quoted_content():
    outer=check.diagnostics();inner=check.presentation_diagnostics()
    assert len(outer)==10 and len(inner)==22
    for rows in (outer,inner):
        assert rows[0]['values']==[True]*3
        assert all(not all(r['values']) for r in rows[1:])
    ds={d['name']:d for d in check.source_excerpt()['declarations']}
    # Preserve the initial direction and later assertions, not just their content.
    assert [ds[name]['body']['force'] for name in ('eipo','eipr','eipu')]==['direct','assert','assert']
    assert check.backprojection(check.document())==check.source_excerpt()


def test_native_references_preserve_individuals_and_five_settings_without_executing_roles():
    doc=deepcopy(check.restored()['document']);n=check.names()
    for assignments,sort in [(check.ROLE_ASSIGNMENTS,'individual'),(check.SETTING_ASSIGNMENTS,'situation')]:
        name='expectedindividual' if sort=='individual' else 'expectedsetting'
        doc['declarations'].append(dict(kind='primitive',name=name,parameters=[],result=sort))
        for old in assignments:
            doc['statements']=[ask(op('equal',call(n[old]),call(name)))]
            h=context(doc);h[name]=lambda old=old:check.BASE[old]
            assert run(doc,h)==[True]
            h[name]=lambda:'other' if sort=='individual' else 'front'
            assert run(doc,h)==[False]


def test_length_and_speed_are_references_without_an_invented_numeric_value():
    doc=deepcopy(check.restored()['document']);n=check.names()
    for old in check.CUT_ASSIGNMENTS:
        doc['statements']=[ask(apply(call(n[old]),check.author.num(q))) for q in (0,1)]
        for threshold,expected in [(0,[False,False]),(1,[True,False]),(2,[True,True])]:
            cuts=check.cut_model(check.BASE)
            node=check.CUT_ASSIGNMENTS[old][0]
            key=(check.BASE['eirf'],check.BASE[node],check.canonical(dict(kind='function_ref',symbol=check.reference_roles(check.CUT_ASSIGNMENTS)[old])),check.BASE['ri'])
            cuts[key]=cut(threshold)
            assert run(doc,context(doc,cuts=cuts))==expected
    ds={d['name']:d for d in doc['declarations']}
    done=set()
    def visit(name,stack):
        assert name not in stack,'Cyclic role reference'
        if name in done:return
        for ref in check._references(ds[name].get('body')):visit(ref,stack|{name})
        done.add(name)
    for old in (*check.SETTING_ASSIGNMENTS,*check.CUT_ASSIGNMENTS):visit(n[old],set())


@pytest.mark.parametrize('field',range(4))
def test_setting_references_reject_each_unknown_key(field):
    doc=deepcopy(check.document());n=check.names()
    for old in check.SETTING_ASSIGNMENTS:
        roles=check.model_roles(check.BASE,check.SETTING_ASSIGNMENTS)
        node=check.SETTING_ASSIGNMENTS[old][0]
        key=(check.BASE['eirf'],check.BASE[node],check.canonical(dict(kind='function_ref',symbol=check.reference_roles(check.SETTING_ASSIGNMENTS)[old])),check.BASE['ri'])
        value=roles.pop(key);bad=list(key);bad[field]='unknown';roles[tuple(bad)]=value
        doc['statements']=[ask(op('equal',call(n[old]),call(n[old])))]
        with pytest.raises(ValueError,match='Unknown setting reference'):run(doc,context(doc,settings=roles))


def test_setting_reference_requires_closed_checked_role_and_copies_mapping():
    role=DescriptionValue('{}',json.dumps(profile.SETTING_ROLE),0);key=('d','n','{}','s');rows={key:'setting'}
    h=profile.SettingReferences(rows).handlers()['describedsettingreference'];rows[key]='changed'
    assert h('d','n',role,'s')=='setting'
    for bad in (False,DescriptionValue('{}',json.dumps('truth'),0),DescriptionValue('{}',json.dumps(profile.SETTING_ROLE),1)):
        with pytest.raises(ValueError,match='checked setting role'):h('d','n',bad,'s')


def test_native_endpoint_record_binds_every_entity_and_reading_slot():
    # Two distinguishable values, one changed component: binding diagnostics only.
    doc=deepcopy(check.restored()['document']);n=check.names()
    doc['declarations'].append(dict(kind='primitive',name='expected',parameters=[],result='individual'))
    entities=list(check.FIELDS)[:8];readings=list(check.FIELDS)[8:]
    doc['statements']=[ask(op('equal',call(n[old]),call('expected'))) for old in entities]
    doc['statements'] += [ask(apply(call(n[old]),check.author.num(0))) for old in readings]
    key=(check.BASE['xi'],check.BASE['ra'],check.BASE['yf'])
    for changed in (None,*range(11)):
        row=['xi']*8;cuts=[cut(0) for _ in range(3)]
        if changed is not None:
            if changed<8:row[changed]='other'
            else:cuts[changed-8]=cut(1)
        records=profile.RodExperimentRecords(entities={key:row},readings={key:cuts})
        h=context(doc,records=records)|dict(expected=lambda:'other')
        assert run(doc,h)==[changed==i for i in range(11)]


def test_native_setting_roles_keep_the_initial_placement_motion_and_inheritance_relations():
    doc=deepcopy(check.document());n=check.names();m=check.mapping()
    doc['declarations'].append(dict(kind='primitive',name='candidate',parameters=[],result='situation'))
    expected=dict(initial=('x4',[('xi','frame','initial'),('xj','frame','initial')]),
        placed=('eislx',[('xi','initial','placed')]),moving=('yv',[('xi','placed','moving')]),
        methoda=('yx',[('moving','methoda')]),methodb=('yx',[('moving','methodb')]))
    for old,(_,role) in check.SETTING_ASSIGNMENTS.items():
        relation,facts=expected[role]
        doc['statements']=[ask(call(check.reference_roles(check.SETTING_ASSIGNMENTS)[old],call('candidate'),call(n['ri'])))]
        for candidate in (check.BASE[old],'front'):
            seen=[]
            def accept(*args):seen.append(args);return args in facts
            h=context(doc)|dict(candidate=lambda:candidate);h[m[relation]]=accept
            assert run(doc,h)==[candidate==check.BASE[old]]
            assert seen and all(args[-1]==candidate for args in seen)


@pytest.mark.parametrize('name,table,key,slot',[
    ('endpointmeasuremententity','entities',('b','f','s'),0),('endpointmeasurementreading','readings',('b','f','s'),0),
    ('intervalstart','intervals',('f','t','s'),None),('intervalend','intervals',('f','t','s'),None),
    ('firstendmark','endmarks',('b','f','s'),None),('lastendmark','endmarks',('b','f','s'),None),
    ('pointtrajectoryfamily','trajectories',('b','f','l','t','a','s'),None)])
def test_records_reject_each_changed_key(name,table,key,slot):
    family=FunctionValue(('individual',),profile.TRAJECTORY,forbidden)
    values=dict(entities=['a']*8,readings=[cut(1)]*3,intervals=[cut(1),cut(2)],endmarks=['a','b'],trajectories=family)
    h=profile.RodExperimentRecords(**{table:{key:values[table]}}).handlers()[name]
    tail=() if slot is None else (slot,)
    assert h(*key,*tail) is not None
    for i in range(len(key)):
        bad=list(key);bad[i]='unknown'
        with pytest.raises(ValueError,match='Unknown rod record'):h(*bad,*tail)


def test_shapes_slots_cut_types_and_interval_endmarks_are_checked_and_copied():
    key=('b','f','s');entities=list('abcdefgh');marks=['a','b'];intervals=[cut(0),cut(1)]
    h=profile.RodExperimentRecords(entities={key:entities},readings={key:[cut(i) for i in range(3)]},
        intervals={key:intervals},endmarks={key:marks}).handlers()
    entities[0]='changed';marks[0]='changed';intervals[0]=cut(2)
    assert h['endpointmeasuremententity'](*key,0)=='a'
    assert h['firstendmark'](*key)=='a' and h['lastendmark'](*key)=='b'
    assert not h['intervalstart'](*key).implementation(0) and h['intervalend'](*key).implementation(0)
    for name,size in [('endpointmeasuremententity',8),('endpointmeasurementreading',3)]:
        for i in range(size):assert h[name](*key,Fraction(i)) is not None
        for bad in (True,0.0,Fraction(1,2),-1,size):
            with pytest.raises(ValueError,match='rod slot'):h[name](*key,bad)
    for kwargs in ({'entities':{key:['a']*7}},{'readings':{key:[cut(1)]*2}},
                   {'intervals':{key:[cut(1)]}},{'endmarks':{key:['a']}},
                   {'readings':{key:[cut(1),False,cut(1)]}}, {'intervals':{key:[cut(1),FunctionValue(('individual',),'truth',forbidden)]}},
                   {'trajectories':{key:False}},{'trajectories':{key:FunctionValue(('individual',),profile.CUT,forbidden)}}):
        with pytest.raises(ValueError):profile.RodExperimentRecords(**kwargs)


def test_native_trajectory_family_preserves_point_and_time_application():
    doc=deepcopy(check.document());m=check.mapping();n=check.names()
    def family(point):
        def position(time):return cut((1 if point=='xi' else 0)+(1 if time(Fraction(0)) else 0))
        return FunctionValue((profile.CUT,),profile.CUT,position)
    model=profile.RodExperimentRecords(trajectories={('xi','frame','ta','rb','yn','moving'):FunctionValue(('individual',),profile.TRAJECTORY,family)})
    # Ground all six keys explicitly; this isolates nested-function binding.
    specs=[('rod','individual','xi'),('frame','individual','frame'),('lu','individual','ta'),('tu','individual','rb'),
           ('axis','individual','yn'),('setting','situation','moving'),('point','individual','xi'),('time',profile.CUT,None)]
    doc['declarations'] += [dict(kind='primitive',name=name,parameters=[],result=sort) for name,sort,_ in specs]
    fn=call(m['eislu'],*[call(name) for name in ('rod','frame','lu','tu','axis','setting')])
    doc['statements']=[ask(apply(apply(apply(fn,call('point')),call('time')),check.author.num(q))) for q in (0,1)]
    h=handlers(doc)|{name:(lambda value=value:value) for name,_,value in specs}
    h.update({check.vocabulary()._symbols[k]:f for k,f in model.handlers().items()})
    for point,t,expected in [('xi',0,[True,False]),('other',0,[False,False]),('xi',1,[True,True]),('other',1,[True,False])]:
        h['point']=lambda:point;h['time']=lambda:cut(t)
        assert run(doc,h)==expected


def test_changed_composition_role_or_record_binding_cannot_reuse_evidence():
    for old in ('eipg','eipk','eipi','eipj','eipl','eipm','eipt','sbv','ya','yb','yc','yd','yf','xn','xv','rodrolespeed'):
        doc=deepcopy(check.document());ds={d['name']:d for d in doc['declarations']}
        ds[check.names()[old]]['body']=dict(kind='truth',value=True)
        with pytest.raises(ValueError,match='Changed migration'):check.backprojection(doc)
