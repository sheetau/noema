"""Record four whole-unit readings of the ninth-section transformation."""
from functools import lru_cache
from pathlib import Path
import json
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import REQUIREMENTS,digest,selection_binding,validate_hashes,validate_review
from noema.review_registry import merge_pins
ROOT=Path(__file__).resolve().parents[1]
def read(path):return (ROOT/path).read_text(encoding='utf-8')
FULL='examples/v014/einstein-convective-transformation-claim.noema';CORE='examples/v014/convective-transformation-claim-core.noema'
BASIS='data/convective-transformation-claim-basis-v1.json';ANNOTATIONS='data/convective-transformation-claim-identifiers-v1.json'
SOURCE='data/einstein-convective-transformation-reading-v1.json';REPORT='reports/convective-transformation-claim-v1.json'
INVENTORY='artifacts/written-units-v1/einstein-1905.json';DOC='docs/convective-transformation-claim-v1.md'
REVIEWS=tuple(f'data/einstein-convective-transformation-u{n:04d}-review-v1.json' for n in range(233,237))
CLAUSES=(
 (('Transformiert man diese Gleichungen, ',['ek2a','eiswm','ekzc','ekzx','eisqt','s46','s6k','s6l'],'先行導入eiswfの同じ原系方程式を対象とし、同じ二系の座標と両場の変換を用いる。一般のmanを特定の実験者や実施済みの操作に替えない。'),
  ('welche im System [M0387] gelten mögen, ',['ek2a','ug','ekzc','ekz3','ekyz','ra'],'Kで同じ方程式が成立するものとして議論を進める仮定。先行の物理的解釈と法則を共有し、現実の測定又はKだけで成立する限定を加えない。'),
  ('mit Hilfe der Transformationsgleichungen von § 3 und § 6 ',['ek2a','eisov','eisms','ejeh','zno','ejvm','ekzx'],'同じ論説の第三節の最終座標式と第六節の最終場変換を現在の同じ設定へ用いる。二つの節とその内容を保持する。'),
  ('auf das System [M0388], ',['ekzx','zbm','eisqt','s6m','ejsn'],'行先をkとし、同じ逆写像で場の引数と領域を変更して新系の物理的な場へ接続する。Kの同じ数値座標をそのまま使わない。'),
  ('so erhält man die Gleichungen:',['ek2a','zc','ekz3','ekz7','ekz6','ek2b','eisox'],'元の方程式と現在の変換設定から結果を得るという著者の提示として、後続の六式とその五等式の補足へ接続する。双方向の同値性又は検証済みの導出へ強めない。')),
 (('[M0389]',['ekz4','ekzz','s5u','semf','semc','s5v','ekzu','ekzv','s6k','s6l','s6m','eisox'],'同じ新二場・新座標・領域・ρ′・三流速を使う三行二列の六式。18偏微分、電気側の1/Vと対流項、磁気側の符号と印刷された係数を保持する。'),),
 (('wobei',['ek2b','uf','eiswo','ekz5'],'六式に使う同じ新密度と三速度を後続の五等式で補足する接続として読む。独立した別の法則や削除可能な区切りへ替えない。'),),
 (('[M0390]',['ekz5','ekz2','ekzy','sent','sens','semt','semd','s5t','ekzr','ekzs','ekzt','ekzu','ekzv','eisox','uh'],'三速度の分数と、同じρ′の発散・変換の二関係を五等式として保持する。正のβと非零分母、三対角偏微分、旧新の同一地点対応、符号付き密度を保つ。'),),
)
SEMANTICS=(
 'ek2aはugの原系成立仮定、先行ekzcへの照応、二つの節の最終則の使用を一つの導出提示zcへ結ぶ。ekz3はekzxの同じ全設定で旧法則ekyqを要求し、ekz7は同じ設定で六式と五等式の結果を要求する。ekzxが現在の物理的な系・単位・場・正逆座標対応へ両変換を適用するため、節番号の引用だけで変換の意味を済ませない。',
 'ekzzはs6k/s6lで変換した二場とs6mの同じ逆像領域について、全有効新点で18偏微分s5uと印刷semfを満たす二微分表を要求する。ρ′と三速度は同じekzv/ekzuから取る。電気側の対流項とV、磁気側の時間微分と回転の符号を保持し、印刷の1/V欠落を修正しない。ekz4がその表示内容を現在の設定へ閉じる。',
 'ek2bは導入から六式、そこからwobei、そこから五等式へ続く同じ著者の説明ufを保持する。ek2cが四箇所の区別と順序を保つ。前文の密度定義を導いた別のwobeiを使わず、この六式に現れる同じ新量の補足として範囲を固定する。',
 'ekzyは同じ新点の逆像で元のρと三速度を取り、同じβ、同じ新ρ′と三速度、同じ新電場・領域・新点・新電気微分表をsentへ渡す。sensは三速度と密度変換semt及び同じ新密度の電気発散semd、sentはその三対角値を実際のs5tへ結ぶ。ekz2が全新領域、ekz5が同じ全設定についての表示内容を閉じ、uhとeisoxが著者の補足提示へ接続する。',
)
WHOLE=(
 '原刊の一文を先行のK方程式と後続の二表示へ戻して全文再読した。diese、Kでの成立仮定、§3と§6を手段とする変換、kを行先とすること、so erhält manの結果提示とコロンの表示接続を保持したと判断する。manの非人称の導出を特定人物の実験に替えず、現在の変換設定を全称内容へ結ぶ採用読解である。',
 '三行二列の六式について、全ての左辺、18偏微分の成分と軸、右辺の差の順、三つの1/V、同じρ′と各uξ/uη/uζを原刊と固定MathMLへ照合して再読した。磁気側の係数欠落を含め、印刷された六式全体を保持したと判断する。導出の物理的妥当性についての判断ではない。',
 'wobeiを直前の六式と直後の三速度及びρ′の連鎖式まで続けて再読した。同じ式に使う量の説明という役割と指示範囲を保持したと判断する。原刊上の行間を新しい独立主張へ変えていない。',
 '三速度の各分子・分母・軸と、ρ′の二つの等号、三偏微分の和、β(1−v ux/V²)ρを全て再読した。K/kの同じ出来事の座標対応の下で五等式を保持したと判断する。新速度の測定解釈を次文から前提へ逆流させず、密度零でも速度式を残し、同じ新密度を六式と共有する。',
)

