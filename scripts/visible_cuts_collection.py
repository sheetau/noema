"""Edition-thirteen collection entry point; prior entry points are preserved."""
from scripts.visible_cuts_vocabulary import CutsVocabulary
from scripts.visible_collection import compile_collection as _compile, decode_collection as _decode, iter_collection_volumes


def compile_collection(document,label,vocabulary=None,**options):
    return _compile(document,label,vocabulary or CutsVocabulary(),**options)


def decode_collection(pages,vocabulary=None,**options):
    return _decode(pages,vocabulary or CutsVocabulary(),**options)


def main(argv=None):
    import argparse
    from pathlib import Path
    from noema.constructed import parse,format_graph
    from scripts.visible_word_forms import Word
    from scripts.visible_syntax_geometry import to_svg,from_svg
    from scripts.visible_lexical_script import require
    cli=argparse.ArgumentParser(description=__doc__);sub=cli.add_subparsers(dest='command',required=True)
    w=sub.add_parser('render');w.add_argument('source',type=Path);w.add_argument('directory',type=Path)
    w.add_argument('--label',nargs='+',required=True);w.add_argument('--public-names',action='store_true')
    d=sub.add_parser('decode');d.add_argument('sources',type=Path,nargs='+');d.add_argument('--public-names',action='store_true')
    args=cli.parse_args(argv);v= CutsVocabulary()
    try:
        if args.command=='render':
            doc=parse(args.source.read_text(encoding='utf-8'))
            if args.public_names:doc=v.encode(doc)
            require(not args.directory.exists() or not any(args.directory.iterdir()),'Output directory must be new or empty')
            args.directory.mkdir(parents=True,exist_ok=True);count=0
            for volume in iter_collection_volumes(doc,Word('proper',tuple(args.label)),v):
                for page in volume['pages']:
                    count+=1
                    (args.directory/('page-'+str(count).zfill(5)+'.svg')).write_text(to_svg(page['shapes']),encoding='utf-8',newline='\n')
            print('Saved',count,'pages')
        else:
            result=decode_collection((from_svg(p.read_text(encoding='utf-8')) for p in args.sources),v,public_names=args.public_names)
            print(format_graph(result['document']))
    except (ValueError,OSError) as error:cli.error(str(error))
    return 0


if __name__=='__main__':raise SystemExit(main())
