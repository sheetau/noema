"""Define conservative determined extensions and keep introduction explanations separate."""
from copy import deepcopy
import json
from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from scripts.compose_origin_clock import ROOT, definition, v
from scripts.compose_limits import call as k, app, op, both, quant as q
from scripts.compose_field_equations import CUT, POINT
from scripts.compose_force_wordings import ZERO
from scripts.compose_rest_force import AXES

PARENT='examples/v014/einstein-field-dependence.noema'
CONSTRUCTION='h['+CUT+' '+POINT+' '+POINT+'] '+POINT


def definitions():
    base=v('base');extended=v('extended');state=v('state')
    text=definition('scz2','base h[a] c extended h[a a] c',q('f','state','a',
        op('z',app(base,state),q('g','extra','a',app(extended,state,v('extra'))))))
    unique=q('f','state','a',q('f','first','a',q('f','second','a',op('y',
        both(app(extended,state,v('first')),app(extended,state,v('second'))),op('e',v('first'),v('second'))))))
    text+=definition('sda2','base h[a] c extended h[a a] c',both(k('scz2',base,extended),unique))
    args='base h[a] c calculate h[a] a'
    text+=definition('sdb2',args+' state a extra a',both(app(base,state),op('e',v('extra'),app(v('calculate'),state))))
    graph='i[state a extra a]['+k('sdb2',base,v('calculate'),state,v('extra'))+']'
    text+=definition('sdc2',args,k('sda2',base,graph))
    parameters='light '+CUT+' velocity '+POINT+' magnetic '+POINT
    extra=v('extra');valid=k('sck2',v('light'),v('velocity'),'i[axis a]['+ZERO+']',v('magnetic'))
    formula=k('sci2',v('light'),v('velocity'),v('magnetic'))
    text+=definition('sdd2',parameters+' extra '+POINT,both(valid,k('shn',AXES,extra,'p ba'),k('sho',AXES,extra,formula,'p sca')))
    relation=lambda value:k('sdd2',v('light'),v('velocity'),v('magnetic'),value)
    witness=q('g','extra',POINT,relation(extra))
    unique=q('f','first',POINT,q('f','second',POINT,op('y',both(relation(v('first')),relation(v('second'))),
        k('sho',AXES,v('first'),v('second'),'p sca'))))
    text+=definition('sde2',parameters,op('y',valid,both(witness,unique)))
    return text


MEANINGS={
    'scz2':'元の状態が許容されることと、追加値を持つ許容された拡張が存在することが、全状態で同値である。元の状態を排除したり、元で不許可の状態を追加したりしない。空の元集合でも成立し得るので、整合性や実現の証明とは分ける。',
    'sda2':'scz2の保存条件と、同じ元の状態に対する追加値の一意性を要求する。別の元の状態が同じ追加値を持つことは許す。ここでは追加値は個体として同一性を比較する。',
    'sdb2':'元の許容条件と、既存の全域関数で計算した値への等値だけから拡張関係を定義する。新しい自由度や別の許容条件を加えない。',
    'sdc2':'sdb2で定義した拡張が、元の状態の保存と追加値の一意性を満たすという条件。全域関数の結果は同じ個体領域に属するという型の規約で使う。',
    'sdd2':'正の光速度と有効な速度・磁気ベクトルに対し、追加値が既存の(u×H)/Vの空間三成分へ一致する定義関係。関数の個体同一性や空間成分以外の一致を要求しない。',
    'sde2':'有効な入力ごとにsdd2を満たす追加ベクトルが存在し、その空間三成分が一意であるという条件。光速度・入力の許容範囲をこの定義で狭めない。実数演算の閉性を自動で証明するものではない。',
    'sdf2':'全ての有効な光速度・速度・磁気ベクトルについて、電動力の追加項がsde2を満たすという、補助項の決定可能性の部分的な読み。理論上の補助概念という役割の意味全体とは同一視しない。',
    'sdg2':'補助項の決定可能性と前段の基準系依存の内容を保持し、著者がその依存性の記述を追加項の構成を導入する理由として採用する。両内容の成立だけから説明関係を補わない。',
}


