"""Connect pulse criteria, clock relations and the author's scoped assumption."""
from copy import deepcopy
import json

from noema.grammar import format_graph, parse
from noema.meaning_basis import audit_basis
from noema.language import convert
from scripts.compose_limits import ROOT
from scripts.compose_clock_protocol import compose as clock_protocol, composed_basis as clock_basis
from scripts.compose_curve_discourse import conditional_basis


def definitions():
    return '''
d saa[selected h[a] c relation h[a a] c] c[
 f first a[f second a[y[w[c[v selected][v first]][c[v selected][v second]]][
  y[c[v relation][v second v first]][c[v relation][v first v second]]
 ]]]
].
d sab[selected h[a] c relation h[a a] c] c[
 f first a[f second a[f third a[y[w[c[v selected][v first]][w[c[v selected][v second]][c[v selected][v third]]]][
  y[w[c[v relation][v first v second]][c[v relation][v first v third]]][c[v relation][v second v third]]
 ]]]]
].
d sac[selected h[a] c relation h[a a] c reference a] c[
 w[c[v selected][v reference]][f clock a[y[c[v selected][v clock]][c[v relation][v clock v reference]]]]
].
d sad[trials h[a] c criterion h[a] c] c[
 w[g trial a[c[v trials][v trial]]][f trial a[y[c[v trials][v trial]][c[v criterion][v trial]]]]
].
'''


def generic_composed():
    doc=parse('n:\n'+definitions())
    basis={'version':'synchrony-network-basis-v1','document':'examples/v014/synchrony-network.noema','primitives':[],
        'definitions':{
            'saa':'指定範囲内の関係の対称性。対象の異なりを追加せず、自己関係も量化範囲に含める。',
            'sab':'範囲内の一つの対象が二つと関係するなら、その二つも関係するという条件。単なる対称性とは別に保持する。',
            'sac':'一つの共通参照対象が指定範囲に含まれ、範囲内の全対象がその同じ参照対象と関係する。各対象ごとに別の参照対象を選ばない。',
            'sad':'関連する試行が少なくとも一つあり、その全てで同じ判定条件が成立する。一回の成功や空集合を全体の成立にしない。'},
        'unresolved':[
            '関係と対象範囲は引数で与える。対称性とsabだけでは空の関係も成立し、全対象同士の関係や物理的実現可能性を保証しない。',
            'sacを対称性・sabと組み合わせた場合の全対象間の関係は論理的な条件付き帰結であり、観測や時計の調整可能性の証明ではない。',
            '試行範囲の完全性、測定誤差、連続時間での成立、原文の任意個数にわたる整合的実現は別に検討する。']}
    audit_basis(doc,basis)
    return format_graph(doc,'compact')+'\n',basis


