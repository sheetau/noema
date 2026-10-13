"""Compose scalar-field partials and the six source curl equations."""
from copy import deepcopy
import json

from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from scripts.compose_origin_clock import ROOT, definition, v
from scripts.compose_limits import call as k, app, op, both, quant as q
from scripts.compose_comoving_labels import CUT, TAU

POINT='h[a] '+CUT
REGION='h['+' '.join([CUT]*4)+'] c'
FIELD='h[a] '+TAU
JET='h[a a] '+CUT
ROLES=('yn','yo','yp','zc7')
PARENT='examples/v014/einstein-theory-transition.noema'


def rational_definition():
    return definition('s6a','light b rate b positive b negative b',both(k('aa','n p a b',v('light')),
        op('e',v('rate'),k('ad',v('light'),k('ab',v('positive'),k('ac',v('negative')))))))


def generic_composed():
    doc=parse('n:r aa[b b] c.r ab[b b] b.r ac[b] b.r ad[b b] b.'+rational_definition())
    labels={'aa':'有理数の厳密順序。','ab':'有理数の加算。','ac':'有理数の加法逆元。','ad':'有理数の乗算。'}
    basis=dict(version='field-equations-basis-v1',document='examples/v014/field-equations.noema',
        primitives=[dict(symbol=d['name'],parameters=d['parameters'],result=d['result'],
            arguments=['value'] if d['name']=='ac' else ['left','right'],meaning_ja=labels[d['name']])
            for d in doc['declarations'] if d['kind']=='primitive'],
        definitions={'s6a':'正のVについてrate=V*(positive-negative)という有理数の関係。微分値であるという条件は別に与える。'},
        unresolved=['微分可能性や物理的な力の定義を有理数の等式だけで認定しない。'])
    audit_basis(doc,basis)
    return format_graph(doc,'compact')+'\n',basis


def definitions():
    point=v('point');zero=k('bb','n p a b')
    coords=[app(point,k(role)) for role in ROLES]
    inside=app(v('region'),*coords)
    moved=[k('szi',op('e',v('axis'),k(role)),v('input'),coord) for role,coord in zip(ROLES,coords)]
    axis=op('x',op('e',v('axis'),k('yn')),op('x',op('e',v('axis'),k('yo')),
        op('x',op('e',v('axis'),k('yp')),op('e',v('axis'),k('zc7')))))
    slice_domain='i[input '+CUT+']['+app(v('region'),*moved)+']'
    slice_value='i[input '+CUT+']['+app(v('function'),*moved)+']'
    text=definition('s5t','function '+TAU+' region '+REGION+' point '+POINT+' axis a value '+CUT,
        both(k('shn',k('shx'),point,'p ba'),axis,inside,k('ba',v('value')),
            k('sjs',slice_domain,slice_value,app(point,v('axis')),v('value'))))
    args='electric '+FIELD+' magnetic '+FIELD+' region '+REGION+' point '+POINT
    jets='electricjet '+JET+' magneticjet '+JET
    partials=[]
    for field,jet in (('electric','electricjet'),('magnetic','magneticjet')):
        for component in ROLES[:3]:
            for axisrole in ROLES:
                if component==axisrole:continue
                partials.append(k('s5t',app(v(field),k(component)),v('region'),point,k(axisrole),app(v(jet),k(component),k(axisrole))))
    text+=definition('s5u',args+' '+jets,both(*partials))
    text+=definition('s5v','light '+CUT+' rate '+CUT+' positive '+CUT+' negative '+CUT,
        both(*(k('ba',v(a)) for a in ('light','rate','positive','negative')),k('bg',zero,v('light')),
            k('sca',v('rate'),k('shv',v('light'),k('bf',v('positive'),v('negative'))))))
    balances=[]
    for i,component in enumerate(ROLES[:3]):
        nextrole=ROLES[(i+1)%3];lastrole=ROLES[(i+2)%3]
        rate=lambda jet:app(v(jet),k(component),k('zc7'))
        entry=lambda jet,component,axis:app(v(jet),k(component),k(axis))
        balances += [k('s5v',v('light'),rate('electricjet'),entry('magneticjet',lastrole,nextrole),entry('magneticjet',nextrole,lastrole)),
            k('s5v',v('light'),rate('magneticjet'),entry('electricjet',nextrole,lastrole),entry('electricjet',lastrole,nextrole))]
    text+=definition('s5w','light '+CUT+' '+jets,both(*balances))
    text+=definition('s5x',args+' light '+CUT,q('g','electricjet',JET,q('g','magneticjet',JET,
        both(k('s5u',v('electric'),v('magnetic'),v('region'),point,v('electricjet'),v('magneticjet')),
            k('s5w',v('light'),v('electricjet'),v('magneticjet'))))))
    active=both(k('shn',k('shx'),point,'p ba'),inside)
    text+=definition('s5y','electric '+FIELD+' magnetic '+FIELD+' region '+REGION+' light '+CUT,
        both(k('ba',v('light')),k('bg',zero,v('light')),q('g','point',POINT,active),
            q('f','point',POINT,op('y',active,k('s5x',v('electric'),v('magnetic'),v('region'),point,v('light'))))))
    return text+rational_definition()


