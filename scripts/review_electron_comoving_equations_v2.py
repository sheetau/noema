"""Read the initial equations and transformations as four whole source units."""
from functools import lru_cache
from pathlib import Path
import json
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import REQUIREMENTS,digest,selection_binding,validate_hashes,validate_review
from noema.review_registry import merge_pins
ROOT=Path(__file__).resolve().parents[1]
def read(path):return (ROOT/path).read_text(encoding='utf-8')
FULL='examples/v014/einstein-electron-comoving-equations-v2.noema';CORE='examples/v014/electron-comoving-equations-v2-core.noema'
BASIS='data/electron-comoving-equations-basis-v2.json';ANNOTATIONS='data/electron-comoving-equations-identifiers-v2.json'
SOURCE='data/einstein-electron-comoving-equations-reading-v2.json';REPORT='reports/electron-comoving-equations-v2.json'
INVENTORY='artifacts/written-units-v1/einstein-1905.json';DOC='docs/electron-comoving-equations-v2.md'
REVIEWS={n:f'data/einstein-electron-comoving-equations-u{n:04}-review-v2.json' for n in range(246,250)}
CLAUSES={
246:(
 ('Aus der oben gemachten Voraussetzung in Verbindung mit dem Relativitätsprinzip ',['ek35','eifj','ek7n','ek7o','eisra','eisch'],'前に採った同じ瞬間静止時の法則と同じ相対性原理を結んだ前提。仮定の採用箇所への照応と、相対性原理という呼称をその同じ内容へ結ぶ。'),
 ('ist klar, daß sich das Elektron ',['ek7o','zc','uh','zdg','eisxh','ek6z'],'同じ電子について、著者が同じ帰結を述べ、前提から従うもの・明白なものとして提示する。機械的な証明済みにはしない。'),
 ('in der unmittelbar folgenden Zeit (für kleine Werte von [M0406]) ',['ek74','ek7a','ek7b','ek7c','ek32','ek63'],'原刊も電子テキストもM0406はtである。Kの同じ出来事からの右側初期変化をek74のo(Δt)へ結び、kの微分変数τはek7cのo(Δτ)で別に保持する。両履歴は同じ出来事対応を共有し、全時間の厳密式へ広げない。v1の原刊τという照合判断は撤回する。'),
 ('vom System [M0407] aus betrachtet nach den Gleichungen bewegt:', ['ek6z','ek7c','ek7m','ek7o','ek7q','eisxy','eisox'],'同じkの校正された物理設定・実二階微分・電場に対する初期三式を、次の表示へ接続する。Kの加速度や旧節の別のkへ取り違えず、コロンの予告と著者帰属を保持する。'),
),
247:(
 ('[M0408]', ['ek7m','ek7c','ek3t','ek3s','ek3v','sepp','ek32','ek7k','eisox'],'三行のμ d²ξ/dτ²=εX′、μ d²η/dτ²=εY′、μ d²ζ/dτ²=εZ′を同じkの実座標時刻二階微分と同じ点の電場へ結ぶ。三軸をそれぞれ比較し、同じ電荷・低速慣性質量・単位を共有する。前文の初期運動という範囲を保った表示であり、有限区間に無条件の厳密式を要求しない。'),
),
248:(
 ('wobei die Zeichen [M0409] sich auf das System [M0410] beziehen. ',['ek7d','ek7e','ek7f','ek7g','ek7h','ek7k','ek7r','eiswy','eiswz'],'原刊のξ,η,ζ,τ,X′,Y′,Z′を同じkの物理設定から射影する意味説明。電子テキストM0409のτ脱落を記録し、座標三成分・座標時刻・場三成分を混ぜない。'),
 ('Setzen wir noch fest, daß für [M0411] [M0412] sein soll, ',['ek6f','ek62','ek63','ek7l','ek7t','ug','eisra'],'前の同じ座標選択へ、Kのt=x=y=z=0にkのτ=ξ=η=ζ=0を対応させる追加設定を採る。全四原点ずれを零へ結び、前のkを別の系に変更しない。'),
 ('so gelten die Transformationsgleichungen der §§ 3 und 6, ',['ek7u','ek73','ek72','ek7y','ek7z','eisov','ejeh','ejvm','zc','uh'],'第三節の最終四座標変換と第六節の最終場変換を参照し、この同じ追加設定に対して全変換が成り立つと提示する。全適用は磁場三式を含み、直後の七式だけに縮めない。旧節の特定の系・速度をそのまま代入せず、現在の同じV,vで構成する。'),
 ('so daß gilt:', ['ek7s','ek7u','ek7v','ek7x','eisox'],'続く七式を同じ変換の帰結として表示する。wobeiから二文目のコロンまでを本文順序・説明・引用・著者帰属へ接続する。'),
),
249:(
 ('[M0413]', ['ek65','ek66','ek64','ek6x','ek6y','s46','s6i','ek7s','ek7u','ek7i','ek7j'],'τ=β(t−vx/V²)、ξ=β(x−vt)、η=y、ζ=zの四式と、X′=X、Y′=β(Y−vN/V)、Z′=β(Z+vM/V)の三式を全て保持する。同じ旧点を新点へ写し、実新電場の値を同じ旧点での二場の混合へ結ぶ。βの正の根、同じV,v、符号、分母、全領域の範囲を保ち、表示されていない磁気側三式を追加しない。'),
),
}

