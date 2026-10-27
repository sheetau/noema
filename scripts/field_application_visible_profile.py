"""Optional electromagnetic-process descriptions and event membership."""
from copy import deepcopy
import json
from noema.constructed import parse,format_graph
from noema.constructed_discourse import normalize_document,function_sort,description_sort
from noema.constructed_semantics import FunctionValue,DescriptionValue
from scripts.vacuum_assumption_visible_profile import ROOT,VacuumAssumptionVisibleVocabulary,write_once,CUT
from scripts.field_application_visible_profile_contracts import CONTRACTS,SOURCE_RELATIONS
from scripts.visible_word_forms import Word,canonical,symbol
from scripts.visible_lexical_script import require

LIBRARY='examples/v016/field-application-visible-profile-v1.noema'
BASIS='data/field-application-visible-profile-basis-v1.json'
MANIFEST='noema/resources/visible-field-application-visible-profile-v1.json'
ALL_CONTRACTS=CONTRACTS
PARAMETERS={n:r['parameters'] for n,r in ALL_CONTRACTS.items()}
PARTS=('home','above','give','inside','aki','nao','book','round')
SPELLINGS={'electromagneticprocessdescription': ['above',
                                       'round',
                                       'treeone',
                                       'home',
                                       'nao',
                                       'book',
                                       'birdone',
                                       'rain',
                                       'rain'],
 'processfielddescription': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'rain', 'town'],
 'processeventmembership': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'rain', 'home']}
CONTEXT=['同じ過程・系・二場・領域を物理的な記述へ結ぶ。',
 '所属関係は同じ過程の全出来事を指定し、変換の成功例だけへ狭めない。',
 '電荷輸送・電気側・磁気側の規約は閉じた型付き記述として参照する。']
LIMITS=['固定アルファベットと共通375語を維持し、採用済み3規約を任意profile68へ公開する。',
 '数値が同じ無関係な過程・場・領域を取り替えず、仮定上の設定を実験済みへ変えない。',
 '光だけへ限定せず、三種類の作用が全て同時に起こることを要求しない。',
 '出来事の所属から座標記録、変換の成功、場の法則を導かない。未知の所属を偽と補わない。',
 '引用した規約の識別は規約の実行や真理の認定とは別である。',
 '全実数・全関数域の条件を保持し、有限診断を全領域の証明としない。']



def library():
    return dict(schema_version='0.16',lexicon_version='0.16',declarations=[
        dict(kind='primitive',name=n,parameters=r['parameters'],result=r['result']) for n,r in ALL_CONTRACTS.items()],statements=[])


def basis():
    return dict(status='optional_field_application_visible_profile',document=LIBRARY,definitions={},primitives=ALL_CONTRACTS,
        public_contracts={n:dict(arguments=[dict(role=a,sort=s) for a,s in zip(r['arguments'],r['parameters'],strict=True)],
            result=r['result'],interpretation_inputs=CONTEXT) for n,r in ALL_CONTRACTS.items()},
        source_relations=SOURCE_RELATIONS,limitations=LIMITS)


def manifest():
    return dict(schema='noema-visible-optional-profile-1',edition=68,parent_profile=67,core_edition=12,
        library=LIBRARY,basis=BASIS,spellings=SPELLINGS,
        naming_convention='above/round/treeone/home/nao/book/birdone/rainを電磁過程の記述・二場による記述・全所属出来事の語群とする。後続要素は公開規約を区別する綴りであり、語義番号ではない。過程・系・場・領域・出来事・文脈は本文で合成する。')


def prepare():
    write_once(LIBRARY,format_graph(library())+'\n');write_once(BASIS,basis());write_once(MANIFEST,manifest())


class FieldApplicationVisibleVocabulary(VacuumAssumptionVisibleVocabulary):
    def __init__(self):
        super().__init__();data=self.document();parent=deepcopy(data)
        require(json.loads((ROOT/MANIFEST).read_text(encoding='utf-8'))==manifest(),'FieldApplication-visible profile changed')
        require(parse((ROOT/LIBRARY).read_text(encoding='utf-8'))==library(),'FieldApplication-visible declarations changed')
        require(json.loads((ROOT/BASIS).read_text(encoding='utf-8'))==basis(),'FieldApplication-visible meanings changed')
        for d in library()['declarations']:
            n=d['name'];r=ALL_CONTRACTS[n];require(n not in self._words,'Profile name collision')
            word=canonical(Word('compound',tuple(SPELLINGS[n])),self)
            data['primitives'][n]=d;data['compounds'][n]=dict(parts=list(word.parts),parameters=d['parameters'],result=d['result'],
                roles=r['arguments'],meaning=r['meaning_ja'],context=CONTEXT,contrast=LIMITS,aliases=[])
            self._words[n]=word
        data.update(schema='noema-visible-field-application-visible-profile-1',edition=68)
        data['naming_convention']+='\n'+manifest()['naming_convention'];self._document=data
        self._primitives=deepcopy(data['primitives']);self._symbols={n:symbol(w,self) for n,w in self._words.items()}
        require(len(set(self._symbols.values()))==len(self._words),'Profile spelling collision')
        self._by_symbol={s:n for n,s in self._symbols.items()};self._order=self._topological()
        normalize_document(dict(schema_version='0.16',lexicon_version='0.16',declarations=[self._plain_declaration(n) for n in self._order],statements=[]))
        for field in ('entries','compounds','definitions','primitives'):
            require(all(data[field].get(n)==d for n,d in parent[field].items()),'Previous profile changed')
