"""Build harmonic profiles and six-component plane waves from existing calculus."""
from copy import deepcopy
import json

from noema.extraction import extract_document, extract_basis
from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from scripts.compose_origin_clock import ROOT, definition, v
from scripts.compose_limits import call as k, app, op, both, quant as q
from scripts.compose_field_equations import CUT, TAU, FIELD, ROLES

PARENT = 'examples/v014/einstein-wave-directions.noema'
PROFILE = 'h['+CUT+'] '+CUT
ZERO, ONE = k('bb','n p a b'), k('bb','n p b b')
AMPLITUDES = ('ex','ey','ez','hx','hy','hz')
ROOTS = ('sdv2','sdy2','sdz2','sd22','sd23','sd24','s6k','s6l')


def params(names):
    return ' '.join(name+' '+CUT for name in names.split())


def definitions():
    sine, cosine, point = map(v, ('sine','cosine','point'))
    pair = 'sine '+PROFILE+' cosine '+PROFILE
    text = definition('sdt2',pair+' point '+CUT,both(k('ba',point),
        k('sjs','p ba',sine,point,app(cosine,point)),
        k('sjs','p ba',cosine,point,k('be',app(sine,point)))))
    text += definition('sdu2',pair,both(k('sca',app(sine,ZERO),ZERO),k('sca',app(cosine,ZERO),ONE)))
    text += definition('sdv2',pair,both(k('sjo','p ba',sine),k('sjo','p ba',cosine),
        k('sdu2',sine,cosine),q('f','point',CUT,op('y',k('ba',point),k('sdt2',sine,cosine,point)))))
    base = 'profile '+PROFILE+' '+params('light rate ax ay az')
    V,w,a,b,c = map(v,('light','rate','ax','ay','az'))
    coords = list(map(v,('x','y','z','time')))
    phase = k('sds2',V,w,a,b,c,coords[3],*coords[:3])
    text += definition('sdw2',base+' amplitude '+CUT,
        'i['+params('x y z time')+']['+k('shv',v('amplitude'),app(v('profile'),phase))+']',TAU)
    # Select cuts inside the scalar function: szi is not a polymorphic selector.
    component = ZERO
    for role,amp in reversed(list(zip(ROLES[:3],('ex','ey','ez')))):
        component=k('szi',op('e',v('component'),k(role)),v(amp),component)
    text += definition('sdx2',base+' '+params('ex ey ez'),
        'i[component a]['+k('sdw2',v('profile'),V,w,a,b,c,component)+']',FIELD)
    s=v('speed');amplitudes=list(map(v,AMPLITUDES))
    text += definition('sdy2',params('light speed rate ax ay az '+' '.join(AMPLITUDES)),both(
        k('sdl2',V,s,w,a,b,c),*(k('ba',x) for x in amplitudes)))
    beta=k('soy',V,s);ratio=k('shv',s,k('sjd',V))
    ex,ey,ez,hx,hy,hz=amplitudes
    transformed=(ex,k('s6d',beta,ratio,ey,hz),k('s6e',beta,ratio,ez,hy),
                 hx,k('s6e',beta,ratio,hy,ez),k('s6d',beta,ratio,hz,ey))
    outputs=[v('new'+name) for name in AMPLITUDES]
    text += definition('sdz2',params('light speed '+' '.join(AMPLITUDES)+' '+' '.join('new'+n for n in AMPLITUDES)),
        both(k('s45',V,s),*(k('ba',x) for x in amplitudes+outputs),
             *(k('sca',actual,expected) for actual,expected in zip(outputs,transformed))))
    shifted=(k('sdn2',V,s,w,a),k('sdo2',V,s,a),k('sdp2',V,s,a,b),k('sdp2',V,s,a,c))
    args='profile '+PROFILE+' '+params('light speed rate ax ay az '+' '.join(AMPLITUDES))
    for name,amps in (('sd22',transformed[:3]),('sd23',transformed[3:])):
        text += definition(name,args,k('sdx2',v('profile'),V,*shifted,*amps),FIELD)
    text += definition('sd24',pair+' '+params('light speed rate ax ay az '+' '.join(AMPLITUDES)),
        both(k('sdv2',sine,cosine),k('sdy2',V,s,w,a,b,c,*amplitudes)))
    return text


