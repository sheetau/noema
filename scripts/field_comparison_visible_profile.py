"""Optional display correspondence for a closed two-field equation form."""
from copy import deepcopy
import json
from noema.constructed import parse,format_graph
from noema.constructed_discourse import normalize_document,function_sort,description_sort
from noema.constructed_semantics import FunctionValue,DescriptionValue
from scripts.moving_field_visible_profile import ROOT,MovingFieldVisibleVocabulary,write_once,CUT
from scripts.field_comparison_visible_profile_contracts import CONTRACTS,SOURCE_RELATIONS
from scripts.visible_word_forms import Word,canonical,symbol
from scripts.visible_lexical_script import require

LIBRARY='examples/v016/field-comparison-visible-profile-v1.noema'
BASIS='data/field-comparison-visible-profile-basis-v1.json'
MANIFEST='noema/resources/visible-field-comparison-visible-profile-v1.json'
ALL_CONTRACTS=CONTRACTS
PARAMETERS={n:r['parameters'] for n,r in ALL_CONTRACTS.items()}
PARTS=('home','above','give','inside','aki','nao','book','round')
SPELLINGS={'twofielddisplayform': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'rain']}
CONTEXT=['同じ表示・閉じた式・二場・領域・光速度・文脈を対応させる。',
 '三軸・四座標・偏微分・差の符号・定数と各引数位置を保持する。',
 '分母払いと式の配置順の正規化は別に明示し、元資料と照合する。']
LIMITS=['固定アルファベットと共通375語を維持し、採用済みの表示対応規約を任意profile70へ公開する。',
 '表示と閉じた式の対応は、式の真理、場の数値の同一性や比例の証明ではない。',
 '係数ψの参照・速度のみの引数・全点全六成分への適用は本文で構成する。',
 '正負零の係数と定数関数を排除せず、非零・正・偶・値1を補わない。',
 '同じ微分方程式に適合しても比例しない既存反例と、原著者への推論の帰属を保つ。',
 '有限診断を全実数・全関数域の証明や人間による独立読解とは扱わない。']



def library():
    return dict(schema_version='0.16',lexicon_version='0.16',declarations=[
        dict(kind='primitive',name=n,parameters=r['parameters'],result=r['result']) for n,r in ALL_CONTRACTS.items()],statements=[])


def basis():
    return dict(status='optional_field_comparison_visible_profile',document=LIBRARY,definitions={},primitives=ALL_CONTRACTS,
        public_contracts={n:dict(arguments=[dict(role=a,sort=s) for a,s in zip(r['arguments'],r['parameters'],strict=True)],
            result=r['result'],interpretation_inputs=CONTEXT) for n,r in ALL_CONTRACTS.items()},
        source_relations=SOURCE_RELATIONS,limitations=LIMITS)


def manifest():
    return dict(schema='noema-visible-optional-profile-1',edition=70,parent_profile=69,core_edition=12,
        library=LIBRARY,basis=BASIS,spellings=SPELLINGS,
        naming_convention='above/round/treeone/home/nao/book/birdone/fruit/rainを閉じた二場方程式の表示対応規約の綴りとする。等価性・全点全成分の比例・理由と必要性は本文で合成する。')


def prepare():
    write_once(LIBRARY,format_graph(library())+'\n');write_once(BASIS,basis());write_once(MANIFEST,manifest())


class FieldComparisonVisibleVocabulary(MovingFieldVisibleVocabulary):
    def __init__(self):
        super().__init__();data=self.document();parent=deepcopy(data)
        require(json.loads((ROOT/MANIFEST).read_text(encoding='utf-8'))==manifest(),'FieldComparison-visible profile changed')
        require(parse((ROOT/LIBRARY).read_text(encoding='utf-8'))==library(),'FieldComparison-visible declarations changed')
        require(json.loads((ROOT/BASIS).read_text(encoding='utf-8'))==basis(),'FieldComparison-visible meanings changed')
        for d in library()['declarations']:
            n=d['name'];r=ALL_CONTRACTS[n];require(n not in self._words,'Profile name collision')
            word=canonical(Word('compound',tuple(SPELLINGS[n])),self)
            data['primitives'][n]=d;data['compounds'][n]=dict(parts=list(word.parts),parameters=d['parameters'],result=d['result'],
                roles=r['arguments'],meaning=r['meaning_ja'],context=CONTEXT,contrast=LIMITS,aliases=[])
            self._words[n]=word
        data.update(schema='noema-visible-field-comparison-visible-profile-1',edition=70)
        data['naming_convention']+='\n'+manifest()['naming_convention'];self._document=data
        self._primitives=deepcopy(data['primitives']);self._symbols={n:symbol(w,self) for n,w in self._words.items()}
        require(len(set(self._symbols.values()))==len(self._words),'Profile spelling collision')
        self._by_symbol={s:n for n,s in self._symbols.items()};self._order=self._topological()
        normalize_document(dict(schema_version='0.16',lexicon_version='0.16',declarations=[self._plain_declaration(n) for n in self._order],statements=[]))
        for field in ('entries','compounds','definitions','primitives'):
            require(all(data[field].get(n)==d for n,d in parent[field].items()),'Previous profile changed')
