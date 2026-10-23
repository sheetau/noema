"""Read the second principle and its cross-unit speed/time explanation."""
from functools import lru_cache
import json,re
from xml.etree import ElementTree as ET
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import REQUIREMENTS,digest,selection_binding,validate_hashes,validate_review
from noema.review_registry import merge_pins
from scripts.compose_second_principle import ROOT,read,FULL,CORE,BASIS,ANNOTATIONS,INDICES,LIMITS

INVENTORY='artifacts/written-units-v1/einstein-1905.json';DOC='docs/second-principle-v1.md'
SOURCE='data/einstein-second-principle-source-reading-v1.json';READING='data/second-principle-reading-v1.json';REPORT='reports/second-principle-v1.json'
REVIEWS=tuple(f'data/einstein-second-principle-u00{i}-review-v1.json' for i in (26,27,28))
PRIORS=('data/einstein-first-principle-review-v1.json','data/einstein-event-time-summary-review-v1.json','data/einstein-two-principle-introduction-review-v1.json')
REASONS=(
 '固定u0026〜u0028の計305転記文字・253本文文字を原刊895頁の番号2から第一節の定義参照の終わりまで照合した。M0041のV、M0042の光路/時間、引用符付きruhendenとZeitdauerを保持する。',
 '同じ静止系の全光線に一つのVを固定し、放出元の静止・運動いずれも同じ条件で扱う。速度式の経路長・正の時間間隔・速度を結び、時間は第一節の同じ時刻付与の終値と始値の差とする。',
 'この静止系はra、Vは既出tc、局所時計の共通参照はrc、単位はrb/ta/tbである。各区間の同じ光・放出元・放出・始終・時計・場所・指示値を保ち、第一節eisdyの定義eingへ参照を結ぶ。',
 '第二項の定義提示、先行する光速度原理への指示、第一原理からの順序、Hierbeiからwobeiまで続く速度と時間の補足を保持する。原理の実証、実測値の報告、別の第三原理にはしない。',
 '絶対静止、現代の光速値、静止光源だけの範囲、放出速度の加算、往復係数2、直線距離による経路長の代用、光源固有時又は受信時刻の代用を加えない。零や負の経過時間を商の分母にしない。',
 '光・真空・経路・全範囲・単位のeifw/eifx、放出元の排他的分類saz、両端時刻のeing、正の片道速度saxを合成する。表示式eiovと物理的適用eiow、量の呼称と節の定義参照を区別する。',
 '原刊と数式構造の照合、既存の第一節の判断、数値式、時計表示・分類・範囲・型付き規則の全位置と提示の検査を固定する。同期は局所検査の明示入力であり、全物理状況や全実数の自動証明にはしない。',
 '法則文と、三原文単位をまたぐ速度・時間の説明を通読した。各単位を共有文脈の中で確認し、明示した真空・非零区間・第一節の時間という読みの下で欠落はないと判断する。u0029以降は残る。',
)


def prose(s):return sum(not c.isspace() for c in re.sub(r'\[M\d+\]','',s))


def source_record():
    inv=json.loads(read(INVENTORY));units=inv['units'][25:28];math={m['id']:m for m in inv['math'] if m['id'] in ('M0041','M0042')}
    assert [len(u['text']) for u in units]==[215,24,66] and [prose(u['text']) for u in units]==[181,16,56]
    assert math['M0041']['sha256']=='fad146c158bc7dc725209b362adcee4dfb08d7da13a15bf61ab90897102da806'
    assert math['M0042']['sha256']=='5b9efd0af2b9888458899f242088025a511f8d036eafe22f9b00f0ee03d75930'
    frac=ET.fromstring(math['M0042']['mathml']).find('.//{*}mfrac');assert [''.join(x.itertext()) for x in frac]==['Lichtweg','Zeitdauer']
    assert ''.join(ET.fromstring(math['M0041']['mathml']).itertext())=='V'
    paths=[INVENTORY,DOC,'scripts/review_second_principle.py','artifacts/einstein-rest-time-v1/page-895.jpg','artifacts/einstein-rest-time-v1/page-895.html','artifacts/einstein-rest-time-v1/retrieval.json']
    assert digest((ROOT/paths[3]).read_bytes())=='d6d76216b027b8121b3d2822e93e9293b1afafd86fdf222a7dca39a23ea78289'
    details={'M0041':dict(reading='V',bindings={'V':'tc'},definition='eiot'),'M0042':dict(reading='Geschwindigkeit = Lichtweg / Zeitdauer',bindings={'Geschwindigkeit':'eiov parameter 2: speed','Lichtweg':'eiov parameter 0: path','Zeitdauer':'eiov parameter 1: duration; eiou'},definition='eiov')}
    segments=[dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[0,len(u['text'])],text=u['text'],nonblank_characters=prose(u['text']),math=[dict(id=i,sha256=math[i]['sha256'],**details[i]) for i in u['math_ids']]) for u in units]
    return dict(version='einstein-second-principle-source-reading-v1',reviewer='assistant_visual_and_text_review',pages=['895'],images=[paths[3]],segments=segments,observations=['番号2の法則文にVがあり、その後のHierbei istから表示式とwobeiの時間参照まで一つの説明が続く。','分子はLichtweg、分母はZeitdauer。左辺Geschwindigkeitは数式外の転記u0027にも保持する。','ruhendenは同じ系の既存呼称、引用されたZeitdauerは第一節の時刻定義による時間間隔を指す。'],semantic_completion=False,source_sha256={p:digest((ROOT/p).read_bytes()) for p in paths})


