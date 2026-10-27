"""Optional clock calibration alternatives, described real questions and time-unit conversion."""
from copy import deepcopy
import json
from noema.constructed import parse,format_graph
from noema.constructed_discourse import normalize_document,function_sort,description_sort
from noema.constructed_semantics import FunctionValue,DescriptionValue
from scripts.shape_dimension_visible_profile import ROOT,ShapeDimensionVisibleVocabulary,write_once,CUT
from scripts.origin_clock_visible_profile_contracts import CONTRACTS,SOURCE_RELATIONS
from scripts.visible_word_forms import Word,canonical,symbol
from scripts.visible_lexical_script import require

LIBRARY='examples/v016/origin-clock-visible-profile-v1.noema'
BASIS='data/origin-clock-visible-profile-basis-v1.json'
MANIFEST='noema/resources/visible-origin-clock-visible-profile-v1.json'
ALL_CONTRACTS=CONTRACTS
PARAMETERS={n:r['parameters'] for n,r in ALL_CONTRACTS.items()}
PARTS=('home','above','give','inside','aki','nao','book','round')
SPELLINGS={'clockrestcalibrationtrial': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'home', 'rain'],
 'describedrealquestionpresentation': ['above',
                                       'round',
                                       'treeone',
                                       'home',
                                       'nao',
                                       'book',
                                       'birdone',
                                       'home',
                                       'town'],
 'timeunitlinearconversion': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'home', 'home']}
CONTEXT=['同じ時計・系・実際の設定と許容される代替設定、または同じ時間量・単位・換算尺度を保持する。', '問いの記述と著者による提示を区別し、答えの存在・一意性・発見済みを追加しない。']
LIMITS=['共通375語と固定アルファベットを維持し、旧採用規約3件を任意プロファイルとして公開する。文ごとの原始述語ではない。',
 '時計の表示能力の物理的実現、測定装置の精度、秒の歴史的実現方法を、この規約の公開だけで構成済みとしない。',
 '線形換算に原点移動を加えない。正の尺度と時間単位の型は本文の定義で要求する。',
 '全時刻・全記録・実数の量化を有限標本に縮めず、有限診断を一般証明や独立読解と扱わない。']


def library():
    return dict(schema_version='0.16',lexicon_version='0.16',declarations=[
        dict(kind='primitive',name=n,parameters=r['parameters'],result=r['result']) for n,r in ALL_CONTRACTS.items()],statements=[])


def basis():
    return dict(status='optional_origin_clock_visible_profile',document=LIBRARY,definitions={},primitives=ALL_CONTRACTS,
        public_contracts={n:dict(arguments=[dict(role=a,sort=s) for a,s in zip(r['arguments'],r['parameters'],strict=True)],
            result=r['result'],interpretation_inputs=CONTEXT) for n,r in ALL_CONTRACTS.items()},
        source_relations=SOURCE_RELATIONS,limitations=LIMITS)


def manifest():
    return dict(schema='noema-visible-optional-profile-1',edition=60,parent_profile=59,core_edition=12,
        library=LIBRARY,basis=BASIS,spellings=SPELLINGS,
        naming_convention='above/round/treeone/home/nao/book/birdone/homeを時計の代替設定・実数値の問い・時間単位換算の語群とする。後続要素は公開規約を区別する綴りであり、文中の語義番号ではない。時計・系・単位・作用範囲は本文で結ぶ。')


def prepare():
    write_once(LIBRARY,format_graph(library())+'\n');write_once(BASIS,basis());write_once(MANIFEST,manifest())


class OriginClockVisibleVocabulary(ShapeDimensionVisibleVocabulary):
    def __init__(self):
        super().__init__();data=self.document();parent=deepcopy(data)
        require(json.loads((ROOT/MANIFEST).read_text(encoding='utf-8'))==manifest(),'OriginClock-visible profile changed')
        require(parse((ROOT/LIBRARY).read_text(encoding='utf-8'))==library(),'OriginClock-visible declarations changed')
        require(json.loads((ROOT/BASIS).read_text(encoding='utf-8'))==basis(),'OriginClock-visible meanings changed')
        for d in library()['declarations']:
            n=d['name'];r=ALL_CONTRACTS[n];require(n not in self._words,'Profile name collision')
            word=canonical(Word('compound',tuple(SPELLINGS[n])),self)
            data['primitives'][n]=d;data['compounds'][n]=dict(parts=list(word.parts),parameters=d['parameters'],result=d['result'],
                roles=r['arguments'],meaning=r['meaning_ja'],context=CONTEXT,contrast=LIMITS,aliases=[])
            self._words[n]=word
        data.update(schema='noema-visible-origin-clock-visible-profile-1',edition=60)
        data['naming_convention']+='\n'+manifest()['naming_convention'];self._document=data
        self._primitives=deepcopy(data['primitives']);self._symbols={n:symbol(w,self) for n,w in self._words.items()}
        require(len(set(self._symbols.values()))==len(self._words),'Profile spelling collision')
        self._by_symbol={s:n for n,s in self._symbols.items()};self._order=self._topological()
        normalize_document(dict(schema_version='0.16',lexicon_version='0.16',declarations=[self._plain_declaration(n) for n in self._order],statements=[]))
        for field in ('entries','compounds','definitions','primitives'):
            require(all(data[field].get(n)==d for n,d in parent[field].items()),'Previous profile changed')
