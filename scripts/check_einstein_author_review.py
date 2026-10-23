"""Bind the independently stated reading of the complete printed author credit."""
from functools import lru_cache
from noema.semantic_reviews import REQUIREMENTS, digest, selection_binding, validate_review
from scripts.check_einstein_author_credit import (
    ROOT, FULL, BASIS, ANNOTATIONS, INDEX, SOURCE, INVENTORY, DOC, REPORT, catalog, record)

REVIEW = 'data/einstein-author-credit-review-v1.json'
REASONS = (
    '固定転記u0002全16文字・14非空白文字を原刊891頁のvon A. Einstein.と照合した。数式はない。表題前の配列番号3.は別の版面情報として照合記録に残している。',
    '名称使用の成立、名称を同じ対象へ適用する関係、同じ文書の著者として表示する役割を合成した。単なる名前の出現から著者性を補わず、同じ表示行為・人物・文書・文脈を結んだ。',
    'eirdは名称、eireはこの前付の表示、eirfは当該論説、eirgは前付文脈、rdは既存本文と共通の著者参照である。名称個体を人物へ同一化せず、他文書や他人の署名へ取り替えない。',
    'vonによる著者表示として読む。理論内容の真理、自筆署名、物理的な印刷者、表示の歴史的な真正性を主張する単位としては扱わない。',
    'A. Einsteinの識別表記を保持し、A.を本単位の記述内でAlbertへ展開しない。末尾の句点は表示の区切りで、名称の構成部分にしない。表題の主題や隣接する導入段落を確認範囲へ含めない。',
    '既存の一般定義rqqxの本体・引数・意味をeiaaへ保存した。成立・名称適用・著者表示の三関係と四参照、rd、eiabの全依存規約を確認し、原語一文を不透明な基本関係へ置き換えない。',
    '原刊の視認・単位全体の通読と、三関係の8組合せ、全10引数位置の対照、名称と人物の同一化拒否、未知入力拒否、旧206主張の保持、表記往復の検査を分けた。有限検査だけから意味同値を認定しない。',
    'von A. Einstein.を論説の前付の著者表示として再読し、同じ名称と既存著者参照、論説、表示の役割、区切りを欠落なく結ぶと判断した。この短い単位に未処理項目はないが、表題と導入段落は未完である。',
)


def review_record():
    c=catalog();u=record(INVENTORY)['units'][1]
    evidence=dict(source_reading=[SOURCE],formal_checks=[REPORT],semantic_reading=[DOC])
    pins=dict(c.source_sha256)
    for p in (SOURCE,REPORT):
        for name,value in record(p)['source_sha256'].items():
            assert name not in pins or pins[name]==value
            pins[name]=value
    for p in (SOURCE,REPORT,DOC,INVENTORY,ANNOTATIONS,'scripts/check_einstein_author_review.py'):
        pins[p]=digest((ROOT/p).read_bytes())
    return dict(schema_version='noema-semantic-review-1',work='einstein-1905',unit=u['id'],
        reviewer='assistant_review',decision='equivalent_under_stated_reading',
        document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,
        source=dict(inventory=INVENTORY,unit_sha256=u['text_sha256'],text=u['text'],range=[0,len(u['text'])],math=[]),
        selection=selection_binding(c,[INDEX]),
        interpretation=['前付のvon A. Einstein.を、この名称が示す人物を同じ論説の著者として表示するものと読む。表示の実行者と著者を同一視しない。'],
        limits=['明示した読みの下でのアシスタントの判断であり、独立査読、自動同義証明、著者同定の歴史学的な証明ではない。',
            '短い前付一単位の判断である。表題の主題、導入の電磁現象、本文と全数式の意味確認は未完。'],
        unresolved=[],requirements=[dict(id=k,decision='satisfied',reason=v) for k,v in zip(REQUIREMENTS,REASONS,strict=True)],
        evidence=evidence,source_sha256=pins)


def prepare():
    from scripts.audit_opening_scope import write_exact,encoded
    write_exact(ROOT/REVIEW,encoded(review_record()))


@lru_cache(None)
def build_report():
    assert record(REVIEW)==review_record()
    active=dict(document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source_inventory=INVENTORY)
    result=validate_review(ROOT,REVIEW,'einstein-1905',active,catalog(),record(INVENTORY))
    return dict(status='einstein_author_credit_whole_unit_review_bound',document=FULL,
        unit=result['unit'],source_nonblank_characters=result['source_nonblank_characters'],
        whole_unit_semantically_verified=True,semantic_equivalence_automatically_proved=False,
        source_sha256=record(REVIEW)['source_sha256']|{REVIEW:digest((ROOT/REVIEW).read_bytes())})
