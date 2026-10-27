"""Optional mechanical-clock, rotating-body and physical-inference conventions."""
from copy import deepcopy
import json
from noema.constructed import parse,format_graph
from noema.constructed_discourse import normalize_document,function_sort,description_sort
from noema.constructed_semantics import FunctionValue,DescriptionValue
from scripts.origin_clock_visible_profile import ROOT,OriginClockVisibleVocabulary,write_once,CUT
from scripts.clock_transport_visible_profile_contracts import CONTRACTS,SOURCE_RELATIONS
from scripts.visible_word_forms import Word,canonical,symbol
from scripts.visible_lexical_script import require

LIBRARY='examples/v016/clock-transport-visible-profile-v1.noema'
BASIS='data/clock-transport-visible-profile-basis-v1.json'
MANIFEST='noema/resources/visible-clock-transport-visible-profile-v1.json'
ALL_CONTRACTS=CONTRACTS
PARAMETERS={n:r['parameters'] for n,r in ALL_CONTRACTS.items()}
PARTS=('home','above','give','inside','aki','nao','book','round')
SPELLINGS={'mechanicalpart': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'above', 'rain'],
 'restoringrotationaloscillator': ['above',
                                   'round',
                                   'treeone',
                                   'home',
                                   'nao',
                                   'book',
                                   'birdone',
                                   'above',
                                   'town'],
 'regulatesclockrate': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'above', 'home'],
 'clockcondition': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'above', 'above'],
 'othercomparisoncondition': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'above', 'give'],
 'completecomparisonconditions': ['above',
                                  'round',
                                  'treeone',
                                  'home',
                                  'nao',
                                  'book',
                                  'birdone',
                                  'above',
                                  'inside'],
 'attachedsurfaceclock': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'above', 'birdone'],
 'uniformbodyrotation': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'above', 'treeone'],
 'axialcoordinatequantity': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'above', 'aki'],
 'axisdistancequantity': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'above', 'nao'],
 'bodysurfacepoint': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'above', 'book'],
 'verysmallratedifference': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'above', 'fruit'],
 'presentsdistinctivefocus': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'above', 'red'],
 'physicalinferencecandidate': ['above',
                                'round',
                                'treeone',
                                'home',
                                'nao',
                                'book',
                                'birdone',
                                'above',
                                'round'],
 'designatescurveelapsedtimerule': ['above',
                                    'round',
                                    'treeone',
                                    'home',
                                    'nao',
                                    'book',
                                    'birdone',
                                    'above',
                                    'bird']}
CONTEXT=['機械的な構成・調整、物体・場所・回転軸、同じ比較範囲と設定を引数として保持する。', '著者・主張・焦点・先行議論の順序、推論の基準状況と候補、型付き規則の全引数を区別する。']
LIMITS=['共通375語と固定アルファベットを維持し、旧採用規約15件を任意プロファイルとして公開する。原文の文ごとに原始述語を追加するものではない。',
 '機械の構造一致と時計の校正、その他の条件の完全一致は別々に要求する。物理的な時計の実現や実際の地球への適用を、この規約だけで証明しない。',
 '曲線経路への拡張は本文の明示した仮定として扱う。特異な点への注意喚起、引用や表記の識別は内容の真理を含意しない。',
 '物理的帰結の候補を後件の真偽で選別しない。候補の非空性と基準状況の包含、全候補での成立は本文で要求する。',
 '非常に小さい差の具体的な数値閾値を補わない。有限診断を全実数域の証明や独立読解と扱わない。']


def library():
    return dict(schema_version='0.16',lexicon_version='0.16',declarations=[
        dict(kind='primitive',name=n,parameters=r['parameters'],result=r['result']) for n,r in ALL_CONTRACTS.items()],statements=[])


def basis():
    return dict(status='optional_clock_transport_visible_profile',document=LIBRARY,definitions={},primitives=ALL_CONTRACTS,
        public_contracts={n:dict(arguments=[dict(role=a,sort=s) for a,s in zip(r['arguments'],r['parameters'],strict=True)],
            result=r['result'],interpretation_inputs=CONTEXT) for n,r in ALL_CONTRACTS.items()},
        source_relations=SOURCE_RELATIONS,limitations=LIMITS)


def manifest():
    return dict(schema='noema-visible-optional-profile-1',edition=61,parent_profile=60,core_edition=12,
        library=LIBRARY,basis=BASIS,spellings=SPELLINGS,
        naming_convention='above/round/treeone/home/nao/book/birdone/aboveを機械時計・回転物体・物理的推論の語群とする。後続要素は公開規約を区別する綴りであり、文中の語義番号ではない。機構・物体・軸・比較条件・提示と推論の範囲は本文で結ぶ。')


def prepare():
    write_once(LIBRARY,format_graph(library())+'\n');write_once(BASIS,basis());write_once(MANIFEST,manifest())


class ClockTransportVisibleVocabulary(OriginClockVisibleVocabulary):
    def __init__(self):
        super().__init__();data=self.document();parent=deepcopy(data)
        require(json.loads((ROOT/MANIFEST).read_text(encoding='utf-8'))==manifest(),'ClockTransport-visible profile changed')
        require(parse((ROOT/LIBRARY).read_text(encoding='utf-8'))==library(),'ClockTransport-visible declarations changed')
        require(json.loads((ROOT/BASIS).read_text(encoding='utf-8'))==basis(),'ClockTransport-visible meanings changed')
        for d in library()['declarations']:
            n=d['name'];r=ALL_CONTRACTS[n];require(n not in self._words,'Profile name collision')
            word=canonical(Word('compound',tuple(SPELLINGS[n])),self)
            data['primitives'][n]=d;data['compounds'][n]=dict(parts=list(word.parts),parameters=d['parameters'],result=d['result'],
                roles=r['arguments'],meaning=r['meaning_ja'],context=CONTEXT,contrast=LIMITS,aliases=[])
            self._words[n]=word
        data.update(schema='noema-visible-clock-transport-visible-profile-1',edition=61)
        data['naming_convention']+='\n'+manifest()['naming_convention'];self._document=data
        self._primitives=deepcopy(data['primitives']);self._symbols={n:symbol(w,self) for n,w in self._words.items()}
        require(len(set(self._symbols.values()))==len(self._words),'Profile spelling collision')
        self._by_symbol={s:n for n,s in self._symbols.items()};self._order=self._topological()
        normalize_document(dict(schema_version='0.16',lexicon_version='0.16',declarations=[self._plain_declaration(n) for n in self._order],statements=[]))
        for field in ('entries','compounds','definitions','primitives'):
            require(all(data[field].get(n)==d for n,d in parent[field].items()),'Previous profile changed')
