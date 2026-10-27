"""Optional explanation, field-designation and typed region references."""
from copy import deepcopy
import json
from noema.constructed import parse,format_graph
from noema.constructed_discourse import normalize_document,function_sort,description_sort
from noema.constructed_semantics import FunctionValue,DescriptionValue
from scripts.sixth_heading_visible_profile import ROOT,SixthHeadingVisibleVocabulary,write_once,CUT
from scripts.vacuum_assumption_visible_profile_contracts import CONTRACTS,SOURCE_RELATIONS
from scripts.visible_word_forms import Word,canonical,symbol
from scripts.visible_lexical_script import require

LIBRARY='examples/v016/vacuum-assumption-visible-profile-v1.noema'
BASIS='data/vacuum-assumption-visible-profile-basis-v1.json'
MANIFEST='noema/resources/visible-vacuum-assumption-visible-profile-v1.json'
REGION=function_sort([CUT]*4,'truth')
ROLE=function_sort([REGION,'situation'],'truth')
EXTRA={'describedfourcuttruthfunctionreference': {'parameters': ['individual',
                                                           'individual',
                                                           {'kind': 'description',
                                                            'result': {'kind': 'function',
                                                                       'parameters': [{'kind': 'function',
                                                                                       'parameters': [{'kind': 'function',
                                                                                                       'parameters': ['number'],
                                                                                                       'result': 'truth'},
                                                                                                      {'kind': 'function',
                                                                                                       'parameters': ['number'],
                                                                                                       'result': 'truth'},
                                                                                                      {'kind': 'function',
                                                                                                       'parameters': ['number'],
                                                                                                       'result': 'truth'},
                                                                                                      {'kind': 'function',
                                                                                                       'parameters': ['number'],
                                                                                                       'result': 'truth'}],
                                                                                       'result': 'truth'},
                                                                                      'situation'],
                                                                       'result': 'truth'}},
                                                           'situation'],
                                            'result': {'kind': 'function',
                                                       'parameters': [{'kind': 'function',
                                                                       'parameters': ['number'],
                                                                       'result': 'truth'},
                                                                      {'kind': 'function',
                                                                       'parameters': ['number'],
                                                                       'result': 'truth'},
                                                                      {'kind': 'function',
                                                                       'parameters': ['number'],
                                                                       'result': 'truth'},
                                                                      {'kind': 'function',
                                                                       'parameters': ['number'],
                                                                       'result': 'truth'}],
                                                       'result': 'truth'},
                                            'arguments': ['document', 'node', 'role_description', 'context'],
                                            'meaning_ja': '同じ文書・箇所・提示文脈で、閉じた役割関係の記述に結び付けて照合する、四つの切断から真偽値への関数の参照。役割は本文で定義する。参照取得から役割の成立、存在の証明や唯一性を導かず、引用した役割や候補関数を実行しない。未知の参照を拒否し、役割に合う任意の関数を選んだり値を補ったりしない。'}}
ALL_CONTRACTS=CONTRACTS|EXTRA
PARAMETERS={n:r['parameters'] for n,r in ALL_CONTRACTS.items()}
PARTS=('home','above','give','inside','aki','nao','book','round')
SPELLINGS={'authorexplainsby': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'round', 'rain'],
 'threecomponentfielddesignation': ['above',
                                    'round',
                                    'treeone',
                                    'home',
                                    'nao',
                                    'book',
                                    'birdone',
                                    'round',
                                    'town'],
 'describedfourcuttruthfunctionreference': ['above',
                                            'round',
                                            'treeone',
                                            'home',
                                            'nao',
                                            'book',
                                            'birdone',
                                            'round',
                                            'home']}
CONTEXT=['説明する箇所と説明に使う箇所を同じ著者・文脈へ結ぶ。', '順序付き三成分の表記を同じ文書内の閉じた型付き規約へ結ぶ。', '領域参照は文書・箇所・閉役割・文脈を全て照合し、役割の真理を実行条件にしない。']
LIMITS=['共通375語と固定アルファベットを維持し、採用済み2規約と一般型の参照1規約を任意プロファイルへ公開する。',
 '説明・言い換えの談話関係だけから二つの内容の厳密な同値性を導かない。',
 '三成分の数値、物理的な種類、場の単位、同じ領域での対応は本文に合成し、綴りや実装識別子で代用しない。',
 '領域や場の参照取得では閉役割・候補関数を実行せず、未知の箇所・型・rank・文脈を拒否する。',
 '仮定内容の引用から六式の真理、実験の実施、発散条件や変換後の結果を導かない。',
 '全実数領域・関数域への量化は本文に保持し、有限の結合診断を全領域の証明にしない。']


