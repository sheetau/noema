import pytest

from scripts.check_kant_typed_binders import cases,checked,lam
from scripts.check_kant_public_fragment import canonical
from scripts.check_visible_syntax import call,logic,variable,quant
from scripts.kant_public_fragment import compile_statement,decode,events
from scripts.kant_type_grammar import type_tokens,read_type,read_type_list
from scripts.visible_syntax_geometry import to_svg,from_svg


@pytest.mark.parametrize('index',range(len(cases())))
def test_native_types_and_lambda_parameters_survive_actual_svg(index):
    checked(index)


def test_parameter_order_and_each_slot_have_distinct_visible_forms():
    rows=[checked(i) for i,(key,_,_) in enumerate(cases()) if key.startswith(('lambda-slot-','lambda-order-'))]
    assert len(rows)==5 and len({r['svg'] for r in rows})==5


def test_existing_individual_forms_are_kept():
    simple=canonical(quant('forall','x',logic('equal',variable('x'),variable('x'))))
    assert events(simple)[0]['token']=='forall'
    body=lam(['individual'])
    tokens=[e['token'] for e in events(canonical(logic('equal',body,body)))]
    assert 'lambda_individual' in tokens and 'lambda_typed' not in tokens


@pytest.mark.parametrize('rank',[0,1,128])
def test_description_rank_is_not_counted_as_type_nesting(rank):
    value=dict(kind='description',result=dict(kind='sequence',element='number'),**({'rank':rank} if rank else {}))
    stream=iter(type_tokens(value))
    assert read_type(lambda:next(stream))==value
    assert list(stream)==[]


@pytest.mark.parametrize('tokens,error',[
    (['type_number'],'outside a visible type header'),
    (['types_end'],'outside a visible type header'),
    (['forall_typed','bound0'],'Expected a public type'),
    (['forall_typed','quote_raise','type_number'],'rank marker'),
    (['forall_typed','type_function','type_number'],'type-list'),
    (['lambda_typed','types_more','type_number'],'Incomplete visible type'),
    (['forall_typed','type_sequence'],'Incomplete visible type'),
    (['lambda_typed','types_end'],'Incomplete visible expression'),
])
def test_malformed_type_headers_are_rejected_from_actual_geometry(monkeypatch,tokens,error):
    stream=[dict(token=t,side=None,depth=i,path=[i]) for i,t in enumerate(tokens)]
    monkeypatch.setattr('scripts.kant_public_fragment.events',lambda *args:stream)
    drawing=compile_statement(None,silent=False)
    with pytest.raises(ValueError,match=error):
        decode(from_svg(to_svg(drawing['shapes'])))


def test_type_header_cannot_hide_an_argument_branch(monkeypatch):
    tokens=['forall_typed','type_number','equal','bound0','bound0']
    stream=[dict(token=t,side='bound0' if i==1 else None,depth=i,path=[i]) for i,t in enumerate(tokens)]
    monkeypatch.setattr('scripts.kant_public_fragment.events',lambda *args:stream)
    drawing=compile_statement(None,silent=False)
    with pytest.raises(ValueError,match='Type header cannot carry'):
        decode(drawing['shapes'])


def test_mixed_type_binding_errors_are_not_erased():
    f=lam(['number']);f['body']=call('rain',variable('a'))
    with pytest.raises(ValueError,match='sort'):
        compile_statement(dict(kind='assert',body=logic('equal',f,f)))
    f=lam(['number','individual']);f['parameters'][1]['name']='a'
    with pytest.raises(ValueError,match='Duplicate parameter'):
        compile_statement(dict(kind='assert',body=logic('equal',f,f)))
