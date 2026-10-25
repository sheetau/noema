"""Record a whole-sentence reading independently of finite formal checks."""
from functools import lru_cache
from pathlib import Path
import json
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import REQUIREMENTS,digest,selection_binding,validate_hashes,validate_review
from noema.review_registry import merge_pins
ROOT=Path(__file__).resolve().parents[1]
def read(path):return (ROOT/path).read_text(encoding='utf-8')
FULL='examples/v014/einstein-electron-convention-caution.noema';CORE='examples/v014/electron-convention-caution-core.noema'
BASIS='data/electron-convention-caution-basis-v1.json';ANNOTATIONS='data/electron-convention-caution-identifiers-v1.json'
SOURCE='data/einstein-electron-convention-caution-reading-v1.json';REPORT='reports/electron-convention-caution-v1.json'
INVENTORY='artifacts/written-units-v1/einstein-1905.json';DOC='docs/electron-convention-caution-v1.md'
REVIEW='data/einstein-electron-convention-caution-u0259-review-v1.json'
CLAUSES=(
 ('Natürlich ',['zdg','en7'],'前半の条件文を著者が当然・明白なものとして提示する。実際の真理や読者全員の同意へ替えない。'),
 ('würde man bei anderer Definition der Kraft und der Beschleunigung andere Zahlen für die Massen erhalten; ',['enp','enq','enr','ens','ent','enu','env','enw','emf','enn','eiszc','eiszd','eisze'],'同じ動く電子・物理設定・単位の下で、力・加速度の操作的な定義を採り替える関連仮定状況が非空で、その全てで元の二質量とは少なくとも一方の数値が異なるという条件文。定義の実質的な変更と結果の差を区別し、文脈範囲を差から逆算しない。係数を全応答域で同定し、唯一の成功例にも無制限の全定義にも縮めない。'),
 ('man ersieht daraus, ',['zc','eiswm','en7'],'直前の別定義での数値差から、著者が次の注意要求を導く推論を提示する。先行の同じ二質量への照応を保ち、事実から規範を自動証明しない。'),
 ('daß man bei der Vergleichung verschiedener Theorien der Bewegung des Elektrons ',['en2','en3','eisvd','vd','eisxn','eiszf','eiszg'],'電子の運動の法則を体系の内容として持つ、異なる理論を比較する一般の主体と活動。理論を単なる文字列や数値表にせず、同じ左右・主体・主題を比較手続きへ渡す。特定の理論の真理は比較の資格に入れない。'),
 ('sehr vorsichtig verfahren muß.', ['en4','en5','en6','seqm','eiszh','eiszi','eiszj','zrcmust'],'関連する事項への持続的吟味と、意味・単位・同じ事例の対応を確認する手続きを、通常の基準を大きく上回る程度で遂行すべきという方法上の要求。慎重さの採用した読みを明示し、sehr、義務、主体と活動を保つ。現実の遂行、成功、完全性又は比較活動の存在を補わない。'),
)

