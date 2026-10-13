"""Bind wave representations, observers and unit-scaled amplitude records."""
from copy import deepcopy
import json

from noema.extraction import extract_document, extract_basis
from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from scripts.compose_origin_clock import ROOT, definition, v
from scripts.compose_limits import call as k, app, op, both
from scripts.compose_field_equations import CUT, FIELD, REGION, POINT, ROLES
from scripts.compose_plane_waveforms import PROFILE, AMPLITUDES

PARENT='examples/v014/einstein-wave-amplitudes.noema'
ASSIGNED='h[a a '+FIELD+' '+FIELD+' '+REGION+' a a d] c'
RECORDED='h[a a d] c'
MOTION='h[a a '+CUT+' '+CUT+' d] c'
ZERO,ONE=k('bb','n p a b'),k('bb','n p b b')
REP=[('wave','a'),('frame','a'),('electrickind','a'),('magnetickind','a'),('context','d'),
     ('electric',FIELD),('magnetic',FIELD),('region',REGION),('sine',PROFILE),('cosine',PROFILE),
     *[(n,CUT) for n in ('light','rate','ax','ay','az',*AMPLITUDES)],('assigned',ASSIGNED)]
OBS=[('observer','a'),('record','a'),('event','a'),('point',POINT),('magneticside','c'),
     ('unit','a'),('scale','b'),('value',CUT),('recordedby',RECORDED)]
READ=[('wave','a'),('frame','a'),('kind','a'),('context','d'),('region',REGION),
      *[(n,t) for n,t in OBS if n!='magneticside']]
ALL=REP+OBS


def parameters(items):
    return ' '.join(n+' '+t for n,t in items)


def invoke(name,items,overrides=None):
    overrides=overrides or {}
    return k(name,*(overrides.get(n,v(n)) for n,t in items))


def pair_parameters():
    shared={'wave','electrickind','magnetickind','context','sine','cosine','light','rate','ax','ay','az',*AMPLITUDES,'assigned','recordedby','magneticside'}
    items=[(n,t) for n,t in ALL if n in shared]
    for prefix in ('old','new'):
        items += [(prefix+n,t) for n,t in ALL if n not in shared]
    return items+[('speed',CUT),('motion',MOTION)]


def definitions():
    V,w,a,b,c=map(v,('light','rate','ax','ay','az'));amps=list(map(v,AMPLITUDES))
    electric=k('sdx2',v('sine'),V,w,a,b,c,*amps[:3])
    magnetic=k('sdx2',v('sine'),V,w,a,b,c,*amps[3:])
    text=definition('sean',parameters(REP),both(k('va',v('frame')),k('cf',v('wave')),
        op('u',op('e',v('electrickind'),v('magnetickind'))),
        app(v('assigned'),*(v(n) for n in ('wave','frame','electric','magnetic','region','electrickind','magnetickind','context'))),
        k('znn',*(v(n) for n in ('frame','electric','magnetic','region','context'))),
        k('sd24',v('sine'),v('cosine'),V,ZERO,w,a,b,c,*amps),k('seaj',a,b,c,*amps),
        k('sai2',ONE,electric,magnetic,v('electric'),v('magnetic'),v('region'))))
    coords=[app(v('point'),k(role)) for role in ROLES]
    text+=definition('seao',parameters(READ),both(k('xb',v('observer')),
        k('x4',v('observer'),v('frame'),v('context')),
        app(v('recordedby'),v('record'),v('observer'),v('context')),
        k('zpb',v('observer'),v('frame'),v('event'),v('point'),v('context')),
        k('shn',k('shx'),v('point'),'p ba'),app(v('region'),*coords),
        k('sbw2',*(v(n) for n in ('record','wave','kind','frame','event','unit','scale','value','context')),'p zof','p zog')))
    physical_value=k('bj',v('scale'),v('value'))
    electric_read=both(invoke('seao',READ,{'kind':v('electrickind')}),k('seal',*amps[:3],physical_value))
    magnetic_read=both(invoke('seao',READ,{'kind':v('magnetickind')}),k('seal',*amps[3:],physical_value))
    text+=definition('seap',parameters(ALL),both(invoke('sean',REP),
        op('y',op('u',v('magneticside')),electric_read),op('y',v('magneticside'),magnetic_read)))
    shared={n for n,t in pair_parameters() if not n.startswith(('old','new'))}
    old={n:v('old'+n) for n,t in ALL if n not in shared}
    new={n:v('new'+n) for n,t in ALL if n not in shared}
    speed=v('speed');beta=k('soy',V,speed);ratio=k('shv',speed,k('sjd',V))
    ex,ey,ez,hx,hy,hz=amps
    mixed=(ex,k('s6d',beta,ratio,ey,hz),k('s6e',beta,ratio,ez,hy),
           hx,k('s6e',beta,ratio,hy,ez),k('s6d',beta,ratio,hz,ey))
    new.update(dict(zip(AMPLITUDES,mixed)))
    new.update(rate=k('sdn2',V,speed,w,a),ax=k('sdo2',V,speed,a),
               ay=k('sdp2',V,speed,a,b),az=k('sdp2',V,speed,a,c))
    text+=definition('seaq',parameters(pair_parameters()),both(k('s45',V,speed),
        app(v('motion'),v('oldframe'),v('newframe'),V,speed,v('context')),
        invoke('seap',ALL,old),invoke('seap',ALL,new),
        k('saj2',k('s6m',V,speed,v('oldregion')),v('newregion'))))
    return text


