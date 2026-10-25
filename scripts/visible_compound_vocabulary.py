"""Public compound spellings with preserved definitions and root vocabulary."""
from copy import deepcopy
import json
import re
from noema.constructed import parse
from noema.constructed_discourse import normalize_document,sort
from noema.meaning_catalog import _references
from scripts.visible_defined_vocabulary import DefinedVocabulary,check_defined_extension,ROOT
from scripts.visible_word_forms import Word,canonical,symbol
from scripts.visible_lexical_script import require
from scripts.shared_modality import renamed

SCHEMA='noema-visible-compound-vocabulary-1'
MANIFEST='noema/resources/visible-compound-vocabulary-v1.json'
MODULES=[dict(document='examples/v016/shared-'+name+'-v1.noema',basis='data/shared-'+name+'-basis-v1.json')
         for name in ('time','reference','readings')]


class CompoundVocabulary(DefinedVocabulary):
    def __init__(self,document=None):
        super().__init__()
        baseline=self.document()
        if document is None:
            source=json.loads((ROOT/MANIFEST).read_text(encoding='utf-8'))
            require(source['schema']=='noema-visible-compound-vocabulary-source-1' and source['edition']==3
                    and source['modules']==MODULES,'Unknown compound vocabulary source')
            definitions=deepcopy(baseline['definitions']);compounds={}
            for module in MODULES:
                library=parse((ROOT/module['document']).read_text(encoding='utf-8'))
                basis=json.loads((ROOT/module['basis']).read_text(encoding='utf-8'))
                names={d['name'] for d in library['declarations']}
                require(library['schema_version']=='0.16' and not library['statements'] and not basis['primitives']
                        and basis['document']==module['document'] and names==set(basis['definitions'])==set(basis['public_contracts']),
                        'Shared module and meaning inventory differ')
                require(not names & (set(definitions)|set(baseline['entries'])),'Shared name collision')
                for d in library['declarations']:
                    n=d['name'];contract=basis['public_contracts'][n]
                    require(d['kind']=='definition','Compound definition became primitive')
                    require([a['sort'] for a in contract['arguments']]==[p['sort'] for p in d['parameters']]
                            and contract['result']==d['result'],'Shared signature differs')
                    require(n in source['spellings'],'Missing public spelling')
                    definitions[n]=d
                    compounds[n]=dict(parts=source['spellings'][n],parameters=[p['sort'] for p in d['parameters']],
                        result=d['result'],roles=[p['role'] for p in contract['arguments']],meaning=basis['definitions'][n],
                        context=[p['role']+': '+p['interpretation'] for p in contract['arguments']],
                        contrast=basis['limitations'],aliases=[])
            require(set(compounds)==set(source['spellings']),'Unmatched public compound spelling')
            document=dict(schema=SCHEMA,edition=3,entries=baseline['entries'],definitions=definitions,
                          compounds=compounds,naming_convention=source['naming_convention'])
        data=deepcopy(document)
        require(isinstance(data,dict) and set(data)=={'schema','edition','entries','definitions','compounds','naming_convention'}
                and data['schema']==SCHEMA and type(data['edition']) is int and data['edition']==3,'Invalid compound vocabulary')
        require(data['entries']==baseline['entries'],'Existing root meanings or forms changed')
        require(isinstance(data['compounds'],dict) and data['compounds'],'Missing shared compounds')
        require(isinstance(data['definitions'],dict) and set(data['definitions'])==set(baseline['definitions'])|set(data['compounds']),
                'Every compound must have one shared definition')
        require(isinstance(data['naming_convention'],str) and data['naming_convention'].strip(),'Missing naming convention')
        words={n:Word('root',(n,)) for n in baseline['entries']}
        for n,entry in data['compounds'].items():
            require(isinstance(n,str) and re.fullmatch('[a-z2-7]+',n) and n not in baseline['entries'],'Invalid compound name')
            require(isinstance(entry,dict) and set(entry)=={'parts','parameters','result','roles','meaning','context','contrast','aliases'},
                    'Invalid shared compound entry')
            require(type(entry['parts']) is list,'Invalid compound spelling')
            words[n]=canonical(Word('compound',tuple(entry['parts'])),self)
            require(isinstance(entry['parameters'],list),'Invalid parameter types')
            for t in [*entry['parameters'],entry['result']]:sort(t,'0.16')
            for field in ('roles','context','contrast','aliases'):
                require(isinstance(entry[field],list) and all(isinstance(x,str) and x.strip() for x in entry[field]),'Invalid compound '+field)
            require(not entry['aliases'] and len(entry['roles'])==len(entry['parameters']) and entry['contrast']
                    and isinstance(entry['meaning'],str) and entry['meaning'].strip(),'Missing public compound meaning')
        self._words=words
        self._symbols={n:symbol(w,self) for n,w in words.items()}
        require(len(set(self._symbols.values()))==len(words),'Shared compound spelling collision')
        self._by_symbol={s:n for n,s in self._symbols.items()}
        self._definitions=deepcopy(data['definitions']);self._document=data
        require(all(isinstance(d,dict) and d.get('kind')=='definition' and d.get('name')==n
                    for n,d in self._definitions.items()),'Shared definition became primitive or mismatched')
        for n,d in baseline['definitions'].items():
            require(self._definitions.get(n)==d,'Existing root definition changed')
        self._order=self._topological()
        declarations=[]
        for name in self._order:
            d=self._plain_declaration(name);entry=self.entry(name)
            params=[p['sort'] for p in d['parameters']] if d['kind']=='definition' else d['parameters']
            require(params==entry['parameters'] and d['result']==entry['result'],'Compound signature differs')
            declarations.append(d)
        checked=normalize_document(dict(schema_version='0.16',lexicon_version='0.16',declarations=declarations,statements=[]))
        self._definitions={d['name']:d for d in checked['declarations'] if d['kind']=='definition'}
        self._document['definitions']=deepcopy(self._definitions)

    def _topological(self):
        # During the inherited constructor only the edition-2 roots exist.
        if not hasattr(self,'_words'):return super()._topological()
        names=set(self._words);active,done,order=set(),set(),[]
        def visit(n):
            require(n in names,'Unknown shared dependency')
            require(n not in active,'Cyclic shared definitions')
            if n in done:return
            active.add(n)
            for ref in sorted(_references(self._definitions.get(n,{}).get('body'))):visit(ref)
            active.remove(n);done.add(n);order.append(n)
        for n in sorted(names):visit(n)
        return order

    def shared_name(self,name):
        if name in self._document['compounds']:return name
        return self.resolve(name)[0]

    def entry(self,name):
        name=self.shared_name(name)
        return deepcopy(self._document['compounds'].get(name,self._document['entries'].get(name)))

    def word(self,name):return self._words[self.shared_name(name)]

    def name_for(self,word):return self._by_symbol.get(symbol(word,self))

    def declaration(self,name):
        return renamed(self._plain_declaration(self.shared_name(name)),self._symbols)

    def imports(self,names):
        selected=set()
        def visit(n):
            n=self.shared_name(n)
            if n in selected:return
            selected.add(n)
            for ref in _references(self._definitions.get(n,{}).get('body')):visit(ref)
        for name in names:visit(name)
        return [self.declaration(n) for n in self._order if n in selected]

    def encode(self,document):return normalize_document(renamed(document,self._symbols))

    def decode_names(self,document):return normalize_document(renamed(document,self._by_symbol))


def check_compound_extension(previous,successor):
    check_defined_extension(previous,successor)
    for name,entry in previous.document().get('compounds',{}).items():
        require(successor.document()['compounds'].get(name)==entry,'Extension changed shared compound spelling or meaning')
    return True
