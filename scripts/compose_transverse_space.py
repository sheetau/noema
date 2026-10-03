"""Express both transverse coordinates using axis-scoped light rays."""
from copy import deepcopy
import json

from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from scripts.compose_moving_light_trip import ROOT, both
from scripts.compose_affine_time_form import CUT


def rational_definitions():
    return '''
d snw[light b speed b component b distance b time b xprime b] c[w[k sla[v light v speed v component]][w[k aa[n p a b v time]][w[k aa[n p a b v distance]][w[e[v distance][k ad[v component v time]]][e[v xprime][n p a b]]]]]].
d snx[light b scale b inverse b distance b] b[k ad[v scale k ad[k ad[v light v inverse] v distance]]].
d sny[light b speed b scale b component b inverse b distance b time b coordinate b] c[w[k snw[v light v speed v component v distance v time n p a b]][w[k sja[n p b b v component v inverse]][e[v coordinate][k ad[v scale k ad[v light v time]]]]]].
d snz[light b speed b scale b inverse b xprime b time b tau b coordinate b] c[w[k sly[v light v speed v inverse]][w[e[v tau][k slz[v light v speed v scale v inverse v xprime v time]]][e[v coordinate][k ad[v light v tau]]]]].
'''


MEANINGS={
    'snw':'0≤v<Vと正の横成分wについて、選んだ横距離がw*t、x′が0となる光線上の有理数条件。tと距離は正である。',
    'snx':'a*V*distance/wの有理数の式。wの逆数と同じ速度・係数を呼出側で結ぶ。',
    'sny':'同じ横方向の光線で、x′=0のτ=a*tを使う座標=V*τの式と、wの逆数を結ぶ。',
    'snz':'同じx′,t,aを使う先行のτの式と、選択軸の座標=V*τを同時に結ぶ。x′の零は呼出側が別に要求する。',
}


