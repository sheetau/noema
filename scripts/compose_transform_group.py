"""Define group laws compositionally and apply them to parallel boosts."""
from copy import deepcopy
import json

from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from scripts.compose_origin_clock import ROOT, CUT, definition, v
from scripts.compose_limits import call as k, app, op, both, quant as q
from scripts.compose_homogeneous_coordinates import VECTOR


def laws(real=False):
    typ=CUT if real else 'a'
    names=('s4y','s4z','s42','s43','s44') if real else ('s4t','s4u','s4v','s4w','s4x')
    carrier,operation,identity,inverse=map(v,('carrier','operation','identity','inverse'))
    x,y,z=map(v,('left','right','third'))
    inside=lambda x:app(carrier,x);apply=lambda x,y:app(operation,x,y)
    equal=lambda x,y:k('sca',x,y) if real else op('e',x,y)
    pair='carrier h['+typ+'] c operation h['+typ+' '+typ+'] '+typ
    def all_values(vs,body):
        for name in reversed(vs):body=q('f',name,typ,body)
        return body
    text=definition(names[0],pair,all_values(('left','right'),op('y',both(inside(x),inside(y)),inside(apply(x,y)))))
    text+=definition(names[1],pair,all_values(('left','right','third'),op('y',both(inside(x),inside(y),inside(z)),
        equal(apply(apply(x,y),z),apply(x,apply(y,z))))))
    text+=definition(names[2],pair+' identity '+typ,both(inside(identity),all_values(('left',),op('y',inside(x),
        both(equal(apply(identity,x),x),equal(apply(x,identity),x))))))
    inv=app(inverse,x)
    text+=definition(names[3],pair+' identity '+typ+' inverse h['+typ+'] '+typ,
        all_values(('left',),op('y',inside(x),both(inside(inv),equal(apply(x,inv),identity),equal(apply(inv,x),identity)))))
    validity=[all_values(('left',),op('y',inside(x),k('ba',x)))] if real else []
    text+=definition(names[4],pair+' identity '+typ+' inverse h['+typ+'] '+typ,
        both(*validity,k(names[0],carrier,operation),k(names[1],carrier,operation),
             k(names[2],carrier,operation,identity),k(names[3],carrier,operation,identity,inverse)))
    return text


GROUP_MEANINGS={
    's4t':'指定範囲の任意の二要素を指定二項操作で合成した結果が、同じ範囲に属する。',
    's4u':'指定範囲の任意の三要素について二通りの括り方で合成した値が等しい。交換則は要求しない。',
    's4v':'指定した単位元が範囲に属し、全要素に対して左からも右からも合成の値を変えない。空の範囲は単位元を持たない。',
    's4w':'指定した逆操作が各要素を同じ範囲の要素へ写し、左右両方の合成が同じ指定単位元になる。範囲外の値を逆元として使わない。',
    's4x':'個体型の範囲・二項操作・単位元・逆操作が、閉性・結合則・両側の単位元と逆元の条件を満たす群。可換性や有限性は要求しない。',
    's4y':'s4tの実切断版。群全体のs44で、範囲の全要素が有効な切断であることも要求する。',
    's4z':'s4uの実切断版。切断の関数としての個体同一性ではなく、scaによる実数値の一致を用いる。',
    's42':'s4vの実切断版。範囲の非空性は単位元の所属で要求する。',
    's43':'s4wの実切断版。逆操作の値の所属と両側の等式を保持する。',
    's44':'範囲の全値が有効な実切断であり、s4y・s4z・s42・s43が成立する群。全切断への量化を有限の速度一覧へ置き換えない。',
}


def generic_composed():
    doc=parse('n:'+laws())
    basis=dict(version='group-laws-basis-v1',document='examples/v014/group-laws.noema',primitives=[],
        definitions={name:meaning for name,meaning in GROUP_MEANINGS.items() if name in ('s4t','s4u','s4v','s4w','s4x')},
        unresolved=['これは指定された構造が群の条件を満たすという構成的定義であり、現実の任意の操作が群をなすという主張ではない。'])
    audit_basis(doc,basis)
    return format_graph(doc,'compact')+'\n',basis


