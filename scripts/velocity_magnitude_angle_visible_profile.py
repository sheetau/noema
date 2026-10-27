"""Optional intended-theory, content correspondence, quantity interpretation and typed function reference conventions."""
from copy import deepcopy
import json
from noema.constructed import parse,format_graph
from noema.constructed_discourse import normalize_document,function_sort,description_sort
from noema.constructed_semantics import FunctionValue,DescriptionValue
from scripts.velocity_addition_setting_visible_profile import ROOT,VelocityAdditionSettingVisibleVocabulary,write_once,CUT
from scripts.velocity_magnitude_angle_visible_profile_contracts import CONTRACTS,SOURCE_RELATIONS
from scripts.visible_word_forms import Word,canonical,symbol
from scripts.visible_lexical_script import require

LIBRARY='examples/v016/velocity-magnitude-angle-visible-profile-v1.noema'
BASIS='data/velocity-magnitude-angle-visible-profile-basis-v1.json'
MANIFEST='noema/resources/visible-velocity-magnitude-angle-visible-profile-v1.json'
PAIR=function_sort(['truth'],CUT)
ROLE=function_sort([PAIR,'situation'],'truth')
EXTRA={'describedtruthcutfunctionreference': {'parameters': ['individual',
                                                       'individual',
                                                       {'kind': 'description',
                                                        'result': {'kind': 'function',
                                                                   'parameters': [{'kind': 'function',
                                                                                   'parameters': ['truth'],
                                                                                   'result': {'kind': 'function',
                                                                                              'parameters': ['number'],
                                                                                              'result': 'truth'}},
                                                                                  'situation'],
                                                                   'result': 'truth'}},
                                                       'situation'],
                                        'result': {'kind': 'function',
                                                   'parameters': ['truth'],
                                                   'result': {'kind': 'function',
                                                              'parameters': ['number'],
                                                              'result': 'truth'}},
                                        'arguments': ['document', 'node', 'role_description', 'context'],
                                        'meaning_ja': '同じ文書・箇所・提示文脈で、閉じた役割関係の記述に結び付けて照合する、真理値を受け実数切断型の値を返す関数への参照。役割の定義は本文に示す。参照取得から役割の現実の成立、関数の存在・一意性、返り値の実数としての条件を導かず、引用された役割や候補関数を実行しない。未知の参照を補わない。'}}
ALL_CONTRACTS=CONTRACTS|EXTRA
PARAMETERS={n:r['parameters'] for n,r in ALL_CONTRACTS.items()}
PARTS=('home','above','give','inside','aki','nao','book','round')
SPELLINGS={'intendedtheorydestination': ['above',
                               'round',
                               'treeone',
                               'home',
                               'nao',
                               'book',
                               'birdone',
                               'inside',
                               'rain'],
 'claimcontentcorrespondence': ['above',
                                'round',
                                'treeone',
                                'home',
                                'nao',
                                'book',
                                'birdone',
                                'inside',
                                'town'],
 'presentsquantityinterpretation': ['above',
                                    'round',
                                    'treeone',
                                    'home',
                                    'nao',
                                    'book',
                                    'birdone',
                                    'inside',
                                    'home'],
 'describedtruthcutfunctionreference': ['above',
                                        'round',
                                        'treeone',
                                        'home',
                                        'nao',
                                        'book',
                                        'birdone',
                                        'inside',
                                        'above']}
CONTEXT=['同じ理論構成課題と到達先、項目と閉じた内容、同じ数量の指定と解釈を保持する。', '真理値から切断への関数参照は型付きの閉じた役割で取得し、その役割や関数を実行しない。']
LIMITS=['共通375語と固定アルファベットを維持し、既存の採用規約3件と既存参照方式の型特殊化1件を任意プロファイルで公開する。',
 '理論の指示と物理的真理、内容対応と仮定としての使用、数量の解釈と命名を区別する。',
 '参照取得は存在・一意性・実数条件を証明しない。未知入力を補わず、役割引用と候補関数を実行しない。',
 '角度、積分、微分、ノルム、符号付き商の条件は既存本文定義で合成する。',
 '有限の識別診断、復号、意味判断、独立読解は別に扱う。']


