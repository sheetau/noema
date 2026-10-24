"""Whole-unit rereading of the asymmetry and seat-of-force questions, u0177."""
from functools import lru_cache
import json
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import REQUIREMENTS,digest,selection_binding,validate_hashes,validate_review
from noema.review_registry import merge_pins
from scripts.compose_seat_questions import ROOT,read,FULL,CORE,BASIS,ANNOTATIONS,LIMITS
from scripts.check_seat_questions import DOC,SOURCE,INVENTORY,DEPENDENCIES,source_record

REPORT='reports/seat-questions-v1.json';REVIEW='data/einstein-seat-questions-u0177-review-v1.json';INDICES=[360,361,362]
CLAUSES=(
 ([360],['ejz5','ejz6','ejz7','ekaa','ekab','ekac','ekad','ekae','ekaf','eisq5','eisra','eisrb','eidd','eidh','eida','eia2'],'序文の同じ磁石と導体・相対運動が生成に寄与する電流の考察へ戻る。通常の見方で両場合を排他的な説明機構へ分類した非対称性が、展開した理論の見方では共通機構で説明できるという読みを採る。妥当な全比較で許容説明が非空かつ各説明が共通分類を持つ。単なる電流値の一致や説明の不在を解消にせず、後方参照、ferner、klar、著者の主張を保持する。'),
 ([362],['ekal','ekam','ekan','ekao','ekap','ekaq','eisrl','eisrm','eisrn','eisro','eisrq','eisrp','ejzt','ejyg','eisqs'],'引用符付きSitzを、自立した起電作用の本来的な発生場所を求める問いと読む。場所候補を答えとする問いと、自立した同じ担い手に所在があるという必要前提を分け、従前の探究と新理論による前提の拒絶を同じ対象へ結ぶ。電動力は先行の同じ概念と物理的役割に接続する。著者の発問や一般の局所力の位置質問への禁止ではない。Auchは第一文に同じ第二文内容を加える。'),
 ([361,362],['ekag','ekah','ekai','ekaj','ekak','eisrj','eisrr','ekap'],'単極機は、許容する運転で一回転以上の一様回転、二つの滑り接触による固定した回路方向、同じ過程の磁場と誘導作用、反転せず恒等零でない出力を満たせる装置類として構成する。括弧はこの問題の適用先を取り上げる。同じ概念の証人を問いと共有し、磁石と導体の別体性や現に運転済みを要求せず、全問題の範囲をこの装置類だけにしない。'),
 ([362],['ekan','ekao','ekap','ekaq','ekar','ekas','eisro','eisrp','eisrq','eisrb'],'gegenstandslosは必要前提を新理論が積極的に退けるため従来の探究の対象を失うこと。werdenは理論の移行に伴う扱いの変化であり、物理的な時間経過で力が消えることではない。候補集合が空、未回答、不明、前提を単に偽と評価することと区別する。第二文全体を同じ著者・論説へ帰属し、第一文に続く追加判断として提示する。'),
)

