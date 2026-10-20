"""Bind Kant's public-use duty to a fixed activity scope throughout its period."""
from copy import deepcopy
from functools import lru_cache
import json

from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT, closure

PARENT = 'examples/v016/kant-question-discourse.noema'
PARENT_BASIS = 'data/question-discourse-basis-v1.json'
FULL = 'examples/v016/kant-public-freedom-duty.noema'
CORE = 'examples/v016/public-freedom-duty-core.noema'
BASIS = 'data/public-freedom-duty-basis-v1.json'
ANNOTATIONS = 'data/public-freedom-duty-identifiers-v1.json'
PRIMITIVES = {
    'h235q': ('[a d] a', ['public', 'reference'],
              '同じ公衆と基準文脈で、一般的な許可方針が適用される全ての時機を指定する期間枠。検査用の有限期間や啓蒙の到達を比べるh222gの期間と同一視しない。許可がある時点だけ、始終だけ、特定の成功事例の期間だけへ縮めない。候補経過への解釈は既存h7q/h7rを用い、期間の全範囲の正しい供給は解釈の責任とする。'),
    'h235r': ('[a d] a', ['regulator', 'reference'],
              'この基準文脈で、指定の規範源が活動の許可方針を定める立場。方針を受ける人の学識者としての立場とは区別する。特定の歴史的人物や官職名、正当な権力の所有をこの参照だけで断定しない。'),
    'h235s': ('[] a', [],
              '固定原文kant-1784:u0012回答文内の[704,768)、公的理性使用は常に自由であるべきと述べる節の箇所。回答文全体のh235p内にあり、後続の唯一性・可能性・私的使用の条件をこの箇所へ含めない。'),
}
MEANINGS = {
    'r2ye': '同じ公衆・基準・内側の規範源・期間枠について、整合した非空の対象期間の全点でhznaの公的使用の自由が成立する内容。全読者と各人の公的活動・役割は基準で固定し、許可と反対要求だけを各点で評価する。公的使用はzzo、自由は積極的な実行許可と不実行要求の不在という規範的な読み。実際の活動実行は不要。',
    'r2yf': '三個体の列を公衆・内側の規範源・期間枠の順に受け、第五段落の基準h232vに固定したr2yeを返す。過不足の列を拒否する。h7iの三引数とは役割が違うので別の記述参照とし、同じ列長だけで対象を交換しない。',
    'r2yg': '同じ公衆の内側規範源h222fに対し、その方針を定める立場h235rで、著者waを出所としてr2yfの全期間の自由を要求する。h235qの一般的適用期間を使い、前段の啓蒙比較期間を流用しない。時間量化は要求内容の中にあり、内容を実行せず、実際の許可・活動・要求の正当性を導かない。',
    'r2yh': '第五段落の同じ基準h232vにおける非空の公衆範囲h222eの全てについて、r2ygの自由要求が評価文脈で成立するという回答節の内容。公的使用の活動一つ・人物一人だけへの要求へ狭めない。',
    'r2yi': '回答文の公的使用の自由要求の節h235sに、内容r2yhを著者wa・第五段落の提示文脈h232oで帰属する。要求を述べたことと要求の実在・充足を分け、後続の啓蒙実現の可能性や私的使用への許可まで帰属済みとはしない。',
}
LIMITS = [
    '公的使用の後続定義に沿い、本人の理性を学識者として読者世界へ向けて使う活動というzzoを再利用する。人前の全行為でも、特定職業の全行為でもない。私的使用の職務分類zzpとは排他的な二分法を仮定しない。',
    'freiは先行文と同じ規範的な読みとして、固定した全公的活動への積極的実行許可と不実行要求の不在を採る。物理的な妨害の全面不在、実際の発言、発言内容の真理、不実行への積極的許可を補わない。',
    'muß jederzeitは全適用時機における自由を要求する読みとする。各時点で同じ要求が述べられることや、現実に自由が成立することへ交換しない。原文は特定の統治者を名指さないため、内側の規範源h222fを方針を定める名宛人として読むことも明示的な解釈である。',
    '適用期間h235qは全ての関連時機であり、啓蒙の達成を比べるh222gの有限期間をそのまま借りない。形式は無限の時点も量化できるが、有限検査は全期間や公衆範囲の外部的な網羅性を証明しない。範囲を縮めた別入力が真になることを原文範囲の充足とは認めない。',
    '方針の内容を評価する際、公衆・本人・役割・活動の分類を基準h232vから動かさない。候補時点の禁止や不実行によって分類を取り消し、全称許可を空虚に成立させることを防ぐ。',
    '原文[704,768)の節の構成と帰属までを行う。Ich antworteという自己提示、der allein kannの排他性と可能性、私的使用の頻度・程度・留保、回答文全体の対照と通読は未完。新たな文単位・全単位の意味確認文字数は加算しない。',
]


