"""Record whole-unit readings of the affine time conclusion and its qualifications."""
from functools import lru_cache
import json
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import REQUIREMENTS,digest,selection_binding,validate_hashes,validate_review
from noema.review_registry import merge_pins
from scripts.compose_affine_time_claim import ROOT,read,FULL,CORE,BASIS,ANNOTATIONS,INDEX,LIMITS
from scripts.check_affine_time_claim import DOC,SOURCE,INVENTORY,PRIOR,DEPENDENCIES,source_record

REPORT='reports/affine-time-claim-v1.json'
REVIEWS=tuple(f'data/einstein-affine-time-u{n:04d}-review-v1.json' for n in (62,63,64))
CLAUSES=(
 (
  ('Aus diesen Gleichungen folgt, ',['ei4p','ei4r','skn','slm'],'先行する同じτの縦横偏微分条件から、後続の式が帰結として得られるという著者の提示を保持する。'),
  ('da [M0111] eine lineare Funktion ist:',['ei4o','ei4n','smr','smd'],'同じτの線形性を推論理由に加える。先行するアフィン性の読みと同じ五係数の延長・偏微分値を明示して接続する。'),
 ),
 (('[M0112],',['smn','smj','smi','smh','ei4t'],'τ=a(t−v*x′/(V²−v²))を同じ帰結の内容として保持し、コンマで続く係数と仮定の説明へ結ぶ。'),),
 (
  ('wobei [M0113] eine vorläufig unbekannte Funktion [M0114] ist ',['smj','smr','smp','smq','smb','ei4u','ei4w'],'式のaを同じφの同じvでの値として説明し、現在段階の候補複数性という明示した未知性の読みを保つ。'),
  ('und der Kürze halber angenommen ist, ',['ei4x','ug','zex'],'同じ箇所の追加説明として原点条件を仮定し、その理由を記述の簡潔さとする。無条件な物理法則に変えない。'),
  ('daß im Anfangspunkte von [M0115] für [M0116] [M0117] sei.',['ei4q','ei4l','ei4j','ei4g','ei4h','ei4i'],'同じk原点の出来事の現在二座標組でτ=0ならt=0を要求する。零点が存在する規約として読み、空間ラベルの選択は別条件として扱う。'),
 ),
)
REASONS=(
 (
  '固定u0062全67文字・51本文文字とM0111を原刊899頁へ照合した。先行する三つの偏微分条件と後続の具体式を含めて読んだ。',
  'diesen Gleichungenの先行参照、folgtの帰結、daの理由、同じτの線形性を保持する。ei4pは縦横条件、同じ係数と実際の偏微分値、後続で明示される原点仮定を結ぶ。',
  '同じzd4のτ、光速tc、速度zb7、先行出発時刻を用いる。現在のアフィン時間行と補助座標x′=x−vtをei4nへ結び、五係数のうち時間係数を同じφ(v)へ結ぶ。',
  'ei4rのzcで前提から式への著者の帰結を記述する。ei4tは同じ著者・論説・第三節へ帰属し、先行する横二式の提示に続ける。',
  '全測定入力上のアフィン性と全実数四入力への延長を区別し、後者は同じ式を使う明示的解釈とする。係数を入力ごとに選び直さず、原点仮定を微分だけからの帰結にしない。',
  'linearは先行箇所と同じアフィン表示の読みとする。実数値・微分・全空間の意味は既存の切断と極限による定義を用い、未説明の新規原始語で一文を置換しない。',
  '原刊、固定MathML、同じ係数と関数への結合検査、旧有理数係数補題を根拠にする。一般の微分一意性や実数体の定理、著者の物理的主張の真理を有限検査が証明したとはしない。',
  '先行方程式、線形性、表示式、後置された係数と仮定の説明を通読した。同じ係数による延長という解釈の下で、この導入文の全関係・参照・提示を欠落なく記述したと判断する。',
 ),
 (
  '固定u0063全8文字の表示式M0112とコンマを原刊899頁へ照合した。数式を除くコンマ一文字を本文集計に含める。',
  'τとa(t−v*x′/(V²−v²))の等号を保持する。aは括弧全体に掛かり、分母はV²−v²、xは補助座標x′であり、負号と二乗を保つ。',
  'smn/smjは同じτとφ、同じVとvを用い、aはφ(v)として評価する。前提smrも同じφ(v)を時間係数へ結び、前提と結論で別の候補関数へ交換しない。',
  'u0062に導かれる同じ著者の帰結内容である。単独の無条件な定義採用や検査器による導出へ変えず、末尾コンマに続くu0064の説明と合わせて読む。',
  '全有効四入力で同じ式を要求し、y,zへの隠れた依存や加法定数を結論に残さない。定数の除去は別の原点条件による。aの値・符号・最終速度関数をここで固定しない。',
  'smhの実切断の加減乗除とsmiの0≤v<V、全四入力の量化を使う。V²−v²の分母範囲と同じ係数を保持し、原語の数式画像の引用だけにしない。',
  '原刊と固定MathML、構成済み有理切断の代入、非零定数や横方向依存の反例を用いる。全実数の量化は拒否し、有限点での一致を全域の定理証明にしない。',
  '導入文から式、続くa=φ(v)と原点仮定まで再読した。明示したアフィン延長と原点規約の読みの下で、式全体の作用範囲・記号・参照と帰結の役割を欠落なく保持したと判断する。',
 ),
 (
  '固定u0064全155文字・98本文文字とM0113–M0117を原刊899頁へ照合した。全体を三範囲で保持し、直前の式から文末まで読んだ。',
  'wobeiによる係数の説明、暫定的未知性、速度関数φ(v)、undによる追加、簡潔さの理由、仮定の位置付け、k原点におけるτ=0ならt=0を保つ。',
  'aは直前の同じ式の時間係数、φは同じ速度域と考察段階の候補族へ結ぶ。kは同じ運動系、二時刻は同じ原点出来事と現在二座標組へ結び、異なる出来事の零値を混ぜない。',
  'ei4uは暫定的な未決定性の提示uh、ei4xは原点内容の仮定ugと同じ仮定の簡潔さzexである。式、未知係数、原点仮定を同じ著者・論説・第三節へ本文順に帰属する。',
  '未知は現在段階で異なる速度関数候補が残るという読みであり、唯一の解を知らないという知識一般には拡張しない。時刻規約の全称含意と非空の零点を保ち、別の空間原点規約を原文時刻条件の逐語的主張としない。',
  'smp/smq/smbは同じ許容速度域の候補と現在関数の値一致を記述する。ei4g–ei4lは測定・局所時計・全τ対応へ結ぶ。後段でφが確定する過程や全候補の物理的正しさを加えない。',
  '原刊と固定原文、同じ候補・速度・段階の対照例、原点の全称条件と別の零値の検査を用いる。現在の読解判断、有限の条件検査、一般の知識理論と物理的証明を区別する。',
  '直前の式を含め一文全体を再読し、未知性の採用解釈と時刻・空間原点の区別を明記した。その読みの下で係数・留保・理由・仮定・条件範囲・本文順序の欠落はないと判断する。',
 ),
)

