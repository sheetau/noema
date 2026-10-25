"""Visible edition-seven entry point, retaining original decoders and limits."""
from scripts.visible_generality_vocabulary import GeneralityVocabulary
from scripts.visible_public_page import PublicWriter,PublicReader
from scripts import visible_selection_page as previous
from scripts.visible_syntax import Reader
from scripts.visible_syntax_vocabulary import Vocabulary
from scripts.visible_page import split_rows,FRAMES
from scripts.visible_syntax_geometry import recognize,to_svg,from_svg,MAX_GLYPHS
from scripts.visible_lexical_script import require


def vocabulary_for(tokens):
    r=Reader(tokens,Vocabulary())
    require(r.keyword()=='document','Missing document header')
    require(r.natural()==16,'Unsupported Noema edition')
    edition=r.natural()
    return GeneralityVocabulary() if edition==7 else previous.vocabulary_for(tokens)


def compile_document(document,vocabulary=None,**layout):
    return previous.compile_document(document,vocabulary or GeneralityVocabulary(),**layout)


def decode_document(shapes,vocabulary=None):
    tokens=recognize(shapes)
    return PublicReader(tokens,vocabulary or vocabulary_for(tokens)).document()


def compile_page(document,vocabulary=None,**layout):
    return previous.compile_page(document,vocabulary or GeneralityVocabulary(),**layout)


def page_vocabulary(shapes):
    # First collect the header even if its separate fields span multiple rows.
    # The unchanged page decoder then validates all framing, breaks and syntax.
    payload=[]
    for ordinal,row in enumerate(split_rows(shapes)):
        tokens=recognize(row);r=Reader(tokens,Vocabulary())
        require(r.take()==FRAMES['start'],'Missing row start marker')
        require(r.natural()==ordinal,'Missing, repeated or reordered row')
        if r.peek()==FRAMES['paragraph']:r.take()
        payload.extend(tokens[r.i:-1])
        require(len(payload)<=MAX_GLYPHS,'Payload glyph budget exceeded')
    return vocabulary_for(payload)


def decode_page(shapes,vocabulary=None,*,public_names=False):
    return previous.decode_page(shapes,vocabulary or page_vocabulary(shapes),public_names=public_names)


def main(argv=None):
    import argparse,json
    from pathlib import Path
    from noema.constructed import parse,format_graph
    cli=argparse.ArgumentParser(description='Read/write Noema pages with public vocabulary editions 1–7.')
    sub=cli.add_subparsers(dest='command',required=True)
    write=sub.add_parser('render');write.add_argument('source',type=Path);write.add_argument('output',type=Path)
    write.add_argument('--width',type=float,default=1800.);write.add_argument('--paragraph',type=int,action='append',default=[])
    write.add_argument('--public-names',action='store_true')
    read=sub.add_parser('decode');read.add_argument('source',type=Path);read.add_argument('--native',action='store_true')
    read.add_argument('--public-names',action='store_true')
    args=cli.parse_args(argv)
    try:
        source=args.source.read_text(encoding='utf-8')
        if args.command=='render':
            document=parse(source)
            if args.public_names:document=GeneralityVocabulary().encode(document)
            page=compile_page(document,max_width=args.width,paragraph_starts=args.paragraph);svg=to_svg(page['shapes'])
            require(not args.output.exists() or args.output.read_text(encoding='utf-8')==svg,
                    'Output exists with different content; select a new output path')
            args.output.parent.mkdir(parents=True,exist_ok=True)
            if not args.output.exists():args.output.write_text(svg,encoding='utf-8',newline='\n')
            print(json.dumps(dict(output=str(args.output),rows=page['rows'])))
        else:
            result=decode_page(from_svg(source),public_names=args.public_names)
            print(format_graph(result['document']) if args.native else json.dumps(result,ensure_ascii=False,indent=2))
    except (ValueError,OSError) as error:cli.error(str(error))
    return 0


if __name__=='__main__':raise SystemExit(main())
