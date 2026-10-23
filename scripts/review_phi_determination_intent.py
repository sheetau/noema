"""Whole reading of the still-unknown coefficient and its intended determination."""
from functools import lru_cache
import json
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import REQUIREMENTS,digest,selection_binding,validate_hashes,validate_review
from noema.review_registry import merge_pins
from scripts.compose_phi_determination_intent import ROOT,read,FULL,CORE,BASIS,ANNOTATIONS,INDEX,LIMITS
from scripts.check_phi_determination_intent import DOC,SOURCE,INVENTORY,PRIOR,DEPENDENCIES,source_record

REPORT='reports/phi-determination-intent-v1.json'
REVIEW='data/einstein-phi-determination-intent-u0092-review-v1.json'
CLAUSES=(
 ('In den entwickelten Transformationsgleichungen ',['ei7c','ejaw'],'既に得た現在の四座標変換式を指す。'),
 ('tritt noch eine unbekannte Funktion [M0148] von [M0149] auf, ',['spc','sqc','sqd','srp','ejaw'],'同じ速度vの関数φが先行段階に続いて現在も未決定として残る。'),
 ('welche wir nun bestimmen wollen.',['ejax','zgm','zgl','spc'],'その同じ関数を今の論述段階から決定する著者の意図を述べる。'),
)
REASONS=(
 '固定u0092全140文字・非空白本文109文字とM0148–M0149を原刊901頁へ照合した。直前の両立性の結論から一文全体を読み、後続の第三系導入との境界を確認した。',
 '既に得た変換式への指示、未知関数がなお残ること、φがvの関数であること、関係節による同じ対象の引継ぎ、著者の今から決定する意図を保持する。nochは先行段階と現在段階の未決定性、nunは決定へ進む論述段階として接続した。',
 '変換式はei7c、M0148は同じ正規化後のspc、M0149はその相対速度引数であり、前のaを同値として代用しない。sqdとsrpは同じ候補族sqcを異なる段階zfm/zglで扱い、zgmの関数記述も同じspcを指定する。',
 '未知関数の残存を著者の主張uh、決定をその関数についての意図zgmとして分けて同じ第三節へ接続する。意図は決定完了の報告に替えない。未知性zgtから意図zgnへの順序と、前の両立性zggから一文全体への順序を同じ著者・論説で保持する。',
 '未決定を関数の不存在や各速度で候補が全て違うことへ強めず、一点での候補一致を全関数の確定へ弱めない。二段階の候補集合の同一性、間の全瞬間の心理状態、原文にない成功・唯一解・方法の発見、φ=1や負速度での値を加えない。',
 '有効な候補族・現在候補の保持・現在の正規化後関数との一致smq・同じ対象速度で異なる候補の存在smbを再利用する。意図は既存zgmの明示された意味規約と同じ閉じた関数記述を使い、原文一文を新しい未説明の原始語へ置き換えない。',
 '原刊・固定本文・意味規約の通読と、同じ段階と速度での候補相違、現在関数と族の値の一致、候補の有効性、現在候補の残存、同じ関数への意図の帰属を確認した。実切断・関数全体への量化は有限評価器の拒否を保ち、明示的例化と有限境界を一般的な証明とはしない。',
 '既出式の指示から未知関数の残存、同じ対象を受ける関係節と決定意図まで一文を再読した。先行と現在の論述段階での候補未決定性という読みの下で、参照・範囲・残存・意図を欠落なく記述したと判断する。',
)


@lru_cache(None)
def record():
    catalog=load_catalog(ROOT,BASIS);paths={FULL,CORE,BASIS,ANNOTATIONS,SOURCE,REPORT,INVENTORY,DOC,PRIOR,*DEPENDENCIES,'scripts/review_phi_determination_intent.py','tests/test_phi_determination_intent_review.py'}
    pins={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)};merge_pins(pins,catalog.source_sha256)
    for p in (SOURCE,REPORT,*DEPENDENCIES):
        evidence=json.loads(read(p));validate_hashes(ROOT,evidence['source_sha256']);merge_pins(pins,evidence['source_sha256'])
    s=source_record()['segments'][0];clauses=[];offset=0
    for text,symbols,reason in CLAUSES:
        assert s['text'][offset:offset+len(text)]==text and all(n in catalog.entries for n in symbols)
        clauses.append(dict(range=[offset,offset+len(text)],text=text,definitions=symbols,reason=reason));offset+=len(text)
    assert offset==len(s['text']) and len(REASONS)==len(REQUIREMENTS)
    return dict(schema_version='noema-semantic-review-1',work='einstein-1905',unit=s['unit'],reviewer='assistant_review',decision='equivalent_under_stated_reading',document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source=dict(inventory=INVENTORY,unit_sha256=s['unit_sha256'],text=s['text'],range=s['range'],math=[{k:m[k] for k in ('id','sha256')} for m in s['math']]),selection=selection_binding(catalog,[INDEX]),source_order_statements=[INDEX],clauses=clauses,interpretation=LIMITS,limits=['候補族による未決定性、論述段階の残存と現在、著者の意図という明示した読みの下でのアシスタントの通読判断。独立査読、一般的な認識理論や意味同値の自動証明ではない。','後続u0093以降と二作品全体の目標は未完。'],unresolved=[],requirements=[dict(id=k,decision='satisfied',reason=v) for k,v in zip(REQUIREMENTS,REASONS)],evidence=dict(source_reading=[SOURCE],formal_checks=[REPORT,*DEPENDENCIES],semantic_reading=[DOC]),reviewed_prose_characters=s['source_nonblank_characters'],source_sha256=pins)


def prepare():
    from scripts.audit_opening_scope import write_exact
    write_exact(ROOT/REVIEW,json.dumps(record(),ensure_ascii=False,indent=2)+'\n')


@lru_cache(None)
def build_report():
    active=dict(document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source_inventory=INVENTORY);catalog=load_catalog(ROOT,BASIS);inv=json.loads(read(INVENTORY));r=record()
    assert json.loads(read(REVIEW))==r
    validate_review(ROOT,REVIEW,'einstein-1905',active,catalog,inv);pins=dict(r['source_sha256']);pins[REVIEW]=digest((ROOT/REVIEW).read_bytes())
    return dict(status='still_unknown_phi_and_determination_intent_whole_unit_reviewed',document=FULL,source_units={r['unit']:r['reviewed_prose_characters']},reviewed_math_elements=2,whole_units_semantically_verified=True,verified_full_units={'kant-1784':0,'einstein-1905':1},semantic_equivalence_automatically_proved=False,source_sha256=pins)
