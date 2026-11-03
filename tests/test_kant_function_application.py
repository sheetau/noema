import pytest
from scripts.check_kant_function_application import cases,checked,fixture,apply,ref
from scripts.kant_public_fragment import decode,events,side_order,compile_statement
from scripts.kant_lexical_context import LexicalContext,use_context
from scripts.kant_interleaved_layout import compile_stream
from scripts.visible_syntax_geometry import from_svg,to_svg
from scripts.check_visible_syntax import call,quant,variable,quote,logic
from noema.constructed_discourse import function_sort


@pytest.mark.parametrize('index',range(len(cases())))
def test_application_uses_visible_function_type_and_preserves_exact_syntax(index):
    row=checked(index)
    if row['key'] in ('two-reference','exchanged','three-reference'):
        assert row['maximum_sides']==(3 if row['key']=='three-reference' else 2)
        assert row['branch_limits']==[]


def test_function_remains_first_on_main_continuation():
    assert side_order('apply',count=1)==[]
    assert side_order('apply',count=4)==[2,1,3]
    for count in range(2,9):
        order=side_order('apply',count=count)
        assert 0 not in order and sorted(order)==list(range(1,count))


def test_application_reader_does_not_call_writer(monkeypatch):
    context,_=fixture();row=checked(4)
    def forbidden(*args,**kwargs):raise AssertionError('Reader must not regenerate source')
    monkeypatch.setattr('scripts.kant_public_fragment.compile_statement',forbidden)
    assert decode(from_svg(row['svg']),lexicon=LexicalContext.from_published(context.published()))==row['source']


def test_quote_cannot_capture_an_ambient_function_binding():
    context,_=fixture()
    inner=apply(variable('f'),call('book'))
    source=dict(kind='assert',body=quant('forall','f',logic('equal',quote(inner),quote(inner)),function_sort(['individual'],'truth')))
    with pytest.raises(ValueError,match='Unbound variable'):
        compile_statement(source,lexicon=context,multiple=True)


@pytest.mark.parametrize('fault',['non-function','too-many','missing'])
def test_visible_application_rejects_wrong_function_or_argument_count(fault):
    context,_=fixture()
    with use_context(context):
        stream=events(cases()[2][2],multiple=True)
        if fault=='non-function':
            # Replace the main function_ref + above by one individual word.
            stream[1:]=[dict(token=call('book')['symbol'],word=call('book')['symbol'],side=None,depth=1,path=[0])]
        elif fault=='too-many':stream[0]['extra_sides'].append(stream[0]['side'])
        else:stream[0]['extra_sides']=[]
        drawing=compile_stream(stream)
    with pytest.raises(ValueError,match='requires a function type|Too many branches|Incomplete visible expression'):
        decode(from_svg(to_svg(drawing['shapes'])),lexicon=LexicalContext.from_published(context.published()))
