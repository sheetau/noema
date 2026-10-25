"""Edition five: shared arithmetic primitives and identical module dependencies."""
from copy import deepcopy
import json
import re
from noema.constructed import parse
from noema.constructed_discourse import normalize_document,sort
from scripts.visible_scope_vocabulary import ScopeVocabulary
from scripts.visible_compound_vocabulary import CompoundVocabulary,check_compound_extension,ROOT
from scripts.visible_defined_vocabulary import DefinedVocabulary
from scripts.visible_word_forms import Word,canonical,symbol
from scripts.visible_lexical_script import require

SCHEMA='noema-visible-quantity-vocabulary-1'
MANIFEST='noema/resources/visible-quantity-vocabulary-v1.json'
MODULES=[dict(document='examples/v016/shared-'+n+'-v1.noema',basis='data/shared-'+n+'-basis-v1.json')
         for n in ('plurality','quantities')]
PRIMITIVES={'rationalbelow','rationaladd','rationalnegate','rationalmultiply'}


def module_records(modules=MODULES):
    records={}
    for module in modules:
        library=parse((ROOT/module['document']).read_text(encoding='utf-8'))
        basis=json.loads((ROOT/module['basis']).read_text(encoding='utf-8'))
        names={d['name'] for d in library['declarations']}
        require(library['schema_version']=='0.16' and not library['statements'] and basis['document']==module['document']
                and names==set(basis['definitions'])|set(basis['primitives']) and names==set(basis['public_contracts']),
                'Shared module and public inventory differ')
        for declaration in library['declarations']:
            n=declaration['name'];contract=basis['public_contracts'][n]
            if declaration['kind']=='primitive':
                require(n in PRIMITIVES and n in basis['primitives'],'Unrecognized shared primitive')
                record=basis['primitives'][n]
                require(record['parameters']==declaration['parameters'] and record['result']==declaration['result']
                        and record['arguments']==[p['role'] for p in contract['arguments']],'Primitive convention differs')
                meaning=record['meaning_ja'];params=declaration['parameters']
            else:
                require(declaration['kind']=='definition' and n not in PRIMITIVES,'Shared declaration kind changed')
                meaning=basis['definitions'][n];params=[p['sort'] for p in declaration['parameters']]
            require(params==[p['sort'] for p in contract['arguments']] and declaration['result']==contract['result'],
                    'Shared signature differs')
            current=dict(declaration=declaration,contract=contract,meaning=meaning)
            if n in records:
                require(all(records[n][k]==current[k] for k in current),'Shared dependency differs between modules')
                records[n]['limits']=sorted(set(records[n]['limits'])|set(basis['limitations']))
            else:records[n]=dict(current,limits=sorted(set(basis['limitations'])))
    return records


class QuantityVocabulary(CompoundVocabulary):
    def __init__(self,document=None):
        # Initialize the unchanged root validator; compound primitives are then
        # validated explicitly, never substituted with pretend definitions.
        DefinedVocabulary.__init__(self)
        parent=ScopeVocabulary();baseline=parent.document()
        if document is None:
            source=json.loads((ROOT/MANIFEST).read_text(encoding='utf-8'))
            require(source['schema']=='noema-visible-vocabulary-extension-source-1' and source['edition']==5
                    and source['parent_edition']==4 and source['modules']==MODULES,'Unknown quantity vocabulary source')
            document=deepcopy(baseline);document['primitives']={}
            records=module_records()
            require(set(records)==set(source['spellings']),'Unmatched public spelling')
            require(not set(records)&(set(baseline['entries'])|set(baseline['compounds'])),'Shared name collision')
            for n,row in records.items():
                d=row['declaration'];contract=row['contract']
                document['primitives' if d['kind']=='primitive' else 'definitions'][n]=d
                document['compounds'][n]=dict(parts=source['spellings'][n],parameters=[p['sort'] for p in contract['arguments']],
                    result=contract['result'],roles=[p['role'] for p in contract['arguments']],meaning=row['meaning'],
                    context=[p['role']+': '+p['interpretation'] for p in contract['arguments']],contrast=row['limits'],aliases=[])
            document['naming_convention']+='\n'+source['naming_convention']
            document.update(schema=SCHEMA,edition=5)
        data=deepcopy(document)
        require(isinstance(data,dict) and set(data)=={'schema','edition','entries','definitions','primitives','compounds','naming_convention'}
                and data['schema']==SCHEMA and type(data['edition']) is int and data['edition']==5,'Invalid quantity vocabulary')
        require(data['entries']==baseline['entries'],'Existing root meanings or forms changed')
        require(isinstance(data['compounds'],dict) and isinstance(data['definitions'],dict) and isinstance(data['primitives'],dict),
                'Invalid shared inventory')
        require(set(data['primitives'])==PRIMITIVES,'Shared arithmetic inventory differs')
        require(set(data['definitions']).isdisjoint(data['primitives']) and set(data['definitions'])|set(data['primitives'])
                ==set(DefinedVocabulary().document()['definitions'])|set(data['compounds']),'Shared declaration inventory differs')
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
        self._words=words;self._symbols={n:symbol(w,self) for n,w in words.items()}
        require(len(set(self._symbols.values()))==len(words),'Shared compound spelling collision')
        self._by_symbol={s:n for n,s in self._symbols.items()}
        self._definitions=deepcopy(data['definitions']);self._primitives=deepcopy(data['primitives']);self._document=data
        require(all(isinstance(d,dict) and d.get('kind')=='definition' and d.get('name')==n
                    for n,d in self._definitions.items()),'Shared definition became primitive or mismatched')
        expected={n:r['declaration'] for n,r in module_records().items() if n in PRIMITIVES}
        require(self._primitives==expected,'Shared arithmetic declaration changed')
        check_compound_extension(parent,self)
        self._order=self._topological();declarations=[]
        for n in self._order:
            d=self._plain_declaration(n);entry=self.entry(n)
            params=[p['sort'] for p in d['parameters']] if d['kind']=='definition' else d['parameters']
            require(params==entry['parameters'] and d['result']==entry['result'],'Shared signature differs')
            declarations.append(d)
        checked=normalize_document(dict(schema_version='0.16',lexicon_version='0.16',declarations=declarations,statements=[]))
        self._definitions={d['name']:d for d in checked['declarations'] if d['kind']=='definition'}
        self._document['definitions']=deepcopy(self._definitions)

    def _plain_declaration(self,name):
        if name in getattr(self,'_primitives',{}):return deepcopy(self._primitives[name])
        return super()._plain_declaration(name)


def check_quantity_extension(previous,successor):
    check_compound_extension(previous,successor)
    for n,d in previous.document().get('primitives',{}).items():
        require(successor.document().get('primitives',{}).get(n)==d,'Extension changed shared arithmetic')
    return True
