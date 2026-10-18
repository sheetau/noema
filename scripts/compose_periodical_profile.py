"""Describe editorial association and nominal cadence apart from a title string."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_falling_depiction import ROOT, closure
from scripts.compose_qualified_judgment import both
from scripts.compose_gregorian_rules import seq

PARENT = 'examples/v016/kant-judgment-standards.noema'
PARENT_BASIS = 'data/judgment-standards-basis-v1.json'
FULL = 'examples/v016/kant-periodical-profile.noema'
CORE = 'examples/v016/periodical-profile-core.noema'
LIBRARY = 'examples/v016/periodical-profile.noema'
BASIS = 'data/periodical-profile-basis-v1.json'
ANNOTATIONS = 'data/periodical-profile-identifiers-v1.json'
PRIMITIVES = {
    'hzwh': ('[a a i[h[a] e] i[h[a] e] d] c', ['著者', '記述の使用箇所', '対象を選ぶ記述', '呼称内の性質記述', '文脈'],
        '著者がこの箇所で、前者の記述で指す対象について、後者の性質記述を呼称内で使う。対象は人にも物にもなり得る。記述内容の現実の成立や著者の字義通りの信念は含意しない。'),
    'hzwa': ('[a a b b d] c', ['刊行系列', '暦', '周期の日数', '周期ごとの通常号数', '文脈'],
        'この刊行系列が、この暦の連続した指定日数を一周期として繰り返し、各周期に指定数の通常号を出す慣行上の刊行方針を持つ。日数と号数は正の整数である。周期の始点や曜日は指定せず、暦日を一定の秒数と同一視しない。観測した平均頻度や、全ての号の実際の発行、欠刊の不在、特別号の禁止を含意しない。'),
    'hzwb': ('[a a d] c', ['人物', '刊行系列', '文脈'],
        'この人物が、この刊行系列の文面を作成・選定・編成して出すことに編集上の責任を持つ。責任の関係を述べ、各記事の単独著作、印刷・販売の版元、所有権、法的な役職の詳細や唯一の責任者であることまでは含意しない。'),
    'hzwc': ('[] a', [], '脚注でBüschingの名を通じて刊行系列へ結ばれる人物。刊行系列hzkd、号hzkc、人物を指す名称hzwdとは別の参照である。'),
    'hzwd': ('[] a', [], '脚注の刊行物の呼び方に含まれるBüschingという人物の名称。原語の綴りは識別表記へ置き、名称自体を人物や刊行系列と同一視しない。'),
}
MEANINGS = {
    'rqw4': '周期の日数と通常号数を有効な32進自然数列として検査し、どちらも正であることを要求する。その同じ数値・系列・暦・文脈を、慣行上の刊行方針へ結ぶ。比率が等しい別の周期と号数へ自動換算しない。',
    'rqw5': '同じ刊行系列と文脈について、指定人物の編集上の責任とrqw4の刊行方針を結ぶ。別系列の責任や別文脈の周期を混ぜない。',
    'hzwe': 'Büschingへの人物参照hzwcと既存の暦hzixを固定し、編集上の責任と、暦上の7日周期に通常1号という刊行方針を持つ系列の性質。実際の欠刊や号の表示日付とは別である。',
    'hzwf': '脚注で既に参照する刊行系列hzkdと同一である対象を選ぶ性質。人物や特定の号を系列へ置き換えない。',
    'hzwg': '同じ脚注の名称使用hzkjで人物の名称hzwdをhzwcへ、既存の系列名hzkeをhzkdへ結び、著者がその系列をhzweの性質で記述することを述べる。記述の使用から刊行方針や編集責任の現実の成立を補わない。',
}
LIMITS = [
    'Büsching’schen wöchentlichen Nachrichtenを、固有の刊行系列を、人物への編集上の帰属と名目的な週刊周期で指す呼び方として読む。単なる名称の文字列から関係を推定する規則は作らない。',
    '原刊週報の表題に人物名と週刊の表示があり、版元は別の行にあることを確認した。編集上の責任という読みであり、現代の編集長職、全記事の単独著作、刊行費用負担や法的所有を追加しない。',
    '7日周期に1号という方針は、14日周期に2号という平均の同じ方針と区別する。欠刊・特別号・発行日のずれを排除しない。周期の位相、日曜日始まり、月曜日発行、1日86400秒を原文へ補わない。',
    'hzwaとhzwbは刊行制度の一般関係、hzwhは人・物を対象とする呼称内の記述の使用を表す一般関係である。刊行制度の全社会理論や、暦日の物理的な長さを証明するものではない。週刊専用の真偽記号や対訳辞書を追加しない。',
    'hzwgは呼称内で使う記述を保持する。現実の人物属性を呼称から推定しない既存の敬称と同様に、記述を実際に評価する場合と区別する。',
    '名称の全表題、原刊の号数・頁数・人物の名の展開・版元は原文への追加主張にしない。名前の綴りと参照対象は別添えの識別表記で管理する。',
    '既存41文を保存して著者注の記述を一文補足する。偶発性と思想の一致の基準、著者注全体および両作品全文の意味確認は残る。',
]


@lru_cache(None)
def parent():
    return load_catalog(ROOT, PARENT_BASIS)


def definitions():
    text = ''.join('r ' + n + sig + '.' for n, (sig, _, _) in PRIMITIVES.items())
    fields = 'series a calendar a days j[b] issues j[b] context d cadence h[a a b b d] c'
    args = 'v series v calendar v days v issues v context v cadence'
    text += 'd rqw4[' + fields + '] c[' + both(
        'k rqse[v days]', 'k rqse[v issues]',
        'k hc[n p a b k rqsf[v days]]', 'k hc[n p a b k rqsf[v issues]]',
        'c[v cadence][v series v calendar k rqsf[v days] k rqsf[v issues] v context]') + '].'
    text += 'd rqw5[person a ' + fields + ' responsible h[a a d] c] c[' + both(
        'c[v responsible][v person v series v context]', 'k rqw4[' + args + ']') + '].'
    text += 'd hzwe[series a] e[b context[k rqw5[k hzwc[] v series k hzix[] ' + seq([7]) + ' ' + seq([1]) + ' v context p hzwa p hzwb]]].'
    text += 'd hzwf[series a] e[b context[e[v series][k hzkd[]]]].'
    text += 'd hzwg[] c[' + both(
        'u[e[k hzwd[]][k hzwc[]]]', 'u[e[k hzwc[]][k hzkd[]]]',
        'k dg[k hzkj[] k hzjl[]]',
        'k hzih[k hzkj[] k hzwd[] k hzwc[] k hzjl[]]',
        'k hzih[k hzkj[] k hzke[] k hzkd[] k hzjl[]]',
        'k rq[k wa[] k hzkj[] r[p hzwf] r[p hzwe] k hzjl[] p hzwh]') + '].'
    return text


def build():
    old = parent()
    assert not (set(MEANINGS) | set(PRIMITIVES)) & set(old.entries)
    doc = deepcopy(old.document)
    statements, doc['statements'] = doc['statements'], []
    size = len(doc['declarations'])
    doc = parse(format_graph(doc, 'compact') + definitions() + 's[k hzwg[]].')
    doc['statements'] = statements + doc['statements']
    core = deepcopy(doc)
    core['declarations'] = closure(doc, ['hzwg', 'hzwe', 'rqw4', 'rqw5'])
    core['statements'] = doc['statements'][-1:]
    lib = deepcopy(core)
    lib['declarations'] = closure(doc, ['rqw4', 'rqw5'])
    lib['statements'] = []
    primitives = {}
    for declaration in doc['declarations'][size:]:
        if declaration['kind'] == 'primitive':
            name = declaration['name']
            _, labels, meaning = PRIMITIVES[name]
            primitives[name] = dict(parameters=declaration['parameters'], result=declaration['result'], arguments=labels, meaning_ja=meaning)
    basis = dict(status='editorial_association_and_nominal_calendar_cadence_in_designation', document=FULL, library=LIBRARY,
        parent=PARENT, inherited_meaning_basis=PARENT_BASIS, primitives=primitives, definitions=MEANINGS,
        new_signatures={d['name']: {k: d[k] for k in ('parameters', 'result')} for d in doc['declarations'][size:]}, limitations=LIMITS)
    body = format_graph(doc, 'compact') + '\n'
    ann = json.loads((ROOT / 'data/explanatory-question-identifiers-v1.json').read_text(encoding='utf-8'))
    ann.update(document=FULL, document_sha256=digest(body.encode('utf-8')))
    ann['entries'].append(dict(symbol='hzwd', role='designation', forms=[dict(text='Büsching', language='de', role='uninflected_person_designation')]))
    encoded = lambda value: json.dumps(value, ensure_ascii=False, indent=2) + '\n'
    return {FULL: body, CORE: format_graph(core, 'compact') + '\n', LIBRARY: format_graph(lib, 'compact') + '\n',
        BASIS: encoded(basis), ANNOTATIONS: encoded(ann)}


def main():
    for name, body in build().items():
        path = ROOT / name
        if path.exists():
            assert path.read_text(encoding='utf-8') == body, name
        else:
            with path.open('x', encoding='utf-8', newline='\n') as stream:
                stream.write(body)
    print('Periodical description composed separately from its title and publication history', flush=True)


if __name__ == '__main__':
    main()
