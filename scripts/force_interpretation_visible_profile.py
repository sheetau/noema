"""Optional directed calibration, unit coordinates and physical wording conventions."""
from copy import deepcopy
import json
from noema.constructed import parse,format_graph
from noema.constructed_discourse import normalize_document,function_sort,description_sort
from noema.constructed_semantics import FunctionValue,DescriptionValue
from scripts.field_symmetry_visible_profile import ROOT,FieldSymmetryVisibleVocabulary,write_once,CUT
from scripts.force_interpretation_visible_profile_contracts import CONTRACTS,SOURCE_RELATIONS
from scripts.visible_word_forms import Word,canonical,symbol
from scripts.visible_lexical_script import require

LIBRARY='examples/v016/force-interpretation-visible-profile-v1.noema'
BASIS='data/force-interpretation-visible-profile-basis-v1.json'
MANIFEST='noema/resources/visible-force-interpretation-visible-profile-v1.json'
ALL_CONTRACTS=CONTRACTS
PARAMETERS={n:r['parameters'] for n,r in ALL_CONTRACTS.items()}
PARTS=('home','above','give','inside','aki','nao','book','round')
SPELLINGS={'directedcomparisontrial': ['above',
                             'round',
                             'treeone',
                             'home',
                             'nao',
                             'book',
                             'birdone',
                             'fruit',
                             'home',
                             'rain'],
 'baseunitdimensions': ['above',
                        'round',
                        'treeone',
                        'home',
                        'nao',
                        'book',
                        'birdone',
                        'fruit',
                        'home',
                        'town'],
 'pointchargecarrier': ['above',
                        'round',
                        'treeone',
                        'home',
                        'nao',
                        'book',
                        'birdone',
                        'fruit',
                        'home',
                        'home'],
 'unitpositionassignment': ['above',
                            'round',
                            'treeone',
                            'home',
                            'nao',
                            'book',
                            'birdone',
                            'fruit',
                            'home',
                            'above'],
 'directedelectricforcerecord': ['above',
                                 'round',
                                 'treeone',
                                 'home',
                                 'nao',
                                 'book',
                                 'birdone',
                                 'fruit',
                                 'home',
                                 'give'],
 'definitionbasedclaim': ['above',
                          'round',
                          'treeone',
                          'home',
                          'nao',
                          'book',
                          'birdone',
                          'fruit',
                          'home',
                          'inside'],
 'canwordcontent': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'home', 'aki']}
CONTEXT=['同じ対象・試行・系・出来事・単位と提示文脈を保持する。',
 '校正の条件、原理からの推論、定義に基づく主張、式の言葉による解釈を本文で合成する。']
LIMITS=['固定アルファベットと共通375語を維持し、採用済み7規約を任意profile72へ公開する。',
 '有向試行の作用元と受け手を区別し、電気的寄与を合力や反作用へ置き換えない。',
 '点電荷の理想化は、第二担体の点性、粒子の実在、試行の実施を含意しない。',
 '長さ・質量・時間の次元と尺度を保持し、本文のcm・Dynを現代SIの定数へ置き換えない。',
 '静止と瞬間静止、校正出来事と評価出来事、校正座標と場の座標は本文で区別する。',
 '引用した定義や内容を実行しない。定義適用の帰属は、主張の真理や推論の自動認定ではない。',
 '言葉で述べる可能性を、留保を除いた厳密同値や発話済みと同一視しない。',
 '型付き参照の規約は親profileを継承し、役割の成立・存在・唯一性は取得だけでは保証しない。']



def library():
    return dict(schema_version='0.16',lexicon_version='0.16',declarations=[
        dict(kind='primitive',name=n,parameters=r['parameters'],result=r['result']) for n,r in ALL_CONTRACTS.items()],statements=[])


def basis():
    return dict(status='optional_force_interpretation_visible_profile',document=LIBRARY,definitions={},primitives=ALL_CONTRACTS,
        public_contracts={n:dict(arguments=[dict(role=a,sort=s) for a,s in zip(r['arguments'],r['parameters'],strict=True)],
            result=r['result'],interpretation_inputs=CONTEXT) for n,r in ALL_CONTRACTS.items()},
        source_relations=SOURCE_RELATIONS,limitations=LIMITS)


def manifest():
    return dict(schema='noema-visible-optional-profile-1',edition=72,parent_profile=71,core_edition=12,
        library=LIBRARY,basis=BASIS,spellings=SPELLINGS,
        naming_convention='above/round/treeone/home/nao/book/birdone/fruit/homeを有向校正・単位・物理的な解釈の規約の語群とする。後続要素は保存した規約の綴りを区別する。対象の役割、条件、原理の適用と言い方の順序は本文で合成する。')


def prepare():
    write_once(LIBRARY,format_graph(library())+'\n');write_once(BASIS,basis());write_once(MANIFEST,manifest())


class ForceInterpretationVisibleVocabulary(FieldSymmetryVisibleVocabulary):
    def __init__(self):
        super().__init__();data=self.document();parent=deepcopy(data)
        require(json.loads((ROOT/MANIFEST).read_text(encoding='utf-8'))==manifest(),'ForceInterpretation-visible profile changed')
        require(parse((ROOT/LIBRARY).read_text(encoding='utf-8'))==library(),'ForceInterpretation-visible declarations changed')
        require(json.loads((ROOT/BASIS).read_text(encoding='utf-8'))==basis(),'ForceInterpretation-visible meanings changed')
        for d in library()['declarations']:
            n=d['name'];r=ALL_CONTRACTS[n];require(n not in self._words,'Profile name collision')
            word=canonical(Word('compound',tuple(SPELLINGS[n])),self)
            data['primitives'][n]=d;data['compounds'][n]=dict(parts=list(word.parts),parameters=d['parameters'],result=d['result'],
                roles=r['arguments'],meaning=r['meaning_ja'],context=CONTEXT,contrast=LIMITS,aliases=[])
            self._words[n]=word
        data.update(schema='noema-visible-force-interpretation-visible-profile-1',edition=72)
        data['naming_convention']+='\n'+manifest()['naming_convention'];self._document=data
        self._primitives=deepcopy(data['primitives']);self._symbols={n:symbol(w,self) for n,w in self._words.items()}
        require(len(set(self._symbols.values()))==len(self._words),'Profile spelling collision')
        self._by_symbol={s:n for n,s in self._symbols.items()};self._order=self._topological()
        normalize_document(dict(schema_version='0.16',lexicon_version='0.16',declarations=[self._plain_declaration(n) for n in self._order],statements=[]))
        for field in ('entries','compounds','definitions','primitives'):
            require(all(data[field].get(n)==d for n,d in parent[field].items()),'Previous profile changed')
