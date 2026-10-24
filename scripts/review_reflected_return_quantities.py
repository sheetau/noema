"""Review the whole return introduction and its three-row display."""
from functools import lru_cache
from pathlib import Path
import json,re
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import REQUIREMENTS,digest,selection_binding,validate_hashes,validate_review
from noema.review_registry import merge_pins
ROOT=Path(__file__).resolve().parents[1]
def read(path):return (ROOT/path).read_text(encoding='utf-8')
FULL='examples/v014/einstein-reflected-return-quantities.noema';CORE='examples/v014/reflected-return-quantities-core.noema'
BASIS='data/reflected-return-quantities-basis-v1.json';ANNOTATIONS='data/reflected-return-quantities-identifiers-v1.json'
INVENTORY='artifacts/written-units-v1/einstein-1905.json';DOC='docs/reflected-return-quantities-v1.md'
READING='data/einstein-reflected-return-quantities-reading-v1.json';REPORT='reports/reflected-return-quantities-v1.json'
PRIOR='data/einstein-mirror-wave-quantities-u0219-review-v1.json'
UNITS=('u0220','u0221')
def path(unit):return 'data/einstein-reflected-return-quantities-'+unit+'-review-v1.json'

@lru_cache(None)
def record(unit):
    position=UNITS.index(unit);catalog=load_catalog(ROOT,BASIS);inv=json.loads(read(INVENTORY));u=inv['units'][219+position];text=u['text'];reading=json.loads(read(READING));segment=reading['segments'][position];index=400+position
    assert segment['unit']==u['id'] and segment['source']==text and segment['statements']==[index]
    paths={FULL,CORE,BASIS,ANNOTATIONS,INVENTORY,DOC,READING,REPORT,PRIOR,'docs/mirror-wave-quantities-v1.md','scripts/review_reflected_return_quantities.py','tests/test_reflected_return_quantities_review.py'}
    pins={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)};merge_pins(pins,catalog.source_sha256)
    for p in (REPORT,READING,PRIOR):
        evidence=json.loads(read(p));validate_hashes(ROOT,evidence['source_sha256']);merge_pins(pins,evidence['source_sha256'])
    contents=[
      'Endlichを入射指定→k反射→K帰還という局所系列の締めくくりと読み、erhält manを著者の帰結提示、durch Rücktransformierenを同じk反射波への速度−vの変換構成から得るという手段、aufs ruhende System Kを戻し先の静止系、für das reflektierte Lichtを同じ反射光への対象限定、コロンを後続三行への説明と順序へ結ぶ。',
      'M0376の三行と各二等号をすべて保持する。A‴はA″を逆変換した中間式に、cosφ‴はcosφ″の逆速度による商に、ν‴はν″を逆変換した中間式に等置し、各中間式を旧A・φ・νによる最右辺へ結ぶ。振幅分母1−(v/V)²、角の外側の負号と共通分子、周波数最右辺だけの(1−v/V)²を原刊どおり保存する。',
    ]
    reasons=[
      f'原刊914頁末の導入と915頁冒頭の全三行を続けて読み、{u["id"]}の全範囲[0,{len(text)})とM0375又はM0376を固定した。画像とMathMLの根号・括弧・プライム・等号・句点を照合し、原刊にある分母の差を転記訂正としない。',
      contents[position],
      '同じ鏡・入射波・反射過程・系・尺度・局所モデルの82設定を引き継ぎ、Kでの三量の八役割を加えた90設定を共有する。六係数の同じ選択側、戻した法線とKの+x軸の実数角、同じ位相の周期数へ結び、三重プライムを別光の記号にしない。kの結線角の読解は変更しない。',
      '構成された逆変換量から得るという帰結、先行反射式の再表示と照応、局所系列の締めくくり、コロン、命名、式表示、著者帰属と本文順序を分けて保持する。引用された式を帰属の条件として真理評価せず、計算成功や実験済みを補わない。',
      '印刷された六等式を物理設定eks3の前件に含めない。原刊の周波数分母と物理的逆変換の不一致、継承した結線角と斜め入射の中間式の不一致を明記する。正面入射だけへの限定や、式に合う軸への無断変更を避ける。',
      '逆Lorentz変換、鏡映、振幅の大きさ、実数角、周期、六等式と量化は既存定義から合成する。新しい一般関係eisuzは指定した説明系列の締めくくりの提示だけで、光や式の内容を格納しない。表記個体は同じ波の量へ結ぶ命名規則を持つ。',
      '90引数、86量化位置、各命名の84証人と真偽値の側、全六等式の中間値、正面・斜め入射の数値不一致、命名・逆変換構成・照応・締めくくり・表示・帰属と既存400主張の保存を局所検査する。有限対照は一般解析又は意味同義性の自動証明ではない。',
      '導入と三行を同じ反射の続きとして再読した。明示した理想鏡面・局所モデル、Kの角の基準、kの継承した角の読みと原刊の式の保存の下で、この単位の内容・対象・条件・式又は導入・提示の役割を欠落なく記述したと判断する。著者の式をすべて真とする判断ではない。',
    ]
    count=len(re.sub(r'\s','',re.sub(r'\[M\d+\]','',text)));assert count==segment['reviewed_prose_characters']
    source=dict(inventory=INVENTORY,unit_sha256=u['text_sha256'],text=text,range=[0,len(text)],math=segment['math'])
    return dict(schema_version='noema-semantic-review-1',work='einstein-1905',unit=u['id'],reviewer='assistant_review',decision='equivalent_under_stated_reading',document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source=source,selection=selection_binding(catalog,[index]),clauses=[dict(range=source['range'],text=text,statements=[index],definitions=segment['definitions'],reason=contents[position])],interpretation=reading['interpretation_limits'],limits=['明示した読みの下でのアシスタント判断であり、独立査読又は同義性の自動証明ではない。','原刊の周波数分母と継承した角の読解による不一致を保存し、歴史的な誤植の一意な確定や原文の訂正は行わない。','後続のエネルギー収支・仕事・光圧と二作品全体は未完。'],unresolved=[],requirements=[dict(id=k,decision='satisfied',reason=v) for k,v in zip(REQUIREMENTS,reasons)],evidence=dict(source_reading=[READING,PRIOR],formal_checks=[REPORT],semantic_reading=[DOC,'docs/mirror-wave-quantities-v1.md']),reviewed_prose_characters=count,source_sha256=pins)

def prepare():
    from scripts.audit_opening_scope import write_exact
    for unit in UNITS:write_exact(ROOT/path(unit),json.dumps(record(unit),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    active=dict(document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source_inventory=INVENTORY);catalog=load_catalog(ROOT,BASIS);inv=json.loads(read(INVENTORY));pins={};counts={};maths=0
    for unit in UNITS:
        r=record(unit);assert json.loads(read(path(unit)))==r
        validate_review(ROOT,path(unit),'einstein-1905',active,catalog,inv);merge_pins(pins,r['source_sha256']);pins[path(unit)]=digest((ROOT/path(unit)).read_bytes());counts[r['unit']]=r['reviewed_prose_characters'];maths+=len(r['source']['math'])
    assert sum(counts.values())==80 and maths==2
    return dict(status='return_introduction_and_display_reviewed_with_source_disagreements_preserved',document=FULL,source_units=counts,reviewed_math_elements=maths,whole_units_semantically_verified=True,verified_full_units={'kant-1784':0,'einstein-1905':2},semantic_equivalence_automatically_proved=False,source_sha256=pins)
