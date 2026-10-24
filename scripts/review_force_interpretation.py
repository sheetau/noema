"""Record the separate whole-paragraph reading of Einstein u0173."""
from functools import lru_cache
import json
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import REQUIREMENTS,digest,selection_binding,validate_hashes,validate_review
from noema.review_registry import merge_pins
from scripts.compose_force_interpretation import ROOT,read,FULL,CORE,BASIS,ANNOTATIONS,WHOLE_INDICES,LIMITS
from scripts.check_force_interpretation import DOC,SOURCE,INVENTORY,DEPENDENCIES,source_record

REPORT='reports/force-interpretation-v1.json'
REVIEW='data/einstein-force-interpretation-u0173-review-v1.json'
CLAUSES=(
 (['ejxd','ejxg','eisox','ejvm','uf','ue'],'直前の六式の同じ表示と内容を受け、同じ著者が以下の注記をその解釈として提示する。後続の仮定・推論・力の同定・二表現への導入を同じ説明の順序へ結ぶ。'),
 (['ejwf','ejwg','ejwh','ejwi','ejwk','eisqc','ejwc','ejwd','ejwe','eisqd','eisqe','sbw2'],'点状の電気量zolのKでの単位値1を仮定し、d. h.以下の作用による校正で説明する。同じ量を持つ別対象、第一対象のKへの静止、同時刻の距離1 cm、第一対象から第二対象への力の大きさ1 Dyn、量・単位・記録・向きを保つ。第二対象の静止や力の特定方向を追加しない。'),
 (['ejwl','ejwm','ejwn','ejwp','eion','eisch','scc2','sbw2'],'diese elektrische Masseは同じ点状の電気量zolであり慣性質量ではない。同じ出来事と電気量単位・尺度でkにおける値も1とする別記録を結び、相対性原理に基づくという著者の推論として保持する。'),
 (['ejww','ejwu','ejws','ejwt','ejwy','ejwz','ejw4','x4','eisql','eispi'],'同じ電気量がKに静止する場合の条件文として、同じ評価出来事・位置・単位の電場三成分と、その対象自身に働く力を同定する。definitionsgemäßを既存の場の定義への参照に保つ。'),
 (['ejwx','ejwr','ejwq','seoc','ejwv','ejwt','ejw2','ejw6','eispi'],'同じ電気量が少なくとも当該瞬間にkで静止する場合に、そのkで測った力とプライム付き電場三成分を同定する。三つの座標時刻微分0を同じ対象の履歴へ結び、前後の静止や加速度0は要求しない。'),
 (['ejw7','ejs3','s6k','ejxa','ejxb','ejxc','ejxe','ejxi','eisqo','eislk'],'直前六式の電気側三式を、先行する単位電気量・力の解釈の下で、続く第一・第二の言い方によって述べられるという著者のmithinの帰結を保持する。可能性、同じ対象と条件の展開、二項の相違と順序を保ち、後続二項の内容を完成認定しない。'),
)

