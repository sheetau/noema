"""Optional material, local driving and electrodynamic inquiry conventions."""
from copy import deepcopy
import json
from noema.constructed import parse,format_graph
from noema.constructed_discourse import normalize_document,function_sort,description_sort
from noema.constructed_semantics import FunctionValue,DescriptionValue
from scripts.kinematic_transition_visible_profile import ROOT,KinematicTransitionVisibleVocabulary,write_once,CUT
from scripts.sixth_heading_visible_profile_contracts import CONTRACTS,SOURCE_RELATIONS
from scripts.visible_word_forms import Word,canonical,symbol
from scripts.visible_lexical_script import require

LIBRARY='examples/v016/sixth-heading-visible-profile-v1.noema'
BASIS='data/sixth-heading-visible-profile-basis-v1.json'
MANIFEST='noema/resources/visible-sixth-heading-visible-profile-v1.json'
ALL_CONTRACTS=CONTRACTS
PARAMETERS={n:r['parameters'] for n,r in ALL_CONTRACTS.items()}
PARTS=('home','above','give','inside','aki','nao','book','round')
SPELLINGS={'materialoccupancy': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'treeone', 'rain'],
 'localdrivingunit': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'treeone', 'town'],
 'fieldequationtransformationinquiry': ['above',
                                        'round',
                                        'treeone',
                                        'home',
                                        'nao',
                                        'book',
                                        'birdone',
                                        'treeone',
                                        'home'],
 'physicalnatureinquiry': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'treeone', 'above']}
CONTEXT=['物質占有は同じ物体・系・文脈と長さ/時間単位で指定する。', '局所的な力/電荷の単位を、閉回路の電圧や力そのものの単位と区別する。', '研究主題は閉じた型付き内容を引用し、研究対象と文脈を同じ本文の中で結ぶ。']
LIMITS=['共通375語と固定アルファベットを維持し、採用済み4規約を任意プロファイルへ公開する。',
 '物質の穴や外側を外接領域だけで占有へ含めず、標本だけで全時空領域を認定しない。',
 '研究主題の提示から方程式の不変性、物理的起源の確定、具体的実験の実行を導かない。',
 '真空の方程式規約と単位試験電荷の条件を、同一の実試行への要求として結合しない。',
 '静止や磁場に平行な運動では零作用の比較例を許容する。',
 '引用の識別、有限の引数結合診断、実域全体の証明、独立読解を区別する。']


def library():
    return dict(schema_version='0.16',lexicon_version='0.16',declarations=[
        dict(kind='primitive',name=n,parameters=r['parameters'],result=r['result']) for n,r in ALL_CONTRACTS.items()],statements=[])


def basis():
    return dict(status='optional_sixth_heading_visible_profile',document=LIBRARY,definitions={},primitives=ALL_CONTRACTS,
        public_contracts={n:dict(arguments=[dict(role=a,sort=s) for a,s in zip(r['arguments'],r['parameters'],strict=True)],
            result=r['result'],interpretation_inputs=CONTEXT) for n,r in ALL_CONTRACTS.items()},
        source_relations=SOURCE_RELATIONS,limitations=LIMITS)


def manifest():
    return dict(schema='noema-visible-optional-profile-1',edition=66,parent_profile=65,core_edition=12,
        library=LIBRARY,basis=BASIS,spellings=SPELLINGS,
        naming_convention='above/round/treeone/home/nao/book/birdone/treeoneを物質占有・局所駆動単位・電磁気的研究主題の語群とする。後続要素は公開規約を区別する綴りであり、文中の語義番号ではない。対象・単位・引用内容・文脈は本文の合成で結ぶ。')


def prepare():
    write_once(LIBRARY,format_graph(library())+'\n');write_once(BASIS,basis());write_once(MANIFEST,manifest())


class SixthHeadingVisibleVocabulary(KinematicTransitionVisibleVocabulary):
    def __init__(self):
        super().__init__();data=self.document();parent=deepcopy(data)
        require(json.loads((ROOT/MANIFEST).read_text(encoding='utf-8'))==manifest(),'SixthHeading-visible profile changed')
        require(parse((ROOT/LIBRARY).read_text(encoding='utf-8'))==library(),'SixthHeading-visible declarations changed')
        require(json.loads((ROOT/BASIS).read_text(encoding='utf-8'))==basis(),'SixthHeading-visible meanings changed')
        for d in library()['declarations']:
            n=d['name'];r=ALL_CONTRACTS[n];require(n not in self._words,'Profile name collision')
            word=canonical(Word('compound',tuple(SPELLINGS[n])),self)
            data['primitives'][n]=d;data['compounds'][n]=dict(parts=list(word.parts),parameters=d['parameters'],result=d['result'],
                roles=r['arguments'],meaning=r['meaning_ja'],context=CONTEXT,contrast=LIMITS,aliases=[])
            self._words[n]=word
        data.update(schema='noema-visible-sixth-heading-visible-profile-1',edition=66)
        data['naming_convention']+='\n'+manifest()['naming_convention'];self._document=data
        self._primitives=deepcopy(data['primitives']);self._symbols={n:symbol(w,self) for n,w in self._words.items()}
        require(len(set(self._symbols.values()))==len(self._words),'Profile spelling collision')
        self._by_symbol={s:n for n,s in self._symbols.items()};self._order=self._topological()
        normalize_document(dict(schema_version='0.16',lexicon_version='0.16',declarations=[self._plain_declaration(n) for n in self._order],statements=[]))
        for field in ('entries','compounds','definitions','primitives'):
            require(all(data[field].get(n)==d for n,d in parent[field].items()),'Previous profile changed')
