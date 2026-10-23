"""Read the three source units as one empirical light-speed adoption sentence."""
from functools import lru_cache
import json
import re
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import REQUIREMENTS,digest,selection_binding,validate_hashes,validate_review
from noema.review_registry import merge_pins
from scripts.compose_empirical_light_constant import ROOT,read,FULL,CORE,BASIS,ANNOTATIONS,INDEX,LIMITS

INVENTORY='artifacts/written-units-v1/einstein-1905.json';DOC='docs/empirical-light-constant-v1.md'
SOURCE='data/einstein-empirical-light-constant-source-reading-v1.json';READING='data/empirical-light-constant-reading-v1.json'
REPORT='reports/empirical-light-constant-v1.json'
REVIEWS=tuple(f'data/einstein-empirical-light-constant-u00{i}-review-v1.json' for i in (19,20,21))
PRIORS=('data/einstein-event-time-summary-review-v1.json','data/einstein-local-synchrony-paragraph-review-v1.json')
REASONS=(
 '固定u0019〜u0021を原刊894頁のWir setzen nochからsei.までの一文へ照合した。本文46文字と66文字、間の式M0040、括弧内の真空中の光速度を含める。三単位を独立した三文へ分けない。',
 '経験に従う追加採用、全適用試行に共通の値、2倍の一方向距離と同じA時計の帰着−出発という経過時間、真空光往復の速度としての同じ量を保持する。零や負の経過時間、往路だけの距離、反射時計の指示を分母へ替えない。',
 'A/Bの場所ziq/zir、時計eisib/eisik、代表往復eisjj、出発帰着のeisjo/eisjqを共有する。Vは既存tc、距離は同じ試行のtgでthへ結び、系ra・時間単位rb・長さta・速度tb・著者rd・経験tnを固定する。',
 'Wir setzen festは著者による論述上の採用ug、der Erfahrung gemäßはtoによる経験への位置付けとする。nochは先の時刻定義への追加、括弧内の語句は同じ量への補足とし、一般式の代表配置への具体化と一文の順序を保持する。',
 '現代の光速値、実験名、測定済みの全標本、他系との不変性の詳細、任意の曲がった経路の2倍距離を補わない。全適用試行を成功した組だけへ限定せず、試行ごとに異なる速度を選ばない。B時計との同期式は速度測定の式へ加えない。',
 '全適用範囲eiskrと既存tdの一致をeinqで構成し、非空性・完全性・全試行の共通値はsan/sam/sakを再利用する。距離th・両真空区間tk・互換単位ti/tj・物理的往復sal・速度式saiを合成し、文全体を新しい真偽入力へ置き換えない。',
 '原刊照合と一文の通読を、数値式、別距離・別方向の二試行、共通値と範囲、全引数と名付き時刻、経験帰属と括弧補足の検査から区別する。有限検査では構成した有理値の切断だけを使い、未知の切断を点の標本で推定しない。全実数と物理的普遍性は有限標本で証明しない。',
 '導入節、表示式、普遍定数と括弧内説明まで一文として通読した。各原文単位はこの共有された文の構成部分として解釈する。明示した同一系の全適用試行の読みの下で内容・参照・数量・範囲・提示の未処理項目はないと判断する。後続の時刻定義の重要な条件を述べるu0022以降は残る。',
)


def prose(text):return sum(not c.isspace() for c in re.sub(r'\[M\d+\]','',text))


def source_record():
    inv=json.loads(read(INVENTORY));units=inv['units'][18:21];m=next(m for m in inv['math'] if m['id']=='M0040')
    assert m['sha256']=='540c2f8a99022e08a3073a57ed05c4ab6135c1f23baab7507f326695efe65593'
    assert [prose(u['text']) for u in units]==[46,0,66]
    paths=[INVENTORY,'artifacts/einstein-synchrony-continuation-v1/page-894.jpg','artifacts/einstein-synchrony-continuation-v1/page-894.html','artifacts/einstein-synchrony-continuation-v1/retrieval.json','scripts/review_empirical_light_constant.py']
    segments=[dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[0,len(u['text'])],text=u['text'],nonblank_characters=prose(u['text']),math=[dict(id='M0040',sha256=m['sha256'],reading='2 AB/(t′_A−t_A)=V',bindings={'A_place':'ziq','B_place':'zir','departure':'eisjo','return':'eisjq','distance':'tg(eisjj)','V':'tc'},definition='eins') ] if u['math_ids'] else []) for u in units]
    return dict(version='einstein-empirical-light-constant-source-reading-v1',reviewer='assistant_visual_and_text_review',pages=['894'],images=[paths[1]],segments=segments,observations=['原刊894頁で分子の2と上線付きAB、分母のA側帰着t′と出発tの差、右辺Vを確認した。三単位で一つの従属節を含む文である。','noch、der Erfahrung gemäß、universelle Konstanteと括弧内die Lichtgeschwindigkeit im leeren Raumeを保持する。原文に数値や実験名はない。'],semantic_completion=False,source_sha256={p:digest((ROOT/p).read_bytes()) for p in paths})


