"""Visible row framing and paragraph positions for Noema circle documents."""
import math

from scripts.visible_lexical_script import _shape_set, _translate, require
from scripts.visible_syntax_geometry import clean, render, recognize, to_svg, from_svg, MAX_GLYPHS
from scripts.visible_syntax import Writer, Reader
from scripts.visible_syntax_vocabulary import Vocabulary
from scripts.balanced_circle_script import LARGE, PITCH, MIN_GAP, STROKE, EPS, nucleus

MAX_ROWS = 128
FRAME_DIRECTIONS = {'start':1, 'continue':3, 'paragraph':5, 'finish':7}


def frame(kind):
    return nucleus(0.,PITCH,LARGE,'nested',FRAME_DIRECTIONS[kind])


FRAMES = {kind:_shape_set(frame(kind)['shapes']) for kind in FRAME_DIRECTIONS}


class LayoutReader(Reader):
    """Derive unbreakable spans and top-level positions from visible syntax."""
    def __init__(self, signatures, vocabulary):
        super().__init__(signatures,vocabulary)
        self.spans, self.top_statements = [],[]

    def _record(self, method):
        start = self.i
        result = method()
        self.spans.append((start,self.i))
        return result

    def keyword(self): return self._record(super().keyword)
    def natural(self): return self._record(super().natural)
    def word(self): return self._record(super().word)

    def statement(self, depth=0):
        if depth==0: self.top_statements.append(self.i)
        return super().statement(depth)

    def legal_boundaries(self):
        blocked = {i for start,end in self.spans for i in range(start+1,end)}
        return set(range(len(self.tokens)+1))-blocked


def packet(payload, ordinal, *, paragraph=False, final=False, vocabulary=None):
    require(payload, 'Empty row payload')
    w=Writer(vocabulary or Vocabulary())
    w.glyphs.append(frame('start'))
    w.natural(ordinal)
    if paragraph: w.glyphs.append(frame('paragraph'))
    w.glyphs.extend(payload)
    w.glyphs.append(frame('finish' if final else 'continue'))
    return w.glyphs


def compile_page(document, vocabulary=None, *, max_width=1800., paragraph_starts=(),
                 first_rail=0, gap=80., row_gap=64., indents=None):
    v=vocabulary or Vocabulary()
    w=Writer(v); w.document(document)
    require(len(w.glyphs)<=MAX_GLYPHS,'Payload glyph budget exceeded')
    trace=LayoutReader([_shape_set(g['shapes']) for g in w.glyphs],v)
    trace.document()
    require(type(max_width) in (int,float) and math.isfinite(max_width) and max_width>0,
            'Invalid page width')
    require(type(row_gap) in (int,float) and math.isfinite(row_gap) and row_gap>=2*MIN_GAP+STROKE,
            'Insufficient row separation')
    require(isinstance(paragraph_starts,(tuple,list)) and all(type(i) is int and
            0<=i<len(trace.top_statements) for i in paragraph_starts)
            and list(paragraph_starts)==sorted(set(paragraph_starts)), 'Invalid paragraph starts')
    paragraph_offsets={trace.top_statements[i] for i in paragraph_starts}
    boundaries=sorted(trace.legal_boundaries())
    rows,offset= [],0
    while offset<len(w.glyphs):
        require(len(rows)<MAX_ROWS,'Row count exceeds budget')
        paragraph=offset in paragraph_offsets
        ceiling=min((i for i in paragraph_offsets if i>offset),default=len(w.glyphs))
        best=None
        for end in (i for i in boundaries if offset<i<=ceiling):
            glyphs=packet(w.glyphs[offset:end],len(rows),paragraph=paragraph,
                          final=end==len(w.glyphs),vocabulary=v)
            drawing=render(glyphs,first_rail=first_rail,gap=gap)
            if drawing['width']>max_width: break
            best=end,drawing
        require(best is not None,'Page width cannot contain an indivisible syntax unit')
        offset,drawing=best
        rows.append(drawing)
    if indents is None: indents=[0.]*len(rows)
    require(isinstance(indents,(tuple,list)) and len(indents)==len(rows) and all(
        type(x) in (int,float) and math.isfinite(x) and x>=0 for x in indents),'Invalid row indents')
    shapes,bottom=[],None
    for drawing,indent in zip(rows,indents):
        lo,hi=vertical_bounds(drawing['shapes'])
        shift=0. if bottom is None else bottom+row_gap-lo
        shapes.extend(_translate(drawing['shapes'],indent,shift))
        bottom=hi+shift
    clean(shapes)
    return dict(shapes=shapes,width=max(r['width']+i for r,i in zip(rows,indents)),
                height=vertical_bounds(shapes)[1]-vertical_bounds(shapes)[0],rows=len(rows))


