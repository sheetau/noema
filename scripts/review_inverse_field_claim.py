"""Read the complete inverse-method sentence and its displayed conclusion."""
from functools import lru_cache
import json
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import REQUIREMENTS,digest,selection_binding,validate_hashes,validate_review
from noema.review_registry import merge_pins
from scripts.compose_inverse_field_claim import ROOT,read,FULL,CORE,BASIS,ANNOTATIONS,INDICES,SOURCE_ORDER,LIMITS
from scripts.check_inverse_field_claim import DOC,SOURCE,INVENTORY,PRIORS,DEPENDENCIES,source_record

REPORT='reports/inverse-field-claim-v1.json'
REVIEWS=tuple(f'data/einstein-inverse-field-claim-u{n:04d}-review-v1.json' for n in (165,166))
CLAUSES=(
 (('Bildet man nun die Umkehrung dieses Gleichungssystems, ',['ejuh','ejur','ejus','ejut','ejuu','ejuy'],'直前の共通係数付き六式を逆にする操作を条件として採る。同じ物理的な両場・過程と領域を保持する。'),
  ('erstens durch Auflösen der soeben erhaltenen Gleichungen, ',['ejus','sbp2','sbj2','sbk2','ejuu','ejvb'],'第一法は直前の式を解く。逆係数を使うことと非零条件、soebenの直前表示への参照を保つ。'),
  ('zweitens durch Anwendung der Gleichungen auf die inverse Transformation (von [M0308] auf [M0309]), ',['ejut','sbq2','sbl2','sbm2','ejuu'],'第二法は同じ規則を逆変換へ適用する。kからKへ、新しい二場から元の二場を復元する方向を保つ。第一法とは別の結論記述へ接続する。'),
  ('welche durch die Geschwindigkeit [M0310] charakterisiert ist, ',['sbl2','sbm2','s6k','s6l','znz'],'逆変換の速度を-vとし、同じ係数関数も-vで評価する。'),
  ('so folgt, indem man berücksichtigt, daß die beiden so erhaltenen Gleichungssysteme identisch sein müssen:',['ejuv','ejuw','ejux','ejuy','ejuz','ejvc','sbo2','ejrj','zc'],'二つの式が任意の入力で同じでなければならないという必要性を採用し、その考慮から続く係数積1が従うという著者の提示を構成する。')),
 (('[M0311].',['ejuz','saq2','san2','znz','ejvc','eisox'],'同じ第六節の係数についてφ(v)φ(-v)=1を表し、前の一文の結論表示へ接続する。句点で一文が終わることを保持する。'),),
)
SEMANTICS=(
 '一つの逆変換を二方法で作る条件、直前の式を解く第一法、同じ規則を逆向きの系に適用する第二法、逆速度-v、式の同一性の必要性を考慮した帰結、という一文の関係を接続する。',
 '同じ係数関数のvと-vでの値の積が実数1であることを構成する。非零な正負の係数を許し、係数自体の値1や偶性を先取りしない。',
)
WHOLE=(
 'u0165全体を原刊909頁と直前の六式に照合して再読した。Bildet manの操作条件、二方法の順序と区別、soeben、逆向きの二系、逆速度、両式の同一性、必要性、その考慮を理由にした帰結まで、明示した読みの下で欠落なく保持したと判断する。',
 'u0166の式と句点を原刊909頁で再読し、両引数v/-v、同じφ、積、値1を照合した。直前の文の結論として接続し、字形差の明示的な読みの下で全体を記述したと判断する。',
)

