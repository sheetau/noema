"""Review the entire material-mirror supposition and four-quantity question unit."""
from functools import lru_cache
from pathlib import Path
import json,re
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import REQUIREMENTS,digest,selection_binding,validate_hashes,validate_review
from noema.review_registry import merge_pins
# A review reads the generated evidence. Importing the newest composer merely
# for constants traverses the historical composer chain and can exhaust Python's
# import stack; neither generation nor numerical fixtures are needed here.
ROOT=Path(__file__).resolve().parents[1]
def read(path):return (ROOT/path).read_text(encoding='utf-8')
FULL='examples/v014/einstein-reflected-light-inquiry.noema';CORE='examples/v014/reflected-light-inquiry-core.noema'
BASIS='data/reflected-light-inquiry-basis-v1.json';ANNOTATIONS='data/reflected-light-inquiry-identifiers-v1.json';INDEX=395
INVENTORY='artifacts/written-units-v1/einstein-1905.json';SOURCE='data/light-complex-facsimile-v1.json'
DOC='docs/reflected-light-inquiry-v1.md';READING='data/einstein-reflected-light-inquiry-sentence-reading-v1.json'
PRIOR='data/einstein-perfect-mirror-setting-sentence-reading-v1.json'

REPORT='reports/reflected-light-inquiry-v1.json';REVIEW='data/einstein-reflected-light-inquiry-u0215-review-v1.json'
PREVIOUS_REPORT='reports/perfect-mirror-setting-v1.json';PREVIOUS_DOC='docs/perfect-mirror-setting-v1.md'

@lru_cache(None)
def record():
    catalog=load_catalog(ROOT,BASIS);inv=json.loads(read(INVENTORY));u=inv['units'][214];text=u['text'];math={m['id']:m for m in inv['math']}
    paths={FULL,CORE,BASIS,ANNOTATIONS,INVENTORY,SOURCE,DOC,READING,REPORT,PRIOR,PREVIOUS_DOC,PREVIOUS_REPORT,'scripts/review_reflected_light_inquiry.py','tests/test_reflected_light_inquiry_review.py'}
    pins={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)};merge_pins(pins,catalog.source_sha256)
    # SOURCE is an image manifest, already pinned above; the two readings pin
    # and verify the actual page image as well as that manifest.
    for p in (REPORT,READING,PRIOR,PREVIOUS_REPORT):
        evidence=json.loads(read(p));validate_hashes(ROOT,evidence['source_sha256']);merge_pins(pins,evidence['source_sha256'])
    first=json.loads(read(PRIOR));second=json.loads(read(READING));limits=json.loads(read(BASIS))['limitations']
    clauses=[dict(range=r['range'],text=r['source'],statements=[i],definitions=r['definitions'],reason=r['requirements'][-1]['reason']) for r,i in [(first,394),(second,INDEX)]]
    reasons=[
      '原刊914頁でu0214の共通変換則からu0215の二文、後続の入射・反射のk表示とKへの帰還まで通読した。u0215全304文字の範囲、255非空白本文文字とM0368=ξ=0を固定する。第一文[0,157)と第二文[158,304)の間にある空白以外の全範囲を保持する。',
      '同じ完全な物質的平面、同じ前節の平面波、同じ界面相互作用と戻りの波を保持し、完全反射を静止系kでの全四経路の収支と透過・物体移転の別々の零へ結ぶ。その同じ面への平均法線力と反射後の方向・周期数・平均流を四量の問いへ接続する。',
      'im letzten Paragraphを前の番号付き第七節へ結び、die spiegelnde Flächeとdes Lichtes nach der Reflexionを第一文の同じ物体・波・過程へ結ぶ。第二文の74設定は前文の66設定をそのまま保持し、六実数候補の外側で一つの割当を共有する。',
      'Es seiの思考上の想定と採用、nunの論述順序、Wir fragenの著者による問いの提示をそれぞれ保持する。仮定の現実成立や測定済み、答えの主張、解の存在・一意性へ置き換えない。',
      '厚さ零の物質的平面シート、静止した完全導体の平滑面の代表反射モデル、負の法線側からの非零入射、後続に合わせるKの四量という読みを明示する。前節の近似を保存し、実際の場の誤差零や全材料の反射解の唯一性を追加しない。圧力は同じ物質部分の一周期平均、強度はK静止位置の反射波の一周期平均で、二つの時間幅を混同しない。',
      '物質点履歴・同一出来事記録・Lorentz変換・全成分の場・同じ単位とエネルギー流・全域の周期と積分を既存規約から合成する。新しい物理対応は界面波と完全な四経路モデルの一般関係、質問提示は型付きの一般関係であり、一文の意味を原始語義へ格納しない。',
      '第一文の保存済み614対照と今回の逆変換・全点照射・74設定・六候補・平均区間・質問・引用・全既存記述保存の検査を証拠として分離する。有限対照を実数全域のモデル存在、一般積分又は意味同義性の自動証明へ変えない。',
      '完全反射面の仮定からその面への光圧と反射後の光の方向・周波数・強度を問う二文を再読した。明示した理想面・代表モデル・K・周期平均の読みの下でu0215の内容・照応・条件・仮定及び質問の提示を欠落なく記述したと判断する。',
    ]
    count=len(re.sub(r'\s','',re.sub(r'\[M\d+\]','',text)));assert count==255
    assert first['reviewed_prose_characters']+second['reviewed_prose_characters']==count
    source=dict(inventory=INVENTORY,unit_sha256=u['text_sha256'],text=text,range=[0,len(text)],math=[dict(id=n,sha256=math[n]['sha256']) for n in u['math_ids']])
    return dict(schema_version='noema-semantic-review-1',work='einstein-1905',unit=u['id'],reviewer='assistant_review',decision='equivalent_under_stated_reading',document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source=source,selection=selection_binding(catalog,[394,INDEX]),clauses=clauses,interpretation=first['interpretation_limits']+limits,limits=['明示した読みの下でのアシスタントによる判断であり、独立査読又は意味同義性の自動証明ではない。','現実の鏡の製作可能性、完全導体候補の全材料での唯一性、実際の場の誤差零は主張しない。','後続の入射量の導入、各系の式と変換の提示、光圧の仕事による導出及び二作品全体は未完。'],unresolved=[],requirements=[dict(id=k,decision='satisfied',reason=v) for k,v in zip(REQUIREMENTS,reasons)],evidence=dict(source_reading=[SOURCE,PRIOR,READING],formal_checks=[PREVIOUS_REPORT,REPORT],semantic_reading=[PREVIOUS_DOC,DOC]),reviewed_prose_characters=count,source_sha256=pins)

def prepare():
    from scripts.audit_opening_scope import write_exact
    write_exact(ROOT/REVIEW,json.dumps(record(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    active=dict(document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source_inventory=INVENTORY);catalog=load_catalog(ROOT,BASIS);inv=json.loads(read(INVENTORY));r=record()
    assert json.loads(read(REVIEW))==r
    validate_review(ROOT,REVIEW,'einstein-1905',active,catalog,inv)
    pins=dict(r['source_sha256']);pins[REVIEW]=digest((ROOT/REVIEW).read_bytes())
    return dict(status='material_mirror_supposition_and_four_quantity_question_whole_unit_reviewed',document=FULL,source_units={r['unit']:255},reviewed_math_elements=1,whole_units_semantically_verified=True,verified_full_units={'kant-1784':0,'einstein-1905':1},semantic_equivalence_automatically_proved=False,source_sha256=pins)
