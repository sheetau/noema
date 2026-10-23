"""Review the whole assumed curve extension and its Earth-clock consequence."""
from functools import lru_cache
import json
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import REQUIREMENTS,digest,selection_binding,validate_hashes,validate_review
from noema.review_registry import merge_pins
from scripts.compose_curve_earth_claim import ROOT,read,FULL,CORE,BASIS,ANNOTATIONS,INDICES,LIMITS
from scripts.check_curve_earth_claim import DOC,SOURCE,INVENTORY,PRIOR,DEPENDENCIES,source_record

REPORT='reports/curve-earth-claim-v1.json';REVIEW='data/einstein-curve-earth-u0128-review-v1.json'
CLAUSES=(
 ('Nimmt man an, ',['ejmi','ejmm','ejmn'],'同じ推論範囲で拡張を仮定として採用する発話を、先行する折れ線帰還の後へ置く。拡張の無条件な証明とはしない。'),
 ('daß das für eine polygonale Linie bewiesene Resultat ',['ejlc','ejlx','ejmi'],'前段の現在表示を用いる折れ線結果ejlcを参照し、その箇所zjbを著者が証明済みとして扱う。処理系による証明認定ではない。'),
 ('auch für eine stetig gekrümmte Kurve gelte, ',['ejlp','ejlv','ejlx'],'同じ結果がC1の位置と連続速度を持つ経路にも成立するという拡張内容。全実時刻の幾何と現在表示、一定の正の光速未満の速さを保持する読みである。'),
 ('so erhält man den Satz: ',['ejly','ejmj','ejmo','ejmp'],'前段結果と拡張仮定から、同じ範囲で後続の閉曲線帰還結果を得るという著者の帰結提示。モデルの全期間法則の補足ejmlは発話外に置く。'),
 ('Befinden sich in [M0237] zwei synchron gehende Uhren ',['ejk2','ejlq','ejlr','ejlw'],'同じ場所Aの異なる二時計を、共通K尺度での初期の同期した進行と現在表示へ結ぶ。帰還の条件を含む同じ一般的な条件付き内容を使う。'),
 ('und bewegt man die eine derselben auf einer geschlossenen Kurve mit konstanter Geschwindigkeit, ',['ejlp','ejlq','ejlr','ejlw'],'一方の同じ時計が閉曲線を一定の速さで進む。速度ベクトルを一定にして曲がれなくする読みではない。経路の全時刻と同じ時計・出来事・記録・指示・場所を結ぶ。'),
 ('bis sie wieder nach [M0238] zurückkommt, ',['ejlr','ejk2'],'正の経過時間の後に同じAと三座標位置へ戻る。出発と帰着は異なる出来事であり、同じ場所を同じ時刻へ同定しない。参照時計はその場所に残る。'),
 ('was [M0239] Sek. dauern möge, ',['ejlt','ejmj','eisom','eison'],'同じ経路の終始時刻差を共通尺度から秒へ換算するejltに、所要時間の表記tを型付きで結ぶ。絶対時刻や指示の原点ではない。mögeは所要時間の記号的な指定として読む。'),
 ('so geht die letztere Uhr bei ihrer Ankunft in [M0240] gegenüber der unbewegt gebliebenen um [M0241] Sek. nach. ',['ejls','ejla','ejk7','swy','ejlw','ejmj'],'同じ帰着出来事・場所の二時計の現在表示を比較し、移動時計が遅れる向きと全所要時間の½t(v/V)²秒を保つ。前段から二次近似と固定所要時間での四次以上の留保を継承する。'),
 ('Man schließt daraus, ',['ejmk','ejmq','ejmr'],'同じ閉曲線の帰還結果ejlwから、後続の地球比較ejmgを帰結として述べ、発話順序も保つ。推論の帰属と実世界での十分な導出を区別する。'),
 ('daß eine am Erdäquator befindliche Unruhuhr ',['syi','syk','ejmc','ejmd'],'地球の赤道の場所に固定され、復元弾性を持つ回転振動系の反復を調速に使う時計。機械的部分、振動作用、調速機能を合成し、名称だけで時計の種類を済ませない。'),
 ('um einen sehr kleinen Betrag langsamer laufen muß ',['ejlz','ejma','ejmb','ejme','ejmf','ejmg'],'同じK期間内の任意の正の時間幅で、実際の指示差から得る正の平均歩度が小さく、その差が文脈上非常に小さいという読み。mußは基準設定自身を含む非空の物理的候補全てでの必要性とする。'),
 ('als eine genau gleich beschaffene, ',['ejmc','cd'],'比較対象の時計は同じ構造・性状を持つ。進み率の同一性や同じ指示値を、この構造の一致へ混ぜない。'),
 ('sonst gleichen Bedingungen unterworfene, ',['syj','ejmc'],'運動と地理的位置を除くその他の比較条件の範囲が完全かつ非空であり、その全条件の成立・不成立が二時計で一致する。'),
 ('an einem Erdpole befindliche Uhr.',['syl','ejmc','ejmd','ejmg'],'同じ地球の一方の極に固定された第二時計で、北極・南極を限定しない。離れた時計を同じ出来事にせず、別の指示原点を許す。一様回転する地球という背景を許容状況の明示した制約に置く。'),
)
REASONS=(
 '固定u0128の全二文690原文文字、552非空白本文文字と五数式要素を原刊904–905頁で再読した。改頁で分かれたun-bewegtと½t(v/V)²秒を同じ帰還文へ戻し、A0018は頁境界として扱う。機械時計の用語は製造者の調速器・ばねの説明とも照合した。',
 '前段の証明済みという位置付け、曲線への拡張仮定、その下での帰結、初期同期、閉曲線と一定の速さ、同所帰還、所要時間、到着遅れ、地球の機構と同構造/その他同条件/赤道と極/小さな歩度差/必要性を列挙した。各節の連続した範囲を同じNoema本文の定義へ対応させた。',
 '前段結果は現行ejlc、拡張はejlx、帰還結果はejlwである。同じ経路の現在記録と指示・始終出来事・場所・時刻差・秒尺度を共有する。tは同じ経路のejltへ結び、地球の比較では別々の現在表示を共通K時間幅へ結ぶ。残した時計、移動時計、赤道時計、極時計を取り違えない。',
 '仮定採用と著者の証明済みという位置付け、同じ範囲の帰結、そこからの地球時計の推論を三つの順序付きメッセージへ帰属した。引用内容は条件と全称量化を保持する。mußは結果から候補を選ばない非空の物理的候補範囲に対する全称で、規範的義務や有限評価器の真理認定へ替えない。',
 'C1幾何、正の光速未満の共通速さ、理想時計の全期間法則、前段からの近似留保、一様回転地球、任意の正の比較幅にわたる歩度差という読みを明示した。全期間法則の補足は著者の発話と前件から分離する。地球時計に初期同期、同じ指示原点、同所帰還を要求せず、小ささの数値閾値も補わない。',
 '回転振動の機構を既存の部分・復元弾性の振動・調速の三関係で合成し、同構造とその他全条件の一致を分けた。赤道/両極は表面と軸座標から定め、平均歩度は現在表示の差と時間幅から構成した。新規基本関係は物理的推論の候補範囲と型付き表記対応で、残る新規記号はtの識別子である。語形や一文全体を真偽のオラクルにしない。',
 '機構の三証人、完全な条件範囲、地理座標、全候補/全実時刻の表示、独立した指示原点、正の区間と歩度、差の向きと程度基準、様相候補の非空性/基準包含/全称、発話の参照・順序・tの型を局所対照検査した。全実数と関数の量化を残し、有限実行拒否も確認する。旧判断と意味規約の一致を検証し、原文の判断はこれらの検査と分ける。',
 '前後の折れ線結果と第5節への境界を含めて二文全体を再読した。明示した解釈の下で、曲線への仮定と閉曲線帰還の結論、およびそこから同構造・その他同条件の赤道時計が極時計よりごく僅かに遅く進まなければならないという推論の内容・提示・範囲を欠落なく保持したと判断する。',
)

