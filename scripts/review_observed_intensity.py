"""Review the hypothetical source-intensity boundary under the stated reading."""
from functools import lru_cache
import json
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import REQUIREMENTS,digest,selection_binding,validate_hashes,validate_review
from noema.review_registry import merge_pins
from scripts.compose_observed_intensity import ROOT,read,FULL,CORE,BASIS,ANNOTATIONS,LIMITS,INDEX
from scripts.check_observed_intensity import DOC,SOURCE,INVENTORY,DEPENDENCIES,source_record
REPORT='reports/observed-intensity-v1.json';REVIEW='data/einstein-observed-intensity-u0201-review-v1.json'

@lru_cache(None)
def record():
    catalog=load_catalog(ROOT,BASIS);s=source_record()['segments'][0];text=s['text'];first=text.index('daß');second=text.index(', diese Lichtquelle')+1
    paths={FULL,CORE,BASIS,ANNOTATIONS,SOURCE,REPORT,INVENTORY,DOC,*DEPENDENCIES,'docs/radiative-intensity-v1.md','docs/observed-amplitude-v1.md','scripts/review_observed_intensity.py','tests/test_observed_intensity_review.py'}
    pins={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)};merge_pins(pins,catalog.source_sha256)
    for p in (SOURCE,REPORT,*DEPENDENCIES):
        evidence=json.loads(read(p));validate_hashes(ROOT,evidence['source_sha256']);merge_pins(pins,evidence['source_sha256'])
    clauses=[
      dict(range=[0,first],text=text[:first],statements=[INDEX],definitions=['ekco','ekik','ekkk','ekkl','ekkm','eissb','zc'],reason='先行の同じ波の変換表示・一般振幅比を展開済みの式として参照し、同じ強度の境界内容がそこから従うという著者の提示を保持する。'),
      dict(range=[first,second],text=text[first:second],statements=[INDEX],definitions=['eket','ekia','ekkd','ekke','ekkf','ekkg','eisoe','eiscv','ekkh','ekjt'],reason='同じ光源・波・観測者の条件を共有する。源の−R*n、旧法線−xと旧実数角π、同じ観測者の+x速度で接近を構成し、M0348=Vでの仮定を0<v<Vの許容代替設定がVへ下から近づく境界として読む。'),
      dict(range=[second,len(text)],text=text[second:],statements=[INDEX],definitions=['eiste','eistf','ekjy','ekjz','ekka','ekkb','ekkc','ekkg','ekki','ekkj','ekjt','ekkn','ekko','uh','eir3','ue'],reason='同じ源の放射を同じ観測者の系の平均エネルギー流へ結び、正の入射流を固定した非空な関係の全出力について無限への発散を述べる。erscheinenを受信系での量の現れ、müßteをその理論内の仮定的帰結として保持し、実測や規範的要求へ替えない。'),
    ]
    assert all(n in catalog.entries for clause in clauses for n in clause['definitions'])
    reasons=[
      '固定在庫u0201全文160非空白本文文字とM0348=Vを、保存した原刊912頁及び直前の振幅式の照合記録と対応させた。Es folgt、展開済みの式、観測者と光源、näherte、unendlich intensiv、erscheinen müßteを落とさず、原文及び画像をハッシュで固定した。',
      '同じ光源の同じ放射を、同じ観測者の系での単位横断面積を通るエネルギー流の周期平均として読む。光速で接近するという反実仮想は、理論内の有限速度の代替設定がVへ下から近づく境界とする。その関係の任意に近い点の存在及び任意上限を超える全出力を述べる。',
      '66設定で同じ源・波・過程・観測者・二系・校正単位・場・振幅・周期を束縛する。50背景は入射波と正の入射平均流を含め固定し、速度で変わる補助量と代替状況の16証人を一つの点の中で共有する。diese Lichtquelleを同じsourceから生じたwaveの対応に保持する。',
      '先行ekco及びekikを展開済みの式への内容参照にし、eissbで当文の強度・接近を伴う適用形を明示する。zcで同じ境界主張が従うという著者の提示、uhで仮定範囲内の主張、eir3で同じ著者・論説への帰属、ueで直前表示との順序を保持する。引用内容を帰属時に真として実行しない。',
      '採用読解は非零の伝播する真空光の局所平面波、強度はエネルギー流の周期平均、光速での仮定は非到達の左境界であると明記した。当文の横波条件を先行の一般振幅の主張へ遡及追加しない。零入射、心理的明るさ、測定実施、光速観測者の実在、全領域外の厳密場、同一現実状況での複数速度を補わない。',
      'エネルギーを仕事と交換収支、単位を力と変位の積へ結ぶ一般校正eisteと、数式を波のエネルギー流モデルとして採用する一般対応eistfを分けた。外積・三方向・正弦二乗・周期積分・平均・接近・境界・対象同一性は合成し、文全体を一つの原始語へ隠さない。',
      '周期積分の同じ引数、三流成分、物理的な単位と役割、66設定全位置、代替状況の全経路、16存在位置、62及び46全称位置、50背景位置、引用と帰結を検査した。前段の1460対照と4代数補題も保持する。有限の周期波形は診断用であり正弦の周期積分定理の証明ではなく、全実数・全関数の評価は拒否する。',
      '一文を再読し、展開済みの式から、同じ源へVで近づくという仮定、同じ源の放射が同じ観測者に無限に強く現れるという帰結まで、関係・量・参照・提示を接続したと判断する。境界読解と非零の真空平面波の平均流という明示解釈の下での判断であり、唯一の歴史的意図や物理的真理の自動証明とはしない。',
    ]
    assert len(reasons)==len(REQUIREMENTS)
    return dict(schema_version='noema-semantic-review-1',work='einstein-1905',unit=s['unit'],reviewer='assistant_review',decision='equivalent_under_stated_reading',document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source=dict(inventory=INVENTORY,unit_sha256=s['unit_sha256'],text=text,range=s['range'],math=[{k:m[k] for k in ('id','sha256')} for m in s['math']]),selection=selection_binding(catalog,[INDEX]),clauses=clauses,interpretation=LIMITS,limits=['明示した解釈の下でのアシスタントによる意味判断であり、独立査読や意味同義性の自動証明ではない。','光速での反実仮想を有限速度からの境界として読み、非零の真空平面波の周期平均流を強度として採る。唯一の歴史的意図の確定ではない。','u0178及びu0202以降と二作品全体の目標は未完。'],unresolved=[],requirements=[dict(id=k,decision='satisfied',reason=v) for k,v in zip(REQUIREMENTS,reasons)],evidence=dict(source_reading=[SOURCE,'data/einstein-radiative-intensity-reading-v1.json'],formal_checks=[REPORT,*DEPENDENCIES],semantic_reading=[DOC,'docs/radiative-intensity-v1.md','docs/observed-amplitude-v1.md']),reviewed_prose_characters=s['source_nonblank_characters'],source_sha256=pins)

def prepare():
    from scripts.audit_opening_scope import write_exact
    write_exact(ROOT/REVIEW,json.dumps(record(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    r=record();assert json.loads(read(REVIEW))==r
    active=dict(document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source_inventory=INVENTORY)
    validate_review(ROOT,REVIEW,'einstein-1905',active,load_catalog(ROOT,BASIS),json.loads(read(INVENTORY)))
    return dict(status='hypothetical_source_intensity_at_light_speed_whole_unit_reviewed',document=FULL,source_units={r['unit']:r['reviewed_prose_characters']},reviewed_math_elements=1,whole_units_semantically_verified=True,verified_full_units={'kant-1784':0,'einstein-1905':1},semantic_equivalence_automatically_proved=False,source_sha256=r['source_sha256']|{REVIEW:digest((ROOT/REVIEW).read_bytes())})
