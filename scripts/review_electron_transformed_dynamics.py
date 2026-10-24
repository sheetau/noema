"""Whole-unit judgment for transforming the initial equations into (A)."""
from functools import lru_cache
from pathlib import Path
import json
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import REQUIREMENTS,digest,selection_binding,validate_hashes,validate_review
from noema.review_registry import merge_pins
ROOT=Path(__file__).resolve().parents[1]
def read(path):return (ROOT/path).read_text(encoding='utf-8')
FULL='examples/v014/einstein-electron-transformed-dynamics.noema';CORE='examples/v014/electron-transformed-dynamics-core.noema'
BASIS='data/electron-transformed-dynamics-basis-v1.json';ANNOTATIONS='data/electron-transformed-dynamics-identifiers-v1.json'
SOURCE='data/einstein-electron-transformed-dynamics-reading-v1.json';REPORT='reports/electron-transformed-dynamics-v1.json'
INVENTORY='artifacts/written-units-v1/einstein-1905.json';DOC='docs/electron-transformed-dynamics-v1.md'
REVIEWS={n:f'data/einstein-electron-transformed-dynamics-u{n:04}-review-v1.json' for n in (250,251)}
CLAUSES={
250:(
 ('Mit Hilfe dieser Gleichungen ',['eiswm','eisov','eli','eln','ek7s','ek66'],'直前の同じ七変換式を指し、それを現在の変換の手段として用いる。節番号だけを参照したり、これから得る式(A)を前提として指したりしない。'),
 ('transformieren wir die obigen Bewegungsgleichungen ',['elg','elh','elj','eln','ek7m','ek7c','eiswm','zc'],'同じ著者が上のkの初期三式を、同じ座標と場の変換によって表し直す操作を提示する。元の運動式と手段の七変換式を別の照応で保ち、引用内容の真理を機械的に実行しない。'),
 ('vom System [M0414] auf das System [M0415] ',['ek76','ek75','ek63','ela','eln','eisxy','ra','eisd4'],'M0414=kからM0415=Kへの向き。同じ電子・出来事・単位・二履歴を保ち、新系のτ微分と旧系のt微分をseppへ結ぶ。初期速度(v,0,0)での縦β³、横β²を同じ実加速度へ適用する。'),
 ('und erhalten:', ['elj','elk','ell','elm','eln','elp','eisox','uh'],'同じKの三式を結果として得るという提示と次の式への予告を保つ。前の運動法則の問いには同じ法則個体と具体的内容を結び、候補の唯一性や実験確認は加えない。'),
),
251:(
 ('[M0416]', ['ela','elb','elc','elk','eld','ele','elf','ell','ek75','ek76','eisyo','eisch','eisox'],'(A)の三行ax=εX/(μβ³)、ay=ε(Y−vN/V)/(μβ)、az=ε(Z+vM/V)/(μβ)を同じKの実二階座標時刻微分と同じ四点の実二場へ接続する。三軸、分母、横二項の符号、βの正の枝、同じμ・ε・v・Vを保持する。ラベル(A)はこの同じ表示内容を指し、先行の小tの初期運動範囲を継承する。'),
),
}
@lru_cache(None)
def records():
    catalog=load_catalog(ROOT,BASIS);source=json.loads(read(SOURCE));basis=json.loads(read(BASIS))
    paths={FULL,CORE,BASIS,ANNOTATIONS,SOURCE,REPORT,INVENTORY,DOC,'scripts/review_electron_transformed_dynamics.py','tests/test_electron_transformed_dynamics_review.py'}
    pins={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)};merge_pins(pins,catalog.source_sha256)
    for path in (SOURCE,REPORT):
        evidence=json.loads(read(path));validate_hashes(ROOT,evidence['source_sha256']);merge_pins(pins,evidence['source_sha256'])
    result=[]
    for n,s in zip((250,251),source['units']):
        clauses=[];offset=0
        for text,symbols,reason in CLAUSES[n]:
            assert s['text'][offset:offset+len(text)]==text and all(x in catalog.entries for x in symbols)
            clauses.append(dict(range=[offset,offset+len(text)],text=text,statements=[421],definitions=symbols,reason=reason));offset+=len(text)
        assert offset==len(s['text']) and s['unit']==f'einstein-1905:u{n:04}'
        reasons=(
         f'固定u{n:04}の全文と数式要素を原刊918頁の前後とともに再読した。u0250の一文とu0251の三行は同じ変換導入と表示の一群である。M0414=k、M0415=K、M0416の(A)と三等号を保持する。原刊の小tの訂正版を引き継ぎ、原文在庫を変更しない。',
         '同じPAIRの両履歴・指定出来事について旧新のseppを明示する。初期速度(v,0,0)に対して新加速度を縦β³・横β²で旧加速度へ結び、同じ新電場を先行七式の旧二場の混合へ結ぶ。結果は同じ旧点の三つの実二階微分と電磁場による(A)である。場や加速度を運動式の帰結として最初から定義しない。',
         '電子eisxh、出来事eisxv、K=ra、k=eisxy、v=eisxt、V=tc、同じ電荷・低速慣性質量・単位尺度・新旧履歴を保持する。上の運動式はek7m、これらの変換式はek7sへ照応する。新旧で同じ引数を使い、旧節の別のk又は同名速度へ交換しない。(A)の呼称はelkへ結ぶ。',
         'Mit Hilfeは先行式を現在用いるeisov、dieserとobigenは別のeiswm照応として保持する。transformierenとerhaltenは同じ前提から同じ結果を得る著者のzc/uh提示であり、物理法則の自動証明にはしない。表示eisox・命名eisch・前の探究への接続eisra・説明uf・順序ue・著者帰属eir3を共有する。',
         '同じ代表配置と0≤v<V、V>0、μ>0、正のβを保持する。Kのtによる初期変化o(Δt)を継承し、有限時間の厳密解・一定加速度・任意方向の式へ広げない。縦横の質量に書き換える後続の別問題はここで完成扱いしない。途中の加速度変換を原刊の追加表示とはしない。',
         '原始記号は四つの本文箇所・法則個体・式ラベルへの参照だけである。微分、物理的場と量、代数式、適合、全対応記述、引用と提示は既存概念から合成する。同じ法則の適合viを全代表設定の全対応記述で実際の(A)と同値に結び、その同じlawをek4wへ渡して前の質問の候補とする。名前だけ、数値一例の一致、別の型のeiswpで代用しない。',
         '保持した有理関数の厳密な商微分により両系のnative seppを対照し、縦加速度非零、偽の速度関数、三軸の加速度と場の符号を区別する。解析的な微分はモデル解釈であり、物理的履歴の帰属は別の明示入力である。全設定の量化は一つずつの実際の束縛を二値で診断し、全実数・全関数域の有限認定と未知入力を拒否する。',
         f'u{n:04}を前の共動初期三式・七変換式と次の質量の問いの間に置いて再読した。同じ二系と対象の変換操作、参照、結果の三行とラベル、前の法則探究との内容接続が揃ったと判断する。これは明示した初期運動の読みの下での全単位判断であり、全物理理論の真理や独立査読を主張しない。',
        )
        assert len(reasons)==len(REQUIREMENTS)
        result.append(dict(schema_version='noema-semantic-review-1',work='einstein-1905',unit=s['unit'],reviewer='assistant_review',decision='equivalent_under_stated_reading',document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source=dict(inventory=INVENTORY,unit_sha256=s['unit_sha256'],text=s['text'],range=s['range'],math=[{k:m[k] for k in ('id','sha256')} for m in s['math']]),selection=selection_binding(catalog,[421]),source_order_statements=[421],clauses=clauses,interpretation=basis['limitations'],limits=['明示した初期運動の読みでのアシスタントによる全単位判断。独立査読、一般の連鎖律、物理法則の真理又は原文同義性の自動証明ではない。','同じlawの内容と前の質問の候補を接続するが、唯一解や実験確認を加えない。','後続の縦横の質量の問い・式の書換え、第十節見出しと二作品全体は未完。'],unresolved=[],requirements=[dict(id=k,decision='satisfied',reason=v) for k,v in zip(REQUIREMENTS,reasons)],evidence=dict(source_reading=[SOURCE],formal_checks=[REPORT],semantic_reading=[DOC]),reviewed_prose_characters=s['source_nonblank_characters'],source_sha256=pins))
    return result
def prepare():
    from scripts.audit_opening_scope import write_exact
    for n,r in zip((250,251),records()):write_exact(ROOT/REVIEWS[n],json.dumps(r,ensure_ascii=False,indent=2)+'\n')
@lru_cache(None)
def build_report():
    catalog=load_catalog(ROOT,BASIS);inventory=json.loads(read(INVENTORY));active=dict(document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source_inventory=INVENTORY);pins={}
    for n,r in zip((250,251),records()):
        assert json.loads(read(REVIEWS[n]))==r;validate_review(ROOT,REVIEWS[n],'einstein-1905',active,catalog,inventory);merge_pins(pins,r['source_sha256']);pins[REVIEWS[n]]=digest((ROOT/REVIEWS[n]).read_bytes())
    return dict(status='transformed_initial_dynamics_two_whole_units_reviewed',document=FULL,source_units={r['unit']:r['reviewed_prose_characters'] for r in records()},reviewed_math_elements=3,whole_units_semantically_verified=True,verified_full_units={'kant-1784':0,'einstein-1905':2},semantic_equivalence_automatically_proved=False,source_sha256=pins)
