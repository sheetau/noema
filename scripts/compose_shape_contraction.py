"""Compose arbitrary spatial predicates, directional widths and a boundary limit."""
from copy import deepcopy
import json

from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from scripts.compose_sphere_slice import ROOT, CUT
from scripts.compose_limits import call as k, app, op, both, quant as q, lam

SHAPE='h['+' '.join([CUT]*3)+'] c'
DOMAIN='h['+CUT+'] c'
ZERO='n p a b'; ONE='n p b b'; TWO='n p c b'
v=lambda name:'v '+name


def definition(name,params,body,result='c'):
    return 'd '+name+'['+params+'] '+result+'['+body+'].\n'


def rational_definitions():
    V,s,f,L,eps,delta=map(v,('light','speed','factor','length','epsilon','delta'))
    mul=lambda a,b:k('ad',a,b);sq=lambda a:mul(a,a)
    sub=lambda a,b:k('ab',a,k('ac',b));lt=lambda a,b:k('aa',a,b)
    text=definition('stt','light b speed b factor b',both(lt(ZERO,V),lt(sq(s),sq(V)),lt(ZERO,f),op('e',mul(sq(V),sq(f)),sub(sq(V),sq(s)))))
    text+=definition('stu','light b length b epsilon b delta b',both(lt(ZERO,V),lt(ZERO,L),lt(ZERO,eps),lt(ZERO,delta),
        op('e',mul(mul(TWO,k('ab',sq(L),sq(eps))),delta),mul(V,sq(eps)))))
    return text


GENERIC_MEANINGS={
    'stt':'光速未満の符号付き速度と、正の縦方向の縮小率。有理数の多項式条件で表す。',
    'stu':'正の光速・長さ・精度について、delta=V*epsilon²/(2*(length²+epsilon²))を分母を払って表す。極限の近傍の候補。'}


