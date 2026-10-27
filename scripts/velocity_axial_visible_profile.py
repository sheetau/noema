"""Optional contextual attention-value and noteworthiness conventions."""
from copy import deepcopy
import json
from noema.constructed import parse,format_graph
from noema.constructed_discourse import normalize_document,function_sort,description_sort
from noema.constructed_semantics import FunctionValue,DescriptionValue
from scripts.velocity_magnitude_angle_visible_profile import ROOT,VelocityMagnitudeAngleVisibleVocabulary,write_once,CUT
from scripts.velocity_axial_visible_profile_contracts import CONTRACTS,SOURCE_RELATIONS
from scripts.visible_word_forms import Word,canonical,symbol
from scripts.visible_lexical_script import require

LIBRARY='examples/v016/velocity-axial-visible-profile-v1.noema'
BASIS='data/velocity-axial-visible-profile-basis-v1.json'
MANIFEST='noema/resources/visible-velocity-axial-visible-profile-v1.json'
ALL_CONTRACTS=CONTRACTS
PARAMETERS={n:r['parameters'] for n,r in ALL_CONTRACTS.items()}
PARTS=('home','above','give','inside','aki','nao','book','round')
SPELLINGS={'contextualattentionvalue': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'aki', 'rain'],
 'contextualnoteworthiness': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'aki', 'town']}
CONTEXT=['同じ記述内容と評価文脈について、注意を向ける価値と注目に値する基準を区別する。', '対称性の数理的条件は既存の本文定義で合成し、その評価とは別に保持する。']
LIMITS=['共通375語と固定アルファベットを維持し、既存の採用規約2件を任意プロファイルで公開する。',
 '注意価値を内容の真理値、驚きの強さ、計算の負担と同一視しない。',
 '著者の評価を全読者共通の尺度にはせず、原文にない数値閾値を固定しない。',
 '入力交換の対称性、正方向への非零運動、符号付き商の条件は既存本文定義で合成する。',
 '有限の識別診断、復号、意味判断、独立読解は別に扱う。']


def library():
    return dict(schema_version='0.16',lexicon_version='0.16',declarations=[
        dict(kind='primitive',name=n,parameters=r['parameters'],result=r['result']) for n,r in ALL_CONTRACTS.items()],statements=[])


def basis():
    return dict(status='optional_velocity_axial_visible_profile',document=LIBRARY,definitions={},primitives=ALL_CONTRACTS,
        public_contracts={n:dict(arguments=[dict(role=a,sort=s) for a,s in zip(r['arguments'],r['parameters'],strict=True)],
            result=r['result'],interpretation_inputs=CONTEXT) for n,r in ALL_CONTRACTS.items()},
        source_relations=SOURCE_RELATIONS,limitations=LIMITS)


def manifest():
    return dict(schema='noema-visible-optional-profile-1',edition=64,parent_profile=63,core_edition=12,
        library=LIBRARY,basis=BASIS,spellings=SPELLINGS,
        naming_convention='above/round/treeone/home/nao/book/birdone/akiを文脈的な注意価値と注目基準の語群とする。後続要素は公開規約を区別する綴りであり、文中の語義番号ではない。評価対象の内容と数理的な条件は本文で結ぶ。')


def prepare():
    write_once(LIBRARY,format_graph(library())+'\n');write_once(BASIS,basis());write_once(MANIFEST,manifest())


class VelocityAxialVisibleVocabulary(VelocityMagnitudeAngleVisibleVocabulary):
    def __init__(self):
        super().__init__();data=self.document();parent=deepcopy(data)
        require(json.loads((ROOT/MANIFEST).read_text(encoding='utf-8'))==manifest(),'VelocityAxial-visible profile changed')
        require(parse((ROOT/LIBRARY).read_text(encoding='utf-8'))==library(),'VelocityAxial-visible declarations changed')
        require(json.loads((ROOT/BASIS).read_text(encoding='utf-8'))==basis(),'VelocityAxial-visible meanings changed')
        for d in library()['declarations']:
            n=d['name'];r=ALL_CONTRACTS[n];require(n not in self._words,'Profile name collision')
            word=canonical(Word('compound',tuple(SPELLINGS[n])),self)
            data['primitives'][n]=d;data['compounds'][n]=dict(parts=list(word.parts),parameters=d['parameters'],result=d['result'],
                roles=r['arguments'],meaning=r['meaning_ja'],context=CONTEXT,contrast=LIMITS,aliases=[])
            self._words[n]=word
        data.update(schema='noema-visible-velocity-axial-visible-profile-1',edition=64)
        data['naming_convention']+='\n'+manifest()['naming_convention'];self._document=data
        self._primitives=deepcopy(data['primitives']);self._symbols={n:symbol(w,self) for n,w in self._words.items()}
        require(len(set(self._symbols.values()))==len(self._words),'Profile spelling collision')
        self._by_symbol={s:n for n,s in self._symbols.items()};self._order=self._topological()
        normalize_document(dict(schema_version='0.16',lexicon_version='0.16',declarations=[self._plain_declaration(n) for n in self._order],statements=[]))
        for field in ('entries','compounds','definitions','primitives'):
            require(all(data[field].get(n)==d for n,d in parent[field].items()),'Previous profile changed')
