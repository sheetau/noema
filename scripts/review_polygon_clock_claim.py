"""Review the whole polygon extension and its explicit return case."""
from functools import lru_cache
import json
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import REQUIREMENTS,digest,selection_binding,validate_hashes,validate_review
from noema.review_registry import merge_pins
from scripts.compose_polygon_clock_claim import ROOT,read,FULL,CORE,BASIS,ANNOTATIONS,INDICES,LIMITS
from scripts.check_polygon_clock_claim import DOC,SOURCE,INVENTORY,PRIOR,DEPENDENCIES,source_record

REPORT='reports/polygon-clock-claim-v1.json';REVIEW='data/einstein-polygon-clock-u0127-review-v1.json'
CLAUSES=(
 ('Man sieht sofort, ',['ejlg','zdg'],'前段の結果の拡張が直ちに認められるという著者の明白さの提示を、同じ一般内容ejlcへ帰属する。読者全員の認知や処理系の証明認定へ替えない。'),
 ('daß dies Resultat auch dann noch gilt, ',['ejkm','ejlc','ejlg'],'dies Resultatを前段の現在の条件付き到着結果ejkmへ結び、次の折れ線でも同じ結果が成立すると拡張する。非同期、遅れの向きと全所要時間の量、秒換算、二次近似と留保を保つ。'),
 ('wenn die Uhr in einer beliebigen polygonalen Linie sich von [M0233] nach [M0234] bewegt, ',['ejkx','ejky','ejkz','ejk2','ejk3','ejla','ejlc'],'同じ時計が共通速さで任意の有限折れ線をAからBへ進む条件。全区間を同じ出来事・記録・指示・場所関数で接続し、各全時刻の現在表示と代表経路、初期同期と参照時計の残留、到着比較を共有する。'),
 ('und zwar auch dann, ',['ejlh','ejld','ejlk','ejll'],'一般主張に続いて特に次の場合も成立すると明示する。帰還を一般主張の前件へ混ぜず、同じ到着結果を保つ別の条件付き内容へ接続する。'),
 ('wenn die Punkte [M0235] und [M0236] zusammenfallen.',['ejlb','sxo','ejk2','ejld'],'AとBは同じ場所と三座標位置である。正の全所要時間を隔てる出発と帰着の出来事は異なり、初期には二時計が同じ出来事を共有できる。'),
)
REASONS=(
 '固定u0127の全一文、155非空白本文文字と四つのA/B表示を原刊904頁で照合した。Man sieht sofort、dies Resultat、auch dann noch、beliebigen polygonalen Linie、und zwar auch dann、端点の一致を前後の文脈を含めて読んだ。',
 '任意の非空有限区間列を同じ時計・速さ・記録と指示の関数で接続し、各区間の全実時刻と全現在候補を保持する。初期同期と参照時計の残留、同じ到着での二指示、全所要時間の差と望遠和、遅れの向き・共通秒換算・二次近似と固定Tの四次以上の留保を結んだ。',
 'dies Resultatは現在の前段結果ejkmであり、旧稿の部分的な前件付き数値式に戻さない。経路全体で同じ時計と速度を用い、折れ点は同じ出来事・指示・記録を共有する。A/Bの再訪を出来事の同一性へ替えず、所要時間を一区間の時間や絶対時刻へ替えない。',
 '一般拡張と明白さをejlg、帰還の場合の明示をejlhにより同じ著者の二つの順序付き発話として表す。任意量化を持つ条件付き内容を引用し、著者への帰属を計算器による真理認定や単なる関数定義で済ませない。',
 '共通の正の速さを前段から継承し、零長の重複頂点は表記の冗長として除く有限折れ線という読みを明示した。自己交差や場所の再訪は除外しない。方向転換時などに追加指示変化がないという区間法則はejle/ejlfの発話外の解釈注記に置き、原文の前件ejk3を狭めない。連続曲線への仮定は次の単位へ残す。',
 '既存の全出現の畳み込み・同じ出来事の接続・数値率・現在表示・代表経路・初期静止・全期間指示・近似誤差・帰属関係を合成した。和の三定義を旧稿から意味とともにそのまま再利用し、原始記号を追加せず任意の折れ線と帰還を記述した。',
 '区間と同じ折れ点の引数、全候補と全時刻の範囲、帰還の初期出来事共有、順序と重複区間、指示リセットと望遠和の区別、全所要時間の秒換算・厳密差・近似残差、任意量化と条件の作用範囲、前段参照・明白さ・発話外注記を対照検査する。下位の全実数条件と旧数値核の根拠は固定した依存報告を保持し、有限検査を意味判断の自動根拠にしない。',
 '一文全体を前段の直線移送結果と後段の連続曲線への仮定の間で再読した。明示した読みの下で、前段の結果が同じ時計の任意の折れ線移送にも成立し、出発地点に帰還する場合も含むという内容と、その直ちに認められる拡張としての提示を欠落なく保持したと判断する。',
)

