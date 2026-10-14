"""Describe signed regional totals and connect them to local charge density."""
from copy import deepcopy
import json

from noema.extraction import extract_document,extract_basis
from noema.grammar import parse,format_graph
from noema.meaning_basis import audit_basis
from scripts.compose_origin_clock import ROOT,definition,v
from scripts.compose_limits import call as k,app,op,both,quant,lam
from scripts.compose_situated_criticism import params,args
from scripts.compose_local_density import CUT,POINT,BALL,MEASURE,FIXED,ROLES
from scripts.compose_density_referents import ELECTRIC,FRAMES

PARENT='examples/v014/einstein-local-density.noema'
DOMAIN='h['+BALL+'] c'
TOTAL='h['+BALL+'] '+CUT
CLOCK='h[a a a d] '+CUT
KEYS=[('frame','a'),('event','a'),('lengthunit','a'),('timeunit','a'),('chargeunit','a'),('context','d')]
DOMAINS='h[a a a a a d] '+DOMAIN
TOTALS='h[a a a a a d] '+TOTAL
ADAPTER=[('distribution','a'),('timeunit','a'),('original',MEASURE),('clock',CLOCK),('domains',DOMAINS),('totals',TOTALS)]
SOURCE=[('light',CUT)]+FIXED+[('clock',CLOCK),('domains',DOMAINS),('totals',TOTALS),('electricassigned',ELECTRIC),('frames',FRAMES)]
ROOTS=['seoo','seop','seoq','seor','seos','seot','seow','seou','seov']
ZERO=k('bb','n p a b')


def sets(pointsort):
    region='h['+pointsort+'] c';domain='h['+region+'] c';total='h['+region+'] '+CUT
    universe,left,right=map(v,('universe','left','right'))
    empty=lam('point',pointsort,op('u',op('e',v('point'),v('point'))))
    union=lam('point',pointsort,op('x',app(left,v('point')),app(right,v('point'))))
    difference=lam('point',pointsort,both(app(left,v('point')),op('u',app(right,v('point')))))
    base=[('universe',region),('left',region),('right',region)]
    every=lambda body:quant('f','point',pointsort,op('y',app(universe,v('point')),body))
    pairs=lambda body:quant('f','left',region,quant('f','right',region,body))
    selected=both(app(v('domain'),left),app(v('domain'),right))
    text=definition('seoo',params(base),every(op('z',app(left,v('point')),app(right,v('point')))))
    text+=definition('seop',params(base),every(op('u',both(app(left,v('point')),app(right,v('point'))))))
    text+=definition('seoq',params([('universe',region),('domain',domain)]),both(app(v('domain'),empty),pairs(both(
        op('y',k('seoo',universe,left,right),op('z',app(v('domain'),left),app(v('domain'),right))),
        op('y',selected,both(app(v('domain'),union),app(v('domain'),difference)))))))
    totalargs=[('universe',region),('domain',domain),('total',total)]
    q=lambda r:app(v('total'),r)
    text+=definition('seor',params(totalargs),both(k('seoq',universe,v('domain')),k('ba',q(empty)),k('sca',q(empty),ZERO),
        quant('f','region',region,op('y',app(v('domain'),v('region')),k('ba',q(v('region'))))),
        pairs(op('y',selected,both(
            op('y',k('seoo',universe,left,right),k('sca',q(left),q(right))),
            op('y',k('seop',universe,left,right),k('sca',q(union),k('bd',q(left),q(right)))))))))
    text+=definition('seos',params(totalargs+[('region',region),('value',CUT)]),both(
        k('seor',universe,v('domain'),v('total')),app(v('domain'),v('region')),k('ba',v('value')),k('sca',q(v('region')),v('value'))))
    return text


def definitions():
    text=sets(POINT)
    text+=definition('seot',params([('point',POINT),('time',CUT)]),both(k('ba',v('time')),
        *[k('ba',app(v('point'),k(axis))) for axis in ROLES],k('sca',app(v('point'),k('zc7')),v('time'))))
    same=both(app(v('universe'),v('first')),app(v('universe'),v('second')),
        *[k('sca',app(v('first'),k(axis)),app(v('second'),k(axis))) for axis in ROLES])
    invariant=quant('f','first',POINT,quant('f','second',POINT,op('y',same,
        op('z',app(v('region'),v('first')),app(v('region'),v('second'))))))
    text+=definition('seow',params([('universe',BALL),('domain',DOMAIN)]),
        quant('f','region',BALL,op('y',app(v('domain'),v('region')),invariant)))
    local=[('flow','a'),('frame','a'),('event','a'),('region',BALL),('lengthunit','a'),('chargeunit','a'),('value',CUT),('context','d')]
    time=app(v('clock'),*(v(n) for n in ('frame','event','timeunit','context')))
    universe=lam('point',POINT,k('seot',v('point'),time))
    domain=app(v('domains'),*args(KEYS));total=app(v('totals'),*args(KEYS))
    body=both(op('e',v('flow'),v('distribution')),k('ba',time),
        app(v('original'),*args(local)),k('seow',universe,domain),k('seos',universe,domain,total,v('region'),v('value')))
    text+=definition('seou',params(ADAPTER),'i['+params(local)+']['+body+']',MEASURE)
    adapted=k('seou',v('distribution'),v('timeunit'),v('measured'),v('clock'),v('domains'),v('totals'))
    fixed=[adapted if n=='measured' else v(n) for n,_ in FIXED]
    text+=definition('seov',params(SOURCE),k('seon',v('light'),*fixed,v('electricassigned'),v('frames')),'e')
    return text


