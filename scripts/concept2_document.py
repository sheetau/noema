"""Incremental concept-2 documents: only prior visible declarations are known.

Full names are compositional root sequences, not dictionary row numbers.
The same ink recognizer reads records and statements; page geometry supplies
their boundaries. A failed record never changes the reader's dictionary.
"""
from copy import deepcopy
from scripts.concept2_codec_v8 import Codec
from scripts import concept2_composition as composition
from scripts.kant_type_grammar import type_tokens, type_list_tokens, read_type, read_type_list
from noema.constructed_discourse import normalize_document


def empty_document():
    return dict(schema_version='0.16',lexicon_version='0.16',declarations=[],statements=[])


def full_parts(name):
    from scripts.visible_word_forms import read_symbol
    from scripts.kant_public_lexicon import vocabulary
    word=read_symbol(name,vocabulary())
    if word.kind not in ('root','compound'):raise ValueError('A lexical declaration needs a root or compound name')
    return [composition.old.root_symbol(p) for p in word.parts]


def full_name(parts):
    from scripts.visible_word_forms import Word,symbol
    from scripts.kant_public_lexicon import vocabulary
    names=tuple(composition.old.root_name(p) for p in parts)
    return symbol(Word('root' if len(names)==1 else 'compound',names),vocabulary())


def references(value):
    if isinstance(value,list):return set().union(*(references(x) for x in value))
    if not isinstance(value,dict):return set()
    own={value['symbol']} if value.get('kind') in ('call','function_ref') else set()
    return own.union(*(references(x) for x in value.values()))


def signature(declaration):
    return dict(kind='primitive',name=declaration['name'],result=deepcopy(declaration['result']),
        parameters=deepcopy(declaration['parameters'] if declaration['kind']=='primitive' else [p['sort'] for p in declaration['parameters']]))


def make_plan(statement,dictionary,*,sharing=True):
    # An assumption has separate statement scopes; never hoist value references
    # from a child or its condition into another child.
    if statement['kind']=='suppose':
        condition=composition.make_plan(dict(kind='assert',body=statement['condition']),dictionary,sharing=sharing)['plan']
        condition['body']=condition['body']['body']
        return dict(kind='suppose',condition=condition,
            statements=[make_plan(s,dictionary,sharing=sharing) for s in statement['statements']])
    return composition.make_plan(statement,dictionary,sharing=sharing)['plan']


def complete_public_dictionary(published):
    """Restore explicit base imports omitted from the old publication payload."""
    from scripts.kant_lexical_context import LexicalContext
    context=LexicalContext.from_published(published)
    result=deepcopy(published)
    result['native']=dict(empty_document(),declarations=context.declarations_for(tuple(context.declarations)))
    if set(x['symbol'] for x in result['aliases'])-set(context.declarations):
        raise ValueError('A published spelling has no declaration')
    return result


