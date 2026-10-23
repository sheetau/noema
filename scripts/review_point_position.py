"""Pin the complete conditional reading of stationary-point position measurement."""
from functools import lru_cache
import json
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.semantic_reviews import REQUIREMENTS,digest,selection_binding,validate_hashes,validate_review
from noema.review_registry import merge_pins
from scripts.check_einstein_principles_paragraph import calls
from scripts.compose_point_position import ROOT,read,FULL,CORE,BASIS,ANNOTATIONS,LIMITS

INVENTORY='artifacts/written-units-v1/einstein-1905.json';SOURCE='data/einstein-point-position-source-reading-v1.json'
DOC='docs/point-position-v1.md';REPORT='reports/point-position-v1.json';REVIEW='data/einstein-point-position-review-v1.json'
REASONS=(
 '固定u0009全242文字・211非空白文字を原刊892頁と照合した。Ruht ein materieller Punktからausgedrückt werden.までの全一文を覆い、Koordinaten-systemとaus-gedrücktの行末分割を接続した転記へ対応させた。数式・著者脚注はない。',
 '同じ座標系に対する物質点の静止を条件とし、その位置を剛体物差しとEuclid幾何学で決定し、Cartesian座標で表せるという可能性を保持する。静止は完全な履歴の全時刻対、物差しは全使用期間と全道具、幾何は正規直交三軸への符号付き射影として合成する。',
 'diesem Koordinatensystemとletzteremを先行の同じra、seine Lageを量化された同じ物質点の位置へ結ぶ。物理的な点・系・単位、方法・幾何記録・許容された実施設定を共有し、別の点の位置決定と座標表現を混ぜない。',
 'eiifの条件内容をeiigで主張し、eiihで同じ著者rdと論説eirfへ帰属する。直前の静止系命名の箇所eisedから当該箇所eiselへの順序を保持する。測定を命じる発話や、実測結果の報告へ置き換えない。',
 '物質点を空間点や物体全体へ替えず、静止の端点一致や都合のよい瞬間だけに縮めない。可能性から参照状況での測定済みを導かず、現実の任意の実機精度や全実数の有限計算を要求しない。原点・軸方向は選択でき、右手系は明示した規約である。',
 '物質点の帰属eirhと完全履歴se、剛性eigy、正規直交三軸eiajと射影eiamを再利用して意味を確認した。校正、全道具の範囲、記録の物理的割当、長さの比較・移し取り・分割とEuclid作図による操作、対象を保持する許容設定は各引数と意味規約を明示する。文全体を未説明の一つの真偽入力で代用しない。',
 '原刊照合、厳密な有理数埋込みによる射影と再構成、誤成分・別対象・途中の運動・不適格な道具の拒否、全引数の接続、条件文と帰属の検査を固定した。全実数と全関数の有限評価は拒否し、局所量化本体の対照例を全域の証明や物理的実測へ昇格させない。',
 '静止という条件から、同じ位置を同じ系で決定し表せるという可能性までを全一文として再読した。明示した読みの下で内容・範囲・参照・提示の未処理項目はないと判断する。後続の運動・時間の段落と第一節全体はこの判断の範囲外である。',
)

