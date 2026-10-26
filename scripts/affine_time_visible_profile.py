"""Optional coefficient alternatives, brevity and typed function references."""
from copy import deepcopy
import json
from noema.constructed import parse,format_graph
from noema.constructed_discourse import normalize_document,function_sort,description_sort
from noema.constructed_semantics import FunctionValue,DescriptionValue
from scripts.transverse_visible_profile import ROOT,TransverseVisibleVocabulary,write_once,CUT
from scripts.visible_word_forms import Word,canonical,symbol
from scripts.visible_lexical_script import require
from scripts.affine_time_visible_profile_contracts import CONTRACTS,SOURCE_RELATIONS

LIBRARY='examples/v016/affine-time-visible-profile-v1.noema'
BASIS='data/affine-time-visible-profile-basis-v1.json'
MANIFEST='noema/resources/visible-affine-time-visible-profile-v1.json'
I='individual';S='situation';N='number'
PHI=function_sort([CUT],CUT)
FAMILY=function_sort([S],PHI)
FUNCTION_TYPES={'describedcutfunctionreference':PHI,'describedsituationcutfunctionfamilyreference':FAMILY}
EXTRA={name:dict(parameters=[I,I,description_sort(function_sort([sort,S],'truth')),S],result=sort,
    arguments=['document','node','role_description','context'],
    meaning_ja='同じ文書・箇所・提示文脈で、閉じた役割関係の記述に結び付けて照合する'+('切断から切断への関数' if sort==PHI else '状況ごとに切断から切断への関数を返す関数族')+'への参照。役割は本文で定義する。参照取得から役割の成立、値の実数妥当性、存在の証明や唯一性を導かず、引用した役割を実行しない。未知の参照を拒否し、具体的な関数式や候補の値を補わない。') for name,sort in FUNCTION_TYPES.items()}

ALL_CONTRACTS=CONTRACTS|EXTRA
PARAMETERS={n:r['parameters'] for n,r in ALL_CONTRACTS.items()}
PARTS=('home','above','give','inside','aki','nao','book','round')
SPELLINGS={name:['above','round','treeone','home',PARTS[i//8],PARTS[i%8]] for i,name in enumerate(ALL_CONTRACTS)}
CONTEXT=['同じ課題・方式・対象・文書・文脈を保持する。見かけ、可能性、採用、実施を区別する。']
LIMITS=['共通375語は不変。旧関係の型・役割・意味を任意プロファイルとして公開する。',
        '記録の成分位置は公開されたデータの欄であり語義番号ではない。未知の値を既定値で補わない。',
        '参照・引用・前方指示はその内容の真理や実験済みを意味しない。有限診断を全実数の証明としない。']


def library():
    return dict(schema_version='0.16',lexicon_version='0.16',declarations=[
        dict(kind='primitive',name=n,parameters=r['parameters'],result=r['result']) for n,r in ALL_CONTRACTS.items()],statements=[])


def basis():
    return dict(status='optional_affine_time_visible_profile',document=LIBRARY,definitions={},primitives=ALL_CONTRACTS,
        public_contracts={n:dict(arguments=[dict(role=a,sort=s) for a,s in zip(r['arguments'],r['parameters'],strict=True)],
            result=r['result'],interpretation_inputs=CONTEXT) for n,r in ALL_CONTRACTS.items()},
        source_relations=SOURCE_RELATIONS,limitations=LIMITS)


def manifest():
    return dict(schema='noema-visible-optional-profile-1',edition=45,parent_profile=44,core_edition=12,
        library=LIBRARY,basis=BASIS,spellings=SPELLINGS,
        naming_convention='above/round/treeone/homeを係数候補・簡潔さの理由と型付き関数参照の語群とする。後続の二要素は公開規約で区別する綴りであり、文中に数値の語義表を置かない。役割と数学は本文定義として示す。')


def prepare():
    write_once(LIBRARY,format_graph(library())+'\n');write_once(BASIS,basis());write_once(MANIFEST,manifest())


class AffineTimeVisibleVocabulary(TransverseVisibleVocabulary):
    def __init__(self):
        super().__init__();data=self.document();parent=deepcopy(data)
        require(json.loads((ROOT/MANIFEST).read_text(encoding='utf-8'))==manifest(),'AffineTime-visible profile changed')
        require(parse((ROOT/LIBRARY).read_text(encoding='utf-8'))==library(),'AffineTime-visible declarations changed')
        require(json.loads((ROOT/BASIS).read_text(encoding='utf-8'))==basis(),'AffineTime-visible meanings changed')
        for d in library()['declarations']:
            n=d['name'];r=ALL_CONTRACTS[n];require(n not in self._words,'Profile name collision')
            word=canonical(Word('compound',tuple(SPELLINGS[n])),self)
            data['primitives'][n]=d;data['compounds'][n]=dict(parts=list(word.parts),parameters=d['parameters'],result=d['result'],
                roles=r['arguments'],meaning=r['meaning_ja'],context=CONTEXT,contrast=LIMITS,aliases=[])
            self._words[n]=word
        data.update(schema='noema-visible-affine-time-visible-profile-1',edition=45)
        data['naming_convention']+='\n'+manifest()['naming_convention'];self._document=data
        self._primitives=deepcopy(data['primitives']);self._symbols={n:symbol(w,self) for n,w in self._words.items()}
        require(len(set(self._symbols.values()))==len(self._words),'Profile spelling collision')
        self._by_symbol={s:n for n,s in self._symbols.items()};self._order=self._topological()
        normalize_document(dict(schema_version='0.16',lexicon_version='0.16',declarations=[self._plain_declaration(n) for n in self._order],statements=[]))
        for field in ('entries','compounds','definitions','primitives'):
            require(all(data[field].get(n)==d for n,d in parent[field].items()),'Previous profile changed')

class TypedFunctionReferences:
    """Known candidates of one of the two explicit public function types."""
    def __init__(self,name,roles):
        require(name in FUNCTION_TYPES,'Unknown function reference type')
        self.name=name;self.sort=FUNCTION_TYPES[name];self.role=function_sort([self.sort,S],'truth')
        require(all(isinstance(x,FunctionValue) and list(x.parameters)==self.sort['parameters']
                    and x.result==self.sort['result'] and callable(x.implementation) for x in roles.values()),
                'Expected a candidate of the declared function type')
        self.roles=dict(roles)

    def described(self,doc,node,role,context):
        require(isinstance(role,DescriptionValue) and json.loads(role.result_type)==self.role and role.rank==0,
                'Expected a checked function role description')
        key=(doc,node,role.syntax,context)
        require(key in self.roles,'Unknown typed function reference');return self.roles[key]

    def handlers(self):return {self.name:self.described}
