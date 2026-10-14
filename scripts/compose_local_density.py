"""Explain local normalized charge density through shrinking spatial balls."""
from copy import deepcopy
import json

from noema.extraction import extract_document,extract_basis
from noema.grammar import parse,format_graph
from noema.meaning_basis import audit_basis
from scripts.compose_origin_clock import ROOT,definition,v
from scripts.compose_limits import call as k,app,op,both,quant
from scripts.compose_situated_criticism import params,args
from scripts.compose_field_equations import CUT,POINT,ROLES
from scripts.compose_density_referents import ELECTRIC,FRAMES
from scripts.compose_material_velocity import DENSITY

PARENT='examples/v014/einstein-material-velocity.noema'
PROFILE='h['+CUT+'] '+CUT
BALL='h['+POINT+'] c'
MEASURE='h[a a a '+BALL+' a a '+CUT+' d] c'
UNITS='h[a a a d] c'
MEMBER='h[a a d] c'
LIMIT=[('upper',CUT),('charge',PROFILE),('volume',PROFILE),('average',PROFILE),('density',CUT)]
BOUND=[('matter','a'),('distribution','a'),('frame','a'),('event','a'),('point',POINT),('context','d'),
    ('lengthunit','a'),('timeunit','a'),('chargeunit','a'),('pi',CUT)]+LIMIT+[('measured',MEASURE),('chartunits',UNITS),('member',MEMBER)]
NORMAL=BOUND+[('normalized',CUT)]
FIXED=[('distribution','a'),('pi',CUT),('lengthunit','a'),('timeunit','a'),('chargeunit','a'),('measured',MEASURE),('chartunits',UNITS),('member',MEMBER)]
ROOTS=['seog','seoh','seoi','seoj','seok','seol','seom','seon']
ZERO=k('bb','n p a b')


def coord(point,axis):return app(point,k(axis))
def radius_domain(radius):return both(k('ba',radius),k('bg',ZERO,radius),k('bg',radius,v('upper')))
def ball(center,radius):return 'i[probe '+POINT+']['+k('seog',center,radius,v('probe'))+']'


def definitions():
    center,probe,radius=map(v,('center','probe','radius'));mul=lambda a,b:k('shv',a,b)
    distances=[k('bf',coord(probe,a),coord(center,a)) for a in ROLES[:3]]
    squares=[mul(x,x) for x in distances];distance=k('bd',k('bd',squares[0],squares[1]),squares[2])
    text=definition('seog',params([('center',POINT),('radius',CUT),('probe',POINT)]),both(
        *[k('ba',coord(p,a)) for p in (center,probe) for a in ROLES],k('ba',radius),k('bg',ZERO,radius),
        k('sca',coord(center,'zc7'),coord(probe,'zc7')),k('bg',distance,mul(radius,radius))))
    text+=definition('seoh',params([(n,CUT) for n in ('charge','volume','average')]),both(
        *[k('ba',v(n)) for n in ('charge','volume','average')],k('bg',ZERO,v('volume')),
        k('sca',v('charge'),mul(v('average'),v('volume')))))
    text+=definition('seoi',params(LIMIT[:-1]),both(k('ba',v('upper')),k('bg',ZERO,v('upper')),
        quant('f','radius',CUT,op('y',radius_domain(radius),k('seoh',*(app(v(n),radius) for n in ('charge','volume','average')))))))
    domain='i[radius '+CUT+']['+radius_domain(radius)+']'
    text+=definition('seoj',params(LIMIT),both(k('seoi',*args(LIMIT[:-1])),k('sjr',domain,v('average'),ZERO,v('density'))))
    assigned=app(v('measured'),v('distribution'),v('frame'),v('event'),ball(v('point'),radius),v('lengthunit'),v('chargeunit'),app(v('charge'),radius),v('context'))
    profiles=quant('f','radius',CUT,op('y',radius_domain(radius),both(k('sedm',radius,v('pi'),app(v('volume'),radius)),assigned)))
    text+=definition('seok',params(BOUND),both(*[k('ba',coord(v('point'),a)) for a in ROLES],k('va',v('frame')),
        k('zpb',v('matter'),v('frame'),v('event'),v('point'),v('context')),
        app(v('member'),v('matter'),v('distribution'),v('context')),
        app(v('chartunits'),v('frame'),v('lengthunit'),v('timeunit'),v('context')),k('sedi',v('pi')),
        k('seoj',*args(LIMIT)),profiles))
    text+=definition('seol',params(NORMAL),both(k('seok',*args(BOUND)),k('seml',v('pi'),v('normalized'),v('density'))))
    local=[('matter','a'),('frame','a'),('event','a'),('normalized',CUT),('context','d')]
    witness=k('seol',*args(NORMAL))
    for name,sort in reversed([('point',POINT)]+LIMIT):witness=quant('g',name,sort,witness)
    text+=definition('seom',params(FIXED),'i['+params(local)+']['+witness+']',DENSITY)
    source=[('light',CUT)]+FIXED+[('electricassigned',ELECTRIC),('frames',FRAMES)]
    content=k('seof',v('light'),k('seom',*args(FIXED)),v('electricassigned'),v('frames'))
    text+=definition('seon',params(source),'b context['+both(k('sedi',v('pi')),op('t',content,v('context')))+']','e')
    return text


