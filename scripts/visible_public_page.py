"""Versioned visible imports for both root and shared compound names."""
from noema.constructed_discourse import normalize_document
from scripts.visible_compound_vocabulary import CompoundVocabulary
from scripts.visible_defined_vocabulary import DefinedVocabulary
from scripts.visible_syntax_vocabulary import Vocabulary
from scripts.visible_word_forms import Word,symbol,read_symbol
from scripts.shared_modality import renamed
from scripts.visible_sharing import SharedWriter,SharedReader,nodes,MAX_EXPANDED_NODES
from scripts.visible_syntax import Reader,END
from scripts.visible_syntax_geometry import render,recognize,to_svg,from_svg,MAX_GLYPHS
from scripts.visible_shared_page import paginate
from scripts.visible_page import LayoutReader,split_rows,FRAMES
from scripts.visible_lexical_script import require,_shape_set


def shared_name(vocabulary,word):
    if hasattr(vocabulary,'name_for'):return vocabulary.name_for(word)
    return word.parts[0] if word.kind=='root' else None


class PublicWriter(SharedWriter):
    def document(self,document):
        doc=normalize_document(document)
        require(doc['schema_version']=='0.16','Visible grammar requires Noema 0.16')
        require(nodes(doc)<=MAX_EXPANDED_NODES,'Expanded document exceeds node budget')
        self.keyword('document');self.natural(16);self.natural(self.v.document()['edition'])
        for d in doc['declarations']:
            word=read_symbol(d['name'],self.v);name=shared_name(self.v,word)
            if name is not None:
                require(d==self.v.declaration(name),'Declaration differs from the shared public meaning')
                self.keyword('import');self.name(d['name']);continue
            require(d['kind']=='definition' and word.kind!='root','Local names require visible definitions')
            require(word.kind!='proper' or (d['parameters']==[] and d['result']=='individual'),
                    'Proper names designate individuals')
            self.keyword('definition');self.name(d['name']);self.parameters(d['parameters']);self.type(d['result'])
            self.expr(d['body'],tuple(p['name'] for p in d['parameters']))
        self.end()
        for s in doc['statements']:self.statement(s)
        self.end()
        return doc


class PublicReader(SharedReader):
    def document(self):
        require(self.keyword()=='document','Missing visible document header')
        require(self.natural()==16,'Unsupported Noema edition')
        require(self.natural()==self.v.document()['edition'],'Unknown shared vocabulary edition')
        declarations,statements=[],[]
        while self.peek()!=END:
            k,word=self.keyword(),self.word();name=shared_name(self.v,word)
            if k=='import':
                require(name is not None,'Unknown shared word import')
                declarations.append(self.v.declaration(name))
            else:
                require(k=='definition' and word.kind!='root','Expected definition or import')
                require(name is None,'Local definition shadows a shared public word')
                self.serial=0;parameters=self.parameters();result=self.type()
                require(word.kind!='proper' or (parameters==[] and result=='individual'),
                        'Proper names designate individuals')
                body=self.expr(tuple(p['name'] for p in parameters))
                declarations.append(dict(kind='definition',name=symbol(word,self.v),parameters=parameters,result=result,body=body))
        self.end()
        while self.peek()!=END:statements.append(self.statement())
        self.end()
        require(self.i==len(self.tokens),'Extra visible syntax after document')
        document=normalize_document(dict(schema_version='0.16',lexicon_version='0.16',declarations=declarations,statements=statements))
        require(nodes(document)<=MAX_EXPANDED_NODES,'Expanded document exceeds node budget')
        return document


class PublicLayoutReader(LayoutReader,PublicReader):
    pass


def vocabulary_for(signatures):
    r=Reader(signatures,Vocabulary())
    require(r.keyword()=='document','Missing document header')
    require(r.natural()==16,'Unsupported Noema edition')
    edition=r.natural();constructors={1:Vocabulary,2:DefinedVocabulary,3:CompoundVocabulary}
    require(edition in constructors,'Unknown shared vocabulary edition')
    return constructors[edition]()


def compile_document(document,vocabulary=None,**layout):
    w=PublicWriter(vocabulary or CompoundVocabulary());w.document(document)
    return render(w.glyphs,**layout)


def decode_document(shapes,vocabulary=None):
    stream=recognize(shapes)
    return PublicReader(stream,vocabulary or vocabulary_for(stream)).document()


def compile_page(document,vocabulary=None,*,max_width=1800.,paragraph_starts=(),
                 first_rail=0,gap=80.,row_gap=64.,indents=None,automatic=True):
    v=vocabulary or CompoundVocabulary();w=PublicWriter(v,automatic=automatic);w.document(document)
    require(len(w.glyphs)<=MAX_GLYPHS,'Payload glyph budget exceeded')
    trace=PublicLayoutReader([_shape_set(g['shapes']) for g in w.glyphs],v);trace.document()
    return paginate(w.glyphs,trace,v,max_width=max_width,paragraph_starts=paragraph_starts,
                    first_rail=first_rail,gap=gap,row_gap=row_gap,indents=indents)


def decode_page(shapes,vocabulary=None,*,public_names=False):
    rows=split_rows(shapes)
    payload,boundaries,paragraphs=[],[],[]
    # Framing and numerals have the same grammar in all three editions.
    for ordinal,row in enumerate(rows):
        tokens=recognize(row);r=Reader(tokens,Vocabulary())
        require(r.take()==FRAMES['start'],'Missing row start marker')
        require(r.natural()==ordinal,'Missing, repeated or reordered row')
        if r.peek()==FRAMES['paragraph']:r.take();paragraphs.append(len(payload))
        require(tokens[-1]==FRAMES['finish' if ordinal==len(rows)-1 else 'continue'],'Incorrect continuation or final-row marker')
        part=tokens[r.i:-1]
        require(part and not any(t in FRAMES.values() for t in part),'Empty or misplaced row framing')
        if payload:boundaries.append(len(payload))
        payload.extend(part)
    require(len(payload)<=MAX_GLYPHS,'Payload glyph budget exceeded')
    v=vocabulary or vocabulary_for(payload);trace=PublicLayoutReader(payload,v);document=trace.document()
    require(set(boundaries)<=trace.legal_boundaries(),'Row divides an indivisible syntax unit')
    require(all(i in trace.top_statements for i in paragraphs),'Paragraph starts inside a definition or scope')
    if public_names:
        if hasattr(v,'decode_names'):document=v.decode_names(document)
        else:document=normalize_document(renamed(document,{symbol(Word('root',(n,)),v):n for n in v.document()['entries']}))
    return dict(document=document,paragraph_starts=[trace.top_statements.index(i) for i in paragraphs])


def main(argv=None):
    import argparse,json
    from pathlib import Path
    from noema.constructed import parse,format_graph
    cli=argparse.ArgumentParser(description='Read/write Noema pages with public compound definitions.')
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
            if args.public_names:document=CompoundVocabulary().encode(document)
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
