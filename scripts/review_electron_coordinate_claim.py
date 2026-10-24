"""Review the whole normalization choice and comoving-rest unit."""
from functools import lru_cache
from pathlib import Path
import json
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import REQUIREMENTS,digest,selection_binding,validate_hashes,validate_review
from noema.review_registry import merge_pins
ROOT=Path(__file__).resolve().parents[1]
def read(path):return (ROOT/path).read_text(encoding='utf-8')
FULL='examples/v014/einstein-electron-coordinate-claim.noema';CORE='examples/v014/electron-coordinate-claim-core.noema'
BASIS='data/electron-coordinate-claim-basis-v1.json';ANNOTATIONS='data/electron-coordinate-claim-identifiers-v1.json'
SOURCE='data/einstein-electron-coordinate-reading-v1.json';REPORT='reports/electron-coordinate-claim-v1.json'
INVENTORY='artifacts/written-units-v1/einstein-1905.json';DOC='docs/electron-coordinate-claim-v1.md'
REVIEW='data/einstein-electron-coordinate-u0245-review-v1.json'
CLAUSES=(
 ('Ohne die Allgemeinheit der Betrachtung zu beeinflussen, ',[417],['ek6e','ek54','ek55','ek6a','ek6b','ek6d','ek6k','zct'],'全ての許容物理設定に対し、同じ物理的法則の答え候補を双方向に保つ代表配置があるという一般性。場・軌道・微分・単位・対象を同じ座標変更へ結び、その一般性を仮定を採る根拠として提示する。単なる三速度の回転だけでは済ませない。'),
 ('können und wollen wir annehmen, ',[417],['ek6j','ek6k','eism4','ug'],'同じ著者が同じ仮定採用行為を正当に行えることと、その仮定を今採用する決定を述べる。許容と採用を分け、物理的な実験又は単なる願望へ替えない。'),
 ('daß das Elektron in dem Momente, wo wir es ins Auge fassen, ',[417],['ek6f','ek6g','eisxh','eisxv','eisnx','eisra'],'先に導入した同じ電子を、前の第二の場合で指定した同じ出来事において考察へ取り上げる。閉じた特徴内容が同じ電子と出来事を固定し、視覚的観測の実施を補わない。'),
 ('sich im Koordinatensprung befinde ',[417],['ek56','ek6f','ek6g','ek47'],'原刊のKoordinaten-sprungを座標原点と読み、指定出来事をKの空間原点へ置く。綴りを修正せず、括弧の時刻指定と合わせて同じ四原点に結ぶ。'),
 ('und sich längs der [M0399]-Achse des Systems [M0400] mit der Geschwindigkeit [M0401] bewege. ',[417],['ek56','ek6f','ek6i','ek4r','eisxt','eisxu','eisx5','eisnb','ek6l','ek6m'],'同じKのX方向へ瞬間速度(v,0,0)を選び、vはu0244の同じ非負の速さへ結ぶ。電子の全時間の一定速度や、この第一文での光速上限を補わない。第一文の句点までを同じ著者に帰属する。'),
 ('Es ist dann einleuchtend, ',[418],['ek6r','ek6s','uh','zdg','eisra'],'第一文の同じ仮定を受けた帰結として、著者が同じ物理内容ek6rを述べて明白として提示する。有限検査が物理的な真理を証明したという意味にはしない。'),
 ('daß das Elektron im genannten Momente ([M0402] ) ',[418],['ek6n','ek6o','eisxv','ek6h','ek6t','ek6u','eisa5'],'第一文と同じ電子・出来事を指し、括弧t=0は同じKの時刻成分の零を補足する。別の時点、kの時刻零又は有限の静止期間へ替えない。'),
 ('relativ zu einem längs der [M0403]-Achse mit der konstanten Geschwindigkeit [M0404] parallelbewegten Koordinatensystem [M0405] ',[418],['ek6n','ek5w','ek5n','ek5s','eioj','eisxy','eisxz','eisx2','eisx3','eisx4','ek6p'],'同じKのX方向へ同じvで等速並進する一つのkを選び、同じ単位と出来事対応、両系の完全な局所履歴へ接続する。原点ずれを未指定に保ち、存在内容は新系での静止を前提にしない。一定速度が掛かるのは座標系である。'),
 ('ruht.',[418],['ek6o','ek5x','seoc','ek6q','ek6r','ek6v','ek6w'],'同じ選んだ配置において、同じ出来事の新座標時刻に対する実際の三微分が零となるという瞬間静止を帰結にする。加速度零や前後の静止を要求せず、第二文の句点までを同じ著者の論説へ帰属する。'),
)

