from copy import deepcopy
import pytest
from scripts.concept2_assembly_reader import AssemblyCodec
from scripts.concept2_assembly import expand_plan
from scripts import concept2_composition as c,concept2_geometry_v5 as g
from tests.test_concept2_trunk import codec as prior_fixture


@pytest.fixture(scope='module')
def codec():return AssemblyCodec(prior_fixture.__wrapped__().dictionary)


def word(codec,name):return dict(form='word',parts=codec.dictionary['selected_spellings'][name])
def call(codec,name):return dict(kind='call',symbol=word(codec,name),arguments=[])
def eq(a,b):return dict(kind='equal',arguments=[a,b])


def verify(codec,body):
    plan=dict(form='scope',quotation=True,body=dict(kind='assert',body=body))
    expected=expand_plan(plan,codec.dictionary);tokens=codec.encode(plan)
    drawing=g.layout(codec.units(tokens))[0]
    assert codec.read_svg(c.svg(drawing['shapes']))['native']==expected
    return tokens


def test_every_value_and_word_alias_key_has_a_meaningful_use(codec):
    for label in range(8):
        verify(codec,eq(dict(form='local-definition',label=label,value=call(codec,'a')),dict(form='local-use',label=label)))
        define=dict(kind='call',symbol=dict(form='word-definition',label=label,parts=codec.dictionary['selected_spellings']['a']),arguments=[])
        use=dict(kind='call',symbol=dict(form='word-use',label=label),arguments=[])
        verify(codec,eq(define,use))


def test_every_quotation_template_lane_and_mode_has_a_meaningful_use(codec):
    for lane in (-1,0,1):
        for mode in ('quoted_value','quoted_ref'):
            value=lambda name:call(codec,name) if mode=='quoted_value' else dict(kind='function_ref',symbol=word(codec,name))
            define=dict(form='template-definition',lane=lane,mode=mode,rank=None,value=value('a'))
            use=dict(form='template-use',lane=lane,value=value('b'))
            verify(codec,eq(define,use))


def test_every_dot_identity_pairs_values_without_changing_them(codec):
    for label in range(256):
        define=dict(form='dot-definition',label=label,value=call(codec,'a'))
        use=dict(form='dot-use',label=label)
        tokens=verify(codec,eq(define,use))
        assert ('dot-bare',153) in tokens if label==153 else tokens.count(('dot',label))==2


@pytest.mark.parametrize('family',['values','quoted','references'])
def test_both_separator_lengths_are_used_in_their_actual_argument_context(codec,family):
    dictionary=deepcopy(codec.dictionary)
    element=dict(kind='description',result='individual') if family=='quoted' else 'individual'
    dictionary['native']['declarations'].append(dict(kind='primitive',name='seven',parameters=[element]*7,result='truth'))
    parts=[c.old.root_symbol('rain'),c.old.root_symbol('rain')]
    dictionary['selected_spellings']['seven']=parts;dictionary['aliases'].append(dict(symbol='seven',parts=parts))
    typed=AssemblyCodec(dictionary);value=call(typed,'a')
    if family=='quoted':value=dict(kind='quote',body=value)
    if family=='references':
        args=[dict(form='role-definition',lane=lane,value=value) for lane in (-1,0,1)]
        args.extend(dict(form='role-use',lane=lane) for lane in (-1,0,1,-1))
    else:args=[value]*7
    tokens=verify(typed,dict(kind='call',symbol=word(typed,'seven'),arguments=args))
    assert ('separator',family,False) in tokens and ('separator',family,True) in tokens
