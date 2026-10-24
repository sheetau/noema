"""Connect both force wordings to the same physical instantaneous velocity."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_vacuum_field_domain import ROOT,read
from scripts.compose_material_relative_frame import define
from scripts.compose_material_velocity import DOMAIN as TIMES,CURVE
from scripts.compose_relativity_conjecture import content
from scripts.compose_two_postulates import quote
from scripts.compose_field_equations import POINT,ROLES
from scripts.compose_force_wordings import vector,at
from scripts.compose_rest_force import AXES
from scripts.compose_limits import v,call as k,app,op,both,quant as q

PARENT='examples/v014/einstein-force-interpretation.noema';PARENT_BASIS='data/force-interpretation-basis-v1.json'
FULL='examples/v014/einstein-force-motion-binding.noema';CORE='examples/v014/force-motion-binding-core.noema'
BASIS='data/force-motion-binding-basis-v1.json';ANNOTATIONS='data/force-motion-binding-identifiers-v1.json'
INDICES=[167,168]
LOCAL=[(n,'a') for n in ('carrier','frame','event','chargerecord','chargeunit','lengthunit','timeunit')]+[('point',POINT),('velocity',POINT),('context','d')]
HISTORY=LOCAL+[('domain',TIMES),('curve',CURVE)]
MEANINGS={
 'ejxj':'同じ三空間軸の速度成分が有効な実数であり、その二乗和が正である。任意方向の非零瞬間速度を扱い、横成分を0に固定しない。光速との大小はこの定義へ隠さず、適用側で指定する。',
 'ejxk':'同じ点状電気量・系・評価出来事・位置・文脈を、量単位の値1、長さと時間の座標規約、単位明示の位置、および同じ物理的履歴seocの三つの座標時刻微分へ結ぶ。速度はその同じ履歴の三成分であり、単なる運動ラベルや位置の差ではない。',
 'ejxl':'同じ全LOCAL引数についてejxkを満たす時間領域と座標履歴が存在する。同じ二証人を全速度成分に共有し、各成分ごとに別の履歴へ交換しない。',
 'ejxm':'任意方向の速度を引数に、同じzol・K・zpo・zpj・単位値記録zpp・zou・ta/rbのejxlを、現在のKの物理的な両場ejsyと領域znk内の同じ位置へ結ぶ。先行校正のcm座標を代入しない。',
 'ejxn':'現在のKの同じ電磁場内で、ejxmの任意方向の非零瞬間速度が存在するという、両項に共通する運動前提。x方向だけを動くことの定義にしない。',
 'ejxo':'現在の光速度tcと符号付き変換速度zb7を許容域s45へ置き、ejxmの実際の三速度を(zb7,0,0)に一致させた標準配置の特殊化。ejxn一般への同値や全方向への拡張を主張しない。',
 'ejxp':'ejxoの同じ対象・出来事にkで瞬間静止ejwrを要求し、同じ長さ・時間単位のk座標zpkと現在のkの物理的な場ejtuを結び、K位置zpjの正規化Lorentz像とk位置の全四座標を一致させる。点の数値変換だけで相対静止を認定しない。',
 'ejxq':'旧来の第一項の標準配置における部分記述。現在の物理的な単位電気量がejxoで動く場合、同じ地点の固定した電気・磁気側の値について、既存scm2の一次外積式と厳密混合式の差が速度比の二次のオーダーとなる。追加寄与の物理的帰属と任意方向への拡張は未完であり、全文の代用ではない。',
 'ejxr':'新しい第二項の標準配置における部分記述。ejxpの場合、kでの同じ対象の力を現在の単位電気量・物理的な静止試験応答ejwvへ結び、kの電場三成分を逆座標変換付きのs6kへ全領域で等置し、同じzpkで評価した変換後の電場が同じ力zpmになる。Kの力zplとの成分等置は要求しない。',
 'ejxs':'第一項の標準配置に限る部分内容ejxqを同じ著者の提示へ結ぶ。旧来という言い方の位置付けは未完。',
 'ejxt':'第一項の部分提示ejxsを述べるメッセージ。',
 'ejxu':'第一項を同じ著者・論説へ帰属し、二表現の導入eisqnの後へ接続する。旧文167を置き換え、全文の判断を加えない。',
 'ejxv':'第二項の標準配置に限る部分内容ejxrを同じ著者の提示へ結ぶ。新しいという対比と任意方向への接続は未完。',
 'ejxw':'第二項の部分提示ejxvを述べるメッセージ。',
 'ejxx':'第二項を同じ著者・論説へ帰属し、第一項zpqの後へ接続する。旧文168を置き換え、全文の判断を加えない。',
}
LIMITS=[
 'u0174–u0175を原刊909末尾と910頁で連続して読む。Ist ... bewegtは同じ点状の単位電気量の非零瞬間速度として読む。零速度極限は近似の族に残し、全期間の等速又は加速度0を加えない。',
 'ejxj–ejxnは三方向を扱う一般の依存群である。本文へ接続するejxq/ejxrは標準配置のx方向だけの部分記述であり、任意方向を無言に除外した全単位完成とはしない。適切な軸選択・回転と場・力の成分対応が残る。',
 'seocの履歴、内点と座標時刻微分を使い、ejslの校正された座標規約とeisqdの単位明示位置を共有する。電気量記録は力評価出来事zpoで値1とし、校正出来事zooとの同一性や時間にわたる保存則を追加しない。',
 '第一項は電気力に加わる電動力の物理的な寄与の同定をまだ含まない。既存の数値外積・加算と二次剰余を現行の運動・場へ接続する段階である。全場に一様な誤差定数、有限速度での一次式の厳密同値を主張しない。',
 '第二項は当該瞬間に対象へ相対静止するkで測る力として読み、同じkの位置で変換後の場を評価する。単なるzpa、旧scf2、一般のxmから静止・力の同定を引き継がない。実在する有限の試験体が真空域を占有したという条件は補わない。',
 'Alte/Neue Ausdrucksweiseの対比、第一項で引用されたelektromotorische Kraftの語の位置付け、任意方向への接続と両項全体の意味判断は未完。A0024は頁910への区切りで脚注ではない。M0318はv/V。',
 '新しい原始記号を追加せず、旧360主張のうち167–168だけを更新する。既判断のu0173を含む他358主張、全旧定義・意味・証拠を保持する。有限検査は全実数・全関数域の証明又は意味判断ではない。',
]

def definitions():
    zero=k('bb','n p a b');one=k('bb','n p b b');ctx=v('context');velocity=v('velocity')
    components=[app(velocity,k(a)) for a in ROLES[:3]]
    squared=k('sexb',*components,*components)
    text=define('ejxj',[('velocity',POINT)],both(k('shn',AXES,velocity,'p ba'),k('bg',zero,squared)))
    text+=define('ejxk',HISTORY,both(k('ejxj',velocity),k('eisqc',v('carrier'),ctx),
        k('ejsl',*[v(n) for n in ('frame','lengthunit','timeunit','context')]),
        k('eisqd',*[v(n) for n in ('carrier','frame','event','lengthunit','timeunit','point','context')]),
        k('sbw2',v('chargerecord'),v('carrier'),k('zor'),v('frame'),v('event'),v('chargeunit'),'n p b b',one,ctx,'p zof','p zog'),
        k('seoc',v('carrier'),v('frame'),ctx,v('domain'),v('curve'),v('event'),v('point'),*components)))
    text+=define('ejxl',LOCAL,q('g','domain',TIMES,q('g','curve',CURVE,k('ejxk',*[v(n) for n,_ in HISTORY]))))
    fixed=dict(carrier=k('zol'),frame=k('ra'),event=k('zpo'),chargerecord=k('zpp'),chargeunit=k('zou'),lengthunit=k('ta'),timeunit=k('rb'),point=k('zpj'),velocity=velocity,context=ctx)
    text+=define('ejxm',[('velocity',POINT),('context','d')],both(k('ejxl',*[fixed[n] for n,_ in LOCAL]),k('ejsy',ctx),app(k('znk'),*[app(k('zpj'),k(a)) for a in ROLES])))
    text+=define('ejxn',[('context','d')],q('g','velocity',POINT,k('ejxm',velocity,ctx)))
    text+=define('ejxo',[('context','d')],both(k('s45',k('tc'),k('zb7')),k('ejxm',vector((k('zb7'),zero,zero)),ctx)))
    text+=define('ejxp',[('context','d')],both(k('ejxo',ctx),k('ejwr',k('zol'),k('zbm'),k('zpo'),k('zpk'),ctx),
        k('ejsl',k('zbm'),k('ta'),k('rb'),ctx),k('eisqd',k('zol'),k('zbm'),k('zpo'),k('ta'),k('rb'),k('zpk'),ctx),k('ejtu',ctx),
        k('shn',k('shx'),k('zpk'),'p ba'),k('sho',k('shx'),k('s46',k('tc'),k('zb7'),k('zpj')),k('zpk'),'p sca')))
    p=v('point');transformed=k('s6k',k('tc'),k('zb7'),k('znl'),k('znm'))
    text+=content('ejxq',op('y',k('ejxo',p),k('scm2',at(k('znl'),k('zpj')),at(k('znm'),k('zpj')))))
    text+=content('ejxr',op('y',k('ejxp',p),both(k('ejwv',p),k('ejs3',k('znr'),transformed,k('znt')),k('scb2',AXES,transformed,k('zpk'),k('zpm')))))
    author=k('rd');paper=k('eirf')
    for val,msg,claim,body,node,prior in [('ejxs','ejxt','ejxu','ejxq','zpq','eisqn'),('ejxv','ejxw','ejxx','ejxr','zpr','zpq')]:
        text+=content(val,k('uh',k(node),author,quote(body),k('zno'),p))
        text+='d '+msg+'[] f[j s[k '+val+'[]]].\n'
        text+=define(claim,[],both(k('eir3',k(node),author,paper,quote(msg),k('ri')),k('ue',k(prior),k(node),k('ri')),op('u',op('e',k(prior),k(node)))))
    return text

def build():
    old=parse(read(PARENT));assert len(old['statements'])==360
    assert not set(MEANINGS)&{d['name'] for d in old['declarations']}
    doc=deepcopy(old);doc['statements']=[];doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=deepcopy(old['statements'])
    for i,n in zip(INDICES,('ejxu','ejxx')):doc['statements'][i]=dict(kind='assert',body=dict(kind='call',symbol=n,arguments=[]))
    added=doc['declarations'][len(old['declarations']):]
    basis=dict(status='force_wordings_physical_motion_dependency_standard_case_only',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives={},definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=INDICES).document
    ann=json.loads(read('data/force-interpretation-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
