"""Pin the moving-frame energy question and its explanatory restatement."""
from functools import lru_cache
import json,re
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,selection_binding,validate_hashes,REQUIREMENTS
from scripts.compose_portion_energy_inquiry import ROOT,read,FULL,BASIS,INDEX,LIMITS,MEANINGS

INVENTORY='artifacts/written-units-v1/einstein-1905.json';SOURCE='data/einstein-radiative-density-reading-v1.json'
DOC='docs/portion-energy-inquiry-v1.md';READING='data/einstein-portion-energy-inquiry-sentence-reading-v1.json'
PRIOR='data/einstein-same-light-portion-tail-sentence-reading-v1.json'
REASONS=(
 '原刊913頁のu0205第二文[108,272)を通読し、二つの系記号M0356とM0357がともにkであることを照合した。d. h.中の二つの点で文を分割しない。',
 'この面の内部にあるエネルギーを、同じ光の部分の新系同時断面の位相平均密度の空間積分へ結ぶ。総量と密度、瞬間値と平均、球面とその閉内部を区別する。',
 '同じ68設定を先に固定し、候補だけを変える。部分zvaa、旧系K、既出V、二つのk、新旧単位、逆Lorentz領域、同じ時刻断面と密度を保持する。新総量の既知値又は存在証人を条件に入れない。',
 'Wir fragenを著者の条件付き質問提示eistsへ、d.h.を同じ問いのekodからekoeへの説明eismeへ結ぶ。後半を独立の新しい質問行為、答えの主張又は質問への肯定回答にしない。',
 '平均エネルギー、後続τ=0に合わせた断面、初期部分の連続体輸送の読みを明示する。実測済み、既知の答え、解の存在・唯一性、後続の総量比の導出済みを追加しない。',
 'eistsは型付きの一般質問族提示であり、具体的な光やエネルギーを語義へ含めない。波・物理的単位・密度・部分の割当は既存関係へ、候補は空間積分へ合成して接続する。',
 '設定の分離、全68役割、同じ初期部分への接続、候補と実際の積分、空・単一・複数回答、引用の非実行と説明の向きを検査する。有限モデルと全実数の理論・原文の通読判断は別の根拠である。',
 '前の球面内の持続する同じ部分から次の楕円体の説明まで再読し、明示した位相平均と同時断面の読みの下で、同じ量の質問・参照・言換え・著者帰属を記述したと判断する。',
)

@lru_cache(None)
def build_reading():
    inv=json.loads(read(INVENTORY));u=inv['units'][204];s=u['text'][108:272];math={m['id']:m for m in inv['math']}
    assert s.startswith('Wir fragen') and s.endswith('System [M0357].')
    ids=re.findall(r'\[(M\d+)\]',s);assert ids==['M0356','M0357']
    count=len(re.sub(r'\s','',re.sub(r'\[M\d+\]','',s)))
    validate_hashes(ROOT,json.loads(read(SOURCE))['source_sha256']);catalog=load_catalog(ROOT,BASIS)
    paths=[INVENTORY,SOURCE,DOC,PRIOR,'artifacts/written-facsimiles-v1/einstein-p913-0.jpg','scripts/read_portion_energy_inquiry.py']
    return dict(schema_version='noema-sentence-reading-1',status='same_portion_energy_inquiry_and_gloss_checked_under_explicit_reading',reviewer='assistant_close_reading',document=FULL,meaning_basis=BASIS,unit=u['id'],range=[108,272],source=s,source_text_sha256=u['text_sha256'],source_nonblank_characters=count,reviewed_prose_characters=count,reviewed_math_elements=2,math=[dict(id=n,sha256=math[n]['sha256']) for n in ids],selection=selection_binding(catalog,[INDEX]),requirements=[dict(id=k,judgment='preserved_under_stated_reading',reason=v) for k,v in zip(REQUIREMENTS,REASONS)],definitions=list(MEANINGS),interpretation_limits=LIMITS,whole_paragraph_complete=False,verified_full_units=0,semantic_equivalence_automatically_proved=False,remaining_in_paragraph=[],source_sha256={p:digest((ROOT/p).read_bytes()) for p in paths})
