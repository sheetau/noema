"""Compose coordinate pullback and mixed field components independently."""
from copy import deepcopy
import json

from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from scripts.compose_origin_clock import ROOT, definition, v
from scripts.compose_limits import call as k, app, op, both
from scripts.compose_field_equations import CUT, TAU, POINT, REGION, FIELD, ROLES

PARENT='examples/v014/einstein-field-equations.noema'
MAP='h['+POINT+'] '+POINT


def rational_definitions():
    return definition('s6b','beta b ratio b own b cross b',k('ad',v('beta'),k('ab',v('own'),k('ac',k('ad',v('ratio'),v('cross'))))),'b')+definition(
        's6c','beta b ratio b own b cross b',k('ad',v('beta'),k('ab',v('own'),k('ad',v('ratio'),v('cross')))),'b')


def generic_composed():
    doc=parse('n:r ab[b b] b.r ac[b] b.r ad[b b] b.'+rational_definitions())
    labels={'ab':'有理数の加算。','ac':'有理数の加法逆元。','ad':'有理数の乗算。'}
    basis=dict(version='field-transform-basis-v1',document='examples/v014/field-transform.noema',
        primitives=[dict(symbol=d['name'],parameters=d['parameters'],result=d['result'],
            arguments=['value'] if d['name']=='ac' else ['left','right'],meaning_ja=labels[d['name']]) for d in doc['declarations'] if d['kind']=='primitive'],
        definitions={'s6b':'β*(own-ratio*cross)という有理数の線形結合。','s6c':'β*(own+ratio*cross)という有理数の線形結合。'},
        unresolved=['βと比率の物理的な意味および許容範囲、関数の引数の変換は別に与える。'])
    audit_basis(doc,basis)
    return format_graph(doc,'compact')+'\n',basis


def point_expression(coordinates):
    value=k('bb','n p a b')
    for role,coord in reversed(list(zip(ROLES,coordinates))):value=k('szi',op('e',v('role'),k(role)),coord,value)
    return 'i[role a]['+value+']'


def definitions():
    text=rational_definitions()
    for name,operation in (('s6d','bf'),('s6e','bd')):
        text+=definition(name,'beta '+CUT+' ratio '+CUT+' own '+CUT+' cross '+CUT,
            k('shv',v('beta'),k(operation,v('own'),k('shv',v('ratio'),v('cross')))),CUT)
    params=' '.join(name+' '+CUT for name in ('x','y','z','time'))
    coords=list(map(v,('x','y','z','time')));point=point_expression(coords)
    mapped=app(v('mapping'),point);mappedcoords=[app(mapped,k(role)) for role in ROLES]
    for name,result,arg in (('s6f',TAU,'function '+TAU),('s6g',REGION,'function '+REGION)):
        text+=definition(name,arg+' mapping '+MAP,'i['+params+']['+app(v('function'),*mappedcoords)+']',result)
    text+=definition('s6h','field '+FIELD+' mapping '+MAP,'i[component a]['+k('s6f',app(v('field'),v('component')),v('mapping'))+']',FIELD)
    V,s=map(v,('light','speed'));beta=k('soy',V,s);ratio=k('shv',s,k('sjd',V))
    e=lambda role:app(app(v('electric'),k(role)),*coords)
    h=lambda role:app(app(v('magnetic'),k(role)),*coords)
    electric=(e('yn'),k('s6d',beta,ratio,e('yo'),h('yp')),k('s6e',beta,ratio,e('yp'),h('yo')))
    magnetic=(h('yn'),k('s6e',beta,ratio,h('yo'),e('yp')),k('s6d',beta,ratio,h('yp'),e('yo')))
    args='light '+CUT+' speed '+CUT+' electric '+FIELD+' magnetic '+FIELD
    for name,components in (('s6i',electric),('s6j',magnetic)):
        value=k('bb','n p a b')
        for role,component in reversed(list(zip(ROLES[:3],components))):value=k('szi',op('e',v('component'),k(role)),component,value)
        text+=definition(name,args,'i[component a][i['+params+']['+value+']]',FIELD)
    inverse='i[point '+POINT+']['+k('s46',V,k('bf',k('bb','n p a b'),s),v('point'))+']'
    for name,mixing in (('s6k','s6i'),('s6l','s6j')):
        text+=definition(name,args,k('s6h',k(mixing,V,s,v('electric'),v('magnetic')),inverse),FIELD)
    text+=definition('s6m','light '+CUT+' speed '+CUT+' region '+REGION,k('s6g',v('region'),inverse),REGION)
    text+=definition('s6n',args+' region '+REGION,both(k('s45',V,s),k('s5y',
        k('s6k',V,s,v('electric'),v('magnetic')),k('s6l',V,s,v('electric'),v('magnetic')),k('s6m',V,s,v('region')),V)))
    return text


