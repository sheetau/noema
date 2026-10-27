"""Optional attributed intention to determine a function; no successful determination implied."""
from copy import deepcopy
import json
from noema.constructed import parse,format_graph
from noema.constructed_discourse import normalize_document,function_sort,description_sort
from noema.constructed_semantics import FunctionValue,DescriptionValue
from scripts.wave_compatibility_conclusion_visible_profile import ROOT,WaveCompatibilityConclusionVisibleVocabulary,write_once,CUT
from scripts.visible_word_forms import Word,canonical,symbol
from scripts.visible_lexical_script import require
CONTRACTS={'presentsfunctiondeterminationintent': {'parameters': ['individual', 'individual', {'kind': 'description', 'result': {'kind': 'function', 'parameters': [{'kind': 'function', 'parameters': ['number'], 'result': 'truth'}], 'result': {'kind': 'function', 'parameters': ['number'], 'result': 'truth'}}}, 'situation', 'individual', 'situation'], 'result': 'truth', 'arguments': ['node', 'author', 'function_description', 'stage', 'scope', 'context'], 'meaning_ja': '著者が指定した関数の記述を対象として、その値を決定する意図を示す。決定済み・唯一解・計算手段を含意しない。'}};SOURCE_RELATIONS={'zgm':'presentsfunctiondeterminationintent'}

LIBRARY='examples/v016/phi-determination-intent-visible-profile-v1.noema'
BASIS='data/phi-determination-intent-visible-profile-basis-v1.json'
MANIFEST='noema/resources/visible-phi-determination-intent-visible-profile-v1.json'
ALL_CONTRACTS=CONTRACTS
PARAMETERS={n:r['parameters'] for n,r in ALL_CONTRACTS.items()}
PARTS=('home','above','give','inside','aki','nao','book','round')
SPELLINGS={'presentsfunctiondeterminationintent':['above', 'round', 'treeone', 'home', 'nao', 'book', 'home', 'above']}
CONTEXT=['同じ課題・方式・対象・文書・文脈を保持する。見かけ、可能性、採用、実施を区別する。']
LIMITS=['共通375語は不変。旧関係の型・役割・意味を任意プロファイルとして公開する。',
        '記録の成分位置は公開されたデータの欄であり語義番号ではない。未知の値を既定値で補わない。',
        '参照・引用・前方指示はその内容の真理や実験済みを意味しない。有限診断を全実数の証明としない。']


def library():
    return dict(schema_version='0.16',lexicon_version='0.16',declarations=[
        dict(kind='primitive',name=n,parameters=r['parameters'],result=r['result']) for n,r in ALL_CONTRACTS.items()],statements=[])


def basis():
    return dict(status='optional_phi_determination_intent_visible_profile',document=LIBRARY,definitions={},primitives=ALL_CONTRACTS,
        public_contracts={n:dict(arguments=[dict(role=a,sort=s) for a,s in zip(r['arguments'],r['parameters'],strict=True)],
            result=r['result'],interpretation_inputs=CONTEXT) for n,r in ALL_CONTRACTS.items()},
        source_relations=SOURCE_RELATIONS,limitations=LIMITS)


def manifest():
    return dict(schema='noema-visible-optional-profile-1',edition=54,parent_profile=53,core_edition=12,
        library=LIBRARY,basis=BASIS,spellings=SPELLINGS,
        naming_convention='above/round/treeone/home/nao/book/home/aboveを、指定した関数の値を決定する意図の綴りとする。著者・対象の記述・段階・範囲・文脈を引数で区別する。')


def prepare():
    write_once(LIBRARY,format_graph(library())+'\n');write_once(BASIS,basis());write_once(MANIFEST,manifest())


class PhiDeterminationIntentVisibleVocabulary(WaveCompatibilityConclusionVisibleVocabulary):
    def __init__(self):
        super().__init__();data=self.document();parent=deepcopy(data)
        require(json.loads((ROOT/MANIFEST).read_text(encoding='utf-8'))==manifest(),'PhiDeterminationIntent-visible profile changed')
        require(parse((ROOT/LIBRARY).read_text(encoding='utf-8'))==library(),'PhiDeterminationIntent-visible declarations changed')
        require(json.loads((ROOT/BASIS).read_text(encoding='utf-8'))==basis(),'PhiDeterminationIntent-visible meanings changed')
        for d in library()['declarations']:
            n=d['name'];r=ALL_CONTRACTS[n];require(n not in self._words,'Profile name collision')
            word=canonical(Word('compound',tuple(SPELLINGS[n])),self)
            data['primitives'][n]=d;data['compounds'][n]=dict(parts=list(word.parts),parameters=d['parameters'],result=d['result'],
                roles=r['arguments'],meaning=r['meaning_ja'],context=CONTEXT,contrast=LIMITS,aliases=[])
            self._words[n]=word
        data.update(schema='noema-visible-phi-determination-intent-visible-profile-1',edition=54)
        data['naming_convention']+='\n'+manifest()['naming_convention'];self._document=data
        self._primitives=deepcopy(data['primitives']);self._symbols={n:symbol(w,self) for n,w in self._words.items()}
        require(len(set(self._symbols.values()))==len(self._words),'Profile spelling collision')
        self._by_symbol={s:n for n,s in self._symbols.items()};self._order=self._topological()
        normalize_document(dict(schema_version='0.16',lexicon_version='0.16',declarations=[self._plain_declaration(n) for n in self._order],statements=[]))
        for field in ('entries','compounds','definitions','primitives'):
            require(all(data[field].get(n)==d for n,d in parent[field].items()),'Previous profile changed')
