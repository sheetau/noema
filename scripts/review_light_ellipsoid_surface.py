"""Review both full units of the same-surface ellipsoid and equation sentence."""
from functools import lru_cache
import json
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import REQUIREMENTS,digest,selection_binding,validate_hashes,validate_review
from noema.review_registry import merge_pins
from scripts.compose_light_ellipsoid_surface import ROOT,read,FULL,CORE,BASIS,ANNOTATIONS,LIMITS,MEANINGS,INDEX
from scripts.read_light_ellipsoid_surface import INVENTORY,SOURCE,DOC,READING,PRIOR,REASONS

REPORT='reports/light-ellipsoid-surface-v1.json'
REVIEWS=['data/einstein-light-ellipsoid-surface-u0206-review-v1.json','data/einstein-light-ellipsoid-surface-u0207-review-v1.json']

@lru_cache(None)
def records():
    catalog=load_catalog(ROOT,BASIS);inv=json.loads(read(INVENTORY));reading=json.loads(read(READING));paths={FULL,CORE,BASIS,ANNOTATIONS,INVENTORY,SOURCE,DOC,READING,REPORT,PRIOR,'scripts/review_light_ellipsoid_surface.py','tests/test_light_ellipsoid_surface_review.py'}
    pins={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)};merge_pins(pins,catalog.source_sha256)
    for p in (REPORT,READING,PRIOR):
        evidence=json.loads(read(p));validate_hashes(ROOT,evidence['source_sha256']);merge_pins(pins,evidence['source_sha256'])
    out=[]
    for i,segment in enumerate(reading['segments']):
        u=inv['units'][205+i];text=u['text'];assert segment['source']==text and segment['unit_sha256']==u['text_sha256']
        source=dict(inventory=INVENTORY,unit_sha256=u['text_sha256'],text=text,range=[0,len(text)],math=[dict(id=m['id'],sha256=m['sha256']) for m in segment['math']])
        reason=('同じ球面をkで見た全時刻の楕円体面としてekosに述べ、τ=0の方程式ekotをコロンで導入する。ダッシュ内は考察する系の指定であり、光学像へ替えない。' if i==0 else '全三差の平方と右辺R²をekopで構成し、同じ球面のk時刻零断面との双方向の所属一致をekorへ結ぶ。数式のみを別対象の主張として切り離さず、直前のコロンの表示として帰属する。')
        reasons=list(REASONS);reasons[1]=reason;reasons[-1]=f'{u["id"]}を隣接する本文・式と一続きの文として再読し、明示した可逆線形像・同じ部分・校正座標の読みの下で、全内容・参照・条件・提示を記述したと判断する。'
        out.append(dict(schema_version='noema-semantic-review-1',work='einstein-1905',unit=u['id'],reviewer='assistant_review',decision='equivalent_under_stated_reading',document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source=source,selection=selection_binding(catalog,[INDEX]),clauses=[dict(range=[0,len(text)],text=text,statements=[INDEX],definitions=list(MEANINGS),reason=reason)],interpretation=LIMITS,limits=['明示した読みの下でのアシスタントによる判断であり、独立査読又は意味同義性の自動証明ではない。','可逆線形像の幾何学の意味を使うが全実数の主軸定理・位相的性質・物理的妥当性の機械的証明を主張しない。','次の体積の命名・比、以後の総量比及び二作品全体は未完。'],unresolved=[],requirements=[dict(id=k,decision='satisfied',reason=v) for k,v in zip(REQUIREMENTS,reasons)],evidence=dict(source_reading=[SOURCE,READING],formal_checks=[REPORT],semantic_reading=[DOC]),reviewed_prose_characters=segment['reviewed_prose_characters'],source_sha256=pins))
    return out

def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,r in zip(REVIEWS,records()):write_exact(ROOT/p,json.dumps(r,ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    active=dict(document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source_inventory=INVENTORY);catalog=load_catalog(ROOT,BASIS);inv=json.loads(read(INVENTORY));pins={}
    for p,r in zip(REVIEWS,records()):
        assert json.loads(read(p))==r;validate_review(ROOT,p,'einstein-1905',active,catalog,inv);merge_pins(pins,r['source_sha256']);pins[p]=digest((ROOT/p).read_bytes())
    return dict(status='same_light_boundary_ellipsoid_and_zero_time_equation_whole_units_reviewed',document=FULL,source_units={r['unit']:r['reviewed_prose_characters'] for r in records()},reviewed_math_elements=2,whole_units_semantically_verified=True,verified_full_units={'kant-1784':0,'einstein-1905':2},semantic_equivalence_automatically_proved=False,source_sha256=pins)