def library():
    return dict(schema_version='0.16',lexicon_version='0.16',declarations=[
        dict(kind='primitive',name=n,parameters=r['parameters'],result=r['result']) for n,r in ALL_CONTRACTS.items()],statements=[])


def basis():
    return dict(status='optional_vacuum_assumption_visible_profile',document=LIBRARY,definitions={},primitives=ALL_CONTRACTS,
        public_contracts={n:dict(arguments=[dict(role=a,sort=s) for a,s in zip(r['arguments'],r['parameters'],strict=True)],
            result=r['result'],interpretation_inputs=CONTEXT) for n,r in ALL_CONTRACTS.items()},
        source_relations=SOURCE_RELATIONS,limitations=LIMITS)


def manifest():
    return dict(schema='noema-visible-optional-profile-1',edition=67,parent_profile=66,core_edition=12,
        library=LIBRARY,basis=BASIS,spellings=SPELLINGS,
        naming_convention='above/round/treeone/home/nao/book/birdone/roundを説明関係・三成分表記・四切断真偽関数参照の語群とする。後続要素は公開規約を区別する綴りであり、文中の語義番号ではない。箇所・対象・閉役割・文脈は本文の合成で結ぶ。')


def prepare():
    write_once(LIBRARY,format_graph(library())+'\n');write_once(BASIS,basis());write_once(MANIFEST,manifest())


class VacuumAssumptionVisibleVocabulary(SixthHeadingVisibleVocabulary):
    def __init__(self):
        super().__init__();data=self.document();parent=deepcopy(data)
        require(json.loads((ROOT/MANIFEST).read_text(encoding='utf-8'))==manifest(),'VacuumAssumption-visible profile changed')
        require(parse((ROOT/LIBRARY).read_text(encoding='utf-8'))==library(),'VacuumAssumption-visible declarations changed')
        require(json.loads((ROOT/BASIS).read_text(encoding='utf-8'))==basis(),'VacuumAssumption-visible meanings changed')
        for d in library()['declarations']:
            n=d['name'];r=ALL_CONTRACTS[n];require(n not in self._words,'Profile name collision')
            word=canonical(Word('compound',tuple(SPELLINGS[n])),self)
            data['primitives'][n]=d;data['compounds'][n]=dict(parts=list(word.parts),parameters=d['parameters'],result=d['result'],
                roles=r['arguments'],meaning=r['meaning_ja'],context=CONTEXT,contrast=LIMITS,aliases=[])
            self._words[n]=word
        data.update(schema='noema-visible-vacuum-assumption-visible-profile-1',edition=67)
        data['naming_convention']+='\n'+manifest()['naming_convention'];self._document=data
        self._primitives=deepcopy(data['primitives']);self._symbols={n:symbol(w,self) for n,w in self._words.items()}
        require(len(set(self._symbols.values()))==len(self._words),'Profile spelling collision')
        self._by_symbol={s:n for n,s in self._symbols.items()};self._order=self._topological()
        normalize_document(dict(schema_version='0.16',lexicon_version='0.16',declarations=[self._plain_declaration(n) for n in self._order],statements=[]))
        for field in ('entries','compounds','definitions','primitives'):
            require(all(data[field].get(n)==d for n,d in parent[field].items()),'Previous profile changed')


class FourCutTruthFunctionReferences:
    """Look up a typed region function without evaluating it or its role."""
    def __init__(self,roles):
        require(all(isinstance(x,FunctionValue) and x.parameters==tuple([CUT]*4)
                    and x.result=='truth' and callable(x.implementation) for x in roles.values()),
                'Expected a four-cut truth-valued function')
        self.roles=dict(roles)

    def described(self,doc,node,role,context):
        require(isinstance(role,DescriptionValue) and json.loads(role.result_type)==ROLE and role.rank==0,
                'Expected a checked four-cut truth-function role description')
        key=(doc,node,role.syntax,context)
        require(key in self.roles,'Unknown four-cut truth-function reference')
        return self.roles[key]

    def handlers(self):return dict(describedfourcuttruthfunctionreference=self.described)
