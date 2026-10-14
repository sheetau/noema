"""Keep velocity, charge density and current transformations separately typed."""
from copy import deepcopy
import json

from noema.extraction import extract_document,extract_basis
from noema.grammar import parse,format_graph
from noema.meaning_basis import audit_basis
from scripts.compose_origin_clock import ROOT,definition,v
from scripts.compose_limits import call as k,app,op,both
from scripts.compose_situated_criticism import params,args
from scripts.compose_convection_fields import CUT,POINT,JET,ROLES,INPUTS as SINGLE,ASSIGN

PARENT='examples/v014/einstein-convection-fields.noema'
FLOW='light speed beta density ux uy uz newdensity vx vy vz'
CURRENT='light speed beta density jx jy jz newdensity kx ky kz'
FACTOR='density ux uy uz jx jy jz newdensity vx vy vz kx ky kz'
COMBINED=FLOW+' jx jy jz kx ky kz'
JETFLOW=[(n,CUT) for n in ('light','speed','density','newdensity')]+[
    ('velocity',POINT),('newvelocity',POINT)]+[(n,JET) for n in ('electricjet','magneticjet','newelectricjet','newmagneticjet')]
FRAMES='h[a a '+CUT+' d] c'
COMMON={'matter','event','context','light','pi','assigned'}
INPUTS=[('matter','a'),('event','a'),('oldframe','a'),('newframe','a'),('context','d'),('light',CUT),('speed',CUT),('pi',CUT)]
for prefix in ('old','new'):
    INPUTS += [(prefix+n,sort) for n,sort in SINGLE if n not in COMMON|{'frame'}]
INPUTS += [('assigned',ASSIGN),('frames',FRAMES)]
ROOTS=['semp','semq','semr','sems','semt','semu','semv','semw','semx','semy','semz','sena','senb']


def equations(real=False):
    symbols=('semt','semu','semv','semw') if real else ('semp','semq','semr','sems')
    typ=CUT if real else 'b';zero=k('bb','n p a b') if real else 'n p a b'
    mul=lambda a,b:k('shv' if real else 'ad',a,b)
    sub=lambda a,b:k('bf',a,b) if real else k('ab',a,k('ac',b))
    eq=lambda a,b:k('sca',a,b) if real else op('e',a,b)
    square=mul(v('light'),v('light'));D=sub(square,mul(v('speed'),v('ux')))
    valid=lambda names:[k('ba',v(n)) for n in names.split()] if real else []
    normal=k('srd' if real else 'sra',*map(v,('light','speed','beta')))
    flow=valid(FLOW)+[normal,op('u',eq(D,zero)),
        eq(mul(D,v('vx')),mul(square,sub(v('ux'),v('speed')))),
        eq(mul(mul(v('beta'),D),v('vy')),mul(square,v('uy'))),
        eq(mul(mul(v('beta'),D),v('vz')),mul(square,v('uz'))),
        eq(mul(square,v('newdensity')),mul(mul(v('beta'),D),v('density')))]
    text=definition(symbols[0],params([(n,typ) for n in FLOW.split()]),both(*flow))
    current=valid(CURRENT)+[normal,
        eq(mul(square,v('newdensity')),mul(v('beta'),sub(mul(square,v('density')),mul(v('speed'),v('jx'))))),
        eq(v('kx'),mul(v('beta'),sub(v('jx'),mul(v('speed'),v('density'))))),eq(v('ky'),v('jy')),eq(v('kz'),v('jz'))]
    text+=definition(symbols[1],params([(n,typ) for n in CURRENT.split()]),both(*current))
    factors=valid(FACTOR)+[eq(v(j),mul(v(rho),v(u))) for rho,us,js in (
        ('density',('ux','uy','uz'),('jx','jy','jz')),('newdensity',('vx','vy','vz'),('kx','ky','kz'))) for u,j in zip(us,js)]
    text+=definition(symbols[2],params([(n,typ) for n in FACTOR.split()]),both(*factors))
    text+=definition(symbols[3],params([(n,typ) for n in COMBINED.split()]),both(
        k(symbols[0],*map(v,FLOW.split())),k(symbols[2],*map(v,FACTOR.split()))))
    return text