MEANINGS={
    'seoo':'指定した対象範囲内の全点で所属が一致する二領域。範囲外の所属や式の書き方は領域の区別に使わない。',
    'seop':'指定した対象範囲内で共通の点を持たない二領域。',
    'seoq':'空領域を含み、和集合と差集合で閉じ、対象範囲内で同じ領域を同じように受け入れる定義域。全ての部分集合や無限領域の量が存在するとは要求しない。',
    'seor':'seoqの定義域の各領域に有限な実数値を与える符号付きの総量。空領域は零、同じ領域の値は等しく、重ならない二領域の和集合の値は和になる。非負性・単調性・可算加法性は課さない。',
    'seos':'seorを満たす同じ総量関数に、定義域に属する領域とその実数値を結ぶ。定義域外の関数値を総量として採用しない。',
    'seot':'指定した有効な座標時刻と同じ時刻を持つ、有効な四座標の点。球内の量を同時刻の三次元領域へ制限する対象範囲。',
    'seow':'定義域に含まれる各領域は、対象範囲内で四座標が等しい二つの点表現を同じように含む。四つの軸以外の関数値で場所や量を区別しない。',
    'seou':'分布と時刻単位を固定し、元の電気量の帰属に、同じ系・出来事・長さ/時刻/電荷単位・文脈の総量関数と定義域を結ぶ。出来事の座標時刻で切った範囲で有限加法性を要求する。元の帰属を消して任意の加法的量を電荷と認定しない。',
    'seov':'seouで整合性を課した球内総電荷の帰属を、既存の密度の極限と速度の履歴による説明へ渡す。追加の著者主張や元の未展開の関係との無条件の同値を宣言しない。',
}
LIMITS=[
    '総量の有限加法性と同じ領域への値の一意性を説明する構成。可算加法性、一般の積分との同値、特異な電荷分布の局所密度の存在は未証明であり、この定義だけから要求しない。',
    '定義域を明示して無限の空間全体の有限電荷を要求しない。範囲外の点の所属で同じ領域を区別せず、定義域と値の双方に外延的一致を要求する。',
    '空間の領域族には四座標が同じ点表現で所属が一致する条件を課す。POINTの他の引数に割り当てた値を隠れた空間座標として使わない。',
    '符号付きの電荷は相殺するので、総量零から空領域や電荷の不在を導かず、領域の包含から量の大小を導かない。',
    'clockは同じ系・出来事・時刻単位・文脈の座標時刻。domainsとtotalsは同じ系・出来事・長さ/時刻/電荷単位・文脈の領域族と総量関数。単位変更の規約の物理的実現は別途必要。',
    '元の電気量の帰属を保持した上で総量の整合性を課す。有限加法性だけでは電荷と別種の量を識別できない。作用・測定・校正の基礎説明と原文単位全体の意味確認は未完。',
]


def source_composed():
    doc=parse((ROOT/PARENT).read_text(encoding='utf-8'));statements,doc['statements']=doc['statements'],[]
    doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=statements
    basis=deepcopy(json.loads((ROOT/'data/einstein-local-density-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='einstein-additive-charge-basis-v1',document='examples/v014/einstein-additive-charge.noema')
    basis['definitions'].update(MEANINGS);basis['unresolved']+=LIMITS
    audit_basis(doc,basis);return format_graph(doc,'compact')+'\n',basis


def generic_composed():
    parent=parse((ROOT/PARENT).read_text(encoding='utf-8'))
    basis=json.loads((ROOT/'data/einstein-local-density-basis-v1.json').read_text(encoding='utf-8'))
    selected=extract_document(parent,roots=['ba','bb','bd','sca'],statement_indices=[])
    basis=extract_basis(parent,basis,selected,version='additive-charge-basis-v1',document_path='examples/v014/additive-charge.noema')
    doc=parse(format_graph(selected.document,'compact')+sets('a'))
    basis['definitions'].update({n:MEANINGS[n] for n in ROOTS[:5]});basis['unresolved'] += [LIMITS[i] for i in (0,1,3)]
    audit_basis(doc,basis);return format_graph(doc,'compact')+'\n',basis


def core_composed():
    text,basis=source_composed();doc=parse(text);selected=extract_document(doc,roots=ROOTS,statement_indices=[])
    basis=extract_basis(doc,basis,selected,version='additive-charge-core-basis-v1',document_path='examples/v014/additive-charge-core.noema')
    return format_graph(selected.document,'compact')+'\n',basis


BUILDERS=((generic_composed,'additive-charge'),(source_composed,'einstein-additive-charge'),(core_composed,'additive-charge-core'))


def main():
    for builder,stem in BUILDERS:
        text,basis=builder()
        for name,body in ((basis['document'],text),('data/'+stem+'-basis-v1.json',json.dumps(basis,ensure_ascii=False,indent=2)+'\n')):
            path=ROOT/name
            if path.exists():
                if path.read_text(encoding='utf-8')!=body:raise ValueError('Stored additive charge differs: '+name)
            else:
                with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(body)
        print(stem,len(text),'characters')


if __name__=='__main__':main()
