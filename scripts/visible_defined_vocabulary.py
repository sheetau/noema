"""Shared words may denote published definitions, not just primitives."""
from copy import deepcopy
import json
from pathlib import Path

from noema.constructed import parse
from noema.constructed_discourse import normalize_document
from noema.meaning_catalog import _references
from scripts.visible_syntax_vocabulary import Vocabulary
from scripts.visible_lexical_script import require,check_extension
from scripts.visible_word_forms import Word,symbol,read_symbol
from scripts.shared_modality import renamed

ROOT=Path(__file__).resolve().parents[1]
SCHEMA='noema-visible-defined-vocabulary-1'


class DefinedVocabulary(Vocabulary):
    def __init__(self,document=None):
        if document is None:
            source=json.loads((ROOT/'noema/resources/visible-defined-vocabulary-v1.json').read_text(encoding='utf-8'))
            require(source['schema']=='noema-visible-defined-vocabulary-source-1' and source['edition']==2
                    and source['library']=='examples/v016/shared-modality-v1.noema'
                    and source['meaning_basis']=='data/shared-modality-basis-v1.json','Unknown shared library')
            library=parse((ROOT/source['library']).read_text(encoding='utf-8'))
            basis=json.loads((ROOT/source['meaning_basis']).read_text(encoding='utf-8'))
            require(basis['document']==source['library'] and not basis['primitives'],'Shared library must retain definitions')
            entries=Vocabulary().document()['entries']
            definitions={d['name']:d for d in library['declarations']}
            require(set(definitions)==set(source['forms'])==set(basis['definitions'])==set(basis['public_contracts']),
                    'Shared definition/meaning/form inventories differ')
            for name,d in definitions.items():
                require(d['kind']=='definition','Shared definition became primitive')
                contract=basis['public_contracts'][name]
                require([r['sort'] for r in contract['arguments']]==[p['sort'] for p in d['parameters']]
                        and contract['result']==d['result'],'Shared public signature differs')
                entries[name]=dict(parameters=[p['sort'] for p in d['parameters']],result=d['result'],
                    roles=[r['role'] for r in contract['arguments']],meaning=basis['definitions'][name],
                    context=contract['interpretation_inputs'],contrast=basis['limitations'],form=source['forms'][name],aliases=[])
            document=dict(schema=SCHEMA,edition=2,entries=entries,definitions=definitions)
        data=deepcopy(document)
        require(isinstance(data,dict) and set(data)=={'schema','edition','entries','definitions'}
                and data['schema']==SCHEMA and type(data['edition']) is int and data['edition']==2,
                'Invalid defined vocabulary')
        # Reuse the visible-form and type checks without changing the pinned
        # v1 implementation. The public edition is restored after validation.
        super().__init__(dict(schema='noema-visible-vocabulary-1',edition=1,entries=data['entries']))
        check_extension(Vocabulary(),self)
        definitions=data['definitions']
        require(isinstance(definitions,dict) and set(definitions)==set(data['entries'])-set(Vocabulary().document()['entries']),
                'Every new root must have a public definition')
        require(all(isinstance(d,dict) and d.get('kind')=='definition' for d in definitions.values()),
                'Shared definition became primitive or malformed')
        self._definitions=deepcopy(definitions)
        self._document=data
        self._order=self._topological()
        declarations=[]
        for name in self._order:
            d=self._plain_declaration(name)
            require(d['name']==name,'Definition name differs')
            entry=self.resolve(name)[1]
            params=[p['sort'] for p in d['parameters']] if d['kind']=='definition' else d['parameters']
            require(params==entry['parameters'] and d['result']==entry['result'],'Definition signature differs')
            declarations.append(d)
        checked=normalize_document(dict(schema_version='0.16',lexicon_version='0.16',declarations=declarations,statements=[]))
        self._definitions={d['name']:d for d in checked['declarations'] if d['kind']=='definition'}
        self._document['definitions']=deepcopy(self._definitions)

    def _plain_declaration(self,name):
        if name in self._definitions:
            d=deepcopy(self._definitions[name])
            require(isinstance(d,dict) and d.get('kind')=='definition','Shared definition became primitive')
            return d
        _,e=self.resolve(name)
        return dict(kind='primitive',name=name,parameters=e['parameters'],result=e['result'])

    def _topological(self):
        names=set(self._document['entries']); active,done,order=set(),set(),[]
        def visit(n):
            require(n in names,'Unknown shared dependency')
            require(n not in active,'Cyclic shared definitions')
            if n in done:return
            active.add(n)
            for ref in sorted(_references(self._definitions.get(n,{}).get('body'))): visit(ref)
            active.remove(n); done.add(n); order.append(n)
        for name in sorted(names): visit(name)
        return order

    def declaration(self,name):
        canonical,_=self.resolve(name)
        mapping={n:symbol(Word('root',(n,)),self) for n in self._document['entries']}
        return renamed(self._plain_declaration(canonical),mapping)

    def imports(self,names):
        selected=set()
        def visit(n):
            canonical,_=self.resolve(n)
            if canonical in selected:return
            selected.add(canonical)
            for ref in _references(self._definitions.get(canonical,{}).get('body')): visit(ref)
        for n in names: visit(n)
        return [self.declaration(n) for n in self._order if n in selected]

    def encode(self,document):
        mapping={n:symbol(Word('root',(n,)),self) for n in self._document['entries']}
        return normalize_document(renamed(document,mapping))

    def decode_names(self,document):
        mapping={symbol(Word('root',(n,)),self):n for n in self._document['entries']}
        return normalize_document(renamed(document,mapping))


def check_defined_extension(previous,successor):
    check_extension(previous,successor)
    for name,definition in previous.document()['definitions'].items():
        require(successor.document()['definitions'].get(name)==definition,'Extension changed a shared definition')
    return True
