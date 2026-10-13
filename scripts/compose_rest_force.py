"""Connect unit charge and frame-local force, correcting the inherited rest binding."""
from copy import deepcopy
import json
from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from scripts.compose_origin_clock import ROOT, definition, v
from scripts.compose_limits import call as k, app, op, both
from scripts.compose_field_equations import CUT, POINT, FIELD, ROLES

PARENT='examples/v014/einstein-charge-calibration.noema'
AXES='l[a][k yn[] k yo[] k yp[]]'


def replace_symbol(node, old, new):
    if isinstance(node,list):return [replace_symbol(x,old,new) for x in node]
    if not isinstance(node,dict):return node
    return {key:new if key=='symbol' and value==old else replace_symbol(value,old,new) for key,value in node.items()}


def definitions():
    coords=[app(v('point'),k(role)) for role in ROLES]
    vector='i[axis a]['+app(app(v('field'),v('axis')),*coords)+']'
    return definition('scb2','axes j[a] field '+FIELD+' point '+POINT+' vector '+POINT,
        both(k('shn',k('shx'),v('point'),'p ba'),k('shn',v('axes'),v('vector'),'p ba'),
            k('shn',v('axes'),vector,'p ba'),k('sho',v('axes'),vector,v('vector'),'p sca')))


MEANINGS={
    'scb2':'指定した四座標で場を評価した成分と、指定ベクトルの成分が一致する。座標と非空・重複のない成分列、両側の実数値の有効性を要求する。関数の実装上の同一性とは区別する。',
    'scc2':'先行する同じ電気量の対象について、同じ出来事・文脈・電気量の単位で、移動系で測った値も1であるという結果条件。静止系の数値を別系の結果へコピーする操作ではない。',
    'scd2':'先行する校正の仮定と相対性原理の内容を合わせた、電気量1の移動系への帰属の推論前提。これだけから電荷不変性が証明されたとはしない。',
    'sce2':'第一の電気量が静止系に静止するなら、その系の同じ対象・出来事での力ベクトルが、対象の四座標で評価した電気側の場の三成分と一致するという条件文。',
    'scf2':'第一の電気量が当該出来事で移動系に瞬間的に静止するなら、その系で測った力ベクトルが、その系の四座標で評価した電気側の場の三成分と一致するという条件文。前後の時間の静止は要求しない。',
}


