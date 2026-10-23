"""Read the complete two-sentence transfer consequence under its explicit interpretation."""
from functools import lru_cache
import json
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import REQUIREMENTS,digest,selection_binding,validate_hashes,validate_review
from noema.review_registry import merge_pins
from scripts.compose_clock_transfer_claim import ROOT,read,FULL,CORE,BASIS,ANNOTATIONS,INDICES,LIMITS
from scripts.check_clock_transfer_claim import DOC,SOURCE,INVENTORY,PRIOR,DEPENDENCIES,source_record

REPORT='reports/clock-transfer-claim-v1.json';REVIEW='data/einstein-clock-transfer-u0126-review-v1.json'
CLAUSES=(
 ('Hieraus ergibt sich folgende eigentümliche Konsequenz. ',['ejkp','eisoi','ejkt','ejku'],'前の単位秒の遅れと近似ejjvを指し、次の同じ条件付き結果ejkmを特有の帰結として予告する。評価から真理を導かない。'),
 ('Sind in den Punkten [M0219] und [M0220] von [M0221] ruhende, ',['ejke','ejkf','ejkj'],'異なるA/BでKに静止する二時計を、全初期区間の代表位置と現在表示へ結ぶ。条件の設定であり、実際の実験済みを主張しない。'),
 ('im ruhenden System betrachtet, synchron gehende Uhren vorhanden, ',['ejkb','ejkf','ejkj'],'Kの同じ時刻で全初期区間に同じ指示を持つ二時計の同期。共通の指示原点を許し、一回の偶然の一致へ縮めない。'),
 ('und bewegt man die Uhr in [M0222] mit der Geschwindigkeit [M0223] auf der Verbindungslinie nach [M0224], ',['ejkd','swo','swp','ejkf','ejkj'],'Aの同じ時計を速さvでBへ直線等速移送する条件。三次元方向、全時刻と全現在候補、正の所要時間を保持し、端点だけで経路を済ませない。'),
 ('so gehen nach Ankunft dieser Uhr in [M0225] die beiden Uhren nicht mehr synchron, ',['ejj7','ejkk','ejkm','ejkq'],'全初期区間で同期した同じ二時計が、到着直後の同じB・出来事で等しくない指示を持つ。否定を移送条件の外に出さず、未指定の永続期間を補わない。'),
 ('sondern die von [M0226] nach [M0227] bewegte Uhr geht gegenüber der von Anfang an in [M0228] befindlichen ',['ejke','ejkf','ejkl','ejkr','ejks'],'移送した時計と初めからBに残る時計を交換せず、非同期という第一項に対して遅れの向きと量を第二項にする。両項は同じ前件を保つ。'),
 ('um [M0229] Sek. (bis auf Größen vierter und höherer Ordnung) nach, ',['swv','swk','swy','sww','ejkl'],'同じ到着指示差を正の共通尺度で秒に換算し、同じK所要時間と速度比の二乗の半分へ結ぶ。前段の厳密率を残差の構成基準とする明示した読みで四次以上の留保を保持する。'),
 ('wenn [M0230] die Zeit ist, welche die Uhr von [M0231] nach [M0232] braucht.',['ejki','eisok','ejks','ejkv','ejkw'],'tを同じ時計のAからBへの所要時間として説明し、共通換算後の秒数を指す規則へ結ぶ。絶対座標時刻や時計の指示経過へ替えず、第二文を閉じる。'),
)
REASONS=(
 '固定u0126の二文、424非空白本文文字と14数式要素を原刊904頁で通読した。前段の一秒の遅れからHieraus、folgende/eigentümliche、初期同期と直線移送、到着直後の比較、½tv²/V²秒と四次以上の留保、末尾の所要時間tを照合した。',
 '初期同期と移送設定ejkfを前件に保ち、同じ到着出来事・場所の局所表示から非同期ejkkと正方向の遅れejklを結ぶ。Tの秒換算と実際の到着指示差、二次表示と残差を共有し、全初期・移送区間の表示存在、全候補、代表軌跡を前段から継承した。',
 '同じ移送時計zie、B時計zip、A/B、出発・初期B読み・到着の三出来事、三つの現在K記録、四指示、二状況を保持する。tは同じ移送のK時間差を秒へ換算するejkiとeisokに結び、前の座標時刻tやτ、別の時計、遠隔の受信時刻へ替えない。',
 '第一文は前のejjvから後続の条件付きejkmへの帰結予告と特異性評価である。第二文は原文の設定を前件とする結果を著者へ帰属し、非同期と遅れの対照も同じ前件を保つ。所要時間の説明を閉じた規則への記号解釈に接続する。',
 '到着直後の同所比較、共通の初期表示原点、正の単一直線移送、固定所要時間についてのBig-Oという読みを明示する。前段の厳密な遅れ率を残差の構成基準として用いる補足の区間法則はejkoにより発話外へ置き、著者の原文前件を狭めない。加速応答の証明、未指定の無限未来、具体的な残差係数を補わない。',
 '現在表示と全期間の履歴、局所指示、秒と正の換算、正の平方根、実数の近似、帰結・対照・記号解釈を既存定義から合成した。特異性の提示はKantで用いた一般的なh224rと同じ意味を今回の引用型に適用し、時計の物理法則を新しい基本記号へ隠さない。',
 '所要時間と絶対時刻の区別、二つの量の共通換算、到着時の同じ二時計と出来事・場所、非一致と遅れの方向、共通表示原点への不変性、厳密値と二次近似、固定Tの誤差関数、条件の真理表、引用の非実行、先行箇所の順序、発話外の補足を検査した。有限の検査から物理的真理や意味同値を自動認定しない。',
 '前段の単位秒の遅れと、後続する折れ線・帰還への拡張を含めて二文全体を再読した。明示した読みの下で、初期同期した二時計の一方を直線移送した到着時に、B時計に対して留保付きの量だけ遅れるという条件付きの関係と、その予告・評価・対比・量の説明を欠落なく保持したと判断する。',
)

