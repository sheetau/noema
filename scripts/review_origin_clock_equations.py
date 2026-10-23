"""Read the equation introduction, both displays and their conjunction as a whole."""
from functools import lru_cache
import json
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import REQUIREMENTS,digest,selection_binding,validate_hashes,validate_review
from noema.review_registry import merge_pins
from scripts.compose_origin_clock_equations import ROOT,read,FULL,CORE,BASIS,ANNOTATIONS,INDEX,LIMITS
from scripts.check_origin_clock_equations import DOC,SOURCE,INVENTORY,PRIOR,DEPENDENCIES,source_record

REPORT='reports/origin-clock-equations-v1.json'
REVIEWS=tuple(f'data/einstein-origin-clock-equations-u{n:04d}-review-v1.json' for n in range(119,123))
CLAUSES=(
 (
  ('Zwischen die Größen [M0211], [M0212] und [M0213], ',['ejjc','ejje','svf','svg'],'同じK記録のx,tと同じ出来事のk記録のτを二式の数量として参照する。三つを同じ系の成分にまとめない。'),
  ('welche sich auf den Ort dieser Uhr beziehen, ',['ejit','ejjc','ejjd','ejip','ejir'],'前の時計zieの局所表示と現在所在、両系記録と原点配置を保持する。一般の任意の空間点や別時計の記録に替えない。'),
  ('gelten offenbar die Gleichungen:',['ejjf','ejjg','ejjh','ejji','ejjk'],'同じ時計の全対応対で二式が成り立つという内容を、既出の設定と変換に基づく明白な帰結として著者へ帰属し、コロンに続く両式を導入する。'),
 ),
 (('[M0214]',['svf','spd','soy','sjd','stw','ejje','ejjf'],'同じ二記録のτ=β(t−vx/V²)を保持し、βを同じ正の1/√(1−(v/V)²)へ結ぶ。'),),
 (('und',['ejje','ejjf','ejjg'],'同じ時計の同じ記録対で時間変換式と原点の軌道式を共に要求する連言。選言や別対象の式の並置に替えない。'),),
 (('[M0215].',['svg','ejje','ejjf','ejjk'],'同じK記録のx=vtを時間変換と連言し、一文の終端として帰属する。一般の空間点に要求せず、次のEs ist alsoの結果は別に残す。'),),
)
SEMANTICS=(
 '数量三つの役割、時計の場所への参照、式の成立と明白さ、二式へのコロンを接続した。ejjdは同じ時計の全現在対を変換範囲とkの原点に結び、ejjfはその全対に両式を要求する。',
 '分子1、分母の平方根、根号内の1−(v/V)²、括弧内のt−(v/V²)xを同じ光速と速度で構成する。既存のsvf/spdが同じ二記録の時間式を与え、ejjeが同じ係数soyと逆平方根sjd(stw)の一致を要求する。',
 'ejjeが既存svfの時間式とsvgの原点軌道を連言し、ejjfが同じ局所記録の全範囲へ適用する。二つの式に別々の出来事を選ぶことも、一方だけが真であることも連言の成立にしない。',
 'svgが同じK記録の空間第一成分xを同じ速度vと時刻tの積へ結ぶ。ejjfの全局所記録範囲とejjdのk原点配置を保持し、句点で導入からの一文を閉じる。',
)
WHOLE=(
 '原刊の導入全体を直前の時計の問いと後続の両式に続けて再読した。同じ時計の場所に関するx,t,τと、二式が明白に成り立つという提示を、明示した文脈上の前提の読みの下で欠落なく保持したと判断する。',
 '導入と時間式からundまでを再読した。同じ時計の両系座標に関する時間変換の表示として、逆平方根・二つの分数・二乗・減算・積・記録順を欠落なく保持したと判断する。',
 '二つの表示式の間にあるundを前後とともに再読した。同じ場所と記録範囲で二式を共に要求する連言を欠落なく保持したと判断する。',
 'undからx=vt.と次のEs ist alsoまでを再読した。同じ時計のk原点に対応するKでの軌道という読みの下で、系・時刻・速度・積・等号・一文の終端を欠落なく保持したと判断する。',
)

