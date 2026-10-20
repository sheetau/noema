"""Compose standing instruction across tasks, audiences and alternative acts."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT, closure
from scripts.compose_qualitative_influence import both, TRUE
from scripts.compose_protected_remarks import bind
from scripts.compose_confessional_teaching import NAMES, FIELDS, ARGS, MESSAGE, STANDARD

PARENTS = ('data/ranked-appointment-basis-v1.json', 'data/public-civic-opinion-basis-v1.json')
LIBRARY = 'examples/v016/teaching-policy.noema'
BASIS = 'data/teaching-policy-basis-v1.json'
TASK = 'k h246n[v person v role v church v subject v occasion v reference]'
RECIPIENT = 'k h246o[v occasion v recipient v reference]'
AUDIENCE = 'x[k h6t[v students v recipient v reference]][k h6t[v members v recipient v reference]]'
CRITERIA = 'k h246j[v standard v reference]'
PRIMITIVES = {
    'h246n': ('[a a a a a d] c', ['person', 'role', 'organization', 'subject', 'occasion', 'reference'],
        '固定した基準で、この人・職務・組織・主題に属する教示の担当機会・任務の完全な範囲に、この機会が属する。単一の実行活動とは分け、同じ任務に複数の代替活動や追加の講説を含められる。実行済み・適合・成功・許可によって任務を選び直さず、不実行の任務も含める。機会を期間枠としてh7q/h7rへ渡し、採用解釈における教示時機を固定する。要求そのものは別に構成する。'),
    'h246o': ('[a a d] c', ['occasion', 'recipient', 'reference'],
        'この教示任務で担当する受け手の完全な範囲にこの人が含まれる。基準で固定した生徒・会衆全体から、各任務の宛先を割り当てる。実際の出席、理解、教示済みを範囲の条件にせず、不在者を結果に合わせて除外しない。全体範囲との包含・非空性・全宛先の担当網羅は定義側で結ぶ。'),
    'h246p': ('[a a d] c', ['occasion', 'activity', 'reference'],
        'この任務に属する教示活動の候補の完全な範囲にこの活動が含まれる。代替方法と追加の職務上の講説を含め、実行・基準適合・受け手への到達によって分類を取り消さない。同じ人の職務外の学識者としての発言とは分ける。候補全ての実行を要求する関係ではない。'),
}
MEANINGS = {
    'r355': '同じ聖職者・教会・信条・完全な二宛先の設定r35tについて、同じ担当任務h246nの宛先h246oが非空で、全て元の生徒または会衆成員に含まれる。任務や宛先を実行の成否で選ばない。',
    'r356': '同じ任務r355に属する活動h246pが、担当宛先に同じ主題・発話を説明的に提示し、同じ教会の採用基準を満たす実行内容。rfwの生起・委任・奉仕・採用・全宛先提示を再利用するが、毎回元の二集団全員へ同じ講義を要求せず、その任務の非空宛先に限定する。',
    'r357': '同じ任務の候補活動で、同じ本人が同じ主題・発話を説明・教示し、担当宛先の少なくとも一人へ実際に提示したこと。生起dg、提示者f3、説明h246lと提示f2を結び、基準適合や他の宛先全員への到達を前提にしない。',
    'r36a': '同じ設定・活動・発話について、同じ本人の職務委任・奉仕・職務としての活動位置付け、同じ信条の同じ閉じた条件列の採用を評価時にも確認し、その列の全基準rfuを満たす。内容の真理や本人の確信を自動条件にしない。',
    'r36b': '同じ任務の全活動と全型適合発話記述について、実際の教示r357があれば同じ活動・発話がr36aを満たす内容。一つの適合する講義や発話の存在で、別の不適合な追加教示を覆い隠さない。',
    'r36c': '同じ任務の期間枠を候補経過で解釈し、tbによる非空で整合した期間を保つ。その期間内に担当宛先への適合した教示r356が少なくとも一つあり、期間内の全点で全ての実際の教示がr36bを満たす。全候補活動の実行や全時点の連続講義は要求しない。',
    'r36d': '同じr35tの設定で、担当任務の範囲が非空、二宛先全員が少なくとも一つの任務に割り当てられ、全任務についてr36cの教示方針を満たす内容。生徒と会衆を別の機会に教示でき、同じ機会に重複所属する人も許す。',
    'r36e': '本人・職務・教会・会衆・生徒範囲・会衆成員範囲・信条・主題・基準の正確な九個体列と固定基準点をr36dの一般的な教示方針へ接続する閉じた段階1の目標。任意の一活動を固定しない。',
    'r36f': '同じ教会から本人・職務へ、r36eの一般的な教示方針を正極性で要求する内容。引用した方針は実行せず、現実の講義やその適合を要求の存在から導かない。',
    'r36g': '同じ教会による同じ本人・職務の過去任用に、r36fと同じ方針記述・九個体列・内容基準・正極性が条件として付されていた内容。任用関係r35yを再利用する。',
    'r36h': '一般的な教示方針について、r36fの現在要求とr36gの同じ過去任用条件をr35zへ接続する。個別活動への条件を単に寄せ集めず、一つの方針記述を同じ任用行為へ結ぶ。dennの説明関係は別に保持する。',
}
LIMITS = [
    'u0012[2984,3185)の職務上の一般的教示義務のための依存群。本文、意味確認文字数、全文帰属は更新しない。dennとEben soの談話関係は未統合。',
    'Vortragは継続する職務上の教示として読む。原文に日時や回数を補わず、担当機会・担当宛先・所属活動の完全な範囲を基準で明示する。各任務の適用時機はh7q/h7rの同じ期間枠で扱い、法的・制度的な正当性や網羅性を検査例だけから証明しない。',
    '各担当機会に少なくとも一つの適合した提示を求め、期間内のその任務に属する実際の説明・教示は全て基準適合を求める。実行をしないだけでは前者を満たさず、追加の不適合な教示を一つの適合例で相殺しない。受け手の理解、本人の信仰、教義の真理は要求しない。',
    '一回の講義で生徒と会衆の全員へ同じ話をする必要はない。各担当機会の宛先は元の二範囲の部分集合とし、全体の担当網羅を別に要求する。重複担当を禁じず、異なる機会で同じ活動を共有することも原文にない不等式で排除しない。',
    '宛先・信条・主題・基準は今回の職務事例の固定基準に対して記述する。異なる時期の職務構成や後続の辞職・良心・変更を同じ固定設定へ混ぜず、必要な箇所で別に構成する。',
    '実際の教示についての全発話記述域とその存在量化を保持する。有限評価器の全域拒否を維持し、有限の二発話へ制限した診断用試験を全域の証明として扱わない。',
]


@lru_cache(None)
def parents(): return tuple(load_catalog(ROOT, p) for p in PARENTS)


def definitions():
    taskfields, taskargs = FIELDS + ' occasion a', ARGS + ' v occasion'
    fields, args = taskfields + ' activity a message ' + MESSAGE, taskargs + ' v activity v message'
    text = 'd r355[' + taskfields + '] c[' + both('k r35t[' + ARGS + ']', TASK,
        'g recipient a[' + RECIPIENT + ']', 'f recipient a[y[' + RECIPIENT + '][' + AUDIENCE + ']]') + '].\n'
    audiences = ' '.join('i[recipient a][' + both('k h6t[v ' + n + ' v recipient v reference]', RECIPIENT) + ']'
        for n in ('students', 'members'))
    adoption = 'i[organization a rule a criteria ' + STANDARD + ' at d][k h246i[v organization v creed v rule v criteria v at]]'
    teaching = 'c[k rfw[v church v role v standard ' + audiences + ' v subject v message ' + CRITERIA + (
        ' p h246k ' + adoption + ' p cb p cf p dg p f3 p f2]][v person v activity]')
    common = ['k r355[' + taskargs + ']', 'k h246p[v occasion v activity v reference]',
        'k h246l[v person v activity v subject v message v point]']
    text += 'd r356[' + fields + '] e[b point[' + both(*common, 't[' + teaching + '][v point]') + ']].\n'
    text += 'd r357[' + fields + '] e[b point[' + both(*common, 'k dg[v activity v point]',
        'k f3[v person v activity v point]', 'g recipient a[' + both(RECIPIENT,
            'k f2[v activity v recipient v subject v message v point]') + ']') + ']].\n'
    text += 'd r36a[' + FIELDS + ' activity a message ' + MESSAGE + '] e[b point[' + both(
        'k r35s[v church v creed v subject v standard v reference]', 'k h246k[v person v church v role v point]',
        'k cf[v person v role v point]', 'k cb[v person v activity v role v point]',
        'k h246i[v church v creed v standard ' + CRITERIA + ' v point]',
        't[k rfu[v subject v message s[' + CRITERIA + ']]][v point]') + ']].\n'
    text += 'd r36b[' + taskfields + '] e[b point[f activity a[f message ' + MESSAGE + '[y[' + (
        't[k r357[' + args + ']][v point]') + '][t[k r36a[' + ARGS + ' v activity v message]][v point]]]]]].\n'
    interval = 'k tb[i[at d][k h7q[v occasion v candidate v at]] i[at d][k h7r[v occasion v candidate v at]] i[first d last d][k ic[v first v last v candidate]]]'
    positive = 'g at d[' + both('k h7r[v occasion v candidate v at]',
        'g activity a[g message ' + MESSAGE + '[t[k r356[' + args + ']][v at]]]') + ']'
    uniform = 'f at d[y[k h7r[v occasion v candidate v at]][t[k r36b[' + taskargs + ']][v at]]]'
    text += 'd r36c[' + taskfields + '] e[b candidate[' + both('k r355[' + taskargs + ']', interval, positive, uniform) + ']].\n'
    text += 'd r36d[' + FIELDS + '] e[b candidate[' + both('k r35t[' + ARGS + ']', 'g occasion a[' + TASK + ']',
        'f recipient a[y[' + AUDIENCE + '][g occasion a[' + both(TASK, RECIPIENT) + ']]]',
        'f occasion a[y[' + TASK + '][t[k r36c[' + taskargs + ']][v candidate]]]') + ']].\n'
    text += 'd r36e[bindings j[a] reference d] e[b candidate[' + bind(NAMES,
        't[k r36d[' + ARGS + ']][v candidate]') + ']].\n'
    concrete = 'v church v person v role r b[p r36e] l[a][' + ' '.join('v ' + n for n in NAMES) + '] v reference ' + TRUE + ' v point'
    for name, target in [('r36f', 'h237z'), ('r36g', 'r35y'), ('r36h', 'r35z')]:
        text += 'd ' + name + '[' + FIELDS + '] e[b point[k ' + target + '[' + concrete + ']]].\n'
    return text


def build():
    old, temporal = parents(); doc = deepcopy(old.document)
    doc.update(declarations=closure(doc, ['r35t', 'rfw', 'r35y', 'r35z', 'h246l', 'f2', 'f3', 'cb']), statements=[])
    imported = {d['name']: old.entries[d['name']] for d in doc['declarations']}
    for d in closure(temporal.document, ['tb', 'h7q', 'h7r']):
        n = d['name']
        if n in imported:
            assert d == imported[n]['declaration'] and temporal.entries[n]['meaning_ja'] == imported[n]['meaning_ja']
        else: doc['declarations'].append(d); imported[n] = temporal.entries[n]
    assert not (set(PRIMITIVES) | set(MEANINGS)) & set().union(*(set(p.entries) for p in parents()))
    doc = parse(format_graph(doc, 'compact') + ''.join('r ' + n + row[0] + '.' for n, row in PRIMITIVES.items()) + definitions())
    ds = {d['name']: d for d in doc['declarations']}
    primitives = {n: dict(parameters=e['declaration']['parameters'], result=e['declaration']['result'], arguments=e['arguments'],
        meaning_ja=e['meaning_ja']) for n, e in imported.items() if e['kind'] == 'primitive'}
    primitives.update({n: dict(parameters=ds[n]['parameters'], result=ds[n]['result'], arguments=row[1], meaning_ja=row[2])
        for n, row in PRIMITIVES.items()})
    sources = set().union(*(set(c.source_sha256) for c in parents()))
    basis = dict(status='standing_teaching_policy_with_tasks_and_all_actual_expositions', document=LIBRARY, primitives=primitives,
        definitions={n: e['meaning_ja'] for n, e in imported.items() if e['kind'] == 'definition'} | MEANINGS,
        imported_symbols={n: e['meaning_basis'] for n, e in imported.items()},
        import_source_sha256={p: digest((ROOT / p).read_bytes()) for p in sorted(sources)}, limitations=LIMITS)
    return {LIBRARY: format_graph(doc, 'compact') + '\n', BASIS: json.dumps(basis, ensure_ascii=False, indent=2) + '\n'}
