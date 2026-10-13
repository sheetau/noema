"""Represent a common scalar without deriving it from shared differential laws."""
from copy import deepcopy
import json
from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from scripts.compose_origin_clock import ROOT, definition, v
from scripts.compose_limits import call as k, app, op, both, quant as q
from scripts.compose_field_equations import CUT, POINT, FIELD, REGION, ROLES

PARENT='examples/v014/einstein-law-specialization.noema'


def definitions():
    scaled='i[axis a]['+k('shv',v('scale'),app(v('first'),v('axis')))+']'
    text=definition('sag2','axes j[a] scale '+CUT+' first '+POINT+' second '+POINT,
        both(k('ba',v('scale')),k('shn',v('axes'),v('first'),'p ba'),k('shn',v('axes'),v('second'),'p ba'),
            k('sho',v('axes'),scaled,v('second'),'p sca')))
    fields=' '.join(name+' '+FIELD for name in ('electric','magnetic','newelectric','newmagnetic'))
    args='scale '+CUT+' '+fields
    coords=[app(v('point'),k(role)) for role in ROLES]
    components='l[a][k yn[] k yo[] k yp[]]'
    vector=lambda name:'i[axis a]['+app(app(v(name),v('axis')),*coords)+']'
    text+=definition('sah2',args+' point '+POINT,both(k('shn',k('shx'),v('point'),'p ba'),
        k('sag2',components,v('scale'),vector('electric'),vector('newelectric')),
        k('sag2',components,v('scale'),vector('magnetic'),vector('newmagnetic'))))
    inside=both(k('shn',k('shx'),v('point'),'p ba'),app(v('region'),*coords))
    text+=definition('sai2',args+' region '+REGION,both(k('ba',v('scale')),q('g','point',POINT,inside),
        q('f','point',POINT,op('y',inside,k('sah2',*(v(n) for n in ('scale','electric','magnetic','newelectric','newmagnetic','point')))))))
    text+=definition('saj2','first '+REGION+' second '+REGION,q('f','point',POINT,
        op('y',k('shn',k('shx'),v('point'),'p ba'),op('z',app(v('first'),*coords),app(v('second'),*coords)))))
    return text


MEANINGS={
    'sag2':'指定した非空・重複のない成分列について、全成分が有効な実数であり、同じ実数係数を第一ベクトルに掛けると第二ベクトルになる。係数の非零性や一意性はこの条件から補わない。',
    'sah2':'同じ四座標で電気・磁気それぞれの三成分を評価し、一つの共通係数で新しい二場の全六成分へ対応させる。',
    'sai2':'空でない有効な四座標領域の全点でsah2を要求する。係数は全点の量化の外にあり、場所や時刻ごとに選び直せない。',
    'saj2':'有効な四座標の全点で二つの領域への所属が一致する。異なる領域の共通部分だけに主張を縮めない。',
    'sak2':'速度だけを引数とする同じψの値で、逆座標変換を合成した混合場の全六成分と動く系の成分を結ぶという著者の主張内容。新旧の場と系への割当、許容速度、共通領域を明示する。',
}


def composed():
    doc=parse((ROOT/PARENT).read_text(encoding='utf-8'));statements,doc['statements']=doc['statements'],[]
    text=format_graph(doc,'compact')+definitions()+'r znz[] h['+CUT+'] '+CUT+'.r zn2[] a.'
    V,s=k('tc'),k('zb7');oldE,oldH=k('znl'),k('znm');newE,newH=k('znr'),k('zns')
    region=k('s6m',V,s,k('znk'))
    text+=definition('sak2','','b context['+both(k('s45',V,s),
        k('znn',k('ra'),oldE,oldH,k('znk'),v('context')),
        k('znn',k('zbm'),newE,newH,k('znt'),v('context')),
        k('saj2',region,k('znt')),
        k('sai2',app(k('znz'),s),k('s6k',V,s,oldE,oldH),k('s6l',V,s,oldE,oldH),newE,newH,region))+']','e')
    doc=parse(text);doc['statements']=statements
    doc=parse(format_graph(doc,'compact')+'s[k uh[k zn2[] k rd[] r[k sak2[]] k zno[] k ri[]]].')
    basis=deepcopy(json.loads((ROOT/'data/einstein-law-specialization-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='einstein-field-common-scale-basis-v1',document='examples/v014/einstein-field-common-scale.noema')
    for name,meaning in (('znz','本文の共通係数ψへの関数参照。引数は速度のみで、座標や成分は引数にしない。非零性、偶関数性、値が1であることは後続の別の主張。'),('zn2','u0163の共通係数に関する結論とu0164の六式を提示する主張箇所。推論の妥当性認定とは別。')):
        d=next(d for d in doc['declarations'] if d['name']==name)
        basis['primitives'].append(dict(symbol=name,parameters=d['parameters'],result=d['result'],arguments=[],meaning_ja=meaning))
    basis['definitions'].update(MEANINGS)
    basis['unresolved'] += [
        'u0163の共通係数に関する結論節とu0164を部分記述する。同じ微分方程式を満たすことだけから共通係数があるとは導かず、著者の主張として帰属させる。等価性・記号置換・明白さを含む推論の前半は未記述。',
        '保存したM0307ではM′の右辺が小文字zだが、公開された原刊908頁スキャンでは大文字Zと読める。生の資料は変更せず、data/field-common-scale-facsimile-v1.jsonの局所照合に基づきZを使う。',
        '同じ速度で全ての場の候補を比較する普遍的な係数かどうか、力の操作的定義・真空・単位・測定と、原文の意味一致確認は未完。原刊照合は指定式の局所確認であり全文確認ではない。']
    audit_basis(doc,basis)
    return format_graph(doc,'compact')+'\n',basis


def generic_composed():
    text,basis=composed();doc=parse(text);byname={d['name']:d for d in doc['declarations']};needed={'sag2'}
    def references(node):
        if isinstance(node,list):return set().union(*(references(n) for n in node)) if node else set()
        if not isinstance(node,dict):return set()
        found={node['symbol']} if node.get('symbol') in byname else set()
        return found|set().union(*(references(n) for n in node.values()))
    todo=list(needed)
    while todo:
        for name in references(byname[todo.pop()])-needed:needed.add(name);todo.append(name)
    doc['declarations']=[d for d in doc['declarations'] if d['name'] in needed];doc['statements']=[]
    basis=dict(version='field-common-scale-basis-v1',document='examples/v014/field-common-scale.noema',
        primitives=[p for p in basis['primitives'] if p['symbol'] in needed],
        definitions={n:m for n,m in basis['definitions'].items() if n in needed},
        unresolved=['共通係数によるベクトルの対応だけを表す汎用定義。微分方程式や物理的な場の関係をこれだけで決めない。'])
    audit_basis(doc,basis)
    return format_graph(doc,'compact')+'\n',basis


def main():
    for builder,name in ((generic_composed,'field-common-scale'),(composed,'einstein-field-common-scale')):
        text,basis=builder()
        for filename,body in ((basis['document'],text),('data/'+name+'-basis-v1.json',json.dumps(basis,ensure_ascii=False,indent=2)+'\n')):
            path=ROOT/filename
            if path.exists():
                if path.read_text(encoding='utf-8')!=body:raise ValueError('Stored common scale differs: '+filename)
            else:
                with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(body)
    print('Common scalar across components and coordinates composed')


if __name__=='__main__':main()
