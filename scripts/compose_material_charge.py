"""Relate an affine material slice, its volume factor and charge density."""
from copy import deepcopy
import json

from noema.extraction import extract_document,extract_basis
from noema.grammar import parse,format_graph
from noema.meaning_basis import audit_basis
from scripts.compose_origin_clock import ROOT,definition,v
from scripts.compose_limits import call as k,app,op,both
from scripts.compose_situated_criticism import params,args
from scripts.compose_density_boost import FLOW,CUT,FRAMES

PARENT='examples/v014/einstein-density-boost.noema'
COORD='light speed beta ux uy uz ax ay az time tau x y z xi eta zeta'
JAC='light speed beta ux uy uz stretch sheary shearz'
CELL=FLOW+' stretch sheary shearz volume newvolume charge newcharge'
ASSIGN='h[a a a '+CUT+' '+CUT+' '+CUT+' d] c'
PAIRING='h[a a a a a d] c'
INPUTS=[(n,'a') for n in ('matter','oldframe','newframe','oldslice','newslice')]+[('context','d')]+[(n,CUT) for n in CELL.split()]+[
    ('assigned',ASSIGN),('paired',PAIRING),('frames',FRAMES)]
ROOTS=['senc','send','sene','senf','seng','senh','seni']


def definitions(real=False):
    coordinate,jacobian,cell=('senf','seng','senh') if real else ('senc','send','sene')
    sort=CUT if real else 'b'
    zero=k('bb','n p a b') if real else 'n p a b'
    mul=lambda a,b:k('shv' if real else 'ad',a,b)
    add=lambda a,b:k('bd' if real else 'ab',a,b)
    sub=lambda a,b:k('bf',a,b) if real else add(a,k('ac',b))
    eq=lambda a,b:k('sca',a,b) if real else op('e',a,b)
    lt=lambda a,b:k('bg' if real else 'aa',a,b)
    valid=lambda names:[k('ba',v(n)) for n in names.split()] if real else []
    V,s,beta,ux,uy,uz=map(v,('light','speed','beta','ux','uy','uz'))
    square=mul(V,V);D=sub(square,mul(s,ux))
    normal=k('srd' if real else 'sra',V,s,beta)
    coords=[eq(v(axis),add(v(label),mul(v(velocity),v('time')))) for axis,label,velocity in (
        ('x','ax','ux'),('y','ay','uy'),('z','az','uz'))]
    coords += [eq(v('xi'),mul(beta,sub(v('x'),mul(s,v('time'))))),eq(v('eta'),v('y')),eq(v('zeta'),v('z')),
        eq(mul(square,v('tau')),mul(beta,sub(mul(square,v('time')),mul(s,v('x')))))]
    text=definition(coordinate,params([(n,sort) for n in COORD.split()]),both(*valid(COORD),normal,lt(zero,D),*coords))
    jac=[eq(mul(mul(beta,D),v('stretch')),square),
         eq(mul(D,v('sheary')),mul(s,uy)),eq(mul(D,v('shearz')),mul(s,uz))]
    text+=definition(jacobian,params([(n,sort) for n in JAC.split()]),both(*valid(JAC),normal,lt(zero,D),*jac))
    text+=definition(cell,params([(n,sort) for n in CELL.split()]),both(*valid(CELL),
        k('semt' if real else 'semp',*map(v,FLOW.split())),k(jacobian,*map(v,JAC.split())),
        lt(zero,v('volume')),lt(zero,v('newvolume')),
        eq(v('newvolume'),mul(v('stretch'),v('volume'))),
        eq(v('charge'),mul(v('density'),v('volume'))),eq(v('newcharge'),mul(v('newdensity'),v('newvolume')))))
    return text


