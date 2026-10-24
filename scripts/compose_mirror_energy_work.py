"""Bind moving-boundary radiation averages and mechanical work to one mirror patch."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_limits import ROOT,R,F,v,call as k,app,op,both
from scripts.compose_material_relative_frame import define,args
from scripts.compose_field_equations import TAU
from scripts.compose_observed_intensity import MODEL,VECTOR
from scripts.compose_radiative_density import SCALAR,DENSITY_MODEL
from scripts.compose_mirror_surface_pressure import BOUNDS,FORCE,AVERAGE as PRESSURE
from scripts.compose_reflected_light_inquiry import SETTING as FORCE_SETTING,selected
from scripts.compose_reflected_return_quantities import SETTING as QUANTITIES,returned_args
from scripts.compose_doppler_infinity import quantified

def read(path):return (ROOT/path).read_text(encoding='utf-8')
PARENT='examples/v014/einstein-reflected-return-quantities.noema';PARENT_BASIS='data/reflected-return-quantities-basis-v1.json'
FULL='examples/v014/einstein-mirror-energy-work.noema';CORE='examples/v014/mirror-energy-work-core.noema'
BASIS='data/mirror-energy-work-basis-v1.json';ANNOTATIONS='data/mirror-energy-work-identifiers-v1.json'
COORDS=[(n,R) for n in ('x','y','z','time')]
MOVING=SCALAR+[('speed',R)]
TRACE=[('flux',TAU)]+[(n,R) for n in ('speed','y','z')]
MEAN=TRACE+[(n,R) for n in ('lower','upper','mean')]
PATCH_MEAN=[('flux',TAU),('speed',R)]+BOUNDS+[(n,R) for n in ('lower','upper','mean')]
WORK=[('force',FORCE),('speed',R),('lower',R),('upper',R)]+BOUNDS+[('work',R)]
SETTING=QUANTITIES+[(n,t) for n,t in FORCE_SETTING if n not in dict(QUANTITIES)]
OUTPUTS=[(n,R) for n in ('incoming','outgoing','pressure','work')]
TOTAL=SETTING+OUTPUTS
PRINTED=[(n,R) for n in ('pi','amplitude','light','speed','anglecos')]
MEANINGS={
 'ekto':'同じ波のエネルギー流ekkaと密度ekkyから、+x方向へ速度vで動く面に相対的な+x流Jx−v*uを構成する。境界速度の場ekk7を同じ四座標へ適用し、鏡へ向かう成分と静止面のJxを区別する。',
 'ektp':'同じ四座標スカラー流fluxを、同じ鏡のK軌跡x=v*tと固定した接線座標y,zへ引き戻した時間関数。xだけ動かして時刻又は横位置を別の出来事へ替えない。',
 'ektq':'同じ正長のK時間区間でektpをRiemann積分し、その値をduration*meanへ結ぶ点ごとの時間平均。平均値は符号付きで、全体の面積をまだ掛けない。',
 'ektr':'同じ正面積矩形の全有効なy,zについて、範囲内なら同じflux・速度・K時間区間・meanのektqを要求する。一地点や角だけで一様な面平均を認定せず、実数全域の条件を保持する。',
 'ekts':'同じ98設定で逆変換量eks3と面部分・一周期・力モデルekrtを結び、Kの原文単位校正ekk2、同じ入射波と同じ反射波の密度及び流モデルを同じ局所領域へ採用する。物理的モデルの追加採用であり、既存の場の誤差上限だけから密度や流の十分性を推論しない。',
 'ektt':'同じforceの+x成分へ同じ速度を掛け、全K時間での機械的仕事率v*Fx(t)を返す。面がx方向へ並進するので接線力はこの仕事に寄与しないが、接線力自体を零に制限しない。',
 'ektu':'同じ力モデルのekttを同じK区間で積分し、その値をwork*area*durationへ結ぶ。workは単位面積時間あたりの符号付き機械的仕事であり、圧力の定義又はエネルギー差を前提にしない。',
 'ektv':'原文M0377のA²/(8*pi)*(V*cosφ−v)を既存平均密度ekleから構成する。時間平均密度と面への相対法線速度の積であり、波の進行方向の強度とは異なる。',
 'ektw':'原文M0378のA‴²/(8*pi)*(−V*cosφ‴+v)を構成する。戻る量を正に取る向きと三重プライム全体の平方を保持する。',
 'ektx':'同じ102設定で物理設定ekts、全矩形の同じ時間平均入出流、同じ力の平均圧力ekq3、機械的仕事積分ektuを共有する。仕事=入出差、仕事=P*v及び圧力の閉じた式は成立条件に加えない。',
 'ekty':'同じ設定のincomingとoutgoingを、それぞれ原文M0377とM0378の表示右辺へ等置する帰結候補。波の余弦にはKの旧角と戻したK角を用い、kの結線角へ取り違えない。',
 'ektz':'同じ有効な入出流と仕事についてwork=incoming−outgoingを述べる収支の帰結候補。物理モデルの四経路帰属又はエネルギー原理の著者参照を、この数式だけで代替しない。',
 'ekt2':'同じ有効な圧力・速度・仕事についてwork=pressure*speedを述べる帰結候補。零速度でも定義され、仕事率から圧力を除算して定めない。',
 'ekt3':'原文M0381の2*A²/(8*pi)*(cosφ−v/V)²/(1−(v/V)²)という値。分子全体の平方と分母の平方範囲を保持する。',
 'ekt4':'同じ設定の圧力が原文M0381のekt3に等しいという帰結候補。仕事の式だけから速度零で導けるとはしない。',
}
LIMITS=[
 'u0222–u0223の本文統合に必要な、動く鏡面へのエネルギー流と機械的仕事の依存群。既存402主張・全単位判断・原文対応範囲を保存する。今回だけで原文四文の著者提示、offenbar、エネルギー原理、Pの命名、so erhält man及び表示まで記述したとはしない。',
 '同じ理想鏡と代表平面波、同じ物質的矩形、同じ力の相互作用を使う。kの一周期に対応する鏡上のK時間区間β*[tau0,tau0+T′]を共有する。K静止点での反射周期をこの区間へ代用しない。全矩形と全区間が局所モデルの領域にある条件はekrtで保持する。',
 '原文の単位面積・単位時間あたりのエネルギーは、同じ面部分の各点で一周期を時間平均した一様な面エネルギー流密度と読む。全接線位置の積分条件を明示し、瞬間の正弦場が全矩形で一様であるとの仮定を追加しない。同じ一様平均なので面積倍により総量へ接続できる。',
 '密度と流の物理的採用はそれぞれekkz/ekkbで明示する。単位校正は同じKの力・長さ時間・場・エネルギー単位と4*pi*κ=Vへ結ぶ。原文のA²/(8*pi)を任意の数値係数の命名にしない。実際の場と代表場の誤差零を補わない。',
 '面に相対的な入出流はJx−v*uとその反転であり、Vcosφとvを混同しない。Kで戻る光のx成分が正でも、鏡に対する戻り速度v−Vcosφ‴は正になり得る。仕事と圧力は同じ力の区間積分を使い、熱や蓄積といった別経路をエネルギー差から勝手に零とすることはまだ行わない。',
 'workはFx*vのK時間積分を同じ面積と時間幅で割った符号付き値。forceは支持力を含む合力でなく同じ光の相互作用の寄与である。eisteによりエネルギー単位を力と変位の積に整合させる。v=0で仕事が零でも、圧力は独立な力平均として非零でよい。',
 '原刊の周波数最右辺の分母の不一致と、kの角の字義的な結線読解を保存する。入出エネルギー式では同じKでの振幅とKの角を用い、周波数の不一致を修正するための条件を追加しない。',
 '全実数の面上の量化と全区間のRiemann積分を有限標本へ縮めない。多項式波形による検査は引数・軌跡・積分値の結合診断であり正弦波の代用ではない。物理的なエネルギー原理、零速度の圧力の導出、本文の全単位判断は後続の責務である。',
]

def physical_rows():
    numeric,front,edge,ret,ku,force=selected();region=k('s6m',v('light'),k('be',v('speed')),front)
    get=lambda name:[app(k(name,*ret),k(a)) for a in ('yn','yo','yp')]
    oldamps=[v(n) for n in ('ex','ey','ez','hx','hy','hz')]
    oldphase=k('ekbf',v('light'),v('rate'),v('ax'),v('ay'),v('az'))
    newphase=k('ekbf',v('light'),k('ekrk',*ret),*get('ekrl'));newamps=get('ekrm')+get('ekrn')
    shared={n:v(n) for n,t in SETTING}|dict(frame=k('ra'),scope=k('eistk'),coefficient=v('labcoefficient'),region=region)
    rows=[]
    for wave,process,phase,amps in [(v('wave'),v('process'),oldphase,oldamps),(v('reflectedwave'),v('reflectedprocess'),newphase,newamps)]:
        rows.append(shared|dict(wave=wave,process=process,phase=phase,**dict(zip(('ex','ey','ez','hx','hy','hz'),amps))))
    return rows,force

def definitions():
    zero=k('bb','n p a b');one=k('bb','n p b b');two=k('bb','n p c b');mul=lambda x,y:k('shv',x,y)
    coords=args(COORDS);relative=k('ekk6',k('ekka',*args(VECTOR)),k('ekky',*args(SCALAR)),k('ekk7',v('speed'),one,zero,zero))
    text=define('ekto',MOVING,app(relative,k('yn')),TAU)
    text+=define('ektp',TRACE,'i[time '+R+']['+app(v('flux'),mul(v('speed'),v('time')),v('y'),v('z'),v('time'))+']',F)
    duration=k('bf',v('upper'),v('lower'))
    text+=define('ektq',MEAN,both(*(k('ba',v(n)) for n,t in MEAN if t==R),k('bg',v('lower'),v('upper')),k('sede',v('lower'),v('upper'),k('ektp',*args(TRACE)),mul(duration,v('mean')))))
    inside=both(k('ba',v('y')),k('ba',v('z')),k('lg',v('ylower'),v('yupper'),v('y')),k('lg',v('zlower'),v('zupper'),v('z')))
    text+=define('ektr',PATCH_MEAN,both(k('ekqw',*args(BOUNDS)),k('ba',v('lower')),k('ba',v('upper')),k('bg',v('lower'),v('upper')),quantified('f',[(n,R) for n in ('y','z')],op('y',inside,k('ektq',*args(MEAN))))))
    rows,force=physical_rows()
    models=[k(symbol,*[row[n] for n,t in fields]) for row in rows for symbol,fields in [('ekkb',MODEL),('ekkz',DENSITY_MODEL)]]
    text+=define('ekts',SETTING,both(k('eks3',*args(QUANTITIES)),k('ekrt',*args(FORCE_SETTING)),k('ekk2',v('labcoefficient'),v('light'),v('pi')),*models))
    text+=define('ektt',[('force',FORCE),('speed',R)],'i[time '+R+']['+mul(v('speed'),app(app(v('force'),v('time')),k('yn')))+']',F)
    text+=define('ektu',WORK,both(*(k('ba',v(n)) for n,t in WORK if t==R),k('bg',v('lower'),v('upper')),k('ekqw',*args(BOUNDS)),k('sede',v('lower'),v('upper'),k('ektt',v('force'),v('speed')),mul(v('work'),mul(k('ekqv',*args(BOUNDS)),duration)))))
    density=k('ekle',v('pi'),v('amplitude'));longitudinal=mul(v('light'),v('anglecos'))
    text+=define('ektv',PRINTED,mul(density,k('bf',longitudinal,v('speed'))),R)
    text+=define('ektw',PRINTED,mul(density,k('bf',v('speed'),longitudinal)),R)
    flows=[k('ekto',*[row[n] for n,t in MOVING]) for row in rows]
    flows[1]='i['+' '.join(n+' '+t for n,t in COORDS)+']['+k('be',app(flows[1],*coords))+']'
    means=[k('ektr',f,v('speed'),*args(BOUNDS),force['lower'],force['upper'],v(name)) for f,name in zip(flows,('incoming','outgoing'))]
    pressure={n:v(n) for n,t in TOTAL}|dict(lower=force['lower'],upper=force['upper'])
    text+=define('ektx',TOTAL,both(k('ekts',*args(SETTING)),*means,k('ekq3',*[pressure[n] for n,t in PRESSURE]),k('ektu',*[pressure[n] for n,t in WORK])))
    text+=define('ekty',TOTAL,both(k('sca',v('incoming'),k('ektv',*args(PRINTED))),k('sca',v('outgoing'),k('ektw',v('pi'),v('labamplitude'),v('light'),v('speed'),v('labanglecos')))))
    text+=define('ektz',[(n,R) for n in ('incoming','outgoing','work')],both(*(k('ba',v(n)) for n in ('incoming','outgoing','work')),k('sca',v('work'),k('bf',v('incoming'),v('outgoing')))))
    text+=define('ekt2',[(n,R) for n in ('pressure','speed','work')],both(*(k('ba',v(n)) for n in ('pressure','speed','work')),k('sca',v('work'),mul(v('pressure'),v('speed')))))
    ratio=mul(v('speed'),k('sjd',v('light')));delta=k('bf',v('anglecos'),ratio);den=k('bf',one,mul(ratio,ratio))
    text+=define('ekt3',PRINTED,mul(mul(two,density),mul(mul(delta,delta),k('sjd',den))),R)
    text+=define('ekt4',TOTAL,k('sca',v('pressure'),k('ekt3',*args(PRINTED))))
    return text

@lru_cache(None)
def build():
    old=parse(read(PARENT));assert len(old['statements'])==402
    assert not set(MEANINGS)&{d['name'] for d in old['declarations']}
    doc=deepcopy(old);doc['statements']=[];doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']
    added=doc['declarations'][len(old['declarations']):]
    basis=dict(status='same_mirror_moving_flux_and_mechanical_work_dependencies',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives={},definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=[]).document
    ann=json.loads(read('data/reflected-return-quantities-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode()))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
