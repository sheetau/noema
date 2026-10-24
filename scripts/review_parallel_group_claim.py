"""Review the complete cross-page alternative/composition/group passage."""
from functools import lru_cache
import json
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import REQUIREMENTS,digest,selection_binding,validate_hashes,validate_review
from noema.review_registry import merge_pins
from scripts.compose_parallel_group_claim import ROOT,read,FULL,CORE,BASIS,ANNOTATIONS,LIMITS
from scripts.check_parallel_group_claim import DOC,SOURCE,INVENTORY,PRIORS,DEPENDENCIES,source_record

REPORT='reports/parallel-group-claim-v1.json'
REVIEWS=tuple(f'data/einstein-parallel-group-u{n:04d}-review-v1.json' for n in (147,148,149))
REASONS=(
 (
  'u0147全範囲の二文を原刊906頁へ照合した。第一文のWir hätten、同方向の場合、auch、二変換の合成、§3、erhalten könnenを確認した。第二文のFühren wirから第三系・原点・Ξ軸・速度w・対応座標・§3と同形式・vだけの置換までを、次のM0285と907頁のtrittへ続く一文として読んだ。',
  '第一文は現在より前の同じ段階に利用可能だった別の方法ejrfであり、以前の方法と別方法が同じejprへ至る。第二文は同じK/kへ第三系を加えるejrmと、その設定及び二回適用ejq7から同じ四式の速度引数だけを置換したejq6を得るejrnである。点の同方向条件と第三系の並進条件を混同しない。',
  '第一文のU/v/wは現在の同じ点の取得ejpaと同方向の内容ejprへ結ぶ。別導出の補助設定では第三系速度zltと点速度zkqの対応及び同じ点の全現在出来事を第三系原点へ合わせる条件を明示した。第二文のk′はzloで、§3の逆変換第三系zgiではない。K/kは先行eiwvと命名zcg、x/y/z/tは現在の測定・時刻の規則へ参照する。',
  'wirは著者の論述上の声とし、過去の別導出、第三系の思考上の導入・仮定・命名、条件から得る式という各役割を同じ著者・論説・第五節へ帰属する。光速度表示zln、振り返りzm2、導入zlr、結果zlsの本文順序を保持する。実行済みの歴史や現実の第三系の実在は補わない。',
  'hätten…könnenを実行や不採用へ替えず、同じ結論へ至る別方法の利用可能性として保持した。物理的な系速度には光速未満条件がある一方、前段の点速度の式は狭めていない。§3と同じ式のための共通原点・零時刻・校正を明示し、任意の原点ずれを消さない。著者の方法の終点と一般的な導出の妥当性を区別する。',
  '全体並進と軸上原点はeja2、現在三記録はeiyx/ejqv、非空全対象の存在と値の一意性はejqw、二変換と同形式の置換はs4m/s4l/s3jへ分解する。別導出は非空有限列・利用可能性・許容規則・同じ結論をs2w/s5i/s5hで構成し、同じ点の全履歴と実際の速さへ接続する。一文専用の基本述語は追加していない。',
  '三系の校正・全原点座標・共有中間記録・全候補記録、補助原点と同じ点の出来事・全履歴・速さ、過去段階・同じ方法の各手順、節と量の参照、帰属と順序を保存済み対照及び今回の検査で確認した。全実数量化を標本へ縮めず、有限例や許容手順を一般の物理導出の証明としない。',
  '二文全体と式・次頁の動詞までを通読した。明示した過去の利用可能性、補助第三系による点の式への接続、既出K/kに加える第三系の同形式の四変換という読みの下で、条件・参照・提示・ページをまたぐ連続を欠落なく記述したと判断する。領域差は隠さず、著者の推論の正しさの認定とは分けた。',
 ),
 (
  'u0148全範囲[M0285]を原刊906頁末へ照合した。分子v+w、分母1+vw/V²と、前のdie Größe及び次頁のtrittを確認した。独立した等式ではなく、§3の式のvに代わって入る量として読む。',
  's3j(tc,zb7,zlt)がこの二重分数の値を構成し、その同じ値をs4lの速度引数へ渡すejq3/ejq6で置換を表す。βも合成速度を引数に取り、時刻式・縦位置式・横二成分を全て保持する。単なる通常の和v+wや係数β(v)β(w)ではない。',
  'vは同じKに対するkの速度zb7、ここでのwはk′のkに対する速度zlt、Vは同じ光速度tcである。wを前段の点速度と無条件に同一視せず、その対応は別導出の補助設定に限って明示する。初系・中間系・第三系の同じ出来事の現在記録へ結ぶ。',
  '式はejrnで第三系設定と二回適用から得る同形式の四式の一部として提示され、ejrwが導入zlrから結果zlsへの本文順序を保つ。前文・表示・trittを別々の発話へ分断せず、同じ著者・論説・第五節へ帰属する。',
  '式自体の符号付き商と、二つの物理的な系速度の光速未満条件を区別する。負の速度と零を排除せず、原点ずれや任意の尺度率を補わない。物理的に実現する全出来事の範囲を、全実数四組の実在へ拡張しない。',
  '二重分数は既存の実切断の加算・積・逆数s3jで構成する。同形式という関係は同じs4lを共有し、その速度引数だけを変えることで保持する。全対象の存在・値の一意性と全対応記録への適用をejqw/ejqzへ分け、式が成立する記録だけを選ばない。',
  '既存の有理多項式検査は合成速度の領域・係数と四式の一致を扱う。現在記録の対照は時刻・横座標・中間記録の取り違えと誤ったβ積を拒否する。今回の帰属・参照検査と原刊照合を併用したが、有限対照を全実切断の演算法則や一般物理導出の証明とはしない。',
  '表示式全体を、その前の速度置換の指定と後の動詞に接続して再読した。同じ三系の四変換の速度引数を原刊の商へ置き換えるという明示した読みの下で、全式と提示を欠落なく記述したと判断する。',
 ),
 (
  'u0149全範囲を原刊907頁冒頭へ照合した。前頁の文を閉じるtrittとセミコロン、man sieht daraus、solche Paralleltransformationen、挿入句wie dies sein muß、eine Gruppe bildenを確認した。次の運動学の総括u0150はこの単位へ混ぜない。',
  '冒頭はejrn/ejrwの同形式の置換を完結する。主節は現在の合成結果と全域の合成則ejroから同じ変換族の群s5fが分かるというejrpである。挿入句は同じ数学的前提ejrkに相対的な非空全称の必要性ejrlを、同じ群の主張へ補うejrqである。',
  'darausは直前の合成結果を指し、solcheは同じ軸・光速度・係数1・共通原点の変換族を指す。diesは同じ群の内容s5fであり、第三系の実在や表示式単独に替えない。数学的な全速度・全四入力の域と、現在の三系の物理的記録域は別に保持する。',
  '群の帰結提示を同じ著者・論説・第五節へ帰属し、合成結果zlsから群zluへの順序を保つ。必要性の補足はeisa5で同じs5fへ挿入的に結び、独立した後続の論点や読者の承認済みの内容にしない。帰属から引用された群や必要性の真理を実行しない。',
  '群は閉性だけではなく結合則・両側単位元・両側逆と全写像の一致を含む。負の速度と零を残し、正速度だけの集合や全方向の変換一般へ変更しない。必要性は固定した数学的解釈内の全評価状況に関する読みで、義務や全モデルでの論理的必然性とはしない。前提範囲の非空性を要求する。',
  '群はs44/s47とs5a–s5eで合成的に構成する。ejrjは前提が真の状況だけを候補とし、s5kでその非空全域に同じ結論を要求する。ejrkの正のVと異なる四役割は群の成否を参照しない。未説明な選定zlzを用いず、一文専用の基本述語へ必要性を隠していない。',
  '必要性を前提・結論の全真偽組合せで対照し、空の候補、失敗する一候補、選ばれていない現在の真理を区別した。群の既存証拠は閉性と群の違い、結合則、両側逆、全写像の同一性を扱う。符号付き速度と四座標の対照、全実数量化の列挙拒否、挿入句の対象と発話帰属を確認した。',
  '前頁からの動詞、合成から分かるという主節、同じ変換族、群の構造、必要性の挿入句まで通読した。明示した数学的設定に相対的な必要性という読みの下で、単位全体の内容・参照・提示を欠落なく記述したと判断する。数学的内容が状況に依存しない場合の真偽の固定性を隠さず、著者の推論の機械証明とは区別した。',
 ),
)

