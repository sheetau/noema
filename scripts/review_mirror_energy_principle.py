"""Review the complete energy/work paragraph and the pressure display."""
from functools import lru_cache
from pathlib import Path
import json,re
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import REQUIREMENTS,digest,selection_binding,validate_hashes,validate_review
from noema.review_registry import merge_pins
ROOT=Path(__file__).resolve().parents[1]
def read(path):return (ROOT/path).read_text(encoding='utf-8')
FULL='examples/v014/einstein-mirror-energy-principle.noema';CORE='examples/v014/mirror-energy-principle-core.noema'
BASIS='data/mirror-energy-principle-basis-v1.json';ANNOTATIONS='data/mirror-energy-principle-identifiers-v1.json'
INVENTORY='artifacts/written-units-v1/einstein-1905.json';DOC='docs/mirror-energy-principle-v1.md'
READING='data/einstein-mirror-energy-principle-reading-v1.json';REPORT='reports/mirror-energy-principle-v1.json'
PRIOR='data/einstein-reflected-return-quantities-u0221-review-v1.json';UNITS=('u0222','u0223')
def path(unit):return 'data/einstein-mirror-energy-principle-'+unit+'-review-v1.json'

@lru_cache(None)
def record(unit):
    position=UNITS.index(unit);catalog=load_catalog(ROOT,BASIS);inv=json.loads(read(INVENTORY));u=inv['units'][221+position];text=u['text'];reading=json.loads(read(READING));segment=reading['segments'][position];index=402+position
    assert segment['unit']==u['id'] and segment['source']==text and segment['statements']==[index]
    paths={FULL,CORE,BASIS,ANNOTATIONS,INVENTORY,DOC,READING,REPORT,PRIOR,'docs/mirror-energy-work-v1.md','scripts/review_mirror_energy_principle.py','tests/test_mirror_energy_principle_review.py'}
    pins={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)};merge_pins(pins,catalog.source_sha256)
    for p in (REPORT,READING,PRIOR):
        evidence=json.loads(read(p));validate_hashes(ROOT,evidence['source_sha256']);merge_pins(pins,evidence['source_sha256'])
    contents=[
      '四文を一続きに読む。第一文は同じKで測った同じ鏡の単位面積時間あたりの入射エネルギーをM0377へ等置し、offenbarの著者提示を含む。第二文は同じ面部分から戻る量をM0378へ等置する。第三文はこの二表示の差を同じ光圧の仕事へ、完全収支のエネルギー原理に基づく帰結として結ぶ。第四文のdie letztereは同じ仕事を指し、Pを同じ圧力と命名し、仕事=P*vへの等置の下で後続表示を得るという条件付き導出とコロンを保持する。',
      'M0381のP=2*A²/(8*pi)*(cosφ−v/V)²/(1−(v/V)²)という全表示を保持する。2、振幅の平方、8*pi、差全体の平方、分母の比の平方を区別し、Pを同じKの物質的面部分の同じ力・区間・面積の平均圧力へ結ぶ。先行四文からの表示であり、仕事の式だけが零速度の圧力も決めるという証明を追加しない。',
    ]
    reasons=[
      f'原刊915頁の四文と後続表示を読み、{u["id"]}の全範囲[0,{len(text)})と全ての数式要素を固定した。MathMLと原刊画像の三重プライム全体の平方、負号、各括弧、二つの平方範囲、句点とコロンを照合した。',
      contents[position],
      '同じ102設定に、両波のK物理モデル、動く鏡面への相対流、全矩形での時間平均、同じ光の力の平均圧力と機械的仕事の積分を保つ。一般の有限区間エネルギー収支の対応は同じ相互作用・物体・面部分・K・単位・領域・区間へ結び、平均値を同じ面積時間倍して総量へ変える。',
      'offenbar、エネルギー原理の命名参照、二つの表示への照応、仕事への後方照応、Pの命名、条件付き帰結、コロン、表示、四文の順序と区別、著者と論説への帰属を分けて保持する。引用された保存則と表示式を外側で真理評価しない。',
      '理想鏡のこの議論ではKの透過と非機械的正味移転を零とする読みを明示する。kでの正味移転零からKの仕事零を導かず、数値的保存式・仕事=P*v・圧力の閉式を設定の前件にしない。零速度での仕事の圧力未決定性と先行の原式の不一致を保存する。',
      '新一般関係eisu2は任意の有限面部分・時間区間の五経路の物理的対応だけを扱い、保存式や鏡・原文の式を格納しない。エネルギー原理はekt5を満たす全設定の保存式ekt7として合成し、同じ仕事・面積・時間・場と照応・提示は既存定義を再使用する。原文一文を一つの原始関係に置き換えない。',
      '完全収支の役割と102設定、98共有量化位置とP命名の96証人、一般原理の全量化位置、真偽値の選択側、五経路の数的収支、正負零速度、引用内容と提示、四文の照応・順序・帰属、全五式、既存402主張と意味を局所検査した。有限対照は全域解析又は意味同義性の自動証明ではない。',
      '同じ鏡の問いからKへの逆変換、四文の仕事の導出、光圧表示まで再読した。明示した理想モデル・Kの同じ面積時間平均・完全収支と非機械的正味移転零という読みの下で、この単位の対象・内容・条件・数式・照応・著者提示を欠落なく記述したと判断する。全ての著者の式が真であるとの判断ではない。',
    ]
    count=len(re.sub(r'\s','',re.sub(r'\[M\d+\]','',text)));assert count==segment['reviewed_prose_characters']
    source=dict(inventory=INVENTORY,unit_sha256=u['text_sha256'],text=text,range=[0,len(text)],math=segment['math'])
    return dict(schema_version='noema-semantic-review-1',work='einstein-1905',unit=u['id'],reviewer='assistant_review',decision='equivalent_under_stated_reading',document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source=source,selection=selection_binding(catalog,[index]),clauses=[dict(range=source['range'],text=text,statements=[index],definitions=segment['definitions'],reason=contents[position])],interpretation=reading['interpretation_limits'],limits=['明示した読みの下でのアシスタント判断であり、独立査読又は同義性の自動証明ではない。','零速度の圧力の導出と先行の角・周波数の不一致を解消したとの主張ではない。','後続の近似・経験と他理論への言及、第八節見出し、二作品全体は未完。'],unresolved=[],requirements=[dict(id=k,decision='satisfied',reason=v) for k,v in zip(REQUIREMENTS,reasons)],evidence=dict(source_reading=[READING,PRIOR],formal_checks=[REPORT],semantic_reading=[DOC,'docs/mirror-energy-work-v1.md']),reviewed_prose_characters=count,source_sha256=pins)

def prepare():
    from scripts.audit_opening_scope import write_exact
    for unit in UNITS:write_exact(ROOT/path(unit),json.dumps(record(unit),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    active=dict(document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source_inventory=INVENTORY);catalog=load_catalog(ROOT,BASIS);inv=json.loads(read(INVENTORY));pins={};counts={};maths=0
    for unit in UNITS:
        r=record(unit);assert json.loads(read(path(unit)))==r
        validate_review(ROOT,path(unit),'einstein-1905',active,catalog,inv);merge_pins(pins,r['source_sha256']);pins[path(unit)]=digest((ROOT/path(unit)).read_bytes());counts[r['unit']]=r['reviewed_prose_characters'];maths+=len(r['source']['math'])
    assert sum(counts.values())==359 and maths==5
    return dict(status='four_energy_sentences_and_pressure_display_reviewed',document=FULL,source_units=counts,reviewed_math_elements=maths,whole_units_semantically_verified=True,verified_full_units={'kant-1784':0,'einstein-1905':2},semantic_equivalence_automatically_proved=False,source_sha256=pins)