@lru_cache(None)
def records():
    catalog=load_catalog(ROOT,BASIS)
    paths={FULL,CORE,BASIS,ANNOTATIONS,SOURCE,REPORT,INVENTORY,DOC,*PRIORS,*DEPENDENCIES,'scripts/review_inverse_field_claim.py','tests/test_inverse_field_claim_review.py'}
    pins={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)};merge_pins(pins,catalog.source_sha256)
    for p in (SOURCE,REPORT,*DEPENDENCIES):
        evidence=json.loads(read(p));validate_hashes(ROOT,evidence['source_sha256']);merge_pins(pins,evidence['source_sha256'])
    out=[]
    for i,s in enumerate(source_record()['segments']):
        clauses=[];offset=0
        for text,symbols,reason in CLAUSES[i]:
            assert s['text'][offset:offset+len(text)]==text and all(n in catalog.entries for n in symbols)
            clauses.append(dict(range=[offset,offset+len(text)],text=text,definitions=symbols,reason=reason));offset+=len(text)
        assert offset==len(s['text'])
        reasons=(
            f"固定{s['unit']}の全範囲と全数式要素{[m['id'] for m in s['math']]}を原刊909頁に照合した。u0165–u0166を一文として読み、φ/ψの字形差は旧照合記録の読みを明示して生資料と区別した。",
            SEMANTICS[i],
            '直前の共通係数付き六式はejuh、K/kはra/zbm、V/vはtc/zb7、旧新の二場はznl/znmとznr/zns、領域はznk/zntである。係数znzをvと-vで評価し、第三節の係数へ戻さない。両方法は同じ旧新の役割・逆座標写像・全六成分を保つ。',
            '二方法はsbs2による非空手順の接続として記述し、引用を実行しない。ejrjで同一性の必要性を構成し、zcでそれを考慮した推論の提示へ結ぶ。著者・論説への帰属、直前からの順序、帰結からの表示と説明を保持する。',
            '逆数が存在する範囲を明示するが正値を追加しない。式の同一性は任意入力の係数写像一致と読み、零の場の偶然の一致では済ませない。現在の物理的設定と先行式を保持し、偶性・係数自体の値1を結論へ補わない。',
            '既存の実数演算、逆速度の場変換、全成分・全点の一致、内容の真偽、非空全称、計算手順と著者の提示を合成する。新しい基本関係は導入せず、追加の参照個体eisp5は式の表示箇所に限定する。',
            '逆速度での係数評価、非零条件、現在の設定と両方法・前提の接続、実際のNoema手順列、非空全状況の必要性、正負の係数積、著者・理由・表示・順序を対照した。保存した六成分逆演算検査と零の場の反例、係数消去の記号的検証、全実数列挙拒否をハッシュ照合して保持する。',
            WHOLE[i],
        )
        assert len(reasons)==len(REQUIREMENTS)
        out.append(dict(schema_version='noema-semantic-review-1',work='einstein-1905',unit=s['unit'],reviewer='assistant_review',decision='equivalent_under_stated_reading',document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source=dict(inventory=INVENTORY,unit_sha256=s['unit_sha256'],text=s['text'],range=s['range'],math=[{k:m[k] for k in ('id','sha256')} for m in s['math']]),selection=selection_binding(catalog,INDICES),source_order_statements=SOURCE_ORDER,clauses=clauses,interpretation=LIMITS,limits=['明示した読みの下でのアシスタントによる全単位の通読判断。独立査読や意味同値の自動証明ではない。','一般の許容変形の健全性や物理的な論証の正しさを認定せず、著者の二方法と必要性・帰結の提示を記述する。','u0167以降と二作品全体の目標は未完。'],unresolved=[],requirements=[dict(id=k,decision='satisfied',reason=v) for k,v in zip(REQUIREMENTS,reasons)],evidence=dict(source_reading=[SOURCE],formal_checks=[REPORT,*DEPENDENCIES],semantic_reading=[DOC]),reviewed_prose_characters=s['source_nonblank_characters'],source_sha256=pins))
    return out

def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,r in zip(REVIEWS,records()):write_exact(ROOT/p,json.dumps(r,ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    active=dict(document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source_inventory=INVENTORY)
    catalog=load_catalog(ROOT,BASIS);inv=json.loads(read(INVENTORY));pins={}
    for p,r in zip(REVIEWS,records()):
        assert json.loads(read(p))==r;validate_review(ROOT,p,'einstein-1905',active,catalog,inv)
        merge_pins(pins,r['source_sha256']);pins[p]=digest((ROOT/p).read_bytes())
    return dict(status='inverse_field_claim_two_whole_units_reviewed',document=FULL,source_units={r['unit']:r['reviewed_prose_characters'] for r in records()},reviewed_math_elements=4,whole_units_semantically_verified=True,verified_full_units={'kant-1784':0,'einstein-1905':2},semantic_equivalence_automatically_proved=False,source_sha256=pins)
