"""Ask for equations describing a trajectory without assuming an answer exists."""
from copy import deepcopy
import json

from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from scripts.compose_origin_clock import ROOT, CUT, definition, v
from scripts.compose_limits import call as k, op, both, quant as q
from scripts.compose_coordinate_correspondence import SIDE, SYSTEM, generic_composed as correspondence


def generic_definitions():
    args='scope h[a] c member h[a] c valid h['+CUT+'] c same h['+CUT+' '+CUT+'] c'
    selected=lambda n:'c[v scope][v '+n+']'
    member=lambda n:'c[v member][v '+n+']'
    text=definition('szb','equations '+SYSTEM+' '+args,both(
        op('u',op('e','d[v equations]','n p a b')),
        q('g','record','a',both(selected('record'),member('record'))),
        q('f','record','a',op('y',selected('record'),op('z',
            k('sgx',v('equations'),v('record'),v('record'),v('valid'),v('same')),member('record'))))))
    text+=definition('szh',args,'j v[i[equations '+SYSTEM+']['+k('szb',v('equations'),v('scope'),v('member'),v('valid'),v('same'))+']]','g['+SYSTEM+']')
    text+=definition('szi','choice c left '+CUT+' right '+CUT,'i[bound b]['+op('x',both(v('choice'),'c[v left][v bound]'),both(op('u',v('choice')),'c[v right][v bound]'))+']',CUT)
    return text


GENERIC_MEANINGS={
    'szb':'指定範囲で、非空の有限方程式列の解が対象の集合と過不足なく一致する。範囲内の対象の存在も要求する。同じ記録をsgxの二つの記録引数へ渡し、一記録上の方程式として使う。',
    'szh':'szbを満たす方程式列を答えとして求める質問。条件を満たす候補の存在・唯一性・発見済みは主張しない。',
    'szi':'真偽の選択値に従って二つの実切断述語の一方を選ぶ。真なら左、偽なら右の述語と各有理数で同じ値になる。両側が有効な実数かどうかは別条件。'}


def generic_composed():
    text,basis=correspondence();doc=parse(text+generic_definitions())
    basis=deepcopy(basis);basis.update(version='equation-description-basis-v1',document='examples/v014/equation-description.noema')
    basis['definitions'].update(GENERIC_MEANINGS)
    basis['unresolved'] += ['方程式で指定集合を過不足なく記述する課題を表す。全ての対象集合に有限個の方程式が存在するという主張や、その式を発見する計算手続は含まない。']
    audit_basis(doc,basis)
    return format_graph(doc,'compact')+'\n',basis


