"""Review the section-five heading and its complete opening assumption."""
from functools import lru_cache
import json
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import REQUIREMENTS,digest,selection_binding,validate_hashes,validate_review
from noema.review_registry import merge_pins
from scripts.compose_velocity_opening_claim import ROOT,read,FULL,CORE,BASIS,ANNOTATIONS,INDICES,LIMITS
from scripts.check_velocity_opening_claim import DOC,SOURCE,INVENTORY,PRIOR,DEPENDENCIES,source_record

REPORT='reports/velocity-opening-claim-v1.json'
REVIEWS=tuple(f'data/einstein-velocity-opening-u{n:04d}-review-v1.json' for n in range(129,133))
CLAUSES=(
 (('§ 5. ',['ejm6','eihq','eisoq','eisor','eisdx'],'第一部の直接の下位区分を案内する深さ2・表示番号5の節見出し。箇所と区分を区別する。'),
  ('Additionstheorem der Geschwindigkeiten.',['ejm2','ejm3','ejm4','ejm5','eisoo','eisop'],'同じ点と二系・適用状況・出来事の全範囲を保った三つの速度の合成規則を、前提から導く定理の論述として主題にする。')),
 (('In dem längs der [M0242]-Achse des Systems [M0243] mit der Geschwindigkeit [M0244] bewegten System [M0245] ',['ejmx','eivz','eioj'],'既出のKの正X方向に速度vで等速並進するkを、同じ全配置・尺度・比較状況へ接続する。'),
  ('bewege sich ein Punkt ',['ejnb','ejmy','ejmw','ejmu','ug'],'一つの点の運動を仮定として置く。同じ点の全期間の現在記録と位置を保ち、現実での運動の成立の報告に替えない。'),
  ('gemäß den Gleichungen:',['ejmw','ejmv','syr','ejnd'],'同じ仮定の内容として続く三式を導入し、全期間の等速運動と原点を通る条件へ接続する。')),
 (('[M0246]',['ejmw','ejmv','syr','ejms','ejmu'],'同じ点のkでの同じ時刻τについてξ=wξτ、η=wητ、ζ=0を共に要求する。二つの速度成分は全期間に共通で、三式末尾のコンマから定数の説明に続く。'),),
 (('wobei [M0247] und [M0248] Konstanten bedeuten.',['ejnb','ejm7','ejna','eislo','eisos','eisot'],'前の三式のwξとwηがそれぞれ同じ点の縦・横の定速度を意味するという説明。両表記を型付き規則へ結び、同じ文を閉じる。'),),
)
SEMANTICS=(
 '番号と階層、速度の合成、定理という論述種類を接続した。ejm2は二系の全配置での相対速度、ejmvは同じ点の各系での全期間の速度、ejm3/ejm4は同じ出来事の全範囲を保持する。見出しはこれらの関係を扱う主題であり、通常のベクトル加算や特定公式そのものを主張しない。',
 'KのX軸に沿う速度vのkとその中の点を、eivzとejmwで同じ状況へ結ぶ。bewegeを仮定の採用ugとして表現し、コロンに続く三式とwobei以下の説明を同じ内容ejnbと帰属ejndに保つ。',
 'syrの三つの等式とejmvの全時刻の定速度条件を、同じ実際の座標関数へ結ぶ。下端の三式と全期間の定速度から、全期間で原点を通る二直線式と第三成分零を要求する。下端時刻自体を零に限定しない。',
 '二つの表記個体eisos/eisotを、それぞれejm7/ejnaの規則へeisloで結ぶ。規則は同じ点zkbの同じ全期間のejmwと成分zkc/zkdを指定する。定数は互いに異なる値という意味ではなく、同値・零・負も許す。',
)
WHOLE=(
 '節見出し全体を直前の地球時計の結論と後続の設定・節末までの文書区分に照合した。第五節の番号、第一部内の階層、速度合成定理という主題を、明示した読みの下で欠落なく保持したと判断する。',
 '導入全体を三式とwobei以下に続く一文として再読した。K・X・v・kの役割、点の仮定、三式への導入を欠落なく保持したと判断する。',
 '導入、三式、末尾のコンマ、定数説明を連続して再読した。同じkの点の全期間で同じτと二定数を用いる三等式と零の第三成分を欠落なく保持したと判断する。',
 '三式の末尾からwobei以下と句点までを再読した。直前の二つの成分記号が定数を意味する説明と同じ仮定の文の終端を欠落なく保持したと判断する。',
)

