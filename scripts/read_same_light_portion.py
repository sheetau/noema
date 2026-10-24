"""Read the sentence spanning the moving-sphere display and persistent enclosure."""
from functools import lru_cache
import json,re
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,selection_binding,validate_hashes,REQUIREMENTS
from scripts.compose_same_light_portion import ROOT,read,FULL,BASIS,INDEX,LIMITS,MEANINGS

INVENTORY='artifacts/written-units-v1/einstein-1905.json';SOURCE='data/einstein-radiative-density-reading-v1.json'
DOC='docs/same-light-portion-v1.md';READING='data/einstein-same-light-portion-tail-sentence-reading-v1.json'
PREVIOUS=['data/einstein-density-unit-scope-sentence-reading-v1.json','data/einstein-equal-volume-supposition-sentence-reading-v1.json','data/einstein-volume-denial-sentence-reading-v1.json']
REASONS=(
 '原刊913頁のu0203[422,597)–u0204–u0205[0,107)を、セミコロンを含む一文として通読した。本文148+94=242非空白文字、M0354の方向余弦とM0355の球面式を照合した。残る問いは分離する。',
 '同じ平面波・球面の全表面全時刻の無流出入eknkと、初期位置との一対一な対応・所属・瞬間密度の持続eknvを物理的な同じ部分へ結ぶ。全体の正味流や総エネルギーだけの一致で代用しない。',
 'K,V,波範囲,部分zvaa,状況を固定し、残る65役割を条件・帰結で共有する。diese Flächeは同じ球面、derselbe Lichtkomplexは同じ初期部分の輸送として読む。新しい対象を成功例として選び直さない。',
 'Sind ... so ...を同じ設定に関する条件内容ekny、wir können daher sagenをekn2の記述可能性への著者帰属uhと根拠提示udへ接続する。eisraで後方参照を保持し、必然や明白性へ強めない。',
 'dauerndを全実時刻として保つため、全領域履歴で採用する理想モデルをeknpへ明示する。有限局所近似からの無条件の外挿、光子の存在論、観測不能な別の微視的交換履歴の排除は追加しない。瞬間密度と位相平均総量も区別する。',
 '同じ初期領域と密度の輸送を既存の関数・実数・領域の合成で定め、一般関係を増やさない。原始記号三件は原文の節と文全体への参照であり、一文の意味を格納する述語ではない。記述可能性・主張・帰結提示・照応は既存関係を再利用する。',
 '逆向きと前進の位置対応、同量だが異なる分布、領域と密度零の節、全四座標と65束縛位置、同じ物理設定、根拠と記述の向き、引用の非実行を検査する。有限診断や原来の有理補題は物理モデルの全域的妥当性又は意味同義性の自動証明ではない。',
 '前の三文から球面式を経て、同じ集合を永久に囲むと述べ得るという箇所まで再読した。初期部分の連続体輸送・全時刻理想モデルという明示した読みの下で、条件・球面・無流出入・同一性・持続・帰結提示・帰属を記述したと判断する。',
)

@lru_cache(None)
def build_reading():
    inv=json.loads(read(INVENTORY));math={m['id']:m for m in inv['math']};segments=[]
    for index,a,b in [(202,422,597),(203,0,7),(204,0,107)]:
        u=inv['units'][index];s=u['text'][a:b];ids=re.findall(r'\[(M\d+)\]',s)
        segments.append(dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[a,b],source=s,reviewed_prose_characters=len(re.sub(r'\s','',re.sub(r'\[M\d+\]','',s))),math=[dict(id=n,sha256=math[n]['sha256']) for n in ids],statements=[INDEX],definitions=list(MEANINGS),status='explicit_interpretive_annotation'))
    assert [s['reviewed_prose_characters'] for s in segments]==[148,0,94]
    assert [m['id'] for s in segments for m in s['math']]==['M0354','M0355']
    assert segments[-1]['source'].endswith('Lichtkomplex umschließt.')
    validate_hashes(ROOT,json.loads(read(SOURCE))['source_sha256']);catalog=load_catalog(ROOT,BASIS)
    paths=[INVENTORY,SOURCE,DOC,'artifacts/written-facsimiles-v1/einstein-p913-0.jpg','reports/moving-ball-transport-v1.json',*PREVIOUS,'scripts/read_same_light_portion.py']
    return dict(schema_version='noema-sentence-reading-1',status='cross_unit_sentence_content_and_presentation_checked_under_explicit_reading',reviewer='assistant_close_reading',document=FULL,meaning_basis=BASIS,unit=segments[-1]['unit'],range=[0,107],source=segments[-1]['source'],source_text_sha256=segments[-1]['unit_sha256'],source_nonblank_characters=94,reviewed_prose_characters=94,reviewed_math_elements=0,cross_unit_segments=segments,cross_unit_reviewed_prose_characters=242,cross_unit_reviewed_math_elements=2,selection=selection_binding(catalog,[INDEX]),requirements=[dict(id=k,judgment='preserved_under_stated_reading',reason=v) for k,v in zip(REQUIREMENTS,REASONS)],definitions=list(MEANINGS),interpretation_limits=LIMITS,whole_paragraph_complete=False,verified_full_units=0,semantic_equivalence_automatically_proved=False,remaining_in_paragraph=['u0205[108,272)の新系エネルギーの問いとd.h.'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in paths})
