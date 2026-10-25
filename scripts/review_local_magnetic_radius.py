"""Record complete readings of the third item, its two displays and oder."""
from functools import lru_cache
from pathlib import Path
import json
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import REQUIREMENTS,digest,selection_binding,validate_hashes,validate_review
from noema.review_registry import merge_pins
ROOT=Path(__file__).resolve().parents[1]
def read(path):return (ROOT/path).read_text(encoding='utf-8')
FULL='examples/v014/einstein-local-magnetic-radius.noema';CORE='examples/v014/local-magnetic-radius-core.noema'
BASIS='data/local-magnetic-radius-basis-v1.json';ANNOTATIONS='data/local-magnetic-radius-identifiers-v1.json'
SOURCE='data/einstein-local-magnetic-radius-reading-v1.json';REPORT='reports/local-magnetic-radius-v1.json'
INVENTORY='artifacts/written-units-v1/einstein-1905.json';DOC='docs/local-magnetic-radius-v1.md'
REVIEWS=['data/einstein-local-magnetic-radius-u'+str(n).zfill(4)+'-review-v1.json' for n in range(271,275)]
CLAUSES=(
 (
  ('3. ',['eislk','es7'],'同じ実験的性質の列挙の第三項という位置を保持する。列挙導入の全文判断は別途残る。'),
  ('Wir berechnen den Krümmungsradius [M0439] der Bahn, ',['sevc','esp','es4','es6','eiszy','eisnw','es7'],'同じ著者の計算の取組として、同じ実軌道の局所曲率の逆数である正の半径を問う。実三速度と二階微分、座標長さと同じ単位・尺度へ結び、Rの呼称を保つ。候補質問へ答えの磁場公式を先取りせず、実測済みともしない。'),
  ('wenn eine senkrecht zur Geschwindigkeit des Elektrons wirkende magnetische Kraft [M0440] ',['ejsn','eico','ek3q','eso','esw','es5','ug','eisnw'],'同じ電子・K・局所出来事の実速さと磁場Nを、瞬間速度(v,0,0)、磁場(0,0,N)という垂直配置へ結ぶ。Nは単位に校正された磁場成分で、機械的磁気力−qvN/Vとは区別する。wennはその物理的事例の条件設定として提示する。'),
  ('(als einzige ablenkende Kraft) ',['eis4t','esm','esn','eta','eisa5'],'同じ出来事の全ての実際の非磁気的作用源の寄与が接線方向に限られるという排他条件を括弧の挿入として保つ。横電場零だけ、観測した寄与の一覧だけ、他の横力が相殺した総和零だけでは代用しない。'),
  ('vorhanden ist. ',['eso','esn','esp','esw','ug'],'同じ物理的磁場・作用・実軌道が存在する事例であるという条件を閉じる。作用のない名前だけのN、別の電子又は出来事の力を接続しない。接線電場と接線加速度は許す。'),
  ('Aus der zweiten der Gleichungen (A) erhalten wir:',['ess','est','esx','esy','esz','eis3v','eiswm','zc','uf','es7','etb','etc'],'同じ(A)の第二行を、同じ事例の横加速度・質量・電荷・速度・磁場へ適用する。第二という序数と先行式への照応を保持し、局所幾何と同じ条件の下で次の等号列を得る著者の推論とコロンを接続する。'),
 ),
 (
  ('[M0441]',['ek3q','sevc','esp','ess','esq','esu','esz','etd','ete','etf','eisox','uh'],'−d²y/dt²＝v²/R＝(q/μ)(v/V)N√(1−(v/V)²)を全て記述する。yの座標時刻二階微分は同じ実軌道のayであり、先頭負号、両等号、正の半径、q/μ、v/V、Nと平方根を保つ。qN>0の印刷方向を明示し、接線加速度を零に限定しない。'),
 ),
 (
  ('oder',['est','esy','esz','es2','es3','zd3','etg','eth','eti','uf','uh'],'同じ実曲率・方向・単位・第二(A)を前提として、直前の全等号列を直後の半径式へ同値に書き換える提示。前提を共有しない無条件同値、真偽の排他的選言、別事例の代案とはしない。'),
 ),
 (
  ('[M0442]',['esp','esr','esv','es2','etj','etk','etl','eisox','uh'],'R＝V²(μ/q)(v/V)/√(1−(v/V)²)/Nを同じ局所半径へ結ぶ。V²、μ/q、内側のv/V、平方根による除算、1/Nと正のR・非零分母を保持する。Nとqをそれぞれ絶対値へ替えず、前のoderと同じ著者・論説・事例へ続ける。'),
 ),
)

