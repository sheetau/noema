"""Optional physical inquiry about equations and specified subject properties."""
from copy import deepcopy
import json
from noema.constructed import parse,format_graph
from noema.constructed_discourse import normalize_document,function_sort,description_sort
from noema.constructed_semantics import FunctionValue,DescriptionValue
from scripts.transverse_symmetry_claim_visible_profile import ROOT,TransverseSymmetryClaimVisibleVocabulary,write_once,CUT
from scripts.visible_word_forms import Word,canonical,symbol
from scripts.visible_lexical_script import require
CONTRACTS={'introducesphysicalequationsinquiry': {'parameters': ['individual',
                                                       'individual',
                                                       {'kind': 'description',
                                                        'result': {'kind': 'function',
                                                                   'parameters': ['individual', 'individual'],
                                                                   'result': 'truth'}},
                                                       {'kind': 'sequence',
                                                        'element': {'kind': 'description',
                                                                    'result': {'kind': 'function',
                                                                               'parameters': ['individual'],
                                                                               'result': 'truth'}}},
                                                       'individual',
                                                       'situation'],
                                        'result': 'truth',
                                        'arguments': ['node',
                                                      'author',
                                                      'equations',
                                                      'subject_properties',
                                                      'scope',
                                                      'context'],
                                        'meaning_ja': '著者が節題で、指定した方程式の物理的な意味を指定した対象の性質について検討すると示す。本文の結論を節題から補わない。'}}
SOURCE_RELATIONS={'zhr': 'introducesphysicalequationsinquiry'}

LIBRARY='examples/v016/physical-meaning-heading-visible-profile-v1.noema'
BASIS='data/physical-meaning-heading-visible-profile-basis-v1.json'
MANIFEST='noema/resources/visible-physical-meaning-heading-visible-profile-v1.json'
ALL_CONTRACTS=CONTRACTS
PARAMETERS={n:r['parameters'] for n,r in ALL_CONTRACTS.items()}
PARTS=('home','above','give','inside','aki','nao','book','round')
SPELLINGS={'introducesphysicalequationsinquiry': ['above',
                                        'round',
                                        'treeone',
                                        'home',
                                        'nao',
                                        'book',
                                        'birdone',
                                        'rain']}
CONTEXT=['同じ方程式、対象の性質の列、著者、節の範囲、文脈を保つ。研究主題の提示から結論や証明の完成を補わない。']
LIMITS=['共通375語とアルファベットを維持し、採用済みの物理的意味に関する主題提示を任意プロファイルへ公開する。',
 '同じ方程式の記述と対象性質の記述列を受け取り、主題の提示、主張の真理、実験、導出の完成を区別する。',
 '引用した関係や性質を参照取得や主題提示から実行しない。有限診断は実数全域の証明ではない。']


def library():
    return dict(schema_version='0.16',lexicon_version='0.16',declarations=[
        dict(kind='primitive',name=n,parameters=r['parameters'],result=r['result']) for n,r in ALL_CONTRACTS.items()],statements=[])


def basis():
    return dict(status='optional_physical_meaning_heading_visible_profile',document=LIBRARY,definitions={},primitives=ALL_CONTRACTS,
        public_contracts={n:dict(arguments=[dict(role=a,sort=s) for a,s in zip(r['arguments'],r['parameters'],strict=True)],
            result=r['result'],interpretation_inputs=CONTEXT) for n,r in ALL_CONTRACTS.items()},
        source_relations=SOURCE_RELATIONS,limitations=LIMITS)


def manifest():
    return dict(schema='noema-visible-optional-profile-1',edition=58,parent_profile=57,core_edition=12,
        library=LIBRARY,basis=BASIS,spellings=SPELLINGS,
        naming_convention='above/round/treeone/home/nao/book/birdoneを方程式の物理的意味を指定した対象について検討する主題提示の語群とする。後続要素は公開規約を区別する綴りであり、対象や引数は本文で結ぶ。')


def prepare():
    write_once(LIBRARY,format_graph(library())+'\n');write_once(BASIS,basis());write_once(MANIFEST,manifest())


class PhysicalMeaningHeadingVisibleVocabulary(TransverseSymmetryClaimVisibleVocabulary):
    def __init__(self):
        super().__init__();data=self.document();parent=deepcopy(data)
        require(json.loads((ROOT/MANIFEST).read_text(encoding='utf-8'))==manifest(),'PhysicalMeaningHeading-visible profile changed')
        require(parse((ROOT/LIBRARY).read_text(encoding='utf-8'))==library(),'PhysicalMeaningHeading-visible declarations changed')
        require(json.loads((ROOT/BASIS).read_text(encoding='utf-8'))==basis(),'PhysicalMeaningHeading-visible meanings changed')
        for d in library()['declarations']:
            n=d['name'];r=ALL_CONTRACTS[n];require(n not in self._words,'Profile name collision')
            word=canonical(Word('compound',tuple(SPELLINGS[n])),self)
            data['primitives'][n]=d;data['compounds'][n]=dict(parts=list(word.parts),parameters=d['parameters'],result=d['result'],
                roles=r['arguments'],meaning=r['meaning_ja'],context=CONTEXT,contrast=LIMITS,aliases=[])
            self._words[n]=word
        data.update(schema='noema-visible-physical-meaning-heading-visible-profile-1',edition=58)
        data['naming_convention']+='\n'+manifest()['naming_convention'];self._document=data
        self._primitives=deepcopy(data['primitives']);self._symbols={n:symbol(w,self) for n,w in self._words.items()}
        require(len(set(self._symbols.values()))==len(self._words),'Profile spelling collision')
        self._by_symbol={s:n for n,s in self._symbols.items()};self._order=self._topological()
        normalize_document(dict(schema_version='0.16',lexicon_version='0.16',declarations=[self._plain_declaration(n) for n in self._order],statements=[]))
        for field in ('entries','compounds','definitions','primitives'):
            require(all(data[field].get(n)==d for n,d in parent[field].items()),'Previous profile changed')
