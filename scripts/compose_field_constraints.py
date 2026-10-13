"""Make divergence, full jets, and the conditional chain-rule connection explicit."""
from copy import deepcopy
import json

from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from scripts.compose_origin_clock import ROOT, definition, v
from scripts.compose_limits import call as k, app, op, both, quant as q
from scripts.compose_field_equations import CUT, FIELD, POINT, REGION, JET, ROLES

PARENT='examples/v014/einstein-field-transform.noema'
NAMES=[field+component+axis for field in ('e','h') for component in 'xyz' for axis in 'xyzu']
NEW_RESIDUALS=tuple('s7'+s for s in 'abcdefgh')
OLD_RESIDUALS=tuple('s7'+s for s in 'ijklmnop')


def rational_definitions():
    add=lambda a,b:k('ab',a,b);sub=lambda a,b:add(a,k('ac',b));mul=lambda a,b:k('ad',a,b)
    beta,ratio=v('beta'),v('ratio')
    e=[[v('e'+c+a) for a in 'xyzu'] for c in 'xyz'];h=[[v('h'+c+a) for a in 'xyzu'] for c in 'xyz']
    def pull(jet):return [[mul(beta,add(row[0],mul(ratio,row[3]))),row[1],row[2],mul(beta,add(row[3],mul(ratio,row[0])))] for row in jet]
    ep,hp=pull(e),pull(h)
    plus=lambda a,b:mul(beta,add(a,mul(ratio,b)));minus=lambda a,b:mul(beta,sub(a,mul(ratio,b)))
    en=[ep[0],[minus(a,b) for a,b in zip(ep[1],hp[2])],[plus(a,b) for a,b in zip(ep[2],hp[1])]]
    hn=[hp[0],[plus(a,b) for a,b in zip(hp[1],ep[2])],[minus(a,b) for a,b in zip(hp[2],ep[1])]]
    def residuals(e,h):
        er=[sub(e[i][3],sub(h[(i+2)%3][(i+1)%3],h[(i+1)%3][(i+2)%3])) for i in range(3)]
        hr=[add(h[i][3],sub(e[(i+2)%3][(i+1)%3],e[(i+1)%3][(i+2)%3])) for i in range(3)]
        return er+hr+[add(add(a[0][0],a[1][1]),a[2][2]) for a in (e,h)]
    args=' '.join(name+' b' for name in NAMES);text=''
    for symbols,parameters,es,hs in ((OLD_RESIDUALS,args,e,h),(NEW_RESIDUALS,'beta b ratio b '+args,en,hn)):
        for symbol,body in zip(symbols,residuals(es,hs)):text+=definition(symbol,parameters,body,'b')
    return text


RATIONAL_MEANINGS={symbol:('変換後' if symbols==NEW_RESIDUALS else '変換前')+'の'+label+'。時間座標u=Vtでの有理数の微分係数を引数とする。微分の存在自体は別に要求する。'
    for symbols in (OLD_RESIDUALS,NEW_RESIDUALS) for symbol,label in zip(symbols,('電気側xの残差','電気側yの残差','電気側zの残差','磁気側xの残差','磁気側yの残差','磁気側zの残差','電気側の発散','磁気側の発散'))}


def generic_composed():
    doc=parse('n:r ab[b b] b.r ac[b] b.r ad[b b] b.'+rational_definitions())
    labels={'ab':'有理数の加算。','ac':'有理数の加法逆元。','ad':'有理数の乗算。'}
    basis=dict(version='field-constraints-basis-v1',document='examples/v014/field-constraints.noema',
        primitives=[dict(symbol=d['name'],parameters=d['parameters'],result=d['result'],arguments=['value'] if d['name']=='ac' else ['left','right'],meaning_ja=labels[d['name']]) for d in doc['declarations'] if d['kind']=='primitive'],
        definitions=RATIONAL_MEANINGS.copy(),unresolved=['u=Vtを用いた数値係数の代数であり、一般の実関数の全微分可能性や連鎖律を証明する文書ではない。'])
    audit_basis(doc,basis)
    return format_graph(doc,'compact')+'\n',basis


