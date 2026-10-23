"""Read the retrospective definition and common-reference event-time paragraph."""
from functools import lru_cache
import json
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import REQUIREMENTS,digest,selection_binding,validate_hashes,validate_review
from noema.review_registry import merge_pins
from scripts.compose_event_time_summary import ROOT,read,FULL,CORE,BASIS,ANNOTATIONS,INDEX,LIMITS

INVENTORY='artifacts/written-units-v1/einstein-1905.json';DOC='docs/event-time-summary-v1.md'
SOURCE='data/einstein-event-time-summary-source-reading-v1.json';READING='data/event-time-summary-reading-v1.json'
REPORT='reports/event-time-summary-v1.json';REVIEW='data/einstein-event-time-summary-review-v1.json'
PRIORS=('data/einstein-local-synchrony-paragraph-review-v1.json','data/einstein-consistent-synchrony-review-v1.json','data/einstein-synchrony-three-clock-review-v1.json')
REASONS=(
 '固定u0018全515文字・447非空白本文文字を原刊894頁のWir haben soからsynchron läuft.までへ照合した。第一文233文字、第二文214文字で、数式はない。括弧内gedachter、引用符付きgleichzeitigとZeit、全時刻決定で同じ時計という挿入句を含める。',
 '第一文は思考上の物理的経験を手段として先の同期規約を定めたことと、それによる同時性・時間の定義の獲得を保持する。第二文は出来事と同時の指示、同じ発生場所の静止時計、同じ特定の静止参照時計への同期をeingで結ぶ。',
 '先の同期定義eimp/eimk、考察素材の局所時計eik7と光往復eiml、同じ定義課題eisjfと時間規約eisjdを再利用する。全ての時刻付与でrcを固定し、各出来事の表示・時計・場所・値を取り違えない。rjは既存の時刻定義箇所を継承する。',
 'Wir haben soを著者による先行手続きの振り返りとして、damitをeinlからeinmへの理由として、offenbarを定義到達の明白さの帰属として保持する。Zeitの引用符は定義される概念を取り上げる働きであり、単なる字面の置換とはしない。二文の帰属と直前の第二法則からの順序も保持する。',
 '実際の実験実施、実験者の人数、全出来事の発生、任意の不整合な入力に対する読取りの存在・一意性を補わない。近傍の別時点に同じ値を示す表示、遠隔受信の指示、出来事ごとに別参照時計を選ぶ条件へ弱めない。同時性と時間の片方だけを定義したことにしない。',
 '物理的な経験内容、思考上の扱い、内容への対応、先行手続きの振り返りを独立した規約に分ける。時刻付与は既存quと局所的一致eisgm、同時性は二つの付与条件と数値等値scaで合成する。旧草案qwは現行本文に存在しないため、その読みを現在の依存定義で再構成する。',
 '原刊照合と通読判断を、表示出来事の存在結合・場所・値・時計の静止・固定参照の検査、qoを含む本体の数値例、理由の向き・明白さ・定義採用の引用の検査から区別する。未知入力と全実数の有限標本化は拒否する。有限検査を全物理状況や意味同値の自動証明としない。',
 '前の同期規約とその二法則を受け、思考上の物理的経験によって定義に到達したという第一文から、出来事と同時の局所指示を同じ参照時計に結ぶ第二文まで通読した。明示した関係的な時刻付与と同時性の読みの下で、内容・参照・範囲・提示の未処理項目はないと判断する。次の光速度を普遍定数と置く文は別単位として残る。',
)


