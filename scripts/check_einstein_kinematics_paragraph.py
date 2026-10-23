"""Pin the holistic two-sentence reading of Einstein's kinematic foundation."""
from functools import lru_cache
import json
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import REQUIREMENTS,digest,selection_binding,validate_hashes,validate_review
from noema.review_registry import merge_pins
from scripts.check_einstein_principles_paragraph import calls
from scripts.compose_kinematic_difficulties import ROOT,read,FULL,CORE,BASIS,ANNOTATIONS

INVENTORY='artifacts/written-units-v1/einstein-1905.json';SOURCE='data/einstein-kinematics-source-reading-v1.json'
DOC='docs/einstein-kinematics-paragraph-v1.md';REVIEW='data/einstein-kinematics-paragraph-review-v1.json'
STEMS=('kinematic-foundation','kinematic-difficulties')
READINGS=tuple('data/'+n+'-reading-v1.json' for n in STEMS)
REPORTS=tuple('reports/'+n+'-v1.json' for n in STEMS)+('reports/rigid-body-kinematics-v1.json',)
SPANS=((0,260),(261,423));ORDER=(217,218)
REASONS=(
 '固定u0005全423文字・369非空白文字を原刊892頁の照合記録と二文の範囲で確認した。文間空白一文字以外を重複なく覆う。数式・著者脚注はなく、直後の部・節の見出しは別単位である。',
 'これから展開する理論が剛体の運動学を基礎とすること、他のあらゆる電気力学との比較、各理論の全主張が剛体（座標系）・時計・電磁過程の関係を扱うという理由、同じ事情の不十分な考慮が当時の複数の困難の根であるという説明を保持する。',
 '予定理論を前段落の同じ構成eigjへ結ぶ。各理論は電気力学の文脈で読む。dieses Umstandesを前文の理由内容eihaへ固定し、同じ実践・分野・判断点と同じ全困難を束ねる。座標系という括弧説明を物理的な参照物体の役割として読む。',
 '二文の内容を同じ著者・論説へ主張として帰属する。比較とdaの説明理由を保持し、第二文の基礎的な原因と区別する。否定、複数性、全範囲、論説当時、根と戦うという比喩の読みを明示し、本文順序を保持する。帰属時に物理内容を実行しない。',
 '予定理論の完成、既成の時間規約の全採用、運動学だけでの電磁法則の導出、各式が三対象を明記すること、遠隔時計の同期や実機設置を追加しない。考慮不足を単なる無知へ、根を相関や唯一原因へ、論説当時を現在の読者へ替えない。',
 '全物質点・全実数履歴による剛性、座標参照の役割、時計の校正、電磁過程、全理論と全主張の指示規約、運動学への基礎依存、事情の取扱いと十分性、概念的困難・当時の課題・基礎的原因の意味規約を再読した。説明のない原語や文単位の名札で代用していない。',
 '二文の判断記録と局所検査、剛性の依存群、原刊照合、現行本文と依存する意味規約を固定した。既存の表題・著者表示・導入二段落の判断を保持する。有限の対照例を全理論・全主張・全実数域の列挙、因果関係の歴史的実証、同義性の自動証明へ昇格させない。',
 '物理的な主張の指示内容を理由とする運動学への基礎依存と、その同じ事情の考慮不足を根とする困難の診断を、連続する二文として通読した。明示した解釈の下で内容・条件・範囲・照応・提示の未処理項目はないと判断する。次の見出しと節の本文はこの単位の範囲外である。',
)

