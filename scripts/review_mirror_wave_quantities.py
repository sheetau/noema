"""Review the four complete incident/reflected quantity units without regenerating them."""
from functools import lru_cache
from pathlib import Path
import json,re
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import REQUIREMENTS,digest,selection_binding,validate_hashes,validate_review
from noema.review_registry import merge_pins
ROOT=Path(__file__).resolve().parents[1]
def read(path):return (ROOT/path).read_text(encoding='utf-8')
FULL='examples/v014/einstein-mirror-wave-quantities.noema';CORE='examples/v014/mirror-wave-quantities-core.noema'
BASIS='data/mirror-wave-quantities-basis-v1.json';ANNOTATIONS='data/mirror-wave-quantities-identifiers-v1.json'
INVENTORY='artifacts/written-units-v1/einstein-1905.json';DOC='docs/mirror-wave-quantities-v1.md'
READING='data/einstein-mirror-wave-quantities-reading-v1.json';REPORT='reports/mirror-wave-quantities-v1.json'
PRIOR='data/einstein-reflected-light-inquiry-u0215-review-v1.json';ANGLE='data/einstein-aberration-presentation-u0193-review-v1.json'
UNITS=('u0216','u0217','u0218','u0219')
def path(unit):return 'data/einstein-mirror-wave-quantities-'+unit+'-review-v1.json'