MEANINGS={
    'senc':'同じ物質点のラベル(aₓ,aᵧ,a_z)を使い、x=aₓ+uₓt等の等速並進と、標準配置のローレンツ座標変換を同時に満たす二系の点を述べる。D=V²−v*uₓ>0を明示し、旧時刻tと新時刻τを同一にしない。',
    'send':'同じ正のDと正のbetaについて、βD*stretch=V²、D*sheary=v*uᵧ、D*shearz=v*u_zを満たす。同じ新時刻の物質ラベルから位置への線形部分を、三角行列[[stretch,0,0],[sheary,1,0],[shearz,0,1]]の三係数で指定する。',
    'sene':'同じ三速度・密度の変換semp、同時刻切片の係数send、正の二体積とnewvolume=stretch*volume、両側の総量=density*volumeを結ぶ。二つの総量の等値は前提に含めない。負・零の密度と電荷を許す。',
    'senf':'sencの物質点・座標対応を有効な実切断で表す。三速度はこの構成の期間を通じて一定とする解釈であり、加速運動全体を一つの並進として扱わない。',
    'seng':'sendの同時刻切片の三係数を有効な実切断で表す。伸縮係数は切断の数値等値で指定する。一般の三次元測度の変換定理をこの式だけで証明したとは扱わない。',
    'senh':'seneの密度・体積・電荷を有効な実切断で結ぶ。密度が一様で、ラベルで追う領域に対して指定の体積変換が適用できる場合の構成。非一様密度の積分や任意に変形する物体の境界流束は別途必要。',
    'seni':'同じ物質領域と二系の二切片を、明示された対応関係と基準系の配置へ結び、それぞれに割り当てた密度・体積・総電荷の値へsenhを適用する。二切片が同じ座標時刻や同じ出来事であることを補わない。',
}
LIMITS=[
    '物質ラベルは旧系のt=0での位置を基準にした等速並進のラベルである。新系の同時刻τを固定すると、物質点ごとに旧時刻tが異なる。旧系の一つの時刻面をそのまま新系の同時刻体積と同一視しない。',
    '三角行列の行列式はstretchであり、D>0と正のbetaにより正となる。数式での体積変換は同じラベル領域への幾何学的な条件として与える。一般の測度論・積分変数変換の機械的な証明は未完。',
    '密度と体積の積は同じ系で密度が一様な領域の総量である。単一流の分解を使い、電荷密度が零なら総量も零だが、速度を零と定めない。複数種の電流や非一様密度を一様な一領域へ無断でまとめない。',
    '実数版の全ての演算法則の機械的証明は未完である。有理数の恒等関係と、有理値を実切断へ埋めた有限例を区別して検査する。',
    '任意の加速・変形をする物体、動く境界を横切る電荷、連続の式から一般の積分保存則を導くことは未完。この一様並進の結果だけで原文の任意の運動を証明し終えたとしない。',
]


def source_composed():
    doc=parse((ROOT/PARENT).read_text(encoding='utf-8'))
    basis=deepcopy(json.loads((ROOT/'data/einstein-density-boost-basis-v1.json').read_text(encoding='utf-8')))
    statements,doc['statements']=doc['statements'],[]
    conditions=[app(v('frames'),v('oldframe'),v('newframe'),v('speed'),v('context')),
        app(v('paired'),*map(v,('matter','oldframe','newframe','oldslice','newslice','context')))]
    for prefix,density,volume,charge in (('old','density','volume','charge'),('new','newdensity','newvolume','newcharge')):
        conditions.append(app(v('assigned'),v('matter'),v(prefix+'frame'),v(prefix+'slice'),v(density),v(volume),v(charge),v('context')))
    conditions.append(k('senh',*map(v,CELL.split())))
    text=definitions()+definitions(True)+definition('seni',params(INPUTS),both(*conditions))
    doc=parse(format_graph(doc,'compact')+text);doc['statements']=statements
    basis.update(version='einstein-material-charge-basis-v1',document='examples/v014/einstein-material-charge.noema')
    basis['definitions'].update(MEANINGS);basis['unresolved']+=LIMITS+[
        'assignedは同じ物質領域・系・切片・文脈に、共通の規格で密度・体積・総電荷を割り当てる関係引数。pairedは一様並進で追う同じラベル領域の二つの同時刻切片への対応を指定する。物理的な対応を数値一致だけから補わない。',
        'u0238の電荷の不変性への前段として、密度と体積の相殺を操作的な条件として部分記述する。時間を通じた不変性には各時点での対応と、物体に随伴する側の総電荷の一定性が別に必要である。',
        'πを用いる電荷密度の換算、単位の実現、体積測定、同じ物体の追跡、任意運動の保存則と原文全文の意味一致は未完。既存174件の本文主張を保存し、新しい原始概念・著者主張を追加しない。',
    ]
    audit_basis(doc,basis)
    return format_graph(doc,'compact')+'\n',basis


def projected(roots,stem):
    text,basis=source_composed();doc=parse(text)
    selected=extract_document(doc,roots=roots,statement_indices=[])
    result=extract_basis(doc,basis,selected,version=stem+'-basis-v1',document_path='examples/v014/'+stem+'.noema')
    return format_graph(selected.document,'compact')+'\n',result


def generic_composed():return projected(ROOTS[:3],'material-charge')
def core_composed():return projected(ROOTS,'material-charge-core')
BUILDERS=((generic_composed,'material-charge'),(source_composed,'einstein-material-charge'),(core_composed,'material-charge-core'))


def main():
    for builder,stem in BUILDERS:
        text,basis=builder()
        for name,body in ((basis['document'],text),('data/'+stem+'-basis-v1.json',json.dumps(basis,ensure_ascii=False,indent=2)+'\n')):
            path=ROOT/name
            if path.exists():
                if path.read_text(encoding='utf-8')!=body:raise ValueError('Stored material charge differs: '+name)
            else:
                with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(body)
        print(stem,len(text),'characters')


if __name__=='__main__':main()
