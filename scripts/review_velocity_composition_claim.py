"""Reread angle interpretation, easy-calculation transition and printed quotient."""
from functools import lru_cache
import json
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import REQUIREMENTS,digest,selection_binding,validate_hashes,validate_review
from noema.review_registry import merge_pins
from scripts.compose_velocity_composition_claim import ROOT,read,FULL,CORE,BASIS,ANNOTATIONS,LIMITS
from scripts.check_velocity_composition_claim import DOC,SOURCE,INVENTORY,PRIORS,DEPENDENCIES,source_record

REPORT='reports/velocity-composition-claim-v1.json'
REVIEWS=tuple(f'data/einstein-velocity-composition-u{n:04d}-review-v1.json' for n in (139,140))
REASONS=(
 (
  'u0139全範囲を原刊906頁で、前頁のαの指定から角の意味の説明、Nach einfacher Rechnung ergibt sich:、次の表示式まで照合した。α、v、wの三つの参照と第一文の句点、後半のコロンを区別して固定した。',
  '第一文は直前のαを同じ二速度の間の角として理解する提示ejo5/ejo7である。後半は同じ運動と三量の定義ejpbから表示式ejpcが得られるという帰結提示ejpeと、同じ計算が低負担であるという評価ejpfを保持する。式が続くことだけで簡単という評価を代用しない。',
  'αの実数測度eiso4と単位円成分zkt、系速度zb7、点のk速さzkq及びK速さzkpは同じ現在の点・両系・尺度・全期間に結ぶ。ejpaはejoi/ejoj/ejowを共有し、計算前提と結果は同じejpa(zb6)を用いる。dannは前の定義を受ける説明の進行で、物理的な後時刻には替えない。',
  '角をそう理解する説明、計算から得られる帰結、計算の低負担評価を別の提示として同じ著者・論説・第五節へ帰属する。zkvからzkx、コロンからzkwへの順序と同じ結論を保持する。引用した結論の真理や実際に計算した履歴を帰属から実行しない。',
  '角の向きと枝は前段の明示した解釈を保つ。簡単は同じ許容手順列の負担合計が文脈基準に入るという読みで、具体的な手順数・閾値・実行時間は加えない。点の光速上限や正分母条件を新たな前提にせず、負分母で結論が非負速さと不一致になる場合も隠さない。',
  '角は実数積分とπ、内積と有向面積へ、U/wは同じ現在座標の実微分と非負ノルムへ合成する。低負担評価は既存s2w/s2x/s2yと利用可能な同じ方法zlw/zlx、許容関係zla、負担zlbと基準zlcへ分解する。この文だけを表す未説明の原始述語を追加しない。',
  '符号付き式の本体、同じ三量と文脈、非空で連続した手順・同じ方法・非負負担合計、引用と帰属の全引数を対照した。負分母の前提を排除せず結論が偽になり得る検査も保存する。一般的な物理導出の証明や、容易さの評価自体の正しさを検査通過と同一視しない。',
  'αの意味の説明から計算への移行、表示式と句点まで続けて再読した。同じ角の解釈、同じ計算の低負担評価、帰結提示と参照先を、明示した読みの下で欠落なく記述したと判断する。原文の主張を記述することと、その無条件な正しさを認定することを区別している。',
 ),
 (
  'u0140全範囲[M0257]を原刊906頁で照合した。非負平方根の中の二平方和・交差項・減算された商の二乗、外側の分母、等号と句点を確認した。固定電子転記の分母sinは原刊のcosと異なり、既存訂正記録に従う。元のハッシュと訂正後の別ハッシュを併記し、原データは変えない。',
  'U=√((v²+w²+2vw cosα)−(vw sinα/V)²)/(1+vw cosα/V²)をs2r/s2s/s2tで保持する。二つのcosと分子のsin、係数2、各積と二乗、非負の根、外側の符号付き商を区別する。二乗式だけや絶対値分母へ置き換えない。',
  'Uは同じ点のKでの全期間の座標微分から得る非負速さ、wは同じ点のkでの二定速度の非負ノルム、vは同じ両系の実際の相対速度、Vは同じ光速である。αの測度とcos/sinに当たる単位円成分はejowを通じて同じ速度ベクトルへ結ぶ。個別の数値記号だけの式にしない。',
  '直前のNach einfacher Rechnung ergibt sich:が導く表示上の結論である。ejpeが同じ前提からejpcを帰結として提示し、ejpfはその同じ計算を評価し、ejpkは表示式を同じ著者・第五節の主張として帰属する。計算導入と式の順序を保つ。',
  '正のV・非負w・単位円条件、非負被開平数と非零分母を保持する。元の角の指定で除外する零ベクトル・縦成分零を黙って拡張しない。一方、点の光速上限や正分母だけへの制限は追加しない。負分母の非負Uに対する反例を保持し、式を正しくするために印刷された主張を改変しない。',
  '既存s2r/s2s/s2tの本体と意味を変えず、現在の物理的な取得規則へ接続し直した。切断の演算、平方根、符号付き逆数、単位円と実数角度、現在履歴と微分を明示する。式全体に固有の新しい基本記号は追加していない。',
  '原刊と転記訂正の構造を確認し、平行・斜め・符号反転・相殺・負分母・零分母・負被開平数の対照を行った。負分母の例では右辺−25と非負ノルム25を区別する。過去の多項式証拠は適用条件を保って参照し、全実切断や全物理状況での導出の機械証明とはしない。',
  '計算への導入、表示式の全項と根号・分数・句点、次の対称性への移行まで通読した。原刊の訂正層、既出の三量の意味、角の枝と符号付き商の読みの下で、式と提示の役割を欠落なく記述したと判断する。歴史的な暗黙条件を一意に確定したり、原文の普遍的な正しさを認定したりする判断ではない。',
 ),
)


