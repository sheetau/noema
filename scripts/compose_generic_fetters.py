"""Join kindwise generic force, ordered continuations and relational depiction."""
from copy import deepcopy
from functools import lru_cache
import json

from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT, closure

PARENT = 'examples/v016/kant-polymorphic-forms.noema'
PARENT_BASIS = 'data/polymorphic-forms-basis-v1.json'
FULL = 'examples/v016/kant-generic-fetters.noema'
CORE = 'examples/v016/generic-fetters-core.noema'
LIBRARY = 'examples/v016/ordered-conditional-profiles.noema'
BASIS = 'data/generic-fetters-basis-v1.json'
ANNOTATIONS = 'data/generic-fetters-identifiers-v1.json'
KIND_BASIS = 'data/conjoined-kinds-basis-v1.json'
APPOSITION = 'examples/v016/kant-property-apposition.noema'
APPOSITION_BASIS = 'data/property-apposition-basis-v1.json'
PRIMITIVES = {
    'hzzzb': ('d a', 'c', ['scope', 'case'], '同じ第三文の提示文脈で、規定または定型表現を用いる一般的作用を比較する対象・本人・基準の事例。仮定の事例を含められ、作用の成功した事例だけを選ばない。'),
    'hzzzc': ('d a', 'a', ['scope', 'case'], '同じ提示文脈と事例で使う対象。分類・作用・描写の同じ位置に保持し、結果に合わせて別の対象へ替えない。'),
    'hzzzd': ('d a', 'a', ['scope', 'case'], '同じ提示文脈と事例の利用者。作用・自然的能力・未成熟を同じ本人へ結ぶ。'),
    'hzzze': ('d a', 'd', ['scope', 'case'], '同じ事例の使用とその継続を比較する基準状況。文章を提示する文脈や実際の現在と自動同一視しない。'),
    'hzzzf': ('d a a', 'c', ['scope', 'preferred', 'other'], '同じ提示文脈における使用事例の通常性の厳密な優先関係。使用環境や妨害などの背景を比較し、未成熟という結果そのものから優先を作らない。各種類の内部で評価する。'),
    'hzzzg': ('d a a d d', 'c', ['scope', 'object', 'person', 'anchor', 'branch'], '同じ対象・本人・基準の使用について比較する継続履歴の候補。同じ事例に固定した背景で使い続ける場合とやめる場合を比較し、結果だけを理由に候補を削らない。'),
    'hzzzh': ('d a a d d d', 'c', ['scope', 'object', 'person', 'anchor', 'branch', 'point'], '同じ対象・本人・基準・候補について比較する一つの履歴に属する状況。基準以降はその候補の残りの生涯の全範囲を含める解釈で、結果が続いた観測点だけを集めた範囲や都合のよい途中打切りではない。反事実の別履歴の状況を混ぜない。実際の履歴の完全性は解釈根拠を要する。'),
    'hzzzi': ('d a a d d d d', 'c', ['scope', 'object', 'person', 'anchor', 'branch', 'earlier', 'later'], '同じ候補履歴内での厳密な時間的先行。候補・本人・対象を固定し、本文順序や通常性順位と混同しない。履歴内の厳密全順序を構成で検査する。'),
    'hzzzj': ('', 'a', [], '第三段落第三文の主語Satzungen und Formeln、固定転写u0010 [293,314) の箇所。'),
    'hzzzk': ('', 'a', [], '同じ第三文のdieseで先行する主語を受けて道具として説明する同格句、固定転写u0010 [316,416) の箇所。'),
}
MEANINGS = {
    'r2fr': '各比較候補の履歴が基準を含み、厳密な全順序を持つことを要求する。その同じ履歴の基準以降の全点をrbyで選び、既存r2euの条件付き継続を評価する。継続点だけを独立に選ばず、空候補・不可能な継続前件は成立させない。',
    'r2fs': '同じ提示文脈・対象・本人について、基準で規定または型制限を広げた定型表現r2fhに属し、同じ対象と本人の吟味のない誤用r2ewを続ける候補履歴では、同じ使用活動の因果的結果r2exも残部全体で続く。実際の残余生涯の結果h26は要求しない。',
    'r2ft': '同じ文章文脈whに固定したr2fsの対象・本人を、二位置の列へ渡す比喩の対象側の記述。身体的足枷h2bの位置と対応させる。',
    'r2fu': '同じ提示文脈の比較事例を規定hd2と定型表現r2fgの種類ごとに分け、各種類の通常事例で、同じ対象・本人・基準のr2fsが成立するという一般化。種類を一つへ混ぜて一方の不成立を隠さず、重なりは許す。',
    'r2fv': '第三文の一般化r2fuへの主張帰属、同じ条件付きの対象関係r2ftと足枷h2bの比喩帰属、r2fwの同格参照、既存ho2の合理的使用から誤用への言い直し、前後文との本文順序を合わせる。帰属された世界内容は実行しない。',
    'r2fw': '主語句とdieseで受ける同格句が、同じ著者・第三文の範囲・提示文脈で、規定と定型表現の同じ合成的な種類記述r2fhを指す。同格による説明と本文順序を既存rytの構成で結び、実在する個別物の一覧とはしない。',
}
LIMITS = [
    '第三文の通し候補として、二種類への分配的な一般化と、使い続ける候補で残部全体に及ぶ作用という読みを採用する。全ての現実の人が実際に永久に脱出できないという旧対象条件を使わない。',
    '一般化は指定した通常性の比較に依存し、全称や現況の多数ではない。両種類に通常事例を要求するが、現在の実例の存在や二種類の共同作用は要求しない。比較範囲・通常性・履歴の完全性は結果から都合よく選べない解釈入力である。',
    '各履歴に基準と厳密全順序を要求し、基準以降を全て対象にする。個人の無限の寿命、時間の無上界性、終点がないことは課さない。immerwährendenを継続する使用の下で持続するという読みとするが、その強調と語義の最終判断は別に残す。',
    'r2euの前件は履歴の残部全体での使用である。途中でやめた候補の停止前の全時点の保証や、一度の使用が後まで残す効果を今回の式に読み込まない。使用をやめれば必ず成熟するという逆向きの結論もない。',
    '規定は既存の採用された条件付き要求、定型表現は型と引数数を固定しない再利用可能な式の保持として読む。制定や慣習の成立の一般理論、原文の全ての語感の一致を今回の接続だけで完了とはしない。',
    'mechanischenは適用を吟味しない使用として、Naturgabenは同じ本人に帰属する自然的能力として既存の構成を用いる。使用・誤用・原因・結果は同じ活動へ結び、合理的使用の単なる否定へ誤用を縮めない。',
    'dieseは先行する二種類を受ける種類の参照として、同格句はその説明として明示する。指示を原語の文字列や未確定の個体一覧で代用しない。字義的な身体拘束の実在は比喩の帰属から導かない。',
    '一文全体の候補を記述するが、最終の語義・持続の強さ・意味一致の判断は未完。十二全単位と先頭二文の判断を保存し、新しい全単位・文単位の意味確認を主張しない。',
]


