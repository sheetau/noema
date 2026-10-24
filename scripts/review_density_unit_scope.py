"""Supersede the first density sentence's overly broad energy-unit domain."""
from functools import lru_cache
import json
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,selection_binding,REQUIREMENTS
from scripts.compose_density_unit_scope import ROOT,read,FULL,BASIS,INDEX,LIMITS
from scripts.review_density_relativity import INVENTORY,SOURCE,REASONS as PRIOR_REASONS

DOC='docs/density-unit-scope-v1.md';READING='data/einstein-density-unit-scope-sentence-reading-v1.json'
PRIOR='data/einstein-density-relativity-sentence-reading-v1.json'
REASONS=list(PRIOR_REASONS)
REASONS[1]='旧系密度eklq、同じ相対性原理eifjとの根拠ekls、必須の新系適用eklr、著者の帰結提示zcと主張uhを分ける。旧新の同じ60役割へ校正を含む前件eklpを使い、未校正の個体を単位候補へ含めない。'
REASONS[4]='同じ文前半からpro Volumeneinheitを補い、各系の周期平均密度と読む。両系の同じエネルギー単位の校正を基礎設定へ置くが、密度モデルの採用とその平均値は結論側に残す。零振幅を排除せず、同体積の条件や球面を先取りしない。'
REASONS[6]='前候補の物理式・周期・量化接続の検査を引き継ぎ、校正の欠落による過剰な適用域を新たな対照で修正した。旧新それぞれの校正と全引数の同一性、未校正域の除外、同じ60量化役割及び帰結提示を検査した。旧385主張は保持する。'
REASONS[7]='第一文を再読し、校正された共通単位の下で旧系密度の説明から相対性原理により新系の説明へ進むという明示した読みで、内容と提示を欠落なく記述したと判断する。前候補の読解判断は本版で置き換える。u0203全体と後続の光の集合は未完。'

@lru_cache(None)
def build_reading():
    unit=json.loads(read(INVENTORY))['units'][202];source=unit['text'][:163];assert source.endswith('zu betrachten.')
    catalog=load_catalog(ROOT,BASIS);symbols=['ekle','eklp','eklg','eklh','eklq','eklr','ekls','eklt','eklu','eklv','eiste','eistj','eifj','ekll','zc','uh']
    assert all(n in catalog.entries for n in symbols)
    paths=[INVENTORY,DOC,SOURCE,PRIOR,'docs/density-relativity-v1.md','reports/density-relativity-v1.json','reports/radiative-density-v1.json','scripts/review_density_unit_scope.py','scripts/review_density_relativity.py']
    return dict(schema_version='noema-sentence-reading-1',status='sentence_content_and_presentation_checked_under_explicit_reading',reviewer='assistant_close_reading',document=FULL,meaning_basis=BASIS,unit=unit['id'],range=[0,163],source=source,source_text_sha256=unit['text_sha256'],source_nonblank_characters=141,reviewed_prose_characters=127,reviewed_math_elements=2,selection=selection_binding(catalog,[INDEX]),requirements=[dict(id=k,judgment='preserved_under_stated_reading',reason=v) for k,v in zip(REQUIREMENTS,REASONS)],definitions=symbols,interpretation_limits=LIMITS,supersedes_for_current_snapshot=PRIOR,whole_paragraph_complete=False,verified_full_units=0,semantic_equivalence_automatically_proved=False,remaining_in_paragraph=['同体積ならという反実仮想','実際の体積不一致','u0204を挟む動く球面と同じ光の集合','新系の総エネルギーの問いとd.h.'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in paths})
