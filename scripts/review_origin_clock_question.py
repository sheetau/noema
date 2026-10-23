"""Whole-unit reading of the two origin-clock setup/question sentences."""
from functools import lru_cache
import json
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import REQUIREMENTS,digest,selection_binding,validate_hashes,validate_review
from noema.review_registry import merge_pins
from scripts.compose_origin_clock_question import ROOT,read,FULL,CORE,BASIS,ANNOTATIONS,INDICES,LIMITS
from scripts.check_origin_clock_question import DOC,SOURCE,INVENTORY,PRIOR,DEPENDENCIES,source_record

REPORT='reports/origin-clock-question-v1.json';REVIEW='data/einstein-origin-clock-u0118-review-v1.json'
CLAUSES=(
 ('Wir denken uns ferner ',['ejix','ug','zao'],'同じ節の考察へ思考設定を追加する。実際の設置済み報告ではない。'),
 ('eine der Uhren, ',['ejiw','ejio','zie'],'条件を満たす時計の一つを同じzieとして選ぶ。後の配置と問いでも同一の時計である。'),
 ('welche relativ zum ruhenden System ruhend die Zeit [M0207], ',['ejij','ejin','ejio','eiwt'],'Kに静止してtを示せる許容された場合を表す。代表位置が静止し、各局所表示はKの現在の座標時刻に一致する。'),
 ('relativ zum bewegten System ruhend die Zeit [M0208] anzugeben befähigt sind, ',['ejik','ejil','ejim','ejin','ejio','eiym'],'kに静止してτを示せる許容された場合も同じ時計について存在する。Kでの能力と現在同時の静止へまとめず、全候補の校正と全自系時刻の表示存在を保つ。'),
 ('im Koordinatenursprung von [M0209] gelegen ',['ejip','ejja','zbn','zbv'],'今回はkの原点に置く。原点の測定三座標、時計の全代表位置、全局所候補の所在を同じ原点に結ぶ。'),
 ('und so gerichtet, daß sie die Zeit [M0210] angibt. ',['ejip','ejin','ejil','ejiz'],'今回の表示がτと同じ尺度・原点である校正を保持する。未知の倍率や任意のずれは認めず、設定の文を著者と論説へ帰属する。'),
 ('Wie schnell geht diese Uhr, ',['ejis','ejiu','ejiv','eji2'],'同じ時計の正の一定な進み率を問う。異なる比較時刻があり、全時間順の記録組で指示差が同じ候補率に従うことを答えの条件とする。答えの存在や特定の値は断言しない。'),
 ('vom ruhenden System aus betrachtet?',['ejiq','ejjb','ejir','ejit','eji4'],'Kの全対象時刻について、同じ出来事のK時刻と同所の時計表示を比較する。kから見た率や遠隔信号の受信率に替えず、設定に続く著者の問いとして帰属する。'),
)
REASONS=(
 '固定u0118を原刊903頁末から904頁冒頭へ続けて再読した。Wir denken uns fernerからangibt.までの設定とWie schnellからbetrachtet?までの問いを一つの原文単位として保持し、M0207=t、M0208=τ、M0209=k、M0210=τを照合した。',
 '二系の許容された代替設定、完全な代表位置の静止、独立した局所候補、全ての表示の校正、各自系時刻の存在を合成した。現在のk原点の配置に加え、問いの候補条件では同じ出来事の両系記録とKの全対象時刻、全時間順の指示差を結んだ。',
 '時計zie、Kとk、長さ・時間の尺度、基準状況、各代替状況、出来事・表示・場所・四記録を区別して共有する。tとτは既存の各系の時刻規則に参照し、同じ数値へ等置しない。各系に静止できるという二つの能力を、現に両系に同時に静止することへ替えない。',
 'ugとzaoは同じ節に思考設定を追加する提示であり、実物の製作や配置の報告ではない。zihは実数の答えを求める問いを引用する。外側の著者帰属を断定しても、引用した設定の物理的真理や問われた率の存在・一意性・値はそこから断定しない。',
 '静止は時計の代表位置、so gerichtetはτと同じ尺度・原点への校正と読む。Wie schnellはこの一様運動と理想時計の正の一定率と明示する。後続の二式・平方根・遅れの近似は先取りせず、一般に変動する時計の全ての進み方までこの候補型に含むとはしない。',
 '新しい基本記号を追加せず、既存の許容代替設定zid、現在所在zab、局所対応eisgm、場所付き四記録eiyw、実軌跡sb/se、実数の順序と差積、引用と問いを組み合わせた。旧zacの動く時計対K時計の比較を一般的な局所校正へ流用せず、旧判断・検査器は保存した。',
 '各証人スロット、独立した候補と校正、誤った別表示、三軸の原点、同じ出来事の両系記録、正の区間と全時間、全時間順の記録組、第三点で破れる一定率、未決の問いを対照検査した。全実数量化は保持し、有限検査の成功を意味同値や物理的実現の自動証明へ変換しない。',
 '二文全体と前後を再読した。同じ時計の両系での能力、現在のk原点配置とτへの校正、Kから見た進み方の問い、追加の考察設定という役割を、明示した一定率の読みの下で欠落なく保持したと判断する。u0119以降の座標式と答えの導出は次の作業である。',
)

