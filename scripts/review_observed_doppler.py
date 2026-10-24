"""Whole-unit reading of source/observer frequency and its displayed consequence."""
from functools import lru_cache
import json
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import REQUIREMENTS,digest,selection_binding,validate_hashes,validate_review
from noema.review_registry import merge_pins
from scripts.compose_observed_doppler import ROOT,read,FULL,CORE,BASIS,ANNOTATIONS,LIMITS
from scripts.check_observed_doppler import DOC,SOURCE,INVENTORY,DEPENDENCIES,source_record

REPORT='reports/observed-doppler-v1.json'
REVIEWS=['data/einstein-observed-doppler-u0188-review-v1.json','data/einstein-observed-doppler-u0189-review-v1.json']

@lru_cache(None)
def records():
    catalog=load_catalog(ROOT,BASIS)
    paths={FULL,CORE,BASIS,ANNOTATIONS,SOURCE,REPORT,INVENTORY,DOC,*DEPENDENCIES,'scripts/review_observed_doppler.py','tests/test_observed_doppler_review.py'}
    pins={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)};merge_pins(pins,catalog.source_sha256)
    for p in (SOURCE,REPORT,*DEPENDENCIES):
        evidence=json.loads(read(p));validate_hashes(ROOT,evidence['source_sha256']);merge_pins(pins,evidence['source_sha256'])
    out=[]
    for i,s in enumerate(source_record()['segments']):
        if i==0:
            meaning='同じ光源のKに静止する配置族−R*nと全正距離の方向極限、同じ放射位相率ωから最小周期へ結ぶν、同じ観測者のKにおける正X速度vとkの静止経路、源から観測者への方向と速度の角φ、その観測者が受け取る位相の周期数ν′を条件にする。新旧の時刻は逆Lorentz写像で対応させる。'
            presentation='先行M0327第一式ω′への参照項目eissoと内容ekecをeisoxへ結び、著者がこの式から同じ55役割への全称条件ekebを帰結として提示するzcを置く。コロンは同じν′の表示へのuf/ue、全体は著者と論説へのeir3である。'
            symbols=['ekd3','ekd4','ekd5','ekd6','ekd7','ekea','ekeb','ekec','eked','ekef','ekdm','ekdq','ekc7','eissk','eissl','zc','eisox']
        else:
            meaning='ν′=ν(1−cosφ*v/V)/sqrt(1−(v/V)^2)を、直前の同じ源・波・観測者・系・単位・角の条件付き帰結として記述する。νを分子全体へ掛け、分母は正の平方根、v/Vを平方する。ν′又はω′を時間周期と取り違えない。'
            presentation='コロンに続く表示eissnをeisoxで同じ条件内容ekebへ結び、ekeiで著者と論説へ帰属する。無条件の数値等式又は実測報告に替えず、直前u0188からの順序と説明を共有する。'
            symbols=['ekdr','ekea','ekeb','ekeg','ekei','eisox','eir3','ue']
        clauses=[dict(range=s['range'],text=s['text'],statements=s['statements'],definitions=symbols,reason=meaning+' '+presentation)]
        assert all(n in catalog.entries for n in symbols)
        reasons=[
          '固定在庫の全文、M0328–M0333のMathMLと原刊911頁を、先行のω′及び三方向余弦の表示から続けて照合した。光源と観測者の条件文と後続表示を一組として再読した。',
          meaning,
          'M0328は先行のω′、M0329は源のν、M0330は同じ正X速度v、M0331は源から観測者への線と速度の角φ、M0332は受信ν′、M0333は印刷された式と固定する。V、K/k、同じ波・過程・源・観測者・長さ時間単位を先行ekclから引き継ぐ。',
          presentation,
          '無限遠はモデル族の方向極限、wahrgenommenは同じ周期的放射成分の受信周期数として読む。実在源の同時多地点配置、無限の実数座標、源の点状性、近似誤差からの厳密位相の推定、現実の実験実施、色の意識的知覚を補わない。既存近似を保持し、v=0の角の割当も加えない。',
          '新しい基本関係は対象と配置モデル族の物理的対応及び放射・受信位相の帰属だけで、速度・静止・遠距離極限・角・周期数・条件・等式を含めない。これらは曲線、全称条件、既存の物理履歴、正弦の最小周期と印刷式によって合成する。ν′の結論を条件に含めない。',
          '曲線と位相、逆座標時刻、区間端点、59役割の接続、55量化位置の同一割当条件、放射と受信の真偽、式への参照と引用を局所対照する。検査の物理関係と正弦周期の境界を明示し、未知入力・全実数関数域の列挙を拒否する。有限の通過から原文の意味一致又は物理法則の真理を自動認定しない。',
          '原文のAus der Gleichung für ω′ folgt、光源の遠さと周期数、相対速度と基準系、線と角、知覚される周期数、式による指定、コロンと表示を通して読み直した。明示した理想化モデル・同じ周期的成分・標準配置の下で、今回の全文の内容と提示を欠落なく記述したと判断する。後続のドップラー原理の命名、特殊例、光行差は先取りしない。',
        ]
        assert len(reasons)==len(REQUIREMENTS)
        out.append(dict(schema_version='noema-semantic-review-1',work='einstein-1905',unit=s['unit'],reviewer='assistant_review',decision='equivalent_under_stated_reading',document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source=dict(inventory=INVENTORY,unit_sha256=s['unit_sha256'],text=s['text'],range=s['range'],math=[{k:m[k] for k in ('id','sha256')} for m in s['math']]),selection=selection_binding(catalog,s['statements']),clauses=clauses,interpretation=LIMITS,limits=['明示した解釈の下でのアシスタントの意味判断であり、独立査読や意味同義性の自動証明ではない。','正弦・極限・実数算術・物理法則の一般的な真理を有限診断から証明していない。','u0178及びu0190以降と二作品全体の目標は未完。'],unresolved=[],requirements=[dict(id=k,decision='satisfied',reason=v) for k,v in zip(REQUIREMENTS,reasons)],evidence=dict(source_reading=[SOURCE],formal_checks=[REPORT,*DEPENDENCIES],semantic_reading=[DOC]),reviewed_prose_characters=s['source_nonblank_characters'],source_sha256=pins))
    return out

def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,r in zip(REVIEWS,records()):write_exact(ROOT/p,json.dumps(r,ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    active=dict(document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source_inventory=INVENTORY);catalog=load_catalog(ROOT,BASIS);inv=json.loads(read(INVENTORY));pins={}
    for p,r in zip(REVIEWS,records()):
        assert json.loads(read(p))==r
        validate_review(ROOT,p,'einstein-1905',active,catalog,inv);merge_pins(pins,r['source_sha256']);pins[p]=digest((ROOT/p).read_bytes())
    return dict(status='physical_source_observer_conditional_and_doppler_display_whole_units_reviewed',document=FULL,source_units={r['unit']:r['reviewed_prose_characters'] for r in records()},reviewed_math_elements=6,whole_units_semantically_verified=True,verified_full_units={'kant-1784':0,'einstein-1905':2},semantic_equivalence_automatically_proved=False,source_sha256=pins)
