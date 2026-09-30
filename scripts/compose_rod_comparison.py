"""Keep frame-relative naming, attributed necessity and announced derivation apart."""
from copy import deepcopy
import json

from noema.grammar import format_graph, parse
from noema.meaning_basis import audit_basis
from scripts.compose_event_time import ROOT


def definitions():
    return '''
d sbx[value h[b] c baseline h[b] c measured h[h[b] c] c valid h[h[b] c] c comparison h[h[b] c h[b] c] c] c[
 w[c[v valid][v value]][w[c[v valid][v baseline]][w[c[v measured][v value]][c[v comparison][v value v baseline]]]]
].
d sby[value h[b] c measured h[h[b] c] c same h[h[b] c h[b] c] c] c[
 w[c[v measured][v value]][f other h[b] c[y[c[v measured][v other]][c[v same][v value v other]]]]
].
d sbz[baseline h[b] c measured h[h[b] c] c valid h[h[b] c] c same h[h[b] c h[b] c] c comparison h[h[b] c h[b] c] c] c[
 g value h[b] c[w[k sbx[v value v baseline v measured v valid v comparison]][k sby[v value v measured v same]]]
].
d sca[first h[b] c second h[b] c] c[k sag[v first v second p bc]].
d scb[first h[b] c second h[b] c] c[u[k sca[v first v second]]].
'''


MEANINGS = {
    'sbx':'候補と比較基準が有効な値であり、指定方法で候補が得られ、同じ候補と基準が指定比較関係を満たす。基準のすり替えや未測定値の比較を許さない。',
    'sby':'指定候補が測定条件を満たし、条件を満たす全候補が指定の値の同一性でこれに一致する。空の結果集合を一意な結果とは扱わない。',
    'sbz':'存在する一意な測定値が、基準との指定比較関係を満たすという読み。一意性は値の同一性によるもので、関数の実装同一性によらない。',
    'sca':'実数を表す下側切断の両方向包含による値の一致。有効な切断であることは利用側が要求する。',
    'scb':'scaの否定による値の不一致。どちらが大きいかは決めない。',
}


