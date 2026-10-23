"""Read the connective sentence and both halves of its single expanded equation."""
from functools import lru_cache
import json
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import REQUIREMENTS,digest,selection_binding,validate_hashes,validate_review
from noema.review_registry import merge_pins
from scripts.compose_light_time_expansion import ROOT,read,FULL,CORE,BASIS,ANNOTATIONS,INDEX,LIMITS
from scripts.check_light_time_expansion import DOC,SOURCE,INVENTORY,PRIORS,DEPENDENCIES,source_record

REPORT='reports/light-time-expansion-v1.json'
REVIEWS=tuple(f'data/einstein-light-time-expansion-u{n:04d}-review-v1.json' for n in (51,52,53))
CLAUSES=(
 (
  ('oder, ',['ei2s','zd3','ei2d'],'直前の同じ中点式を同値な形で書き換える提示として読む。'),
  ('indem man die Argumente der Funktion [M0099] beifügt ',['ei2o','ei2r','sjk','sjg'],'同じτ候補の四引数を明示し、三出来事と実際のk時計値へ接続する。'),
  ('und das Prinzip der Konstanz der Lichtgeschwindigkeit im ruhenden Systeme anwendet:',['ei2p','eios','ei2m','ei2n'],'同じKで光速度原理を全適用範囲と両光路へ結び、後続の一つの展開式を導く書換えの前提とする。'),
 ),
 (
  ('[M0100]',['ei2r','sjf','sjg','sit'],'同じτの出発値と帰着値の半和を左辺とする。帰着の第四引数はtに往路と復路の二経過時間を加える。'),
 ),
 (
  ('[M0101]',['ei2r','sjf','sjg','sit'],'等号を介して同じ反射値を右辺へ結ぶ。反射の第一引数はx′、第四引数はtに往路の経過時間だけを加える。'),
 ),
)
REASONS=(
 (
  '固定u0051全142文字・116本文文字とM0099を原刊898頁へ照合し、oderからanwendetまでを三つの連続範囲で保持した。直後の左右の表示式を一つの帰結として読む。',
  'oderの書換え、同じ関数への引数の付加、静止系の光速度一定の適用を保持する。引数は単なる転記でなく、同じ三出来事のK四座標とk時計指示に接続する。',
  'ei2bの現在の往復と全同期、ei2lの同じ座標組、ei2nの両端点と光の全履歴、ei2mの現在のK局所時計と全光速度適用範囲を結ぶ。同じ候補zd4をeizzとsjkへ渡す。',
  'zd3の引用により、同じ著者が同じ前提の下で現在の中点式ei2dをei2rへ同値な形に書き換えると読む。同じ第三節・論説・直前の提示との順序を保持する。',
  'K時刻をτへ交換せず、原点を全時刻で同じ位置にせず、t=0やx′=ξを補わない。局所数値例を一般物理法則の証明や具体的τ解の発見へ昇格させない。',
  '表示式の0,x′,0と零横座標を、この正方向往復の座標規約として明示する。x′>0と0<v<Vを置き、負の補助値を許す先行抽象往復へ商の正経過時間解釈を無条件に広げない。新規原始語はない。',
  '現在の座標・局所表示・全履歴への各接続を対照検査し、旧逆数と有理代数の証拠を保存する。検査通過と原文の通読判断を分け、全実数上の物理的含意は自動証明していない。',
  '先行の同じ中点条件、後続二行の展開式と微分への移行を含めて通読した。明示した原点と正方向の読みの下で、引数・適用する原理・書換え・著者と順序を欠落なく記述したと判断する。',
 ),
 (
  '固定u0052全7文字のM0100を原刊898頁とMathMLへ照合した。分子1・分母2、三つの零位置、同じt、V-vとV+vの二分母を保持する。数式単位なので本文文字には加算しない。',
  '左辺は出発値τ(0,0,0,t)と帰着値τ(0,0,0,t+x′/(V-v)+x′/(V+v))の和の半分である。係数・両項・四引数・二経過時間をすべて保持する。',
  '同じ関数zd4と試行zdqを使い、sjkで出発と帰着の実際の時計値へ結ぶ。K時刻は同じ現在の四座標と局所表示に一致し、二経過時間は同じ端点と光の完全履歴を前提に読む。',
  'この左辺だけを独立した真理主張にせず、u0053の右辺と一つの式ei2rにする。u0051の条件付き書換えei2sを述べる同じ著者主張ei2uを三単位で共有する。',
  '半分の欠落、往路と復路の分母交換、帰着で別関数や別の出発時刻を使うことを許さない。任意の符号のx′を正の経過時間へ読むことや、無条件な全域同義性を加えない。',
  '既存sjf/sjgとsitの切断の妥当性・和・正逆数・半尺度倍・数値等値を再利用する。正方向の光往復という明示した読みを用い、式ごとの新規原始語を追加しない。',
  '数式木、旧逆数構成と有理代数、正確な有理切断例と時刻原点をずらした対照を保持する。零や負のx′でも代数式だけは成立し得る対照により、代数式と物理的往復の範囲を区別する。',
  '前の中点式からの書換えと右辺を合わせて再読した。明示した同じ条件の下で左辺全体の三位置・時刻・半和・表示上の役割を欠落なく記述したと判断する。',
 ),
 (
  '固定u0053全7文字のM0101を原刊898頁とMathMLへ照合した。冒頭の等号、τの四引数、第一引数x′と第四引数t+x′/(V-v)、末尾の句点までを一式の右辺として読む。',
  '右辺は同じ反射値τ(x′,0,0,t+x′/(V-v))である。二つの零横座標、同じt、往路の商一つ、左辺との実数値の等値を保持する。',
  '同じ候補zd4の反射値を同じ試行のqjへ結ぶ。反射位置x′は同じK出来事のx-vtであり、往路の全履歴・同じ光速Vと速度v・現在の局所時刻に接続する。',
  'u0052の左辺から続く等号の右辺であり、独立したτの定義や解ではない。三単位共通のei2uにより、前の中点式を同じ前提の下で書き換えた著者の提示を保持する。',
  '反射値に復路分を加えず、分母をV+vにせず、第一引数を零やξへ替えない。式から具体的τ変換式や独立した実在する光試行を発見したとはしない。',
  '既存sjgの第二関数値を同じ四引数のまま使う。零横成分と正の補助位置という座標の読みを明示し、分割された数式ごとに新しい原始語を作らない。',
  '同じ関数の三回の呼出し、四引数、分母の符号と半分の係数を正確な有理切断で対照確認する。局所検査と旧代数は接続の証拠であり、一般実数法則や意味同値の自動証明ではない。',
  '左辺とu0051の書換え文、次の無限小の導入まで含めて再読した。明示した同じ試行の読みの下で右辺・等値・文の結びを欠落なく記述したと判断し、微分は次の範囲へ残す。',
 ),
)

