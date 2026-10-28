"""New whole-unit judgment after correcting u0176 locations and text order."""
from copy import deepcopy
from functools import lru_cache
import json

from noema.meaning_catalog import load_catalog
from noema.review_registry import merge_pins
from noema.semantic_reviews import REQUIREMENTS, digest, selection_binding, validate_hashes, validate_review
from scripts import compose_auxiliary_reference_order as correction

ROOT = correction.ROOT
REVIEW = 'data/einstein-auxiliary-reference-order-u0176-review-v1.json'
REPORT = 'reports/einstein-auxiliary-reference-order-review-v1.json'
INDICES = [38, 39, 40, 41]


@lru_cache(None)
def record():
    c = correction
    catalog = load_catalog(ROOT, c.BASIS)
    old = c.read(c.OLD_REVIEW)
    validate_hashes(ROOT, old['source_sha256'])
    source = c.read(c.SOURCE)
    formal = c.read(c.REPORT)
    validate_hashes(ROOT, formal['source_sha256'])
    assert formal['old_order_rejected_by_source_positions']
    assert formal['quoted_physical_content_preserved']
    assert formal['replaced_statement_indices'] == [40, 41]
    assert source['range'] == [0, 344] and source['source_nonblank_characters'] == 302
    assert catalog.document['declarations'][:len(c.parent()['declarations'])] == c.parent()['declarations']
    evidence = dict(source_reading=[c.SOURCE, c.OLD_READING],
                    formal_checks=[c.REPORT, *old['evidence']['formal_checks']],
                    semantic_reading=[c.DOC, *old['evidence']['semantic_reading']])
    pins = dict(catalog.source_sha256)
    merge_pins(pins, old['source_sha256'])
    merge_pins(pins, formal['source_sha256'])
    merge_pins(pins, source['source_sha256'])
    paths = {c.FULL, c.BASIS, c.ANNOTATIONS, c.INVENTORY, c.OLD_REVIEW,
             'scripts/review_auxiliary_reference_order.py'}
    paths.update(p for values in evidence.values() for p in values)
    for path in paths:
        merge_pins(pins, {path: digest((ROOT / path).read_bytes())})
        if path.endswith('.json'):
            merge_pins(pins, c.read(path).get('source_sha256', {}))
    clauses = deepcopy(old['clauses'])
    indices = {169: 38, 170: 39, 171: 40, 172: 41}
    for clause in clauses:
        clause['statements'] = [indices[i] for i in clause['statements']]
        clause['definitions'] = [c.RENAMES.get(n, n) for n in clause['definitions']]
        assert all(n in catalog.entries for n in clause['definitions'])
    clauses[1]['definitions'] += [c.WHOLE, 'magauxwholepresentation']
    clauses[1]['reason'] += ' 主節zpvは末尾の根拠節zptより前にあり、第二文全体の参照を主節と区別する。'
    clauses[2]['definitions'] += [c.WHOLE]
    clauses[2]['reason'] += ' 主張とMan siehtの提示には同じ第二文全体の参照を与える。'
    reasons = [
        '固定u0176の344文字・302非空白文字を原刊910頁の実表示と照合し、類推の第一文とMan siehtからbesitzenまでの第二文を続けて読んだ。原文・数式要素・版を変更しない。第一文、第二文全体、主節、導入理由、末尾の根拠節の文字範囲を保存する。',
        '磁気側の二つの言い方への類推、展開済みの理論、電動力の補助的な役割だけという限定、同じ概念の理論導入とその理由、電気・磁気の作用の系依存性を維持する。非空の全構成的使用と各使用の定義展開を含み、物理的内容ejzv/ejzwとその依存定義は全て同一である。',
        '旧ejzzは末尾の根拠節zptが主節zpvに先行するという逆順を含んでいた。原文範囲に基づきzpv→zptへ訂正する。第二文全体magauxsecondsentenceを導入理由の旧箇所zpwと区別し、第一文zps→第二文全体の順序を与える。主節がそれを含む文全体より前にあるという条件は課さない。welcher/seineの概念証人と、理論・過程・出来事・単位の同一性を維持する。',
        '類推はeisqu、主張はuh、明白さの提示はzdg、著者と論説への帰属はeir3を維持する。新しい全体参照を用いるuhとzdgは、補助概念と導入理由を共に含む同じ閉じたejzwを指定する。主節の部分内容ejzvとの交換を認めず、引用の評価を物理法則の証明としない。',
        '磁極の実在、全場・全速度での変化、電磁過程自体の不存在、一次近似の厳密等値、概念の全理論的保存拡張証明を補わない。有限検査で誤った順序を受容する代わりに原文位置を訂正し、元の条件・量化・留保を保持する。主節と関係節の共有概念を分離しない。',
        '新基本記号は同じ文書内の第二文全体を指す位置参照だけである。補助性と導入理由は既存の公開意味規約と型付き合成による。四つの新定義は参照・本文順序・主張の引用・発話帰属を組み合わせる。旧宣言を全て保存し、綴りや位置だけを物理的意味の代用にしない。',
        '新検査は実際の原文範囲から旧順序を拒否し、修正後の順序、部分と全体の区別、同じ全体内容への提示、未知入力拒否を確認する。既存の物理的本体は宣言の完全一致と以前の固定証拠で照合する。旧提示順序のfixtureは原文順序の証拠として再利用しない。型・往復・有限検査・今回の通読判断の範囲を区別する。',
        '前の二つの言い方から続くu0176全体を再読した。磁気側への類推、補助概念の限定、展開済み理論、同じ概念の導入理由、両種の場の系依存性、Man siehtの全体提示が保持され、本文の主節と根拠節の順序も原文と一致する。既存の明示した物理的解釈の下で、修正した四主張の選択が全単位に対応すると新たに判断する。',
    ]
    assert len(reasons) == len(REQUIREMENTS)
    interpretation = list(old['interpretation'])
    interpretation[-1] = 'Man siehtは著者が第二文全体を明白として提示することを意味する。実在の観察者や実験実施を追加しない。磁動力への類推は既存ejzhの構成を保つ。'
    interpretation += ['主節と根拠節の本文順序を原文位置に合わせ、第二文全体の参照を主節・導入理由の箇所と区別する。']
    return dict(schema_version='noema-semantic-review-1', work='einstein-1905',
        unit=source['unit'], reviewer='assistant_review', decision='equivalent_under_stated_reading',
        document=c.FULL, meaning_basis=c.BASIS, identifier_annotations=c.ANNOTATIONS,
        source=dict(inventory=c.INVENTORY, unit_sha256=source['unit_sha256'], text=source['text'], range=source['range'], math=[]),
        selection=selection_binding(catalog, INDICES), clauses=clauses, interpretation=interpretation,
        supersedes_review=c.OLD_REVIEW,
        correction='本文順序の逆転と第二文全体の提示参照を訂正。旧記録を保存し、原文全体について新たに判断した。',
        limits=['明示した解釈に基づくアシスタントの全単位判断。独立査読・同義性の自動証明ではない。',
                '物理法則の真理、全実数・関数域の有限検査による証明、全理論の保存拡張を主張しない。',
                '円文字への接続と可視復号は次の工程であり、この判断だけでは円文字統合の完了件数を増やさない。'],
        unresolved=[], requirements=[dict(id=name, decision='satisfied', reason=reason) for name, reason in zip(REQUIREMENTS, reasons)],
        evidence=evidence, reviewed_prose_characters=302, source_sha256=pins)


def prepare():
    correction.write_once(REVIEW, record())


@lru_cache(None)
def build_report():
    result = record()
    assert correction.read(REVIEW) == result
    active = dict(document=correction.FULL, meaning_basis=correction.BASIS,
                  identifier_annotations=correction.ANNOTATIONS, source_inventory=correction.INVENTORY)
    validate_review(ROOT, REVIEW, 'einstein-1905', active,
                    load_catalog(ROOT, correction.BASIS), correction.read(correction.INVENTORY))
    pins = dict(result['source_sha256'])
    pins[REVIEW] = digest((ROOT / REVIEW).read_bytes())
    return dict(status='auxiliary_reference_order_whole_unit_rereviewed', document=correction.FULL,
        source_units={result['unit']: 302}, whole_units_semantically_verified=True,
        verified_full_units={'kant-1784': 0, 'einstein-1905': 1},
        semantic_equivalence_automatically_proved=False, replaces_existing_unit_judgment=True,
        source_sha256=pins)
