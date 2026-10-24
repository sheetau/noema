"""Whole-unit rereading of the distant source and approximation assumption."""
from functools import lru_cache
import json
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import REQUIREMENTS,digest,selection_binding,validate_hashes,validate_review
from noema.review_registry import merge_pins
from scripts.compose_distant_wave_source import ROOT,read,FULL,CORE,BASIS,ANNOTATIONS,LIMITS,INDEX
from scripts.check_distant_wave_source import DOC,SOURCE,INVENTORY,DEPENDENCIES,source_record

REPORT='reports/distant-wave-source-v1.json';REVIEW='data/einstein-distant-wave-source-u0179-review-v1.json'
CLAUSES=(
 (['ekba','ekaz','ejsn','ejsl','ra','eiscc'],'Im Systeme Kを既存の同じKへ結び、全ての位置・場・単位を同じ系で指定する。Kという綴りだけで基準系を代用しない。'),
 (['ekba','ekbb','ekax','ekaw','eisrt','eisru','eisrv'],'源とその同じ電磁過程・波を仮定する。支持範囲が非空で、その全位置の原点距離が局所空間部分の尺度に対して非常に大きい倍率以上であるという読みを採る。物理的な放射の帰属を数値関数から推測せず、点源・静止・可視光・現実の実験を追加しない。'),
 (['ekat','ekau','ekav','ekaz'],'原点の正の近傍を含む有界な空間部分を、正の長さの時間区間で固定して考察する読みを採る。球形には限定せず、原点の一点・一時刻だけの包含から全域条件へ飛躍しない。同じ領域を物理場と近似へ渡す。'),
 (['ekay','ekaz','ekba','ekbb','ekbc','ekbd','seat','sd24','sdx2','sds2','eisrw','eissa'],'二つの実際の場を同じ共通位相・正弦・六振幅の場で全領域にわたって近似し、二誤差が同じ単位と用途で十分という規約を別に要求する。dargestellt seiも同じ仮定の範囲に含め、後続M0320の表示へコロンで参照する。遠さだけから十分性や波形を導出しない。'),
)

