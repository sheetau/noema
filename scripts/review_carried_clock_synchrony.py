"""Read the added carried clocks, local time gloss and qualified synchrony name."""
from functools import lru_cache
import json,re
from xml.etree import ElementTree as ET
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import REQUIREMENTS,digest,selection_binding,validate_hashes,validate_review
from noema.review_registry import merge_pins
from scripts.compose_carried_clock_synchrony import ROOT,read,FULL,CORE,BASIS,ANNOTATIONS,INDICES,LIMITS

INVENTORY='artifacts/written-units-v1/einstein-1905.json';DOC='docs/carried-clock-synchrony-v1.md'
SOURCE='data/einstein-carried-clock-synchrony-source-reading-v1.json';REPORT='reports/carried-clock-synchrony-v1.json'
REVIEW='data/einstein-carried-clock-synchrony-review-v1.json'
PRIORS=('data/einstein-kinematic-replacement-review-v1.json','data/einstein-synchronized-endpoints-method-review-v1.json')
DEPENDENCIES=('reports/rod-methods-v1.json','reports/event-time-summary-v1.json','reports/rest-system-time-v1.json')
REASONS=(
 '固定u0035全321文字・257本文文字とM0052/M0053のA/Bを原刊896頁に照合した。二端への取り付け、局所時刻との一致、その説明と静止系における同期の呼称を保持する。',
 '動く時計の取り付けと全区間の位置を同じ端点のseへ結び、同じ出来事の両表示・場所・局所時計・値をscv/eing/eisgm/sbへ接続する。全実時刻の照合記録の存在と全記録への条件を保つ。',
 '同じ棒xi・二端xn/xo・別々の時計zaj/zak、静止系ra・単位ta/rb・同じ参照rcを保つ。A/Bの呼称と端点の対応をeisd4で結び、第一節の時間規約eisjdとeingを保持する。',
 'Wir denken uns fernerは先の棒設定への追加の想定ug/zao、d. h.は同じ時計の同期の言い方の説明eisme、alsoは条件から呼称適用への理由eisdkとして保持する。想定の実現や測定済みへ変えない。',
 '動く時計自体へ静止系のccやrcとの直接qoを課さない。局所時計と場所の変更を許し、自然な固有時進行・補正機構・共動観測者の判定や後の光往復式は追加しない。',
 '時計の物理的取り付け、代表位置の全時間履歴、現在位置、局所的な表示の一致を分ける。既存の時計・世界線・同期・時刻の意味規約を再利用し、全時間の対応を有限標本の一致にしない。',
 '原刊画像、固定原文・MathML、既存の端点測定と第一節の時刻規約の証拠を保存する。局所条件と記録の結合・有限の量化骨格・引用の検査を、全実数や物理的実現・同義性の自動証明と区別する。',
 '直前の二操作と通常の運動学の仮定、直後の共動観測者と光往復に照らして通読した。静止系時刻に表示を合わせた棒端時計を追加する想定と、その説明・呼称という読みで欠落はないと判断する。u0036以降は残る。',
)


def source_record():
    inv=json.loads(read(INVENTORY));u=inv['units'][34]
    count=sum(not c.isspace() for c in re.sub(r'\[M\d+\]','',u['text']))
    assert u['id']=='einstein-1905:u0035' and len(u['text'])==321 and count==257
    maths=[next(m for m in inv['math'] if m['id']==n) for n in ('M0052','M0053')]
    assert [''.join(ET.fromstring(m['mathml']).itertext()) for m in maths]==['A','B']
    receipt='artifacts/einstein-rod-methods-v1/retrieval.json';paths={INVENTORY,DOC,'scripts/review_carried_clock_synchrony.py',receipt}
    for row in json.loads(read(receipt))['sources']:
        assert digest((ROOT/row['path']).read_bytes())==row['sha256'];paths.add(row['path'])
    assert digest((ROOT/'artifacts/einstein-rod-methods-v1/page-896.jpg').read_bytes())=='62f25cc4a43dce692fe34e00673499c572f3533564e5d84790463ea53d687912'
    return dict(version='einstein-carried-clock-synchrony-source-reading-v1',reviewer='assistant_visual_and_text_review',pages=['896'],images=['artifacts/einstein-rod-methods-v1/page-896.jpg'],segments=[dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[0,len(u['text'])],text=u['text'],nonblank_characters=count,math=[dict(id=m['id'],sha256=m['sha256'],printed=form,binding=binding) for m,form,binding in zip(maths,('A','B'),('eismf designates xn','eismg designates xo'))])],observations=['fernerは同じ設定への追加であり、A/Bは括弧内に置かれる。','d. h.の説明は、その時々の現在位置の静止系時刻への一致を述べる。','末尾はalsoを伴う引用された同期の呼称である。'],semantic_completion=False,source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})


@lru_cache(None)
def record():
    catalog=load_catalog(ROOT,BASIS);u=json.loads(read(INVENTORY))['units'][34];assert json.loads(read(SOURCE))==source_record()
    paths={FULL,CORE,BASIS,ANNOTATIONS,INVENTORY,SOURCE,REPORT,DOC,*PRIORS,*DEPENDENCIES,'scripts/review_carried_clock_synchrony.py','tests/test_carried_clock_synchrony_review.py'}
    pins={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)};merge_pins(pins,catalog.source_sha256)
    for p in (SOURCE,REPORT,*DEPENDENCIES):
        rec=json.loads(read(p));validate_hashes(ROOT,rec['source_sha256']);merge_pins(pins,rec['source_sha256'])
    return dict(schema_version='noema-semantic-review-1',work='einstein-1905',unit=u['id'],reviewer='assistant_review',decision='equivalent_under_stated_reading',document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source=dict(inventory=INVENTORY,unit_sha256=u['text_sha256'],text=u['text'],range=[0,len(u['text'])],math=[{k:m[k] for k in ('id','sha256')} for m in source_record()['segments'][0]['math']]),selection=selection_binding(catalog,list(INDICES)),source_order_statements=list(INDICES),interpretation=LIMITS,limits=['明示した解釈の下のアシスタントによる通読判断。独立査読や同義性の自動証明ではない。','u0036以降と二作品全体の目標は未完。'],unresolved=[],requirements=[dict(id=k,decision='satisfied',reason=v) for k,v in zip(REQUIREMENTS,REASONS)],evidence=dict(source_reading=[SOURCE],formal_checks=[REPORT,*DEPENDENCIES],semantic_reading=[DOC]),source_sha256=pins)


def prepare():
    from scripts.audit_opening_scope import write_exact
    write_exact(ROOT/REVIEW,json.dumps(record(),ensure_ascii=False,indent=2)+'\n')


def build_report():
    rec=record();assert json.loads(read(REVIEW))==rec
    active=dict(document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source_inventory=INVENTORY)
    validate_review(ROOT,REVIEW,'einstein-1905',active,load_catalog(ROOT,BASIS),json.loads(read(INVENTORY)))
    return dict(status='carried_clocks_and_local_rest_time_whole_unit_reviewed',document=FULL,source_units={'einstein-1905:u0035':257},whole_units_semantically_verified=True,verified_full_units={'kant-1784':0,'einstein-1905':1},semantic_equivalence_automatically_proved=False,source_sha256=rec['source_sha256']|{REVIEW:digest((ROOT/REVIEW).read_bytes())})
