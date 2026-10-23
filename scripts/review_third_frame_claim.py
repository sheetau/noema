"""Record a whole reading of the third-frame introduction and its four equation chains."""
from functools import lru_cache
import json
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import REQUIREMENTS,digest,selection_binding,validate_hashes,validate_review
from noema.review_registry import merge_pins
from scripts.compose_third_frame_claim import ROOT,read,FULL,CORE,BASIS,ANNOTATIONS,INDICES,LIMITS
from scripts.check_third_frame_claim import DOC,SOURCE,INVENTORY,PRIOR,DEPENDENCIES,source_record

REPORT='reports/third-frame-claim-v1.json'
REVIEWS=tuple(f'data/einstein-third-frame-claim-u{n:04d}-review-v1.json' for n in (93,94))
CLAUSES=(
 (
  ('Wir führen zu diesem Zwecke ',['ejbi','eisnq','zgm'],'前文の同じφを決定する意図を目的とする導入行為。'),
  ('noch ein drittes Koordinatensystem [M0150] ein, ',['ejbh','ejbb','eisd3','eisd4'],'既出二系へ別の第三系K′を追加導入し呼称を付す。'),
  ('welches relativ zum System [M0151] derart in Paralleltranslationsbewegung parallel zur [M0152]-Achse begriffen sei, ',['eja2','eioj','sfc','ejbh'],'同じkに対し縦軸方向の全配置の平行並進を仮定する。'),
  ('daß sich dessen Koordinatenursprung mit der Geschwindigkeit [M0153] auf der [M0154]-Achse bewege. ',['eja2','eislc','ejbb'],'同じ第三系の原点が−vでkの縦軸上を進む条件。'),
  ('Zur Zeit [M0155] mögen alle drei Koordinatenanfangspunkte zusammenfallen ',['eja3','ei46','ejbb'],'t=0の同じ基準出来事で三原点を一致させる仮定。'),
  ('und es sei für [M0156] die Zeit [M0157] des Systems [M0158] gleich Null. ',['eja3','ejbg','ejbj'],'同じt=x=y=z=0で第三系の時刻t′も零とし、その記号の規則を保持する。'),
  ('Wir nennen [M0159] die Koordinaten, im System [M0160] gemessen, ',['ejbd','ejbe','ejbf','ejbj','eisnw'],'第三系で測る三位置座標にx′,y′,z′を採用する現在の命名。'),
  ('und erhalten durch zweimalige Anwendung unserer Transformationsgleichungen:',['ejbl','ejbc','ejbk','eja6','eja7'],'同じ四式を同じ中間記録で二回適用し、後続の全四連鎖等式を得るという提示。'),
 ),
 (('[M0161]',['ejbk','ejba','eja4','eja5','eja6','eja7','srd','sre','srf','srg','srh'],'同じ三系の現在記録に対するt′,x′,y′,z′の全四連鎖等式。各中間式と共通倍率の最終式、全八等号を保持する。'),),
)
REASONS=(
 (
  '固定u0093の全575文字・非空白本文426文字とM0150–M0160を原刊901頁へ照合した。前文のφ決定意図から第三系導入の三文と後続表示式まで通読し、印字Ξと三位置記号を確認した。',
  '同じ目的への手段、第三系の追加導入、kに対する全体並進と−vの原点軌道、縦軸上条件、t=0の三原点一致、同じ零出来事でのt′=0、測定座標の命名、同じ四式の二回適用と結果の提示を保持する。',
  'zu diesem Zweckeはzgnの同じspcの決定意図を受ける。K′はzgi、kはzbm、Ξはkの縦軸、三零点の基準出来事はzgkである。x′,y′,z′とt′は第三系の現在の測定規則に固定し、以前の補助x′や他系の値を代用しない。',
  'Wir führenは議論上の導入、sei/mögenは同じ設定の仮定、Wir nennenは現在の三位置座標の命名、erhaltenは二回適用から結果を得る著者の提示として分ける。同じ著者・論説・第三節と前文からの順序を保ち、仮定の引用を現実の実証に替えない。',
  '目的に決定の成功や唯一解を加えず、単なる意図の新規発生へ弱めない。三系を別とし、第三系の存在を世界唯一としない。原点の軌道が軸に平行なだけの横ずれ、別出来事の零点の混合、記録欠落を空の全称で隠すことを拒否する。第四の時刻命名やφ=1を補わない。',
  '導入・仮定・個体呼称・現在測定・全配置並進・二回変換・結果帰属を既存定義で合成する。新しい関係は表明済み意図を受ける一般目的関係eisnqと量規則の一般命名関係eisnwであり、五呼称以外に原文専用の未説明な内容原始語を作らない。',
  '原刊と固定本文・意味規約の通読を根拠とし、先の280対照例による運動・三記録・全八等式の検査、今回の目的・命名・引用・帰属の検査を別の証拠として保持する。物理基礎への境界、有限例と一般量化、著者の主張と処理系による真理証明を区別する。',
  '目的付き導入から二つの仮定文の条件、三位置の命名、二回適用の結果を導くコロンまで再読した。全配置・現在の同じ出来事の記録と、既出意図への手段という明示した読みの下で、三文の関係・参照・提示を欠落なく記述したと判断する。',
 ),
 (
  '固定u0094のM0161を原刊901頁の四行に照合した。順序t′,x′,y′,z′、八等号、時間式のv/V²とξ、第一位置式のvτ、二つのβ(−v)、横二式にβがないこと、各最終値の同じφ(v)φ(−v)を確認した。',
  '同じ出来事の三記録に同じ四式をvと−vで続けて適用する中間式と、全四成分が元の対応成分の共通倍率倍になる最終式を両方保持する。全対象への記録の存在と各系の値の一意性をeja5で要求し、同じ値の別記録は許す。',
  't,x,y,zはKの第一記録、τ,ξ,η,ζはkの同じ中間記録、t′,x′,y′,z′はK′の最後の記録である。同じV=tc、v=zb7、正規化後φ=spcを用い、φ(−v)を別関数やφ(v)の値へ交換しない。',
  'u0093のerhalten durch zweimalige Anwendungに続く結果表示であり、ejblのzcが現在四式と第三系の設定・二回適用ejbcからejbkを得ると提示する。同じ著者・節へ帰属し、単独の無条件の物理的実証としない。',
  '中間式を最終倍率だけで省略せず、時刻を除いた三位置だけに縮めない。βの正の枝を保ち、負の速度を正速度専用条件へ押し込めない。φの正負値の対称性、正値・非零、積1、相対静止や恒等変換を加えない。',
  '実切断の四式sre、同じ中間記録の二回適用srf、全四成分への倍率srgと同じ関数の積srhを再利用する。旧shd/smkによる記録依存を避け、現在のeiyxと全対応三組への量化へ接続する。',
  '保存済みの有理代数証拠と、正負で異なるφ、零・負のφ、積が1以外の例、全四中間成分と全四最終成分の変更に対する対照検査を保持した。これは任意の実切断と全物理世界の真理の証明ではなく、通読判断とは別の局所証拠である。',
  'u0093末尾の適用提示から四行の各項・係数・符号・分母・等号・句点まで再読した。同じ出来事の現在三記録と同じ関数の二回適用という読みの下で、全四連鎖等式と論述上の役割を欠落なく記述したと判断する。',
 ),
)