MEANINGS={
    'sean':'同じ光の対象・基準系・文脈へ、二場・領域・電気側と磁気側の量の種類を割り当て、正規化した正弦、横波の振幅条件、非空領域全点での波形一致を要求する。assigned引数は同じ波の場の割当と基準尺度の規約を指定する。有限標本から同定したとはしない。',
    'seao':'同じ観測者が指定系に静止する設定で、その観測者に帰属する記録を、同じ波・量の種類・系・出来事・単位・値・文脈へ結ぶ。観測者の当該出来事の四座標が領域内にあることを要求する。recordedbyは記録・観測者・文脈の帰属関係である。',
    'seap':'seanの同じ波の表現とseaoの記録を結び、指定側の三振幅の大きさが単位尺度×記録値と一致する。真のmagneticsideは磁気側、偽は電気側。数値が同じでも量の種類を交換しない。',
    'seaq':'同じ波・波形・光速度・量の種類・文脈について、二系のseapを周波数・方向・六振幅の変換で接続する。motion引数は同じV,vによる標準配置の二系と単位尺度の対応を指定する。領域も同じ逆座標変換で一致させる。観測者・出来事・記録・単位は系ごとに明示する。',
}


def source_composed():
    doc=parse((ROOT/PARENT).read_text(encoding='utf-8'))
    basis=deepcopy(json.loads((ROOT/'data/einstein-wave-amplitudes-basis-v1.json').read_text(encoding='utf-8')))
    statements,doc['statements']=doc['statements'],[]
    doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=statements
    basis.update(version='einstein-wave-readings-basis-v1',document='examples/v014/einstein-wave-readings.noema')
    basis['definitions'].update(MEANINGS)
    basis['unresolved'] += [
        'u0197の静止系と移動系で測る電気側または磁気側の振幅へ、観測者・記録・出来事・量の種類・単位・領域を部分的に接続する。測定装置、校正誤差、光源、遠方近似、命名と探索の談話は未完。',
        'assigned、recordedby、motionは型付きの明示引数である。一般的な帰属関係と標準配置を別に与える必要があり、数値や関数の一致から物理的な同一対象・観測者・系間運動を自動推定しない。',
        '二場の関数値は各量の種類の基準尺度に換算された成分として解釈する。電気側と磁気側で同じ数値倍率を使う規約は既存の理論設定に依存し、任意の単位系へ無条件には拡張しない。',
        '二系の記録で出来事や観測者を同一とは要求しない。平面波の一定振幅を各記録地点で測る条件であり、受信信号の同じ位相や同じ光子の同定を主張しない。',
        '正弦・非空領域全点での関数一致・変換領域の一致は全域条件。検査の有限標本は引数の接続を区別する証人に限り、これらを証明したとはしない。',
        '値の記録関係は仮定上の測定にも使える。現実に測定を実施したことや、誤差のない実測が可能であることは、この構成だけからは従わない。本文173主張を保持する。',
    ]
    audit_basis(doc,basis)
    return format_graph(doc,'compact')+'\n',basis


def core_composed():
    text,basis=source_composed();doc=parse(text)
    selected=extract_document(doc,roots=['seaq'],statement_indices=[])
    projected=extract_basis(doc,basis,selected,version='wave-readings-core-basis-v1',document_path='examples/v014/wave-readings-core.noema')
    return format_graph(selected.document,'compact')+'\n',projected


def main():
    for builder,stem in ((source_composed,'einstein-wave-readings'),(core_composed,'wave-readings-core')):
        text,basis=builder()
        for name,body in ((basis['document'],text),('data/'+stem+'-basis-v1.json',json.dumps(basis,ensure_ascii=False,indent=2)+'\n')):
            path=ROOT/name
            if path.exists():
                if path.read_text(encoding='utf-8')!=body:raise ValueError('Stored wave readings differ: '+name)
            else:
                with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(body)
        print(stem,len(text),'characters')


if __name__=='__main__':main()