MEANINGS={
    's6b':'有理数のβ*(own-ratio*cross)。符号を明示した混合の比較用定義。',
    's6c':'有理数のβ*(own+ratio*cross)。',
    's6d':'実切断でβ*(own-ratio*cross)を構成する。引数の有効性は呼出側の領域条件で指定する。',
    's6e':'実切断でβ*(own+ratio*cross)を構成する。',
    's6f':'新しい四座標を指定写像で旧四座標へ写し、その旧座標で同じスカラー関数を評価する合成関数。場の成分の混合とは別の操作。',
    's6g':'s6fと同じ写像による領域の逆像。新座標の点が入ることと、対応する旧座標の点が元の領域に入ることを一致させる。',
    's6h':'同じ写像を三成分を含む場の全成分に使い、各成分の四座標引数を変える。',
    's6i':'同じ旧座標で(X, β(Y-vN/V), β(Z+vM/V))を構成する。引数の座標変換はまだ含めない。',
    's6j':'同じ旧座標で(L, β(M+vZ/V), β(N-vY/V))を構成する。',
    's6k':'s6iの混合成分を、既存の速度-vの逆座標変換を合成して新座標の関数として構成する。',
    's6l':'s6jの混合成分を同じ逆座標変換で新座標の関数として構成する。',
    's6m':'元の領域を同じ逆座標変換の逆像として新座標で表す。新旧の数値をそのまま同じ点とは扱わない。',
    's6n':'正のVと|v|<Vを要求し、同じ新座標の二場と領域に既存の六つの微分方程式s5yを適用する。旧六式からの帰結をこの定義だけで保証しない。',
    's6o':'本文が提示する、変換後の六式の内容。静止系の成分値を直接新系で測った物理量と同一視しない。',
    's6p':'旧場の六式、先行する§3の座標対応sso、同じVとvの許容条件を共有する、本文の変換操作への部分的な前提。真空の未記述条件は別課題として残る。',
}


def composed():
    doc=parse((ROOT/PARENT).read_text(encoding='utf-8'));statements,doc['statements']=doc['statements'],[]
    text=format_graph(doc,'compact')+definitions()+'r znq[] a.'
    text+=definition('s6o','','b context['+k('s6n',k('tc'),k('zb7'),k('znl'),k('znm'),k('znk'))+']','e')
    text+=definition('s6p','','b context['+both(op('t',k('s5z'),v('context')),op('t',k('sso'),v('context')),k('s45',k('tc'),k('zb7')))+']','e')
    doc=parse(text);doc['statements']=statements
    doc=parse(format_graph(doc,'compact')+'s[k zc[k znq[] k rd[] r[k s6p[]] r[k s6o[]] k zno[] k ri[]]].')
    basis=deepcopy(json.loads((ROOT/'data/einstein-field-equations-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='einstein-field-transform-basis-v1',document='examples/v014/einstein-field-transform.noema')
    d=next(d for d in doc['declarations'] if d['name']=='znq')
    basis['primitives'].append(dict(symbol='znq',parameters=d['parameters'],result=d['result'],arguments=[],meaning_ja='u0156から変換後の六式を提示する推論箇所。推論の著者への帰属と、前提の十分性の機械的認定は区別する。'))
    basis['definitions'].update(MEANINGS)
    basis['unresolved'] += [
        'M0291・M0292の混合された成分と新座標での六式、M0290の既存v、M0293の既存βへ部分接続した。u0156の電磁的過程という概念と全文の意味一致確認は未完。',
        '前段で表示した六つの回転の式だけからは、変換後の六式は一般に導けない。静的なE=(x,0,0),H=0が反例となる。真空を表す追加の条件とその基礎説明はまだ前提に接続されていない。',
        's6pからs6oへの記述は著者が帰結として提示したという部分的な談話記録であり、妥当な定理として認定したものではない。全微分可能性や連鎖律、発散条件との接続を未証明のまま補わない。',
        '構成した混合関数を、動く系で実際に測る力の定義と同一視しない。後続の比較・共通係数・物理的定義は未記述。907〜908頁の原刊照合は未実施。']
    audit_basis(doc,basis)
    return format_graph(doc,'compact')+'\n',basis


def main():
    for builder,name in ((generic_composed,'field-transform'),(composed,'einstein-field-transform')):
        text,basis=builder()
        for filename,body in ((basis['document'],text),('data/'+name+'-basis-v1.json',json.dumps(basis,ensure_ascii=False,indent=2)+'\n')):
            path=ROOT/filename
            if path.exists():
                if path.read_text(encoding='utf-8')!=body:raise ValueError('Stored field transformation differs: '+filename)
            else:
                with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(body)
    print('Field component mixing and inverse-coordinate pullback composed')


if __name__=='__main__':main()
