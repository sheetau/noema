"""Bind public and individual possibilities to the same prospective frame."""
from copy import deepcopy
from functools import lru_cache
import json

from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT, closure
from scripts.compose_described_dissemination import declaration

PARENT = 'examples/v016/kant-third-paragraph.noema'
PARENT_BASIS = 'data/third-paragraph-basis-v1.json'
FULL = 'examples/v016/kant-prospective-comparison.noema'
CORE = 'examples/v016/prospective-comparison-core.noema'
BASIS = 'data/prospective-comparison-basis-v1.json'
ANNOTATIONS = 'data/prospective-comparison-identifiers-v1.json'
FIELDS = [
    ('audience', 'a'), ('person', 'a'), ('source', 'a'), ('frame', 'a'),
    ('origins', 'h[d] d'), ('extent', 'h[h[a] c h[a] c] c'),
    ('cases', 'h[d] c'), ('scale', 'h[a] c'), ('less', 'h[a a] c'),
    ('near', 'h[a] c'), ('low', 'a'), ('high', 'a'),
    ('publicdegree', 'a'), ('individualdegree', 'a'), ('conditioneddegree', 'a'),
]
MEANINGS = {
    'r2ku': '指定した同じ人の自己形成による自立h4pが、同じ期間枠・候補の経過に属し、候補内の起点より厳密に後に完了する。aaの人であることを要求し、過去に完了した自立h4qの単なる再利用を拒否する。開始は起点以前でもよく、本人の活動・対象・因果を保持する。',
    'r2kv': '比較対象がaaの人であることと、同じ候補集合の全候補の期間枠・起点対応hzneを検査し、公衆の将来の能力変化hzngと同じ期間・起点・候補の個人の自己形成r2kuをrqstで比較する。公衆・参照文脈・広がり・比較個人・尺度値は固定した明示引数。人でない対象の最低値を個人の不可能性へ流用せず、過去の成功者の存在や候補件数の比へ置き換えない。',
    'r2kw': 'r2kvの比較と、同じ公衆・参照文脈・出所・期間・起点・広がり・候補・尺度によるhznhの条件付きのほぼ必然を結ぶ。自由の条件を課す前後で目標の公衆や変化を取り替えない。無条件の程度と条件付きの程度を同一化せず、後者が前者より厳密に高いという追加条件も課さない。',
    'r2kx': '指定した公衆・比較個人・出所・期間枠・候補・尺度等を保持したr2kwの内容。内容を評価する状況を人と公的活動の参照文脈として固定し、候補内部の起点はoriginsで別に与える。内容の評価文脈を全候補の起点へ自動代入しない。',
    'r2ky': 'r2kxの全十五引数を同じ順序の閉じた記述で充足し、階数1の閉じた内容記述を作る。実行結果や未充足の関数を引用内容としない。',
    'r2kz': 'r2kyの内容記述を、既存の結論側箇所hzp4・著者wa・提示文脈hzp3へhzonで帰属する構成。内容の真理や現実の許可を実行しない。引数を固定した本文主張はまだ追加せず、第一文の完成判定とは分ける。',
}
LIMITS = [
    '第四段落第一文の比較と条件付き様相を結ぶ部分構成。公衆の自己啓蒙を、公衆内部の活動が自立的な理解力の使用を広げる変化として読む方向を採る。第二文の自己評価・態度の伝播の全機構を第一文の真理条件へ必須追加しない。',
    '公衆の社会的な範囲と適切な広がり基準、比較する個人の文脈的な選択は未確定。単なる任意の読者範囲や、成功者だけの集合を公衆の完成定義としない。原文の一般的な個人対公衆を、任意に選んだ実在の一人へ確定してはいない。',
    '比較両側は同じ候補・期間枠・候補ごとの起点を持つ。過程は起点前に始まっていてもよいが、両側とも起点後に完了する。将来の公衆と過去の個人の成功、別の候補の自立を比較しない。',
    '自由は公的理性使用の許可を選択経過で維持する既存hznfの読みを引き継ぐ。物理的機会・他の妨害・全ての規範源の条件を説明し終えたとはしない。許可は必要条件・十分原因・現実の事実へ強めない。',
    '尺度と近さは既存rqst・rqsuの質的で厳密な読み。数値確率を補わず、条件付き程度が無条件の程度を必ず上回るという追加の主張をjaの代用にしない。jaの談話上の強め方、aber、nurの作用範囲は別途接続する。',
    '新しい基本記号や本文主張を追加しない。全十五記述を充足した帰属構成は作るが、原文に適した引数の固定と第一文全体の意味確認は未完。従来十三単位の判断を保持する。',
]


