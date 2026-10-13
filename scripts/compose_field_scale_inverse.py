"""Separate inverse scalar products, evenness and the selected unit branch."""
from copy import deepcopy
import json
from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from scripts.compose_origin_clock import ROOT, definition, v
from scripts.compose_limits import call as k, app, op, both
from scripts.compose_field_equations import CUT, FIELD
from scripts.compose_field_transform import rational_definitions

PARENT='examples/v014/einstein-field-common-scale.noema'


def rational():
    text=definition('sam2','first b second b',op('e',k('ad',v('first'),v('second')),'n p b b'))
    for name,forward,reverse in (('sax2','s6b','s6c'),('say2','s6c','s6b')):
        own=k('ad',v('first'),k(forward,v('beta'),v('ratio'),v('own'),v('cross')))
        cross=k('ad',v('first'),k(forward,v('beta'),v('ratio'),v('cross'),v('own')))
        text+=definition(name,'beta b ratio b first b second b own b cross b',k('ad',v('second'),k(reverse,v('beta'),v('ratio'),own,cross)),'b')
    return text


MEANINGS={
    'sam2':'二つの有理係数の積が1になるという逆係数の条件。零係数は成立させられない。',
    'sax2':'β(own-ratio*cross)型の二成分を第一係数で拡大し、逆符号の混合と第二係数を適用した値。',
    'say2':'β(own+ratio*cross)型についてsax2と反対の符号順序で往復させた値。',
    'sal2':'同じ実数係数で場の各成分の値を掛けた関数を構成する。座標引数はそのまま保持する。',
    'san2':'有効な実数係数二つの積が1である条件。正であるとは要求しない。',
    'sao2':'有効な実数値が1である条件。',
    'sap2':'逆係数の積が1、両係数が等しい、第一係数が正という三条件から値1を結論する条件文。正の条件を原文に勝手に追加しないための独立した数学的注記。',
    'saq2':'許容速度でψ(v)ψ(-v)=1とする本文の主張内容。',
    'sar2':'許容速度でψ(v)=ψ(-v)とする本文の主張内容。対称性の物理的根拠は別の未記述事項。',
    'sas2':'saq2とsar2を同じ文脈で採用した前提。正の係数という条件は加えていない。',
    'sat2':'許容速度でψ(v)=1とする本文の結論内容。',
    'sau2':'先行の共通係数を1とした六つの場変換の内容。二系の場の割当と領域一致を保持する。',
    'sav2':'先行の共通係数を持つ六式と、その係数の値が1という内容を同じ文脈で採用する前提。',
}


def generic_composed():
    doc=parse('n:r aa[b b] c.r ab[b b] b.r ac[b] b.r ad[b b] b.'+rational_definitions()+rational())
    labels={'aa':'有理数の厳密順序。','ab':'有理数の加算。','ac':'有理数の加法逆元。','ad':'有理数の乗算。'}
    from scripts.compose_field_transform import MEANINGS as previous
    basis=dict(version='field-scale-inverse-basis-v1',document='examples/v014/field-scale-inverse.noema',
        primitives=[dict(symbol=d['name'],parameters=d['parameters'],result=d['result'],arguments=['value'] if d['name']=='ac' else ['left','right'],meaning_ja=labels[d['name']]) for d in doc['declarations'] if d['kind']=='primitive'],
        definitions={n:(MEANINGS|previous)[n] for n in ('s6b','s6c','sam2','sax2','say2')},
        unresolved=['βの正規化条件は別に与える。有理数の恒等式であり、任意の実関数の微分方程式や物理的な同定の証明ではない。'])
    audit_basis(doc,basis)
    return format_graph(doc,'compact')+'\n',basis


