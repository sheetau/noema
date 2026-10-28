"""Optional typed references to individual-to-real-value maps."""
from copy import deepcopy
import json
from noema.constructed import parse,format_graph
from noema.constructed_discourse import normalize_document,function_sort,description_sort
from noema.constructed_semantics import FunctionValue,DescriptionValue
from scripts.field_comparison_visible_profile import ROOT,FieldComparisonVisibleVocabulary,write_once,CUT
from scripts.visible_word_forms import Word,canonical,symbol
from scripts.visible_lexical_script import require
CONTRACTS={};SOURCE_RELATIONS={}

LIBRARY='examples/v016/field-symmetry-visible-profile-v1.noema'
BASIS='data/field-symmetry-visible-profile-basis-v1.json'
MANIFEST='noema/resources/visible-field-symmetry-visible-profile-v1.json'
I='individual';S='situation';N='number'
MAP=function_sort([I],CUT)
ROLE=function_sort([MAP,S],'truth')
EXTRA={'describedindividualcutfunctionreference':dict(parameters=[I,I,description_sort(ROLE),S],result=MAP,
    arguments=['document','node','role_description','context'],
    meaning_ja='同じ文書・箇所・提示文脈で、閉じた役割関係の記述に結び付けて照合する、個体から実数値への関数への参照。役割は本文で定義する。参照取得から役割の成立、存在の証明や唯一性を導かず、引用した役割や候補関数を実行しない。未知の参照を拒否し、役割に合う任意の写像を選んだり値を補ったりしない。')}

ALL_CONTRACTS=CONTRACTS|EXTRA
PARAMETERS={n:r['parameters'] for n,r in ALL_CONTRACTS.items()}
PARTS=('home','above','give','inside','aki','nao','book','round')
SPELLINGS={'describedindividualcutfunctionreference': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'town']}
CONTEXT=['同じ文書・箇所・提示文脈と、本文で定義した閉じた役割を保持する。', '候補は個体から実数値への関数。四座標の役割と領域は、この取得規約とは別に本文で指定する。']
LIMITS=['固定アルファベットと共通375語を維持し、型付き参照だけを任意profile71へ追加する。', '引用した役割や候補関数を取得時に実行しない。役割の成立、存在・唯一性、物理的な応答を保証しない。', '未知の文書・箇所・役割・文脈を拒否する。候補を推測したり既定値を補ったりしない。', '点の有効性・領域、脚注の五零成分・非零N、符号反転、係数の偶性・値1は本文で別に構成する。']


def library():
    return dict(schema_version='0.16',lexicon_version='0.16',declarations=[
        dict(kind='primitive',name=n,parameters=r['parameters'],result=r['result']) for n,r in ALL_CONTRACTS.items()],statements=[])


def basis():
    return dict(status='optional_field_symmetry_visible_profile',document=LIBRARY,definitions={},primitives=ALL_CONTRACTS,
        public_contracts={n:dict(arguments=[dict(role=a,sort=s) for a,s in zip(r['arguments'],r['parameters'],strict=True)],
            result=r['result'],interpretation_inputs=CONTEXT) for n,r in ALL_CONTRACTS.items()},
        source_relations=SOURCE_RELATIONS,limitations=LIMITS)


def manifest():
    return dict(schema='noema-visible-optional-profile-1',edition=71,parent_profile=70,core_edition=12,
        library=LIBRARY,basis=BASIS,spellings=SPELLINGS,
        naming_convention='above/round/treeone/home/nao/book/birdone/fruit/townを個体から実数値への関数参照の綴りとする。役割・座標・領域は本文定義で構成する。')


def prepare():
    write_once(LIBRARY,format_graph(library())+'\n');write_once(BASIS,basis());write_once(MANIFEST,manifest())


class FieldSymmetryVisibleVocabulary(FieldComparisonVisibleVocabulary):
    def __init__(self):
        super().__init__();data=self.document();parent=deepcopy(data)
        require(json.loads((ROOT/MANIFEST).read_text(encoding='utf-8'))==manifest(),'FieldSymmetry-visible profile changed')
        require(parse((ROOT/LIBRARY).read_text(encoding='utf-8'))==library(),'FieldSymmetry-visible declarations changed')
        require(json.loads((ROOT/BASIS).read_text(encoding='utf-8'))==basis(),'FieldSymmetry-visible meanings changed')
        for d in library()['declarations']:
            n=d['name'];r=ALL_CONTRACTS[n];require(n not in self._words,'Profile name collision')
            word=canonical(Word('compound',tuple(SPELLINGS[n])),self)
            data['primitives'][n]=d;data['compounds'][n]=dict(parts=list(word.parts),parameters=d['parameters'],result=d['result'],
                roles=r['arguments'],meaning=r['meaning_ja'],context=CONTEXT,contrast=LIMITS,aliases=[])
            self._words[n]=word
        data.update(schema='noema-visible-field-symmetry-visible-profile-1',edition=71)
        data['naming_convention']+='\n'+manifest()['naming_convention'];self._document=data
        self._primitives=deepcopy(data['primitives']);self._symbols={n:symbol(w,self) for n,w in self._words.items()}
        require(len(set(self._symbols.values()))==len(self._words),'Profile spelling collision')
        self._by_symbol={s:n for n,s in self._symbols.items()};self._order=self._topological()
        normalize_document(dict(schema_version='0.16',lexicon_version='0.16',declarations=[self._plain_declaration(n) for n in self._order],statements=[]))
        for field in ('entries','compounds','definitions','primitives'):
            require(all(data[field].get(n)==d for n,d in parent[field].items()),'Previous profile changed')

class IndividualCutFunctionReferences:
    def __init__(self,roles):
        require(all(isinstance(x,FunctionValue) and x.parameters==(I,) and x.result==CUT and callable(x.implementation) for x in roles.values()),
                'Expected an individual-to-cut function')
        self.roles=dict(roles)

    def described(self,doc,node,role,context):
        require(isinstance(role,DescriptionValue) and json.loads(role.result_type)==ROLE and role.rank==0,
                'Expected a checked individual-cut-map role description')
        key=(doc,node,role.syntax,context)
        require(key in self.roles,'Unknown individual-cut-map reference')
        return self.roles[key]

    def handlers(self):return dict(describedindividualcutfunctionreference=self.described)
