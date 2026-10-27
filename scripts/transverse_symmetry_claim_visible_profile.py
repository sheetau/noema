"""Optional physical interpretation, spatial symmetry reason and measured-length family reference."""
from copy import deepcopy
import json
from noema.constructed import parse,format_graph
from noema.constructed_discourse import normalize_document,function_sort,description_sort
from noema.constructed_semantics import FunctionValue,DescriptionValue
from scripts.transverse_endpoint_claim_visible_profile import ROOT,TransverseEndpointClaimVisibleVocabulary,write_once,CUT
from scripts.visible_word_forms import Word,canonical,symbol
from scripts.visible_lexical_script import require
CONTRACTS={'attributesphysicalfunctioninterpretation': {'parameters': ['individual',
                                                             'individual',
                                                             {'kind': 'description',
                                                              'result': {'kind': 'function',
                                                                         'parameters': [{'kind': 'function',
                                                                                         'parameters': ['number'],
                                                                                         'result': 'truth'}],
                                                                         'result': {'kind': 'function',
                                                                                    'parameters': ['number'],
                                                                                    'result': 'truth'}}},
                                                             {'kind': 'description', 'result': 'content'},
                                                             'individual',
                                                             'situation'],
                                              'result': 'truth',
                                              'arguments': ['node',
                                                            'author',
                                                            'function_description',
                                                            'physical_content',
                                                            'scope',
                                                            'context'],
                                              'meaning_ja': '著者が関数の物理的な解釈を、指定した測定内容によって与える。関数値の計算済み事実や全速度での証明とは分ける。'},
 'attributesspatialsymmetryreason': {'parameters': ['individual',
                                                    'individual',
                                                    {'kind': 'description', 'result': 'content'},
                                                    'individual',
                                                    'situation'],
                                     'result': 'truth',
                                     'arguments': ['node', 'author', 'conclusion', 'scope', 'reference'],
                                     'meaning_ja': 'authorがnodeで、同じ背景と尺度の下で空間的な配置の向きの変更を特別扱いしないという物理的対称性を理由として、conclusionの内容をscopeで提示する。どの対象・配置・変更・量の範囲で何が不変なのかはconclusionの合成内容へ明示する。理由の種類を示す論述上の帰属であり、その対称性の実験的検証、全物理法則の定理、結論の自動証明や明白さ自体を含意しない。'}}
SOURCE_RELATIONS={'zhf': 'attributesphysicalfunctioninterpretation', 'eisn2': 'attributesspatialsymmetryreason'}

LIBRARY='examples/v016/transverse-symmetry-claim-visible-profile-v1.noema'
BASIS='data/transverse-symmetry-claim-visible-profile-basis-v1.json'
MANIFEST='noema/resources/visible-transverse-symmetry-claim-visible-profile-v1.json'
I='individual';S='situation'
FAMILY=function_sort([S],CUT)
ROLE=function_sort([FAMILY,S],'truth')
EXTRA={'describedsituationcutfunctionreference':dict(parameters=[I,I,description_sort(ROLE),S],result=FAMILY,
    arguments=['document','node','role_description','context'],
    meaning_ja='同じ文書・箇所・提示文脈で、閉じた役割関係の記述に結び付けて照合する、状況ごとに切断を返す関数への参照。役割は本文で定義する。参照取得から役割の成立、存在や唯一性を導かず、引用した役割や候補関数を実行しない。未知の参照を拒否し、任意の候補を選んだり値を補ったりしない。')}
ALL_CONTRACTS=CONTRACTS|EXTRA
PARAMETERS={n:r['parameters'] for n,r in ALL_CONTRACTS.items()}
PARTS=('home','above','give','inside','aki','nao','book','round')
SPELLINGS={'attributesphysicalfunctioninterpretation': ['above',
                                              'round',
                                              'treeone',
                                              'home',
                                              'nao',
                                              'book',
                                              'inside',
                                              'rain'],
 'attributesspatialsymmetryreason': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'inside', 'town'],
 'describedsituationcutfunctionreference': ['above',
                                            'round',
                                            'treeone',
                                            'home',
                                            'nao',
                                            'book',
                                            'inside',
                                            'home']}
