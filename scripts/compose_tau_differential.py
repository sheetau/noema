"""Describe the small-displacement step with explicit local differentiability."""
from copy import deepcopy
import json

from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from scripts.compose_moving_light_trip import ROOT, both
from scripts.compose_homogeneous_coordinates import CUT
from scripts.compose_comoving_labels import TAU


def rational_definitions():
    return '''
d ska[light b speed b space b time b outward b returning b] c[
 w[k sjb[n p b b v light v speed v outward v returning]][
 e[k ad[k ad[n p b c k ab[v outward v returning]] v time]][k ab[v space k ad[v outward v time]]]]].
d skb[light b speed b space b time b] c[
 w[u[k aa[v speed n p a b]]][w[k aa[v speed v light]][
 e[k ab[k ad[k ab[k ad[v light v light] k ac[k ad[v speed v speed]]] v space] k ad[v speed v time]]][n p a b]]]].
'''


MEANINGS={
    'ska':'正の分母の二逆数を明示した有理数の微分係数の式。½(1/(V-v)+1/(V+v))*τt=τx+τt/(V-v)。係数が実際の偏導関数であることは別に要求する。',
    'skb':'有理数の同じ係数について、0≤v<Vのもとで(V²-v²)*τx+v*τt=0という分母を払った式。',
}


