"""Bind required means and passive execution roles to the same public work."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT, closure
from scripts.compose_qualitative_influence import both
from scripts import compose_institutional_coordination as coordination

PARENT = 'examples/v016/kant-use-definitions.noema'
PARENT_BASIS = 'data/use-definitions-basis-v1.json'
FULL = 'examples/v016/kant-mechanism-requirements.noema'
CORE = 'examples/v016/mechanism-requirements-core.noema'
BASIS = 'data/mechanism-requirements-basis-v1.json'
ANNOTATIONS = 'data/mechanism-requirements-identifiers-v1.json'
PRIMITIVES = {
    'h236w': ('[a a d] c', ['work', 'community', 'reference'],
              '指定の仕事が、この政治的共同体の共通の利害・公的な運営に関わる事務である。特定者の私的な好みや利益だけに関わる事柄とは分ける。既に実行済み、政府が常に正しい、全員が同じ利害を持つことは要求しない。仕事の集合はこの関係の全範囲であり、機構の必要性や成功した事務だけを分類条件にしない。'),
    'h236x': ('[a d] c', ['work', 'point'],
              'その事務が、この場面でその仕事として定められた働きに沿って遂行されている。事務の名前や予定だけ、別の仕事の実行、単に誰かが動いていることとは分ける。全ての遠い公的目標の達成、正当性、最善の成果までは要求しない。'),
    'h236y': ('[a a a d] c', ['mechanism', 'community', 'work', 'reference'],
              '同じ共同体の同じ事務について、役割・指示系統・分担を一定の規則で結び付けて執行を組織する仕組みである。計画された仕組みも分類し、既に作動中であることや物理機械であることは含意しない。任意の物をMechanismという名前だけで分類せず、制度的な構成の関係を要求する。'),
    'h236z': ('[a a d] c', ['mechanism', 'work', 'point'],
              '指定の仕組みが同じ事務に適用できる状態に整えられ、その事務の手段として利用可能である。抽象的な構想があるだけとは分け、現に作動していること、事務の成功、唯一の手段であることは要求しない。'),
    'h237a': ('[a a a d] c', ['person', 'role', 'work', 'point'],
              '本人が同じ役割で同じ事務の執行を担当し、役割に外から与えられた運営方針・指図に沿ってその執行を行う。職名を持つだけ、何もせず静止すること、別の仕事を遂行することとは分ける。命令全体の完全履行や方針の正当性は、この関係だけから導かない。'),
    'h237b': ('[a a a d] c', ['person', 'role', 'work', 'point'],
              '本人がその職務の遂行の中で、同じ事務の運営方針を自分の判断によって独立に決め直す立場を行使する。与えられた方針を適用するための個々の実務判断、内心の思考、職務外で学識者として論じることとは区別する。'),
    'h237c': ('[a a d] c', ['person', 'community', 'reference'],
              'この人が同じ基準においてこの政治的共同体の成員である。読者として向けられた範囲や、たまたま共同体の場所にいることとは分ける。現在の官職、全政策への同意、実際の事務への参加は別条件である。'),
    'h237d': ('[a a d] h[a] c', ['mechanism', 'work', 'reference'],
              '同じ仕組み・事務・基準において、指定内容をその役割で求める対象者の範囲。評価時点で従った人だけを集め直さず、要求を受ける側を固定する。非空性、人であること、共同体所属、役割への割当ては合成側で検査する。'),
    'h237e': ('[a a a d] a', ['person', 'mechanism', 'work', 'reference'],
              '同じ本人・仕組み・事務についてこの記述で扱う役割。本人の全役割が一つしかないことは含意しない。別の事務や学識者としての立場を無断で流用せず、当該の割当て自体はh237fで検査する。'),
    'h237f': ('[a a a a d] c', ['person', 'role', 'mechanism', 'work', 'reference'],
              'この仕組みの同じ事務について、同じ人がこの役割の担当者として割り当てられている。役割の自己申告や、その場で似た行動をしたことだけとは分ける。実際の執行、能力、正当な任用は含意しない。'),
    'h237g': ('[a a d] a', ['mechanism', 'work', 'reference'],
              'この仕組みの同じ事務で職務上の要求を課す規範の出所。特定の歴史的人物、政府本人、機構という対象との同一性を参照だけで補わない。要求の実在・対象内容は既存h7kで別に検査する。'),
    'h237h': ('[a d] a', ['work', 'reference'],
              'この事務について同じ基準の説明で取り上げる仕組みの参照。唯一可能な仕組みとは主張しない。仕組みとしての構成、必要性、利用可能性、役割の割当てをこの参照の存在だけで代用しない。'),
    'h237i': ('[a d] a', ['work', 'reference'],
              'この事務について同じ説明が扱う政治的共同体の参照。全世界で唯一の共同体、全ての事務で同じ国家、読者世界全体との同一性は含意しない。利害との関係はh236w、成員関係はh237cで検査する。'),
    'h237j': ('[] a', [], '固定原文kant-1784:u0012の[1298,1496)、ist zu manchen Geschäftenからpassiv verhalten müssenまでの、目的節を接続する前の主節・関係節の箇所。Nunと後続um以下を含めない。'),
}
MEANINGS = {
    'r2zt': '同じ事務・基準に関して、事務がその働きに沿って遂行されるという目標内容。評価点でh236xを要求する。必要性を述べる際の引用対象とし、仕事の実行や公的目標の達成を要件の存在から導かない。',
    'r2zu': '同じ人・役割・事務について、外から与えられた方針に沿って執行するh237aと、その職務の遂行中に独立に運営方針を決め直すh237bの不在を結ぶ。職務に限った受動的な執行内容であり、思考の停止や別の立場での議論の禁止ではない。',
    'r2zv': '本人・役割・事務の順にちょうど三個体を持つ引数列からr2zuを構成する。不足・余分・順序の違いを捨てず、要求の引用先として用いる。引用されたことだけで実際の執行を認定しない。',
    'r2zw': '同じ事務・基準が参照する仕組みh237hが、この事務に利用可能な状態にあるという内容。必要要件の内容h232fと一致させ、別の事務の仕組みや実際の作動を代用しない。',
    'r2zx': '同じ事務・共同体・仕組みについて、公的利害に関わる事務、制度的な仕組みの構成、事務遂行r2ztへの供給要件h232e、その要件内容r2zw、固定した非空の成員範囲に同じ職務上の受動的遂行r2zvを要求するr2zsを接続する。必要性と要求を述べる内容であり、要件供給や実際の服従は実行しない。',
    'r2zy': '第五段落の固定基準h232vでr2zxを満たす事務が少なくとも一つあるという内容。内容の評価点に従って事務・成員・要求の基準を選び直さない。全ての公的事務へ一般化せず、他の事務には仕組みが不要だとも断定しない。manchenの非全称の存在読みとして組み立てた部分内容である。',
    'r2zz': '主節・関係節の部分箇所h237jにr2zyを著者wa・第五段落の提示文脈h232oで帰属する。既存の段階3主張帰属h236iを使い、低い記述段階へ落とさない。私的使用定義からの本文順序を保持する。Nunの説明関係と後続目的節の意味はまだ含めない。',
}
LIMITS = [
    'u0012[1298,1496)の主節・関係節を本文へ接続する部分構成。文全体[1294,1660)の意味確認、目的節の接続、全単位の確認文字数追加は行わない。',
    '必要性は、固定した背景の下で事務を進めるために供給を求める条件というh232eの読みを採る。全可能世界での論理的必然、唯一の手段、現実の供給、条件だけでの成功は追加しない。要件内容h232fを合成された利用可能性r2zwに固定する。',
    'passivは、職務の執行で運営方針を独立に決め直さないという読みを採る。与えられた方針の適用に必要な判断や、別の学識者の立場からの議論を排除しない。一般的な服従の全要件r2udを有限例で置き換えるものではない。',
    'manchenは全称化しない存在読みである。単一の歴史的事務への名指しでも、他の事務全ての不要性でもない。複数の種類を総称するニュアンスと本文全体での量化の適合は最終通読に残す。',
    'r2zn/r2zsだけを依存群から本文へ取り込み、対象者・役割・事務・要求内容を接続する。方向付けと抑止のr2zo..r2zrは目的節の接続に残り、定義番号は既存ライブラリ全体のr2zn..r2zsを予約済みとして扱う。',
    '機構を物理機械へ分類せず、制度的な役割と分担の構成として扱う。規範源と政府と機構を参照だけで同一化しない。原文による関係の適切さは文全体の判断で確認する。',
]


@lru_cache(None)
def parent():
    return load_catalog(ROOT, PARENT_BASIS)


@lru_cache(None)
def library():
    return load_catalog(ROOT, coordination.BASIS)


def definitions():
    text = '''
d r2zt[work a reference d] e[b point[k h236x[v work v point]]].
d r2zu[person a role a work a] e[b point[w[k h237a[v person v role v work v point]][u[k h237b[v person v role v work v point]]]]].
d r2zv[bindings j[a]] e[b point[
 g person a[g role a[g work a[
 w[k h7g[v bindings]][w[a[v bindings][n p a b][v person]][
 w[a[v bindings][n p b b][v role]][w[a[v bindings][n p c b][v work]][
 t[k r2zu[v person v role v work]][v point]]]]]
 ]]]
]].
d r2zw[work a reference d] e[b point[k h236z[k h237h[v work v reference] v work v point]]].
'''
    m = 'k h237h[v work v reference]'
    c = 'k h237i[v work v reference]'
    text += 'd r2zx[work a reference d] c[' + both(
        'k h236w[v work ' + c + ' v reference]',
        'k h236y[' + m + ' ' + c + ' v work v reference]',
        'k h232e[' + m + ' r b[p r2zt] v work v reference]',
        'e[k h232f[' + m + ' v reference]][r b[p r2zw]]',
        'k r2zs[k h237d[' + m + ' v work v reference] ' + c + ' v reference p aa p h237c ' +
        m + ' v work k h237g[' + m + ' v work v reference] '
        'i[person a][k h237e[v person ' + m + ' v work v reference]] p h237f r[p r2zv] p h7k]') + '].\n'
    text += '''
d r2zy[] e[b evaluation[g work a[k r2zx[v work k h232v[]]]]].
d r2zz[] c[w[k h236i[k h237j[] k wa[] r d[k r2zy[]] k h232o[]]][k ue[k h236s[] k h237j[] k h232o[]]]].
'''
    return text


def build():
    old, lib = parent(), library()
    assert not (set(PRIMITIVES) | set(MEANINGS)) & (set(old.entries) | set(lib.entries))
    doc = deepcopy(old.document)
    statements, doc['statements'] = doc['statements'], []
    imports = closure(lib.document, ['r2zs'])
    assert not {d['name'] for d in imports} & set(old.entries)
    doc['declarations'] += deepcopy(imports)
    doc = parse(format_graph(doc, 'compact') + ''.join(
        'r ' + n + row[0] + '.' for n, row in PRIMITIVES.items()) + definitions())
    added = doc['declarations'][len(old.document['declarations']):]
    new = dict(kind='assert', body=dict(kind='call', symbol='r2zz', arguments=[]))
    doc['statements'] = statements + [new]
    core = deepcopy(doc)
    core.update(declarations=closure(doc, [*MEANINGS]), statements=[new])
    ds = {d['name']: d for d in added}
    meanings = {d['name']: lib.entries[d['name']]['meaning_ja'] for d in imports} | MEANINGS
    basis = dict(status='required_institutional_means_and_passive_role_partial_sentence',
                 document=FULL, parent=PARENT, inherited_meaning_basis=PARENT_BASIS,
                 definitions=meanings,
                 primitives={n: dict(parameters=ds[n]['parameters'], result=ds[n]['result'],
                                     arguments=row[1], meaning_ja=row[2]) for n, row in PRIMITIVES.items()},
                 new_signatures={d['name']: {k: d[k] for k in ('parameters', 'result')} for d in added},
                 imported_symbols={d['name']: coordination.BASIS for d in imports},
                 import_source_sha256={p: digest((ROOT / p).read_bytes())
                                       for p in (coordination.LIBRARY, coordination.BASIS)},
                 limitations=LIMITS)
    body = format_graph(doc, 'compact') + '\n'
    annotations = json.loads((ROOT / 'data/use-definitions-identifiers-v1.json').read_text(encoding='utf-8'))
    annotations.update(document=FULL, document_sha256=digest(body.encode('utf-8')))
    enc = lambda value: json.dumps(value, ensure_ascii=False, indent=2) + '\n'
    return {FULL: body, CORE: format_graph(core, 'compact') + '\n',
            BASIS: enc(basis), ANNOTATIONS: enc(annotations)}
