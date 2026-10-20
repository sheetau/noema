"""Integrate conditional scholarly reasoning without impairing the assigned work."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT, closure
from scripts.compose_qualitative_influence import both, TRUE
from scripts.compose_nonimpairing_reasoning import MODEL, STATE, on

PARENT = 'examples/v016/kant-office-obedience.noema'
PARENT_BASIS = 'data/office-obedience-basis-v1.json'
DEPENDENCY = 'data/nonimpairing-reasoning-basis-v1.json'
FULL = 'examples/v016/kant-scholarly-compatibility.noema'
CORE = 'examples/v016/scholarly-compatibility-core.noema'
BASIS = 'data/scholarly-compatibility-basis-v1.json'
ANNOTATIONS = 'data/scholarly-compatibility-identifiers-v1.json'
NAMES = ('person', 'office', 'work', 'community', 'world', 'activity', 'scholar', 'writing', 'audience')
CONTEXT = ' '.join(n + ' a' for n in NAMES) + ' reference d'
CARGS = ' '.join('v ' + n for n in NAMES) + ' v reference'
CLASS = 'i[h[' + 'a ' * 9 + 'd] c]'
THREE = 'i[h[a a a d] c]'
# Model providers share this ordered prefix; no provider can silently choose a
# different activity, job, baseline, evaluation point or method.
PREFIX = 'a a a d d a'
PRIMITIVES = {
    'h242i': ('[] a', [], '固定原文kant-1784:u0012[1743,2122)、So fernからangesetzt ist.までの一文全体の箇所。'),
    'h242j': ('[' + PREFIX + '] j[a]', ['person', 'activity', 'work', 'reference', 'start', 'method'],
              '同じ本人・活動・事務・固定基準・開始状況・方法に対する因果比較モデルの有限変数列。実行の有無と事務への効果を比較するための範囲であり、有害な結果を事後に除外しない。モデルの実世界への適合は明示した解釈の仮定である。'),
    'h242k': ('[' + PREFIX + ' a h[a] c] c', ['person', 'activity', 'work', 'reference', 'start', 'method', 'variable', 'state'],
              '同じモデルで、この変数に同じ割当てから与える二値の構造方程式の値。実行側と不実行側で他の方程式と外生背景を固定する。異なる背景の解を混ぜた相関を因果比較としない。'),
    'h242l': ('[' + PREFIX + '] a', ['person', 'activity', 'work', 'reference', 'start', 'method'],
              '同じモデルで、指定本人による指定活動の実行の有無を介入する変数。列内の所属と実行内容zzqとの両介入での一致は合成側で検査する。名前だけで実行対応を認定しない。'),
    'h242m': ('[' + PREFIX + ' h[a] c] d', ['person', 'activity', 'work', 'reference', 'start', 'method', 'state'],
              '同じモデルの割当てに対応する比較状況。指定活動の実行と同じ事務の遂行を評価する状況であり、実行側と不実行側で別の人物・職務の成功を借りない。仮定の比較状況を現在の出来事へ昇格させない。'),
    'h242n': ('[a d d] c', ['work', 'reference', 'point'],
              '同じ固定基準で、指定事務の遂行が指定比較状況について評価されている。品質、遅延、量など採用した評価観点を比較中に替えない。未知の評価を害の不在として補わない。'),
    'h242o': ('[a d d d] c', ['work', 'reference', 'left', 'right'],
              '同じ固定基準の観点で、左の状況における指定事務の遂行が右の同じ事務の遂行以上である。完全達成か否かの二値や、論じる本人の利益に限定しない。比較の反射性・推移性・比較可能性は合成側で確認する。'),
    'h242p': ('[' + PREFIX + '] c', ['person', 'activity', 'work', 'reference', 'start', 'method'],
              '同じ本人が、指定活動と事務を扱うこの方法を指定開始状況から実践的に実行できる。規範的許可だけ、実際の実行、事務を損なわないという結論とは別の入力である。安全な方法だけを利用可能と選び直さない。'),
    'h242q': ('[' + PREFIX + ' d] c', ['person', 'activity', 'work', 'reference', 'start', 'method', 'outcome'],
              '同じ本人・活動・事務・固定基準・開始状況で同じ方法を用いる場合の想定結果に、この状況が含まれる。別方法の成功や違う基準の結果を流用しない。'),
    'h242r': ('[' + PREFIX + ' d] c', ['person', 'activity', 'work', 'reference', 'start', 'method', 'outcome'],
              '同じ方法の想定結果のうち、同じ文脈で評価する結果にこの状況が含まれる。非空性、想定結果の部分集合、同じモデルの実行側全解との一致は合成側で確認し、悪化する解を恣意的に除外しない。'),
    'h242s': ('[a a i d[e] ' + THREE + ' ' + THREE + ' ' + THREE + ' d] c',
              ['node', 'presenter', 'outer_content', 'scope', 'first_focus', 'further_focus', 'context'],
              '提示者が同じ内容内で、同じ三個体・基準の範囲について第二の焦点を第一にとどまることを越えたものとして段階的に強調する。三内容は同じ引数順を共有する。主張の条件・引用・様相を保持し、第一の撤回、焦点の現実の真理、数値的な程度差を含意しない。問いに限定したh235mと同種の取り立てを叙述内の内容族に適用する。'),
    'h242t': ('[a a i d[e] ' + CLASS + ' ' + CLASS + ' ' + CLASS + ' d] c',
              ['node', 'presenter', 'outer_content', 'scope', 'explained', 'clarification', 'context'],
              '提示者が同じ九個体・基準の範囲で、第一の捉え方を第二の立場・活動分類によって説明し具体化する。両族の引数順と外側の条件作用域を保つ。説明としてのつながりであり、第一の自己認識だけから第二の能力・資格が論理的に導かれること、同義性、実際の実行は含意しない。'),
    'h242u': ('[a a i d[e] ' + CLASS + ' ' + CLASS + ' d] c',
              ['node', 'presenter', 'outer_content', 'scope', 'limited_aspect', 'context'],
              '提示者が同じ九個体・基準の範囲で、焦点となる役割関係をその人のある側面に限定して述べる。人の全生活・全立場を尽くす規定にはしない。割合の数値、活動時間の一部分だけ、他の立場の不存在へ変換せず、外側の条件や帰属を保持する。'),
}
MEANINGS = {
    'r3y': '指定した同じモデルの実行側の非空の全解で、同じ書かれた作品scと参照可能な外部記録sdが存在する。記録を基準状況での刊行済み事実とせず、実行可能性の結果内に置く。',
    'r3z': '同じ人の学識者としての公的使用r2zi、同じ活動の本来の公衆cc/ce、同じ作品を介してその公衆へ向ける活動構成h242gを結ぶ。作品と外部記録の実在sc/sdはここでは要求せず、候補を実行する結果内のr3yへ委ねる。',
    'r32a': '固定した同じ人・活動・事務・作品・基準について、一つの方法を選ぶ。その開始状況と方法の同じモデルで、r3uの因果的非悪化、r3vの全結果に結ばれた実行能力、r3yの同じ書面の外部記録をすべて満たす可能性の内容。三条件に別々の方法を使わない。',
    'r32b': '同じ九個体・基準で、先行事務に割り当てられた担当者r3m、同じ事務の共同体への参照、共同体と世界市民社会の成員としての一人称の自己理解r3r、学識者の書面による公的活動候補r3z、理拠を述べ検討する活動h232pを結ぶ。許可・実行・成功で対象を選ばない。',
    'r32c': 'r32bと同じ九個体・基準から、同じ本人が同じ共同体と世界市民社会の成員と自分を捉えるr3rを取り出す。説明の焦点であり、成員性の真理を追加しない。',
    'r32d': 'r32bと同じ九個体・基準から、同じ本人の学識者としての書面を通じた公的議論の候補r3zとh232pを取り出す。mithinの説明先を別人や別活動へ移さない。',
    'r32e': 'r32bと同じ九個体・基準から、先行事務の機構に割り当てられた同じ本人の職務r3mと、その共同体参照の一致を取り出す。その人全体を尽くさない側面として提示する対象。',
    'r32f': '第五段落の固定基準h232vでr32bを満たす各九個体の組について、同じ評価状況でr32aが成立するという条件的な一般内容。範囲外の職務内議論に許可を与えず、前件や書面の現実の成立を別に断言しない。',
    'r32h': '同じ本人・共同体・世界市民社会・基準で、本人が一人称の判断において共同体への成員性r3pを同じ束縛で肯定する。世界市民社会側と共通のr3rの範囲で第一の焦点を示す。',
    'r32i': 'r32hと同じ三個体・基準で、世界市民社会への成員性r3qを一人称の判断で肯定する焦点。真理の断言や世界政府の実在へ変換しない。',
    'r32g': '文全体h242iの条件内容r32fを著者waと第五段落の提示h232oへ帰属する。前文r3nとの役割別の対照、確かに論じうるという承認、自己理解の段階的強調、学識者としての説明、職務は部分的な側面であるという限定、本文順序を同じ内容へ結ぶ。',
}
LIMITS = [
    'So fernを、その人が指定の自己理解と学識者としての公的活動の立場にある限りという条件の一般化として読む。対象は分類された活動内容の組であり、現実の全刊行・あらゆる発信行為の成功を主張しない。自己理解から自動的に資格や能力が発生するという推論ではない。',
    'kannはこの立場で論じることが職務の遂行と実践的に両立しうるという読みを採る。前文の職務内の許可否定を撤回する個別の積極的許可とはしない。allerdingsはこの限定された可能性への確かな承認、aberは同じ人の理性使用を異なる役割から対照する提示として保持する。社会的自由への規範的主張は先行回答に保持されている。',
    'dieser Theil der Maschineとpassives Gliedは先行する同じ事務・機構・固定成員・割当て職務を受ける。物理的な機械部品の同一性を加えない。受動的遂行への先行要求は撤回せず、本人が実際に服従したという事実も追加しない。',
    'zugleichは同じ人・同じ基準で職務の成員と広い社会の成員としての自己理解が併存すること、zum Theileはその人のある職務上の側面への限定として読む。数値的な割合や勤務時間の部分に置き換えない。',
    'ganzenは局所的な職務集団に限定されない共同体全体、Weltbürgergesellschaftは国家を越えて人々を市民として位置付ける社会の構想とする。法的国籍、現在の世界政府、全員の相互承認を補わない。ansiehtは一人称の自己理解であり、内容の真理とは分ける。',
    'ja sogarは同じ自己理解の中で世界市民社会の成員性まで進める強調、mithinはその立場を公衆へ書面で向ける学識者として具体化する説明として読む。強調による第一内容の撤回や、二つの立場の論理的同義性は加えない。',
    'im eigentlichen Verstandeは先行の全読者世界ceを受け、単なる大人数や役所内の聴衆にしない。durch Schriftenは同じ活動・作品・宛先を結び、可能な実行結果で同じ作品の外部記録を要求する。現実に刊行済みであることや読者の受領・理解は要求しない。',
    'ohne daß dadurchは同じ論じる活動の実行による同じ事務の悪化がないという因果的留保。固定背景で実行側と不実行側の全解を比較する頑健なモデル解釈を採る。低下の評価欠落・解なし・比較不能を無害へ補わず、確率的通常性や無期限の絶対的無害性とはしない。',
    '定義と有限の対照検査は、実社会の因果機構の同定や原文との同義性の自動証明ではない。条件文の量化接続、実行可能性、書面の結果内での存在、非事実的な帰属を分けて確認する。旧本文と全記述域の有限評価拒否は保持する。',
]


@lru_cache(None)
def parent():
    return load_catalog(ROOT, PARENT_BASIS)


@lru_cache(None)
def dependency():
    return load_catalog(ROOT, DEPENDENCY)


def definitions():
    text = 'd r3y[writing a ' + MODEL + '] c[' + on('rw', 'i[state ' + STATE + '][' + both(
        'k sc[v writing c[v view][v state]]', 'k sd[v writing c[v view][v state]]') + ']') + '].\n'
    text += 'd r3z[person a activity a scholar a writing a audience a reference d] c[' + both(
        'k r2zi[v person v activity v scholar v reference]', 'k cc[v activity v audience v reference]',
        'k ce[v audience v reference]', 'k h242g[v activity v writing v audience v reference]') + '].\n'
    prefix = 'v person v activity v work v reference v point v method'
    model = ('k h242j[' + prefix + '] i[item a state ' + STATE + '][k h242k[' + prefix + ' v item v state]] '
             'k h242l[' + prefix + '] i[state ' + STATE + '][k h242m[' + prefix + ' v state]]')
    scale = ('i[work a start d outcome d][k h242n[v work v reference v outcome]] '
             'i[work a start d left d right d][k h242o[v work v reference v left v right]]')
    available = 'i[actor a method a start d][k h242p[v actor v activity v work v reference v start v method]]'
    outcomes = 'i[actor a method a start d outcome d][k h242q[v actor v activity v work v reference v start v method v outcome]]'
    selected = 'i[actor a method a start d outcome d][k h242r[v actor v activity v work v reference v start v method v outcome]]'
    text += 'd r32a[person a activity a work a writing a reference d] e[b point[g method a[' + both(
        'k r3u[v person v activity v work v point ' + model + ' ' + scale + ']',
        'k r3v[v person v activity v method v point ' + model + ' ' + available + ' ' + outcomes + ' ' + selected + ']',
        'k r3y[v writing ' + model + ']') + ']]].\n'
    office = both('k r3m[v person v office v work v reference]', 'e[v community][k h237i[v work v reference]]')
    self = 'k r3r[v person v community v world v reference]'
    scholar = both('k r3z[v person v activity v scholar v writing v audience v reference]', 'k h232p[v activity v reference]')
    for name, body in [('r32b', both(office, self, scholar)), ('r32c', self), ('r32d', scholar), ('r32e', office)]:
        text += 'd ' + name + '[' + CONTEXT + '] c[' + body + '].\n'
    args = ' '.join('v ' + n for n in NAMES) + ' k h232v[]'
    conditional = 'y[k r32b[' + args + ']][t[k r32a[v person v activity v work v writing k h232v[]]][v point]]'
    for name in reversed(NAMES):
        conditional = 'f ' + name + ' a[' + conditional + ']'
    text += 'd r32f[] e[b point[' + conditional + ']].\n'
    for name, focus in [('r32h', 'r3p'), ('r32i', 'r3q')]:
        text += 'd ' + name + '[person a community a world a reference d] c[g judgment a[' + both(
            'k fa[v person v judgment v reference]', 'k h242h[v judgment v person v reference]',
            'k h242d[v judgment r[p ' + focus + '] l[a][v person v community v world] ' + TRUE + ' v reference]') + ']].\n'
    n, author, ctx, content = 'k h242i[]', 'k wa[]', 'k h232o[]', 'r d[k r32f[]]'
    text += 'd r32g[] c[' + both(
        'k h236i[' + n + ' ' + author + ' ' + content + ' ' + ctx + ']',
        'k h236k[' + n + ' ' + author + ' k h242c[] r d[k r3n[]] ' + n + ' ' + content + ' r[p r2zg] ' + ctx + ']',
        'k h242b[' + n + ' ' + author + ' ' + content + ' ' + ctx + ']',
        'k h242s[' + n + ' ' + author + ' ' + content + ' r[p r3r] r[p r32h] r[p r32i] ' + ctx + ']',
        'k h242t[' + n + ' ' + author + ' ' + content + ' r[p r32b] r[p r32c] r[p r32d] ' + ctx + ']',
        'k h242u[' + n + ' ' + author + ' ' + content + ' r[p r32b] r[p r32e] ' + ctx + ']',
        'k ue[k h242c[] ' + n + ' ' + ctx + ']', 'u[e[k h242c[]][' + n + ']]') + '].\n'
    return text


def build():
    old, lib = parent(), dependency()
    doc = deepcopy(old.document)
    statements, doc['statements'] = doc['statements'], []
    imported = {}
    for d in lib.document['declarations']:
        name = d['name']
        if name in old.entries:
            assert d == old.entries[name]['declaration']
            assert lib.entries[name]['meaning_ja'] == old.entries[name]['meaning_ja']
        else:
            doc['declarations'].append(d); imported[name] = lib.entries[name]
    assert not (set(PRIMITIVES) | set(MEANINGS)) & (set(old.entries) | set(imported))
    doc = parse(format_graph(doc, 'compact') + ''.join('r ' + n + row[0] + '.' for n, row in PRIMITIVES.items()) + definitions())
    added = doc['declarations'][len(old.document['declarations']):]
    new = dict(kind='assert', body=dict(kind='call', symbol='r32g', arguments=[]))
    doc['statements'] = statements + [new]
    core = deepcopy(doc); core.update(declarations=closure(doc, list(MEANINGS)), statements=[new])
    ds = {d['name']: d for d in added}
    meanings = {n: e['meaning_ja'] for n, e in imported.items() if e['kind'] == 'definition'} | MEANINGS
    primitives = {n: dict(parameters=ds[n]['parameters'], result=ds[n]['result'], arguments=e['arguments'], meaning_ja=e['meaning_ja'])
                  for n, e in imported.items() if e['kind'] == 'primitive'}
    primitives.update({n: dict(parameters=ds[n]['parameters'], result=ds[n]['result'], arguments=row[1], meaning_ja=row[2]) for n, row in PRIMITIVES.items()})
    basis = dict(status='conditional_scholarly_reasoning_without_work_impairment', document=FULL, parent=PARENT,
                 inherited_meaning_basis=PARENT_BASIS, definitions=meanings, primitives=primitives,
                 new_signatures={d['name']: {k: d[k] for k in ('parameters', 'result')} for d in added},
                 imported_symbols={n: e['meaning_basis'] for n, e in imported.items()},
                 import_source_sha256={p: digest((ROOT / p).read_bytes()) for p in sorted(lib.source_sha256)}, limitations=LIMITS)
    body = format_graph(doc, 'compact') + '\n'
    annotations = json.loads((ROOT / 'data/office-obedience-identifiers-v1.json').read_text(encoding='utf-8'))
    annotations.update(document=FULL, document_sha256=digest(body.encode('utf-8')))
    enc = lambda value: json.dumps(value, ensure_ascii=False, indent=2) + '\n'
    return {FULL: body, CORE: format_graph(core, 'compact') + '\n', BASIS: enc(basis), ANNOTATIONS: enc(annotations)}
