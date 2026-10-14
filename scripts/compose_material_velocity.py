"""Explain coordinate velocity using a two-sided material trajectory."""
from copy import deepcopy
import json

from noema.extraction import extract_document,extract_basis
from noema.grammar import parse,format_graph
from noema.meaning_basis import audit_basis
from scripts.compose_origin_clock import ROOT,definition,v
from scripts.compose_limits import call as k,app,op,both,quant
from scripts.compose_situated_criticism import params,args
from scripts.compose_density_referents import INPUTS,ASSIGN,ELECTRIC,FRAMES
from scripts.compose_field_equations import CUT,POINT,ROLES

PARENT='examples/v014/einstein-equation-presentation.noema'
DOMAIN='h['+CUT+'] c'
CURVE='h['+CUT+'] '+POINT
DENSITY='h[a a a '+CUT+' d] c'
TRACK=[('matter','a'),('frame','a'),('context','d'),('domain',DOMAIN),('curve',CURVE)]
AT=TRACK+[('event','a'),('point',POINT)]+[(n,CUT) for n in ('ux','uy','uz')]
SOURCE=INPUTS+[(prefix+n,sort) for prefix in ('old','new') for n,sort in (('domain',DOMAIN),('curve',CURVE))]
ROOTS=['senz','seoa','seob','seoc','seod','seoe','seof']


def coord(point,axis):return app(point,k(axis))
def valid(point):return both(*(k('ba',coord(point,a)) for a in ROLES))
def equalpoints(first,second):return both(*(k('sca',coord(first,a),coord(second,a)) for a in ROLES))


def definitions():
    # A relative derivative on a selected sequence or one-sided domain is not
    # enough to specify ordinary coordinate-time velocity at an interior point.
    text=definition('senz',params([('domain',DOMAIN),('time',CUT)]),both(k('ba',v('time')),app(v('domain'),v('time')),
        quant('g','radius',CUT,both(k('ba',v('radius')),k('bg',k('bb','n p a b'),v('radius')),
            quant('f','moment',CUT,op('y',k('sjp',v('moment'),v('time'),v('radius')),app(v('domain'),v('moment'))))))))
    point=app(v('curve'),v('time'))
    text+=definition('seoa',params(TRACK+[('event','a'),('time',CUT)]),both(k('ba',v('time')),app(v('domain'),v('time')),
        valid(point),k('sca',coord(point,'zc7'),v('time')),k('zpb',v('matter'),v('frame'),v('event'),point,v('context'))))
    existence=quant('g','time',CUT,quant('g','event','a',k('seoa',*args(TRACK),v('event'),v('time'))))
    forward=quant('f','time',CUT,op('y',both(k('ba',v('time')),app(v('domain'),v('time'))),
        quant('g','event','a',k('seoa',*args(TRACK),v('event'),v('time')))))
    observed=v('observed');time=coord(observed,'zc7')
    reverse=quant('f','event','a',quant('f','observed',POINT,op('y',both(valid(observed),app(v('domain'),time),
        k('zpb',v('matter'),v('frame'),v('event'),observed,v('context'))),equalpoints(observed,app(v('curve'),time)))))
    text+=definition('seob',params(TRACK),both(existence,forward,reverse))
    point=v('point');time=coord(point,'zc7')
    partials=[k('sjs',v('domain'),'i[moment '+CUT+']['+coord(app(v('curve'),v('moment')),axis)+']',time,v(speed))
        for axis,speed in zip(ROLES[:3],('ux','uy','uz'))]
    text+=definition('seoc',params(AT),both(k('seob',*args(TRACK)),valid(point),k('senz',v('domain'),time),
        k('zpb',v('matter'),v('frame'),v('event'),point,v('context')),equalpoints(point,app(v('curve'),time)),*partials))
    conditions=[k('senv',*args(INPUTS))]
    for prefix,point,vel in (('old','oldpoint',('ux','uy','uz')),('new','point',('vx','vy','vz'))):
        conditions.append(k('seoc',v('matter'),v(prefix+'frame'),v('context'),v(prefix+'domain'),v(prefix+'curve'),v('event'),v(point),*map(v,vel)))
    text+=definition('seod',params(SOURCE),both(*conditions))
    local=[('matter','a'),('frame','a'),('event','a'),('density',CUT)]+[(n,CUT) for n in ('ux','uy','uz')]+[('context','d')]
    witness=k('seoc',*args(AT))
    for name,sort in reversed([('domain',DOMAIN),('curve',CURVE),('point',POINT)]):witness=quant('g',name,sort,witness)
    body=both(app(v('densityassigned'),v('matter'),v('frame'),v('event'),v('density'),v('context')),witness)
    text+=definition('seoe',params([('densityassigned',DENSITY)]),'i['+params(local)+']['+body+']',ASSIGN)
    fixed=[('light',CUT),('densityassigned',DENSITY),('electricassigned',ELECTRIC),('frames',FRAMES)]
    text+=definition('seof',params(fixed),k('senx',v('light'),k('seoe',v('densityassigned')),v('electricassigned'),v('frames')),'e')
    return text


