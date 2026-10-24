"""Whole-unit rereading of seven wave equations and their vector explanation."""
from functools import lru_cache
import json
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import REQUIREMENTS,digest,selection_binding,validate_hashes,validate_review
from noema.review_registry import merge_pins
from scripts.compose_wave_display import ROOT,read,FULL,CORE,BASIS,ANNOTATIONS,LIMITS,INDICES
from scripts.check_wave_display import DOC,SOURCE,INVENTORY,DEPENDENCIES,source_record

REPORT='reports/wave-display-v1.json'
REVIEWS=['data/einstein-wave-display-u0180-review-v1.json','data/einstein-wave-display-u0181-review-v1.json']
CLAUSES=(
 (('[M0320]',['ekbf','ekbg','ekbh','ekbi','ekbm','ekbo','ekbp','ekbq','sds2','sdx2','seat'],'同じ四座標で、六つの場成分をそれぞれの係数と共通sin Φの積へ等置し、Φをω(t−(ax+by+cz)/V)へ等置する。三つの空間項全体をVで割り、ωは括弧全体に掛かる。先行の物理場との近似誤差を保つ表現場の七式として提示する。'),),
 (
  ('Hierbei sind ([M0321]) und ([M0322]) ',['ekbe','ekbj','ekbl','ekbr','eissb'],'Hierbeiで直前の表示式の同じ六係数を受け、三つずつ同じ三空間軸のベクトルとしてまとめる。別の波や別の系の振幅へ交換しない。'),
  ('die Vektoren, welche die Amplitude des Wellenzuges bestimmen, ',['ekbj','ekbl','seal','seag','sd24','sdx2'],'正規化した同じ正弦に掛かる二つの固定ベクトルが波列の振幅を定める。符号と方向を保持し、各ベクトルの非負の大きさは三成分の二乗和平方根で得る。振幅を一成分又は測定済みの記録にしない。'),
  ('[M0323] die Richtungskosinus der Wellennormalen.',['ekbk','ekbl','ekbn','ekbr','ekbs','ekbt','ejsn','eisdd'],'同じ校正されたCartesian基底でn=(a,b,c)が単位長さを持ち、同時刻の等位相点の位置差と直交するという法線を構成する。その三成分を各軸との方向余弦として読む。実際の場の全波面を厳密な平面にせず、同じ局所近似の表現波面に適用する。'),
 ),
)
REASONS=(
 (
  '固定u0180のM0320を原刊910頁へ照合した。六成分の等式とΦの定義の七等号、六つのsinと共通Φ、係数の下付き0、ωの括弧、空間三項を分子とする分数と分母Vを確認した。本文文字は0であり、数式の全体を判断対象とする。',
  'X,Y,Z及びL,M,Nそれぞれに対応する係数とsin Φの積を述べ、同じΦを独立に位相式へ結ぶ。二場は同じ四座標・領域・正弦・位相を共有する。七式を全有効領域へ量化し、一つの点の一致で全表示を代用しない。',
  '表示値は同じu0179のK、V、源・波・過程・二場・単位・近似領域の割当に結ぶ。X0/Y0/Z0とL0/M0/N0はそれぞれ対応する三成分、a/b/cは同じ三軸、ωは同じ時間尺度の位相率である。別の設定の数値を寄せ集めない。',
  'コロンで示された七式は先行の仮定設定の明示としてeissbを通じて著者へ帰属する。等号は近似表現の式であり、実際の場の誤差が零という新しい実験結果や別の物理法則の断言にはしない。前後の箇所と順序も接続する。',
  '先行の十分な近似を維持し、実際の物理場と表現場を区別する。横波の振幅関係、全場の方程式、特定の数値又は光源の静止を付け加えない。ωを通常の周期数νと数値同一視せず、Vの分母を一つの空間項だけへ掛けない。',
  '同じ位相関数を既存sds2で構成し、七式を個別の実数等号と積で表す。正弦の規約sd24と二場の構成sdx2、物理的な近似設定ekazを保持する。原式の綴りや一つの原始記号を七式の代用にしない。新しい基本関係は同じ仮定の明示・説明という一般の提示関係だけである。',
  '各六成分の誤りと、位相を変更して六成分も合わせた誤りを対照し、七番目の等式の独立性を確認した。四座標の量化と領域の内外、35引数の先行設定、31存在証人を診断する。正弦と全実数域の真理を診断用の関数から証明したとはしない。',
  '直前の仮定から七表示式を通して読み、同じ表現場の各成分・共通位相・値の割当・適用範囲・著者の提示を欠落なく記述したと判断する。明示した近似表現としての読みを保ち、原著者の物理理論の真理を認定する判断とは区別する。',
 ),
 (
  '固定u0181全本文109非空白文字とM0321–M0323を原刊910頁へ照合し、直前の七式から続けて読んだ。二つの係数三つ組の下付き0と方向の三つ組を保持し、Hierbeiから句点まで分断せず対象にした。',
  '同じ六係数を二つのベクトルへまとめ、それらが正規化した正弦の波列の振幅を定めること、a/b/cが波面法線の方向余弦であることを合成する。ベクトルの各成分と非負の大きさ、単位法線と同時刻の等位相面を分けて表す。',
  'Hierbeiはu0180の同じ係数・正弦・位相を指す。Kの同じ校正済みCartesian基底と二場の単位を保持し、電気側と磁気側のベクトルを交換しない。a/b/cは位相の同じ三空間項であり、別の幾何学的な三つ組ではない。',
  'この一文は先行表示で用いる量の説明としてeissbへ結ぶ。新たな波源の仮定、別の実験による振幅測定又は新しい波の導入として扱わない。著者・論説・先行箇所と本文順序を同じ内容へ帰属する。',
  '二ベクトルを大きさだけへ縮めず、成分の符号と方向を保つ。波面は同時刻の近似表現の等位相面と読み、別時刻の点の等位相や実際の場の全波面へ拡張しない。横波条件や二つのノルムの数値一致をこの文に追加しない。',
  '三成分ベクトルは空間軸への割当、振幅の大きさは非負の二乗和平方根、法線は単位方向と等位相点の位置差への直交で構成する。校正された直交基底で単位ベクトルの軸成分が方向余弦になる読みを用い、原語又は未説明の名詞記号へ置換しない。',
  '符号付きの各成分・零ベクトル・誤った大きさ、三軸に沿う法線と斜めの法線、誤った位相関数、同時刻の位置対を対照する。領域と全位置対の七座標、同じ31存在証人を検査する。有限例と一般の物理的な波面、原文の意味判断は確認範囲が異なる。',
  '七表示式に続く説明を再読し、係数の二ベクトル・波列の振幅を定める役割・三方向余弦・波面法線・Hierbeiの参照と提示を、明示した局所近似の読みの下で欠落なく記述したと判断する。第七節の見出しと後続の観測・変換は別の未完単位として残す。',
 ),
)

