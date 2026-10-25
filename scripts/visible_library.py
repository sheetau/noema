"""Public definition imports for visible documents and pages."""
from noema.constructed_discourse import normalize_document
from scripts.visible_defined_vocabulary import DefinedVocabulary
from scripts.visible_syntax_vocabulary import Vocabulary
from scripts.visible_word_forms import read_symbol
from scripts.visible_sharing import SharedWriter,SharedReader,nodes,MAX_EXPANDED_NODES
from scripts.visible_syntax import Reader
from scripts.visible_syntax_geometry import recognize,render,MAX_GLYPHS,to_svg,from_svg
from scripts.visible_shared_page import SharedLayoutReader,paginate,decode_page as prior_decode_page
from scripts.visible_page import split_rows,FRAMES
from scripts.visible_lexical_script import require,_shape_set


class LibraryWriter(SharedWriter):
    def document(self,document):
        doc=normalize_document(document)
        require(doc['schema_version']=='0.16','Visible grammar requires Noema 0.16')
        require(nodes(doc)<=MAX_EXPANDED_NODES,'Expanded document exceeds node budget')
        self.keyword('document'); self.natural(16); self.natural(self.v.document()['edition'])
        for d in doc['declarations']:
            word=read_symbol(d['name'],self.v)
            if word.kind=='root':
                require(d==self.v.declaration(word.parts[0]),'Declaration differs from the shared public meaning')
                self.keyword('import'); self.name(d['name'])
                continue
            require(d['kind']=='definition','Local names require visible definitions')
            require(word.kind!='proper' or (d['parameters']==[] and d['result']=='individual'),
                    'Proper names designate individuals')
            self.keyword('definition'); self.name(d['name']); self.parameters(d['parameters']); self.type(d['result'])
            self.expr(d['body'],tuple(p['name'] for p in d['parameters']))
        self.end()
        for statement in doc['statements']: self.statement(statement)
        self.end()
        return doc


def vocabulary_for(signatures):
    reader=Reader(signatures,Vocabulary())
    require(reader.keyword()=='document','Missing document header')
    require(reader.natural()==16,'Unsupported Noema edition')
    edition=reader.natural()
    require(edition in (1,2),'Unknown shared vocabulary edition')
    return Vocabulary() if edition==1 else DefinedVocabulary()


def compile_document(document,vocabulary=None,**layout):
    w=LibraryWriter(vocabulary or DefinedVocabulary()); w.document(document)
    return render(w.glyphs,**layout)


def decode_document(shapes,vocabulary=None):
    stream=recognize(shapes)
    return SharedReader(stream,vocabulary or vocabulary_for(stream)).document()


def compile_page(document,vocabulary=None,*,max_width=1800.,paragraph_starts=(),
                 first_rail=0,gap=80.,row_gap=64.,indents=None,automatic=True):
    v=vocabulary or DefinedVocabulary()
    w=LibraryWriter(v,automatic=automatic); w.document(document)
    require(len(w.glyphs)<=MAX_GLYPHS,'Payload glyph budget exceeded')
    trace=SharedLayoutReader([_shape_set(g['shapes']) for g in w.glyphs],v); trace.document()
    return paginate(w.glyphs,trace,v,max_width=max_width,paragraph_starts=paragraph_starts,
                    first_rail=first_rail,gap=gap,row_gap=row_gap,indents=indents)


def decode_page(shapes,vocabulary=None):
    if vocabulary is None:
        # Read enough visible payload for the fixed document header. Native
        # 16 plus known dictionary 1/2 consumes 10/11 glyphs. Full framing and
        # every boundary are validated by the ordinary page decoder below.
        header=[]
        for row in split_rows(shapes):
            stream=recognize(row); reader=Reader(stream,Vocabulary())
            require(reader.take()==FRAMES['start'],'Missing row start')
            reader.natural()
            if reader.peek()==FRAMES['paragraph']: reader.take()
            header.extend(stream[reader.i:-1])
            if len(header)>=12: break
        vocabulary=vocabulary_for(header)
    return prior_decode_page(shapes,vocabulary)


def main(argv=None):
    import argparse,json
    from pathlib import Path
    from noema.constructed import parse,format_graph
    cli=argparse.ArgumentParser(description='Render/read visible Noema with shared definitions.')
    sub=cli.add_subparsers(dest='command',required=True)
    write=sub.add_parser('render'); write.add_argument('source',type=Path); write.add_argument('output',type=Path)
    write.add_argument('--width',type=float,default=1800.); write.add_argument('--paragraph',type=int,action='append',default=[])
    write.add_argument('--public-names',action='store_true',help='Encode ordinary public vocabulary names before rendering.')
    read=sub.add_parser('decode'); read.add_argument('source',type=Path); read.add_argument('--native',action='store_true')
    read.add_argument('--public-names',action='store_true',help='Print ordinary public names for dictionary 2 words.')
    args=cli.parse_args(argv)
    try:
        source=args.source.read_text(encoding='utf-8')
        if args.command=='render':
            doc=parse(source)
            if args.public_names: doc=DefinedVocabulary().encode(doc)
            page=compile_page(doc,max_width=args.width,paragraph_starts=args.paragraph)
            svg=to_svg(page['shapes'])
            require(not args.output.exists() or args.output.read_text(encoding='utf-8')==svg,
                    'Output exists with different content; select a new output path')
            args.output.parent.mkdir(parents=True,exist_ok=True)
            if not args.output.exists(): args.output.write_text(svg,encoding='utf-8',newline='\n')
            print(json.dumps(dict(output=str(args.output),rows=page['rows'])))
        else:
            result=decode_page(from_svg(source))
            if args.public_names: result['document']=DefinedVocabulary().decode_names(result['document'])
            print(format_graph(result['document']) if args.native else json.dumps(result,ensure_ascii=False,indent=2))
    except (ValueError,OSError) as error: cli.error(str(error))
    return 0


if __name__=='__main__': raise SystemExit(main())
