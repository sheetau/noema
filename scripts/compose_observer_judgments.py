"""Describe opposite observer judgments with their criteria and hypothetical scope."""
from copy import deepcopy
import json

from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from scripts.compose_moving_light_trip import ROOT, both

TRUE='e[n p a b][n p a b]'
FALSE='u['+TRUE+']'


def definitions():
    return '''
d sdk[who a description i[e] polarity c context d judges h[a i[e] c d] c] c[
 c[v judges][v who v description v polarity v context]
].
d sdl[who a description i[e] polarity c context d judges h[a i[e] c d] c] c[
 w[k sdk[v who v description v polarity v context v judges]][z[v polarity][t[s[v description]][v context]]]
].
'''


MEANINGS={
    'sdk':'同じ主体・内容の記述・肯否・文脈について判断が帰属される。否定判断は肯定判断の不在ではない。内容を評価せず、実際に正しいことも含意しない。',
    'sdl':'sdkに加え、記述を明示的に評価した内容の現在文脈での真偽が、判断の肯否と一致する。正当化や知識一般の十分条件ではない。',
}


def generic_composed():
    doc=parse('n:\n'+definitions())
    basis={'version':'observer-judgments-basis-v1','document':'examples/v014/observer-judgments.noema',
        'primitives':[],'definitions':MEANINGS.copy(),'unresolved':[
            '判断の帰属関係は引数で与える。証拠・認識・推論から判断が成立する一般理論は未構成。',
            '同じ真偽の別記述への置換、全ての判断の無矛盾性や完全性は仮定しない。']}
    audit_basis(doc,basis)
    return format_graph(doc,'compact')+'\n',basis