MEANINGS={
    'senz':'指定時刻を含む正の半径の実開区間が、時間の定義域に含まれる。孤立点・片側だけの履歴を、通常の両側の瞬間速度の根拠として使わない。',
    'seoa':'曲線の引数と四座標の時刻成分を同じ値にし、指定時刻に同じ物質点・基準系・出来事・文脈の座標へ結ぶ。',
    'seob':'空でない時間領域の各実時刻にseoaを満たす出来事が存在し、同じ物質点・系・文脈に割り当てられた領域内の全座標も同じ曲線と一致する。',
    'seoc':'同じ物質点の座標時刻による履歴seobと、その内点senzでの三空間座標の微分sjsを結び、指定された出来事の瞬間速度成分を記述する。',
    'seod':'M0390の五つの等式・必要な電場微分・参照先senvに、同じ物質点と出来事の新旧二系での座標時間微分を結ぶ。密度の定義や任意運動の保存則は追加しない。',
    'seoe':'密度だけの帰属関係から、速度成分をseocの履歴と微分によって説明した密度・速度の帰属関係を構成する。曲線・領域・地点は存在量化し、原始的な速度割当にはしない。',
    'seof':'固定された光速度・電場割当・二系配置に、seoeで速度を説明した帰属関係を渡すsenxの内容。これを著者が提示したという新しい主張は追加しない。',
}
LIMITS=[
    'ここで追跡するのは一つの物質点の履歴である。広がりを持つ物体全体、複数種の電荷の流れ、同時刻に複数位置を持つ分布を、無条件に一本の曲線へ縮めない。',
    '曲線の引数は基準系の四座標の時刻成分である。固有時など別のパラメーターによる微分を、座標時刻の速度として同一視しない。',
    'zpbによる出来事の座標への対応、基準系と単位尺度の物理的な意味は既存の規約を使う。測定の実現、規格化密度と電荷分布の説明、全単位の意味一致は未完。',
    'seoeとseofは速度の意味を具体化する構成であり、前版の固定関係zqdとの無条件の同値や、著者がこの形式化をそのまま採用したことを主張しない。',
    '有限のアフィン・二次曲線の検査は、全実時刻の履歴の存在や一般の差商極限の機械的証明ではない。全域量化は有限列へ置き換えない。',
]


def source_composed():
    doc=parse((ROOT/PARENT).read_text(encoding='utf-8'));statements,doc['statements']=doc['statements'],[]
    doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=statements
    basis=deepcopy(json.loads((ROOT/'data/einstein-equation-presentation-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='einstein-material-velocity-basis-v1',document='examples/v014/einstein-material-velocity.noema')
    basis['definitions'].update(MEANINGS);basis['unresolved']+=LIMITS
    audit_basis(doc,basis);return format_graph(doc,'compact')+'\n',basis


def projected(roots,stem):
    text,basis=source_composed();doc=parse(text);selected=extract_document(doc,roots=roots,statement_indices=[])
    basis=extract_basis(doc,basis,selected,version=stem+'-basis-v1',document_path='examples/v014/'+stem+'.noema')
    return format_graph(selected.document,'compact')+'\n',basis


def generic_composed():return projected(['senz','seoa','seob','seoc','seoe'],'material-velocity')
def core_composed():return projected(ROOTS,'material-velocity-core')
BUILDERS=((generic_composed,'material-velocity'),(source_composed,'einstein-material-velocity'),(core_composed,'material-velocity-core'))


def main():
    for builder,stem in BUILDERS:
        text,basis=builder()
        for name,body in ((basis['document'],text),('data/'+stem+'-basis-v1.json',json.dumps(basis,ensure_ascii=False,indent=2)+'\n')):
            path=ROOT/name
            if path.exists():
                if path.read_text(encoding='utf-8')!=body:raise ValueError('Stored velocity differs: '+name)
            else:
                with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(body)
        print(stem,len(text),'characters')


if __name__=='__main__':main()
