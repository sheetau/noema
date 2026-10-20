"""Connect possible enlightenment to public use in every productive route."""
from copy import deepcopy
from functools import lru_cache
import json

from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT, closure
from scripts.compose_qualitative_influence import both

PARENT = 'examples/v016/kant-public-freedom-duty.noema'
PARENT_BASIS = 'data/public-freedom-duty-basis-v1.json'
FULL = 'examples/v016/kant-public-enlightenment-route.noema'
CORE = 'examples/v016/public-enlightenment-route-core.noema'
BASIS = 'data/public-enlightenment-route-basis-v1.json'
ANNOTATIONS = 'data/public-enlightenment-route-identifiers-v1.json'
PRIMITIVES = {
    'h235t': ('[] a', [], '固定原文kant-1784:u0012回答文[768,833)、公的使用だけが人間の啓蒙を実現できると続ける節の箇所。直前の自由要求h235sと同じ回答h235pに属する。'),
}
MEANINGS = {
    'r2yj': '同じ公衆・基準・候補経過で、期間・母集団の有効性r2wz、開始終了のr2xa、同じ一過程の変化比率r2xcがh222jを超えることを要求する。r2xeで存在量化した啓蒙達成を個々の過程・時間証拠へ取り出し、異なる過程の成果を合併しない。',
    'r2yk': '同じ公衆・基準・候補・過程・開始終了点について、hzmxで内部の人の能力変化を実際に生じさせる当事者と活動部分があり、その同じ当事者・活動が基準でzzoの公的使用に分類される。公的活動の同時生起だけでは足りず、別過程・別対象・別時間の因果を流用しない。活動分類は基準、実行と結果生成は候補内で評価する。',
    'r2yl': '結果で選別しない同じh222kの非空の候補経過全てを有効化し、公的活動を生産的部分に持つ啓蒙達成の証拠が少なくとも一つあり、全候補の全啓蒙達成証拠がそのような部分を持つことを要求する。公的使用なしに成功する過程が一つでもあれば成立しない。失敗候補や他の背景・補助条件は許す。',
    'r2ym': '第五段落の基準h232vに固定した非空の公衆範囲h222e全てについて、r2ylの公的使用を不可欠とする達成可能性を述べる内容。啓蒙・期間・範囲は先行r2lnと同じ採用解釈へ結び、公的使用そのものの自由要求r2yhと取り替えない。',
    'r2yn': '回答の後続節h235tへr2ymを同じ著者wa・提示文脈h232oで帰属し、自由要求の節h235sからの順序を保つ。内容を評価せず、現実の成功や著者の主張の真理を帰属から導かない。',
}
LIMITS = [
    'derは前節の公的使用を受ける。自由の政策状態そのものを啓蒙の原因とする代用ではなく、zzoの活動が同じ変化過程で能力変化を生じさせることをhzmxへ接続する。',
    'der allein kannは、公的使用を生産的部分に含む啓蒙の達成経路が可能であり、公的使用を欠く経路では達成できないという読みを採る。公的使用があれば必ず成功する、公的使用以外の背景条件や補助行為は不要である、全活動が公的使用でなければならない、という主張は加えない。',
    '公的使用の部分は同じ過程で同じ対象の能力変化に実際に作用する必要がある。無関係な公的発言との同時生起を不可欠性の証拠にしない。候補経過・過程の網羅性はh222k等の解釈入力の責任であり、成功例や公的使用がある例だけへ範囲を縮めない。',
    '同じ候補内に複数の達成過程がある場合も全てを調べる。公的使用を含む一過程で、別の非公的な達成過程を隠せない。失敗例があっても可能性は成立し得るが、全て失敗なら成立しない。',
    'unter Menschenは先行r2lnと同じ公衆の人々における自立的な能力変化の広がりとして読む。有限の全読者・固定期間・内部の作用・文脈の広がり基準という既存の採用解釈を継承し、単なる情報増加や経済的成果に替えない。',
    '今回の可能性は文脈で比較する経過に相対的であり、全ての論理的可能世界についての定理や原著者の主張の実証ではない。形式の量化を有限の実行例と同一視しない。候補の有効性を確認し、未評価を失敗や非公的経路の不在に置き換えない。',
    '回答文の節の部分構成であり、Ich antworteの自己提示、私的使用の頻度・程度・進行への留保、全文の対照と原刊通読は残る。文単位の確認済み文字数は加算しない。',
]


