"""Compose a fixed-point claim and the reviewed light-speed specialization."""
from copy import deepcopy
import json

from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from scripts.compose_origin_clock import ROOT, CUT, definition, v
from scripts.compose_limits import call as k, op, both, quant as q


def definitions():
    V,w,U=map(v,('limit','moving','result'))
    f,x=v('operation'),v('value');applied='c['+f+']['+x+']'
    text=definition('s4b','operation h['+CUT+'] '+CUT+' value '+CUT,
        both(k('ba',x),k('ba',applied),k('sca',applied,x)))
    text+=definition('s4c','limit b moving b result b',k('s3f',V,V,w,U))
    text+=definition('s4d','limit '+CUT+' moving '+CUT+' result '+CUT,k('s3g',V,V,w,U))
    operation='i[value '+CUT+']['+k('s3j',V,x,w)+']'
    result=k('s3j',V,V,w)
    text+=definition('s4e','limit '+CUT+' moving '+CUT,
        op('y',k('s3s',V,w),both(k('s4d',V,w,result),k('s4b',operation,V))))
    text+=definition('s4f','limit '+CUT,both(k('ba',V),k('bg',k('bb','n p a b'),V),
        q('f','moving',CUT,k('s4e',V,w))))
    return text


def composed():
    doc=parse((ROOT/'examples/v014/einstein-speed-deficits.noema').read_text(encoding='utf-8'))
    statements,doc['statements']=doc['statements'],[]
    text=format_graph(doc,'compact')+definitions()+'r zlm[] a.r zln[] a.\n'
    V,w,U=k('tc'),k('zkq'),k('zkp')
    text+=definition('s4g','','b context['+k('s4f',V)+']','e')
    text+=definition('s4h','','b context['+both(k('s3s',V,w),k('szs',U,k('zke')),
        k('s4d',V,w,U),k('sca',U,V))+']','e')
    W=v('moving');result=k('s3j',V,V,W)
    text+=definition('s4i','','b context['+both(k('ba',V),k('bg',k('bb','n p a b'),V),
        q('f','moving',CUT,op('y',k('s3s',V,W),k('s4d',V,W,result))))+']','e')
    doc=parse(text);doc['statements']=statements
    doc=parse(format_graph(doc,'compact')+'''
s[k zc[k zlm[] k rd[] r[k s4i[]] r[k s4g[]] k zkf[] k ri[]]].
s[k uh[k zln[] k rd[] r[k s4h[]] k zkf[] k ri[]]].
''')
    basis=deepcopy(json.loads((ROOT/'data/speed-deficits-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='light-invariance-basis-v1',document='examples/v014/einstein-light-invariance.noema')
    decls={d['name']:d for d in doc['declarations']}
    for name,meaning in (('zlm','光速度が光速未満の速度との合成で変わらないと述べる箇所。'),('zln','光速度を代入した商とVとの等式を示すM0273の箇所。')):
        d=decls[name];basis['primitives'].append(dict(symbol=name,parameters=d['parameters'],result=d['result'],arguments=[],meaning_ja=meaning))
    basis['definitions'].update({
        's4b':'一引数の実切断関数に対して、有効な入力値と有効な出力値が等しいという不動点の関係。速度に限らず使える。',
        's4c':'有理数の一次元合成式s3fの一方の入力を上限Vにした関係。V>0と非零分母を要求するが、もう一方の入力の光速未満という制限とU=Vは埋め込まない。',
        's4d':'有効な実切断と非零分母を要求するs3gで、一方の入力をVにした関係。訂正済みM0273の商(V+w)/(1+w/V)に対応する。',
        's4e':'0≤w<Vなら、一次元式で構成した結果がs4dを満たし、その合成操作に対してVが不動点になる。入力範囲の外での含意成立を速度不変性の実例とはしない。',
        's4f':'正の有効なVについて、任意の実切断wに対するs4eを全称量化した主張。有限の速度一覧へ縮めない。',
        's4g':'光速度tcに関するs4fの内容。前段に続く非負の一次元速度の読みを採用する。',
        's4h':'既存のwが0≤w<V、既存のUが同じ物理的文脈の速さであり、訂正済みの商に等しく、さらにVに等しいという内容。',
        's4i':'任意の0≤w<Vに対して、先行する一次元式でVとwから構成した結果がその特殊化を満たす、という前提内容。'})
    basis['unresolved'] += [
        'u0145とu0146の部分記述。速度範囲は前段の非負の同方向の読みを引き継ぐ。符号付き入力の代数は別に検査するが、任意方向の物理的主張へ拡張しない。',
        'M0273は訂正記録を明示的に採用し、分母を1+w/Vとする。原文スナップショットの小文字vは書き換えない。',
        '合成式の引数Vへの特殊化を表し、既存の座標系速度zb7=Vとは述べない。光速の座標系や発散するローレンツ係数を物理的に許容したことにはしない。',
        '代数上はw≠−Vなら結果Vとなるが、この広い領域を原文の光速未満の適用範囲と同一視しない。w=−Vは分母零として除外する。',
        '全実切断の体・順序の法則、歴史的な方向の規約、後続の二変換の合成、原文全体との意味一致確認は未完。']
    audit_basis(doc,basis)
    return format_graph(doc,'compact')+'\n',basis


def main():
    text,basis=composed()
    for name,body in ((basis['document'],text),('data/light-invariance-basis-v1.json',json.dumps(basis,ensure_ascii=False,indent=2)+'\n')):
        path=ROOT/name
        if path.exists():
            if path.read_text(encoding='utf-8')!=body:raise ValueError('Stored light invariance differs: '+name)
        else:
            with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(body)
    print('Fixed-point claim and reviewed light-speed specialization composed')


if __name__=='__main__':main()