def source_record():
    u=json.loads(read(INVENTORY))['units'][17];s=u['text'];assert len(s)==515 and not u['math_ids']
    assert s[:265].endswith('gewonnen.') and s[266:].startswith('Die „Zeit“') and s.endswith('synchron läuft.')
    paths=[INVENTORY,'artifacts/einstein-synchrony-continuation-v1/page-894.jpg','artifacts/einstein-synchrony-continuation-v1/page-894.html','artifacts/einstein-synchrony-continuation-v1/retrieval.json','scripts/review_event_time_summary.py']
    return dict(version='einstein-event-time-summary-source-reading-v1',reviewer='assistant_visual_and_text_review',pages=['894'],images=[paths[1]],segments=[dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[a,b],text=s[a:b],nonblank_characters=sum(not c.isspace() for c in s[a:b]),math=[]) for a,b in ((0,265),(266,515))],observations=['原刊894頁の二文を照合した。gedachterの括弧、物理的経験による手段、so/damit/offenbar、引用されたgleichzeitigとZeitを保持する。','第二文は出来事と同時の指示、その場所、静止時計、特定の静止参照時計と全時刻決定でその同じ時計を使う条件を含む。続くWir setzen nochからの光速度の定数設定は対象外。'],semantic_completion=False,source_sha256={p:digest((ROOT/p).read_bytes()) for p in paths})


def build_reading():
    paths=[INVENTORY,DOC,SOURCE,*PRIORS,'scripts/review_event_time_summary.py']
    return dict(schema_version='noema-connected-reading-1',status='retrospective_definition_and_event_time_rule_checked_under_explicit_reading',reviewer='assistant_close_reading',document=FULL,meaning_basis=BASIS,segments=source_record()['segments'],source_nonblank_characters=447,selection=selection_binding(load_catalog(ROOT,BASIS),[INDEX,INDEX+1]),requirements=[dict(requirement=k,judgment='preserved_under_stated_reading',reason=v) for k,v in zip(REQUIREMENTS,REASONS)],interpretation_limits=LIMITS,verified_full_units=0,semantic_equivalence_automatically_proved=False,remaining=['全単位判断の登録、u0019以降の光速度の定数設定'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in paths})


@lru_cache(None)
def review_record():
    catalog=load_catalog(ROOT,BASIS);u=json.loads(read(INVENTORY))['units'][17]
    paths={FULL,CORE,BASIS,ANNOTATIONS,INVENTORY,DOC,SOURCE,READING,REPORT,*PRIORS,'scripts/review_event_time_summary.py','tests/test_event_time_summary_review.py'}
    pins={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)};merge_pins(pins,catalog.source_sha256)
    for p in (SOURCE,READING,REPORT,*PRIORS):
        r=json.loads(read(p));validate_hashes(ROOT,r['source_sha256']);merge_pins(pins,r['source_sha256'])
    return dict(schema_version='noema-semantic-review-1',work='einstein-1905',unit=u['id'],reviewer='assistant_review',decision='equivalent_under_stated_reading',document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source=dict(inventory=INVENTORY,unit_sha256=u['text_sha256'],text=u['text'],range=[0,len(u['text'])],math=[]),selection=selection_binding(catalog,[INDEX,INDEX+1]),source_order_statements=[INDEX,INDEX+1],interpretation=LIMITS[:-1],limits=['明示した解釈に基づくアシスタントの通読判断。独立査読・唯一の歴史的解釈・同義性の自動証明・物理的実現の証明ではない。','u0019以降と二作品全体の記述は未完。'],unresolved=[],requirements=[dict(id=k,decision='satisfied',reason=v) for k,v in zip(REQUIREMENTS,REASONS)],evidence=dict(source_reading=[SOURCE],formal_checks=[REPORT],semantic_reading=[DOC]),source_sha256=pins)


def prepare():
    from scripts.audit_opening_scope import write_exact
    write_exact(ROOT/REVIEW,json.dumps(review_record(),ensure_ascii=False,indent=2)+'\n')


def build_report():
    r=review_record();assert json.loads(read(REVIEW))==r
    active=dict(document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source_inventory=INVENTORY)
    result=validate_review(ROOT,REVIEW,'einstein-1905',active,load_catalog(ROOT,BASIS),json.loads(read(INVENTORY)))
    assert result['source_nonblank_characters']==447
    return dict(status='event_time_summary_whole_unit_reviewed',document=FULL,source_units={'einstein-1905:u0018':447},whole_units_semantically_verified=True,verified_full_units={'kant-1784':0,'einstein-1905':1},semantic_equivalence_automatically_proved=False,source_sha256=r['source_sha256']|{REVIEW:digest((ROOT/REVIEW).read_bytes())})
