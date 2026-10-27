"""Optional proof presentation, proof tasks and shared admissible settings."""
from copy import deepcopy
import json
from noema.constructed import parse,format_graph
from noema.constructed_discourse import normalize_document,function_sort,description_sort
from noema.constructed_semantics import FunctionValue,DescriptionValue
from scripts.origin_constants_visible_profile import ROOT,OriginConstantsVisibleVocabulary,write_once,CUT
from scripts.visible_word_forms import Word,canonical,symbol
from scripts.visible_lexical_script import require
CONTRACTS={'presentedproofbycontext': {'parameters': ['individual', 'individual', {'kind': 'description', 'result': 'content'}, 'situation', 'individual'], 'result': 'truth', 'arguments': ['proof', 'agent', 'content', 'stage', 'scope'], 'meaning_ja': '指定主体がその段階までの論述範囲で対象内容の証明として当該論証を提示済みである。論証の妥当性や検査器の受理を含意しない。'}, 'presentsprooftask': {'parameters': ['individual', 'individual', {'kind': 'description', 'result': 'content'}, 'situation', 'individual', 'situation'], 'result': 'truth', 'arguments': ['node', 'author', 'target', 'stage', 'scope', 'context'], 'meaning_ja': '著者が指定段階で対象内容を証明すべき課題として提示する。達成済みも解の存在も断言しない。'}, 'presentstaskreason': {'parameters': ['individual', 'individual', {'kind': 'description', 'result': 'content'}, 'individual', 'individual', 'situation'], 'result': 'truth', 'arguments': ['node', 'author', 'reason', 'task', 'scope', 'context'], 'meaning_ja': '著者が引用した内容を、その課題を行う理由として挙げる。理由の真理や論理的十分性を含意しない。'}, 'jointcontentadmissiblesetting': {'parameters': [{'kind': 'description', 'result': 'content'}, {'kind': 'description', 'result': 'content'}, 'situation', 'situation'], 'result': 'truth', 'arguments': ['first', 'second', 'reference', 'setting'], 'meaning_ja': 'referenceの判断において、同じ閉じたfirst・secondを両立性の対象として保ったまま検討する、許容される一つの物理的設定setting。共通の物理量・系・時計・単位・法則の解釈を共有し、二内容のそれぞれに別々の世界や意味を割り当てない。対象領域に関係する制約に従う全設定を扱い、両方が真になるものだけを結果から選別しない。両内容の成立と許容設定の存在はsqhの合成で要求する。見かけの候補点での評価はそこでの許容性の見積りであり、現実の許容性を認定する証拠ではない。'}};SOURCE_RELATIONS={'zfr': 'presentedproofbycontext', 'zga': 'presentsprooftask', 'zgb': 'presentstaskreason', 'eiscj': 'jointcontentadmissiblesetting'}

LIBRARY='examples/v016/light-proof-task-visible-profile-v1.noema'
BASIS='data/light-proof-task-visible-profile-basis-v1.json'
MANIFEST='noema/resources/visible-light-proof-task-visible-profile-v1.json'
ALL_CONTRACTS=CONTRACTS
PARAMETERS={n:r['parameters'] for n,r in ALL_CONTRACTS.items()}
PARTS=('home','above','give','inside','aki','nao','book','round')
SPELLINGS={name:['above','round','treeone','home','aki',PARTS[i//8],PARTS[i%8]] for i,name in enumerate(ALL_CONTRACTS)}
CONTEXT=['同じ課題・方式・対象・文書・文脈を保持する。見かけ、可能性、採用、実施を区別する。']
LIMITS=['共通375語は不変。旧関係の型・役割・意味を任意プロファイルとして公開する。',
        '記録の成分位置は公開されたデータの欄であり語義番号ではない。未知の値を既定値で補わない。',
        '参照・引用・前方指示はその内容の真理や実験済みを意味しない。有限診断を全実数の証明としない。']


def library():
    return dict(schema_version='0.16',lexicon_version='0.16',declarations=[
        dict(kind='primitive',name=n,parameters=r['parameters'],result=r['result']) for n,r in ALL_CONTRACTS.items()],statements=[])


def basis():
    return dict(status='optional_light_proof_task_visible_profile',document=LIBRARY,definitions={},primitives=ALL_CONTRACTS,
        public_contracts={n:dict(arguments=[dict(role=a,sort=s) for a,s in zip(r['arguments'],r['parameters'],strict=True)],
            result=r['result'],interpretation_inputs=CONTEXT) for n,r in ALL_CONTRACTS.items()},
        source_relations=SOURCE_RELATIONS,limitations=LIMITS)


def manifest():
    return dict(schema='noema-visible-optional-profile-1',edition=51,parent_profile=50,core_edition=12,
        library=LIBRARY,basis=BASIS,spellings=SPELLINGS,
        naming_convention='above/round/treeone/home/akiを証明提示・証明課題・課題理由・共通許容設定の語群とする。後続二要素は公開規約による綴りであり、文中の語義番号ではない。証明の欠如と両立性は既存定義で合成する。')


def prepare():
    write_once(LIBRARY,format_graph(library())+'\n');write_once(BASIS,basis());write_once(MANIFEST,manifest())


class LightProofTaskVisibleVocabulary(OriginConstantsVisibleVocabulary):
    def __init__(self):
        super().__init__();data=self.document();parent=deepcopy(data)
        require(json.loads((ROOT/MANIFEST).read_text(encoding='utf-8'))==manifest(),'LightProofTask-visible profile changed')
        require(parse((ROOT/LIBRARY).read_text(encoding='utf-8'))==library(),'LightProofTask-visible declarations changed')
        require(json.loads((ROOT/BASIS).read_text(encoding='utf-8'))==basis(),'LightProofTask-visible meanings changed')
        for d in library()['declarations']:
            n=d['name'];r=ALL_CONTRACTS[n];require(n not in self._words,'Profile name collision')
            word=canonical(Word('compound',tuple(SPELLINGS[n])),self)
            data['primitives'][n]=d;data['compounds'][n]=dict(parts=list(word.parts),parameters=d['parameters'],result=d['result'],
                roles=r['arguments'],meaning=r['meaning_ja'],context=CONTEXT,contrast=LIMITS,aliases=[])
            self._words[n]=word
        data.update(schema='noema-visible-light-proof-task-visible-profile-1',edition=51)
        data['naming_convention']+='\n'+manifest()['naming_convention'];self._document=data
        self._primitives=deepcopy(data['primitives']);self._symbols={n:symbol(w,self) for n,w in self._words.items()}
        require(len(set(self._symbols.values()))==len(self._words),'Profile spelling collision')
        self._by_symbol={s:n for n,s in self._symbols.items()};self._order=self._topological()
        normalize_document(dict(schema_version='0.16',lexicon_version='0.16',declarations=[self._plain_declaration(n) for n in self._order],statements=[]))
        for field in ('entries','compounds','definitions','primitives'):
            require(all(data[field].get(n)==d for n,d in parent[field].items()),'Previous profile changed')
