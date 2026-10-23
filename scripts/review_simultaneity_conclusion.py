"""Review the complete, explicitly universal reading of the conclusion."""
from functools import lru_cache
import json,re
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import REQUIREMENTS,digest,selection_binding,validate_hashes,validate_review
from noema.review_registry import merge_pins
from scripts.compose_simultaneity_conclusion import ROOT,read,FULL,CORE,BASIS,ANNOTATIONS,INDEX,LIMITS

DOC='docs/simultaneity-conclusion-v1.md';SOURCE='data/einstein-simultaneity-conclusion-source-reading-v1.json';INVENTORY='artifacts/written-units-v1/einstein-1905.json'
REPORT='reports/simultaneity-conclusion-v1.json';REVIEW='data/einstein-simultaneity-conclusion-review-v1.json'
PRIORS=('data/einstein-observer-contrast-review-v1.json',)
DEPENDENCIES=('reports/observer-contrast-v1.json','reports/first-principle-v1.json','reports/local-clock-valuation-v1.json')
REASONS=(
 '固定u0041全325文字・283本文文字を原刊897頁のWir sehen alsoからaufzufassen sindまで照合した。数式のない一文であり、次の§3の見出しは含めない。',
 '同時性に絶対的な意味を与える解釈への禁止と、相対運動する系では非同時と捉える全称的な内容・認識上の要請を合成する。時刻付与、非零の等速並進、全四時刻の利用可能性を共通範囲へ結ぶ。',
 '同じ二出来事を両系で追い、各系の参照時計・局所表示・単位・唯一の時刻候補を保つ。先行する観測者の対比eiue、結論箇所zbk、著者rdと論説eirfを接続する。',
 'Wir sehen alsoは前段から見いだす結論の提示、dürfenは解釈上の許否、sondernは訂正的対置、aufzufassen sindは認識上の要請として保持する。nicht mehrは系を変えた捉え方である。',
 '旧sem/sepの運動方向の位置差を付け加えず、全称条件を変化例の存在へ弱めない。未付与を非同時、系変更を後日の変化、著者の帰属を内容の真理証明にしない。後段の変換公式や光速度上限を前提へ追加しない。',
 '絶対的な意味は系の比較で同時性が不変という適用上の性格として読む。二系は節の等速並進の文脈で捉える。汎用の方法的許否・認識上の要請・訂正的対置を明示し、文ごとの未分解な原始記号では代用しない。',
 '原文・画像・先行規約・局所検査を固定する。全称条件の偽となる有限モデルと引用への帰属を区別する検査は、著者の物理的結論、全実数、意味同値の自動証明ではない。',
 '前の時計判断の対比と次の変換理論の見出しを含む文脈で一文全体を通読した。文面の強い全称的な読みを明示し、その真偽の保証とは分けて全内容と論述上の働きを保持したと判断する。',
)

@lru_cache(None)
def source_record():
    inv=json.loads(read(INVENTORY));u=inv['units'][40]
    assert u['id']=='einstein-1905:u0041' and len(u['text'])==325
    assert u['text_sha256']=='d7a76cee5507db3a7dd6a62b48c3fb46a44db5279c62f8e52aa5f1b427b5ffaf'
    count=sum(not c.isspace() for c in u['text']);assert count==283 and not re.search(r'\[M\d+\]',u['text'])
    receipt='artifacts/einstein-moving-trip-v1/retrieval.json';paths={INVENTORY,DOC,'scripts/review_simultaneity_conclusion.py',receipt}
    for row in json.loads(read(receipt))['sources']:
        assert digest((ROOT/row['path']).read_bytes())==row['sha256'];paths.add(row['path'])
    return dict(version='einstein-simultaneity-conclusion-source-reading-v1',reviewer='assistant_visual_and_text_review',pages=['897'],segments=[dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[0,len(u['text'])],text=u['text'],nonblank_characters=count,math=[])],observations=['keine absolute Bedeutung beimessen dürfenは解釈への禁止を持つ。','sondern以下は二出来事が別の系では非同時と捉えられるという全称的な文面を持ち、位置差の限定は記されていない。','Wir sehen alsoは前段からの結論、nicht mehrは比較する系の変更として読む。'],semantic_completion=False,source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})

@lru_cache(None)
def record():
    catalog=load_catalog(ROOT,BASIS);segment=source_record()['segments'][0]
    paths={FULL,CORE,BASIS,ANNOTATIONS,INVENTORY,DOC,SOURCE,REPORT,*PRIORS,*DEPENDENCIES,'scripts/review_simultaneity_conclusion.py','tests/test_simultaneity_conclusion_review.py'}
    pins={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)};merge_pins(pins,catalog.source_sha256)
    for p in (SOURCE,REPORT,*DEPENDENCIES):
        evidence=json.loads(read(p));validate_hashes(ROOT,evidence['source_sha256']);merge_pins(pins,evidence['source_sha256'])
    return dict(schema_version='noema-semantic-review-1',work='einstein-1905',unit=segment['unit'],reviewer='assistant_review',decision='equivalent_under_stated_reading',document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source=dict(inventory=INVENTORY,unit_sha256=segment['unit_sha256'],text=segment['text'],range=segment['range'],math=[]),selection=selection_binding(catalog,[INDEX]),source_order_statements=[INDEX],interpretation=LIMITS,limits=['明示した全称的解釈の下のアシスタントによる通読判断。独立査読、物理的な結論の保証、同義性の自動証明ではない。','u0042以降と二作品全体の目標は未完。'],unresolved=[],requirements=[dict(id=k,decision='satisfied',reason=v) for k,v in zip(REQUIREMENTS,REASONS)],evidence=dict(source_reading=[SOURCE],formal_checks=[REPORT,*DEPENDENCIES],semantic_reading=[DOC]),source_sha256=pins)

def prepare():
    from scripts.audit_opening_scope import write_exact
    write_exact(ROOT/REVIEW,json.dumps(record(),ensure_ascii=False,indent=2)+'\n')

def build_report():
    rec=record();assert json.loads(read(REVIEW))==rec
    active=dict(document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source_inventory=INVENTORY)
    validate_review(ROOT,REVIEW,'einstein-1905',active,load_catalog(ROOT,BASIS),json.loads(read(INVENTORY)))
    return dict(status='simultaneity_conclusion_whole_unit_reviewed',document=FULL,source_units={'einstein-1905:u0041':283},whole_units_semantically_verified=True,verified_full_units={'kant-1784':0,'einstein-1905':1},semantic_equivalence_automatically_proved=False,source_sha256=rec['source_sha256']|{REVIEW:digest((ROOT/REVIEW).read_bytes())})