@lru_cache(None)
def record(unit):
    position=UNITS.index(unit);catalog=load_catalog(ROOT,BASIS);inv=json.loads(read(INVENTORY));u=inv['units'][215+position];text=u['text'];reading=json.loads(read(READING));segment=reading['segments'][position];index=396+position
    assert segment['unit']==u['id'] and segment['source']==text and segment['statements']==[index]
    paths={FULL,CORE,BASIS,ANNOTATIONS,INVENTORY,DOC,READING,REPORT,PRIOR,ANGLE,'docs/aberration-line-v1.md','scripts/review_mirror_wave_quantities.py','tests/test_mirror_wave_quantities_review.py'}
    pins={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)};merge_pins(pins,catalog.source_sha256)
    for p in (REPORT,READING,PRIOR,ANGLE):
        evidence=json.loads(read(p));validate_hashes(ROOT,evidence['source_sha256']);merge_pins(pins,evidence['source_sha256'])
    contents=[
      'Das einfallende Licht sei durch die Größen ... definiertを、同じ入射光のKでの振幅・実数角の余弦・周期数の指定という仮定採用として保持する。括弧内のKと次文のkを区別し、Von k aus betrachtetの対応量とコロンを同じ次の三式へ結ぶ。',
      'M0372の三行をA′、cosφ′、ν′の順で保持する。振幅と周期数は同じ(1−(v/V)cosφ)/sqrt(1−(v/V)²)倍、角余弦は(cosφ−v/V)/(1−(v/V)cosφ)である。根号の範囲、平方、プライム、共通の旧角と速度を保持する。',
      'Für das reflektierte Lichtの対象は同じ面への相互作用から戻る波である。erhalten wirを著者の帰結提示、wenn ... auf das System k beziehenを同じkで記述する条件として保持し、コロンを同じ後続三式へ接続する。',
      'M0374の三行A″=A′、cosφ″=−cosφ′、ν″=ν′を保持する。二重プライムは同じkの反射後、一重プライムは同じkの入射を表す。角だけの符号反転を振幅又は周期数にも適用せず、Kへの再変換と混同しない。',
    ]
    reasons=[
      f'原刊914頁のu0215の仮定・問いからu0219の三式までを通読し、対象{u["id"]}の全範囲[0,{len(text)})を保存した。数式は保存在庫の全行と原刊を照合し、局所記号や句点・コロンによる誤分割をしない。',
      contents[position],
      '先行の同じbody・wave・process・反射過程・二系・近似・単位を82設定で保持する。A系列の側は一度選び、各三係数の非負の大きさへ、ν系列は同じ位相と周期へ、φ系列は指定した二方向の実数角へ結ぶ。量と対象に別の証人を選ばない。',
      '量の指定と仮定採用、命名、条件付きの著者主張と帰結提示、表示の対応及びコロン、著者帰属と順序を区別する。引用内容の真理を帰属の条件とせず、測定済み又は導出の健全性の機械証明を補わない。',
      'φ′は先行u0193で固定したkの同時刻の光源―観測者結線と波面法線との角を継承し、φ″は反射法線と同じ比較結線との角と読む。この読みでは角の表示式に不一致があることを明示し、結線を座標軸へ変更しない。入射側と全三方向・二偏光を保ち、正面入射だけへ縮めない。',
      '大きさ・Lorentz成分変換・鏡映・角の内積と測度・全域周期条件・存在及び全称量化を既存規約から合成する。新規記号は箇所と局所表記の参照個体だけで、新しい一般基本関係へこの単位の意味を格納しない。綴りの一致だけで量の同一性を認定しない。',
      '全82引数、全78量化位置、各名前76証人と真偽値の側、六つの印刷等式、角の具体的な不一致、命名・仮定・コロン・表示・帰属と既存記述の保存を検査した。数値幾何の対照を全物理モデルの存在、一般解析又は意味同義性の自動証明にしない。',
      '四単位の導入と表示を一続きで再読した。明示した理想鏡面・局所代表モデル・同じ側と周期・継承した結線角の読みの下で、この単位の内容、対象、参照、条件、式又は導入及び著者の提示を欠落なく記述したと判断する。表示式をすべて真と認定する判断とは区別する。',
    ]
    count=len(re.sub(r'\s','',re.sub(r'\[M\d+\]','',text)));assert count==segment['reviewed_prose_characters']
    source=dict(inventory=INVENTORY,unit_sha256=u['text_sha256'],text=text,range=[0,len(text)],math=segment['math'])
    return dict(schema_version='noema-semantic-review-1',work='einstein-1905',unit=u['id'],reviewer='assistant_review',decision='equivalent_under_stated_reading',document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source=source,selection=selection_binding(catalog,[index]),clauses=[dict(range=source['range'],text=text,statements=[index],definitions=segment['definitions'],reason=contents[position])],interpretation=reading['interpretation_limits'],limits=['明示した読みの下でのアシスタントによる判断であり、独立査読又は同義性の自動証明ではない。','継承した結線角の読みと印刷式の不一致は保存する。歴史的意図又は誤植の一意な確定、原文の訂正は行わない。','後続のKへの再変換、光圧の導出と近似、二作品全体は未完。'],unresolved=[],requirements=[dict(id=k,decision='satisfied',reason=v) for k,v in zip(REQUIREMENTS,reasons)],evidence=dict(source_reading=[READING,PRIOR,ANGLE],formal_checks=[REPORT],semantic_reading=[DOC,'docs/aberration-line-v1.md']),reviewed_prose_characters=count,source_sha256=pins)

def prepare():
    from scripts.audit_opening_scope import write_exact
    for unit in UNITS:write_exact(ROOT/path(unit),json.dumps(record(unit),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    active=dict(document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source_inventory=INVENTORY);catalog=load_catalog(ROOT,BASIS);inv=json.loads(read(INVENTORY));pins={};counts={};maths=0
    for unit in UNITS:
        r=record(unit);assert json.loads(read(path(unit)))==r
        validate_review(ROOT,path(unit),'einstein-1905',active,catalog,inv);merge_pins(pins,r['source_sha256']);pins[path(unit)]=digest((ROOT/path(unit)).read_bytes());counts[r['unit']]=r['reviewed_prose_characters'];maths+=len(r['source']['math'])
    assert sum(counts.values())==184 and maths==6
    return dict(status='four_incident_reflected_quantity_units_reviewed_under_literal_angle_reading',document=FULL,source_units=counts,reviewed_math_elements=maths,whole_units_semantically_verified=True,verified_full_units={'kant-1784':0,'einstein-1905':4},semantic_equivalence_automatically_proved=False,source_sha256=pins)