@lru_cache(None)
def record():
    catalog=load_catalog(ROOT,BASIS);s=source_record()['segments'][0]
    paths={FULL,CORE,BASIS,ANNOTATIONS,SOURCE,REPORT,INVENTORY,DOC,PRIOR,*DEPENDENCIES,'scripts/review_clock_transfer_claim.py','tests/test_clock_transfer_claim_review.py'}
    pins={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)};merge_pins(pins,catalog.source_sha256)
    for p in (SOURCE,REPORT,*DEPENDENCIES):
        evidence=json.loads(read(p));validate_hashes(ROOT,evidence['source_sha256']);merge_pins(pins,evidence['source_sha256'])
    clauses=[];offset=0
    for text,symbols,reason in CLAUSES:
        assert s['text'][offset:offset+len(text)]==text and all(n in catalog.entries for n in symbols)
        clauses.append(dict(range=[offset,offset+len(text)],text=text,definitions=symbols,reason=reason));offset+=len(text)
    assert offset==len(s['text']) and len(REASONS)==len(REQUIREMENTS)
    return dict(schema_version='noema-semantic-review-1',work='einstein-1905',unit=s['unit'],reviewer='assistant_review',decision='equivalent_under_stated_reading',document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source=dict(inventory=INVENTORY,unit_sha256=s['unit_sha256'],text=s['text'],range=s['range'],math=[{k:m[k] for k in ('id','sha256')} for m in s['math']]),selection=selection_binding(catalog,list(INDICES)),source_order_statements=list(INDICES),clauses=clauses,interpretation=LIMITS,limits=['前段の厳密な遅れ率を近似残差の構成基準とし、全区間の指示法則を発話外の解釈注記に置くという明示した読みの下でのアシスタントの判断。独立査読、唯一の読解、加速応答の物理的導出、意味同値の自動証明ではない。','u0127以降と二作品全体の目標は未完。'],unresolved=[],requirements=[dict(id=k,decision='satisfied',reason=v) for k,v in zip(REQUIREMENTS,REASONS)],evidence=dict(source_reading=[SOURCE],formal_checks=[REPORT,*DEPENDENCIES],semantic_reading=[DOC]),reviewed_prose_characters=s['source_nonblank_characters'],source_sha256=pins)

def prepare():
    from scripts.audit_opening_scope import write_exact
    write_exact(ROOT/REVIEW,json.dumps(record(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    r=record();assert json.loads(read(REVIEW))==r
    active=dict(document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source_inventory=INVENTORY)
    validate_review(ROOT,REVIEW,'einstein-1905',active,load_catalog(ROOT,BASIS),json.loads(read(INVENTORY)))
    return dict(status='current_clock_transfer_conditional_consequence_whole_unit_reviewed',document=FULL,source_units={r['unit']:r['reviewed_prose_characters']},reviewed_math_elements=14,whole_units_semantically_verified=True,verified_full_units={'kant-1784':0,'einstein-1905':1},semantic_equivalence_automatically_proved=False,source_sha256=r['source_sha256']|{REVIEW:digest((ROOT/REVIEW).read_bytes())})
