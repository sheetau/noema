"""Edition nine joins answer and conversation definitions without altering dependencies."""
from copy import deepcopy
import json
from noema.constructed import parse
from noema.constructed_discourse import normalize_document
from scripts.visible_speech_vocabulary import SpeechVocabulary,ROOT
from scripts.visible_quantity_vocabulary import check_quantity_extension
from scripts.visible_word_forms import Word,canonical,symbol
from scripts.visible_lexical_script import require

SCHEMA='noema-visible-conversation-vocabulary-1'
MANIFEST='noema/resources/visible-conversation-vocabulary-v1.json'
LIBRARIES=[dict(library='examples/v016/shared-answers-v1.noema',basis='data/shared-answers-basis-v1.json'),
    dict(library='examples/v016/shared-conversation-v1.noema',basis='data/shared-conversation-basis-v1.json')]


class ConversationVocabulary(SpeechVocabulary):
    def __init__(self,document=None):
        super().__init__();data=self.document();parent=deepcopy(data)
        source=json.loads((ROOT/MANIFEST).read_text(encoding='utf-8'))
        require(source['schema']=='noema-visible-vocabulary-extension-source-2' and source['edition']==9
            and source['parent_edition']==8 and source['libraries']==LIBRARIES,'Invalid conversation vocabulary source')
        new_names=set();seen=set()
        for library_spec in LIBRARIES:
            library=parse((ROOT/library_spec['library']).read_text(encoding='utf-8'))
            basis=json.loads((ROOT/library_spec['basis']).read_text(encoding='utf-8'))
            names={d['name'] for d in library['declarations']}
            require(library['schema_version']=='0.16' and not library['statements'] and basis['document']==library_spec['library']
                and names==set(basis['public_contracts'])==set(basis['definitions'])|set(basis['primitives']),
                'Shared conversation inventory differs')
            require(not names&seen,'Repeated source declaration');seen.update(names)
            for d in library['declarations']:
                name=d['name'];contract=basis['public_contracts'][name]
                parameters=d['parameters'] if d['kind']=='primitive' else [p['sort'] for p in d['parameters']]
                meaning=basis['primitives'][name]['meaning_ja'] if d['kind']=='primitive' else basis['definitions'][name]
                roles=[p['role'] for p in contract['arguments']]
                context=[p['role']+': '+p['interpretation'] for p in contract['arguments']]
                require(parameters==[p['sort'] for p in contract['arguments']] and d['result']==contract['result'],'Shared signature differs')
                if name in self._words:
                    entry=self.entry(name)
                    require(d==self._plain_declaration(name) and meaning==entry['meaning'] and roles==entry['roles']
                        and context==entry['context'] and name not in source['spellings'],'Existing dependency meaning differs')
                    continue
                require(d['kind']=='definition' and name in source['spellings'],'Unexpected new declaration')
                word=canonical(Word('compound',tuple(source['spellings'][name])),self)
                require(2<=len(word.parts)<=3,'Invalid conversation spelling')
                data['definitions'][name]=d
                data['compounds'][name]=dict(parts=list(word.parts),parameters=parameters,result=d['result'],roles=roles,
                    meaning=meaning,context=context,contrast=basis['limitations'],aliases=[])
                new_names.add(name)
        require(new_names==set(source['spellings']),'Conversation spelling inventory differs')
        data.update(schema=SCHEMA,edition=9);data['naming_convention']+='\n'+source['naming_convention']
        require(document is None or document==data,'Edition nine differs from its published meanings')
        self._document=data;self._definitions=deepcopy(data['definitions'])
        self._words.update({n:canonical(Word('compound',tuple(data['compounds'][n]['parts'])),self) for n in new_names})
        self._symbols={n:symbol(w,self) for n,w in self._words.items()}
        require(len(set(self._symbols.values()))==len(self._words),'Conversation spelling collision')
        self._by_symbol={s:n for n,s in self._symbols.items()};self._order=self._topological()
        checked=normalize_document(dict(schema_version='0.16',lexicon_version='0.16',
            declarations=[self._plain_declaration(n) for n in self._order],statements=[]))
        self._definitions={d['name']:d for d in checked['declarations'] if d['kind']=='definition'}
        self._document['definitions']=deepcopy(self._definitions)
        for field in ('entries','compounds','definitions','primitives'):
            require(all(self._document[field].get(n)==d for n,d in parent[field].items()),'Existing vocabulary changed')