@lru_cache(None)
def records():
    catalog=load_catalog(ROOT,BASIS);s=source_record()
    paths={FULL,CORE,BASIS,ANNOTATIONS,SOURCE,REPORT,INVENTORY,DOC,*DEPENDENCIES,'scripts/review_force_interpretation.py','tests/test_force_interpretation_review.py'}
    pins={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)};merge_pins(pins,catalog.source_sha256)
    for p in (SOURCE,REPORT,*DEPENDENCIES):
        evidence=json.loads(read(p));validate_hashes(ROOT,evidence['source_sha256']);merge_pins(pins,evidence['source_sha256'])
    clauses=[]
    for part,(symbols,reason) in zip(s['sentences'],CLAUSES,strict=True):
        assert all(n in catalog.entries for n in symbols)
        clauses.append(dict(range=part['range'],text=part['text'],statements=part['statements'],definitions=symbols,reason=reason))
    assert ''.join(c['text'] for c in clauses)==s['text'] and s['source_nonblank_characters']==700
    reasons=(
        '固定u0173の全842転記文字・700非空白本文文字とM0315–M0317を原刊909頁へ照合し、六文を連続して再読した。直前M0314の六式と、続く番号付き二項への参照を確認した。原資料は変更しない。',
        '六式の解釈導入、点状電気量1の仮定と作用による校正、相対性原理に基づく移動系での値1、Kに静止する場合とkに瞬間静止する場合の場と力の同定、電気側三式から二つの言い表しへの帰結を全て構成する。条件・単位・数・方向・定義参照・可能性を省かない。',
        'K/kはra/zbm、同じ第一電気量はzol、校正の相手はzom、校正出来事はzoo、力の評価出来事はzpo。場はznl/znr、力はzpl/zpm、位置はzpj/zpk。電気量単位zouと力単位Dynを同じ記録・換算へ結ぶ。二出来事や二系の数値を勝手に同一化しない。最初の三式は電気側s6kとの一致で、二言い方はzpq/zprを指す。',
        '第二文はugによる仮定とufによる説明、第三文はzcによる原理に基づく推論、第四文はeisqlによる定義参照と条件文、第五文は瞬間静止の条件文、第六文はzcによる帰結と二言い方の可能性である。第一文と全六文の著者・論説・本文順序をeir3、uf、ueで保つ。引用された内容を実測済み又は処理系の物理的真理として実行しない。',
        '第二対象の静止・点状性、力の固定方向、校正と力評価の同時性、一般の電荷保存、全期間の二系への同時静止、加速度0、真空内の試験体の実在は補わない。力はこの電磁場の議論の理想的な試験電気量への局所作用と読み、支持力等を含む合力にしない。二言い方以外の不可能性や後続項の留保なしの厳密同値を加えない。',
        '点状電気量は電気的な強さと極性の点状担体、単位は独立した基準への次元と尺度、位置は明示した座標単位、力は機械的な作用の寄与として意味規約を共有する。距離・大きさ・全三成分、三微分0、同じ単位電気量と場の静止試験応答を合成する。新規一般関係eisqoは式を指定解釈の下で言語的に述べる可能性であり、物理的内容・二項の個数と順序・著者帰属は別に合成する。',
        '既存の校正219対照、移動系の電気量83対照、静止条件付きの力179対照を固定ハッシュで照合し、新たに電気側三成分、解釈の全前提、二言い方の全引数、導入と番号と順序を対照した。構文・型・表記往復と依存一致を確認し、全実数・全関数域を有限列で証明する扱いを拒否する。これらは通読判断と別の検証証拠である。',
        '原刊909頁の六文を、直前六式から後続二項への一続きの解釈段落として再読した。指示対象、仮定・理由・条件・留保、単位と数量、定義と場の物理的意味、著者による導入・推論・可能性、順序を明示した読みの下で欠落なく記述したと判断する。後続u0174–u0175の内容の意味判断はここに含めない。',
    )
    assert len(reasons)==len(REQUIREMENTS)
    record=dict(schema_version='noema-semantic-review-1',work='einstein-1905',unit=s['unit'],reviewer='assistant_review',decision='equivalent_under_stated_reading',document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source=dict(inventory=INVENTORY,unit_sha256=s['unit_sha256'],text=s['text'],range=s['range'],math=[{k:m[k] for k in ('id','sha256')} for m in s['math']]),selection=selection_binding(catalog,sorted(WHOLE_INDICES)),source_order_statements=WHOLE_INDICES,clauses=clauses,interpretation=LIMITS,limits=['明示した解釈の下でのアシスタントによる全六文の通読判断。独立査読や同義性の自動証明ではない。','原著者の電荷不変性・力の定義の適用・二表現への推論を物理学上の定理として証明したとはしない。','u0174以降と二作品全体の目標は未完。'],unresolved=[],requirements=[dict(id=k,decision='satisfied',reason=v) for k,v in zip(REQUIREMENTS,reasons)],evidence=dict(source_reading=[SOURCE],formal_checks=[REPORT,*DEPENDENCIES],semantic_reading=[DOC]),reviewed_prose_characters=700,source_sha256=pins)
    return [record]

def prepare():
    from scripts.audit_opening_scope import write_exact
    write_exact(ROOT/REVIEW,json.dumps(records()[0],ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    r=records()[0];assert json.loads(read(REVIEW))==r
    active=dict(document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source_inventory=INVENTORY)
    validate_review(ROOT,REVIEW,'einstein-1905',active,load_catalog(ROOT,BASIS),json.loads(read(INVENTORY)))
    pins=dict(r['source_sha256']);pins[REVIEW]=digest((ROOT/REVIEW).read_bytes())
    return dict(status='force_interpretation_whole_paragraph_reviewed',document=FULL,source_units={r['unit']:700},reviewed_math_elements=3,whole_units_semantically_verified=True,verified_full_units={'kant-1784':0,'einstein-1905':1},semantic_equivalence_automatically_proved=False,source_sha256=pins)