@lru_cache(None)
def record():
    catalog=load_catalog(ROOT,BASIS);s=json.loads(read(SOURCE));basis=json.loads(read(BASIS))
    paths={FULL,CORE,BASIS,ANNOTATIONS,SOURCE,REPORT,INVENTORY,DOC,'scripts/review_electron_convention_caution.py','tests/test_electron_convention_caution_review.py'}
    pins={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)};merge_pins(pins,catalog.source_sha256)
    for path in (SOURCE,REPORT):
        evidence=json.loads(read(path));validate_hashes(ROOT,evidence['source_sha256']);merge_pins(pins,evidence['source_sha256'])
    clauses=[];offset=0
    for text,symbols,reason in CLAUSES:
        assert s['text'][offset:offset+len(text)]==text,offset
        assert all(n in catalog.entries for n in symbols)
        clauses.append(dict(range=[offset,offset+len(text)],text=text,statements=[426],definitions=symbols,reason=reason));offset+=len(text)
    assert offset==len(s['text'])
    reasons=(
     '固定u0259全文を原刊919頁の二質量表示直後の一段落と照合した。Natürlich、würde、anderer Definition、andere Zahlen、man ersieht daraus、verschiedener Theorien、sehr、mußを含む一文の範囲を固定し、数式の転記に縮めない。',
     '各句の関係と作用範囲はclausesに列挙した。元の力・加速度の射影、物理的操作定義の採用と変更、独立に選択された仮定範囲の非空・全称、新しい係数の存在と数値差、理論の内容所属、同じ比較活動、注意事項の全称、高い程度、方法上の要求を合成した。',
     '同じ先行emfの電子eisxh、出来事eisxv、kの力とKの加速度、低速質量・電荷・単位・速度を保持する。元の二質量はμβ³,μβ²。同じ46設定を射影と再定義へ渡し、質量候補の外側で固定する。理論の左右・主体・活動・主題をen3で一致させ、注意・程度・要求にも同じ主体と活動を渡す。',
     'en7はuhで条件文と要求をそれぞれ述べ、zdgでNatürlichの明白さを添え、zcで前半から要求への著者の推論を提示する。eiswmで先行二質量へ戻り、ueで二句及び先行表示の順序を保つ。eobは全文メッセージを同じ著者・論説へ帰属する。引用内容を提示時に実行しない。',
     '別定義は同じ物理条件での操作的再評価として読む。前半は関連すると先に定めた範囲の全称で、一例だけでも全ての想像可能な定義でもない。動く電子の文脈を明示し、静止境界や補償する変更を隠さない。後半の慎重さは吟味と拙速な不一致判定の回避という明示した読みであり、原文に検査項目の列挙、成功・完全性、現実の遵守を追加しない。',
     '力・加速度と同じ履歴の意味は既存規約とemfへ依存し、新しい操作的定義関係には測定対象・系・時計・作用による数量の定め方を明示する。理論はeisvdの体系と電子運動法則の内容所属で構成する。注意、程度、比較、内容所属という一般的な関係を用い、一文全体の真理を新しい原始記号として置かない。',
     '局所検査は実際の三成分map、同じ履歴、定義と結果の独立性、全注意事項、程度、要求と遵守、提示の各役割、非空・全称・存在の束縛を扱う。全実数域は有限検査で認定しない。検査の成功、物理的な主張の真理、規範の妥当性と原文の意味判断を区別し、元の426主張と判断根拠を保存する。',
     'u0259を先行二質量表示と後続物質点への拡張の間へ戻して再読した。条件文、明白さ、照応と推論、電子運動理論の比較、一般主体、非常に慎重な遂行の要求が同じ参照・範囲で揃うため、明示した解釈の下で全文を記述できたと判断する。これはアシスタントの意味判断であり、独立査読や自動同義性証明ではない。後続u0260以降の完成を含めない。',
    )
    assert len(reasons)==len(REQUIREMENTS)
    return dict(schema_version='noema-semantic-review-1',work='einstein-1905',unit=s['unit'],reviewer='assistant_review',decision='equivalent_under_stated_reading',document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source=dict(inventory=INVENTORY,unit_sha256=s['unit_sha256'],text=s['text'],range=s['range'],math=[]),selection=selection_binding(catalog,[426]),source_order_statements=[426],clauses=clauses,interpretation=basis['limitations'],limits=['明示した読みの下でのアシスタントによる全単位判断。独立査読、物理的真理、規範の正当性又は原文同義性の自動証明ではない。','後続の物質点への適用拡張、運動エネルギー、実験的な検証条件は未完。'],unresolved=[],requirements=[dict(id=k,decision='satisfied',reason=v) for k,v in zip(REQUIREMENTS,reasons)],evidence=dict(source_reading=[SOURCE],formal_checks=[REPORT],semantic_reading=[DOC]),reviewed_prose_characters=s['source_nonblank_characters'],source_sha256=pins)

def prepare():
    from scripts.audit_opening_scope import write_exact
    write_exact(ROOT/REVIEW,json.dumps(record(),ensure_ascii=False,indent=2)+'\n')
@lru_cache(None)
def build_report():
    r=record();assert json.loads(read(REVIEW))==r
    catalog=load_catalog(ROOT,BASIS);inventory=json.loads(read(INVENTORY));active=dict(document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source_inventory=INVENTORY)
    validate_review(ROOT,REVIEW,'einstein-1905',active,catalog,inventory)
    return dict(status='whole_alternative_definitions_and_care_sentence_reviewed',document=FULL,source_units={r['unit']:r['reviewed_prose_characters']},whole_units_semantically_verified=True,verified_full_units={'kant-1784':0,'einstein-1905':1},semantic_equivalence_automatically_proved=False,source_sha256=r['source_sha256']|{REVIEW:digest((ROOT/REVIEW).read_bytes())})
