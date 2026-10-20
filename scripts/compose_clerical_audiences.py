"""Bind a clerical role and its pupils and congregation to one institution."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT, closure
from scripts.compose_qualitative_influence import both

PARENT = 'data/public-civic-opinion-basis-v1.json'
LIBRARY = 'examples/v016/clerical-audiences.noema'
BASIS = 'data/clerical-audiences-basis-v1.json'
PRIMITIVES = {
    'h245x': ('[a a d] c', ['course', 'subject', 'reference'],
        'この学習課程が同じ主題の初歩・基礎を理解させるための体系的な教授に位置付けられている。実際の一回の発話、学習の達成、全専門知識の教授とは分ける。主題・課程・固定基準を保持する。'),
    'h245y': ('[a d] c', ['course', 'reference'],
        '同じ課程の教授内容が、問いを置きそれに対応する答えを示す問答の形式で組織されている。偶然質問が出た授業、受け手が自由に論じること、単に疑問符があることとは区別する。各問答の実行・内容の真理や暗記の達成は要求しない。'),
    'h245z': ('[a d] c', ['subject', 'reference'],
        'この主題は宗教上の信仰・生活・実践の基礎となる教えに関するもの。地理・会計等の一般的知識だけとは区別する領域指定である。特定の宗派・神学説、その教えの真理、本人の信仰を含意しない。'),
    'h246a': ('[a a a a a d] c', ['teacher', 'role', 'institution', 'learner', 'course', 'reference'],
        '同じ制度的な教育関係において、指定の学習者が、この組織におけるこの役割の担い手から、同じ課程の教授を受ける生徒として位置付けられる。偶然の聴衆、別の教師の生徒、過去一回の受領や現在の学習成果とは区別する。所属や担当を成績・同意によって選び直さない。'),
    'h246b': ('[a a a a i[h[a] e] d] c',
        ['provider', 'role', 'group', 'institution', 'member_activity', 'reference'],
        'この組織・役割の同じ担い手に、この成員集団について、指定された各成員の活動への配慮・指導が制度・慣行上委ねられている。単なる同席、組織内の別集団の担当、全世界の人への一般的助言とは分ける。集団の所有、実際の指導や成功、成員全員の信念一致を意味しない。'),
    'h246c': ('[a a d] c', ['group', 'member', 'reference'],
        'この固定基準で、この人が指定された成員集団に属している。会場での同席、当日の出席、発話の受領、政治的な市民権とは区別する。集団の全ての該当成員について同じ関係を使い、都合のよい受け手だけを選ばない。'),
}
MEANINGS = {
    'r35m': '既存spで存在量化していた聖職者の役割・共同体を引数で固定する。rqxmの継続的な宗教上の援助者であり、その同じ役割でsoへの援助が主要な務めで、同じ教会組織から任用され、同じ組織の公的宗教奉仕hzxiを担う責務がある。別の役割・共同体の証人を混ぜない。',
    'r35n': '同じ課程が、指定の宗教上の基礎的な教えを主題とする初歩の教授h245x/h245zであり、問答の形式h245yを持つ。教理問答の学習課程として採る読み。特定の教理内容の真理や教材の物理的な所持を要求しない。',
    'r35o': '人である同じ学習者が、同じ本人・役割・組織からr35nの課程を学ぶ生徒h246aである。課程と宗教上の主題は同じ存在証人を共有する。単に公衆の受け手であることだけで生徒とはしない。',
    'r35p': '人であり、同じ固定基準で指定の成員集団に属する者。宗教的な会衆としての担当関係はr35qで同じ聖職者・教会・役割へ結ぶ。当日の出席者だけに限定しない。',
    'r35q': '同じ聖職者・役割・教会r35mと、その人にsoへの配慮を委ねた同じ会衆集団h246bを結ぶ。二つの宛先範囲h6tが、それぞれ本人の教理問答の生徒r35o全員と、同じ会衆の成員r35p全員に正確に一致することを全個体で要求する。範囲を実行時の受領や理解で選ばず、両範囲の重なりを許す。',
}
LIMITS = [
    'u0012[2984,3185)の聖職者と二つの受け手範囲を同じ制度的関係へ結ぶ依存群。教会の信条、教示の実行内容、義務、同じ条件での過去任用、dennとEben so、全文帰属は未統合。新規意味確認文字数は加算しない。',
    'Geistlicherは既存spの明示した読みを保持し、存在証人の役割・組織を固定する。教会の共同組織としての分類は後続の信条・教示基準の構成で接続する。この群だけでKircheの全語義を説明済みとはしない。',
    'Katechismusschülerは、問答体による宗教の初歩の教授を受ける生徒という読み。物理的な本の所持、特定版、洗礼・堅信礼の前後、年齢を勝手に指定しない。Gemeineは同じ聖職者の配慮・指導に委ねられた集団として読む。',
    '二つの宛先を和集合へまとめる前に、各範囲が完全であることを別々に固定する。同じ人が両方に属する場合を排除せず、余計な第三者や一人の取りこぼしは拒否する。',
    '範囲を指定するこの構成自体は、現に授業が行われることや非空の出席者を要求しない。非空宛先への実際の教示は後続の活動内容で扱い、範囲の空から教示が済んだとはしない。',
    '基本関係は領域・学習課程・形式・教育上の担当・集団への配慮・成員所属を別々に説明する。同じ文の真偽を一つの入力で返す関係は追加しない。採用した歴史語義の根拠はdata/clerical-teaching-lexical-v1.jsonに保存する。',
]


@lru_cache(None)
def parent(): return load_catalog(ROOT, PARENT)


def definitions():
    text = 'd r35m[person a role a church a reference d] c[' + both(
        'k rqxm[v person v reference]', 'k hzwn[v person v role v reference]',
        'k hzwo[v role r[p so] v reference]', 'k hzwu[v role r[p so] v reference]',
        'k hzxf[v person v role v church v reference]', 'k hzxg[v role r[p hzxi] v church v reference]') + '].\n'
    text += 'd r35n[course a subject a reference d] c[' + both(
        'k h245x[v course v subject v reference]', 'k h245y[v course v reference]', 'k h245z[v subject v reference]') + '].\n'
    text += 'd r35o[person a role a church a learner a reference d] c[' + both('k aa[v learner]',
        'g course a[g subject a[' + both('k r35n[v course v subject v reference]',
            'k h246a[v person v role v church v learner v course v reference]') + ']]') + '].\n'
    text += 'd r35p[group a member a reference d] c[' + both('k aa[v member]', 'k h246c[v group v member v reference]') + '].\n'
    text += 'd r35q[person a role a church a congregation a students a members a reference d] c[' + both(
        'k r35m[v person v role v church v reference]',
        'k h246b[v person v role v congregation v church r[p so] v reference]',
        'f recipient a[' + both(
            'e[k h6t[v students v recipient v reference]][k r35o[v person v role v church v recipient v reference]]',
            'e[k h6t[v members v recipient v reference]][k r35p[v congregation v recipient v reference]]') + ']') + '].\n'
    return text


def build():
    old = parent(); doc = deepcopy(old.document)
    doc.update(declarations=closure(doc, ['rqxm', 'hzwn', 'hzwo', 'hzwu', 'hzxf', 'hzxg', 'hzxi', 'so', 'h6t']), statements=[])
    imported = {d['name']: old.entries[d['name']] for d in doc['declarations']}
    assert not (set(PRIMITIVES) | set(MEANINGS)) & set(old.entries)
    doc = parse(format_graph(doc, 'compact') + ''.join('r ' + n + row[0] + '.' for n, row in PRIMITIVES.items()) + definitions())
    ds = {d['name']: d for d in doc['declarations']}
    primitives = {n: dict(parameters=e['declaration']['parameters'], result=e['declaration']['result'], arguments=e['arguments'],
        meaning_ja=e['meaning_ja']) for n, e in imported.items() if e['kind'] == 'primitive'}
    primitives.update({n: dict(parameters=ds[n]['parameters'], result=ds[n]['result'], arguments=row[1], meaning_ja=row[2])
        for n, row in PRIMITIVES.items()})
    basis = dict(status='same_clerical_role_and_complete_pupil_congregation_ranges', document=LIBRARY, primitives=primitives,
        definitions={n: e['meaning_ja'] for n, e in imported.items() if e['kind'] == 'definition'} | MEANINGS,
        imported_symbols={n: e['meaning_basis'] for n, e in imported.items()},
        import_source_sha256={p: digest((ROOT / p).read_bytes()) for p in sorted(old.source_sha256)}, limitations=LIMITS)
    return {LIBRARY: format_graph(doc, 'compact') + '\n', BASIS: json.dumps(basis, ensure_ascii=False, indent=2) + '\n'}
