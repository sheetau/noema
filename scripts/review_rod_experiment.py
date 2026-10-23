"""Read the complete rod setup, imagined motion and prospective length inquiry."""
from functools import lru_cache
import json,re
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import REQUIREMENTS,digest,selection_binding,validate_hashes,validate_review
from noema.review_registry import merge_pins
from scripts.compose_rod_experiment import ROOT,read,FULL,CORE,BASIS,ANNOTATIONS,INDICES,LIMITS
from scripts.check_rod_geometry import source_record as geometry_source

INVENTORY='artifacts/written-units-v1/einstein-1905.json';DOC='docs/rod-experiment-v1.md'
SOURCE='data/einstein-rod-experiment-source-reading-v1.json';REPORT='reports/rod-experiment-v1.json';REVIEW='data/einstein-rod-experiment-review-v1.json'
PRIORS=('data/einstein-second-principle-u0026-review-v1.json','data/einstein-second-principle-u0027-review-v1.json','data/einstein-second-principle-u0028-review-v1.json')
DEPENDENCY='reports/rod-geometry-v1.json'
REASONS=(
 '原刊895頁のEs seiから二操作を導入するコロンまで、固定u0029の496転記文字・395本文文字を照合した。五数式対象l/X/v/X/xと第一文のセミコロンを保持する。',
 '同じ静止棒と同じく静止した物差しによる初期長、長軸のX軸上配置、その後の正のX方向等速並進、運動する棒の長さへの問いを結ぶ。全物質点の静止・距離保存・全時刻対の並進を使う。',
 'derselbe/dem Stabe/bewegten Stabesは同じxi、Maßstabは同じxj、静止系は既出ra、l=ya、v=yb、X/xは第一空間成分ynとする。初期・配置後・運動後・二測定の文脈と同じ長さ時間単位を保つ。',
 '第一文を仮定的な対象と長さを置く設定指示、第二文を思考上の操作の想定、第三文を方法付き問いと二操作で調べる想定として著者へ帰属する。本文三文と後続二方法の順序を保つ。',
 '全物質点を軸上に限らず、初期観測者の静止や後続観測者との同一性を足さない。運動前後の長さ一致、配置後の待ち時間、加速法則、現実の測定や問いの答えの存在・唯一性を補わない。',
 '既存のeipe/eipd/eipgとeiahへ全履歴・形状・計量を結び、sbqの接触と読み、sbvの独立した二方法を保持する。形状の同定と測定の物理入力を、合成された数値・履歴条件や有限の検査入力と区別する。',
 '原刊と五数式の照合、既存の棒幾何の固定検査、履歴の全引数・三段階・測定・方法付き候補・引用と提示の検査を記録する。全実数履歴や物理的実現、原文との意味同値の自動証明にはしない。',
 '三文を後続二方法への前方参照も含めて通読した。直線状の巨視的な棒、仮定的な設定・操作、同じ対象の方法付きの問いという明示した読みで欠落はないと判断する。u0030以降の詳述と比較は残る。',
)


def source_record():
    prior=geometry_source();stored=json.loads(read('data/einstein-rod-geometry-source-reading-v1.json'))
    assert prior==stored;validate_hashes(ROOT,prior['source_sha256'])
    u=json.loads(read(INVENTORY))['units'][28];text=u['text']
    starts=[0,text.index('Wir denken'),text.index('Wir fragen')];ends=[starts[1]-1,starts[2]-1,len(text)]
    bindings={'M0043':{'l':'ya; eipi/eipj length'},'M0044':{'X':'yn; eipd via eipj'},'M0045':{'v':'yb; eipk speed'},'M0046':{'X':'yn; eipg via eipk'},'M0047':{'x':'first spatial coordinate selected by yn; positive eipf/sbm speed'}}
    math=[dict(m,bindings=bindings[m['id']]) for m in prior['math']]
    paths=[DOC,'scripts/review_rod_experiment.py','data/einstein-rod-geometry-source-reading-v1.json']
    pins=dict(prior['source_sha256']);pins.update({p:digest((ROOT/p).read_bytes()) for p in paths})
    return dict(version='einstein-rod-experiment-source-reading-v1',reviewer='assistant_visual_and_text_review',pages=['895'],images=['artifacts/einstein-rest-time-v1/page-895.jpg'],segments=[dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[0,len(text)],text=text,nonblank_characters=395,math=math)],sentences=[dict(range=[a,b],text=text[a:b],statement=idx) for a,b,idx in zip(starts,ends,INDICES)],observations=prior['observations']+['セミコロンを含む第一文は設定の指示で、第二文はhieraufによる順序、第三文は二つの以下の操作へのコロンを保持する。'],semantic_completion=False,source_sha256=pins)


@lru_cache(None)
def record():
    catalog=load_catalog(ROOT,BASIS);u=json.loads(read(INVENTORY))['units'][28];assert json.loads(read(SOURCE))==source_record()
    paths={FULL,CORE,BASIS,ANNOTATIONS,INVENTORY,SOURCE,REPORT,DEPENDENCY,DOC,*PRIORS,'scripts/review_rod_experiment.py','tests/test_rod_experiment_review.py'}
    pins={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)};merge_pins(pins,catalog.source_sha256)
    for p in (SOURCE,REPORT,DEPENDENCY):
        rec=json.loads(read(p));validate_hashes(ROOT,rec['source_sha256']);merge_pins(pins,rec['source_sha256'])
    return dict(schema_version='noema-semantic-review-1',work='einstein-1905',unit=u['id'],reviewer='assistant_review',decision='equivalent_under_stated_reading',document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source=dict(inventory=INVENTORY,unit_sha256=u['text_sha256'],text=u['text'],range=[0,len(u['text'])],math=[{k:m[k] for k in ('id','sha256')} for m in source_record()['segments'][0]['math']]),selection=selection_binding(catalog,list(INDICES)),source_order_statements=list(INDICES),interpretation=LIMITS,limits=['明示した解釈に基づくアシスタントの通読判断。独立査読・唯一の歴史的解釈・同義性の自動証明ではない。','u0030以降と二作品全体の目標は未完。'],unresolved=[],requirements=[dict(id=k,decision='satisfied',reason=v) for k,v in zip(REQUIREMENTS,REASONS)],evidence=dict(source_reading=[SOURCE],formal_checks=[REPORT,DEPENDENCY],semantic_reading=[DOC]),source_sha256=pins)


def prepare():
    from scripts.audit_opening_scope import write_exact
    write_exact(ROOT/REVIEW,json.dumps(record(),ensure_ascii=False,indent=2)+'\n')


def build_report():
    rec=record();assert json.loads(read(REVIEW))==rec
    active=dict(document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source_inventory=INVENTORY)
    validate_review(ROOT,REVIEW,'einstein-1905',active,load_catalog(ROOT,BASIS),json.loads(read(INVENTORY)))
    assert source_record()['segments'][0]['nonblank_characters']==395
    return dict(status='rod_setup_imagined_motion_and_length_inquiry_whole_unit_reviewed',document=FULL,source_units={'einstein-1905:u0029':395},whole_units_semantically_verified=True,verified_full_units={'kant-1784':0,'einstein-1905':1},semantic_equivalence_automatically_proved=False,source_sha256=rec['source_sha256']|{REVIEW:digest((ROOT/REVIEW).read_bytes())})
