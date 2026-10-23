"""Record a holistic reading of both sentences of Einstein u0045."""
from functools import lru_cache
import json
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import REQUIREMENTS,digest,selection_binding,validate_hashes,validate_review
from noema.review_registry import merge_pins
from scripts.compose_clock_site_time import ROOT,read,FULL,CORE,BASIS,ANNOTATIONS,LIMITS
from scripts.check_clock_site_time import DOC,SOURCE,INVENTORY,FIRST,DEPENDENCIES,source_record

REPORT='reports/clock-site-time-v1.json';REVIEW='data/einstein-clock-site-time-review-v1.json'
CLAUSES=(
 ('Es werde ferner ',['eiyr','eiys','eiyt'],'先行空間測定への追加採用と指示の力、同じ著者への帰属を保持する。'),
 ('mittels der im ruhenden System befindlichen ruhenden Uhren ',['eiye','eiyf','eiyg'],'同じ静止系に置かれた初期と同じ時計の校正、自系の静止、実際の局所表示を結ぶ。'),
 ('durch Lichtsignale in der in § 1 angegebenen Weise ',['qo','qn','sad','db','eiyn','eiyq'],'§1の光往復全試行の手順と参照先を保持し、一回の成功や別の同期方式へ替えない。'),
 ('die Zeit [M0079] des ruhenden Systems ',['eiwt','eiyj','eiyq'],'既出tの静止系の規則を維持し、出来事の局所時刻と系内の生起時点の値を明示的に結ぶ。'),
 ('für alle Punkte des letzteren bestimmt, in denen sich Uhren befinden; ',['sgg','sgi','eiyh','eiyi','eiyk'],'時計のある全地点の全対象出来事へ同じ場所の時刻を付与する。時計のない地点に時計や値を補わない。'),
 ('ebenso werde die Zeit [M0080] des bewegten Systems ',['eiym','eiyp','eiyr','eiys'],'同じ手順による移動系の時刻設定も指示し、τを同じ移動系の時点規則へ結ぶ。tとτの一致は加えない。'),
 ('für alle Punkte des bewegten Systems, in welchen sich relativ zu letzterem ruhende Uhren befinden, ',['eiye','eiyf','eiyk'],'移動系に相対的に静止する同じ時計がある全地点を対象とし、静止基準Kでの静止や内部停止へ替えない。'),
 ('bestimmt durch Anwendung der in § 1 genannten Methode der Lichtsignale zwischen den Punkten, in denen sich die letzteren Uhren befinden.',['eiyo','eiyq','eiyf','qo','db','eiyg'],'第二の§1参照を保持し、同じ時計所在地点間の光往復・局所読みで時刻を付与する。別地点の時計や遠隔信号の受信時刻を対象の局所時刻に混ぜない。'),
)
REASONS=(
 '固定原文u0045の全761文字・602本文文字とM0075〜M0080を対象とする。第一文の保存済み原刊照合に加え、898頁の第二文を画像で再照合した。範囲[0,240)と[241,761)の間は空白一文字であり、内容の欠落はない。',
 '同じ二系の全空間の三座標測定、同じ物差しと時計、時計所在地の全出来事の時刻付与、全光往復試行、局所表示、存在・一意性、六座標と二時刻の対応を合成した。第二文の追加指示と二つの第一節参照も保持した。',
 'K/k・原点・三軸・物差し・全配備時計と移動後設定は先行段落と同じ対象を保つ。第一文は修正版eiydのまま、K/kの命名は先行zcgに置く。tの既存eiwtを変更せず、出来事と時点の対応eisnkを経て同じ局所時刻へ結ぶ。τはzbmの規則へ固定する。',
 '第一文は測定済みの配置を今想定するという著者の行為を述べる。第二文はそこへ時刻設定をさらに追加する指示である。両者を実験完了の事実報告、単なる可能性、引用内容の物理的実現の証明へ替えない。',
 '全空間への時計設置、時計内部の停止、初期の未指定参照時計との同一性、加速機構、両系の座標値・時刻値・同時性の一致を補わない。出来事範囲を成功例へ狭めず、一回の光試行で同期を認定しない。§1の整合的な時計網として全配備時計対の同期を要求する読みを明記する。',
 '物差しによる有向距離と全空間への取得、校正された時計の代表配置履歴・同所表示、光往復同期は既存定義へ展開される。出来事と系内時点の対応は意味を明示した一般関係として採り、値の一致と存在を別に合成する。τの新しい呼称は規則の引用と結び、文字だけで意味を済ませない。',
 '原刊画像・固定原文、第一文の修正済み判断、局所時刻・時計校正の既存検査、今回の全配備・全試行・全時計所在地・引数接続・引用非実行の対照検査を保存した。有限例は全実数の検査や物理的真理・同義性の自動証明ではない。',
 '二文を先行u0044の同じ運動設定と後続u0046の座標時刻対応に照らして通読した。第一文の測定済み想定を受け、第二文で両系の時計所在地へ§1の手順で時刻を付与するという明示した読みの下で、対象・量化・方法・表記・指示を欠落なく記述したと判断する。第一文176文字は602文字に含み、別加算しない。',
)