def definitions():
    text=laws()+laws(True);V,s,w=map(v,('light','speed','moving'));vector=v('vector')
    zero=k('bb','n p a b');one=k('bb','n p b b');mul=lambda x,y:k('shv',x,y)
    text+=definition('s45','light '+CUT+' speed '+CUT,both(k('ba',V),k('ba',s),k('bg',zero,V),k('bg',mul(s,s),mul(V,V))))
    coord=lambda role:app(vector,k(role));role=v('role')
    values=(k('spe',V,s,one,coord('yn'),coord('zc7')),coord('yo'),coord('yp'),k('spd',V,s,one,coord('yn'),coord('zc7')))
    result=zero
    for axis,value in reversed(list(zip(('yn','yo','yp','zc7'),values))):result=k('szi',op('e',role,k(axis)),value,result)
    text+=definition('s46','light '+CUT+' speed '+CUT+' vector '+VECTOR,'i[role a]['+result+']',VECTOR)
    carrier='i[speed '+CUT+']['+k('s45',V,s)+']'
    operation='i[speed '+CUT+' moving '+CUT+']['+k('s3j',V,s,w)+']'
    inverse='i[speed '+CUT+']['+k('bf',zero,s)+']'
    text+=definition('s47','light '+CUT,both(k('ba',V),k('bg',zero,V),k('s44',carrier,operation,zero,inverse)))
    valid=lambda vector:k('shn',k('shx'),vector,'p ba')
    equal=lambda first,last:k('sho',k('shx'),first,last,'p sca')
    T=lambda speed,vector:k('s46',V,speed,vector)
    middle=T(s,vector);last=T(w,middle);direct=T(k('s3j',V,s,w),vector)
    text+=definition('s5a','light '+CUT+' speed '+CUT+' moving '+CUT+' vector '+VECTOR,
        op('y',both(k('s45',V,s),k('s45',V,w),valid(vector)),
           both(valid(middle),valid(last),valid(direct),equal(last,direct))))
    text+=definition('s5b','light '+CUT+' vector '+VECTOR,
        op('y',both(k('s45',V,zero),valid(vector)),both(valid(T(zero,vector)),equal(T(zero,vector),vector))))
    back=T(k('bf',zero,s),middle);other=T(s,T(k('bf',zero,s),vector))
    text+=definition('s5c','light '+CUT+' speed '+CUT+' vector '+VECTOR,
        op('y',both(k('s45',V,s),valid(vector)),both(valid(back),valid(other),equal(back,vector),equal(other,vector))))
    text+=definition('s5d','light '+CUT+' speed '+CUT+' moving '+CUT,
        q('f','vector',VECTOR,op('y',valid(vector),equal(T(s,vector),T(w,vector)))))
    composite=q('f','speed',CUT,q('f','moving',CUT,q('f','vector',VECTOR,k('s5a',V,s,w,vector))))
    faithful=q('f','speed',CUT,q('f','moving',CUT,op('y',both(k('s45',V,s),k('s45',V,w)),
        op('z',k('s5d',V,s,w),k('sca',s,w)))))
    text+=definition('s5e','light '+CUT,both(k('s47',V),composite,q('f','vector',VECTOR,k('s5b',V,vector)),
        q('f','speed',CUT,q('f','vector',VECTOR,k('s5c',V,s,vector))),faithful))
    text+=definition('s5f','','b context['+k('s5e',k('tc'))+']','e')
    general=composite.replace('v light','k tc[]')
    text+=definition('s5g','','b context['+both(k('ba',k('tc')),k('bg',zero,k('tc')),general)+']','e')
    return text