CONTEXT=['同じ課題・方式・対象・文書・文脈を保持する。見かけ、可能性、採用、実施を区別する。']
LIMITS=['共通375語とアルファベットを維持し、採用済みの物理的解釈と対称性の理由を任意プロファイルへ公開する。',
 '同じ関数・測定内容・著者・論述範囲・文脈を合成側で保持する。理由の帰属、内容の採用、明白さ、物理的証明は別の関係である。',
 '新しい参照型は状況から切断への関数であり、状況から切断関数への族と区別する。参照取得と引用は内容を実行しない。',
 '測定長の正の枝、全方向の比較範囲、同じ物体と尺度は本文定義が担う。有限診断を全実域の証明としない。']


def library():
    return dict(schema_version='0.16',lexicon_version='0.16',declarations=[
        dict(kind='primitive',name=n,parameters=r['parameters'],result=r['result']) for n,r in ALL_CONTRACTS.items()],statements=[])


def basis():
    return dict(status='optional_transverse_symmetry_claim_visible_profile',document=LIBRARY,definitions={},primitives=ALL_CONTRACTS,
        public_contracts={n:dict(arguments=[dict(role=a,sort=s) for a,s in zip(r['arguments'],r['parameters'],strict=True)],
            result=r['result'],interpretation_inputs=CONTEXT) for n,r in ALL_CONTRACTS.items()},
        source_relations=SOURCE_RELATIONS,limitations=LIMITS)


def manifest():
    return dict(schema='noema-visible-optional-profile-1',edition=57,parent_profile=56,core_edition=12,
        library=LIBRARY,basis=BASIS,spellings=SPELLINGS,
        naming_convention='above/round/treeone/home/nao/book/insideを物理的解釈・対称性理由と状況ごとの切断関数参照の語群とする。後続要素は公開規約を区別する綴りであり、対象や引数は本文で結ぶ。')


def prepare():
    write_once(LIBRARY,format_graph(library())+'\n');write_once(BASIS,basis());write_once(MANIFEST,manifest())


class TransverseSymmetryClaimVisibleVocabulary(TransverseEndpointClaimVisibleVocabulary):
    def __init__(self):
        super().__init__();data=self.document();parent=deepcopy(data)
        require(json.loads((ROOT/MANIFEST).read_text(encoding='utf-8'))==manifest(),'TransverseSymmetryClaim-visible profile changed')
        require(parse((ROOT/LIBRARY).read_text(encoding='utf-8'))==library(),'TransverseSymmetryClaim-visible declarations changed')
        require(json.loads((ROOT/BASIS).read_text(encoding='utf-8'))==basis(),'TransverseSymmetryClaim-visible meanings changed')
        for d in library()['declarations']:
            n=d['name'];r=ALL_CONTRACTS[n];require(n not in self._words,'Profile name collision')
            word=canonical(Word('compound',tuple(SPELLINGS[n])),self)
            data['primitives'][n]=d;data['compounds'][n]=dict(parts=list(word.parts),parameters=d['parameters'],result=d['result'],
                roles=r['arguments'],meaning=r['meaning_ja'],context=CONTEXT,contrast=LIMITS,aliases=[])
            self._words[n]=word
        data.update(schema='noema-visible-transverse-symmetry-claim-visible-profile-1',edition=57)
        data['naming_convention']+='\n'+manifest()['naming_convention'];self._document=data
        self._primitives=deepcopy(data['primitives']);self._symbols={n:symbol(w,self) for n,w in self._words.items()}
        require(len(set(self._symbols.values()))==len(self._words),'Profile spelling collision')
        self._by_symbol={s:n for n,s in self._symbols.items()};self._order=self._topological()
        normalize_document(dict(schema_version='0.16',lexicon_version='0.16',declarations=[self._plain_declaration(n) for n in self._order],statements=[]))
        for field in ('entries','compounds','definitions','primitives'):
            require(all(data[field].get(n)==d for n,d in parent[field].items()),'Previous profile changed')


class SituationCutFunctionReferences:
    def __init__(self,roles):
        require(all(isinstance(x,FunctionValue) and x.parameters==(S,) and x.result==CUT and callable(x.implementation) for x in roles.values()),'Expected a situation-to-cut function')
        self.roles=dict(roles)

    def described(self,doc,node,role,context):
        require(isinstance(role,DescriptionValue) and json.loads(role.result_type)==ROLE and role.rank==0,'Expected a checked situation-cut-function role description')
        key=(doc,node,role.syntax,context)
        require(key in self.roles,'Unknown situation-cut-function reference')
        return self.roles[key]

    def handlers(self):return dict(describedsituationcutfunctionreference=self.described)
