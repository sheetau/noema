"""Connect a physical sphere's surface events to one frame's time slice."""
from copy import deepcopy
import json

from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from scripts.compose_moving_light_trip import ROOT, both
from scripts.compose_affine_time_form import CUT


def definitions():
    return '''
d ssu[radius b x b y b z b] c[w[k aa[n p a b v radius]][e[k ab[k ad[v x v x] k ab[k ad[v y v y] k ad[v z v z]]]][k ad[v radius v radius]]]].
d ssv[light b speed b beta b radius b x b y b z b time b] c[w[k sra[v light v speed v beta]][k ssu[v radius k ad[v beta k ab[v x k ac[k ad[v speed v time]]]] v y v z]]].
d ssw[beta b radius b longitudinal b transversey b transversez b] c[w[k aa[n p a b v beta]][w[k aa[n p a b v radius]][w[k aa[n p a b v longitudinal]][w[e[k ad[v beta v longitudinal]][v radius]][w[e[v transversey][v radius]][e[v transversez][v radius]]]]]]].
d ssx[longitudinal b radius b x b y b z b] c[w[k aa[n p a b v longitudinal]][w[k aa[n p a b v radius]][e[k ab[k ad[k ad[v radius v radius] k ad[v x v x]] k ad[k ad[v longitudinal v longitudinal] k ab[k ad[v y v y] k ad[v z v z]]]]][k ad[k ad[v longitudinal v longitudinal] k ad[v radius v radius]]]]]].
'''


MEANINGS={
    'ssu':'正の半径の球面の有理数条件。内部を含む球体とは区別する。',
    'ssv':'許容速度と正のβの下で、中心x=v*tの移動を含む球面の時空的な集合の有理数条件。',
    'ssw':'βとの積が半径になる正の縦半軸と、元の半径に等しい二つの横半軸。直径ではない。',
    'ssx':'正の縦半軸と等しい二横半軸を持つ回転楕円体の表面条件。正の分母を払った形で書く。'}


