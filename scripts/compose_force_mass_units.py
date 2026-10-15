"""Keep rest-mass, force and acceleration readings in explicit unit scales."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document,extract_basis
from noema.meaning_basis import audit_basis
from scripts.compose_acceleration_units import ROOT,CUT,DIM,ALL as ACC_ALL,INPUTS as ACC_INPUTS,META,READINGS
from scripts.compose_material_acceleration import PROFILES,ACCEL,FORCE
from scripts.compose_origin_clock import definition,v
from scripts.compose_limits import call as k,app,both,op,quant
from scripts.compose_situated_criticism import params,args

PARENT='examples/v014/einstein-acceleration-units.noema'
SOURCE='examples/v014/einstein-force-mass-units.noema'
LIBRARY='examples/v014/force-mass-units.noema'
CORE='examples/v014/force-mass-units-core.noema'
RESTMASS='h[a a a '+CUT+' d] c'
MASS=[('massaxis','a'),('massunit','a'),('massdim',DIM),('forcedim',DIM),('massscale',CUT),('forcescale',CUT),('restmassassigned',RESTMASS)]
NORMAL=[(n,CUT) for n in ('light','speed','beta','restmass')]
ALL=ACC_ALL+MASS+NORMAL
INPUTS=ACC_INPUTS+MASS
NUMERIC='light speed beta restmass massscale forcescale accelerationscale longitudinal transverse'
ROOTS=['sepz','seqa','seqb','seqc','seqd']


def definitions():
    text=''
    for real,name in ((False,'sepz'),(True,'seqa')):
        typ=CUT if real else 'b';fields=[(n,typ) for n in NUMERIC.split()]
        light,speed,beta,mu,M,F,A,L,T=args(fields)
        mul=lambda a,b:k('shv' if real else 'ad',a,b)
        eq=lambda a,b:k('sca',a,b) if real else op('e',a,b)
        zero=k('bb','n p a b') if real else 'n p a b'
        factor=mul(mul(mu,M),A);square=mul(beta,beta)
        text+=definition(name,params(fields),both(*([k('ba',x) for x in args(fields)] if real else []),
            k('srd' if real else 'sra',light,speed,beta),
            *(k('bg' if real else 'aa',zero,s) for s in (M,F,A)),
            eq(mul(L,F),mul(factor,mul(square,beta))),eq(mul(T,F),mul(factor,square))))
    dimensions=[(n,'a') for n in ('massaxis','lengthaxis','timeaxis')]+[(n,DIM) for n in ('massdim','accelerationdim','forcedim')]
    text+=definition('seqb',params(dimensions),both(
        op('u',op('e',v('massaxis'),v('lengthaxis'))),op('u',op('e',v('massaxis'),v('timeaxis'))),
        k('dh',v('massaxis'),v('massdim')),
        quant('f','axis','a',op('e',app(v('forcedim'),v('axis')),k('ab',app(v('massdim'),v('axis')),app(v('accelerationdim'),v('axis')))))))
    text+=definition('seqc',params(ALL),both(k('sepx',*args(ACC_ALL)),k('seqb',*args(dimensions)),
        app(v('units'),v('forceunit'),v('forcedim'),v('forcescale'),v('context')),
        app(v('units'),v('massunit'),v('massdim'),v('massscale'),v('context')),
        app(v('restmassassigned'),v('matter'),v('event'),v('massunit'),v('restmass'),v('context')),
        k('seqa',*(v(n) for n in NUMERIC.split()))))
    fixed=[k('zramatter'),k('ra'),v('context'),v('domain'),v('curve'),k('zraevent'),v('point')]+args(PROFILES+ACCEL)
    fixed+=[k('zbm'),k('zraforceunit'),k('zraaccelerationunit')]+args(FORCE[3:])+[k('zralongitudinal'),k('zratransverse')]+args(META+READINGS+MASS)
    fixed+=[k('tc'),k('zb7'),k('soy',k('tc'),k('zb7')),k('zramu')]
    text+=definition('seqd',params(INPUTS),'b context['+k('seqc',*fixed)+']','e')
    return text


MEANINGS={
    'sepz':'正の質量・力・加速度の単位尺度M,F,Aの下で、縦係数Lと横係数Tを L*F=mu*M*A*beta^3、T*F=mu*M*A*beta^2 で結ぶ有理数の関係。muはmassunitの読みであり、力/加速度の単位での係数と同じ数値とは限らない。',
    'seqa':'sepzを実切断で表す。全ての入力値の有効性、正の尺度、光速度とbetaの正規化を保持する。muの符号は数学的入力として制限しない。',
    'seqb':'質量の基底軸を長さ・時間から分け、力の次元指数を質量と加速度の指数の和とする。量の種類の物理的な定義や、力の観測を次元だけから補わない。',
    'seqc':'既存の座標加速度・単位付き記録・換算後の力の式に、力と質量の単位尺度、同じ対象・出来事への低速質量の帰属と、尺度を含む係数式を接続する。',
    'seqd':'本文の固定した対象・出来事・K・k・mu・二係数について、力・加速度・質量の尺度を含む内容を作る。以前のmuを無条件に力/加速度の単位の数値として使う読みを置き換える候補であり、新しい著者主張は追加しない。',
}
LIMITS=[
    '同じ単位系での数値関係を具体化した。単位の変更と、力や加速度そのものの物理的な定義の変更は別であり、u0259の異なる定義・理論の比較を単位換算だけで表し終えたとはしない。',
    'restmassassignedは同じ対象・出来事・質量単位・文脈のmuの帰属を明示する入力関係である。低速での質量の測定操作や、電荷と場から力を定める物理的な説明はなお残る。',
    '質量尺度M、力尺度F、加速度尺度Aは共通の基準量に対する正の一定尺度で、基準の力は基準の質量×加速度に整合すると指定する。この基準や校正の物理的実現は単位関係の解釈に残る。',
    '独立した長さ・時間・質量の基底次元を使う。自然単位で次元を同一視する別の体系を、この定義だけで扱うとはしない。数理上はmuの零・負値を排除しないが、負の物理的質量を主張するわけではない。',
    '有理数の尺度変換の証明と、登録した有理数を埋め込む実切断モデルの検査を区別する。全実数の体の法則、観測の実現、原文の意味一致の機械的証明は未完。先行176文は保持する。',
]


def build():
    old=parse((ROOT/PARENT).read_text(encoding='utf-8'));doc=deepcopy(old);doc['statements']=[]
    doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']
    basis=json.loads((ROOT/'data/einstein-acceleration-units-basis-v1.json').read_text(encoding='utf-8'))
    basis.update(version='einstein-force-mass-units-basis-v1',document=SOURCE)
    basis['definitions'].update(MEANINGS);basis['unresolved']+=LIMITS;audit_basis(doc,basis)
    files={SOURCE:format_graph(doc,'compact')+'\n','data/einstein-force-mass-units-basis-v1.json':basis}
    for path,roots in ((LIBRARY,ROOTS[:3]),(CORE,ROOTS)):
        selected=extract_document(doc,roots=roots,statement_indices=[]);stem=path.rsplit('/',1)[1][:-6]
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