def generic_composed():
    text=(ROOT/'examples/v014/light-time-arguments.noema').read_text(encoding='utf-8')
    doc=parse(text+rational_definitions())
    basis=deepcopy(json.loads((ROOT/'data/light-time-arguments-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='tau-differential-basis-v1',document='examples/v014/tau-differential.noema')
    basis['definitions'].update(MEANINGS)
    basis['unresolved']+=['微分係数の式の有理数代数を、関数の微分可能性や極限による導出の証明と同一視しない。']
    audit_basis(doc,basis)
    return format_graph(doc,'compact')+'\n',basis


LIMIT_ALIASES={'la':'sjo','lb':'sjp','lc':'sjq','ld':'sjr','li':'sjs','cd':'shv','cg':'sjt'}


def limit_declarations():
    old=parse((ROOT/'examples/v011/limits.noema').read_text(encoding='utf-8'))
    def rename(node):
        if isinstance(node,list):return [rename(x) for x in node]
        if not isinstance(node,dict):return node
        result={k:rename(v) for k,v in node.items()}
        if result.get('symbol') in LIMIT_ALIASES:result['symbol']=LIMIT_ALIASES[result['symbol']]
        if result.get('kind')=='definition':result['name']=LIMIT_ALIASES.get(result['name'],result['name'])
        return result
    return [rename(d) for d in old['declarations'] if d['name'] in ('la','lb','lc','ld','li')]


def source_composed():
    doc=parse((ROOT/'examples/v014/einstein-light-time-arguments.noema').read_text(encoding='utf-8'))
    statements,doc['statements']=doc['statements'],[]
    text=format_graph(doc,'compact')+rational_definitions()+'''
d sju[value h[b] c] c[k bc[k bb[n p a b] v value]].
d sjt[value h[b] c] h[b] c[i[q b][x[w[k sju[v value]][c[k sjd[v value]][v q]]][w[u[k sju[v value]]][c[k be[k sjd[k be[v value]]]][v q]]]]].
'''
    doc=parse(text);doc['declarations']+=limit_declarations();text=format_graph(doc,'compact')
    zero='k bb[n p a b]';one='k bb[n p b b]'
    variables=('x','y','z','time','spacederivative','timederivative')
    parameters='function '+TAU+' '+' '.join(n+' '+CUT for n in variables)
    base='c[v function][v x v y v z v time]'
    norm='k bd[k shu[v dx] k shu[v dt]]'
    shifted='c[v function][k bd[v x v dx] v y v z k bd[v time v dt]]'
    linear='k bd['+base+' k bd[k shv[v spacederivative v dx] k shv[v timederivative v dt]]]'
    increments=both('k ba[v dx]','k ba[v dt]','k bg['+zero+' '+norm+']','k bg['+norm+' v delta]')
    bound='k sjp['+shifted+' '+linear+' k shv[v epsilon '+norm+']]'
    local='f epsilon '+CUT+'[y['+both('k ba[v epsilon]','k bg['+zero+' v epsilon]')+'][g delta '+CUT+'['+both(
        'k ba[v delta]','k bg['+zero+' v delta]',
        'f dx '+CUT+'[f dt '+CUT+'[y['+increments+']['+bound+']]]')+']]]'
    text+='d sjv['+parameters+'] c['+both(*('k ba[v '+n+']' for n in variables),'k ba['+base+']',local)+'].\n'
    text+='d sjw['+parameters+'] c['+both(*('k ba[v '+n+']' for n in variables),
        'k sjs[p ba i[position '+CUT+'][c[v function][v position v y v z v time]] v x v spacederivative]',
        'k sjs[p ba i[moment '+CUT+'][c[v function][v x v y v z v moment]] v time v timederivative]')+'].\n'
    coefficient_args='light '+CUT+' speed '+CUT+' space '+CUT+' time '+CUT
    guards=[*('k ba[v '+n+']' for n in ('light','speed','space','time')),'k bc['+zero+' v speed]','k bg[v speed v light]']
    alpha='k sjd[k bf[v light v speed]]';beta='k sjd[k bd[v light v speed]]'
    lhs='k shv[k bj[n p b c k bd['+alpha+' '+beta+']] v time]'
    rhs='k bd[v space k shv['+alpha+' v time]]'
    text+='d sjx['+coefficient_args+'] c['+both(*guards,'k sca['+lhs+' '+rhs+']')+'].\n'
    denominator='k bf[k shv[v light v light] k shv[v speed v speed]]'
    text+='d sjy['+coefficient_args+'] c['+both(*guards,
        'k sca[k bd[v space k shv[k sje[v speed '+denominator+'] v time]] '+zero+']')+'].\n'
    text+='d skc[function '+TAU+' light '+CUT+' speed '+CUT+' time '+CUT+' radius '+CUT+'] c['+both(
        'k ba[v radius]','k bg['+zero+' v radius]',
        'f step '+CUT+'[y['+both('k ba[v step]','k bg['+zero+' v step]','k bg[v step v radius]')+'][k sjg[v function v step v light v speed v time]]]')+'].\n'
    text+='''
r zd5[] h[b] c.r zd6[] h[b] c.r zd7[] h[b] c.r zea[] a.r zeb[] a.
'''
    time='k sjh[k qe[k zdq[]] v context]'
    partialargs='k zd4[] '+zero+' '+zero+' '+zero+' '+time+' k zd6[] k zd7[]'
    text+='d skd[context d] c['+both('k sjl[v context]',
        'k skc[k zd4[] k tc[] k zb7[] '+time+' k zd5[]]',
        'k sjv['+partialargs+']','k sjw['+partialargs+']')+'].\n'
    text+='''
d ske[] e[b context[k skd[k zb6[]]]].
d skf[] e[b context[k sjx[k tc[] k zb7[] k zd6[] k zd7[]]]].
d skg[] e[b context[k sjy[k tc[] k zb7[] k zd6[] k zd7[]]]].
'''
    doc=parse(text);doc['statements']=statements
    doc=parse(format_graph(doc,'compact')+'''
s[k zc[k zea[] k rd[] r[k ske[]] r[k skf[]] k rh[] k ri[]]].
s[k zd3[k zeb[] k rd[] r[k ske[]] r[k skf[]] r[k skg[]] k rh[] k ri[]]].
''')
    basis=deepcopy(json.loads((ROOT/'data/einstein-light-time-arguments-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='einstein-tau-differential-basis-v1',document='examples/v014/einstein-tau-differential.noema')
    basis['definitions'].update(MEANINGS)
    old_basis=json.loads((ROOT/'data/limits-basis-v1.json').read_text(encoding='utf-8'))
    for old,new in LIMIT_ALIASES.items():
        if old in ('la','lb','lc','ld','li'):basis['definitions'][new]='既存の'+old+'と同じ定義を記号を置換して再利用。'+old_basis['definitions'][old]
    basis['definitions'].update({
        'sju':'有効な実切断について0以上の値である条件。',
        'sjt':'非零の実切断の符号付き逆数。正ならsjd、負なら符号を反転してsjdを適用し再び符号反転する。差商では零を除く。',
        'sjv':'指定した(x′,y,z,t)でy,zを固定し、x′とtの二変数に関して、指定した二係数による一次近似の誤差が任意のεに対しε*(|dx|+|dt|)未満になる局所的な全微分可能性。正の近傍半径を存在量化し、全ての非零の微小な変位を検査する。',
        'sjw':'同じ四引数関数・評価点について、他の三変数を固定したx′とtの各切片の微分をsjsで指定する。別々の偏微分の存在だけでsjvを含意させない。',
        'sjx':'有効な実切断の二偏微分値について、原文M0103の逆数の和を含む等式を構成する。0≤v<Vの範囲を保持する。',
        'sjy':'同じ二偏微分値について、原文M0104のτx+v/(V²-v²)*τt=0という等式を構成する。',
        'skc':'固定した候補τ・V・v・tについて、ある指定された正の半径より小さい全ての正の変位hで、前段の中点式が成立するという近傍条件。有限の選択例の一致ではない。',
        'skd':'前段の試行と関数の結合、任意に小さい正の変位での中点式、同じ点での二変数の全微分可能性と偏微分値を明示した推論前提。',
        'ske':'同じ設定でskdの前提を使うという内容。原文の無限小を、正の変位を0へ近づける極限として部分解釈する。',
        'skf':'原点で同じτ候補のx′・tの偏微分値が最初の微分形の式を満たすという内容。',
        'skg':'同じ偏微分値が分母V²-v²を持つ整理後の式を満たすという内容。'})
    declarations={d['name']:d for d in doc['declarations']}
    for name,meaning in (
        ('zd5','中点条件を課す正の変位の近傍半径の候補。単独の有限な試行距離とは区別する。'),
        ('zd6','同じτ候補の評価点(0,0,0,t)におけるx′偏微分の候補値。skdで実際の偏微分と結ぶ。'),
        ('zd7','同じτ候補の同じ評価点におけるt偏微分の候補値。'),
        ('zea','x′を無限小に選んだとき前の中点式から微分形が従うと述べる箇所。'),
        ('zeb','最初の微分形をτx+v/(V²-v²)*τt=0へ整理して提示する箇所。')):
        d=declarations[name];basis['primitives'].append(dict(symbol=name,parameters=d['parameters'],result=d['result'],arguments=[],meaning_ja=meaning))
    basis['unresolved']+=[
        'u0054〜u0057の部分記述。無限小という言い方を通常の実数の極限で解釈する。新しい無限小数を導入したとは主張しない。',
        '連鎖律を正当化する十分条件として二変数の全微分可能性と近傍全体の式を明示した。これらの前提が原文でこの形で明記されているとは主張しない。先行する線形性からの接続も未証明。',
        '極限・差商は既存定義を再利用するが、全実数上の連鎖律とこの極限による推論の一般的な機械的証明は未完。有理数の代数検査や有限モデルを代用しない。',
        '今回は原点と選択した静止系時刻での条件。後続の任意の出発点への一般化、y,z方向の条件、τの具体形、原刊照合、全文の意味確認は未完。']
    audit_basis(doc,basis)
    return format_graph(doc,'compact')+'\n',basis


def main():
    for compose,filename in ((generic_composed,'data/tau-differential-basis-v1.json'),(source_composed,'data/einstein-tau-differential-basis-v1.json')):
        text,basis=compose()
        for name,body in ((basis['document'],text),(filename,json.dumps(basis,ensure_ascii=False,indent=2)+'\n')):
            path=ROOT/name
            if path.exists():
                if path.read_text(encoding='utf-8')!=body:raise ValueError('Stored tau differential differs: '+name)
            else:
                with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(body)
    print('Local differentiability and tau differential equations composed')


if __name__=='__main__':main()
