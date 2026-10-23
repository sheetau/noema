"""Read the two measurement operations across the original page boundary."""
from functools import lru_cache
import json,re
from xml.etree import ElementTree as ET
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import REQUIREMENTS,digest,selection_binding,validate_hashes,validate_review
from noema.review_registry import merge_pins
from scripts.compose_rod_methods import ROOT,read,FULL,CORE,BASIS,ANNOTATIONS,INDICES,LIMITS

INVENTORY='artifacts/written-units-v1/einstein-1905.json';DOC='docs/rod-methods-v1.md'
SOURCE='data/einstein-rod-methods-source-reading-v1.json';REPORT='reports/rod-methods-v1.json'
REVIEWS=('data/einstein-comoving-ruler-method-review-v1.json','data/einstein-synchronized-endpoints-method-review-v1.json')
PRIORS=('data/einstein-rod-experiment-review-v1.json','data/einstein-event-time-summary-review-v1.json')
DEPENDENCIES=('reports/rod-geometry-v1.json','reports/rod-experiment-v1.json','reports/first-principle-v1.json')
REASONS=(
 '原刊895頁の二操作と896頁冒頭を固定u0030/u0031に照合した。a)207本文文字、b)353本文文字、M0048のt、b)第二文の引用符付きLänge des Stabesを保持する。',
 '方法aの同伴・直接接触・読みと静止の場合への手順比較、方法bの静止時計・第一節の同期・同じ指定時刻の二端の場所・同じく静止した物差しによる距離を結ぶ。両値候補を長さと呼び得る許容を分ける。',
 '先の棒xi・物差しxj、今回の観測者xk、同じraと同伴側xl、別設定ye/yf、両端xn/xo・出来事xp/xq・場所xt/xu・時計xr/xsを保持する。tは同じxvで、第一節のeingと共通参照rc・単位rbを使う。',
 'u0029が想定した二操作の詳述として、方法の候補条件をxzで著者へ帰属する。コロンに続く第一項・第二項、手順の仮定的比較、第一節への参照、追加の呼称の許容を保持し、現実の実測報告にはしない。',
 '初期長yaとの一致、二方法の値の一致・相違、相対性原理からの結論、比較側の静止の現実化を加えない。方法bで観測者の静止、遠隔受信時刻、別の物差し、二設定で同時に両系へ静止する条件を足さない。',
 '既存の全物質点履歴、剛性、等速並進、共通の直接測定sbe、二端のsbf、局所時刻eing、世界線と座標sb、距離th/xh、軸長eipaを合成する。物理的な操作・尺度の読みと、数値の条件や有限の検査入力を区別する。',
 '原刊二頁と数式の固定記録、先の棒設定・幾何・第一節の判断を保持する。履歴の引数、時計表示と指定時刻、観測操作、二つの測定の値と提示の検査は、全実数・物理的実現・意味同値の自動証明と区別する。',
 '二方法を前段の問いと後段の比較に照らして通読した。巨視的な同伴と直接測定、静止系の同時刻の端点測定、手順比較と呼称の許容という読みで欠落はないと判断する。u0032以降の結論と論証は残る。',
)


def prose(s):return sum(not c.isspace() for c in re.sub(r'\[M\d+\]','',s))


