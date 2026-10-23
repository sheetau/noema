"""Read the rest-system time naming across the original page boundary."""
from functools import lru_cache
import json
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import REQUIREMENTS,digest,selection_binding,validate_hashes,validate_review
from noema.review_registry import merge_pins
from scripts.compose_rest_system_time import ROOT,read,FULL,CORE,BASIS,ANNOTATIONS,INDEX,LIMITS

INVENTORY='artifacts/written-units-v1/einstein-1905.json';DOC='docs/rest-system-time-v1.md'
SOURCE='data/einstein-rest-system-time-source-reading-v1.json';READING='data/rest-system-time-reading-v1.json'
REPORT='reports/rest-system-time-v1.json';REVIEW='data/einstein-rest-system-time-review-v1.json'
PRIORS=('data/einstein-event-time-summary-review-v1.json','data/einstein-empirical-light-constant-u0021-review-v1.json')
REASONS=(
 '固定u0022全207文字・177非空白本文文字を原刊894頁末のWesentlich istから895頁冒頭の呼称末尾まで照合した。セミコロンの両側と引用形die Zeit des ruhenden Systemsを含める。A0006は空の改頁標識であり、本文の命題を加えない。',
 '前半は同じ静止系に静止する時計で時間を定義したというein2と、その条件の重要性eiskvを保持する。後半は同じ時間規約を指す命名ein3と、系への所属einzを理由とする向きを保持する。',
 'die eben definierte Zeitを、先に共通時間として導入し直前のrjでeingにより定義した同じ規約eisjdへ結ぶ。局所時計と参照時計rcは同じra・rbを使い、新しい呼称eisksが別の対象を指さない。',
 'Wesentlichを定義理解の重要性、definiert habenとebenを直前の定義を受ける振り返り、wir nennenを著者の現在の命名宣言として保持する。wegenは同じ系への所属から命名への理由であり、名称から物理的性質を作る逆の説明ではない。',
 '絶対静止、全系共通の時間、局所A時間だけ、別規約の再定義、他者の実際の名称使用を足さない。重要性を論理的必然性や自明性へ替えず、時計の静止・所在を名称だけで代用しない。',
 '時計条件は既存eing/qu/qt/saf/saeの連言から構成したeinx/einyで保持する。規約と規則の対応eisku、重要性eiskv、引用形の識別表記を分け、命名そのものは既存eisd4を再利用する。',
 '原刊二頁の照合と通読を、時刻付与から時計条件への定義展開・連言除去、固定系と別系の有限例、規約・名称・理由・重要性・順序の結合検査から区別する。全実数表現への含意は有限標本の成功から推論せず、一般評価の有限標本化は拒否する。',
 '先の時刻定義と速度定数の採用に続き、同じ系で静止する時計を用いたことが重要であり、その系への所属によって同じ時間を名付けるという一文を通読した。明示した操作上の所属の読みの下で内容・参照・範囲・理由・提示に未処理項目はないと判断する。次の第二節見出し以降は残る。',
)


def source_record():
    inv=json.loads(read(INVENTORY));u=inv['units'][21];s=u['text'];assert len(s)==207 and sum(not c.isspace() for c in s)==177 and not u['math_ids']
    note=next(a for a in inv['annotations'] if a['id']=='A0006');assert note['kind']=='page' and note['source_id']=='895' and not note['text']
    paths=[INVENTORY,'artifacts/einstein-synchrony-continuation-v1/page-894.jpg','artifacts/einstein-synchrony-continuation-v1/page-894.html','artifacts/einstein-synchrony-continuation-v1/retrieval.json','artifacts/einstein-rest-time-v1/page-895.jpg','artifacts/einstein-rest-time-v1/page-895.html','artifacts/einstein-rest-time-v1/retrieval.json','scripts/review_rest_system_time.py']
    return dict(version='einstein-rest-system-time-source-reading-v1',reviewer='assistant_visual_and_text_review',pages=['894','895'],images=[paths[1],paths[4]],segments=[dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[0,len(s)],text=s,nonblank_characters=177,math=[])],editorial_annotations=[dict(id='A0006',kind='page',page='895',adds_proposition=False)],observations=['894頁末のWesentlich ist, daß wir die Zeit mittels im ruhenden Systemから895頁冒頭のruhender Uhrenへ続く一文を照合した。','eben definierte Zeit、wegen dieser Zugehörigkeit、引用符付きdie Zeit des ruhenden Systemsを保持する。引用された名前の改行は別の語や命題にしない。'],semantic_completion=False,source_sha256={p:digest((ROOT/p).read_bytes()) for p in paths})


