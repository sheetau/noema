"""Optional moving response, quoted vector term, wording contrast and physical chart correspondence."""
from copy import deepcopy
import json
from noema.constructed import parse,format_graph
from noema.constructed_discourse import normalize_document,function_sort,description_sort
from noema.constructed_semantics import FunctionValue,DescriptionValue
from scripts.force_interpretation_visible_profile import ROOT,ForceInterpretationVisibleVocabulary,write_once,CUT
from scripts.two_force_wordings_visible_profile_contracts import CONTRACTS,SOURCE_RELATIONS
from scripts.visible_word_forms import Word,canonical,symbol
from scripts.visible_lexical_script import require

LIBRARY='examples/v016/two-force-wordings-visible-profile-v1.noema'
BASIS='data/two-force-wordings-visible-profile-basis-v1.json'
MANIFEST='noema/resources/visible-two-force-wordings-visible-profile-v1.json'
ALL_CONTRACTS=CONTRACTS
PARAMETERS={n:r['parameters'] for n,r in ALL_CONTRACTS.items()}
PARTS=('home','above','give','inside','aki','nao','book','round')
SPELLINGS={'movingtestforceresponse': ['above',
                             'round',
                             'treeone',
                             'home',
                             'nao',
                             'book',
                             'birdone',
                             'fruit',
                             'above',
                             'rain'],
 'quotedvectorquantityterm': ['above',
                              'round',
                              'treeone',
                              'home',
                              'nao',
                              'book',
                              'birdone',
                              'fruit',
                              'above',
                              'town'],
 'establishednewwordingcontrast': ['above',
                                   'round',
                                   'treeone',
                                   'home',
                                   'nao',
                                   'book',
                                   'birdone',
                                   'fruit',
                                   'above',
                                   'home'],
 'physicalcoordinatecorrespondence': ['above',
                                      'round',
                                      'treeone',
                                      'home',
                                      'nao',
                                      'book',
                                      'birdone',
                                      'fruit',
                                      'above',
                                      'above']}
CONTEXT=['同じ対象・出来事・系・単位・背景の両場・提示文脈を保持する。',
 '速度応答、用語の引用、旧新の言い方、物理的な座標対応を別の関係として合成する。']
LIMITS=['固定アルファベットと共通375語を維持し、採用済み四規約を任意profile73へ公開する。',
 '速度応答は同じ背景の電磁的寄与であり、合力・実測・特定の力の法則を自動認定しない。',
 '零速度との一致、外積の順序、一次式と二次以上の留保は本文で合成する。',
 '引用用語の規則を実行せず、表記だけを物理的な意味の代用にしない。',
 '旧新の対置は歴史的初出、禁止、優劣、有限速度での厳密同値を含意しない。',
 '座標全域の同一出来事対応を、数値写像や記録のある一点だけで認定しない。',
 '瞬間共動と前後の静止を区別し、共動系の力に旧系の成分をコピーしない。',
 '型付き参照の取得は役割の成立・存在・唯一性や引用内容の真理を保証しない。']



def library():
    return dict(schema_version='0.16',lexicon_version='0.16',declarations=[
        dict(kind='primitive',name=n,parameters=r['parameters'],result=r['result']) for n,r in ALL_CONTRACTS.items()],statements=[])


def basis():
    return dict(status='optional_two_force_wordings_visible_profile',document=LIBRARY,definitions={},primitives=ALL_CONTRACTS,
        public_contracts={n:dict(arguments=[dict(role=a,sort=s) for a,s in zip(r['arguments'],r['parameters'],strict=True)],
            result=r['result'],interpretation_inputs=CONTEXT) for n,r in ALL_CONTRACTS.items()},
        source_relations=SOURCE_RELATIONS,limitations=LIMITS)


def manifest():
    return dict(schema='noema-visible-optional-profile-1',edition=73,parent_profile=72,core_edition=12,
        library=LIBRARY,basis=BASIS,spellings=SPELLINGS,
        naming_convention='above/round/treeone/home/nao/book/birdone/fruit/aboveを速度応答・用語の引用・言い方・物理的座標対応の規約の語群とする。後続要素は保存した規約の綴りを区別する。二つの言い表しの条件、数式、近似、対象の役割は本文で合成する。')


def prepare():
    write_once(LIBRARY,format_graph(library())+'\n');write_once(BASIS,basis());write_once(MANIFEST,manifest())


class TwoForceWordingsVisibleVocabulary(ForceInterpretationVisibleVocabulary):
    def __init__(self):
        super().__init__();data=self.document();parent=deepcopy(data)
        require(json.loads((ROOT/MANIFEST).read_text(encoding='utf-8'))==manifest(),'TwoForceWordings-visible profile changed')
        require(parse((ROOT/LIBRARY).read_text(encoding='utf-8'))==library(),'TwoForceWordings-visible declarations changed')
        require(json.loads((ROOT/BASIS).read_text(encoding='utf-8'))==basis(),'TwoForceWordings-visible meanings changed')
        for d in library()['declarations']:
            n=d['name'];r=ALL_CONTRACTS[n];require(n not in self._words,'Profile name collision')
            word=canonical(Word('compound',tuple(SPELLINGS[n])),self)
            data['primitives'][n]=d;data['compounds'][n]=dict(parts=list(word.parts),parameters=d['parameters'],result=d['result'],
                roles=r['arguments'],meaning=r['meaning_ja'],context=CONTEXT,contrast=LIMITS,aliases=[])
            self._words[n]=word
        data.update(schema='noema-visible-two-force-wordings-visible-profile-1',edition=73)
        data['naming_convention']+='\n'+manifest()['naming_convention'];self._document=data
        self._primitives=deepcopy(data['primitives']);self._symbols={n:symbol(w,self) for n,w in self._words.items()}
        require(len(set(self._symbols.values()))==len(self._words),'Profile spelling collision')
        self._by_symbol={s:n for n,s in self._symbols.items()};self._order=self._topological()
        normalize_document(dict(schema_version='0.16',lexicon_version='0.16',declarations=[self._plain_declaration(n) for n in self._order],statements=[]))
        for field in ('entries','compounds','definitions','primitives'):
            require(all(data[field].get(n)==d for n,d in parent[field].items()),'Previous profile changed')
