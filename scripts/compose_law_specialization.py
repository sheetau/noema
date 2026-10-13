"""Specialize a shared law without identifying its distinct representations."""
from copy import deepcopy
import json

from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from scripts.compose_origin_clock import ROOT, definition, v
from scripts.compose_limits import call as k, app, op, both
from scripts.compose_field_equations import FIELD, REGION
from scripts.compose_law_invariance import definitions as invariance_definitions, MEANINGS as INVARIANCE_MEANINGS

PARENT='examples/v014/einstein-total-differential.noema'


def definitions():
    args='history a first a second a law a left a right a represented h[a a a] c conforms h[a a] c'
    names=('history','first','second','law','left','right','represented','conforms')
    shared=both(k('sap',v('history'),v('first'),v('second'),v('law'),v('represented'),v('conforms')),
        app(v('represented'),v('history'),v('first'),v('left')),app(v('represented'),v('history'),v('second'),v('right')))
    text=definition('s77',args,shared)
    contents='source e target e context d'
    text+=definition('saa2',args+' '+contents,both(k('s77',*(v(n) for n in names)),
        op('z',app(v('conforms'),v('law'),v('left')),op('t',v('source'),v('context'))),
        op('z',app(v('conforms'),v('law'),v('right')),op('t',v('target'),v('context')))))
    text+=definition('sab2',args+' '+contents,op('y',both(k('saa2',*(v(n) for n in names),v('source'),v('target'),v('context')),
        op('t',v('source'),v('context'))),op('t',v('target'),v('context'))))
    return text


MEANINGS={
    's77':'同じ候補履歴の二表現に同じ法則を適用する。先行するsapの全対応記述対での適合一致に加え、指定された左・右の記述が実際に各系の対応表現であることを要求する。',
    'saa2':'s77の法則適合を、同じ文脈での二つの内容の真偽へそれぞれ結ぶ。対象の記述、数値、内容の記述文字列を同一視しない。',
    'sab2':'saa2と源側の内容が成立するとき、対象側の内容が成立するという条件付きの適用例。源側が成立していなければ対象側の成立を断言しない。',
}


def generic_composed():
    doc=parse('n:'+invariance_definitions()+definitions())
    basis=dict(version='law-specialization-basis-v1',document='examples/v014/law-specialization.noema',primitives=[],
        definitions=INVARIANCE_MEANINGS|MEANINGS,unresolved=[
            '同じ履歴の対応記述と、法則適合の内容との対応を明示的な前提にする。二つの式を同時に満たすという事実だけから同じ履歴や同じ量とは認定しない。'])
    audit_basis(doc,basis)
    return format_graph(doc,'compact')+'\n',basis


