"""Review all four units of the enclosed energy ratio and its zero-angle form."""
from functools import lru_cache
import json
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import REQUIREMENTS,digest,selection_binding,validate_hashes,validate_review
from noema.review_registry import merge_pins
from scripts.compose_light_energy_ratio import ROOT,read,FULL,CORE,BASIS,ANNOTATIONS,LIMITS,MEANINGS,INDEX
from scripts.read_light_energy_ratio import INVENTORY,SOURCE,DOC,READING,PRIOR,REASONS

REPORT='reports/light-energy-ratio-v1.json'
REVIEWS=[f'data/einstein-light-energy-ratio-u{n:04d}-review-v1.json' for n in range(210,214)]
CLAUSES=[
 '同じ面が囲む同じ放射部分の旧系と新系の平均総量を、ekpmの各系の空間積分とekpo/ekppの取得規則へ結び、E/E′と命名する。先行する密度・振幅・体積から一般比へという帰結とコロンを保持する。',
 'E′/E、(A′²S′/(8π))/(A²S/(8π))、(1−(v/V)cosφ)/√(1−(v/V)²)の二つの等号をekplで同じ値へ結ぶ。根号は最後の分母、各密度は対応する体積に掛かる。コンマで次の関係節へ続く。',
 'welche Formelを直前の同じ一般式へ結び、同じ実数角φ=0をekptに課す。同じ条件で一般形から特殊形へ移る提示eissbと、後者が前者より簡明という厳密比較eistb及びコロンを保持する。',
 '同じ二総量のE′/E=√((1−v/V)/(1+v/V))をekpu/ekpvで構成し、同じ零角設定のekpxとして表示する。差と和、比全体の正の平方根、直前の関係節と句点を保つ。',
]

@lru_cache(None)
def records():
    catalog=load_catalog(ROOT,BASIS);inv=json.loads(read(INVENTORY));reading=json.loads(read(READING));paths={FULL,CORE,BASIS,ANNOTATIONS,INVENTORY,SOURCE,DOC,READING,REPORT,PRIOR,'scripts/review_light_energy_ratio.py','tests/test_light_energy_ratio_review.py'}
    pins={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)};merge_pins(pins,catalog.source_sha256)
    for p in (REPORT,READING,PRIOR):
        evidence=json.loads(read(p));validate_hashes(ROOT,evidence['source_sha256']);merge_pins(pins,evidence['source_sha256'])
    out=[]
    for i,segment in enumerate(reading['segments']):
        u=inv['units'][209+i];text=u['text'];assert segment['source']==text and segment['unit_sha256']==u['text_sha256']
        source=dict(inventory=INVENTORY,unit_sha256=u['text_sha256'],text=text,range=[0,len(text)],math=[dict(id=m['id'],sha256=m['sha256']) for m in segment['math']])
        reason=CLAUSES[i];reasons=list(REASONS);reasons[1]=reason;reasons[-1]=f'{u["id"]}を隣接する本文・式・関係節と一続きの文として再読し、明示した同時内部・平均総量・量名・零角と比較の読みの下で全内容を記述したと判断する。'
        out.append(dict(schema_version='noema-semantic-review-1',work='einstein-1905',unit=u['id'],reviewer='assistant_review',decision='equivalent_under_stated_reading',document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source=source,selection=selection_binding(catalog,[INDEX]),clauses=[dict(range=[0,len(text)],text=text,statements=[INDEX],definitions=list(MEANINGS),reason=reason)],interpretation=LIMITS,limits=['明示した読みの下でのアシスタントによる判断であり、独立査読又は意味同義性の自動証明ではない。','有限検査と有理補題は全実数域の積分論・平方根の存在又は物理理論を機械的に証明したとはしない。','後続の周波数との変換法則の同一性、完全鏡の議論及び二作品全体は未完。'],unresolved=[],requirements=[dict(id=k,decision='satisfied',reason=v) for k,v in zip(REQUIREMENTS,reasons)],evidence=dict(source_reading=[SOURCE,READING],formal_checks=[REPORT],semantic_reading=[DOC]),reviewed_prose_characters=segment['reviewed_prose_characters'],source_sha256=pins))
    return out

def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,r in zip(REVIEWS,records()):write_exact(ROOT/p,json.dumps(r,ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    active=dict(document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source_inventory=INVENTORY);catalog=load_catalog(ROOT,BASIS);inv=json.loads(read(INVENTORY));pins={}
    for p,r in zip(REVIEWS,records()):
        assert json.loads(read(p))==r;validate_review(ROOT,p,'einstein-1905',active,catalog,inv);merge_pins(pins,r['source_sha256']);pins[p]=digest((ROOT/p).read_bytes())
    return dict(status='same_light_energy_names_ratio_and_zero_angle_whole_units_reviewed',document=FULL,source_units={r['unit']:r['reviewed_prose_characters'] for r in records()},reviewed_math_elements=5,whole_units_semantically_verified=True,verified_full_units={'kant-1784':0,'einstein-1905':4},semantic_equivalence_automatically_proved=False,source_sha256=pins)