@lru_cache(None)
def records():
    catalog=load_catalog(ROOT,BASIS)
    paths={FULL,CORE,BASIS,ANNOTATIONS,SOURCE,REPORT,INVENTORY,DOC,PRIOR,*DEPENDENCIES,'scripts/review_velocity_opening_claim.py','tests/test_velocity_opening_claim_review.py'}
    pins={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)};merge_pins(pins,catalog.source_sha256)
    for p in (SOURCE,REPORT,*DEPENDENCIES):
        evidence=json.loads(read(p));validate_hashes(ROOT,evidence['source_sha256']);merge_pins(pins,evidence['source_sha256'])
    out=[]
    for i,s in enumerate(source_record()['segments']):
        clauses=[];offset=0;index=INDICES[0 if i==0 else 1]
        for text,symbols,reason in CLAUSES[i]:
            assert s['text'][offset:offset+len(text)]==text and all(n in catalog.entries for n in symbols)
            clauses.append(dict(range=[offset,offset+len(text)],text=text,definitions=symbols,reason=reason));offset+=len(text)
        assert offset==len(s['text'])
        reasons=(
            f"固定{s['unit']}の全範囲を原刊905頁の見出し、設定、三式、二定数説明に照合した。本文と数式要素{[m['id'] for m in s['math']]}をハッシュへ固定し、直前の結論と後続の課題、第二部直前までの区分も確認した。",
            SEMANTICS[i],
            'K/k、X、v、点zkb、kでのτとξ/η/ζ、二成分zkc/zkdを既出の比較状況zb6へ接続する。見出しの関係では対象・二系・適用状況と同じ出来事の全範囲を保ち、両系の座標時刻の数値を同一視しない。',
            '見出しは定理の主題と文書案内であり、証明完了の認定ではない。bewegeは同じ節で著者が置く仮定であり、三式とwobei以下はその一文を構成する。型付き表記規則の引用から実測又は現実での成立を導かない。',
            '全期間と現在の全記録を指定し、式に合う観測だけに限定しない。既出の系の速度の条件は継承するが、点の二成分には正・負・零・相互の一致を許し、光速上限を追加しない。点を一つの三座標世界線として読み、質量・電荷・内部構造を仮定しない。u0133以降の求解や公式はこの範囲へ先取りしない。',
            '新規の一般関係は三成分量の合成の主題と定理の論述種類であり、残る四基本記号は節・箇所・表記の個体参照である。速度の物理的な意味、全出来事範囲と全期間、三式の積・等号・零、仮定と帰属は既存定義から合成する。一文の真偽を新規基本記号へ隠さない。',
            '相対速度の各成分、同じ出来事の存在証人の全引数、両系の範囲一致、三量の全引数、二表記の参照先、見出し階層と原文順序を対照検査した。全期間と座標の下位意味は前段の固定証拠を参照する。有限例を全実数の物理モデル又は意味同値の自動証明に替えない。',
            WHOLE[i],
        )
        assert len(reasons)==len(REQUIREMENTS)
        out.append(dict(schema_version='noema-semantic-review-1',work='einstein-1905',unit=s['unit'],reviewer='assistant_review',decision='equivalent_under_stated_reading',document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source=dict(inventory=INVENTORY,unit_sha256=s['unit_sha256'],text=s['text'],range=s['range'],math=[{k:m[k] for k in ('id','sha256')} for m in s['math']]),selection=selection_binding(catalog,[index]),source_order_statements=[index],clauses=clauses,interpretation=LIMITS,limits=['明示した読みの下でのアシスタントの通読判断。独立査読、全可能解釈の包含、物理的真理又は意味同値の自動証明ではない。','u0133以降と二作品全体の目標は未完。'],unresolved=[],requirements=[dict(id=k,decision='satisfied',reason=v) for k,v in zip(REQUIREMENTS,reasons)],evidence=dict(source_reading=[SOURCE],formal_checks=[REPORT,*DEPENDENCIES],semantic_reading=[DOC]),reviewed_prose_characters=s['source_nonblank_characters'],source_sha256=pins))
    return out


def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,r in zip(REVIEWS,records()):write_exact(ROOT/p,json.dumps(r,ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    active=dict(document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source_inventory=INVENTORY)
    catalog=load_catalog(ROOT,BASIS);inv=json.loads(read(INVENTORY));pins={}
    for p,r in zip(REVIEWS,records()):
        assert json.loads(read(p))==r
        validate_review(ROOT,p,'einstein-1905',active,catalog,inv);merge_pins(pins,r['source_sha256']);pins[p]=digest((ROOT/p).read_bytes())
    return dict(status='velocity_composition_heading_and_complete_opening_assumption_whole_units_reviewed',document=FULL,source_units={r['unit']:r['reviewed_prose_characters'] for r in records()},reviewed_math_elements=7,whole_units_semantically_verified=True,verified_full_units={'kant-1784':0,'einstein-1905':4},semantic_equivalence_automatically_proved=False,source_sha256=pins)
