"""Keep acquired nature-like persistence without prescribing its learning cause."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT, closure
from scripts.compose_courageous_undertaking import replace_symbols

PARENT = 'examples/v016/kant-assessed-difficulty.noema'
PARENT_BASIS = 'data/assessed-difficulty-basis-v1.json'
FULL = 'examples/v016/kant-nature-sentence.noema'
CORE = 'examples/v016/nature-sentence-core.noema'
BASIS = 'data/nature-sentence-basis-v1.json'
ANNOTATIONS = 'data/nature-sentence-identifiers-v1.json'
MAPPING = {'r2da': 'r2ea', 'r2dk': 'r2eb', 'r2dy': 'r2ec', 'r2dz': 'r2ed'}
MEANINGS = {
    'r2ea': '同じ本人の内的構成が現在の未成熟へ寄与するr2ctと、実際の過程による程度の増加・現在までの近接域の保持r2cpを結ぶ。生の測定の一意性を保ち、外的更新もその都度の決定もない共同の比較r2czで程度を検査する。指導下の経験や特定の形成原因を必須にしない。以前は決め直したときだけ寄与した場合も、自律的な寄与の程度が進んだことを表せる。',
    'r2eb': '同じ基準の性向尺度列、順序、近接域、両端、生の測定をr2eaへ結び、同じ本人の内的構成を取る。具体的な形成経験を補わず、現在の内的寄与、実際の程度変化、結果状態の保持を残す。',
    'r2ec': '同じ非空の人の範囲の各人について、本性に近い後天的な定着r2ebと自己作業による離脱の非容易性r2dxを同じ人物へ結ぶ。未成熟は先行するbfと同じ内容であり、生来の性質や全員の達成可能性を主張しない。',
    'r2ed': '第一文のr2ecを同じ著者・談話箇所・基準へ引用して帰属し、先行する同じ六箇所からの帰結提示と本文順序を保持する。本文の主張を記述するもので、その主張の現実の真理や推論の正しさは評価しない。',
}
LIMITS = [
    '本性に近いという句を、後天的に内側から維持される性向が、外的更新とその都度の選び直しを要さず働く程度を増し、現在は近接域にあるという読みで具体化する。自然一般や先天的起源の定義ではない。',
    'gewordenenの変化過程と現在までの結果状態を要求するが、その過程が必ず他人の指導下の経験だったとはしない。旧r2csは指導経験を明示したい場合の語彙として保存する。',
    '共同の比較条件で一つの程度を評価する。以前の外的更新なしの比較では決め直した場合に寄与していたとしても、それだけで以前から選び直し不要だったとはしない。二つの異なる比較範囲へ同じ下端を要求する旧接続を取り除く。',
    '近接域は完全な上端を除くという読みを採る。全ての反対意思に抗して働くこと、いかなる方法でも抑制できないこと、完全な無意識をこの句へ加えない。後年の習慣論の全条件を1784年の比喩へ逆輸入しない。',
    '候補の背景、測定、近接域、力の尺度・帯、人物範囲は公開規約に従う文脈入力であり、主張の結果に合わせて変更しない。未知を低い値や不存在へ補わない。',
    'この肯定の単独文では、形容的説明と離脱の困難を同じ人物について併記する読みを採る。形容的説明の背景としての役割は読解記録に分け、埋込みや否定に対する一般的な前提投射規則まで実証したとはしない。',
    '第52文だけを更新し、先行51文、旧定義、十二単位のレビューを保つ。一文の意味判断は採用した読解の下でのアシスタントによる判断であり、独立査読や同義性の自動証明ではない。段落の残りとアインシュタイン論文は未完である。',
]


@lru_cache(None)
def parent(): return load_catalog(ROOT, PARENT_BASIS)


def revised_nature(old):
    row = deepcopy(old.entries['r2cv']['declaration'])
    body = row['body']['body']
    assert body['kind'] == 'and' and body['arguments'][0]['content']['symbol'] == 'r2cs'
    row['body']['body'] = body['arguments'][1]
    row = replace_symbols(row, {'r2cu': 'r2cz'})
    row['name'] = 'r2ea'
    return row


def build():
    old = parent(); doc = deepcopy(old.document)
    assert not set(MEANINGS) & set(old.entries)
    size = len(doc['declarations']); doc['declarations'].append(revised_nature(old))
    for name in ('r2dk', 'r2dy', 'r2dz'):
        row = replace_symbols(deepcopy(old.entries[name]['declaration']), MAPPING)
        row['name'] = MAPPING[name]; doc['declarations'].append(row)
    assert len(doc['statements']) == 52 and doc['statements'][-1]['body']['content']['symbol'] == 'r2dz'
    doc['statements'][-1] = replace_symbols(doc['statements'][-1], MAPPING)
    doc = parse(format_graph(doc, 'compact'))
    core = deepcopy(doc); core.update(declarations=closure(doc, list(MEANINGS) + ['wh']), statements=[doc['statements'][-1]])
    added = doc['declarations'][size:]; assert len(added) == 4
    basis = dict(status='nature_like_acquisition_without_prescribed_training_origin', document=FULL, parent=PARENT,
        inherited_meaning_basis=PARENT_BASIS, primitives={}, definitions=MEANINGS,
        new_signatures={d['name']: {key: d[key] for key in ('parameters', 'result')} for d in added}, limitations=LIMITS)
    body = format_graph(doc, 'compact') + '\n'
    annotations = json.loads((ROOT / 'data/assessed-difficulty-identifiers-v1.json').read_text(encoding='utf-8'))
    annotations.update(document=FULL, document_sha256=digest(body.encode('utf-8')))
    encode = lambda value: json.dumps(value, ensure_ascii=False, indent=2) + '\n'
    return {FULL: body, CORE: format_graph(core, 'compact') + '\n', BASIS: encode(basis), ANNOTATIONS: encode(annotations)}


if __name__ == '__main__':
    from scripts.audit_opening_scope import write_exact
    for path, body in build().items(): write_exact(ROOT / path, body)
    print('Four definitions, no new inputs; the first sentence rebound', flush=True)
