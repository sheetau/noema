from copy import deepcopy
import pytest

from scripts import kant_public_fragment as writing
from scripts.check_kant_bound_argument_contact import cases, contacts, OUT
from scripts.check_kant_multiple_arguments import fixture
from scripts.check_kant_public_fragment import canonical
from scripts.check_visible_syntax import call, variable, quant
from scripts.kant_lexical_context import use_context
from scripts.kant_interleaved_layout import compile_stream
from scripts.visible_syntax_geometry import from_svg,to_svg
from scripts.check_kant_root_overlap import saved_page


def test_quote_cannot_capture_the_actual_surrounding_binder():
    context=fixture()[0]
    with use_context(context):
        stream=deepcopy(writing.events(cases()[0][1],multiple=True))
        assert [e['token'] for e in stream[:2]]==['forall_typed','type_situation']
        # Keep the outer binder and introduce a quotation inside its body.
        stream.insert(2,dict(token='quote',side=None,depth=0,path=()))
        svg=to_svg(compile_stream(stream)['shapes'])
    assert contacts(svg)
    with pytest.raises(ValueError,match='Unbound visible variable'):
        writing.decode(from_svg(svg),lexicon=context)


def test_later_branch_keeps_a_line_when_tangent_would_reverse_branch_order():
    context,names=fixture()
    body=dict(kind='call',symbol=names[2],arguments=[call('aki'),variable('x'),call('nao'),call('book')])
    with use_context(context):source=canonical(quant('forall','x',body))
    path=OUT.parent/'kant-bound-contact-prefix/trial-v1/individual.svg'
    svg=path.read_text(encoding='utf-8')
    assert not contacts(svg)
    assert writing.decode(from_svg(svg),lexicon=context)==source


def test_contact_reader_has_no_generation_or_layout_dependency(monkeypatch):
    context=fixture()[0]
    svg=(OUT/'situation-first.svg').read_text(encoding='utf-8')
    def forbidden(*args,**kwargs):raise AssertionError('Reader called the writer')
    monkeypatch.setattr(writing,'compile_statement',forbidden)
    monkeypatch.setattr('scripts.kant_interleaved_layout.compile_stream',forbidden)
    assert writing.decode(list(reversed(from_svg(svg))),lexicon=context)==cases()[0][1]


def test_shared_argument_page_still_prohibits_eccentric_containment():
    assert saved_page()==dict(svg_count=24,circles=244,legal=True)