def composed():
    doc=parse((ROOT/'examples/v014/einstein-parallel-composition.noema').read_text(encoding='utf-8'))
    statements,doc['statements']=doc['statements'],[]
    doc=parse(format_graph(doc,'compact')+definitions()+'r zlu[] a.\n');doc['statements']=statements
    doc=parse(format_graph(doc,'compact')+'s[k zc[k zlu[] k rd[] r[k s5g[]] r[k s5f[]] k zlq[] k ri[]]].\n')
    basis=deepcopy(json.loads((ROOT/'data/parallel-composition-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='transform-group-basis-v1',document='examples/v014/einstein-transform-group.noema')
    decl=next(d for d in doc['declarations'] if d['name']=='zlu')
    basis['primitives'].append(dict(symbol='zlu',parameters=decl['parameters'],result=decl['result'],arguments=[],meaning_ja='平行変換の合成から群をなすと述べるu0149の箇所。'))
    basis['definitions'].update(GROUP_MEANINGS|{
        's45':'V>0かつ符号付き速度の二乗がV²より小さいという、両方向と零を含む有効な実切断の範囲。',
        's46':'係数1の既存の位置・時刻式を四成分の数値ベクトルへ適用した写像。指定四役割以外の値は零にする。定義域はs45とshnで指定する。',
        's47':'許容された符号付き速度、一次元合成、単位元0、逆速度−vがs44の群となる条件。速度域を非負に狭めない。',
        's5a':'許容された二速度と任意の有効な四成分入力について、二回の写像と合成速度の写像が有効で、四成分で一致するという条件付きの関係。',
        's5b':'任意の有効な四成分入力で、速度0の写像が有効で入力と一致する。',
        's5c':'任意の有効な四成分入力で、vと−vの二順序の合成がともに有効で入力へ戻る。',
        's5d':'任意の有効な四成分入力で、指定した二速度の写像が四成分で一致する。関数実装の識別子や観測済みの一点だけを比較しない。',
        's5e':'速度の群s47が、全四成分入力上で合成・単位元・両側逆変換を保って作用し、写像全体の一致と速度の一致が同値である。これにより速度で指定された変換の族を群として記述する。',
        's5f':'同じ光速度tcに関するs5eの内容。全方向のローレンツ変換一般ではなく、同じ軸・同じ原点の平行な変換の族。',
        's5g':'同じ光速度における先行する合成則を、任意の許容速度と四成分入力に対するs5aとして参照する内容。固定された三系の一出来事だけへ縮めない。'})
    basis['unresolved'] += [
        'u0149の群をなすという主節の部分記述。「wie dies sein muß」の挿入句の必然性・規範性の読みは確定せず、対応範囲から除外する。',
        '群は閉性だけではなく結合則・単位元・逆元を持つ構造として展開した。合成則だけから群であると一般的に結論する推論を有効と認定したものではない。',
        '変換の同一性は指定四成分での全入力における値の一致である。役割外の値や関数実装の同一性は数学的な四座標写像の意味に含めない。',
        '数値座標の全域と、物理的に観測済みの三記録の範囲は区別する。全実切断の体・平方根の一般法則、基礎的な群論からの導出の機械的証明、歴史的な語義と原文全体の意味一致確認は未完。']
    audit_basis(doc,basis)
    return format_graph(doc,'compact')+'\n',basis


def main():
    for compose,name in ((generic_composed,'data/group-laws-basis-v1.json'),(composed,'data/transform-group-basis-v1.json')):
        text,basis=compose()
        for filename,body in ((basis['document'],text),(name,json.dumps(basis,ensure_ascii=False,indent=2)+'\n')):
            path=ROOT/filename
            if path.exists():
                if path.read_text(encoding='utf-8')!=body:raise ValueError('Stored group differs: '+filename)
            else:
                with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(body)
    print('Generic group laws and the parallel-transform family composed')


if __name__=='__main__':main()
