"""Optional motion history, spatial symmetry and epistemic adoption permission."""
from copy import deepcopy
import json
from noema.constructed import parse,format_graph
from noema.constructed_discourse import normalize_document
from scripts.standard_configuration_visible_profile import ROOT,StandardConfigurationVisibleVocabulary,write_once,CUT
from scripts.visible_word_forms import Word,canonical,symbol
from scripts.visible_lexical_script import require
from scripts.parallel_choice_visible_profile_contracts import CONTRACTS,SOURCE_RELATIONS

LIBRARY='examples/v016/parallel-choice-visible-profile-v1.noema'
BASIS='data/parallel-choice-visible-profile-basis-v1.json'
MANIFEST='noema/resources/visible-parallel-choice-visible-profile-v1.json'
I='individual';S='situation';N='number'
EXTRA={}

ALL_CONTRACTS=CONTRACTS|EXTRA
PARAMETERS={n:r['parameters'] for n,r in ALL_CONTRACTS.items()}
PARTS=('home','above','give','inside','aki','nao','book','round')
SPELLINGS={name:['above','round','fly',PARTS[i//8],PARTS[i%8]] for i,name in enumerate(ALL_CONTRACTS)}
CONTEXT=['同じ課題・方式・対象・文書・文脈を保持する。見かけ、可能性、採用、実施を区別する。']
LIMITS=['共通375語は不変。旧関係の型・役割・意味を任意プロファイルとして公開する。',
        '記録の成分位置は公開されたデータの欄であり語義番号ではない。未知の値を既定値で補わない。',
        '参照・引用・前方指示はその内容の真理や実験済みを意味しない。有限診断を全実数の証明としない。']


def library():
    return dict(schema_version='0.16',lexicon_version='0.16',declarations=[
        dict(kind='primitive',name=n,parameters=r['parameters'],result=r['result']) for n,r in ALL_CONTRACTS.items()],statements=[])


def basis():
    return dict(status='optional_parallel_choice_visible_profile',document=LIBRARY,definitions={},primitives=ALL_CONTRACTS,
        public_contracts={n:dict(arguments=[dict(role=a,sort=s) for a,s in zip(r['arguments'],r['parameters'],strict=True)],
            result=r['result'],interpretation_inputs=CONTEXT) for n,r in ALL_CONTRACTS.items()},
        source_relations=SOURCE_RELATIONS,limitations=LIMITS)


def manifest():
    return dict(schema='noema-visible-optional-profile-1',edition=37,parent_profile=36,core_edition=12,
        library=LIBRARY,basis=BASIS,spellings=SPELLINGS,
        naming_convention='above/round/flyを運動履歴・空間対称性・仮定採用の許容の語群とする。後続の二要素は公開規約で区別する綴りであり、文中に数値の語義表を置かない。役割と数学は本文定義として示す。')


def prepare():
    write_once(LIBRARY,format_graph(library())+'\n');write_once(BASIS,basis());write_once(MANIFEST,manifest())


class ParallelChoiceVisibleVocabulary(StandardConfigurationVisibleVocabulary):
    def __init__(self):
        super().__init__();data=self.document();parent=deepcopy(data)
        require(json.loads((ROOT/MANIFEST).read_text(encoding='utf-8'))==manifest(),'Parallel-choice-visible profile changed')
        require(parse((ROOT/LIBRARY).read_text(encoding='utf-8'))==library(),'Parallel-choice-visible declarations changed')
        require(json.loads((ROOT/BASIS).read_text(encoding='utf-8'))==basis(),'Parallel-choice-visible meanings changed')
        for d in library()['declarations']:
            n=d['name'];r=ALL_CONTRACTS[n];require(n not in self._words,'Profile name collision')
            word=canonical(Word('compound',tuple(SPELLINGS[n])),self)
            data['primitives'][n]=d;data['compounds'][n]=dict(parts=list(word.parts),parameters=d['parameters'],result=d['result'],
                roles=r['arguments'],meaning=r['meaning_ja'],context=CONTEXT,contrast=LIMITS,aliases=[])
            self._words[n]=word
        data.update(schema='noema-visible-parallel-choice-visible-profile-1',edition=37)
        data['naming_convention']+='\n'+manifest()['naming_convention'];self._document=data
        self._primitives=deepcopy(data['primitives']);self._symbols={n:symbol(w,self) for n,w in self._words.items()}
        require(len(set(self._symbols.values()))==len(self._words),'Profile spelling collision')
        self._by_symbol={s:n for n,s in self._symbols.items()};self._order=self._topological()
        normalize_document(dict(schema_version='0.16',lexicon_version='0.16',declarations=[self._plain_declaration(n) for n in self._order],statements=[]))
        for field in ('entries','compounds','definitions','primitives'):
            require(all(data[field].get(n)==d for n,d in parent[field].items()),'Previous profile changed')
