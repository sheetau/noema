"""Optional frame-law and light-segment relations with known record fields."""
from copy import deepcopy
import json
from noema.constructed import parse,format_graph
from noema.constructed_discourse import normalize_document
from noema.constructed_semantics import FunctionValue
from scripts.light_speed_time_profile import ROOT,LightSpeedTimeVocabulary,write_once,CUT
from scripts.text_reference_profile import TextPresentation
from scripts.visible_word_forms import Word,canonical,symbol
from scripts.visible_lexical_script import require
from scripts.two_principles_contracts import CONTRACTS,SOURCE_RELATIONS,FIELD_CONTRACTS

LIBRARY='examples/v016/two-principles-profile-v1.noema'
BASIS='data/two-principles-profile-basis-v1.json'
MANIFEST='noema/resources/visible-two-principles-profile-v1.json'
EXTRA={
 'segmententity':dict(parameters=['individual','number'],result='individual',arguments=['segment','slot'],
    meaning_ja='同じ光伝播区間の記録から個体候補を取得する。欄0は光、1は放出元、2は放出出来事、3は始点出来事、4は終点出来事、5は始点時計、6は終点時計、7は始点場所、8は終点場所。欄は記録の成分位置であり語義番号ではない。物理的な帰属・真空条件・時刻規約は別の関係で指定する。未知の記録や欄を既定値で補わない。'),
 'segmentreading':dict(parameters=['individual','number'],result=CUT,arguments=['segment','slot'],
    meaning_ja='同じ光伝播区間の記録から切断型の読みの候補を取得する。欄0は始点時計の読み、1は終点時計の読み、2はその区間の幾何学的な光路長。記録は同じ系・単位・設定に結ばれる。経路長を端点間距離や往復距離へ替えない。取得だけでは実数の妥当性・実測・物理的成立を主張せず、未知の記録や欄を補わない。'),
 'frameaxisreference':dict(parameters=['individual','number','situation'],result='individual',arguments=['frame','component','context'],
    meaning_ja='同じ座標系・提示文脈で、第一・第二・第三の座標成分を指定する軸への参照を取得する。成分番号は1から3で、座標表示の欄に対応する。軸の物理的な方向・正規直交性・系間の対応は座標規約で別に指定し、名前や番号だけから系間の方向一致を導かない。未知の系・文脈・成分番号を補わない。')}
