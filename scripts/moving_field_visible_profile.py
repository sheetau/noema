"""Optional signed probe-force responses and physical unit calibration."""
from copy import deepcopy
import json
from noema.constructed import parse,format_graph
from noema.constructed_discourse import normalize_document,function_sort,description_sort
from noema.constructed_semantics import FunctionValue,DescriptionValue
from scripts.field_application_visible_profile import ROOT,FieldApplicationVisibleVocabulary,write_once,CUT
from scripts.moving_field_visible_profile_contracts import CONTRACTS,SOURCE_RELATIONS
from scripts.visible_word_forms import Word,canonical,symbol
from scripts.visible_lexical_script import require

LIBRARY='examples/v016/moving-field-visible-profile-v1.noema'
BASIS='data/moving-field-visible-profile-basis-v1.json'
MANIFEST='noema/resources/visible-moving-field-visible-profile-v1.json'
ALL_CONTRACTS=CONTRACTS
PARAMETERS={n:r['parameters'] for n,r in ALL_CONTRACTS.items()}
PARTS=('home','above','give','inside','aki','nao','book','round')
SPELLINGS={'magneticpolestrengthkind': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'book', 'rain'],
 'signedtestforceresponse': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'book', 'town'],
 'amountfieldforcecalibration': ['above',
                                 'round',
                                 'treeone',
                                 'home',
                                 'nao',
                                 'book',
                                 'birdone',
                                 'book',
                                 'home']}
CONTEXT=['同じ系・座標尺度・領域・量種・力単位・文脈で物理的な応答を同定する。',
 '試験量と大きさを零へ近づける一次応答を、符号付き量で規格化して扱う。',
 '量種・校正・応答の基本規約と、本文で構成する全点全試験量の比例を区別する。']
LIMITS=['固定アルファベットと共通375語を維持し、採用済み3規約を任意profile69へ公開する。',
 '電荷と磁極強度を区別し、慣性質量、支持力などを含む合力、全磁石への合力へ読み替えない。',
 '磁極の局所的理想化は、孤立磁荷や実際の試験体の存在を含意しない。',
 '理想応答を有限の大きな試験体の厳密な線形応答や、実験を実施した証拠としない。',
 '正の単位換算係数を同じ文脈で保持し、1や現代SIの定数へ固定しない。',
 '計算上の混合関数と物理的に定義した移動場を、この規約だけで同一視しない。',
 '有限例や引用の参照取得を、全実数・全関数域の証明や世界の真理の認定としない。']



def library():
    return dict(schema_version='0.16',lexicon_version='0.16',declarations=[
        dict(kind='primitive',name=n,parameters=r['parameters'],result=r['result']) for n,r in ALL_CONTRACTS.items()],statements=[])


def basis():
    return dict(status='optional_moving_field_visible_profile',document=LIBRARY,definitions={},primitives=ALL_CONTRACTS,
        public_contracts={n:dict(arguments=[dict(role=a,sort=s) for a,s in zip(r['arguments'],r['parameters'],strict=True)],
            result=r['result'],interpretation_inputs=CONTEXT) for n,r in ALL_CONTRACTS.items()},
        source_relations=SOURCE_RELATIONS,limitations=LIMITS)


def manifest():
    return dict(schema='noema-visible-optional-profile-1',edition=69,parent_profile=68,core_edition=12,
        library=LIBRARY,basis=BASIS,spellings=SPELLINGS,
        naming_convention='above/round/treeone/home/nao/book/birdone/bookを磁極強度・符号付き試験量への力応答・単位積校正の語群とする。後続要素は保存された公開規約の綴りを区別する。場の定義、条件文、原理の適用は本文で合成する。')


def prepare():
    write_once(LIBRARY,format_graph(library())+'\n');write_once(BASIS,basis());write_once(MANIFEST,manifest())


class MovingFieldVisibleVocabulary(FieldApplicationVisibleVocabulary):
    def __init__(self):
        super().__init__();data=self.document();parent=deepcopy(data)
        require(json.loads((ROOT/MANIFEST).read_text(encoding='utf-8'))==manifest(),'MovingField-visible profile changed')
        require(parse((ROOT/LIBRARY).read_text(encoding='utf-8'))==library(),'MovingField-visible declarations changed')
        require(json.loads((ROOT/BASIS).read_text(encoding='utf-8'))==basis(),'MovingField-visible meanings changed')
        for d in library()['declarations']:
            n=d['name'];r=ALL_CONTRACTS[n];require(n not in self._words,'Profile name collision')
            word=canonical(Word('compound',tuple(SPELLINGS[n])),self)
            data['primitives'][n]=d;data['compounds'][n]=dict(parts=list(word.parts),parameters=d['parameters'],result=d['result'],
                roles=r['arguments'],meaning=r['meaning_ja'],context=CONTEXT,contrast=LIMITS,aliases=[])
            self._words[n]=word
        data.update(schema='noema-visible-moving-field-visible-profile-1',edition=69)
        data['naming_convention']+='\n'+manifest()['naming_convention'];self._document=data
        self._primitives=deepcopy(data['primitives']);self._symbols={n:symbol(w,self) for n,w in self._words.items()}
        require(len(set(self._symbols.values()))==len(self._words),'Profile spelling collision')
        self._by_symbol={s:n for n,s in self._symbols.items()};self._order=self._topological()
        normalize_document(dict(schema_version='0.16',lexicon_version='0.16',declarations=[self._plain_declaration(n) for n in self._order],statements=[]))
        for field in ('entries','compounds','definitions','primitives'):
            require(all(data[field].get(n)==d for n,d in parent[field].items()),'Previous profile changed')
