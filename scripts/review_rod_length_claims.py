"""Read complete length naming, necessity and future-determination sentences."""
from functools import lru_cache
import json,re
from xml.etree import ElementTree as ET
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import REQUIREMENTS,digest,selection_binding,validate_hashes,validate_review
from noema.review_registry import merge_pins
from scripts.compose_rod_length_claims import ROOT,read,FULL,CORE,BASIS,ANNOTATIONS,INDICES,LIMITS

INVENTORY='artifacts/written-units-v1/einstein-1905.json';DOC='docs/rod-length-claims-v1.md'
SOURCE='data/einstein-rod-length-claims-source-reading-v1.json';REPORT='reports/rod-length-claims-v1.json'
REVIEWS=('data/einstein-comoving-length-necessity-review-v1.json','data/einstein-rest-frame-length-announcement-review-v1.json')
PRIORS=('data/einstein-comoving-ruler-method-review-v1.json','data/einstein-synchronized-endpoints-method-review-v1.json')
DEPENDENCIES=('reports/rod-methods-v1.json','reports/first-principle-v1.json','reports/second-principle-v1.json')
REASONS=(
 '原刊896頁の二文を固定u0032/u0033に照合した。二つのlをyaへ固定し、引用された二呼称と第二呼称の括弧付きbewegtenを保持する。',
 '各方法で得る値の存在・数値的一意性と、同じ初期長との比較をsbzで構成する。方法aの等値に関する根拠付き必要性と、方法bの値決定・不一致の予告を分け、両呼称の数量内容を既存の剛体軸長へ結ぶ。',
 '同じ棒xi・単位ta・移動側xl・静止側raと初期長ya、別設定ye/yfを保持する。方法eip2/eip6、現在の二原理eion/eiot、同じ著者rd・論説eirfと後続範囲ziへ照応する。',
 'nennen wollenは呼称の採用意向の表明、mußは原理に基づく必要性の帰属、werden wir bestimmen und findenは後続の値決定と不一致の予告として保持する。現在の測定結果や完了した導出へ変えない。',
 '方法aの比較を方法bとの直接比較へ替えず、方法bの不一致へ収縮方向・率を追加しない。命名意向を義務や他者の同意へ替えず、予告先を原文にない特定段落の明示引用としない。',
 'zb/zc/zd、sce、sbx/sby/sbz、sca/scbと現行方法・幾何を再利用する。追加のeisl7は二呼称に共通の命名意向の関係で、原文の一文を原始関係に埋め込まない。定冠詞の存在・数値的一意性の読みを明示する。',
 '原刊画像・MathML・固定原文と先の方法・原理の証拠を保存する。有限の論理骨格、実切断の候補、幾何への結合と引用の非実行の検査は、全実数の唯一性・物理的真理・導出の証明と区別する。',
 '前の二方法、後の通常運動学の暗黙の仮定、後続の形状比較に照らして二文を通読した。命名意向、必要性の帰属、二原理に基づく決定・不一致の予告という読みで欠落はないと判断する。後続の論証は未完である。',
)


def prose(s):return sum(not c.isspace() for c in re.sub(r'\[M\d+\]','',s))


