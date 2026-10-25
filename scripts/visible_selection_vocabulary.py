"""Frozen edition-six addition to the existing arithmetic vocabulary."""
from copy import deepcopy
import json
from noema.constructed import parse
from noema.constructed_discourse import normalize_document
from scripts.visible_quantity_vocabulary import QuantityVocabulary,check_quantity_extension,ROOT
from scripts.visible_word_forms import Word,canonical,symbol
from scripts.visible_lexical_script import require
from scripts.shared_selection import LIBRARY,BASIS,NEW_NAMES

SCHEMA='noema-visible-selection-vocabulary-1'
MANIFEST='noema/resources/visible-selection-vocabulary-v1.json'


class SelectionVocabulary(QuantityVocabulary):
    def __init__(self,document=None):
        super().__init__()
        data=self.document();parent=deepcopy(data)
        source=json.loads((ROOT/MANIFEST).read_text(encoding='utf-8'))
        require(source['schema']=='noema-visible-vocabulary-extension-source-1' and source['edition']==6
                and source['parent_edition']==5 and source['library']==LIBRARY and source['basis']==BASIS
                and set(source['spellings'])==set(NEW_NAMES),'Invalid selection vocabulary source')
        library=parse((ROOT/LIBRARY).read_text(encoding='utf-8'));basis=json.loads((ROOT/BASIS).read_text(encoding='utf-8'))
        require(not library['statements'] and basis['document']==LIBRARY and {d['name'] for d in library['declarations']}
                ==set(basis['public_contracts'])==set(basis['primitives'])|set(basis['definitions']),'Shared selection inventory differs')
        for declaration in library['declarations']:
            name=declaration['name'];contract=basis['public_contracts'][name]
            params=declaration['parameters'] if declaration['kind']=='primitive' else [p['sort'] for p in declaration['parameters']]
            meaning=basis['primitives'][name]['meaning_ja'] if declaration['kind']=='primitive' else basis['definitions'][name]
            require(params==[p['sort'] for p in contract['arguments']] and declaration['result']==contract['result'],'Shared signature differs')
            if name not in NEW_NAMES:
                entry=self.entry(name)
                require(declaration==self._plain_declaration(name) and meaning==entry['meaning']
                        and entry['roles']==[p['role'] for p in contract['arguments']]
                        and entry['context']==[p['role']+': '+p['interpretation'] for p in contract['arguments']],
                        'Existing dependency meaning differs')
                continue
            require(name not in self._words and (declaration['kind']=='primitive')==(name=='truthindicator'),
                    'Selection declaration kind or name differs')
            word=canonical(Word('compound',tuple(source['spellings'][name])),self)
            require(2<=len(word.parts)<=3,'Invalid selection spelling')
            data['primitives' if declaration['kind']=='primitive' else 'definitions'][name]=declaration
            data['compounds'][name]=dict(parts=list(word.parts),parameters=params,result=declaration['result'],
                roles=[p['role'] for p in contract['arguments']],meaning=meaning,
                context=[p['role']+': '+p['interpretation'] for p in contract['arguments']],contrast=basis['limitations'],aliases=[])
        data.update(schema=SCHEMA,edition=6)
        data['naming_convention']+='\n'+source['naming_convention']
        # This edition is the published addition, not a dialect with the same
        # visible version number. Alternate proposed meanings need a new edition.
        require(document is None or document==data,'Edition six differs from its published meanings')
        self._document=data;self._definitions=deepcopy(data['definitions']);self._primitives=deepcopy(data['primitives'])
        self._words.update({n:canonical(Word('compound',tuple(data['compounds'][n]['parts'])),self) for n in NEW_NAMES})
        self._symbols={n:symbol(w,self) for n,w in self._words.items()}
        require(len(set(self._symbols.values()))==len(self._words),'Selection spelling collision')
        self._by_symbol={s:n for n,s in self._symbols.items()};self._order=self._topological()
        checked=normalize_document(dict(schema_version='0.16',lexicon_version='0.16',
            declarations=[self._plain_declaration(n) for n in self._order],statements=[]))
        self._definitions={d['name']:d for d in checked['declarations'] if d['kind']=='definition'}
        self._document['definitions']=deepcopy(self._definitions)
        for field in ('entries','definitions','primitives','compounds'):
            require(all(self._document[field].get(n)==d for n,d in parent[field].items()),'Existing vocabulary changed')
