"""Bind a qualified private-use policy inside, rather than outside, permission."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT, closure
from scripts.compose_qualitative_influence import STATE, both
from scripts.compose_restriction_questions import supplied
from scripts.compose_qualified_private_influence import BASIS as POLICY_BASIS

PARENT = 'examples/v016/kant-public-enlightenment-route.noema'
PARENT_BASIS = 'data/public-enlightenment-route-basis-v1.json'
FULL = 'examples/v016/kant-private-policy-permission.noema'
CORE = 'examples/v016/private-policy-permission-core.noema'
BASIS = 'data/private-policy-permission-basis-v1.json'
ANNOTATIONS = 'data/private-policy-permission-identifiers-v1.json'
PRIMITIVES = {
    'h235u': ('[a a a i c[h[j[a]] e] j[a] c d] c',
              ['source', 'addressee', 'role', 'description', 'bindings', 'polarity', 'context'],
              '規範の出所が、名宛人にその立場で、閉じた段階2の記述へ同じ順の個体列を適用した内容の指定極性を積極的に許可する。h7lと同じ規範的関係を高い記述段階で扱う。対象を許可時に実行せず、内容の真理・履行・義務・正当性、反対極性の許可を含意しない。'),
    'h235v': ('[a a a d a] c', ['public', 'person', 'role', 'reference', 'case'],
              '同じ公衆・本人・委ねられた職務・基準で検討する私的使用の制限方針案の全範囲。制限の強さ・頻度・啓蒙への結果が条件を満たす案だけに選別しない。同じ背景の下で可能な要求表を索引とし、実際の適用や許可の存在は含意しない。'),
    'h235w': ('[d a] j[d]', ['context', 'case'],
              '同じ文脈の方針案について、要求への適合で選別する前の本人の私的使用の全選択肢の有限列。重複なしでh235xの範囲を尽くすことはr2yqが検査する。同じ本人・職務・関連背景・要求内容を保ち、全時点と介入両側で固定する。'),
    'h235x': ('[d a d] c', ['context', 'case', 'choice'],
              '同じ方針案の本人・職務・関連背景を保って本人の私的使用の選択だけを変えた、要求への適合で選別する前の全選択肢の範囲。要求に適合するものだけや他人の違反を混ぜない。期間中と介入の両側で固定する。'),
    'h235y': ('[d a d] b', ['context', 'case', 'choice'],
              '同じ方針案の私的選択肢の重み。正であり、選択の細分化では合計を保存する。機会の時間重みとは区別し、介入の結果や禁止の有無で替えない。正値はr2yqが検査する。'),
    'h235z': ('[d a d d] b', ['context', 'case', 'branch', 'point'],
              '同じ方針案・候補経過・対象時点で、全選択肢のうち要求に不適合となる選択肢の重み付き割合。自己申告値を正しいと仮定せずr2yqの計算と照合する。'),
    'h236a': ('[a d] h[b] c', ['public', 'reference'],
              '同じ公衆と基準で、私的使用の選択肢の排除率が非常に狭い制限と呼べる程度にあるかの基準。全案・本人・職務・候補で固定し、結果の良否から選ばない。正の制限であることを別に検査する。具体的な閾値を原文へ補わず、数値例は検査例に限る。'),
    'h236b': ('[a d] h[b] c', ['public', 'reference'],
              '同じ公衆と基準で、強い制限が対象時機にしばしば適用されると呼べる頻度の基準。程度の基準と区別し、全案・本人・職務・候補で固定する。正の頻度は別に検査し、原文にない普遍的閾値を補わない。'),
    'h236c': ('[d a d] j[d]', ['context', 'case', 'branch'],
              '同じ方針案と候補経過で、同じh222g期間枠に入る全対象時機の有限列。r2ysがh7rの範囲との一致・無重複を確認する。強い制限が成立した時機だけに縮めない。'),
    'h236d': ('[d a d d] b', ['context', 'case', 'branch', 'point'],
              '同じ方針案・候補経過・対象時機の機会頻度の正の重み。私的選択肢の重みと区別し、強い制限の成否から調整しない。対応経過では同じ機会区分と重みの規約を保つ。'),
    'h236e': ('[d a d] b', ['context', 'case', 'branch'],
              '同じ方針案・候補経過で、強い私的制限が対象時機に成立する重み付き頻度。r2ysが全時点の程度と機会重みから再計算して照合する。許可から現実の頻度を導かない。'),
    'h236f': ('[d a] a', ['context', 'case'],
              '同じ方針案の期間全体の強い制限の頻度を含む方針の成立に対応する介入変数。単一時点の全要求有効を表すh235fとは区別する。r2yvで方針との対応を検査し、なし側にはr2yxの同じ全要求の全期間解除を要求する。'),
    'h236g': ('[a d] b', ['public', 'reference'],
              '同じ公衆・基準で、啓蒙の一過程の広がりr2xcの低下が特に妨げる程度に至らないと読む上限。程度・頻度の基準とは別で全案・本人・職務・対応組に共通、結果から逆算しない。非負を検査し、0や原文にない具体値へ固定しない。'),
    'h236h': ('[a d a a] c', ['public', 'reference', 'person', 'role'],
              '同じ公衆・基準の議論で私的使用への一般的許可を述べる全ての本人・委ねられた職務の組。許可や成功した案がある組だけを選ばず、同じ本人に複数職務を許す。本人が人であり、その職務で理性を使う活動があることは利用側でzzpとともに検査する。'),
    'h236i': ('[a a i d[e] d] c', ['node', 'author', 'content', 'context'],
              '著者が指定箇所・提示文脈に、閉じた段階3の内容記述を主張するという帰属。hzonと同じ非事実的な帰属を高い記述段階で扱い、低い段階へ強制変換しない。引用内容・内側の許可・許可された方針の実現を実行または肯定しない。'),
    'h236j': ('[] a', [],
              '固定原文kant-1784:u0012回答文内[833,980)、私的使用に強い制限がしばしばあり得ることと啓蒙への留保を述べる節の箇所。回答全体h235pの中で公的使用側h235tに続く。談話上の対照の意味自体はこの参照だけでは表さない。'),
}
MEANINGS = {
    'r2yz': '同じ公衆・本人・職務・方針案を、第五段落の提示h232oと固定基準h232vへ束縛し、r2yyの強い制限の頻度・完全解除・同じ啓蒙への許容低下の内容を返す。要求表はh234v〜h235b、規範適用はh234s、モデルと対応はh235d/e/g/hを再利用する。内側規範源h222f、期間h222g、程度・頻度・許容基準を案の結果から替えない。',
    'r2z2': '同じ本人・職務について結果から選別しないh235vの方針案のうち、r2yzの頻度と程度と低下の留保を同時に満たす案があるという内容。存在量化は許可対象の内側に置く。全ての制限案が許されること、一つの有害な案もないこと、現実の案の実施は主張しない。',
    'r2z3': '個体列を公衆・本人・職務の順のちょうど三要素として読み、r2z2を返す閉じた方針内容アダプター。段階2で引用し、空列・短い列・余分な引数を切り捨てない。',
    'r2z4': '著者waを規範の出所として、同じ公衆の方針規範源h222fに、その方針を決める立場h235rで、同じ公衆・本人・職務へr2z3を適用した内容を積極的に許可する。h235uへの段階2記述と正極性を使い、実際の強い制限や許容低下の成立を評価しない。',
    'r2z5': '固定基準h232vの非空の全公衆範囲h222eで、非空の全本人・職務範囲h236hを取り、各本人が人でその職務の私的使用zzpがあり、r2z4の許可が評価文脈で成立するという内容。同じ人の別の職務を一括せず、許可済みの対象だけに範囲を縮めない。',
    'r2z6': '回答文の私的使用節h236jに、同じ著者waと提示h232oでr2z5の許可内容を段階3で帰属し、公的使用の実現節h235tからの文章順序を保つ。帰属から許可の実在・内側の方針の真理や実施を導かない。対照と自己回答の談話接続はまだ別に必要である。',
}
LIMITS = [
    'darfを規範的な積極的許可として、著者を評価側の出所、同じh222fを方針の名宛人、h235rを方針を決める立場と読む。一般的な許可であり、特定の歴史上の統治者の実際の許可や義務としない。',
    '強い制限の頻度と啓蒙への留保を一つの許可対象に含め、適合する方針案の存在を許可の内側で量化する。許可された内容が現実に成立するとは述べず、任意の強い制限が無害または許可済みとも述べない。この作用域は明示した解釈である。',
    'derselbenは同じ本人の理性の使用、Privatgebrauchは後続定義の委ねられた市民的職務における使用zzpとして束縛する。本人が複数職務を持つ場合も各組を区別し、公的使用の単なる否定として定義しない。',
    '全要求の内容・本人・職務・選択範囲は固定する。原文にない数値閾値や実際の頻度・因果モデルを補わず、程度・頻度・許容低下の基準を同じ公衆と参照で固定する。入力範囲の外部的な網羅性と歴史的なモデルの妥当性は有限検査だけでは証明しない。',
    'h235d/e/g/hのモデル・対応欄を同じ提示文脈と方針案へ接続する。要因だけは全期間の方針を表すh236fとし、単一時点の全要求適用を表すh235fへ戻さない。解除は同じ表の全期間不適用とする。',
    '進行尺度・固定期間・選択の重みと頻度の重み・全対応組は先行のr2yyを継承する。許容差の推移性は仮定しない。全記述域の有限評価拒否を弱めず、許可を調べるだけなら引用内容は実行しない。',
    '原文[833,980)の命題内容を構成して帰属する段階であり、aber/ohne doch darumの対照・期待の取り消し、Ich antworteの自己提示、回答全体の原刊照合と通読は残る。新たな文単位・全単位の意味確認文字数は加算しない。',
]


@lru_cache(None)
def parent():
    return load_catalog(ROOT, PARENT_BASIS)


@lru_cache(None)
def policy():
    return load_catalog(ROOT, POLICY_BASIS)


def bound_args():
    args = ('k h222f[v public k h232v[]] v person v role k h232v[] ' +
            supplied() + ' p h234s k h235w[v context v case] '
            'i[choice d][k h235x[v context v case v choice]] '
            'i[choice d][k h235y[v context v case v choice]] '
            'k h222g[v public k h232v[]] '
            'i[branch d point d][k h235z[v context v case v branch v point]] '
            'k h236a[v public k h232v[]] '
            'i[branch d][k h236c[v context v case v branch]] '
            'i[branch d point d][k h236d[v context v case v branch v point]] '
            'i[branch d][k h236e[v context v case v branch]] k h236b[v public k h232v[]] '
            'k h235d[v context v case] '
            'i[variable a state ' + STATE + '][k h235e[v context v case v variable v state]] '
            'k h236f[v context v case] '
            'i[state ' + STATE + '][k h235g[v context v case v state]] '
            'i[on ' + STATE + ' off ' + STATE + '][k h235h[v context v case v on v off]] '
            'v public k h236g[v public k h232v[]]')
    return args.replace('v context', 'k h232o[]')


def definitions():
    text = 'd r2yz[public a person a role a case a] e[k r2yy[' + bound_args() + ']].\n'
    text += '''d r2z2[public a person a role a] e[b evaluation[
 g case a[w[k h235v[v public v person v role k h232v[] v case]][
 t[k r2yz[v public v person v role v case]][v evaluation]]]
]].
d r2z3[bindings j[a]] e[b evaluation[
 g public a[g person a[g role a[
 w[k h7g[v bindings]][w[a[v bindings][n p a b][v public]][
 w[a[v bindings][n p b b][v person]][w[a[v bindings][n p c b][v role]][
 t[k r2z2[v public v person v role]][v evaluation]]]]]
 ]]]
]].
d r2z4[public a person a role a evaluation d] c[
 k h235u[k wa[] k h222f[v public k h232v[]]
 k h235r[k h222f[v public k h232v[]] k h232v[]]
 r c[p r2z3] l[a][v public v person v role] e[v public][v public] v evaluation]
].
'''
    scope = 'k h236h[v public k h232v[] v person v role]'
    text += 'd r2z5[] e[b evaluation[' + both(
        'g public a[k h222e[v public k h232v[]]]',
        'f public a[y[k h222e[v public k h232v[]]][' + both(
            'g person a[g role a[' + scope + ']]',
            'f person a[f role a[y[' + scope + '][' + both(
                'k aa[v person]', 'g activity a[k zzp[v person v activity v role k h232v[]]]',
                'k r2z4[v public v person v role v evaluation]') + ']]]') + ']]') + ']].\n'
    text += '''d r2z6[] c[w[k h236i[k h236j[] k wa[] r d[k r2z5[]] k h232o[]]][
 k ue[k h235t[] k h236j[] k h232o[]]]].
'''
    return text


def build():
    old, prior = parent(), policy()
    doc = deepcopy(old.document)
    statements, doc['statements'] = doc['statements'], []
    imported = {}
    for d in prior.document['declarations']:
        n = d['name']
        if n in old.entries:
            assert old.entries[n]['declaration'] == d
            assert old.entries[n]['meaning_ja'] == prior.entries[n]['meaning_ja']
        else:
            assert d['kind'] == 'definition'
            doc['declarations'].append(deepcopy(d))
            imported[n] = prior.entries[n]['meaning_ja']
    assert not (set(PRIMITIVES) | set(MEANINGS)) & (set(old.entries) | set(imported))
    doc = parse(format_graph(doc, 'compact') + ''.join(
        'r ' + n + row[0] + '.' for n, row in PRIMITIVES.items()) + definitions())
    added = doc['declarations'][len(old.document['declarations']):]
    new = dict(kind='assert', body=dict(kind='call', symbol='r2z6', arguments=[]))
    doc['statements'] = statements + [new]
    core = deepcopy(doc)
    core.update(declarations=closure(doc, list(MEANINGS)), statements=[new])
    decls = {d['name']: d for d in added}
    basis = dict(status='private_policy_permission_clause_partial_answer', document=FULL,
                 parent=PARENT, inherited_meaning_basis=PARENT_BASIS, definitions=imported | MEANINGS,
                 primitives={n: dict(parameters=decls[n]['parameters'], result=decls[n]['result'],
                                     arguments=row[1], meaning_ja=row[2]) for n, row in PRIMITIVES.items()},
                 new_signatures={d['name']: {k: d[k] for k in ('parameters', 'result')} for d in added},
                 imported_policy=POLICY_BASIS, import_source_sha256=dict(prior.source_sha256),
                 limitations=LIMITS)
    body = format_graph(doc, 'compact') + '\n'
    annotations = json.loads((ROOT / 'data/public-enlightenment-route-identifiers-v1.json').read_text(encoding='utf-8'))
    annotations.update(document=FULL, document_sha256=digest(body.encode('utf-8')))
    encoded = lambda value: json.dumps(value, ensure_ascii=False, indent=2) + '\n'
    return {FULL: body, CORE: format_graph(core, 'compact') + '\n',
            BASIS: encoded(basis), ANNOTATIONS: encoded(annotations)}
