"""Ask four quantities of the same reflection, in the source's resting frame."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_perfect_mirror_setting import ROOT,read,SETTING as PRIOR_SETTING,INTERACTION,models
from scripts.compose_stationary_mirror_boundary import GEOMETRY
from scripts.compose_mirror_surface_pressure import BOUNDS,FORCE,SETTING as FORCE_SETTING
from scripts.compose_observed_intensity import COEFFICIENT
from scripts.compose_wave_cycle_frequency import HARMONIC
from scripts.compose_field_equations import POINT,FIELD,REGION
from scripts.compose_material_relative_frame import define,args
from scripts.compose_relativity_conjecture import content
from scripts.compose_two_postulates import quote
from scripts.compose_doppler_infinity import quantified
from scripts.compose_limits import R,F,v,call as k,app,op,both

PARENT='examples/v014/einstein-perfect-mirror-setting.noema';PARENT_BASIS='data/perfect-mirror-setting-basis-v1.json'
FULL='examples/v014/einstein-reflected-light-inquiry.noema';CORE='examples/v014/reflected-light-inquiry-core.noema'
BASIS='data/reflected-light-inquiry-basis-v1.json';ANNOTATIONS='data/reflected-light-inquiry-identifiers-v1.json';INDEX=395
RETURN=[(n,R) for n in ('light','speed','rate')]+GEOMETRY
WAVE=[('profile',F)]+RETURN
COORDS=[(n,R) for n in ('x','y','z','time')]
COVER=[('region',REGION),('lower',R),('upper',R)]+BOUNDS
SETTING=PRIOR_SETTING+[('patch','a'),('forcelower',R)]+BOUNDS+[('force',FORCE),('labcoefficient',R)]
ANSWERS=[(n,R) for n in ('pressure','nx','ny','nz','receivedfrequency','intensity')]
QUESTION='g['+' '.join(t for n,t in ANSWERS)+']'
code=lambda result:'i[h['+' '.join(t for n,t in SETTING)+'] '+result+']'
PRIMITIVES={
 'eisuf':([('node','a'),('author','a'),('anchor','a'),('prior','i[e]'),('condition',code('c')),('question',code(QUESTION)),('scope','a'),('context','d')],'authorがscopeのanchorで導入したpriorを引き継ぎ、nodeでconditionの下にquestionを問うという論述上の提示。同じ型と順序の74設定を取る二つの閉じた規則に一つの割当を共有し、六実数の答え候補の外側で固定する。この型の条件付き質問族への一般的な提示関係であり、光・鏡・圧力・方向などの具体的対象や候補条件は引用規則で別に合成する。先行の証人を候補ごとに選び直さず、仮定の現実成立、解の存在・一意性・既知性、調査実施済み、引用の自動実行を要求しない。六実数を六つの独立した発話行為に分割せず、構成側で定めた量の組として同時に問う。'),
 'eisug':([], '固定原文einstein-1905:u0215[158,304)のWir fragenからnach der Reflexion.まで、同じ面への光圧と反射後の光の方向・周波数・強度を問う第二文の箇所。'),
}
MEANINGS={
 'ekrk':'kで入射のrateと全三方向を持つ波の法線成分を反転し、速度−vの逆Lorentz変換を適用したKでの反射波の位相率。kの周期数や入射率をKの反射率と同一視しない。',
 'ekrl':'同じk入射方向の鏡映と速度−vによる逆変換からKの反射方向三成分を構成する。三軸以外は零。Kでのx成分が常に負とは仮定しない。',
 'ekrm':'kの入射電磁係数へ完全導体の反射符号を適用し、その同じ二場の速度−v変換からKの反射電場三係数を得る。',
 'ekrn':'ekrmと同じ反射と逆変換によるKの反射磁場三係数。電場と磁場の符号を混同しない。',
 'ekro':'同じprofile、V、K反射位相率・三方向と電場三係数から全四座標の反射電場代表モデルを構成する。',
 'ekrp':'ekroと同じ波形・位相・方向を共有する反射磁場代表モデル。二つの場を別の波にしない。',
 'ekrq':'同じ一周期位相cycleをK反射位相率で割った時間周期。通常周波数はこの逆数として候補条件へ結び、角周波数との数値同一視を避ける。',
 'ekrr':'同じVとvについて物質面ξ=0上のk時刻tauをK時刻β*tauへ移す。静止したK観測点の周期ではなく同じ面上の出来事の時刻である。',
 'ekrs':'正長時間区間と正面積の矩形について、全有効四座標で同じ面部分と区間に入る点が同じ光の領域内にあることを要求する。端点だけ又は一物質点の照射を面部分全体の条件にしない。',
 'ekrt':'同じ74設定で前の完全反射仮定ekrf、同じ面の矩形とkの一周期の全照射、Kへ時間変換した同じ相互作用による力モデルekq4、Kの単位校正と同じ入射・反射代表場の物理的帰属eisucを保持する。求める圧力・反射方向・周波数・平均強度を既知値として設定へ入れない。',
 'ekru':'同じ74設定を固定し、圧力を同じKの面積と時間区間での法線力平均へ、方向三成分を同じK反射波へ、周期数をその正規化位相対の周期へ、強度を進行方向のκ(E×H)の一周期平均へ結ぶ六実数候補。方向三成分は一つの量の表示であり、圧力と面を横切る流及び進行方向の強度を混同しない。',
 'ekrv':'同じ対象・単位・領域・面部分・過程・力履歴を閉じ込めたekruの質問。候補を変えても設定を再選択せず、解の存在・一意性や導出済みを主張しない。',
 'ekrw':'同じ前文の仮定ekrgを受け、同じekrt条件とekrv質問の族を著者が第八節で問う提示。Wirは論述主体の一人称複数と読み、共同著者や読者全員の行為を補わない。',
 'ekrx':'同じ面への光圧と反射後の光の三性質を問う著者の提示ekrwを述べるメッセージ。',
 'ekry':'u0215第二文を同じ著者・論説へ帰属し、同じ鏡面と入射波の仮定の第一文に続ける。後続式の答えを述べたとする主張へ替えない。',
}
LIMITS=[
 'u0215[158,304)第二文の125非空白本文文字を対象とする。第一文の130文字とM0368を同じ対象と仮定へ接続し、全体判断は二文の読み合わせを別に行う。',
 '後続u0216–u0223の静止系へ戻す記述と静止系で測るエネルギーに合わせ、問いの四量はKで記述する読みを採る。kでの同じ理想完全導体面・局所代表モデルを保持し、その逆変換を同じ相互作用のK代表モデルに採用する。実際の場の誤差零や全材料の一般的反射解の唯一性を加えない。',
 '方向は既存の校正した三軸に対する有向単位法線、周波数はKの静止位置での周期数、強度は進行方向に直交する単位面積を通るエネルギー流の一周期平均として読む。角周波数、鏡面法線を横切る流、振幅そのものとは区別する。',
 '光圧は同じ相互作用が同じ有限矩形の物質部分へ及ぼす+x法線力を、同じK時間区間と面積で平均した量とする。力の物理的な帰属は既存eisubで保持し、支持力を含む合力にしない。静止鏡でも定義でき、仕事を速度で割って定義しない。',
 '鏡上のk時刻tau0からtau0+T′の一周期を選び、全矩形・全区間が光の同じ局所モデル領域内にあると要求する。面上のξ=0ではK時刻がβ*tauなので、力の平均区間はβ*tau0からβ*(tau0+T′)へ変換する。Kの静止位置での反射波の周期とは区別する。面が光を受けるのに十分な一周期区間を選ぶ明示的な局所理想化であり、実測期間を勝手に延長しない。',
 '強度の平均は同じK反射正弦代表波の正規化位相原点零における一周期を取る。原点を変えても同じ平均になる標準的な正弦波の読みであり、実際の場を全時間で観測したとの主張ではない。正弦の最小周期条件とRiemann積分を記述に残し、有限診断を全実数の解析定理の証明にしない。',
 '仮定の74役割は候補の外側で固定する。力履歴や代表場は記号的な物理設定であり、数値測定済み又は求める六実数を既に知っていることではない。六つの数は圧力、一つの方向の三成分、周期数、強度で四量を表す。後続の具体的な数式提示やその導出、特にM0376の扱いはこの質問提示へ混入させない。',
 'eisufは既存eisse/eistsと同じ一般的な条件付き質問提示を74設定・六実数候補の型へ特殊化する。具体的な文の意味は仮定・候補・質問・照応・帰属の合成に置き、光や鏡の性質を原始関係へ格納しない。',
]

def returned():
    V,speed=v('light'),k('be',v('speed'));beta=k('soy',V,speed);r=k('shv',speed,k('sjd',V));a=k('be',v('ax'))
    rate=k('sdn2',V,speed,v('rate'),a)
    direction=[k('sdo2',V,speed,a),k('sdp2',V,speed,a,v('ay')),k('sdp2',V,speed,a,v('az'))]
    # Reflect in k first, then transform both E and H with velocity -v.
    e=[v('ex'),k('be',v('ey')),k('be',v('ez'))];h=[k('be',v('hx')),v('hy'),v('hz')]
    electric=[e[0],k('s6d',beta,r,e[1],h[2]),k('s6e',beta,r,e[2],h[1])]
    magnetic=[h[0],k('s6e',beta,r,h[1],e[2]),k('s6d',beta,r,h[2],e[1])]
    return rate,direction,electric,magnetic

def selected():
    numeric,inc,ref,front,edge,rates=models()
    row={n:v(n) for n,t in SETTING};ret=[numeric[n] if n in numeric else v(n) for n,t in RETURN]
    lo=k('ekrr',v('light'),v('speed'),v('forcelower'));ku=k('bd',v('forcelower'),v('newperiod'));hi=k('ekrr',v('light'),v('speed'),ku)
    force=row|dict(process=v('interaction'),frame=k('ra'),scope=k('eistk'),lower=lo,upper=hi)
    return numeric,front,edge,ret,ku,force

def definitions():
    text=''.join('r '+n+'['+' '.join(t for _,t in fs)+'] '+('c' if fs else 'a')+'.\n' for n,(fs,_) in PRIMITIVES.items())
    zero=k('bb','n p a b');rate,direction,electric,magnetic=returned();axes=('yn','yo','yp')
    text+=define('ekrk',RETURN,rate,R)
    for name,values in [('ekrl',direction),('ekrm',electric),('ekrn',magnetic)]:text+=define(name,RETURN,k('ekbe',*values),POINT)
    get=lambda name,ret:[app(k(name,*ret),k(axis)) for axis in axes]
    for name,field in [('ekro','ekrm'),('ekrp','ekrn')]:text+=define(name,WAVE,k('sdx2',v('profile'),v('light'),k('ekrk',*args(RETURN)),*get('ekrl',args(RETURN)),*get(field,args(RETURN))),FIELD)
    text+=define('ekrq',RETURN+[('cycle',R)],k('shv',v('cycle'),k('sjd',k('ekrk',*args(RETURN)))),R)
    text+=define('ekrr',[(n,R) for n in ('light','speed','tau')],k('shv',k('soy',v('light'),v('speed')),v('tau')),R)
    covered=both(*(k('ba',v(n)) for n,t in COORDS),k('lg',v('lower'),v('upper'),v('time')),k('ekqx',*args(BOUNDS),*args(COORDS)))
    text+=define('ekrs',COVER,both(k('ba',v('lower')),k('ba',v('upper')),k('bg',v('lower'),v('upper')),k('ekqw',*args(BOUNDS)),quantified('f',COORDS,op('y',covered,app(v('region'),*args(COORDS))))))
    numeric,front,edge,ret,ku,force=selected();shared={n:v(n) for n,t in SETTING}|dict(frame=k('ra'),scope=k('eistk'),coefficient=v('labcoefficient'))
    inc=[k('sdx2',v('sine'),v('light'),v('rate'),v('ax'),v('ay'),v('az'),*[v(n) for n in fs]) for fs in [('ex','ey','ez'),('hx','hy','hz')]]
    ref=[k(n,v('sine'),*ret) for n in ('ekro','ekrp')]
    physical=shared|dict(incidentE=inc[0],incidentH=inc[1],reflectedE=ref[0],reflectedH=ref[1],region=k('s6m',v('light'),k('be',v('speed')),front))
    fixed=[op('e',v(n),k(symbol)) for n,symbol in [('frame','ra'),('scope','eisrx')]]+[k('sca',v('light'),k('tc'))]
    text+=define('ekrt',SETTING,both(*fixed,k('ekrf',*args(PRIOR_SETTING)),k('ekrs',edge,v('forcelower'),ku,*args(BOUNDS)),k('ekq4',*[force[n] for n,t in FORCE_SETTING]),k('eiste',*[shared[n] for n,t in COEFFICIENT]),k('eisuc',*[physical[n] for n,t in INTERACTION])))
    period=k('ekrq',*ret,v('cycle'));rate=k('ekrk',*ret);direction=get('ekrl',ret);e=get('ekrm',ret);h=get('ekrn',ret)
    pressure=k('ekq3',v('force'),force['lower'],force['upper'],*args(BOUNDS),v('pressure'))
    dirs=both(*(k('ba',v(n)) for n in ('nx','ny','nz')),*(k('sca',v(n),d) for n,d in zip(('nx','ny','nz'),direction)))
    frequency=k('ekc7',*args(HARMONIC),rate,zero,period,v('receivedfrequency'))
    intensity=k('ekjh',v('labcoefficient'),*direction,*e,*h,k('ekc5',v('sine'),rate,zero),zero,period,k('shv',period,v('intensity')),v('intensity'))
    text+=define('ekru',SETTING+ANSWERS,both(k('ekrt',*args(SETTING)),pressure,dirs,frequency,intensity))
    text+=define('ekrv',SETTING,'j v[i['+' '.join(n+' '+t for n,t in ANSWERS)+']['+k('ekru',*args(SETTING+ANSWERS))+']]',QUESTION)
    node=k('eisug');author=k('rd');p=v('point')
    text+=content('ekrw',k('eisuf',node,author,k('eisue'),quote('ekrg'),'r[p ekrt]','r[p ekrv]',k('eistk'),p))
    text+='d ekrx[] f[j s[k ekrw[]]].\n'
    text+=define('ekry',[],both(k('eir3',node,author,k('eirf'),quote('ekrx'),k('ri')),k('ue',k('eisue'),node,k('ri')),op('u',op('e',k('eisue'),node))))
    return text

@lru_cache(None)
def build():
    old=parse(read(PARENT));assert len(old['statements'])==INDEX
    assert not (set(MEANINGS)|set(PRIMITIVES))&{d['name'] for d in old['declarations']}
    doc=deepcopy(old);doc['statements']=[];doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']+[dict(kind='assert',body=dict(kind='call',symbol='ekry',arguments=[]))]
    added=doc['declarations'][len(old['declarations']):]
    primitives={d['name']:dict(parameters=d['parameters'],result=d['result'],arguments=[n for n,t in PRIMITIVES[d['name']][0]],meaning_ja=PRIMITIVES[d['name']][1]) for d in added if d['kind']=='primitive'}
    basis=dict(status='same_reflection_four_quantity_question_in_resting_frame',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives=primitives,definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=[INDEX]).document
    ann=json.loads(read('data/perfect-mirror-setting-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