def generic_composed():
    doc=parse((ROOT/'examples/v014/transverse-rod-scale.noema').read_text(encoding='utf-8')+definitions())
    basis=deepcopy(json.loads((ROOT/'data/transverse-rod-scale-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='sphere-slice-basis-v1',document='examples/v014/sphere-slice.noema')
    basis['definitions'].update(MEANINGS)
    basis['unresolved']+=['幾何学的な球面と物体の剛性を区別する。断面を選ぶ時刻と座標系を明示する。']
    audit_basis(doc,basis)
    return format_graph(doc,'compact')+'\n',basis


def source_composed():
    doc=parse((ROOT/'examples/v014/einstein-transverse-rod-scale.noema').read_text(encoding='utf-8'))
    statements,doc['statements']=doc['statements'],[]
    text=format_graph(doc,'compact')+definitions();zero='k bb[n p a b]';one='k bb[n p b b]'
    mul=lambda a,b:'k shv['+a+' '+b+']';add=lambda a,b:'k bd['+a+' '+b+']'
    coord=lambda record,role:'k zc6['+record+' k '+role+'[]]'
    square=lambda value:mul(value,value)
    sumsq=lambda x,y,z:add(square(x),add(square(y),square(z)))
    text+='d ssy[radius '+CUT+' x '+CUT+' y '+CUT+' z '+CUT+'] c['+both(*('k ba[v '+n+']' for n in ('radius','x','y','z')),
        'k bg['+zero+' v radius]','k sca['+sumsq('v x','v y','v z')+' '+square('v radius')+']')+'].\n'
    xyz=[coord('v record',role) for role in ('yn','yo','yp')];t=coord('v record','zc7')
    V='k tc[]';v='k zb7[]';beta='k soy['+V+' '+v+']'
    text+='d ssz[record a radius '+CUT+'] c[w[k sha[v record p ba]][k ssy[v radius '+' '.join(xyz)+']]].\n'
    text+='d sta[object a] c[w[k zbq[v object k zb6[]]][k xm[v object k ra[] k zb6[]]]].\n'
    text+='d stb[object a] c[w[k ca[v object]][k xm[v object k ra[] k zb6[]]]].\n'
    text+='d stc[record a radius '+CUT+'] c['+both('k sha[v record p ba]','k srd['+V+' '+v+' '+beta+']',
        'k ssy[v radius '+mul(beta,'k sin['+v+' '+xyz[0]+' '+t+']')+' '+xyz[1]+' '+xyz[2]+']')+'].\n'
    text+='d std[record a radius '+CUT+'] c[w[k stc[v record v radius]][k sca['+t+' '+zero+']]].\n'
    ratio='k sje['+v+' '+V+']'
    text+='d ste[] '+CUT+'[k sky[k bf['+one+' '+square(ratio)+']]].\n'
    denominator=square('k ste[]')
    text+='d stf[record a radius '+CUT+'] c['+both('k sha[v record p ba]','k srd['+V+' '+v+' '+beta+']','k sbg[v radius]',
        'k sbg[k ste[]]','k sca['+t+' '+zero+']',
        'k sca['+add('k sje['+square(xyz[0])+' '+denominator+']',add(square(xyz[1]),square(xyz[2])))+' '+square('v radius')+']')+'].\n'
    text+='d stg[radius '+CUT+' longitudinal '+CUT+' transversey '+CUT+' transversez '+CUT+'] c['+both(
        'k srd['+V+' '+v+' '+beta+']',*('k sbg[v '+n+']' for n in ('radius','longitudinal','transversey','transversez')),
        'k sca['+mul(beta,'v longitudinal')+' v radius]','k sca[v longitudinal '+mul('v radius','k ste[]')+']',
        'k sca[v transversey v radius]','k sca[v transversez v radius]')+'].\n'
    text+='d sth[radius '+CUT+'] '+CUT+'[k sje[v radius '+beta+']].\n'
    text+='d sti[longitudinal '+CUT+' radius '+CUT+' x '+CUT+' y '+CUT+' z '+CUT+'] c['+both('k sbg[v longitudinal]','k sbg[v radius]',
        *('k ba[v '+n+']' for n in ('x','y','z')),
        'k sca['+add('k sje['+square('v x')+' '+square('v longitudinal')+']','k sje['+add(square('v y'),square('v z'))+' '+square('v radius')+']')+' '+one+']')+'].\n'
    text+='d stj[record a radius '+CUT+'] c['+both('k sha[v record p ba]','k srd['+V+' '+v+' '+beta+']',
        'k sca['+t+' '+zero+']','k sti[k sth[v radius] v radius '+' '.join(xyz)+']')+'].\n'
    text+='r zhr[a a i[h[a a] c] j[i[h[a] c]] a d] c.r zht[] a.\n'
    text+='r zhu[a a d] c.r zhv[a a a d] c.r zhw[] a.r zhx[] '+CUT+'.r zhy[] a.r zhz[] a.r zh2[] a.r zh3[] a.r zh4[] a.\n'
    def surface_graph(frame,formula,zero_slice=False):
        chart='k shd[v event v record k '+frame+'[] v setting]'
        selected=both('k zc4[v event]',chart,*(['k sca['+t+' '+zero+']'] if zero_slice else []))
        member='k zhu[v body v event v setting]'
        return both('g event a[g record a['+both(selected,member)+']]',
            'f event a[f record a[y['+selected+'][z['+member+'][k '+formula+'[v record v radius]]]]]',
            'f event a[y['+member+']['+both('k zc4[v event]',
                'g record a['+chart+']')+']]')
    setup=both('k zbq[v body v setting]','k x4[v body k zbm[] v setting]','k sbg[v radius]',
        'k zbv[k zbm[] k zbn[k zbm[] v setting] v setting]',
        'k zhv[v body k zbn[k zbm[] v setting] k zbm[] v setting]',
        'k zgj[k zbm[] k ra[] k zbo[k ra[] k yn[] v setting] '+v+' k ta[] k rb[] v setting]')
    text+='d stk[body a radius '+CUT+' setting d] c['+both(setup,surface_graph('zbm','ssz'))+'].\n'
    text+='d stl[body a radius '+CUT+' setting d] c['+surface_graph('ra','stc')+'].\n'
    text+='d stm[body a radius '+CUT+' setting d] c['+surface_graph('ra','stf',True)+'].\n'
    body='k zhw[]';radius='k zhx[]';setting='k zb6[]'
    text+='d stn[] e[b context[k stk['+body+' '+radius+' '+setting+']]].\n'
    text+='d sto[] e[b context['+both('t[k stn[]][v context]','t[k sso[]][v context]','t[k shi[]][v context]')+']].\n'
    text+='d stp[] e[b context[k stl['+body+' '+radius+' '+setting+']]].\n'
    text+='d stq[] e[b context[k stm['+body+' '+radius+' '+setting+']]].\n'
    text+='d str[] e[b context[k stg['+radius+' k sth['+radius+'] '+radius+' '+radius+']]].\n'
    text+='d sts[] e[b context['+both('t[k stq[]][v context]','t[k str[]][v context]',
        'f event a[f record a[y['+both('k zc4[v event]','k shd[v event v record k ra[] '+setting+']','k sca['+t+' '+zero+']')+'][z[k zhu['+body+' v event '+setting+']][k stj[v record '+radius+']]]]]')+']].\n'
    doc=parse(text);doc['statements']=statements
    doc=parse(format_graph(doc,'compact')+'''
s[k zhr[k zht[] k rd[] r[p ssn] l[i[h[a] c]][r[p sta] r[p stb]] k rh[] k ri[]]].
s[k ug[k zhy[] k rd[] r[k stn[]] k rh[] k ri[]]].
s[k zc[k zhz[] k rd[] r[k sto[]] r[k stp[]] k rh[] k ri[]]].
s[k zc[k zh2[] k rd[] r[k stp[]] r[k stq[]] k rh[] k ri[]]].
s[k zc[k zh3[] k rd[] r[k stq[]] r[k sts[]] k rh[] k ri[]]].
s[k uh[k zh4[] k rd[] r[k str[]] k rh[] k ri[]]].
''')
    basis=deepcopy(json.loads((ROOT/'data/einstein-transverse-rod-scale-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='einstein-sphere-slice-basis-v1',document='examples/v014/einstein-sphere-slice.noema')
    basis['definitions'].update(MEANINGS|{
        'ssy':'有効な実切断による正の半径の球面条件。中心からの三座標の二乗和が半径の二乗に等しい。',
        'ssz':'同じ有効な四座標記録の空間三成分を球面条件へ渡す。時刻は球面の静止側の位置条件へ混ぜない。',
        'sta':'節題が対象とする、指定設定で静止系に対して動く剛な物体の性質。',
        'stb':'節題が対象とする、指定設定で静止系に対して動く時計の性質。',
        'stc':'静止系の記録に、β(x-v*t)、y、zを使った移動する球面の条件を与える。光の波面の拡大とは区別する。',
        'std':'stcで静止系の時刻t=0を選んだ断面。',
        'ste':'本文の√(1-(v/V)²)。srdの許容速度の下で正の値として使う。',
        'stf':'t=0でx²/(√(1-(v/V)²))²+y²+z²=R²を要求する。平方根を落として分母を二重に二乗しない。',
        'stg':'縦半軸R/β=R*√(1-(v/V)²)と、二つの横半軸Rを結ぶ。正の中心から表面までの距離であり直径ではない。',
        'sth':'候補の縦半軸R/β。正当な半径とβの条件は呼出側で要求する。',
        'sti':'正の縦半軸aと共通の横半軸Rを使う回転楕円体の表面条件x²/a²+(y²+z²)/R²=1。',
        'stj':'静止系でt=0の記録が、R/βとRを半軸とする回転楕円体の表面にあること。',
        'stk':'同じ剛な物体が移動系で静止し、中心がその原点にあり、正の半径の球面条件と物体表面の出来事が対象範囲で過不足なく一致する。',
        'stl':'同じ物体表面の出来事が静止系の記録を持ち、移動する球面の時空条件と過不足なく一致する。',
        'stm':'静止系で時刻零の非空の断面を選び、その断面内で物体表面への所属と本文の楕円体式を過不足なく結ぶ。零時刻外の出来事を零時刻の形へ混ぜない。',
        'stn':'正の半径、移動系で静止する球、中心の原点との一致という設定内容。',
        'sto':'球の設定に最終の座標式と両系での記録の存在を合わせた変換の前提。',
        'stp':'静止系で記述した同じ物体表面の時空条件という内容。',
        'stq':'静止系の時刻零での断面の方程式という内容。',
        'str':'回転楕円体の三つの正の半軸の値という内容。',
        'sts':'同じ時刻零の表面を回転楕円体の表面条件と半軸へ結ぶ内容。'})
    decls={d['name']:d for d in doc['declarations']}
    for name,args,meaning in (
        ('zhr',['node','author','equations','subject_properties','scope','context'],'著者が節題で、指定した方程式の物理的な意味を指定した対象の性質について検討すると示す。本文の結論を節題から補わない。'),
        ('zht',[],'動く剛体と時計について方程式の物理的意味を扱う§4の節題。'),
        ('zhu',['body','event','setting'],'出来事が同じ物体の物理的な表面上に属する。座標方程式への適合とは独立に与え、内部や別物体の表面と区別する。物質的な境界の一般的構成は未完。'),
        ('zhv',['body','place','frame','setting'],'指定系での物体の幾何学的中心がその場所にある。半径や球面性はこの関係だけでは与えない。'),
        ('zhw',[],'§4で検討する同じ剛な物体。球形はstkの条件で与え、識別子だけでは決めない。'),
        ('zhx',[],'物体の静止側で測る正の半径Rの候補。'),
        ('zhy',[],'移動系で静止する中心原点の球を設定する箇所。'),
        ('zhz',[],'同じ球面へ最終の座標変換式を適用する箇所。'),
        ('zh2',[],'静止系でt=0の表面方程式を述べる箇所。'),
        ('zh3',[],'動く球の同時刻の形を回転楕円体として述べる箇所。'),
        ('zh4',[],'回転楕円体の軸の値を示す箇所。本文のRという値に合わせて半軸として読む。')):
        d=decls[name];basis['primitives'].append(dict(symbol=name,parameters=d['parameters'],result=d['result'],arguments=args,meaning_ja=meaning))
    basis['unresolved']+=[
        'u0109〜u0115の部分記述。剛性・物理的な表面・中心の一般的構成、連続空間の記録範囲、原刊照合と原文との意味一致は未完。',
        '本文の軸R/β,R,Rは中心からの半軸として明示した。端から端までの軸長はその二倍であり、両者を同じ値にしない。',
        '両系で同時刻を選ぶと一般には別の出来事集合になる。球の静止側の球面性を、静止系で同時の二出来事が移動系でも同時であるという仮定へ変えない。',
        '静止系の零時刻断面の非空性はstmで要求する。実際の全空間・全時刻でその測定が可能なことや、一般の実切断の体の法則は有限の検査で証明しない。',
        '光速での極限、超光速に対する留保、任意形状と時計への帰結は後続の本文として未接続。']
    audit_basis(doc,basis)
    return format_graph(doc,'compact')+'\n',basis


def main():
    for compose,name in ((generic_composed,'sphere-slice'),(source_composed,'einstein-sphere-slice')):
        text,basis=compose()
        for filename,body in ((basis['document'],text),('data/'+name+'-basis-v1.json',json.dumps(basis,ensure_ascii=False,indent=2)+'\n')):
            path=ROOT/filename
            if path.exists():
                if path.read_text(encoding='utf-8')!=body:raise ValueError('Stored sphere slice differs: '+filename)
            else:
                with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(body)
    print('Physical sphere, frame-bound surface slice and semiaxes composed')


if __name__=='__main__':main()
