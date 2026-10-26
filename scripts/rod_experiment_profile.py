"""Optional rod measurement, imagined settings and trajectory inputs."""
from copy import deepcopy
import json
from noema.constructed import parse,format_graph
from noema.constructed_discourse import normalize_document,function_sort,description_sort
from noema.constructed_semantics import FunctionValue,DescriptionValue
from scripts.two_principles_profile import ROOT,TwoPrinciplesVocabulary,write_once,CUT
from scripts.text_reference_profile import TextPresentation
from scripts.visible_word_forms import Word,canonical,symbol
from scripts.visible_lexical_script import require
from scripts.rod_experiment_contracts import CONTRACTS,SOURCE_RELATIONS

LIBRARY='examples/v016/rod-experiment-profile-v1.noema'
BASIS='data/rod-experiment-profile-basis-v1.json'
MANIFEST='noema/resources/visible-rod-experiment-profile-v1.json'
I='individual';S='situation';N='number';T='truth'
SETTING_ROLE=function_sort([S,S],T)
TRAJECTORY=function_sort([CUT],CUT)
EXTRA={
 'describedsettingreference':dict(parameters=[I,I,description_sort(SETTING_ROLE),S],result=S,
    arguments=['document','node','role_description','context'],
    meaning_ja='同じ文書・箇所・提示文脈で、本文に示した閉じた役割関係の記述に結び付けて照合する設定への参照。仮定的な設定も扱う。役割は候補設定と提示文脈を受け取る。取得から役割の真理、物理的実在、実行、唯一性を導かず、引用した役割を実行しない。未知の参照を既定値で補わない。'),
 'endpointmeasuremententity':dict(parameters=[I,I,S,N],result=I,arguments=['body','frame','setting','slot'],
    meaning_ja='同じ物体・評価系・測定設定に結ばれた二端点測定の記録から個体候補を取得する。欄0/1は二端点、2/3は各端点の位置を評価する出来事、4/5は各出来事に対応する局所時計、6/7は各出来事の場所。対応する側を全欄で保つ。欄は公開記録の成分位置であり語義番号ではない。時計の静止・同期、同時刻、物理的帰属や測定完了は別の合成条件で指定する。未知の記録や欄を補わない。'),
 'endpointmeasurementreading':dict(parameters=[I,I,S,N],result=CUT,arguments=['body','frame','setting','slot'],
    meaning_ja='同じ物体・評価系・測定設定の二端点測定記録から切断型の数値候補を取得する。欄0/1は二つの局所時計の対応する出来事時点の読み、欄2は両端を評価する指定時刻。時計と場所は同じ個体記録へ対応させる。実数妥当性・同期・三値の一致・実測の成立は別に指定し、取得から導かない。未知の記録や欄を補わない。')}
