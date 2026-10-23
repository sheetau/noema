"""Pin the holistic four-sentence reading of Einstein's principles paragraph."""
from functools import lru_cache
import json
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import REQUIREMENTS,digest,selection_binding,validate_hashes,validate_review
from noema.review_registry import merge_pins
from scripts.compose_ether_dispensability import ROOT,read,FULL,CORE,BASIS,ANNOTATIONS

INVENTORY='artifacts/written-units-v1/einstein-1905.json';SOURCE='data/einstein-principles-source-reading-v1.json'
DOC='docs/einstein-principles-paragraph-v1.md';REVIEW='data/einstein-principles-paragraph-review-v1.json'
STEMS=('relativity-conjecture','two-postulates','sufficient-postulates','ether-dispensability')
READINGS=tuple('data/'+n+'-reading-v1.json' for n in STEMS)
REPORTS=tuple('reports/'+n+'-v1.json' for n in STEMS)+('reports/vacuum-light-postulate-v1.json',)
SPANS=((0,522),(523,889),(890,1081),(1082,1425));ORDER=(213,214,215,216)
REASONS=(
 '固定u0004全1425文字・1244非空白文字を原刊891–892頁の照合記録と四文の範囲で確認した。文間空白三文字以外を重複なく覆う。M0001の大文字Vをtcへ結び、A0002は頁境界として区別する。',
 '類似例と検出試行の失敗から推測へ進む根拠、絶対静止への対応特性の否定、全適格系の共通法則、一次までの既証、二仮定の採用意思・命名・見かけ上のみの不整合、共通光速度、二前提の十分性、光エーテル導入の不要性という限定付き予告を保持する。',
 'diese Vermutungとderen Inhaltとmit ihmは同じeifjへ、Diese beiden Voraussetzungenはeifj/eifyへ結ぶ。第三文の同じ方法・基礎・到達先を束ね、第四文の開発予定の見解を同じ構成eigjへ結ぶ。Lichtätherは先行Lichtmediumと同じ対象と読み、関係節は真空空間を修飾すると明記した。',
 '四文の主張を同じ著者・論説へ帰属する。推測の認識的位置付け、採用への意思、後続本文での命名、追加と挿入、見かけの留保、十分性、将来の成立予告とその限りでという理由を分け、本文順序を保持する。引用する物理内容を帰属時に実行しない。',
 '推測や仮定を現在の実証へ昇格させず、一次までの既証を全次数へ広げない。光速度へ数値・物質媒体・加速座標系を補わず、二前提の必要性・最小性・導出完了も加えない。静止物体を静的電磁場へ替えず、光エーテル不要を実在否定へ、空間点の速度不付与を物体の運動否定へ広げない。',
 '物理的対象と法則、全適格系・全区間・全光源運動状態、局所時刻と速度、推測と意思、呼称と後続範囲、両立性と見かけ、構成方法と基礎・単純さ・無矛盾、理論的導入と空間点・速度量・不要性・予告の意味規約を再読した。原語の綴りや文単位の名札で内容を代用していない。',
 '四文の判断記録と局所検査、光速度の依存群、原刊照合、現行本文と全依存定義・意味規約を固定した。既存の表題・著者表示・第一段落の選択は不変である。有限の引数・量化・構成例を物理的実証、全実数の列挙、全帰結の決定手続き、同義性の自動証明へ昇格させない。',
 '一般の根拠から同じ推測、二仮定の導入と名称、同じ二前提による理論構成の十分性、これからの見解での二否定と光媒体不要の予告へ進む四文を通読した。各文の明示した解釈を共有する段落として、未処理の内容・条件・留保・照応・提示はないと判断する。後続の運動学を論じる段落は範囲外である。',
)

def calls(node):
    if isinstance(node,dict):
        if node.get('kind')=='call':yield node
        for x in node.values():yield from calls(x)
    elif isinstance(node,list):
        for x in node:yield from calls(x)

