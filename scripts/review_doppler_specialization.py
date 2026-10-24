"""Whole-unit reading of the named law, its speed scope and zero-angle form."""
from functools import lru_cache
import json
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import REQUIREMENTS,digest,selection_binding,validate_hashes,validate_review
from noema.review_registry import merge_pins
from scripts.compose_doppler_specialization import ROOT,read,FULL,CORE,BASIS,ANNOTATIONS,LIMITS
from scripts.check_doppler_specialization import DOC,SOURCE,INVENTORY,DEPENDENCIES,source_record

REPORT='reports/doppler-specialization-v1.json'
REVIEWS=['data/einstein-doppler-specialization-u0190-review-v1.json','data/einstein-doppler-specialization-u0191-review-v1.json']

@lru_cache(None)
def records():
    catalog=load_catalog(ROOT,BASIS)
    paths={FULL,CORE,BASIS,ANNOTATIONS,SOURCE,REPORT,INVENTORY,DOC,*DEPENDENCIES,'scripts/review_doppler_specialization.py','tests/test_doppler_specialization_review.py'}
    pins={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)};merge_pins(pins,catalog.source_sha256)
    for p in (SOURCE,REPORT,*DEPENDENCIES):
        evidence=json.loads(read(p));validate_hashes(ROOT,evidence['source_sha256']);merge_pins(pins,evidence['source_sha256'])
    out=[]
    for i,s in enumerate(source_record()['segments']):
        meaning='直前の放射・受信周期数の式をDoppelersche Prinzipという同じ呼称へ結び、先行の許容移動速度の全域を、同じ物理条件と数式の速度引数への全称量化で明示する。続いて同じ実数角φ=0の場合を取り、その式を見通しのよい形として導入する。' if i==0 else '同じφ=0の条件の下で、ν′=ν*sqrt((1−v/V)/(1+v/V))を表示する。差が分子、和が分母、平方根は正であり、νは根号の外へ掛かる。同じ源・波・観測者・系・単位の周期数を保持する。'
        presentation='eissbで先行内容と全速度の明示内容を結び、eischで原理名を後者へ対応させる。φ=0の一般形と簡明な形を同じ適用域でeissbへ結び、その形式の評価eissp、コロンと後続表示へのuf/ue、著者と論説へのeir3を保つ。' if i==0 else '直前のコロンに続く同じ表示として、eisoxで条件内容eke3へ結び、著者と論説へeir3で帰属する。独立した無条件の等式、実測報告又は別の法則の導入へ切り離さない。'
        if i==0:
            cut=s['text'].index(' Für')
            clauses=[dict(range=[0,cut],text=s['text'][:cut],statements=[372],definitions=['ekej','ekem','eker','eket','ekeu','ekev','eke2','eke5','eisch','eissb','eisss'],reason='Diesは先行eissnの同じ周期数の式を受ける。原理名と全速度の条件を結び、固定速度の別の物理設定を残さない。'),dict(range=[cut,len(s['text'])],text=s['text'][cut:],statements=[372],definitions=['ekey','ekez','eke3','eke4','eke6','eke7','ekfb','eissp','uf','ue'],reason='同じ実数角φ=0を条件にして一般式を平方根比の形で明示し、その形の見通しのよさとコロンから表示への提示を保持する。')]
        else:
            clauses=[dict(range=s['range'],text=s['text'],statements=[373],definitions=['ekew','ekey','ekez','eke3','ekfc','ekfe','eisox','eir3'],reason=meaning+' '+presentation)]
        assert all(n in catalog.entries for clause in clauses for n in clause['definitions'])
        reasons=[
          '固定在庫のu0190の二文とu0191の全表示、M0334とM0335のMathMLを原刊911頁末から912頁冒頭へ照合した。Doppelersche Prinzipの原綴り、φ=0、平方根の範囲と分数の分子分母を保持した。',
          meaning,
          'Diesはu0189の同じ一般ドップラー表示、die Gleichungはその式、M0334は同じ実数角φの零条件、M0335は同じνとν′の特殊形と読む。先行K/k、V、単位、源・過程・波・観測者・近似と位相の物理的役割を保持し、速度引数を全12依存定義へ渡す。',
          presentation,
          '任意速度は先行する移動観測者の標準配置0<v<Vの全域であり、一次近似や検査標本に縮めない。零速度の角の新規定義、超光速への拡張、独立の測定事実、全読者が容易に理解したという心理事実は補わない。式を理論に都合よく変更せず、後続u0192の無限大の印字も先取りしない。',
          '原理の名称は放射・受信の周期数の合成内容への命名規約で、原語の綴りだけを意味の代用にしない。新基本関係eisspは既出記号規約で式の量的依存を見渡しやすいという形式評価だけである。物理的対象、速度、角、周期数、等式、全称条件及び著者帰属は別に合成する。',
          '全12定義の速度伝達と元のzb7への特殊化による構造復元、実際の逆座標による領域、正確な有理数の複数速度比と尺度変更、角の零と他の枝、全56量化位置、命名・評価・表示の参照を検査する。全実数及び全関数域を有限標本に置き換えず、有限の通過を物理法則の一般証明や意味同義性の自動証明としない。',
          '前文の源・観測者の条件と一般式から続けて、原理の同定、任意速度、φ=0の場合、見通しのよい形、コロン及び同じ表示を再読した。明示した先行の移動標準配置・同じ周期成分の解釈の下で、今回の単位全体の内容と提示を欠落なく記述したと判断する。',
        ]
        assert len(reasons)==len(REQUIREMENTS)
        out.append(dict(schema_version='noema-semantic-review-1',work='einstein-1905',unit=s['unit'],reviewer='assistant_review',decision='equivalent_under_stated_reading',document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source=dict(inventory=INVENTORY,unit_sha256=s['unit_sha256'],text=s['text'],range=s['range'],math=[{k:m[k] for k in ('id','sha256')} for m in s['math']]),selection=selection_binding(catalog,s['statements']),clauses=clauses,interpretation=LIMITS,limits=['明示した解釈の下でのアシスタントによる意味判断であり、独立査読や意味同義性の自動証明ではない。','物理法則の真理及び全実数演算の一般的な定理を有限診断から証明していない。','u0178及びu0192以降と二作品全体の目標は未完。'],unresolved=[],requirements=[dict(id=k,decision='satisfied',reason=v) for k,v in zip(REQUIREMENTS,reasons)],evidence=dict(source_reading=[SOURCE],formal_checks=[REPORT,*DEPENDENCIES],semantic_reading=[DOC]),reviewed_prose_characters=s['source_nonblank_characters'],source_sha256=pins))
    return out

def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,r in zip(REVIEWS,records()):write_exact(ROOT/p,json.dumps(r,ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    active=dict(document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source_inventory=INVENTORY);catalog=load_catalog(ROOT,BASIS);inv=json.loads(read(INVENTORY));pins={}
    for p,r in zip(REVIEWS,records()):
        assert json.loads(read(p))==r
        validate_review(ROOT,p,'einstein-1905',active,catalog,inv);merge_pins(pins,r['source_sha256']);pins[p]=digest((ROOT/p).read_bytes())
    return dict(status='named_doppler_law_arbitrary_speeds_zero_angle_and_display_whole_units_reviewed',document=FULL,source_units={r['unit']:r['reviewed_prose_characters'] for r in records()},reviewed_math_elements=2,whole_units_semantically_verified=True,verified_full_units={'kant-1784':0,'einstein-1905':2},semantic_equivalence_automatically_proved=False,source_sha256=pins)