@lru_cache(None)
def review_record():
    catalog=load_catalog(ROOT,BASIS);inventory=json.loads(read(INVENTORY));unit=inventory['units'][4]
    assert unit['id']=='einstein-1905:u0005'
    readings=[json.loads(read(p)) for p in READINGS];positions=set()
    for r,span,index in zip(readings,SPANS,ORDER):
        assert r['status']=='sentence_content_and_presentation_checked_under_explicit_reading'
        assert r['source_text_sha256']==unit['text_sha256'] and r['range']==list(span) and r['source']==unit['text'][span[0]:span[1]]
        assert r['selection']==selection_binding(catalog,[index])
        assert not positions.intersection(range(*span));positions.update(range(*span))
    assert all(i in positions or ch.isspace() for i,ch in enumerate(unit['text']))
    assert len(unit['text'])==423 and sum(not ch.isspace() for ch in unit['text'])==sum(r['source_nonblank_characters'] for r in readings)==369
    assert unit['math_ids']==[]
    ds={d['name']:d for d in catalog.document['declarations']}
    for name in ('eihd','eihk'):assert ds[name]['body']['kind']=='message' and ds[name]['body']['force']=='assert'
    def quoted_call(parent,callee,slot,target):
        cs=[c for c in calls(ds[parent]['body']) if c['symbol']==callee]
        assert len(cs)==1 and cs[0]['arguments'][slot]==dict(kind='quote',body=dict(kind='call',symbol=target,arguments=[]))
    quoted_call('eig7','eisdj',2,'eigj')
    quoted_call('eihc','eisdk',1,'eiha');quoted_call('eihc','eisdk',2,'eihb')
    quoted_call('eihf','eisdm',2,'eiha');quoted_call('eihf','eisdn',1,'eiha')
    for name in ('eihc','eihj'):
        body=ds[name]['body'];assert body['kind']=='content'
        assert body['body']['arguments'][0]==dict(kind='evaluate',content=dict(kind='call',symbol='eiha',arguments=[]),situation=dict(kind='variable',name=body['variable']))
    for parent,first,last in (('eihe','eisdc','eisdl'),('eihl','eisdl','eisds')):
        order=next(c for c in calls(ds[parent]['body']) if c['symbol']=='ue')
        assert [a['symbol'] for a in order['arguments']]==[first,last,'ri']
    # Both halves of the diagnosis keep the same closed circumstance and research domain.
    args=next(c for c in calls(ds['eihi']['body']) if c['symbol']=='eihf')['arguments']
    assert next(c for c in calls(ds['eihi']['body']) if c['symbol']=='eihh')['arguments']==args[1:]
    root=next(c for c in calls(ds['eihi']['body']) if c['symbol']=='eisdq')['arguments']
    assert [root[0],root[2],root[3]]==args
    for p,indices in (('data/electrodynamics-title-review-v1.json',[212]),('data/einstein-author-credit-review-v1.json',[206]),('data/einstein-opening-paragraph-review-v1.json',[207,208,209,210,211]),('data/einstein-principles-paragraph-review-v1.json',[213,214,215,216])):
        assert selection_binding(catalog,indices)==json.loads(read(p))['selection']
    evidence=dict(source_reading=[SOURCE,*READINGS],formal_checks=list(REPORTS),semantic_reading=[DOC,*('docs/'+n+'-v1.md' for n in STEMS),'docs/rigid-body-kinematics-v1.md'])
    paths={FULL,CORE,BASIS,ANNOTATIONS,INVENTORY,'scripts/check_einstein_kinematics_paragraph.py','tests/test_einstein_kinematics_paragraph.py','scripts/check_einstein_principles_paragraph.py',*(p for xs in evidence.values() for p in xs)}
    pins={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)};merge_pins(pins,catalog.source_sha256)
    for paths in evidence.values():
        for p in paths:
            if p.endswith('.json'):
                record=json.loads(read(p));validate_hashes(ROOT,record['source_sha256']);merge_pins(pins,record['source_sha256'])
    return dict(schema_version='noema-semantic-review-1',work='einstein-1905',unit=unit['id'],reviewer='assistant_review',decision='equivalent_under_stated_reading',document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,
        source=dict(inventory=INVENTORY,unit_sha256=unit['text_sha256'],text=unit['text'],range=[0,len(unit['text'])],math=[]),selection=selection_binding(catalog,list(ORDER)),source_order_statements=list(ORDER),
        interpretation=[v for r in readings for v in r['interpretation_limits']]+['二文を同じ理論的主張の指示関係の下で読む。過去の文別記録の段落判断未完という記述は過去の進捗であり、本判断の未解決点ではない。'],
        limits=['明示した物理的・認識的・談話的な規約に基づくアシスタントの判断。全ての歴史的解釈、独立査読、自然言語との同義性の自動証明、物理法則や歴史的因果の実証を主張しない。','この段落より後の全単位記述は未完で、二作品全体の目標は継続する。'],unresolved=[],requirements=[dict(id=k,decision='satisfied',reason=v) for k,v in zip(REQUIREMENTS,REASONS)],evidence=evidence,source_sha256=pins)

def prepare():
    from scripts.audit_opening_scope import write_exact
    write_exact(ROOT/REVIEW,json.dumps(review_record(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    assert json.loads(read(REVIEW))==review_record()
    active=dict(document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source_inventory=INVENTORY)
    verified=validate_review(ROOT,REVIEW,'einstein-1905',active,load_catalog(ROOT,BASIS),json.loads(read(INVENTORY)))
    return dict(status='einstein_kinematics_paragraph_holistically_reviewed_under_explicit_reading',document=FULL,source_unit='einstein-1905:u0005',sentence_ranges=SPANS,source_order_statements=ORDER,source_nonblank_characters=verified['source_nonblank_characters'],preserved_prior_reviews=True,whole_unit_semantically_verified=True,verified_full_units={'kant-1784':0,'einstein-1905':1},semantic_equivalence_automatically_proved=False,source_sha256=review_record()['source_sha256']|{REVIEW:digest((ROOT/REVIEW).read_bytes())})
