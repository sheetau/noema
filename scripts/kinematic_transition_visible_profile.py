"""Optional task, presentation and kinematic inquiry conventions."""
from copy import deepcopy
import json
from noema.constructed import parse,format_graph
from noema.constructed_discourse import normalize_document,function_sort,description_sort
from noema.constructed_semantics import FunctionValue,DescriptionValue
from scripts.velocity_axial_visible_profile import ROOT,VelocityAxialVisibleVocabulary,write_once,CUT
from scripts.kinematic_transition_visible_profile_contracts import CONTRACTS,SOURCE_RELATIONS
from scripts.visible_word_forms import Word,canonical,symbol
from scripts.visible_lexical_script import require

LIBRARY='examples/v016/kinematic-transition-visible-profile-v1.noema'
BASIS='data/kinematic-transition-visible-profile-basis-v1.json'
MANIFEST='noema/resources/visible-kinematic-transition-visible-profile-v1.json'
ALL_CONTRACTS=CONTRACTS
PARAMETERS={n:r['parameters'] for n,r in ALL_CONTRACTS.items()}
PARTS=('home','above','give','inside','aki','nao','book','round')
SPELLINGS={'taskrequiredproposition': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'nao', 'rain'],
 'presentedexample': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'nao', 'town'],
 'prospectivetaskentry': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'nao', 'home'],
 'kinematicinquirydomain': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'nao', 'above']}
CONTEXT=['必要な命題の集合は同じ主体・課題・基準段階から指定する。', '例の提示、課題開始の提示、目標達成を別々の関係として扱う。', '運動学の研究領域は閉じた型の物体・位置・時刻・配置の規約を引用して指定する。']
LIMITS=['共通375語と固定アルファベットを維持し、既存の採用規約4件を任意プロファイルで公開する。',
 '文脈的な必要性は論理的必然性や全人類に共通の必要性ではない。',
 '例の利用可能性や提示予定だけを提示済みと数えない。',
 '課題への移行から解決・目標達成・後続の実行完了を導かない。',
 '運動学の分類だけから運動の実現可能性や特定の変換則を導かない。',
 '引用内容の識別、有限診断、実域全体の証明、独立読解は別に扱う。']


def library():
    return dict(schema_version='0.16',lexicon_version='0.16',declarations=[
        dict(kind='primitive',name=n,parameters=r['parameters'],result=r['result']) for n,r in ALL_CONTRACTS.items()],statements=[])


def basis():
    return dict(status='optional_kinematic_transition_visible_profile',document=LIBRARY,definitions={},primitives=ALL_CONTRACTS,
        public_contracts={n:dict(arguments=[dict(role=a,sort=s) for a,s in zip(r['arguments'],r['parameters'],strict=True)],
            result=r['result'],interpretation_inputs=CONTEXT) for n,r in ALL_CONTRACTS.items()},
        source_relations=SOURCE_RELATIONS,limitations=LIMITS)


def manifest():
    return dict(schema='noema-visible-optional-profile-1',edition=65,parent_profile=64,core_edition=12,
        library=LIBRARY,basis=BASIS,spellings=SPELLINGS,
        naming_convention='above/round/treeone/home/nao/book/birdone/naoを課題の必要条件・提示・研究領域の語群とする。後続要素は公開規約を区別する綴りであり、文中の語義番号ではない。集合・内容・参照段階は本文の合成で結ぶ。')


def prepare():
    write_once(LIBRARY,format_graph(library())+'\n');write_once(BASIS,basis());write_once(MANIFEST,manifest())


class KinematicTransitionVisibleVocabulary(VelocityAxialVisibleVocabulary):
    def __init__(self):
        super().__init__();data=self.document();parent=deepcopy(data)
        require(json.loads((ROOT/MANIFEST).read_text(encoding='utf-8'))==manifest(),'KinematicTransition-visible profile changed')
        require(parse((ROOT/LIBRARY).read_text(encoding='utf-8'))==library(),'KinematicTransition-visible declarations changed')
        require(json.loads((ROOT/BASIS).read_text(encoding='utf-8'))==basis(),'KinematicTransition-visible meanings changed')
        for d in library()['declarations']:
            n=d['name'];r=ALL_CONTRACTS[n];require(n not in self._words,'Profile name collision')
            word=canonical(Word('compound',tuple(SPELLINGS[n])),self)
            data['primitives'][n]=d;data['compounds'][n]=dict(parts=list(word.parts),parameters=d['parameters'],result=d['result'],
                roles=r['arguments'],meaning=r['meaning_ja'],context=CONTEXT,contrast=LIMITS,aliases=[])
            self._words[n]=word
        data.update(schema='noema-visible-kinematic-transition-visible-profile-1',edition=65)
        data['naming_convention']+='\n'+manifest()['naming_convention'];self._document=data
        self._primitives=deepcopy(data['primitives']);self._symbols={n:symbol(w,self) for n,w in self._words.items()}
        require(len(set(self._symbols.values()))==len(self._words),'Profile spelling collision')
        self._by_symbol={s:n for n,s in self._symbols.items()};self._order=self._topological()
        normalize_document(dict(schema_version='0.16',lexicon_version='0.16',declarations=[self._plain_declaration(n) for n in self._order],statements=[]))
        for field in ('entries','compounds','definitions','primitives'):
            require(all(data[field].get(n)==d for n,d in parent[field].items()),'Previous profile changed')
