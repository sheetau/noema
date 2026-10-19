"""Separate deliberated selection, unselected response, and contrary decisions."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT, closure
from scripts.compose_graded_change import SCALE, parameters
from scripts.compose_limits import v, call as k, op, both, quant, definition

PARENT = 'examples/v016/kant-internalized-state.noema'
PARENT_BASIS = 'data/internalized-state-basis-v1.json'
FULL = 'examples/v016/kant-unselected-continuation.noema'
CORE = 'examples/v016/unselected-continuation-core.noema'
BASIS = 'data/unselected-continuation-basis-v1.json'
ANNOTATIONS = 'data/unselected-continuation-identifiers-v1.json'
PRIMITIVES = {
    'hzzf': (['judgment', 'target', 'description', 'polarity', 'point'], 'この判断は、当該局面の選択肢を検討した上で、指定対象を記述された状態にする、またはその状態に保つ方針を新たに採る実践的な決定である。極性が偽なら、その状態を避ける、またはやめる方針を採る。主体はfaで別に結ぶ。事実についての肯定判断hznn、単なる希望、以前からの方針、成功や能力とは別である。対象の記述に適した認知上の捉え方は解釈時に必要であり、本人が機構の細部を知ることを要求しない。'),
    'hzzg': (['target', 'person', 'description', 'anchor', 'point', 'candidate'], '指定履歴点における本人と対象の関連する構成、以前からの方針、知識、機会を保ち、記述された状態についてその都度検討して決めることを比較できる局面。新たな決定の有無・極性を変え得る比較とし、その結果や対象の作動を保存条件にしない。本人が新しく訓練された場合や別人に置き換わった場合は含めない。比較期間・背景・実践的決定の区切りは文脈入力である。'),
}
MEANINGS = {
    'r2cw': '同じ本人を主体とする同じ判断が、同じ対象・性質記述・極性について、この局面で新たに採る実践的決定である。主体だけの一致や内容だけの一致を別の判断から寄せ集めない。結果の真理や実行は要求しない。',
    'r2cx': '同じ内的構成が本人の未成熟に実際に寄与するr2ctが成立し、その作動を進める・やめるという両極性の新たな実践的決定は、この局面にない。現在の非熟慮的な作動の一つの記述であり、以前からの方針、意識一般、本人の能力の欠如とは同一視しない。',
    'r2cy': '同じ本人が同じ構成の作動をやめる方針を新たに採り、作動を進める反対の決定はなく、それでもr2ctの内的寄与がこの局面で成立している。停止を実際に試みたこと、手段がすべて失敗すること、将来も止められないことは含めない。',
    'r2cz': '同じ本人・構成・基準・履歴点について、外的更新の比較と実践的決定の比較に共通する候補から、外的更新も、その都度の両極性の決定もない局面を選ぶ。その非空範囲で内的寄与r2ctを評価し、指定程度をrqsrの両端と整合させる。現在の一例だけでこの傾向を認定しない。',
    'r2da': 'r2cvの経験による形成・現在の内的寄与・程度の増加と保持に、選び直さない比較r2czを接続する。元の評価の一意性を検査してから比較との整合を確認する。同じ尺度の値を二つの比較へ用いる明示的な読みであり、現在も選び直していないことや停止能力の欠如は要求しない。',
}
LIMITS = [
    '本性との比較に、その都度の熟慮を伴う決定をやり直さなくても働くという軸を加える。全ての自動性、無意識、無目的、反復回数、習慣の全語義とは同一視しない。',
    '後年のKant AA VII149には内的な強制と考えなしの反復があるが、意図的に習慣を採用する場合もある。以前からの方針を許し、1784年の句に現在の反対意思を必須としない。',
    'やめると決めても作動した一例r2cyと、適切な抑制の試みや利用可能な方法でも停止できないことは異なる。今回の構成は後者の強制性・能力の否定をまだ完成させない。',
    '実践的決定について未知を不存在へ置き換えない。記録が見つからないだけで両極性の不存在を入力しない。対象の捉え方、比較期間、背景、中間値と近接域の校正は解釈入力として残る。',
    '外的更新なしの比較と、さらにその都度の決定がない比較を同じ程度で評価する。両方の端点条件に合わない評価を拒むが、中間値の相対的な妥当性を自動的に証明するものではない。',
    '既存51本文文と十二単位の判断を保つ。原文句の全条件、個々人の離脱の困難、also、人称・量化と著者帰属は残り、意味確認済み分量を増やさない。',
]


@lru_cache(None)
def parent():
    return load_catalog(ROOT, PARENT_BASIS)


def definitions():
    text = 'r hzzf[a a i[h[a] e] c d] c.r hzzg[a a i[h[a] e] d d d] c.'
    chosen = quant('g', 'judgment', 'a', both(k('fa', v('person'), v('judgment'), v('point')),
        k('hzzf', v('judgment'), v('target'), v('description'), v('polarity'), v('point'))))
    text += definition('r2cw', 'person a target a description i[h[a] e] polarity c point d', chosen)
    yes = op('e', v('pattern'), v('pattern')); no = op('u', yes)
    def choice(polarity, point):
        return k('r2cw', v('person'), v('pattern'), 'r[p r2cr]', polarity, v(point))
    def unselected(point):
        return both(op('u', choice(yes, point)), op('u', choice(no, point)))
    def contribution(point):
        return op('t', k('r2ct', v('pattern'), v('person')), v(point))
    def content(name, body):
        return 'd ' + name + '[pattern a person a] e[b point[' + body + ']].'
    text += content('r2cx', both(contribution('point'), unselected('point')))
    text += content('r2cy', both(contribution('point'), choice(no, 'point'), op('u', choice(yes, 'point'))))
    cases = 'i[candidate d][' + both(k('hzzd', v('pattern'), v('person'), 'r[p bf]', v('anchor'), v('point'), v('candidate')),
        k('hzzg', v('pattern'), v('person'), 'r[p r2cr]', v('anchor'), v('point'), v('candidate')),
        op('u', k('hzze', v('person'), 'r[p bf]', v('candidate'))), unselected('candidate')) + ']'
    text += definition('r2cz', 'pattern a person a anchor d point d scale h[a] c degree a low a high a',
        k('rqsr', cases, 'i[candidate d][' + contribution('candidate') + ']', v('scale'), v('degree'), v('low'), v('high')))
    fields = [('person', 'a'), ('pattern', 'a')] + SCALE[:-1] + [('measured', 'h[a i[h[a] e] a d d a] c')]
    raw = 'i[at d value a][c[v measured][v actor v description v reference v anchor v at v value]]'
    measured = 'i[actor a description i[h[a] e] reference a anchor d point d degree a][' + both(
        k('r2cl', raw, v('scale'), v('point'), v('degree')),
        k('r2cz', v('reference'), v('actor'), v('anchor'), v('point'), v('scale'), v('degree'), v('low'), v('high'))) + ']'
    args = 'v person v pattern ' + ' '.join('v ' + n for n, _ in SCALE[:-1]) + ' ' + measured
    return text + 'd r2da[' + parameters(fields) + '] e[k r2cv[' + args + ']].'


def build():
    old = parent(); doc = deepcopy(old.document)
    assert not (set(MEANINGS) | set(PRIMITIVES)) & set(old.entries)
    size = len(doc['declarations']); statements = doc['statements']; doc['statements'] = []
    doc = parse(format_graph(doc, 'compact') + definitions())
    doc['statements'] = statements; doc = parse(format_graph(doc, 'compact'))
    core = deepcopy(doc); core.update(declarations=closure(doc, list(MEANINGS)), statements=[])
    added = doc['declarations'][size:]; by_name = {d['name']: d for d in added}
    assert len(added) == 7
    basis = dict(status='unselected_continuation_and_contrary_decision_comparison_candidate', document=FULL,
        parent=PARENT, inherited_meaning_basis=PARENT_BASIS,
        primitives={n: dict(parameters=by_name[n]['parameters'], result=by_name[n]['result'], arguments=args, meaning_ja=meaning)
                    for n, (args, meaning) in PRIMITIVES.items()}, definitions=MEANINGS,
        new_signatures={d['name']: {k: d[k] for k in ('parameters', 'result')} for d in added}, limitations=LIMITS)
    body = format_graph(doc, 'compact') + '\n'
    annotations = json.loads((ROOT / 'data/internalized-state-identifiers-v1.json').read_text(encoding='utf-8'))
    annotations.update(document=FULL, document_sha256=digest(body.encode('utf-8')))
    encode = lambda x: json.dumps(x, ensure_ascii=False, indent=2) + '\n'
    return {FULL: body, CORE: format_graph(core, 'compact') + '\n', BASIS: encode(basis), ANNOTATIONS: encode(annotations)}


if __name__ == '__main__':
    from scripts.audit_opening_scope import write_exact
    for path, body in build().items():
        write_exact(ROOT / path, body)
    print('Five definitions and two general inputs composed; no new authored assertions', flush=True)
