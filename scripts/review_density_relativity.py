"""Read the complete first density sentence without certifying its whole unit."""
from functools import lru_cache
import json
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,selection_binding,validate_hashes,REQUIREMENTS
from scripts.compose_density_relativity import ROOT,read,FULL,BASIS,INDEX,LIMITS

INVENTORY='artifacts/written-units-v1/einstein-1905.json';DOC='docs/density-relativity-v1.md'
SOURCE='data/einstein-radiative-density-reading-v1.json'
READING='data/einstein-density-relativity-sentence-reading-v1.json'
REASONS=(
 'u0203[0,163)を原刊913頁及び固定転記と照合した。M0349はA²/(8pi)、M0350はA′²/(8pi)。Daからbetrachtenまでを第一文として通読し、後続の同体積の文を今回の範囲へ加算しない。',
 '旧系の単位体積当たりエネルギーの説明ekli、同じ相対性原理eifjとの前提連言eklk、そこから新系の説明ekljが従わなければならないというzc、同じ新系解釈の主張を分けて保持する。',
 '同じ源・波・過程・観測者・二系・単位・位相・周期・旧新振幅を64役割で共有する。固定K,V,先行波の範囲及び状況以外の60役割を旧新で同じ順に量化する。第八節eistkの考察と、引き継ぐ第七節eisrxの波の仮定を区別する。A,A′は既存ekiaの同じ非負振幅である。',
 'Da ... so ... nach ... haben wir ... zu betrachtenを、旧系の説明を前提とする論述上の根拠と必須の帰結の提示として読む。引用内容を評価して真理を要求せず、命令の実行、測定完了、独立した導出検証又は新しい相対性原理の提案へ置き換えない。',
 '新系でも省略されたpro Volumeneinheitを引き継ぎ、各系の周期平均密度と読む。現実の瞬間総エネルギー、同じ体積の条件、正面接近、非零振幅又は後続の球面を第一文へ追加しない。密度モデルを前件から分離し、結論を仮定した条件にしない。',
 '密度の物理的なモデル対応と仕事校正、同じ正弦の周期積分、元と変換後の位相・領域を既存定義から構成する。Relativitätsprinzipは既存eiscgと内容eifjへの別表記参照であり、綴りだけで原理を代用しない。新しい一般原始関係は追加しない。',
 '旧新のモデルと周期平均、同じ60量化役割、原理と旧系説明を合わせた根拠、引用の向き、著者と文書と前後順序を対照する。旧385主張及び判断を保持し、全実数・全関数の量化を有限例へ置換しない。下位の積分と密度・流の検査は固定済みの証拠を引き継ぐ。',
 '第一文を前後の波と密度・体積の文脈とともに再読した。明示した周期平均密度の読みの下で、旧系の説明、同じ原理による新系適用、参照及び提示の役割を欠落なく記述したと判断する。u0203全体と続く球面を挟む一文の確認は残る。',
)

@lru_cache(None)
def build_reading():
    unit=json.loads(read(INVENTORY))['units'][202];source=unit['text'][:163]
    assert source=='Da [M0349] gleich der Lichtenergie pro Volumeneinheit ist, so haben wir nach dem Relativitätsprinzip [M0350] als die Lichtenergie im bewegten System zu betrachten.'
    validate_hashes(ROOT,json.loads(read(SOURCE))['source_sha256'])
    catalog=load_catalog(ROOT,BASIS);symbols=['ekle','eklf','eklg','eklh','ekli','eklj','eklk','ekll','eklm','ekln','eklo','eifj','eiscg','ekia','ekkz','ekk4','zc','uh']
    assert all(n in catalog.entries for n in symbols) and len(REASONS)==len(REQUIREMENTS)
    paths=[INVENTORY,DOC,SOURCE,'reports/radiative-density-v1.json','reports/two-postulates-v1.json','scripts/review_density_relativity.py']
    return dict(schema_version='noema-sentence-reading-1',status='sentence_content_and_presentation_checked_under_explicit_reading',reviewer='assistant_close_reading',document=FULL,meaning_basis=BASIS,unit=unit['id'],range=[0,163],source=source,source_text_sha256=unit['text_sha256'],source_nonblank_characters=sum(not c.isspace() for c in source),reviewed_prose_characters=127,reviewed_math_elements=2,selection=selection_binding(catalog,[INDEX]),requirements=[dict(id=k,judgment='preserved_under_stated_reading',reason=v) for k,v in zip(REQUIREMENTS,REASONS)],definitions=symbols,interpretation_limits=LIMITS,whole_paragraph_complete=False,verified_full_units=0,semantic_equivalence_automatically_proved=False,remaining_in_paragraph=['同体積ならという反実仮想','実際の体積不一致','u0204を挟む動く球面とエネルギーの流出入・同じ光の集合','新系の総エネルギーの問いとd.h.'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in paths})
