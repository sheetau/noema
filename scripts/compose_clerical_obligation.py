"""Integrate clerical teaching duty and its stated appointment explanation."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT, closure
from scripts.compose_qualitative_influence import both
from scripts.compose_civic_example import quantify
from scripts.compose_confessional_teaching import NAMES

PARENT = 'examples/v016/kant-public-civic-opinion.noema'
PARENT_BASIS = 'data/public-civic-opinion-basis-v1.json'
DEPENDENCIES = ('data/teaching-policy-basis-v1.json',)
FULL = 'examples/v016/kant-clerical-obligation.noema'
CORE = 'examples/v016/clerical-obligation-core.noema'
BASIS = 'data/clerical-obligation-basis-v1.json'
ANNOTATIONS = 'data/clerical-obligation-identifiers-v1.json'
PRIMITIVES = {
    'h246q': ('[] a', [], '固定原文kant-1784:u0012[2984,3185)、Eben so ist ein Geistlicherからangenommen worden.までの聖職者の教示義務と任用条件を述べる一文全体。'),
    'h246r': ('[] a', [], '同じ一文の[2984,3134)、Eben soからseinen Vortrag zu thun;までの、同じ教会に仕える聖職者の教示義務の主節。'),
    'h246s': ('[] a', [], '同じ一文の[3135,3185)、denn er ist auf diese Bedingung angenommen worden.という、同じ教示条件での過去任用を理由として提示する節。'),
}
MEANINGS = {
    'r36i': '第五段落の固定基準h232vで、同じ九個体を持つ全ての職務事例r35tに、教示方針への正の要求r36fがあるという主節の内容。一人の唯一の実在者や一回の任意の講義に限定せず、実際の履行・本人の信仰・教義の真理は要求しない。',
    'r36j': 'r36iと同じ基準・九個体の全職務事例について、r36gの同じ方針記述・束縛・基準・正極性を条件とする過去の任用がある内容。erとdiese Bedingungを同じ本人・役割・教会と同じ一般教示方針へ保持する。',
    'r36k': '同じ評価点で教示義務の主節r36iと過去任用の理由節r36jを合わせた一文全体の内容。前者の実在を後者から推論する規則にはせず、著者の説明は帰属側で別に保持する。',
    'r36l': '一文全体・主節・理由節を同じ著者waと第五段落の提示文脈h232oへ帰属する。udで任用の理由節を教示義務の根拠として提示し、h245mで先行する市民の制約例と並列する。直前の公的見解の文からの順序と主節から理由節への順序を保持し、引用内容の真理は実行しない。',
}
LIMITS = [
    'ein Geistlicherは聖職者の一般的職務事例として、同じ役割・教会・二宛先・信条・主題・基準を持つ全事例への条件付き全称で読む。実在する唯一の人物や、本人の私的な信仰の確実性を加えない。',
    'Katechismusschülerは同じ本人・職務・組織に結ぶ初歩的な宗教の問答教授の生徒、Gemeineは同じ職務で配慮を委ねられた宗教上の会衆という読み。単なる当日の出席者や政治的市民へ置換しない。保存したAdelung語義は補助根拠であり唯一の歴史的解釈の証明ではない。',
    'Symbolは同じ教会が共同の立場として採用した信条、Kircheはその教えと宗教的実践を持つ組織と読む。信条内容と教示基準はNoemaの閉じた記述であり、教義の真理・本人の確信・成員全員の私的な信念一致を要求しない。der er dientは同じ本人・職務・教会への奉仕を保持する。',
    'verbundenは制度上の教示義務、Vortragは継続する職務上の説明・教示とする。各担当機会に少なくとも一つの基準に沿う教示を求め、その期間内の実際の説明も全て同じ基準に適合させる一般方針r36eを要求対象にする。一回の任意の講義、単なる中立的引用、全候補活動の実行へ縮約しない。',
    '担当機会・宛先・候補活動の完全な範囲を固定し、不実行・不適合を理由に除外しない。生徒と会衆を別々の機会に教示すること、複数の代替方法や重複担当を許す。全宛先の担当網羅と各期間の非空・整合を保ち、原文に日時・回数・具体的な教義を補わない。範囲の現実への適用は明示解釈の責任である。',
    'auf diese Bedingung angenommen wordenは、同じ教会による本人の同じ職務への過去任用に、現在の要求と同じ一般方針・九個体列・内容基準・正極性が付されたという読み。任用行為・過去時点を同じ証人へ結び、別の任用や条件を寄せ集めない。本人の承諾、採用前の履行済み、法的正当性や任命者名は補わない。',
    'dennは著者が同じ条件での任用を教示義務の説明として提示する関係であり、任用事実から現在の義務を自動導出する普遍法則、因果の証明、説明の十分性とはしない。主節と理由節の世界内容と、根拠として提示する談話関係をともに保つ。',
    'Eben soは先行する市民の役割上の制約例と同様に、聖職者の職務上の制約を示す並列と読む。直前の学識者としての公的見解の不違反を、聖職者の教示義務の根拠や同じ内容へ取り違えない。本文順序はその直前文から接続する。',
    '意味判断は原刊と依存定義の通読による、明示解釈下のアシスタントの判断である。全発話記述域は保持して有限評価を拒否し、局所実評価、型付き境界での量化接続、有限診断例を区別する。独立査読、同義性の自動証明、教会制度や規範の正当化ではない。',
]


@lru_cache(None)
def parent(): return load_catalog(ROOT, PARENT_BASIS)


@lru_cache(None)
def dependencies(): return tuple(load_catalog(ROOT, p) for p in DEPENDENCIES)


def definitions():
    args = ' '.join('v ' + n for n in NAMES) + ' k h232v[]'
    text = ''
    for name, target in [('r36i', 'r36f'), ('r36j', 'r36g')]:
        text += 'd ' + name + '[] e[b point[' + quantify(NAMES,
            'y[k r35t[' + args + ']][t[k ' + target + '[' + args + ']][v point]]') + ']].\n'
    text += 'd r36k[] e[b point[' + both('t[k r36i[]][v point]', 't[k r36j[]][v point]') + ']].\n'
    author, ctx = 'k wa[]', 'k h232o[]'
    quote = lambda n: 'r d[k ' + n + '[]]'
    claims = ['k h236i[k ' + node + '[] ' + author + ' ' + quote(content) + ' ' + ctx + ']'
        for node, content in [('h246q', 'r36k'), ('h246r', 'r36i'), ('h246s', 'r36j')]]
    claims += ['k ud[' + author + ' i[node a][e[v node][k h246s[]]] k h246r[] ' + ctx + ']',
        'k h245m[k h246q[] ' + author + ' k h245f[] ' + quote('r34x') + ' ' + quote('r36k') + ' ' + ctx + ']',
        'k ue[k h245u[] k h246q[] ' + ctx + ']', 'k ue[k h246r[] k h246s[] ' + ctx + ']']
    claims += ['u[e[k ' + first + '[]][k ' + last + '[]]]' for first, last in (
        ('h245u', 'h246q'), ('h246q', 'h246r'), ('h246q', 'h246s'), ('h246r', 'h246s'))]
    text += 'd r36l[] c[' + both(*claims) + '].\n'
    return text


def build():
    old = parent(); doc = deepcopy(old.document); statements, doc['statements'] = doc['statements'], []; imported = {}
    for lib in dependencies():
        for d in lib.document['declarations']:
            n = d['name']; previous = old.entries.get(n, imported.get(n))
            if previous: assert d == previous['declaration'] and lib.entries[n]['meaning_ja'] == previous['meaning_ja'], n
            else: doc['declarations'].append(d); imported[n] = lib.entries[n]
    assert not (set(PRIMITIVES) | set(MEANINGS)) & (set(old.entries) | set(imported))
    doc = parse(format_graph(doc, 'compact') + ''.join('r ' + n + row[0] + '.' for n, row in PRIMITIVES.items()) + definitions())
    added = doc['declarations'][len(old.document['declarations']):]
    new = dict(kind='assert', body=dict(kind='call', symbol='r36l', arguments=[])); doc['statements'] = statements + [new]
    core = deepcopy(doc); core.update(declarations=closure(doc, list(MEANINGS)), statements=[new]); ds = {d['name']: d for d in added}
    meanings = {n: e['meaning_ja'] for n, e in imported.items() if e['kind'] == 'definition'} | MEANINGS
    primitives = {n: dict(parameters=ds[n]['parameters'], result=ds[n]['result'], arguments=e['arguments'], meaning_ja=e['meaning_ja'])
        for n, e in imported.items() if e['kind'] == 'primitive'}
    primitives.update({n: dict(parameters=ds[n]['parameters'], result=ds[n]['result'], arguments=row[1], meaning_ja=row[2]) for n, row in PRIMITIVES.items()})
    sources = set().union(*(set(lib.source_sha256) for lib in dependencies()))
    basis = dict(status='clerical_teaching_duty_with_same_appointment_explanation', document=FULL, parent=PARENT, inherited_meaning_basis=PARENT_BASIS,
        definitions=meanings, primitives=primitives, new_signatures={d['name']: {k: d[k] for k in ('parameters', 'result')} for d in added},
        imported_symbols={n: e['meaning_basis'] for n, e in imported.items()},
        import_source_sha256={p: digest((ROOT / p).read_bytes()) for p in sorted(sources)}, limitations=LIMITS)
    body = format_graph(doc, 'compact') + '\n'; annotations = json.loads((ROOT / 'data/public-civic-opinion-identifiers-v1.json').read_text(encoding='utf-8'))
    annotations.update(document=FULL, document_sha256=digest(body.encode('utf-8')))
    enc = lambda v: json.dumps(v, ensure_ascii=False, indent=2) + '\n'
    return {FULL: body, CORE: format_graph(core, 'compact') + '\n', BASIS: enc(basis), ANNOTATIONS: enc(annotations)}
