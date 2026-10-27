"""Optional attributed proof status; the conclusion content is composed in the text."""
from copy import deepcopy
import json
from noema.constructed import parse,format_graph
from noema.constructed_discourse import normalize_document,function_sort,description_sort
from noema.constructed_semantics import FunctionValue,DescriptionValue
from scripts.rest_spherical_wave_visible_profile import ROOT,RestSphericalWaveVisibleVocabulary,write_once,CUT
from scripts.visible_word_forms import Word,canonical,symbol
from scripts.visible_lexical_script import require
CONTRACTS={'presentsasproved': {'parameters': ['individual', 'individual', 'situation'], 'result': 'truth', 'arguments': ['author', 'node', 'context'], 'meaning_ja': '著者が指定箇所の内容を既に証明されたものとして扱う。著者による証明済みという位置付けであり、検査器が証明を確認したという関係ではない。'}};SOURCE_RELATIONS={'ui':'presentsasproved'}

LIBRARY='examples/v016/wave-compatibility-conclusion-visible-profile-v1.noema'
BASIS='data/wave-compatibility-conclusion-visible-profile-basis-v1.json'
MANIFEST='noema/resources/visible-wave-compatibility-conclusion-visible-profile-v1.json'
ALL_CONTRACTS=CONTRACTS
PARAMETERS={n:r['parameters'] for n,r in ALL_CONTRACTS.items()}
PARTS=('home','above','give','inside','aki','nao','book','round')
SPELLINGS={name:['above','round','treeone','home','nao','book',PARTS[i//8],PARTS[i%8]] for i,name in enumerate(ALL_CONTRACTS)}
CONTEXT=['同じ課題・方式・対象・文書・文脈を保持する。見かけ、可能性、採用、実施を区別する。']
LIMITS=['共通375語は不変。旧関係の型・役割・意味を任意プロファイルとして公開する。',
        '記録の成分位置は公開されたデータの欄であり語義番号ではない。未知の値を既定値で補わない。',
        '参照・引用・前方指示はその内容の真理や実験済みを意味しない。有限診断を全実数の証明としない。']


def library():
    return dict(schema_version='0.16',lexicon_version='0.16',declarations=[
        dict(kind='primitive',name=n,parameters=r['parameters'],result=r['result']) for n,r in ALL_CONTRACTS.items()],statements=[])


def basis():
    return dict(status='optional_wave_compatibility_conclusion_visible_profile',document=LIBRARY,definitions={},primitives=ALL_CONTRACTS,
        public_contracts={n:dict(arguments=[dict(role=a,sort=s) for a,s in zip(r['arguments'],r['parameters'],strict=True)],
            result=r['result'],interpretation_inputs=CONTEXT) for n,r in ALL_CONTRACTS.items()},
        source_relations=SOURCE_RELATIONS,limitations=LIMITS)


def manifest():
    return dict(schema='noema-visible-optional-profile-1',edition=53,parent_profile=52,core_edition=12,
        library=LIBRARY,basis=BASIS,spellings=SPELLINGS,
        naming_convention='above/round/treeone/home/nao/bookを著者による証明済みの位置付けの語群とする。後続二要素は公開規約の綴り。検査器による証明認定と区別し、対象内容と論述上の結論は既存定義で合成する。')


def prepare():
    write_once(LIBRARY,format_graph(library())+'\n');write_once(BASIS,basis());write_once(MANIFEST,manifest())


class WaveCompatibilityConclusionVisibleVocabulary(RestSphericalWaveVisibleVocabulary):
    def __init__(self):
        super().__init__();data=self.document();parent=deepcopy(data)
        require(json.loads((ROOT/MANIFEST).read_text(encoding='utf-8'))==manifest(),'WaveCompatibilityConclusion-visible profile changed')
        require(parse((ROOT/LIBRARY).read_text(encoding='utf-8'))==library(),'WaveCompatibilityConclusion-visible declarations changed')
        require(json.loads((ROOT/BASIS).read_text(encoding='utf-8'))==basis(),'WaveCompatibilityConclusion-visible meanings changed')
        for d in library()['declarations']:
            n=d['name'];r=ALL_CONTRACTS[n];require(n not in self._words,'Profile name collision')
            word=canonical(Word('compound',tuple(SPELLINGS[n])),self)
            data['primitives'][n]=d;data['compounds'][n]=dict(parts=list(word.parts),parameters=d['parameters'],result=d['result'],
                roles=r['arguments'],meaning=r['meaning_ja'],context=CONTEXT,contrast=LIMITS,aliases=[])
            self._words[n]=word
        data.update(schema='noema-visible-wave-compatibility-conclusion-visible-profile-1',edition=53)
        data['naming_convention']+='\n'+manifest()['naming_convention'];self._document=data
        self._primitives=deepcopy(data['primitives']);self._symbols={n:symbol(w,self) for n,w in self._words.items()}
        require(len(set(self._symbols.values()))==len(self._words),'Profile spelling collision')
        self._by_symbol={s:n for n,s in self._symbols.items()};self._order=self._topological()
        normalize_document(dict(schema_version='0.16',lexicon_version='0.16',declarations=[self._plain_declaration(n) for n in self._order],statements=[]))
        for field in ('entries','compounds','definitions','primitives'):
            require(all(data[field].get(n)==d for n,d in parent[field].items()),'Previous profile changed')
