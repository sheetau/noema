"""Read the first numbered principle with an explicit law-preservation reading."""
from functools import lru_cache
import json
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import REQUIREMENTS,digest,selection_binding,validate_hashes,validate_review
from noema.review_registry import merge_pins
from scripts.compose_first_principle import ROOT,read,FULL,CORE,BASIS,ANNOTATIONS,INDEX,LIMITS

INVENTORY='artifacts/written-units-v1/einstein-1905.json';DOC='docs/first-principle-v1.md'
SOURCE='data/einstein-first-principle-source-reading-v1.json';REPORT='reports/first-principle-v1.json';REVIEW='data/einstein-first-principle-review-v1.json'
PRIORS=('data/einstein-two-principle-introduction-review-v1.json','data/einstein-principles-paragraph-review-v1.json')
REASONS=(
 '固定u0025全255文字・226本文文字を原刊895頁の番号1からbezogen werdenまで照合した。数式・脚注はなく、物理系、状態変化、二座標系、相対的等速並進、独立性を含める。',
 '同じ全物理法則が両系で成立し、同じ物理系の全候補履歴の全対応記述で適合が保存されるというeiomを、等速並進する全系対へeionで要求する。各側の記述存在と全範囲を保持する。',
 'diese Zustandsänderungenは同じ候補履歴を指し、どちらの座標系でも同じ法則と物理系を保つ。原理の参照は先の相対性原理に結ぶが、その先行内容を今回の定式化へ無条件に代入しない。',
 '導入wuの第一項としてvkで原理の定義を提示するvl、著者・論説への帰属、表示番号1と本文順序を保持する。処理系自身の実証済み主張へ替えない。',
 '観測履歴だけの一致、座標値や式の字面の一致、全候補の適合、同じ系自身だけの比較を代用しない。軸一致・特定方向・絶対静止・二系の共通時刻・特定変換式は補わない。',
 '全配置点の同じ速度ベクトルによる変位で相対的等速並進を構成する。物理系の状態・量と範囲、同じ法則としての成立、候補記述の適合を分け、旧vb/vc/vgだけへ意味を委ねない。',
 '原刊と意味規約の通読、数値核、全点・全時点の接続、全法則・全候補・両側記述、同じ理論の全系対、定義提示の検査を保存する。有限配置を全連続時間や全物理法則の証明へ替えない。',
 '番号1の定義を一文全体として通読し、明示した外延的保存と各系での法則成立の読みの下で欠落はないと判断する。原理の論理的導出・実証や後続第二原理の全単位判断は含めない。',
)


def source_record():
    u=json.loads(read(INVENTORY))['units'][24];assert len(u['text'])==255 and sum(not c.isspace() for c in u['text'])==226 and not u['math_ids']
    paths=[INVENTORY,DOC,'scripts/review_first_principle.py','artifacts/einstein-rest-time-v1/page-895.jpg','artifacts/einstein-rest-time-v1/page-895.html','artifacts/einstein-rest-time-v1/retrieval.json']
    assert digest((ROOT/paths[3]).read_bytes())=='d6d76216b027b8121b3d2822e93e9293b1afafd86fdf222a7dca39a23ea78289'
    return dict(version='einstein-first-principle-source-reading-v1',reviewer='assistant_visual_and_text_review',pages=['895'],images=[paths[3]],segments=[dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[0,len(u['text'])],text=u['text'],nonblank_characters=226,math=[])],observations=['二原理への導入直後の番号1である。relativ zueinander、gleichförmiger Translationsbewegung、auf welches von zwei、diese Zustandsänderungenの係りを保持する。','原刊の行末分綴は固定転記の一語として読む。番号は原理の列挙であり物理量ではない。'],semantic_completion=False,source_sha256={p:digest((ROOT/p).read_bytes()) for p in paths})


@lru_cache(None)
def record():
    catalog=load_catalog(ROOT,BASIS);u=json.loads(read(INVENTORY))['units'][24];assert json.loads(read(SOURCE))==source_record()
    paths={FULL,CORE,BASIS,ANNOTATIONS,INVENTORY,SOURCE,REPORT,DOC,*PRIORS,'scripts/review_first_principle.py','tests/test_first_principle_review.py'}
    pins={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)};merge_pins(pins,catalog.source_sha256)
    for p in (SOURCE,REPORT):
        rec=json.loads(read(p));validate_hashes(ROOT,rec['source_sha256']);merge_pins(pins,rec['source_sha256'])
    return dict(schema_version='noema-semantic-review-1',work='einstein-1905',unit=u['id'],reviewer='assistant_review',decision='equivalent_under_stated_reading',document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source=dict(inventory=INVENTORY,unit_sha256=u['text_sha256'],text=u['text'],range=[0,len(u['text'])],math=[]),selection=selection_binding(catalog,[INDEX]),source_order_statements=[INDEX],interpretation=LIMITS,limits=['明示した解釈に基づくアシスタントの通読判断。独立査読、唯一の歴史的解釈、同義性の自動証明ではない。','u0026以降と二作品全体の目標は未完。'],unresolved=[],requirements=[dict(id=k,decision='satisfied',reason=v) for k,v in zip(REQUIREMENTS,REASONS)],evidence=dict(source_reading=[SOURCE],formal_checks=[REPORT],semantic_reading=[DOC]),source_sha256=pins)


def prepare():
    from scripts.audit_opening_scope import write_exact
    write_exact(ROOT/REVIEW,json.dumps(record(),ensure_ascii=False,indent=2)+'\n')


@lru_cache(None)
def build_report():
    rec=record();assert json.loads(read(REVIEW))==rec
    result=validate_review(ROOT,REVIEW,'einstein-1905',dict(document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source_inventory=INVENTORY),load_catalog(ROOT,BASIS),json.loads(read(INVENTORY)))
    assert result['source_nonblank_characters']==226
    return dict(status='first_principle_whole_unit_reviewed',document=FULL,source_units={'einstein-1905:u0025':226},whole_units_semantically_verified=True,verified_full_units={'kant-1784':0,'einstein-1905':1},semantic_equivalence_automatically_proved=False,source_sha256=rec['source_sha256']|{REVIEW:digest((ROOT/REVIEW).read_bytes())})