@lru_cache(None)
def parent():
    return load_catalog(ROOT, PARENT_BASIS)


def definitions():
    return '''
d r2ye[public a reference d source a frame a] e[b candidate[
 w[k tb[i[point d][k h7q[v frame v candidate v point]]
           i[point d][k h7r[v frame v candidate v point]]
           i[first d last d][k ic[v first v last v candidate]]]][
 k tc[i[point d][k h7r[v frame v candidate v point]]
      b point[k hzna[v public v reference v source v point]]]]
]].
d r2yf[bindings j[a]] e[b candidate[
 g public a[g source a[g frame a[
 w[k h7g[v bindings]][w[a[v bindings][n p a b][v public]][
 w[a[v bindings][n p b b][v source]][w[a[v bindings][n p c b][v frame]][
 t[k r2ye[v public k h232v[] v source v frame]][v candidate]]]]]
 ]]]
]].
d r2yg[public a evaluation d] c[
 k rds[k wa[] k h222f[v public k h232v[]]
       k h235r[k h222f[v public k h232v[]] k h232v[]]
       r[p r2yf] l[a][v public k h222f[v public k h232v[]] k h235q[v public k h232v[]]]
       e[v public][v public] v evaluation p h7g p h7k p h7l]
].
d r2yh[] e[b evaluation[
 w[g public a[k h222e[v public k h232v[]]]][
 f public a[y[k h222e[v public k h232v[]]][k r2yg[v public v evaluation]]]]
]].
d r2yi[] c[k hzon[k h235s[] k wa[] r b[k r2yh[]] k h232o[]]].
'''


def build():
    old = parent()
    doc = deepcopy(old.document)
    statements, doc['statements'] = doc['statements'], []
    assert not (set(PRIMITIVES) | set(MEANINGS)) & set(old.entries)
    doc = parse(format_graph(doc, 'compact') + ''.join(
        'r ' + n + row[0] + '.' for n, row in PRIMITIVES.items()) + definitions())
    added = doc['declarations'][len(old.document['declarations']):]
    new = dict(kind='assert', body=dict(kind='call', symbol='r2yi', arguments=[]))
    doc['statements'] = statements + [new]
    core = deepcopy(doc)
    core.update(declarations=closure(doc, list(MEANINGS)), statements=[new])
    decls = {d['name']: d for d in added}
    basis = dict(status='public_freedom_duty_clause_partial_answer', document=FULL,
                 parent=PARENT, inherited_meaning_basis=PARENT_BASIS, definitions=MEANINGS,
                 primitives={n: dict(parameters=decls[n]['parameters'], result=decls[n]['result'],
                                     arguments=row[1], meaning_ja=row[2]) for n, row in PRIMITIVES.items()},
                 new_signatures={d['name']: {k: d[k] for k in ('parameters', 'result')} for d in added},
                 limitations=LIMITS)
    body = format_graph(doc, 'compact') + '\n'
    annotations = json.loads((ROOT / 'data/question-discourse-identifiers-v1.json').read_text(encoding='utf-8'))
    annotations.update(document=FULL, document_sha256=digest(body.encode('utf-8')))
    encoded = lambda value: json.dumps(value, ensure_ascii=False, indent=2) + '\n'
    return {FULL: body, CORE: format_graph(core, 'compact') + '\n',
            BASIS: encoded(basis), ANNOTATIONS: encoded(annotations)}
