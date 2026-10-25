"""Whole-unit readings for the mass inquiry and conditional mass conventions."""
from functools import lru_cache
from pathlib import Path
import json
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import REQUIREMENTS,digest,selection_binding,validate_hashes,validate_review
from noema.review_registry import merge_pins
ROOT=Path(__file__).resolve().parents[1]
def read(path):return (ROOT/path).read_text(encoding='utf-8')
FULL='examples/v014/einstein-electron-directional-masses.noema';CORE='examples/v014/electron-directional-masses-core.noema'
BASIS='data/electron-directional-masses-basis-v1.json';ANNOTATIONS='data/electron-directional-masses-identifiers-v1.json'
SOURCE='data/einstein-electron-directional-masses-reading-v1.json';REPORT='reports/electron-directional-masses-v1.json'
INVENTORY='artifacts/written-units-v1/einstein-1905.json';DOC='docs/electron-directional-masses-v1.md'
UNITS=(252,254,255,256,257,258)
REVIEWS={n:f'data/einstein-electron-directional-masses-u{n:04}-review-v1.json' for n in UNITS}

CLAUSES={
252:(
 ('Wir fragen nun in Anlehnung an die übliche Betrachtungsweise nach der „longitudinalen“ und „transversalen“ Masse des bewegten Elektrons. ',[423],['eme','emd','emc','emx','emy','eisyu','eisyv','eisyx'],'同じ動く電子の二つの方向別係数を、後続で指定する規約を用いて問う。通常の考え方への準拠、縦横の名称、問いの対象と著者を保持し、答えの既知性は加えない。'),
 ('Wir schreiben die Gleichungen (A) in der Form',[422],['elq','elr','els','elu','elv','elx','zd3','eiswm','eisch','eisox'],'先行(A)を同じ三行六等号へ書き換えて示す旧主張422を共有する。第一文の問いと第二文の書換えを同じ順序で読み合わせる。'),
),
254:(
 ('und bemerken zunächst, daß [M0418] die Komponenten der auf das Elektron wirkenden ponderomotorischen Kraft sind, und zwar in einem in diesem Moment mit dem Elektron mit gleicher Geschwindigkeit wie dieses bewegten System betrachtet. ',[424],['ely','ema','ek63','eibs','em3','uh','eiswm'],'先行の三行を受けてまずεX′,εY′,εZ′を、同じ電子と瞬間的に同速のkで見る機械力の三成分として指摘する。力の記録・実電場・同じ出来事・電荷・単位を共有する。'),
 ('(Diese Kraft könnte beispielsweise mit einer im letzten System ruhenden Federwage gemessen werden.) ',[424],['el2','el3','el4','el5','el6','el7','emb','em3','eir5','eisa5'],'この同じ力を、同じkに静止するばね秤で測り得るという括弧内の一例。弾性の復元作用・校正目盛り・可能な機械的比較と同じ三成分を保持する。測定済み、唯一の測定法、三軸同時測定へ替えない。'),
 ('Wenn wir nun diese Kraft schlechtweg „die auf das Elektron wirkende Kraft“ nennen und die Gleichung',[425],['emk','ems','emt','enc','em6','eisyw'],'同じkの力の記録を端的に電子に働く力と呼ぶという選択を条件の前件へ置き、続く数値法則へ接続する。無修飾の呼称から物理的な系の限定を取り払わない。'),
),
255:(
 ('Massenzahl × Beschleunigungszahl = Kraftzahl',[425],['sepe','seph','sepi','emr','em6','eisox'],'保持する数値法則の表示。整合する単位の同じ三成分へ係数×加速度=力を展開し、縦の係数と横二成分共通の係数を区別する。任意の三数値が無条件に等式を満たす内容にしない。'),
),
256:(
 ('aufrechterhalten, und wenn wir ferner festsetzen, daß die Beschleunigungen im ruhenden System [M0419] gemessen werden sollen, so erhalten wir aus obigen Gleichungen:',[425],['emc','emr','emt','emu','emn','emo','enc','em6','zraconvention','zc','eisd4'],'数値法則を保持し、さらに加速度を静止系Kで測る規約を採るなら、直前の三行六等号から続く二質量を得るという条件付き導出。力のkと加速度のKを区別し、同じ実微分と単位尺度を保持する。'),
),
257:(
 ('Longitudinale Masse [M0420]',[425],['emh','emi','emj','emp','emv','emx','em6','eisyx','eisox'],'同じ運動軸xの縦係数をμ/(sqrt(1−(v/V)²))³と表示する。正の平方根全体の三乗、分子μ、比v/V、同じ単位・速度・低速質量と命名を保持する。'),
),
258:(
 ('Transversale Masse [M0421]',[425],['emh','emj','emq','emw','emx','em6','eisyx','eisox'],'同じ運動軸に直交するy,z共通の横係数をμ/(1−(v/V)²)と表示する。分母に平方根を補わず、別規約のμβへ直さない。同じ二係数を一組として得る結論へ接続する。'),
),
}

