"""Keep axial support, directed motion and the signed scalar quotient distinct."""
from copy import deepcopy
import json

from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from scripts.compose_origin_clock import ROOT, CUT, definition, v
from scripts.compose_limits import call as k, op, both


def definitions():
    V,s,w,U=map(v,('light','speed','moving','result'));zero='n p a b'
    mul=lambda a,b:k('ad',a,b);add=lambda a,b:k('ab',a,b)
    D=add(mul(V,V),mul(s,w))
    text=definition('s3f','light b speed b moving b result b',both(k('aa',zero,V),op('u',op('e',D,zero)),
        op('e',mul(D,U),mul(mul(V,V),add(s,w)))))
    zero=k('bb',zero);one=k('bb','n p b b');den=k('s2s',V,s,w,one)
    text+=definition('s3j','light '+CUT+' speed '+CUT+' moving '+CUT,k('shv',k('bd',s,w),k('sjt',den)),CUT)
    text+=definition('s3g','light '+CUT+' speed '+CUT+' moving '+CUT+' result '+CUT,both(
        *(k('ba',a) for a in (V,s,w,U)),k('bg',zero,V),op('u',k('sca',den,zero)),k('sca',U,k('s3j',V,s,w))))
    x,y,r=map(v,('longitudinal','transverse','magnitude'))
    text+=definition('s3h','longitudinal '+CUT+' transverse '+CUT,both(k('ba',x),k('ba',y),k('sca',y,zero)))
    text+=definition('s3i','longitudinal '+CUT+' transverse '+CUT+' magnitude '+CUT,both(k('s3h',x,y),
        k('szn',r,x,y),k('bg',zero,r),k('sca',x,r)))
    return text


def composed():
    doc=parse((ROOT/'examples/v014/einstein-calculation-discourse.noema').read_text(encoding='utf-8'))
    statements,doc['statements']=doc['statements'],[]
    text=format_graph(doc,'compact')+definitions()+'r zlf[] a.\n'
    zero=k('bb','n p a b')
    text+=definition('s3k','','b context['+both(k('syw'),k('szt',k('zkq'),k('zke')),
        k('bg',zero,k('zb7')),k('s3i',k('zkc'),k('zkd'),k('zkq')))+']','e')
    text+=definition('s3l','','b context['+both(k('szs',k('zkp'),k('zke')),
        k('s3g',k('tc'),k('zb7'),k('zkq'),k('zkp')))+']','e')
    text+=definition('s3m','','b context['+op('y','t[k s3k[]][v context]','t[k s3l[]][v context]')+']','e')
    doc=parse(text);doc['statements']=statements
    doc=parse(format_graph(doc,'compact')+'s[k zc[k zlf[] k rd[] r[k s3k[]] r[k s3l[]] k zkf[] k ri[]]].\n')
    basis=deepcopy(json.loads((ROOT/'data/calculation-discourse-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='axial-composition-basis-v1',document='examples/v014/einstein-axial-composition.noema')
    d=next(d for d in doc['declarations'] if d['name']=='zlf')
    basis['primitives'].append(dict(symbol='zlf',parameters=d['parameters'],result=d['result'],arguments=[],
        meaning_ja='wも縦軸方向である場合に速度合成式M0263を得ると述べる本文箇所。'))
    basis['definitions'].update({
        's3f':'有理数の符号付き一次元合成。V>0、D=V²+v*w≠0、D*U=V²*(v+w)。入力や結果を非負の速さへ自動変換しない。',
        's3j':'実切断による(v+w)/(1+v*w/V²)の構成式。分母に既存s2s、外側の除算に符号付き逆数sjtを使う。定義域はs3gで要求する。',
        's3g':'有効な実切断、正のV、非零分母の下で、符号付きのUがs3jの値であるという関係。光速未満や方向の条件は式の定義域と区別する。',
        's3h':'平面内の縦・横速度成分が有効で、横成分が0である。同じ軸に沿う正負の運動と零速度を許し、正方向という意味は付けない。',
        's3i':'s3hに非負ノルムを結び、大きさが正で縦成分と等しいことを要求する。正方向への非零の運動であり、逆方向・零速度とは区別する。',
        's3k':'既存の点の運動と同じwの大きさを保ち、点が縦軸の正方向へ進み、基準系速度vも正であるという採用した条件の読み。原文の符号規約の唯一の解釈とはしない。',
        's3l':'同じ点の静止系の座標微分から得た非負の速さUが、M0263の一次元式を満たす内容。符号付きの式単独と、測定対象への接続を区別する。',
        's3m':'s3kが成立するならs3lが成立するという条件内容。条件の成立、結論の無条件の真理、著者への推論の帰属は別々に扱う。'})
    basis['unresolved'] += [
        'u0141後半とM0263を部分記述した。Richtung der X-Achseを正の縦方向として読む規約を明示し、軸上という条件だけに弱めない。',
        '原文中の速度の正負と方向の歴史的な規約は全体として未確定。零速度には方向を与えず、式の零入力での成立を別に検査する。',
        '非負速度での角の式との接続、符号付き速度の光速未満の保存は有理数の補助検査を持つが、全実切断の体・平方根の一般法則と物理モデルの機械的証明は未完。',
        '原刊906頁のM0263を照合した。後続の二速度が光速未満である場合の本文、欠損量κ・λによる論証、光速度の不変性と全文の意味一致確認は残る。']
    audit_basis(doc,basis)
    return format_graph(doc,'compact')+'\n',basis


def main():
    text,basis=composed()
    for name,body in ((basis['document'],text),('data/axial-composition-basis-v1.json',json.dumps(basis,ensure_ascii=False,indent=2)+'\n')):
        path=ROOT/name
        if path.exists():
            if path.read_text(encoding='utf-8')!=body:raise ValueError('Stored axial composition differs: '+name)
        else:
            with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(body)
    print('Axial support, positive direction and signed scalar composition composed')


if __name__=='__main__':main()
