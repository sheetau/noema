"""Page adapter for the explicit sharing grammar; v1 evidence stays unchanged."""
import math

from scripts.visible_sharing import SharedWriter,SharedReader
from scripts.visible_page import LayoutReader,packet,split_rows,vertical_bounds,FRAMES,MAX_ROWS
from scripts.visible_syntax import Reader
from scripts.visible_syntax_vocabulary import Vocabulary
from scripts.visible_syntax_geometry import clean,render,recognize,to_svg,from_svg,MAX_GLYPHS
from scripts.visible_lexical_script import require,_shape_set,_translate
from scripts.balanced_circle_script import MIN_GAP,STROKE


class SharedLayoutReader(LayoutReader,SharedReader):
    pass


def compile_page(document,vocabulary=None,*,max_width=1800.,paragraph_starts=(),
                 first_rail=0,gap=80.,row_gap=64.,indents=None,automatic=True):
    v=vocabulary or Vocabulary()
    w=SharedWriter(v,automatic=automatic); w.document(document)
    require(len(w.glyphs)<=MAX_GLYPHS,'Payload glyph budget exceeded')
    trace=SharedLayoutReader([_shape_set(g['shapes']) for g in w.glyphs],v)
    trace.document()
    return paginate(w.glyphs,trace,v,max_width=max_width,paragraph_starts=paragraph_starts,
                    first_rail=first_rail,gap=gap,row_gap=row_gap,indents=indents)


def paginate(glyphs,trace,v,*,max_width,paragraph_starts,first_rail,gap,row_gap,indents):
    # Preserve v1 row framing, break rules and geometry. The grammar reader is
    # explicit here so extending it does not patch a pinned historical module.
    require(type(max_width) in (int,float) and math.isfinite(max_width) and max_width>0,'Invalid page width')
    require(type(row_gap) in (int,float) and math.isfinite(row_gap) and row_gap>=2*MIN_GAP+STROKE,
            'Insufficient row separation')
    require(isinstance(paragraph_starts,(tuple,list)) and all(type(i) is int and
            0<=i<len(trace.top_statements) for i in paragraph_starts)
            and list(paragraph_starts)==sorted(set(paragraph_starts)),'Invalid paragraph starts')
    paragraphs={trace.top_statements[i] for i in paragraph_starts}
    boundaries=sorted(trace.legal_boundaries())
    rows,offset=[],0
    while offset<len(glyphs):
        require(len(rows)<MAX_ROWS,'Row count exceeds budget')
        ceiling=min((i for i in paragraphs if i>offset),default=len(glyphs))
        best=None
        for end in (i for i in boundaries if offset<i<=ceiling):
            row=packet(glyphs[offset:end],len(rows),paragraph=offset in paragraphs,final=end==len(glyphs),vocabulary=v)
            drawing=render(row,first_rail=first_rail,gap=gap)
            if drawing['width']>max_width: break
            best=end,drawing
        require(best is not None,'Page width cannot contain an indivisible syntax unit')
        offset,drawing=best; rows.append(drawing)
    if indents is None: indents=[0.]*len(rows)
    require(isinstance(indents,(tuple,list)) and len(indents)==len(rows) and all(
        type(x) in (int,float) and math.isfinite(x) and x>=0 for x in indents),'Invalid row indents')
    shapes,bottom=[],None
    for drawing,indent in zip(rows,indents):
        lo,hi=vertical_bounds(drawing['shapes'])
        shift=0. if bottom is None else bottom+row_gap-lo
        shapes.extend(_translate(drawing['shapes'],indent,shift)); bottom=hi+shift
    clean(shapes)
    lo,hi=vertical_bounds(shapes)
    return dict(shapes=shapes,width=max(r['width']+i for r,i in zip(rows,indents)),height=hi-lo,rows=len(rows))


def decode_page(shapes,vocabulary=None):
    v=vocabulary or Vocabulary()
    rows=split_rows(shapes)
    payload,boundaries,paragraphs=[],[],[]
    for ordinal,row in enumerate(rows):
        tokens=recognize(row); reader=Reader(tokens,v)
        require(reader.take()==FRAMES['start'],'Missing row start marker')
        require(reader.natural()==ordinal,'Missing, repeated or reordered row')
        if reader.peek()==FRAMES['paragraph']:
            reader.take(); paragraphs.append(len(payload))
        require(tokens[-1]==FRAMES['finish' if ordinal==len(rows)-1 else 'continue'],
                'Incorrect continuation or final-row marker')
        part=tokens[reader.i:-1]
        require(part and not any(t in FRAMES.values() for t in part),'Empty or misplaced row framing')
        if payload: boundaries.append(len(payload))
        payload.extend(part)
    require(len(payload)<=MAX_GLYPHS,'Payload glyph budget exceeded')
    trace=SharedLayoutReader(payload,v); document=trace.document()
    require(set(boundaries)<=trace.legal_boundaries(),'Row divides an indivisible syntax unit')
    require(all(i in trace.top_statements for i in paragraphs),'Paragraph starts inside a definition or scope')
    return dict(document=document,paragraph_starts=[trace.top_statements.index(i) for i in paragraphs])


def main(argv=None):
    import argparse
    import json
    from pathlib import Path
    from noema.constructed import parse,format_graph
    cli=argparse.ArgumentParser(description='Render and decode Noema pages with explicit sharing.')
    sub=cli.add_subparsers(dest='command',required=True)
    write=sub.add_parser('render'); write.add_argument('source',type=Path); write.add_argument('output',type=Path)
    write.add_argument('--width',type=float,default=1800.)
    write.add_argument('--paragraph',type=int,action='append',default=[])
    write.add_argument('--no-sharing',action='store_true')
    read=sub.add_parser('decode'); read.add_argument('source',type=Path); read.add_argument('--native',action='store_true')
    args=cli.parse_args(argv)
    try:
        source=args.source.read_text(encoding='utf-8')
        if args.command=='render':
            page=compile_page(parse(source),max_width=args.width,paragraph_starts=args.paragraph,
                              automatic=not args.no_sharing)
            svg=to_svg(page['shapes'])
            require(not args.output.exists() or args.output.read_text(encoding='utf-8')==svg,
                    'Output exists with different content; select a new output path')
            args.output.parent.mkdir(parents=True,exist_ok=True)
            if not args.output.exists(): args.output.write_text(svg,encoding='utf-8',newline='\n')
            print(json.dumps(dict(output=str(args.output),rows=page['rows'],visible_primitives=len(page['shapes']))))
        else:
            result=decode_page(from_svg(source))
            print(format_graph(result['document']) if args.native else json.dumps(result,ensure_ascii=False,indent=2))
    except (ValueError,OSError) as error: cli.error(str(error))
    return 0


if __name__=='__main__': raise SystemExit(main())