@lru_cache(None)
def record():
    catalog=load_catalog(ROOT,BASIS);s=source_record()['segments'][0]
    paths={FULL,CORE,BASIS,ANNOTATIONS,SOURCE,REPORT,INVENTORY,DOC,PRIOR,*DEPENDENCIES,'scripts/review_origin_clock_question.py','tests/test_origin_clock_question_review.py'}
    pins={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)};merge_pins(pins,catalog.source_sha256)
    for p in (SOURCE,REPORT,*DEPENDENCIES):
        evidence=json.loads(read(p));validate_hashes(ROOT,evidence['source_sha256']);merge_pins(pins,evidence['source_sha256'])
    clauses=[];offset=0
    for text,symbols,reason in CLAUSES:
        assert s['text'][offset:offset+len(text)]==text and all(n in catalog.entries for n in symbols)
        clauses.append(dict(range=[offset,offset+len(text)],text=text,definitions=symbols,reason=reason));offset+=len(text)
    assert offset==len(s['text']) and len(REASONS)==len(REQUIREMENTS)
    math=[{k:m[k] for k in ('id','sha256')} for m in s['math']]
    return dict(schema_version='noema-semantic-review-1',work='einstein-1905',unit=s['unit'],reviewer='assistant_review',decision='equivalent_under_stated_reading',document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source=dict(inventory=INVENTORY,unit_sha256=s['unit_sha256'],text=s['text'],range=s['range'],math=math),selection=selection_binding(catalog,list(INDICES)),source_order_statements=list(INDICES),clauses=clauses,interpretation=LIMITS,limits=['代表位置の静止、正確な座標時刻への校正、一様運動の理想時計の一定進み率という明示した読みの下でのアシスタントの通読判断。全可能解釈の包含、独立査読、意味同値の自動証明や実際の物理的実現の証明ではない。','u0119以降と二作品全体の目標は未完。'],unresolved=[],requirements=[dict(id=k,decision='satisfied',reason=v) for k,v in zip(REQUIREMENTS,REASONS)],evidence=dict(source_reading=[SOURCE],formal_checks=[REPORT,*DEPENDENCIES],semantic_reading=[DOC]),reviewed_prose_characters=s['source_nonblank_characters'],source_sha256=pins)

def prepare():
    from scripts.audit_opening_scope import write_exact
    write_exact(ROOT/REVIEW,json.dumps(record(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    r=record();assert json.loads(read(REVIEW))==r
    active=dict(document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source_inventory=INVENTORY)
    validate_review(ROOT,REVIEW,'einstein-1905',active,load_catalog(ROOT,BASIS),json.loads(read(INVENTORY)))
    return dict(status='origin_clock_setup_and_open_question_whole_unit_reviewed',document=FULL,source_units={r['unit']:r['reviewed_prose_characters']},reviewed_math_elements=4,whole_units_semantically_verified=True,verified_full_units={'kant-1784':0,'einstein-1905':1},semantic_equivalence_automatically_proved=False,source_sha256=r['source_sha256']|{REVIEW:digest((ROOT/REVIEW).read_bytes())})