@lru_cache(None)
def records():
    catalog=load_catalog(ROOT,BASIS);s=source_record()
    paths={FULL,CORE,BASIS,ANNOTATIONS,SOURCE,REPORT,INVENTORY,DOC,*DEPENDENCIES,'docs/asymmetry-resolution-v1.md','docs/unipolar-machine-v1.md','scripts/review_seat_questions.py','tests/test_seat_questions_review.py'}
    pins={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)};merge_pins(pins,catalog.source_sha256)
    for p in (SOURCE,REPORT,*DEPENDENCIES):
        evidence=json.loads(read(p));validate_hashes(ROOT,evidence['source_sha256']);merge_pins(pins,evidence['source_sha256'])
    clauses=[]
    for part,(indices,symbols,reason) in zip(s['clauses'],CLAUSES,strict=True):
        assert all(n in catalog.entries for n in symbols)
        clauses.append(dict(range=part['range'],text=part['text'],statements=indices,definitions=symbols,reason=reason))
    assert ''.join(c['text'] for c in clauses)==s['text'] and s['source_nonblank_characters']==264 and s['math']==[]
    reasons=(
      '固定u0177の全301文字・264非空白文字を原刊910頁と照合し、前段の補助概念と系依存性から第一文・第二文を続けて読んだ。Sitzの引用符と単極機の括弧を保持する。独立数式要素はなく、原文や旧証拠を変更しない。',
      '第一文は序文の非対称性への後方参照、相対運動による電流生成、同じ比較観点での共通機構による説明、fernerとklarを含む。第二文は所在を答えとする問い、同じ概念と設定に関する必要前提、従前の探究、新理論による前提の拒絶、理論移行、括弧の適用例、Auchを組み合わせる。',
      '第一文は序文の同じ磁石eisaa・導体eisab・過程eisacと既存の相対履歴・準備条件へ結ぶ。第二文はeisqs/ejygの同じ電動力概念を一つの証人にし、全適用設定と単極機の括弧で共有する。前提の担い手と所在も同じ証人である。従前の見方eisakと展開した理論eisqwを区別する。',
      '両文の主張をuhとeir3へ帰属し、第一文の明白さをzdg、前段への追加と第二文のAuchをeisrbで示す。第二文内のg[a]は言及される問いであり、著者が発問して回答を要求する発話へ変えない。前提の拒絶は原著者の理論判断として記述する。',
      'Sitzを系に依存する作用の分解から独立した発生源の所在として読む。通常の局所力の位置を問うことまで失効させず、力そのものの不存在も述べない。gegenstandslosを空の候補集合・未回答・不明へ縮めず、werdenに物理時間による消滅を加えない。単極機は適用先として取り上げ、全問題の排他的な範囲とはしない。前段の補助性だけから拒絶を自動導出しない。',
      '第一文の共通説明は非空性・全称条件・分類の共有を合成し、物理的な相対運動と電流への生成寄与を保持する。第二文の新基本関係は問題設定、所在候補、自立した担い手、物理的所在、必要前提、理論による拒絶、従前の探究、括弧の適用先であり、文全体の専用原始記号ではない。前提は存在量化と内容型、問いは候補条件と質問型で構成する。装置類は回転・接触・回路・誘導・極性の先行構成に接続する。',
      '局所検査は二値個体域で候補・前提の証人・必要前提・従前の扱い・拒絶の区別を調べ、量化の範囲、同じ概念と設定の接続、引用内容と追加提示の対応を確認する。第一文と装置の実数・関数を含む下位構成は固定証拠を照合し、全無限域を有限模型で代用しない。検査の真偽を意味同義性又は物理的真理の証明にしない。',
      '原刊の段落全体を再読し、序文の非対称性が消えるという第一文と、所在の問いが対象を失うという第二文の両方を、参照・量化・提示・括弧まで同じ文脈に接続したと判断する。採用したSitzと理論移行の読みを明示した下で、全単位に未処理の意味要素はない。後続の第7節以降と二作品全体の目標は別に残る。',
    )
    assert len(reasons)==len(REQUIREMENTS)
    first=json.loads(read('data/asymmetry-resolution-basis-v1.json'))['limitations']
    machine=json.loads(read('data/unipolar-machine-basis-v1.json'))['limitations'][:4]
    record=dict(schema_version='noema-semantic-review-1',work='einstein-1905',unit=s['unit'],reviewer='assistant_review',decision='equivalent_under_stated_reading',document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source=dict(inventory=INVENTORY,unit_sha256=s['unit_sha256'],text=s['text'],range=s['range'],math=[]),selection=selection_binding(catalog,INDICES),clauses=clauses,interpretation=LIMITS+first[:4]+machine,limits=['明示した読みの下でのアシスタントによる通読判断であり、独立査読・意味同義性の自動証明ではない。','Sitzの自立した発生源という読みは前段を踏まえた解釈である。理論による前提の拒絶を有限模型の真偽や補助性だけから推論しない。','原著者の理論的・物理的結論の真理や、二作品全体の記述完成を認定する記録ではない。'],unresolved=[],requirements=[dict(id=k,decision='satisfied',reason=v) for k,v in zip(REQUIREMENTS,reasons)],evidence=dict(source_reading=[SOURCE],formal_checks=[REPORT,*DEPENDENCIES],semantic_reading=[DOC,'docs/asymmetry-resolution-v1.md','docs/unipolar-machine-v1.md']),reviewed_prose_characters=264,source_sha256=pins)
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
    return dict(status='asymmetry_and_seat_questions_whole_unit_reviewed',document=FULL,source_units={r['unit']:264},reviewed_math_elements=0,whole_units_semantically_verified=True,verified_full_units={'kant-1784':0,'einstein-1905':1},semantic_equivalence_automatically_proved=False,source_sha256=pins)