MEANINGS={
    's5t':'同じ四座標のうち指定軸だけを動かし、指定領域との共通部分で、同じスカラー関数の差商の極限sjsを要求する。領域外や別の軸の微分を流用しない。',
    's5u':'二つの三成分場について、同じ場所・時刻と領域で、各成分の時間微分と他の二空間軸の偏微分を指定する。六つの式に必要な18微分を結ぶ。',
    's5v':'正の有効な実切断Vについて、rate=V*(positive-negative)を要求する。分母を払った形であり、V=0を許さない。',
    's5w':'三軸の循環順序を保ち、電気側の時間微分が磁気側の回転のV倍、磁気側が電気側の回転の負のV倍である六条件。物理的解釈はこの代数関係の外で指定する。',
    's5x':'同じ二場・領域・四座標で18偏微分値が存在し、その同じ値が六条件を満たす。微分値の未結合な数表だけを場の解とはしない。',
    's5y':'指定領域に有効な四座標が存在し、その全ての点で同じ二場と同じ正のVに対してs5xを要求する。有限点の標本で全領域を置換しない。',
    's5z':'静止系Kへの二場と領域の割当を同じ文脈で保持し、その領域で六つの微分方程式が成立するという、仮定として引用する内容。',
    's6a':'有理数で正のVとrate=V*(positive-negative)を要求する比較用の関係。',
}


def composed():
    doc=parse((ROOT/PARENT).read_text(encoding='utf-8'));statements,doc['statements']=doc['statements'],[]
    text=format_graph(doc,'compact')+definitions()+(
        'r znk[] '+REGION+'.r znl[] '+FIELD+'.r znm[] '+FIELD+'.r znn[a '+FIELD+' '+FIELD+' '+REGION+' d] c.r zno[] a.r znp[] a.')
    text+=definition('s5z','','b context['+both(k('znn',k('ra'),k('znl'),k('znm'),k('znk'),v('context')),
        k('s5y',k('znl'),k('znm'),k('znk'),k('tc')))+']','e')
    doc=parse(text);doc['statements']=statements
    doc=parse(format_graph(doc,'compact')+'s[k ug[k znp[] k rd[] r[k s5z[]] k zno[] k ri[]]].')
    basis=deepcopy(json.loads((ROOT/'data/einstein-theory-transition-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='einstein-field-equations-basis-v1',document='examples/v014/einstein-field-equations.noema')
    decls={d['name']:d for d in doc['declarations']}
    for name,args,meaning in (
        ('znk',[],'六つの方程式を仮定する四座標領域。空の領域での空虚な成立をs5yで排除する。物理的な真空の一般的定義は未完。'),
        ('znl',[],'静止系で電気的な力を表すと本文が指定する三成分のスカラー場。yn,yo,ypにX,Y,Zを対応させる。電気的な力の操作的説明は未完。'),
        ('znm',[],'同じ静止系で磁気的な力を表すと本文が指定する三成分のスカラー場。yn,yo,ypにL,M,Nを対応させる。磁気的な力の操作的説明は未完。'),
        ('znn',['frame','electric','magnetic','region','context'],'同じ座標系・文脈に、指定領域と電気側・磁気側の成分場を割り当てる。二場の交換や別の系への割当を同一視しない。'),
        ('zno',[],'§6冒頭の方程式を仮定する論述範囲。前段第一部の総括範囲とは別に保持する。'),
        ('znp',[],'u0153からM0287の式を仮定として導入する箇所。')):
        d=decls[name];basis['primitives'].append(dict(symbol=name,parameters=d['parameters'],result=d['result'],arguments=args,meaning_ja=meaning))
    basis['definitions'].update(MEANINGS)
    basis['unresolved'] += [
        'u0153の仮定導入とu0154のM0287を部分記述した。見出し、分野名・真空・電気的／磁気的な力の基礎説明、u0155以後の本文は未完。',
        '本文に表示された六つの回転の式だけを記述した。発散条件を追加せず、完全な真空電磁場の条件を尽くしたとも扱わない。',
        '偏微分は指定領域の各軸切片での相対極限として構成した。領域の開性や物理的な境界条件、単位系の説明、関数の全域での解と原文全体の意味一致確認は未完。',
        '全実切断上の偏微分の存在と六式の成立を、有限のアフィン場検査や有理数の代数だけでは認定しない。907頁の原刊照合は未実施。']
    audit_basis(doc,basis)
    return format_graph(doc,'compact')+'\n',basis


def main():
    for builder,name in ((generic_composed,'field-equations'),(composed,'einstein-field-equations')):
        text,basis=builder()
        for filename,body in ((basis['document'],text),('data/'+name+'-basis-v1.json',json.dumps(basis,ensure_ascii=False,indent=2)+'\n')):
            path=ROOT/filename
            if path.exists():
                if path.read_text(encoding='utf-8')!=body:raise ValueError('Stored field equations differ: '+filename)
            else:
                with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(body)
    print('Field partials and six equations composed')


if __name__=='__main__':main()