@lru_cache(None)
def records():
    catalog=load_catalog(ROOT,BASIS)
    paths={FULL,CORE,BASIS,ANNOTATIONS,SOURCE,REPORT,INVENTORY,DOC,*DEPENDENCIES,'scripts/review_wave_display.py','tests/test_wave_display_review.py'}
    pins={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)};merge_pins(pins,catalog.source_sha256)
    for p in (SOURCE,REPORT,*DEPENDENCIES):
        evidence=json.loads(read(p));validate_hashes(ROOT,evidence['source_sha256']);merge_pins(pins,evidence['source_sha256'])
    out=[]
    for i,s in enumerate(source_record()['segments']):
        clauses=[];offset=0
        for text,symbols,reason in CLAUSES[i]:
            assert s['text'][offset:offset+len(text)]==text and all(n in catalog.entries for n in symbols)
            clauses.append(dict(range=[offset,offset+len(text)],text=text,statements=[INDICES[i]],definitions=symbols,reason=reason));offset+=len(text)
        assert offset==len(s['text']) and len(REASONS[i])==len(REQUIREMENTS)
        out.append(dict(schema_version='noema-semantic-review-1',work='einstein-1905',unit=s['unit'],reviewer='assistant_review',decision='equivalent_under_stated_reading',document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source=dict(inventory=INVENTORY,unit_sha256=s['unit_sha256'],text=s['text'],range=s['range'],math=[{k:m[k] for k in ('id','sha256')} for m in s['math']]),selection=selection_binding(catalog,[INDICES[i]]),clauses=clauses,interpretation=LIMITS,limits=['明示した近似表現と同時刻の等位相面の読みの下でのアシスタントによる判断。独立査読・意味同義性の自動証明ではない。','実際の場との誤差を零にせず、全無限域・正弦の物理的な実現又は全放射理論を有限診断で証明していない。','u0178とu0182以降及び二作品全体の目標は未完。'],unresolved=[],requirements=[dict(id=k,decision='satisfied',reason=v) for k,v in zip(REQUIREMENTS,REASONS[i])],evidence=dict(source_reading=[SOURCE],formal_checks=[REPORT,*DEPENDENCIES],semantic_reading=[DOC]),reviewed_prose_characters=s['source_nonblank_characters'],source_sha256=pins))
    return out

def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,r in zip(REVIEWS,records()):write_exact(ROOT/p,json.dumps(r,ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    active=dict(document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source_inventory=INVENTORY);catalog=load_catalog(ROOT,BASIS);inv=json.loads(read(INVENTORY));pins={}
    for p,r in zip(REVIEWS,records()):
        assert json.loads(read(p))==r
        validate_review(ROOT,p,'einstein-1905',active,catalog,inv);merge_pins(pins,r['source_sha256']);pins[p]=digest((ROOT/p).read_bytes())
    return dict(status='seven_wave_equations_and_vector_explanation_whole_units_reviewed',document=FULL,source_units={r['unit']:r['reviewed_prose_characters'] for r in records()},reviewed_math_elements=4,whole_units_semantically_verified=True,verified_full_units={'kant-1784':0,'einstein-1905':2},semantic_equivalence_automatically_proved=False,source_sha256=pins)