def library():
    return dict(schema_version='0.16',lexicon_version='0.16',declarations=[
        dict(kind='primitive',name=n,parameters=r['parameters'],result=r['result']) for n,r in ALL_CONTRACTS.items()],statements=[])


def basis():
    return dict(status='optional_velocity_magnitude_angle_visible_profile',document=LIBRARY,definitions={},primitives=ALL_CONTRACTS,
        public_contracts={n:dict(arguments=[dict(role=a,sort=s) for a,s in zip(r['arguments'],r['parameters'],strict=True)],
            result=r['result'],interpretation_inputs=CONTEXT) for n,r in ALL_CONTRACTS.items()},
        source_relations=SOURCE_RELATIONS,limitations=LIMITS)


def manifest():
    return dict(schema='noema-visible-optional-profile-1',edition=63,parent_profile=62,core_edition=12,
        library=LIBRARY,basis=BASIS,spellings=SPELLINGS,
        naming_convention='above/round/treeone/home/nao/book/birdone/insideを理論の到達先・項目の内容・数量の解釈と型付き関数参照の語群とする。後続要素は公開規約を区別する綴りであり、文中の語義番号ではない。角度や物理量の関係は本文で合成する。')


def prepare():
    write_once(LIBRARY,format_graph(library())+'\n');write_once(BASIS,basis());write_once(MANIFEST,manifest())


class VelocityMagnitudeAngleVisibleVocabulary(VelocityAdditionSettingVisibleVocabulary):
    def __init__(self):
        super().__init__();data=self.document();parent=deepcopy(data)
        require(json.loads((ROOT/MANIFEST).read_text(encoding='utf-8'))==manifest(),'VelocityMagnitudeAngle-visible profile changed')
        require(parse((ROOT/LIBRARY).read_text(encoding='utf-8'))==library(),'VelocityMagnitudeAngle-visible declarations changed')
        require(json.loads((ROOT/BASIS).read_text(encoding='utf-8'))==basis(),'VelocityMagnitudeAngle-visible meanings changed')
        for d in library()['declarations']:
            n=d['name'];r=ALL_CONTRACTS[n];require(n not in self._words,'Profile name collision')
            word=canonical(Word('compound',tuple(SPELLINGS[n])),self)
            data['primitives'][n]=d;data['compounds'][n]=dict(parts=list(word.parts),parameters=d['parameters'],result=d['result'],
                roles=r['arguments'],meaning=r['meaning_ja'],context=CONTEXT,contrast=LIMITS,aliases=[])
            self._words[n]=word
        data.update(schema='noema-visible-velocity-magnitude-angle-visible-profile-1',edition=63)
        data['naming_convention']+='\n'+manifest()['naming_convention'];self._document=data
        self._primitives=deepcopy(data['primitives']);self._symbols={n:symbol(w,self) for n,w in self._words.items()}
        require(len(set(self._symbols.values()))==len(self._words),'Profile spelling collision')
        self._by_symbol={s:n for n,s in self._symbols.items()};self._order=self._topological()
        normalize_document(dict(schema_version='0.16',lexicon_version='0.16',declarations=[self._plain_declaration(n) for n in self._order],statements=[]))
        for field in ('entries','compounds','definitions','primitives'):
            require(all(data[field].get(n)==d for n,d in parent[field].items()),'Previous profile changed')


class TruthCutFunctionReferences:
    """Closed-role lookup for a truth-to-cut function, without evaluating it."""
    def __init__(self,roles):
        require(all(isinstance(x,FunctionValue) and x.parameters==('truth',) and x.result==CUT
                    and callable(x.implementation) for x in roles.values()),'Expected a truth-to-cut function')
        self.roles=dict(roles)

    def described(self,doc,node,role,context):
        require(isinstance(role,DescriptionValue) and json.loads(role.result_type)==ROLE and role.rank==0,
                'Expected a checked truth-cut-function role description')
        key=(doc,node,role.syntax,context)
        require(key in self.roles,'Unknown truth-cut-function reference')
        return self.roles[key]

    def handlers(self):return dict(describedtruthcutfunctionreference=self.described)