@lru_cache(None)
def parent(): return load_catalog(ROOT, PARENT_BASIS)


@lru_cache(None)
def imports():
    kinds = load_catalog(ROOT, KIND_BASIS)
    row = deepcopy(kinds.entries['r2fa']['declaration'])
    parts = (ROOT / APPOSITION).read_text(encoding='utf-8').split('.')
    selected = [p.strip()+'.' for p in parts if p.strip().startswith(('d ryt[', 'r ibbdenotes[', 'r ibbclarifies['))]
    assert len(selected) == 3
    appos = parse('p:' + ''.join(selected))
    basis = json.loads((ROOT / APPOSITION_BASIS).read_text(encoding='utf-8'))
    return [row, *appos['declarations']], {
        'r2fa': kinds.entries['r2fa']['meaning_ja'], 'ryt': basis['definitions']['ryt'],
        'ibbdenotes': basis['primitive_conventions']['ibbdenotes'], 'ibbclarifies': basis['primitive_conventions']['ibbclarifies']}


def definitions():
    history = 'i[point d][c[v histories][v anchor v branch v point]]'
    order = 'i[first d second d][c[v before][v anchor v branch v first v second]]'
    valid = 'f branch d[y[c[v candidates][v anchor v branch]][w[c[v histories][v anchor v branch v anchor]][k ta['+history+' '+order+']]]]'
    tails = 'i[start d branch d point d][c[k rby[i[entry d][c[v histories][v start v branch v entry]] i[first d second d][c[v before][v start v branch v first v second]] v start]][v point]]'
    ordered = 'd r2fr[condition e result e anchor d candidates h[d d] c histories h[d d d] c before h[d d d d] c] c[w['+valid+'][k r2eu[v condition v result v anchor v candidates '+tails+']]].'
    return ordered + '''
d r2fs[scope d object a person a anchor d] c[w[t[k r2fh[v object]][v anchor]][
 k r2fr[k r2ew[v object v person] k r2ex[v object v person] v anchor
 i[start d branch d][k hzzzg[v scope v object v person v start v branch]]
 i[start d branch d point d][k hzzzh[v scope v object v person v start v branch v point]]
 i[start d branch d first d second d][k hzzzi[v scope v object v person v start v branch v first v second]]]
]].
d r2ft[participants j[a]] e[k rbv[i[object a person a][b anchor[k r2fs[k wh[] v object v person v anchor]]] v participants]].
d r2fu[] e[b scope[k r2fa[
 i[item a][w[k hzzzb[v scope v item]][t[k hd2[k hzzzc[v scope v item]]][k hzzze[v scope v item]]]]
 i[item a][w[k hzzzb[v scope v item]][t[k r2fg[k hzzzc[v scope v item]]][k hzzze[v scope v item]]]]
 i[first a second a][k hzzzf[v scope v first v second]]
 i[item a][k r2fs[v scope k hzzzc[v scope v item] k hzzzd[v scope v item] k hzzze[v scope v item]]]
]]].
d r2fw[] c[k ryt[k hzzzj[] k hzzzk[] k wa[] r b[p r2fh] k h2d[] k wh[] p ibbdenotes p ue p ibbclarifies]].
d r2fv[] c[w[k uc[k h2d[] k wa[] r[k r2fu[]] k wh[]]][w[
 k rbu[k h2d[] k wa[] r[p r2ft] r[p h2b] k wh[]]][w[k r2fw[]][w[k ho2[]][w[
 k ue[k hzzr[] k h2d[] k wh[]]][k ue[k h2d[] k h3a[] k wh[]]]]]]]].
'''