@lru_cache(None)
def records():
    catalog=load_catalog(ROOT,BASIS)
    paths={FULL,CORE,BASIS,ANNOTATIONS,SOURCE,REPORT,INVENTORY,DOC,*PRIORS,*DEPENDENCIES,'scripts/review_parallel_group_claim.py','tests/test_parallel_group_claim_review.py'}
    pins={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)};merge_pins(pins,catalog.source_sha256)
    for p in (SOURCE,REPORT,*DEPENDENCIES):
        evidence=json.loads(read(p));validate_hashes(ROOT,evidence['source_sha256']);merge_pins(pins,evidence['source_sha256'])
    selections=([145,146,148],[146],[146,147,149]);orders=([148,145,146],[146],[146,147,149])
    symbols=(['ejri','ejrf','ejrc','ejrd','ejre','ejpr','ejrm','ejrn','ejrv','ejrw','ejq4','ejq7','ejq6'],['s3j','s4l','s4m','ejqv','ejqw','ejqz','ejq3','ejq6','ejrn','ejrw'],['ejrn','ejrw','ejro','ejrp','ejrq','ejrx','ejry','ejrj','ejrk','ejrl','s5k','s5f','s5e','s47','s44'])
    out=[]
    for i,s in enumerate(source_record()['segments']):
        assert len(REASONS[i])==len(REQUIREMENTS) and all(n in catalog.entries for n in symbols[i])
        out.append(dict(schema_version='noema-semantic-review-1',work='einstein-1905',unit=s['unit'],reviewer='assistant_review',decision='equivalent_under_stated_reading',document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source=dict(inventory=INVENTORY,unit_sha256=s['unit_sha256'],text=s['text'],range=s['range'],math=[{k:m[k] for k in ('id','sha256')} for m in s['math']]),selection=selection_binding(catalog,selections[i]),source_order_statements=orders[i],clauses=[dict(range=s['range'],text=s['text'],definitions=symbols[i],reason=REASONS[i][1])],interpretation=LIMITS,limits=['明示した過去の利用可能性、第三系原点を使う補助導出、同じ四式の速度置換、符号付きの平行変換群、固定した数学的解釈内の必要性という読みの下でのアシスタントの判断。独立査読・唯一の歴史的語義・意味同値の自動証明ではない。','前段の点速度と補助第三系の速度域の差を保持し、著者の一般物理導出や許容規則の健全性を認定しない。全実数四入力の数学的性質から、全四入力が物理的に実在するとはしない。','u0150以降と二作品全体の目標は未完。'],unresolved=[],requirements=[dict(id=k,decision='satisfied',reason=v) for k,v in zip(REQUIREMENTS,REASONS[i])],evidence=dict(source_reading=[SOURCE],formal_checks=[REPORT,*DEPENDENCIES],semantic_reading=[DOC]),reviewed_prose_characters=s['source_nonblank_characters'],source_sha256=pins))
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
    return dict(status='alternative_third_frame_composition_and_group_whole_units_reviewed',document=FULL,source_units={r['unit']:r['reviewed_prose_characters'] for r in records()},reviewed_math_elements=12,whole_units_semantically_verified=True,verified_full_units={'kant-1784':0,'einstein-1905':3},general_physical_derivation_proved=False,semantic_equivalence_automatically_proved=False,source_sha256=pins)
