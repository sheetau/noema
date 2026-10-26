"""Optional temporal discourse, role-based references and shared light-trial records."""
from copy import deepcopy
import json

from noema.constructed import parse,format_graph
from noema.constructed_discourse import normalize_document,function_sort,description_sort
from noema.constructed_semantics import FunctionValue,DescriptionValue
from scripts.physical_position_profile import ROOT,PhysicalPositionVocabulary,write_once
from scripts.text_reference_profile import TextPresentation
from scripts.visible_word_forms import Word,canonical,symbol
from scripts.visible_lexical_script import require
from scripts.temporal_discourse_contracts import CONTRACTS,SOURCE_RELATIONS,FIELD_CONTRACTS

LIBRARY='examples/v016/temporal-discourse-profile-v1.noema'
BASIS='data/temporal-discourse-profile-basis-v1.json'
MANIFEST='noema/resources/visible-temporal-discourse-profile-v1.json'
I='individual';S='situation';N='number';T='truth'
CUT=function_sort([N],T);ROLE=function_sort([I,S],T)
EXTRA={
 'describedreference':dict(parameters=[I,I,description_sort(ROLE),S],result=I,
    arguments=['document','node','role_description','context'],meaning_ja='同じ文書・箇所・提示文脈で、閉じた役割関係の記述に結び付けて照合する対象への参照。役割の定義は本文に示す。参照を与えることから役割関係の現実の成立、対象の現実の存在、世界での唯一性を導かず、引用された役割を実行しない。未知の参照は補わない。'),
 'footnotereference':dict(parameters=[I,I,N,S],result=I,
    arguments=['document','attachment','printed_number','context'],meaning_ja='同じ文書・提示文脈で、指定した本文箇所に付された正の整数の著者脚注番号が指す注本文の箇所への参照。番号の再使用は付着箇所で区別する。編集注や原文一覧での配置を本文順序に置き換えず、参照の取得から脚注対応の成立や注内容の真理を導かない。'),
 'roundtripentity':dict(parameters=[I,N],result=I,arguments=['trial','slot'],
    meaning_ja='同じ光往復試行の個体項目を返す。0は出発側の場所、1は反射側の場所、2は出発出来事、3は反射出来事、4は帰着出来事、5は光信号。項目の物理的整合性や伝播・反射の成立は別条件であり、未知試行・未知項目・範囲外添字を既定値で補わない。'),
 'roundtripreading':dict(parameters=[I,N],result=CUT,arguments=['trial','slot'],
    meaning_ja='同じ光往復試行の時計読みの成分を返す。0は出発時、1は反射時、2は帰着時の実数切断の形を持つ値。有効な実数であること、同じ時計・場所・単位への結合、同期の成立は別条件であり、未知試行・未知項目・範囲外添字を零で補わない。')}
