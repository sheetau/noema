"""Whole reading of mutual rest, attributed identity necessity and reciprocal scale."""
from functools import lru_cache
import json
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import REQUIREMENTS,digest,selection_binding,validate_hashes,validate_review
from noema.review_registry import merge_pins
from scripts.compose_reciprocal_claim import ROOT,read,FULL,CORE,BASIS,ANNOTATIONS,INDICES,LIMITS
from scripts.check_reciprocal_claim import DOC,SOURCE,INVENTORY,PRIOR,DEPENDENCIES,source_record

REPORT='reports/reciprocal-claim-v1.json'
REVIEWS=tuple(f'data/einstein-reciprocal-claim-u{n:04d}-review-v1.json' for n in (95,96))
CLAUSES=(
 (
  ('Da die Beziehungen zwischen [M0162]und [M0163] die Zeit [M0164] nicht enthalten, ',['ejbr','ejbs','srh'],'同じK/K′の三位置関係が同じ速度だけの倍率で書け、時間tを含まないことを理由とする。'),
  ('so ruhen die Systeme [M0165] und [M0166] gegeneinander, ',['ejbq','ejbt','ejbw'],'その理由から同じKとK′が両向きに相対静止すると述べる。'),
  ('und es ist klar, ',['ejbx','zdg'],'後続の同じ恒等変換の内容を明らかだと提示する。'),
  ('daß die Transformation von [M0167] auf [M0168] die identische Transformation sein muß. ',['ejbu','ejbx','zc'],'KからK′への変換が四座標全ての恒等変換でなければならないと推論する。'),
  ('Es ist also:',['ejbv','ejby','sro'],'同じ連鎖等式と恒等性から後続の相反積1を結論する提示。'),
 ),
 (('[M0169].',['sro','srh','spc','ejby'],'同じ正規化後のφをvと−vで評価した二値の積が1であると述べ、句点で結ぶ。'),),
)
REASONS=(
 (
  '固定u0095の全253文字・非空白本文167文字とM0162–M0168を原刊901頁末・902頁冒頭へ照合した。頁境界をまたぐ同じ第一文とEs ist alsoの第二文導入を通読した。固定本文のM0162直後の空白欠如は語の関係を変えず、その本文は変更しない。',
  '同じ空間式の時間tの非出現を理由とする相互静止、その静止に続く恒等変換の必要性と明白さ、同じ連鎖等式・恒等性から後続相反積への結論提示を保持する。空間三式・静止・四座標恒等性を一つの未説明の関係へまとめない。',
  'x′,y′,z′は第三系K′、x,y,zはKの同じ出来事の現在記録であり、以前の補助x′を指さない。tはKの時刻。K→K′の向きを保ち、共通倍率は直前の同じspcの正負速度値の積srhに固定する。',
  'Da ... soはその理由から相互静止が従うというzc、sein mußも恒等性がその前提から従わなければならないという同じ推論帰属、ist klarは同じ恒等性の明白さzdgとして述べる。Es ist alsoは次の表示式へ進む第三の結論提示であり、全て同じ著者・論説・節と本文順序を保つ。',
  '時間を含まないことを時間変換式の削除や座標全体の不変性へ替えず、原点だけの静止や一時点の標本だけに縮めない。恒等性には時間を含む全四成分を保持し、二系個体や記録名の同一性を加えない。一般には不足する校正条件や非零証人を原文の前提へ補って推論を修理しない。',
  '空間式は既存実切断の積と各位置成分だけから構成するejbr、相互静止は全配置・全時点のeiojの零速度、恒等性は現在三記録とshhの値一致として構成する。必要性を含む既存zcと明白さzdgを再利用し、新しい原始語にこの一文を埋め込まない。',
  '原刊・固定本文・意味規約の通読に、空間式の時刻変更、全四成分の恒等性、同値の別記録、全配置の静止の本体、全対象の存在と引用・帰属の対照を併記する。有限モデルの域と演算を明示し、未知入力に架空の値を補わない。著者の推論の妥当性をこれらの成功だけで証明したとはしない。',
  '901頁末の理由節から902頁冒頭の恒等変換の必要性・明白さ、Es ist alsoまで再読した。具体的な時間引数のない三式、全配置の相互静止、現在四座標の恒等性と著者への帰属という読みの下で、二文の参照・範囲・提示を欠落なく保持したと判断する。',
 ),
 (
  '固定u0096のM0169と句点を原刊902頁冒頭へ照合した。二つの同じφ、第一引数v、第二引数−v、二値の積、等号と右辺1を確認した。',
  '同じ正規化後の関数φのvと−vの値を共に有効な実切断として扱い、その積が1であるsroを述べる。単なる二値の等しさや各値1という条件へ替えない。',
  'φは前の四連鎖等式・未知関数の決定意図と同じspc、vは同じzb7、積は同じsrh。以前の係数aをφとして代用せず、正負引数に別々の関数を割り当てない。',
  'u0095末尾のEs ist alsoに続く結論であり、ejbyが現在の連鎖等式と恒等性ejbvから同じsroを述べる。著者と同じ論述箇所zgsへ帰属し、前提なしの処理系による物理的実証として扱わない。',
  '相反する二値がそれぞれ1であること、正値性、後続の長さによる対称性を加えない。零原点での恒等性だけでは倍率を決められないことを検査側で保持する一方、原文にない非零記録を著者の前提へ足さない。',
  '既存の同じ関数適用spc、符号反転、実切断の乗法と値同値を用いるsro/srhを再利用する。意味規約を変えず、全記録と結論への前提だけを現在の測定へ更新する。',
  '原刊の表示式の通読と、正・負の相反する組、積が1でない組、零原点の反例を局所対照として保持する。保存済み有理代数証拠と同じ関数の引数の検査を使い、全実切断・全物理世界の真理又は意味同値の自動証明とはしない。',
  '直前の恒等変換への推論からEs ist also、二値の積と右辺1、句点まで再読した。同じ関数の正負速度値の相反関係を著者が結論するという明示した読みの下で、式と論述上の役割を欠落なく記述したと判断する。',
 ),
)


