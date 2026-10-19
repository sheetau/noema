"""Apply the current capacity and factive-cause constructions to a deprivation clause."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT, closure
from scripts.compose_courageous_undertaking import replace_symbols

PARENT = 'examples/v016/kant-defeasible-learning.noema'
PARENT_BASIS = 'data/defeasible-learning-basis-v1.json'
FULL = 'examples/v016/kant-current-deprivation.noema'
CORE = 'examples/v016/current-deprivation-core.noema'
BASIS = 'data/current-deprivation-basis-v1.json'
ANNOTATIONS = 'data/current-deprivation-identifiers-v1.json'
MEANINGS = {
    'r2cf': '同じ本人が自分の理解力を使うbmについて、現在の本人側の判断基盤を保った通常の機会プロフィールで、行使能力がないことをrqvoで評価する。現在地で方法が利用できないだけ、未知の方法区分、将来の訓練の可能性とは分ける。他者の指導を排除するbbの条件は加えない。',
    'r2ch': 'r2cfと同じ本人・活動bm・現在のプロフィールについて、既存のrqvnで肯定的な行使能力を評価する。否定評価の単純な否定ではないため、評価が欠けると両方が不成立になり得る。',
    'r2cg': '本人の同じ基準において、過去にbmの試みを許容されたことがないh3と、現在の行使能力がないr2cfが成立し、前者が後者へ実際に因果的に寄与する。内容の直接評価とhzieによって、既存の事実的な因果の三条件を組み立てる。説明への採用ea、同時成立、経験不在h6、普遍的な能力法則とは分ける。',
}
LIMITS = [
    '第三段落の能力とweil節の部分的な内容式であり、人称の量化範囲や著者への帰属をまだ確定していない。既存の51本文文は保持し、新しい無条件の主張は加えない。',
    'このweil節には、過去の許容不在が現在の不能へ寄与したという事態間の因果の読みを採る。weil一般の全用法を因果へ強制する規則ではない。',
    'vor der Handは同じ基準で現在の判断基盤を保持する評価として扱う。未来の回復、永続的不能、wirklichの談話的な強調はこの三定義から自動的に決まらない。',
    'h3の社会的な許容の不在という読解と、宣言した履歴の範囲を継承する。実効的な機会の全容、現実の全履歴の網羅性、基本的な因果・認知・許容の構成的説明は残る。',
    '第一文のほとんど本性となった状態・個々人の困難・also、第二文前半の愛着・sogar、人称と量化、残りの段落は別途確認する。意味確認済み分量は増やさない。',
]


@lru_cache(None)
def parent():
    return load_catalog(ROOT, PARENT_BASIS)


def build():
    old = parent(); doc = deepcopy(old.document)
    assert not set(MEANINGS) & set(old.entries)
    size = len(doc['declarations'])
    for name, operator in [('r2cf', 'rqvo'), ('r2ch', 'rqvn')]:
        entry = replace_symbols(deepcopy(old.entries['up']['declaration']), {'bb': 'bm', 'rqvn': operator})
        entry['name'] = name
        doc['declarations'].append(entry)
    statements = doc['statements']; doc['statements'] = []
    doc = parse(format_graph(doc, 'compact') + '''
d r2cg[person a] e[b scene[w[t[k h3[v person]][v scene]][w[
 t[k r2cf[v person]][v scene]
][k hzie[v person r[p h3] v person r[p r2cf] v scene]]]]].
''')
    doc['statements'] = statements
    doc = parse(format_graph(doc, 'compact'))
    core = deepcopy(doc)
    core.update(declarations=closure(doc, list(MEANINGS)), statements=[])
    added = doc['declarations'][size:]
    assert len(added) == 3 and all(d['kind'] == 'definition' for d in added)
    basis = dict(status='current_capacity_and_actual_deprivation_cause_composed', document=FULL,
        parent=PARENT, inherited_meaning_basis=PARENT_BASIS, primitives={}, definitions=MEANINGS,
        new_signatures={d['name']: {k: d[k] for k in ('parameters', 'result')} for d in added}, limitations=LIMITS)
    body = format_graph(doc, 'compact') + '\n'
    annotations = json.loads((ROOT / 'data/defeasible-learning-identifiers-v1.json').read_text(encoding='utf-8'))
    annotations.update(document=FULL, document_sha256=digest(body.encode('utf-8')))
    encode = lambda x: json.dumps(x, ensure_ascii=False, indent=2) + '\n'
    return {FULL: body, CORE: format_graph(core, 'compact') + '\n', BASIS: encode(basis), ANNOTATIONS: encode(annotations)}


if __name__ == '__main__':
    from scripts.audit_opening_scope import write_exact
    for path, body in build().items():
        write_exact(ROOT / path, body)
    print('Three composed definitions, zero new primitives; all 51 authored assertions preserved', flush=True)
