"""Review the leading pressure approximation and its empirical/theoretical placement."""
from functools import lru_cache
from pathlib import Path
import json,re
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import REQUIREMENTS,digest,selection_binding,validate_hashes,validate_review
from noema.review_registry import merge_pins
ROOT=Path(__file__).resolve().parents[1]
def read(path):return (ROOT/path).read_text(encoding='utf-8')
FULL='examples/v014/einstein-pressure-leading-approximation.noema';CORE='examples/v014/pressure-leading-approximation-core.noema'
BASIS='data/pressure-leading-approximation-basis-v1.json';ANNOTATIONS='data/pressure-leading-approximation-identifiers-v1.json'
INVENTORY='artifacts/written-units-v1/einstein-1905.json';DOC='docs/pressure-leading-approximation-v1.md'
READING='data/einstein-pressure-leading-approximation-reading-v1.json';REPORT='reports/pressure-leading-approximation-v1.json'
PRIOR='data/einstein-mirror-energy-principle-u0223-review-v1.json';UNITS=('u0224','u0225')
def path(unit):return 'data/einstein-pressure-leading-approximation-'+unit+'-review-v1.json'

@lru_cache(None)
def record(unit):
    position=UNITS.index(unit);catalog=load_catalog(ROOT,BASIS);inv=json.loads(read(INVENTORY));u=inv['units'][223+position];text=u['text'];reading=json.loads(read(READING));segment=reading['segments'][position];index=404+position
    assert segment['unit']==u['id'] and segment['source']==text and segment['statements']==[index]
    paths={FULL,CORE,BASIS,ANNOTATIONS,INVENTORY,DOC,READING,REPORT,PRIOR,'docs/mirror-energy-principle-v1.md','scripts/review_pressure_leading_approximation.py','tests/test_pressure_leading_approximation_review.py'}
    pins={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)};merge_pins(pins,catalog.source_sha256)
    for p in (REPORT,READING,PRIOR):
        evidence=json.loads(read(p));validate_hashes(ROOT,evidence['source_sha256']);merge_pins(pins,evidence['source_sha256'])
    contents=[
      'In erster Annäherungを同じ速度比v/Vの先頭項までの近似と読み、erhält manを同じ先行圧力法則とその実数極限からの著者の帰結提示へ結ぶ。in Übereinstimmungの二つのmitを省かず、経験から認められた規則と、文脈で比較対象となる複数の他理論の全てが同じ次数制限した圧力結果を与えるという内容を保持する。前の表示への照応と、後続の式への順序を含む。',
      'M0382のP=2*A²/(8*pi)*cos²φという全表示を保持する。2、振幅の平方、8*pi、余弦全体の平方を区別し、Pは先行と同じK・物質的面部分・光の力・時間区間・面積の平均圧力である。印刷の等号は直前の近似指定の作用範囲内にあり、非零速度の厳密等式へ変えない。',
    ]
    reasons=[
      f'原刊915頁の先行圧力式から近似への導入と表示を続けて読み、{u["id"]}の全範囲[0,{len(text)})を固定した。M0382の分数、二つの平方、係数2、句点、導入末にコロンがないことを原刊画像とMathMLで照合した。',
      contents[position],
      '同じ102設定と98可変役割を保持し、Pの命名は同じpatch・力・区間・面積のekuhを再使用する。pi,A,V,cosφを固定した速度比rの族ekuxは、先行の同じ圧力右辺ekt3をspeed=r*Vで評価する。零での値と実数極限を結び、別の圧力又は別の角へ交換しない。',
      '同じ先行法則と極限の根拠から近似を得るという帰結、経験と他理論への両枝の一致、先行表示への照応、Pの命名、近似範囲内の表示、著者と論説への帰属、文の順序を保持する。引用された生の等式や経験的な比較を提示検査の外側で実行せず、実証完了を含意しない。',
      '原式に即して先頭近似を次数0と明示し、別箇所の次数1の読解を変更しない。数学的な係数族の極限と、鏡の全状態を固定した物理的な加減速の実現を区別する。経験の生データ・誤差率・理論名を補わず、他理論の範囲を結果に都合よく縮めない。',
      '先頭値と係数族、実数極限、共有量化、次数制限、複数性、他理論の全称条件は既存の数学・論理・eisbn/eifkから合成する。新一般関係eisvcは出所と量的内容の対応、eisvdは理論の比較範囲だけを扱い、光圧式や近似・一致・著者提示を一つの原始関係へ格納しない。',
      '正負零速度比、振幅零、掠める角、絶対誤差、先頭項と線形項の相違、実数極限の境界と有限実行の拒否、全98量化位置、理論の複数性と現在理論からの区別、経験を含む全出所の内容対応、次数・照応・命名・帰属、原式と既存404主張を検査する。有限対照は実数極限又は物理法則・意味同義性の自動証明ではない。',
      '同じ鏡についての厳密な圧力表示から先頭近似と二つの比較へ進む一文として再読した。明示した零次の展開、経験からの規則、文脈上の複数の他理論という読みの下で、この単位の量・式・範囲・比較・提示を欠落なく記述したと判断する。現実の測定による正しさや全ての他理論との一致を認定したものではない。',
    ]
    count=len(re.sub(r'\s','',re.sub(r'\[M\d+\]','',text)));assert count==segment['reviewed_prose_characters']
    source=dict(inventory=INVENTORY,unit_sha256=u['text_sha256'],text=text,range=[0,len(text)],math=segment['math'])
    return dict(schema_version='noema-semantic-review-1',work='einstein-1905',unit=u['id'],reviewer='assistant_review',decision='equivalent_under_stated_reading',document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source=source,selection=selection_binding(catalog,[index]),clauses=[dict(range=source['range'],text=text,statements=[index],definitions=segment['definitions'],reason=contents[position])],interpretation=reading['interpretation_limits'],limits=['明示した読みの下でのアシスタント判断であり、独立査読又は同義性の自動証明ではない。','先頭近似は次数0であり、一般に線形項を保持しない。経験データの検証又は名指されていない理論の同定は行わない。','後続の光学問題の一般的方法、第八節見出し及び二作品全体は未完。'],unresolved=[],requirements=[dict(id=k,decision='satisfied',reason=v) for k,v in zip(REQUIREMENTS,reasons)],evidence=dict(source_reading=[READING,PRIOR],formal_checks=[REPORT],semantic_reading=[DOC,'docs/mirror-energy-principle-v1.md']),reviewed_prose_characters=count,source_sha256=pins)

def prepare():
    from scripts.audit_opening_scope import write_exact
    for unit in UNITS:write_exact(ROOT/path(unit),json.dumps(record(unit),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    active=dict(document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source_inventory=INVENTORY);catalog=load_catalog(ROOT,BASIS);inv=json.loads(read(INVENTORY));pins={};counts={};maths=0
    for unit in UNITS:
        r=record(unit);assert json.loads(read(path(unit)))==r
        validate_review(ROOT,path(unit),'einstein-1905',active,catalog,inv);merge_pins(pins,r['source_sha256']);pins[path(unit)]=digest((ROOT/path(unit)).read_bytes());counts[r['unit']]=r['reviewed_prose_characters'];maths+=len(r['source']['math'])
    assert sum(counts.values())==80 and maths==1
    return dict(status='leading_pressure_approximation_and_both_agreements_reviewed',document=FULL,source_units=counts,reviewed_math_elements=maths,whole_units_semantically_verified=True,verified_full_units={'kant-1784':0,'einstein-1905':2},semantic_equivalence_automatically_proved=False,source_sha256=pins)
