"""Collate and review the assumption of consistent synchronization."""
from functools import lru_cache
import json
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import REQUIREMENTS,digest,selection_binding,validate_hashes,validate_review
from noema.review_registry import merge_pins
from scripts.compose_consistent_synchrony import ROOT,read,FULL,CORE,BASIS,ANNOTATIONS,INDEX,LIMITS

INVENTORY='artifacts/written-units-v1/einstein-1905.json';DOC='docs/consistent-synchrony-v1.md'
SOURCE='data/einstein-consistent-synchrony-source-reading-v1.json';READING='data/consistent-synchrony-reading-v1.json'
REPORT='reports/consistent-synchrony-v1.json';REVIEW='data/einstein-consistent-synchrony-review-v1.json'
REASONS=(
 '固定u0015全173文字・149非空白本文文字を原刊894頁のWir nehmen anからBeziehungen gelten:までへ照合した。数式はなく、コロンで次の二項目を導く原文の全範囲を保持する。',
 'この同期定義の無矛盾な実現可能性、個数の上限を置かない全有限点列、同じ配置・状況・時計履歴で全点対の必要試行を満たすこと、一般的な二法則、仮定採用を分けて保持する。点対ごとの別々の実現へ量化順序を弱めない。',
 'diese Definitionを直前eisjsで採用したeimkへ、系と単位をra/rbへ結ぶ。全点対は同じconfigurationとresult、各点の同じ時計写像、各時計・出来事の同じ指示履歴を共有する。後続二関係は既存qp/qqとu0016/u0017の箇所を順序付きで固定する。',
 'Wir nehmen anを著者がeim3を仮定として採用するugへの引用として記述する。alsoの説明は実現可能性eim2から二関係qrへ向け、一般性は全対象への量化に置く。コロンの前方参照と直前の定義からの順序を保持する。',
 'beliebig vieleを二点・三点や固定上限へ縮めず、全有限列に量化する。無限個の同時配置までの強い読みは採らないことを明示する。候補を成功者だけに絞らず、点対ごとの独立な値選択、単独試行、空の試行範囲、実際の同期済みを代用しない。',
 '点の範囲、候補配置、時計写像、時計ごとの許容指示履歴、必要試行の範囲を意味規約付き入力として分離した。全時計対の等時間式・非空性・物理的役割・共有された割当ての成立を合成側で確認し、無矛盾な実現という一文を一つの真偽入力にしない。',
 '原刊照合、文全体の読解、局所検査、前の同期定義と現行本文・依存規約を固定する。有限列の明示例、同じ値を共有する試行、配置候補の取り違え、仮定の非事実性を確認し、全有限列や全実数の直接有限評価は拒否する。物理的存在定理や意味同値を自動証明したとはしない。',
 '直前の同期の定義から、任意個数の地点への無矛盾な実現を仮定し、その下で一般に二関係が成り立つという一文を通読した。明示した有限個数の読みの下で、この単位の内容・参照・量化・提示に未処理項目はないと判断する。次の二項目の印字記号と提示の本文接続は別単位として残る。',
)


def source_record():
    u=json.loads(read(INVENTORY))['units'][14];s=u['text'];assert s.startswith('Wir nehmen an') and s.endswith('Beziehungen gelten:') and not u['math_ids']
    paths=[INVENTORY,'artifacts/einstein-synchrony-continuation-v1/page-894.jpg','artifacts/einstein-synchrony-continuation-v1/page-894.html','artifacts/einstein-synchrony-continuation-v1/retrieval.json','scripts/review_consistent_synchrony.py']
    return dict(version='einstein-consistent-synchrony-source-reading-v1',reviewer='assistant_visual_and_text_review',pages=['894'],images=[paths[1]],segments=[dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[0,len(s)],text=s,nonblank_characters=sum(not c.isspace() for c in s),math=[])],observations=['原刊894頁のWir nehmen anからコロンまでを照合した。widerspruchsfreier Weise möglich、und zwar für beliebig viele Punkte、daß also allgemeinを保持する。','この定義は直前の光往復による同期定義を受ける。コロンの後は第一の対称性と第二の三時計条件であり、一般関係だけを任意個数での実現可能性の全内容としない。'],semantic_completion=False,source_sha256={p:digest((ROOT/p).read_bytes()) for p in paths})


