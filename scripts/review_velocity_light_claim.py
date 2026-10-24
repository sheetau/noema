"""Reread light-speed invariance, scoped variables and the corrected display."""
from functools import lru_cache
import json
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import REQUIREMENTS,digest,selection_binding,validate_hashes,validate_review
from noema.review_registry import merge_pins
from scripts.compose_velocity_light_claim import ROOT,read,FULL,CORE,BASIS,ANNOTATIONS,LIMITS
from scripts.check_velocity_light_claim import DOC,SOURCE,INVENTORY,PRIORS,DEPENDENCIES,source_record

REPORT='reports/velocity-light-claim-v1.json'
REVIEWS=tuple(f'data/einstein-velocity-light-u{n:04d}-review-v1.json' for n in (145,146))
REASONS=(
 (
  'u0145の二文全範囲を原刊906頁で照合した。Es folgt ferner、光速度V、引用符付きのUnterlichtgeschwindigkeit、合成によって変化し得ないという否定、Man erhält für diesen Fallとコロンを確認し、次の表示式までを同じ提示として読んだ。M0272のVを固定した。',
  '第一文は同じ一次元式の光速度への特殊化s4iから、不動点と全称s4gが得られるというejqnである。全ての0≤w<Vについて同じ操作がVを保つと読み、単なる一組の一致や変化が観測されなかった過去の記録へ縮めない。第二文は同じ場合から原刊の二つの等号ejquを得るというejqoである。',
  'Vは同じ光速度tc、合成は直前と同じs3g/s3jである。表示式のw/Uはこの特殊化の相手と結果という局所変数に束縛する。物理的な適用では同じ点のk速度をV、実際の系速度を光速未満の相手へ結ぶ。ejqk–ejqmは同じ点・K/k・現在全履歴・座標微分・非負ノルムを保持し、数値の入力交換を物理的役割の交換にしない。',
  'fernerは前の不足量による説明zllから光速度の帰結zlmへの続きとして保持する。第二文のこの場合は同じ特殊化s4iを受け、コロンの後の式zlnまで同じ著者・論説・第五節に帰属する。引用された全称や式を、その帰属から真として実行しない。',
  'nicht geändert werden kannを全ての許容入力でVが不動点という読みで保持し、話者の知識や技術的能力に替えない。非負・同方向の既存の読みを維持し、負の相手や任意方向へ広げない。一般式の零入力と現在の正の相対運動を区別し、光速の系、特殊化した場合の実在、別の物体を加えない。',
  '不変性は一般の関数の不動点s4b、実切断への全称s4f、同じ合成式の結果構成で表す。原刊の簡約商はejqg/ejqhで加算と二段の除算へ分解する。現在の物理的な取得規則は条件付き適用ejqtとして表示内容へ実際に含め、一文専用の未説明の基本述語は追加しない。',
  '不動点を恒等・平行移動・二乗の別関数でも検査し、許容域と代数上の広い域、零分母、原刊と転記の違い、同じ点と相手・結果・文脈、両入力順、全称の束縛と有限列挙拒否を確認した。現在の取得の下位関係は保存した証拠へ結ぶ。有限例と有理多項式証拠は全実切断や普遍的な物理導出の証明ではない。',
  '第一文の続き・合成相手・不変性、第二文のこの場合・帰結提示・コロン、表示式全体まで通読した。一般的な数式の特殊化と、同じ点への条件付き適用という明示した読みの下で、両文の内容と提示を欠落なく記述したと判断する。局所変数の読みを明示し、元の固定値の役割を書き換えていない。',
 ),
 (
  'u0146全範囲[M0273]を原刊906頁で照合した。U、最初の等号、分子V+w、分母1+w/V、第二の等号とV、句点を確認した。固定電子転記の分母の小文字vは原刊と異なるため、既存の訂正記録を使い、元と訂正後のMathML及びハッシュを併記する。',
  '原刊のU=(V+w)/(1+w/V)=Vをejqhによる商への等値と、同じ結果のVへの等値として保持する。ejqiは同じ一次元式から構成した一つの結果を双方へ渡し、ejqjは任意の許容入力へ適用する。単にU=Vだけや、簡約前の式だけで済ませない。',
  'この式のwは光速未満の合成相手、Uはその同じ合成の結果という局所的な束縛を採る。同じ光速度tcと同じ合成式を共有し、前段の固定値zkq/zkpを無条件には流用しない。条件付きの物理適用では点のk速度がV、系速度が相手となり、結果を同じ点のKでの実際の微分値のノルムへ結ぶ。',
  '直前のMan erhält für diesen Fall:が導く表示式としてejqoが同じ特殊化からejquを得ると提示する。ejquは一般式と、前の物理的な速度の取得規則に対する条件付き適用を含む。コロンと式を別の無条件な発話へ分断せず、同じ著者・論説・第五節へ帰属する。',
  '一般式の相手は0≤w<Vであり、光速の入力は数式の一方の引数への特殊化である。実際の系速度zb7=Vは課さない。代数上はw≠−Vで値がVとなっても原文の範囲を広げず、w=−VでU=Vが成り立つだけでは商を成立させない。正の相対運動に零の方向を追加しない。',
  'ejqgは(V+w)/(1+w/V)を実切断の加算・Vの正の逆数・外側の符号付き逆数で構成し、ejqhが有効性・正のV・非零分母を要求する。旧s3g/s3jと物理的な取得ejpa/ejoiの意味は変更せず、数値入力の交換前後と同じ結果の関係を明示する。新しい原始記号は追加しない。',
  '二つの等号を独立に失敗させる対照、零・負・境界・特異な入力、原刊のVを小文字vにした場合の9/2対5、同じ光速度の点と光速未満の系、誤った結果や文脈の拒否を検査した。全実数量化は有限の速度一覧へ縮めない。原刊の読解、有限対照、一般的な物理導出の正当性は別の根拠である。',
  '直前のこの場合の指定とコロン、原刊の二重分数と二つの等号・句点、次の二変換による別導出への移行まで通読した。原刊訂正、局所的な合成相手と結果、同じ物理的な取得への条件付き適用という明示した読みの下で欠落なく記述したと判断する。光速の座標系や無条件な実在を補っていない。',
 ),
)