def jet_definitions():
    V,s=v('light'),v('speed')
    flow=[V,s,k('soy',V,s),v('density')]+[app(v('velocity'),k(a)) for a in ROLES[:3]]
    flow += [v('newdensity')]+[app(v('newvelocity'),k(a)) for a in ROLES[:3]]
    transform=k('s6w',V,s,*map(v,('electricjet','magneticjet','newelectricjet','newmagneticjet')))
    old=k('seme',V,v('density'),v('velocity'),v('electricjet'),v('magneticjet'))
    text=definition('semx',params(JETFLOW),both(transform,k('semd',v('electricjet'),v('density')),old,k('semt',*flow)))
    text+=definition('semy',params(JETFLOW),both(k('semx',*args(JETFLOW)),k('semd',v('newelectricjet'),v('newdensity'))))
    text+=definition('semz',params(JETFLOW),both(k('semy',*args(JETFLOW)),
        k('seme',V,v('newdensity'),v('newvelocity'),v('newelectricjet'),v('newmagneticjet'))))
    text+=definition('sena',params(JETFLOW),both(k('semx',*args(JETFLOW)),
        k('sca',k('s6q',v('magneticjet')),k('bb','n p a b'))))
    return text


def point_value(prefix,field):
    coords=[app(v(prefix+'point'),k(role)) for role in ROLES]
    if field=='velocity':return 'i[axis a]['+app(app(v(prefix+'velocityfield'),'v axis'),*coords)+']'
    return app(v(prefix+field+'field'),*coords)


def binding_definition():
    def fields(prefix):return [v(n) if n in COMMON else v(prefix+n) for n,_ in SINGLE]
    conditions=[app(v('frames'),v('oldframe'),v('newframe'),v('speed'),v('context')),
        k('semn',*fields('old')),k('semm',*fields('new')),
        k('seml',v('pi'),point_value('new','density'),point_value('new','charge'))]
    for prefix in ('old','new'):
        conditions.append(k('s6s',*(v(prefix+n) for n in ('electric','magnetic','region','point','electricjet','magneticjet'))))
    expected=k('s46',v('light'),v('speed'),v('oldpoint'))
    conditions += [k('sca',app(v('newpoint'),k(role)),app(expected,k(role))) for role in ROLES]
    mapping=dict(light=v('light'),speed=v('speed'),density=point_value('old','density'),newdensity=point_value('new','density'),
        velocity=point_value('old','velocity'),newvelocity=point_value('new','velocity'))
    mapping.update({name:v('old'+name) for name in ('electricjet','magneticjet')})
    mapping.update({name:v(name) for name in ('newelectricjet','newmagneticjet')})
    conditions.append(k('semy',*(mapping[n] for n,_ in JETFLOW)))
    return definition('senb',params(INPUTS),both(*conditions))