@lru_cache(None)
def review_record():
    catalog=load_catalog(ROOT,BASIS);inventory=json.loads(read(INVENTORY));unit=inventory['units'][3]
    assert unit['id']=='einstein-1905:u0004'
    readings=[json.loads(read(p)) for p in READINGS];positions=set()
    for r,span,index in zip(readings,SPANS,ORDER):
        assert r['status']=='sentence_content_and_presentation_checked_under_explicit_reading'
        assert r['source_text_sha256']==unit['text_sha256'] and r['range']==list(span) and r['source']==unit['text'][span[0]:span[1]]
        assert r['selection']==selection_binding(catalog,[index])
        assert not positions.intersection(range(*span));positions.update(range(*span))
    assert all(i in positions or ch.isspace() for i,ch in enumerate(unit['text']))
    assert len(unit['text'])==1425 and sum(not ch.isspace() for ch in unit['text'])==sum(r['source_nonblank_characters'] for r in readings)==1244
    assert unit['math_ids']==['M0001']
    math=[dict(id=m['id'],sha256=m['sha256']) for m in inventory['math'] if m['id'] in unit['math_ids']]
    assert math==[dict(id='M0001',sha256='fad146c158bc7dc725209b362adcee4dfb08d7da13a15bf61ab90897102da806')]
    ds={d['name']:d for d in catalog.document['declarations']}
    for name in ('eifs','eigb','eigk','eigu'):assert ds[name]['body']['kind']=='message' and ds[name]['body']['force']=='assert'
    def quoted_call(parent,callee,slot,target):
        cs=[c for c in calls(ds[parent]['body']) if c['symbol']==callee]
        assert len(cs)==1 and cs[0]['arguments'][slot]==dict(kind='quote',body=dict(kind='call',symbol=target,arguments=[]))
    quoted_call('eifz','ug',2,'eifj');quoted_call('eif2','ug',2,'eify')
    quoted_call('eif4','eisch',1,'eifj');quoted_call('eigi','eigh',1,'eifj');quoted_call('eigi','eigh',2,'eify')
    quoted_call('eigt','eiscv',2,'eigj')
    for parent,first,last in (('eigc','eisb4','eiscl'),('eigl','eiscl','eiscu'),('eigv','eiscu','eisdc')):
        order=next(c for c in calls(ds[parent]['body']) if c['symbol']=='ue')
        assert [a['symbol'] for a in order['arguments']]==[first,last,'ri']
    speed=next(c for c in calls(ds['eify']['body']) if c['symbol']=='eifx')
    assert speed['arguments'][1]==dict(kind='call',symbol='tc',arguments=[])
    for p,indices in (('data/electrodynamics-title-review-v1.json',[212]),('data/einstein-author-credit-review-v1.json',[206]),('data/einstein-opening-paragraph-review-v1.json',[207,208,209,210,211])):
        assert selection_binding(catalog,indices)==json.loads(read(p))['selection']
    evidence=dict(source_reading=[SOURCE,*READINGS],formal_checks=list(REPORTS),semantic_reading=[DOC,*('docs/'+n+'-v1.md' for n in STEMS)])
    paths={FULL,CORE,BASIS,ANNOTATIONS,INVENTORY,'scripts/check_einstein_principles_paragraph.py','tests/test_einstein_principles_paragraph.py',*(p for xs in evidence.values() for p in xs)}
    pins={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)};merge_pins(pins,catalog.source_sha256)
    for paths in evidence.values():
        for p in paths:
            if p.endswith('.json'):
                record=json.loads(read(p));validate_hashes(ROOT,record['source_sha256']);merge_pins(pins,record['source_sha256'])
    return dict(schema_version='noema-semantic-review-1',work='einstein-1905',unit=unit['id'],reviewer='assistant_review',decision='equivalent_under_stated_reading',document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,
        source=dict(inventory=INVENTORY,unit_sha256=unit['text_sha256'],text=unit['text'],range=[0,len(unit['text'])],math=math),selection=selection_binding(catalog,list(ORDER)),source_order_statements=list(ORDER),
        interpretation=[v for r in readings for v in r['interpretation_limits']]+['四文を同じ推測・二仮定・構成課題の下で読む。旧文別記録の後続未完という記述は過去の進捗であり、本段落の今回の未解決点ではない。'],
        limits=['明示した物理的・認識的・談話的な規約に基づくアシスタントの判断。歴史的な全ての読み、独立査読、自然言語との同義性の自動証明、物理法則の実証を主張しない。','この段落より後の全単位記述は未完で、二作品全体の目標は継続する。'],unresolved=[],requirements=[dict(id=k,decision='satisfied',reason=v) for k,v in zip(REQUIREMENTS,REASONS)],evidence=evidence,source_sha256=pins)

def prepare():
    from scripts.audit_opening_scope import write_exact
    write_exact(ROOT/REVIEW,json.dumps(review_record(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    assert json.loads(read(REVIEW))==review_record()
    active=dict(document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source_inventory=INVENTORY)
    verified=validate_review(ROOT,REVIEW,'einstein-1905',active,load_catalog(ROOT,BASIS),json.loads(read(INVENTORY)))
    return dict(status='einstein_principles_paragraph_holistically_reviewed_under_explicit_reading',document=FULL,source_unit='einstein-1905:u0004',sentence_ranges=SPANS,source_order_statements=ORDER,source_nonblank_characters=verified['source_nonblank_characters'],preserved_prior_reviews=True,whole_unit_semantically_verified=True,verified_full_units={'kant-1784':0,'einstein-1905':1},semantic_equivalence_automatically_proved=False,source_sha256=review_record()['source_sha256']|{REVIEW:digest((ROOT/REVIEW).read_bytes())})