@lru_cache(None)
def records():
    catalog=load_catalog(ROOT,BASIS);source=json.loads(read(SOURCE));basis=json.loads(read(BASIS));out=[]
    paths={FULL,CORE,BASIS,ANNOTATIONS,SOURCE,REPORT,INVENTORY,DOC,'scripts/review_convective_transformation_claim.py','tests/test_convective_transformation_claim_review.py'}
    pins={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)};merge_pins(pins,catalog.source_sha256)
    for p in (SOURCE,REPORT):
        evidence=json.loads(read(p));validate_hashes(ROOT,evidence['source_sha256']);merge_pins(pins,evidence['source_sha256'])
    assert len(source['segments'])==4;binding=selection_binding(catalog,[410])
    for i,s in enumerate(source['segments']):
        clauses=[];offset=0
        for text,symbols,reason in CLAUSES[i]:
            assert s['text'][offset:offset+len(text)]==text,(i,offset,text)
            assert all(n in catalog.entries for n in symbols)
            clauses.append(dict(range=[offset,offset+len(text)],text=text,statements=[410],definitions=symbols,reason=reason));offset+=len(text)
        assert offset==len(s['text'])
        reasons=(
            f"固定{s['unit']}の全範囲と数式{[m['id'] for m in s['math']]}を原刊916頁へ照合した。原文・MathML・原刊像をハッシュで固定し、四単位を同じ一文の前後関係へ接続した。",
            SEMANTICS[i],
            '同じ先行方程式ekzc、K=ra、k=zbm、V=tc、長さta・時間rb・速度tb、同じ元の二場・分布・密度・流速と変換後の関数を共有する。ekz3/4/5/7では物理的contextを評価点に固定し、他の32引数を全称量化する。元の法則は同じGLOBAL32、二結果は同じSETTING33へ結ぶ。新旧の同じ数値四組を出来事の同一性の代用にしない。',
            '原系での成立はugによる議論の仮定、dieseは先行内容への照応、二節は確定した内容の使用参照、得るという叙述はzcによる著者の推論提示、数式はeisox、五等式はuhによる補足、wobeiはufによる説明接続として区別する。eir3で同じ著者と論説へ一文を帰属し、提示の評価で物理内容を実行しない。',
            '磁気側の1/V欠落を印刷どおり保存し、磁気側発散零や担体付着、新系で測った速度の同定、総電荷不変を前提に足さない。明示した分数の適用域を対象領域全体に要求し、分母零の点だけを隠して除かない。D>0、流速の上限、正の密度、逆向きの同値推論や現実の実験実施を追加しない。',
            '電荷と流速の物理的意味、同じ二系の全座標規約、場の単位・力との対応、逆像領域、実数演算・偏微分、先行の内容と著者の推論帰属を既存の定義・一般関係で説明する。追加する二原始記号は本文箇所の参照のみで、原文の一文を未分析の原始命題へ収納しない。',
            '四つの閉じた内容の全量化位置と同じcontext、結果二式の全引数、仮定・照応・両節参照・推論・表示・補足・説明・順序・著者帰属を対照する。元の変換量の数値と引数接続の証拠を引き継ぎ、原刊の式の18偏微分・三つの1/V・五等号を別に照合する。検査通過だけで原文同義性、連続体全域の物理法則、導出の正しさを認定しない。',
            WHOLE[i],
        )
        assert len(reasons)==len(REQUIREMENTS)
        out.append(dict(schema_version='noema-semantic-review-1',work='einstein-1905',unit=s['unit'],reviewer='assistant_review',decision='equivalent_under_stated_reading',document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source=dict(inventory=INVENTORY,unit_sha256=s['unit_sha256'],text=s['text'],range=s['range'],math=[{k:m[k] for k in ('id','sha256')} for m in s['math']]),selection=binding,source_order_statements=[410],clauses=clauses,interpretation=basis['limitations'],limits=['明示した読みの下でのアシスタントによる全単位判断。独立査読や原文同義性の自動証明ではない。','印刷された式と著者の導出提示を記述することは、物理的真理又は導出の健全性を証明することとは別である。','二作品全体の目標は未完。'],unresolved=[],requirements=[dict(id=k,decision='satisfied',reason=v) for k,v in zip(REQUIREMENTS,reasons)],evidence=dict(source_reading=[SOURCE],formal_checks=[REPORT],semantic_reading=[DOC]),reviewed_prose_characters=s['source_nonblank_characters'],source_sha256=pins))
    return out

def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,r in zip(REVIEWS,records()):write_exact(ROOT/p,json.dumps(r,ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    catalog=load_catalog(ROOT,BASIS);inventory=json.loads(read(INVENTORY));active=dict(document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source_inventory=INVENTORY);pins={}
    for p,r in zip(REVIEWS,records()):
        assert json.loads(read(p))==r;validate_review(ROOT,p,'einstein-1905',active,catalog,inventory)
        merge_pins(pins,r['source_sha256']);pins[p]=digest((ROOT/p).read_bytes())
    return dict(status='convective_transformation_four_whole_units_reviewed',document=FULL,source_units={r['unit']:r['reviewed_prose_characters'] for r in records()},reviewed_math_elements=4,whole_units_semantically_verified=True,verified_full_units={'kant-1784':0,'einstein-1905':4},semantic_equivalence_automatically_proved=False,source_sha256=pins)