def build_reading():
    paths=[INVENTORY,DOC,SOURCE,*PRIORS,'scripts/review_empirical_light_constant.py']
    return dict(schema_version='noema-connected-reading-1',status='three_source_units_one_empirical_constant_sentence_checked',reviewer='assistant_close_reading',document=FULL,meaning_basis=BASIS,segments=source_record()['segments'],source_nonblank_characters=112,selection=selection_binding(load_catalog(ROOT,BASIS),[INDEX]),requirements=[dict(requirement=k,judgment='preserved_under_stated_reading',reason=v) for k,v in zip(REQUIREMENTS,REASONS)],interpretation_limits=LIMITS,verified_full_units=0,semantic_equivalence_automatically_proved=False,remaining=['共有文を構成する三原文単位の判断登録、u0022以降'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in paths})


@lru_cache(None)
def review_record(i):
    catalog=load_catalog(ROOT,BASIS);u=json.loads(read(INVENTORY))['units'][18+i];segment=source_record()['segments'][i]
    paths={FULL,CORE,BASIS,ANNOTATIONS,INVENTORY,DOC,SOURCE,READING,REPORT,*PRIORS,'scripts/review_empirical_light_constant.py','tests/test_empirical_light_constant_review.py'}
    pins={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)};merge_pins(pins,catalog.source_sha256)
    for p in (SOURCE,READING,REPORT,*PRIORS):
        r=json.loads(read(p));validate_hashes(ROOT,r['source_sha256']);merge_pins(pins,r['source_sha256'])
    return dict(schema_version='noema-semantic-review-1',work='einstein-1905',unit=u['id'],reviewer='assistant_review',decision='equivalent_under_stated_reading',document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source=dict(inventory=INVENTORY,unit_sha256=u['text_sha256'],text=u['text'],range=[0,len(u['text'])],math=[{k:m[k] for k in ('id','sha256')} for m in segment['math']]),selection=selection_binding(catalog,[INDEX]),source_order_statements=[INDEX],interpretation=LIMITS[:-1]+['この単位はu0019〜u0021で一つの文を構成する。選択は共有された文全体であり、他の二部分を削って単独の主張へ解釈しない。'],limits=['明示した解釈に基づくアシスタントの通読判断。独立査読・唯一の歴史的解釈・同義性の自動証明・物理的普遍性の証明ではない。','u0022以降と二作品全体の記述は未完。'],unresolved=[],requirements=[dict(id=k,decision='satisfied',reason=v) for k,v in zip(REQUIREMENTS,REASONS)],evidence=dict(source_reading=[SOURCE],formal_checks=[REPORT],semantic_reading=[DOC]),source_sha256=pins)


def prepare():
    from scripts.audit_opening_scope import write_exact
    for i,p in enumerate(REVIEWS):write_exact(ROOT/p,json.dumps(review_record(i),ensure_ascii=False,indent=2)+'\n')


def build_report():
    active=dict(document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source_inventory=INVENTORY);catalog=load_catalog(ROOT,BASIS);pins={}
    for i,p in enumerate(REVIEWS):
        r=review_record(i);assert json.loads(read(p))==r
        validate_review(ROOT,p,'einstein-1905',active,catalog,json.loads(read(INVENTORY)))
        assert prose(r['source']['text'])==(46,0,66)[i]
        merge_pins(pins,r['source_sha256']);pins[p]=digest((ROOT/p).read_bytes())
    return dict(status='three_source_units_of_empirical_light_constant_sentence_reviewed',document=FULL,source_units={'einstein-1905:u0019':46,'einstein-1905:u0020':0,'einstein-1905:u0021':66},whole_units_semantically_verified=True,verified_full_units={'kant-1784':0,'einstein-1905':3},semantic_equivalence_automatically_proved=False,source_sha256=pins)