@lru_cache(None)
def records():
    catalog=load_catalog(ROOT,BASIS);paths={FULL,CORE,BASIS,ANNOTATIONS,SOURCE,REPORT,INVENTORY,DOC,PRIOR,*DEPENDENCIES,'scripts/review_origin_clock_equations.py','tests/test_origin_clock_equations_review.py'}
    pins={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)};merge_pins(pins,catalog.source_sha256)
    for p in (SOURCE,REPORT,*DEPENDENCIES):
        evidence=json.loads(read(p));validate_hashes(ROOT,evidence['source_sha256']);merge_pins(pins,evidence['source_sha256'])
    out=[]
    for i,s in enumerate(source_record()['segments']):
        clauses=[];offset=0
        for text,symbols,reason in CLAUSES[i]:
            assert s['text'][offset:offset+len(text)]==text and all(n in catalog.entries for n in symbols)
            clauses.append(dict(range=[offset,offset+len(text)],text=text,definitions=symbols,reason=reason));offset+=len(text)
        assert offset==len(s['text'])
        reasons=(
            f"固定{s['unit']}の全範囲を原刊904頁の導入・時間式・und・軌道式の一続きの文の中で照合した。本文範囲と数式要素{[m['id'] for m in s['math']]}をハッシュへ固定し、前の問いと次の導出も確認した。",
            SEMANTICS[i],
            '同じ時計zie、現在状況zb6、Kのx,t、同じ出来事のkのτ、同じV,vを固定する。ejitが局所表示・所在・代表軌跡と二記録を結び、ejjcが既出の全変換の範囲と同じ出来事対応へ接続する。原点はk側であり、Kでのxを零にしない。',
            '導入から二式までを、著者が既出の時計設定と最終変換から成り立つと述べる内容としてzcで帰属し、zdgでその明白さを保持する。コロンとundは同じ二式の導入と連言であり、処理系の証明認定や実際の観測報告ではない。',
            '全現在対を先に指定し、式に合う対だけに絞らない。現在の0<v<Vの設定を継承し、数値核では負の座標時刻を排除しない。kの原点時計の記録へ適用し、一般の空間点や内部部品へx=vtを強制しない。後続の進み率・単位時間の遅れ・近似を先取りしない。',
            '新しい原始記号を追加せず、実切断の差・積・商・正の根、既存svf/svg、全局所記録対、全時刻の校正された代表軌跡、引用と帰結の帰属を合成する。式を原語文字列や平坦化MathMLで代用せず、記号と算術の意味を既存規約へ接続する。',
            '二式それぞれだけが成立する例、符号付き時刻、正の逆平方根、原点三成分、同じ出来事の結合、全選択対への数値式の適用と著者帰属を対照検査した。全時間の下位意味は変更のない前段の証拠を参照する。有限例と通読判断を一般実数体や物理的真理の自動証明と混同しない。',
            WHOLE[i],
        )
        assert len(reasons)==len(REQUIREMENTS)
        out.append(dict(schema_version='noema-semantic-review-1',work='einstein-1905',unit=s['unit'],reviewer='assistant_review',decision='equivalent_under_stated_reading',document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source=dict(inventory=INVENTORY,unit_sha256=s['unit_sha256'],text=s['text'],range=s['range'],math=[{k:m[k] for k in ('id','sha256')} for m in s['math']]),selection=selection_binding(catalog,[INDEX]),source_order_statements=[INDEX],clauses=clauses,interpretation=LIMITS,limits=['同じ原点時計の現在の全記録に二式が成り立つという明示した読みの下でのアシスタントの通読判断。独立査読、全可能解釈の包含、物理的真理や意味同値の自動証明ではない。','u0123以降と二作品全体の目標は未完。'],unresolved=[],requirements=[dict(id=k,decision='satisfied',reason=v) for k,v in zip(REQUIREMENTS,reasons)],evidence=dict(source_reading=[SOURCE],formal_checks=[REPORT,*DEPENDENCIES],semantic_reading=[DOC]),reviewed_prose_characters=s['source_nonblank_characters'],source_sha256=pins))
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
    return dict(status='origin_clock_equation_introduction_and_both_formulas_whole_units_reviewed',document=FULL,source_units={r['unit']:r['reviewed_prose_characters'] for r in records()},reviewed_math_elements=5,whole_units_semantically_verified=True,verified_full_units={'kant-1784':0,'einstein-1905':4},semantic_equivalence_automatically_proved=False,source_sha256=pins)
