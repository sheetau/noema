"""Define transverse amplitude vectors and the facsimile-reviewed squared ratio."""
from copy import deepcopy
import json

from noema.extraction import extract_document, extract_basis
from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from scripts.compose_origin_clock import ROOT, definition, v
from scripts.compose_limits import call as k, op, both
from scripts.compose_plane_waveforms import CUT, AMPLITUDES
from scripts.compose_field_transform import rational_definitions as mixing_definitions

PARENT='examples/v014/einstein-plane-waveforms.noema'
ZERO,ONE='n p a b','n p b b'
VECTOR_ARGS='ax ay az ex ey ez hx hy hz'


def params(names,sort):
    return ' '.join(name+' '+sort for name in names.split())


def vector_definitions(real=False):
    sort=CUT if real else 'b'
    norm,dot,det,transverse=('seag','seah','seai','seaj') if real else ('seaa','seab','seac','sead')
    mul=lambda a,b:k('shv' if real else 'ad',a,b)
    add=lambda a,b:k('bd' if real else 'ab',a,b)
    sub=lambda a,b:k('bf',a,b) if real else add(a,k('ac',b))
    eq=lambda a,b:k('sca',a,b) if real else op('e',a,b)
    zero=k('bb',ZERO) if real else ZERO;one=k('bb',ONE) if real else ONE
    x,y,z=map(v,('x','y','z'))
    text=definition(norm,params('x y z',sort),add(mul(x,x),add(mul(y,y),mul(z,z))),sort)
    a,b,c,ex,ey,ez,hx,hy,hz=map(v,VECTOR_ARGS.split())
    text+=definition(dot,params('ax ay az ex ey ez',sort),add(mul(a,ex),add(mul(b,ey),mul(c,ez))),sort)
    u,w,U,W=map(v,('lefta','leftb','righta','rightb'))
    text+=definition(det,params('lefta leftb righta rightb',sort),sub(mul(u,W),mul(w,U)),sort)
    cross=(k(det,b,c,ey,ez),k(det,c,a,ez,ex),k(det,a,b,ex,ey))
    guards=[k('ba',v(n)) for n in VECTOR_ARGS.split()] if real else []
    text+=definition(transverse,params(VECTOR_ARGS,sort),both(*guards,
        eq(k(norm,a,b,c),one),eq(k(dot,a,b,c,ex,ey,ez),zero),
        *(eq(h,val) for h,val in zip((hx,hy,hz),cross))))
    return text


def rational_definitions():
    text=vector_definitions()
    mul=lambda a,b:k('ad',a,b);sub=lambda a,b:k('ab',a,k('ac',b));sq=lambda a:mul(a,a)
    V,s,a,p,new=map(v,('light','speed','ax','power','newpower'))
    text+=definition('seae',params('light speed ax power newpower','b'),both(
        k('aa',ZERO,V),k('aa',sq(s),sq(V)),op('u',k('aa',ONE,sq(a))),
        op('u',k('aa',p,ZERO)),op('u',k('aa',new,ZERO)),
        op('e',mul(sub(sq(V),sq(s)),new),mul(p,sq(sub(V,mul(a,s)))))))
    return text


RATIONAL_MEANINGS={
    'seaa':'三成分の二乗和。非負の振幅そのものとは区別する。',
    'seab':'同じ三軸での二つのベクトルの内積。',
    'seac':'二つの二成分から作る行列式lefta*rightb−leftb*righta。外積の各成分に再利用する。',
    'sead':'単位方向n、n・E=0、H=n×Eという有理数の横波振幅の条件。Hの向きを逆転させない。零振幅は許す。',
    'seae':'正の光速度、光速未満の符号付き速度、絶対値1以下の方向余弦、非負の二つの二乗振幅について、(V²−v²)A′²=A²(V−av)²を要求する。原刊912頁の平方根のない分母に対応する。',
}


def generic_composed():
    doc=parse('n:r aa[b b] c.r ab[b b] b.r ac[b] b.r ad[b b] b.'+mixing_definitions()+rational_definitions())
    labels={'aa':'有理数の厳密な小なり。','ab':'有理数の加算。','ac':'有理数の加法逆元。','ad':'有理数の乗算。'}
    basis={'version':'wave-amplitudes-basis-v1','document':'examples/v014/wave-amplitudes.noema',
        'primitives':[{'symbol':d['name'],'parameters':d['parameters'],'result':d['result'],
            'arguments':['value'] if d['name']=='ac' else ['left','right'],'meaning_ja':labels[d['name']]}
            for d in doc['declarations'] if d['kind']=='primitive'],
        'definitions':{**RATIONAL_MEANINGS,'s6b':'β*(own−ratio*cross)の有理数の成分混合。','s6c':'β*(own＋ratio*cross)の有理数の成分混合。'},
        'unresolved':['有理数のベクトルと代数の条件。実数全域の解析や電磁的測定の意味は別途必要。横波条件を原文の明示的な断言として追加しない。']}
    audit_basis(doc,basis)
    return format_graph(doc,'compact')+'\n',basis


