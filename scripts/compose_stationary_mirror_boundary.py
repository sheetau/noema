"""Compose a six-component stationary ideal-conductor reflection boundary."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_energy_frequency_law import ROOT,read
from scripts.compose_field_equations import POINT,TAU,FIELD
from scripts.compose_wave_cycle_frequency import HARMONIC
from scripts.compose_material_relative_frame import define,args
from scripts.compose_doppler_infinity import quantified
from scripts.compose_limits import R,F,v,call as k,app,op,both

PARENT='examples/v014/einstein-energy-frequency-law.noema';PARENT_BASIS='data/energy-frequency-law-basis-v1.json'
FULL='examples/v014/einstein-stationary-mirror-boundary.noema';CORE='examples/v014/stationary-mirror-boundary-core.noema'
BASIS='data/stationary-mirror-boundary-basis-v1.json';ANNOTATIONS='data/stationary-mirror-boundary-identifiers-v1.json'
DIRECTION=[(n,R) for n in ('ax','ay','az')]
ELECTRIC=[(n,R) for n in ('ex','ey','ez')];MAGNETIC=[(n,R) for n in ('hx','hy','hz')]
GEOMETRY=DIRECTION+ELECTRIC+MAGNETIC
PAIR=GEOMETRY+[('ref'+n,t) for n,t in GEOMETRY]
PHASE=[('light',R),('rate',R)]+DIRECTION
WAVE=[('profile',F),('light',R),('rate',R)]+GEOMETRY
COORDS=[(n,R) for n in ('x','y','z','time')]
FLUXPOINT=WAVE+[('coefficient',R)]+COORDS
HARMONIC_MODEL=HARMONIC+[('light',R),('rate',R)]+GEOMETRY+[(n,R) for n in ('period','frequency','coefficient')]
AXES=('yn','yo','yp')
MEANINGS={
 'ekqb':'平面x=0に関する方向の反転(-ax,ay,az)を三軸ベクトルとして返す。接線方向を反転せず、第四役割等への拡張は零。',
 'ekqc':'静止した完全導体平面の候補反射電場の係数(Ex,-Ey,-Ez)を返す。偏光の接線成分の符号を保持し、振幅ノルムだけへの縮約を避ける。',
 'ekqd':'同じ候補反射磁場の係数(-Hx,Hy,Hz)を返す。電場と同じ符号規則を流用しない。',
 'ekqe':'同じ九入力と九出力について、全値の妥当性、入射条件ekqf、三つの反転構成の全成分一致を要求する。出力を枝ごとに別の波から選ばない。',
 'ekqf':'単位方向、横電場とH=n×Eのseaj、正の法線方向ax及び正の電場ノルム二乗を持つ入射係数。x<0側からx=0へ到達する非零の波の配置に使い、接線のみの伝播を入射としない。',
 'ekqg':'同じ十八係数について反射側のseaj、負の反射法線、電場・磁場の各ノルム二乗の保存を要求する帰結条件。ekqeの前提には含めず、候補構成からの整合を別に検査する。',
 'ekqh':'同じVと位相率を保ち、法線方向だけを反転した四座標位相。境界の全時刻・全接線位置で入射位相と一致する候補。',
 'ekqi':'同じ波形・位相率・反転方向及び(Ex,-Ey,-Ez)から反射電場の全三成分関数を構成する。位相のずれを振幅の絶対値へ隠さない。',
 'ekqj':'ekqiと同じ波形・位相を用い、(-Hx,Hy,Hz)から反射磁場の全三成分関数を構成する。',
 'ekqk':'同じ有効な境界点x=0、正のVと位相率について、入射・反射位相の一致、全十二場成分の妥当性、合計電場の二接線成分0、合計磁場の法線成分0を結ぶ。法線電場と接線磁場まで零とは要求しない。',
 'ekql':'同じ一つの波形・V・位相率・九係数のまま、x=0の全有効四座標でekqkを要求する。境界の一標本だけで完全な境界条件を認定しない。',
 'ekqm':'同じ境界点・正の係数について、入射と反射の各κ(E×H)の法線流が逆符号、二接線流が同符号であることを全三軸で照合する。合成場の外積ではなく二つの進行波の流を比較し、面積時間あたりの仕事への物理的同定は別に必要。',
 'ekqn':'同じ正弦・余弦・pi・一周期、位相率、時間周期と周期数のekc7、正のVと流換算係数、入射係数ekqf、全境界のekql及びekqmを結ぶ数学的な理想鏡モデル。反射波は同じ位相率と波形から構成するので周期の規約を選び直さない。',
}
LIMITS=[
 'u0215の完全反射面を接続するための依存群。現在の394主張を全て保存し、原始関係・著者主張・原文対応範囲・全単位判断を追加しない。物理的な鏡・相互作用と先行の同じ平面波への対応、仮定の提示、四量の問いは未完。',
 '採用する候補は静止した完全導体の平滑な無限平面という理想化である。完全反射という語だけから任意の反射体の偏光位相がこの符号規則を持つとは推論しない。後の本文接続でこの限定を明示して初めて解釈として使える。境界電荷・表面電流の微視的機構、材料の実在、全周波数帯の物性を証明したとはしない。',
 '現在は任意の校正された直交座標のx=0を扱う数学的構成。本文のξ=0とはkの座標面を意味し、Kのx=0へ取り違えない。物理的な面とk、Kでのx=v*t、波の入射・反射所属及び範囲は次の共有設定で指定する。',
 '入射側を負の法線側としax>0、非零の横波を要求する。垂直入射と任意の二接線成分、二偏光及びその重ね合わせを許し、伝播が平面に平行な場合や零波を到達する光と認定しない。',
 '境界でE接線の合計とH法線の合計を零とする。法線電場・接線磁場は一般に残る。二つの進行波の法線エネルギー流は相殺し、接線流は一般に残る。これだけで透過場の不在、物理的吸収0、力・圧力又は運動する鏡の仕事を定義したとはしない。',
 '正弦・余弦・piと周期の全実数条件は既存ekc7を使用する。位相率と周期数を同一値にせず、固定点の空間的位相差があっても同じ時間率を持つ。有限検査の有理数値波形は正弦と称しない。',
 '数式の有限診断、全有理数上の多項式補題、全実数を量化する定義、物理的解釈及び原文同義性の判断を区別する。未知の演算又は全関数域を有限検査で成功としない。後続の反射光の答えや原刊の式の不整合はここで改訂しない。',
]

def reflected():
    return [k('be',v('ax')),v('ay'),v('az'),v('ex'),k('be',v('ey')),k('be',v('ez')),k('be',v('hx')),v('hy'),v('hz')]

def definitions():
    zero=k('bb','n p a b');positive=lambda x:both(k('ba',x),k('bg',zero,x))
    ref=reflected();text=''
    for name,fields,values in [('ekqb',DIRECTION,ref[:3]),('ekqc',ELECTRIC,ref[3:6]),('ekqd',MAGNETIC,ref[6:])]:
        text+=define(name,fields,k('ekbe',*values),POINT)
    checks=[]
    for name,fields,outputs in [('ekqb',DIRECTION,PAIR[9:12]),('ekqc',ELECTRIC,PAIR[12:15]),('ekqd',MAGNETIC,PAIR[15:18])]:
        checks += [k('sca',v(n),app(k(name,*args(fields)),k(axis))) for (n,t),axis in zip(outputs,AXES)]
    text+=define('ekqf',GEOMETRY,both(k('seaj',*args(GEOMETRY)),positive(v('ax')),positive(k('seag',*args(ELECTRIC)))))
    text+=define('ekqe',PAIR,both(*(k('ba',v(n)) for n,t in PAIR),k('ekqf',*args(GEOMETRY)),*checks))
    text+=define('ekqg',PAIR,both(k('seaj',*args(PAIR[9:])),k('bg',v('refax'),zero),*(k('sca',k('seag',*[v('ref'+n) for n,t in fs]),k('seag',*args(fs))) for fs in (ELECTRIC,MAGNETIC))))
    text+=define('ekqh',PHASE,k('ekbf',v('light'),v('rate'),*ref[:3]),TAU)
    for name,values in [('ekqi',ref[3:6]),('ekqj',ref[6:])]:
        text+=define(name,WAVE,k('sdx2',v('profile'),v('light'),v('rate'),*ref[:3],*values),FIELD)
    coords=args(COORDS);oldphase=app(k('ekbf',*args(PHASE)),*coords);newphase=app(k('ekqh',*args(PHASE)),*coords)
    oldfields=[k('sdx2',v('profile'),*args(PHASE),*args(fs)) for fs in (ELECTRIC,MAGNETIC)]
    newfields=[k(n,*args(WAVE)) for n in ('ekqi','ekqj')]
    fields=[[app(app(field,k(axis)),*coords) for axis in AXES] for field in oldfields+newfields]
    cancellations=[k('sca',k('bd',fields[0][i],fields[2][i]),zero) for i in (1,2)]+[k('sca',k('bd',fields[1][0],fields[3][0]),zero)]
    text+=define('ekqk',WAVE+COORDS,both(k('sejm',*coords),positive(v('light')),positive(v('rate')),*(k('ba',x) for x in [oldphase,newphase]+sum(fields,[])),k('sca',oldphase,newphase),*cancellations))
    allpoints=lambda body:quantified('f',COORDS,op('y',k('sejm',*coords),body))
    text+=define('ekql',WAVE,allpoints(k('ekqk',*args(WAVE),*coords)))
    unit=k('bb','n p b b');basis=((unit,zero,zero),(zero,unit,zero),(zero,zero,unit));flow=[]
    for i,axis in enumerate(basis):
        incoming=k('ekjf',v('coefficient'),*axis,*fields[0],*fields[1]);outgoing=k('ekjf',v('coefficient'),*axis,*fields[2],*fields[3])
        flow.append(k('sca',outgoing,k('be',incoming) if i==0 else incoming))
    text+=define('ekqm',FLUXPOINT,both(k('ekqk',*args(WAVE),*coords),positive(v('coefficient')),*flow))
    wave=[v('sine') if n=='profile' else v(n) for n,t in WAVE]
    text+=define('ekqn',HARMONIC_MODEL,both(positive(v('light')),positive(v('coefficient')),k('ekqf',*args(GEOMETRY)),k('ekc7',*args(HARMONIC),v('rate'),zero,v('period'),v('frequency')),k('ekql',*wave),allpoints(k('ekqm',*wave,v('coefficient'),*coords))))
    return text

def build():
    old=parse(read(PARENT));assert len(old['statements'])==394
    assert not set(MEANINGS)&{d['name'] for d in old['declarations']}
    doc=deepcopy(old);doc['statements']=[];doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']
    added=doc['declarations'][len(old['declarations']):]
    basis=dict(status='stationary_ideal_conductor_six_component_boundary_dependencies',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives={},definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=[]).document
    ann=json.loads(read('data/energy-frequency-law-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
