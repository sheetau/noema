"""Bind outcome exclusion and concessive expectation to the same conditional."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT, closure
from scripts.compose_scalar_backgrounds import PAIR

PARENT = 'examples/v016/kant-minimum-challenge.noema'
PARENT_BASIS = 'data/minimum-challenge-basis-v1.json'
FULL = 'examples/v016/kant-limited-consequence.noema'
CORE = 'examples/v016/limited-consequence-core.noema'
LIBRARY = 'examples/v016/scoped-outcome-exclusion.noema'
BASIS = 'data/limited-consequence-basis-v1.json'
ANNOTATIONS = 'data/limited-consequence-identifiers-v1.json'
MEANINGS = {
    'r2ia': '同じ対象・状況で焦点条件が成立し、空でない明示的な代替条件列の全条件が不成立である。列にない条件や別の対象・状況の条件を排除せず、期待や望ましさも要求しない。焦点から含意される弱い条件を自動的に除く演算ではないため、代替の選定は呼出側で行う。',
    'r2ib': '前版r2gzと同じ本人・判断・課題・基準について、同じ比較場面・対応活動・保持基盤・機会・通常性を使い、r2gvの確実な遂行条件を評価する。対応活動が空の場面や無効な基盤から確実性を導かない。',
    'r2ic': '同じ人物・判断・課題・時点に実際の独立判断r2gxがあり、その同じ活動のr2ibの確実な遂行条件が成立する。判断の真理や全ての方法にわたる能力とは別の条件。',
    'r2id': '同じ人物・判断・課題・時点で、不確かな独立判断r2haを焦点とし、同じ判断についての確かな遂行r2icを代替としてr2iaで排除する。前版の非確実性と両立する対照を明示し、別の活動の確実性や現在の理由支持を否定しない。',
    'r2ie': '提示文脈whで固定された同じ課題についてr2idを満たす判断があるという内容。限定は存在する同じ判断の内部に置き、本人の全判断が不確かであるという全称へ拡大しない。',
    'r2if': '前版r2htの最小性と理由付き帰結を保ち、同じ課題への限定付き判断r2ieを加える。因果入力hzieの二記述r2hhとr2hbは変えず、限定や尺度自体が不慣れにより生じたとはしない。',
    'r2ig': '同じ本人・文脈で著者の提示する通常予想keを既存jaへ渡す。候補は非空で、全候補が同じ依存離脱r2gtを満たし、不確かな判断r2hbは満たさない。現実の離脱や帰結はこの背景だけでは要求せず、最小課題への期待比較h222cとも区別する。',
    'r2ih': '同じ本人・仮定状況で、最小課題についての尺度背景r2huと、依存離脱を認めた通常予想に対する譲歩背景r2igを共に要求する。二つの比較範囲・入力を交換しない。',
    'r2ii': '提示文脈whに固定した同じ本人・非空の仮定集合で、依存離脱r2gtなら限定・最小性・因果理由を持つ帰結r2ifが成立し、前件を満たす仮定もあるという内容。',
    'r2ij': 'r2iiと同じ本人・仮定集合・前件に、二つの背景r2ihを結ぶ非空の条件内容。背景を離脱の仮定内に置く読みを保つ。',
    'r2ik': '第一文から継承する同じ非空の人物範囲へ、限定を含む前景r2iiを適用する。',
    'r2il': 'r2ikと同じ人物範囲へ、尺度と譲歩の背景r2ijを適用する。',
    'r2im': '閉じた前景r2ikと背景r2ilを既存rstの対として保持する。前景の否定と背景の否定を区別し、対を構成するだけでは内容を実行しない。',
    'r2in': '同じ先行比喩と両側の指示対応r2giを保ち、理由付き条件文の箇所h3sに前景、主節の範囲h3aに背景を置いてr2imを同じ著者waへrqtvで帰属する候補。h3aからh3sへの順序も検査する。内容の真理は断定せず、身体描写と対象側の全対応の証明とも別である。',
}
LIMITS = [
    'nur unsicherenの対象側を、同じ実行された判断が確かな遂行に達していないという焦点と代替の対照として読む。判断が存在することは保持し、本人に一切の判断能力がない、他の全活動も不確か、現在の判断に理由がないとはしない。nurの全用法、韻律・評価的含意を一意に定めたものではない。',
    'この対照の確かな遂行は、前版の不確かさと同じ比較に基づく。前版で既に非確実性を要求しているため、追加の排除はこの読みでは真理条件を強めない。対照の明示と、新しい排除事実の追加を区別する。',
    'dennochには既存jaの通常候補による操作化を使う。全ての採用候補で前件が成立して帰結が成立しないという強い条件であり、数値確率の大小や全ての自然言語の譲歩に同値とはしない。候補を結論の成否から選ぶ規則は追加しない。',
    '予想側で不確かな判断が成立しないことから、確かな判断の存在は導かない。不確かな判断の否定と、確かな判断の積極的な予想を区別する。最小課題の尺度期待h222c、離脱後の通常予想ke、実際の因果寄与hzieは独立した入力。',
    '帰属候補は同じ閉じた二内容、著者、箇所、前景と背景の範囲を保つ。指示対応r2giを参照するが、身体的な幅・跳躍・運動種類と知的な課題・判断・慣れの全対応、種類照応、第四文全体の読解確認は残る。',
    '現行の有限評価器は論理式の両辺と内容の全状況を評価する。範囲外の関数値を問い合わせることがあり、意味上の無断言を部分入力だけで実行できる保証とはしない。未知入力を不成立に補わない。',
    '本文54文、全ての既存宣言・意味規約、十二全単位と先頭三文の判断は保持する。候補帰属を含めまだ本文へ採用せず、第四文の新しい意味確認済み分量を加えない。',
]


@lru_cache(None)
def parent(): return load_catalog(ROOT, PARENT_BASIS)


def additions():
    return '''
d r2ia[item a point d focus h[a d] c alternatives j[h[a d] c]] c[
 w[c[v focus][v item v point]][w[u[e[d[v alternatives]][n p a b]]][
 q[v alternatives][e[n p a b][n p a b]][i[valid c alternative h[a d] c][w[v valid][u[c[v alternative][v item v point]]]]]
 ]]].
d r2ib[person a judgment a topic a anchor d] c[k r2gv[
 i[scene d][k hzzzt[v person v judgment v topic v anchor v scene]]
 i[scene d][w[k hzzzu[v person v judgment v topic v anchor v scene]][g counterpart a[k hzzzx[v person v judgment v topic v anchor v scene v counterpart]]]]
 i[scene d][k hzzzv[v person v topic v scene]]
 i[first d last d][k hzzzw[v person v judgment v topic v anchor v first v last]]
 i[scene d][f counterpart a[y[k hzzzx[v person v judgment v topic v anchor v scene v counterpart]][k r2gy[v person v counterpart v topic v scene]]]]
 ]].
d r2ic[person a judgment a topic a anchor d] c[w[k r2gx[v person v judgment v topic v anchor]][k r2ib[v person v judgment v topic v anchor]]].
d r2id[person a judgment a topic a anchor d] c[k r2ia[v judgment v anchor
 i[activity a point d][k r2ha[v person v activity v topic v point]]
 l[h[a d] c][i[activity a point d][k r2ic[v person v activity v topic v point]]]
 ]].
d r2ie[person a] e[b point[g judgment a[k r2id[v person v judgment k hzzzz[v person k wh[]] v point]]]].
d r2if[person a] e[b point[w[t[k r2ht[v person]][v point]][t[k r2ie[v person]][v point]]]].
d r2ig[person a] e[b point[k ja[v person k r2gt[v person] r[p r2gt] k r2hb[v person] v point
 i[subject a premise i[h[a] e] context d alternative d][k ke[k wa[] v subject v premise v context v alternative]]
 ]]].
d r2ih[person a] e[b point[w[t[k r2hu[v person]][v point]][t[k r2ig[v person]][v point]]]].
d r2ii[person a] e[b anchor[w[e[v anchor][k wh[]]][w[
 k rc[v person p r2gt p r2if i[scene d][k hzzzy[v person v anchor v scene]]]
 ][k re[v person p r2gt i[scene d][k hzzzy[v person v anchor v scene]]]]]]].
d r2ij[person a] e[b anchor[w[e[v anchor][k wh[]]][w[
 k rc[v person p r2gt p r2ih i[scene d][k hzzzy[v person v anchor v scene]]]
 ][k re[v person p r2gt i[scene d][k hzzzy[v person v anchor v scene]]]]]]].
d r2ik[] e[k r2ef[p r2ii]].
d r2il[] e[k r2ef[p r2ij]].
d r2im[] '''+PAIR+'''[k rst[r c[k r2ik[]] r c[k r2il[]]]].
d r2in[] c[w[k r2gi[]][w[k rqtv[k h3s[] k wa[] k r2im[] k h3s[] k h3a[] k wh[]]][k ue[k h3a[] k h3s[] k wh[]]]]].
'''


def build():
    old = parent(); doc = deepcopy(old.document); statements = doc['statements']; doc['statements'] = []
    assert not set(MEANINGS) & set(old.entries)
    doc = parse(format_graph(doc, 'compact') + additions()); doc['statements'] = statements
    core = deepcopy(doc); core.update(declarations=closure(doc, ['r2in', 'rsx', 'rsy', 'rsw']), statements=[])
    lib = deepcopy(doc); lib.update(declarations=closure(doc, ['r2ia', 'ja', 'jb']), statements=[])
    added = doc['declarations'][len(old.document['declarations']):]; assert len(added) == 14
    basis = dict(status='unasserted_limited_consequence_and_concession_candidate', document=FULL, parent=PARENT,
        inherited_meaning_basis=PARENT_BASIS, definitions=MEANINGS, primitives={},
        new_signatures={d['name']: {k: d[k] for k in ('parameters', 'result')} for d in added}, limitations=LIMITS)
    body = format_graph(doc, 'compact') + '\n'
    annotations = json.loads((ROOT / 'data/minimum-challenge-identifiers-v1.json').read_text(encoding='utf-8'))
    annotations.update(document=FULL, document_sha256=digest(body.encode('utf-8')))
    encoded = lambda value: json.dumps(value, ensure_ascii=False, indent=2) + '\n'
    return {FULL: body, CORE: format_graph(core, 'compact')+'\n', LIBRARY: format_graph(lib, 'compact')+'\n', BASIS: encoded(basis), ANNOTATIONS: encoded(annotations)}


if __name__ == '__main__':
    from scripts.audit_opening_scope import write_exact
    for path, body in build().items(): write_exact(ROOT / path, body)
    print('Limited consequence and concessive background composed; 54 statements preserved', flush=True)
