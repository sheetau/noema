from copy import deepcopy
from itertools import product
import pytest

from scripts.visible_page import (compile_page,decode_page,split_rows,packet,frame,FRAMES,
                                 LayoutReader,vertical_bounds,to_svg,from_svg)
from scripts.visible_syntax import Writer,Reader
from scripts.visible_syntax_geometry import render,recognize
from scripts.visible_lexical_script import _shape_set,_translate
from scripts.balanced_circle_script import line,MIN_GAP,STROKE
from scripts.check_visible_syntax import (integrated_document,vocabulary,doc,assertion,num,logic,
                                        call,quote,quant,variable)
from scripts.check_visible_page import specimens


def syntax(document):
    w=Writer(vocabulary()); w.document(document)
    reader=LayoutReader([_shape_set(g['shapes']) for g in w.glyphs],vocabulary())
    reader.document()
    return w.glyphs,reader


def lay_rows(rows,separation=160.,indents=None):
    if indents is None: indents=[0.]*len(rows)
    shapes=[]
    for i,(row,x) in enumerate(zip(rows,indents)):
        shapes+=_translate(row,x,i*separation)
    return shapes


def at_cuts(glyphs,cuts,paragraphs=(),ordinals=None,finish=True):
    limits=[0,*cuts,len(glyphs)]
    rows=[]
    for i,(a,b) in enumerate(zip(limits,limits[1:])):
        ordinal=i if ordinals is None else ordinals[i]
        rows.append(render(packet(glyphs[a:b],ordinal,paragraph=a in paragraphs,
                                  final=finish and i==len(limits)-2))['shapes'])
    return lay_rows(rows)


def test_standalone_definition_numeric_formula_nested_quote_and_scopes_wrap():
    d=integrated_document()
    for e in specimens():
        assert decode_page(from_svg(e['svg']))==dict(document=d,paragraph_starts=e['paragraphs'])
        assert e['page']['width']<=e['max_width']
    assert len({e['page']['rows'] for e in specimens()})>1


def test_every_legal_and_illegal_cut_of_a_document_is_classified():
    # This small whole document exercises header numbers, a compound name,
    # declaration types, a variable distance and a negative rational.
    from scripts.visible_word_forms import Word,symbol
    name=symbol(Word('compound',('rain','home')),vocabulary())
    definition=dict(kind='definition',name=name,parameters=[dict(name='x',sort='number')],
                    result='number',body=variable('x'))
    d=doc(assertion(logic('equal',dict(kind='call',symbol=name,arguments=[num(-3,2)]),num(-3,2))),
          definitions=(definition,))
    glyphs,trace=syntax(d)
    for cut in range(1,len(glyphs)):
        page=at_cuts(glyphs,[cut])
        if cut in trace.legal_boundaries():
            assert decode_page(page)['document']==d
        else:
            with pytest.raises(ValueError,match='indivisible'): decode_page(page)


def test_two_levels_of_quote_and_quantifier_environments_cross_rows():
    e=quant('forall','x',quant('exists','y',logic('not',logic('equal',variable('x'),variable('y')))))
    d=doc(assertion(logic('equal',quote(quote(e)),quote(quote(e)))))
    glyphs,trace=syntax(d)
    cuts=sorted(trace.legal_boundaries()-{0,len(glyphs)})
    # Many short rows retain the same quotation namespace and variable slots.
    page=at_cuts(glyphs,cuts)
    assert decode_page(page)['document']==d


@pytest.mark.parametrize('width,rail',list(product((1600.,2200.,3200.),(0,2))))
def test_legal_wrapping_and_vertical_placement_preserve_document(width,rail):
    d=integrated_document()
    page=compile_page(d,max_width=width,first_rail=rail,row_gap=100.,paragraph_starts=(0,2))
    assert decode_page(page['shapes'])==dict(document=d,paragraph_starts=[0,2])


def test_translation_scaling_indent_spacing_and_segment_storage_are_layout_only():
    d=integrated_document(); page=compile_page(d,max_width=2400.,paragraph_starts=(1,3))
    rows=split_rows(page['shapes'])
    # Move each normalized row to an independent baseline with ample space.
    flat=[]
    for i,row in enumerate(rows):
        lo,hi=vertical_bounds(row)
        flat+=_translate(row,(i%3)*47.5,i*170.-lo)
    changed=[]
    for s in _translate(flat,93.75,-42.5,1.3):
        if s['kind']=='circle': changed.append(s)
        else:
            a,b=(s['x1'],s['y1']),(s['x2'],s['y2']); m=((a[0]+b[0])/2,(a[1]+b[1])/2)
            changed.extend((line(b,m),line(m,a)))
    assert decode_page(list(reversed(changed)))==dict(document=d,paragraph_starts=[1,3])


