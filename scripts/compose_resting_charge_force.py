"""Bind rest and instantaneous rest to the unit test-charge force convention."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_vacuum_field_domain import ROOT,read
from scripts.compose_material_relative_frame import define
from scripts.compose_relativity_conjecture import content
from scripts.compose_two_postulates import quote
from scripts.compose_field_equations import POINT,FIELD,REGION
from scripts.compose_material_velocity import DOMAIN as TIMES,CURVE
from scripts.compose_electric_action import FIELDS
from scripts.compose_moving_field_definition import RESPONSE,FIELD_ARGS
from scripts.compose_rest_force import AXES
from scripts.compose_limits import v,call as k,app,op,both,quant as q

PARENT='examples/v014/einstein-moving-unit-charge.noema';PARENT_BASIS='data/moving-unit-charge-basis-v1.json'
FULL='examples/v014/einstein-resting-charge-force.noema';CORE='examples/v014/resting-charge-force-core.noema'
BASIS='data/resting-charge-force-basis-v1.json';ANNOTATIONS='data/resting-charge-force-identifiers-v1.json'
INDICES=[165,166]
REST=[('carrier','a'),('frame','a'),('event','a'),('point',POINT),('context','d')]
LOCAL=[(n,'a') for n in ('carrier','frame','event','chargerecord','forcerecord','chargeunit','fieldunit','forceunit','lengthunit','timeunit')]+[('point',POINT),('electricfield',FIELD),('magneticfield',FIELD),('region',REGION),('force',POINT),('context','d')]
PRIMITIVES={
 'eisqk':([], '同じ点状電気量zolを、力を評価する出来事zpoで移動系k=zbmにより値1とする結果記録。先行校正の出来事zooの記録zpdと区別し、時間的な電荷保存の定理をこの記録名から導かない。'),
 'eisql':([('node','a'),('author','a'),('definition','i[e]'),('claim','i[e]'),('scope','a'),('context','d')], 'authorがnodeにおいて、scopeで既に用いているdefinitionの規約に従ってclaimを述べるという定義参照の提示。定義の内容とその適用結果は別々の閉じた内容として保持する。新しい定義をここで作ること、経験的な証拠だけを根拠にすること、引用の実行や推論の自動証明とは区別する。対象・単位・条件と結果の合成は引用内容の側で明示し、基本関係へ文全体の物理的な真偽を隠さない。'),
}
MEANINGS={
 'ejwq':'同じ点状担体・系・出来事・四座標・文脈と指定した時間領域・履歴について、seocの三つの座標時刻微分がいずれも0となる。両側の内点と同じ対象の履歴を保ち、加速度0や近傍全体の静止は要求しない。',
 'ejwr':'同じ担体と当該出来事に、ejwqを満たす時間領域と物理的な座標履歴が存在するという瞬間静止。旧zpaや運動の否定だけで静止を認定しない。',
 'ejws':'点状電気量eisqcの同じ評価出来事の位置を明示単位で割り当て、同じ電気量単位の値1、同じ場と力の単位の積の換算1、同じ対象に働く電気的な力の記録をeibsへ結ぶ。力ベクトルを同じ点の電場三成分と同定する。',
 'ejwt':'ejwsの同じ位置・電気量単位・力単位・場単位・換算1を、ejtsによる静止試験電荷の物理的な理想応答へ共有する。その同じ点で量1に対する応答が同じ力の全三成分と一致する。',
 'ejwu':'現在のK=ra、二場znl/znmと領域znk、zolの評価出来事zpo、位置zpj、力zplと記録zpeを同じ単位電気量記録zppへ結ぶ。場単位と理想応答は存在量化し、同じ二証人をejwt全体へ共有する。',
 'ejwv':'現在のk=zbm、二場znr/znsと領域znt、同じzolと評価出来事zpo、位置zpk、力zpmと記録zpfを同じ単位電気量記録eisqkへ結ぶ。Kの座標値や力成分をコピーしない。',
 'ejww':'同じ第一対象zolがKに静止するなら、その系・当該出来事でejwuの物理的な単位電気量と場・力の同定が成立するという第四文。静止を無条件に主張しない。',
 'ejwx':'同じ第一対象zolが当該出来事にkで瞬間静止ejwrするなら、その系・出来事でejwvの同定が成立するという第五文。前後の静止や加速度0を加えない。',
 'ejwy':'Kの現在の電場znlについて、同じ座標尺度ta/rb、量単位zou、力単位Dynで換算1となる場単位と理想応答を持つejtsという、第四文が参照する場の定義内容。特定の実測や真空内の試験体の実在は要求しない。',
 'ejwz':'著者が第四文の静止条件付き同定ejwwを述べ、その根拠の性格を場の定義ejwyへの参照として明示する。同じ(X,Y,Z)の表記を現在のKの場の規則ejs4へ結ぶ。',
 'ejw2':'著者が第五文の瞬間静止条件付き同定ejwxを述べ、(X′,Y′,Z′)を現在のkの場の規則ejtxへ結ぶ。力がkで測られることは結論内容の同じ系・単位・記録に保持する。',
 'ejw3':'第四文の定義による条件付き同定ejwzを述べるメッセージ。',
 'ejw4':'第四文を同じ著者・論説へ帰属し、先の移動系での電気量1の推論に続ける。旧文165を置き換える。',
 'ejw5':'第五文の瞬間静止条件付き同定ejw2を述べるメッセージ。',
 'ejw6':'第五文を同じ著者・論説へ帰属し、第四文に続ける。旧文166を置き換える。',
}
LIMITS=[
 'u0173第四・第五文を、同じ点状の単位電気量を二つの系で扱う条件文として読む。第四文のKへの静止と、第五文の少なくとも当該瞬間のkへの静止を同時に断言しない。',
 '三つの速度成分0は同じ対象の座標時刻微分であり、加速度や前後の速度を0に固定しない。全実数の履歴・微分の存在は有限標本で認定せず、未知の物理的な位置・履歴を静止と補わない。',
 'この電磁場の議論でのKraftは理想的な試験電気量への局所的な作用として読む。電気側の場の既存の静止試験応答を用い、重力や支持力を含む合力へ置き換えない。実際に有限の試験体が元の場を乱さない、真空領域を占有した、実測したという条件は追加しない。',
 '同じ単位電気量という仮定を力の評価出来事zpoでも保つ読みを、Kではzpp、kではeisqkの値1の結果記録へ明示する。先行校正の出来事zooとzpoの同一性も非同一性も断言せず、任意の時間にわたる保存則を証明したとはしない。',
 '場の四座標には現在の尺度ta/rbを使う。先行校正のcm/秒の座標eisqg/hを数値で代入しない。量単位zou、力単位Dyn、場単位の積の換算1を同じ物理的な規約へ結び、単位の異なる値の一致で力と場を同定しない。',
 '場の定義ejtsは全領域・全符号付き試験量に対する理想応答であり、本文の同じ電場znl/znrを使う。真空の方程式全体やLorentz変換の全式をこの局所同定の追加前提にはしない。磁気側の既出場との組は同じznnへ保持する。',
 'definitionsgemäßは既存の場の定義を参照する提示として表す一般関係を一つ追加する。物理的な力・場・単位・瞬間静止は既存の規約と数式から合成し、文全体を一原始述語にしない。残る一基本記号はkの単位電気量記録の参照。',
 '旧文165–166だけを置き換え、他356主張、旧版、既判断と証拠を保つ。u0173の第一文・第六文と段落全体の通読判断は未完。',
]

def definitions():
    text=''.join('r '+n+'['+' '.join(t for _,t in fs)+'] '+('c' if fs else 'a')+'.\n' for n,(fs,_) in PRIMITIVES.items())
    zero=k('bb','n p a b');one=k('bb','n p b b');ctx=v('context')
    explicit=REST+[('domain',TIMES),('curve',CURVE)]
    text+=define('ejwq',explicit,k('seoc',v('carrier'),v('frame'),ctx,v('domain'),v('curve'),v('event'),v('point'),zero,zero,zero))
    text+=define('ejwr',REST,q('g','domain',TIMES,q('g','curve',CURVE,k('ejwq',*[v(n) for n,_ in explicit]))))
    fixed={n:v(n) for n,_ in LOCAL};fixed.update(chargescale='n p b b',forcescale='n p b b',charge=one,conversion=one,electric=v('force'))
    text+=define('ejws',LOCAL,both(k('va',v('frame')),k('eisqc',v('carrier'),ctx),k('eisqd',v('carrier'),v('frame'),v('event'),v('lengthunit'),v('timeunit'),v('point'),ctx),k('eibs',*[fixed[n] for n,_ in FIELDS])))
    def field_definition(values):
        fields=dict(kind=k('zor'),frame=values['frame'],lengthunit=values['lengthunit'],timeunit=values['timeunit'],amountunit=values['chargeunit'],forceunit=values['forceunit'],region=values['region'],context=values['context'],response=values['response'],fieldunit=values['fieldunit'],conversion=one,field=values['electricfield'])
        return k('ejts',*[fields[n] for n,_ in FIELD_ARGS])
    values={n:v(n) for n,_ in LOCAL+[('response',RESPONSE)]}
    text+=define('ejwt',LOCAL+[('response',RESPONSE)],both(k('ejws',*[v(n) for n,_ in LOCAL]),field_definition(values),k('sho',AXES,v('force'),app(v('response'),v('point'),one),'p sca')))
    records={}
    for name,frame,e,h,region,point,force,record,charge in [('ejwu','ra','znl','znm','znk','zpj','zpl','zpe','zpp'),('ejwv','zbm','znr','zns','znt','zpk','zpm','zpf','eisqk')]:
        values=dict(carrier=k('zol'),frame=k(frame),event=k('zpo'),chargerecord=k(charge),forcerecord=k(record),chargeunit=k('zou'),fieldunit=v('fieldunit'),forceunit=k('zot'),lengthunit=k('ta'),timeunit=k('rb'),point=k(point),electricfield=k(e),magneticfield=k(h),region=k(region),force=k(force),context=ctx,response=v('response'))
        records[name]=values
        body=k('ejwt',*[values[n] for n,_ in LOCAL+[('response',RESPONSE)]])
        text+=define(name,[('context','d')],q('g','fieldunit','a',q('g','response',RESPONSE,body)))
    p=v('point')
    text+=content('ejww',op('y',k('x4',k('zol'),k('ra'),p),k('ejwu',p)))
    text+=content('ejwx',op('y',k('ejwr',k('zol'),k('zbm'),k('zpo'),k('zpk'),p),k('ejwv',p)))
    values=records['ejwu']|{'context':p}
    text+=content('ejwy',q('g','fieldunit','a',q('g','response',RESPONSE,field_definition(values))))
    a=k('rd');scope=k('zno');paper=k('eirf')
    text+=content('ejwz',both(k('uh',k('zph'),a,quote('ejww'),scope,p),k('eisql',k('zph'),a,quote('ejwy'),quote('ejww'),scope,p),k('eispi',k('eispj'),'r[p ejs4]',paper,p)))
    text+=content('ejw2',both(k('uh',k('zpi'),a,quote('ejwx'),scope,p),k('eispi',k('eispv'),'r[p ejtx]',paper,p)))
    for value,message,claim,node,prior in [('ejwz','ejw3','ejw4','zph','zpg'),('ejw2','ejw5','ejw6','zpi','zph')]:
        text+='d '+message+'[] f[j s[k '+value+'[]]].\n'
        text+=define(claim,[],both(k('eir3',k(node),a,paper,quote(message),k('ri')),k('ue',k(prior),k(node),k('ri')),op('u',op('e',k(prior),k(node)))))
    return text

def build():
    old=parse(read(PARENT));assert len(old['statements'])==358
    assert not(set(PRIMITIVES)|set(MEANINGS))&{d['name'] for d in old['declarations']}
    doc=deepcopy(old);doc['statements']=[];doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=deepcopy(old['statements'])
    for i,n in zip(INDICES,('ejw4','ejw6')):doc['statements'][i]=dict(kind='assert',body=dict(kind='call',symbol=n,arguments=[]))
    added=doc['declarations'][len(old['declarations']):]
    primitives={d['name']:dict(parameters=d['parameters'],result=d['result'],arguments=[n for n,_ in PRIMITIVES[d['name']][0]],meaning_ja=PRIMITIVES[d['name']][1]) for d in added if d['kind']=='primitive'}
    basis=dict(status='rest_and_instantaneous_rest_unit_charge_force',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives=primitives,definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=INDICES).document
    ann=json.loads(read('data/moving-unit-charge-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
