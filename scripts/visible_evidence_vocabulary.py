"""Edition eleven preserves evidence and information-revision meanings."""
from copy import deepcopy
import json
from noema.constructed import parse
from noema.constructed_discourse import normalize_document
from scripts.visible_deadline_vocabulary import DeadlineVocabulary,ROOT,check_quantity_extension
from scripts.visible_word_forms import Word,canonical,symbol
from scripts.visible_lexical_script import require

SCHEMA='noema-visible-evidence-vocabulary-1'
MANIFEST='noema/resources/visible-evidence-vocabulary-v1.json'
LIBRARIES=[dict(library='examples/v016/shared-evidence-v1.noema',basis='data/shared-evidence-basis-v1.json'),
    dict(library='examples/v016/shared-revision-v1.noema',basis='data/shared-revision-basis-v1.json')]


class EvidenceVocabulary(DeadlineVocabulary):
    def __init__(self,document=None):
        super().__init__();data=self.document();parent=deepcopy(data)
        source=json.loads((ROOT/MANIFEST).read_text(encoding='utf-8'))
        require(source['schema']=='noema-visible-vocabulary-extension-source-2' and source['edition']==11
            and source['parent_edition']==10 and source['libraries']==LIBRARIES,'Invalid evidence vocabulary source')
        records={}
        for spec in LIBRARIES:
            library=parse((ROOT/spec['library']).read_text(encoding='utf-8'));basis=json.loads((ROOT/spec['basis']).read_text(encoding='utf-8'))
            names={d['name'] for d in library['declarations']}
            require(library['schema_version']=='0.16' and not library['statements'] and basis['document']==spec['library']
                and names==set(basis['public_contracts'])==set(basis['definitions'])|set(basis['primitives']),'Shared evidence inventory differs')
            for d in library['declarations']:
                name=d['name'];contract=basis['public_contracts'][name]
                parameters=d['parameters'] if d['kind']=='primitive' else [p['sort'] for p in d['parameters']]
                meaning=basis['primitives'][name]['meaning_ja'] if d['kind']=='primitive' else basis['definitions'][name]
                roles=[p['role'] for p in contract['arguments']]
                context=(contract['interpretation_inputs'] if 'interpretation_inputs' in contract else
                    [p['role']+': '+p['interpretation'] for p in contract['arguments']])
                require(parameters==[p['sort'] for p in contract['arguments']] and d['result']==contract['result'],'Shared signature differs')
                record=dict(declaration=d,meaning=meaning,roles=roles,context=context,parameters=parameters)
                if name in records:
                    require(record==records[name],'Repeated dependency meaning differs')
                    continue
                records[name]=record
                if name in self._words:
                    entry=self.entry(name)
                    require(d==self._plain_declaration(name) and meaning==entry['meaning'] and roles==entry['roles']
                        and context==entry['context'] and name not in source['spellings'],'Existing dependency meaning differs')
                    continue
                require((d['kind']=='definition' or name=='claimchoice') and name in source['spellings'],'Unexpected new declaration')
                if d['kind']=='primitive':
                    primitive=basis['primitives'][name]
                    require(primitive['parameters']==parameters and primitive['result']==d['result'] and primitive['arguments']==roles,'Primitive convention differs')
                word=canonical(Word('compound',tuple(source['spellings'][name])),self)
                require(2<=len(word.parts)<=3,'Invalid evidence spelling')
                data['primitives' if d['kind']=='primitive' else 'definitions'][name]=d
                data['compounds'][name]=dict(parts=list(word.parts),parameters=parameters,result=d['result'],roles=roles,
                    meaning=meaning,context=context,contrast=basis['limitations'],aliases=[])
        new_names=set(records)-set(self._words)
        require(new_names==set(source['spellings']),'Evidence spelling inventory differs')
        data.update(schema=SCHEMA,edition=11);data['naming_convention']+='\n'+source['naming_convention']
        require(document is None or document==data,'Edition eleven differs from its published meanings')
        self._document=data;self._definitions=deepcopy(data['definitions']);self._primitives=deepcopy(data['primitives'])
        self._words.update({n:canonical(Word('compound',tuple(data['compounds'][n]['parts'])),self) for n in new_names})
        self._symbols={n:symbol(w,self) for n,w in self._words.items()}
        require(len(set(self._symbols.values()))==len(self._words),'Evidence spelling collision')
        self._by_symbol={s:n for n,s in self._symbols.items()};self._order=self._topological()
        checked=normalize_document(dict(schema_version='0.16',lexicon_version='0.16',
            declarations=[self._plain_declaration(n) for n in self._order],statements=[]))
        self._definitions={d['name']:d for d in checked['declarations'] if d['kind']=='definition'}
        self._document['definitions']=deepcopy(self._definitions)
        for field in ('entries','compounds','definitions','primitives'):
            require(all(self._document[field].get(n)==d for n,d in parent[field].items()),'Existing vocabulary changed')
