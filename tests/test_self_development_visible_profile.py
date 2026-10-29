"""Preserve actor/episode bindings and typed count-only comparison alternatives."""
from copy import deepcopy
from fractions import Fraction
import json
import pytest
from noema.constructed_discourse import normalize_document
from noema.constructed_semantics import evaluate_document,SequenceValue,FunctionValue
from scripts import self_development_visible_profile as profile
from scripts.shared_modality import call
from scripts.visible_collection import compile_collection,decode_collection
from scripts.visible_syntax_geometry import to_svg,from_svg
from scripts.visible_word_forms import Word


def test_contracts_survive_actual_svg():
    vocabulary=profile.SelfDevelopmentVisibleVocabulary()
    doc=normalize_document(dict(schema_version='0.16',lexicon_version='0.16',
        declarations=vocabulary.imports(set(profile.ALL_CONTRACTS)),statements=[]))
    pages=compile_collection(doc,Word('proper',('book','home','above','aki')),vocabulary,payload=768)['pages']
    assert decode_collection([from_svg(to_svg(p['shapes'])) for p in pages],vocabulary)['document']==doc
    assert len(doc['declarations'])==7


def primitive(name,parameters,result):return dict(kind='primitive',name=name,parameters=parameters,result=result)
def canonical(sort):return json.dumps(sort,sort_keys=True,separators=(',',':'))
def run(doc,values):
    domain=('a','b','c','other')
    return [r['value'] for r in evaluate_document(doc,individuals=domain,situations=domain,
        primitives=values,memoize_definitions=False,memoize_expressions=False)]


def fixture(name):
    row=profile.CONTRACTS[name]
    declarations=[primitive(name,row['parameters'],row['result'])]
    arguments=[];values={}
    for i,sort in enumerate(row['parameters']):
        symbol='jarg'+'abc'[i];value=Fraction(5) if sort=='number' else 'abc'[i]
        declarations.append(primitive(symbol,[],sort));arguments.append(call(symbol))
        values[symbol]=lambda value=value:value
    if row['result']=='truth':body=call(name,*arguments)
    else:
        declarations.append(primitive('jinspect',[row['result']],'truth'))
        body=call('jinspect',call(name,*arguments))
    return normalize_document(dict(schema_version='0.16',lexicon_version='0.16',declarations=declarations,
        statements=[dict(kind='ask',body=body)])),values


def alternative_sequence(flags):
    sort=profile.CONTRACTS['countfocusalternatives']['result']['element']
    functions=tuple(FunctionValue(('number',),'truth',lambda count,flag=flag:flag and count>=2) for flag in flags)
    return SequenceValue(functions,canonical(sort))


def test_every_population_context_person_episode_and_point_slot():
    for name,row in profile.CONTRACTS.items():
        doc,values=fixture(name)
        expected=tuple(Fraction(5) if s=='number' else 'abc'[i] for i,s in enumerate(row['parameters']))
        def relation(*args):
            if args!=expected:raise ValueError('Unknown self-development input')
            return alternative_sequence((True,False)) if isinstance(row['result'],dict) else Fraction(3,2) if row['result']=='number' else True
        values[name]=relation
        if row['result']!='truth':
            values['jinspect']=(lambda seq:len(seq.items)==2 and [fn(Fraction(3)) for fn in seq.items]==[True,False]) if isinstance(row['result'],dict) else lambda n:n==Fraction(3,2)
        assert run(doc,values)==[True]
        for i,sort in enumerate(row['parameters']):
            changed=values|{'jarg'+'abc'[i]:(lambda:Fraction(6)) if sort=='number' else (lambda:'other')}
            with pytest.raises(ValueError,match='Unknown self-development'):run(doc,changed)
        def unknown(*args):raise ValueError('Unspecified self-development input')
        with pytest.raises(ValueError,match='Unspecified'):run(doc,values|{name:unknown})
        if row['result']=='truth':assert run(doc,values|{name:lambda *args:False})==[False]


def test_count_alternatives_keep_order_empty_list_and_number_only_inputs():
    name='countfocusalternatives';doc,values=fixture(name)
    for flags in ((),(False,True),(True,False),(True,True)):
        expected=[[False,flag,flag] for flag in flags]
        values[name]=lambda *args,flags=flags:alternative_sequence(flags)
        values['jinspect']=lambda seq:len(seq.items)==len(flags) and [[f(Fraction(n)) for n in (0,2,5)] for f in seq.items]==expected
        assert run(doc,values)==[True]
    def unknown(n):raise ValueError('Unknown count condition')
    element=profile.CONTRACTS[name]['result']['element']
    seq=SequenceValue((FunctionValue(('number',),'truth',unknown),),canonical(element))
    values[name]=lambda *args:seq
    values['jinspect']=lambda sequence:sequence.items[0](Fraction(2))
    with pytest.raises(ValueError,match='Unknown count condition'):run(doc,values)
    wrong=[SequenceValue((),canonical('individual')),
        SequenceValue((FunctionValue(('individual',),'truth',lambda p:True),),canonical(element)),
        SequenceValue((FunctionValue(('number',),'number',lambda p:Fraction(1)),),canonical(element))]
    for seq in wrong:
        with pytest.raises(ValueError):run(doc,values|{name:lambda *args,seq=seq:seq})
    invalid=deepcopy(doc)
    next(d for d in invalid['declarations'] if d['name']=='jarga')['result']='individual'
    with pytest.raises(ValueError):normalize_document(invalid)


def test_population_threshold_preserves_exact_numbers_and_rejects_non_numbers():
    name='populationfewerthreshold';doc,values=fixture(name)
    for threshold in (Fraction(0),Fraction(1,3),Fraction(4)):
        values[name]=lambda population,context,threshold=threshold:threshold
        values['jinspect']=lambda value:value==threshold
        assert run(doc,values)==[True]
    # Positivity is a composed condition, not a silent coercion by the word.
    for wrong in ('a',True):
        with pytest.raises(ValueError):run(doc,values|{name:lambda *args,wrong=wrong:wrong})
