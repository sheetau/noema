"""Review both full units of volume naming and simple-calculation presentation."""
from functools import lru_cache
import json
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import REQUIREMENTS,digest,selection_binding,validate_hashes,validate_review
from noema.review_registry import merge_pins
from scripts.compose_light_volume_ratio import ROOT,read,FULL,CORE,BASIS,ANNOTATIONS,LIMITS,MEANINGS,INDEX
from scripts.read_light_volume_ratio import INVENTORY,SOURCE,DOC,READING,PRIOR,REASONS

REPORT='reports/light-volume-ratio-v1.json'
REVIEWS=['data/einstein-light-volume-ratio-u0208-review-v1.json','data/einstein-light-volume-ratio-u0209-review-v1.json']

@lru_cache(None)
def records():
    catalog=load_catalog(ROOT,BASIS);inv=json.loads(read(INVENTORY));reading=json.loads(read(READING));paths={FULL,CORE,BASIS,ANNOTATIONS,INVENTORY,SOURCE,DOC,READING,REPORT,PRIOR,'scripts/review_light_volume_ratio.py','tests/test_light_volume_ratio_review.py'}
    pins={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)};merge_pins(pins,catalog.source_sha256)
    for p in (REPORT,READING,PRIOR):
        evidence=json.loads(read(p));validate_hashes(ROOT,evidence['source_sha256']);merge_pins(pins,evidence['source_sha256'])
    out=[]
    for i,segment in enumerate(reading['segments']):
        u=inv['units'][207+i];text=u['text'];assert segment['source']==text and segment['unit_sha256']==u['text_sha256']
        source=dict(inventory=INVENTORY,unit_sha256=u['text_sha256'],text=text,range=[0,len(text)],math=[dict(id=m['id'],sha256=m['sha256']) for m in segment['math']])
        reason=('同じ球とこの楕円体の内部の二体積をekpa/ekpbとeisloでS/S′に命名する。積分とcosφ=aを前提とする計算列を同じ比の帰結へ接続し、その容易性を著者に帰属する。コロンから次の式を導入する。' if i==0 else 'ekox/ekoyでS′/S=√(1−(v/V)²)/(1−(v/V)cosφ)を構成し、ekpeで同じ設定と二体積へ接続する。根号、余弦、減算、分子分母の向きと直前の命名・計算の表示を保持する。')
        reasons=list(REASONS);reasons[1]=reason;reasons[-1]=f'{u["id"]}を隣接する本文・式と一続きの文として再読し、明示した同時断面・量名・計算評価の読みの下で、全内容・参照・条件・提示を記述したと判断する。'
        out.append(dict(schema_version='noema-semantic-review-1',work='einstein-1905',unit=u['id'],reviewer='assistant_review',decision='equivalent_under_stated_reading',document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source=source,selection=selection_binding(catalog,[INDEX]),clauses=[dict(range=[0,len(text)],text=text,statements=[INDEX],definitions=list(MEANINGS),reason=reason)],interpretation=LIMITS,limits=['明示した読みの下でのアシスタントによる判断であり、独立査読又は意味同義性の自動証明ではない。','既存積分と今回の有理補題は範囲を限定した証拠であり、全実数の積分論、物理理論又は具体的な省略計算の実施済み履歴を機械的に証明したとはしない。','次のE/E′命名と総量比及び二作品全体は未完。'],unresolved=[],requirements=[dict(id=k,decision='satisfied',reason=v) for k,v in zip(REQUIREMENTS,reasons)],evidence=dict(source_reading=[SOURCE,READING],formal_checks=[REPORT],semantic_reading=[DOC]),reviewed_prose_characters=segment['reviewed_prose_characters'],source_sha256=pins))
    return out

def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,r in zip(REVIEWS,records()):write_exact(ROOT/p,json.dumps(r,ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    active=dict(document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source_inventory=INVENTORY);catalog=load_catalog(ROOT,BASIS);inv=json.loads(read(INVENTORY));pins={}
    for p,r in zip(REVIEWS,records()):
        assert json.loads(read(p))==r;validate_review(ROOT,p,'einstein-1905',active,catalog,inv);merge_pins(pins,r['source_sha256']);pins[p]=digest((ROOT/p).read_bytes())
    return dict(status='same_light_volumes_named_and_ratio_whole_units_reviewed',document=FULL,source_units={r['unit']:r['reviewed_prose_characters'] for r in records()},reviewed_math_elements=3,whole_units_semantically_verified=True,verified_full_units={'kant-1784':0,'einstein-1905':2},semantic_equivalence_automatically_proved=False,source_sha256=pins)