def generic_composed():
    doc=parse((ROOT/'examples/v014/sphere-slice.noema').read_text(encoding='utf-8')+rational_definitions())
    basis=deepcopy(json.loads((ROOT/'data/sphere-slice-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='shape-contraction-basis-v1',document='examples/v014/shape-contraction.noema')
    basis['definitions'].update(GENERIC_MEANINGS)
    basis['unresolved']+=['多項式の極限評価を、実切断上の全域的な極限の機械的証明とは扱わない。']
    audit_basis(doc,basis)
    return format_graph(doc,'compact')+'\n',basis


def source_composed():
    doc=parse((ROOT/'examples/v014/einstein-sphere-slice.noema').read_text(encoding='utf-8'))
    statements,doc['statements']=doc['statements'],[]
    text=format_graph(doc,'compact')+rational_definitions()
    z=k('bb',ZERO);one=k('bb',ONE);two=k('bb',TWO)
    mul=lambda a,b:k('shv',a,b);sq=lambda a:mul(a,a)
    sub=lambda a,b:k('bf',a,b);lt=lambda a,b:k('bg',a,b);eq=lambda a,b:k('sca',a,b)
    positive=lambda a:k('sbg',a);valid=lambda a:k('ba',a)
    coord=lambda record,axis:k('zc6',record,k(axis))
    V,s,t=map(v,('light','speed','instant'));beta=k('soy',V,s)
    admissible=k('srd',V,s,beta)
    text+=definition('stw','light '+CUT+' speed '+CUT,k('sky',sub(one,sq(k('sje',s,V)))),CUT)
    text+=definition('stx','light '+CUT+' speed '+CUT+' factor '+CUT,both(admissible,positive(v('factor')),
        eq(v('factor'),k('stw',V,s)),eq(mul(beta,v('factor')),one)))
    # Time-independent predicates may describe disconnected or open shapes.
    xyz=list(map(v,('x','y','z')))
    transformed=app(v('shape'),mul(beta,sub(xyz[0],mul(s,t))),*xyz[1:])
    text+=definition('stv','shape '+SHAPE+' light '+CUT+' speed '+CUT+' instant '+CUT,
        'i[x '+CUT+' y '+CUT+' z '+CUT+']['+both(admissible,valid(t),*(valid(a) for a in xyz),transformed)+']',SHAPE)
    coords=[coord(v('record'),axis) for axis in ('yn','yo','yp')]
    text+=definition('sty','shape '+SHAPE+' light '+CUT+' speed '+CUT+' record a',both(k('sha',v('record'),'p ba'),
        app(k('stv',v('shape'),V,s,coord(v('record'),'zc7')),*coords)))
    text+=definition('stz','shape '+SHAPE+' record a',both(k('sha',v('record'),'p ba'),app(v('shape'),*coords)))
    def graph(formula,selected_time=False):
        chart=k('shd',v('event'),v('record'),v('frame'),v('setting'))
        selected=both(k('zc4',v('event')),chart,*([eq(coord(v('record'),'zc7'),t)] if selected_time else []))
        member=k('zhu',v('body'),v('event'),v('setting'))
        shape=k(formula,v('shape'),*([V,s] if formula=='sty' else []),v('record'))
        return both(q('g','event','a',q('g','record','a',both(selected,member))),
            q('f','event','a',q('f','record','a',op('y',selected,op('z',member,shape)))),
            q('f','event','a',op('y',member,both(k('zc4',v('event')),q('g','record','a',chart)))))
    text+=definition('sua','body a shape '+SHAPE+' frame a setting d',both(k('zbq',v('body'),v('setting')),
        k('x4',v('body'),v('frame'),v('setting')),graph('stz')))
    text+=definition('sub','body a shape '+SHAPE+' frame a light '+CUT+' speed '+CUT+' instant '+CUT+' setting d',
        both(admissible,valid(t),graph('sty',True)))
    # Same observed time is required; comoving time need not be equal.
    params='first a last a firstmoving a lastmoving a light '+CUT+' speed '+CUT
    unit='i[value '+CUT+']['+one+']'
    text+=definition('suc',params,both(k('sre',v('first'),v('firstmoving'),V,s,unit),
        k('sre',v('last'),v('lastmoving'),V,s,unit),eq(coord(v('first'),'zc7'),coord(v('last'),'zc7'))))
    differences=[]
    for axis in ('yn','yo','yp'):
        observed=sub(coord(v('last'),axis),coord(v('first'),axis))
        proper=sub(coord(v('lastmoving'),axis),coord(v('firstmoving'),axis))
        differences.append(eq(observed,mul(k('stw',V,s),proper) if axis=='yn' else proper))
    text+=definition('sud',params,both(k('suc',*(v(n) for n in ('first','last','firstmoving','lastmoving','light','speed'))),*differences))
    # The observed slice must exist; all event records must participate in the transform.
    params='body a shape '+SHAPE+' observer a resting a light '+CUT+' speed '+CUT+' instant '+CUT+' setting d'
    charts=both(k('shd',v('event'),v('first'),v('observer'),v('setting')),k('shd',v('event'),v('second'),v('resting'),v('setting')))
    text+=definition('sue',params,both(admissible,valid(t),op('u',op('e',v('observer'),v('resting'))),
        k('sua',v('body'),v('shape'),v('resting'),v('setting')),
        k('zgj',v('resting'),v('observer'),k('zbo',v('observer'),k('yn'),v('setting')),s,k('ta'),k('rb'),v('setting')),
        q('f','event','a',op('y',k('zc4',v('event')),q('g','first','a',q('g','second','a',charts)))),
        q('f','event','a',q('f','first','a',q('f','second','a',op('y',both(k('zc4',v('event')),charts),k('sre',v('first'),v('second'),V,s,unit))))),
        q('g','event','a',q('g','record','a',both(k('zc4',v('event')),k('zhu',v('body'),v('event'),v('setting')),
            k('shd',v('event'),v('record'),v('observer'),v('setting')),eq(coord(v('record'),'zc7'),t))))))
    args=[v(n) for n in ('body','shape','observer','resting','light','speed','instant','setting')]
    text+=definition('suf',params,op('y',k('sue',*args),k('sub',v('body'),v('shape'),v('observer'),V,s,t,v('setting'))))
    for name,observer,resting,speed in [('sug','ra','zbm',k('zb7')),('suh','zbm','ra',sub(z,k('zb7')))]:
        claim=k('suf',v('body'),v('shape'),k(observer),k(resting),k('tc'),speed,t,k('zb6'))
        text+=definition(name,'','b context['+q('f','body','a',q('f','shape',SHAPE,q('f','instant',CUT,claim)))+']','e')
    # Coordinate projections and tight bounds describe width without assuming extrema exist.
    axes=op('x',op('e',v('axis'),k('yn')),op('x',op('e',v('axis'),k('yo')),op('e',v('axis'),k('yp'))))
    selected=op('x',both(op('e',v('axis'),k('yn')),eq(v('value'),v('x'))),op('x',both(op('e',v('axis'),k('yo')),eq(v('value'),v('y'))),both(op('e',v('axis'),k('yp')),eq(v('value'),v('z')))))
    projection=both(*(valid(a) for a in xyz),app(v('shape'),*xyz),selected)
    for name in reversed(('x','y','z')):projection=q('g',name,CUT,projection)
    text+=definition('sui','shape '+SHAPE+' axis a value '+CUT,both(valid(v('value')),axes,
        *(op('u',op('e',k(a),k(b))) for a,b in (('yn','yo'),('yn','yp'),('yo','yp'))),projection))
    inside=lambda value:both(valid(value),app(v('domain'),value))
    low,high,bound=map(v,('lower','upper','bound'))
    bounds=both(k('bc',low,v('value')),k('bc',v('value'),high))
    upper=q('f','value',CUT,op('y',inside(v('value')),k('bc',v('value'),bound)))
    lower=q('f','value',CUT,op('y',inside(v('value')),k('bc',bound,v('value'))))
    text+=definition('suj','domain '+DOMAIN+' lower '+CUT+' upper '+CUT,both(valid(low),valid(high),
        q('g','value',CUT,inside(v('value'))),q('f','value',CUT,op('y',inside(v('value')),bounds)),
        q('f','bound',CUT,op('y',valid(bound),both(op('y',upper,k('bc',high,bound)),op('y',lower,k('bc',bound,low)))))))
    projection=lam('value',CUT,k('sui',v('shape'),v('axis'),v('value')))
    text+=definition('suk','shape '+SHAPE+' axis a width '+CUT,both(valid(v('width')),q('g','lower',CUT,q('g','upper',CUT,
        both(k('suj',projection,low,high),eq(v('width'),sub(high,low)))))))
    widths=[v(n) for n in ('properx','propery','properz','observedx','observedy','observedz')]
    widthconditions=[]
    for i,axis in enumerate(('yn','yo','yp')):
        widthconditions.extend([k('suk',v('shape'),k(axis),widths[i]),k('suk',k('stv',v('shape'),V,s,t),k(axis),widths[i+3])])
    text+=definition('sul','shape '+SHAPE+' light '+CUT+' speed '+CUT+' instant '+CUT+' '+' '.join(n+' '+CUT for n in ('properx','propery','properz','observedx','observedy','observedz')),
        op('y',both(admissible,valid(t),*widthconditions),both(eq(widths[3],mul(k('stw',V,s),widths[0])),eq(widths[4],widths[1]),eq(widths[5],widths[2]))))
    body=k('sul',v('shape'),V,s,t,*widths)
    for name in reversed(('shape','instant','properx','propery','properz','observedx','observedy','observedz')):
        body=q('f',name,SHAPE if name=='shape' else CUT,body)
    text+=definition('suv','light '+CUT+' speed '+CUT,'b context['+body+']','e')
    text+=definition('sum','','b context[t[k suv[k tc[] k zb7[]]][v context]]','e')
    text+=definition('suu','','b context['+both('t[k suh[]][v context]',
        't['+k('suv',k('tc'),sub(z,k('zb7')))+'][v context]')+']','e')
    other=v('other')
    text+=definition('sus','light '+CUT+' speed '+CUT+' other '+CUT,
        op('y',both(admissible,k('srd',V,other,k('soy',V,other)),lt(sq(s),sq(other))),lt(k('stw',V,other),k('stw',V,s))))
    text+=definition('sut','','b context['+q('f','speed',CUT,q('f','other',CUT,k('sus',k('tc'),s,other)))+']','e')
    # A quantified boundary limit has no evaluation at v=V and never constructs beta there.
    L,eps,delta=map(v,('length','epsilon','delta'))
    text+=definition('sun','light '+CUT+' length '+CUT+' epsilon '+CUT,k('sje',mul(V,sq(eps)),mul(two,k('bd',sq(L),sq(eps)))),CUT)
    domain=both(valid(s),k('bc',z,s),lt(s,V))
    near=both(domain,lt(sub(V,s),delta))
    text+=definition('suo','light '+CUT+' delta '+CUT,both(positive(V),positive(delta),q('g','speed',CUT,near)))
    small=both(valid(mul(L,k('stw',V,s))),k('bc',z,mul(L,k('stw',V,s))),lt(mul(L,k('stw',V,s)),eps))
    text+=definition('sup','light '+CUT+' length '+CUT,both(positive(V),positive(L),
        q('f','delta',CUT,op('y',positive(delta),k('suo',V,delta))),
        q('f','epsilon',CUT,op('y',positive(eps),q('g','delta',CUT,both(positive(delta),q('f','speed',CUT,op('y',near,small))))))))
    text+=definition('suq','','b context['+q('f','length',CUT,op('y',positive(L),k('sup',k('tc'),L)))+']','e')
    text+=definition('sur','','b context['+q('f','speed',CUT,q('f','beta',CUT,op('y',both(valid(s),valid(v('beta')),valid(k('tc')),
        op('u',lt(sq(s),sq(k('tc'))))),op('u',k('srd',k('tc'),s,v('beta'))))))+']','e')
    text+='r zh5[] a.r zh6[] a.r zh7[] a.r zia[] a.r zib[] a.r zic[] a.\n'
    doc=parse(text);doc['statements']=statements
    doc=parse(format_graph(doc,'compact')+'''
s[k uh[k zh5[] k rd[] r[k sug[]] k rh[] k ri[]]].
s[k uh[k zh6[] k rd[] r[k sum[]] k rh[] k ri[]]].
s[k uh[k zic[] k rd[] r[k sut[]] k rh[] k ri[]]].
s[k zfl[k zh7[] k rd[] r[k sug[]] r[k suq[]] k rh[] k ri[]]].
s[k uh[k zia[] k rd[] r[k sur[]] k rh[] k ri[]]].
s[k uh[k zib[] k rd[] r[k suu[]] k rh[] k ri[]]].
s[k zdg[k zib[] k rd[] r[k suu[]] k rh[] k ri[]]].
''')
    basis=deepcopy(json.loads((ROOT/'data/einstein-sphere-slice-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='einstein-shape-contraction-basis-v1',document='examples/v014/einstein-shape-contraction.noema')
    basis['definitions'].update(GENERIC_MEANINGS|{
        'stv':'任意の時間に依存しない三座標の形の条件を、β(x-v*t),y,zの代入で観測系の同時刻の形に変換する。',
        'stw':'速度を引数とする√(1-(v/V)²)の候補値。許容域は呼出側が明示する。',
        'stx':'許容速度、正の縮小率、平方根の式、βとの積1を結ぶ。',
        'sty':'観測系の四座標記録を、任意形状の変換条件に適用する。',
        'stz':'物体の静止系の四座標記録を、時間に依存しない任意形状の条件に適用する。',
        'sua':'同じ剛な物体が指定系で静止し、物理的な表面と形状条件が全測定記録で一致する。表面と測定範囲は非空。',
        'sub':'指定した観測系の同時刻で、同じ物体表面と変換された任意形状が全測定記録で一致する。断面は非空。',
        'suc':'同じ観測時刻の二記録と、それぞれに対応する物体静止系の記録を最終の四式で結ぶ。',
        'sud':'sucの下で縦の符号付き座標差が縮小率倍、二つの横の差が不変である。物体静止系での同時性は要求しない。',
        'sue':'同じ剛体の静止形、二つの異なる系、運動と単位、全出来事の両系の測定と四式、観測時刻の非空の表面を結ぶ前提。',
        'suf':'sueから同じ物体の観測時刻の形subへの条件付き帰結。',
        'sug':'全ての物体・形状条件・観測時刻について、Kからkに静止する物体を見る場合のsufを述べる内容。',
        'suh':'全ての物体・形状条件・観測時刻について、kからKに静止する物体を見る場合のsuf。速度を反転し、両系の役割を交換する。',
        'sui':'有効な三座標で指定形状を満たす点の、指定した座標軸への射影。',
        'suj':'有効な実切断の非空の集合に対する下限と上限。最大の下界と最小の上界を要求し、集合内の達成点は要求しない。',
        'suk':'形状の指定軸への射影の上限と下限の差。空集合や無限幅に有限の幅を割り当てない。',
        'sul':'変換前後の三つの有限幅が定義される場合、縦幅が縮小率倍、横幅が不変となる条件付き帰結。',
        'sum':'対象速度での任意形状・任意時刻・定義される幅についてsulを述べる内容。球面性は要求しない。',
        'suv':'指定した光速と符号付き速度で、任意形状・時刻・定義される幅についてsulを述べる一般の内容。',
        'suu':'系と速度を反転した形状の帰結suhと、逆速度における三軸の幅の帰結suvを合わせる。',
        'sus':'許容された二つの符号付き速度について、速さの二乗が大きい方で正の縮小率が小さくなる条件付き帰結。',
        'sut':'全ての許容された速度対でsusを述べる内容。向きが逆の速度も速さの二乗で比較する。',
        'sun':'正のV・長さ・精度に対する近傍半径V*epsilon²/(2*(length²+epsilon²))の候補値。',
        'suo':'光速未満の非負速度が光速へ下側から集積するための、任意の指定正近傍内の点の存在。',
        'sup':'正の有限長の縮小後の値がv→Vの下側極限で零へ近づく。集積条件と全精度・近傍の量化を含み、v=Vでの変換は要求しない。',
        'suq':'任意の正の有限長について、縦の長さの下側極限が零となる内容。原文の平面への収縮をこの極限として読む追加解釈。',
        'sur':'光速以上の速さには正規のsrdを満たす有限βがないという内容。原文の議論の無意味性全体の定義ではない。'})
    decls={d['name']:d for d in doc['declarations']}
    for name,meaning in [('zh5','任意形状への帰結の箇所。'),('zh6','三軸の寸法の変化を示す箇所。'),
                         ('zh7','光速での平面への収縮を下側極限として読む追加解釈の箇所。'),('zia','光速を超える場合の適用範囲の留保の箇所。'),('zib','二つの系を交換しても同じ帰結があると明らかに述べる箇所。'),('zic','速さが大きいほど縦の縮小が強いと述べる箇所。')]:
        d=decls[name];basis['primitives'].append(dict(symbol=name,parameters=d['parameters'],result=d['result'],arguments=[],meaning_ja=meaning))
    basis['unresolved']+=[
        'u0116とu0117の部分記述。任意の形状の条件を渡せることと、物理的な任意の剛体の全ての性質を定義したことは区別する。',
        '光速での平面への収縮は有限の物体の縦幅の下側極限という追加解釈。v=Vに正規の変換を適用することと区別し、平面集合の位相的な収束や一様な全物体の極限とはしない。',
        '任意形状の幅は上限・下限から記述した。有限モデルの測定記録の検査を、連続空間の全位置を覆うことや実切断の完全性の証明にはしない。',
        '超光速で議論が無意味という留保の全意味と、後続で光速が無限大速度の物理的な役割を果たすという予告は未記述。',
        '逆の系の帰結は役割と速度を反転した別の測定設定を必要とする。同じ物体を両系で同時に静止させない。原刊照合と原文との意味一致は未完。']
    audit_basis(doc,basis)
    return format_graph(doc,'compact')+'\n',basis


def main():
    for compose,name in ((generic_composed,'shape-contraction'),(source_composed,'einstein-shape-contraction')):
        text,basis=compose()
        for relative,body in ((basis['document'],text),('data/'+name+'-basis-v1.json',json.dumps(basis,ensure_ascii=False,indent=2)+'\n')):
            path=ROOT/relative
            if path.exists():
                if path.read_text(encoding='utf-8')!=body:raise ValueError('Stored shape contraction differs: '+relative)
            else:
                with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(body)
    print('Arbitrary shape predicates, directional widths and light-speed limit composed')


if __name__=='__main__':main()
