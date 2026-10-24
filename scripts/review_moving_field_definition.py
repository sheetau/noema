"""Review the complete conditional requirement and six moving-frame equations."""
from functools import lru_cache
import json
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import REQUIREMENTS,digest,selection_binding,validate_hashes,validate_review
from noema.review_registry import merge_pins
from scripts.compose_moving_field_definition import ROOT,read,FULL,CORE,BASIS,ANNOTATIONS,INDEX,LIMITS
from scripts.check_moving_field_definition import DOC,SOURCE,INVENTORY,PRIORS,DEPENDENCIES,source_record

REPORT='reports/moving-field-definition-v1.json'
REVIEWS=tuple(f'data/einstein-moving-field-definition-u{n:04d}-review-v1.json' for n in (161,162))
CLAUSES=(
 (('Das Relativitätsprinzip fordert nun, ',['ejt2','ejt3','ejt4','ejt6','eion','zc'],'相対性原理の同じ理論・全法則・全候補範囲を保ち、この法則への適用による要求として著者が述べる。'),
  ('daß die Maxwell-Hertzschen Gleichungen für den leeren Raum auch im System [M0294] gelten, wenn sie im System [M0295] gelten, ',['ejt5','ejs6','ejtw','ejsm','eisch'],'同じ真空の法則がKで成立するならkでも成立するという条件文。後件だけの無条件な主張へ替えない。'),
  ('d. h. daß für die im bewegten System [M0296] durch ihre ponderomotorischen Wirkungen auf elektrische bez. magnetische Massen definierten Vektoren der elektrischen und magnetischen Kraft ',['ejtq','ejtr','ejts','ejtt','ejtu','eisps','eispt','eispu','eibr','uf'],'電荷と磁極強度を担う試験系への機械力の理想応答という採用解釈を、同じ移動系・地点時刻・量種・単位・三成分へ接続する。d. h.は先の要求の説明を導く。'),
  ('([M0297] und [M0298]) des bewegten Systems [M0299] die Gleichungen gelten:',['ejtx','ejty','ejtz','ejtw','ejt6','eispi','eisox'],'同じ移動系の電気側・磁気側の二つの三成分表記を実際の場の規則へ結び、この二場に続く式を要求する。')),
 (('[M0300]',['ejtv','ejtw','ejt5','ejt6','s5y','s5w'],'同じ移動系の新しい二場znr/zns、領域zntとVについての六回転式。条件付き要求の表示による具体化として保持し、前文の計算上の混合成分との等値は補わない。'),),
)
SEMANTICS=(
 '第一原理の理論証人をejt2/ejt3で共有し、法則・候補履歴・二つの対応記述と現行の方程式内容を接続する。ejt5はKならkという条件文を保つ。ejtq以下は機械力の理想応答により二場を定義し、ejtx/ejtyで表記へ結ぶ。原理による要求・言い換え・表示の役割を合成する。',
 '原刊の六つの等式を、三つの電気側時間微分と三つの磁気側時間微分、それぞれの空間微分の差として保持する。同じVと全領域でのs5yを使い、原刊の二列の順を論理上の六条件の欠落へしない。',
)
WHOLE=(
 'u0161全体を原刊908頁と前後の文へ照合して再読した。相対性原理による条件付き要求、空の領域、同じK/k、d. h.、力の作用による二場の定義、電気的・磁気的質量の区別、二つのプライム付き三成分表記を全て保持したと、明示した試験系の読みの下で判断する。',
 'u0162の六式全体を原刊908頁で再読し、18偏微分の成分と軸、1/V、正負、プライムを照合した。直前の条件付き要求の具体化であり、六式の全部を欠落なく記述したと判断する。',
)

@lru_cache(None)
def records():
    catalog=load_catalog(ROOT,BASIS)
    paths={FULL,CORE,BASIS,ANNOTATIONS,SOURCE,REPORT,INVENTORY,DOC,*PRIORS,*DEPENDENCIES,'scripts/review_moving_field_definition.py','tests/test_moving_field_definition_review.py'}
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
            f"固定{s['unit']}の全範囲と全数式要素{[m['id'] for m in s['math']]}を原刊908頁へ照合した。一文の条件・説明・二場・六式を連続して読み、ハッシュを固定した。",
            SEMANTICS[i],
            'K/kはra/zbm、Vはtc、移動系の二場znr/znsと領域znt、三空間軸と時刻、ta/rbの尺度を保つ。試験電荷と試験磁極の応答を同じ電磁過程eisppへ結び、同じ理論・法則・履歴の二記述を共有する。',
            'zcは著者が原理の適用から条件文を要求する提示であり、前件又は後件の真理を自動認定しない。ufでd. h.の説明と式の具体化を結び、表示内容は同じejtwへ固定する。eir3は同じ著者と論説へ帰属する。',
            '試験量の正負・零、全有効点と全三成分を保持する。試験体の実在や孤立磁荷の発見、慣性質量、磁石全体への合力、前文の混合関数との等値を追加しない。全法則の原理を成功例だけへ縮めず、別理論の証人を取り混ぜない。',
            '電荷は既存zor、磁極強度は二極性と局所力で尺度を与える明示した基本量として採る。理想応答eisptと単位積eispuは一般の物理的同定規約であり、その全点の比例・座標・三成分・量化は合成する。機械力と場の意味を原語の綴りや説明なしの式で代用しない。',
            '正負・零の試験量、各三成分、四つの座標、全範囲、物理的帰属の全引数、九つの証人位置、原理と適用の理論共有、法則適合との真偽対応、条件文と引用の提示を検査した。下位の六式・真空・第一原理は固定証拠を再利用する。有限対照や検査成功から意味判断を自動生成しない。',
            WHOLE[i],
        )
        assert len(reasons)==len(REQUIREMENTS)
        out.append(dict(schema_version='noema-semantic-review-1',work='einstein-1905',unit=s['unit'],reviewer='assistant_review',decision='equivalent_under_stated_reading',document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source=dict(inventory=INVENTORY,unit_sha256=s['unit_sha256'],text=s['text'],range=s['range'],math=[{k:m[k] for k in ('id','sha256')} for m in s['math']]),selection=selection_binding(catalog,[INDEX]),source_order_statements=[INDEX],clauses=clauses,interpretation=LIMITS,limits=['明示した読みの下でのアシスタントによる全単位の通読判断。独立査読や意味同値の自動証明ではない。','理想試験系と局所的な磁極という解釈を明示した。原著者の物理的な主張の真理、実在する孤立磁荷、極限実験の完遂を認定していない。','u0163以降と二作品全体の目標は未完。'],unresolved=[],requirements=[dict(id=k,decision='satisfied',reason=v) for k,v in zip(REQUIREMENTS,reasons)],evidence=dict(source_reading=[SOURCE],formal_checks=[REPORT,*DEPENDENCIES],semantic_reading=[DOC]),reviewed_prose_characters=s['source_nonblank_characters'],source_sha256=pins))
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
    return dict(status='moving_field_definition_two_whole_units_reviewed',document=FULL,source_units={r['unit']:r['reviewed_prose_characters'] for r in records()},reviewed_math_elements=7,whole_units_semantically_verified=True,verified_full_units={'kant-1784':0,'einstein-1905':2},semantic_equivalence_automatically_proved=False,source_sha256=pins)
