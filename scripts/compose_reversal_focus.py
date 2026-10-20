"""Attach noteworthy presentation and emphatic bearers to the same claim."""
from copy import deepcopy
from functools import lru_cache
import json

from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT, closure

PARENT = 'examples/v016/kant-reversal-yoke.noema'
PARENT_BASIS = 'data/reversal-yoke-basis-v1.json'
FULL = 'examples/v016/kant-reversal-focus.noema'
CORE = 'examples/v016/reversal-focus-core.noema'
BASIS = 'data/reversal-focus-basis-v1.json'
ANNOTATIONS = 'data/reversal-focus-identifiers-v1.json'
PRIMITIVES = {
    'h224r': ('[a a i d[e] i d[e] j[a] d] c',
              ['node', 'author', 'claim', 'focus', 'discussion', 'context'],
              '同じ主張と提示文脈の中で、指定された先行の議論に関して、焦点の内容を通常の予期から外れる特異な点として特に注意を向けて提示するという帰属。先行議論の文章箇所の列を明示する。客観的な発生頻度・確率、主張の確信度や必然性の増加、引用内容の真理を含意しない。'),
    'h224s': ('[a a i d[e] i d[h[j[a]] e] i d[h[j[a]] e] d] c',
              ['node', 'author', 'claim', 'scope', 'feature', 'context'],
              '同じ主張の該当する述定を提示するとき、範囲の順序付き対象列の最終位置の担い手自身を、焦点の関係の担い手として取り立てる帰属。範囲と焦点は同じ列と内容評価点を共有する。単に関係者や代理が担うという提示と区別するが、他者の関与を全て排除せず、単独性を要求しない。焦点の述定が元の主張の条件・否定・量化のどこにあるかを保ち、帰属の評価時にその真理を条件の外で断言しない。'),
    'h224t': ('[] a', [], '固定原文kant-1784:u0011第三文の[449,469)、Besonders ist hiebeiの提示箇所。'),
    'h224u': ('[] a', [], '固定原文kant-1784:u0011第三文の[560,566)、強制する公衆自身を取り立てるselbstの箇所。'),
    'h224v': ('[] a', [], '固定原文kant-1784:u0011第三文の[637,643)、啓蒙不能である扇動者自身を取り立てるselbstの箇所。'),
}
MEANINGS = {
    'r2nr': '同じ公衆・事例について、既存r2mrの扇動条件と公衆による先行後見人全員の保持という含意部分だけを取り出す。r2neと同じ参照供給とr2mu/r2mt/r2naを使う。先行背景や時間条件は元の主張r2nfに保ち、この部分式だけで主張全体を代用しない。',
    'r2ns': '順序付き列[公衆,事例,担い手]と評価点について、同じ公衆範囲・事例範囲を要求し、担い手を公衆そのものへ固定する焦点範囲。関係の成功を範囲の条件にしない。',
    'r2nt': '同じ三位置の担い手が公衆そのものであることと、その公衆のr2nrを結ぶ焦点族。公衆自身による強制を、元の扇動条件付きのまま取り立てる。後件の強制を無条件化しない。',
    'r2nu': '同じ三位置と評価点の公衆・事例範囲において、担い手を同じ事例の扇動者列の成員へ固定する焦点範囲。実際に不能である者だけへ範囲を縮めない。',
    'r2nv': '同じ三位置の担い手が同じ扇動者列に属し、その同じ事例の扇動時点に既存r2mtの取得不能を満たす内容。元のr2mqの前件内で、各扇動者に要求される性質の焦点として引用する。',
    'r2nw': '同じ前半の主張r2nfを、先頭二文hzp4/hzp5の議論に関して特異で注目すべき点として提示する帰属。hiebeiの議論上の参照を明示する。',
    'r2nx': '同じ主張r2nf・著者・提示文脈において、第一のselbstを公衆自身の条件付き強制、第二を扇動者自身の前件内の取得不能へ、それぞれの範囲と焦点族で結ぶ。',
    'r2ny': '既存の関係内容・頚木の描写・種類の照応r2nqに、特異性の取り立てr2nwと二つの自己の取り立てr2nxを統合する。第三文後半は含めない。',
}
LIMITS = [
    'Besonders ist hiebeiは、前二文の公衆の自己啓蒙についての議論に関して、作用の反転を特異で注目すべき点として提示する読み。単なる程度の増加、数値的な稀少性、論理的な矛盾という読みは加えない。',
    '第一のselbstは、以前は作用を受けた公衆自身が後に強制するという担い手の取り立てと読む。「強制さえする」という尺度の添加の読みは採らない。共同的な行為を既存r2mlで表し、公衆の全成員が単独で同じ行為をするとはしない。',
    '第二のselbstは扇動する後見人本人たちの不能を取り立てる。不能は元の条件の前件内のr2mqにあり、全ての後見人や前文の自己思考者へ拡張しない。範囲は扇動者列の全成員で、不能の成否から選ばない。',
    '三位置の焦点族は、公衆・事例・担い手と内容評価点を共有する。第一の焦点は元の含意の投影、第二はその前件に出現する同じ不能述定である。帰属は閉じた段階3の引用であり、世界の真理を実行評価しない。',
    '現代辞書は語義の区別を確認する補助として用いる。歴史的な構文であるBesonders ist hiebeiの採用読解を辞書だけで唯一に確定したとはしない。原文の並びと前後文から採用した解釈を記録する。',
    '先頭59文と既存13区間・先頭二文382非空白文字を保持する。第三文後半の偏見の植え付け・害・報復と文全体の統合・通読は未完であり、第三文の確認済み文字数は増やさない。',
]


