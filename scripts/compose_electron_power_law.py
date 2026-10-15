"""Connect the longitudinal equation along a trajectory without dividing by speed."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document,extract_basis
from noema.meaning_basis import audit_basis
from scripts.compose_convention_comparison import ROOT,CUT
from scripts.compose_electron_axis_motion import ALL as MOTION,DOMAIN,CURVE,ROLES,coord
from scripts.compose_origin_clock import definition,v
from scripts.compose_limits import call as k,app,both,op,quant,ZERO
from scripts.compose_situated_criticism import params,args

PARENT='examples/v014/einstein-electron-axis-motion.noema'
SOURCE='examples/v014/einstein-electron-power-law.noema'
LIBRARY='examples/v014/electron-power-law.noema'
CORE='examples/v014/electron-power-law-core.noema'
READING='data/electron-power-law-reading-v1.json'
SCALAR='h['+CUT+'] '+CUT
NUMERIC='light speed beta mass charge field acceleration'
PROFILES=[(n,SCALAR) for n in ('velocity','acceleration','profile')]
CONSTANTS=[(n,CUT) for n in ('light','mass','charge')]
LOCAL=[('domain',DOMAIN),('curve',CURVE),('moment',CUT)]+PROFILES+CONSTANTS
ALL=MOTION+PROFILES+CONSTANTS


def definitions():
    text=''
    for real,law,power in ((False,'sesa','sesc'),(True,'sesb','sesd')):
        typ=CUT if real else 'b';fields=[(n,typ) for n in NUMERIC.split()]
        light,speed,beta,mass,charge,field,acceleration=args(fields)
        mul=lambda a,b:k('shv' if real else 'ad',a,b)
        eq=lambda a,b:k('sca',a,b) if real else op('e',a,b)
        zero=k('bb',ZERO) if real else ZERO
        normal=[k('srd' if real else 'sra',light,speed,beta),k('bg' if real else 'aa',zero,mass)]
        force=mul(charge,field);dynamic=mul(mass,mul(mul(mul(beta,beta),beta),acceleration))
        valid=[k('ba',x) for x in args(fields)] if real else []
        text+=definition(law,params(fields),both(*valid,*normal,eq(force,dynamic)))
        text+=definition(power,params(fields),both(*valid,*normal,eq(mul(force,speed),mul(dynamic,speed))))
    point=app(v('curve'),v('moment'));speed=app(v('velocity'),v('moment'));accel=app(v('acceleration'),v('moment'))
    position=coord(point,ROLES[0]);field=app(v('profile'),position)
    coordinate='i[time '+CUT+']['+coord(app(v('curve'),v('time')),ROLES[0])+']'
    text+=definition('sese',params(LOCAL),both(k('senz',v('domain'),v('moment')),k('seru',v('curve'),v('moment')),
        k('sjs',v('domain'),coordinate,v('moment'),speed),k('sjs',v('domain'),v('velocity'),v('moment'),accel),
        k('sesb',v('light'),speed,k('soy',v('light'),speed),v('mass'),v('charge'),field,accel)))
    lower,upper=[coord(v(n),ROLES[3]) for n in ('startpoint','endpoint')]
    local=[v('domain'),v('curve'),v('moment')]+args(PROFILES+CONSTANTS)
    text+=definition('sesf',params(ALL),both(k('serw',*args(MOTION)),
        k('sca',app(v('velocity'),lower),k('bb',ZERO)),k('sca',app(v('velocity'),upper),v('finalspeed')),
        quant('f','moment',CUT,op('y',both(k('ba',v('moment')),k('sxs',lower,upper,v('moment'))),k('sese',*local)))))
    return text


MEANINGS={
    'sesa':'同じ正規化betaと正の質量で、charge*field=mass*beta^3*accelerationとする有理数の縦方向の式。速度・電荷・場・加速度の符号は固定しない。',
    'sesb':'sesaを実切断で記述する。光速度と速度の適用範囲、正のbeta、全入力の有効性を保持する。',
    'sesc':'sesaの両辺へ同じ速度を掛けた仕事率の等式。速度零では力の式と同値にならない。',
    'sesd':'sescの実切断版。零速度での仕事率の等値だけから、力や加速度の関係を逆推定しない。',
    'sese':'同じ座標時刻と曲線について、xの時間微分をvelocity、velocityの時間微分をaccelerationへ結び、同じ位置で静電場のプロファイルを評価してsesbを課す。betaはその時刻の速度から求め、終端値へ固定しない。',
    'sesf':'前段の原点・初速零・軸上の軌道と同じ端点を保ち、全運動区間でseseを要求する。速度関数の両端も零とfinalspeedへ結ぶ。',
    'sesg':'u0261末尾の、運動過程全体で第一の式(A)が成り立つという部分内容。前段の静電力設定と同じ場・電荷・位置・粒子・系・両端を共有する。',
    'sesh':'同じ全区間の運動方程式sesg、仕事積分sert、収支と無放射等の前提serqを合わせる内容構成子。これだけで積分の変数変換や最終のエネルギー式を証明したとはしない。',
}
LIMITS=[
    '速度で割らずに力の式と仕事率の式を分ける。速度零でも力や加速度は零とは限らず、仕事率が零だから力の式が成立するという逆向きの推論は認めない。',
    'V・mu・epsilonはこの運動区間で固定された値として使う。場の位置関数は前段の仕事積分と同じものを使い、単位は原文の式に整合する共通規約を前提とする。',
    '微分と物理的な履歴の全域解釈、静電力の基礎説明、ゆっくりした加速と無放射、積分の変数変換の一般定理は未完である。',
    '今回の局所的な式と仕事率の一致は、原刊の中間速度積分にmuがない問題を修正した著者発話とはしない。先行の原文保存とmuを含む候補は分離したまま保持する。',
]


def build():
    old=parse((ROOT/PARENT).read_text(encoding='utf-8'));doc=deepcopy(old);doc['statements']=[]
    values={'zrivelocity':(SCALAR,'同じ粒子・Kのx方向の座標速度関数。曲線の時間微分へ結ぶ。'),
        'zriacceleration':(SCALAR,'同じ座標速度の時間微分となる加速度関数。'),
        'zrinode':('a','u0261末尾で運動区間全体の第一式(A)に言及する箇所。')}
    text=definitions()+''.join('r '+n+'[] '+sort+'.' for n,(sort,_) in values.items())
    fixed=[k('zramatter'),k('ra'),v('context'),k('zrhdomain'),k('zrhcurve'),k('zrgstart'),k('zraevent'),
        k('zrhstartpoint'),k('zrhendpoint'),k('zrgposition'),k('zb7'),k('zrivelocity'),k('zriacceleration'),k('zrgprofile'),k('tc'),k('zramu'),k('zrgcharge')]
    content=lambda name:'t['+k(name)+']['+v('context')+']'
    text+=definition('sesg','','b context['+both(content('serx'),k('sesf',*fixed))+']','e')
    text+=definition('sesh','','b context['+both(*(content(n) for n in ('sesg','sert','serq')))+']','e')
    doc=parse(format_graph(doc,'compact')+text)
    new=parse(format_graph(doc,'compact')+'s[k uh[k zrinode[] k rd[] r[k sesg[]] k zrgscope[] k ri[]]].')['statements']
    doc['statements']=old['statements']+new
    basis=json.loads((ROOT/'data/einstein-electron-axis-motion-basis-v1.json').read_text(encoding='utf-8'))
    basis.update(version='einstein-electron-power-law-basis-v1',document=SOURCE)
    basis['definitions'].update(MEANINGS);basis['unresolved']+=LIMITS;lookup={d['name']:d for d in doc['declarations']}
    for name,(_,meaning) in values.items():
        d=lookup[name];basis['primitives'].append(dict(symbol=name,parameters=d['parameters'],result=d['result'],arguments=[],meaning_ja=meaning))
    audit_basis(doc,basis)
    files={SOURCE:format_graph(doc,'compact')+'\n','data/einstein-electron-power-law-basis-v1.json':basis}
    for path,roots,indices in ((LIBRARY,['sesa','sesb','sesc','sesd','sese','sesf'],[]),(CORE,['sesh','sesd'],[len(old['statements'])])):
        selected=extract_document(doc,roots=roots,statement_indices=indices);stem=path.rsplit('/',1)[1][:-6]
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
