"""Whole-unit rereading of magnetic analogy and the auxiliary concept, u0176."""
from functools import lru_cache
import json
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import REQUIREMENTS,digest,selection_binding,validate_hashes,validate_review
from noema.review_registry import merge_pins
from scripts.compose_auxiliary_role import ROOT,read,FULL,CORE,BASIS,ANNOTATIONS,LIMITS
from scripts.check_auxiliary_role import DOC,SOURCE,INVENTORY,DEPENDENCIES,source_record

REPORT='reports/auxiliary-role-v1.json'
REVIEW='data/einstein-auxiliary-role-u0176-review-v1.json'
INDICES=[169,170,171,172]
CLAUSES=(
 ([169],['ejy3','ejy4','ejy5','ejy6','ejy7','ejzi','ejza','ejzb','ejzc','ejzd','ejze','ejzf','ejzg','ejzh','eisqu','eisqv'],'磁動力への類推は、同じ点状単位磁極の旧系での追加寄与と−u×E/Vの一次近似、瞬間共動系での磁気側の静止試験作用という二つの言い方を対応させる。引用語の物理的役割と著者による類推の提示を保つ。仮定上の磁極への条件付き記述であり、孤立磁極の実在を追加しない。'),
 ([171,172],['ejzt','ejzu','ejzv','ejzw','ejzx','ejzy','ejzz','ejz2','eisqz','eisq2','eisq3','ejyg','ejx4','eisqy','eiscw','zdg'],'同じ展開済み理論に導入された電動力概念を、先の引用語と物理的な追加寄与の規則へ結ぶ。使用が少なくとも一件あり、全ての構成的使用が既存量からの残差への定義展開で尽くされることを、補助的な役割だけという読みとする。Man siehtは関係節も含む第二文全体を著者が明白と提示することとして接続する。'),
 ([172],['ejzw','eisq4','ejzt','eiscw','ejzo','ejz2','ejz3','ejz4'],'welcherとseineは主節と同じ概念の証人を指す。系依存性を同じ理論について述べ、その事情が当該概念の理論への導入を説明する理由だと結ぶ。単なる両命題の併記や含意、別概念の導入、心理的な因果へ交換しない。'),
 ([170,172],['ejzj','ejzk','ejzl','ejzm','ejzn','ejzo','ejzp','ejzq','ejzr','ejzs','ejzw','eisqx','eispn','ejts','eisqt','ejm2','scv2'],'電気・磁気の局所作用の有無の区分を理論全体で運動状態から独立にはできないという読みを保持する。理論が許す同じ過程・同じ出来事を非零速度の二系で比較し、同じ五単位と四試験応答、両場の変換と領域を共有する。両量種それぞれに零・非零が変わる許容例を要求する。全場・全速度での変化や電磁過程自体の消滅とはしない。'),
)

