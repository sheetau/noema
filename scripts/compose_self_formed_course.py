"""Bind the same self-forming work to both autonomy and a reliable course."""
from copy import deepcopy
from functools import lru_cache
import json

from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT, closure
from scripts.compose_reliable_course import substitute

PARENT = 'examples/v016/kant-reliable-course.noema'
PARENT_BASIS = 'data/reliable-course-basis-v1.json'
FULL = 'examples/v016/kant-self-formed-course.noema'
CORE = 'examples/v016/self-formed-course-core.noema'
BASIS = 'data/self-formed-course-basis-v1.json'
ANNOTATIONS = 'data/self-formed-course-identifiers-v1.json'
REBOUND = dict(zip(
    ('r2jn', 'r2jo', 'r2jp', 'r2jq', 'r2jr', 'r2js', 'r2jt', 'r2ju', 'r2jv', 'r2jw', 'r2jx'),
    ('r2kd', 'r2ke', 'r2kf', 'r2kg', 'r2kh', 'r2ki', 'r2kj', 'r2kk', 'r2kl', 'r2km', 'r2kn'),
))
SUBSTITUTIONS = {**REBOUND, 'r2jm': 'r2kc'}
MEANINGS = {
    'r2jz': '指定された過程そのものが、基準時までに、ある本人の精神への自己活動による自立達成h4pの過程であったという内容。因果の要因側を過程個体へ結び、現在もその作業が継続していることは要求しない。',
    'r2ka': '指定された活動そのものが、基準時までに、ある本人の理由ある独立判断と通常比較での確かな遂行を全過程に持つr2jiの活動であったという内容。因果の結果側を活動個体へ結び、現在も活動中であることは要求しない。',
    'r2kb': '同じ本人・自己形成過程・先行時点・達成時点・知的活動・完了時点・基準時を固定し、h4pの自立達成とr2jiの確かな活動を同じ履歴のrctで結ぶ。その同じ過程のr2jzの側面が、その同じ活動のr2kaの成立へrqquの因果的寄与を持つ。別の作業や別の活動の寄与、時間順や共存だけでは満たさない。',
    'r2kc': '基準時までにr2kbの同じ本人による両成果と因果接続の証拠がある内容。本人の精神への同じ働きかけが自立を生じさせ、確かな知的活動にも寄与するという第五文の成功者の条件。',
    'r2kd': '指定列の各人にr2kcの肯定例かh4tの評価条件を要求する。因果のない旧r2jmだけを新しい成功の肯定例として用いない。因果関係や活動の解釈を未知から偽へ変換しない。',
    'r2ke': '同じ全対象列でr2kcの成功者をh4kにより数え、一人以上かつ文脈上の上限未満を要求する。評価条件はr2kd、譲歩背景は別条件として保持する。',
    'r2kf': 'r2keの同じ人数と母集団、文脈、上限を保持し、h5vの数量代替を既存rczで排除する。因果の不足を無視して旧成功者を数えない。',
    'r2kg': '自己活動による自立h4qを認めた著者の通常予想で、同じ人のr2kcの両成果を予想しないというjaの譲歩背景。候補の非空性と前提保持を維持する。',
    'r2kh': '実際のr2kcの該当者に同じ文脈のr2kgを分配する。予想の成否を人数の性質へ混ぜない。',
    'r2ki': '同じ全対象列についてr2kfの数量条件と代替排除を前景内容にする。予想keは実行しない。',
    'r2kj': '全対象の正確な列挙、r2kdの評価条件、該当者へのr2khの背景を要求する内容。正の成功者数や少数性は前景側に保つ。',
    'r2kk': '全対象を表す有限列が存在しr2kiの前景が成立する内容。任意の有限列への量化を保持する。',
    'r2kl': '同じ全対象を表す有限列が存在しr2kjの背景が成立する内容。前景と同じr2kcの該当者条件を使う。',
    'r2km': '閉じたr2kkの前景とr2klの背景をrstの対にする。前景だけの否定を引き続き許す。',
    'r2kn': '前版と同じ著者・結論箇所・文脈・前景と譲歩の範囲へr2kmを帰属し、第四文の主節と理由からの推論提示と本文順序を保持する。内容を現実の真理として実行しない。',
}
LIMITS = [
    'durch eigene Bearbeitung ihres Geistesを、離脱と確かな歩みの両方へかかる手段・因果の表現として読む。前版の時間的共存から因果を推論するのでなく、同じ作業から同じ活動への寄与を明示する。',
    'h4mは本人の考え方・判断の習慣・認知的な働きなどの精神的な部分、h4nはそれを本人が吟味し組み直すように働きかける活動という既存の意味規約を採る。h4oは両関係の本人・部分・作業を共有する。精神全体の全部分を一度に変えること、魂や脳の物理機構を付け加えない。',
    '本人が関与する自己形成であり、教師・助言・他の原因を排除しない。方法、回数、努力量、意図、改善の程度は原文が特定していないため固定値を追加しない。成功はh4nの語義に埋めず、h4pとr2jiと因果接続で要求する。',
    '因果の要因と結果は過程個体と活動個体を指し、双方の実際の成立はrqquと同じ本人を束縛するrctの両方で確認する。記述内の存在量化は別人の経験を当該本人へ移す許可ではない。',
    '過程と知的活動の同一性も相違も強制しない。同じ複合過程の二つの記述を許すが、因果の自己依存が妥当かはhzieの解釈入力の条件であり、同一個体だから寄与を自動認定しない。',
    '完了点の順序は達成点≦活動完了点≦基準時。活動の開始が達成後であること、唯一・十分・必要な原因、将来の永久的な自立は要求しない。',
    '自己形成と両成果のこの読みを本文へ採用するが、heraus zu wikkelnの解放描写と対象側の対応、第五文および第三段落全体の通し判断は残る。',
]


