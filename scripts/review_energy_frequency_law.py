"""Review the whole common-law and noteworthy-appraisal sentence."""
from functools import lru_cache
import json
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import REQUIREMENTS,digest,selection_binding,validate_hashes,validate_review
from noema.review_registry import merge_pins
from scripts.compose_energy_frequency_law import ROOT,read,FULL,CORE,BASIS,ANNOTATIONS,LIMITS,MEANINGS,INDEX
from scripts.read_energy_frequency_law import INVENTORY,SOURCE,DOC,READING,PRIOR,REASONS

REPORT='reports/energy-frequency-law-v1.json'
REVIEW='data/einstein-energy-frequency-law-u0214-review-v1.json'

@lru_cache(None)
def record():
    catalog=load_catalog(ROOT,BASIS);inv=json.loads(read(INVENTORY));reading=json.loads(read(READING));paths={FULL,CORE,BASIS,ANNOTATIONS,INVENTORY,SOURCE,DOC,READING,REPORT,PRIOR,'scripts/review_energy_frequency_law.py','tests/test_energy_frequency_law_review.py'}
    pins={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)};merge_pins(pins,catalog.source_sha256)
    for p in (REPORT,READING,PRIOR):
        evidence=json.loads(read(p));validate_hashes(ROOT,evidence['source_sha256']);merge_pins(pins,evidence['source_sha256'])
    u=inv['units'][213];text=u['text'];segment=reading['segments'][0];assert segment['source']==text and segment['unit_sha256']==u['text_sha256']
    source=dict(inventory=INVENTORY,unit_sha256=u['text_sha256'],text=text,range=[0,len(text)],math=[])
    reason='同じ放射部分の平均総エネルギーと同じ観測者の受信周期数を、同じ70設定の二つの一般則から同じ運動倍率seckへ結ぶ。65役割の全許容割当での同じ関数形を述べ、同じ内容への注意価値を別に著者へ帰属する。'
    return dict(schema_version='noema-semantic-review-1',work='einstein-1905',unit=u['id'],reviewer='assistant_review',decision='equivalent_under_stated_reading',document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source=source,selection=selection_binding(catalog,[INDEX]),clauses=[dict(range=[0,len(text)],text=text,statements=[INDEX],definitions=list(MEANINGS),reason=reason)],interpretation=LIMITS,limits=['明示した読みの下でのアシスタントによる判断であり、独立査読又は意味同義性の自動証明ではない。','有限検査は全実数域の物理法則を証明しない。総量・周期・観測者の既存証拠は依存定義と意味の不変性を確認して再利用する。','後続の完全鏡と反射の議論及び二作品全体は未完。'],unresolved=[],requirements=[dict(id=k,decision='satisfied',reason=v) for k,v in zip(REQUIREMENTS,REASONS)],evidence=dict(source_reading=[SOURCE,READING],formal_checks=[REPORT],semantic_reading=[DOC]),reviewed_prose_characters=133,source_sha256=pins)

def prepare():
    from scripts.audit_opening_scope import write_exact
    write_exact(ROOT/REVIEW,json.dumps(record(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    active=dict(document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source_inventory=INVENTORY);catalog=load_catalog(ROOT,BASIS);inv=json.loads(read(INVENTORY));r=record()
    assert json.loads(read(REVIEW))==r;validate_review(ROOT,REVIEW,'einstein-1905',active,catalog,inv);pins=dict(r['source_sha256']);pins[REVIEW]=digest((ROOT/REVIEW).read_bytes())
    return dict(status='same_energy_frequency_motion_law_and_attention_whole_unit_reviewed',document=FULL,source_units={r['unit']:133},reviewed_math_elements=0,whole_units_semantically_verified=True,verified_full_units={'kant-1784':0,'einstein-1905':1},semantic_equivalence_automatically_proved=False,source_sha256=pins)
