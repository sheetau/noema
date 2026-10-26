"""Optional empirical speed and time-convention relations."""
from copy import deepcopy
import json
from noema.constructed import parse,format_graph
from noema.constructed_discourse import normalize_document,function_sort,description_sort
from noema.constructed_semantics import FunctionValue,DescriptionValue
from scripts.synchrony_profile import ROOT,SynchronyVocabulary,write_once
from scripts.text_reference_profile import TextPresentation
from scripts.visible_word_forms import Word,canonical,symbol
from scripts.visible_lexical_script import require
from scripts.light_speed_time_contracts import CONTRACTS,SOURCE_RELATIONS

LIBRARY='examples/v016/light-speed-time-profile-v1.noema'
BASIS='data/light-speed-time-profile-basis-v1.json'
MANIFEST='noema/resources/visible-light-speed-time-profile-v1.json'
I='individual';S='situation';N='number';T='truth'
CUT=function_sort([N],T);ROLE=function_sort([CUT,S],T)
EXTRA={'describedcutreference':dict(parameters=[I,I,description_sort(ROLE),S],result=CUT,
    arguments=['document','node','role_description','context'],meaning_ja='同じ文書・箇所・提示文脈で、閉じた役割関係の記述に結び付けて照合する切断型の値への参照。役割の定義は本文に示す。参照を与えることから役割の成立、実数としての妥当性、実測済み、値の唯一性を導かず、引用した役割を実行しない。数値を補わず、未知の参照を拒否する。')}
REUSED=set()
ALL_CONTRACTS={n:r for n,r in CONTRACTS.items() if n not in REUSED}|EXTRA
PARAMETERS={n:r['parameters'] for n,r in ALL_CONTRACTS.items()}
PARTS=('home','above','give','inside','aki','nao','book','round')
SPELLINGS={name:['above','book','fly',PARTS[i//8],PARTS[i%8]] for i,name in enumerate(ALL_CONTRACTS)}
CONTEXT=['同じ課題・方式・対象・文書・文脈を保持する。見かけ、可能性、採用、実施を区別する。']
LIMITS=['共通375語は不変。旧関係の型・役割・意味を任意プロファイルとして公開する。',
        '記録の成分位置は公開されたデータの欄であり語義番号ではない。未知の値を既定値で補わない。',
        '参照・引用・前方指示はその内容の真理や実験済みを意味しない。有限診断を全実数の証明としない。']


def library():
    return dict(schema_version='0.16',lexicon_version='0.16',declarations=[
        dict(kind='primitive',name=n,parameters=r['parameters'],result=r['result']) for n,r in ALL_CONTRACTS.items()],statements=[])


def basis():
    return dict(status='optional_light_speed_time_profile',document=LIBRARY,definitions={},primitives=ALL_CONTRACTS,
        public_contracts={n:dict(arguments=[dict(role=a,sort=s) for a,s in zip(r['arguments'],r['parameters'],strict=True)],
            result=r['result'],interpretation_inputs=CONTEXT) for n,r in ALL_CONTRACTS.items()},
        source_relations=SOURCE_RELATIONS,limitations=LIMITS)


def manifest():
    return dict(schema='noema-visible-optional-profile-1',edition=25,parent_profile=24,core_edition=12,
        library=LIBRARY,basis=BASIS,spellings=SPELLINGS,
        naming_convention='above/book/flyを光速度と時間規約の語群とする。後続の二要素は公開規約で区別する綴りであり、文中に数値の語義表を置かない。役割と数学は本文定義として示す。')


def prepare():
    write_once(LIBRARY,format_graph(library())+'\n');write_once(BASIS,basis());write_once(MANIFEST,manifest())


class LightSpeedTimeVocabulary(SynchronyVocabulary):
    def __init__(self):
        super().__init__();data=self.document();parent=deepcopy(data)
        for name in REUSED:
            row=data['compounds'][name];r=CONTRACTS[name]
            require((row['parameters'],row['result'],row['roles'],row['meaning'])==
                    (r['parameters'],r['result'],r['arguments'],r['meaning_ja']),'Reused contract differs')
        require(json.loads((ROOT/MANIFEST).read_text(encoding='utf-8'))==manifest(),'Light-speed-time profile changed')
        require(parse((ROOT/LIBRARY).read_text(encoding='utf-8'))==library(),'Light-speed-time declarations changed')
        require(json.loads((ROOT/BASIS).read_text(encoding='utf-8'))==basis(),'Light-speed-time meanings changed')
        for d in library()['declarations']:
            n=d['name'];r=ALL_CONTRACTS[n];require(n not in self._words,'Profile name collision')
            word=canonical(Word('compound',tuple(SPELLINGS[n])),self)
            data['primitives'][n]=d;data['compounds'][n]=dict(parts=list(word.parts),parameters=d['parameters'],result=d['result'],
                roles=r['arguments'],meaning=r['meaning_ja'],context=CONTEXT,contrast=LIMITS,aliases=[])
            self._words[n]=word
        data.update(schema='noema-visible-light-speed-time-profile-1',edition=25)
        data['naming_convention']+='\n'+manifest()['naming_convention'];self._document=data
        self._primitives=deepcopy(data['primitives']);self._symbols={n:symbol(w,self) for n,w in self._words.items()}
        require(len(set(self._symbols.values()))==len(self._words),'Profile spelling collision')
        self._by_symbol={s:n for n,s in self._symbols.items()};self._order=self._topological()
        normalize_document(dict(schema_version='0.16',lexicon_version='0.16',declarations=[self._plain_declaration(n) for n in self._order],statements=[]))
        for field in ('entries','compounds','definitions','primitives'):
            require(all(data[field].get(n)==d for n,d in parent[field].items()),'Previous profile changed')


class CutReferences:
    """Known cut-shaped values selected by closed roles, never by sampled truth."""
    def __init__(self,roles):
        require(all(isinstance(x,FunctionValue) and x.parameters==('number',) and x.result=='truth'
                    for x in roles.values()),'Expected cut-shaped candidate')
        self.roles=dict(roles)

    def described(self,doc,node,role,context):
        require(isinstance(role,DescriptionValue) and json.loads(role.result_type)==ROLE and role.rank==0,
                'Expected a checked cut role description')
        key=(doc,node,role.syntax,context)
        require(key in self.roles,'Unknown cut reference');return self.roles[key]

    def handlers(self):return dict(describedcutreference=self.described)


class SpeedTrialRecords:
    """Known trial clocks and one-way distance candidates; no physical inference."""
    def __init__(self,rows):
        require(all(isinstance(row,(tuple,list)) and len(row)==3 for row in rows.values()),'Expected two clocks and a distance')
        require(all(isinstance(row[2],FunctionValue) and row[2].parameters==('number',) and row[2].result=='truth'
                    for row in rows.values()),'Expected cut-shaped distance')
        self.rows={trial:tuple(row) for trial,row in rows.items()}

    def field(self,trial,index):
        require(trial in self.rows,'Unknown speed trial');return self.rows[trial][index]

    def handlers(self):return dict(departureclock=lambda t:self.field(t,0),
        reflectionclock=lambda t:self.field(t,1),trialdistance=lambda t:self.field(t,2))
