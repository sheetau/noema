"""Connect job-scoped permission denial and a requirement of guided obedience."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT, closure
from scripts.compose_qualitative_influence import both
from scripts.compose_scoped_obedience import FIELDS
from scripts.compose_situated_criticism import params

PARENT = 'examples/v016/kant-public-purpose-mechanism.noema'
PARENT_BASIS = 'data/public-purpose-mechanism-basis-v1.json'
FULL = 'examples/v016/kant-office-obedience.noema'
CORE = 'examples/v016/office-obedience-core.noema'
BASIS = 'data/office-obedience-basis-v1.json'
ANNOTATIONS = 'data/office-obedience-identifiers-v1.json'
CODE = 'i[h[a a] e]'
FOLLOW = 'h[a a a a ' + CODE + ' c d d] c'
CLASS = 'i[h[a a a d] c]'
NEGATIVE = 'i b[h[a a a d] e]'
POSITIVE = 'i c[h[a a a d] e]'
PRIMITIVES = {
    'h237x': ('[a a a a d] c', ['person', 'role', 'work', 'activity', 'reference'],
              '同じ本人・職務・事務・基準で、指定活動がその事務をその職務で行う活動候補の範囲に属する。実行・許可・要求への適合を分類の条件としない。別の仕事や同じ本人の学識者としての職務外の活動を混ぜず、不都合な要求や禁止された活動を事後に除外しない。'),
    'h237y': ('[a d] c', ['work', 'reference'],
              '同じ基準で、直前の機構の説明h237wが取り上げ、Hierが受ける事務の範囲。全ての公的事務への一般化ではなく、その説明で扱う事務を固定する。現在許可された、従った、成功した事務だけへ選び直さず、先行説明r3cへの適合と非空性は合成側で確認する。'),
    'h237z': ('[a a a i b[h[j[a] d] e] j[a] d c d] c',
              ['source', 'person', 'role', 'target', 'bindings', 'reference', 'polarity', 'point'],
              'この規範の出所が、この本人にこの職務で、同じ順序の個体列と指定の基準を段階1の閉じた内容関数へ適用した内容の指定極性を満たすよう要求する。h7kと同じ規範関係を段階1の記述で扱い、内容の基準引数を明示する。要求時に内容を実行せず、現在の履行、正当性、許可の存在を含意しない。'),
    'h242a': ('[a a ' + CLASS + ' ' + NEGATIVE + ' ' + POSITIVE + ' d] c',
              ['node', 'presenter', 'scope', 'negative', 'replacement', 'context'],
              '提示者が同じ箇所で、指定範囲の同じ本人・職務・事務・基準について、第一の否定的内容が退けた選択に代えて第二の肯定的内容を提示する。範囲と二内容の引数順は共通である。否定を撤回せず、要求や許可の様相を保持する訂正的な対置で、二内容の論理的矛盾、唯一の選択肢、現実の履行は含意しない。'),
    'h242b': ('[a a i d[e] d] c', ['node', 'presenter', 'content', 'context'],
              '提示者がこの箇所の限定された内容を、この議論の文脈では確かに認めるものとして提示する。単なる主張への帰属とは別の承認的な取り立てであり、無条件の普遍化、論理的自明性、読者全員の信念、内容の実際の真理を含意しない。後続で別の立場の留保を置く余地を否定しない。'),
    'h242c': ('[] a', [], '固定原文kant-1784:u0012の[1661,1742)、Hier ist es nun freilichからsondern man muß gehorchen.までの文全体。'),
}
MEANINGS = {
    'r3h': '指定した出所・本人・基準・役割範囲・要求記録について、全記述域での網羅rtx、記録妥当性と履行rtw、同じ各要求を遂行の指示として受け入れ調整する関係を結ぶ。既存r2udの三条件を一般の記録引数で構成し、偶然の一致や空の記録による要求消去を認めない。',
    'r3i': '同じ出所・本人の要求記録h233wから、指定職務かつ同じ事務の活動範囲h237xに属するものを選ぶ。要求関係自体も同じ活動範囲に限定し、r3hの全記述域の網羅・履行・指示に従う調整を適用する。別の仕事や役割への要求をこの事務の服従に混ぜない。',
    'r3j': '同じ本人・職務・事務・基準の全ての理性による言語的検討の活動候補について、同じ規範源h237gによる実行zzqへの積極的な許可がない内容。ca/h232p/cb/h237xで固定する範囲を実行・許可の結果で選び直さず、許可否定を実際の沈黙や負極性の要求と同一視しない。',
    'r3k': '本人・職務・事務の正確な三個体列と明示した基準から、同じ機構の規範源h237gへ結んだr3iの服従内容を構成する。余分や不足の列を拒否し、全記述域を省略しない。要求の対象として段階1で引用する。',
    'r3l': '同じ本人・職務・事務について、同じ機構の規範源がr3kの服従内容を正極性で要求する内容。要求の評価点と要求対象を固定する基準を分け、要求を引用する段階を保持する。実際の服従は実行しない。',
    'r3m': 'Hierが受ける固定した事務範囲と、その機構の固定した成員範囲・共同体所属・割当て役割を同じ本人・職務・事務・基準で照合する範囲。人であること、h237eの役割参照、h237fの割当てを確認し、本人の他の立場を含めない。',
    'r3n': '第五段落の基準h232vでHierの事務範囲が非空であり、その全事務が先行の機構と目的の説明r3cを満たす。その固定した範囲の全ての本人・職務について、同じ評価点でr3jの許可否定とr3lの服従要求を合わせる。前の説明から関係の正当性や実際の履行を導いたとはしない。',
    'r3o': '文全体h242cのr3nを著者wa・提示文脈h232oへ帰属し、同じ範囲r3mでr3jからr3lへの訂正的な対置を示す。freilichを限定された内容の承認として取り立て、直前の機構文を具体化する説明ufと順序ueへ結ぶ。引用内容を実行しない。',
}
LIMITS = [
    'Hierは直前に述べた制度的な事務・機構・成員・割当て職務の範囲と読む。同じ人の全生活や学識者としての公的議論へ広げない。事務の範囲は許可・服従の成否より先に固定する。',
    'nicht erlaubtは同じ規範源による積極的実行許可の否定として読む。未知の許可を偽に補わず、不実行への積極的要求と同じ述語にしない。実際に論じなかったこと、物理的な不能、思考そのものの停止は加えない。',
    'gehorchenは同じ職務・事務に属する要求を網羅して履行し、それを自分の遂行の指示として受け入れ調整する内容とする。先行r2zuの受動性だけで代用せず、別の職務の全要求を加えない。',
    '全記述域での網羅rtxを保持する。有限評価器による全域評価は拒否し、有限記述の診断や引用の成功を全域の実行証明にしない。',
    'man mußは同じ事務の各担当者への服従要求として構成する。服従への道徳的賛同、要求の正当性、現実の履行は追加しない。原文に特定の統治者名を補わない。',
    'sondernは否定した選択に代わる肯定的な要求の提示、nunは直前の説明の具体化への継続、freilichはこの限定では確かに認めるという取り立てと読む。後続の学識者としての自由との留保を先取りして否定しない。',
]


@lru_cache(None)
def parent():
    return load_catalog(ROOT, PARENT_BASIS)


def definitions():
    fields = ' '.join('v ' + n for n, _ in FIELDS)
    text = 'd r3h[' + params(FIELDS) + ' followed ' + FOLLOW + '] e[b point[' + both(
        'k rtx[' + fields + ']',
        'k rtw[' + fields + ' v point]',
        'f item a[y[c[v items][v item]][c[v followed][v source v person '
        'c[v roles][v item] c[v actions][v item] c[v descriptions][v item] '
        'c[v signs][v item] v anchor v point]]]') + ']].\n'
    scoped = ('i[origin a recipient a office a activity a description ' + CODE + ' sign c anchor d][' +
              both('k h237x[v recipient v office v work v activity v reference]',
                   'k h7a[v origin v recipient v office v activity v description v sign v anchor]') + ']')
    items = 'i[item a][' + both(
        'k h233w[v source v person v reference v item]',
        'e[k h233x[v item]][v role]',
        'k h237x[v person v role v work k h233y[v item] v reference]') + ']'
    text += ('d r3i[source a person a role a work a reference d] e[k r3h['
             'v source v person v reference i[office a][e[v office][v role]] ' + items +
             ' p h233x p h233y p h233z p h234a ' + scoped + ' p h234b]].\n')
    m = 'k h237h[v work v reference]'
    source = 'k h237g[' + m + ' v work v reference]'
    candidate = both('k ca[v person v activity v reference]', 'k h232p[v activity v reference]',
                     'k cb[v person v activity v role v reference]',
                     'k h237x[v person v role v work v activity v reference]')
    text += 'd r3j[person a role a work a reference d] e[b point[f activity a[y[' + candidate + '][u[' + (
        'k h7b[' + source + ' v person v role v activity r[p zzq] e[v person][v person] v point]') + ']]]]].\n'
    text += '''
d r3k[bindings j[a] reference d] e[b point[
 g person a[g role a[g work a[
 w[k h7g[v bindings]][w[a[v bindings][n p a b][v person]][
 w[a[v bindings][n p b b][v role]][w[a[v bindings][n p c b][v work]][
 t[k r3i[k h237g[k h237h[v work v reference] v work v reference]
 v person v role v work v reference]][v point]]]]]
 ]]]
]].
'''
    text += ('d r3l[person a role a work a reference d] e[b point[k h237z[' + source +
             ' v person v role r b[p r3k] l[a][v person v role v work] v reference e[v person][v person] v point]]].\n')
    text += 'd r3m[person a role a work a reference d] c[' + both(
        'k h237y[v work v reference]', 'k aa[v person]',
        'c[k h237d[' + m + ' v work v reference]][v person]',
        'k h237c[v person k h237i[v work v reference] v reference]',
        'e[v role][k h237e[v person ' + m + ' v work v reference]]',
        'k h237f[v person v role ' + m + ' v work v reference]') + '].\n'
    ref = 'k h232v[]'
    text += 'd r3n[] e[b point[' + both(
        'g work a[k h237y[v work ' + ref + ']]',
        'f work a[y[k h237y[v work ' + ref + ']][' + both(
            'k r3c[v work ' + ref + ']',
            'f person a[f role a[y[k r3m[v person v role v work ' + ref + ']][' + both(
                't[k r3j[v person v role v work ' + ref + ']][v point]',
                't[k r3l[v person v role v work ' + ref + ']][v point]') + ']]]') + ']]') + ']].\n'
    text += 'd r3o[] c[' + both(
        'k h236i[k h242c[] k wa[] r d[k r3n[]] k h232o[]]',
        'k h242a[k h242c[] k wa[] r[p r3m] r b[p r3j] r c[p r3l] k h232o[]]',
        'k h242b[k h242c[] k wa[] r d[k r3n[]] k h232o[]]',
        'k uf[k wa[] k h237w[] k h242c[] k h232o[]]',
        'k ue[k h237w[] k h242c[] k h232o[]]') + '].\n'
    return text


def build():
    old = parent()
    assert not (set(PRIMITIVES) | set(MEANINGS)) & set(old.entries)
    doc = deepcopy(old.document)
    statements, doc['statements'] = doc['statements'], []
    doc = parse(format_graph(doc, 'compact') + ''.join(
        'r ' + n + row[0] + '.' for n, row in PRIMITIVES.items()) + definitions())
    added = doc['declarations'][len(old.document['declarations']):]
    new = dict(kind='assert', body=dict(kind='call', symbol='r3o', arguments=[]))
    doc['statements'] = statements + [new]
    core = deepcopy(doc); core.update(declarations=closure(doc, list(MEANINGS)), statements=[new])
    ds = {d['name']: d for d in added}
    basis = dict(status='office_argument_permission_denial_and_obedience_requirement',
                 document=FULL, parent=PARENT, inherited_meaning_basis=PARENT_BASIS,
                 definitions=MEANINGS,
                 primitives={n: dict(parameters=ds[n]['parameters'], result=ds[n]['result'],
                                     arguments=row[1], meaning_ja=row[2]) for n, row in PRIMITIVES.items()},
                 new_signatures={d['name']: {k: d[k] for k in ('parameters', 'result')} for d in added},
                 limitations=LIMITS)
    body = format_graph(doc, 'compact') + '\n'
    annotations = json.loads((ROOT / 'data/public-purpose-mechanism-identifiers-v1.json').read_text(encoding='utf-8'))
    annotations.update(document=FULL, document_sha256=digest(body.encode('utf-8')))
    enc = lambda value: json.dumps(value, ensure_ascii=False, indent=2) + '\n'
    return {FULL: body, CORE: format_graph(core, 'compact') + '\n', BASIS: enc(basis), ANNOTATIONS: enc(annotations)}