@lru_cache(None)
def parent():
    return load_catalog(ROOT, PARENT_BASIS)


def additions():
    return '''
d r2jz[process a] e[b anchor[g person a[g earlier d[g attained d[
 k h4p[v person v process v earlier v attained v anchor]]]]]].
d r2ka[episode a] e[b anchor[g person a[g completed d[
 k r2ji[v person v episode v completed v anchor]]]]].
d r2kb[person a process a earlier d attained d episode a completed d anchor d] c[w[
 k rct[i[point d][k ia[v person v anchor v point]] i[first d last d][k ic[v first v last v anchor]]
 v person v attained v completed v anchor
 i[who a when d reference d][k h4p[v who v process v earlier v when v reference]]
 i[who a when d reference d][k r2ji[v who v episode v when v reference]]]
 ][k rqqu[v process r[p r2jz] v episode r[p r2ka] v anchor]]].
d r2kc[person a] e[b anchor[g process a[g earlier d[g attained d[g episode a[g completed d[
 k r2kb[v person v process v earlier v attained v episode v completed v anchor]]]]]]]].
'''


def build():
    old = parent()
    doc = deepcopy(old.document)
    statements, doc['statements'] = doc['statements'], []
    assert not set(MEANINGS) & set(old.entries)
    doc = parse(format_graph(doc, 'compact') + additions())
    for declaration in old.document['declarations']:
        if declaration['name'] in REBOUND:
            rebound = substitute(declaration, SUBSTITUTIONS)
            rebound['name'] = REBOUND[declaration['name']]
            doc['declarations'].append(rebound)
    doc = parse(format_graph(doc, 'compact'))
    assert statements[15]['body']['symbol'] == 'r2jx'
    statements[15] = dict(kind='assert', body=dict(kind='call', symbol='r2kn', arguments=[]))
    doc['statements'] = statements
    core = deepcopy(doc)
    core.update(declarations=closure(doc, ['r2kn']), statements=[statements[15]])
    added = doc['declarations'][len(old.document['declarations']):]
    basis = dict(status='same_self_work_causes_autonomy_and_contributes_to_course_partial',
                 document=FULL, parent=PARENT, inherited_meaning_basis=PARENT_BASIS,
                 definitions=MEANINGS, primitives={}, rebound_definitions=REBOUND,
                 new_signatures={d['name']: {k: d[k] for k in ('parameters', 'result')} for d in added},
                 limitations=LIMITS)
    body = format_graph(doc, 'compact') + '\n'
    annotations = json.loads((ROOT / 'data/reliable-course-identifiers-v1.json').read_text(encoding='utf-8'))
    annotations.update(document=FULL, document_sha256=digest(body.encode('utf-8')))
    encoded = lambda value: json.dumps(value, ensure_ascii=False, indent=2) + '\n'
    return {FULL: body, CORE: format_graph(core, 'compact') + '\n',
            BASIS: encoded(basis), ANNOTATIONS: encoded(annotations)}