def definitions():
    zero=k('bb','n p a b');V,s=v('light'),v('speed');point=v('point')
    entry=lambda jet,c,a:app(jet,k(c),k(a))
    div=k('bd',k('bd',entry(v('jet'),'yn','yn'),entry(v('jet'),'yo','yo')),entry(v('jet'),'yp','yp'))
    text=definition('s6q','jet '+JET,div,CUT)
    jetargs='electricjet '+JET+' magneticjet '+JET
    diagonals=[k('ba',entry(v(jet),role,role)) for jet in ('electricjet','magneticjet') for role in ROLES[:3]]
    text+=definition('s6r','light '+CUT+' '+jetargs,both(k('s5w',V,v('electricjet'),v('magneticjet')),*diagonals,
        k('sca',k('s6q',v('electricjet')),zero),k('sca',k('s6q',v('magneticjet')),zero)))
    fieldargs='electric '+FIELD+' magnetic '+FIELD+' region '+REGION+' point '+POINT
    diagonal_partials=[k('s5t',app(v(field),k(role)),v('region'),point,k(role),entry(v(jet),role,role))
        for field,jet in (('electric','electricjet'),('magnetic','magneticjet')) for role in ROLES[:3]]
    text+=definition('s6s',fieldargs+' '+jetargs,both(k('s5u',v('electric'),v('magnetic'),v('region'),point,v('electricjet'),v('magneticjet')),*diagonal_partials))
    beta=k('soy',V,s);ratio=k('shv',s,k('sjd',V));jet=v('jet');component=v('component');axis=v('axis')
    dx=app(jet,component,k('yn'));dt=app(jet,component,k('zc7'))
    newx=k('shv',beta,k('bd',dx,k('shv',k('shv',s,k('shv',k('sjd',V),k('sjd',V))),dt)))
    newt=k('shv',beta,k('bd',dt,k('shv',s,dx)))
    value=k('bb','n p a b')
    for role,val in reversed(list(zip(ROLES,(newx,app(jet,component,k('yo')),app(jet,component,k('yp')),newt)))):
        value=k('szi',op('e',axis,k(role)),val,value)
    text+=definition('s6t','light '+CUT+' speed '+CUT+' jet '+JET,'i[component a axis a]['+value+']',JET)
    pe=k('s6t',V,s,v('electricjet'));ph=k('s6t',V,s,v('magneticjet'))
    ep=lambda role:app(pe,k(role),axis);hp=lambda role:app(ph,k(role),axis)
    mixed=((ep('yn'),k('s6d',beta,ratio,ep('yo'),hp('yp')),k('s6e',beta,ratio,ep('yp'),hp('yo'))),
        (hp('yn'),k('s6e',beta,ratio,hp('yo'),ep('yp')),k('s6d',beta,ratio,hp('yp'),ep('yo'))))
    args='light '+CUT+' speed '+CUT+' '+jetargs
    for name,entries in zip(('s6u','s6v'),mixed):
        value=zero
        for role,val in reversed(list(zip(ROLES[:3],entries))):value=k('szi',op('e',component,k(role)),val,value)
        text+=definition(name,args,'i[component a axis a]['+value+']',JET)
    newargs='newelectricjet '+JET+' newmagneticjet '+JET
    equal=[]
    for name,expected in (('newelectricjet','s6u'),('newmagneticjet','s6v')):
        for c in ROLES[:3]:
            for a in ROLES:
                actual=entry(v(name),c,a);target=entry(k(expected,V,s,v('electricjet'),v('magneticjet')),c,a)
                equal += [k('ba',actual),k('sca',actual,target)]
    text+=definition('s6w',args+' '+newargs,both(k('s45',V,s),
        *(k('ba',entry(v(jet),c,a)) for jet in ('electricjet','magneticjet') for c in ROLES[:3] for a in ROLES),*equal))
    oldpoint=k('s46',V,k('bf',zero,s),point)
    fields=(k('s6k',V,s,v('electric'),v('magnetic')),k('s6l',V,s,v('electric'),v('magnetic')))
    region=k('s6m',V,s,v('region'))
    text+=definition('s6x',fieldargs+' light '+CUT+' speed '+CUT+' '+jetargs+' '+newargs,both(
        k('s6s',v('electric'),v('magnetic'),v('region'),oldpoint,v('electricjet'),v('magneticjet')),
        k('s6s',*fields,region,point,v('newelectricjet'),v('newmagneticjet')),
        k('s6w',V,s,v('electricjet'),v('magneticjet'),v('newelectricjet'),v('newmagneticjet'))))
    text+=definition('s6y',fieldargs+' light '+CUT,q('g','electricjet',JET,q('g','magneticjet',JET,both(
        k('s6s',v('electric'),v('magnetic'),v('region'),point,v('electricjet'),v('magneticjet')),
        k('s6r',V,v('electricjet'),v('magneticjet'))))))
    inside=both(k('shn',k('shx'),point,'p ba'),app(v('region'),*(app(point,k(role)) for role in ROLES)))
    text+=definition('s6z','electric '+FIELD+' magnetic '+FIELD+' region '+REGION+' light '+CUT,both(
        k('ba',V),k('bg',zero,V),q('g','point',POINT,inside),q('f','point',POINT,op('y',inside,k('s6y',v('electric'),v('magnetic'),v('region'),point,V)))))
    condition=both(k('s6x',v('electric'),v('magnetic'),v('region'),point,V,s,v('electricjet'),v('magneticjet'),v('newelectricjet'),v('newmagneticjet')),
        k('s6r',V,v('electricjet'),v('magneticjet')))
    for name in reversed(('electricjet','magneticjet','newelectricjet','newmagneticjet')):condition=q('g',name,JET,condition)
    text+=definition('s72',fieldargs+' light '+CUT+' speed '+CUT,condition)
    text+=definition('s73',fieldargs+' light '+CUT+' speed '+CUT,op('y',
        k('s72',v('electric'),v('magnetic'),v('region'),point,V,s),k('s6y',*fields,region,point,V)))
    return text+rational_definitions()


