"""Connect origin, rest and axial motion to the same work episode endpoints."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document,extract_basis
from noema.meaning_basis import audit_basis
from scripts.compose_convention_comparison import ROOT,CUT
from scripts.compose_material_velocity import TRACK,DOMAIN,CURVE,POINT,ROLES,coord,valid
from scripts.compose_origin_clock import definition,v
from scripts.compose_limits import call as k,app,both,op,quant,ZERO
from scripts.compose_situated_criticism import params,args

PARENT='examples/v014/einstein-electron-energy-balance.noema'
SOURCE='examples/v014/einstein-electron-axis-motion.noema'
LIBRARY='examples/v014/electron-axis-motion.noema'
CORE='examples/v014/electron-axis-motion-core.noema'
READING='data/electron-axis-motion-reading-v1.json'
ENDPOINTS=[('start','a'),('end','a'),('startpoint',POINT),('endpoint',POINT),('finalposition',CUT),('finalspeed',CUT)]
ALL=TRACK+ENDPOINTS
DRIVEN='a a a a a h['+CUT+'] '+CUT+' '+CUT+' d'


def definitions():
    moment=v('moment');point=app(v('curve'),moment);zero=k('bb',ZERO)
    text=definition('seru',params([('curve',CURVE),('moment',CUT)]),both(k('ba',moment),valid(point),
        k('sca',coord(point,ROLES[3]),moment),*[k('sca',coord(point,axis),zero) for axis in ROLES[1:3]]))
    lower,upper=v('lower'),v('upper')
    inside=both(k('ba',moment),k('sxs',lower,upper,moment))
    text+=definition('serv',params([('domain',DOMAIN),('curve',CURVE),('lower',CUT),('upper',CUT)]),both(
        k('ba',lower),k('ba',upper),k('bg',lower,upper),quant('f','moment',CUT,op('y',inside,
            both(app(v('domain'),moment),k('seru',v('curve'),moment))))))
    first,last=v('startpoint'),v('endpoint')
    text+=definition('serw',params(ALL),both(k('va',v('frame')),valid(first),valid(last),
        k('serv',v('domain'),v('curve'),coord(first,ROLES[3]),coord(last,ROLES[3])),
        k('seoc',*args(TRACK),v('start'),first,zero,zero,zero),
        k('seoc',*args(TRACK),v('end'),last,v('finalspeed'),zero,zero),
        *[k('sca',coord(first,axis),zero) for axis in ROLES[:3]],
        k('ba',v('finalposition')),k('ba',v('finalspeed')),k('sca',coord(last,ROLES[0]),v('finalposition'))))
    return text


MEANINGS={
    'seru':'時刻momentで曲線の四座標が有効で、時刻成分がmoment、yとzが零である。xの値や符号はこの条件では制限しない。',
    'serv':'開始時刻より終了時刻が後であり、その閉区間の全実時刻が定義域に属し、seruを満たす。定義域を狭めて軸外への逸脱を隠したり、両端だけで全区間の条件を代用したりしない。',
    'serw':'同じ対象・系・履歴について、開始と終了の出来事をseocへ結び、開始位置を原点、開始速度三成分を零、終了速度を(finalspeed,0,0)、終了位置のxをfinalpositionとする。区間全体はservで同じX軸に保つ。',
    'serx':'u0261の同じ粒子・系K・エネルギー交換の両端に、原点からの軸上の運動と静電力の設定を結ぶ前件内容。前件が現実に成立すると別途断言するものではない。',
    'sery':'serxの運動と力の設定なら、前段のsertの仕事積分と場から取り出す量の対応が成立するという条件文。前件の事実性や積分値の存在を条件文の真偽だけから補わない。',
    'serz':'同じ軌道設定serxを、既存serqの収支・初期エネルギー零・無放射の前提へ接続する内容構成子。初速零だけから既存のエネルギー値が零になることを証明したとはしない。',
}
LIMITS=[
    'serwは既存の座標時刻による二側の速度seocを再利用する。履歴の定義域は運動区間より広くてよいが、閉じた運動区間の全時刻を含まなければならない。',
    'zrhdriveは同じ対象・場・系・両端・場の位置プロファイル・電荷・文脈を結ぶ静電力の設定入力である。電場と力の法則、単位の校正、静電場の時間独立性の基礎説明は未展開。',
    '終了速度を前段のvへ、終了位置を仕事積分の上端へ結び、開始の出来事をエネルギー収支と共有する。座標と各量の単位規約が整合する前提を使う。',
    '曲線の全域と解析的な微分のモデル検査を、全実切断の極限や物理的な履歴の証明とはしない。ゆっくりした加速、無放射の論証、仕事積分の速度への変数変換と全体の意味一致は残る。',
]


def build():
    old=parse((ROOT/PARENT).read_text(encoding='utf-8'));doc=deepcopy(old);doc['statements']=[]
    values={'zrhdomain':(DOMAIN,'同じ粒子の座標時刻の履歴領域。開始と終了の内点近傍と全運動区間を含む。'),
        'zrhcurve':(CURVE,'同じ粒子・Kの座標時刻から四座標への曲線。'),
        'zrhstartpoint':(POINT,'エネルギー過程の開始出来事の四座標。'),
        'zrhendpoint':(POINT,'同じ過程の終了出来事の四座標。'),
        'zrhnode':('a','u0261の運動設定から仕事の式へ進む条件文の箇所。')}
    text=definitions()+''.join('r '+n+'[] '+sort+'.' for n,(sort,_) in values.items())
    text+='r zrhdrive['+DRIVEN+'] c.'
    fixed=[k('zramatter'),k('ra'),v('context'),k('zrhdomain'),k('zrhcurve'),k('zrgstart'),k('zraevent'),
        k('zrhstartpoint'),k('zrhendpoint'),k('zrgposition'),k('zb7')]
    driven=k('zrhdrive',k('zramatter'),k('zrgfield'),k('ra'),k('zrgstart'),k('zraevent'),k('zrgprofile'),k('zrgcharge'),v('context'))
    text+=definition('serx','','b context['+both(k('serw',*fixed),driven)+']','e')
    content=lambda name:'t['+k(name)+']['+v('context')+']'
    text+=definition('sery','','b context['+op('y',content('serx'),content('sert'))+']','e')
    text+=definition('serz','','b context['+both(content('serx'),content('serq'))+']','e')
    doc=parse(format_graph(doc,'compact')+text)
    new=parse(format_graph(doc,'compact')+'s[k uh[k zrhnode[] k rd[] r[k sery[]] k zrgscope[] k ri[]]].')['statements']
    doc['statements']=old['statements']+new
    basis=json.loads((ROOT/'data/einstein-electron-energy-balance-basis-v1.json').read_text(encoding='utf-8'))
    basis.update(version='einstein-electron-axis-motion-basis-v1',document=SOURCE)
    basis['definitions'].update(MEANINGS);basis['unresolved']+=LIMITS;lookup={d['name']:d for d in doc['declarations']}
    for name,(_,meaning) in values.items():
        d=lookup[name];basis['primitives'].append(dict(symbol=name,parameters=d['parameters'],result=d['result'],arguments=[],meaning_ja=meaning))
    d=lookup['zrhdrive'];basis['primitives'].append(dict(symbol=d['name'],parameters=d['parameters'],result=d['result'],
        arguments=['particle','field','frame','start','end','profile','charge','context'],meaning_ja='同じ粒子が指定の静電場の作用下にあるという運動区間の設定。場の位置プロファイルと電荷を同じ仕事積分へ結ぶ。'))
    audit_basis(doc,basis)
    files={SOURCE:format_graph(doc,'compact')+'\n','data/einstein-electron-axis-motion-basis-v1.json':basis}
    for path,roots,indices in ((LIBRARY,['seru','serv','serw'],[]),(CORE,['serz'],[len(old['statements'])])):
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