def source_composed():
    doc=convert(parse(clock_protocol()),'0.14')
    text=format_graph(doc,'compact')+definitions()+'''
r qa[a a d] c.r qb[a a a a d a] c.
r qc[a] a.r qd[a] a.r qe[a] a.r qf[a] a.r qg[a] a.r qh[a] a.
r qi[a] h[b] c.r qj[a] h[b] c.r qk[a] h[b] c.r ql[a a a a d] c.
r ra[] a.r rb[] a.r rc[] a.r rd[] a.r re[] a.r rf[] a.r rg[] a.r rh[] a.r ri[] d.
r ug[a a i[e] a d] c.r uh[a a i[e] a d] c.
d qm[clock a frame a context d] c[w[k qa[v clock v frame v context]][w[k ca[v clock]][w[k cc[v clock v frame]][
 g place a[k cb[v clock v place v frame]]
]]]].
d qn[first a second a frame a unit a context d criterion h[a a a a a a a a a a h[b] c h[b] c h[b] c] c] c[
 w[k ql[v first v second v frame v unit v context]][
  k sad[i[trial a][k qb[v first v second v frame v unit v context v trial]]
   i[trial a][c[v criterion][v first v second k qc[v trial] k qd[v trial] k qe[v trial] k qf[v trial]
    k qg[v trial] k qh[v trial] v frame v unit k qi[v trial] k qj[v trial] k qk[v trial]]]]
 ]
].
d qo[first a second a frame a unit a context d] c[
 w[k qm[v first v frame v context]][w[k qm[v second v frame v context]][w[k ci[v unit]][
  x[e[v first][v second]][k qn[v first v second v frame v unit v context p db]]
 ]]]
].
d qv[frame a unit a context d] c[w[k ci[v unit]][w[g clock a[k qa[v clock v frame v context]]][
 f clock a[y[k qa[v clock v frame v context]][k qm[v clock v frame v context]]]
]]].
d qp[] e[b context[w[k qv[k ra[] k rb[] v context]][
 k saa[i[clock a][k qa[v clock k ra[] v context]] i[first a second a][k qo[v first v second k ra[] k rb[] v context]]]
]]].
d qq[] e[b context[w[k qv[k ra[] k rb[] v context]][
 k sab[i[clock a][k qa[v clock k ra[] v context]] i[first a second a][k qo[v first v second k ra[] k rb[] v context]]]
]]].
d qr[] e[b context[w[t[k qp[]][v context]][t[k qq[]][v context]]]].
d qs[] e[b context[w[k qv[k ra[] k rb[] v context]][
 k sac[i[clock a][k qa[v clock k ra[] v context]] i[first a second a][k qo[v first v second k ra[] k rb[] v context]] k rc[]]
]]].
s[w[k ug[k re[] k rd[] r[k qr[]] k rh[] k ri[]]][w[
 k uh[k rf[] k rd[] r[k qp[]] k rh[] k ri[]]
][k uh[k rg[] k rd[] r[k qq[]] k rh[] k ri[]]]]].
'''
    doc=parse(text)
    basis=deepcopy(clock_basis())
    basis.update(version='einstein-synchrony-network-basis-v1',document='examples/v014/einstein-synchrony-network.noema')
    basis['definitions'].update(generic_composed()[1]['definitions'])
    decls={d['name']:d for d in doc['declarations']}
    records=[
        ('qa',['clock','frame','context'],'この基準系と文脈で同期条件を検討する時計の範囲。数を二つや三つに固定しない。'),
        ('qb',['first_clock','second_clock','frame','unit','context','trial'],'同じ二時計・基準系・単位・評価文脈に関連する光往復の試行。現実の一回の実験だけに限らず、検討する理想的な試行も含められる。'),
        ('ql',['first_clock','second_clock','frame','unit','context'],'この組の評価ではqbで指定した試行が必要な範囲を尽くすという明示的な前提。検査器が現実の全時刻を調べたという認定ではない。')]
    for name,label in (('qc','出発側の場所'),('qd','反射側の場所'),('qe','出発の出来事'),('qf','反射の出来事'),('qg','帰着の出来事'),('qh','光信号')):
        records.append((name,['trial'],'同じ一往復の試行に対応する'+label+'。組合せの物理的な整合性はdbで確認する。'))
    for name,label in (('qi','出発'),('qj','反射'),('qk','帰着')):
        records.append((name,['trial'],'同じ一往復の'+label+'時の読みを表す実数の切断。値が実数の条件を満たすこと、時計・場所・単位への接続はdbで確認する。'))
    for name,label in (('ra','検討する静止基準系'),('rb','共通の時間単位'),('rc','全ての比較に使う同じ参照時計'),
        ('rd','著者'),('re','同期の整合性を仮定する箇所'),('rf','対称性を述べる箇所'),('rg','三時計の関係を述べる箇所'),('rh','同期規約の検討範囲'),('ri','この文章を提示する文脈')):
        records.append((name,[],label+'への局所参照。識別子だけを内容の説明の代用にしない。'))
    for name,args,meaning in records:
        d=decls[name]
        basis['primitives'].append({'symbol':name,'parameters':d['parameters'],'result':d['result'],'arguments':args,'meaning_ja':meaning})
    basis['primitives'] += [deepcopy(record) for record in conditional_basis()['primitives'] if record['symbol'] in ('ug','uh')]
    basis['definitions'].update({
        'qm':'選択された時計が、その基準系で静止し、同じ基準系での設置場所を持つ。',
        'qn':'試行範囲が完全という前提の下で、非空の全関連試行へ、同じ時計対・基準系・単位と各試行の場所・出来事・光・読みを判定関数へ渡す。',
        'qo':'同じ有効な静止時計は自己と同期するとし、異なる二時計にはqnを既存の一往復条件dbへ接続する。これは明示した試行範囲に相対的な合成である。',
        'qv':'時計範囲が非空で、その全時計が同じ基準系で適切に配置され、時間単位も適切である。無効な選択対象を単に無視しない。',
        'qp':'同じ基準系・単位・文脈の時計範囲について、qoの対称性を述べる内容。',
        'qq':'同じ条件の三時計について、一時計が残り二時計と同期すればその二時計も同期するという内容。',
        'qr':'qpとqqを合わせた、仮定される関係法則の部分的な内容。任意個数での物理的実現可能性全体とは区別する。',
        'qs':'範囲の全時計が一つの同じ参照時計rcと同期する内容。別々の参照時計への置換を許さない。'})
    basis['unresolved'] += generic_composed()[1]['unresolved'] + [
        'u0015の任意個数で矛盾なく実現できるという可能性の全体は未記述で、ここでは後続の二関係法則を仮定として接続した。',
        'u0018の同じ参照時計という条件だけを接続した。出来事の時刻、同時性、局所観測、定義採用の全文はまだ未記述である。',
        '自己同期を同一時計の規約として明示した。異なる時計の全理想試行に対する完全性と、読みの物理的な実現は未確定。',
        '有限の関係モデルによる論理検査と、実数の切断を含む全試行の物理的検証は分ける。著者への仮定の帰属は、その内容の真理や証明済みという主張を含まない。']
    audit_basis(doc,basis)
    return format_graph(doc,'compact')+'\n',basis


def main():
    for compose,filename in ((generic_composed,'data/synchrony-network-basis-v1.json'),
                             (source_composed,'data/einstein-synchrony-network-basis-v1.json')):
        text,basis=compose()
        for name,body in ((basis['document'],text),(filename,json.dumps(basis,ensure_ascii=False,indent=2)+'\n')):
            path=ROOT/name
            if path.exists():
                if path.read_text(encoding='utf-8')!=body: raise ValueError('Stored synchrony network differs: '+name)
            else:
                with path.open('x',encoding='utf-8',newline='\n') as stream: stream.write(body)
    print('Pulse criteria, synchrony relations and scoped assumption composed')


if __name__=='__main__': main()
