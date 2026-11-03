from copy import deepcopy
from itertools import permutations
import pytest

from scripts import flow_circle as f
from scripts.check_structural_circle import cases,full_vocabulary
from scripts.check_flow_circle import specimen
from scripts.check_visible_syntax import vocabulary,doc,assertion,call,logic,num,quant,variable
from scripts.visible_lexical_script import _translate,_shape_set
from scripts.balanced_circle_script import circle,line,SMALL,MEDIUM,LARGE


@pytest.mark.parametrize('case',range(40))
def test_all_grammar_contrasts_from_actual_svg(case):
    # Shared within this check process, so the report reuses this same SVG check.
    assert specimen(case)['document']==cases()[case][2]


@pytest.mark.parametrize('line_atoms',[4,7,16,32])
def test_quote_binding_and_word_continuations(line_atoms):
    d=cases()[8][2]
    assert f.decode_page(f.compile_page(d,line_atoms=line_atoms)['shapes'])==d


@pytest.mark.parametrize('order',list(permutations(('aki','nao','book'))))
def test_three_argument_permutations(order):
    d=doc(assertion(call('give',*(call(n) for n in order))),roots=('give','aki','nao','book'))
    assert f.decode_page(f.compile_page(d)['shapes'])==d


def test_full_public_alphabet_is_injective_and_each_shape_is_read():
    v=full_vocabulary();alphabet=f.alphabet(v)
    for g,tokens in alphabet.values():
        # Each letter is tested with a visible margin and a known large anchor.
        glyphs=f.flow_packet([f.ligature('document'),g],0,True)
        drawn=f.render_line(glyphs)
        read=f.recognize_line(f.from_svg(f.to_svg(drawn['shapes'])),v)
        assert read[2:-1]==f.expanded([f.ligature('document'),g],v)


@pytest.mark.parametrize('stacked',[False,True])
def test_hand_drawn_horizontal_branch_without_renderer(monkeypatch,stacked):
    # ordinal 0, numeral end, above(birdone,treeone), finish. Independent ink.
    rings=[(0,32,SMALL),(55,32,SMALL),(150,32,LARGE),(280,0,MEDIUM),(380,64,MEDIUM),(460,64,SMALL)]
    paths=[((0,32),(SMALL,32)),((150,32),(150,32-LARGE)),
           ((280,0),(280,-MEDIUM)),((380,64),(380,64+MEDIUM)),
           ((460,64),(460+SMALL,64)),((460,64),(460,64-SMALL)),
           ((SMALL,32),(55-SMALL,32)),((55+SMALL,32),(150-LARGE,32)),
           ((150+LARGE,32),(210,32)),((210,32),(242,0)),((242,0),(280-MEDIUM,0)),
           ((210,32),(242,64)),((242,64),(380-MEDIUM,64)),((380+MEDIUM,64),(460-SMALL,64))]
    if stacked:
        def shift(x,y):return (x-100 if x>=380-MEDIUM else x,y)
        rings=[(*shift(x,y),r) for x,y,r in rings]
        paths=[(shift(*a),shift(*b)) for a,b in paths]
    shapes=[circle(*c) for c in rings]+[line(a,b) for a,b in paths]
    monkeypatch.setattr(f,'render_line',lambda *a,**k:pytest.fail('Decoder invoked renderer'))
    tokens=f.recognize_line(shapes,vocabulary())
    reader=f.FlowReader(tokens[2:-1],vocabulary())
    assert reader.statement()==assertion(call('above',call('birdone'),call('treeone')))
    assert reader.i==len(reader.tokens)


@pytest.mark.parametrize('branches',[True,False])
def test_branch_allograph_and_scaled_segmented_svg_preserve_syntax(branches):
    d=cases()[8][2];shapes=f.compile_page(d,branches=branches)['shapes'];changed=[]
    for s in _translate(shapes,193.25,-601.4,1.73):
        if s['kind']=='circle':changed.append(s)
        else:
            a,b=(s['x1'],s['y1']),(s['x2'],s['y2']);m=((a[0]+b[0])/2,(a[1]+b[1])/2)
            changed.extend((line(b,m),line(m,a)))
    assert f.decode_page(list(reversed(changed)))==d


