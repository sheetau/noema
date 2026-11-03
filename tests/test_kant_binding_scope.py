import pytest

from scripts.check_kant_binding_scope import cases, checked, preserved, nested
from scripts.check_kant_public_fragment import canonical
from scripts.check_visible_syntax import call, logic, variable, quote
from scripts.kant_public_fragment import compile_statement, decode, events, split
from scripts.visible_syntax_geometry import to_svg, from_svg


@pytest.mark.parametrize('index', range(len(cases())))
def test_visible_binding_scope_roundtrip(index):
    checked(index)


@pytest.mark.parametrize('index', range(40))
def test_previous_actual_svgs_keep_exact_syntax(index):
    preserved(index)


def test_every_binding_position_has_distinct_geometry():
    for depth in (3,5):
        rows=[checked(i) for i,(key,_,_) in enumerate(cases()) if key.startswith('depth-'+str(depth))]
        assert len({r['svg'] for r in rows})==depth
        assert [r['shifts'] for r in rows]==[max(0,depth-slot-2) for slot in range(depth)]


def test_recursive_scope_rule_is_not_a_finite_glyph_number_table():
    # Exercise recursion without an expensive large drawing or model domain.
    names=tuple('v'+str(i) for i in range(70))
    scope=names
    node=variable(names[0])
    count=0
    while True:
        token,children,scope=split(node,scope)
        if token!='bound_shift':break
        assert children==[node]
        count+=1
    assert count==68 and token=='bound1'


@pytest.mark.parametrize('tail,depth,error', [
    (['bound_shift','bound1'],2,'outside the visible scope'),
    (['bound_shift','bound0'],3,'must precede'),
    (['bound_shift','equal','bound0','bound1'],3,'must precede'),
    (['bound_shift'],3,'must precede'),
    (['bound_shift','bound_shift','bound1'],3,'outside the visible scope'),
    (['quote','bound_shift','bound1'],3,'outside the visible scope'),
])
def test_malformed_outward_references_are_rejected_from_geometry(monkeypatch,tail,depth,error):
    # Deliberately author grammar tokens without a native AST to test the reader.
    tokens=['forall']*depth+tail
    stream=[dict(token=t,side=None,depth=i,path=[i]) for i,t in enumerate(tokens)]
    monkeypatch.setattr('scripts.kant_public_fragment.events',lambda *args:stream)
    drawing=compile_statement(None,silent=False)
    with pytest.raises(ValueError,match=error):
        decode(from_svg(to_svg(drawing['shapes'])))


def test_quotation_does_not_capture_an_outside_binder():
    source=dict(kind='assert',body=nested(('a','b','c'),logic('equal',quote(variable('a')),quote(call('book')))))
    with pytest.raises(ValueError,match='Unbound variable'):
        compile_statement(source)


def test_three_binders_keep_old_nearest_reference_spelling():
    source=canonical(nested(('a','b','c'),call('above',variable('c'),variable('b'))))
    tokens=[e['token'] for e in events(source,branch=False)]
    assert tokens[-2:]==['bound0','bound1']
    assert 'bound_shift' not in tokens