def composed():
    doc=parse((ROOT/PARENT).read_text(encoding='utf-8'));statements,doc['statements']=doc['statements'],[]
    text=format_graph(doc,'compact')+definitions()
    text+='r zpu[a i[e] i['+CONSTRUCTION+'] a d] c.r zpv[] a.r zpw[] a.'
    universal=q('f','light',CUT,q('f','velocity',POINT,q('f','magnetic',POINT,k('sde2',v('light'),v('velocity'),v('magnetic')))))
    text+=definition('sdf2','','b context['+universal+']','e')
    ctx=v('context')
    text+=definition('sdg2','','b context['+both(op('t',k('sdf2'),ctx),op('t',k('scx2'),ctx),
        k('zpu',k('rd'),'r[k scx2[]]','r[p sci2]',k('zno'),ctx))+']','e')
    doc=parse(text);doc['statements']=statements;text=format_graph(doc,'compact')
    for node,content in (('zpv','sdf2'),('zpw','sdg2')):text+='s[k uh[k '+node+'[] k rd[] r[k '+content+'[]] k zno[] k ri[]]].'
    doc=parse(text)
    basis=deepcopy(json.loads((ROOT/'data/einstein-field-dependence-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='einstein-auxiliary-terms-basis-v1',document='examples/v014/einstein-auxiliary-terms.noema')
    for name,args,meaning in (
        ('zpu',['author','reason_description','construction_description','scope','context'],'著者が指定範囲の説明で、理由の記述を、型付きの構成を導入する理由として採用する。構成はここでは実数と二ベクトルからベクトルを作る関数の記述。構成を実行済みとすることや、理由の真理・十分性・実在の因果機構は、この関係だけからは従わない。'),
        ('zpv',[],'u0176で追加項に補助概念の役割だけを与えるという箇所。現在は入力を制限せず値が定まる構成としての部分解釈。'),
        ('zpw',[],'同じ段落で、基準系への依存を追加項の導入の理由として説明する箇所。')):
        d=next(d for d in doc['declarations'] if d['name']==name)
        basis['primitives'].append(dict(symbol=name,parameters=d['parameters'],result=d['result'],arguments=args,meaning_ja=meaning))
    basis['definitions'].update(MEANINGS)
    basis['unresolved'] += [
        'u0176の補助概念の役割を、既存の許容入力を変えず空間三成分が一意に決まる定義として部分解釈した。元の理論全体への保存的拡張を形式的に証明したものではなく、理論上の役割・存在論・nurの全意味は未完。',
        '導入理由は真偽の一致と別の、記述を保持する採用関係として接続した。説明の十分性や心理的・歴史的因果の一般理論は未完。原文のMan siehtという明白さの位置付けは対応範囲から除く。',
        '関数の実装上の同一性を追加値の一意性に使わず、空間三成分で比較する。全実切断の演算の閉性と構成の存在証明、物理概念の説明、前段の依存性の全意味と全文の意味一致確認は未完。']
    audit_basis(doc,basis)
    return format_graph(doc,'compact')+'\n',basis


def generic_composed():
    text,basis=composed();doc=parse(text);byname={d['name']:d for d in doc['declarations']};needed={'scz2','sda2','sdb2','sdc2','sdd2','sde2'}
    def references(node):
        if isinstance(node,list):return set().union(*(references(n) for n in node)) if node else set()
        if not isinstance(node,dict):return set()
        found={node['symbol']} if node.get('symbol') in byname else set()
        return found|set().union(*(references(n) for n in node.values()))
    todo=list(needed)
    while todo:
        for name in references(byname[todo.pop()])-needed:needed.add(name);todo.append(name)
    doc['declarations']=[d for d in doc['declarations'] if d['name'] in needed];doc['statements']=[]
    basis=dict(version='auxiliary-terms-basis-v1',document='examples/v014/auxiliary-terms.noema',
        primitives=[p for p in basis['primitives'] if p['symbol'] in needed],definitions={n:m for n,m in basis['definitions'].items() if n in needed},
        unresolved=['元の許容状態の保存と追加値の一意性を分ける定義。補助概念という理論上の役割の全意味や、任意の元理論の整合性を保証するものではない。'])
    audit_basis(doc,basis)
    return format_graph(doc,'compact')+'\n',basis


def main():
    for builder,name in ((generic_composed,'auxiliary-terms'),(composed,'einstein-auxiliary-terms')):
        text,basis=builder()
        for filename,body in ((basis['document'],text),('data/'+name+'-basis-v1.json',json.dumps(basis,ensure_ascii=False,indent=2)+'\n')):
            path=ROOT/filename
            if path.exists():
                if path.read_text(encoding='utf-8')!=body:raise ValueError('Stored auxiliary terms differ: '+filename)
            else:
                with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(body)
    print('Determined conservative extensions and introduction explanation composed')


if __name__=='__main__':main()