def generic_composed():
    doc=parse((ROOT/'examples/v014/rod-setup.noema').read_text(encoding='utf-8')+definitions())
    basis=deepcopy(json.loads((ROOT/'data/rod-setup-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='rod-comparison-basis-v1',document='examples/v014/rod-comparison.noema')
    basis['definitions'].update(MEANINGS)
    basis['unresolved'] += [
        'sby・sbzは実切断の関数領域全体に量化する。有限の候補だけでその存在・一意性を認定しない。',
        'sbzは定冠詞を存在・一意性として読む解釈を明示したもので、自然言語の定冠詞の一般的な理論ではない。',
        '比較の内容が真であること、著者がその比較を述べたこと、理由からその比較を導出したことは別に扱う。']
    audit_basis(doc,basis)
    return format_graph(doc,'compact')+'\n',basis


def source_composed():
    old=parse((ROOT/'examples/v014/einstein-rod-setup.noema').read_text(encoding='utf-8'))
    statements,old['statements']=old['statements'],[]
    doc=parse(format_graph(old,'compact')+definitions()+'''
r za[a a a h[b] c d] c.
r zb[a a i[h[h[b] c d] c] i[h[h[b] c d] c] a d] c.
r zc[a a i[e] i[e] a d] c.
r zd[a a i[g[h[b] c]] i[e] j[i[e]] a a d] c.
r ze[] a.r zf[] a.r zg[] a.r zh[] a.r zi[] a.
d scc[] e[b context[
 k sbz[k ya[] i[value h[b] c][k sbi[v value k ye[]]] p sbg p sca p sca]
]].
d scd[] e[b context[
 k sbz[k ya[] i[value h[b] c][k sbk[v value k yf[]]] p sbg p sca p scb]
]].
d sce[method h[h[b] c d] c setting d] g[h[b] c][j v[i[value h[b] c][c[v method][v value v setting]]]].
d scf[] g[h[b] c][k sce[p sbk k yf[]]].
d scg[value h[b] c context d] c[
 w[k xa[k xi[]]][w[k va[k xl[]]][w[k ti[k ta[]]][k za[k xi[] k xl[] k ta[] v value v context]]]]
].
d sch[value h[b] c context d] c[
 w[k xa[k xi[]]][w[k va[k ra[]]][w[k ti[k ta[]]][w[k xm[k xi[] k ra[] v context]][k za[k xi[] k ra[] k ta[] v value v context]]]]]
].
''')
    doc['statements']=statements
    doc=parse(format_graph(doc,'compact')+'''
s[k zb[k ze[] k rd[] r[p sbi] r[p scg] k xy[] k ri[]]].
s[k zb[k zf[] k rd[] r[p sbk] r[p sch] k xy[] k ri[]]].
s[k zc[k zg[] k rd[] r[k saw[]] r[k scc[]] k xy[] k ri[]]].
s[k zd[k zh[] k rd[] r[k scf[]] r[k scd[]] l[i[e]][r[k saw[]] r[k sbd[]]] k zi[] k xy[] k ri[]]].
''')
    basis=deepcopy(json.loads((ROOT/'data/einstein-rod-setup-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='einstein-rod-comparison-basis-v1',document='examples/v014/einstein-rod-comparison.noema')
    for prior_gap in (
        'u0032以降の長さの命名、静止時の長さとの同値、二原理からの相違の導出、旧運動学への帰属は未記述。',
        '本草案で初期設定と問いを部分的に接続したが、u0032以降の同値・相違・論証と原刊照合、全文の意味確認は残る。',
    ):
        basis['unresolved'].remove(prior_gap)
    basis['definitions'].update(MEANINGS)
    descriptions=[
        ('za',['object','frame','length_unit','value','context'],'対象の長さを指定基準系・単位・文脈で指定値として記述する数量関係。どの測定規約がこの呼称を満たすかは命名による接続で指定する。一般的な長さの構成説明は未完。'),
        ('zb',['node','author','method','label','scope','context'],'著者が指定方法で得られる量を、指定した構成的な数量記述によって呼ぶという命名規約を提示する。両記述を評価して測定の実行済み事実に変換しない。'),
        ('zc',['node','author','premise','conclusion','scope','context'],'著者がこの前提の記述に基づき、この結論の記述が従わなければならないと述べる。述べたという帰属であり、前提・結論の真理や有効な導出の検証を含まない。'),
        ('zd',['node','author','question','expected_conclusion','premises','later_argument','scope','context'],'著者が後続の議論で、指定した前提群に基づき質問の値を決め、指定した結論を得ると予告する。将来の論述を指すものであり、既に決定・導出・測定が成功したことは含意しない。'),
        ('ze',[],'方法aの長さの呼び方を提示する本文箇所。'),
        ('zf',[],'方法bの長さの呼び方を提示する本文箇所。'),
        ('zg',[],'相対性原理による初期長との一致を述べる本文箇所。'),
        ('zh',[],'二原理から方法bの値を定めて違いを得ると予告する本文箇所。'),
        ('zi',[],'値の決定と比較を行うと予告された後続議論。具体的な段落・導出との接続は未完。'),
    ]
    declarations={d['name']:d for d in doc['declarations']}
    for name,args,meaning in descriptions:
        d=declarations[name]
        basis['primitives'].append(dict(symbol=name,parameters=d['parameters'],result=d['result'],arguments=args,meaning_ja=meaning))
    basis['definitions'].update({
        'scc':'方法aの一意な正の長さが、初期静止長yaと値として一致するという内容。方法aの測定設定yeを使う。',
        'scd':'方法bの一意な正の長さが、同じ初期静止長yaとは一致しないという内容。方法bの測定設定yfを使い、収縮方向や具体的な公式は補わない。',
        'sce':'指定方法・設定における長さの値を問う質問。答えの存在・唯一性は質問の構成だけでは要求しない。',
        'scf':'これから決定すると予告された方法bの長さの質問。二方法全体の問いsbvとは区別する。',
        'scg':'同じ棒の長さを、移動側の基準系xlと長さ単位taに関して述べる構成的な数量記述。',
        'sch':'同じ運動する棒の長さを、静止側の基準系raと同じ単位taに関して述べる構成的な数量記述。'})
    basis['unresolved'] += generic_composed()[1]['unresolved'][-3:] + [
        'u0032・u0033の命名・等値の帰属・決定予告を本草案で部分接続した。長さという数量の基礎、命名や論述行為の一般的説明は未完。',
        '必要性を著者の根拠付き主張として帰属したが、相対性原理と初期設定から等値が導かれることを証明したものではない。',
        '二原理はsawとsbdへの既存の記述参照で指定する。予告された後続議論の実体と、ローレンツ収縮の導出への接続は未完。',
        'u0034の旧運動学の暗黙の仮定と幾何学的置換、原刊照合、全文の意味確認は残る。']
    audit_basis(doc,basis)
    return format_graph(doc,'compact')+'\n',basis


def main():
    for compose,filename in ((generic_composed,'data/rod-comparison-basis-v1.json'),(source_composed,'data/einstein-rod-comparison-basis-v1.json')):
        text,basis=compose()
        for name,body in ((basis['document'],text),(filename,json.dumps(basis,ensure_ascii=False,indent=2)+'\n')):
            path=ROOT/name
            if path.exists():
                if path.read_text(encoding='utf-8')!=body:raise ValueError('Stored rod comparison differs: '+name)
            else:
                with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(body)
    print('Frame-relative length names, attributed equality and announced determination composed')


if __name__=='__main__':main()