@lru_cache(None)
def records():
    catalog=load_catalog(ROOT,BASIS);source=json.loads(read(SOURCE));basis=json.loads(read(BASIS))
    paths={FULL,CORE,BASIS,ANNOTATIONS,SOURCE,REPORT,INVENTORY,DOC,'scripts/review_local_magnetic_radius.py','tests/test_local_magnetic_radius_review.py'}
    pins={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)};merge_pins(pins,catalog.source_sha256)
    for path in (SOURCE,REPORT):
        e=json.loads(read(path));validate_hashes(ROOT,e['source_sha256']);merge_pins(pins,e['source_sha256'])
    output=[]
    source_reasons=(
     '原刊921頁u0271を第二項の表示と第三項最初の表示の間で照合した。番号3、Wir berechnen、Krümmungsradius R der Bahn、wenn、senkrecht zur Geschwindigkeit des Elektrons、magnetische Kraft N、括弧内のals einzige ablenkende Kraft、vorhanden ist、Aus der zweiten der Gleichungen (A) erhalten wirとコロンを保持する。',
     '原刊921頁u0272とM0441を照合した。−d²y/dt²、v²/R、(q/μ)(v/V)N√(1−(v/V)²)の三項と二つの等号、先頭の負号、分母・平方・根号を保存する。単に最終の半径式だけでこの表示を代用しない。',
     '原刊921頁u0273のoderを、M0441とM0442の間にある独立した書換えの語として照合した。文字列だけ又は二つの表示の順序だけで代用せず、同じ前提の下での同値書換えを記述する。',
     '原刊921頁u0274とM0442を照合した。R、等号、V²、μ/q、(v/V)/√(1−(v/V)²)、1/Nと句点を保持し、前のoderと同じ局所半径の表示へ結ぶ。',
    )
    for i,s in enumerate(source['units']):
        selection=[437+i];offset=0;clauses=[]
        for text,symbols,reason in CLAUSES[i]:
            assert s['text'][offset:offset+len(text)]==text,offset
            assert all(n in catalog.entries for n in symbols)
            clauses.append(dict(range=[offset,offset+len(text)],text=text,statements=selection,definitions=symbols,reason=reason));offset+=len(text)
        assert offset==len(s['text'])
        reasons=(
         source_reasons[i],
         'ek3qと既存の実微分、ejsnと二つの力の物理的作用、低速質量・符号付き電荷・整合単位をesoへ共有し、全作用源の排他条件をesm/esnへ合成する。espは同じ実三速度・三加速度のsevcを正の局所半径へ結ぶ。essの第二(A)、esq/esrの印刷式、条件付き同値es3、量質問と著者の提示を分けて構成する。',
         '第三項の新しい局所軌道・出来事・位置・二場・二力記録を同じ電子・K・μ・q・V・速度・単位へ結ぶ。静電加速の全軌道を流用しない。Rは座標と同じ長さ尺度、Nは同じ実磁場の同じ出来事のz成分。全ての非磁気的作用源について同じframe・event・forceunitで判断し、別の場又は他の出来事の無偏向を代用しない。',
         '第三項の序数、半径計算の取組と候補質問、R/Nの呼称、wennの設定と括弧の挿入を保持する。第二(A)への序数・照応とそこからの著者の導出、二つの表示、同じ前提でのoderの書換え、同じ著者・論説・本文順序を分ける。引用内容の真理や実験実施を提示だけから認定しない。',
         '瞬間速度を正x、磁場をz、曲率の瞬間法平面をxy面に選ぶ標準配置として読む。正のRと印刷の−ayの向きにqN>0を対応させ、q,Nがともに負の例も保持する。接線電場・接線加速度・接線方向の他の力を許す。全軌道の円・平面性・等速・一様場は追加せず、静止又は曲率零の有限半径も追加しない。Nの絶対値への無断修正や原文にない現代の電子電荷固定はしない。',
         '新基本関係eis4tは、同じ物理的作用源の機械的寄与を同じ単位の力ベクトルに帰属する一般的関係だけを担う。全ての作用源への量化と磁気的分類・非磁気的寄与の接線条件、実場・実軌道・局所曲率・単位・数式・導出と書換えは合成する。唯一性や全文を原始記号へ埋め込まず、相殺した横力や未観測の寄与を除外条件の外へ落とさない。',
         '数値検査は正負の電荷と磁場、非単位質量、誤った半径・加速度方向、零分母と未知根号を対照する。排他条件は全記録の個体量化を実評価し、相殺する横力も個別に拒否する。実微分を別途評価し、接線加速度を変えても半径が変わらないこと、同じ正の長さ尺度、第二(A)がない場合の式の非同値、引用の非実行を確認する。全関数域は有限評価を拒否し、旧437主張・意味・判断を保存する。',
         '第三項の導入から二表示とoderまでを、前の電位差の項と後の三関係の総括の間で再読した。実際に何が曲がり、どの物理的寄与だけが偏向させ、どの局所半径をどの単位で求めるか、第二(A)と全等号、符号・同一性・同値書換えが揃っている。各対象単位を明示した解釈の下で欠落なく記述できたと判断する。これはアシスタントの意味判断であり、独立査読・物理的真理・同義性の自動証明ではない。',
        )
        assert len(reasons)==len(REQUIREMENTS)
        output.append(dict(schema_version='noema-semantic-review-1',work='einstein-1905',unit=s['unit'],reviewer='assistant_review',decision='equivalent_under_stated_reading',document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source=dict(inventory=INVENTORY,unit_sha256=s['unit_sha256'],text=s['text'],range=s['range'],math=[{k:m[k] for k in ('id','sha256')} for m in s['math']]),selection=selection_binding(catalog,selection),source_order_statements=selection,clauses=clauses,interpretation=basis['limitations'],limits=['明示した解釈の下でのアシスタントによる全文判断。独立査読、物理的真理又は原文同義性の自動証明ではない。','u0265の列挙導入とu0275の三関係の総括、後続の結語は別途残る。'],unresolved=[],requirements=[dict(id=k,decision='satisfied',reason=v) for k,v in zip(REQUIREMENTS,reasons)],evidence=dict(source_reading=[SOURCE],formal_checks=[REPORT],semantic_reading=[DOC]),reviewed_prose_characters=s['source_nonblank_characters'],source_sha256=pins))
    return output

def prepare():
    from scripts.audit_opening_scope import write_exact
    for path,r in zip(REVIEWS,records()):write_exact(ROOT/path,json.dumps(r,ensure_ascii=False,indent=2)+'\n')
@lru_cache(None)
def build_report():
    rows=records();catalog=load_catalog(ROOT,BASIS);inventory=json.loads(read(INVENTORY));active=dict(document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source_inventory=INVENTORY);pins=dict(rows[0]['source_sha256'])
    for path,r in zip(REVIEWS,rows):
        assert json.loads(read(path))==r;validate_review(ROOT,path,'einstein-1905',active,catalog,inventory);pins[path]=digest((ROOT/path).read_bytes())
    return dict(status='local_magnetic_radius_whole_units_reviewed',document=FULL,source_units={r['unit']:r['reviewed_prose_characters'] for r in rows},reviewed_math_elements=4,whole_units_semantically_verified=True,verified_full_units={'kant-1784':0,'einstein-1905':4},semantic_equivalence_automatically_proved=False,source_sha256=pins)