def interval(shape):
    if shape['kind']=='circle': return shape['y']-shape['r'],shape['y']+shape['r']
    return min(shape['y1'],shape['y2']),max(shape['y1'],shape['y2'])


def vertical_bounds(shapes):
    spans=[interval(s) for s in shapes]
    return min(a for a,b in spans),max(b for a,b in spans)


def split_rows(shapes):
    visible=clean(shapes)
    circles=[s for s in visible if s['kind']=='circle']
    require(circles,'No visible circles')
    scale=LARGE/max(c['r'] for c in circles)
    visible=_translate(visible,0.,0.,scale)
    ordered=sorted(visible,key=lambda s:interval(s)[0])
    rows,bottom=[],None
    for shape in ordered:
        low,high=interval(shape)
        if bottom is None or low>bottom+EPS:
            if bottom is not None:
                require(low-bottom>=2*MIN_GAP+STROKE-EPS,'Insufficient visible row separation')
            rows.append([])
        rows[-1].append(shape)
        bottom=high if bottom is None else max(bottom,high)
    require(len(rows)<=MAX_ROWS,'Row count exceeds budget')
    for row in rows:
        large=max((c['r'] for c in row if c['kind']=='circle'),default=0.)
        require(abs(large-LARGE)<EPS,'Rows must share one geometric scale')
    return rows


def decode_page(shapes, vocabulary=None):
    v=vocabulary or Vocabulary()
    rows=split_rows(shapes)
    payload,boundaries,paragraph_offsets=[],[],[]
    for ordinal,row in enumerate(rows):
        tokens=recognize(row)
        reader=Reader(tokens,v)
        require(reader.take()==FRAMES['start'],'Missing row start marker')
        require(reader.natural()==ordinal,'Missing, repeated or reordered row')
        if reader.peek()==FRAMES['paragraph']:
            reader.take(); paragraph_offsets.append(len(payload))
        expected='finish' if ordinal==len(rows)-1 else 'continue'
        require(tokens[-1]==FRAMES[expected],'Incorrect continuation or final-row marker')
        part=tokens[reader.i:-1]
        require(part and not any(t in FRAMES.values() for t in part),'Empty or misplaced row framing')
        if payload: boundaries.append(len(payload))
        payload.extend(part)
    require(len(payload)<=MAX_GLYPHS,'Payload glyph budget exceeded')
    trace=LayoutReader(payload,v)
    document=trace.document()
    require(set(boundaries)<=trace.legal_boundaries(),'Row divides an indivisible syntax unit')
    require(all(i in trace.top_statements for i in paragraph_offsets),'Paragraph starts inside a definition or scope')
    return dict(document=document,paragraph_starts=[trace.top_statements.index(i) for i in paragraph_offsets])


def main(argv=None):
    import argparse
    import json
    from pathlib import Path
    from noema.constructed import parse,format_graph
    cli=argparse.ArgumentParser(description='Render or read a visibly framed Noema page.')
    sub=cli.add_subparsers(dest='command',required=True)
    write=sub.add_parser('render')
    write.add_argument('source',type=Path)
    write.add_argument('output',type=Path)
    write.add_argument('--width',type=float,default=1800.)
    write.add_argument('--paragraph',type=int,action='append',default=[])
    read=sub.add_parser('decode')
    read.add_argument('source',type=Path)
    read.add_argument('--native',action='store_true',help='Print native Noema; paragraph positions are omitted.')
    args=cli.parse_args(argv)
    try:
        source=args.source.read_text(encoding='utf-8')
        if args.command=='render':
            document=parse(source)
            page=compile_page(document,max_width=args.width,paragraph_starts=args.paragraph)
            text=to_svg(page['shapes'])
            require(not args.output.exists() or args.output.read_text(encoding='utf-8')==text,
                    'Output exists with different content; select a new output path')
            args.output.parent.mkdir(parents=True,exist_ok=True)
            if not args.output.exists(): args.output.write_text(text,encoding='utf-8',newline='\n')
            print(json.dumps(dict(output=str(args.output),rows=page['rows'],visible_primitives=len(page['shapes']))))
        else:
            result=decode_page(from_svg(source))
            print(format_graph(result['document']) if args.native else json.dumps(result,ensure_ascii=False,indent=2))
    except (ValueError,OSError) as error:
        cli.error(str(error))
    return 0


if __name__=='__main__':
    raise SystemExit(main())