MEANINGS = {
    'sdt2':'同じ実数点で、Sの導関数がC、Cの導関数が−Sとなる。既存の実切断の極限による微分sjsを、全実数の定義域で使う。',
    'sdu2':'同じ二関数の原点条件S(0)=0、C(0)=1。位相のずれと振幅の任意性を除く正規化である。',
    'sdv2':'全ての有効な実切断を有効な実切断へ写す二関数S,Cが、原点条件sdu2と全実数点の微分条件sdt2を満たす。正弦・余弦を初期値問題で指定する。存在・一意性の機械的証明をこの定義自体は含まない。',
    'sdw2':'同じ光速度・周波数・三方向余弦の位相sds2へ一変数の波形を適用し、指定した一成分の振幅を掛けた四座標の関数。',
    'sdx2':'三つの振幅に同じsdw2の波形と位相を共有させた三成分の場。空間三軸以外への拡張値は零である。',
    'sdy2':'光速度・符号付き相対速度・正の周波数・単位方向のsdl2と、有効な六つの振幅を要求する。横波や真空の場の方程式はこの条件には含まない。',
    'sdz2':'六つの振幅を、許容速度で既存の場の成分混合s6d/s6eに従って結ぶ。二つの縦成分は保ち、四つの横成分の符号と相手成分を固定する。',
    'sd22':'同じ波形、変換後の周波数・方向余弦、電気側の混合振幅から、新四座標を引数にする三成分の平面波を構成する。',
    'sd23':'sd22と同じ波形・位相変換を使い、磁気側の混合振幅で新四座標の三成分を構成する。',
    'sd24':'正規化した正弦・余弦の全域条件sdv2と、同じ入力のsdy2を要求する。波形構成関数を正弦波として使用する条件であり、光源の実在や観測者の測定を断言しない。',
}


def source_composed():
    doc=parse((ROOT/PARENT).read_text(encoding='utf-8'))
    basis=deepcopy(json.loads((ROOT/'data/einstein-wave-directions-basis-v1.json').read_text(encoding='utf-8')))
    statements,doc['statements']=doc['statements'],[]
    doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=statements
    basis.update(version='einstein-plane-waveforms-basis-v1',document='examples/v014/einstein-plane-waveforms.noema')
    basis['definitions'].update(MEANINGS)
    basis['unresolved'] += [
        '先行草案の正弦波形・六振幅・M0325の未記述事項に対し、今回は初期値問題による正弦の指定と六成分の共有位相を追加する。光源・観測者・測定・遠方近似との対応は引き続き未完。',
        '正弦・余弦の実切断上の存在と一意性、微分法則の一般的な機械的証明は未完。任意の波形を構成できることから、その波形が正弦や真空の解だとは推論しない。',
        '成分混合と共通の波形値の乗算が可換であることは有理数の多項式として検査する。実数切断での全域的証明とは区別する。',
        '具体例では波形を正確な有理数値の関数で与え、座標の逆変換と新位相で六成分が一致することを検査する。この波形を正弦と称しない。',
        'M0345の振幅の二乗比は保存MathMLの分母に平方根がある。今回の六振幅の変換から得るノルム比との照合は未完であり、この式へ対応を付けない。',
        '本文の173主張を保持し、新たな著者の断言を追加しない。M0320/M0325との数式部分対応であり、全文の意味確認ではない。',
    ]
    audit_basis(doc,basis)
    return format_graph(doc,'compact')+'\n',basis


def core_composed():
    text,basis=source_composed();doc=parse(text)
    selected=extract_document(doc,roots=ROOTS,statement_indices=[])
    projected=extract_basis(doc,basis,selected,version='plane-waveforms-core-basis-v1',document_path='examples/v014/plane-waveforms-core.noema')
    return format_graph(selected.document,'compact')+'\n',projected


def main():
    for builder,stem in ((source_composed,'einstein-plane-waveforms'),(core_composed,'plane-waveforms-core')):
        text,basis=builder()
        for name,body in ((basis['document'],text),('data/'+stem+'-basis-v1.json',json.dumps(basis,ensure_ascii=False,indent=2)+'\n')):
            path=ROOT/name
            if path.exists():
                if path.read_text(encoding='utf-8')!=body:raise ValueError('Stored plane waveforms differ: '+name)
            else:
                with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(body)
        print(stem,len(text),'characters')


if __name__=='__main__':main()