def definitions():
    text=rational_definitions()+vector_definitions(True)
    zero,one=k('bb',ZERO),k('bb',ONE)
    V,s,a,p,new=map(v,('light','speed','ax','power','newpower'))
    mul=lambda a,b:k('shv',a,b)
    factor=k('sdn2',V,s,one,a)
    text+=definition('seak',params('light speed ax power newpower',CUT),both(
        *(k('ba',v(n)) for n in ('light','speed','ax','power','newpower')),
        k('s45',V,s),k('bc',mul(a,a),one),k('bc',zero,p),k('bc',zero,new),
        k('sca',new,mul(p,mul(factor,factor)))))
    x,y,z,A=map(v,('x','y','z','amplitude'))
    text+=definition('seal',params('x y z amplitude',CUT),both(
        *(k('ba',n) for n in (x,y,z,A)),k('bc',zero,A),k('sca',mul(A,A),k('seag',x,y,z))))
    n=list(map(v,('ax','ay','az')));e=list(map(v,AMPLITUDES[:3]));h=list(map(v,AMPLITUDES[3:]))
    newe=list(map(v,('newex','newey','newez')));newh=list(map(v,('newhx','newhy','newhz')))
    newA=v('newamplitude')
    # Equality of the E/H magnitudes is required as the meaning of a common
    # wave amplitude; its derivation under transverse conditions is checked separately.
    text+=definition('seam',params('light speed '+VECTOR_ARGS+' '+' '.join('new'+n for n in AMPLITUDES)+' amplitude newamplitude',CUT),both(
        k('s45',V,s),k('seaj',*n,*e,*h),k('sdz2',V,s,*e,*h,*newe,*newh),
        k('seal',*e,A),k('seal',*h,A),k('seal',*newe,newA),k('seal',*newh,newA)))
    return text


MEANINGS={
    'seag':'実数切断の三成分の二乗和を構成する。入力の有効性は利用側で要求する。',
    'seah':'実数切断の三成分の内積。',
    'seai':'実数切断で二次の行列式を構成する。',
    'seaj':'有効な九つの実切断が、単位方向n、横方向のE、H=n×Eを満たす。共通位相で進む真空の平面波に使う振幅条件であり、有限値で微分方程式を代用するものではない。',
    'seak':'有効な実切断、正のV、|v|<V、|a|≤1、非負の二乗振幅について、A′²=A²[β(1−av/V)]²を要求する。平方根のない原刊の分母に対応する。',
    'seal':'有効な三成分の二乗和が振幅Aの二乗で、A≥0である。負の枝を振幅と認定しない。零ベクトルの振幅は零を許す。',
    'seam':'同じ許容速度、単位方向、横波条件、六振幅の変換を共有し、電気側と磁気側の変換前後それぞれを同じ非負の振幅A,A′へ結ぶ。seakの二乗比の結論を前提に含めない。',
}


def source_composed():
    doc=parse((ROOT/PARENT).read_text(encoding='utf-8'))
    basis=deepcopy(json.loads((ROOT/'data/einstein-plane-waveforms-basis-v1.json').read_text(encoding='utf-8')))
    statements,doc['statements']=doc['statements'],[]
    doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=statements
    basis.update(version='einstein-wave-amplitudes-basis-v1',document='examples/v014/einstein-wave-amplitudes.noema')
    basis['definitions'].update(RATIONAL_MEANINGS);basis['definitions'].update(MEANINGS)
    basis['unresolved'] += [
        'M0345の電子テキストにある分母の平方根は原刊912頁では存在しない。元のスナップショットを変えず、別の照合記録を採用して平方根のない二乗振幅比を記述する。',
        '横波とH=n×Eは振幅変換の代数を導く条件として明示した。原文で省かれた導出を著者の明示的な断言として追加しない。全域の正弦波・真空方程式からの導出は未証明。',
        '六成分と非負の振幅を接続するが、特定の光源・観測者・出来事・基準系・単位で測った量との結合は未完。',
        '原刊の二つの振幅式M0345/M0347へ部分対応する。u0197の探索・命名・測定、u0199の帰結の談話、u0201の光速への極限の解釈は未完。',
        '有理数の代数的証明と構成した有理数切断の具体例を、実切断上の全域的証明や全文の意味一致の代用にしない。既存173件の本文主張を保持する。',
    ]
    audit_basis(doc,basis)
    return format_graph(doc,'compact')+'\n',basis


def core_composed():
    text,basis=source_composed();doc=parse(text)
    selected=extract_document(doc,roots=['seam','seak'],statement_indices=[])
    projected=extract_basis(doc,basis,selected,version='wave-amplitudes-core-basis-v1',document_path='examples/v014/wave-amplitudes-core.noema')
    return format_graph(selected.document,'compact')+'\n',projected


def main():
    for builder,stem in ((generic_composed,'wave-amplitudes'),(source_composed,'einstein-wave-amplitudes'),(core_composed,'wave-amplitudes-core')):
        text,basis=builder()
        for name,body in ((basis['document'],text),('data/'+stem+'-basis-v1.json',json.dumps(basis,ensure_ascii=False,indent=2)+'\n')):
            path=ROOT/name
            if path.exists():
                if path.read_text(encoding='utf-8')!=body:raise ValueError('Stored wave amplitudes differ: '+name)
            else:
                with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(body)
        print(stem,len(text),'characters')


if __name__=='__main__':main()