MEANINGS={
    'semp':'許容された基準系速度と正のbeta、非零のD=V²−v*uxを保ち、三速度成分とρの変換を分母を払って表す。ρが零でも速度式を密度で割らず保持する。',
    'semq':'密度と三電流成分について、V²ρ′=beta*(V²ρ−v*Jx)、Jx′=beta*(Jx−vρ)、Jy′=Jy、Jz′=Jzを表す。電流が一つの密度と速度の積であるとは仮定しない。',
    'semr':'変換前と後で、それぞれ三電流成分が同じ密度と対応する速度成分の積である。密度が零なら電流は零だが、速度を零や一意の値とは定めない。',
    'sems':'sempの速度・密度変換とsemrの単一の対流への分解を共有する値で結ぶ。semqの電流変換そのものは前提へ追加しない。',
    'semt':'sempを有効な実切断で表す。D≠0と正のbetaを明示し、原文にない流速の大きさ制限は暗黙に加えない。',
    'semu':'semqの独立した密度・電流の変換を有効な実切断で表す。密度が零で電流が非零の配置も許す。',
    'semv':'semrの変換前後の対流への分解を有効な実切断で表す。複数種の合成流を単一流に自動で分解しない。',
    'semw':'semtとsemvを同じ値で結び、密度・速度による対流の変換と独立な電流変換を比較できる条件。',
    'semx':'既存の同じ速度による24微分係数の変換s6w、元の密度の発散定義、元の対流を含む六式、三速度・密度の変換を結ぶ。新しい発散定義や磁気側の零発散は前提に含めない。',
    'semy':'semxに加え、変換後の電気側の発散が同じ変換後の密度に等しいことを要求する。密度の数式と場の微分値を別々の値にしない。',
    'semz':'semyに加え、変換後の六式が従来の1/Vを含む磁気側の形で成立する。原刊の変換後の印刷形semfと区別する。',
    'sena':'semxに元の磁気側の発散が零という追加条件を明示したもの。原文M0383の六式にこの条件が印刷されているとは主張しない。',
    'senb':'同じ物質・出来事・文脈を二つの基準系の場・密度・流速へ結ぶ。座標の変換と同じ点での両側24微分、密度・電流項、4πの換算、密度と発散の変換の一致を保持する。基準系の配置の割当は引数で明示する。',
}
LIMITS=[
    '速度はKからkへの変換であり、縦方向にux−v、分母に1−v*ux/V²を用いる。逆方向にはvを反転する。密度や電流を零で割って速度を推定しない。',
    '流速の大きさがV以下なら分母は正で密度の符号が保存されるが、定義自体はこの追加制限を仮定しない。形式上の超光速入力を現実の荷電物体の運動と認定しない。',
    '磁気側の零発散を追加しない元の六式だけでは、変換後の磁気側六式の成立は一般には導けない。追加条件senaと、原刊に印刷されたsemfの係数の違いを別々の問題として保持する。',
    'senbは微分係数と密度の対応を同じ出来事へ結ぶ。二場全体の関数としての変換、連鎖律、単位系と電気量の測定、仮定から著者の結論への説明は未完。',
    'framesは標準配置の二系・符号付き速度・文脈を結ぶ関係引数であり、座標値の一致だけから基準系の物理的な配置を補完しない。',
]


def source_composed():
    doc=parse((ROOT/PARENT).read_text(encoding='utf-8'))
    basis=deepcopy(json.loads((ROOT/'data/einstein-convection-fields-basis-v1.json').read_text(encoding='utf-8')))
    statements,doc['statements']=doc['statements'],[]
    doc=parse(format_graph(doc,'compact')+equations()+equations(True)+jet_definitions()+binding_definition());doc['statements']=statements
    basis.update(version='einstein-density-boost-basis-v1',document='examples/v014/einstein-density-boost.noema')
    basis['definitions'].update(MEANINGS);basis['unresolved']+=LIMITS+[
        'M0390の三速度と発散による密度の変換へ部分接続する。新しい原始概念・局所参照・著者の主張は追加しない。u0237の相対性原理との適合、u0238の電荷不変、原文全文の意味一致は未完。',
    ]
    audit_basis(doc,basis)
    return format_graph(doc,'compact')+'\n',basis


def projected(roots,stem):
    text,basis=source_composed();doc=parse(text)
    selected=extract_document(doc,roots=roots,statement_indices=[])
    projected_basis=extract_basis(doc,basis,selected,version=stem+'-basis-v1',document_path='examples/v014/'+stem+'.noema')
    return format_graph(selected.document,'compact')+'\n',projected_basis


def generic_composed():return projected(ROOTS[:4],'density-boost')
def core_composed():return projected(ROOTS+['semf'],'density-boost-core')
BUILDERS=((generic_composed,'density-boost'),(source_composed,'einstein-density-boost'),(core_composed,'density-boost-core'))


def main():
    for builder,stem in BUILDERS:
        text,basis=builder()
        for name,body in ((basis['document'],text),('data/'+stem+'-basis-v1.json',json.dumps(basis,ensure_ascii=False,indent=2)+'\n')):
            path=ROOT/name
            if path.exists():
                if path.read_text(encoding='utf-8')!=body:raise ValueError('Stored density boost differs: '+name)
            else:
                with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(body)
        print(stem,len(text),'characters')


if __name__=='__main__':main()
