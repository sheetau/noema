"""Optional material-axis geometry, action for an existing intention, and quantity naming."""
from copy import deepcopy
import json
from noema.constructed import parse,format_graph
from noema.constructed_discourse import normalize_document,function_sort,description_sort
from noema.constructed_semantics import FunctionValue,DescriptionValue
from scripts.phi_determination_intent_visible_profile import ROOT,PhiDeterminationIntentVisibleVocabulary,write_once,CUT
from scripts.visible_word_forms import Word,canonical,symbol
from scripts.visible_lexical_script import require
CONTRACTS={'materialline': {'parameters': ['individual'],
                  'result': 'truth',
                  'arguments': ['line'],
                  'meaning_ja': '空間に置かれた物質線。単なる数値方向や記号とは分ける。物質の基礎説明は未完。'},
 'rigidbodyidealization': {'parameters': ['individual', 'situation'],
                           'result': 'truth',
                           'arguments': ['object', 'context'],
                           'meaning_ja': '指定設定で形状を固定した剛な物体として扱う。物質軸と物差しへ共通に適用する理想化であり、加速中や全ての系で長さが等しいとの法則は含まない。'},
 'perpendicularmaterialaxes': {'parameters': ['individual', 'individual', 'situation'],
                               'result': 'truth',
                               'arguments': ['first_line', 'second_line', 'context'],
                               'meaning_ja': '二つの物質軸の方向が直交する。局所的なユークリッド方向の内積が零という意味規約。実方向と物理的測定からの接続は未完。'},
 'parallelmaterialaxes': {'parameters': ['individual', 'individual', 'situation'],
                          'result': 'truth',
                          'arguments': ['first_line', 'second_line', 'context'],
                          'meaning_ja': '二物質軸が幾何学的に平行。逆向きもこの関係単体では除かない。位置の一致は要求しない。'},
 'coincidentsupportinglines': {'parameters': ['individual', 'individual', 'situation'],
                               'result': 'truth',
                               'arguments': ['first_line', 'second_line', 'context'],
                               'meaning_ja': '二物質軸の幾何学的な支持直線が重なる。物体の同一性ではなく、単なる平行より強い条件。'},
 'actsforpriorintention': {'parameters': ['individual',
                                          {'kind': 'description', 'result': 'content'},
                                          'individual',
                                          'individual',
                                          'situation'],
                           'result': 'truth',
                           'arguments': ['agent', 'action', 'intention', 'scope', 'reference'],
                           'meaning_ja': 'agentがscopeで既にintentionの箇所に表明した同じ目標を目指すため、actionに記述された行為を手段として行うという目的関係。intentionは意図の表明箇所を指し、意図の対象・内容は別の関係で明示する。目的を意図する気持ちの新規発生に替えず、目標の達成、手段の十分性・成功や、客観的な因果関係の証明を要求しない。actionの実行と意図の同一性は合成側で保持する。'},
 'adoptsquantitydesignation': {'parameters': ['individual',
                                              'individual',
                                              'individual',
                                              {'kind': 'description',
                                               'result': {'kind': 'function',
                                                          'parameters': ['individual',
                                                                         {'kind': 'function',
                                                                          'parameters': ['number'],
                                                                          'result': 'truth'},
                                                                         'situation'],
                                                          'result': 'truth'}},
                                              'individual',
                                              'situation'],
                               'result': 'truth',
                               'arguments': ['node',
                                             'author',
                                             'designation',
                                             'rule',
                                             'document',
                                             'reference'],
                               'meaning_ja': 'authorがnodeで、同じdocumentの量を呼ぶdesignationを、対象・実数値・状況に対する閉じたruleの規約に従う記号として今採用する命名宣言。単なる既出表記の参照とは区別し、ruleの対象・測定単位・役割を保つ。記号の字面から物理的真理を導かず、規則をここで実行して測定を行うこと、他者の同意や歴史上の最初の命名を要求しない。'}}
SOURCE_RELATIONS={'zbp': 'materialline', 'zbq': 'rigidbodyidealization', 'zbs': 'perpendicularmaterialaxes', 'zbt': 'parallelmaterialaxes', 'zbu': 'coincidentsupportinglines', 'eisnq': 'actsforpriorintention', 'eisnw': 'adoptsquantitydesignation'}