@lru_cache(None)
def parent():
    return load_catalog(ROOT, PARENT_BASIS)


def triple(name, body):
    return ('d ' + name + '[roles j[a]] e[b reference['
            'g public a[g case a[g bearer a['
            'w[e[v roles][l[a][v public v case v bearer]]][' + body + ']'
            ']]]]].')


def definitions():
    common = 'w[k h222e[v public v reference]][k h223w[v public v reference v case]]'
    member = 'k hg[k h223z[v case] v bearer]'
    return '''
d r2nr[public a case a] c[
 y[k r2mq[v public k h223z[v case] k h224c[v case] k h224e[v case] k h224d[v case]
 p r2mu p r2mt k r2na[k h224f[v case] k h224l[v case]]]][
 f person a[y[k hg[k h223y[v case] v person]][
 k r2mn[v public k h224e[v case] v person k h224f[v case]
 k h224g[v case] k h224h[v case] k h224i[v case] k h224j[v case] k h224k[v case]]
 ]]
 ]
].
''' + triple('r2ns', 'w[' + common + '][e[v bearer][v public]]') + triple(
        'r2nt', 'w[e[v bearer][v public]][k r2nr[v bearer v case]]') + triple(
        'r2nu', 'w[' + common + '][' + member + ']') + triple(
        'r2nv', 'w[' + member + '][k r2mt[v bearer k h224d[v case]]]') + '''
d r2nw[] c[k h224r[k h224t[] k wa[] r d[k r2nf[]] r d[k r2nf[]]
 l[a][k hzp4[] k hzp5[]] k hzp3[]]].
d r2nx[] c[
 w[k h224s[k h224u[] k wa[] r d[k r2nf[]] r d[p r2ns] r d[p r2nt] k hzp3[]]][
 k h224s[k h224v[] k wa[] r d[k r2nf[]] r d[p r2nu] r d[p r2nv] k hzp3[]]]
].
d r2ny[] c[w[k r2nq[]][w[k r2nw[]][k r2nx[]]]].
'''


def build():
    old = parent()
    doc = deepcopy(old.document)
    statements, doc['statements'] = doc['statements'], []
    assert not (set(PRIMITIVES) | set(MEANINGS)) & set(old.entries)
    text = ''.join('r ' + n + spec[0] + '.' for n, spec in PRIMITIVES.items())
    doc = parse(format_graph(doc, 'compact') + text + definitions())
    added = doc['declarations'][len(old.document['declarations']):]
    assert statements[-1] == dict(kind='assert', body=dict(kind='call', symbol='r2nq', arguments=[]))
    statement = dict(kind='assert', body=dict(kind='call', symbol='r2ny', arguments=[]))
    doc['statements'] = statements[:-1] + [statement]
    core = deepcopy(doc)
    core.update(declarations=closure(doc, ['r2ny']), statements=[statement])
    declarations = {d['name']: d for d in added}
    basis = dict(status='reversal_presentation_focus_partial', document=FULL, parent=PARENT,
                 inherited_meaning_basis=PARENT_BASIS, definitions=MEANINGS,
                 primitives={n: dict(parameters=declarations[n]['parameters'], result=declarations[n]['result'],
                                     arguments=spec[1], meaning_ja=spec[2])
                             for n, spec in PRIMITIVES.items()},
                 new_signatures={d['name']: {k: d[k] for k in ('parameters', 'result')} for d in added},
                 limitations=LIMITS)
    body = format_graph(doc, 'compact') + '\n'
    annotations = json.loads((ROOT / 'data/reversal-yoke-identifiers-v1.json').read_text(encoding='utf-8'))
    annotations.update(document=FULL, document_sha256=digest(body.encode('utf-8')))
    encoded = lambda value: json.dumps(value, ensure_ascii=False, indent=2) + '\n'
    return {FULL: body, CORE: format_graph(core, 'compact') + '\n',
            BASIS: encoded(basis), ANNOTATIONS: encoded(annotations)}