@lru_cache(None)
def records():
    catalog=load_catalog(ROOT,BASIS);s=source_record()
    paths={FULL,CORE,BASIS,ANNOTATIONS,SOURCE,REPORT,INVENTORY,DOC,*DEPENDENCIES,'scripts/review_distant_wave_source.py','tests/test_distant_wave_source_review.py'}
    pins={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)};merge_pins(pins,catalog.source_sha256)
    for p in (SOURCE,REPORT,*DEPENDENCIES):
        evidence=json.loads(read(p));validate_hashes(ROOT,evidence['source_sha256']);merge_pins(pins,evidence['source_sha256'])
    clauses=[]
    for part,(symbols,reason) in zip(s['clauses'],CLAUSES,strict=True):
        assert all(n in catalog.entries for n in symbols)
        clauses.append(dict(range=part['range'],text=part['text'],statements=[INDEX],definitions=symbols,reason=reason))
    assert ''.join(c['text'] for c in clauses)==s['text'] and s['source_nonblank_characters']==198
    reasons=(
      '固定u0179全231文字・198非空白本文文字とM0319=Kを原刊910頁へ照合した。第七節冒頭の一文と、そのコロンが指す次の六成分・位相の表示を連続して確認する。原文と保存式を変更しない。',
      '系K、源の仮定、原点から非常に遠いという程度、電磁波の物理的な発生、原点を含む空間部分、十分な近似、後続式による表現を分けて合成する。遠さには同じ空間尺度・全支持範囲・程度基準、近似には全領域の二誤差と用途上の十分性を要求する。',
      'M0319は既存raのKである。源・過程・波・二場・空間部分・時間区間・長さ時間と場の単位を一組の設定で共有し、Vの速度尺度もeiscc/tbへ結ぶ。数値上限の十分性で別の領域や単位を使わない。位相と正弦は電気側・磁気側の六成分で同じものを用いる。',
      'befinde sichとdargestellt seiを同じ著者の仮定提示ugへ接続する。源が実在したという報告又は読者が装置を建造せよという命令にはしない。コロンの前方参照eissaは同じ数値表現ekayとM0320の箇所へ結び、引用の真理を提示関係だけから実行しない。',
      '源を点・静止・可視光・球対称に限定しない。Raumteilは有界な原点近傍を有限の正の期間で固定する明示的な局所理想化とする。原文にない半径・倍率・期間・誤差の数値は補わない。単に遠いことから十分な近似を導かず、横波の振幅関係や全場の方程式を六波形の表示へ追加しない。',
      '源の支持範囲と物理的放射、程度基準、用途上の十分性、表示式への参照を一般関係として意味を指定する。原点近傍は三座標と距離二乗・包含の二含意、時間範囲は領域の積、遠さは全支持範囲への距離条件で合成する。物理場ejsnと波形sd24/sdx2と誤差seatを再利用し、文全体を一つの新基本記号にしない。',
      '局所幾何学の切断算術、支持範囲の非空性と全点条件、引数を実際の型で共有する検査、多数の存在証人を一つずつ残す診断、六成分の共通位相、仮定提示と前方参照を点検する。無限域は有限標本で代用せず、正弦や放射の物理的真理を診断関数から認定しない。保存済みの下位証拠を検証し、検査と読解を区別する。',
      '原刊の第七節導入を再読し、同じKで遠方の源から来る波を原点を含む空間部分で十分に近似するという仮定を、参照・程度・領域・物理的帰属・近似・提示まで接続したと判断する。採用した局所的な領域と期間の読みの下でこの文の意味要素に未処理はない。見出しu0178と後続の表示式u0180の全単位判断は別に残す。',
    )
    assert len(reasons)==len(REQUIREMENTS)
    record=dict(schema_version='noema-semantic-review-1',work='einstein-1905',unit=s['unit'],reviewer='assistant_review',decision='equivalent_under_stated_reading',document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source=dict(inventory=INVENTORY,unit_sha256=s['unit_sha256'],text=s['text'],range=s['range'],math=[{k:m[k] for k in ('id','sha256')} for m in s['math']]),selection=selection_binding(catalog,[INDEX]),clauses=clauses,interpretation=LIMITS,limits=['明示した読みの下でのアシスタントの通読判断であり、独立査読・同義性の自動証明ではない。','物理的な放射の帰属と用途の十分性は明示した規約に従う。遠方源からの誤差評価の導出や全無限域の証明は行っていない。','原点近傍を固定した有限期間で扱う局所理想化を採る。u0178・u0180と二作品全体の記述は未完。'],unresolved=[],requirements=[dict(id=k,decision='satisfied',reason=v) for k,v in zip(REQUIREMENTS,reasons)],evidence=dict(source_reading=[SOURCE],formal_checks=[REPORT,*DEPENDENCIES],semantic_reading=[DOC]),reviewed_prose_characters=198,source_sha256=pins)
    return [record]

def prepare():
    from scripts.audit_opening_scope import write_exact
    write_exact(ROOT/REVIEW,json.dumps(records()[0],ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    r=records()[0];assert json.loads(read(REVIEW))==r
    active=dict(document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source_inventory=INVENTORY)
    validate_review(ROOT,REVIEW,'einstein-1905',active,load_catalog(ROOT,BASIS),json.loads(read(INVENTORY)))
    pins=dict(r['source_sha256']);pins[REVIEW]=digest((ROOT/REVIEW).read_bytes())
    return dict(status='distant_wave_source_assumption_whole_unit_reviewed',document=FULL,source_units={r['unit']:198},reviewed_math_elements=1,whole_units_semantically_verified=True,verified_full_units={'kant-1784':0,'einstein-1905':1},semantic_equivalence_automatically_proved=False,source_sha256=pins)
