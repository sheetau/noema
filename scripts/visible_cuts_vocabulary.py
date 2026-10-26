"""Edition thirteen adds preserved cut definitions, with no new primitives."""
from copy import deepcopy
import json
from noema.constructed import parse
from noema.constructed_discourse import normalize_document
from scripts.visible_senses_vocabulary import SensesVocabulary, ROOT
from scripts.visible_word_forms import Word, canonical, symbol
from scripts.visible_lexical_script import require

MANIFEST='noema/resources/visible-cuts-vocabulary-v1.json'
SCHEMA='noema-visible-cuts-vocabulary-1'


class CutsVocabulary(SensesVocabulary):
    def __init__(self,document=None):
        super().__init__();data=self.document();parent=deepcopy(data)
        source=json.loads((ROOT/MANIFEST).read_text(encoding='utf-8'))
        require(source['schema']=='noema-visible-vocabulary-extension-source-2' and source['edition']==13
                and source['parent_edition']==12,'Invalid cut vocabulary source')
        library=parse((ROOT/source['library']).read_text(encoding='utf-8'))
        basis=json.loads((ROOT/source['basis']).read_text(encoding='utf-8'))
        require(basis['document']==source['library'] and not library['statements'],'Cut vocabulary library differs')
        require({d['name'] for d in library['declarations']}==set(basis['public_contracts'])
                ==set(basis['definitions'])|set(basis['primitives']),'Cut vocabulary inventory differs')
        new=set()
        for d in library['declarations']:
            name=d['name'];contract=basis['public_contracts'][name]
            parameters=d['parameters'] if d['kind']=='primitive' else [p['sort'] for p in d['parameters']]
            roles=[p['role'] for p in contract['arguments']]
            meaning=basis['primitives'][name]['meaning_ja'] if d['kind']=='primitive' else basis['definitions'][name]
            require(parameters==[p['sort'] for p in contract['arguments']] and d['result']==contract['result'],'Cut signature differs')
            if name in self._words:
                entry=self.entry(name)
                require(d==self._plain_declaration(name) and roles==entry['roles'] and meaning==entry['meaning']
                        and contract['interpretation_inputs']==entry['context'],'Reused arithmetic convention differs')
                continue
            require(d['kind']=='definition' and name in source['spellings'],'Unexpected new cut declaration')
            word=canonical(Word('compound',tuple(source['spellings'][name])),self);new.add(name)
            data['definitions'][name]=d
            data['compounds'][name]=dict(parts=list(word.parts),parameters=parameters,result=d['result'],roles=roles,
                meaning=meaning,context=contract['interpretation_inputs'],contrast=basis['limitations'],aliases=[])
        require(new==set(source['spellings']),'Cut spelling inventory differs')
        data.update(schema=SCHEMA,edition=13);data['naming_convention']+='\n'+source['naming_convention']
        require(document is None or document==data,'Edition thirteen differs from published meanings')
        self._document=data;self._definitions=deepcopy(data['definitions'])
        self._words.update({n:canonical(Word('compound',tuple(data['compounds'][n]['parts'])),self) for n in new})
        self._symbols={n:symbol(w,self) for n,w in self._words.items()}
        require(len(set(self._symbols.values()))==len(self._words),'Cut spelling collision')
        self._by_symbol={s:n for n,s in self._symbols.items()};self._order=self._topological()
        checked=normalize_document(dict(schema_version='0.16',lexicon_version='0.16',
            declarations=[self._plain_declaration(n) for n in self._order],statements=[]))
        self._definitions={d['name']:d for d in checked['declarations'] if d['kind']=='definition'}
        self._document['definitions']=deepcopy(self._definitions)
        for field in ('entries','compounds','definitions','primitives'):
            require(all(self._document[field].get(n)==d for n,d in parent[field].items()),'Existing vocabulary changed')
