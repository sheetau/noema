"""Register an explicit whole-paragraph reading, without rewriting old reviews."""
from copy import deepcopy
from noema.semantic_reviews import digest, selection_binding, validate_hashes, load_reviews
from scripts.check_deterrence_sentence import (
    ROOT, FULL, BASIS, ANNOTATIONS, INVENTORY, INDEX as PREVIOUS, AUDIT, REPORT, DOC,
    PRECEDING, SELECTION, catalog, read, preceding_checks)

INDEX = 'data/semantic-review-index-v87.json'
REVIEW = 'data/kant-second-paragraph-review-v1.json'
INTERPRETATION = [
    '怠惰・臆病を、自然的成長によって他人の指導から既に解放された多くの人がなお生涯の未成熟を受け入れることと、別の人がその後見役を自称する容易さとの、双方への寄与原因と読む。自然的成人と自立的な理解力の行使能力を混同しない。',
    '未成熟な状態にとどまることの実用上の負担の低さを述べ、同じ仮定の一人称者について、書物・魂の世話をする役・医者の三例を開いた列挙として示す。理解・良心・食生活を含む生活上の養生の判断を代行させる条件と、自分の努力が不要になる帰結を分ける。',
    '同じ仮定の本人について、対価を払える条件の下で自分で考える必要がないことと、別の人がその煩わしい仕事を引き受けるという見通しを示す。著者の実生活、思考不能、既に支払ったこと、仕事の実行完了は追加しない。',
    '同じ人間集団の圧倒的多数に女性全体を含め、自立へ踏み出す行為の負担に加えて非常に危険だと判断させる後見人の働きを述べる。最高の監督を引き受けた同じ後見人について、厚意の装いを批判的距離を伴って提示する。実際の善意や正当な権限は断言しない。',
    '同じ監督対象を利用される家畜として描き、先行する理解不足の造成と、同じ装置の外への勇気ある一歩の許容を注意深く妨げる行為を、後の警告より前に置く。閉じ込めと外的な落ち着きは先行局面に結ぶ。警告では本人が補助なしに歩こうとする場合の危険を示す。',
    '同じ対象者・活動に関する危険を非常に高いとはしない著者の評価へ、少数回の不成功経験の後に能力を得る見込みを理由として結ぶ。失敗候補を残す仮定と認識的優先順位を分け、身体の転倒・歩行学習の像を同じ本人と経験へ結ぶ。',
    'それでも同種の先行例の認識が恐れやすさへ寄与し、通常は関連する後続の試み全てから退かせるという主張を置く。萎縮は通常事例の一般化、回避は同じ比較状況の事例全体に対する頻度として区別する。恐れやすさから個々の回避を自動的に導かない。',
    '段落をまたぐ未成熟・自己の理解力の使用は既存bf・bbを使い、この段落内の後見人・監督対象・活動・装置を共有する。仮定の一人称者を著者waや多数集団の一員へ勝手に同定しない。先行例の経験者と後にそれを認識する人も同一人物に限定しない。',
    '後見人が示す危険と著者による危険評価、能力取得の見込みと現実の取得、身体の描写と知的な内容を別の提示として保つ。最後の反期待は同じ低危険評価と同じ萎縮・回避の内容を比較する。',
]
REASONS = [
    ('fixed_source', '固定電子転記u0009の全1438文字・1211非空白文字を指定し、原刊481頁末尾と482頁の第二段落を目視で再読した。七文の全非空白位置を覆い、表記上の差を意味へ追加しない。'),
    ('semantic_relations', '原因の寄与、解放と未成熟の対比、状態の便宜、代行の条件と帰結、支払い可能性と引受け、負担と危険判断、先行する制限と後の警告、学習を理由とする危険評価、萎縮と頻度的回避を、それぞれの既存定義へ照合した。'),
    ('references', '先行の能力bf・使用bb、人間の母集団mvと危険判断を持つ対象dj、後見人と対象者、同じ身体装置、本人・経験・時点の参照を通読した。先頭の他者と仮定の代行者の個別同一性や、経験者と認識者の同一性は加えない。'),
    ('presentation_role', '著者の主張、仮定の一人称、他者の危険提示、自然の宣言・家畜・歩行の非字義的描写、批判的な厚意の装い、理由と反期待を分ける。引用された内容の真理を提示の成立条件にしない。'),
    ('additions_and_omissions', '先頭六文の読解記録と末尾四節を照合した。列挙の開放性、女性全体、最高の監督、注意と目的、先行時点、少数回、推量、通常性、後続する全試行を保持する。法的成人・正当な権限・生涯の服従・現実の学習成功・危険ゼロ・全生活の回避などは加えない。'),
    ('meaning_conventions', '能力・原因・許容・認知・身体運動・提示の公開規約と、その文脈的な通常性・十分さ・負担・危険・回数・割合を確認した。一般化と頻度を区別し、有限の等重み事例という採用範囲を明示する。'),
    ('evidence_and_limits', '原文・原刊画像による読解、各文の語義と作用範囲、現在の四文の帰属と比喩の独立検査、過去の部分内容検査の依存保存、記法往復を分けて示す。有限モデルの合格からドイツ語との同義を自動推論しない。'),
    ('whole_unit_rereading', '七文を一つの段落として再読し、便宜から代行・後見・制限・危険提示を経て最後の反期待に至る関係を確認した。明記した文脈的読解と意味規約の下で未処理の段落内容はないと判断する。後続段落や語義の全可能性には判断を拡張しない。'),
]


