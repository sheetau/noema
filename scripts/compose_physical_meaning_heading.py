"""Bind the fourth heading to current equations, rigid bodies and clock motion."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_final_transform_claim import ROOT,read
from scripts.compose_observer_contrast import FIELDS
from scripts.compose_rod_methods import history,interval
from scripts.compose_material_relative_frame import define
from scripts.compose_limits import R,v,call as k,app,op,both,quant as q

PARENT='examples/v014/einstein-final-transform-claim.noema';PARENT_BASIS='data/final-transform-claim-basis-v1.json'
FULL='examples/v014/einstein-physical-meaning-heading.noema';CORE='examples/v014/physical-meaning-heading-core.noema'
BASIS='data/physical-meaning-heading-basis-v1.json';ANNOTATIONS='data/physical-meaning-heading-identifiers-v1.json';INDEX=326
PRIMITIVES={'eisn5':([], 'この論説の第四節という文書区分。固定原文u0109から第五節u0129直前のu0128までを含み、第一部の直接の下位区分である。見出し位置zht、表示番号、主題は別に結ぶ。')}
MEANINGS={
 'ejer':'同じ対象・系・単位・正の時間区間に三つの代表位置の全se履歴を保持し、区間内の前後する二実数時刻に少なくとも一成分の位置差がある。時計の機構全体を物質点として動かす条件ではなく、同じ時計の配置の運動を記述する。',
 'ejes':'同じ物体の同伴側kでの全物質点の剛性eigyと、比較側Kでの全物質点履歴に基づく運動eiagを、各系の正の対象期間へ結ぶ。この二系の同時性や時刻値を等置しない。',
 'ejet':'同じ時計の型caと、Kでの代表配置の全区間の運動ejerを結ぶ。内部の針の運動だけを時計の移動とせず、校正・同期・遅れの結論はこの分類へ加えない。',
 'ejeu':'現在のK/kの適格記録範囲eiyz/eiy2における最終四式ssnの条件。先に得た同じτ,ξ,η,ζの四式を、その物理的な記録への参照とともに研究主題へ渡す。',
 'ejev':'同じ著者が同じ第四節の主題として、得られた現在四式ejeuの物理的な意味を、動く剛体ejesと動く時計ejetという二種類の対象について検討すると示す。具体的な収縮や時計遅れの結論は含めない。',
 'ejew':'第四節見出しzhtを第一部の深さ2・表示番号4の区分eisn5へ結び、物理的意味を扱う主題ejevを案内する。第三節末のβ指定からの本文順序と、区分・見出し・親区分の区別を保持する。',
}
LIMITS=[
 '原刊903頁のu0109全体を対象とする。第四節は第一部に直接属する深さ2・表示番号4であり、範囲はu0109–u0128。見出しの案内と後続本文の物理的主張・完成を区別する。',
 'erhaltenen Gleichungenは第三節末に得た同じ四座標変換を指す。ejeuは同じ現在のK/k記録の範囲とssnの四式を保持し、名前だけの方程式又は別の旧範囲へ置き換えない。見出し自体は実測や変換則の真理を断言しない。',
 'bewegte starre Körperは同じ二系の比較で、同伴側kの尺度と同時性で剛性を持ち、Kに対して動く物体の主題として読む。eigyの全物質点間距離とeiagの全履歴を保持する。中心又は二端だけで剛性を済ませない。',
 'bewegte Uhrenは時計の代表配置の位置変化として読む。針や内部機構が動いているだけの静置時計を含めず、内部の全物質点を静止又は等速へ固定しない。見出しから時計の同期・校正・特定の遅れを追加しない。',
 '対象の運動は区間内に位置変化があるという分類であり、見出しに印刷されていない特定の軸方向・一定速度・収縮率を加えない。各系の期間は各系の時刻規約を使う。',
 '物理的意味は既存zhrの研究の提示を、物理的記録と方程式、剛性と時計配置の合成内容へ接続して読む。文字列や原語の名称だけを意味に替えず、二対象の一方を落とさない。',
 '有限検査は局所的な運動の証人、全履歴への引数接続、二対象と同じ四式の引用、見出しの階層と順序を調べる。実数全域は有限評価の拒否を保持し、例化した二時刻で全履歴を証明したとはしない。u0110以降及び著者脚注u0281の本文統合は後続。',
]

def definitions():
    text='r eisn5[] a.\n';first=v('first');second=v('second')
    lifted=['i[point a]['+v(a)+']' for a in ('x','y','z')]
    witness=both(k('lg',v('lower'),v('upper'),first),k('lg',v('lower'),v('upper'),second),k('bg',first,second),k('eiae',v('object'),first,second,*lifted))
    text+=define('ejer',FIELDS,both(k('bg',v('lower'),v('upper')),k('eisdd',v('frame'),v('lengthunit'),v('timeunit'),v('context')),k('se',*[v(n) for n,_ in FIELDS]),q('g','first',R,q('g','second',R,witness))))
    body=v('body');ctx=k('zb6');K=k('ra');moving=k('zbm')
    text+=define('ejes',[('body','a')],both(op('u',op('e',K,moving)),k('bg',*interval(K,ctx)),k('bg',*interval(moving,ctx)),k('eigy',*history(body,moving,ctx)),k('eiag',*history(body,K,ctx))))
    tracks=[k('eismh',body,K,k('ta'),k('rb'),k(a),ctx) for a in ('yn','yo','yp')]
    text+=define('ejet',[('body','a')],both(k('ca',body),k('ejer',body,K,ctx,k('ta'),k('rb'),*interval(K,ctx),*tracks)))
    text+=define('ejeu',[('first','a'),('second','a')],both(k('eiyz',first),k('eiy2',second),k('ssn',first,second)))
    text+=define('ejev',[('inquiry','a'),('context','d')],k('zhr',v('inquiry'),k('rd'),'r[p ejeu]','l[i[h[a] c]][r[p ejes] r[p ejet]]',k('eisn5'),v('context')))
    text+=define('ejew',[],both(k('eihq',k('zht'),k('eisn5'),k('eisdx'),k('eirf'),'n p c b','n p e b','r[p ejev]',k('ri')),k('ue',k('eisn4'),k('zht'),k('ri')),op('u',op('e',k('eisn4'),k('zht')))))
    return text

def build():
    old=parse(read(PARENT));assert len(old['statements'])==INDEX;doc=deepcopy(old);doc['statements']=[]
    assert not(set(MEANINGS)|set(PRIMITIVES))&{d['name'] for d in old['declarations']}
    doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']+[dict(kind='assert',body=dict(kind='call',symbol='ejew',arguments=[]))]
    added=doc['declarations'][len(old['declarations']):]
    primitives={d['name']:dict(parameters=d['parameters'],result=d['result'],arguments=[],meaning_ja=PRIMITIVES[d['name']][1]) for d in added if d['kind']=='primitive'}
    basis=dict(status='physical_interpretation_heading_with_current_object_motion',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives=primitives,definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=[INDEX]).document
    ann=json.loads(read('data/final-transform-claim-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
