"""Read the full tacit-kinematics sentence and its attributed reformulation."""
from functools import lru_cache
import json,re
from xml.etree import ElementTree as ET
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import REQUIREMENTS,digest,selection_binding,validate_hashes,validate_review
from noema.review_registry import merge_pins
from scripts.compose_kinematic_replacement import ROOT,read,FULL,CORE,BASIS,ANNOTATIONS,INDICES,LIMITS

INVENTORY='artifacts/written-units-v1/einstein-1905.json';DOC='docs/kinematic-replacement-v1.md'
SOURCE='data/einstein-kinematic-replacement-source-reading-v1.json';REPORT='reports/kinematic-replacement-v1.json'
REVIEW='data/einstein-kinematic-replacement-review-v1.json'
PRIORS=('data/einstein-comoving-length-necessity-review-v1.json','data/einstein-rest-frame-length-announcement-review-v1.json')
DEPENDENCIES=('reports/rod-length-claims-v1.json','reports/rigid-body-kinematics-v1.json','reports/material-body-motion-v1.json')
REASONS=(
 '固定u0034全348文字・294本文文字とM0051のtを原刊896頁に照合した。厳密な等値、暗黙の仮定、言い換え、同じ剛体、指定時刻、特定の静止配置、幾何学的に完全という範囲を保持する。',
 '現行二方法の値の存在・数値的一意性・相互の等値をsckへ結ぶ。置換は同じ物体の全物質点履歴・剛性・運動と静止、指定時刻と全占有座標像の双方向一致、許容静止配置の存在へ構成する。',
 '同じ二方法eip2/eip6と別設定ye/yfを保持する。通常の運動学zr、考察範囲xy、全対象範囲zn、同じra・単位ta/rb、任意に指定された時刻zpを保ち、初期長yaや前の測定時刻xvへの取り違えを防ぐ。',
 '著者が通常の運動学の暗黙の前提を記述する発話として保持する。仮定の使用と非明示をscjで分け、oder mit anderen Wortenはzxで著者の言い換えに帰属する。著者自身の承認や機械的同値証明ではない。',
 '端点距離や重心だけで全幾何を代用せず、幾何の一致に速度・時計・密度・物質点ラベルの一致を加えない。同じ物体の許容静止配置を任意の別模型へ替えず、実際の停止や停止過程の剛性は追加しない。',
 '既存sck/scj/zxとeiag/eiah/eigy/eiad、同じ校正した座標族を再利用する。全占有像は二方向の各点の対応として定義する。znは全対象、zlは同じ静止形状を保つ比較配置、zsは広い使用という入力規約を明記する。',
 '原刊画像と固定原文・MathML、先の二方法・長さの主張・剛体履歴の証拠を保持する。座標像と有限の論理骨格・引数結合の検査を、全実数・全履歴・物理的実在や意味同値の証明と区別する。',
 '前段の方法bの不一致予告と、後段の棒端の時計を含めて再読した。通常の運動学に帰属する暗黙の等値と、その幾何学的置換への言い換えという明示した読みで欠落はないと判断する。u0035以降と後続論証は残る。',
)


def source_record():
    inv=json.loads(read(INVENTORY));u=inv['units'][33]
    count=sum(not c.isspace() for c in re.sub(r'\[M\d+\]','',u['text']))
    assert u['id']=='einstein-1905:u0034' and len(u['text'])==348 and count==294
    m=next(m for m in inv['math'] if m['id']=='M0051');assert ''.join(ET.fromstring(m['mathml']).itertext())=='t'
    receipt='artifacts/einstein-rod-methods-v1/retrieval.json';paths={INVENTORY,DOC,'scripts/review_kinematic_replacement.py',receipt}
    for row in json.loads(read(receipt))['sources']:
        assert digest((ROOT/row['path']).read_bytes())==row['sha256'];paths.add(row['path'])
    assert digest((ROOT/'artifacts/einstein-rod-methods-v1/page-896.jpg').read_bytes())=='62f25cc4a43dce692fe34e00673499c572f3533564e5d84790463ea53d687912'
    return dict(version='einstein-kinematic-replacement-source-reading-v1',reviewer='assistant_visual_and_text_review',pages=['896'],images=['artifacts/einstein-rod-methods-v1/page-896.jpg'],segments=[dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[0,len(u['text'])],text=u['text'],nonblank_characters=count,math=[dict(id=m['id'],sha256=m['sha256'],printed='t',binding='zp: arbitrarily specified comparison epoch; not identified with xv')])],observations=['Die allgemein gebrauchte Kinematikが主語で、nimmt stillschweigend anが両内容の帰属を支える。','einander genau gleichは二操作間の厳密な等値である。','oder mit anderen Wortenに続くin geometrischer Beziehung vollständig、denselben Körper、in bestimmter Lage ruhtを保持する。'],semantic_completion=False,source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})


@lru_cache(None)
def record():
    catalog=load_catalog(ROOT,BASIS);u=json.loads(read(INVENTORY))['units'][33];assert json.loads(read(SOURCE))==source_record()
    paths={FULL,CORE,BASIS,ANNOTATIONS,INVENTORY,SOURCE,REPORT,DOC,*PRIORS,*DEPENDENCIES,'scripts/review_kinematic_replacement.py','tests/test_kinematic_replacement_review.py'}
    pins={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)};merge_pins(pins,catalog.source_sha256)
    for p in (SOURCE,REPORT,*DEPENDENCIES):
        rec=json.loads(read(p));validate_hashes(ROOT,rec['source_sha256']);merge_pins(pins,rec['source_sha256'])
    return dict(schema_version='noema-semantic-review-1',work='einstein-1905',unit=u['id'],reviewer='assistant_review',decision='equivalent_under_stated_reading',document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source=dict(inventory=INVENTORY,unit_sha256=u['text_sha256'],text=u['text'],range=[0,len(u['text'])],math=[{k:m[k] for k in ('id','sha256')} for m in source_record()['segments'][0]['math']]),selection=selection_binding(catalog,list(INDICES)),source_order_statements=list(INDICES),interpretation=LIMITS,limits=['明示した解釈の下のアシスタントによる通読判断。独立査読や同義性の自動証明ではない。','u0035以降と二作品全体の目標は未完。'],unresolved=[],requirements=[dict(id=k,decision='satisfied',reason=v) for k,v in zip(REQUIREMENTS,REASONS)],evidence=dict(source_reading=[SOURCE],formal_checks=[REPORT,*DEPENDENCIES],semantic_reading=[DOC]),source_sha256=pins)


def prepare():
    from scripts.audit_opening_scope import write_exact
    write_exact(ROOT/REVIEW,json.dumps(record(),ensure_ascii=False,indent=2)+'\n')


def build_report():
    rec=record();assert json.loads(read(REVIEW))==rec
    active=dict(document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source_inventory=INVENTORY)
    validate_review(ROOT,REVIEW,'einstein-1905',active,load_catalog(ROOT,BASIS),json.loads(read(INVENTORY)))
    return dict(status='tacit_kinematics_and_geometric_replacement_whole_unit_reviewed',document=FULL,source_units={'einstein-1905:u0034':294},whole_units_semantically_verified=True,verified_full_units={'kant-1784':0,'einstein-1905':1},semantic_equivalence_automatically_proved=False,source_sha256=rec['source_sha256']|{REVIEW:digest((ROOT/REVIEW).read_bytes())})
