"""Connect the axial light trial to current clock readings and its midpoint."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_comoving_time_task import ROOT,read
from scripts.compose_material_relative_frame import define
from scripts.compose_two_postulates import quote
from scripts.compose_relativity_conjecture import content
from scripts.compose_limits import R,v,call as k,op,both,quant as q

PARENT='examples/v014/einstein-comoving-time-task.noema';PARENT_BASIS='data/comoving-time-task-basis-v1.json'
FULL='examples/v014/einstein-axial-time-condition.noema';CORE='examples/v014/axial-time-condition-core.noema'
BASIS='data/axial-time-condition-basis-v1.json';ANNOTATIONS='data/axial-time-condition-identifiers-v1.json';INDEX=277
MEANINGS={
 'eiz5':'同じ出来事の現在のK四座標eiyxから、同じ速度zb7でsinによるx-vtの値を作り、指定補助座標へ一致させる。sinの引数順序は速度・位置・時刻である。ξの代入や横座標・原点の零固定は加えない。',
 'eiz6':'指定出来事の補助座標が、一つの同じK四座標組でeiz5を満たすという存在条件。別の出来事のxとtを混ぜない。',
 'eiz7':'同じ比較出来事・配備時計・地点・移動系・値について、現在の局所表示eiyg、値として一意な時刻付与eiyi、各系時点との対応eiyjと候補zbeへの等値を結ぶ。τの読みを静止系時刻へ取り違えない。',
 'ei2a':'指定試行の同じ二時計・二地点・一光線・三出来事・三読みを、kの原点と縦軸、非退化なda/sde往復、往復とも全経路が軸上にあるzdw、同じ完全試行範囲の同期qoとqb、各読取りのeiz7、厳密な時間順序へ結ぶ。帰着は出発と同じ原点時計である。',
 'ei2b':'先行する同じ測定・並進・全時点平行軸の設定eixt、全配備時計の同期eiyf、全比較出来事の座標対応eiy3を受け、選ばれた試行ei2aと両端の自系静止・同じK並進eizm、反射出来事の補助座標eiz6を結ぶ。',
 'ei2c':'u0049で仮想的に置く、同じ移動後設定の軸方向往復ei2bの内容。実際の光発射済みという主張ではない。',
 'ei2d':'同じ試行の出発・反射・帰着のk時計読取値qi,qj,qkを、既存sitの½(τ₀+τ₂)=τ₁へそのまま渡す内容。中点式だけから往復の実在や時間順序を推定しない。',
 'ei2e':'著者が軸方向の往復ei2cを同じ第三節の仮想設定として採用し、先行するτの指示条件を方程式で表す課題に追加することを保持する。',
 'ei2f':'軸方向の往復の仮想設定ei2eを述べるメッセージ。',
 'ei2g':'u0049前半の仮想設定を同じ著者・論説へ帰属し、先行するτ探索の目的に続ける。',
 'ei2h':'同じ往復設定ei2cを前提に、その同じ三読取値の中点式ei2dでなければならないという著者の必要性の提示を、設定から結論への本文順序とともに保持する。',
 'ei2i':'u0049末尾とu0050の中点式にまたがる必要性ei2hを述べるメッセージ。',
 'ei2j':'条件付きの必要性と表示式を同じ著者・論説へ帰属し、往復設定に続ける。式だけを無条件の独立した実験結果へ替えない。',
}
LIMITS=[
 'u0049全245文字・167本文文字と、数式だけのu0050（M0098）を一つの文と表示式として扱う。出発、軸方向、反射地点、反射と帰着の読取り、同じ原点への復帰、so muß dann seinの必要性と中点式を保持する。',
 'werde gesandt・reflektiert・anlangeは仮想設定の導入である。前段の同期したk時計を使う同じ設定として読む。物理的な発射命令、実験済みや一般的な光速の導出へ置き換えない。',
 '原刊の大文字Xは、この設定の共通の縦方向を指すと読む。既出の初期X支持線一致・同じ正X並進・全時点で対応軸が平行というeixtの設定を保持し、光の全往復経路をk原点から出る同じ縦軸の支持線へ結ぶ。単なる二端の配置や任意の平行な別線だけへ弱めない。両原点の一致や正方向一致を別途追加しない。',
 'x′は反射地点の補助座標値x-vtで、ξや静止系時刻tを意味しない。現在の同じ出来事のK四座標へ結ぶ。この文では原点の補助値を零に固定せず、反射値の符号や零でないことも数値の原点とは独立に補わない。非退化性は異なる両端と三出来事、厳密な時刻順序で保つ。',
 '旧siwの0,x′,0およびy=z=0は使わない。後続u0051–u0053で出る零座標の規約はそこで確認する。一般的な軸方向の往復に、まだ指定されていない座標原点の選択を先取りしない。',
 'τ₀,τ₁,τ₂は同じ試行の出発・反射・帰着でのk局所時計の値である。出発と帰着は同じ時計・同じ原点、反射は別の静止した配備時計へ結ぶ。全時計の自系静止・校正・共通参照・全対全試行の同期と、選択試行がその範囲に含まれることを保持する。',
 '中点式は既存sitで有効な三実数切断の和の半分と反射値の等値を表す。二つの差が等しいという同期規約からの読みを保ち、近似一致、切断の関数個体同一性、三数の大小を等式だけから導くこととは分ける。',
 'u0049末尾とu0050は同じ条件付き結論に属し、同じ主張選択を共有して判断する。著者の必要性の提示、有限の接続検査・有理数代数、全実数上の物理的導出、原文全体の意味判断を区別する。具体的なτ変換式は未導出である。',
]

def definitions():
    e=v('event');t=v('tuple');label=v('label');ctx=v('context');moving=k('zbm');unit=k('rb')
    shifted=k('sin',k('zb7'),k('zc6',t,k('yn')),k('zc6',t,k('zc7')))
    text=define('eiz5',[('event','a'),('tuple','a'),('label',R),('context','d')],both(k('ba',label),k('eiyx',e,t,k('ra'),ctx),k('sca',shifted,label)))
    text+=define('eiz6',[('event','a'),('label',R),('context','d')],q('g','tuple','a',k('eiz5',e,t,label,ctx)))
    text+=define('eiz7',[('event','a'),('clock','a'),('place','a'),('value',R),('context','d')],both(k('zc4',e),k('zcz',e,moving,ctx),k('eiyg',e,v('clock'),v('place'),moving,v('value'),ctx),k('eiyi',e,v('place'),moving,ctx),k('eiyj',e,moving,ctx),k('sca',v('value'),k('zbe',e,moving,unit,ctx))))
    trial=v('trial');first=v('firstclock');second=v('secondclock')
    origin=k('qc',trial);mirror=k('qd',trial);ray=k('qh',trial);axis=k('zbo',moving,k('yn'),ctx)
    events=[k(n,trial) for n in ('qe','qf','qg')];readings=[k(n,trial) for n in ('qi','qj','qk')]
    rows=[k('qb',first,second,moving,unit,ctx,trial),op('u',op('e',first,second)),op('u',op('e',origin,mirror)),op('e',origin,k('zbn',moving,ctx)),k('zbv',moving,origin,ctx),k('zbw',moving,axis,k('yn'),ctx),k('zbz',moving,first,ctx),k('zbz',moving,second,ctx),k('zcu',origin,moving,ctx),k('zcu',mirror,moving,ctx),k('da',first,second,origin,mirror,*events,ray,moving,unit,*readings),k('sde',ray,*events,moving,'p cf','p cg','p ch'),k('qo',first,second,moving,unit,ctx)]
    for a,b in zip(events,events[1:]):rows.append(k('zdw',ray,a,b,axis,moving,ctx))
    for event,clock,place,value in zip(events,(first,second,first),(origin,mirror,origin),readings):rows.append(k('eiz7',event,clock,place,value,ctx))
    rows.extend(k('bg',a,b) for a,b in zip(readings,readings[1:]))
    text+=define('ei2a',[(n,'a') for n in ('trial','firstclock','secondclock')]+[('context','d')],both(*rows))
    current=k('zb6');selected=k('zdq')
    text+=define('ei2b',[],both(k('eixt',current),k('eiyf',moving,current),'t[k eiy3[]][k zb6[]]',k('ei2a',selected,k('zdr'),k('zds'),current),k('eizm',k('qc',selected),current),k('eizm',k('qd',selected),current),k('eiz6',k('qf',selected),k('zdt'),current)))
    text+=content('ei2c',k('ei2b'))
    text+=content('ei2d',k('sit',*(k(n,selected) for n in ('qi','qj','qk'))))
    text+=content('ei2e',both(k('ug',k('zdu'),k('rd'),quote('ei2c'),k('eisms'),v('point')),k('zao',k('zdp'),k('zdu'),k('eisms'),v('point'))))
    text+='d ei2f[] f[j s[k ei2e[]]].\n'
    def author(name,node,message,previous):return define(name,[],both(k('eir3',k(node),k('rd'),k('eirf'),quote(message),k('ri')),k('ue',k(previous),k(node),k('ri')),op('u',op('e',k(previous),k(node)))))
    text+=author('ei2g','zdu','ei2f','zdp')
    text+=content('ei2h',both(k('zc',k('zdv'),k('rd'),quote('ei2c'),quote('ei2d'),k('eisms'),v('point')),k('ue',k('zdu'),k('zdv'),v('point'))))
    text+='d ei2i[] f[j s[k ei2h[]]].\n';text+=author('ei2j','zdv','ei2i','zdu')
    return text

def build():
    old=parse(read(PARENT));assert len(old['statements'])==INDEX;doc=deepcopy(old);doc['statements']=[]
    assert not set(MEANINGS)&{d['name'] for d in old['declarations']}
    doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']+[dict(kind='assert',body=dict(kind='call',symbol=n,arguments=[])) for n in ('ei2g','ei2j')]
    added=doc['declarations'][len(old['declarations']):]
    basis=dict(status='axial_trial_and_moving_clock_midpoint',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives={},definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=[INDEX,INDEX+1]).document
    ann=json.loads(read('data/comoving-time-task-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