def build_reading():
    u=json.loads(read(INVENTORY))['units'][21];paths=[INVENTORY,DOC,SOURCE,*PRIORS,'scripts/review_rest_system_time.py']
    return dict(schema_version='noema-sentence-reading-1',status='stationary_clock_definition_and_reasoned_naming_checked',reviewer='assistant_close_reading',document=FULL,meaning_basis=BASIS,unit=u['id'],range=[0,len(u['text'])],source=u['text'],source_text_sha256=u['text_sha256'],source_nonblank_characters=177,math=[],selection=selection_binding(load_catalog(ROOT,BASIS),[INDEX]),requirements=[dict(requirement=k,judgment='preserved_under_stated_reading',reason=v) for k,v in zip(REQUIREMENTS,REASONS)],interpretation_limits=LIMITS,verified_full_units=0,semantic_equivalence_automatically_proved=False,remaining=['全単位判断の登録、第二節u0023以降'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in paths})


@lru_cache(None)
def review_record():
    catalog=load_catalog(ROOT,BASIS);u=json.loads(read(INVENTORY))['units'][21]
    paths={FULL,CORE,BASIS,ANNOTATIONS,INVENTORY,DOC,SOURCE,READING,REPORT,*PRIORS,'scripts/review_rest_system_time.py','tests/test_rest_system_time_review.py'}
    pins={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)};merge_pins(pins,catalog.source_sha256)
    for p in (SOURCE,READING,REPORT,*PRIORS):
        r=json.loads(read(p));validate_hashes(ROOT,r['source_sha256']);merge_pins(pins,r['source_sha256'])
    return dict(schema_version='noema-semantic-review-1',work='einstein-1905',unit=u['id'],reviewer='assistant_review',decision='equivalent_under_stated_reading',document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source=dict(inventory=INVENTORY,unit_sha256=u['text_sha256'],text=u['text'],range=[0,len(u['text'])],math=[]),selection=selection_binding(catalog,[INDEX]),source_order_statements=[INDEX],interpretation=LIMITS[:-1],limits=['明示した解釈に基づくアシスタントの通読判断。独立査読・唯一の歴史的解釈・同義性の自動証明・全物理状況の証明ではない。','第二節u0023以降と二作品全体の記述は未完。'],unresolved=[],requirements=[dict(id=k,decision='satisfied',reason=v) for k,v in zip(REQUIREMENTS,REASONS)],evidence=dict(source_reading=[SOURCE],formal_checks=[REPORT],semantic_reading=[DOC]),source_sha256=pins)


def prepare():
    from scripts.audit_opening_scope import write_exact
    write_exact(ROOT/REVIEW,json.dumps(review_record(),ensure_ascii=False,indent=2)+'\n')


def build_report():
    r=review_record();assert json.loads(read(REVIEW))==r
    active=dict(document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source_inventory=INVENTORY)
    result=validate_review(ROOT,REVIEW,'einstein-1905',active,load_catalog(ROOT,BASIS),json.loads(read(INVENTORY)))
    assert result['source_nonblank_characters']==177
    return dict(status='rest_system_time_naming_whole_unit_reviewed',document=FULL,source_units={'einstein-1905:u0022':177},whole_units_semantically_verified=True,verified_full_units={'kant-1784':0,'einstein-1905':1},semantic_equivalence_automatically_proved=False,source_sha256=r['source_sha256']|{REVIEW:digest((ROOT/REVIEW).read_bytes())})
