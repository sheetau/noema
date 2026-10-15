"""Bind coordinate acceleration to positive length, time and reading scales."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document,extract_basis
from noema.meaning_basis import audit_basis
from scripts.compose_material_acceleration import ROOT,CUT,TRACK,AT,LAW,LOCAL,PROFILES,ACCEL,FORCE,ROLES,coord
from scripts.compose_origin_clock import definition,v
from scripts.compose_limits import call as k,app,both,op,quant
from scripts.compose_situated_criticism import params,args

PARENT='examples/v014/einstein-material-acceleration.noema'
SOURCE='examples/v014/einstein-acceleration-units.noema'
LIBRARY='examples/v014/acceleration-units.noema'
CORE='examples/v014/acceleration-units-core.noema'
DIM='h[a] b'
UNIT='h[a '+DIM+' '+CUT+' d] c'
META=[(n,'a') for n in ('lengthunit','timeunit','lengthaxis','timeaxis')]+[(n,DIM) for n in ('lengthdim','timedim','accelerationdim')]+[(n,CUT) for n in ('lengthscale','timescale','accelerationscale')]+[('units',UNIT)]
READINGS=[(n,CUT) for n in ('readingx','readingy','readingz')]
ALL=LAW+META+READINGS
INPUTS=LOCAL+META+READINGS
ROOTS=['seps','sept','sepu','sepv','sepw','sepx','sepy']
NAMES='lengthscale timescale accelerationscale coordinate reading'


def basis():return json.loads((ROOT/'data/einstein-material-acceleration-basis-v1.json').read_text(encoding='utf-8'))


def definitions():
    text=''
    for real,name in ((False,'seps'),(True,'sept')):
        typ=CUT if real else 'b';mul=lambda a,b:k('shv' if real else 'ad',a,b)
        fields=[(n,typ) for n in NAMES.split()];L,T,A,x,y=args(fields)
        zero=k('bb','n p a b') if real else 'n p a b'
        positive=[k('bg' if real else 'aa',zero,s) for s in (L,T,A)]
        left=mul(mul(y,A),mul(T,T));right=mul(x,L)
        eq=k('sca',left,right) if real else op('e',left,right)
        text+=definition(name,params(fields),both(*([k('ba',s) for s in (L,T,A,x,y)] if real else []),*positive,eq))
    dimensions=[(n,'a') for n in ('lengthaxis','timeaxis')]+[(n,DIM) for n in ('lengthdim','timedim','accelerationdim')]
    axis=v('axis')
    text+=definition('sepu',params(dimensions),both(op('u',op('e',v('lengthaxis'),v('timeaxis'))),
        k('dh',v('lengthaxis'),v('lengthdim')),k('dh',v('timeaxis'),v('timedim')),
        quant('f','axis','a',op('e',app(v('accelerationdim'),axis),
            k('ab',app(v('lengthdim'),axis),k('ac',k('ad','n p c b',app(v('timedim'),axis))))))))
    names=basis()['source_symbols']['worldlines']
    text+=definition('sepv','unit a dimension '+DIM+' scale '+CUT+' context d',
        quant('g','rational','b',both(k('aa','n p a b',v('rational')),k('ba',v('scale')),
            k('sca',v('scale'),k('bb',v('rational'))),k(names['tl'],v('unit'),v('dimension'),v('rational')))))
    # The bridge is an explicit condition between two prior observation
    # vocabularies, never an implicit identification of namespaces.
    point=app(v('curve'),v('moment'))
    left=k('zpb',v('matter'),v('frame'),v('event'),point,v('context'))
    right=both(k(names['tg'],v('matter'),v('event'),v('context')),
        k(names['tf'],v('event'),v('frame'),v('context'),v('lengthunit'),v('timeunit'),
            coord(point,ROLES[3]),*(coord(point,a) for a in ROLES[:3])))
    text+=definition('sepw',params(TRACK+[('lengthunit','a'),('timeunit','a')]),
        quant('f','moment',CUT,op('y',both(k('ba',v('moment')),app(v('domain'),v('moment'))),
            quant('f','event','a',op('z',left,right)))))
    conditions=[k('va',v('frame')),k('va',v('forceframe')),
        k('zpa',v('matter'),v('forceframe'),v('event'),v('context')),
        k('zraconvention',v('matter'),v('forceframe'),v('frame'),v('event'),v('forceunit'),v('accelerationunit'),v('context')),
        k('sepp',*args(AT)),k('sepw',*args(TRACK),v('lengthunit'),v('timeunit')),k('sepu',*args(dimensions))]
    for unit,dim,scale in (('lengthunit','lengthdim','lengthscale'),('timeunit','timedim','timescale'),('accelerationunit','accelerationdim','accelerationscale')):
        conditions.append(app(v('units'),v(unit),v(dim),v(scale),v('context')))
    for (coordinate,_),(reading,_) in zip(ACCEL,READINGS):
        conditions.append(k('sept',v('lengthscale'),v('timescale'),v('accelerationscale'),v(coordinate),v(reading)))
    conditions.extend([k('zpc',v('forcerecord'),v('matter'),v('forcekind'),v('forceframe'),v('event'),v('forceunit'),v('forcevector'),v('context')),
        k('seph',v('longitudinal'),v('transverse'),*args(READINGS),*(coord(v('forcevector'),a) for a in ROLES[:3]))])
    text+=definition('sepx',params(ALL),both(*conditions))
    fixed=[k('zramatter'),k('ra'),v('context'),v('domain'),v('curve'),k('zraevent'),v('point')]+args(PROFILES+ACCEL)
    fixed+=[k('zbm'),k('zraforceunit'),k('zraaccelerationunit')]+args(FORCE[3:])+[k('zralongitudinal'),k('zratransverse')]+args(META+READINGS)
    coefficients=[k('tc'),k('zb7'),k('soy',k('tc'),k('zb7')),k('zramu'),k('zralongitudinal'),k('zratransverse')]
    text+=definition('sepy',params(INPUTS),'b context['+both(k('sepx',*fixed),k('sepf',*coefficients))+']','e')
    return text


MEANINGS={
    'seps':'正の長さ・時間・加速度単位尺度L,T,Aの下で、座標二階微分xと加速度の読みyを y*A*T^2=x*L で結ぶ有理数の換算関係。時間尺度は二乗する。',
    'sept':'sepsの実切断版。尺度も有効な正の実切断として扱い、数値は符号付きでよい。零の値が不正な尺度を正当化しない。',
    'sepu':'長さと時間の異なる基底軸をdhで確認し、加速度次元の各指数を長さの指数から時間の指数の二倍を引いた値にする。量の種類を次元だけで決定しない。',
    'sepv':'既存worldlinesの単位・次元・正の有理数尺度の規約tlを、実切断尺度と文脈引数を受ける関係へ包む。この旧規約は文脈独立であり、無理数尺度を認める一般のunits関係と同一ではない。',
    'sepw':'同じ対象・基準系・文脈と軌跡の領域内の全時刻・出来事で、zpbによる座標と、worldlinesの物体出来事対応tg・単位付き座標tfが同値であることを明示する。異なる語彙の対応を暗黙に補わない。',
    'sepx':'同じ軌跡の座標加速度、全域の単位付き観測の対応、基底次元と単位尺度の規約、三成分の換算を結び、換算後の加速度の読みを力と質量係数の式へ渡す。',
    'sepy':'前段の本文で固定した対象・出来事・K・k・力と加速度の単位・二係数について、単位付きの加速度と力の関係を作る内容構成子。係数やmuの数値は採用した単位で与える必要がある。',
}
LIMITS=[
    '単位尺度は共通の基準単位に対する値であり、長さ・時間の座標尺度は選んだ領域内で一定とする。時間依存の尺度、一般の再パラメーター化、非線形の単位変換はこの換算式の範囲外。',
    '長さ・時間と加速度単位の尺度を数値式と観測対応へ接続した。units関係による単位の実現・校正・量の種類、基準の共有、力とmuの単位尺度はなお説明が必要。次元一致だけでそれらを認定しない。',
    'sepwは二つの既存観測語彙の対応を明示した条件であり、その現実の成立を機械的に証明したものではない。全軌跡の単位付き測定の存在は有限モデルから補わない。',
    'septは実尺度を許すが、sepvは旧来の有理数尺度の規約を包む互換的な定義である。無理数尺度の測定規約は別のunits入力で記述する。',
    '有理数の換算恒等式の証明と実切断版の式の構成を分ける。実数の連鎖律・単位変更による二階微分の変換の機械的証明、原文区間全体の意味一致は未完。先行176文は変えない。',
]


def build():
    old=parse((ROOT/PARENT).read_text(encoding='utf-8'));doc=deepcopy(old);doc['statements']=[]
    doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']
    meanings=basis();meanings.update(version='einstein-acceleration-units-basis-v1',document=SOURCE)
    meanings['definitions'].update(MEANINGS);meanings['unresolved']+=LIMITS;audit_basis(doc,meanings)
    files={SOURCE:format_graph(doc,'compact')+'\n','data/einstein-acceleration-units-basis-v1.json':meanings}
    for path,roots in ((LIBRARY,ROOTS[:4]),(CORE,ROOTS)):
        selected=extract_document(doc,roots=roots,statement_indices=[]);stem=path.rsplit('/',1)[1][:-6]
        files[path]=format_graph(selected.document,'compact')+'\n'
        files['data/'+stem+'-basis-v1.json']=extract_basis(doc,meanings,selected,version=stem+'-basis-v1',document_path=path)
    return {p:t if isinstance(t,str) else json.dumps(t,ensure_ascii=False,indent=2)+'\n' for p,t in files.items()}


def main():
    for name,body in build().items():
        path=ROOT/name
        if path.exists():assert path.read_text(encoding='utf-8')==body,name
        else:
            with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(body)
        print(name,len(body),flush=True)


if __name__=='__main__':main()