def composed():
    doc=parse((ROOT/PARENT).read_text(encoding='utf-8'));statements,doc['statements']=doc['statements'],[]
    params=' '.join(n+' '+CUT for n in ('x','y','z','time'));coords=[v(n) for n in ('x','y','z','time')]
    text=format_graph(doc,'compact')+rational()+definition('sal2','scale '+CUT+' field '+FIELD,
        'i[component a][i['+params+']['+k('shv',v('scale'),app(app(v('field'),v('component')),*coords))+']]',FIELD)
    one=k('bb','n p b b');zero=k('bb','n p a b')
    text+=definition('san2','first '+CUT+' second '+CUT,both(k('ba',v('first')),k('ba',v('second')),k('sca',k('shv',v('first'),v('second')),one)))
    text+=definition('sao2','value '+CUT,both(k('ba',v('value')),k('sca',v('value'),one)))
    text+=definition('sap2','first '+CUT+' second '+CUT,op('y',both(k('san2',v('first'),v('second')),k('sca',v('first'),v('second')),k('bg',zero,v('first'))),k('sao2',v('first'))))
    text+=''.join('r '+n+'[] a.' for n in ('zn3','zn4','zn5','zn6'))
    V,s=k('tc'),k('zb7');forward=app(k('znz'),s);reverse=app(k('znz'),k('bf',zero,s));domain=k('s45',V,s)
    for name,condition in (('saq2',k('san2',forward,reverse)),('sar2',both(k('ba',forward),k('ba',reverse),k('sca',forward,reverse))),('sat2',k('sao2',forward))):
        text+=definition(name,'','b context['+both(domain,condition)+']','e')
    text+=definition('sas2','','b context['+both(op('t',k('saq2'),v('context')),op('t',k('sar2'),v('context')))+']','e')
    oldE,oldH=k('znl'),k('znm');newE,newH=k('znr'),k('zns');region=k('s6m',V,s,k('znk'))
    text+=definition('sau2','','b context['+both(domain,k('znn',k('ra'),oldE,oldH,k('znk'),v('context')),
        k('znn',k('zbm'),newE,newH,k('znt'),v('context')),k('saj2',region,k('znt')),
        k('sai2',one,k('s6k',V,s,oldE,oldH),k('s6l',V,s,oldE,oldH),newE,newH,region))+']','e')
    text+=definition('sav2','','b context['+both(op('t',k('sak2'),v('context')),op('t',k('sat2'),v('context')))+']','e')
    doc=parse(text);doc['statements']=statements
    text=format_graph(doc,'compact')
    for node,content in (('zn3','saq2'),('zn4','sar2')):text+='s[k uh[k '+node+'[] k rd[] r[k '+content+'[]] k zno[] k ri[]]].'
    for node,premise,conclusion in (('zn5','sas2','sat2'),('zn6','sav2','sau2')):text+='s[k zc[k '+node+'[] k rd[] r[k '+premise+'[]] r[k '+conclusion+'[]] k zno[] k ri[]]].'
    doc=parse(text)
    basis=deepcopy(json.loads((ROOT/'data/einstein-field-common-scale-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='einstein-field-scale-inverse-basis-v1',document='examples/v014/einstein-field-scale-inverse.noema')
    for name,meaning in (('zn3','逆変換から係数の積を1とする結論の提示箇所。二通りの逆変換を行う論述そのものは未記述。'),('zn4','対称性により正負の速度の係数が同じとする結論の提示箇所。対称性の論拠と脚注は未記述。'),('zn5','二つの係数条件から値1を帰結とする著者の推論箇所。正の枝の根拠を補わず、数学的妥当性と帰属を区別する。'),('zn6','係数1を使って六式を提示する著者の推論箇所。')):
        d=next(d for d in doc['declarations'] if d['name']==name);basis['primitives'].append(dict(symbol=name,parameters=d['parameters'],result=d['result'],arguments=[],meaning_ja=meaning))
    basis['definitions'].update(MEANINGS)
    basis['unresolved'] += [
        'M0311〜M0314の係数の積・偶性・値1・最終六式を部分記述する。u0165で二通りの逆変換を比較する過程、u0167と脚注の対称性の理由は未記述。',
        '積1と偶性だけでは係数-1も残る。正の枝を選ぶ条件を著者の前提sas2へ追加せず、独立した注記sap2で区別した。物理的な向きの規約や連続性との接続は未完。',
        '原刊908頁ではψ、909頁ではφと印刷されている。§6の直前の共通係数を指すという読みを明示して同じznzを使い、以前の§3のφへ参照を戻さない。data/field-scale-inverse-facsimile-v1.jsonに原表記を保存する。',
        '一般の実関数に対する逆変換の証明、力の操作的定義・単位・真空、原文全体の意味一致確認は未完。']
    audit_basis(doc,basis)
    return format_graph(doc,'compact')+'\n',basis


def main():
    for builder,name in ((generic_composed,'field-scale-inverse'),(composed,'einstein-field-scale-inverse')):
        text,basis=builder()
        for filename,body in ((basis['document'],text),('data/'+name+'-basis-v1.json',json.dumps(basis,ensure_ascii=False,indent=2)+'\n')):
            path=ROOT/filename
            if path.exists():
                if path.read_text(encoding='utf-8')!=body:raise ValueError('Stored scale inverse differs: '+filename)
            else:
                with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(body)
    print('Inverse coefficient, symmetry and unit-branch claims composed')


if __name__=='__main__':main()