def composed():
    doc=parse((ROOT/PARENT).read_text(encoding='utf-8'));statements,doc['statements']=doc['statements'],[]
    # The previous snapshot incorrectly passed motion (xm) as the rest predicate.
    # Preserve the snapshot and explicitly revise only this definition here.
    doc['declarations']=[replace_symbol(d,'xm','x4') if d['name']=='sby2' else d for d in doc['declarations']]
    text=format_graph(doc,'compact')+definitions()
    text+='r zpa[a a a d] c.r zpb[a a a '+POINT+' d] c.r zpc[a a a a a a '+POINT+' d] c.'
    text+=''.join('r '+name+'[] a.' for name in ('zpd','zpe','zpf','zpg','zph','zpi','zpn','zpo'))
    text+=''.join('r '+name+'[] '+POINT+'.' for name in ('zpj','zpk','zpl','zpm'))
    ctx=v('context');body=k('zol');event=k('zoo')
    text+=definition('scc2','','b context['+both(k('va',k('zbm')),
        k('sbw2',k('zpd'),body,k('zor'),k('zbm'),event,k('zou'),'n p b b',k('bb','n p b b'),ctx,'p zof','p zog'))+']','e')
    text+=definition('scd2','','b context['+both(op('t',k('sca2'),ctx),op('t',k('saw'),ctx))+']','e')
    event=k('zpo')
    for name,frame,E,H,region,point,force,record,rest in (
        ('sce2','ra','znl','znm','znk','zpj','zpl','zpe',k('x4',body,k('ra'),ctx)),
        ('scf2','zbm','znr','zns','znt','zpk','zpm','zpf',k('zpa',body,k('zbm'),event,ctx))):
        coords=[app(k(point),k(role)) for role in ROLES]
        consequent=both(k('va',k(frame)),k('znn',k(frame),k(E),k(H),k(region),ctx),
            k('zpb',body,k(frame),event,k(point),ctx),app(k(region),*coords),
            k('zof',k('zot'),k('zpn'),'n p b b',ctx),
            k('zpc',k(record),body,k('zpn'),k(frame),event,k('zot'),k(force),ctx),
            k('scb2',AXES,k(E),k(point),k(force)))
        text+=definition(name,'','b context['+op('y',rest,consequent)+']','e')
    doc=parse(text);doc['statements']=statements
    text=format_graph(doc,'compact')+'s[k zc[k zpg[] k rd[] r[k scd2[]] r[k scc2[]] k zno[] k ri[]]].'
    for node,content in (('zph','sce2'),('zpi','scf2')):text+='s[k uh[k '+node+'[] k rd[] r[k '+content+'[]] k zno[] k ri[]]].'
    doc=parse(text)
    basis=deepcopy(json.loads((ROOT/'data/einstein-charge-calibration-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='einstein-rest-force-basis-v1',document='examples/v014/einstein-rest-force.noema')
    meanings={
        'zpa':(['body','frame','event','context'],'対象が指定出来事の瞬間に指定系へ相対的に静止している。区間全体の静止や運動の否定から補う関係ではない。瞬間速度からの一般的構成は未完。'),
        'zpb':(['body','frame','event','point','context'],'同じ対象の同じ出来事を、指定系の四座標へ対応させる。別系でも同じ数値になるとはしない。観測記録からの実現は未完。'),
        'zpc':(['record','body','kind','frame','event','unit','vector','context'],'同じ対象に働く力の結果記録を、その系・出来事・単位・三成分ベクトルへ結ぶ。対象から別対象へ及ぼす力と混同しない。力の物理的な基礎説明は未完。'),
        'zpd':([], '移動系で同じ第一対象の電気量を1とする結果記録。'),
        'zpe':([], '静止系で第一対象に働く力のベクトル記録。'),
        'zpf':([], '移動系で第一対象に働く力のベクトル記録。'),
        'zpg':([], '相対性原理に基づき移動系での電気量1を述べる箇所。'),
        'zph':([], '静止系に静止するときの力と場の同定を述べる箇所。'),
        'zpi':([], '移動系に少なくとも当該瞬間静止するときの力と場の同定を述べる箇所。'),
        'zpj':([], '同じ第一対象・出来事に対応する静止系の四座標の候補。'),
        'zpk':([], '同じ第一対象・出来事に対応する移動系の四座標の候補。'),
        'zpl':([], '静止系で第一対象に働く力の三成分ベクトルの候補。'),
        'zpm':([], '移動系で第一対象に働く力の三成分ベクトルの候補。'),
        'zpn':([], '符号と方向を持つ力ベクトルという量の種類。校正試行の力の大きさzoqとは区別する。物理的な構成説明は未完。'),
        'zpo':([], '力を評価する対象上の当該出来事。校正試行の出来事zooとの同一性も非同一性も補わない。'),
    }
    for name,(args,meaning) in meanings.items():
        d=next(d for d in doc['declarations'] if d['name']==name)
        basis['primitives'].append(dict(symbol=name,parameters=d['parameters'],result=d['result'],arguments=args,meaning_ja=meaning))
    basis['definitions'].update(MEANINGS)
    basis['unresolved'] += [
        '訂正: 親文書のsby2は静止の引数へ運動xmを渡していた。この版で測定設定内の静止x4へ訂正した。親の保存資料と検査結果は変更せず、以前のテストが同じ誤解釈を含んだことを記録する。',
        'u0173の電気量1の系間の帰属と、静止条件付きの力ベクトルの同定を部分記述した。静止系は設定内の静止、移動系は少なくとも当該瞬間の静止とし、両条件を同時に断言しない。',
        '同じ対象の出来事の二系の座標を結ぶ一般的観測規約、力の単位と場の物理的な定義、相対性原理から電荷不変性への導出、definitionsgemäßの定義への参照の構成、二つの言い表しと全文の意味一致は未完。']
    audit_basis(doc,basis)
    return format_graph(doc,'compact')+'\n',basis


def generic_composed():
    text,basis=composed();doc=parse(text);byname={d['name']:d for d in doc['declarations']};needed={'scb2'}
    def references(node):
        if isinstance(node,list):return set().union(*(references(n) for n in node)) if node else set()
        if not isinstance(node,dict):return set()
        found={node['symbol']} if node.get('symbol') in byname else set()
        return found|set().union(*(references(n) for n in node.values()))
    todo=list(needed)
    while todo:
        for name in references(byname[todo.pop()])-needed:needed.add(name);todo.append(name)
    doc['declarations']=[d for d in doc['declarations'] if d['name'] in needed];doc['statements']=[]
    basis=dict(version='rest-force-basis-v1',document='examples/v014/rest-force.noema',
        primitives=[p for p in basis['primitives'] if p['symbol'] in needed],definitions={n:m for n,m in basis['definitions'].items() if n in needed},
        unresolved=['指定座標での場の値とベクトルを比較する一般機能。物理的な力や測定をこれだけで定義しない。'])
    audit_basis(doc,basis)
    return format_graph(doc,'compact')+'\n',basis


def main():
    for builder,name in ((generic_composed,'rest-force'),(composed,'einstein-rest-force')):
        text,basis=builder()
        for filename,body in ((basis['document'],text),('data/'+name+'-basis-v1.json',json.dumps(basis,ensure_ascii=False,indent=2)+'\n')):
            path=ROOT/filename
            if path.exists():
                if path.read_text(encoding='utf-8')!=body:raise ValueError('Stored rest-force differs: '+filename)
            else:
                with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(body)
    print('Corrected rest binding and frame-local force statements composed')


if __name__=='__main__':main()