def build():
    old = parent(); doc = deepcopy(old.document); statements = doc['statements']; doc['statements'] = []
    imported, meanings = imports()
    new_names = set(MEANINGS) | set(PRIMITIVES) | set(meanings)
    assert not new_names & set(old.entries)
    size = len(doc['declarations']); doc['declarations'].extend(deepcopy(imported))
    extra = ''.join('r '+n+'['+p+'] '+r+'.' for n,(p,r,_,_) in PRIMITIVES.items())
    doc = parse(format_graph(doc, 'compact') + extra + definitions())
    assert len(statements) == 54 and statements[52]['body']['symbol'] == 'r2fk'
    assert statements[10]['body']['symbol'] == 'ho2' and statements[53]['body']['symbol'] == 'h3b'
    statements[52] = dict(kind='assert', body=dict(kind='call', symbol='r2fv', arguments=[]))
    doc['statements'] = statements; doc = parse(format_graph(doc, 'compact'))
    core = deepcopy(doc); core.update(declarations=closure(doc, ['r2fv']), statements=doc['statements'][52:53])
    library = deepcopy(doc); library.update(declarations=closure(doc, ['r2fr']), statements=[])
    added = doc['declarations'][size:]; assert len(added) == 20
    primitive_rows = {}
    for d in added:
        if d['kind'] != 'primitive': continue
        n = d['name']
        args = PRIMITIVES[n][2] if n in PRIMITIVES else (
            ['node', 'author', 'property_description', 'scope', 'context'] if n == 'ibbdenotes' else ['first', 'second', 'author', 'scope', 'context'])
        primitive_rows[n] = dict(parameters=d['parameters'], result=d['result'], arguments=args,
                                meaning_ja=PRIMITIVES[n][3] if n in PRIMITIVES else meanings[n])
    basis = dict(status='generic_conditional_fetters_sentence_candidate', document=FULL, parent=PARENT,
        inherited_meaning_basis=PARENT_BASIS, primitives=primitive_rows,
        definitions=MEANINGS | {n: meanings[n] for n in ('r2fa', 'ryt')},
        new_signatures={d['name']: {k: d[k] for k in ('parameters', 'result')} for d in added}, limitations=LIMITS,
        imported_sha256={p: digest((ROOT / p).read_bytes()) for p in (KIND_BASIS, APPOSITION, APPOSITION_BASIS)})
    body = format_graph(doc, 'compact') + '\n'
    annotations = json.loads((ROOT / 'data/polymorphic-forms-identifiers-v1.json').read_text(encoding='utf-8'))
    annotations.update(document=FULL, document_sha256=digest(body.encode('utf-8')))
    enc = lambda x: json.dumps(x, ensure_ascii=False, indent=2)+'\n'
    return {FULL: body, CORE: format_graph(core, 'compact')+'\n', LIBRARY: format_graph(library, 'compact')+'\n',
            BASIS: enc(basis), ANNOTATIONS: enc(annotations)}


if __name__ == '__main__':
    from scripts.audit_opening_scope import write_exact
    for path, body in build().items(): write_exact(ROOT / path, body)
    print('Ordered kindwise conditional profile, apposition and depiction joined; statement 52 updated', flush=True)
