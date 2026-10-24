"""Read the third sentence under an explicit unqualified schematic denial."""
from functools import lru_cache
import json
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,selection_binding,validate_hashes,REQUIREMENTS
from scripts.compose_volume_denial import ROOT,read,FULL,BASIS,INDEX,LIMITS

INVENTORY='artifacts/written-units-v1/einstein-1905.json'
SOURCE='data/einstein-radiative-density-reading-v1.json';DOC='docs/volume-denial-v1.md'
READING='data/einstein-volume-denial-sentence-reading-v1.json'
REASONS=(
 '原刊913頁と固定原文u0203[390,421)のDies ist jedoch nicht der Fall.を前後と合わせて通読した。本文26非空白文字・数式要素0。前の第二文と後のSindからの球面説明は境界で区別する。',
 '同じ物理的平均総量設定ekmoの実際の二体積をekl6へ結ぶekmz、その否定ekm2、各設定での否定ekm3を合成する。第二文の仮の比較体積hypovolume又は比の含意全体を否定対象へ取り違えない。',
 'Diesは同じ第二文eistnの等体積の仮置きekmsを受けるという読みで、eisraに先行・現在内容を指定する。K/V/波範囲/同じ部分zvaa/状況を固定し、残る65役割の共有により実際の両系の体積を指定する。',
 'jedochを仮置きと実際の不等との対照としてeisnpへ結び、ekm6で同じ物理的な部分という観点を指定する。uhが否定の主張、eisraが後方参照であり、対照だけで否定を代用しない。',
 '量化が原文に明記されないことを開示し、先行図式の各設定で等体積を否定する強い読みを採る。常に等しいわけではないekm5とは分け、著者の主張を検査都合で弱めない。D≠1を前件に追加しない。強い読みへの反例を保存し、物理的な正しさは認定しない。',
 '一般関係は既存eisra/eisnp/uhを再利用し、文箇所への参照eistoだけを追加する。体積・物理的な部分・校正・位相平均・総量の意味はekmoへ接続し、第三文全体を新しい原始関係へ格納しない。',
 'V5,v3,n=(1/3,2/3,2/3)、非零横波振幅A3の等体積例と通常の不等例を検査する。全65束縛位置、否定と量化の順、同じ著者・文脈・参照内容の方向を確認する。有限診断は全実数物理理論又は意味同義性の自動証明ではない。',
 '第一・第二文と続く球面の導入、後続体積式を踏まえて第三文を再読した。明示した強い図式的否定の読みの下で、否定対象・作用域・指示先・対照・著者帰属を記述したと判断する。特殊方向での反例と他の量化の読みを文書に残し、u0203全体の完成は認定しない。',
)

@lru_cache(None)
def build_reading():
    unit=json.loads(read(INVENTORY))['units'][202];source=unit['text'][390:421]
    assert source=='Dies ist jedoch nicht der Fall.' and sum(not c.isspace() for c in source)==26
    validate_hashes(ROOT,json.loads(read(SOURCE))['source_sha256'])
    catalog=load_catalog(ROOT,BASIS)
    symbols=['ekmz','ekm2','ekm3','ekm4','ekm5','ekm6','ekm7','ekna','eknb','ekmo','ekms','ekl6','eisra','eisnp','uh','zvaa']
    assert all(n in catalog.entries for n in symbols) and len(REASONS)==len(REQUIREMENTS)
    paths=[INVENTORY,DOC,SOURCE,'reports/equal-volume-supposition-v1.json','reports/light-region-slices-v1.json','data/einstein-equal-volume-supposition-sentence-reading-v1.json','scripts/review_volume_denial.py']
    return dict(schema_version='noema-sentence-reading-1',status='sentence_content_and_presentation_checked_under_explicit_reading',reviewer='assistant_close_reading',document=FULL,meaning_basis=BASIS,unit=unit['id'],range=[390,421],source=source,source_text_sha256=unit['text_sha256'],source_nonblank_characters=26,reviewed_prose_characters=26,reviewed_math_elements=0,selection=selection_binding(catalog,[INDEX]),requirements=[dict(id=k,judgment='preserved_under_stated_reading',reason=v) for k,v in zip(REQUIREMENTS,REASONS)],definitions=symbols,interpretation_limits=LIMITS,whole_paragraph_complete=False,verified_full_units=0,semantic_equivalence_automatically_proved=False,remaining_in_paragraph=['u0204を挟む球面運動と無流出入・同じ光の集合','新系の総エネルギーの問いとd.h.'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in paths})