LIBRARY='examples/v016/third-frame-claim-visible-profile-v1.noema'
BASIS='data/third-frame-claim-visible-profile-basis-v1.json'
MANIFEST='noema/resources/visible-third-frame-claim-visible-profile-v1.json'
ALL_CONTRACTS=CONTRACTS
PARAMETERS={n:r['parameters'] for n,r in ALL_CONTRACTS.items()}
PARTS=('home','above','give','inside','aki','nao','book','round')
SPELLINGS={'materialline': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'above', 'rain'], 'rigidbodyidealization': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'above', 'town'], 'perpendicularmaterialaxes': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'above', 'home'], 'parallelmaterialaxes': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'above', 'above'], 'coincidentsupportinglines': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'above', 'give'], 'actsforpriorintention': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'above', 'inside'], 'adoptsquantitydesignation': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'above', 'birdone']}
CONTEXT=['同じ課題・方式・対象・文書・文脈を保持する。見かけ、可能性、採用、実施を区別する。']
LIMITS=['共通375語は不変。旧関係の型・役割・意味を任意プロファイルとして公開する。',
        '記録の成分位置は公開されたデータの欄であり語義番号ではない。未知の値を既定値で補わない。',
        '参照・引用・前方指示はその内容の真理や実験済みを意味しない。有限診断を全実数の証明としない。',
        '物質線・剛性・軸の幾何は採用済みの理想化を保持する。物質の基礎説明、測定と方向の接続、全ての系での長さ不変を新たに証明しない。',
        '目的は先行する同じ意図に結ぶ。命名の規約は既出表記の解釈と区別し、目標達成や物理的な結論の真理を含意しない。']


def library():
    return dict(schema_version='0.16',lexicon_version='0.16',declarations=[
        dict(kind='primitive',name=n,parameters=r['parameters'],result=r['result']) for n,r in ALL_CONTRACTS.items()],statements=[])


def basis():
    return dict(status='optional_third_frame_claim_visible_profile',document=LIBRARY,definitions={},primitives=ALL_CONTRACTS,
        public_contracts={n:dict(arguments=[dict(role=a,sort=s) for a,s in zip(r['arguments'],r['parameters'],strict=True)],
            result=r['result'],interpretation_inputs=CONTEXT) for n,r in ALL_CONTRACTS.items()},
        source_relations=SOURCE_RELATIONS,limitations=LIMITS)


def manifest():
    return dict(schema='noema-visible-optional-profile-1',edition=55,parent_profile=54,core_edition=12,
        library=LIBRARY,basis=BASIS,spellings=SPELLINGS,
        naming_convention='above/round/treeone/home/nao/book/aboveを物質軸の幾何・先行意図への目的・量記号の命名の語群とする。後続要素は公開規約を区別する綴りであり、対象や引数は本文で結ぶ。')


def prepare():
    write_once(LIBRARY,format_graph(library())+'\n');write_once(BASIS,basis());write_once(MANIFEST,manifest())


class ThirdFrameClaimVisibleVocabulary(PhiDeterminationIntentVisibleVocabulary):
    def __init__(self):
        super().__init__();data=self.document();parent=deepcopy(data)
        require(json.loads((ROOT/MANIFEST).read_text(encoding='utf-8'))==manifest(),'ThirdFrameClaim-visible profile changed')
        require(parse((ROOT/LIBRARY).read_text(encoding='utf-8'))==library(),'ThirdFrameClaim-visible declarations changed')
        require(json.loads((ROOT/BASIS).read_text(encoding='utf-8'))==basis(),'ThirdFrameClaim-visible meanings changed')
        for d in library()['declarations']:
            n=d['name'];r=ALL_CONTRACTS[n];require(n not in self._words,'Profile name collision')
            word=canonical(Word('compound',tuple(SPELLINGS[n])),self)
            data['primitives'][n]=d;data['compounds'][n]=dict(parts=list(word.parts),parameters=d['parameters'],result=d['result'],
                roles=r['arguments'],meaning=r['meaning_ja'],context=CONTEXT,contrast=LIMITS,aliases=[])
            self._words[n]=word
        data.update(schema='noema-visible-third-frame-claim-visible-profile-1',edition=55)
        data['naming_convention']+='\n'+manifest()['naming_convention'];self._document=data
        self._primitives=deepcopy(data['primitives']);self._symbols={n:symbol(w,self) for n,w in self._words.items()}
        require(len(set(self._symbols.values()))==len(self._words),'Profile spelling collision')
        self._by_symbol={s:n for n,s in self._symbols.items()};self._order=self._topological()
        normalize_document(dict(schema_version='0.16',lexicon_version='0.16',declarations=[self._plain_declaration(n) for n in self._order],statements=[]))
        for field in ('entries','compounds','definitions','primitives'):
            require(all(data[field].get(n)==d for n,d in parent[field].items()),'Previous profile changed')
