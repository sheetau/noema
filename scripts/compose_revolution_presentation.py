"""Keep possibility, denial and replacement forecast distinct in presentation."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT, closure
from scripts.compose_public_first_sentence import PAIR_SIGNATURE, PAIR_ARGUMENTS, replace_calls

PARENT = 'examples/v016/kant-leading-band.noema'
PARENT_BASIS = 'data/leading-band-basis-v1.json'
FULL = 'examples/v016/kant-revolution-presentation.noema'
CORE = 'examples/v016/revolution-presentation-core.noema'
BASIS = 'data/revolution-presentation-basis-v1.json'
ANNOTATIONS = 'data/revolution-presentation-identifiers-v1.json'
PRIMITIVES = {
    'h227t': ('[a a i d[e] i d[h[a d] c] i d[h[a d] e] i d[h[a d] c] d] c',
              ['node', 'presenter', 'claim', 'subject_scope', 'outcome_family', 'qualification_family', 'context'],
              '提示者が同じ箇所・主張・文脈で、対象範囲の同じ個体と基準に関する結果族の成立を確定していないものとして提示し、同じ限定族に明示された範囲で成立を認める。結果の成立を限定以上に確言せず、限定自体を疑わしいと述べる関係ではない。内心の信念、客観的な確率、結果の否定や失敗例の実在を含意しない。'),
    'h227u': (PAIR_SIGNATURE, PAIR_ARGUMENTS,
              '提示者が同じ箇所・文脈・観点で、第一の内容をその限定を保ったまま一旦認めつつ、第二の内容を退ける理由にはならないものとして譲歩的に扱う。二つの内容の向きを保存する。第一の無条件の真理、両内容の矛盾、通常予想の全候補での逆転は要求しない。'),
    'h227v': (PAIR_SIGNATURE, PAIR_ARGUMENTS,
              '提示者が同じ箇所・文脈・共通観点で、第一の否定的内容によって退けた見通しに代えて、第二の肯定的内容を提示する。第一の否定を撤回せず、第二の条件・様相を保つ訂正的な提示関係。第二が第一の論理的否定であること、世界での真理、唯一の残余選択肢であることは含意しない。'),
    'h227w': ('[] a', [], '固定原文kant-1784:u0011の第五文全体[907,1216)の文章箇所。'),
    'h227x': ('[] a', [], '同第五文[907,1042)の政治的離脱について留保付きで認める側の箇所。末尾の共有述語zu Stande kommenはh227hの範囲で補って読む。'),
    'h227y': ('[] a', [], '同第五文[1042,1101)のaberからセミコロンまで、思考様式の改革について否定する側の箇所。'),
}
MEANINGS = {
    'r2rz': 'r2qyから政治的離脱の可能性側だけを取り出す。閉じた公衆・基準名の一致、全候補の時間枠を保持し、同じ革命と候補による同じ公衆への結果を存在量化する。',
    'r2sa': 'r2qyから改革の経路の不在だけを取り出す。閉じた参照と時間枠は同じで、政治的離脱の成功に制限せず全革命・候補について改革結果の存在を否定する。',
    'r2sb': '同じ非空の公衆範囲と公衆分類・全成員の確認を保ち、r2rzを全公衆へ適用した可能性内容。r2scとの連言はr2qzの二結果を保持する。',
    'r2sc': '同じ非空の公衆範囲と公衆分類・全成員の確認を保ち、r2saを全公衆へ適用した否定内容。新しい偏見の予測までこの否定の範囲に入れない。',
    'r2sd': '同じ公衆・基準に固定した候補内で、ある革命が政治的離脱の結果を実際に公衆へ広げるという結果族。r2rzの存在量化が調べる同じr2qx/r2qrで構成する。',
    'r2se': '同じ公衆範囲と基準におけるr2qxの革命行為を、候補内の性質として取り出す。二結果と予測を、革命の帰結についての議論という共通観点へ結ぶ。',
    'r2sf': '前半の同じ主張r2qzで、同じ公衆範囲h222eの政治的離脱r2sdを、r2rzの可能性という限定の下で未確定の結果として提示する。vielleichtの留保を改革の否定や後半全体へ広げない。',
    'r2sg': '前半の政治的離脱の可能性r2sbと改革経路の不在r2scを、それぞれの箇所と革命の帰結という共通観点へ結ぶ。既存h222qの対比とh227uの譲歩を別々に要求し、wohlがvielleichtの限定を消さないよう保持する。',
    'r2sh': '改革経路の不在r2scを撤回せず、同じ革命の議論で後半の予測r2rnを代わりに示すh227vの訂正的提示。政治的離脱の可能性を否定対象に取り替えない。',
    'r2si': '前半の内容帰属r2ra、後半の予測・語調・比喩r2ry、留保r2sf、譲歩と対比r2sg、訂正的提示r2shを統合し、二つの前半箇所から後半へ本文順を保持する。',
}
LIMITS = [
    'vielleichtは政治的離脱という結果の成立を未確定にする提示、wohlはその限定付きの可能性を認めて次の否定へ進む譲歩として読む。wohlを高確率や成功保証に変えず、vielleichtを改革の否定や後半の予測へかけない。',
    'aberは革命による帰結についての二内容の対比として読む。sondernは、改革の見通しを退けた上で、新しい偏見による判断の方向付けを代わりに提示するものとする。政治的離脱そのものを否定・撤回しない。',
    'niemalsは、固定した候補範囲のどの革命も、公衆の改革と呼ぶ広がりを生まないという既存の否定を維持する。一人の判断改善まで禁止する、全時代・全世界に無制限に量化する、革命以外の改革経路を否定する読みへ強めない。',
    '前半の可能性・否定を構文から抽出し、名前照合・全候補の時間枠・同じ公衆範囲を保つ。h227tの対象は候補内の結果族であり、その可能性があるという主張自体を疑わしいとする二重の様相にはしない。',
    '留保・譲歩・訂正的提示は、内容を引数とする一般的な提示関係である。原文一語や一文の真偽を返す基本語ではなく、世界の真理や提示者の内心の完全な心理機構を定義したものでもない。',
    '既存の全定義と先頭62文を保持し、最後の未レビュー文62をr2siへ統合する。文全体の意味判断は、局所検査の成功だけから出さず、別の通読記録に残す。',
]


@lru_cache(None)
def parent():
    return load_catalog(ROOT, PARENT_BASIS)


def extracted():
    old = parent()
    result = []
    for name, branch in [('r2rz', 0), ('r2sa', 1)]:
        d = deepcopy(old.entries['r2qy']['declaration'])
        d['name'] = name
        cursor = d['body']
        for _ in range(2):
            cursor = cursor['arguments'][1]
        pair = cursor['arguments'][1]
        assert pair['kind'] == 'and'
        assert pair['arguments'][0]['kind'] == 'exists' and pair['arguments'][1]['kind'] == 'not'
        cursor['arguments'][1] = pair['arguments'][branch]
        result.append(d)
    for name, selected in [('r2sb', 'r2rz'), ('r2sc', 'r2sa')]:
        d = replace_calls(deepcopy(old.entries['r2qz']['declaration']), {'r2qy': selected})
        d['name'] = name
        result.append(d)
    return result


def definitions():
    return '''
d r2sd[public a reference d] e[b candidate[
 g act a[w[k r2qx[v public v reference v act v candidate]][
 k r2qr[v public v reference v act v candidate o a[r[p r2qv]][k h227c[v reference] k h227b[v public]]]
 ]]
]].
d r2se[act a] e[b candidate[
 g public a[g reference d[w[k h222e[v public v reference]][k r2qx[v public v reference v act v candidate]]]]
]].
d r2sf[] c[k h227t[k h227x[] k wa[] r d[k r2qz[]]
 r d[p h222e] r d[p r2sd] r d[p r2rz] k hzp3[]]].
d r2sg[] c[
 w[k h222q[k h227h[] k wa[] k h227x[] r b[k r2sb[]] k h227y[] r b[k r2sc[]] r[p r2se] k hzp3[]]][
 k h227u[k h227h[] k wa[] k h227x[] r b[k r2sb[]] k h227y[] r b[k r2sc[]] r[p r2se] k hzp3[]]]
].
d r2sh[] c[k h227v[k h227w[] k wa[] k h227y[] r b[k r2sc[]]
 k h227n[] r b[k r2rn[]] r[p r2se] k hzp3[]]].
d r2si[] c[
 w[k r2ra[]][w[k r2ry[]][w[k r2sf[]][w[k r2sg[]][w[k r2sh[]][
 w[u[e[k h227x[]][k h227y[]]]][w[u[e[k h227y[]][k h227n[]]]][
 w[k ue[k h227x[] k h227y[] k hzp3[]]][k ue[k h227y[] k h227n[] k hzp3[]]]
 ]]]]]]]
].
'''


def build():
    old = parent()
    doc = deepcopy(old.document)
    statements, doc['statements'] = doc['statements'], []
    assert not (set(PRIMITIVES) | set(MEANINGS)) & set(old.entries)
    doc['declarations'].extend(extracted())
    doc = parse(format_graph(doc, 'compact') +
                ''.join('r ' + n + s[0] + '.' for n, s in PRIMITIVES.items()) + definitions())
    added = doc['declarations'][len(old.document['declarations']):]
    assert statements[-1] == dict(kind='assert', body=dict(kind='call', symbol='r2ry', arguments=[]))
    statement = dict(kind='assert', body=dict(kind='call', symbol='r2si', arguments=[]))
    doc['statements'] = statements[:-1] + [statement]
    core = deepcopy(doc)
    core.update(declarations=closure(doc, ['r2si']), statements=[statement])
    decls = {d['name']: d for d in added}
    basis = dict(status='revolution_presentation_integrated', document=FULL, parent=PARENT,
                 inherited_meaning_basis=PARENT_BASIS, definitions=MEANINGS,
                 primitives={n: dict(parameters=decls[n]['parameters'], result=decls[n]['result'],
                                     arguments=s[1], meaning_ja=s[2]) for n, s in PRIMITIVES.items()},
                 new_signatures={d['name']: {k: d[k] for k in ('parameters', 'result')} for d in added},
                 limitations=LIMITS)
    body = format_graph(doc, 'compact') + '\n'
    annotations = json.loads((ROOT / 'data/leading-band-identifiers-v1.json').read_text(encoding='utf-8'))
    annotations.update(document=FULL, document_sha256=digest(body.encode('utf-8')))
    encoded = lambda value: json.dumps(value, ensure_ascii=False, indent=2) + '\n'
    return {FULL: body, CORE: format_graph(core, 'compact') + '\n',
            BASIS: encoded(basis), ANNOTATIONS: encoded(annotations)}