@lru_cache(None)
def record():
    catalog=load_catalog(ROOT,BASIS);s=source_record()['segments'][0]
    paths={FULL,CORE,BASIS,ANNOTATIONS,SOURCE,REPORT,INVENTORY,DOC,PRIOR,*DEPENDENCIES,'scripts/review_curve_earth_claim.py','tests/test_curve_earth_claim_review.py'}
    pins={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)};merge_pins(pins,catalog.source_sha256)
    for p in (SOURCE,REPORT,*DEPENDENCIES):
        evidence=json.loads(read(p));validate_hashes(ROOT,evidence['source_sha256']);merge_pins(pins,evidence['source_sha256'])
    clauses=[];offset=0
    for text,symbols,reason in CLAUSES:
        assert s['text'][offset:offset+len(text)]==text and all(n in catalog.entries for n in symbols)
        clauses.append(dict(range=[offset,offset+len(text)],text=text,definitions=symbols,reason=reason));offset+=len(text)
    assert offset==len(s['text']) and len(REASONS)==len(REQUIREMENTS)
    return dict(schema_version='noema-semantic-review-1',work='einstein-1905',unit=s['unit'],reviewer='assistant_review',decision='equivalent_under_stated_reading',document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source=dict(inventory=INVENTORY,unit_sha256=s['unit_sha256'],text=s['text'],range=s['range'],math=[{k:m[k] for k in ('id','sha256')} for m in s['math']]),selection=selection_binding(catalog,list(INDICES)),source_order_statements=list(INDICES),clauses=clauses,interpretation=LIMITS,limits=['C1経路と理想時計の指示法則、同じK時間幅での平均歩度、一様回転地球という背景、物理的な候補範囲という読みの下でのアシスタントの意味判断。独立査読、唯一の読解、加速応答や実際の地球の物理的導出、意味同値の自動証明ではない。','u0129以降と二作品全体の目標は未完。'],unresolved=[],requirements=[dict(id=k,decision='satisfied',reason=v) for k,v in zip(REQUIREMENTS,REASONS)],evidence=dict(source_reading=[SOURCE],formal_checks=[REPORT,*DEPENDENCIES],semantic_reading=[DOC]),reviewed_prose_characters=s['source_nonblank_characters'],source_sha256=pins)

def prepare():
    from scripts.audit_opening_scope import write_exact
    write_exact(ROOT/REVIEW,json.dumps(record(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    r=record();assert json.loads(read(REVIEW))==r
    active=dict(document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source_inventory=INVENTORY)
    validate_review(ROOT,REVIEW,'einstein-1905',active,load_catalog(ROOT,BASIS),json.loads(read(INVENTORY)))
    return dict(status='assumed_curve_extension_and_earth_clock_whole_unit_reviewed',document=FULL,source_units={r['unit']:r['reviewed_prose_characters']},reviewed_math_elements=5,whole_units_semantically_verified=True,verified_full_units={'kant-1784':0,'einstein-1905':1},semantic_equivalence_automatically_proved=False,source_sha256=r['source_sha256']|{REVIEW:digest((ROOT/REVIEW).read_bytes())})