class DocumentCodec(Codec):
    def __init__(self,seed=None):
        seed=deepcopy(seed if seed is not None else empty_document())
        if seed.get('statements')!=[]:raise ValueError('A dictionary seed cannot contain statements')
        if seed['declarations']:seed=normalize_document(seed)
        spellings={d['name']:full_parts(d['name']) for d in seed['declarations']}
        dictionary=dict(native=seed,selected_spellings=spellings,
            aliases=[dict(symbol=n,parts=p) for n,p in spellings.items()])
        super().__init__(dictionary)
        self.document=empty_document();self.spellings=[]

    def result(self):
        return deepcopy(dict(native=self.document,spellings=self.spellings))

    def canonical_record(self,record):
        kind=record['kind']
        if kind in ('primitive','definition','spelling') and self.document['statements']:
            raise ValueError('Declaration or spelling follows a statement')
        if kind=='spelling':
            if set(record)!={'kind','name','parts'} or record['name'] not in self.declarations:
                raise ValueError('A spelling needs a previously declared name')
            parts=tuple(composition.old.root_symbol(p) for p in record['parts'])
            full_name(parts) # Validates the public roots and component limit.
            if parts in self.aliases:raise ValueError('Duplicate or conflicting spelling')
            return deepcopy(record)
        if kind in ('primitive','definition'):
            name=record['name'];parts=tuple(full_parts(name))
            if name in self.declarations or parts in self.aliases:raise ValueError('Duplicate declaration or reserved spelling')
            deps=references(record)
            if deps-set(self.declarations):raise ValueError('Unknown, forward, or recursive declaration reference')
            if kind=='definition':
                expression=dict(kind='lambda',parameters=record['parameters'],body=record['body'])
                # This also checks indirect quotation/evaluation ranks against
                # the real prior definitions, not only primitive signatures.
                self.validate_native(dict(kind='assert',body=dict(kind='equal',arguments=[expression,expression])))
            source=dict(empty_document(),declarations=[signature(self.declarations[n]) for n in sorted(deps)]+[record])
            return normalize_document(source)['declarations'][-1]
        return self.validate_native(record)

    def register(self,record):
        record=self.canonical_record(record);kind=record['kind']
        if kind in ('primitive','definition'):
            self.declarations[record['name']]=deepcopy(record)
            self.dictionary['native']['declarations'].append(deepcopy(record))
            self.document['declarations'].append(deepcopy(record))
            self._alias(record['name'],full_parts(record['name']))
        elif kind=='spelling':
            self._alias(record['name'],[composition.old.root_symbol(p) for p in record['parts']])
            self.spellings.append(deepcopy(record))
        else:self.document['statements'].append(deepcopy(record))
        return record

    def _alias(self,name,parts):
        parts=tuple(parts)
        self.aliases[parts]=name
        self.prefixes.update(parts[:i] for i in range(1,len(parts)))
        self.dictionary['selected_spellings'][name]=list(parts)
        self.dictionary['aliases'].append(dict(symbol=name,parts=list(parts)))

    def _raw_word(self,parts):
        # A declaration name is read without a dictionary. Its visible stop is
        # mandatory, even if it is currently not a prefix of another word.
        tokens=self.spelling(parts)
        if not tokens or tokens[-1]!=('word-end',):tokens.append(('word-end',))
        return tokens

    def encode_record(self,record,*,sharing=True):
        record=self.canonical_record(record);kind=record['kind']
        if kind not in ('primitive','definition','spelling'):
            return self.encode(make_plan(record,self.dictionary,sharing=sharing))
        out=[('record',kind),*self._raw_word(full_parts(record['name']))]
        def types(items):
            return [('op','quotation-rank') if t=='quote_raise' else ('type',t) for t in items]
        if kind=='spelling':
            return out+self._raw_word([composition.old.root_symbol(p) for p in record['parts']])
        if kind=='primitive':
            return out+types(type_list_tokens(record['parameters']))+types(type_tokens(record['result']))
        out+=types(type_tokens(record['result']))
        expression=dict(kind='lambda',parameters=record['parameters'],body=record['body'])
        plan=composition.make_plan(expression,self.dictionary,sharing=sharing)['plan']
        return out+self.encode(plan,expression=True)

    def parse(self,tokens,*,expression=False):
        if expression:return super().parse(tokens,expression=True)
        if not tokens or tokens[0][0]!='record':
            return self.register(super().parse(tokens))
        pos=1;kind=tokens[0][1]
        def take():
            nonlocal pos
            if pos>=len(tokens):raise ValueError('Truncated document record')
            item=tokens[pos];pos+=1;return item
        def raw_word():
            parts=[]
            while True:
                t=take()
                if t==('word-end',):break
                if t not in self.expansions:raise ValueError('Expected a full spelling and its visible end')
                parts.extend(self.expansions[t])
            full_name(parts);return parts
        def type_take():
            t=take()
            if t==('op','quotation-rank'):return 'quote_raise'
            if t[0]!='type':raise ValueError('Expected a record type')
            return t[1]
        name=full_name(raw_word())
        if kind=='spelling':
            record=dict(kind=kind,name=name,parts=[composition.old.root_name(p) for p in raw_word()])
        elif kind=='primitive':
            parameters=read_type_list(type_take);result=read_type(type_take)
            record=dict(kind=kind,name=name,parameters=parameters,result=result)
        elif kind=='definition':
            result=read_type(type_take)
            value=super().parse(tokens[pos:],expression=True);pos=len(tokens)
            if value['kind']!='lambda':raise ValueError('Definition needs a parameter scope')
            record=dict(kind=kind,name=name,result=result,parameters=value['parameters'],body=value['body'])
        else:raise ValueError('Unknown document record')
        if pos!=len(tokens):raise ValueError('Trailing record tokens')
        return self.register(record)

    def read_document(self,raw):
        self.read_page(raw)
        return self.result()