@lru_cache(None)
def review_record():
    catalog=load_catalog(ROOT,BASIS);unit=json.loads(read(INVENTORY))['units'][8];source=json.loads(read(SOURCE))
    assert unit['id']=='einstein-1905:u0009' and source['source_unit']==unit['id'] and source['unit_sha256']==unit['text_sha256'] and source['text']==unit['text']
    assert len(unit['text'])==242 and sum(not c.isspace() for c in unit['text'])==211 and not unit['math_ids']
    assert source['sentence_ranges']==[dict(range=[0,242],text=unit['text'],nonblank_characters=211)]
    ds={d['name']:d for d in catalog.document['declarations']}
    def get(parent,callee):
        cs=[c for c in calls(ds[parent]['body']) if c['symbol']==callee];assert len(cs)==1;return cs[0]
    def constant(n):return dict(kind='call',symbol=n,arguments=[])
    def var(n):return dict(kind='variable',name=n)
    assert ds['eiig']['body']['force']=='assert'
    assert ds['eiif']['body']['body']['kind']=='forall'
    situation=ds['eiif']['body']['variable'];particle=ds['eiif']['body']['body']['variable']
    assert situation!=particle
    for callee in ('eiia','eiie'):
        assert get('eiif',callee)['arguments']==[var(particle),constant('ra'),var(situation)]
    assert [a['symbol'] for a in get('eiih','ue')['arguments']]==['eised','eisel','ri']
    assert get('eiih','eir3')['arguments']==[constant('eisel'),constant('rd'),constant('eirf'),dict(kind='quote',body=constant('eiig')),constant('ri')]
    p,f,ref=[p['name'] for p in ds['eiie']['parameters']];node=ds['eiie']['body'];bound=[]
    while node['kind']=='exists':bound.append(node['variable']);node=node['body']
    method,lengthunit,record,setting=bound
    assert [a['name'] for a in get('eiie','eisek')['arguments']]==[method,p,f,lengthunit,ref,setting]
    assert [a['name'] for a in get('eiie','eiid')['arguments']]==[method,p,f,lengthunit,record,setting]
    outcome=[p['name'] for p in ds['eiid']['parameters']]
    assert [a['name'] for a in get('eiid','eiic')['arguments']]==[outcome[i] for i in (4,1,2,3,5)]
    # The universally selected ruler is the sole additional variable at this call.
    ruler_call=get('eiid','eiib')['arguments'];assert ruler_call[0]['name'] not in outcome
    assert [a['name'] for a in ruler_call[1:]]==[outcome[i] for i in (0,2,3,5)]
    assert {'se','eirh','zm','eisee','sca'}<={c['symbol'] for c in calls(ds['eih6']['body'])}
    assert {'eigy','eisef'}=={c['symbol'] for c in calls(ds['eiib']['body'])}
    assert len(get('eiic','eih7')['arguments'])==18
    assert len([c for c in calls(ds['eih7']['body']) if c['symbol']=='eiam'])==3
    load_annotations(ROOT,BASIS,ANNOTATIONS)
    evidence=dict(source_reading=[SOURCE],formal_checks=[REPORT],semantic_reading=[DOC])
    paths={FULL,CORE,BASIS,ANNOTATIONS,INVENTORY,SOURCE,REPORT,DOC,'scripts/review_point_position.py','tests/test_point_position_review.py','scripts/check_einstein_principles_paragraph.py'}
    pins={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)};merge_pins(pins,catalog.source_sha256)
    for p in (SOURCE,REPORT):
        record=json.loads(read(p));validate_hashes(ROOT,record['source_sha256']);merge_pins(pins,record['source_sha256'])
    return dict(schema_version='noema-semantic-review-1',work='einstein-1905',unit=unit['id'],reviewer='assistant_review',decision='equivalent_under_stated_reading',document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,
        source=dict(inventory=INVENTORY,unit_sha256=unit['text_sha256'],text=unit['text'],range=[0,242],math=[]),selection=selection_binding(catalog,[223]),source_order_statements=[223],interpretation=LIMITS,
        limits=['明示した読みで原文の意味と提示の役割を照合したアシスタントの判断。独立査読、全ての歴史的解釈、同義性の自動証明、物理的な実測や計算可能性の証明を主張しない。','次段落の運動・時間関数と時間の物理的意味、第一節以降の全単位記述は未完で、二作品全体の目標は継続する。'],unresolved=[],requirements=[dict(id=k,decision='satisfied',reason=v) for k,v in zip(REQUIREMENTS,REASONS)],evidence=evidence,source_sha256=pins)

def prepare():
    from scripts.audit_opening_scope import write_exact
    write_exact(ROOT/REVIEW,json.dumps(review_record(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    assert json.loads(read(REVIEW))==review_record()
    active=dict(document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source_inventory=INVENTORY)
    verified=validate_review(ROOT,REVIEW,'einstein-1905',active,load_catalog(ROOT,BASIS),json.loads(read(INVENTORY)))
    return dict(status='stationary_point_position_holistically_reviewed_under_explicit_reading',document=FULL,source_unit='einstein-1905:u0009',source_order_statements=[223],source_nonblank_characters=verified['source_nonblank_characters'],whole_unit_semantically_verified=True,verified_full_units={'kant-1784':0,'einstein-1905':1},semantic_equivalence_automatically_proved=False,source_sha256=review_record()['source_sha256']|{REVIEW:digest((ROOT/REVIEW).read_bytes())})