@lru_cache(None)
def records():
    catalog=load_catalog(ROOT,BASIS);s=json.loads(read(SOURCE));basis=json.loads(read(BASIS))
    paths={FULL,CORE,BASIS,ANNOTATIONS,SOURCE,REPORT,INVENTORY,DOC,'scripts/review_electron_coordinate_claim.py','tests/test_electron_coordinate_claim_review.py'}
    pins={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)};merge_pins(pins,catalog.source_sha256)
    for p in (SOURCE,REPORT):
        evidence=json.loads(read(p));validate_hashes(ROOT,evidence['source_sha256']);merge_pins(pins,evidence['source_sha256'])
    clauses=[];offset=0
    for text,indices,symbols,reason in CLAUSES:
        assert s['text'][offset:offset+len(text)]==text,(offset,text)
        assert all(n in catalog.entries for n in symbols)
        clauses.append(dict(range=[offset,offset+len(text)],text=text,statements=indices,definitions=symbols,reason=reason));offset+=len(text)
    assert offset==len(s['text']) and s['unit']=='einstein-1905:u0245'
    reasons=(
     '固定u0245全文と七数式出現を原刊917–918頁に照合した。前の第二の場合と初期運動法則の探究、後のkでの運動式と原点指定の間に置き、一般性、許容と採用、考察する指定瞬間、原点、X方向とv、明白さ、同じ瞬間の括弧t=0、等速並進系k、静止と二つの句点まで連続して扱う。原刊にもあるKoordinaten-sprungの綴りは保持する。',
     '一般性は同じ全物理設定と法則候補を保つ代表の存在ek6eとして構成済みであり、第一文の著者提示と採用理由へ結ぶ。ek6f/gが同じ電子・出来事・Kの四原点・瞬間速度をまとめる。第二文は同じ設定へのek5wとek5xを接続し、完全な校正履歴と旧微分の条件、新系の実際の三微分零を前提と帰結に分ける。非空性ek6pを併記して空虚な帰結にしない。',
     '電子eisxhと瞬間速さeisxtは前段から引き継ぐ。eisxvは指定された同じ出来事への参照で、二文の条件と帰結で変えない。選んだk・原点ずれ・新時間域・曲線を同じ四参照に固定し、後続でも利用できる。全33設定引数を同じ順序で共有し、Xの二出現・vの二出現・K・k・t=0の七数式出現を同じ役割へ結ぶ。',
     '第一文は一般性を述べ、正当に採れる仮定を今採用すると表明する論述上の決定として読む。許容eism4は引用された同じ採用行為ek6jを対象とし、ugの実際の採用、eisnxの考察への取上げと区別する。第二文のuhとzdgは同じek6rを対象にし、第一文へのeisra、括弧eisa5、著者帰属eir3と順序ueを保存する。',
     'Koordinatensprungを座標原点と読む解釈を明示する。第一文には光速上限を先取りせず、第二文は正のtcと0≤v<tcの局所的な共動系という適用範囲を明示する。零速度を許す。t=0はKの時刻であり、kの零原点は後続u0248まで保留する。電子の全期間の等速、前後の静止、加速度零、無放射、運動方程式の特定の答えを補わない。',
     '新原始記号は指定出来事、二つの本文箇所、選んだ系とその未指定のずれ・履歴、二つの表記への参照だけである。それぞれを物理的な条件、同一の対象、実際の微分へ合成で接続する。一般性・仮定の許容と採用・考察・並進・瞬間静止・明白さを新しい一個の述語に委ねない。既存の基本概念の意味規約を保存する。',
     '局所検査は全33設定引数、同じk・tc・ずれ・履歴、指定出来事、時刻零、非空性と帰結、引用と実行、許容と採用、同一の主張と明白さ、表記と本文順序を対照する。29証人の結合は他の束縛を固定した二値診断であり全関数域の証明ではない。既存の回転・場変換・履歴・実微分の検査証拠を固定し、未知の入力と全関数域の有限認定の拒否を保つ。',
     '原刊の二文を前後の文脈とともに再読した。一般性を保って同じ電子を指定瞬間のK原点とX方向のvへ配置すると採用し、その同じ瞬間には同じvで等速並進するkに対し静止することを明白として述べる、という内容と提示を保持したと判断する。読みの限定と未指定のk原点を明記した上での全単位判断であり、後の三式や第十節見出しの完成を主張しない。',
    )
    assert len(reasons)==len(REQUIREMENTS)
    return [dict(schema_version='noema-semantic-review-1',work='einstein-1905',unit=s['unit'],reviewer='assistant_review',decision='equivalent_under_stated_reading',document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source=dict(inventory=INVENTORY,unit_sha256=s['unit_sha256'],text=s['text'],range=s['range'],math=[{k:m[k] for k in ('id','sha256')} for m in s['math']]),selection=selection_binding(catalog,[417,418]),source_order_statements=[417,418],clauses=clauses,interpretation=basis['limitations'],limits=['明示した読みの下でのアシスタントによる全単位判断。独立査読、物理法則の真理、原文同義性の自動証明ではない。','kの零原点選択、kでの三運動式とKへの変換、u0244の法則の答えへの接続は後続の単位で行う。','第十節見出しと二作品全体の目標は未完。'],unresolved=[],requirements=[dict(id=k,decision='satisfied',reason=v) for k,v in zip(REQUIREMENTS,reasons)],evidence=dict(source_reading=[SOURCE],formal_checks=[REPORT],semantic_reading=[DOC]),reviewed_prose_characters=s['source_nonblank_characters'],source_sha256=pins)]
def prepare():
    from scripts.audit_opening_scope import write_exact
    write_exact(ROOT/REVIEW,json.dumps(records()[0],ensure_ascii=False,indent=2)+'\n')
@lru_cache(None)
def build_report():
    catalog=load_catalog(ROOT,BASIS);inventory=json.loads(read(INVENTORY));active=dict(document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source_inventory=INVENTORY)
    r=records()[0];assert json.loads(read(REVIEW))==r;validate_review(ROOT,REVIEW,'einstein-1905',active,catalog,inventory)
    pins=dict(r['source_sha256']);pins[REVIEW]=digest((ROOT/REVIEW).read_bytes())
    return dict(status='electron_coordinate_choice_and_comoving_rest_whole_unit_reviewed',document=FULL,source_units={r['unit']:r['reviewed_prose_characters']},reviewed_math_elements=7,whole_units_semantically_verified=True,verified_full_units={'kant-1784':0,'einstein-1905':1},semantic_equivalence_automatically_proved=False,source_sha256=pins)
