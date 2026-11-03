"""Learn declarations from ordered geometry items and a public seed dictionary.

Item ordering/boundaries are supplied here; this is not a page segmentation API.
No future declaration, source body or target spelling table reaches the reader.
"""
from copy import deepcopy
from scripts.kant_lexical_context import LexicalContext,use_context
from scripts import kant_public_fragment as writing


def empty_document():return dict(schema_version='0.16',lexicon_version='0.16',declarations=[],statements=[])


class Reader:
    def __init__(self,seed=None):
        self.seed=deepcopy(seed if seed is not None else empty_document())
        if self.seed.get('statements')!=[]:raise ValueError('Dictionary seed cannot contain statements')
        self.context=LexicalContext(self.seed,compact=False)
        self.document=empty_document()

    def register(self,item):
        if item['kind'] in writing.DECLARATION_TOKENS:
            if self.document['statements']:raise ValueError('Declaration follows a statement')
            if item['name'] in self.context.declarations:raise ValueError('Duplicate or imported declaration name')
            with use_context(self.context):writing.validate_declaration(item,new_name=True)
            declarations=[*self.document['declarations'],deepcopy(item)]
            # Rebuild from only already recovered declarations; do not derive
            # aliases whose earlier spellings could change as more names arrive.
            context=LexicalContext(dict(self.seed,declarations=[*self.seed['declarations'],*declarations]),compact=False)
            self.context=context;self.document['declarations']=declarations
        else:
            with use_context(self.context):writing.validate_native(item)
            self.document['statements'].append(deepcopy(item))
        return item

    def read(self,shapes):
        return self.register(writing.decode_item(shapes,lexicon=self.context))


def decode_items(items,*,seed=None):
    reader=Reader(seed)
    for shapes in items:reader.read(shapes)
    return reader.document


def compile_items(document,*,seed=None,**options):
    if set(document)!=set(empty_document()) or document['schema_version']!='0.16' or document['lexicon_version']!='0.16':
        raise ValueError('Expected a native edition 0.16 document')
    writer=Reader(seed);drawings=[]
    for item in [*document['declarations'],*document['statements']]:
        if item['kind'] in writing.DECLARATION_TOKENS:
            drawing=writing.compile_declaration(item,lexicon=writer.context,full_names=True,**options)
        else:drawing=writing.compile_statement(item,lexicon=writer.context,**options)
        writer.register(item);drawings.append(drawing)
    return drawings