REUSED={'newtonianframe'}
ALL_CONTRACTS={n:r for n,r in CONTRACTS.items() if n not in REUSED}|EXTRA
PARAMETERS={n:r['parameters'] for n,r in ALL_CONTRACTS.items()}
PARTS=('home','above','give','inside','aki','nao','book','round')
SPELLINGS={name:['above','book','aki',PARTS[i//8],PARTS[i%8]] for i,name in enumerate(ALL_CONTRACTS)}
CONTEXT=['同じ課題・方式・対象・文書・文脈を保持する。見かけ、可能性、採用、実施を区別する。']
LIMITS=['共通375語は不変。旧関係の型・役割・意味を任意プロファイルとして公開する。',
        '記録の成分位置は公開されたデータの欄であり語義番号ではない。未知の値を既定値で補わない。',
        '参照・引用・前方指示はその内容の真理や実験済みを意味しない。有限診断を全実数の証明としない。']


def library():
    return dict(schema_version='0.16',lexicon_version='0.16',declarations=[
        dict(kind='primitive',name=n,parameters=r['parameters'],result=r['result']) for n,r in ALL_CONTRACTS.items()],statements=[])


def basis():
    return dict(status='optional_two_principles_profile',document=LIBRARY,definitions={},primitives=ALL_CONTRACTS,
        public_contracts={n:dict(arguments=[dict(role=a,sort=s) for a,s in zip(r['arguments'],r['parameters'],strict=True)],
            result=r['result'],interpretation_inputs=CONTEXT) for n,r in ALL_CONTRACTS.items()},
        source_relations=SOURCE_RELATIONS,limitations=LIMITS)


def manifest():
    return dict(schema='noema-visible-optional-profile-1',edition=26,parent_profile=25,core_edition=12,
        library=LIBRARY,basis=BASIS,spellings=SPELLINGS,
        naming_convention='above/book/akiを物理系の法則と光伝播区間の語群とする。後続の二要素は公開規約で区別する綴りであり、文中に数値の語義表を置かない。役割と数学は本文定義として示す。')


def prepare():
    write_once(LIBRARY,format_graph(library())+'\n');write_once(BASIS,basis());write_once(MANIFEST,manifest())


class TwoPrinciplesVocabulary(LightSpeedTimeVocabulary):
    def __init__(self):
        super().__init__();data=self.document();parent=deepcopy(data)
        for name in REUSED:
            row=data['compounds'][name];r=CONTRACTS[name]
            require((row['parameters'],row['result'],row['roles'],row['meaning'])==
                    (r['parameters'],r['result'],r['arguments'],r['meaning_ja']),'Reused contract differs')
        require(json.loads((ROOT/MANIFEST).read_text(encoding='utf-8'))==manifest(),'Two-principles profile changed')
        require(parse((ROOT/LIBRARY).read_text(encoding='utf-8'))==library(),'Two-principles declarations changed')
        require(json.loads((ROOT/BASIS).read_text(encoding='utf-8'))==basis(),'Two-principles meanings changed')
        for d in library()['declarations']:
            n=d['name'];r=ALL_CONTRACTS[n];require(n not in self._words,'Profile name collision')
            word=canonical(Word('compound',tuple(SPELLINGS[n])),self)
            data['primitives'][n]=d;data['compounds'][n]=dict(parts=list(word.parts),parameters=d['parameters'],result=d['result'],
                roles=r['arguments'],meaning=r['meaning_ja'],context=CONTEXT,contrast=LIMITS,aliases=[])
            self._words[n]=word
        data.update(schema='noema-visible-two-principles-profile-1',edition=26)
        data['naming_convention']+='\n'+manifest()['naming_convention'];self._document=data
        self._primitives=deepcopy(data['primitives']);self._symbols={n:symbol(w,self) for n,w in self._words.items()}
        require(len(set(self._symbols.values()))==len(self._words),'Profile spelling collision')
        self._by_symbol={s:n for n,s in self._symbols.items()};self._order=self._topological()
        normalize_document(dict(schema_version='0.16',lexicon_version='0.16',declarations=[self._plain_declaration(n) for n in self._order],statements=[]))
        for field in ('entries','compounds','definitions','primitives'):
            require(all(data[field].get(n)==d for n,d in parent[field].items()),'Previous profile changed')


class PrincipleRecords:
    """Known segment fields, axes, scales and coordinate candidates."""
    def __init__(self,*,entities=None,readings=None,axes=None,lengthunits=None,timeunits=None,
                 velocities=None,moments=None,coordinates=None):
        from scripts.synchrony_profile import SynchronyRecords
        self.entities=SynchronyRecords.rows(entities or {},9)
        self.readings=SynchronyRecords.rows(readings or {},3)
        for row in self.readings.values():SynchronyRecords.cuts(dict(enumerate(row)))
        self.axes=SynchronyRecords.rows(axes or {},3)
        self.lengthunits=dict(lengthunits or {});self.timeunits=dict(timeunits or {})
        self.velocities=SynchronyRecords.cuts(velocities or {})
        self.moments=SynchronyRecords.cuts(moments or {});self.coordinates=SynchronyRecords.cuts(coordinates or {})

    @staticmethod
    def known(table,key):
        require(key in table,'Unknown principle record');return table[key]

    @classmethod
    def component(cls,table,key,slot,size,base):
        from fractions import Fraction
        require(type(slot) in (int,Fraction),'Expected exact principle slot')
        slot=Fraction(slot);require(slot.denominator==1 and base<=slot<base+size,'Unknown principle slot')
        return cls.known(table,key)[int(slot)-base]

    def handlers(self):return dict(segmententity=lambda t,n:self.component(self.entities,t,n,9,0),
        segmentreading=lambda t,n:self.component(self.readings,t,n,3,0),
        frameaxisreference=lambda f,n,s:self.component(self.axes,(f,s),n,3,1),
        comparisonlengthunit=lambda f,g,s:self.known(self.lengthunits,(f,g,s)),
        comparisontimeunit=lambda f,g,s:self.known(self.timeunits,(f,g,s)),
        commonvelocity=lambda f,g,l,t,a,s:self.known(self.velocities,(f,g,l,t,a,s)),
        momentreading=lambda m,f,t,s:self.known(self.moments,(m,f,t,s)),
        pointcoordinate=lambda p,m,f,l,a,s:self.known(self.coordinates,(p,m,f,l,a,s)))
