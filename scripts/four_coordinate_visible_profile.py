"""Optional interpretive sufficient conditions and spatial function families."""
from copy import deepcopy
import json
from noema.constructed import parse,format_graph
from noema.constructed_discourse import normalize_document,function_sort,description_sort
from noema.constructed_semantics import FunctionValue,DescriptionValue
from scripts.transverse_ray_visible_profile import ROOT,TransverseRayVisibleVocabulary,write_once,CUT
from scripts.visible_word_forms import Word,canonical,symbol
from scripts.visible_lexical_script import require
CONTRACTS={'interpretssufficientcondition':{'parameters': ['individual', 'individual', {'kind': 'description', 'result': 'content'}, {'kind': 'description', 'result': 'content'}, 'individual', 'situation'], 'result': 'truth', 'arguments': ['node', 'source_author', 'additional_premise', 'conclusion', 'scope', 'context'], 'meaning_ja': '本文の推論を指定した追加前提による十分条件として明示化する部分解釈。著者が追加条件を全て述べたことも、その実世界での成立も含意しない。'}};SOURCE_RELATIONS={'zfl':'interpretssufficientcondition'}

LIBRARY='examples/v016/four-coordinate-visible-profile-v1.noema'
BASIS='data/four-coordinate-visible-profile-basis-v1.json'
MANIFEST='noema/resources/visible-four-coordinate-visible-profile-v1.json'
I='individual';S='situation';N='number'
TAU=function_sort([CUT]*4,CUT)
MATRIX=function_sort([I,I],CUT);VECTOR=function_sort([I],CUT)
MAP=function_sort([I],TAU)
ROLE=function_sort([MAP,S],'truth')
EXTRA={'describedindividualfourcutfunctionfamilyreference':dict(parameters=[I,I,description_sort(ROLE),S],result=MAP,
    arguments=['document','node','role_description','context'],
    meaning_ja='同じ文書・箇所・提示文脈で、閉じた役割関係の記述に結び付けて照合する、個体ごとに四つの切断から切断への関数を返す関数族への参照。役割は本文で定義する。参照取得から役割の成立、存在の証明や唯一性を導かず、引用した役割や候補関数を実行しない。未知の参照を拒否し、役割に合う任意の写像を選んだり値を補ったりしない。')}

ALL_CONTRACTS=CONTRACTS|EXTRA
PARAMETERS={n:r['parameters'] for n,r in ALL_CONTRACTS.items()}
PARTS=('home','above','give','inside','aki','nao','book','round')
SPELLINGS={name:['above','round','treeone','home','give',PARTS[i//8],PARTS[i%8]] for i,name in enumerate(ALL_CONTRACTS)}
CONTEXT=['同じ課題・方式・対象・文書・文脈を保持する。見かけ、可能性、採用、実施を区別する。']
LIMITS=['共通375語は不変。旧関係の型・役割・意味を任意プロファイルとして公開する。',
        '記録の成分位置は公開されたデータの欄であり語義番号ではない。未知の値を既定値で補わない。',
        '参照・引用・前方指示はその内容の真理や実験済みを意味しない。有限診断を全実数の証明としない。']


def library():
    return dict(schema_version='0.16',lexicon_version='0.16',declarations=[
        dict(kind='primitive',name=n,parameters=r['parameters'],result=r['result']) for n,r in ALL_CONTRACTS.items()],statements=[])


def basis():
    return dict(status='optional_four_coordinate_visible_profile',document=LIBRARY,definitions={},primitives=ALL_CONTRACTS,
        public_contracts={n:dict(arguments=[dict(role=a,sort=s) for a,s in zip(r['arguments'],r['parameters'],strict=True)],
            result=r['result'],interpretation_inputs=CONTEXT) for n,r in ALL_CONTRACTS.items()},
        source_relations=SOURCE_RELATIONS,limitations=LIMITS)


def manifest():
    return dict(schema='noema-visible-optional-profile-1',edition=49,parent_profile=48,core_edition=12,
        library=LIBRARY,basis=BASIS,spellings=SPELLINGS,
        naming_convention='above/round/treeone/home/giveを閉じた役割による個体ごとの四切断関数族の参照の語群とする。後続の二要素は公開規約で区別する綴りであり、文中に数値の語義表を置かない。役割と数学は本文定義として示す。')


def prepare():
    write_once(LIBRARY,format_graph(library())+'\n');write_once(BASIS,basis());write_once(MANIFEST,manifest())


class FourCoordinateVisibleVocabulary(TransverseRayVisibleVocabulary):
    def __init__(self):
        super().__init__();data=self.document();parent=deepcopy(data)
        require(json.loads((ROOT/MANIFEST).read_text(encoding='utf-8'))==manifest(),'FourCoordinate-visible profile changed')
        require(parse((ROOT/LIBRARY).read_text(encoding='utf-8'))==library(),'FourCoordinate-visible declarations changed')
        require(json.loads((ROOT/BASIS).read_text(encoding='utf-8'))==basis(),'FourCoordinate-visible meanings changed')
        for d in library()['declarations']:
            n=d['name'];r=ALL_CONTRACTS[n];require(n not in self._words,'Profile name collision')
            word=canonical(Word('compound',tuple(SPELLINGS[n])),self)
            data['primitives'][n]=d;data['compounds'][n]=dict(parts=list(word.parts),parameters=d['parameters'],result=d['result'],
                roles=r['arguments'],meaning=r['meaning_ja'],context=CONTEXT,contrast=LIMITS,aliases=[])
            self._words[n]=word
        data.update(schema='noema-visible-four-coordinate-visible-profile-1',edition=49)
        data['naming_convention']+='\n'+manifest()['naming_convention'];self._document=data
        self._primitives=deepcopy(data['primitives']);self._symbols={n:symbol(w,self) for n,w in self._words.items()}
        require(len(set(self._symbols.values()))==len(self._words),'Profile spelling collision')
        self._by_symbol={s:n for n,s in self._symbols.items()};self._order=self._topological()
        normalize_document(dict(schema_version='0.16',lexicon_version='0.16',declarations=[self._plain_declaration(n) for n in self._order],statements=[]))
        for field in ('entries','compounds','definitions','primitives'):
            require(all(data[field].get(n)==d for n,d in parent[field].items()),'Previous profile changed')

class IndividualFourCutFamilyReferences:
    def __init__(self,roles):
        require(all(isinstance(x,FunctionValue) and x.parameters==(I,) and x.result==TAU and callable(x.implementation) for x in roles.values()),
                'Expected an individual-to-four-cut-function family')
        self.roles=dict(roles)

    def described(self,doc,node,role,context):
        require(isinstance(role,DescriptionValue) and json.loads(role.result_type)==ROLE and role.rank==0,
                'Expected a checked individual-four-cut-family role description')
        key=(doc,node,role.syntax,context)
        require(key in self.roles,'Unknown individual-four-cut-family reference')
        return self.roles[key]

    def handlers(self):return dict(describedindividualfourcutfunctionfamilyreference=self.described)