@lru_cache(None)
def records():
    source=source_record();catalog=load_catalog(ROOT,BASIS)
    paths={FULL,CORE,BASIS,ANNOTATIONS,SOURCE,REPORT,INVENTORY,DOC,PRIOR,*DEPENDENCIES,'scripts/review_affine_time_claim.py','tests/test_affine_time_claim_review.py'}
    pins={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)};merge_pins(pins,catalog.source_sha256)
    for p in (SOURCE,REPORT,*DEPENDENCIES):
        evidence=json.loads(read(p));validate_hashes(ROOT,evidence['source_sha256']);merge_pins(pins,evidence['source_sha256'])
    out=[]
    for i,s in enumerate(source['segments']):
        clauses=[];offset=0
        for text,symbols,reason in CLAUSES[i]:
            assert s['text'][offset:offset+len(text)]==text and all(n in catalog.entries for n in symbols)
            clauses.append(dict(range=[offset,offset+len(text)],text=text,definitions=symbols,reason=reason));offset+=len(text)
        assert offset==len(s['text']) and len(REASONS[i])==len(REQUIREMENTS)
        indices=[INDEX] if i<2 else [INDEX,INDEX+1,INDEX+2]
        out.append(dict(schema_version='noema-semantic-review-1',work='einstein-1905',unit=s['unit'],reviewer='assistant_review',decision='equivalent_under_stated_reading',document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source=dict(inventory=INVENTORY,unit_sha256=s['unit_sha256'],text=s['text'],range=s['range'],math=[{k:m[k] for k in ('id','sha256')} for m in s['math']]),selection=selection_binding(catalog,indices),source_order_statements=indices,clauses=clauses,interpretation=LIMITS,limits=['明示したアフィン延長・未知性・原点規約の読みの下でのアシスタントの通読判断。独立査読、一般実数体や微分定理、物理的導出や同義性の自動証明ではない。','u0065以降と二作品全体の目標は未完。'],unresolved=[],requirements=[dict(id=k,decision='satisfied',reason=v) for k,v in zip(REQUIREMENTS,REASONS[i])],evidence=dict(source_reading=[SOURCE],formal_checks=[REPORT,*DEPENDENCIES],semantic_reading=[DOC]),reviewed_prose_characters=s['source_nonblank_characters'],source_sha256=pins))
    return out

def prepare():
    from scripts.audit_opening_scope import write_exact
    for path,r in zip(REVIEWS,records()):write_exact(ROOT/path,json.dumps(r,ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    active=dict(document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source_inventory=INVENTORY);catalog=load_catalog(ROOT,BASIS);inv=json.loads(read(INVENTORY));pins={}
    for path,r in zip(REVIEWS,records()):
        assert json.loads(read(path))==r
        validate_review(ROOT,path,'einstein-1905',active,catalog,inv);merge_pins(pins,r['source_sha256']);pins[path]=digest((ROOT/path).read_bytes())
    return dict(status='affine_time_formula_and_qualifications_whole_units_reviewed',document=FULL,source_units={s['unit']:s['source_nonblank_characters'] for s in source_record()['segments']},reviewed_math_elements=7,whole_units_semantically_verified=True,verified_full_units={'kant-1784':0,'einstein-1905':3},general_real_physical_derivation_proved=False,semantic_equivalence_automatically_proved=False,source_sha256=pins)
