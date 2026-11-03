"""Learn declarations from ordered geometry items and a public seed dictionary.

Item ordering/boundaries are supplied here; this is not a page segmentation API.
No future declaration, source body or target spelling table reaches the reader.
"""
from copy import deepcopy
from scripts.kant_lexical_context import LexicalContext,use_context
from scripts import kant_public_fragment as writing
from scripts.visible_word_forms import Word,symbol


def empty_document():return dict(schema_version='0.16',lexicon_version='0.16',declarations=[],statements=[])


class ReadingContext(LexicalContext):
    def published(self):
        raise ValueError('Export recovered declarations and spelling records, not a legacy dictionary snapshot')


class Reader:
    def __init__(self,seed=None):
        self.seed=deepcopy(seed if seed is not None else empty_document())
        if self.seed.get('statements')!=[]:raise ValueError('Dictionary seed cannot contain statements')
        self.context=ReadingContext(self.seed,compact=False)
        self.document=empty_document()
        self.spellings=[]

    def _context_for(self,declarations,spellings):
        context=ReadingContext(dict(self.seed,declarations=[*self.seed['declarations'],*declarations]),compact=False)
        for record in spellings:
            with use_context(context):writing.validate_spelling(record)
            parts=tuple(symbol(Word('root',(p,)),writing.vocabulary()) for p in record['parts'])
            context.parts[record['name']]=parts
            context.spellings[parts]=record['name']
            context.prefixes.update(parts[:i] for i in range(1,len(parts)+1))
        return context

    def result(self,include_spellings=False):
        return deepcopy(dict(native=self.document,spellings=self.spellings) if include_spellings else self.document)

    def fork(self):
        # Registration replaces the context instead of mutating it. A pending
        # read may share this snapshot, but owns its mutable document lists.
        result=object.__new__(type(self))
        result.seed=deepcopy(self.seed);result.context=self.context
        result.document=deepcopy(self.document);result.spellings=deepcopy(self.spellings)
        return result

    def register(self,item):
        if item['kind']=='spelling':
            if self.document['statements']:raise ValueError('Spelling follows a statement')
            with use_context(self.context):writing.validate_spelling(item)
            spellings=[*self.spellings,deepcopy(item)]
            context=self._context_for(self.document['declarations'],spellings)
            self.context=context;self.spellings=spellings
        elif item['kind'] in writing.DECLARATION_TOKENS:
            if self.document['statements']:raise ValueError('Declaration follows a statement')
            if item['name'] in self.context.declarations:raise ValueError('Duplicate or imported declaration name')
            with use_context(self.context):writing.validate_declaration(item,new_name=True)
            declarations=[*self.document['declarations'],deepcopy(item)]
            # Rebuild from only already recovered declarations; do not derive
            # aliases whose earlier spellings could change as more names arrive.
            context=self._context_for(declarations,self.spellings)
            self.context=context;self.document['declarations']=declarations
        else:
            with use_context(self.context):writing.validate_native(item)
            self.document['statements'].append(deepcopy(item))
        return item

    def read(self,shapes):
        return self.register(writing.decode_item(shapes,lexicon=self.context))


def decode_items(items,*,seed=None,include_spellings=False):
    reader=Reader(seed)
    for shapes in items:reader.read(shapes)
    return reader.result(include_spellings)


def compile_items(document,*,seed=None,**options):
    if set(document)!=set(empty_document()) or document['schema_version']!='0.16' or document['lexicon_version']!='0.16':
        raise ValueError('Expected a native edition 0.16 document')
    return compile_records([*document['declarations'],*document['statements']],seed=seed,**options)


def compile_records(records,*,seed=None,**options):
    writer=Reader(seed);drawings=[]
    for item in records:
        if item['kind']=='spelling':
            drawing=writing.compile_spelling(item,lexicon=writer.context,**options)
        elif item['kind'] in writing.DECLARATION_TOKENS:
            drawing=writing.compile_declaration(item,lexicon=writer.context,full_names=True,**options)
        else:drawing=writing.compile_statement(item,lexicon=writer.context,**options)
        writer.register(item);drawings.append(drawing)
    return drawings


class PublishedStatementReader(Reader):
    """Read bodies with an explicit immutable public dictionary, not target ASTs."""
    def __init__(self,published):
        self.context=LexicalContext.from_published(published)
        self.seed=deepcopy(self.context.document)
        self.document=empty_document();self.spellings=[]

    def register(self,item):
        if item.get('kind') not in ('assert','ask','perform','suppose'):
            raise ValueError('Published body reader requires statements')
        return super().register(item)