def generic_composed():
    doc=parse((ROOT/'examples/v014/longitudinal-light.noema').read_text(encoding='utf-8')+rational_definitions())
    basis=deepcopy(json.loads((ROOT/'data/longitudinal-light-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='transverse-space-basis-v1',document='examples/v014/transverse-space.noema')
    basis['definitions'].update(MEANINGS)
    basis['unresolved']+=['y軸とz軸の光線を別の出来事へ結ぶ。横成分wと全速さVを区別し、一方の光線での式から他方の測定値を流用しない。']
    audit_basis(doc,basis)
    return format_graph(doc,'compact')+'\n',basis


def source_composed():
    doc=parse((ROOT/'examples/v014/einstein-longitudinal-light.noema').read_text(encoding='utf-8'))
    statements,doc['statements']=doc['statements'],[]
    text=format_graph(doc,'compact')+rational_definitions()+'''
r zfa[a] a.r zfb[a] a.r zfc[] a.r zfd[] a.r zfe[] a.r zff[] a.r zfg[] a.
d soa[axis a] c[w[x[e[v axis][k yo[]]][e[v axis][k yp[]]]][w[u[e[k yo[]][k yp[]]]][w[u[e[k yn[]][k yo[]]]][u[e[k yn[]][k yp[]]]]]]].
'''
    zero='k bb[n p a b]';V='k tc[]';v='k zb7[]';w='k sle['+V+' '+v+']';a='c[k zeq[]]['+v+']'
    text+='d sob[light '+CUT+' speed '+CUT+' scale '+CUT+' distance '+CUT+'] '+CUT+'[k shv[v scale k shv[k sje[v light k sle[v light v speed]] v distance]]].\n'
    ctx='v context';depart='k wi[v moving]';end='k wj[v moving]';ray='k wf[v moving]'
    coord=lambda event,frame,role:'k snd['+event+' k '+frame+'[] '+role+' '+ctx+']'
    clauses=['k soa[v axis]','u[e[v rest][v moving]]','e[k wf[v rest]]['+ray+']',
        'e[k wi[v rest]]['+depart+']','e[k wj[v rest]]['+end+']','u[e['+depart+']['+end+']]',
        'e[k wh[v rest]]['+depart+']','e[k wh[v moving]]['+depart+']',
        'k smk['+depart+' '+ctx+']','k sfm['+ctx+']','k skz['+V+' '+v+' '+w+']']
    for segment,frame in (('rest','ra'),('moving','zbm')):
        clauses+=['k wa[v '+segment+' k '+frame+'[] k rb[] k ta[] '+ctx+']',
            'k ba[k wq[v '+segment+']]','k bg['+zero+' k wq[v '+segment+']]',
            'k bg['+zero+' '+coord(end,frame,'v axis')+']']
        for event,reader in ((depart,'wo'),(end,'wp')):
            clauses+=['k shd['+event+' k zdz['+event+' k '+frame+'[] '+ctx+'] k '+frame+'[] '+ctx+']',
                'k sca[k '+reader+'[v '+segment+'] '+coord(event,frame,'k zc7[]')+']']
        for role in ('yo','yp'):
            clauses+=['y[u[e[v axis][k '+role+'[]]]][k sca['+coord(end,frame,'k '+role+'[]')+' '+zero+']]']
    rest_dx='k bf['+coord(end,'ra','k yn[]')+' '+coord(depart,'ra','k yn[]')+']'
    rest_distance='k bf['+coord(end,'ra','v axis')+' '+coord(depart,'ra','v axis')+']'
    moving_distance='k bf['+coord(end,'zbm','v axis')+' '+coord(depart,'zbm','v axis')+']'
    clauses+=['k zbw[k zbm[] k zbo[k zbm[] v axis '+ctx+'] v axis '+ctx+']',
        'k zdw['+ray+' '+depart+' '+end+' k zbo[k zbm[] v axis '+ctx+'] k zbm[] '+ctx+']',
        'k sca[k sne['+end+' '+ctx+'] '+zero+']',
        'k sca['+coord(end,'zbm','k yn[]')+' '+zero+']',
        'k sca[k wq[v moving] '+moving_distance+']',
        'k sca[k shv[k wq[v rest] k wq[v rest]] k bd[k shv['+rest_dx+' '+rest_dx+'] k shv['+rest_distance+' '+rest_distance+']]]',
        'k snf['+depart+' '+ctx+']','k snf['+end+' '+ctx+']']
    text+='d soc[rest a moving a axis a context d] c['+both(*clauses)+'].\n'
    text+='d sod[rest a moving a axis a context d] c['+both('k soc[v rest v moving v axis v context]',
        'k sbc['+V+' v context]','k smw[k zbm[] '+V+' v context]',
        'k smu[v rest '+V+' v context p qo p sax k ra[]]',
        'k smu[v moving '+V+' v context p qo p sax k zbm[]]',
        'k smj[k zd4[] k zeq[] '+V+' '+v+']')+'].\n'
    event='v event';x='k sne['+event+' '+ctx+']';t=coord(event,'ra','k zc7[]');tau=coord(event,'zbm','k zc7[]')
    distance=coord(event,'ra','v axis');target=coord(event,'zbm','v axis')
    guards=['k soa[v axis]','k skz['+V+' '+v+' '+w+']']
    text+='d soe[event a axis a context d] c['+both(*guards,*('k ba['+value+']' for value in (target,tau,x,t,a)),
        'k sca['+target+' k shv['+V+' '+tau+']]',
        'k sca['+target+' k shv['+V+' k smh['+V+' '+v+' '+a+' '+x+' '+t+']]]')+'].\n'
    text+='d sof[event a axis a context d] c['+both(*guards,*('k ba['+value+']' for value in (distance,t,x)),
        'k bg['+zero+' '+distance+']','k bg['+zero+' '+t+']','k sca['+x+' '+zero+']',
        'k sca['+distance+' k shv['+w+' '+t+']]','k sca['+t+' k sje['+distance+' '+w+']]')+'].\n'
    text+='d sog[event a axis a context d] c['+both(*guards,*('k ba['+value+']' for value in (target,a,distance)),
        'k sca['+target+' k sob['+V+' '+v+' '+a+' '+distance+']]')+'].\n'
    text+='''
d soh[axis a context d] c[k sod[k zfa[v axis] k zfb[v axis] v axis v context]].
d soi[context d] c[w[k soh[k yo[] v context]][k soh[k yp[] v context]]].
d soj[] e[b context[k soi[k zb6[]]]].
d sok[] e[b context[k soh[k yo[] k zb6[]]]].
d sol[] e[b context[k soe[k wj[k zfb[k yo[]]] k yo[] k zb6[]]]].
d som[] e[b context[k sof[k wj[k zfb[k yo[]]] k yo[] k zb6[]]]].
d son[] e[b context[w[k soh[k yo[] k zb6[]]][k sof[k wj[k zfb[k yo[]]] k yo[] k zb6[]]]]].
d soo[] e[b context[k sog[k wj[k zfb[k yo[]]] k yo[] k zb6[]]]].
d sop[] e[b context[w[k soh[k yp[] k zb6[]]][k sof[k wj[k zfb[k yp[]]] k yp[] k zb6[]]]]].
d soq[] e[b context[k sog[k wj[k zfb[k yp[]]] k yp[] k zb6[]]]].
'''
    doc=parse(text);doc['statements']=statements
    doc=parse(format_graph(doc,'compact')+'''
s[w[k ug[k zfg[] k rd[] r[k soj[]] k rh[] k ri[]]][k zep[k zfg[] k rd[] k ze6[] k rh[] k ri[]]]].
s[k zc[k zfc[] k rd[] r[k sok[]] r[k sol[]] k rh[] k ri[]]].
s[k zc[k zfd[] k rd[] r[k sok[]] r[k som[]] k rh[] k ri[]]].
s[k zd3[k zfe[] k rd[] r[k son[]] r[k sol[]] r[k soo[]] k rh[] k ri[]]].
s[w[k zc[k zff[] k rd[] r[k sop[]] r[k soq[]] k rh[] k ri[]]][k zep[k zff[] k rd[] k zfe[] k rh[] k ri[]]]].
''')
    basis=deepcopy(json.loads((ROOT/'data/einstein-longitudinal-light-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='einstein-transverse-space-basis-v1',document='examples/v014/einstein-transverse-space.noema')
    basis['definitions'].update(MEANINGS|{
        'soa':'異なる三座標役割のうち、yまたはzを選ぶ。縦方向と重複した横軸を受理しない。',
        'sob':'同じ速度と係数によるa*V*distance/√(V²-v²)の実切断の式。分母と入力の条件は呼出側で要求する。',
        'soc':'選択した横軸の正方向へ共通零点から進む同じ光線を両系の区間に結ぶ。x′=0、運動系のξ=0、非選択の横座標=0を要求する。静止系の光路長は斜めの経路の平方和へ結ぶ。',
        'sod':'同じ横方向の光線の設定、両系での同じ全速さV、先行する同じτの式を結ぶ。',
        'soe':'選んだ横軸の同じ到達出来事について、運動系座標=Vτ=V*a*(t-v*x′/(V²-v²))を要求する。',
        'sof':'同じ横方向の光線上で、静止系の横距離=√(V²-v²)*t、t=横距離/√(V²-v²)、x′=0を同時に要求する。',
        'sog':'同じ到達出来事で運動系の横座標=a*V*静止系横座標/√(V²-v²)と要求する。',
        'soh':'指定軸に対応する両系の区間記録を同じ軸と設定のsodへ渡す。',
        'soi':'同じ設定のy,z両方の光線の前提を要求する。一方の光線だけでは満たさない。',
        'soj':'両横軸の光線を同様に考察するという設定内容。',
        'sok':'y方向の光線に固定した前提内容。',
        'sol':'y方向の光線上のη=Vτとτの式の代入という内容。',
        'som':'y方向の光線上の時刻とx′=0という内容。',
        'son':'同じy方向の光線の前提と、時刻・x′の値をそろえた代入前提。',
        'soo':'y方向の光線上で得るη=a*V*y/√(V²-v²)という内容。',
        'sop':'同じz方向の光線の前提と、時刻・x′の値をそろえた代入前提。',
        'soq':'z方向の光線上で得るζ=a*V*z/√(V²-v²)という内容。'})
    decls={d['name']:d for d in doc['declarations']}
    for name,args,meaning in (
        ('zfa',['axis_role'],'選択した横軸の光線を静止系で測る区間記録。軸ごとに別の光を許す。'),
        ('zfb',['axis_role'],'同じ横軸の光線を運動系で測る区間記録。両系の光と始終出来事はsocで同一に結ぶ。'),
        ('zfc',[],'y方向の光線にη=Vτとτの代入式を与える箇所。'),
        ('zfd',[],'その光線についてt=y/√(V²-v²)とx′=0を併記する箇所。'),
        ('zfe',[],'その値を代入してηの式を提示する箇所。'),
        ('zff',[],'もう一方の横方向についてζの式を提示する箇所。'),
        ('zfg',[],'先行する縦方向と同様に、両横方向の光線を考察する箇所。')):
        d=decls[name];basis['primitives'].append(dict(symbol=name,parameters=d['parameters'],result=d['result'],arguments=args,meaning_ja=meaning))
    basis['unresolved']+=generic_composed()[1]['unresolved'][-1:]+[
        'u0073〜u0080の部分記述。原点から正方向へ出る光線という先行設定を両横軸へ適用する。原文の省略との過不足、原刊照合は未完。',
        '静止系の光路長を両端の縦・横変位の平方和へ結ぶ直線的な幾何を明示的に要求した。物理的な全光路の幾何の証明ではない。',
        'z方向にもy方向と同じ形の時刻・x′条件を明示して、同様の議論として接続した。省略された推論を完全に検証したことは意味しない。',
        '有理数の補題と構成済み切断の検査を、一般の平方根・体の法則の証明としない。光線外への拡張と、全文の意味一致は未完。']
    audit_basis(doc,basis)
    return format_graph(doc,'compact')+'\n',basis


def main():
    for compose,name in ((generic_composed,'transverse-space'),(source_composed,'einstein-transverse-space')):
        text,basis=compose()
        for filename,body in ((basis['document'],text),('data/'+name+'-basis-v1.json',json.dumps(basis,ensure_ascii=False,indent=2)+'\n')):
            path=ROOT/filename
            if path.exists():
                if path.read_text(encoding='utf-8')!=body:raise ValueError('Stored transverse space differs: '+filename)
            else:
                with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(body)
    print('Transverse light coordinates, component speeds and both axes composed')


if __name__=='__main__':main()
