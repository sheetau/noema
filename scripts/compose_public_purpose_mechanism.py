"""Join the institution's prescribed conduct to its shared public purpose."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT, closure
from scripts.compose_qualitative_influence import both
from scripts import compose_institutional_coordination as coordination

PARENT = 'examples/v016/kant-mechanism-requirements.noema'
PARENT_BASIS = 'data/mechanism-requirements-basis-v1.json'
FULL = 'examples/v016/kant-public-purpose-mechanism.noema'
CORE = 'examples/v016/public-purpose-mechanism-core.noema'
BASIS = 'data/public-purpose-mechanism-basis-v1.json'
ANNOTATIONS = 'data/public-purpose-mechanism-identifiers-v1.json'
FAMILY = 'i b[h[a d] e]'
PERSON_FAMILY = 'i b[h[a a d] e]'
PRIMITIVES = {
    'h237k': ('[a d] i[e]', ['work', 'reference'],
              '同じ事務・基準で取り上げる目的内容をまとめた閉じた記述。公的かどうかはh237lで別に検査する。目標の実現・実現可能性、全員の私的意図との一致を含意しない。方向付けと破壊の抑止に同じ記述を渡し、結果の良否で目的を取り替えない。原文が特定していない個別の政策目標をここで創作しない。'),
    'h237l': ('[i[e] a a d] c', ['goal', 'community', 'work', 'reference'],
              'この閉じた内容が、同じ共同体の同じ事務を運営するための公的な目標として置かれている。政府関係者個人の私的利益だけや、実際に偶然生じた結果とは分ける。全住民の同意、目標の正当性、達成は要求しない。'),
    'h237m': ('[a d] a', ['work', 'reference'],
              '同じ事務の説明で扱う政府の参照。組織としての政府を人間一人の意図へ置換しない。管轄関係はh237nで別に検査し、全世界で唯一の政府とはしない。'),
    'h237n': ('[a a d] c', ['government', 'community', 'reference'],
              'この政府が同じ政治的共同体の公的な運営・執行を指揮する制度上の立場にある。肩書だけの人物や私的な希望とは分ける。特定の君主制、道徳的正当性、あらゆる命令の実際の遵守は含意しない。'),
    'h237o': ('[a a d] a', ['mechanism', 'work', 'reference'],
              '同じ機構・事務について目的内容で用いる協調の配置。本文内で同じ配置を追跡する参照であり、存在するだけで人為性・協調・作用の成功を認定しない。'),
    'h237p': ('[a h[a] c a d] c', ['arrangement', 'people', 'work', 'point'],
              'この配置によって、指定された人々の同じ事務での振る舞いが、共通の執行の方向に整合するよう組織されている。偶然同じ場所にいるだけ、別の人々の整合とは分ける。全員の内心の信念一致、自発的同意、同一の動作は要求しない。'),
    'h237q': ('[a a d] c', ['arrangement', 'work', 'point'],
              '同じ事務のこの協調配置が、制度的な規則・指示・分担の設定によって作り出されている。独立した個人の判断が偶然一致しただけの状態とは区別する。人工物の材質や不誠実さという意味ではなく、人為的に整えられた構成を表す。'),
    'h237r': ('[a a a d] c', ['mechanism', 'arrangement', 'work', 'point'],
              'この機構の同じ事務での働きが、この協調配置を生み支える手段となっている。単なる併存や、別の事務を担当する機構の存在では足りない。各人への方向付け・抑止は、同じ配置を渡した別の関係で検査する。'),
    'h237s': ('[a a a a i[e] d] c', ['government', 'person', 'work', 'arrangement', 'goal', 'point'],
              'この政府による運営の方向付けが、同じ協調配置を通じて、本人の同じ事務での振る舞いを指定の目的へ向けて導く。無視された命令、無関係な人の参加、本人の私的な願望だけでは足りない。本人が同じ目標を内心で意図することや目標の達成は要求しない。'),
    'h237t': ('[a a a a i[e] d] c', ['government', 'person', 'work', 'arrangement', 'goal', 'point'],
              'この政府の同じ協調配置を通じた働きが、本人によって同じ事務の指定目的が破壊され達成を妨げられることを抑止する。偶然破壊が起きなかっただけ、別人や別目標への抑止では足りない。目的への積極的な貢献や達成を要求せず、破壊の実行も前提にしない。'),
    'h237u': ('[a a ' + FAMILY + ' ' + FAMILY + ' d] c',
              ['arrangement', 'subject', 'means_family', 'end_family', 'reference'],
              'この制度的な構成では、同じ対象と基準を渡した第一の内容族のように振る舞わせることが、第二の内容族を目指すための仕方として位置付けられている。内容族は対象・基準の順に受ける。個人の心理的意図ではなく、設定された機能上の目的関係であり、手段と目的を実行せず、現在の履行、成果の実現、十分性や確実性を含意しない。'),
    'h237v': ('[a a ' + FAMILY + ' ' + PERSON_FAMILY + ' ' + PERSON_FAMILY + ' d] c',
              ['node', 'presenter', 'enclosing_end', 'primary', 'fallback', 'context'],
              '提示者がこの箇所で、同じ目的内容族の中にある本人ごとの二つの代替を、第一を積極的な結果、第二を少なくとも確保したい控えめな結果として順序づけて示す。外側は対象・基準、内側は同じ対象・本人・基準を引数とする。論理的含意や数値尺度ではなく提示上の最低限の位置付けであり、排他的選言、第二の現実の成立、第一から第二が自動的に成立することは加えない。'),
    'h237w': ('[] a', [], '固定原文kant-1784:u0012の[1294,1660)、Nun istから目的節末尾zu werden.までの文全体。'),
}
MEANINGS = {
    'r3a': '同じ事務・基準から、先行部分の機構h237h、共同体h237i、固定成員範囲h237dを取り、政府h237m・公的目的h237k・同じ協調配置h237oへ結んだr2zrの目標内容。全員について同じ配置を通じた方向付けまたは破壊抑止を要求し、人ごとに成立側が違ってよい。目的内容を構成するだけでは効果を実行しない。',
    'r3b': '同じ機構・事務の固定した非空の成員範囲全員が、基準で割り当てられた同じ役割でr2zuの受動的遂行を行う内容。範囲・役割・所属を評価点で選び直さず、要求r2zsと同じ束縛を使う。目的の手段として引用する内容であり、ここから現実の服従を主張しない。',
    'r3c': '同じ事務について既存の必要性と職務要求r2zxを保持し、同じ目的の公共性と政府の管轄を検査する。その機構が、同じ事務・基準での受動的遂行r3bを、同じ人為的協調と方向付けまたは抑止r3aへ向けた仕方として位置付けるh237uを結ぶ。外側の要求と内側の手段・目標を混ぜず、引用内容を実行しない。',
    'r3d': '第五段落の固定基準h232vにおいて、必要な仕組み・役割要求・公的な目的への機能的関係を持つr3cの事務があるという文内容。全ての公的事務や共同体全員へ一般化しない。参照される人々と事務を結果から選び直さない。',
    'r3e': '同じ事務・本人・基準について、同じ機構の協調配置を通じ、その事務を管轄する政府から同じ目的へ方向付けられるという内容。r3aの各人についての第一の代替だけを取り出す。',
    'r3f': 'r3eと全ての参照を共有し、同じ政府・配置によって同じ目的を本人が破壊することを抑止されるという内容。r3aの第二の代替だけを取り出し、目的の達成や破壊の実行を加えない。',
    'r3g': '文全体h237wの内容r3dを著者wa・提示文脈h232oへ段階3で帰属する。同じ目的r3aの二代替r3e/r3fを最低限の順序として示し、Nunを先行私的使用定義h236sに続く説明ufと本文順序ueへ結ぶ。内容の真理や論理的証明は導かない。',
}
LIMITS = [
    '原文[1294,1660)を、共同体のある事務には機構と職務上の受動的遂行が求められ、それによって公的な目的への方向付け、少なくとも目的破壊の抑止を目指すという読みで構成する。機構の現実の成功へ置き換えない。',
    'manchenとeinigeは具体件数を指定しない非空の範囲として読む。全てを意味させず、必ず誰かや何かを除外する真部分集合とも断定しない。不特定の事務を引数で扱い、原文にない政策名や特定の担当者を補わない。',
    'bloß passivは職務の執行に限り運営方針を独立に決め直さないという先行r2zuの読みを保持する。別の学識者の立場や実務上の適用判断まで抑圧する条件は加えない。',
    '人為的一致は制度的に整えた実務上の協調と読む。全員の内心の同意ではない。政府は制度上の運営主体であり、個人の意図hzuの存在を補わない。',
    '方向付けと破壊抑止は同じ成員についての包含的な代替であり、両方でもよく、人ごとに成立側が違ってよい。wenigstensは第二を控えめな最低限として提示する関係で、論理的な含意や確率値へ変えない。',
    '必要性は既存h232eの供給要件の読みを保持する。目的関係h237uも、全可能世界の必然、達成保証、正当性、実際の履行を含意しない。',
    'Nunは私的使用の定義に続いて、その職務上の制約の背景を説明する転換と読む。時間的な今、先行定義の撤回、前の回答の妥当性を証明したことへ変えない。',
    '通読の判断と有限モデル検査を区別する。一般概念の入力規約を公開するが、政府・公共性・制度の全理論をこの一文で還元し終えたとはしない。後続の服従と学識者としての自由、および二作品全体は未完。',
]


@lru_cache(None)
def parent():
    return load_catalog(ROOT, PARENT_BASIS)


@lru_cache(None)
def library():
    return load_catalog(ROOT, coordination.BASIS)


def fields():
    mechanism = 'k h237h[v work v reference]'
    community = 'k h237i[v work v reference]'
    people = 'k h237d[' + mechanism + ' v work v reference]'
    arrangement = 'k h237o[' + mechanism + ' v work v reference]'
    return mechanism, community, people, arrangement


def definitions():
    m, c, ps, a = fields()
    government, goal = 'k h237m[v work v reference]', 'k h237k[v work v reference]'
    args = (' '.join((ps, c, government, 'v work', a, goal, 'v reference')) +
            ' p aa p h237c p h237s p h237t ' + m + ' p h237n p h237p p h237q p h237r')
    text = 'd r3a[work a reference d] e[k r2zr[' + args + ']].\n'
    role = 'k h237e[v person ' + m + ' v work v reference]'
    text += 'd r3b[work a reference d] e[b point[' + both(
        'k r2zn[' + ps + ' ' + c + ' v reference p aa p h237c]',
        'f person a[y[c[' + ps + '][v person]][' + both(
            'k h237f[v person ' + role + ' ' + m + ' v work v reference]',
            't[k r2zu[v person ' + role + ' v work]][v point]') + ']]') + ']].\n'
    text += 'd r3c[work a reference d] c[' + both(
        'k r2zx[v work v reference]',
        'k h237l[' + goal + ' ' + c + ' v work v reference]',
        'k h237n[' + government + ' ' + c + ' v reference]',
        'k h237u[' + m + ' v work r b[p r3b] r b[p r3a] v reference]') + '].\n'
    text += 'd r3d[] e[b evaluation[g work a[k r3c[v work k h232v[]]]]].\n'
    for name, relation in [('r3e', 'h237s'), ('r3f', 'h237t')]:
        text += 'd ' + name + '[work a person a reference d] e[b point[k ' + relation + '[' + (
            government + ' v person v work ' + a + ' ' + goal + ' v point') + ']]].\n'
    text += 'd r3g[] c[' + both(
        'k h236i[k h237w[] k wa[] r d[k r3d[]] k h232o[]]',
        'k h237v[k h237w[] k wa[] r b[p r3a] r b[p r3e] r b[p r3f] k h232o[]]',
        'k uf[k wa[] k h236s[] k h237w[] k h232o[]]',
        'k ue[k h236s[] k h237w[] k h232o[]]') + '].\n'
    return text


def build():
    old, lib = parent(), library()
    assert not (set(PRIMITIVES) | set(MEANINGS)) & (set(old.entries) | set(lib.entries))
    doc = deepcopy(old.document)
    statements, doc['statements'] = doc['statements'], []
    imported = [d for d in closure(lib.document, ['r2zr']) if d['name'] not in old.entries]
    doc['declarations'] += deepcopy(imported)
    doc = parse(format_graph(doc, 'compact') + ''.join(
        'r ' + n + row[0] + '.' for n, row in PRIMITIVES.items()) + definitions())
    added = doc['declarations'][len(old.document['declarations']):]
    new = dict(kind='assert', body=dict(kind='call', symbol='r3g', arguments=[]))
    doc['statements'] = statements + [new]
    core = deepcopy(doc)
    core.update(declarations=closure(doc, list(MEANINGS)), statements=[new])
    ds = {d['name']: d for d in added}
    basis = dict(status='public_purpose_of_required_mechanism_under_explicit_reading',
                 document=FULL, parent=PARENT, inherited_meaning_basis=PARENT_BASIS,
                 definitions={d['name']: lib.entries[d['name']]['meaning_ja'] for d in imported} | MEANINGS,
                 primitives={n: dict(parameters=ds[n]['parameters'], result=ds[n]['result'],
                                     arguments=row[1], meaning_ja=row[2]) for n, row in PRIMITIVES.items()},
                 new_signatures={d['name']: {k: d[k] for k in ('parameters', 'result')} for d in added},
                 imported_symbols={d['name']: coordination.BASIS for d in imported},
                 import_source_sha256={p: digest((ROOT / p).read_bytes())
                                       for p in (coordination.LIBRARY, coordination.BASIS)},
                 limitations=LIMITS)
    body = format_graph(doc, 'compact') + '\n'
    annotations = json.loads((ROOT / 'data/mechanism-requirements-identifiers-v1.json').read_text(encoding='utf-8'))
    annotations.update(document=FULL, document_sha256=digest(body.encode('utf-8')))
    enc = lambda value: json.dumps(value, ensure_ascii=False, indent=2) + '\n'
    return {FULL: body, CORE: format_graph(core, 'compact') + '\n',
            BASIS: enc(basis), ANNOTATIONS: enc(annotations)}
