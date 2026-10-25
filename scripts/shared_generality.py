"""Explicit normal cases and qualitative degrees, with no new primitives."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.constructed_discourse import normalize_document,function_sort
from scripts.shared_modality import ROOT,v,app,call,op,renamed
from scripts.shared_reference import I,S,T,definition
from scripts.shared_time import q,allof

LIBRARY='examples/v016/shared-generality-v1.noema'
BASIS='data/shared-generality-basis-v1.json'
SOURCES=[dict(document='examples/v016/conjoined-kinds.noema',basis='data/conjoined-kinds-basis-v1.json',
    names={'r2be':'normalcase','r2bf':'normalorder','r2bg':'casegeneric','r2fa':'kindwisegeneric'}),
    dict(document='examples/v016/graded-modality.noema',basis='data/graded-modality-basis-v1.json',
    names={'rqsq':'boundedscale','rqsr':'modaldegree','rqss':'neartop','rqst':'modalmore',
           'rqsu':'conditionednear','rqsv':'comparedconditionednear'})]
GROUP=function_sort([I],T);ORDER=function_sort([I,I],T);ASSIGN=function_sort([I],I)
SCALE=[('scale',GROUP),('less',ORDER)]
STANDARD=SCALE+[('positive',GROUP),('negative',GROUP)]
SUBJECT=[('subject',I),('assignment',ASSIGN)]
PAIR=[('left',I),('right',I),('assignment',ASSIGN)]+SCALE


def args(ps):return [v(n) for n,t in ps]
def equal(a,b):return op('equal',a,b)
def at(name,*xs):return app(name,*(v(x) for x in xs))


@lru_cache(maxsize=1)
def raw():
    ds=[]
    for source in SOURCES:
        old=parse((ROOT/source['document']).read_text(encoding='utf-8'))
        ds.extend(renamed(d,source['names']) for d in old['declarations'] if d['name'] in source['names'])
    def add(n,ps,body):ds.append(definition(n,ps,T,body))
    add('caseuniversal',[('cases',GROUP),('response',GROUP)],
        q('forall','item',I,op('implies',at('cases','item'),at('response','item'))))
    add('caseexception',[('item',I),('cases',GROUP),('response',GROUP)],
        op('and',at('cases','item'),op('not',at('response','item'))))
    irrefl=q('forall','x',I,op('implies',at('scale','x'),op('not',at('less','x','x'))))
    total=q('forall','x',I,q('forall','y',I,op('implies',op('and',at('scale','x'),at('scale','y')),
        op('or',equal(v('x'),v('y')),op('or',at('less','x','y'),at('less','y','x'))))))
    trans=q('forall','x',I,q('forall','y',I,q('forall','z',I,op('implies',
        allof(at('scale','x'),at('scale','y'),at('scale','z'),at('less','x','y'),at('less','y','z')),at('less','x','z')))))
    add('scaleordered',SCALE,allof(q('exists','x',I,at('scale','x')),irrefl,total,trans))
    for name,increase in [('uppercriterion',True),('lowercriterion',False)]:
        contained=q('forall','x',I,op('implies',at('criterion','x'),at('scale','x')))
        upwards=at('less','x','y') if increase else at('less','y','x')
        closed=q('forall','x',I,q('forall','y',I,op('implies',
            allof(at('criterion','x'),at('scale','y'),upwards),at('criterion','y'))))
        add(name,SCALE+[('criterion',GROUP)],op('and',contained,closed))
    disjoint=q('forall','x',I,op('not',op('and',at('positive','x'),at('negative','x'))))
    add('standardsvalid',STANDARD,allof(call('scaleordered',*args(SCALE)),
        call('uppercriterion',*args(SCALE),v('positive')),call('lowercriterion',*args(SCALE),v('negative')),disjoint))
    degree=at('assignment','subject')
    for name,classification in [('degreepositive',app('positive',degree)),('degreenegative',app('negative',degree)),
        ('degreeborderline',op('and',op('not',app('positive',degree)),op('not',app('negative',degree))))]:
        add(name,SUBJECT+STANDARD,allof(call('standardsvalid',*args(STANDARD)),app('scale',degree),classification))
    left=at('assignment','left');right=at('assignment','right')
    for name,relation in [('degreemore',app('less',right,left)),('degreeequal',equal(left,right)),
        ('degreenotless',op('or',equal(left,right),app('less',right,left)))]:
        add(name,PAIR,allof(call('scaleordered',*args(SCALE)),app('scale',left),app('scale',right),relation))
    add('degreeenough',SUBJECT+SCALE+[('criterion',GROUP)],allof(call('scaleordered',*args(SCALE)),
        call('uppercriterion',*args(SCALE),v('criterion')),app('scale',degree),app('criterion',degree)))
    return dict(schema_version='0.16',lexicon_version='0.16',declarations=ds,statements=[])


@lru_cache(maxsize=1)
def composed():return normalize_document(raw())


OLD_ROLES={
 'normalcase':['item','cases','preferred'],'normalorder':['cases','preferred'],
 'casegeneric':['cases','preferred','response'],'kindwisegeneric':['firstcases','secondcases','preferred','response'],
 'boundedscale':['scale','less','low','high'],'modaldegree':['situations','goal','scale','degree','low','high'],
 'neartop':['scale','less','near','low','high'],
 'modalmore':['situations','firstgoal','secondgoal','scale','less','low','high','firstdegree','seconddegree'],
 'conditionednear':['situations','condition','goal','scale','less','near','low','high','degree'],
 'comparedconditionednear':['situations','condition','firstgoal','secondgoal','scale','less','near','low','high','firstdegree','seconddegree','conditioneddegree']}
MEANINGS={
 'caseuniversal':'指定された事例すべてで応答が成立する。空範囲では真になる全称であり、非空の通常事例を要求する総称と区別する。',
 'caseexception':'同じ事例が指定範囲に属し、指定応答を満たさない。通常性の順位や総称の成立は別に調べる。',
 'scaleordered':'非空の尺度範囲に、非反射的・推移的で相異なる二値を比較できる厳密全順序がある。数値・距離・両端の存在は要求しない。',
 'uppercriterion':'受理する値は尺度内にあり、それより高い尺度値も受理する。空範囲・全範囲も許す。順序の妥当性は別条件。',
 'lowercriterion':'受理する値は尺度内にあり、それより低い尺度値も受理する。空範囲・全範囲も許す。順序の妥当性は別条件。',
 'standardsvalid':'尺度の厳密全順序と、上方に閉じた肯定域・下方に閉じた否定域を要求し、両域の重なりを拒否する。両方の外にある値を許す。',
 'degreepositive':'妥当な同じ尺度・判定基準で、対象の割当値が尺度内の明確な肯定域にある。',
 'degreenegative':'妥当な同じ尺度・判定基準で、対象の割当値が尺度内の明確な否定域にある。肯定域への所属の単なる否定ではない。',
 'degreeborderline':'妥当な同じ尺度・判定基準で、対象の既知の割当値が尺度内にあり、肯定域と否定域のどちらにも入らない。入力の未判明ではない。',
 'degreemore':'同じ妥当な尺度と割当で、左対象の尺度値が右対象より厳密に高い。左対象が肯定域にあることは要求しない。',
 'degreeequal':'同じ妥当な尺度と割当で、両対象の尺度値が同一である。対象個体の同一性や、別尺度での同値性は要求しない。',
 'degreenotless':'同じ妥当な尺度と割当で、左対象の尺度値が右対象と同じか、それより高い。',
 'degreeenough':'同じ妥当な尺度で対象の割当値が、明示された上方に閉じた目的基準を満たす。形容詞の肯定域とは別の基準で、目的の実現や基準の適切さは導かない。'}
ROLES={
 'item':'分類・通常性・応答を同じ位置へ結ぶ個体事例。仮定の事例でもよい。',
 'cases':'総称または全称の比較事例の範囲。応答の成功だけから選ばない。',
 'firstcases':'第一の種類の比較範囲。','secondcases':'第二の種類の比較範囲。第一と重なってよい。',
 'preferred':'第一事例が第二事例より通常である厳密な優先関係。結果や件数から自動設定しない。',
 'response':'同じ事例について判断する応答・性質。未知入力は偽にしない。',
 'scale':'今回の比較で同じ意味に固定した質的尺度値の範囲。',
 'less':'第一の尺度値が第二より厳密に低い関係。通常性の優先と向きを取り違えない。',
 'positive':'文脈と比較対象の範囲を固定した、明確な肯定の尺度値。',
 'negative':'同じ文脈で明確な否定の尺度値。肯定の補集合で代用しない。',
 'criterion':'対象の目的・用途を固定した尺度値の受理範囲。数値閾値を自動補完しない。',
 'subject':'程度を判定する対象。','assignment':'対象から同じ尺度の値への明示的な割当。未測定は既定値で補わない。',
 'left':'比較の左対象。','right':'比較の右対象。',
 'situations':'様相の内容を評価する候補状況の範囲。','goal':'同じ候補で評価する内容の真偽。',
 'firstgoal':'比較する第一の内容。','secondgoal':'比較する第二の内容。','condition':'候補状況を制限する条件。',
 'low':'様相尺度の最低値。不可能に対応する。','high':'様相尺度の最高値。必然に対応する。',
 'degree':'対象内容に割り当てた尺度値。','firstdegree':'第一内容の尺度値。','seconddegree':'第二内容の尺度値。',
 'conditioneddegree':'条件で制限した候補内での第一内容の尺度値。','near':'最高値の手前で近いと解釈する範囲。距離を順序から推定しない。'}


def basis():
    meanings={}
    for source in SOURCES:
        old=json.loads((ROOT/source['basis']).read_text(encoding='utf-8'))
        meanings.update({new:old['definitions'][name] for name,new in source['names'].items()})
    meanings.update(MEANINGS);contracts={}
    for d in raw()['declarations']:
        roles=OLD_ROLES.get(d['name'],[p['name'] for p in d['parameters']])
        contracts[d['name']]=dict(arguments=[dict(role=n,sort=p['sort'],interpretation=ROLES[n]) for n,p in zip(roles,d['parameters'])],result=d['result'])
    return dict(status='shared_normal_cases_and_qualitative_degrees',document=LIBRARY,primitives={},definitions=meanings,
        public_contracts=contracts,preserved_definitions=SOURCES,
        limitations=['通常事例による総称は既存r2be/r2bf/r2bg/r2faの明示的な読みを共有する。全ての総称文の唯一の意味や、現在の実例の全称・多数決ではない。',
            '範囲と通常性の経験的根拠は入力規約。結論から都合よく選ぶことを形式的な順位検査で正当化しない。各種類の通常事例を別々に検査する。',
            '通常性の半順序と程度の全順序を区別。程度の距離・確率・普遍的な閾値は導かない。文脈・比較集団・目的を変える場合は関数の解釈を明示する。',
            '境界は既知の割当値が既知の二つの判定域に属さないこと。未知の割当・尺度・基準は拒否し、境界や否定へ変換しない。これは古典真偽上の明示的な境界分類で、一般的な多値論理ではない。',
            '妥当な判定域は互いに排他的だが、空や全体も許す。不正な尺度や重なる域では各判定は偽になり、妥当性の失敗と対象の否定を区別する。',
            '上方に閉じた目的基準を満たすことと、実際に目的を達成することを区別。両端を持つ様相尺度の6定義は旧本文を保持し、一般の程度に両端を強制しない。',
            '有限モデルと束縛診断は無限領域の証明ではない。円文字辞書接続、別領域への学習・第三者読解は続く課題。'])


def prepare():
    for path,text in ((LIBRARY,format_graph(composed())+'\n'),(BASIS,json.dumps(basis(),ensure_ascii=False,indent=2)+'\n')):
        target=ROOT/path
        if target.exists() and target.read_text(encoding='utf-8')!=text:raise ValueError('Published generality differs: '+path)
        if not target.exists():target.write_text(text,encoding='utf-8',newline='\n')


if __name__=='__main__':prepare()