@lru_cache(None)
def parent():
    return load_catalog(ROOT, PARENT_BASIS)


def definitions():
    text = '''
d r2ku[person a frame a initial d branch d] c[w[k aa[v person]][
 k rqtd[i[point d][k h7q[v frame v branch v point]]
 i[first d last d][k ic[v first v last v branch]] v initial
 i[process a start d end d][k h4p[v person v process v start v end v branch]]]
]].
'''
    arguments = [('reference', 'd')] + FIELDS
    guard = 'f branch d[y[c[v cases][v branch]][k hzne[v frame c[v origins][v branch] v branch]]]'
    goal = 'i[branch d][k hzng[v audience v reference v frame c[v origins][v branch] v extent v branch]]'
    compared = 'i[branch d][k r2ku[v person v frame c[v origins][v branch] v branch]]'
    text += declaration('r2kv', arguments, 'c', 'w[k aa[v person]][w[' + guard + '][k rqst[v cases ' +
                        goal + ' ' + compared +
                        ' v scale v less v low v high v publicdegree v individualdegree]]]')
    all_args = ' '.join('v ' + n for n, _ in arguments)
    text += declaration('r2kw', arguments, 'c',
                        'w[k r2kv[' + all_args + ']][k hznh['
                        'v audience v reference v source v frame v origins v extent v cases '
                        'v scale v less v near v low v high v conditioneddegree]]')
    text += declaration('r2kx', FIELDS, 'e', 'b reference[k r2kw[' + all_args + ']]')
    described = [(n, 'i[' + t + ']') for n, t in FIELDS]
    supplied = ' '.join('v ' + n for n, _ in FIELDS)
    text += declaration('r2ky', described, 'i b[e]', 'o a[r b[p r2kx]][' + supplied + ']')
    text += declaration('r2kz', described, 'c',
                        'k hzon[k hzp4[] k wa[] k r2ky[' + supplied + '] k hzp3[]]')
    return text


def build():
    old = parent()
    doc = deepcopy(old.document)
    statements, doc['statements'] = doc['statements'], []
    assert not set(MEANINGS) & set(old.entries)
    doc = parse(format_graph(doc, 'compact') + definitions())
    doc['statements'] = statements
    core = deepcopy(doc)
    core.update(declarations=closure(doc, ['r2kz']), statements=[])
    added = doc['declarations'][len(old.document['declarations']):]
    basis = dict(status='prospective_public_individual_comparison_connected_partial',
                 document=FULL, parent=PARENT, inherited_meaning_basis=PARENT_BASIS,
                 definitions=MEANINGS, primitives={},
                 new_signatures={d['name']: {k: d[k] for k in ('parameters', 'result')} for d in added},
                 limitations=LIMITS)
    body = format_graph(doc, 'compact') + '\n'
    annotations = json.loads((ROOT / 'data/third-paragraph-identifiers-v1.json').read_text(encoding='utf-8'))
    annotations.update(document=FULL, document_sha256=digest(body.encode('utf-8')))
    encoded = lambda value: json.dumps(value, ensure_ascii=False, indent=2) + '\n'
    return {FULL: body, CORE: format_graph(core, 'compact') + '\n',
            BASIS: encoded(basis), ANNOTATIONS: encoded(annotations)}
