"""Explicit whole-unit reading of the remaining light-speed proof task."""
from functools import lru_cache
import json
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import REQUIREMENTS,digest,selection_binding,validate_hashes,validate_review
from noema.review_registry import merge_pins
from scripts.compose_light_proof_task import ROOT,read,FULL,CORE,BASIS,ANNOTATIONS,INDEX,LIMITS
from scripts.check_light_proof_task import DOC,SOURCE,INVENTORY,PRIOR,DEPENDENCIES,source_record

REPORT='reports/light-proof-task-v1.json';REVIEW='data/einstein-light-proof-task-u0086-review-v1.json'
CLAUSES=(
 ('Wir haben nun zu beweisen, daß ',['ei7y','zga','zfx'],'同じ著者が現在の論述段階でこれから証明する課題として提示する。'),
 ('jeder Lichtstrahl sich, im bewegten System gemessen, mit der Geschwindigkeit [M0140] fortpflanzt, ',['ei7v','ei43','eifx','eiyf','ei42'],'移動系で測った全適用光区間が同じVを持つことを課題の後件に置く。'),
 ('falls dies, ',['ei7v'],'同じ速度法則の静止系での成立を前件とする条件を保持する。'),
 ('wie wir angenommen haben, ',['ei7x','ug','wu','wv','eify','eisa5','ei7y'],'同じ光速度原理を先行箇所で仮定に採用したことを振り返る挿入補足を課題へ結ぶ。'),
 ('im ruhenden System der Fall ist; ',['ei7v','ei43','ra'],'静止系で測った同じVの全光区間法則を条件の前件に保持する。'),
 ('denn wir haben den Beweis dafür noch nicht geliefert, ',['ei7w','sqi','zfr','ei7y','zgb'],'現在段階まで同じ論説で証明を提示していないことを述べ、それを課題の理由として挙げる。'),
 ('daß das Prinzip der Konstanz der Lichtgeschwindigkeit mit dem Relativitätsprinzip vereinbar sei.',['eif5','eifj','eify','sqh','eiscj','ei7w'],'未提示の証明の対象は同じ二原理の両立性である。共通の許容設定を使う既存の読みを保持する。'),
)
REASONS=(
 '固定u0086全350文字・本文293文字とM0140を原刊900頁末尾から901頁冒頭へ照合した。改頁がim ruhenden Systemの途中にあることを確認し、条件と後続の理由を一文全体として読んだ。',
 '現在の証明課題、全光線、移動系での測定、同じV、静止系の場合という条件、既採用への挿入補足、未提示の時点限界、両立性という証明対象、dennの理由づけを保持する。有限の一光線や単なる数値の式へ縮めない。',
 'K/kとVは先行の同じ系とtcを使う。静止系の原理は同じeifyの系別法則を現在の時計・測定へ結ぶei43で表す。両立性は既出eifj/eifyを一つの許容設定へ結ぶeif5であり、旧部分草案saw/sbdや別内容へ交換しない。',
 'zgaはこれからの証明課題、eisa5は既採用の挿入補足、uhは証明未提示の説明、zgbはその説明を課題の理由とする著者の提示である。ei72は全体を同じ著者・論説へ帰属し、直前の四定数の箇所からの順序を保つ。',
 '課題の提示からその真理や証明完了を導かず、仮定採用から実証を導かない。証明未提示を内容の偽、証明不可能、後段でも未提示へ変えない。探索範囲は現在の第三節だけでなく同じ論説全体とし、同じ段階・著者・対象に限定する。dennの理由を論理的十分性の証明としない。',
 '全区間と同じ速度の現在のei43、条件内容、指定段階までの提示の有無sqi/zfr、一設定での共充足sqh、先行の仮定採用ugと挿入補足、既存の著者帰属を合成する。未説明の文専用原始語を加えず、同じ原理と測定の意味規約を継承する。',
 '原刊両頁・固定本文・構成式を読み、条件の四真偽組、現在の全区間法則までの接続、移動系の未対応区間、同じVと設定、証明候補の全範囲、別対象・著者・段階・範囲、挿入補足と理由の引数を対照した。有限検査は一般の物理的証明や原文との同義性を自動判定しない。',
 '一文全体を直前の四定数と後続の球面波設定に続けて再読した。明示した全真空光区間、先行仮定、共通設定の両立性と現在までの証明提示という読みの下で、内容・条件・留保・提示上の役割を欠落なく記述したと判断する。',
)

@lru_cache(None)
def record():
    catalog=load_catalog(ROOT,BASIS);s=source_record()['segments'][0]
    paths={FULL,CORE,BASIS,ANNOTATIONS,SOURCE,REPORT,INVENTORY,DOC,PRIOR,*DEPENDENCIES,'scripts/review_light_proof_task.py','tests/test_light_proof_task_review.py'}
    pins={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)};merge_pins(pins,catalog.source_sha256)
    for p in (SOURCE,REPORT,*DEPENDENCIES):
        evidence=json.loads(read(p));validate_hashes(ROOT,evidence['source_sha256']);merge_pins(pins,evidence['source_sha256'])
    clauses=[];offset=0
    for text,symbols,reason in CLAUSES:
        assert s['text'][offset:offset+len(text)]==text and all(n in catalog.entries for n in symbols)
        clauses.append(dict(range=[offset,offset+len(text)],text=text,definitions=symbols,reason=reason));offset+=len(text)
    assert offset==len(s['text']) and len(REASONS)==len(REQUIREMENTS)
    return dict(schema_version='noema-semantic-review-1',work='einstein-1905',unit=s['unit'],reviewer='assistant_review',decision='equivalent_under_stated_reading',document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source=dict(inventory=INVENTORY,unit_sha256=s['unit_sha256'],text=s['text'],range=s['range'],math=[{k:m[k] for k in ('id','sha256')} for m in s['math']]),selection=selection_binding(catalog,[INDEX]),source_order_statements=[INDEX],clauses=clauses,interpretation=LIMITS,limits=['原刊二頁と定義の通読に基づく明示解釈下のアシスタントの意味判断。独立査読、証明提示の史実全般の調査、一般物理的導出・同義性の自動証明ではない。','u0087以降と二作品全体の目標は未完。'],unresolved=[],requirements=[dict(id=k,decision='satisfied',reason=v) for k,v in zip(REQUIREMENTS,REASONS)],evidence=dict(source_reading=[SOURCE],formal_checks=[REPORT,*DEPENDENCIES],semantic_reading=[DOC]),reviewed_prose_characters=s['source_nonblank_characters'],source_sha256=pins)

def prepare():
    from scripts.audit_opening_scope import write_exact
    write_exact(ROOT/REVIEW,json.dumps(record(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    active=dict(document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source_inventory=INVENTORY);catalog=load_catalog(ROOT,BASIS);inv=json.loads(read(INVENTORY));r=record()
    assert json.loads(read(REVIEW))==r
    validate_review(ROOT,REVIEW,'einstein-1905',active,catalog,inv);pins=r['source_sha256'].copy();pins[REVIEW]=digest((ROOT/REVIEW).read_bytes())
    return dict(status='light_proof_task_and_compatibility_gap_whole_unit_reviewed',document=FULL,source_units={r['unit']:r['reviewed_prose_characters']},reviewed_math_elements=1,whole_units_semantically_verified=True,verified_full_units={'kant-1784':0,'einstein-1905':1},general_real_physical_derivation_proved=False,semantic_equivalence_automatically_proved=False,source_sha256=pins)