@lru_cache(None)
def records():
    catalog=load_catalog(ROOT,BASIS)
    paths={FULL,CORE,BASIS,ANNOTATIONS,SOURCE,REPORT,INVENTORY,DOC,*PRIORS,*DEPENDENCIES,'scripts/review_velocity_composition_claim.py','tests/test_velocity_composition_claim_review.py'}
    pins={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)};merge_pins(pins,catalog.source_sha256)
    for p in (SOURCE,REPORT,*DEPENDENCIES):
        evidence=json.loads(read(p));validate_hashes(ROOT,evidence['source_sha256']);merge_pins(pins,evidence['source_sha256'])
    out=[];selections=([132,133,134,135],[133,134,135]);orders=([132,134,135,133],[134,135,133])
    symbols=(['ejo5','ejo7','ejpa','ejpb','ejpc','ejpd','ejpe','ejpf','ejpi','ejpj','ejpk','s2w','s2x','s2y'],['ejpa','ejpc','ejpk','s2r','s2s','s2t','ejoi','ejoj','ejow','ejpe','ejpd'])
    for i,s in enumerate(source_record()['segments']):
        assert len(REASONS[i])==len(REQUIREMENTS) and all(n in catalog.entries for n in symbols[i])
        corrections=[{k:m[k] for k in ('id','sha256','correction_id','reviewed_math_sha256')} for m in s['math'] if 'correction_id' in m]
        out.append(dict(schema_version='noema-semantic-review-1',work='einstein-1905',unit=s['unit'],reviewer='assistant_review',decision='equivalent_under_stated_reading',document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source=dict(inventory=INVENTORY,unit_sha256=s['unit_sha256'],text=s['text'],range=s['range'],math=[{k:m[k] for k in ('id','sha256')} for m in s['math']]),source_corrections=corrections,selection=selection_binding(catalog,selections[i]),source_order_statements=orders[i],clauses=[dict(range=s['range'],text=s['text'],definitions=symbols[i],reason=REASONS[i][1])],interpretation=LIMITS,limits=['非負の速さ、既出の向き付き角、原刊の訂正層と符号付き商、低負担の計算という明示した読みの下でのアシスタントの通読判断。独立査読・全可能解釈の包含・意味同値の自動証明ではない。','負分母で非負速さと一致しない場合もある印刷式と、その導出・容易さを著者が提示したことの記述。普遍的な物理的真理や導出の健全性を認定しない。','u0141以降、u0147の旧前提への接続、二作品全体の目標は未完。'],unresolved=[],requirements=[dict(id=k,decision='satisfied',reason=v) for k,v in zip(REQUIREMENTS,REASONS[i])],evidence=dict(source_reading=[SOURCE],formal_checks=[REPORT,*DEPENDENCIES],semantic_reading=[DOC]),reviewed_prose_characters=s['source_nonblank_characters'],source_sha256=pins))
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
    return dict(status='angle_explanation_easy_calculation_and_printed_quotient_whole_units_reviewed',document=FULL,source_units={r['unit']:r['reviewed_prose_characters'] for r in records()},reviewed_math_elements=4,source_corrections=records()[1]['source_corrections'],whole_units_semantically_verified=True,verified_full_units={'kant-1784':0,'einstein-1905':2},general_physical_derivation_proved=False,semantic_equivalence_automatically_proved=False,source_sha256=pins)
