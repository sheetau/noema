"""Optional physical measurement relations; mathematics remains inline definitions."""
from copy import deepcopy
from fractions import Fraction
import json

from noema.constructed import parse,format_graph
from noema.constructed_discourse import normalize_document
from noema.constructed_semantics import FunctionValue
from scripts.designation_purpose_profile import ROOT,DesignationPurposeVocabulary,write_once
from scripts.visible_word_forms import Word,canonical,symbol
from scripts.visible_lexical_script import require
from scripts.physical_position_contracts import CONTRACTS

LIBRARY='examples/v016/physical-position-profile-v1.noema'
BASIS='data/physical-position-profile-basis-v1.json'
MANIFEST='noema/resources/visible-physical-position-profile-v1.json'
SOURCE_RELATIONS=dict(eirh='materialmember',eisdd='cartesianmetric',eisee='restinterval',eisef='calibratedruler',
    eiseg='positionrecord',eiseh='positioncomponent',eisei='rulerconstruction',eisej='usedruler',
    eisek='permittedmeasurement',zm='geometricbody',zzbu='eventcoordinates',zzbv='objectevent')
PARAMETERS={n:row['parameters'] for n,row in CONTRACTS.items()}
SPELLINGS={n:['town','book','inside',part] for n,part in zip(PARAMETERS,
    ['aki','round','above','give','book','inside','home','treeone','assessmentvalid','town','rain','bird'],strict=True)}
CONTEXT=['同じ対象・系・尺度・全期間・方法・結果をそれぞれの引数で保つ。',
         '数値だけで対象の同一性を補わず、可能な実施状況と参照状況を区別する。']
LIMITS=['関係は旧正本の公開意味規約を保つ物理的入力である。名前だけで条件の成立を補わない。',
        '幾何記録の18成分は数値の位置であり、語義を引く番号ではない。未知の成分や記録を零で補わない。',
        '実数切断・全期間の量化を有限標本に置き換えない。有限の束縛診断と全域の証明を区別する。']


def library():
    return dict(schema_version='0.16',lexicon_version='0.16',declarations=[
        dict(kind='primitive',name=n,parameters=r['parameters'],result=r['result']) for n,r in CONTRACTS.items()],statements=[])


def basis():
    return dict(status='optional_physical_position_profile',document=LIBRARY,definitions={},primitives=CONTRACTS,
        public_contracts={n:dict(arguments=[dict(role=a,sort=s) for a,s in zip(r['arguments'],r['parameters'],strict=True)],
            result=r['result'],interpretation_inputs=CONTEXT) for n,r in CONTRACTS.items()},
        source_relations=SOURCE_RELATIONS,limitations=LIMITS)


def manifest():
    return dict(schema='noema-visible-optional-profile-1',edition=21,parent_profile=20,core_edition=12,
        library=LIBRARY,basis=BASIS,spellings=SPELLINGS,
        naming_convention='town/book/insideを物体と位置測定の語群とする。各関係の意味と役割は公開規約から学ぶ。数学定義は本文に展開し、共通辞書へ追加しない。')


def prepare():
    write_once(LIBRARY,format_graph(library())+'\n');write_once(BASIS,basis());write_once(MANIFEST,manifest())


class PhysicalPositionVocabulary(DesignationPurposeVocabulary):
    def __init__(self):
        super().__init__();data=self.document();parent=deepcopy(data)
        require(json.loads((ROOT/MANIFEST).read_text(encoding='utf-8'))==manifest(),'Physical position profile changed')
        require(parse((ROOT/LIBRARY).read_text(encoding='utf-8'))==library(),'Physical position declarations changed')
        require(json.loads((ROOT/BASIS).read_text(encoding='utf-8'))==basis(),'Physical position meanings changed')
        for d in library()['declarations']:
            n=d['name'];r=CONTRACTS[n];require(n not in self._words,'Profile name collision')
            word=canonical(Word('compound',tuple(SPELLINGS[n])),self)
            data['primitives'][n]=d;data['compounds'][n]=dict(parts=list(word.parts),parameters=d['parameters'],result=d['result'],
                roles=r['arguments'],meaning=r['meaning_ja'],context=CONTEXT,contrast=LIMITS,aliases=[])
            self._words[n]=word
        data.update(schema='noema-visible-physical-position-profile-1',edition=21)
        data['naming_convention']+='\n'+manifest()['naming_convention'];self._document=data
        self._primitives=deepcopy(data['primitives']);self._symbols={n:symbol(w,self) for n,w in self._words.items()}
        require(len(set(self._symbols.values()))==len(self._words),'Profile spelling collision')
        self._by_symbol={s:n for n,s in self._symbols.items()};self._order=self._topological()
        normalize_document(dict(schema_version='0.16',lexicon_version='0.16',declarations=[self._plain_declaration(n) for n in self._order],statements=[]))
        for field in ('entries','compounds','definitions','primitives'):
            require(all(data[field].get(n)==d for n,d in parent[field].items()),'Previous profile changed')


class GeometryRecords:
    """Known typed components; validity and physical ownership are separate."""
    def __init__(self,records):
        self.records={}
        for key,values in records.items():
            require(isinstance(values,(tuple,list)) and len(values)==18,'Expected eighteen geometry components')
            require(all(isinstance(v,FunctionValue) and v.parameters==('number',) and v.result=='truth' for v in values),
                    'Expected real-cut-shaped functions')
            self.records[key]=tuple(values)

    def component(self,record,slot):
        require(type(slot) in (int,Fraction),'Geometry slot must be an exact integer')
        slot=Fraction(slot);require(slot.denominator==1 and 0<=slot<18,'Unknown geometry slot')
        require(record in self.records,'Unknown geometry record');return self.records[record][int(slot)]
