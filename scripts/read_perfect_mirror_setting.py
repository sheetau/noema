"""Pin the complete mirror supposition sentence without claiming the question."""
from functools import lru_cache
import json,re
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,selection_binding,REQUIREMENTS
from scripts.compose_perfect_mirror_setting import ROOT,read,FULL,BASIS,INDEX,LIMITS,MEANINGS

INVENTORY='artifacts/written-units-v1/einstein-1905.json';SOURCE='data/light-complex-facsimile-v1.json'
DOC='docs/perfect-mirror-setting-v1.md';READING='data/einstein-perfect-mirror-setting-sentence-reading-v1.json'
PRIOR='data/einstein-energy-frequency-law-u0214-review-v1.json'
REASONS=(
 '原刊914頁のu0215第一文を句点まで通読した。Es sei nun、Koordinatenebene、ξ=0、vollkommen spiegelnde Fläche、同じ面への関係節、前節の同じ平面波と反射を保持する。範囲は[0,157)、本文130非空白文字とM0368である。',
 '同じ完全な物質点履歴によるkのξ=0面と、同じ波の入射・戻りの全三方向・全六成分・位相を結ぶ。完全導体の候補では境界の接線電場と法線磁場が相殺し、完全な四経路モデルで通過と物体移転が零になる。',
 '前節の同じ源・波・過程・二場・近似・周期・観測者の設定をeketから再利用する。一つの66設定で面、反射過程、領域、単位と係数を共有し、別の波や未計上のエネルギーへ取り替えない。',
 'Es seiをeislzによる思考上の想定とugによる採用へ結び、現実成立の追加の断言にしない。前節参照をeisovとeisraへ、nunの論述の進行を前のu0214からのueへ結ぶ。',
 '静止した完全導体の平滑面、負の法線側からの非零入射、局所の先行近似を引き継ぐ代表モデルという読みを明示する。実際の誤差零、全材料の微視的機構、全域測定や製作可能性を補わない。',
 '物質的平面・二系の記録・波と場・位相と周期・流と単位・全点条件を既存規約から合成する。二つの一般関係は界面における物理的な波と収支モデルの対応であり、完全性と物理式や一文全体を原始語義に収納しない。',
 '流の向き、透過と物体移転の別の零、空の境界、全四座標、全66引数と62証人、同じ単位・過程・時間範囲、引用の非実行と仮定の提示を対照する。有限の結果を物理的な全域存在や原文同義性の自動証明としない。',
 '前の共通変換則から次のWir fragenまで再読した。明示した理想面と代表モデルの読みの下で、この第一文の対象・完全反射・前節照応・仮定提示を記述したと判断する。第二文の四量の問いは未完として分離する。',
)

@lru_cache(None)
def build_reading():
    inv=json.loads(read(INVENTORY));u=inv['units'][214];s=u['text'][:157];math={m['id']:m for m in inv['math']}
    assert s=='Es sei nun die Koordinatenebene [M0368] eine vollkommen spiegelnde Fläche, an welcher die im letzten Paragraph betrachteten ebenen Wellen reflektiert werden.'
    assert u['text'][158:].startswith('Wir fragen');assert digest(u['text'].encode('utf-8'))==u['text_sha256']
    assert len(re.sub(r'\s','',re.sub(r'\[M\d+\]','',s)))==130
    image=json.loads(read(SOURCE))['images'][1];assert image['printed_page']==914 and digest((ROOT/image['path']).read_bytes())==image['sha256']
    catalog=load_catalog(ROOT,BASIS);segment=dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[0,157],source=s,reviewed_prose_characters=130,math=[dict(id='M0368',sha256=math['M0368']['sha256'])],statements=[INDEX],definitions=list(MEANINGS),status='explicit_interpretive_annotation')
    paths=[INVENTORY,SOURCE,DOC,PRIOR,image['path'],'scripts/read_perfect_mirror_setting.py']
    return dict(schema_version='noema-sentence-reading-1',status='perfect_mirror_supposition_sentence_checked_under_explicit_reading',reviewer='assistant_close_reading',document=FULL,meaning_basis=BASIS,unit=u['id'],range=[0,157],source=s,source_text_sha256=u['text_sha256'],source_nonblank_characters=130,reviewed_prose_characters=130,reviewed_math_elements=1,math=segment['math'],segments=[segment],selection=selection_binding(catalog,[INDEX]),requirements=[dict(id=k,judgment='preserved_under_stated_reading',reason=v) for k,v in zip(REQUIREMENTS,REASONS)],definitions=list(MEANINGS),interpretation_limits=LIMITS,whole_paragraph_complete=False,verified_full_units=0,semantic_equivalence_automatically_proved=False,remaining_in_paragraph=['u0215[158,末尾)の光圧と反射後の方向・周波数・強度の問い'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in paths})