@pytest.mark.parametrize('mutation',['missing','extra','field','radius','ray','disconnected'])
def test_unknown_or_damaged_ink_is_rejected(mutation):
    shapes=deepcopy(f.compile_page(cases()[0][2])['shapes'])
    rings=[s for s in shapes if s['kind']=='circle'];lines=[s for s in shapes if s['kind']=='line']
    if mutation=='missing':shapes.remove(rings[2])
    elif mutation=='extra':shapes.append(circle(100000,0,SMALL))
    elif mutation=='field':rings[0]['ast']='hidden'
    elif mutation=='radius':rings[2]['r']*=.9
    elif mutation=='ray':lines[-1]['y2']+=3
    else:shapes.remove(max(lines,key=lambda s:abs(s['x2']-s['x1'])))
    with pytest.raises(ValueError):f.decode_page(shapes)


def test_implicit_assertion_does_not_consume_other_speech_acts():
    for i in (7,8,39):
        d=cases()[i][2]
        assert f.decode_page(f.compile_page(d)['shapes'])==d
    d=cases()[0][2];w=f.FlowWriter(vocabulary());w.statement(d['statements'][0])
    assert _shape_set(w.glyphs[0]['shapes'])!=_shape_set(f.ligature('assert')['shapes'])


def test_quote_cannot_capture_an_outer_variable():
    w=f.FlowWriter(vocabulary());w.keyword('forall');w.type('individual')
    w.keyword('quote');w.natural(0);w.keyword('variable');w.natural(0)
    tokens=f.expanded(w.glyphs,vocabulary())
    with pytest.raises(ValueError,match='Unbound'):f.FlowReader(tokens,vocabulary()).statement()


def test_branch_height_is_bounded_independently_of_expression_nesting():
    e=logic('equal',num(1),num(1))
    for _ in range(20):e=logic('not',e)
    d=doc(assertion(e));p=f.compile_page(d,line_atoms=16)
    assert f.decode_page(p['shapes'])==d
    # The layout has only the three handwriting rails, not one level per AST.
    assert p['rows']<8


def test_reordered_or_truncated_rows_and_wrong_final_mark_rejected():
    from scripts.visible_page import interval
    d=cases()[8][2];shapes=f.compile_page(d,line_atoms=7)['shapes']
    # Remove all ink from the final geometrically separated row.
    spans=sorted((interval(s)[0],interval(s)[1]) for s in shapes)
    bottom=None;starts=[]
    for lo,hi in spans:
        if bottom is None or lo>bottom+1e-6:starts.append(lo)
        bottom=hi if bottom is None else max(bottom,hi)
    cut=[s for s in shapes if interval(s)[0]<starts[-1]]
    with pytest.raises(ValueError):f.decode_page(cut)


def test_automatic_old_sharing_writer_cannot_insert_uncompressed_tokens():
    with pytest.raises(ValueError):f.FlowWriter(vocabulary(),automatic=True)


def test_existing_kant_excerpt_preserves_every_statement():
    from scripts.check_flow_circle import kant_excerpt
    assert kant_excerpt()['statements']==4


def test_word_only_geometry_without_large_circles_uses_margin_scale():
    w=f.FlowWriter(vocabulary());w.expr(call('birdone'))
    drawing=f.compile_glyphs(w.glyphs)
    assert max(s['r'] for s in drawing['shapes'] if s['kind']=='circle')<LARGE
    tokens=f.read_payload(_translate(drawing['shapes'],120,-40,2.3))
    reader=f.FlowReader(tokens,vocabulary())
    assert reader.expr()==call('birdone')
    assert reader.i==len(tokens)


def test_explicit_sharing_ligatures_restore_references():
    w=f.FlowWriter(vocabulary());w.keyword('share');w.expr(num(1));w.keyword('equal')
    for _ in range(2):w.keyword('reuse');w.natural(0)
    drawing=f.compile_glyphs(w.glyphs)
    assert f.decode_excerpt(drawing['shapes'])==[assertion(logic('equal',num(1),num(1)))]


def test_pages_recover_across_quote_scope_and_octal_carry():
    from scripts.check_flow_circle import paged_specimen
    assert len(paged_specimen())>4


@pytest.mark.parametrize('damage',['swap','omit','duplicate','truncate'])
def test_page_order_and_completion_are_visible(damage):
    pages=[p['shapes'] for p in f.compile_pages(cases()[8][2],line_atoms=7,rows_per_page=2)]
    if damage=='swap':pages[0],pages[1]=pages[1],pages[0]
    elif damage=='omit':del pages[1]
    elif damage=='duplicate':pages.insert(1,pages[1])
    else:pages.pop()
    with pytest.raises(ValueError):f.decode_pages(pages)
