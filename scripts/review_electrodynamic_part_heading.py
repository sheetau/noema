"""Record a whole-unit reading of the second part heading."""
from functools import lru_cache
import json
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import REQUIREMENTS,digest,selection_binding,validate_hashes,validate_review
from noema.review_registry import merge_pins
from scripts.compose_electrodynamic_part_heading import ROOT,read,FULL,CORE,BASIS,ANNOTATIONS,INDEX,LIMITS
from scripts.check_electrodynamic_part_heading import DOC,SOURCE,INVENTORY,PRIORS,DEPENDENCIES,source_record

REPORT='reports/electrodynamic-part-heading-v1.json'
REVIEW='data/einstein-electrodynamic-part-u0151-review-v1.json'
REASONS=(
 'u0151全文II. Elektrodynamischer Teil.を原刊907頁で照合した。直前の運動学の総括と応用への移行、直後の§6から独立した部見出しである。ローマ数字II、句点、電気力学を示す形容詞、Teilの部という区分を保持する。',
 'ejsiは、同じ論説に直接属する第二部を既存eihqへ渡し、深さ1・表示番号2と電気力学の主題eie5を合成する。部を表す区分と見出しの箇所を分け、第一部との違いと移行からの本文順序を保持する。',
 '文書eirf、第一部eisdx、直前の移行znjを現在の本文から引き継ぐ。第二部eispbと見出しeispcは区別する。主題は既存eie5に固定し、電荷輸送・電気作用・磁気作用へ接続する。次の第六節の番号や主題を第二部の番号・主題へ代入しない。',
 'eisdv/eisdwの見出しの役割を用い、同じ論説の下位区分を読者へ案内する提示として読む。本文の物理命題を断言する発話、総括の繰り返し、応用課題の達成報告にはしない。中央配置や字体は画像に残し、追加の意味条件へしない。',
 '部番号2と階層深さ1を区別し、下位の節番号が6から続くことを許す。静電気だけ・特定理論だけ・一実験例だけへの縮小、全分野の網羅、本文の定義や導出の完成を追加しない。記事末の謝辞・日付表示や参照位置に付随する注を、物理的な主張へ変換しない。',
 '見出し構造eihqは番号付き区分eisdvと主題案内eisdwへ分解される。電気力学eie5はeisa6と三つの閉じた物理的規約eibf/eibs/eicoを共有する。今回追加した基本記号は区分と箇所への参照だけであり、分野の意味や一文の判定を新しい記号へ隠していない。',
 '部番号・深さ・親文書・主題・順序の欠落と引数の交換、区分・箇所・第一部の同一視、未知入力を対照した。主題の三つの物理的規約も同じ研究対象・文脈へ渡されることを確認した。引用をその場で実行せず、既存本文356主張と前段の意味判断を保持した。',
 '見出し全体を直前・直後とともに再読した。第二部という構造と電気力学という主題を案内する読みの下で、番号・区分・参照・提示を欠落なく記述したと判断する。下位節の内容や物理法則を完成と認定する判断ではない。',
)


@lru_cache(None)
def record():
    catalog=load_catalog(ROOT,BASIS)
    paths={FULL,CORE,BASIS,ANNOTATIONS,SOURCE,REPORT,INVENTORY,DOC,*PRIORS,*DEPENDENCIES,'scripts/review_electrodynamic_part_heading.py','tests/test_electrodynamic_part_heading_review.py'}
    pins={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)};merge_pins(pins,catalog.source_sha256)
    for p in (SOURCE,REPORT,*DEPENDENCIES):
        evidence=json.loads(read(p));validate_hashes(ROOT,evidence['source_sha256']);merge_pins(pins,evidence['source_sha256'])
    s=source_record()['segments'][0];symbols=['ejsi','eihq','eisdv','eisdw','eie5','eisa6','eibf','eibs','eico']
    assert len(REASONS)==len(REQUIREMENTS) and all(n in catalog.entries for n in symbols)
    return dict(schema_version='noema-semantic-review-1',work='einstein-1905',unit=s['unit'],reviewer='assistant_review',decision='equivalent_under_stated_reading',document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source=dict(inventory=INVENTORY,unit_sha256=s['unit_sha256'],text=s['text'],range=s['range'],math=[]),selection=selection_binding(catalog,[INDEX]),source_order_statements=[INDEX],clauses=[dict(range=s['range'],text=s['text'],definitions=symbols,reason=REASONS[1])],interpretation=LIMITS,limits=['原文全体と提示の役割を照合したアシスタントによる判断。独立査読や意味同値の自動証明ではない。','見出しの案内を記述したことから、下位節・注の内容や全物理領域の真理、前段の応用目標の達成を認定しない。','u0152以降と二作品全体の目標は未完。'],unresolved=[],requirements=[dict(id=k,decision='satisfied',reason=v) for k,v in zip(REQUIREMENTS,REASONS)],evidence=dict(source_reading=[SOURCE],formal_checks=[REPORT,*DEPENDENCIES],semantic_reading=[DOC]),reviewed_prose_characters=s['source_nonblank_characters'],source_sha256=pins)


def prepare():
    from scripts.audit_opening_scope import write_exact
    write_exact(ROOT/REVIEW,json.dumps(record(),ensure_ascii=False,indent=2)+'\n')


@lru_cache(None)
def build_report():
    r=record();assert json.loads(read(REVIEW))==r
    active=dict(document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source_inventory=INVENTORY)
    validate_review(ROOT,REVIEW,'einstein-1905',active,load_catalog(ROOT,BASIS),json.loads(read(INVENTORY)))
    pins=r['source_sha256']|{REVIEW:digest((ROOT/REVIEW).read_bytes())}
    return dict(status='second_electrodynamic_part_heading_whole_unit_reviewed',document=FULL,source_units={r['unit']:r['reviewed_prose_characters']},reviewed_math_elements=0,whole_units_semantically_verified=True,verified_full_units={'kant-1784':0,'einstein-1905':1},semantic_equivalence_automatically_proved=False,source_sha256=pins)
