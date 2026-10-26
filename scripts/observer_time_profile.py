"""Optional observer-time relations with known, contextual record components."""
from copy import deepcopy
import json
from noema.constructed import parse,format_graph
from noema.constructed_discourse import normalize_document
from noema.constructed_semantics import FunctionValue
from scripts.temporal_discourse_profile import ROOT,TemporalDiscourseVocabulary,write_once
from scripts.text_reference_profile import TextPresentation
from scripts.visible_word_forms import Word,canonical,symbol
from scripts.visible_lexical_script import require
from scripts.observer_time_contracts import CONTRACTS,SOURCE_RELATIONS

LIBRARY='examples/v016/observer-time-profile-v1.noema'
BASIS='data/observer-time-profile-basis-v1.json'
MANIFEST='noema/resources/visible-observer-time-profile-v1.json'
ALL_CONTRACTS=CONTRACTS
PARAMETERS={n:r['parameters'] for n,r in CONTRACTS.items()}
PARTS=('home','above','give','inside','aki','nao','book','round')
SPELLINGS={name:['above','book','round',PARTS[i//8],PARTS[i%8]] for i,name in enumerate(CONTRACTS)}
CONTEXT=['同じ課題・方式・対象・文書・文脈を保持する。見かけ、可能性、採用、実施を区別する。']
LIMITS=['共通375語は不変。旧関係の型・役割・意味を任意プロファイルとして公開する。',
        '記録の成分位置は公開されたデータの欄であり語義番号ではない。未知の値を既定値で補わない。',
        '参照・引用・前方指示はその内容の真理や実験済みを意味しない。有限診断を全実数の証明としない。']


def library():
    return dict(schema_version='0.16',lexicon_version='0.16',declarations=[
        dict(kind='primitive',name=n,parameters=r['parameters'],result=r['result']) for n,r in ALL_CONTRACTS.items()],statements=[])


def basis():
    return dict(status='optional_observer_time_profile',document=LIBRARY,definitions={},primitives=ALL_CONTRACTS,
        public_contracts={n:dict(arguments=[dict(role=a,sort=s) for a,s in zip(r['arguments'],r['parameters'],strict=True)],
            result=r['result'],interpretation_inputs=CONTEXT) for n,r in ALL_CONTRACTS.items()},
        source_relations=SOURCE_RELATIONS,limitations=LIMITS)


def manifest():
    return dict(schema='noema-visible-optional-profile-1',edition=23,parent_profile=22,core_edition=12,
        library=LIBRARY,basis=BASIS,spellings=SPELLINGS,
        naming_convention='above/book/roundを時間の定義案と観測者の語群とする。後続の二要素は公開規約で区別する綴りであり、文中に数値の語義表を置かない。役割と数学は本文定義として示す。')


def prepare():
    write_once(LIBRARY,format_graph(library())+'\n');write_once(BASIS,basis());write_once(MANIFEST,manifest())


class ObserverTimeVocabulary(TemporalDiscourseVocabulary):
    def __init__(self):
        super().__init__();data=self.document();parent=deepcopy(data)
        require(json.loads((ROOT/MANIFEST).read_text(encoding='utf-8'))==manifest(),'Observer-time profile changed')
        require(parse((ROOT/LIBRARY).read_text(encoding='utf-8'))==library(),'Observer-time declarations changed')
        require(json.loads((ROOT/BASIS).read_text(encoding='utf-8'))==basis(),'Observer-time meanings changed')
        for d in library()['declarations']:
            n=d['name'];r=ALL_CONTRACTS[n];require(n not in self._words,'Profile name collision')
            word=canonical(Word('compound',tuple(SPELLINGS[n])),self)
            data['primitives'][n]=d;data['compounds'][n]=dict(parts=list(word.parts),parameters=d['parameters'],result=d['result'],
                roles=r['arguments'],meaning=r['meaning_ja'],context=CONTEXT,contrast=LIMITS,aliases=[])
            self._words[n]=word
        data.update(schema='noema-visible-observer-time-profile-1',edition=23)
        data['naming_convention']+='\n'+manifest()['naming_convention'];self._document=data
        self._primitives=deepcopy(data['primitives']);self._symbols={n:symbol(w,self) for n,w in self._words.items()}
        require(len(set(self._symbols.values()))==len(self._words),'Profile spelling collision')
        self._by_symbol={s:n for n,s in self._symbols.items()};self._order=self._topological()
        normalize_document(dict(schema_version='0.16',lexicon_version='0.16',declarations=[self._plain_declaration(n) for n in self._order],statements=[]))
        for field in ('entries','compounds','definitions','primitives'):
            require(all(data[field].get(n)==d for n,d in parent[field].items()),'Previous profile changed')


class ReceptionRecords:
    """Known records; component retrieval never supplies physical judgments."""
    def __init__(self,receptions,readings,cases,contexts):
        self.receptions=self.rows(receptions,5);self.cases=self.rows(cases,7)
        self.readings=dict(readings);self.contexts=dict(contexts)
        require(all(isinstance(x,FunctionValue) and x.parameters==('number',) and x.result=='truth'
            for x in self.readings.values()),'Expected cut-shaped reading candidates')

    @staticmethod
    def rows(rows,size):
        require(all(isinstance(v,(tuple,list)) and len(v)==size for v in rows.values()),'Wrong record field count')
        return {k:tuple(v) for k,v in rows.items()}

    @staticmethod
    def known(table,key):
        require(key in table,'Unknown reception record input');return table[key]

    def component(self,table,record,slot,context,size):
        slot=TextPresentation.coordinate(slot)
        require(slot<=size,'Unknown reception record slot')
        return self.known(table,(record,context))[slot-1]

    def handlers(self):
        return dict(receptioncomponent=lambda r,n,s:self.component(self.receptions,r,n,s,5),
            casecomponent=lambda r,n,s:self.component(self.cases,r,n,s,7),
            receptionreading=lambda r,c,u,s:self.known(self.readings,(r,c,u,s)),
            casecontext=lambda r,s:self.known(self.contexts,(r,s)))
