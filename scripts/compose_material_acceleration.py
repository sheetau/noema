"""Build coordinate acceleration from a derivative field on a local history."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document,extract_basis
from noema.meaning_basis import audit_basis
from scripts.compose_mass_coefficients import ROOT,CUT
from scripts.compose_material_velocity import TRACK,DOMAIN,CURVE,POINT,ROLES,coord
from scripts.compose_origin_clock import definition,v
from scripts.compose_limits import call as k,app,both,op,quant
from scripts.compose_situated_criticism import params,args

PARENT='examples/v014/einstein-mass-coefficients.noema'
SOURCE='examples/v014/einstein-material-acceleration.noema'
LIBRARY='examples/v014/material-acceleration.noema'
CORE='examples/v014/material-acceleration-core.noema'
SCALAR='h['+CUT+'] '+CUT
PROFILES=[(n,SCALAR) for n in ('velocityx','velocityy','velocityz')]
ACCEL=[(n,CUT) for n in ('ax','ay','az')]
AT=TRACK+[('event','a'),('point',POINT)]+PROFILES+ACCEL
FORCE=[(n,'a') for n in ('forceframe','forceunit','accelerationunit','forcerecord','forcekind')]+[('forcevector',POINT)]
LAW=AT+FORCE+[(n,CUT) for n in ('longitudinal','transverse')]
LOCAL=[('domain',DOMAIN),('curve',CURVE),('point',POINT)]+PROFILES+ACCEL+FORCE[3:]
ROOTS=['sepn','sepo','sepp','sepq','sepr']


def definitions():
    field=[('domain',DOMAIN),('function',SCALAR),('derivative',SCALAR)]
    moment=v('moment')
    law=op('y',both(k('ba',moment),app(v('domain'),moment)),
        k('sjs',v('domain'),v('function'),moment,app(v('derivative'),moment)))
    text=definition('sepn',params(field),quant('f','moment',CUT,law))
    text+=definition('sepo',params(field+[('time',CUT),('acceleration',CUT)]),both(
        k('senz',v('domain'),v('time')),k('sepn',*args(field)),
        k('sjs',v('domain'),v('derivative'),v('time'),v('acceleration'))))
    time=coord(v('point'),'zc7')
    velocity=[app(v(n),time) for n,_ in PROFILES]
    conditions=[k('seoc',*args(TRACK),v('event'),v('point'),*velocity)]
    for axis,(profile,_),(accel,_) in zip(ROLES[:3],PROFILES,ACCEL):
        function='i[moment '+CUT+']['+coord(app(v('curve'),moment),axis)+']'
        conditions.append(k('sepo',v('domain'),function,v(profile),time,v(accel)))
    text+=definition('sepp',params(AT),both(*conditions))
    forcevalues=[coord(v('forcevector'),axis) for axis in ROLES[:3]]
    text+=definition('sepq',params(LAW),both(k('va',v('frame')),k('va',v('forceframe')),
        k('zpa',v('matter'),v('forceframe'),v('event'),v('context')),
        k('zraconvention',v('matter'),v('forceframe'),v('frame'),v('event'),v('forceunit'),v('accelerationunit'),v('context')),
        k('sepp',*args(AT)),
        k('zpc',v('forcerecord'),v('matter'),v('forcekind'),v('forceframe'),v('event'),v('forceunit'),v('forcevector'),v('context')),
        k('seph',v('longitudinal'),v('transverse'),*args(ACCEL),*forcevalues)))
    bound=[k('zramatter'),k('ra'),v('context'),v('domain'),v('curve'),k('zraevent'),v('point')]+args(PROFILES+ACCEL)
    bound+=[k('zbm'),k('zraforceunit'),k('zraaccelerationunit')]+args(FORCE[3:])+[k('zralongitudinal'),k('zratransverse')]
    coefficients=[k('tc'),k('zb7'),k('soy',k('tc'),k('zb7')),k('zramu'),k('zralongitudinal'),k('zratransverse')]
    text+=definition('sepr',params(LOCAL),'b context['+both(k('sepq',*bound),k('sepf',*coefficients))+']','e')
    return text


MEANINGS={
    'sepn':'指定された実時間の領域内の全ての有効な時刻で、derivativeの値がfunctionの時間微分sjsとなる。ある一点で値が合うだけの関数を速度関数として使わない。',
    'sepo':'指定時刻が領域の両側内点であり、同じ領域の一階微分関数sepnをさらにsjsで微分した値を二階微分とする。領域は局所的に選べる。領域外の微分可能性は要求しない。',
    'sepp':'同じ物質点・基準系・出来事・座標時刻の履歴seocを保ち、三空間座標の一階微分関数とその二階微分を結び、三つの座標加速度を記述する。',
    'sepq':'同じ対象・出来事の力の記録、瞬間共動系、数値化規約と、frameでの座標加速度seppを三成分の質量係数式へ結ぶ。力の系と加速度の系の役割を同一視しない。',
    'sepr':'前段で固定したK・k・対象・出来事・二係数を使い、軌跡からの加速度と同じ力の記録が係数式を満たすという内容を作る。引数を明示した読解候補であり、著者の新たな主張や実際の測定の存在は追加しない。',
}
LIMITS=[
    'sepoは選んだ局所領域全体で一階微分が存在する関数を使う。その領域は任意に小さく選べるが、単独の観測点や有限列だけから近傍の微分可能性を補わない。',
    '座標加速度を二階微分へ分解した。zpbによる軌跡の観測対応、時間・長さの座標尺度とaccelerationunitの換算、zpcによる力の測定およびforcekindの意味はなお入力に依存する。',
    'seprは原文の数値式を具体化する候補の内容構成子であり、先行176文を変更しない。これを全ての対象に成り立つ法則として著者へ帰属させたわけではない。',
    '登録した多項式の対照例と、履歴・近傍・微分関数について明示したモデル前提を検査する。全実切断の解析法則や原文の意味一致を有限評価から認定しない。',
]


def build():
    old=parse((ROOT/PARENT).read_text(encoding='utf-8'));doc=deepcopy(old);doc['statements']=[]
    doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']
    basis=json.loads((ROOT/'data/einstein-mass-coefficients-basis-v1.json').read_text(encoding='utf-8'))
    basis.update(version='einstein-material-acceleration-basis-v1',document=SOURCE)
    basis['definitions'].update(MEANINGS);basis['unresolved']+=LIMITS
    audit_basis(doc,basis)
    files={SOURCE:format_graph(doc,'compact')+'\n','data/einstein-material-acceleration-basis-v1.json':basis}
    for path,roots in ((LIBRARY,ROOTS[:3]),(CORE,ROOTS)):
        selected=extract_document(doc,roots=roots,statement_indices=[])
        stem=path.rsplit('/',1)[1][:-6]
        files[path]=format_graph(selected.document,'compact')+'\n'
        files['data/'+stem+'-basis-v1.json']=extract_basis(doc,basis,selected,version=stem+'-basis-v1',document_path=path)
    return {p:t if isinstance(t,str) else json.dumps(t,ensure_ascii=False,indent=2)+'\n' for p,t in files.items()}


def main():
    for name,body in build().items():
        path=ROOT/name
        if path.exists():assert path.read_text(encoding='utf-8')==body,name
        else:
            with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(body)
        print(name,len(body),flush=True)


if __name__=='__main__':main()
