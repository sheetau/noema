"""Review the complete three-sentence field comparison and its six equations."""
from functools import lru_cache
import json
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import REQUIREMENTS,digest,selection_binding,validate_hashes,validate_review
from noema.review_registry import merge_pins
from scripts.compose_field_comparison_claim import ROOT,read,FULL,CORE,BASIS,ANNOTATIONS,INDEX,LIMITS
from scripts.check_field_comparison_claim import DOC,SOURCE,INVENTORY,PRIORS,DEPENDENCIES,source_record

REPORT='reports/field-comparison-claim-v1.json'
REVIEWS=tuple(f'data/einstein-field-comparison-claim-u{n:04d}-review-v1.json' for n in (163,164))
CLAUSES=(
 (('Offenbar müssen nun die beiden für das System [M0301] gefundenen Gleichungssysteme genau dasselbe ausdrücken, ',['ejub','ejue','ejuf','ejul','ejrj','zdg'],'同じkの二組が同じ意味を表すという必要性と、著者による明白さの提示を保持する。'),
  ('da beide Gleichungssysteme den Maxwell-Hertzschen Gleichungen für das System [M0302] äquivalent sind. ',['ejuc','ejud','ejul','ejs6','s6o','ejtw','zc'],'同じKの式との二つの双方向の等価性を、同じ比較範囲で第一文の理由として接続する。'),
  ('Da die Gleichungen beider Systeme ferner bis auf die die Vektoren darstellenden Symbole übereinstimmen, ',['ejug','ejuk','eispz','s5y'],'さらに、同じ六式の型でベクトル表記だけが異なるという構造上の一致を加える。二場の数値一致ではない。'),
  ('so folgt, daß die in den Gleichungssystemen an entsprechenden Stellen auftretenden Funktionen bis auf einen für alle Funktionen des einen Gleichungssystems gemeinsamen, von [M0303] und [M0304] unabhängigen, eventuell von [M0305] abhängigen Faktor [M0306] übereinstimmen müssen. ',['ejuh','ejui','ejuj','ejum','sak2','sai2','saj2','znz'],'同じ一つのψ(v)を全六成分・領域全体で共有する必要性を結論とする。三座標と時刻から独立し、速度への依存を許すが強制しない。著者の推論の提示を保持する。'),
  ('Es gelten also die Beziehungen:',['ejun','ejuo','eisox','zc','uf'],'前の必要性から続く具体的な六式を結果として導入し、その表示へ説明関係と順序を結ぶ。')),
 (('[M0307]',['ejuh','ejun','s6k','s6l','s6m','sai2','saj2','sak2'],'同じψ(v)、β、V/vで六つの対応成分を結ぶ。逆座標写像による引数と全領域一致を保持し、M′右辺のz/Zは保存した原刊の局所訂正に従う。'),),
)
SEMANTICS=(
 '第一文の二つのKとの等価性、二組が同じ意味を表す必要性、Offenbarをそれぞれ構成する。第二文のさらに同形である理由から全六関数の共通係数への必要性を結び、第三文の結果導入へ続ける。比例や方程式の成否で最初の比較範囲を選ばない。',
 'X′とL′には同じψ(v)、他の四成分には同じψ(v)βと対応するv/Vの混合を用いる。全六成分を同じ四座標と逆写像で評価し、非空の全領域で同じ一つの係数を要求する。',
)
WHOLE=(
 'u0163の三文全体を原刊908頁と先行二組の式に照合して再読した。明白さ、必要性、二つの理由、追加、等価性、同形性、対応関数の全範囲、係数の共通性と独立変数の範囲、速度依存の許容、帰結の表示導入まで保持したと、明示した読みの下で判断する。',
 'u0164の全六式を原刊908頁で再読し、成分・プライム・正負・β・v/V・同じψ(v)を照合した。M′式の原刊Zへの局所訂正と生資料の保持を確認し、同じ場の関数と引数の変換として全六式を欠落なく記述したと判断する。',
)

@lru_cache(None)
def records():
    catalog=load_catalog(ROOT,BASIS)
    paths={FULL,CORE,BASIS,ANNOTATIONS,SOURCE,REPORT,INVENTORY,DOC,*PRIORS,*DEPENDENCIES,'scripts/review_field_comparison_claim.py','tests/test_field_comparison_claim_review.py'}
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
            f"固定{s['unit']}の全範囲と全数式要素{[m['id'] for m in s['math']]}を原刊908頁へ照合した。三文と六式を連続して読み、M0307の局所訂正は旧記録を参照して原資料と区別した。",
            SEMANTICS[i],
            'K/kはra/zbm、V/vはtc/zb7、元の二場znl/znmと領域znk、移動系の二場znr/znsと領域znt、同じ電磁過程eisppを保持する。二組の式はs6oとejtw、Kの式はejs6へ接続し、同じψ=znzを六成分全体で共有する。',
            'zcで各理由から各帰結への著者の提示を結び、zdgでOffenbar、ejrjで非空の全前提候補に対する必要性を構成する。eisoxとufで六式の具体化を結ぶ。引用された推論を処理系の定理や無条件な真理へ替えない。',
            '両方向の等価性を片方向含意へ弱めず、全領域を共通部分だけへ縮めない。全六関数へ同じ係数を使い、場所時刻や成分ごとの係数を許さない。定数のψも許し、非零性・正値・偶性・値1や全く別の場の組についての追加主張は補わない。',
            '同じ表示と閉じた式の型・引数の構造関係eispzを一般の規約として明示する。等価性は内容の真偽と非空全称、比例は既存の場評価・実数積・全点量化から構成し、原文の一文を未説明の一記号へ置換しない。',
            '同じ比較設定の全引数、両方向の真偽対応、非空の全候補、同形性の式型と全引数、正負・零の係数、全六成分と全点、三文の理由・明白さ・必要性・表示・著者帰属を対照した。先行六式の形も固定MathMLで正規化して比較した。既存の前提不足と非比例場の反例を保持する。',
            WHOLE[i],
        )
        assert len(reasons)==len(REQUIREMENTS)
        out.append(dict(schema_version='noema-semantic-review-1',work='einstein-1905',unit=s['unit'],reviewer='assistant_review',decision='equivalent_under_stated_reading',document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source=dict(inventory=INVENTORY,unit_sha256=s['unit_sha256'],text=s['text'],range=s['range'],math=[{k:m[k] for k in ('id','sha256')} for m in s['math']]),selection=selection_binding(catalog,[INDEX]),source_order_statements=[INDEX],clauses=clauses,interpretation=LIMITS,limits=['明示した読みの下でのアシスタントによる全単位の通読判断。独立査読や意味同値の自動証明ではない。','同じ微分方程式から比例が得られるという一般的な推論の正しさを認定せず、原著者の理由と結論の提示を記述する。','u0165以降と二作品全体の目標は未完。'],unresolved=[],requirements=[dict(id=k,decision='satisfied',reason=v) for k,v in zip(REQUIREMENTS,reasons)],evidence=dict(source_reading=[SOURCE],formal_checks=[REPORT,*DEPENDENCIES],semantic_reading=[DOC]),reviewed_prose_characters=s['source_nonblank_characters'],source_sha256=pins))
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
    return dict(status='field_comparison_claim_two_whole_units_reviewed',document=FULL,source_units={r['unit']:r['reviewed_prose_characters'] for r in records()},reviewed_math_elements=7,whole_units_semantically_verified=True,verified_full_units={'kant-1784':0,'einstein-1905':2},semantic_equivalence_automatically_proved=False,source_sha256=pins)
