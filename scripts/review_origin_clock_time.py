"""Whole-unit reading of the clock's proportional time and difference display."""
from functools import lru_cache
import json
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import REQUIREMENTS,digest,selection_binding,validate_hashes,validate_review
from noema.review_registry import merge_pins
from scripts.compose_origin_clock_time import ROOT,read,FULL,CORE,BASIS,ANNOTATIONS,INDEX,LIMITS
from scripts.check_origin_clock_time import DOC,SOURCE,INVENTORY,PRIOR,DEPENDENCIES,source_record

REPORT='reports/origin-clock-time-v1.json'
REVIEWS=tuple(f'data/einstein-origin-clock-time-u{n:04d}-review-v1.json' for n in (123,124))
CLAUSES=(
 (('Es ist also',['ejjn','ejjp'],'同じ時計の直前の時間変換と軌道式から、次の二等式が得られるという著者の帰結提示。'),),
 (('[M0216]',['svj','stw','ejjl','ejjm','ejjn'],'τ=t√(1−(v/V)²)=t−(1−√(1−(v/V)²))tを同じ時計の全記録対へ接続し、直前の帰結の表示として保持する。'),),
)
REASONS=(
 (
  '固定u0123のEs ist also全範囲を原刊904頁のx=vt.と次の表示の間で照合した。本文9非空白文字を固定し、後続の等号連鎖とコンマも確認した。',
  'ejjnが前の二式ejjgと今回の比例式・差の式ejjmを同じ帰結の前提と結論へ結ぶ。ejjpは同じ時計の二式の位置ziiから帰結の位置zijへ文順を保持する。',
  'alsoの参照は直前のτの変換とx=vtである。前提と結論は同じ時計zie、状況zb6、同じ出来事のK/k記録を共有する。先の球の形状や別の時計の結果へ替えない。',
  'zcで同じ著者が前提から結論を得ると述べる働きを表す。外側のeir3はこの提示の論説への帰属であり、質問、仮定の追加、処理系の一般証明認定ではない。',
  'この導入自体に単位秒、遅れの近似、運搬過程を加えない。表示された二等式の全記録範囲は保持し、零時刻一つから問いの率が特定されたという帰結にはしない。',
  '帰結と引用、著者・論説・文順の既存規約を合成する。also専用の基本関係を追加せず、前提と結論の内容も現在の定義に接続する。',
  '著者、前提、結論、節、状況、直前の発話位置を変える対照と、引用された内容をその場で物理的真理として評価しないことを検査した。原刊での接続は通読判断として別に記録する。',
  '前の二式からEs ist alsoと次の表示までを再読した。同じ時計について得られる等号連鎖を導入する帰結という読みの下で、参照先と提示の働きを欠落なく保持したと判断する。',
 ),
 (
  '固定u0124のM0216を原刊904頁の一行の数式へ照合した。二つの等号、二つの根号、v/Vの二乗、外側と内側の減算、最後のtとコンマを確認し、MathMLのハッシュを固定した。',
  'svjの二つの等式は同じτをtと正の平方根の積、およびtから(1−同じ平方根)tを引いた値へ結ぶ。実数値の同値関係の下で原文の隣接する等号連鎖と一致し、ejjlが全ての局所記録対へ適用する。',
  'tは同じ出来事のKの時刻、τは同じ出来事のkの時刻で、同じ時計の校正された表示でもある。V,vと正の根stwは前の二式と同じ対象であり、βとその逆数を交換しない。',
  '直前のEs ist alsoに続く同じ著者の帰結の表示としてejjn/ejjpへ帰属する。末尾のコンマは後のworaus folgtへ続くが、その後の遅れと近似の内容をここで表示済みにしない。',
  '全現在範囲ejjdと同じ局所対ejitを使い、式に合う対だけを先に選ばない。tは負にもなり得る座標時刻で、正の経過時間を要求しない。今回の物理設定の0<v<Vと正の根を継承し、任意の時計尺度や表示原点のずれを許す設定へ変更しない。',
  '既存の実切断の根・積・差、svjの二等式、全時間の校正された原点配置と比較を合成する。旧svk/svlの記録選択に戻らず、現在の全対応へ接続した。新しい原始記号や数式文字列による代用はない。',
  '負・零・正の時刻と異なる速度、逆因子や誤った値、両記録の時刻、全選択対と未知入力を検査した。片方の算術演算だけを壊す試験は両等式の使用確認であって正しい実数モデルの反例ではない。有限検査と原刊読解を一般証明に替えない。',
  '直前の二式と帰結導入から、表示の二つの等号、末尾のコンマ、後続の説明まで再読した。同じ原点時計の時刻を比例形と差の形で表すという読みの下で、全演算と範囲・参照・提示を欠落なく保持したと判断する。',
 ),
)

@lru_cache(None)
def records():
    catalog=load_catalog(ROOT,BASIS);paths={FULL,CORE,BASIS,ANNOTATIONS,SOURCE,REPORT,INVENTORY,DOC,PRIOR,*DEPENDENCIES,'scripts/review_origin_clock_time.py','tests/test_origin_clock_time_review.py'}
    pins={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)};merge_pins(pins,catalog.source_sha256)
    for p in (SOURCE,REPORT,*DEPENDENCIES):
        evidence=json.loads(read(p));validate_hashes(ROOT,evidence['source_sha256']);merge_pins(pins,evidence['source_sha256'])
    out=[]
    for i,s in enumerate(source_record()['segments']):
        clauses=[];offset=0
        for text,symbols,reason in CLAUSES[i]:
            assert s['text'][offset:offset+len(text)]==text and all(n in catalog.entries for n in symbols)
            clauses.append(dict(range=[offset,offset+len(text)],text=text,definitions=symbols,reason=reason));offset+=len(text)
        assert offset==len(s['text']) and len(REASONS[i])==len(REQUIREMENTS)
        out.append(dict(schema_version='noema-semantic-review-1',work='einstein-1905',unit=s['unit'],reviewer='assistant_review',decision='equivalent_under_stated_reading',document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source=dict(inventory=INVENTORY,unit_sha256=s['unit_sha256'],text=s['text'],range=s['range'],math=[{k:m[k] for k in ('id','sha256')} for m in s['math']]),selection=selection_binding(catalog,[INDEX]),source_order_statements=[INDEX],clauses=clauses,interpretation=LIMITS,limits=['同じ原点時計の全現在記録における符号付き座標時刻の比例式・差の式という明示した読みの下でのアシスタントの通読判断。独立査読、物理的真理や意味同値の自動証明ではない。','u0125以降と二作品全体の目標は未完。'],unresolved=[],requirements=[dict(id=k,decision='satisfied',reason=v) for k,v in zip(REQUIREMENTS,REASONS[i])],evidence=dict(source_reading=[SOURCE],formal_checks=[REPORT,*DEPENDENCIES],semantic_reading=[DOC]),reviewed_prose_characters=s['source_nonblank_characters'],source_sha256=pins))
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
    return dict(status='origin_clock_proportional_time_and_difference_whole_units_reviewed',document=FULL,source_units={r['unit']:r['reviewed_prose_characters'] for r in records()},reviewed_math_elements=1,whole_units_semantically_verified=True,verified_full_units={'kant-1784':0,'einstein-1905':2},semantic_equivalence_automatically_proved=False,source_sha256=pins)