@lru_cache(None)
def records():
    source=source_record();catalog=load_catalog(ROOT,BASIS)
    paths={FULL,CORE,BASIS,ANNOTATIONS,SOURCE,REPORT,INVENTORY,DOC,*PRIORS,*DEPENDENCIES,'scripts/review_light_time_expansion.py','tests/test_light_time_expansion_review.py'}
    pins={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)};merge_pins(pins,catalog.source_sha256)
    for p in (SOURCE,REPORT,*DEPENDENCIES):
        evidence=json.loads(read(p));validate_hashes(ROOT,evidence['source_sha256']);merge_pins(pins,evidence['source_sha256'])
    results=[]
    for i,s in enumerate(source['segments']):
        clauses=[];offset=0
        for text,symbols,reason in CLAUSES[i]:
            assert s['text'][offset:offset+len(text)]==text
            assert all(n in catalog.entries for n in symbols)
            clauses.append(dict(range=[offset,offset+len(text)],text=text,definitions=symbols,reason=reason));offset+=len(text)
        assert offset==len(s['text'])
        assert len(REASONS[i])==len(REQUIREMENTS)
        results.append(dict(schema_version='noema-semantic-review-1',work='einstein-1905',unit=s['unit'],reviewer='assistant_review',decision='equivalent_under_stated_reading',document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source=dict(inventory=INVENTORY,unit_sha256=s['unit_sha256'],text=s['text'],range=s['range'],math=[{k:m[k] for k in ('id','sha256')} for m in s['math']]),selection=selection_binding(catalog,[INDEX]),source_order_statements=[INDEX],clauses=clauses,interpretation=LIMITS,limits=['同じ文と左右の表示式を明示した解釈の下で通読したアシスタントの判断。独立査読、全実数上の物理的導出、同義性の自動証明ではない。','u0054以降の無限小と微分、具体的なτ変換式、二作品全体の目標は未完。'],unresolved=[],requirements=[dict(id=k,decision='satisfied',reason=v) for k,v in zip(REQUIREMENTS,REASONS[i])],evidence=dict(source_reading=[SOURCE],formal_checks=[REPORT,*DEPENDENCIES],semantic_reading=[DOC]),reviewed_prose_characters=s['source_nonblank_characters'],source_sha256=pins))
    return results


def prepare():
    from scripts.audit_opening_scope import write_exact
    for path,record in zip(REVIEWS,records()):write_exact(ROOT/path,json.dumps(record,ensure_ascii=False,indent=2)+'\n')


@lru_cache(None)
def build_report():
    active=dict(document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source_inventory=INVENTORY);catalog=load_catalog(ROOT,BASIS);inv=json.loads(read(INVENTORY));pins={}
    for path,record in zip(REVIEWS,records()):
        assert json.loads(read(path))==record
        validate_review(ROOT,path,'einstein-1905',active,catalog,inv);merge_pins(pins,record['source_sha256']);pins[path]=digest((ROOT/path).read_bytes())
    return dict(status='tau_argument_expansion_sentence_and_both_equation_halves_reviewed',document=FULL,source_units={'einstein-1905:u0051':116,'einstein-1905:u0052':0,'einstein-1905:u0053':0},reviewed_math_elements=3,whole_units_semantically_verified=True,verified_full_units={'kant-1784':0,'einstein-1905':3},general_physical_derivation_proved=False,concrete_tau_transformation_derived=False,semantic_equivalence_automatically_proved=False,source_sha256=pins)
