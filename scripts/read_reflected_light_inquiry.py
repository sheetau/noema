"""Pin the complete second sentence and the resting-frame reading of its query."""
from functools import lru_cache
import json,re
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,selection_binding,REQUIREMENTS
from scripts.compose_reflected_light_inquiry import ROOT,read,FULL,BASIS,INDEX,LIMITS,MEANINGS
INVENTORY='artifacts/written-units-v1/einstein-1905.json';SOURCE='data/light-complex-facsimile-v1.json'
DOC='docs/reflected-light-inquiry-v1.md';READING='data/einstein-reflected-light-inquiry-sentence-reading-v1.json'
PRIOR='data/einstein-perfect-mirror-setting-sentence-reading-v1.json'
REASONS=(
 '原刊914頁のu0215[158,304)を句点まで通読し、Wir fragen、同じ面に及ぼされるLichtdruck、反射後の同じ光のRichtung/Frequenz/Intensitätを保持する。本文125非空白文字で、この文には式はない。',
 '光圧を同じ物質部分へのK法線力平均、方向を有向三成分、周波数をKの静止位置での周期数、強度を進行方向のエネルギー流の周期平均へ結ぶ。四量を六実数の候補として同じ問いにまとめる。',
 'die spiegelnde Flächeとdes Lichtes nach der Reflexionを第一文の同じbody/interaction/入射と戻りの波へ接続する。74設定を候補の外側で固定し、対象・単位・区間を選び直さない。',
 'Wir fragenを著者による条件付き質問の提示へ結ぶ。著者帰属と前文からの順序を保ち、答えの断言、解の存在・一意性、実験済みへ替えない。',
 '後続の静止系へ戻す記述に合わせるKの読みと、完全導体の局所代表モデル、同じ矩形の一周期平均を明示する。鏡上の時間変換と静止位置の周期を区別し、先行の近似を誤差零へ変更しない。',
 '鏡映と逆Lorentz変換、全域の周期条件、力の平均とエネルギー流積分を既存定義で合成する。一般関係eisufは型付きの質問提示で、光・鏡やこの一文の意味を原始語義へ収納しない。',
 '逆変換の方向と二偏光、面上の時間変換、全点照射、全74設定と六候補、空単一複数の質問、引用非実行を対照する。有限モデルと積分境界診断を一般解析や原文同義性の自動証明にしない。',
 '第一文の完全反射面の仮定から後続のK/kでの量と静止系への帰還まで読み合わせた。明示した系・代表モデル・平均の読みの下で、この第二文の四量の対象と質問提示を記述したと判断する。後続の答えの式の記述と導出は別に残す。',
)
@lru_cache(None)
def build_reading():
    inv=json.loads(read(INVENTORY));u=inv['units'][214];s=u['text'][158:]
    assert s=='Wir fragen nach dem auf die spiegelnde Fläche ausgeübten Lichtdruck und nach der Richtung, Frequenz und Intensität des Lichtes nach der Reflexion.'
    assert len(u['text'])==304 and len(re.sub(r'\s','',s))==125 and digest(u['text'].encode())==u['text_sha256']
    image=json.loads(read(SOURCE))['images'][1];assert image['printed_page']==914 and digest((ROOT/image['path']).read_bytes())==image['sha256']
    catalog=load_catalog(ROOT,BASIS);segment=dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[158,304],source=s,reviewed_prose_characters=125,math=[],statements=[INDEX],definitions=list(MEANINGS),status='explicit_interpretive_annotation')
    paths=[INVENTORY,SOURCE,DOC,PRIOR,image['path'],'scripts/read_reflected_light_inquiry.py']
    return dict(schema_version='noema-sentence-reading-1',status='reflected_light_four_quantity_question_checked_under_explicit_reading',reviewer='assistant_close_reading',document=FULL,meaning_basis=BASIS,unit=u['id'],range=[158,304],source=s,source_text_sha256=u['text_sha256'],source_nonblank_characters=125,reviewed_prose_characters=125,reviewed_math_elements=0,math=[],segments=[segment],selection=selection_binding(catalog,[INDEX]),requirements=[dict(id=k,judgment='preserved_under_stated_reading',reason=v) for k,v in zip(REQUIREMENTS,REASONS)],definitions=list(MEANINGS),interpretation_limits=LIMITS,whole_paragraph_complete=False,verified_full_units=0,semantic_equivalence_automatically_proved=False,remaining_in_paragraph=['二文を合わせたu0215全単位判断は別記録で行う'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in paths})