def source_record():
    inv=json.loads(read(INVENTORY));units=inv['units'][29:31]
    assert [len(u['text']) for u in units]==[243,420] and [prose(u['text']) for u in units]==[207,353]
    m=next(m for m in inv['math'] if m['id']=='M0048');assert ''.join(ET.fromstring(m['mathml']).itertext())=='t'
    paths={INVENTORY,DOC,'scripts/review_rod_methods.py','artifacts/einstein-rest-time-v1/retrieval.json','artifacts/einstein-rod-methods-v1/retrieval.json'}
    for receipt in ('artifacts/einstein-rest-time-v1/retrieval.json','artifacts/einstein-rod-methods-v1/retrieval.json'):
        for row in json.loads(read(receipt))['sources']:
            assert digest((ROOT/row['path']).read_bytes())==row['sha256'];paths.add(row['path'])
    assert digest((ROOT/'artifacts/einstein-rod-methods-v1/page-896.jpg').read_bytes())=='62f25cc4a43dce692fe34e00673499c572f3533564e5d84790463ea53d687912'
    return dict(version='einstein-rod-methods-source-reading-v1',reviewer='assistant_visual_and_text_review',pages=['895','896'],images=['artifacts/einstein-rest-time-v1/page-895.jpg','artifacts/einstein-rod-methods-v1/page-896.jpg'],segments=[dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[0,len(u['text'])],text=u['text'],nonblank_characters=prose(u['text']),math=[] if i==0 else [dict(id=m['id'],sha256=m['sha256'],printed='t',binding='xv; both local times x2/x3, eip4')]) for i,u in enumerate(units)],observations=['a)の末尾は三者が静止していた場合へのwie wennの比較である。','b)第一文は895頁末尾で終わり、二地点の距離とその呼称を述べる第二文が896頁冒頭へ続く。','同じ物差しを指すvorher genanntenとschon benutzten、今回は静止するin diesem Falle、ebenfallsとbezeichnen kannを保持する。'],semantic_completion=False,source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})


@lru_cache(None)
def record(i):
    catalog=load_catalog(ROOT,BASIS);u=json.loads(read(INVENTORY))['units'][29+i];assert json.loads(read(SOURCE))==source_record()
    paths={FULL,CORE,BASIS,ANNOTATIONS,INVENTORY,SOURCE,REPORT,DOC,*PRIORS,*DEPENDENCIES,'scripts/review_rod_methods.py','tests/test_rod_methods_review.py'}
    pins={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)};merge_pins(pins,catalog.source_sha256)
    for p in (SOURCE,REPORT,*DEPENDENCIES):
        rec=json.loads(read(p));validate_hashes(ROOT,rec['source_sha256']);merge_pins(pins,rec['source_sha256'])
    return dict(schema_version='noema-semantic-review-1',work='einstein-1905',unit=u['id'],reviewer='assistant_review',decision='equivalent_under_stated_reading',document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source=dict(inventory=INVENTORY,unit_sha256=u['text_sha256'],text=u['text'],range=[0,len(u['text'])],math=[{k:m[k] for k in ('id','sha256')} for m in source_record()['segments'][i]['math']]),selection=selection_binding(catalog,[INDICES[i]]),source_order_statements=[INDICES[i]],interpretation=LIMITS,limits=['明示した解釈に基づくアシスタントの通読判断。独立査読・唯一の歴史的解釈・同義性の自動証明ではない。','u0032以降と二作品全体の目標は未完。'],unresolved=[],requirements=[dict(id=k,decision='satisfied',reason=v) for k,v in zip(REQUIREMENTS,REASONS)],evidence=dict(source_reading=[SOURCE],formal_checks=[REPORT,*DEPENDENCIES],semantic_reading=[DOC]),source_sha256=pins)


def prepare():
    from scripts.audit_opening_scope import write_exact
    for i,path in enumerate(REVIEWS):write_exact(ROOT/path,json.dumps(record(i),ensure_ascii=False,indent=2)+'\n')


def build_report():
    pins={};active=dict(document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source_inventory=INVENTORY)
    for i,path in enumerate(REVIEWS):
        rec=record(i);assert json.loads(read(path))==rec
        validate_review(ROOT,path,'einstein-1905',active,load_catalog(ROOT,BASIS),json.loads(read(INVENTORY)))
        merge_pins(pins,rec['source_sha256']);pins[path]=digest((ROOT/path).read_bytes())
    return dict(status='two_rod_measurement_operations_whole_units_reviewed',document=FULL,source_units={'einstein-1905:u0030':207,'einstein-1905:u0031':353},whole_units_semantically_verified=True,verified_full_units={'kant-1784':0,'einstein-1905':2},semantic_equivalence_automatically_proved=False,source_sha256=pins)
