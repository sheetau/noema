"""Review both sentences and the displayed result of the point-motion substitution."""
from functools import lru_cache
import json
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import REQUIREMENTS,digest,selection_binding,validate_hashes,validate_review
from noema.review_registry import merge_pins
from scripts.compose_point_motion_claim import ROOT,read,FULL,CORE,BASIS,ANNOTATIONS,INDICES,LIMITS
from scripts.check_point_motion_claim import DOC,SOURCE,INVENTORY,PRIORS,REFERENCES,DEPENDENCIES,source_record

REPORT='reports/point-motion-claim-v1.json'
REVIEWS=tuple(f'data/einstein-point-motion-u{n:04d}-review-v1.json' for n in (133,134))
CLAUSES=(
 (('Gesucht ist die Bewegung des Punktes relativ zum System [M0249]. ',['ejnn','ejnm','ejnq','ejns','eisou'],'同じ点zkbのKでの全期間の運動を求める課題。候補は同じK時刻の実際の三位置に一致する関数で、結果の式を問いへ先取りしない。'),
  ('Führt man in die Bewegungsgleichungen des Punktes ',['ejmy','ejni','ejnk','ejnt'],'直前の同じ点の平面運動三式を、同じ出来事の両系の全現在記録で扱う書換えの元とする。'),
  ('mit Hilfe der in § 3 entwickelten Transformationsgleichungen ',['eisms','ejeh','ejng','ejno','eisov'],'先行第三節で展開した現在の最終四座標変換を、同じ点の記録の代入に使うという参照。途中の係数付き変換や別節へ替えない。'),
  ('die Größen [M0250] ein, ',['eixv','eixw','eixx','eiwt','ssn','ejni','eislo'],'同じKのx,y,z,tを既出の座標と時刻の規則へ結び、変換により元の運動方程式に導入する。kの四数量の単なる改名にしない。'),
  ('so erhält man:',['ejno','ejnp','zd3','ejnt','ejnv'],'同じ前提の下でKの三式を得るという書換えの提示。コロンに続く表示式と同じ発話として著者へ帰属する。')),
 (('[M0251]',['syt','stw','sjd','ejnh','ejnj','ejnl','ejnp','ejnt','ejnv'],'同じ点のKの全現在記録についてx=(wξ+v)/(1+vwξ/V²)t、y=√(1−(v/V)²)/(1+vwξ/V²)wηt、z=0。三式の連言、正の根、二定数とt、非零分母の定義域を保持する。'),),
)
SEMANTICS=(
 '第一文の求解課題と第二文の変換による書換えを別の発話にし、同じ点の仮定から課題、課題から三式という本文順序を保持した。第二文は§3で展開した変換を用いてKの四数量を元の運動式へ導入し、コロンに続く結果を得るという提示である。',
 '同じV,v,wξ,wηを用いる共通分母と、第一式の和wξ+v、第二式の正の平方根とwη、第三式の零を保持する。非零分母の下でsytの分母を払った三等式を原文の商に対応させ、ejnhがβ=1/√(1−(v/V)²)へ結ぶ。全K記録へejnlで適用する。',
)
WHOLE=(
 '原刊905頁のGesucht istからso erhält man:までの二文を、先行する点の設定と直後の三式に続けて再読した。対象・Kへの相対性・求解の役割・§3で展開した変換への参照・四量の導入と結果提示を、明示した読みの下で欠落なく保持したと判断する。',
 '導入のコロンから三式の終端までを、先行のξ/η/ζの平面式と後続の平行四辺形則の考察に挟んで再読した。分子・分母・平方根・二乗・積・三つの等号・同じK時刻と二定数を保持し、明示した非零分母の読みの下で欠落なく記述したと判断する。',
)

