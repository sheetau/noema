"""Edition seven: normal cases and degrees with frozen earlier vocabularies."""
from copy import deepcopy
import json
from noema.constructed import parse
from noema.constructed_discourse import normalize_document
from scripts.visible_selection_vocabulary import SelectionVocabulary,ROOT
from scripts.visible_quantity_vocabulary import check_quantity_extension
from scripts.visible_word_forms import Word,canonical,symbol
from scripts.visible_lexical_script import require
from scripts.shared_generality import LIBRARY,BASIS

SCHEMA='noema-visible-generality-vocabulary-1'
MANIFEST='noema/resources/visible-generality-vocabulary-v1.json'


class GeneralityVocabulary(SelectionVocabulary):
    def __init__(self,document=None):
        super().__init__();data=self.document();parent=deepcopy(data)
        source=json.loads((ROOT/MANIFEST).read_text(encoding='utf-8'))
        require(source['schema']=='noema-visible-vocabulary-extension-source-1' and source['edition']==7
            and source['parent_edition']==6 and source['library']==LIBRARY and source['basis']==BASIS,'Invalid generality vocabulary source')
        library=parse((ROOT/LIBRARY).read_text(encoding='utf-8'));basis=json.loads((ROOT/BASIS).read_text(encoding='utf-8'))
        names={d['name'] for d in library['declarations']}
        require(library['schema_version']=='0.16' and not library['statements'] and not basis['primitives']
            and basis['document']==LIBRARY and names==set(basis['definitions'])==set(basis['public_contracts'])
            ==set(source['spellings']),'Shared generality inventory differs')
        require(not names&set(self._words),'Shared generality name collision')
        for d in library['declarations']:
            name=d['name'];contract=basis['public_contracts'][name]
            require(d['kind']=='definition','Generality definition became primitive')
            params=[p['sort'] for p in d['parameters']]
            require(params==[p['sort'] for p in contract['arguments']] and d['result']==contract['result'],'Shared signature differs')
            word=canonical(Word('compound',tuple(source['spellings'][name])),self)
            require(2<=len(word.parts)<=3,'Invalid generality spelling')
            data['definitions'][name]=d
            data['compounds'][name]=dict(parts=list(word.parts),parameters=params,result=d['result'],
                roles=[p['role'] for p in contract['arguments']],meaning=basis['definitions'][name],
                context=[p['role']+': '+p['interpretation'] for p in contract['arguments']],contrast=basis['limitations'],aliases=[])
        data.update(schema=SCHEMA,edition=7);data['naming_convention']+='\n'+source['naming_convention']
        require(document is None or document==data,'Edition seven differs from its published meanings')
        self._document=data;self._definitions=deepcopy(data['definitions'])
        self._words.update({n:canonical(Word('compound',tuple(data['compounds'][n]['parts'])),self) for n in names})
        self._symbols={n:symbol(w,self) for n,w in self._words.items()}
        require(len(set(self._symbols.values()))==len(self._words),'Generality spelling collision')
        self._by_symbol={s:n for n,s in self._symbols.items()};self._order=self._topological()
        checked=normalize_document(dict(schema_version='0.16',lexicon_version='0.16',
            declarations=[self._plain_declaration(n) for n in self._order],statements=[]))
        self._definitions={d['name']:d for d in checked['declarations'] if d['kind']=='definition'}
        self._document['definitions']=deepcopy(self._definitions)
        for field in ('entries','compounds','definitions','primitives'):
            require(all(self._document[field].get(n)==d for n,d in parent[field].items()),'Existing vocabulary changed')