ALL_CONTRACTS=CONTRACTS|EXTRA
PARAMETERS={n:r['parameters'] for n,r in ALL_CONTRACTS.items()}
PARTS=('home','above','give','inside','aki','nao','book','round')
# These are published word spellings, not a runtime numbered vocabulary lookup.
SPELLINGS={name:['above','book','inside',PARTS[i//8],PARTS[i%8]] for i,name in enumerate(ALL_CONTRACTS)}
CONTEXT=['文書・本文箇所・参照対象・系・単位・引用の役割と範囲を保つ。',
         '引用、例示、約言、留保、方法上の要請を真理や実施済みの事実へ置き換えない。']
LIMITS=['公開する関係は旧正本の意味規約を保持する。型の類似だけで別の関係と同一視しない。',
        '光往復の項目添字は固定された物理記録の成分位置であり、語義の番号ではない。',
        '役割の記述による参照は本文の定義と文脈を必要とする。原語の文字列や外部の語義番号で内容を代用しない。',
        '有限診断は全実数・全対象・全状況の証明ではない。未知入力を既定値で埋めない。']


def library():
    return dict(schema_version='0.16',lexicon_version='0.16',declarations=[
        dict(kind='primitive',name=n,parameters=r['parameters'],result=r['result']) for n,r in ALL_CONTRACTS.items()],statements=[])


def basis():
    return dict(status='optional_temporal_discourse_profile',document=LIBRARY,definitions={},primitives=ALL_CONTRACTS,
        public_contracts={n:dict(arguments=[dict(role=a,sort=s) for a,s in zip(r['arguments'],r['parameters'],strict=True)],
            result=r['result'],interpretation_inputs=CONTEXT) for n,r in ALL_CONTRACTS.items()},
        source_relations=SOURCE_RELATIONS,source_trial_fields=FIELD_CONTRACTS,limitations=LIMITS)


def manifest():
    return dict(schema='noema-visible-optional-profile-1',edition=22,parent_profile=21,core_edition=12,
        library=LIBRARY,basis=BASIS,spellings=SPELLINGS,
        naming_convention='above/book/insideを時間とその説明の語群とする。後続の二要素は公開規約で区別する綴りであり、文中に数値の語義表を置かない。役割と数学は本文定義として示す。')


def prepare():
    write_once(LIBRARY,format_graph(library())+'\n');write_once(BASIS,basis());write_once(MANIFEST,manifest())


class TemporalDiscourseVocabulary(PhysicalPositionVocabulary):
    def __init__(self):
        super().__init__();data=self.document();parent=deepcopy(data)
        require(json.loads((ROOT/MANIFEST).read_text(encoding='utf-8'))==manifest(),'Temporal profile changed')
        require(parse((ROOT/LIBRARY).read_text(encoding='utf-8'))==library(),'Temporal declarations changed')
        require(json.loads((ROOT/BASIS).read_text(encoding='utf-8'))==basis(),'Temporal meanings changed')
        for d in library()['declarations']:
            n=d['name'];r=ALL_CONTRACTS[n];require(n not in self._words,'Profile name collision')
            word=canonical(Word('compound',tuple(SPELLINGS[n])),self)
            data['primitives'][n]=d;data['compounds'][n]=dict(parts=list(word.parts),parameters=d['parameters'],result=d['result'],
                roles=r['arguments'],meaning=r['meaning_ja'],context=CONTEXT,contrast=LIMITS,aliases=[])
            self._words[n]=word
        data.update(schema='noema-visible-temporal-discourse-profile-1',edition=22)
        data['naming_convention']+='\n'+manifest()['naming_convention'];self._document=data
        self._primitives=deepcopy(data['primitives']);self._symbols={n:symbol(w,self) for n,w in self._words.items()}
        require(len(set(self._symbols.values()))==len(self._words),'Profile spelling collision')
        self._by_symbol={s:n for n,s in self._symbols.items()};self._order=self._topological()
        normalize_document(dict(schema_version='0.16',lexicon_version='0.16',declarations=[self._plain_declaration(n) for n in self._order],statements=[]))
        for field in ('entries','compounds','definitions','primitives'):
            require(all(data[field].get(n)==d for n,d in parent[field].items()),'Previous profile changed')


class TemporalReferences:
    def __init__(self,roles,notes):
        self.roles=dict(roles);self.notes={(d,node,TextPresentation.coordinate(n),s):value for (d,node,n,s),value in notes.items()}

    @staticmethod
    def known(table,key):
        require(key in table,'Unknown temporal reference');return table[key]

    def described(self,doc,node,role,context):
        require(isinstance(role,DescriptionValue) and json.loads(role.result_type)==ROLE and role.rank==0,'Expected a checked role description')
        return self.known(self.roles,(doc,node,role.syntax,context))

    def footnote(self,doc,node,number,context):
        return self.known(self.notes,(doc,node,TextPresentation.coordinate(number),context))

    def handlers(self):return dict(describedreference=self.described,footnotereference=self.footnote)


class LightTrialRecords:
    def __init__(self,entities,readings):
        self.entities={};self.readings={}
        for key,values in entities.items():
            require(isinstance(values,(tuple,list)) and len(values)==6,'Expected six light-trial entities');self.entities[key]=tuple(values)
        for key,values in readings.items():
            require(isinstance(values,(tuple,list)) and len(values)==3,'Expected three light-trial readings')
            require(all(isinstance(x,FunctionValue) and x.parameters==('number',) and x.result=='truth' for x in values),'Expected cut-shaped readings')
            self.readings[key]=tuple(values)

    @staticmethod
    def component(table,trial,slot,size):
        from fractions import Fraction
        require(type(slot) in (int,Fraction),'Trial slot must be an exact integer')
        slot=Fraction(slot);require(slot.denominator==1 and 0<=slot<size,'Unknown trial slot')
        require(trial in table,'Unknown light trial');return table[trial][int(slot)]

    def handlers(self):return dict(roundtripentity=lambda t,n:self.component(self.entities,t,n,6),
        roundtripreading=lambda t,n:self.component(self.readings,t,n,3))