def build_reading():
    paths=[INVENTORY,DOC,SOURCE,*PRIORS,'scripts/review_second_principle.py']
    return dict(schema_version='noema-connected-reading-1',status='second_principle_and_cross_unit_speed_time_explanation_checked',reviewer='assistant_close_reading',document=FULL,meaning_basis=BASIS,segments=source_record()['segments'],source_nonblank_characters=253,selection=selection_binding(load_catalog(ROOT,BASIS),list(INDICES)),requirements=[dict(requirement=k,judgment='preserved_under_stated_reading',reason=v) for k,v in zip(REQUIREMENTS,REASONS)],interpretation_limits=LIMITS,verified_full_units=0,semantic_equivalence_automatically_proved=False,remaining=['三原文単位の判断登録、u0029以降'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in paths})


@lru_cache(None)
def record(i):
    catalog=load_catalog(ROOT,BASIS);u=json.loads(read(INVENTORY))['units'][25+i];segment=source_record()['segments'][i]
    paths={FULL,CORE,BASIS,ANNOTATIONS,INVENTORY,DOC,SOURCE,READING,REPORT,*PRIORS,'scripts/review_second_principle.py','tests/test_second_principle_review.py'}
    pins={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)};merge_pins(pins,catalog.source_sha256)
    for p in (SOURCE,READING,REPORT):
        rec=json.loads(read(p));validate_hashes(ROOT,rec['source_sha256']);merge_pins(pins,rec['source_sha256'])
    indices=list(INDICES) if i==0 else [INDICES[1]]
    return dict(schema_version='noema-semantic-review-1',work='einstein-1905',unit=u['id'],reviewer='assistant_review',decision='equivalent_under_stated_reading',document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source=dict(inventory=INVENTORY,unit_sha256=u['text_sha256'],text=u['text'],range=[0,len(u['text'])],math=[{k:m[k] for k in ('id','sha256')} for m in segment['math']]),selection=selection_binding(catalog,indices),source_order_statements=indices,interpretation=LIMITS+['u0026末尾・u0027・u0028は共有された一続きの説明であり、数式又はwobei節だけを独立の主張へ分離しない。'],limits=['明示した解釈に基づくアシスタントの通読判断。独立査読・唯一の歴史的解釈・同義性の自動証明ではない。','u0029以降と二作品全体の目標は未完。'],unresolved=[],requirements=[dict(id=k,decision='satisfied',reason=v) for k,v in zip(REQUIREMENTS,REASONS)],evidence=dict(source_reading=[SOURCE],formal_checks=[REPORT],semantic_reading=[DOC]),source_sha256=pins)


def prepare():
    from scripts.audit_opening_scope import write_exact
    for i,path in enumerate(REVIEWS):write_exact(ROOT/path,json.dumps(record(i),ensure_ascii=False,indent=2)+'\n')


def build_report():
    active=dict(document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source_inventory=INVENTORY);catalog=load_catalog(ROOT,BASIS);inv=json.loads(read(INVENTORY));pins={}
    for i,path in enumerate(REVIEWS):
        rec=record(i);assert json.loads(read(path))==rec
        validate_review(ROOT,path,'einstein-1905',active,catalog,inv)
        assert prose(rec['source']['text'])==(181,16,56)[i]
        merge_pins(pins,rec['source_sha256']);pins[path]=digest((ROOT/path).read_bytes())
    return dict(status='second_principle_and_speed_time_explanation_whole_units_reviewed',document=FULL,source_units={f'einstein-1905:u00{i}':n for i,n in zip((26,27,28),(181,16,56))},whole_units_semantically_verified=True,verified_full_units={'kant-1784':0,'einstein-1905':3},semantic_equivalence_automatically_proved=False,source_sha256=pins)