@lru_cache(None)
def records():
    catalog=load_catalog(ROOT,BASIS)
    paths={FULL,CORE,BASIS,ANNOTATIONS,SOURCE,REPORT,INVENTORY,DOC,*PRIORS,*REFERENCES,*DEPENDENCIES,'scripts/review_point_motion_claim.py','tests/test_point_motion_claim_review.py'}
    pins={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)};merge_pins(pins,catalog.source_sha256)
    for p in (SOURCE,REPORT,*DEPENDENCIES):
        evidence=json.loads(read(p));validate_hashes(ROOT,evidence['source_sha256']);merge_pins(pins,evidence['source_sha256'])
    out=[]
    for i,s in enumerate(source_record()['segments']):
        clauses=[];offset=0;indices=list(INDICES) if i==0 else [INDICES[1]]
        for text,symbols,reason in CLAUSES[i]:
            assert s['text'][offset:offset+len(text)]==text and all(n in catalog.entries for n in symbols)
            clauses.append(dict(range=[offset,offset+len(text)],text=text,definitions=symbols,reason=reason));offset+=len(text)
        assert offset==len(s['text'])
        reasons=(
            f"固定{s['unit']}の全範囲を原刊905頁の先行設定、二文、表示三式と後続の考察に照合した。本文範囲と数式要素{[m['id'] for m in s['math']]}をハッシュへ固定し、第三節の見出しと最終四式の判断が現在の本文にも同じ内容で保持されることを確認した。",
            SEMANTICS[i],
            '同じ点zkbとK/k、同じ比較状況zb6、Kのx/y/z/tとkのξ/η/ζ/τ、同じV,vと二定数を保持する。ejne/ejnfは同じ出来事の両記録を結び、ejngは両系の全履歴と出来事範囲を保つ。§3はeisms、用いる式はejehで、初期係数φの途中表示を参照しない。',
            'Gesucht istは答えを見いだす課題の提示であり、解の存在や既得の公式の断言ではない。Führt man ... ein, so erhält manは同じ前提の下での書換えの提示として読み、原文の条件と結果の関係をzd3へ結ぶ。先行節の参照も帰属であり、引用内容や計算履歴を実行しない。',
            '全現在記録を変換の成否とは独立に指定し、同じ点の全期間に式を要求する。非零分母は商の明示した定義域で、原文の追加文や物理的速度上限とはしない。負の分母、負・零の成分を許す。零分母で元の変換に合う記録も存在し得るという区別を保持する。後続の平行四辺形則・近似や速度の大きさを混ぜない。',
            '位置・時刻・物差し・局所時計・世界線・全期間と数値式は既存定義から構成する。新しい関係は既存の課題提示を関数回答型で扱う規約と、先行区分で展開した内容を用いる参照の規約であり、物理的な一文全体を基本述語に隠さない。新しい個体記号は課題を提示する箇所だけである。',
            '発話の全引数、四つの記号規則、参照する節と変換内容、著者・論説・本文順序を対照検査した。前段では元の四座標変換と平面式、結果の三式、零・負の分母、同じ出来事の存在証人、全記録と全時刻の候補関数を検査した。固定依存の検査を新たな物理的真理や意味同値の自動証明に替えない。',
            WHOLE[i],
        )
        assert len(reasons)==len(REQUIREMENTS)
        out.append(dict(schema_version='noema-semantic-review-1',work='einstein-1905',unit=s['unit'],reviewer='assistant_review',decision='equivalent_under_stated_reading',document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source=dict(inventory=INVENTORY,unit_sha256=s['unit_sha256'],text=s['text'],range=s['range'],math=[{k:m[k] for k in ('id','sha256')} for m in s['math']]),selection=selection_binding(catalog,indices),source_order_statements=indices,clauses=clauses,interpretation=LIMITS,limits=['明示した解釈の下でのアシスタントの通読判断。独立査読、全可能解釈の包含、物理的真理又は意味同値の自動証明ではない。','u0135以降と二作品全体の目標は未完。'],unresolved=[],requirements=[dict(id=k,decision='satisfied',reason=v) for k,v in zip(REQUIREMENTS,reasons)],evidence=dict(source_reading=[SOURCE],formal_checks=[REPORT,*DEPENDENCIES],semantic_reading=[DOC]),reviewed_prose_characters=s['source_nonblank_characters'],source_sha256=pins))
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
    return dict(status='point_motion_task_and_substitution_result_whole_units_reviewed',document=FULL,source_units={r['unit']:r['reviewed_prose_characters'] for r in records()},reviewed_math_elements=3,whole_units_semantically_verified=True,verified_full_units={'kant-1784':0,'einstein-1905':2},semantic_equivalence_automatically_proved=False,source_sha256=pins)