def source_record():
    inv=json.loads(read(INVENTORY));units=inv['units'][31:33]
    assert [len(u['text']) for u in units]==[195,239] and [prose(u['text']) for u in units]==[158,197]
    maths=[next(m for m in inv['math'] if m['id']==n) for n in ('M0049','M0050')]
    assert all(''.join(ET.fromstring(m['mathml']).itertext())=='l' for m in maths)
    receipt='artifacts/einstein-rod-methods-v1/retrieval.json'
    paths={INVENTORY,DOC,'scripts/review_rod_length_claims.py',receipt}
    for row in json.loads(read(receipt))['sources']:
        assert digest((ROOT/row['path']).read_bytes())==row['sha256'];paths.add(row['path'])
    assert digest((ROOT/'artifacts/einstein-rod-methods-v1/page-896.jpg').read_bytes())=='62f25cc4a43dce692fe34e00673499c572f3533564e5d84790463ea53d687912'
    return dict(version='einstein-rod-length-claims-source-reading-v1',reviewer='assistant_visual_and_text_review',pages=['896'],images=['artifacts/einstein-rod-methods-v1/page-896.jpg'],segments=[dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[0,len(u['text'])],text=u['text'],nonblank_characters=prose(u['text']),math=[dict(id=m['id'],sha256=m['sha256'],printed='l',binding='ya; initial rest length from u0029')]) for u,m in zip(units,maths)],observations=['u0032のmußはnach dem Relativitätsprinzipに結び付く。','両方のnennen wollenを採用意向として保ち、u0033のbewegtenは括弧内にある。','u0033はwerden wir bestimmen und findenという将来の論述の予告である。'],later_context=dict(scope='zi: subsequent reasoning in this paper after zh, not one explicitly cited paragraph',units=[dict(unit=u['id'],unit_sha256=u['text_sha256']) for u in inv['units'][109:116]],completed_here=False),semantic_completion=False,source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})


@lru_cache(None)
def record(i):
    catalog=load_catalog(ROOT,BASIS);u=json.loads(read(INVENTORY))['units'][31+i];assert json.loads(read(SOURCE))==source_record()
    paths={FULL,CORE,BASIS,ANNOTATIONS,INVENTORY,SOURCE,REPORT,DOC,*PRIORS,*DEPENDENCIES,'scripts/review_rod_length_claims.py','tests/test_rod_length_claims_review.py'}
    pins={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)};merge_pins(pins,catalog.source_sha256)
    for p in (SOURCE,REPORT,*DEPENDENCIES):
        rec=json.loads(read(p));validate_hashes(ROOT,rec['source_sha256']);merge_pins(pins,rec['source_sha256'])
    return dict(schema_version='noema-semantic-review-1',work='einstein-1905',unit=u['id'],reviewer='assistant_review',decision='equivalent_under_stated_reading',document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source=dict(inventory=INVENTORY,unit_sha256=u['text_sha256'],text=u['text'],range=[0,len(u['text'])],math=[{k:m[k] for k in ('id','sha256')} for m in source_record()['segments'][i]['math']]),selection=selection_binding(catalog,[INDICES[i]]),source_order_statements=[INDICES[i]],interpretation=LIMITS,limits=['明示した解釈の下のアシスタントによる通読判断。独立査読や同義性の自動証明ではない。','u0034以降と予告された後続論証・二作品全体の目標は未完。'],unresolved=[],requirements=[dict(id=k,decision='satisfied',reason=v) for k,v in zip(REQUIREMENTS,REASONS)],evidence=dict(source_reading=[SOURCE],formal_checks=[REPORT,*DEPENDENCIES],semantic_reading=[DOC]),source_sha256=pins)


def prepare():
    from scripts.audit_opening_scope import write_exact
    for i,path in enumerate(REVIEWS):write_exact(ROOT/path,json.dumps(record(i),ensure_ascii=False,indent=2)+'\n')


def build_report():
    pins={};active=dict(document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source_inventory=INVENTORY)
    for i,path in enumerate(REVIEWS):
        rec=record(i);assert json.loads(read(path))==rec
        validate_review(ROOT,path,'einstein-1905',active,load_catalog(ROOT,BASIS),json.loads(read(INVENTORY)))
        merge_pins(pins,rec['source_sha256']);pins[path]=digest((ROOT/path).read_bytes())
    return dict(status='length_naming_necessity_and_future_determination_whole_units_reviewed',document=FULL,source_units={'einstein-1905:u0032':158,'einstein-1905:u0033':197},whole_units_semantically_verified=True,verified_full_units={'kant-1784':0,'einstein-1905':2},semantic_equivalence_automatically_proved=False,source_sha256=pins)