@pytest.mark.parametrize('change',['first','middle','last','repeat','swap'])
def test_missing_duplicate_and_reordered_rows_rejected(change):
    rows=split_rows(specimens()[1]['page']['shapes'])
    if change=='first': rows.pop(0)
    elif change=='middle': rows.pop(len(rows)//2)
    elif change=='last': rows.pop()
    elif change=='repeat': rows.insert(2,deepcopy(rows[1]))
    else: rows[1],rows[2]=rows[2],rows[1]
    normalized=[_translate(r,0,-vertical_bounds(r)[0]) for r in rows]
    with pytest.raises(ValueError): decode_page(lay_rows(normalized))


def test_same_row_numbers_moved_out_of_order_are_rejected_even_if_document_parses():
    d=doc(assertion(logic('equal',num(1),num(1))),assertion(logic('equal',num(2),num(2))))
    glyphs,trace=syntax(d); cut=trace.top_statements[1]
    with pytest.raises(ValueError,match='reordered'): decode_page(at_cuts(glyphs,[cut],ordinals=[0,0]))


def test_continuation_is_not_a_final_marker():
    glyphs,_=syntax(integrated_document())
    with pytest.raises(ValueError,match='final-row'): decode_page(at_cuts(glyphs,[],finish=False))


def test_blank_space_does_not_introduce_a_paragraph():
    page=compile_page(integrated_document(),row_gap=800.)
    assert decode_page(page['shapes'])['paragraph_starts']==[]


def test_paragraph_marker_cannot_exit_a_nested_assumption():
    base=assertion(logic('equal',num(1),num(1)))
    d=doc(dict(kind='suppose',condition=base['body'],statements=[base,base]))
    glyphs,trace=syntax(d)
    # Find the inner assert keyword by its literal public glyph signatures.
    w=Writer(vocabulary()); w.keyword('assert')
    pattern=[_shape_set(g['shapes']) for g in w.glyphs]
    stream=[_shape_set(g['shapes']) for g in glyphs]
    inner=next(i for i in range(len(stream)-1) if stream[i:i+2]==pattern)
    assert inner not in trace.top_statements
    with pytest.raises(ValueError,match='inside'): decode_page(at_cuts(glyphs,[inner],paragraphs=[inner]))


def test_paragraph_marker_cannot_start_a_definition_or_quote_body():
    glyphs,trace=syntax(integrated_document())
    illegal=[i for i in sorted(trace.legal_boundaries()) if 0<i<len(glyphs) and i not in trace.top_statements]
    for cut in (illegal[0],illegal[len(illegal)//2],illegal[-1]):
        with pytest.raises(ValueError,match='inside'): decode_page(at_cuts(glyphs,[cut],paragraphs=[cut]))


@pytest.mark.parametrize('change',['cross-line','disconnected','hidden','clipped','scaled-row'])
def test_illegal_geometry_or_hidden_svg_is_rejected(change):
    page=deepcopy(specimens()[1]['page']['shapes'])
    if change=='cross-line':
        rows=split_rows(page); a=next(s for s in rows[0] if s['kind']=='circle'); b=next(s for s in rows[1] if s['kind']=='circle')
        page.append(line((a['x'],a['y']),(b['x'],b['y'])))
    elif change=='disconnected':
        longest=max((s for s in page if s['kind']=='line'),key=lambda s:abs(s['x2']-s['x1']))
        page.remove(longest)
    elif change=='scaled-row':
        rows=split_rows(page); rows[1]=_translate(rows[1],0,0,.9); page=[s for r in rows for s in r]
    else:
        svg=to_svg(page)
        if change=='hidden': svg=svg.replace('<circle ','<circle data-row="0" ',1)
        else:
            import re
            svg=re.sub(r'viewBox="[^"]+"','viewBox="0 0 10 10"',svg)
        with pytest.raises(ValueError): from_svg(svg)
        return
    with pytest.raises(ValueError): decode_page(page)


def test_independent_hand_written_framing_does_not_call_page_compiler(monkeypatch):
    # Build the four public framing rings directly, without frame()/packet().
    from scripts.balanced_circle_script import LARGE,PITCH,nucleus
    d=doc(assertion(logic('equal',num(1),num(1))))
    glyphs,trace=syntax(d); cut=trace.top_statements[0]
    rows=[]
    for i,payload in enumerate((glyphs[:cut],glyphs[cut:])):
        prefix=Writer(vocabulary()); prefix.natural(i)
        rings=[nucleus(0.,PITCH,LARGE,'nested',1),*prefix.glyphs]
        if i==1: rings.append(nucleus(0.,PITCH,LARGE,'nested',5))
        rings+=payload+[nucleus(0.,PITCH,LARGE,'nested',7 if i else 3)]
        rows.append(render(rings)['shapes'])
    import scripts.visible_page as module
    monkeypatch.setattr(module,'compile_page',lambda *a,**k:pytest.fail('Called page compiler'))
    assert decode_page(lay_rows(rows,230.))==dict(document=d,paragraph_starts=[0])


def test_layout_requests_that_cannot_preserve_units_are_rejected():
    d=integrated_document()
    for kwargs in (dict(max_width=250),dict(row_gap=1),dict(paragraph_starts=(2,1)),
                   dict(paragraph_starts=(4,)),dict(paragraph_starts=(True,)),dict(indents=[-1])):
        with pytest.raises(ValueError): compile_page(d,**kwargs)


def test_cli_renders_reads_and_preserves_existing_artifact(tmp_path,capsys):
    import json
    from pathlib import Path
    from noema.constructed import parse
    from scripts.visible_page import main
    source=Path(__file__).resolve().parents[1]/'examples/v016/visible-syntax-document-v1.noema'
    svg=tmp_path/'page.svg'
    assert main(['render',str(source),str(svg),'--width','2400','--paragraph','0','--paragraph','2'])==0
    assert json.loads(capsys.readouterr().out)['rows']>1
    assert main(['decode',str(svg)])==0
    decoded=json.loads(capsys.readouterr().out)
    assert decoded==dict(document=integrated_document(),paragraph_starts=[0,2])
    assert main(['decode',str(svg),'--native'])==0
    assert parse(capsys.readouterr().out)==integrated_document()
    original=svg.read_bytes()
    with pytest.raises(SystemExit): main(['render',str(source),str(svg),'--width','3600'])
    assert svg.read_bytes()==original
