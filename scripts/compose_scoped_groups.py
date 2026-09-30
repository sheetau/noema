"""Keep included classes, collective roles and attributed labels distinct."""
from copy import deepcopy
import json

from noema.grammar import format_graph, parse
from noema.meaning_basis import audit_basis
from scripts.compose_limits import ROOT


def definitions():
    return '''
d ro[population h[a] c included h[a] c selected h[a] c] c[
 w[g person a[c[v included][v person]]][f person a[y[c[v included][v person]][
  w[c[v population][v person]][c[v selected][v person]]
 ]]]
].
d rp[actors h[a] c targets h[a] c relation h[a a] c] c[
 w[g actor a[c[v actors][v actor]]][w[g target a[c[v targets][v target]]][
  w[f actor a[y[c[v actors][v actor]][g target a[w[c[v targets][v target]][c[v relation][v actor v target]]]]]][
   f target a[y[c[v targets][v target]][g actor a[w[c[v actors][v actor]][c[v relation][v actor v target]]]]]
  ]
 ]]
].
d rq[node a author a referent i[h[a] e] label i[h[a] e] context d presents h[a a i[h[a] e] i[h[a] e] d] c] c[
 w[u[e[v referent][v label]]][c[v presents][v node v author v referent v label v context]]
].
d rr[actors h[a] c context d occurs h[a d] c participates h[a a d] c] c[
 w[g actor a[c[v actors][v actor]]][g act a[w[c[v occurs][v act v context]][
  f actor a[y[c[v actors][v actor]][c[v participates][v actor v act v context]]]
 ]]]
].
'''


def generic_composed():
    doc = parse('n:\n' + definitions())
    basis = {'version': 'scoped-groups-basis-v1', 'document': 'examples/v014/scoped-groups.noema',
        'primitives': [], 'definitions': {
            'ro': '指定した含有集団が非空で、その全員が母集団に属し、同じ選択条件を満たす。含有集団の一部だけの該当や、母集団外の対象を許さない。',
            'rp': '行為者群と対象群が共に非空で、各行為者には少なくとも一つの対象があり、各対象には少なくとも一人の行為者が指定関係で結び付く。全行為者と全対象の全組合せは要求しない。',
            'rq': '異なる二つの性質記述について、著者が対象を一方の基準で指し、他方をその呼称の描写として使う。どちらの内容も実行評価しない。字義通りか、慣用的か、皮肉かをこの条件だけでは決めない。',
            'rr': '行為者群が非空で、実際に生じる一つの行為に、その全員が同じ文脈で参加する。各人の別々で無関係な行為を、一つの共同作用として混ぜない。'},
        'unresolved': [
            'roの非空性は明示した存在前提であり、空集合を許す一般の包含関係とは区別する。集団の同定基準は引数で与える。',
            'rpは関係による対象範囲の被覆である。全員が全対象へ作用すること、各対象の担当の一意性、共同意図や法的責任を含まない。',
            'rrの一つの行為は複数の部分行為を持ち得る。参加と出来事の発生は引数の意味規約であり、各人が単独で結果に十分な原因になることを含まない。',
            'rqの呼称の使用を与える関係は意味規約である。皮肉の強さや話者の態度、一般の命名理論を確定しない。']}
    audit_basis(doc, basis)
    return format_graph(doc, 'compact') + '\n', basis


