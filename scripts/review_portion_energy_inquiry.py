"""Close the entire persistent-enclosure and energy-question continuation unit."""
from functools import lru_cache
import json,re
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import REQUIREMENTS,digest,selection_binding,validate_hashes,validate_review
from noema.review_registry import merge_pins
from scripts.compose_portion_energy_inquiry import ROOT,read,FULL,CORE,BASIS,ANNOTATIONS,LIMITS,MEANINGS,INDEX
from scripts.read_portion_energy_inquiry import INVENTORY,SOURCE,DOC,READING,PRIOR

REPORT='reports/portion-energy-inquiry-v1.json';REVIEW='data/einstein-portion-energy-inquiry-u0205-review-v1.json'
PREVIOUS_REPORT='reports/same-light-portion-v1.json';PREVIOUS_DOC='docs/same-light-portion-v1.md'

@lru_cache(None)
def record():
    catalog=load_catalog(ROOT,BASIS);inv=json.loads(read(INVENTORY));u=inv['units'][204];text=u['text'];math={m['id']:m for m in inv['math']}
    paths={FULL,CORE,BASIS,ANNOTATIONS,INVENTORY,SOURCE,DOC,READING,REPORT,PRIOR,PREVIOUS_DOC,PREVIOUS_REPORT,'scripts/review_portion_energy_inquiry.py','tests/test_portion_energy_inquiry_review.py'}
    pins={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)};merge_pins(pins,catalog.source_sha256)
    for p in (REPORT,READING,SOURCE,PRIOR,PREVIOUS_REPORT):
        evidence=json.loads(read(p));validate_hashes(ROOT,evidence['source_sha256']);merge_pins(pins,evidence['source_sha256'])
    first=json.loads(read(PRIOR));second=json.loads(read(READING))
    clauses=[dict(range=r['range'],text=r['source'],statements=[i],definitions=r['definitions'],reason=r['requirements'][-1]['reason']) for r,i in [(first,388),(second,INDEX)]]
    reasons=[
      '原刊913頁で、前のu0203末尾とu0204球面式からu0205末尾までを通読した。全272文字の範囲、221非空白本文文字とM0356/M0357を固定し、セミコロンとd.h.の内部の点による誤分割を避ける。',
      '前半は同じ動く球面の局所無流出入、同じ初期部分の一対一な位置対応と密度持続、永久の囲い込みという記述可能性を保持する。後半は同じ部分の新系同時断面の位相平均密度を空間積分した総量を尋ねる。総量・密度・瞬間値・平均を区別する。',
      'diese FlächeとLichtkomplexは前の同じ球面・部分を受ける。二つのkは同じzbm。質問の68役割を候補の外側で固定し、候補ごとに波・単位・対象・系を存在選択しない。newenergyという既知答えを条件に含めない。',
      'wir können daher sagenの記述可能性と帰結提示、Wir fragenの質問提示、d.h.の同じ問いの説明をそれぞれ保つ。問いの後半を別行為として追加せず、質問提示を答えの主張又は解の存在の断言にしない。',
      '全時刻の理想平面波モデルと初期部分の連続体輸送、先行と同じ位相平均エネルギー、後続τ=0の同時断面という読みを明示する。微視的な交換履歴の識別、実測済み、既知の答え、後続の比の導出済みを追加しない。',
      '領域・位置対応・密度・流・平均・積分と物理的な単位及び部分割当を既存規約へ合成する。eistsは同じ型の規則を共有する質問族の一般提示関係であり光又はこの文の意味を格納する原始関係ではない。説明eismeと後方参照eisraを再利用する。',
      '前半の保存済み1155対照と今回の設定分離・68役割・積分候補・空単一複数の質問・引用非実行・説明の向きの検査を根拠として別々に保存する。検査通過を全実数の物理的真理又は意味同義性の自動証明へ変えない。',
      '前の方向余弦・球面式から永久の囲い込み、そして新系に相対的な同じ部分のエネルギーを問う言換えまで再読した。明示した連続体と位相平均・同時断面の読みの下でu0205の内容・参照・条件・提示を欠落なく記述したと判断する。',
    ]
    count=len(re.sub(r'\s','',re.sub(r'\[M\d+\]','',text)));assert count==221
    source=dict(inventory=INVENTORY,unit_sha256=u['text_sha256'],text=text,range=[0,len(text)],math=[dict(id=n,sha256=math[n]['sha256']) for n in u['math_ids']])
    return dict(schema_version='noema-semantic-review-1',work='einstein-1905',unit=u['id'],reviewer='assistant_review',decision='equivalent_under_stated_reading',document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source=source,selection=selection_binding(catalog,[388,INDEX]),clauses=clauses,interpretation=first['interpretation_limits']+LIMITS,limits=['明示した読みの下でのアシスタントによる判断であり、独立査読又は意味同義性の自動証明ではない。','全時刻モデルの物理的な全域妥当性、微視的な粒子の同一性は主張しない。','後続の楕円体の提示・体積と総量の比、二作品全体は未完。'],unresolved=[],requirements=[dict(id=k,decision='satisfied',reason=v) for k,v in zip(REQUIREMENTS,reasons)],evidence=dict(source_reading=[SOURCE,PRIOR,READING],formal_checks=[PREVIOUS_REPORT,REPORT],semantic_reading=[PREVIOUS_DOC,DOC]),reviewed_prose_characters=count,source_sha256=pins)

def prepare():
    from scripts.audit_opening_scope import write_exact
    write_exact(ROOT/REVIEW,json.dumps(record(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    active=dict(document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source_inventory=INVENTORY);catalog=load_catalog(ROOT,BASIS);inv=json.loads(read(INVENTORY));r=record()
    assert json.loads(read(REVIEW))==r
    validate_review(ROOT,REVIEW,'einstein-1905',active,catalog,inv)
    pins=dict(r['source_sha256']);pins[REVIEW]=digest((ROOT/REVIEW).read_bytes())
    return dict(status='persistent_enclosure_and_moving_frame_energy_inquiry_whole_unit_reviewed',document=FULL,source_units={r['unit']:221},reviewed_math_elements=2,whole_units_semantically_verified=True,verified_full_units={'kant-1784':0,'einstein-1905':1},semantic_equivalence_automatically_proved=False,source_sha256=pins)