@lru_cache(None)
def records():
    catalog=load_catalog(ROOT,BASIS);paths={FULL,CORE,BASIS,ANNOTATIONS,SOURCE,REPORT,INVENTORY,DOC,PRIOR,*DEPENDENCIES,'scripts/review_third_frame_claim.py','tests/test_third_frame_claim_review.py'}
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
        selection=list(INDICES if i==0 else [INDICES[1]])
        out.append(dict(schema_version='noema-semantic-review-1',work='einstein-1905',unit=s['unit'],reviewer='assistant_review',decision='equivalent_under_stated_reading',document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source=dict(inventory=INVENTORY,unit_sha256=s['unit_sha256'],text=s['text'],range=s['range'],math=[{k:m[k] for k in ('id','sha256')} for m in s['math']]),selection=selection_binding(catalog,selection),source_order_statements=selection,clauses=clauses,interpretation=LIMITS,limits=['既出の意図への手段、全配置の並進、同じ出来事の現在三記録と二回適用という明示した読みの下でのアシスタントの通読判断。独立査読、一般物理的導出や意味同値の自動証明ではない。','u0095以降と二作品全体の目標は未完。'],unresolved=[],requirements=[dict(id=k,decision='satisfied',reason=v) for k,v in zip(REQUIREMENTS,REASONS[i])],evidence=dict(source_reading=[SOURCE],formal_checks=[REPORT,*DEPENDENCIES],semantic_reading=[DOC]),reviewed_prose_characters=s['source_nonblank_characters'],source_sha256=pins))
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
    return dict(status='third_frame_introduction_and_double_transform_whole_units_reviewed',document=FULL,source_units={r['unit']:r['reviewed_prose_characters'] for r in records()},reviewed_math_elements=12,whole_units_semantically_verified=True,verified_full_units={'kant-1784':0,'einstein-1905':2},semantic_equivalence_automatically_proved=False,source_sha256=pins)