def source_composed():
    doc = parse((ROOT / 'examples/v014/kant-described-appraisals.noema').read_text(encoding='utf-8'))
    statements, doc['statements'] = doc['statements'], []
    text = format_graph(doc, 'compact') + definitions() + '''
r da[a d] c.r db[] a.r dc[a a d] c.r dd[d d] c.r de[a a d] c.
r df[a a d] c.r dg[a d] c.r dq[] a.r dt[a d] c.r du[a a i[h[a] e] i[h[a] e] d] c.r dv[a a a d] c.
d di[actor a target a] e[b context[
 w[k aa[v actor]][w[k aa[v target]][w[u[e[v actor][v target]]][w[k dc[v actor v target v context]][
  g point d[w[u[e[v point][v context]]][w[k dd[v point v context]][
   g act a[w[k de[v actor v act v point]][k dv[v act v actor v target v point]]]
  ]]
 ]]]]]
]].
d dj[person a context d] c[w[k hg[k mp[k mv[]] v person]][t[k uz[v person]][v context]]].
d dk[group a] e[b context[
 w[k hi[k mp[v group] p aa]][k rp[i[actor a][k hg[k mp[v group] v actor]]
  i[target a][k dj[v target v context]] i[actor a target a][t[k di[v actor v target]][v context]]]
 ]
]].
d dl[group a] e[b context[w[k hi[k mp[v group] p aa]][
 k rr[i[actor a][k hg[k mp[v group] v actor]] v context p dg p df]
]]].
d dn[group a] e[b context[w[t[k u5[k mp[v group]]][v context]][
 k ro[i[person a][k hg[k mp[v group] v person]] i[person a][k da[v person v context]]
  i[person a][t[k uz[v person]][v context]]]
]]].
d do[group a] e[b context[
 w[t[k dk[v group]][v context]][w[t[k dl[v group]][v context]][
  w[t[k dn[k mv[]]][v context]][k ea[v group r[p dl] k mv[] r[p dn] v context]]
 ]]
]].
d dp[] e[b context[t[k do[k db[]]][v context]]].
d dr[person a] e[b context[w[k aa[v person]][k da[v person v context]]]].
d ds[person a] e[b context[w[k aa[v person]][k dt[v person v context]]]].
'''
    doc = parse(text)
    doc['statements'] = statements
    doc = parse(format_graph(doc, 'compact') + '''
s[w[k uc[k dq[] k wa[] r[k dp[]] k wh[]]][k ue[k t4[] k dq[] k wh[]]]].
s[k rq[k dq[] k wa[] r[p dr] r[p ds] k wh[] p du]].
''')
    basis = deepcopy(json.loads((ROOT / 'data/kant-described-appraisals-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='kant-scoped-groups-basis-v1', document='examples/v014/kant-scoped-groups.noema')
    basis['definitions'].update(generic_composed()[1]['definitions'])
    basis['unresolved'] = [note for note in basis['unresolved'] if not note.startswith('女性全体を含むという挿入句')]
    decls = {d['name']: d for d in doc['declarations']}
    for name, args, meaning in (
        ('da', ['person', 'context'], 'この歴史的文脈で女性の集団として数える人の分類。美しいという評価や危険だという判断は条件に含めない。性別分類そのものの生物学的・社会的な構成説明は未完であり、語義を説明済みと数えない。'),
        ('db', [], 'ここで後見人と指示される集団。構成員は既存のmpで与え、dkによって指図する立場とその引受けを記述する。'),
        ('dc', ['actor', 'target', 'context'], 'この対象について、行為者が総括的な監督・指図の立場を現在持つ。正当性や制度上の資格を意味しない。監督階層と権限の一般的な説明は未完。'),
        ('dd', ['earlier', 'later'], '第一の状況が第二より時間的に先行する。具体的な時刻、間隔、直前であることは補わない。'),
        ('de', ['actor', 'act', 'point'], 'この人がこの時点でこの行為を行った。自ら発意したことは要求しないため、既存のoaとは区別する。'),
        ('dv', ['act', 'actor', 'target', 'point'], 'この行為により、この人が同じ対象を監督する立場を実際に引き受ける。単にその立場を称する場合も含む既存obより強い条件であり、資格の正当性や行為の自発的な発意は別である。'),
        ('df', ['actor', 'act', 'context'], 'この人が、この文脈で当該行為に能動的な当事者として参加する。他人の行為が同時に起きただけでは含めない。'),
        ('dg', ['act', 'context'], 'この文脈で、その行為が実際に生じる。行為の構成員や結果の因果的な説明は別条件である。'),
        ('dq', [], '人々が自立への一歩を危険だと考えることを、後見人の働きかけによって説明する文の箇所。'),
        ('dt', ['person', 'context'], 'その人が、この描写の文脈で美的に好ましいと表現される性質。女性集団の分類とは分離し、美の一般理論は未定義とする。'),
        ('du', ['node', 'author', 'referent_description', 'label_description', 'context'], '著者がこの箇所で、前者の性質で指す人々に後者の性質の描写を呼称として用いる。対象全員が実際に後者を満たすという認定や、著者が字義通り信じることは含めない。')):
        declaration = decls[name]
        basis['primitives'].append({'symbol': name, 'parameters': declaration['parameters'],
            'result': declaration['result'], 'arguments': args, 'meaning_ja': meaning})
    basis['definitions'].update({
        'di': '人である行為者が別の人を現在総括的に監督し、それより前に同じ対象への立場を実際に引き受ける行為を行っている。現在の立場だけ、単なる自称、他者の行為、未来の引受けでは足りない。',
        'dj': '先行文と同じ母集団mvのうち、負担と危険判断の性質uzを満たす人。この草案で代名詞の対象として採用する範囲。',
        'dk': '重複のない人々からなる後見人群が、djの人々をdiで覆い、各後見人も少なくとも一人を担当する。各人が対象全員を担当するとはしない。',
        'dl': '同じ後見人群の全構成員が、この文脈で生じる一つの行為へ参加している。各人が別個に十分な原因になることは含めない。',
        'dn': '既存u5の大きな割合の条件に、女性集団daの非空性と全員の包含・uzへの該当を加える。女性は実際に美しい人だけ、という選別をしない。',
        'do': '後見人群の立場dk・同じ群の活動dl・同じ母集団mvについての結果dnが成立し、その活動の記述dlが結果の記述dnの原因説明へ採用される。実在の因果機構の証明は含まない。',
        'dp': '指示された後見人群dbについてdoが成立する内容。主張としての記述を著者に帰属し、Noemaの処理系がその真理を認定するのではない。',
        'dr': '文脈で女性集団に分類される人。集団の範囲を、呼称の美的描写dsとは分ける。',
        'ds': '人が美的に好ましいという描写内容。本文ではこの内容を現実の真理として実行せず、呼称としての使用をduへ渡す。'})
    basis['unresolved'] += generic_composed()[1]['unresolved'] + [
        '女性全体の包含と後見人の集団的な作用を接続したが、性別分類、美的評価、監督権限の語義全体は未説明。基本記号へ名前を付けたことを概念の完成としない。',
        '代名詞の対象をuzに該当する母集団の人々とし、後見人群がその範囲を分担して覆う読みを採用した。全人類への監督、各後見人による全員の監督、例外を許す一般的な傾向とは区別する。',
        'gütigstの評価と皮肉、schon・auchの焦点、後続の家畜と歩行器の比喩は未記述。schöne Geschlechtの対象範囲と呼称を分けたが、呼称の効果を一意には確定しない。',
        'eaは原因説明への採用であり、後見人の活動から判断が実際に生じる介入機構は後続文と接続する必要がある。']
    audit_basis(doc, basis)
    return format_graph(doc, 'compact') + '\n', basis


def main():
    for compose, filename in ((generic_composed, 'data/scoped-groups-basis-v1.json'),
                              (source_composed, 'data/kant-scoped-groups-basis-v1.json')):
        text, basis = compose()
        for name, body in ((basis['document'], text), (filename, json.dumps(basis, ensure_ascii=False, indent=2) + '\n')):
            path = ROOT / name
            if path.exists():
                if path.read_text(encoding='utf-8') != body:
                    raise ValueError('Stored scoped group differs: ' + name)
            else:
                with path.open('x', encoding='utf-8', newline='\n') as stream:
                    stream.write(body)
    print('Included classes and collective guardians composed with attributed labels')


if __name__ == '__main__':
    main()