@lru_cache(None)
def records():
    catalog=load_catalog(ROOT,BASIS);paths={FULL,CORE,BASIS,ANNOTATIONS,SOURCE,REPORT,INVENTORY,DOC,PRIOR,*DEPENDENCIES,'scripts/review_reciprocal_claim.py','tests/test_reciprocal_claim_review.py'}
    pins={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)};merge_pins(pins,catalog.source_sha256)
    for p in (SOURCE,REPORT,*DEPENDENCIES):
        evidence=json.loads(read(p));validate_hashes(ROOT,evidence['source_sha256']);merge_pins(pins,evidence['source_sha256'])
    out=[]
    for i,s in enumerate(source_record()['segments']):
        clauses=[];offset=0
        for text,symbols,reason in CLAUSES[i]:
            assert s['text'][offset:offset+len(text)]==text and all(n in catalog.entries for n in symbols)
            clauses.append(dict(range=[offset,offset+len(text)],text=text,definitions=symbols,reason=reason));offset+=len(text)
        assert offset==len(s['text']) and len(REASONS[i])==len(REQUIREMENTS)
        selection=list(INDICES if i==0 else [INDICES[-1]])
        out.append(dict(schema_version='noema-semantic-review-1',work='einstein-1905',unit=s['unit'],reviewer='assistant_review',decision='equivalent_under_stated_reading',document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source=dict(inventory=INVENTORY,unit_sha256=s['unit_sha256'],text=s['text'],range=s['range'],math=[{k:m[k] for k in ('id','sha256')} for m in s['math']]),selection=selection_binding(catalog,selection),source_order_statements=selection,clauses=clauses,interpretation=LIMITS,limits=['具体的な時間引数のない空間三式、全配置の相互静止、現在四座標の恒等性と推論の帰属という読みの下でのアシスタントの通読判断。独立査読、一般物理的導出や意味同値の自動証明ではない。','u0097以降と二作品全体の目標は未完。'],unresolved=[],requirements=[dict(id=k,decision='satisfied',reason=v) for k,v in zip(REQUIREMENTS,REASONS[i])],evidence=dict(source_reading=[SOURCE],formal_checks=[REPORT,*DEPENDENCIES],semantic_reading=[DOC]),reviewed_prose_characters=s['source_nonblank_characters'],source_sha256=pins))
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
    return dict(status='mutual_rest_identity_and_reciprocal_scale_whole_units_reviewed',document=FULL,source_units={r['unit']:r['reviewed_prose_characters'] for r in records()},reviewed_math_elements=8,whole_units_semantically_verified=True,verified_full_units={'kant-1784':0,'einstein-1905':2},semantic_equivalence_automatically_proved=False,source_sha256=pins)
