"""Read the complete common-law observation and its noteworthy appraisal."""
from functools import lru_cache
import json,re
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,selection_binding,REQUIREMENTS
from scripts.compose_energy_frequency_law import ROOT,read,FULL,BASIS,INDEX,LIMITS,MEANINGS

INVENTORY='artifacts/written-units-v1/einstein-1905.json';SOURCE='data/light-complex-facsimile-v1.json'
DOC='docs/energy-frequency-law-v1.md';READING='data/einstein-energy-frequency-law-reading-v1.json'
PRIOR='data/einstein-light-energy-ratio-u0213-review-v1.json'
REASONS=(
 '原刊914頁のu0214を通読した。二種類の量、同じ光の部分、同じ法則、観測者の運動状態に伴う変化、bemerkenswertという評価と句点を確認した。本文に独立の新数式はない。',
 '既存の一般総量比ekpnと同じ観測者の一般周期数則ekeuを、同じV,v,aの共通倍率seckへ結ぶ。E′=D*Eとν′=D*νという同じ関数形を述べ、Eとνの値の同一性へ替えない。',
 '前の同じ部分・波・二系・単位・平均密度と積分、同じ源・観測者・周期・受信経路を一つの70設定から共有する。speed、方向、energy/newenergyとfrequency/newfrequencyを取り違えない。',
 '法則と注目価値の評価を別のuhとして同じ著者・箇所・第八節へ帰属し、先行一般エネルギー比への参照と直前の零角表示からの本文順序を保つ。',
 '運動状態は先行する標準慣性配置の許容相対速度と方向角によるものと読む。65役割の全許容割当を扱い、零角標本、加速の時間発展、実測記録又は光速観測者に替えない。',
 '共通倍率seck、全称条件、既存の物理設定、注目価値s2z/zld/zleを合成し、新しい一般関係を追加しない。新原始記号eisuaは本文箇所への参照であり、全文の意味を語義へ格納しない。',
 '二量の独立な初期値・同倍率と異倍率、運動入力、全65束縛と70引数、評価の対象と状況、引用の非実行・未知入力拒否を検査する。過去の積分・周期・運動の証拠は不変性を確認して再利用する。',
 '前文の一般比と特殊表示からu0214を再読した。同じ部分の平均総量・周期数・標準運動と注意価値の明示した読みの下で、一文全体を欠落なく記述したと判断する。',
)

@lru_cache(None)
def build_reading():
    inv=json.loads(read(INVENTORY));u=inv['units'][213];s=u['text']
    assert s=='Es ist bemerkenswert, daß die Energie und die Frequenz eines Lichtkomplexes sich nach demselben Gesetze mit dem Bewegungszustande des Beobachters ändern.'
    assert not u['math_ids'] and not u['annotation_ids'];assert digest(s.encode('utf-8'))==u['text_sha256']
    facsimile=json.loads(read(SOURCE));image=facsimile['images'][1];assert image['printed_page']==914 and digest((ROOT/image['path']).read_bytes())==image['sha256']
    segment=dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[0,len(s)],source=s,reviewed_prose_characters=len(re.sub(r'\s','',s)),math=[],statements=[INDEX],definitions=list(MEANINGS))
    catalog=load_catalog(ROOT,BASIS);paths=[INVENTORY,SOURCE,DOC,PRIOR,image['path'],'scripts/read_energy_frequency_law.py']
    return dict(schema_version='noema-sentence-reading-1',status='same_energy_frequency_motion_law_and_appraisal_read',reviewer='assistant_close_reading',document=FULL,meaning_basis=BASIS,segments=[segment],reviewed_prose_characters=133,reviewed_math_elements=0,selection=selection_binding(catalog,[INDEX]),requirements=[dict(id=k,judgment='preserved_under_stated_reading',reason=v) for k,v in zip(REQUIREMENTS,REASONS)],interpretation_limits=LIMITS,verified_full_units=0,semantic_equivalence_automatically_proved=False,source_sha256={p:digest((ROOT/p).read_bytes()) for p in paths})
