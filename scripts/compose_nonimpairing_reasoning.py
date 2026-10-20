"""Bind practical execution and causal nonimpairment to one person and method."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT, closure
from scripts.compose_qualitative_influence import both, TRUE

PARENTS = ('data/office-obedience-basis-v1.json', 'data/scholarly-self-ascription-basis-v1.json')
LIBRARY = 'examples/v016/nonimpairing-reasoning.noema'
BASIS = 'data/nonimpairing-reasoning-basis-v1.json'
STATE = 'h[a] c'
MODEL = 'variables j[a] equations h[a h[a] c] c factor a view h[h[a] c] d'
MARGS = 'v variables v equations v factor v view'
SCALE = 'checked h[a d d] c atleast h[a d d d] c'
ABILITY = 'available h[a a d] c outcomes h[a a d d] c selected h[a a d d] c'
PROVIDERS = ('variablesfor h[a a d] j[a] equationsfor h[a a d a h[a] c] c '
             'factorfor h[a a d] a viewfor h[a a d h[a] c] d')
FARGS = 'v variablesfor v equationsfor v factorfor v viewfor v checked v atleast v available v outcomes v selected'
CONTEXT = 'person a office a work a community a world a activity a scholar a writing a audience a reference d'
CARGS = 'v person v office v work v community v world v activity v scholar v writing v audience v reference'
MEANINGS = {
    'r3u': '同じ本人・活動の実行zzqの有無が、両介入の全解で要因と一致するhzeを要求する。その同じモデルの全解を、固定した同じ事務・基準の遂行尺度で評価し、r2vhの非悪化を検査する。事務が全面的に不成立かどうかの二値判定に限定せず、評価欠落・解なしを無害と扱わない。',
    'r3v': '指定した一つの方法について、選択された結果が、同じモデルの実行側の全解を状況へ写した集合と双方向に一致する。その方法だけを利用可能性の候補としてxdを適用し、同じ人が同じ活動を実行できる。別の方法の成功や別モデルの安全性を借りず、悪い結果を評価範囲から落とさない。',
    'r3w': '一つの方法を存在量化し、その同じ本人・方法・開始基準で変数列、方程式、要因、状況対応を取得する。その一つのモデルでr3uの事務非悪化とr3vの実行能力をともに満たす。安全だが実行できない方法と、実行できるが有害な方法の継ぎ合わせでは成立しない。',
    'r3x': '自己理解と書面による公的使用r3tの同じ人・活動・事務・基準を、理拠を述べ検討する活動h232pと実行可能な非悪化r3wへ接続する。先行職務を担当していることは保ち、全職務からの解放や実際の発信を主張しない。文全体の条件化・帰属・談話は別に必要である。',
}
LIMITS = [
    'u0012[1743,2122)の後半へ向けた依存群。本文の主張と意味確認済み文字数は増やさない。kannの実践的な両立可能性を構成する候補であり、許可だけで代用しない。文脈上の許可の含意と談話を含む最終の採用読みは文全体で判断する。',
    '同じ方法で実行するときと実行しないときの介入を、他の方程式と背景を固定して比較する。事務への害を単なる事務の不成立、現在の違反の不在、論理的無矛盾へ置き換えない。',
    'r2vhを使う全解の交差比較は、対応を限定しない頑健な非悪化という明示したモデル解釈である。確率的な通常性や全世界の絶対的無害性ではない。異なる外生背景を同じモデルの解へ混ぜない。背景対応が必要なモデルでは対応関係を別に構成すべきである。',
    'checked(work,reference,point)は同じ事務の遂行が同じ評価観点で評価済みであること、atleast(work,reference,left,right)はleftの遂行がright以上であること。事務の品質・遅延・量などの評価観点をモデル内で固定する。別の事務や論じる人の利益へ尺度をすり替えない。数値尺度や完全達成を一律に要求しない。',
    '利用可能性availableは実践的に実行できる方法であり、社会的許可と同一視しない。outcomesは同じ人・方法・開始点の想定結果、selectedは文脈上評価する結果。選択結果を因果モデルの実行側の全解と一致させるが、そのモデルの現実への適合は別の解釈上の仮定である。',
    'r3xは後件候補への接続であり、r3tの書かれた作品・記録を現実の刊行事実へ昇格させない。So fernの条件化、ja sogar、mithin、aber/allerdings、zugleich、zum Theileと照応の統合が残る。先行職務の要求は削除しない。',
]


@lru_cache(None)
def parents():
    return tuple(load_catalog(ROOT, p) for p in PARENTS)


def on(operator, body):
    return ('k ' + operator + '[v variables v equations i[item a][e[v item][v factor]] '
            'i[item a][' + TRUE + '] ' + body + ']')


def definitions():
    aligned = 'k hze[k zzq[v person v activity] ' + MARGS + ']'
    profile = ('k r2vh[v variables v equations v factor '
               'i[state ' + STATE + '][c[v checked][v work v reference c[v view][v state]]] '
               'i[left ' + STATE + ' right ' + STATE + '][c[v atleast]['
               'v work v reference c[v view][v left] c[v view][v right]]]]')
    text = 'd r3u[person a activity a work a reference d ' + MODEL + ' ' + SCALE + '] c[' + both(aligned, profile) + '].\n'
    selected = 'c[v selected][v person v method v reference v point]'
    image = on('rv', 'i[state ' + STATE + '][e[c[v view][v state]][v point]]')
    exact = 'f point d[z[' + selected + '][' + image + ']]'
    available = 'i[actor a option a point d][' + both(
        'e[v option][v method]', 'c[v available][v actor v option v point]') + ']'
    capable = ('k xd[v person k zzq[v person v activity] v reference ' + available +
               ' v outcomes v selected]')
    text += 'd r3v[person a activity a method a reference d ' + MODEL + ' ' + ABILITY + '] c[' + both(exact, capable) + '].\n'
    model = ('c[v variablesfor][v person v method v reference] '
             'i[item a state ' + STATE + '][c[v equationsfor][v person v method v reference v item v state]] '
             'c[v factorfor][v person v method v reference] '
             'i[state ' + STATE + '][c[v viewfor][v person v method v reference v state]]')
    joint = both('k r3u[v person v activity v work v reference ' + model + ' v checked v atleast]',
                 'k r3v[v person v activity v method v reference ' + model + ' v available v outcomes v selected]')
    text += 'd r3w[person a activity a work a reference d ' + PROVIDERS + ' ' + SCALE + ' ' + ABILITY + '] c[g method a[' + joint + ']].\n'
    text += 'd r3x[' + CONTEXT + ' ' + PROVIDERS + ' ' + SCALE + ' ' + ABILITY + '] c[' + both(
        'k r3t[' + CARGS + ']', 'k h232p[v activity v reference]',
        'k r3w[v person v activity v work v reference ' + FARGS + ']') + '].\n'
    return text


def build():
    old, civic = parents()
    doc = deepcopy(old.document)
    doc.update(declarations=closure(doc, ['hze', 'r2vh', 'xd', 'zzq', 'h232p']), statements=[])
    imported = {d['name']: old.entries[d['name']] for d in doc['declarations']}
    for d in closure(civic.document, ['r3t']):
        name = d['name']
        if name in imported:
            assert d == imported[name]['declaration']
            assert civic.entries[name]['meaning_ja'] == imported[name]['meaning_ja']
        else:
            doc['declarations'].append(d)
            imported[name] = civic.entries[name]
    assert not set(MEANINGS) & set(imported)
    doc = parse(format_graph(doc, 'compact') + definitions())
    meanings, primitives = {}, {}
    for name, e in imported.items():
        d = e['declaration']
        if e['kind'] == 'definition':
            meanings[name] = e['meaning_ja']
        else:
            primitives[name] = dict(parameters=d['parameters'], result=d['result'], arguments=e['arguments'], meaning_ja=e['meaning_ja'])
    sources = set().union(*(set(c.source_sha256) for c in parents()))
    basis = dict(status='practical_execution_with_same_work_causal_nondecrease_dependency', document=LIBRARY,
                 primitives=primitives, definitions=meanings | MEANINGS,
                 imported_symbols={n: e['meaning_basis'] for n, e in imported.items()},
                 import_source_sha256={p: digest((ROOT / p).read_bytes()) for p in sorted(sources)}, limitations=LIMITS)
    return {LIBRARY: format_graph(doc, 'compact') + '\n', BASIS: json.dumps(basis, ensure_ascii=False, indent=2) + '\n'}