MEANINGS={
    's6q':'三つの同軸空間偏微分の和として発散を構成する。',
    's6r':'同じ二場の微分値について六つの回転の式と二つの発散零を要求し、使用する24値全ての有効性を検査する。',
    's6s':'先行の18微分に同軸の6偏微分を加え、同じ二場・領域・四座標に全24値を結ぶ。',
    's6t':'逆座標変換の連鎖則に対応する微分値の線形操作。x方向はβ*(dx+v*dt/V²)、時刻方向はβ*(dt+v*dx)、横方向は元の値を使う。',
    's6u':'s6tで引数を変えた微分値に、電気側と同じ成分混合を施す。',
    's6v':'s6tで引数を変えた微分値に、磁気側と同じ成分混合を施す。',
    's6w':'許容速度と有効な旧24値を要求し、新24値がs6u・s6vの対応する値に等しいという明示的な数値の連鎖則条件。微分可能性からこの条件を導いたとはしない。',
    's6x':'同じ新座標と、その逆変換先の旧座標で、元の場・変換した場と全24微分値を結び、同じ値の間にs6wを要求する。',
    's6y':'同じ点で全24偏微分が存在し、六式と二つの発散零を満たすという局所条件。物理的な真空の概念全体の定義ではない。',
    's6z':'非空の指定領域の全有効座標でs6yを要求する。有限点の検査でこの量化を置換しない。',
    's72':'旧点と新点で実際の微分に結んだ同じ24値の連鎖則条件と、旧点での六式および二つの発散零を含む局所的な十分条件候補。',
    's73':'s72を満たす点で変換後の二場がs6yを満たすという条件付き命題。全実切断の体の法則と連鎖則の導出は機械的に証明していない。',
}


def composed():
    doc=parse((ROOT/PARENT).read_text(encoding='utf-8'));statements,doc['statements']=doc['statements'],[]
    doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=statements
    basis=deepcopy(json.loads((ROOT/'data/einstein-field-transform-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='einstein-field-constraints-basis-v1',document='examples/v014/einstein-field-constraints.noema')
    basis['definitions'].update(MEANINGS|RATIONAL_MEANINGS)
    basis['unresolved'] += [
        '変換時に不足した条件を補う数学的な解釈注記として発散と微分値の連鎖則を追加した。原文がこの形で明示しているとは扱わず、以前の著者帰属の前提を変更しない。',
        '有理数の正規化した時間座標u=Vtにおける残差の恒等式を検査する。全実切断上の体の性質、一般の実関数の全微分可能性からの連鎖則、物理的な真空の基礎説明は未完。',
        '元の場と変換後の場の微分値を結ぶs6wは明示的な追加条件であり、別々の偏微分の存在だけから成立すると仮定しない。領域の開性・境界条件・測定との接続、原文の意味一致確認は未完。']
    audit_basis(doc,basis)
    return format_graph(doc,'compact')+'\n',basis


def main():
    for builder,name in ((generic_composed,'field-constraints'),(composed,'einstein-field-constraints')):
        text,basis=builder()
        for filename,body in ((basis['document'],text),('data/'+name+'-basis-v1.json',json.dumps(basis,ensure_ascii=False,indent=2)+'\n')):
            path=ROOT/filename
            if path.exists():
                if path.read_text(encoding='utf-8')!=body:raise ValueError('Stored field constraints differ: '+filename)
            else:
                with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(body)
    print('Divergence and explicit derivative transformation constraints composed')


if __name__=='__main__':main()