REUSED={'introducesreferent'}
# The earlier source calls the fourth situation role "reference"; profile 19
# names the same presentation context "context". Types and meaning are exact.
REUSED_ARGUMENTS={'introducesreferent':['node','referent','document','context']}
ALL_CONTRACTS={n:r for n,r in CONTRACTS.items() if n not in REUSED}|EXTRA
PARAMETERS={n:r['parameters'] for n,r in ALL_CONTRACTS.items()}
PARTS=('home','above','give','inside','aki','nao','book','round')
SPELLINGS={name:['above','book','home',PARTS[i//8],PARTS[i%8]] for i,name in enumerate(ALL_CONTRACTS)}
CONTEXT=['同じ課題・方式・対象・文書・文脈を保持する。見かけ、可能性、採用、実施を区別する。']
LIMITS=['共通375語は不変。旧関係の型・役割・意味を任意プロファイルとして公開する。',
        '記録の成分位置は公開されたデータの欄であり語義番号ではない。未知の値を既定値で補わない。',
        '参照・引用・前方指示はその内容の真理や実験済みを意味しない。有限診断を全実数の証明としない。']


def library():
    return dict(schema_version='0.16',lexicon_version='0.16',declarations=[
        dict(kind='primitive',name=n,parameters=r['parameters'],result=r['result']) for n,r in ALL_CONTRACTS.items()],statements=[])


def basis():
    return dict(status='optional_rod_experiment_profile',document=LIBRARY,definitions={},primitives=ALL_CONTRACTS,
        public_contracts={n:dict(arguments=[dict(role=a,sort=s) for a,s in zip(r['arguments'],r['parameters'],strict=True)],
            result=r['result'],interpretation_inputs=CONTEXT) for n,r in ALL_CONTRACTS.items()},
        source_relations=SOURCE_RELATIONS,limitations=LIMITS)


def manifest():
    return dict(schema='noema-visible-optional-profile-1',edition=27,parent_profile=26,core_edition=12,
        library=LIBRARY,basis=BASIS,spellings=SPELLINGS,
        naming_convention='above/book/homeを棒の測定と想定設定の語群とする。後続の二要素は公開規約で区別する綴りであり、文中に数値の語義表を置かない。役割と数学は本文定義として示す。')


def prepare():
    write_once(LIBRARY,format_graph(library())+'\n');write_once(BASIS,basis());write_once(MANIFEST,manifest())


class RodExperimentVocabulary(TwoPrinciplesVocabulary):
    def __init__(self):
        super().__init__();data=self.document();parent=deepcopy(data)
        for name in REUSED:
            row=data['compounds'][name];r=CONTRACTS[name]
            require((row['parameters'],row['result'],row['roles'],row['meaning'])==
                    (r['parameters'],r['result'],REUSED_ARGUMENTS[name],r['meaning_ja']),'Reused contract differs')
            require(r['arguments']==['node','referent','document','reference'],'Reused source role labels changed')
        require(json.loads((ROOT/MANIFEST).read_text(encoding='utf-8'))==manifest(),'Rod-experiment profile changed')
        require(parse((ROOT/LIBRARY).read_text(encoding='utf-8'))==library(),'Rod-experiment declarations changed')
        require(json.loads((ROOT/BASIS).read_text(encoding='utf-8'))==basis(),'Rod-experiment meanings changed')
        for d in library()['declarations']:
            n=d['name'];r=ALL_CONTRACTS[n];require(n not in self._words,'Profile name collision')
            word=canonical(Word('compound',tuple(SPELLINGS[n])),self)
            data['primitives'][n]=d;data['compounds'][n]=dict(parts=list(word.parts),parameters=d['parameters'],result=d['result'],
                roles=r['arguments'],meaning=r['meaning_ja'],context=CONTEXT,contrast=LIMITS,aliases=[])
            self._words[n]=word
        data.update(schema='noema-visible-rod-experiment-profile-1',edition=27)
        data['naming_convention']+='\n'+manifest()['naming_convention'];self._document=data
        self._primitives=deepcopy(data['primitives']);self._symbols={n:symbol(w,self) for n,w in self._words.items()}
        require(len(set(self._symbols.values()))==len(self._words),'Profile spelling collision')
        self._by_symbol={s:n for n,s in self._symbols.items()};self._order=self._topological()
        normalize_document(dict(schema_version='0.16',lexicon_version='0.16',declarations=[self._plain_declaration(n) for n in self._order],statements=[]))
        for field in ('entries','compounds','definitions','primitives'):
            require(all(data[field].get(n)==d for n,d in parent[field].items()),'Previous profile changed')


class SettingReferences:
    def __init__(self,roles):self.roles=dict(roles)

    def described(self,doc,node,role,context):
        require(isinstance(role,DescriptionValue) and json.loads(role.result_type)==SETTING_ROLE and role.rank==0,
                'Expected a checked setting role description')
        key=(doc,node,role.syntax,context)
        require(key in self.roles,'Unknown setting reference');return self.roles[key]

    def handlers(self):return dict(describedsettingreference=self.described)


class RodExperimentRecords:
    def __init__(self,*,entities=None,readings=None,intervals=None,endmarks=None,trajectories=None):
        from scripts.synchrony_profile import SynchronyRecords
        self.entities=SynchronyRecords.rows(entities or {},8)
        self.readings=SynchronyRecords.rows(readings or {},3)
        self.intervals=SynchronyRecords.rows(intervals or {},2)
        for row in (*self.readings.values(),*self.intervals.values()):SynchronyRecords.cuts(dict(enumerate(row)))
        self.endmarks=SynchronyRecords.rows(endmarks or {},2)
        require(all(isinstance(f,FunctionValue) and f.parameters==(I,) and f.result==TRAJECTORY
                    for f in (trajectories or {}).values()),'Expected point trajectory family')
        self.trajectories=dict(trajectories or {})

    @staticmethod
    def known(table,key):
        require(key in table,'Unknown rod record');return table[key]

    @classmethod
    def component(cls,table,key,slot,size):
        from fractions import Fraction
        require(type(slot) in (int,Fraction),'Expected exact rod slot')
        slot=Fraction(slot);require(slot.denominator==1 and 0<=slot<size,'Unknown rod slot')
        return cls.known(table,key)[int(slot)]

    def handlers(self):return dict(
        endpointmeasuremententity=lambda b,f,s,n:self.component(self.entities,(b,f,s),n,8),
        endpointmeasurementreading=lambda b,f,s,n:self.component(self.readings,(b,f,s),n,3),
        intervalstart=lambda f,u,s:self.known(self.intervals,(f,u,s))[0],
        intervalend=lambda f,u,s:self.known(self.intervals,(f,u,s))[1],
        firstendmark=lambda b,f,s:self.known(self.endmarks,(b,f,s))[0],
        lastendmark=lambda b,f,s:self.known(self.endmarks,(b,f,s))[1],
        pointtrajectoryfamily=lambda b,f,l,t,a,s:self.known(self.trajectories,(b,f,l,t,a,s)))
