"""Optional composition-topic, theorem-discourse, typed task and prior-content conventions."""
from copy import deepcopy
import json
from noema.constructed import parse,format_graph
from noema.constructed_discourse import normalize_document,function_sort,description_sort
from noema.constructed_semantics import FunctionValue,DescriptionValue
from scripts.clock_transport_visible_profile import ROOT,ClockTransportVisibleVocabulary,write_once,CUT
from scripts.velocity_addition_setting_visible_profile_contracts import CONTRACTS,SOURCE_RELATIONS
from scripts.visible_word_forms import Word,canonical,symbol
from scripts.visible_lexical_script import require

LIBRARY='examples/v016/velocity-addition-setting-visible-profile-v1.noema'
BASIS='data/velocity-addition-setting-visible-profile-basis-v1.json'
MANIFEST='noema/resources/visible-velocity-addition-setting-visible-profile-v1.json'
ALL_CONTRACTS=CONTRACTS
PARAMETERS={n:r['parameters'] for n,r in ALL_CONTRACTS.items()}
PARTS=('home','above','give','inside','aki','nao','book','round')
SPELLINGS={'studiestriplequantitycomposition': ['above',
                                      'round',
                                      'treeone',
                                      'home',
                                      'nao',
                                      'book',
                                      'birdone',
                                      'give',
                                      'rain'],
 'theoreminquiry': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'give', 'town'],
 'presentspositionfunctiontask': ['above',
                                  'round',
                                  'treeone',
                                  'home',
                                  'nao',
                                  'book',
                                  'birdone',
                                  'give',
                                  'home'],
 'referstopriorestablishedcontent': ['above',
                                     'round',
                                     'treeone',
                                     'home',
                                     'nao',
                                     'book',
                                     'birdone',
                                     'give',
                                     'above']}
CONTEXT=['同じ対象・二基準・適用状況と三つの三成分量を引用関係へ保持する。', '主題、定理の論述、解くべき問い、先行節で展開した内容の参照を区別する。']
LIMITS=['共通375語と固定アルファベットを維持し、既存の採用規約4件を任意プロファイルで公開する。',
 '課題提示の意味は既存zdcと共有し、今回の回答型である個体役割と切断を受け切断を返す関数を保つ。',
 '見出しや引用から公式の正しさ、規則の全域性、答えの存在・唯一性、証明済みを導かない。',
 '物理的な量・同一対象・全出来事の条件は既存の本文定義で合成する。数値の一覧で代用しない。',
 '有限の識別診断、復号、意味判断、独立読解は別に扱う。']


def library():
    return dict(schema_version='0.16',lexicon_version='0.16',declarations=[
        dict(kind='primitive',name=n,parameters=r['parameters'],result=r['result']) for n,r in ALL_CONTRACTS.items()],statements=[])


def basis():
    return dict(status='optional_velocity_addition_setting_visible_profile',document=LIBRARY,definitions={},primitives=ALL_CONTRACTS,
        public_contracts={n:dict(arguments=[dict(role=a,sort=s) for a,s in zip(r['arguments'],r['parameters'],strict=True)],
            result=r['result'],interpretation_inputs=CONTEXT) for n,r in ALL_CONTRACTS.items()},
        source_relations=SOURCE_RELATIONS,limitations=LIMITS)


def manifest():
    return dict(schema='noema-visible-optional-profile-1',edition=62,parent_profile=61,core_edition=12,
        library=LIBRARY,basis=BASIS,spellings=SPELLINGS,
        naming_convention='above/round/treeone/home/nao/book/birdone/giveを三成分量の合成主題・定理の論述・型付き課題と先行内容の参照の語群とする。後続要素は公開規約を区別する綴りであり、文中の語義番号ではない。物理量と対象、問いの条件、先行区分と内容は本文で結ぶ。')


def prepare():
    write_once(LIBRARY,format_graph(library())+'\n');write_once(BASIS,basis());write_once(MANIFEST,manifest())


class VelocityAdditionSettingVisibleVocabulary(ClockTransportVisibleVocabulary):
    def __init__(self):
        super().__init__();data=self.document();parent=deepcopy(data)
        require(json.loads((ROOT/MANIFEST).read_text(encoding='utf-8'))==manifest(),'VelocityAdditionSetting-visible profile changed')
        require(parse((ROOT/LIBRARY).read_text(encoding='utf-8'))==library(),'VelocityAdditionSetting-visible declarations changed')
        require(json.loads((ROOT/BASIS).read_text(encoding='utf-8'))==basis(),'VelocityAdditionSetting-visible meanings changed')
        for d in library()['declarations']:
            n=d['name'];r=ALL_CONTRACTS[n];require(n not in self._words,'Profile name collision')
            word=canonical(Word('compound',tuple(SPELLINGS[n])),self)
            data['primitives'][n]=d;data['compounds'][n]=dict(parts=list(word.parts),parameters=d['parameters'],result=d['result'],
                roles=r['arguments'],meaning=r['meaning_ja'],context=CONTEXT,contrast=LIMITS,aliases=[])
            self._words[n]=word
        data.update(schema='noema-visible-velocity-addition-setting-visible-profile-1',edition=62)
        data['naming_convention']+='\n'+manifest()['naming_convention'];self._document=data
        self._primitives=deepcopy(data['primitives']);self._symbols={n:symbol(w,self) for n,w in self._words.items()}
        require(len(set(self._symbols.values()))==len(self._words),'Profile spelling collision')
        self._by_symbol={s:n for n,s in self._symbols.items()};self._order=self._topological()
        normalize_document(dict(schema_version='0.16',lexicon_version='0.16',declarations=[self._plain_declaration(n) for n in self._order],statements=[]))
        for field in ('entries','compounds','definitions','primitives'):
            require(all(data[field].get(n)==d for n,d in parent[field].items()),'Previous profile changed')