def source_composed():
    parent=parse((ROOT/'examples/v014/einstein-velocity-components.noema').read_text(encoding='utf-8'))
    statements,parent['statements']=parent['statements'],[]
    text=format_graph(parent,'compact')+generic_definitions()+'r zki[] a.\n'
    record,event,observed,setting=map(v,('record','event','observed','setting'))
    text+=definition('szc','point a frame a setting d record a',both(k('sha',record,'p ba'),
        q('g','event','a',q('g','observed','a',both(k('zka',v('point'),event,setting),k('zc4',event),
            k('shd',event,observed,v('frame'),setting),k('sha',observed,'p ba'),k('shh',record,observed))))))
    text+=definition('szj','point a frame a setting d',both(q('g','event','a',k('zka',v('point'),event,setting)),
        q('f','event','a',op('y',k('zka',v('point'),event,setting),both(k('zc4',event),
            q('g','observed','a',both(k('shd',event,observed,v('frame'),setting),k('sha',observed,'p ba'))))))))
    scope='i[record a][k sha[v record p ba]]'
    member='i[record a][k szc[k zkb[] k ra[] k zke[] v record]]'
    text+=definition('szd','equations '+SYSTEM,both(k('szj',k('zkb'),k('ra'),k('zke')),k('szb',v('equations'),scope,member,'p ba','p sca')))
    text+=definition('sze','','j v[i[equations '+SYSTEM+'][k szd[v equations]]]','g['+SYSTEM+']')
    V,s,u,w=k('tc'),k('zb7'),k('zkc'),k('zkd')
    D=k('sys',V,s,u);beta=k('soy',V,s);square=k('shv',V,V)
    coord=lambda role:k('zc6',v('second'),k(role))
    mul=lambda a,b:k('shv',a,b)
    time=coord('zc7');zero=k('bb','n p a b')
    pairs=[(mul(D,coord('yn')),mul(square,mul(k('bd',u,s),time))),
        (mul(mul(beta,D),coord('yo')),mul(square,mul(w,time))),(coord('yp'),zero)]
    equations=[]
    for left,right in pairs:
        equations.append('i[first a second a side c]['+k('szi',v('side'),left,right)+']')
    text+=definition('szf','','l['+SIDE+']['+' '.join(equations)+']',SYSTEM)
    text+=definition('szg','','b context['+both(k('srd',V,s,beta),op('u',k('sca',D,zero)),'h[k sze[]][k szf[]]')+']','e')
    doc=parse(text);doc['statements']=statements
    doc=parse(format_graph(doc,'compact')+'s[k zdc[k zki[] k rd[] r[k sze[]] k zkf[] k ri[]]].\n')
    basis=deepcopy(json.loads((ROOT/'data/velocity-components-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='motion-question-basis-v1',document='examples/v014/einstein-motion-question.noema')
    d=next(d for d in doc['declarations'] if d['name']=='zki')
    basis['primitives'].append(dict(symbol='zki',parameters=d['parameters'],result=d['result'],arguments=[],meaning_ja='§5で静止系に対する点の運動を求める課題を提示する本文箇所。'))
    basis['definitions'].update(GENERIC_MEANINGS)
    basis['definitions'].update({
        'szc':'指定点の履歴の出来事に指定基準系で付与された四座標と、値が一致する有効な記録。識別子が異なる同値記録も含める。',
        'szj':'指定点の履歴が非空で、全ての選択出来事に指定基準系で有効な座標記録が少なくとも一つ存在する。測定できた出来事だけへ対象を暗黙に狭めない。',
        'szd':'履歴の全出来事が有効な座標を持ち、静止系での指定点の四座標集合を有効な全座標記録の範囲で過不足なく表す方程式列の候補条件。速度合成の答えの式を条件へ先に埋め込まない。',
        'sze':'szdと同じ条件で、静止系に対する点の運動を表す方程式列を求める質問。',
        'szf':'先行する変換結果の三式を既存の方程式列として構成した候補。D*x=V²*(u+v)*t、beta*D*y=V²*w*t、z=0の左右を選ぶ実切断関数。候補の定義だけでは質問への十分な答えと認定しない。',
        'szg':'既存の許容速度・正のbeta・非零分母の下で、候補szfが質問szeの答え条件を満たすという内容。定義を置くことと、その内容を断言することは別である。'})
    basis['unresolved'] += [
        '親草案で未記述としていたu0133冒頭の課題提示を追加した。引用された質問の帰属に既存のzdcを再利用し、新しい発話用の意味関係は増やさない。',
        '先行するsyvは実際の履歴の座標が式を満たす片方向の条件であり、式の全解が履歴に属することは保証しない。szgをsyyからの帰結や既に得られた回答として主張しない。',
        '全実時刻での出来事の存在と全座標値の表現可能性は未完。有限の候補領域で式が一致する検査を、無限の全空間での意味一致とは数えない。',
        '運動を方程式列として求める読みを採用した。式の発見手続、著者の認識・解決済みの判定、原刊照合と原文の全意味確認は未完。']
    audit_basis(doc,basis)
    return format_graph(doc,'compact')+'\n',basis


def main():
    for compose,basispath in ((generic_composed,'data/equation-description-basis-v1.json'),(source_composed,'data/motion-question-basis-v1.json')):
        text,basis=compose()
        for relative,body in ((basis['document'],text),(basispath,json.dumps(basis,ensure_ascii=False,indent=2)+'\n')):
            path=ROOT/relative
            if path.exists():
                if path.read_text(encoding='utf-8')!=body:raise ValueError('Stored motion question differs: '+relative)
            else:
                with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(body)
    print('Equation descriptions and the motion-finding question composed')


if __name__=='__main__':main()