def composed():
    doc=parse((ROOT/PARENT).read_text(encoding='utf-8'));statements,doc['statements']=doc['statements'],[]
    text=format_graph(doc,'compact')+definitions()+('r znr[] '+FIELD+'.r zns[] '+FIELD+'.r znt[] '+REGION+
        '.r znu[] a.r znv[] a.r znw[] a.r znx[] a.r zny[] a.')
    context=v('context');old=op('t',k('s5z'),context)
    text+=definition('sac2','','b context['+both(k('znn',k('zbm'),k('znr'),k('zns'),k('znt'),context),
        k('s5y',k('znr'),k('zns'),k('znt'),k('tc')))+']','e')
    bridge=both(k('sat',k('ra'),k('zbm'),context),k('vd',k('znu'),context),k('ve',k('znv'),context),
        k('vh',k('znv'),k('ra'),k('znw'),context),k('vh',k('znv'),k('zbm'),k('znx'),context),
        op('z',k('vi',k('znu'),k('znw'),context),old),op('z',k('vi',k('znu'),k('znx'),context),op('t',k('sac2'),context)))
    text+=definition('sad2','','b context['+bridge+']','e')
    text+=definition('sae2','','b context['+both(op('t',k('saw'),context),op('t',k('sad2'),context))+']','e')
    text+=definition('saf2','','b context['+op('y',old,op('t',k('sac2'),context))+']','e')
    doc=parse(text);doc['statements']=statements
    doc=parse(format_graph(doc,'compact')+'s[k zc[k zny[] k rd[] r[k sae2[]] r[k saf2[]] k zno[] k ri[]]].')
    basis=deepcopy(json.loads((ROOT/'data/einstein-total-differential-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='einstein-law-specialization-basis-v1',document='examples/v014/einstein-law-specialization.noema')
    decls={d['name']:d for d in doc['declarations']}
    for name,meaning in (
        ('znr','動く系での電気的な力として本文が定義する三成分X′,Y′,Z′への関数参照。先行する計算上の混合関数s6kとは別に保持する。物理的な定義は未完。'),
        ('zns','動く系での磁気的な力として本文が定義する三成分L′,M′,N′への関数参照。計算上の混合関数s6lと同一だとはまだ要求しない。'),
        ('znt','動く系の成分に方程式を要求する四座標領域。先行する逆像領域との対応と真空の基礎説明は未完。'),
        ('znu','この適用で参照する同じ六式の法則項目。法則の記号だけで式の内容を代用せず、sad2で既存の方程式内容への適合と結ぶ。'),
        ('znv','この適用で二系にわたり比較する同じ候補履歴への参照。実現した履歴だけへの限定や、全候補をこの一例に置換することはしない。'),
        ('znw','その候補履歴についての静止系の記述。'),
        ('znx','同じ候補履歴についての動く系の記述。数値や記述自体が静止系のものと等しいことを意味しない。'),
        ('zny','u0161で相対性原理に基づき条件付きで同じ方程式を要求する箇所。')):
        d=decls[name];basis['primitives'].append(dict(symbol=name,parameters=d['parameters'],result=d['result'],arguments=[],meaning_ja=meaning))
    basis['definitions'].update(MEANINGS|{
        'sac2':'動く系zbmに指定された二つの新しい場と領域が同じ文脈で結び付き、その成分が既存s5yの六式を同じVで満たすという内容。',
        'sad2':'比較対象の二系、選択した同じ法則と候補履歴、二つの対応記述、およびそれぞれの方程式内容への適合を結ぶ適用条件。',
        'sae2':'既存の相対性原理sawとsad2の明示的な適用条件を、同じ文脈で採用した前提。',
        'saf2':'静止系の方程式内容s5zが成立するなら、動く系の新しい場についてsac2が成立するという条件文。両方が現在真であるとは断言しない。'})
    basis['unresolved'] += [
        'u0161の原理による条件付き要求と、u0162のM0300を部分記述した。適用条件sad2は原理から個別の式へ接続するために明示したもので、原文の全ての語がこの形で条件を列挙したとはしない。',
        'ponderomotorischen Wirkungen、elektrische bzw. magnetische Massen、力のベクトルの物理的な定義は未完であり、対応する語句を本文の明示範囲から除外する。',
        '同じ方程式への適合と、候補履歴が同じであること、成分値の同一性・比例関係、同じ測定法による同定は別の条件である。後続の二組の方程式の比較と共通係数は未記述。',
        '第一原理の既存の法則範囲・候補範囲・完全性の意味規約を再利用する。物理的な量の定義、真空、原刊照合と原文全体の意味一致確認は未完。']
    audit_basis(doc,basis)
    return format_graph(doc,'compact')+'\n',basis


def main():
    for builder,name in ((generic_composed,'law-specialization'),(composed,'einstein-law-specialization')):
        text,basis=builder()
        for filename,body in ((basis['document'],text),('data/'+name+'-basis-v1.json',json.dumps(basis,ensure_ascii=False,indent=2)+'\n')):
            path=ROOT/filename
            if path.exists():
                if path.read_text(encoding='utf-8')!=body:raise ValueError('Stored law specialization differs: '+filename)
            else:
                with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(body)
    print('Same-law specialization and independent moving-frame quantities composed')


if __name__=='__main__':main()
