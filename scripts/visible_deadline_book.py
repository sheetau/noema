"""Bounded multi-page documents, carrying visible row continuity across pages.

Single-page adapters and their budgets are unchanged. This transport permits
at most eight pages while retaining the 8192-node document expansion limit.
"""
import math
from scripts.visible_deadline_page import PublicWriter,vocabulary_for
from scripts.visible_deadline_vocabulary import DeadlineVocabulary
from scripts.visible_public_page import PublicLayoutReader
from scripts.visible_page import packet,split_rows,vertical_bounds,FRAMES,MAX_ROWS
from scripts.visible_syntax import Reader
from scripts.visible_syntax_vocabulary import Vocabulary
from scripts.visible_syntax_geometry import render,recognize,clean,MAX_GLYPHS,MAX_SHAPES,to_svg,from_svg
from scripts.visible_lexical_script import require,_shape_set,_translate
from scripts.balanced_circle_script import MIN_GAP,STROKE

MAX_PAGES=8

def compile_book(document,vocabulary=None,*,max_width=4800.,row_gap=64.):
    require(type(max_width) in (int,float) and math.isfinite(max_width) and max_width>0,'Invalid page width')
    require(type(row_gap) in (int,float) and math.isfinite(row_gap) and row_gap>=2*MIN_GAP+STROKE,'Insufficient row separation')
    vocab=vocabulary or DeadlineVocabulary();writer=PublicWriter(vocab);writer.document(document)
    glyphs=writer.glyphs
    require(len(glyphs)<=MAX_PAGES*MAX_GLYPHS,'Book payload exceeds budget')
    trace=PublicLayoutReader([_shape_set(g['shapes']) for g in glyphs],vocab);trace.document()
    boundaries=sorted(trace.legal_boundaries());rows=[];offset=0
    while offset<len(glyphs):
        require(len(rows)<MAX_ROWS,'Book row count exceeds budget')
        best=None
        for end in (i for i in boundaries if offset<i<=min(len(glyphs),offset+MAX_GLYPHS-32)):
            row=packet(glyphs[offset:end],len(rows),paragraph=False,final=end==len(glyphs),vocabulary=vocab)
            drawing=render(row)
            if drawing['width']>max_width:break
            best=end,drawing
        require(best is not None,'Page width cannot contain an indivisible syntax unit')
        end,drawing=best;rows.append((drawing,end-offset));offset=end
    pages=[];shapes=[];count=0;row_count=0;bottom=None
    def flush():
        nonlocal shapes,count,row_count,bottom
        require(len(pages)<MAX_PAGES,'Book page count exceeds budget')
        clean(shapes);pages.append(dict(shapes=shapes,rows=row_count,glyphs=count))
        shapes=[];count=0;row_count=0;bottom=None
    for drawing,n in rows:
        if shapes and (len(shapes)+len(drawing['shapes'])>MAX_SHAPES or count+n>MAX_GLYPHS):flush()
        require(len(drawing['shapes'])<=MAX_SHAPES and n<=MAX_GLYPHS,'Row exceeds page budget')
        low,high=vertical_bounds(drawing['shapes']);shift=0. if bottom is None else bottom+row_gap-low
        shapes.extend(_translate(drawing['shapes'],0.,shift));bottom=high+shift;count+=n;row_count+=1
    if shapes:flush()
    return pages

def decode_book(pages,vocabulary=None,*,public_names=False):
    require(type(pages) is list and 0<len(pages)<=MAX_PAGES,'Invalid book page count')
    payload=[];boundaries=[];ordinal=0
    for page_index,shapes in enumerate(pages):
        rows=split_rows(shapes);page_count=0
        for row_index,row in enumerate(rows):
            require(ordinal<MAX_ROWS,'Book row count exceeds budget')
            tokens=recognize(row);reader=Reader(tokens,Vocabulary())
            require(reader.take()==FRAMES['start'],'Missing row start marker')
            require(reader.natural()==ordinal,'Missing, repeated or reordered book row')
            ordinal+=1
            final=page_index==len(pages)-1 and row_index==len(rows)-1
            require(tokens[-1]==FRAMES['finish' if final else 'continue'],'Incorrect book continuation or final marker')
            part=tokens[reader.i:-1]
            require(part and not any(t in FRAMES.values() for t in part),'Empty or misplaced book framing')
            if payload:boundaries.append(len(payload))
            page_count+=len(part);require(page_count<=MAX_GLYPHS,'Page payload exceeds budget')
            payload.extend(part)
    require(len(payload)<=MAX_PAGES*MAX_GLYPHS,'Book payload exceeds budget')
    vocab=vocabulary or vocabulary_for(payload);trace=PublicLayoutReader(payload,vocab);document=trace.document()
    require(set(boundaries)<=trace.legal_boundaries(),'Book row divides an indivisible syntax unit')
    if public_names:
        if hasattr(vocab,'decode_names'):document=vocab.decode_names(document)
        else:
            from scripts.visible_word_forms import Word,symbol
            from scripts.shared_modality import renamed
            from noema.constructed_discourse import normalize_document
            document=normalize_document(renamed(document,{symbol(Word('root',(n,)),vocab):n for n in vocab.document()['entries']}))
    return dict(document=document,pages=len(pages),rows=ordinal)

def main(argv=None):
    import argparse,json
    from pathlib import Path
    from noema.constructed import parse,format_graph
    cli=argparse.ArgumentParser(description='Read/write a bounded Noema document across visibly ordered pages.')
    sub=cli.add_subparsers(dest='command',required=True)
    write=sub.add_parser('render');write.add_argument('source',type=Path);write.add_argument('directory',type=Path)
    write.add_argument('--width',type=float,default=4800.);write.add_argument('--public-names',action='store_true')
    read=sub.add_parser('decode');read.add_argument('sources',type=Path,nargs='+')
    read.add_argument('--native',action='store_true');read.add_argument('--public-names',action='store_true')
    args=cli.parse_args(argv)
    try:
        if args.command=='render':
            document=parse(args.source.read_text(encoding='utf-8'));vocab=DeadlineVocabulary()
            if args.public_names:document=vocab.encode(document)
            pages=compile_book(document,vocab,max_width=args.width)
            outputs=[(args.directory/('page-'+str(i+1)+'.svg'),to_svg(p['shapes'])) for i,p in enumerate(pages)]
            require(not args.directory.exists() or not any(args.directory.iterdir()),'Book output directory must be new or empty')
            args.directory.mkdir(parents=True,exist_ok=True)
            for path,svg in outputs:path.write_text(svg,encoding='utf-8',newline='\n')
            print(json.dumps(dict(pages=[str(p) for p,s in outputs])))
        else:
            result=decode_book([from_svg(p.read_text(encoding='utf-8')) for p in args.sources],public_names=args.public_names)
            print(format_graph(result['document']) if args.native else json.dumps(result,ensure_ascii=False,indent=2))
    except (ValueError,OSError) as error:cli.error(str(error))
    return 0

if __name__=='__main__':raise SystemExit(main())