@lru_cache(None)
def record():
    catalog=load_catalog(ROOT,BASIS);s=source_record()['segments'][0]
    paths={FULL,CORE,BASIS,ANNOTATIONS,SOURCE,REPORT,INVENTORY,DOC,PRIOR,*DEPENDENCIES,'scripts/review_polygon_clock_claim.py','tests/test_polygon_clock_claim_review.py'}
    pins={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)};merge_pins(pins,catalog.source_sha256)
    for p in (SOURCE,REPORT,*DEPENDENCIES):
        evidence=json.loads(read(p));validate_hashes(ROOT,evidence['source_sha256']);merge_pins(pins,evidence['source_sha256'])
    clauses=[];offset=0
    for text,symbols,reason in CLAUSES:
        assert s['text'][offset:offset+len(text)]==text and all(n in catalog.entries for n in symbols)
        clauses.append(dict(range=[offset,offset+len(text)],text=text,definitions=symbols,reason=reason));offset+=len(text)
    assert offset==len(s['text']) and len(REASONS)==len(REQUIREMENTS)
    return dict(schema_version='noema-semantic-review-1',work='einstein-1905',unit=s['unit'],reviewer='assistant_review',decision='equivalent_under_stated_reading',document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source=dict(inventory=INVENTORY,unit_sha256=s['unit_sha256'],text=s['text'],range=s['range'],math=[{k:m[k] for k in ('id','sha256')} for m in s['math']]),selection=selection_binding(catalog,list(INDICES)),source_order_statements=list(INDICES),clauses=clauses,interpretation=LIMITS,limits=['共通速さの有限折れ線として読み、角などでの追加指示変化を無視する法則を発話外の解釈注記に置くという読みの下でのアシスタントの意味判断。独立査読、唯一の読解、全経路の物理的導出、意味同値の自動証明ではない。','u0128以降と二作品全体の目標は未完。'],unresolved=[],requirements=[dict(id=k,decision='satisfied',reason=v) for k,v in zip(REQUIREMENTS,REASONS)],evidence=dict(source_reading=[SOURCE],formal_checks=[REPORT,*DEPENDENCIES],semantic_reading=[DOC]),reviewed_prose_characters=s['source_nonblank_characters'],source_sha256=pins)

def prepare():
    from scripts.audit_opening_scope import write_exact
    write_exact(ROOT/REVIEW,json.dumps(record(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    r=record();assert json.loads(read(REVIEW))==r
    active=dict(document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source_inventory=INVENTORY)
    validate_review(ROOT,REVIEW,'einstein-1905',active,load_catalog(ROOT,BASIS),json.loads(read(INVENTORY)))
    return dict(status='current_polygon_extension_and_return_whole_unit_reviewed',document=FULL,source_units={r['unit']:r['reviewed_prose_characters']},reviewed_math_elements=4,whole_units_semantically_verified=True,verified_full_units={'kant-1784':0,'einstein-1905':1},semantic_equivalence_automatically_proved=False,source_sha256=r['source_sha256']|{REVIEW:digest((ROOT/REVIEW).read_bytes())})