@lru_cache(None)
def records():
    catalog=load_catalog(ROOT,BASIS);source=json.loads(read(SOURCE));basis=json.loads(read(BASIS))
    paths={FULL,CORE,BASIS,ANNOTATIONS,SOURCE,REPORT,INVENTORY,DOC,'scripts/review_electron_comoving_equations_v2.py','tests/test_electron_comoving_equations_review_v2.py'}
    pins={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)};merge_pins(pins,catalog.source_sha256)
    for path in (SOURCE,REPORT):
        evidence=json.loads(read(path));validate_hashes(ROOT,evidence['source_sha256']);merge_pins(pins,evidence['source_sha256'])
    results=[]
    for n,s in zip(range(246,250),source['units']):
        index=419 if n<248 else 420;clauses=[];offset=0
        for text,symbols,reason in CLAUSES[n]:
            assert s['text'][offset:offset+len(text)]==text,(n,offset,text)
            assert all(x in catalog.entries for x in symbols)
            clauses.append(dict(range=[offset,offset+len(text)],text=text,statements=[index],definitions=symbols,reason=reason));offset+=len(text)
        assert offset==len(s['text']) and s['unit']==f'einstein-1905:u{n:04}'
        reasons=(
         f'固定u{n:04}の全文範囲と全数式要素を、前後のu0246–u0249とともに原刊918頁へ照合した。二つの文章による導入・意味説明・原点選択と二つの表示式を一続きに読み、原文単位の境界は保持する。原刊もM0406はtであり、v1の原刊τという誤った照合判断を撤回する。M0409のτ脱落という電子テキストとの差は保持する。旧記録と固定在庫を改変せず訂正版で全四単位を再判断する。',
         '同じKの設定と前の共動配置から、同じ電子・出来事・電荷・低速慣性質量・単位を共有するkの物理設定を構成した。新電場・磁場・電荷記録・三速度関数・三加速度は独立の証人であり、実際の場と二階微分に結ぶ。三運動式と場変換の一致を前提にせず帰結側で述べる。七式は全領域の同一出来事の座標・場の値へ結ぶ。',
         '電子eisxh、出来事eisxv、k=eisxy、v=eisxt、新時間域eisx2・新曲線eisx3は前文から同じ参照を保つ。全42設定引数を前件と帰結で共有する。ξ,η,ζ、τ、三つの新電場成分、μとε、βとVを同じ物理設定と射影へ接続し、前節の別の具体的なk・速度や別出来事の量を混ぜない。',
         '前の仮定と相対性原理からの帰結をzc、同じ内容の主張をuh、明白さをzdgへ結ぶ。三式の表示eisox、wobeiの説明uf、原点の追加採用ug、前の設定への照応eisra、第三節と第六節への参照eisov、七式の表示と本文順序ueを区別する。これらの帰属から引用された物理内容の真理を実行しない。',
         '小さいtはKの同じ指定出来事からの初期運動として読む。ek74で旧三速度の剰余o(Δt)を明示し、kの同じ出来事ではo(Δτ)と実二階微分を保持する。両履歴の同じ出来事対応と正の初期時刻変化率を共有し、tとτを同じ変数とはしない。有限区間にわたる厳密な運動式・全時間の静止・加速度一定を補わない。新電場の一致は全新領域、七式は全旧領域とする。0≤v<V、正のVとβ、同じ整合単位を明示し、表示にない磁気側の三式を足さない。',
         '新しい原始記号は表記と本文箇所への参照に限る。実際の場、校正、電荷と低速慣性質量、履歴、微分、極限、原点、変換関数、仮定、帰結、明白さ、説明と著者帰属を既存関係から合成する。新電場を変換結果として最初から定義したり、加速度を運動方程式から定義したりしない。両時間の初期剰余は差と商と右側の実極限で構成する。Kの初期変化をkの関数・原点・加速度で代用しない。',
         '局所検査は非一様場の逆座標引戻しと混合符号、四原点と七式、同じ全設定引数、独立の新場、実数演算による三運動式、登録した解析的多項式の初期剰余、提示の同一引用・作用範囲・順序を対照する。Kの初期条件を欠く例と旧新の時間域・速度関数・加速度の取り違えを拒否する。38証人の結合は他を固定した二値診断である。未知入力と全実数・全関数域の有限認定を拒否し、有限例を連続体や原文同義性の自動証明にしない。',
         f'u{n:04}を原刊の前後とともに再読し、各句又は表示式の全行を記録した。前の仮定と相対性原理による同じkの初期三式、記号の同じ系への帰属、追加の四原点選択、先行二節の変換の適用と七式という内容と提示を保持したと判断する。原刊の小さいtとkの微分変数τを区別した初期運動という読みを明示した全単位判断であり、後続のKの運動式の完成を含めない。',
        )
        assert len(reasons)==len(REQUIREMENTS)
        results.append(dict(schema_version='noema-semantic-review-1',work='einstein-1905',unit=s['unit'],reviewer='assistant_review',decision='equivalent_under_stated_reading',document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source=dict(inventory=INVENTORY,unit_sha256=s['unit_sha256'],text=s['text'],range=s['range'],math=[{k:m[k] for k in ('id','sha256')} for m in s['math']]),selection=selection_binding(catalog,[index]),source_order_statements=[index],clauses=clauses,interpretation=basis['limitations'],limits=['明示した読みの下でのアシスタントによる全単位判断。独立査読、物理法則の真理、原文同義性の自動証明ではない。','v1のM0406の照合判断を撤回する。原刊もtであり、M0409のτ脱落だけを電子テキストとの差として保持する。小tとkのτ微分を別々の初期剰余へ結び、有限区間の厳密式とはしない。','後続のKへの変換、法則の答えへの接続、第十節見出しと二作品全体の目標は未完。'],unresolved=[],requirements=[dict(id=k,decision='satisfied',reason=v) for k,v in zip(REQUIREMENTS,reasons)],evidence=dict(source_reading=[SOURCE],formal_checks=[REPORT],semantic_reading=[DOC]),reviewed_prose_characters=s['source_nonblank_characters'],source_sha256=pins))
    return results
def prepare():
    from scripts.audit_opening_scope import write_exact
    for n,record in zip(range(246,250),records()):write_exact(ROOT/REVIEWS[n],json.dumps(record,ensure_ascii=False,indent=2)+'\n')
@lru_cache(None)
def build_report():
    catalog=load_catalog(ROOT,BASIS);inventory=json.loads(read(INVENTORY));active=dict(document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source_inventory=INVENTORY);pins={}
    for n,r in zip(range(246,250),records()):
        assert json.loads(read(REVIEWS[n]))==r;validate_review(ROOT,REVIEWS[n],'einstein-1905',active,catalog,inventory);merge_pins(pins,r['source_sha256']);pins[REVIEWS[n]]=digest((ROOT/REVIEWS[n]).read_bytes())
    return dict(status='four_whole_units_rereviewed_after_original_small_t_correction',document=FULL,source_units={r['unit']:r['reviewed_prose_characters'] for r in records()},reviewed_math_elements=8,whole_units_semantically_verified=True,verified_full_units={'kant-1784':0,'einstein-1905':4},semantic_equivalence_automatically_proved=False,source_sha256=pins)