def build_reading():
    u=json.loads(read(INVENTORY))['units'][14];paths=[INVENTORY,DOC,SOURCE,'scripts/review_consistent_synchrony.py']
    return dict(schema_version='noema-sentence-reading-1',status='sentence_content_and_presentation_checked_under_explicit_reading',reviewer='assistant_close_reading',document=FULL,meaning_basis=BASIS,unit=u['id'],range=[0,len(u['text'])],source=u['text'],source_text_sha256=u['text_sha256'],source_nonblank_characters=149,math=[],selection=selection_binding(load_catalog(ROOT,BASIS),[INDEX]),requirements=[dict(requirement=k,judgment='preserved_under_stated_reading',reason=v) for k,v in zip(REQUIREMENTS,REASONS)],interpretation_limits=LIMITS,whole_paragraph_complete=False,verified_full_units=0,semantic_equivalence_automatically_proved=False,remaining=['全単位判断の登録、後続二項目の本文接続'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in paths})


@lru_cache(None)
def review_record():
    catalog=load_catalog(ROOT,BASIS);u=json.loads(read(INVENTORY))['units'][14];reading=json.loads(read(READING));assert reading['selection']==selection_binding(catalog,[INDEX])
    paths={FULL,CORE,BASIS,ANNOTATIONS,INVENTORY,DOC,SOURCE,READING,REPORT,'scripts/review_consistent_synchrony.py','tests/test_consistent_synchrony_review.py'}
    pins={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)};merge_pins(pins,catalog.source_sha256)
    for p in (SOURCE,READING,REPORT):
        rec=json.loads(read(p));validate_hashes(ROOT,rec['source_sha256']);merge_pins(pins,rec['source_sha256'])
    return dict(schema_version='noema-semantic-review-1',work='einstein-1905',unit=u['id'],reviewer='assistant_review',decision='equivalent_under_stated_reading',document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source=dict(inventory=INVENTORY,unit_sha256=u['text_sha256'],text=u['text'],range=[0,len(u['text'])],math=[]),selection=selection_binding(catalog,[INDEX]),source_order_statements=[INDEX],interpretation=LIMITS[:-1],limits=['明示した解釈に基づくアシスタントの通読判断。独立査読・唯一の歴史的解釈・同義性の自動証明・物理的存在の証明ではない。','u0016以降と二作品全体の記述は未完。'],unresolved=[],requirements=[dict(id=k,decision='satisfied',reason=v) for k,v in zip(REQUIREMENTS,REASONS)],evidence=dict(source_reading=[SOURCE],formal_checks=[REPORT],semantic_reading=[DOC]),source_sha256=pins)


def prepare():
    from scripts.audit_opening_scope import write_exact
    write_exact(ROOT/REVIEW,json.dumps(review_record(),ensure_ascii=False,indent=2)+'\n')


def build_report():
    rec=review_record();assert json.loads(read(REVIEW))==rec
    active=dict(document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source_inventory=INVENTORY)
    result=validate_review(ROOT,REVIEW,'einstein-1905',active,load_catalog(ROOT,BASIS),json.loads(read(INVENTORY)))
    assert result['source_nonblank_characters']==149
    return dict(status='consistent_synchrony_assumption_whole_unit_reviewed',document=FULL,source_units={'einstein-1905:u0015':149},whole_units_semantically_verified=True,verified_full_units={'kant-1784':0,'einstein-1905':1},semantic_equivalence_automatically_proved=False,source_sha256=rec['source_sha256']|{REVIEW:digest((ROOT/REVIEW).read_bytes())})