@lru_cache(None)
def records():
    catalog=load_catalog(ROOT,BASIS)
    paths={FULL,CORE,BASIS,ANNOTATIONS,SOURCE,REPORT,INVENTORY,DOC,*PRIORS,*DEPENDENCIES,'scripts/review_velocity_light_claim.py','tests/test_velocity_light_claim_review.py'}
    pins={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)};merge_pins(pins,catalog.source_sha256)
    for p in (SOURCE,REPORT,*DEPENDENCIES):
        evidence=json.loads(read(p));validate_hashes(ROOT,evidence['source_sha256']);merge_pins(pins,evidence['source_sha256'])
    out=[];selections=([143,144],[144])
    symbols=(['s4b','s4d','s4e','s4f','s4g','s4i','ejqn','ejqo','ejqr','ejqs','ejqj','ejqu','ejqk','ejql','ejqm','ejqt'],['ejqg','ejqh','ejqi','ejqj','ejqk','ejql','ejqm','ejqt','ejqu','ejqo','ejqs','ejpa','ejoi','s3g','s3j'])
    for i,s in enumerate(source_record()['segments']):
        assert len(REASONS[i])==len(REQUIREMENTS) and all(n in catalog.entries for n in symbols[i])
        corrections=[{k:m[k] for k in ('id','sha256','correction_id','reviewed_math_sha256')} for m in s['math'] if 'correction_id' in m]
        out.append(dict(schema_version='noema-semantic-review-1',work='einstein-1905',unit=s['unit'],reviewer='assistant_review',decision='equivalent_under_stated_reading',document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source=dict(inventory=INVENTORY,unit_sha256=s['unit_sha256'],text=s['text'],range=s['range'],math=[{k:m[k] for k in ('id','sha256')} for m in s['math']]),source_corrections=corrections,selection=selection_binding(catalog,selections[i]),source_order_statements=selections[i],clauses=[dict(range=s['range'],text=s['text'],definitions=symbols[i],reason=REASONS[i][1])],interpretation=LIMITS,limits=['同じ合成則の一般的な特殊化、非負の光速未満入力と不動点、局所的な相手と結果の束縛、同じ点の速度取得への条件付き適用という明示した読みの下でのアシスタントの判断。独立査読・全可能解釈の包含・意味同値の自動証明ではない。','数値入力を交換して物理的な適用を結ぶが、系や観測上の役割を交換せず、実際の系速度を光速にしない。適用した場合の実在や普遍的な物理導出を認定しない。','u0147以降とs5mに残る旧前提への接続、二作品全体の目標は未完。'],unresolved=[],requirements=[dict(id=k,decision='satisfied',reason=v) for k,v in zip(REQUIREMENTS,REASONS[i])],evidence=dict(source_reading=[SOURCE],formal_checks=[REPORT,*DEPENDENCIES],semantic_reading=[DOC]),reviewed_prose_characters=s['source_nonblank_characters'],source_sha256=pins))
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
    return dict(status='light_speed_invariance_and_corrected_display_whole_units_reviewed',document=FULL,source_units={r['unit']:r['reviewed_prose_characters'] for r in records()},reviewed_math_elements=2,source_corrections=records()[1]['source_corrections'],whole_units_semantically_verified=True,verified_full_units={'kant-1784':0,'einstein-1905':2},general_physical_derivation_proved=False,semantic_equivalence_automatically_proved=False,source_sha256=pins)
