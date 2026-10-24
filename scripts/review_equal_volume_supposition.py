"""Read the equal-volume conditional without claiming completion of u0203."""
from functools import lru_cache
import json,re
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,selection_binding,validate_hashes,REQUIREMENTS
from scripts.compose_equal_volume_supposition import ROOT,read,FULL,BASIS,INDEX,LIMITS

INVENTORY='artifacts/written-units-v1/einstein-1905.json'
SOURCE='data/einstein-radiative-density-reading-v1.json';DOC='docs/equal-volume-supposition-v1.md'
READING='data/einstein-equal-volume-supposition-sentence-reading-v1.json'
REASONS=(
 '原刊913頁と固定転記のu0203[164,389)を照合した。Es wäreからdas gleiche wäreまでを第二文として通読し、本文174非空白文字・M0351=A′²/A²・M0352=K・M0353=kを保持する。後続Dies ist jedoch nicht der Fallは含めない。',
 '先行の二つの平均密度と総量への関係ekmu、同体積の仮の構成ekms、同じ比較値からの比の条件内容ekmr、思考上の想定eislz・daherの帰結提示zc・条件文の主張uhを分けて接続した。',
 'eines bestimmten Lichtkomplexesを直後の球面による考察へ続く同じ部分zvaaとして読む。K,V,部分,先行波の範囲,状況を固定し、残る65役割と独立な比較体積を量化する。両系の単位・振幅・密度・総量が同じ物理的設定に属し、比較で別の光を選ばない。',
 'Es wäre ... wenn ... das gleiche wäreは同じ振幅・密度の下で体積を等しく仮置きする思考上の条件付き計算としてeislzと含意に保持する。daherは先行の密度説明からこの条件内容が従うというzcへ結ぶ。現実の等体積、実験完了又は物理的な可能世界の実現を要求しない。',
 '新系で測るエネルギーが分子、旧系で測るエネルギーが分母となる。同じ旧側の正の分母を保持し、比はE′A²=EA′²で記述する。実際の新系体積newvolumeと、仮に旧体積に等しいとするhypovolumeを分け、後者からの候補総量を計算する。',
 '部分・領域・平均密度・単位・空間積分は既存ekmi/ekmjに接続し、数値だけの名札にしない。一般の一様密度の代数規則ekmmも保持する。今回の新しい原始記号は文章箇所への参照一件だけで、文全体の意味を新しい関係へ隠していない。',
 '実際の旧新体積が異なる標本でも旧体積を使った比較が成立し、仮の新総量と実際の新総量が異なることを検査する。全65/66量化役割、独立な比較値、引用・根拠・帰結の向きと同じ著者への帰属を対照し、旧386主張及び旧判断を保存する。',
 '第二文を先行密度説明と後続の同じ光の部分の考察と合わせて再読した。明示した平均総量・同じ特定部分・思考上の等体積比較の読みで、条件・対象・比・根拠・帰属を欠落なく記述したと判断する。u0203残部とu0204–u0205全体は未完。',
)

@lru_cache(None)
def build_reading():
    unit=json.loads(read(INVENTORY))['units'][202];source=unit['text'][164:389]
    assert source.startswith('Es wäre daher ') and source.endswith('das gleiche wäre.')
    assert re.findall(r'\[M\d+\]',source)==['[M0351]','[M0352]','[M0353]']
    assert len(re.sub(r'\s','',re.sub(r'\[M\d+\]','',source)))==174
    validate_hashes(ROOT,json.loads(read(SOURCE))['source_sha256'])
    catalog=load_catalog(ROOT,BASIS)
    symbols=['ekmn','ekmo','ekmp','ekmq','ekmt','ekmv','ekms','ekmr','ekmu','ekmw','ekmx','ekmy','ekmi','ekmj','eistm','eislz','zc','uh','eisd3','zvaa']
    assert all(n in catalog.entries for n in symbols) and len(REASONS)==len(REQUIREMENTS)
    paths=[INVENTORY,DOC,SOURCE,'reports/mean-light-energy-v1.json','reports/light-region-slices-v1.json','data/einstein-density-unit-scope-sentence-reading-v1.json','scripts/review_equal_volume_supposition.py']
    return dict(schema_version='noema-sentence-reading-1',status='sentence_content_and_presentation_checked_under_explicit_reading',reviewer='assistant_close_reading',document=FULL,meaning_basis=BASIS,unit=unit['id'],range=[164,389],source=source,source_text_sha256=unit['text_sha256'],source_nonblank_characters=sum(not c.isspace() for c in source),reviewed_prose_characters=174,reviewed_math_elements=3,selection=selection_binding(catalog,[INDEX]),requirements=[dict(id=k,judgment='preserved_under_stated_reading',reason=v) for k,v in zip(REQUIREMENTS,REASONS)],definitions=symbols,interpretation_limits=LIMITS,whole_paragraph_complete=False,verified_full_units=0,semantic_equivalence_automatically_proved=False,remaining_in_paragraph=['体積不一致の一般性の読み','u0204を挟む球面運動と無流出入・同じ光の集合','新系の総エネルギーの問いとd.h.'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in paths})