@lru_cache(None)
def record():
    source=source_record();catalog=load_catalog(ROOT,BASIS);first=json.loads(read(FIRST))
    validate_hashes(ROOT,first['source_sha256']);assert selection_binding(catalog,[270])==first['selection']
    clauses=list(first['clauses']);offset=241
    for text,symbols,reason in CLAUSES:
        assert source['text'][offset:offset+len(text)]==text
        assert all(n in catalog.entries for n in symbols)
        clauses.append(dict(range=[offset,offset+len(text)],text=text,definitions=symbols,reason=reason));offset+=len(text)
    assert offset==761
    paths={FULL,CORE,BASIS,ANNOTATIONS,SOURCE,REPORT,INVENTORY,DOC,FIRST,*DEPENDENCIES,'scripts/review_clock_site_time.py','tests/test_clock_site_time_review.py'}
    pins={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)};merge_pins(pins,catalog.source_sha256)
    for p in (SOURCE,REPORT,*DEPENDENCIES):
        evidence=json.loads(read(p));validate_hashes(ROOT,evidence['source_sha256']);merge_pins(pins,evidence['source_sha256'])
    interpretation=[
     '第一文の既存判断v2を同じ選択で保持する。Wir denken unsは同じ空間を測定済み・六座標を取得済みの配置として想定し採用するという著者の行為である。',
     '同じK/kと物差しを維持し、Kのx,y,zとkのξ,η,ζをそれぞれの三軸役割へ結ぶ。各測定配置で対象・軸・尺度を保ち、全空間の各地点について同じ実測の存在と全有効候補の一意性へ座標値を結ぶ。',
     '移動系の物差しはKに対する既出の運動に同伴し、自系では静止する。両系の原点一致・正方向一致・座標値一致を追加しない。K/kの名称は先行zcgでの命名を再使用する。',
    ]+LIMITS
    return dict(schema_version='noema-semantic-review-1',work='einstein-1905',unit=source['unit'],reviewer='assistant_review',decision='equivalent_under_stated_reading',document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source=dict(inventory=INVENTORY,unit_sha256=source['unit_sha256'],text=source['text'],range=source['range'],math=[{k:m[k] for k in ('id','sha256')} for m in source['math']]),selection=selection_binding(catalog,[270,271]),source_order_statements=[270,271],clauses=clauses,interpretation=interpretation,limits=['明示した解釈の下でのアシスタントの通読判断。独立査読、物理的実現や同義性の自動証明ではない。','u0046以降と二作品全体の目標は未完。'],unresolved=[],requirements=[dict(id=k,decision='satisfied',reason=v) for k,v in zip(REQUIREMENTS,REASONS)],evidence=dict(source_reading=[SOURCE],formal_checks=[REPORT,*DEPENDENCIES],semantic_reading=[DOC,FIRST]),incorporates_sentence_review=FIRST,reviewed_prose_characters=602,additional_sentence_characters_counted_separately=0,source_sha256=pins)

def prepare():
    from scripts.audit_opening_scope import write_exact
    write_exact(ROOT/REVIEW,json.dumps(record(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    rec=record();assert json.loads(read(REVIEW))==rec
    active=dict(document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source_inventory=INVENTORY)
    validate_review(ROOT,REVIEW,'einstein-1905',active,load_catalog(ROOT,BASIS),json.loads(read(INVENTORY)))
    return dict(status='two_frame_space_and_clock_time_whole_unit_reviewed',document=FULL,source_units={'einstein-1905:u0045':602},whole_units_semantically_verified=True,verified_full_units={'kant-1784':0,'einstein-1905':1},incorporated_sentence_characters_not_added_again=176,semantic_equivalence_automatically_proved=False,source_sha256=rec['source_sha256']|{REVIEW:digest((ROOT/REVIEW).read_bytes())})
