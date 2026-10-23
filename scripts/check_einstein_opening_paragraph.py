"""Pin a holistic five-sentence review to the completed opening paragraph."""
from functools import lru_cache
import json
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import REQUIREMENTS,digest,selection_binding,validate_hashes,validate_review
from noema.review_registry import merge_pins
from scripts.compose_apparent_asymmetry import ROOT,read,FULL,CORE,BASIS,ANNOTATIONS

INVENTORY='artifacts/written-units-v1/einstein-1905.json';SOURCE='data/einstein-opening-source-reading-v1.json'
DOC='docs/einstein-opening-paragraph-v1.md';REVIEW='data/einstein-opening-paragraph-review-v1.json'
STEMS=('apparent-asymmetry','interaction-example','observable-contrast','moving-magnet-case','moving-conductor-case')
READINGS=tuple('data/'+n+'-reading-v1.json' for n in STEMS);REPORTS=tuple('reports/'+n+'-v1.json' for n in STEMS)
SPANS=((0,209),(210,307),(308,549),(550,770),(771,1203));ORDER=(211,207,208,209,210)
REASONS=(
 '固定u0003全1203文字・1023非空白文字を、原刊891頁の照合記録と五文の範囲で確認した。文間空白四文字以外を重複なく覆い、数式対象はない。',
 '通常の理論理解と一般適用の説明上の区別、現象には属さないように見えるという留保と周知性、例を考える指示、観測現象の相対運動への依存と説明規則の対照、二場合の場・駆動・エネルギー・電流生成と条件付き履歴一致を保持する。',
 '同じ著者・論説・提示文脈、同じ通常の理解、例での磁石・導体・結合設定、各場合の系と状況・源の場・単位・物質点・断面・時刻対応を照合した。welche、welches、welcher、dieおよびwie im ersten Falleは各説明の同じ区別・場・駆動・生成へつながる。',
 '第二文の指示と他四文の主張、第一文の挿入補足と周知性、例示、第三文の対照、第四文のnämlich、第五文の三つの対照と挿入留保、本文順序を保持する。通常の理解への帰属と著者の最終見解を混同せず、発話帰属から物理内容を実行しない。',
 '実験の実施、原文にない特定の数値や単位系、全適用での非対称性、見かけから現実の差の不存在、機能的依存の逆含意、エネルギーの時間一定性、起電力の機械力との同一視、駆動自体のエネルギーなしから仕事不要という帰結を追加しない。比較の留保を第二の場合全体へ移していない。',
 '理論と解釈、物体と運動、磁石・導体、源に帰属する場・力と結合、観測可能な電流、周囲・電場とエネルギー、局所駆動とその物理的生成、見かけと周知性、発話・例示・対照の意味規約を再読した。原語の綴りや名札だけを残余の説明として用いていない。',
 '五文の判断記録と局所検査、原刊照合、本文・依存定義・意味規約を固定した。既存著者表示の選択も不変である。数値・有限候補・引数接続・量化構造の検査を全実数の証明や原文との自動同義証明へ昇格させない。',
 '一般的な論点から同じ例への呼びかけ、現象と通常の説明の対照、その二説明、最後の電流比較へ進む五文を通読した。各文の明示解釈を共有した段落として、未処理の内容・条件・留保・照応・提示はないと判断する。表題と後続単位はこの判断の範囲外である。',
)

@lru_cache(None)
def review_record():
    catalog=load_catalog(ROOT,BASIS);inventory=json.loads(read(INVENTORY));unit=next(u for u in inventory['units'] if u['id']=='einstein-1905:u0003')
    readings=[json.loads(read(p)) for p in READINGS];positions=set()
    for r,span,index in zip(readings,SPANS,ORDER):
        assert r['status']=='sentence_content_and_presentation_checked_under_explicit_reading'
        assert r['source_text_sha256']==unit['text_sha256'] and r['range']==list(span) and r['source']==unit['text'][span[0]:span[1]]
        assert r['selection']==selection_binding(catalog,[index])
        assert not positions.intersection(range(*span));positions.update(range(*span))
    assert all(i in positions or ch.isspace() for i,ch in enumerate(unit['text']))
    assert len(unit['text'])==1203 and sum(not ch.isspace() for ch in unit['text'])==sum(r['source_nonblank_characters'] for r in readings)==1023
    assert not unit.get('math_ids',[])
    # Explicit source order, message force and shared discourse identities.
    ds={d['name']:d for d in catalog.document['declarations']}
    for name,force in (('eie3','assert'),('eic6','direct'),('eidk','assert'),('eidx','assert'),('eiel','assert')):
        assert ds[name]['body']['kind']=='message' and ds[name]['body']['force']==force,(name,force)
    author=json.loads(read('data/einstein-author-credit-review-v1.json'));assert selection_binding(catalog,[206])==author['selection']
    evidence=dict(source_reading=[SOURCE,*READINGS],formal_checks=list(REPORTS),semantic_reading=[DOC,*('docs/'+n+'-v1.md' for n in STEMS)])
    paths={FULL,CORE,BASIS,ANNOTATIONS,INVENTORY,'scripts/check_einstein_opening_paragraph.py','tests/test_einstein_opening_paragraph.py','data/einstein-author-credit-review-v1.json',*(p for xs in evidence.values() for p in xs)}
    pins={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)};merge_pins(pins,catalog.source_sha256)
    for paths in evidence.values():
        for p in paths:
            if p.endswith('.json'):
                record=json.loads(read(p));validate_hashes(ROOT,record['source_sha256']);merge_pins(pins,record['source_sha256'])
    return dict(schema_version='noema-semantic-review-1',work='einstein-1905',unit=unit['id'],reviewer='assistant_review',decision='equivalent_under_stated_reading',document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,
        source=dict(inventory=INVENTORY,unit_sha256=unit['text_sha256'],text=unit['text'],range=[0,len(unit['text'])],math=[]),selection=selection_binding(catalog,sorted(ORDER)),source_order_statements=list(ORDER),
        interpretation=[v for r in readings for v in r['interpretation_limits']]+['五文を同じ論点と例・通常の理解の下で読む。旧文別記録の後続未完という記述は過去の進捗であり、本段落の今回の未解決点ではない。'],
        limits=['明示した物理的・認識的・談話的な規約に基づくアシスタントの判断。歴史的な全ての読み、独立査読、自然言語との同義性の自動証明、物理法則の実証を主張しない。','表題と後続本文の全単位記述は未完で、二作品全体の目標は継続する。'],unresolved=[],requirements=[dict(id=k,decision='satisfied',reason=v) for k,v in zip(REQUIREMENTS,REASONS)],evidence=evidence,source_sha256=pins)

def prepare():
    from scripts.audit_opening_scope import write_exact
    write_exact(ROOT/REVIEW,json.dumps(review_record(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    assert json.loads(read(REVIEW))==review_record()
    active=dict(document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source_inventory=INVENTORY)
    verified=validate_review(ROOT,REVIEW,'einstein-1905',active,load_catalog(ROOT,BASIS),json.loads(read(INVENTORY)))
    return dict(status='einstein_opening_paragraph_holistically_reviewed_under_explicit_reading',document=FULL,source_unit='einstein-1905:u0003',sentence_ranges=SPANS,source_order_statements=ORDER,source_nonblank_characters=verified['source_nonblank_characters'],preserved_author_review=True,whole_unit_semantically_verified=True,verified_full_units={'kant-1784':0,'einstein-1905':1},semantic_equivalence_automatically_proved=False,source_sha256=review_record()['source_sha256']|{REVIEW:digest((ROOT/REVIEW).read_bytes())})