@lru_cache(None)
def records():
    catalog=load_catalog(ROOT,BASIS);s=source_record()
    paths={FULL,CORE,BASIS,ANNOTATIONS,SOURCE,REPORT,INVENTORY,DOC,*DEPENDENCIES,'scripts/review_auxiliary_role.py','tests/test_auxiliary_role_review.py'}
    pins={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)};merge_pins(pins,catalog.source_sha256)
    for p in (SOURCE,REPORT,*DEPENDENCIES):
        evidence=json.loads(read(p));validate_hashes(ROOT,evidence['source_sha256']);merge_pins(pins,evidence['source_sha256'])
    clauses=[]
    for part,(indices,symbols,reason) in zip(s['clauses'],CLAUSES,strict=True):
        assert all(n in catalog.entries for n in symbols)
        clauses.append(dict(range=part['range'],text=part['text'],statements=indices,definitions=symbols,reason=reason))
    assert ''.join(c['text'] for c in clauses)==s['text'] and s['source_nonblank_characters']==302 and s['math']==[]
    reasons=(
      '固定u0176全344文字・302非空白本文文字を、保存済み原刊910頁と固定転記で照合した。磁動力への類推と続く一文を分断せず読んだ。独立の数式要素はなく、原資料と旧証拠を変更しない。',
      '冒頭の類推では磁気側の旧系の追加寄与・一次近似と共動系の力、引用語の役割、著者の類推を結ぶ。第二文では展開済み理論、補助的な役割だけという限定、同じ概念の導入理由、根拠となる両場の系依存性、Man siehtの提示を合成する。nurには非空の全使用範囲を与え、理由を単なる含意へ縮めない。',
      '電動力はeisqsとejygが指定する同じ概念、理論はeisqwであり、構成課題eigj・論説eirf・現在の展開段階eisqyへ結ぶ。主節と関係節は一つの概念証人を共有する。系依存性では同じ許容過程・出来事・両場・五単位・四応答を二系で比較する。磁極強度と電荷の量種は区別する。',
      '類推はeisqu、本文の主張はuh、第二文全体の明白さはzdg、著者・論説はeir3へ接続する。主節の部分内容と第二文全体を別記録にし、全体の同じ引用内容へMan siehtを与える。著者の物理法則を処理系が実証したとは述べない。',
      'Hilfsbegriffを既存量による定義上の補助と読む。独立な物理入力を残す構成的使用は全称条件を満たさず、単なる語への言及はその範囲に含めない。全理論の保存拡張証明、力の不存在、一次近似の厳密等式、孤立磁極の実在を余計に要求しない。系依存性は全場・全速度での変化や電磁過程自体の不存在へ広げない。',
      '新基本関係は、表現と型付き役割による概念同定、理論内の構成的使用、型付き定義展開、根拠と結論の説明関係である。特定の文全体を一基本記号へ隠さない。補助性は非空条件と全称条件、残差の既存構成、概念導入を合成し、導入理由は同じ理論・概念とejzo/eiscwの引用へ結ぶ。物理的意味は先行の試験応答・場・単位の規約を保持する。',
      '局所検査は使用と展開の全ての二値部分集合、関係引数の取り違え、概念証人の分離、必要な根拠・導入・説明の欠落、引用内容と提示の不一致を対照する。磁動力・残差・系依存性の下位本体は既存の固定証拠を検証する。有限模型の真偽、型と表記往復、原文の読解は確認範囲が異なる。検査用関係表を実際の物理的帰属の証明にしない。',
      '原刊のu0176を前の二つの言い方から続けて再読した。磁動力への類推、展開済みの同じ理論、電動力の補助概念だけという役割、同じ概念の導入とその理由、電気・磁気の作用の系依存性、Man siehtの提示を、明示した解釈の下で欠落なく記述したと判断する。次のu0177の序文の非対称性解消と単極機の所在の問いは別単位として残す。',
    )
    assert len(reasons)==len(REQUIREMENTS)
    record=dict(schema_version='noema-semantic-review-1',work='einstein-1905',unit=s['unit'],reviewer='assistant_review',decision='equivalent_under_stated_reading',document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source=dict(inventory=INVENTORY,unit_sha256=s['unit_sha256'],text=s['text'],range=s['range'],math=[]),selection=selection_binding(catalog,INDICES),clauses=clauses,interpretation=LIMITS,limits=['明示した解釈の下でのアシスタントによる全単位通読判断。独立査読・同義性の自動証明ではない。','構成的な使用の範囲・物理的意味を保つ展開・説明関係の帰属は明示した意味規約に従う。全理論の真理や保存拡張を証明した記録ではない。','u0177以降と二作品全体の目標は未完。'],unresolved=[],requirements=[dict(id=k,decision='satisfied',reason=v) for k,v in zip(REQUIREMENTS,reasons)],evidence=dict(source_reading=[SOURCE],formal_checks=[REPORT,*DEPENDENCIES],semantic_reading=[DOC]),reviewed_prose_characters=302,source_sha256=pins)
    return [record]

def prepare():
    from scripts.audit_opening_scope import write_exact
    write_exact(ROOT/REVIEW,json.dumps(records()[0],ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    r=records()[0];assert json.loads(read(REVIEW))==r
    active=dict(document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source_inventory=INVENTORY)
    validate_review(ROOT,REVIEW,'einstein-1905',active,load_catalog(ROOT,BASIS),json.loads(read(INVENTORY)))
    pins=dict(r['source_sha256']);pins[REVIEW]=digest((ROOT/REVIEW).read_bytes())
    return dict(status='magnetic_analogy_and_auxiliary_role_whole_unit_reviewed',document=FULL,source_units={r['unit']:302},reviewed_math_elements=0,whole_units_semantically_verified=True,verified_full_units={'kant-1784':0,'einstein-1905':1},semantic_equivalence_automatically_proved=False,source_sha256=pins)