def build():
    old = read(PREVIOUS); load_reviews(ROOT, PREVIOUS)
    report = read(REPORT); validate_hashes(ROOT, report['source_sha256'])
    assert report['review_decision'] == 'equivalent_under_stated_reading_for_this_sentence'
    preceding = preceding_checks()
    indices = sorted(set(SELECTION) | {s['index'] for r in preceding['reviews'].values()
                                      for s in r['current_selection']['statements']})
    assert indices == [2, 3, 4, 5, 6, 7, 8, 9, 35, 36, 37, 38, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50]
    unit = next(u for u in read(INVENTORY)['units'] if u['id'] == 'kant-1784:u0009')
    source_readings = ['data/' + n + '-reading-v1.json' for n in PRECEDING] + [AUDIT]
    paths = set(report['source_sha256']) | {PREVIOUS, REPORT, DOC, ANNOTATIONS, INVENTORY}
    pins = {p: digest((ROOT / p).read_bytes()) for p in sorted(paths)}
    review = dict(schema_version='noema-semantic-review-1', work='kant-1784', unit=unit['id'],
        document=FULL, meaning_basis=BASIS, identifier_annotations=ANNOTATIONS,
        source=dict(inventory=INVENTORY, unit_sha256=unit['text_sha256'], text=unit['text'], range=[0, len(unit['text'])], math=[]),
        selection=selection_binding(catalog(), indices), decision='equivalent_under_stated_reading', reviewer='assistant_review',
        interpretation=INTERPRETATION,
        limits=[
            '固定した本文・意味規約・文脈的読解に対するアシスタント自身の判断。独立した専門家の査読や意味一致の自動証明ではない。',
            '先頭六文と末尾一文の個別読解記録に記した語義・作用範囲・基本関係の限界を継承する。綴り・書体・音韻・全ての語感と歴史的含意の復元ではない。',
            '文脈の有限な母集団・等重み事例、認識された先行の不成功例、補助なしの足移動、局所的な恐れやすさなどの採用読解を明示する。無限母集団や架空例を含む全ての読みを保証しない。',
            '著者が述べる人間集団・性別・原因・見込み・頻度の現実的な正しさは判定しない。基本関係の構成的説明の拡充、後続段落、理系論文と文語体系全体の完成は残る。',
        ], unresolved=[], requirements=[dict(id=k, decision='satisfied', reason=v) for k, v in REASONS],
        evidence=dict(source_reading=source_readings, formal_checks=[REPORT, 'reports/guarded-walking-reading-v1.json'],
                      semantic_reading=[DOC]), source_sha256=pins)
    index = deepcopy(old)
    index['works']['kant-1784']['reviews'].append(REVIEW)
    index['source_sha256'].update(pins)
    from scripts.audit_opening_scope import encoded
    index['source_sha256'][REVIEW] = digest(encoded(review).encode('utf-8'))
    return {REVIEW: encoded(review), INDEX: encoded(index)}


def audit_registration():
    old = load_reviews(ROOT, PREVIOUS); new = load_reviews(ROOT, INDEX)
    before = old['works']['kant-1784']; after = new['works']['kant-1784']
    assert after[:-1] == before and len(after) == 12
    assert after[-1]['unit'] == 'kant-1784:u0009' and after[-1]['source_nonblank_characters'] == 1211
    assert sum(r['source_nonblank_characters'] for r in after) == 2212
    assert new['works']['einstein-1905'] == old['works']['einstein-1905'] == []
    a = read(PREVIOUS); b = read(INDEX)
    assert all(b['source_sha256'][p] == h for p, h in a['source_sha256'].items())
    assert b['works']['kant-1784']['reviews'][:-1] == a['works']['kant-1784']['reviews']
    return dict(previous_reviews_unchanged=11, new_reviewed_nonblank_characters=1211,
                total_reviewed_nonblank_characters=2212, reviewed_units=12, automatic_equivalence_proof=False)


if __name__ == '__main__':
    from scripts.audit_opening_scope import write_exact
    import json
    for path, body in build().items():
        write_exact(ROOT / path, body)
    print(json.dumps(audit_registration(), ensure_ascii=False), flush=True)
