"""Compose owned thoughts, completed attentive review, and benevolent purpose."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT, closure
from scripts.compose_qualitative_influence import both, TRUE

PARENTS = ('data/clerical-obligation-basis-v1.json',)
SPEECH_BASIS = 'data/candid-assessments-basis-v1.json'
SPEECH_DOC = 'examples/v016/candid-assessments.noema'
LIBRARY = 'examples/v016/reviewed-thoughts.noema'
BASIS = 'data/reviewed-thoughts-basis-v1.json'
PRIMITIVES = {
    'h246t': ('[a d] c', ['review', 'point'],
        'この検討判断は、その対象内容の吟味を行う過程として、この時点には一応の結論に至り終えている。単に検討を始めた、予定した、途中にあるという場合と区別する。結論の正しさ・肯定・完全な確実性・永久に再検討しないことは含意しない。'),
    'h246u': ('[a a a a d] c', ['person', 'review', 'thought', 'aspect', 'reference'],
        '同じ本人が同じ見解内容をこの吟味判断で検討する際、固定基準で注意を配るべき関連事項の完全な範囲に属する。根拠・反例・帰結などのどれが必要かを解釈で指定し、実際に注意した事項や有利な事項だけへ絞らない。判断の正しさや対象内容の真理は含意しない。'),
}
MEANINGS = {
    'r36m': '本人の同じ判断が、同じ見解h224yの同じ話題h224zを肯定している。fa、fb、hznnを結び、単なる引用・検討や他人の見解と区別する。見解の真理や無謬性は要求しない。',
    'r36n': '同じ本人の同じ吟味判断が、同じ見解の内容を肯定命題の形で取り出したrsbの記述を、同じ話題について検討し、その過程を一応終えている。hzwとh246tを結び、実際に肯定したことや真と証明したことへ変えない。',
    'r36o': '本人・見解の正確な二個体列について、r36nを満たす吟味判断があるという目標内容。慎重な遂行の目標に用い、過不足の列や別人・別見解へ取り替えない。目標への志向だけで達成を導かない。',
    'r36p': '同じ本人の同じ見解への完了した吟味r36nに、本人一人を担い手とするrqvpの注意を結ぶ。同じ吟味行為が生起し本人が参加し、同じr36oの目標へ向けて、固定した非空の全関連事項h246uに本人が注意を配る。別の行為や目標への注意では足りない。',
    'r36q': '同じ本人が基準点で自分の見解を持つr36mに、同じ本人の整合した履歴において基準点以前にr36pの吟味が済んでいることを結ぶ。未来の吟味予定や別の内容の検討では足りず、同じ時点までの完了も許す。内容が真であることは要求しない。',
    'r36r': '同じ本人の同じ見解を持つ判断r36mに、その同じ判断行為が自分とは異なる対象の利益・善を目的とし、それ自体好ましいものとして求めるrqynを結ぶ。他の動機の併存を排除せず、実際の受益・教義の真理・全員の賛同は要求しない。',
    'r36s': '同じ本人・見解・判断について、慎重な吟味済みr36qと同じ判断行為の他者への善意r36rを結ぶ。同じ人物の無関係な親切さ、他人の吟味、別の内容の正しさを借りない。',
    'r36t': '同じ本人・見解についてr36sを満たす判断と受益対象がある。原文にない受益者名を固定せず、自由や使命の適用範囲へ使う見解の資格候補を作る。公的な提示の実行や許可・義務はまだ加えない。',
}
LIMITS = [
    'u0012[3186,3452)のseine sorgfältig geprüften und wohlmeinenden Gedankenに向けた依存群。信条の欠点への見解、改善提案、全公衆への伝達、自由・使命、alle・volle・ja sogar・Aberと全文帰属は未統合。意味確認文字数を加算しない。',
    '見解の保有、吟味、注意、他者の利益への目的を別々に構成する。h224xの確定した原則として受け入れるに足る根拠の確認をそのまま要求せず、今回の見解を確定原則や客観的真理へ強めない。',
    'geprüftは一応の結論まで検討を済ませたこと、sorgfältigは固定した全関連事項への継続した注意という明示した読み。成功した検討と真なる結論を同一化せず、唯一の心理学的定義とはしない。',
    'wohlmeinendは他者の利益・善をそれ自体求め、その見解を持つ判断の目的にもする読み。保存したAdelungのWohlmeinenを補助資料とする。善い結果の実現、他の動機の不在、単に悪意がないこと、全聴衆への同一の好意とは区別する。',
    '見解と吟味の資格は同じ基準点で確認する。吟味はその点以前に完了してよいが、公的な発話が現に行われたことは条件にしない。発言活動・本人の立場・許可や使命への接続は別途行う。',
]


@lru_cache(None)
def parents(): return tuple(load_catalog(ROOT, p) for p in PARENTS)


def speech_entries():
    # This historical basis predates catalog inheritance metadata. Project only
    # these two self-contained definitions; preserve and pin both originals.
    basis = json.loads((ROOT / SPEECH_BASIS).read_text(encoding='utf-8'))
    doc = parse((ROOT / SPEECH_DOC).read_text(encoding='utf-8'))
    ds = closure(doc, ['rsb'])
    assert {d['name'] for d in ds} == {'rsa', 'rsb'}
    return {d['name']: dict(kind='definition', declaration=d,
        meaning_ja=basis['definitions'][d['name']], meaning_basis=SPEECH_BASIS) for d in ds}


def definitions():
    subject, code = 'k h224z[v thought]', 'k h224y[v thought]'
    text = 'd r36m[person a thought a judgment a point d] c[' + both('k aa[v person]',
        'k fa[v person v judgment v point]', 'k fb[v judgment ' + subject + ' v point]',
        'k hznn[v judgment ' + subject + ' ' + code + ' ' + TRUE + ' v point]') + '].\n'
    message = 'k rsb[' + code + ' r[' + TRUE + ']]'
    text += 'd r36n[person a thought a review a point d] c[' + both(
        'k hzw[v person v review ' + subject + ' ' + message + ' v point]', 'k h246t[v review v point]') + '].\n'
    text += 'd r36o[bindings j[a]] e[b point[g person a[g thought a[' + both(
        'e[v bindings][l[a][v person v thought]]', 'g review a[k r36n[v person v thought v review v point]]') + ']]]].\n'
    text += 'd r36p[person a thought a review a reference d point d] c[' + both(
        'k r36n[v person v thought v review v point]',
        'k rqvp[i[actor a][e[v actor][v person]] v review r[p r36o] l[a][v person v thought] '
        'i[aspect a][k h246u[v person v review v thought v aspect v reference]] p hztj p hztl p dg p df v point]') + '].\n'
    history = 'i[at d][k ia[v person v reference v at]]'
    order = 'i[first d last d][k ic[v first v last v reference]]'
    text += 'd r36q[person a thought a judgment a reference d] c[' + both(
        'k r36m[v person v thought v judgment v reference]', 'k ta[' + history + ' ' + order + ']',
        'k ia[v person v reference v reference]', 'g review a[g earlier d[' + both(
            'k ia[v person v reference v earlier]', 'x[k ic[v earlier v reference v reference]][e[v earlier][v reference]]',
            'k r36p[v person v thought v review v reference v earlier]') + ']]') + '].\n'
    text += 'd r36r[person a thought a judgment a beneficiary a reference d] c[' + both(
        'k r36m[v person v thought v judgment v reference]', 'k rqyn[v judgment v person v beneficiary v reference]') + '].\n'
    text += 'd r36s[person a thought a judgment a beneficiary a reference d] c[' + both(
        'k r36q[v person v thought v judgment v reference]', 'k r36r[v person v thought v judgment v beneficiary v reference]') + '].\n'
    text += 'd r36t[person a thought a reference d] c[g judgment a[g beneficiary a[k r36s[v person v thought v judgment v beneficiary v reference]]]].\n'
    return text


def build():
    old, = parents(); doc = deepcopy(old.document)
    doc.update(declarations=closure(doc, ['aa', 'fa', 'fb', 'hznn', 'h224y', 'h224z', 'hzw', 'rqvp', 'rqyn', 'ia', 'ic', 'ta', 'hztj']), statements=[])
    imported = {d['name']: old.entries[d['name']] for d in doc['declarations']}
    for n, entry in speech_entries().items():
        d = entry['declaration']
        if n in imported: assert d == imported[n]['declaration'] and entry['meaning_ja'] == imported[n]['meaning_ja']
        else: doc['declarations'].append(d); imported[n] = entry
    assert not (set(PRIMITIVES) | set(MEANINGS)) & set().union(*(set(p.entries) for p in parents()))
    doc = parse(format_graph(doc, 'compact') + ''.join('r ' + n + row[0] + '.' for n, row in PRIMITIVES.items()) + definitions())
    ds = {d['name']: d for d in doc['declarations']}
    primitives = {n: dict(parameters=e['declaration']['parameters'], result=e['declaration']['result'], arguments=e['arguments'],
        meaning_ja=e['meaning_ja']) for n, e in imported.items() if e['kind'] == 'primitive'}
    primitives.update({n: dict(parameters=ds[n]['parameters'], result=ds[n]['result'], arguments=row[1], meaning_ja=row[2])
        for n, row in PRIMITIVES.items()})
    sources = set().union(*(set(c.source_sha256) for c in parents())) | {SPEECH_BASIS, SPEECH_DOC}
    basis = dict(status='own_carefully_reviewed_well_intentioned_thoughts', document=LIBRARY, primitives=primitives,
        definitions={n: e['meaning_ja'] for n, e in imported.items() if e['kind'] == 'definition'} | MEANINGS,
        imported_symbols={n: e['meaning_basis'] for n, e in imported.items()},
        import_source_sha256={p: digest((ROOT / p).read_bytes()) for p in sorted(sources)}, limitations=LIMITS)
    return {LIBRARY: format_graph(doc, 'compact') + '\n', BASIS: json.dumps(basis, ensure_ascii=False, indent=2) + '\n'}