@lru_cache(None)
def parent():
    return load_catalog(ROOT, PARENT_BASIS)


def definitions():
    args = 'v public v reference v branch v process v before v after'
    params = 'public a reference d branch d process a before d after d'
    text = 'd r2yj[' + params + '] c[' + both(
        'k r2wz[v public v reference v branch]',
        'k r2xa[v public v reference v branch v before v after]',
        'k hc[k h222j[v public v reference] k r2xc[' + args + ']]') + '].\n'
    text += 'd r2yk[' + params + '] c[g actor a[g person a[g part a[g role a[' + both(
        'k hzmx[v public v actor v person v process v part v before v after v branch '
        'i[group a member a point d][k h6t[v group v member v reference]]]',
        'k zzo[v actor v part v role v reference]') + ']]]]].\n'
    candidate = 'k h222k[v public v reference v branch]'
    episode = 'k r2yj[' + args + ']'
    public = 'k r2yk[' + args + ']'
    text += 'd r2yl[public a reference d] c[' + both(
        'k r2wy[v public v reference]',
        'g branch d[' + candidate + ']',
        'f branch d[y[' + candidate + '][k r2wz[v public v reference v branch]]]',
        'g branch d[g process a[g before d[g after d[' + both(candidate, episode, public) + ']]]]',
        'f branch d[f process a[f before d[f after d[y[' + both(candidate, episode) + '][' + public + ']]]]]') + '].\n'
    text += '''
d r2ym[] e[b evaluation[
 w[g public a[k h222e[v public k h232v[]]]][
 f public a[y[k h222e[v public k h232v[]]][k r2yl[v public k h232v[]]]]]
]].
d r2yn[] c[w[k hzon[k h235t[] k wa[] r b[k r2ym[]] k h232o[]]][
 k ue[k h235s[] k h235t[] k h232o[]]]].
'''
    return text


def build():
    old = parent()
    doc = deepcopy(old.document)
    statements, doc['statements'] = doc['statements'], []
    assert not (set(PRIMITIVES) | set(MEANINGS)) & set(old.entries)
    doc = parse(format_graph(doc, 'compact') + ''.join(
        'r ' + n + row[0] + '.' for n, row in PRIMITIVES.items()) + definitions())
    added = doc['declarations'][len(old.document['declarations']):]
    new = dict(kind='assert', body=dict(kind='call', symbol='r2yn', arguments=[]))
    doc['statements'] = statements + [new]
    core = deepcopy(doc)
    core.update(declarations=closure(doc, list(MEANINGS)), statements=[new])
    decls = {d['name']: d for d in added}
    basis = dict(status='public_enlightenment_route_clause_partial_answer', document=FULL,
                 parent=PARENT, inherited_meaning_basis=PARENT_BASIS, definitions=MEANINGS,
                 primitives={n: dict(parameters=decls[n]['parameters'], result=decls[n]['result'],
                                     arguments=row[1], meaning_ja=row[2]) for n, row in PRIMITIVES.items()},
                 new_signatures={d['name']: {k: d[k] for k in ('parameters', 'result')} for d in added},
                 limitations=LIMITS)
    body = format_graph(doc, 'compact') + '\n'
    annotations = json.loads((ROOT / 'data/public-freedom-duty-identifiers-v1.json').read_text(encoding='utf-8'))
    annotations.update(document=FULL, document_sha256=digest(body.encode('utf-8')))
    encoded = lambda value: json.dumps(value, ensure_ascii=False, indent=2) + '\n'
    return {FULL: body, CORE: format_graph(core, 'compact') + '\n',
            BASIS: encoded(basis), ANNOTATIONS: encoded(annotations)}