MEANINGS={
    'seog':'同じ四座標時刻で、中心からの三空間座標の二乗距離が正の半径の二乗より小さい開球の所属条件。四次元の体積や移動する物体の領域と同一視しない。',
    'seoh':'正の体積と符号付きの総量・平均値について、総量＝平均値×体積とする。零体積での比を認めず、電荷と密度の負値や零は許す。',
    'seoi':'0<radius<upperの各有効な実半径で、同じ総電荷・体積・平均密度の三関数がseohを満たす。任意の一半径の一致で置換しない。',
    'seoj':'seoiの平均密度関数が、正の半径から零へ近づくとき指定値へ収束するというsjrの極限条件。零半径で関数値を定義する必要はない。',
    'seok':'追跡する物質点が属する分布を指定し、同じ系・出来事・地点・文脈と単位で各球に含まれるその分布の総電荷を割り当て、体積を同じpiのsedmへ結び、seojの局所密度を得る。球の平均による局所極限である。',
    'seol':'seokの電荷密度と、同じpiを使う既存semlの4pi倍の規格化密度を結ぶ。規格化密度を総電荷や電荷密度そのものと同一視しない。',
    'seom':'対象の分布・pi・長さ/時刻/電荷の単位・所属関係・総量の割当・座標の単位規約を固定し、同じ物質・系・出来事の規格化密度を、縮む球と比の極限の存在で説明する関係を構成する。',
    'seon':'seomの密度の説明を、既存の履歴による速度の説明seofと式の内容へ接続する。同じpiの指定も要求し、存在しない密度の虚偽の割当は作らない。',
}
LIMITS=[
    '球平均による局所極限を選んだ説明である。任意形状の縮小領域との一致、全ての点での存在、特異な点電荷の有限密度を仮定しない。密度が存在しないという内容も否定で記述できる。',
    '球は指定基準系で同時刻の三次元領域である。sedmの断面積分を体積に使い、四次元時空の体積や物質と共に動く境界へ無断で置換しない。',
    'memberは追跡点と選んだ分布の所属を同じ文脈へ結ぶ。measuredはその分布・系・出来事・球領域・長さ単位・電荷単位・値・文脈を結ぶ。測定済みか仮定上の総量かは文脈の解釈による。別の地点や別の時刻の値を半径だけで流用しない。追跡する点自体の総電荷と、その周囲の分布の総電荷を同一視しない。',
    'chartunitsはその系の座標に使う長さ・時刻の単位を同じ文脈で指定する。単位の物理的な実現、電気量の校正、一般の加法的電荷測度や三次元測度との接続は未完。',
    'seom・seonは密度と速度を説明する構成であり、前版zqdとの無条件の同値や、新しい著者の主張を追加しない。原文単位全体の意味確認は未完。',
]


def source_composed():
    doc=parse((ROOT/PARENT).read_text(encoding='utf-8'));statements,doc['statements']=doc['statements'],[]
    doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=statements
    basis=deepcopy(json.loads((ROOT/'data/einstein-material-velocity-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='einstein-local-density-basis-v1',document='examples/v014/einstein-local-density.noema')
    basis['definitions'].update(MEANINGS);basis['unresolved']+=LIMITS
    audit_basis(doc,basis);return format_graph(doc,'compact')+'\n',basis


def projected(roots,stem):
    text,basis=source_composed();doc=parse(text);selected=extract_document(doc,roots=roots,statement_indices=[])
    basis=extract_basis(doc,basis,selected,version=stem+'-basis-v1',document_path='examples/v014/'+stem+'.noema')
    return format_graph(selected.document,'compact')+'\n',basis


def generic_composed():return projected(ROOTS[:4],'local-density')
def core_composed():return projected(ROOTS,'local-density-core')
BUILDERS=((generic_composed,'local-density'),(source_composed,'einstein-local-density'),(core_composed,'local-density-core'))


def main():
    for builder,stem in BUILDERS:
        text,basis=builder()
        for name,body in ((basis['document'],text),('data/'+stem+'-basis-v1.json',json.dumps(basis,ensure_ascii=False,indent=2)+'\n')):
            path=ROOT/name
            if path.exists():
                if path.read_text(encoding='utf-8')!=body:raise ValueError('Stored density differs: '+name)
            else:
                with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(body)
        print(stem,len(text),'characters')


if __name__=='__main__':main()
