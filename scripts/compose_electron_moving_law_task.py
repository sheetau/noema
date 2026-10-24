"""Pose the law of the same electron's initial motion at a specified speed."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_limits import ROOT,R,v,call as k,app,op,both,quant as q
from scripts.compose_material_relative_frame import define
from scripts.compose_point_particle_dynamics import SETTING,CASES,REST,PROFILES,args,coord,ROLES,ZERO,ONE
from scripts.compose_electron_rest_law_claim import FUTURE
from scripts.compose_doppler_infinity import quantified
from scripts.compose_relativity_conjecture import content
from scripts.compose_two_postulates import quote

def read(path):return (ROOT/path).read_text(encoding='utf-8')
PARENT='examples/v014/einstein-electron-rest-law-claim.noema';PARENT_BASIS='data/electron-rest-law-claim-basis-v1.json'
FULL='examples/v014/einstein-electron-moving-law-task.noema';CORE='examples/v014/electron-moving-law-task-core.noema'
BASIS='data/electron-moving-law-task-basis-v1.json';ANNOTATIONS='data/electron-moving-law-task-identifiers-v1.json';INDICES=(415,416)
NORM=[(n,R) for n in ('speed','vx','vy','vz')]
SPEED=REST+[('speed',R)]
code=lambda result:'i[h['+' '.join(t for n,t in SETTING)+'] '+result+']'
PRIMITIVES={
 'eisxn':([('law','a'),('matter','a'),('frame','a'),('context','d')],'lawの適用対象と量の役割が、同じmatterのframeでの位置・速度の変化と、その変化を支配する物理的作用の関係であるという運動法則の範囲指定。法則の内容はviの許容条件へ別に与え、特定の力の公式、法則の真理、全候補の適合、解の存在又は発見済みはこの分類に含めない。単に状態の記述に偶然一致する数値式や、名前だけの法則を運動法則へ認定しない。'),
 'eisxo':([('representation','a')]+SETTING,'representationが同じ設定の物理的な局所運動の記述を過不足なく表す対応。対象・系・出来事・座標単位・場・電荷・低速慣性質量・時間領域・実際の軌道・速度三関数・三加速度を同じ割当のまま保持する。履歴は同じ初期値と微分の根拠として含み、法則の許容条件を問う範囲は同じ時点の状態と直後への初期変化とする。全有限区間での運動を要求しない。直後への初期変化は別にek32等で要求する。記述を別粒子や別時点から集めず、対応する全記述をこの関係の範囲とする。法則への適合、実測済み、同一の文字列や一意の記録を要求しない。位置や物理量の数値本体は別に合成し、この対応に特定の運動方程式を埋め込まない。'),
 'eisxp':([('node','a'),('author','a'),('anchor','a'),('prior','i[e]'),('condition',code('c')),('question',code('g[a]')),('scope','a'),('context','d')],'authorがscopeのanchorで採ったpriorを引き継ぎ、nodeでconditionの下のquestionの答えを見いだすことを現在の課題として提示する。二つの閉じた規則は同じ型と順序の設定引数を取り、一つの許容割当を答え候補の外側で固定して共有する。個体を答えとする条件付き探究の一般関係であり、具体的な物理対象・時点・法則条件は引用規則で構成する。単なる問いの存在や将来の意図へ替えず、解の存在・唯一性・既知性・発見済み・探索の実施済み・引用の自動実行を含意しない。'),
 'eisxq':([('node','a'),('previous','a'),('ordinal','b'),('scope','a'),('context','d')],'同じ論述範囲scopeの一続きの検討で、previousに続く場合nodeをordinal番目として取り上げる。本文の検討順と前の場合への参照を保ち、物理的な時間の経過、二個目の対象、印刷された見出し番号、場合の相互排他性又は全場合の尽くしを含意しない。'),
 'eisxr':([], 'u0244第一文Es besitze nun zweitensからGeschwindigkeit vまでの、同じ電子の第二の場合を置く箇所。'),
 'eisxs':([], 'u0244第二文Wir suchenからbewegtまでの、同じ電子の直後の運動法則を探す箇所。'),
 'eisxt':([], 'u0244の指定された同じ時点における同じ電子の速さvの値。非負ノルムと物理的帰属をek4o/pで構成し、以前の二系間の定速度へ無条件に同一視しない。'),
 'eisxu':([], 'u0244の速さを表すvの表記。後続の軸選択前の大きさであり、値は同じ瞬間速度の三成分へ結ぶ。'),
}
MEANINGS={
 'ek4n':'三つの有効な符号付き速度成分の二乗和を二乗に持つ、有効な非負の速さ。負の枝を拒否し、零と任意の方向を許す。',
 'ek4o':'同じ四座標の時刻成分で同じ三速度関数を評価し、ek4nによって指定した瞬間の速さを与える。異なる時刻や全期間の一定速度に替えない。',
 'ek4p':'前段と同じ粒子の物理的設定ek34と位置変化ek4mを保ち、同じ出来事の瞬間速度の大きさをu0244のvへ結ぶ。X軸方向や全期間の等速、光速上限をここでは加えない。',
 'ek4q':'同じK・提示文脈・単位でek4pの設定があるという第二の場合の仮定内容。全30役割の一つの共同証人を選び、現実の存在を無条件に断言しない。',
 'ek4r':'同じek4pの設定で速さvの値を返す射影規則。ek4pが同じ実速度の非負ノルムへ結んだ値を用いる。',
 'ek4s':'vの表記を同じ物理的設定ek4pと値の射影ek4rへ既存eiswyで接続する。前の系間速度と同名だから等しいとはしない。',
 'ek4t':'著者が同じ電子についてek4qを仮定して議論を進め、先の静止条件の場合に続く第二の場合とする設定操作。前段の導入・運動仮定を参照し、同じvの意味規約を保つ。',
 'ek4u':'第二の場合を置くek4tの指示形式。現実に粒子へ速度を与える実験の命令ではない。',
 'ek4v':'u0244第一文の設定指示を同じ著者・論説へ帰属し、前の座標と質量の意味説明に続ける主張415。',
 'ek4w':'同じ固定されたek4pの設定に対する運動法則の候補。状態変化の法則範囲vd、同じ粒子・系への適用範囲eisxn、法則としての成立eisbi、右側初期変化ek32、非空で完全な同じ運動記述の全てへの適合viを結ぶ。単なる三加速度の数値又は一個の都合のよい記述だけを答えにしない。',
 'ek4x':'設定の引数を候補の外側で固定したek4wの法則個体を答えとする質問。候補の運動方程式の内容はその法則の許容条件viに保持し、まだ求めている特定の公式を答えとして先取りしない。',
 'ek4y':'同じ著者が直前の仮定ek4tを引き継いで、同じ固定設定のek4xの答えを見いだす課題を提示する。第二文を直前のvの場合に結び、引用された物理内容を実行しない。',
 'ek4z':'同じ電子の初期運動法則を探すという現在の課題提示ek4yを断定的に伝える形式。答えの断定ではない。',
 'ek42':'u0244第二文の探究課題を同じ著者・論説へ帰属し、第二の場合の設定に続ける主張416。',
}
LIMITS=[
 'u0244の二文とM0398を原刊917頁へ照合する。Es besitzeの仮定的指示とWir suchenの課題提示を区別し、同じ電子・指定時点・直後の初期運動へ接続する。',
 'vはまだ方向を選ばない非負の速さと読む。三成分の瞬間値の二乗和で指定し、次のu0245のX軸方向への選択を先取りしない。零を退化例として許し、zweitensを二つの場合の排他性とはしない。光速上限や等速運動はこの二文へ補わない。',
 '前段の局所的な古典粒子モデル、同じ出来事の符号付き電荷、低速慣性質量、整合単位、完全な二階微分可能な局所履歴を継承する。存在は著者の設定内容として引用し、現実に電子が発生したとは述べない。',
 'unmittelbar darauf folgenden Zeitteilchenは、指定した同じ出来事の座標時刻から右側への初期速度変化として読む。前段の基点を含む右側領域とek32を再利用し、正長の一定加速区間・最小時間粒・有限時間の厳密解を要求しない。',
 '求めるものは、その初期運動を支配する物理的な運動法則であり、三加速度の測定値だけではない。既存vd/eisbi/viによる法則の範囲・一般的な成立・記述への適合を分け、同じ設定に対応する全記述へ適合を要求する。未知の答えの許容条件はlawを引数とするviへ保持し、この問いの段階で特定の力の公式を定義した又は証明したとはしない。後続の答えを統合するときはそのlawの内容と実際の方程式を別に接続する。',
 '一つの設定を質問の外側で固定し、候補法則ごとに別粒子・別時点・別の場へ変えない。法則としての成立は物理的な基本入力であり、有限点への偶然の当てはめや法則名だけから認定しない。全対応記述を扱うが記録の一意性や数式表示の唯一性は課さない。',
 'nunは論述の進行として、zweitensは先の静止条件の場合に続く検討順として読む。Wirは同じ著者の論述の声であり、共著者集団、読者全員の探索、発見済み・解の存在一意性を足さない。',
 '原始関係は一般的な運動法則の適用範囲、物理設定と記述の対応、個体回答の条件付き探究提示、検討順の指定に限る。速度・初期変化・法則適合・対象同一性・引用・帰属は合成する。第十節見出しと後続の座標選択・変換による具体式は未完。',
]

def definitions():
    text=''.join('r '+n+'['+' '.join(t for _,t in fs)+'] '+(R if n=='eisxt' else 'c' if fs else 'a')+'.\n' for n,(fs,_) in PRIMITIVES.items())
    square=lambda x:k('shv',x,x)
    total=k('bd',k('bd',square(v('vx')),square(v('vy'))),square(v('vz')))
    text+=define('ek4n',NORM,both(*(k('ba',v(n)) for n,t in NORM),op('u',k('bg',v('speed'),ZERO)),k('sca',square(v('speed')),total)))
    moment=coord(v('point'),ROLES[3])
    text+=define('ek4o',SPEED,k('ek4n',v('speed'),*(app(v(n),moment) for n,t in PROFILES)))
    text+=define('ek4p',SETTING,both(k('ek34',*args(SETTING)),k('ek4m',v('domain'),v('curve')),k('ek4o',*args(REST),k('eisxt'))))
    fields=[(('location' if n=='point' else n),t) for n,t in CASES]
    bound=args(SETTING,frame=k('ra'),context=v('point'),electricconversion=ONE,point=v('location'))
    text+=content('ek4q',quantified('g',fields,k('ek4p',*bound)))
    text+=define('ek4r',SETTING,k('eisxt'),R)
    p=v('point');author=k('rd');paper=k('eirf');scope=k('eisxg');intro=k('eisxr');task=k('eisxs')
    text+=content('ek4s',k('eiswy',k('eisxu'),'r[p ek4p]','r[p ek4r]',paper,scope,p))
    text+=content('ek4t',both(k('ug',intro,author,quote('ek4q'),scope,p),k('eisxq',intro,k('eisxd'),'n p c b',scope,p),k('eisra',intro,author,paper,k('eisxb'),quote('ek4h'),quote('ek4q'),scope,p),op('t',k('ek4s'),p)))
    text+='d ek4u[] f[j m[k ek4t[]]].\n'
    text+=define('ek4v',[],both(k('eir3',intro,author,paper,quote('ek4u'),k('ri')),k('ue',k('eisxf'),intro,k('ri')),op('u',op('e',k('eisxf'),intro))))
    ctx=v('context');law=v('law');rep=v('representation');represented=k('eisxo',rep,*args(SETTING))
    text+=define('ek4w',SETTING+[('law','a')],both(k('ek4p',*args(SETTING)),k('ek32',*args(FUTURE)),k('vd',law,ctx),k('eisxn',law,v('matter'),v('frame'),ctx),k('eisbi',law,v('frame'),ctx),q('g','representation','a',represented),q('f','representation','a',op('y',represented,k('vi',law,rep,ctx)))))
    text+=define('ek4x',SETTING,'j v[i[law a]['+k('ek4w',*args(SETTING),law)+']]','g[a]')
    text+=content('ek4y',k('eisxp',task,author,intro,quote('ek4t'),'r[p ek4p]','r[p ek4x]',scope,p))
    text+='d ek4z[] f[j s[k ek4y[]]].\n'
    text+=define('ek42',[],both(k('eir3',task,author,paper,quote('ek4z'),k('ri')),k('ue',intro,task,k('ri')),op('u',op('e',intro,task))))
    return text

@lru_cache(None)
def build():
    old=parse(read(PARENT));assert len(old['statements'])==INDICES[0]
    assert not(set(MEANINGS)|set(PRIMITIVES))&{d['name'] for d in old['declarations']}
    doc=deepcopy(old);doc['statements']=[];doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']+[dict(kind='assert',body=dict(kind='call',symbol=n,arguments=[])) for n in ('ek4v','ek42')]
    added=doc['declarations'][len(old['declarations']):]
    prim={d['name']:dict(parameters=d['parameters'],result=d['result'],arguments=[n for n,t in PRIMITIVES[d['name']][0]],meaning_ja=PRIMITIVES[d['name']][1]) for d in added if d['kind']=='primitive'}
    basis=dict(status='same_electron_second_speed_case_and_initial_motion_law_task',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives=prim,definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=list(INDICES)).document
    ann=json.loads(read('data/electron-rest-law-claim-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode()))
    ann['entries'].append(dict(symbol='eisxu',role='designation',forms=[dict(text='v',language='de',role='printed_identifying_form')]))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