def source_composed():
    old=parse((ROOT/'examples/v014/einstein-moving-light-trip.noema').read_text(encoding='utf-8'))
    statements,old['statements']=old['statements'],[]
    text=format_graph(old,'compact')+definitions()+'''
r zba[a i[e] c d] c.r zbb[] a.r zbc[a a i[e] i[e] a d] c.
d sdm[midpoint h[h[b] c h[b] c h[b] c] c] c[
 c[v midpoint][k zag[k zas[]] k zag[k zat[]] k zag[k zau[]]]
].
d sdn[context d tracking h[a d] c] c[
 w[c[v tracking][k zaj[] v context]][c[v tracking][k zak[] v context]]
].
d sdo[] e[b context[k sdm[p bi]]].
d sdp[] e[b context[k sdn[v context p scx]]].
'''
    args='context d judges h[a i[e] c d] c'
    text+='d sdq['+args+'] c['+both(*(
        f'k sdk[k {who}[] r[k sdo[]] {FALSE} v context v judges]' for who in ('zay','zaz')))+'].\n'
    observer='w[k xb[v who]][k x4[v who k ra[] v context]]'
    text+='d sdr['+args+'] c['+both('g who a['+observer+']',
        'f who a[y['+observer+'][k sdk[v who r[k sdp[]] '+TRUE+' v context v judges]]]')+'].\n'
    text+='''
d sds[context d judges h[a i[e] c d] c] c[w[k sdq[v context v judges]][k sdr[v context v judges]]].
d sdt[] e[b context[k sds[k yd[] p zba]]].
d sdu[] e[b context[
 w[t[k scy[]][v context]][w[t[k sdh[]][v context]][w[t[k sdj[]][v context]][k bg[k bb[n p a b] k yb[]]]]]
]].
d sdv[] e[b context[k sdq[k yd[] p zba]]].
d sdw[] e[b context[k sdr[k yd[] p zba]]].
'''
    doc=parse(text);doc['statements']=statements
    doc=parse(format_graph(doc,'compact')+'''
s[k zc[k zbb[] k rd[] r[k sdu[]] r[k sdt[]] k xy[] k ri[]]].
s[k zbc[k zbb[] k rd[] r[k sdv[]] r[k sdw[]] k xy[] k ri[]]].
''')
    basis=deepcopy(json.loads((ROOT/'data/einstein-moving-light-trip-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='einstein-observer-judgments-basis-v1',document='examples/v014/einstein-observer-judgments.noema')
    basis['definitions'].update(MEANINGS)
    decls={d['name']:d for d in doc['declarations']}
    for name,args,meaning in (
        ('zba',['observer','description','polarity','context'],'観測者が指定内容を肯定または否定と判断するという関係。想定された運動文脈で用い、現実の観測の発生や正当な推論をそれだけでは主張しない。'),
        ('zbb',[],'共動する観測者と静止系の観測者の同期判断を対比する本文箇所。'),
        ('zbc',['node','author','first_content','second_content','scope','context'],'著者が指定範囲で二つの内容を対比して提示する。第一・第二の順序を保持し、内容自体の真理や論理的矛盾を含意しない。')):
        d=decls[name]
        basis['primitives'].append(dict(symbol=name,parameters=d['parameters'],result=d['result'],arguments=args,meaning_ja=meaning))
    basis['definitions'].update({
        'sdm':'既存の同じ光往復の三記録の時計指示へ、引数の中点条件を適用した結果。記録と時計・光・試行の適切な接続は先行設定sdhで要求する。',
        'sdn':'同じ二時計が、同じ文脈で引数の時刻追従条件をそれぞれ満たす。',
        'sdo':'sdoの内容は、設定済みの三時計指示がbiの中点条件を満たすこと。時計が静止しているとの条件を補わない。',
        'sdp':'同じ二時計が静止系の局所時刻へ追従するというscxの内容。先行する限定付きの同期という呼称zanに接続する解釈。',
        'sdq':'先行設定で各時計と共に動く二観測者が、sdoの内容をともに否定と判断する。sdoの真偽自体は評価しない。',
        'sdr':'同じ文脈で静止系に静止している観測者の範囲が非空で、全員がsdpの内容を肯定と判断する。個人の名を新たに作らない。',
        'sds':'同じ文脈においてsdqとsdrの異なる基準の判断が併存する。無条件の同期と非同期という一つの命題の矛盾にはしない。',
        'sdt':'運動の想定文脈ydにおける二群の判断の内容。著者の条件付きの推論結果として引用する。',
        'sdu':'先行する時計の設定scy、試行と観測者sdh、往復時間の結果sdj、正の棒速度を同時に保持した推論の前提内容。',
        'sdv':'対比の第一項、想定文脈ydでの共動観測者の否定判断。',
        'sdw':'対比の第二項、想定文脈ydでの静止系の観測者の肯定判断。'})
    old_pending='中点条件の適用を、条件が成立するとの判定に置き換えない。u0040後半の観測者ごとの判定の帰属と、u0041の一般的な相対的同時性への結論は未接続。'
    basis['unresolved'].remove(old_pending)
    basis['unresolved']+=generic_composed()[1]['unresolved']+[
        'u0040後半の部分解釈。静止系の観測者の肯定を、直前の静止系時刻への追従による限定付きの同期scxとして読む。中点条件の肯定としては読まない。',
        '静止系の観測者を同じ設定内の非空の全観測者として記述する。現実の全人類への量化ではない。würdenの様相全体や認識から発言に至る一般過程は未説明。',
        '正しい数値条件だけから観測者が判断することは論理的に導けない。著者の推論帰属zcと別に、認識・計算能力等の橋渡しが残る。',
        'u0041の相対的同時性への一般化、原刊画像の照合、本文全体の意味確認は未完。']
    audit_basis(doc,basis)
    return format_graph(doc,'compact')+'\n',basis


def main():
    for compose,filename in ((generic_composed,'data/observer-judgments-basis-v1.json'),(source_composed,'data/einstein-observer-judgments-basis-v1.json')):
        text,basis=compose()
        for name,body in ((basis['document'],text),(filename,json.dumps(basis,ensure_ascii=False,indent=2)+'\n')):
            path=ROOT/name
            if path.exists():
                if path.read_text(encoding='utf-8')!=body:raise ValueError('Stored observer judgment differs: '+name)
            else:
                with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(body)
    print('Criterion-sensitive observer judgments composed')


if __name__=='__main__':main()
