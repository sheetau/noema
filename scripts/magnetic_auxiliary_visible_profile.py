"""Optional analogy and theoretical concept use, preserving the fixed core."""
from copy import deepcopy
import json
from noema.constructed import parse,format_graph
from noema.constructed_discourse import normalize_document,function_sort,description_sort
from noema.constructed_semantics import FunctionValue,DescriptionValue
from scripts.two_force_wordings_visible_profile import ROOT,TwoForceWordingsVisibleVocabulary,write_once,CUT
from scripts.magnetic_auxiliary_visible_profile_contracts import CONTRACTS,SOURCE_RELATIONS
from scripts.visible_word_forms import Word,canonical,symbol
from scripts.visible_lexical_script import require

LIBRARY='examples/v016/magnetic-auxiliary-visible-profile-v1.noema'
BASIS='data/magnetic-auxiliary-visible-profile-basis-v1.json'
MANIFEST='noema/resources/visible-magnetic-auxiliary-visible-profile-v1.json'
ALL_CONTRACTS=CONTRACTS
PARAMETERS={n:r['parameters'] for n,r in ALL_CONTRACTS.items()}
PARTS=('home','above','give','inside','aki','nao','book','round')
SPELLINGS={'theoreticalconceptadoption': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'inside', 'rain'], 'attributedcontentanalogy': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'inside', 'town'], 'theorypermittedphysicalconfiguration': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'inside', 'home'], 'developedtheorypresentation': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'inside', 'above'], 'expressionconceptphysicalrole': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'inside', 'give'], 'theoryconstructiveconceptuse': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'inside', 'inside'], 'conceptusedefinitionalexpansion': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'inside', 'aki'], 'theoreticalintroductiongrounds': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'inside', 'nao']}
CONTEXT=['同じ理論・概念・使用・物理的な対象と提示文脈を保つ。', '引用した役割と構成を閉じた型で指定し、引用から物理的な真理を導かない。']
LIMITS=['固定アルファベットと共通375語を維持し、既存の八規約を任意profile74で公開する。', '類推の対応内容、磁気側の符号と近似、仮定上の磁極、共動系の条件は本文で合成する。', '理論の許容配置は実測例だけに限定しない。未知の関係を既定の偽や許容済みとして補わない。', '構成的使用の全範囲に独立な仮定としての使用も含め、置換成功例だけへ狭めない。', '定義展開は同じ使用の全箇所と物理的役割を保つ。全理論の保存拡張証明とは区別する。', '導入理由は同じ理論と概念への説明関係であり、単なる含意や心理的原因にしない。']


def library():
    return dict(schema_version='0.16',lexicon_version='0.16',declarations=[
        dict(kind='primitive',name=n,parameters=r['parameters'],result=r['result']) for n,r in ALL_CONTRACTS.items()],statements=[])


def basis():
    return dict(status='optional_magnetic_auxiliary_visible_profile',document=LIBRARY,definitions={},primitives=ALL_CONTRACTS,
        public_contracts={n:dict(arguments=[dict(role=a,sort=s) for a,s in zip(r['arguments'],r['parameters'],strict=True)],
            result=r['result'],interpretation_inputs=CONTEXT) for n,r in ALL_CONTRACTS.items()},
        source_relations=SOURCE_RELATIONS,limitations=LIMITS)


def manifest():
    return dict(schema='noema-visible-optional-profile-1',edition=74,parent_profile=73,core_edition=12,
        library=LIBRARY,basis=BASIS,spellings=SPELLINGS,
        naming_convention='above/round/treeone/home/nao/book/birdone/fruit/insideを類推・理論・構成的使用の公開規約の語群とする。後続要素は規約の綴りを区別し、文全体の物理的意味は合成する。')


def prepare():
    write_once(LIBRARY,format_graph(library())+'\n');write_once(BASIS,basis());write_once(MANIFEST,manifest())


class MagneticAuxiliaryVisibleVocabulary(TwoForceWordingsVisibleVocabulary):
    def __init__(self):
        super().__init__();data=self.document();parent=deepcopy(data)
        require(json.loads((ROOT/MANIFEST).read_text(encoding='utf-8'))==manifest(),'MagneticAuxiliary-visible profile changed')
        require(parse((ROOT/LIBRARY).read_text(encoding='utf-8'))==library(),'MagneticAuxiliary-visible declarations changed')
        require(json.loads((ROOT/BASIS).read_text(encoding='utf-8'))==basis(),'MagneticAuxiliary-visible meanings changed')
        for d in library()['declarations']:
            n=d['name'];r=ALL_CONTRACTS[n];require(n not in self._words,'Profile name collision')
            word=canonical(Word('compound',tuple(SPELLINGS[n])),self)
            data['primitives'][n]=d;data['compounds'][n]=dict(parts=list(word.parts),parameters=d['parameters'],result=d['result'],
                roles=r['arguments'],meaning=r['meaning_ja'],context=CONTEXT,contrast=LIMITS,aliases=[])
            self._words[n]=word
        data.update(schema='noema-visible-magnetic-auxiliary-visible-profile-1',edition=74)
        data['naming_convention']+='\n'+manifest()['naming_convention'];self._document=data
        self._primitives=deepcopy(data['primitives']);self._symbols={n:symbol(w,self) for n,w in self._words.items()}
        require(len(set(self._symbols.values()))==len(self._words),'Profile spelling collision')
        self._by_symbol={s:n for n,s in self._symbols.items()};self._order=self._topological()
        normalize_document(dict(schema_version='0.16',lexicon_version='0.16',declarations=[self._plain_declaration(n) for n in self._order],statements=[]))
        for field in ('entries','compounds','definitions','primitives'):
            require(all(data[field].get(n)==d for n,d in parent[field].items()),'Previous profile changed')