@lru_cache(None)
def records():
    catalog=load_catalog(ROOT,BASIS);source=json.loads(read(SOURCE));basis=json.loads(read(BASIS));sources={int(x['unit'][-4:]):x for x in source['units']}
    paths={FULL,CORE,BASIS,ANNOTATIONS,SOURCE,REPORT,INVENTORY,DOC,'scripts/review_electron_directional_masses.py','tests/test_electron_directional_masses_review.py'}
    pins={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)};merge_pins(pins,catalog.source_sha256)
    for path in (SOURCE,REPORT):
        evidence=json.loads(read(path));validate_hashes(ROOT,evidence['source_sha256']);merge_pins(pins,evidence['source_sha256'])
    results=[]
    for n in UNITS:
        s=sources[n];offset=0;clauses=[];order=[]
        for text,indices,symbols,reason in CLAUSES[n]:
            assert s['text'][offset:offset+len(text)]==text,(n,offset)
            assert all(x in catalog.entries for x in symbols)
            clauses.append(dict(range=[offset,offset+len(text)],text=text,statements=indices,definitions=symbols,reason=reason));offset+=len(text)
            order.extend(i for i in indices if i not in order)
        assert offset==len(s['text'])
        reasons=(
         f'固定u{n:04}の全文を、原刊918頁末の問いから919頁の二質量表示まで読み合わせた。本文の七単位u0252–u0258は連続した問い・書換え・説明・括弧例示・条件文・三つの表示である。u0253の既存判断を保存し、今回は残る六単位の全文を判断する。数式要素の分母、次数、プライム、系名を原刊へ照合した。',
         '各句の要件はclausesに列挙した。問いを同じ二係数候補emeへ、力の三成分を同じ実電場と力記録elyへ、測定可能性を同じ力のembへ接続する。規約の条件と二分数の表示をemc、emt、enc、emj、emp、emqへ結び、縦と横の同時の存在はemoに明記する。',
         '電子eisxh、出来事eisxv、K=ra、k=eisxy、v=eisxt、V=tc、μ、εと単位尺度を前の同じPAIRから引き継ぐ。三行の右端は同じkの場、加速度は同じKの実二階微分である。指示語この力・最後の系・上の式を別の対象へ取り替えず、xと直交するy,zの係数という幾何をek63とsephに保つ。',
         '質問の提示eisyu、当時の考察慣行への準拠eisyv、まず指摘するuhと本文順、ばね秤の例示eir5と括弧補足eisa5、端的な呼称eisyw、条件文encの主張とzcの導出、式表示eisoxと名称eisyx、著者eir3を区別する。内容を定義しただけにせず本文へ接続し、引用された物理内容は提示時に自動実行しない。',
         '問いの二係数は直後に指定される規約での値として読む。力をk、加速度をKに帰属し、派生加速度の尺度A T²=Lと力の尺度M A=Fを保つ。測定は同じ力の寄与の可能な比較であり、元の加速軌道を装置の可能結果へ丸ごと複製しない。v=0では選択した軸の係数が同じμとなる。全数値の実験的実現、実際の測定、唯一の測定法又は現代の別質量規約を追加しない。',
         '力・弾性要素・校正目盛り・物理的可能性・単位・実加速度は既存定義と明示した物理対応で構成する。二質量は全成分関係の係数同定sepiと実三成分sephを共有し、単なる名称や一つの零入力で代用しない。平方根・積・逆数・全称・存在・条件・引用を合成し、新しい四関係は一般的な論述と型付き名称の接続であって個別文の真理を格納しない。',
         '検査は完全平方の有理例による両分母、各力成分、負根・係数入替え、条件文の真理表、公開された同じ48引数、全44束縛と二候補、提示関係の欠落・役割交換・引用非実行を扱う。全域の係数関係の数学的根拠は既存mass-coefficientsの証拠に接続する。小さい有限域の結合診断、実数体の一般定理、物理法則の真理、原文同義性の判断は区別する。',
         f'u{n:04}全体を前後の一群へ戻して再読し、clausesの各内容とその提示が同じ参照・条件・範囲で揃うと判断する。これは明示した読みの下でのアシスタントの全文判断であり、独立査読又は意味一致の機械的証明ではない。次の別定義に関するu0259以降と二作品全体の完了を含めない。',
        )
        assert len(reasons)==len(REQUIREMENTS)
        results.append(dict(schema_version='noema-semantic-review-1',work='einstein-1905',unit=s['unit'],reviewer='assistant_review',decision='equivalent_under_stated_reading',document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source=dict(inventory=INVENTORY,unit_sha256=s['unit_sha256'],text=s['text'],range=s['range'],math=[{k:m[k] for k in ('id','sha256')} for m in s['math']]),selection=selection_binding(catalog,sorted(order)),source_order_statements=order,clauses=clauses,interpretation=basis['limitations'],limits=['明示した読みの下でのアシスタントによる全単位判断。独立査読、物理的真理又は原文同義性の自動証明ではない。','後続の別定義・理論比較、質量の適用範囲と運動エネルギーは未完。'],unresolved=[],requirements=[dict(id=k,decision='satisfied',reason=v) for k,v in zip(REQUIREMENTS,reasons)],evidence=dict(source_reading=[SOURCE],formal_checks=[REPORT],semantic_reading=[DOC]),reviewed_prose_characters=s['source_nonblank_characters'],source_sha256=pins))
    return results
def prepare():
    from scripts.audit_opening_scope import write_exact
    for n,record in zip(UNITS,records()):write_exact(ROOT/REVIEWS[n],json.dumps(record,ensure_ascii=False,indent=2)+'\n')
@lru_cache(None)
def build_report():
    catalog=load_catalog(ROOT,BASIS);inventory=json.loads(read(INVENTORY));active=dict(document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source_inventory=INVENTORY);pins={}
    for n,r in zip(UNITS,records()):
        assert json.loads(read(REVIEWS[n]))==r;validate_review(ROOT,REVIEWS[n],'einstein-1905',active,catalog,inventory);merge_pins(pins,r['source_sha256']);pins[REVIEWS[n]]=digest((ROOT/REVIEWS[n]).read_bytes())
    return dict(status='six_whole_units_mass_inquiry_force_example_and_conditional_masses_reviewed',document=FULL,source_units={r['unit']:r['reviewed_prose_characters'] for r in records()},reviewed_math_elements=4,whole_units_semantically_verified=True,verified_full_units={'kant-1784':0,'einstein-1905':6},semantic_equivalence_automatically_proved=False,source_sha256=pins)
