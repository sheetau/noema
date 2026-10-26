"""Optional local-clock and synchrony relations with contextual records."""
from copy import deepcopy
import json
from noema.constructed import parse,format_graph
from noema.constructed_discourse import normalize_document
from noema.constructed_semantics import FunctionValue
from scripts.observer_time_profile import ROOT,ObserverTimeVocabulary,write_once
from scripts.text_reference_profile import TextPresentation
from scripts.visible_word_forms import Word,canonical,symbol
from scripts.visible_lexical_script import require
from scripts.synchrony_contracts import CONTRACTS,SOURCE_RELATIONS

LIBRARY='examples/v016/synchrony-profile-v1.noema'
BASIS='data/synchrony-profile-basis-v1.json'
MANIFEST='noema/resources/visible-synchrony-profile-v1.json'
EXTRA={'discoursestageafter':dict(parameters=['individual','individual','situation'],result='individual',
    arguments=['document','boundary','context'],meaning_ja='同じ文書と提示文脈で、指定された談話箇所までを含めた論述段階を指す。基準にする箇所の境界は本文で固定する。物理的な現在時刻、文全体の最終状態、そこまでの主張の真理とは区別する。未知の文書・境界・文脈を既定の段階で補わない。')}
REUSED={'adoptsassumption'}
ALL_CONTRACTS={n:r for n,r in CONTRACTS.items() if n not in REUSED}|EXTRA
PARAMETERS={n:r['parameters'] for n,r in ALL_CONTRACTS.items()}
PARTS=('home','above','give','inside','aki','nao','book','round')
SPELLINGS={name:['above','book','red',PARTS[i//8],PARTS[i%8]] for i,name in enumerate(ALL_CONTRACTS)}
CONTEXT=['同じ課題・方式・対象・文書・文脈を保持する。見かけ、可能性、採用、実施を区別する。']
LIMITS=['共通375語は不変。旧関係の型・役割・意味を任意プロファイルとして公開する。',
        '記録の成分位置は公開されたデータの欄であり語義番号ではない。未知の値を既定値で補わない。',
        '参照・引用・前方指示はその内容の真理や実験済みを意味しない。有限診断を全実数の証明としない。']


def library():
    return dict(schema_version='0.16',lexicon_version='0.16',declarations=[
        dict(kind='primitive',name=n,parameters=r['parameters'],result=r['result']) for n,r in ALL_CONTRACTS.items()],statements=[])


def basis():
    return dict(status='optional_synchrony_profile',document=LIBRARY,definitions={},primitives=ALL_CONTRACTS,
        public_contracts={n:dict(arguments=[dict(role=a,sort=s) for a,s in zip(r['arguments'],r['parameters'],strict=True)],
            result=r['result'],interpretation_inputs=CONTEXT) for n,r in ALL_CONTRACTS.items()},
        source_relations=SOURCE_RELATIONS,limitations=LIMITS)


def manifest():
    return dict(schema='noema-visible-optional-profile-1',edition=24,parent_profile=23,core_edition=12,
        library=LIBRARY,basis=BASIS,spellings=SPELLINGS,
        naming_convention='above/book/redを局所時計と同期の語群とする。後続の二要素は公開規約で区別する綴りであり、文中に数値の語義表を置かない。役割と数学は本文定義として示す。')


def prepare():
    write_once(LIBRARY,format_graph(library())+'\n');write_once(BASIS,basis());write_once(MANIFEST,manifest())


class SynchronyVocabulary(ObserverTimeVocabulary):
    def __init__(self):
        super().__init__();data=self.document();parent=deepcopy(data)
        for name in REUSED:
            row=data['compounds'][name];r=CONTRACTS[name]
            require((row['parameters'],row['result'],row['roles'],row['meaning'])==
                    (r['parameters'],r['result'],r['arguments'],r['meaning_ja']),'Reused contract differs')
        require(json.loads((ROOT/MANIFEST).read_text(encoding='utf-8'))==manifest(),'Synchrony profile changed')
        require(parse((ROOT/LIBRARY).read_text(encoding='utf-8'))==library(),'Synchrony declarations changed')
        require(json.loads((ROOT/BASIS).read_text(encoding='utf-8'))==basis(),'Synchrony meanings changed')
        for d in library()['declarations']:
            n=d['name'];r=ALL_CONTRACTS[n];require(n not in self._words,'Profile name collision')
            word=canonical(Word('compound',tuple(SPELLINGS[n])),self)
            data['primitives'][n]=d;data['compounds'][n]=dict(parts=list(word.parts),parameters=d['parameters'],result=d['result'],
                roles=r['arguments'],meaning=r['meaning_ja'],context=CONTEXT,contrast=LIMITS,aliases=[])
            self._words[n]=word
        data.update(schema='noema-visible-synchrony-profile-1',edition=24)
        data['naming_convention']+='\n'+manifest()['naming_convention'];self._document=data
        self._primitives=deepcopy(data['primitives']);self._symbols={n:symbol(w,self) for n,w in self._words.items()}
        require(len(set(self._symbols.values()))==len(self._words),'Profile spelling collision')
        self._by_symbol={s:n for n,s in self._symbols.items()};self._order=self._topological()
        normalize_document(dict(schema_version='0.16',lexicon_version='0.16',declarations=[self._plain_declaration(n) for n in self._order],statements=[]))
        for field in ('entries','compounds','definitions','primitives'):
            require(all(data[field].get(n)==d for n,d in parent[field].items()),'Previous profile changed')


class SynchronyRecords:
    """Known candidate fields, without default truth or physical validation."""
    def __init__(self,*,local=None,local_readings=None,directions=None,direction_readings=None,
                 clocks=None,histories=None,stages=None):
        self.local=self.rows(local or {},2);self.directions=self.rows(directions or {},6)
        self.local_readings=self.cuts(local_readings or {});self.histories=self.cuts(histories or {})
        self.direction_readings=self.rows(direction_readings or {},6)
        for row in self.direction_readings.values():self.cuts(dict(enumerate(row)))
        self.clocks=dict(clocks or {});self.stages=dict(stages or {})

    @staticmethod
    def rows(rows,size):
        require(all(isinstance(v,(tuple,list)) and len(v)==size for v in rows.values()),'Wrong synchrony record size')
        return {k:tuple(v) for k,v in rows.items()}

    @staticmethod
    def cuts(rows):
        require(all(isinstance(x,FunctionValue) and x.parameters==('number',) and x.result=='truth'
                    for x in rows.values()),'Expected cut-shaped candidate');return dict(rows)

    @staticmethod
    def known(table,key):
        require(key in table,'Unknown synchrony record input');return table[key]

    @classmethod
    def component(cls,table,key,slot,size,base):
        from fractions import Fraction
        require(type(slot) in (int,Fraction),'Expected exact synchrony slot')
        slot=Fraction(slot);require(slot.denominator==1 and base<=slot<base+size,'Unknown synchrony slot')
        return cls.known(table,key)[int(slot)-base]

    def handlers(self):
        return dict(localcomponent=lambda e,c,n,s:self.component(self.local,(e,c,s),n,2,1),
            localreading=lambda e,c,u,s:self.known(self.local_readings,(e,c,u,s)),
            directioncomponent=lambda p,n,s:self.component(self.directions,(p,s),n,6,0),
            directionreading=lambda p,n,t,f,u,s:self.component(self.direction_readings,(p,t,f,u,s),n,6,0),
            configurationclock=lambda c,p:self.known(self.clocks,(c,p)),
            configurationreading=lambda c,k,e,f,u,s:self.known(self.histories,(c,k,e,f,u,s)),
            discoursestageafter=lambda d,n,s:self.known(self.stages,(d,n,s)))
