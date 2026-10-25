"""Edition-twelve book transport, with unchanged page and document limits."""
from scripts.visible_senses_vocabulary import SensesVocabulary
from scripts.visible_senses_page import page_vocabulary
from scripts.visible_evidence_book import MAX_PAGES,compile_book as previous_compile,decode_book as previous_decode
from scripts.visible_syntax_geometry import to_svg,from_svg
from scripts.visible_lexical_script import require


def compile_book(document,vocabulary=None,**layout):
    return previous_compile(document,vocabulary or SensesVocabulary(),**layout)


def decode_book(pages,vocabulary=None,*,public_names=False):
    require(type(pages) is list and 0<len(pages)<=MAX_PAGES,'Invalid book page count')
    return previous_decode(pages,vocabulary or page_vocabulary(pages[0]),public_names=public_names)


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
            document=parse(args.source.read_text(encoding='utf-8'));vocab=SensesVocabulary()
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
