"""Record the train/clock quotation while keeping the author's note pending."""
import json
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,selection_binding
from scripts.compose_train_clock_example import ROOT,read,FULL,BASIS,INDEX,LIMITS

INVENTORY='artifacts/written-units-v1/einstein-1905.json';DOC='docs/train-clock-example-v1.md'

def build_reading():
    unit=json.loads(read(INVENTORY))['units'][9];source=unit['text'][482:666]
    assert source.startswith('Wenn ich z. B. sage:') and source.endswith('Ereignisse.“')
    rows=[
        ('固定原文と注','原刊893頁の第四文全151非空白文字と、文末の著者脚注1)が固定u0279を指す対応を保持する。注本文は別単位として未完を明示する。',['eisfm','eisfn','eisfo']),
        ('同じ指示対象','その列車・ここ・私の時計を同じ例の話者・列車・場所・時計へ結び、二つの引用で同じ到着を使う。現実の列車や著者の旅行を補わない。',['eise4','eise5','eise6','eisff','eisfg','eisfi','eisfk']),
        ('七時の到着','列車が同じ場所へ達する到着と、その出来事における同じ時計の7時の読みを結ぶ。存在・目撃だけで到着とせず、停止や乗降も追加しない。',['eisfb','ce','eii4','eii6']),
        ('短針と時の表示','同じ時計の小さい針を時針として指定し、十二時表示の目盛7、同じ表示出来事、同じ時計の読みを結ぶ。長針・別時計・七単位の経過時間・特定の午前午後へ替えない。',['eise7','eisfa','eisfc','eisdf','eii3']),
        ('同時的な二出来事','同じ到着と短針の表示を区別した出来事として同じ場所へ結び、既存eihmにより同じ系・時間尺度の有効で一意な付与時刻の一致を要求する。別時点の読みや未付与値で一致を認めない。',['eii5','eii7','eihm']),
        ('仮定した発言の約言','Wenn ich sageを発言の前件、etwaをおおよその説明関係として分け、同じ第一引用から第二引用への向きを保つ。両内容の真理、実際の発言歴、厳密な論理的同値を補わない。',['eisfd','eisfe','eija']),
        ('例示と帰属','同じ著者・論説へ条件付き説明を主張として帰属し、第三文の時間判断の論点を考える具体例として結ぶ。例を物理的証明へ替えず、本文順序と脚注参照を保持する。',['eir5','eijb','eijc']),
        ('理想化と検査範囲','局所の同じ場所への割当を理想化として明示し、脚注が指摘する不精密さを解決済みとはしない。全実数の一意性は有限標本で代用せず、引数・数値の一致・引用・約言の接続を検査する。',['eihm','eii4','eii5','eija']),
    ]
    paths=[INVENTORY,DOC,'data/einstein-time-continuation-source-reading-v1.json','scripts/review_train_clock_example.py']
    return dict(schema_version='noema-sentence-reading-1',status='sentence_content_and_presentation_checked_under_explicit_reading',reviewer='assistant_close_reading',document=FULL,meaning_basis=BASIS,unit=unit['id'],range=[482,666],source=source,source_text_sha256=unit['text_sha256'],source_nonblank_characters=sum(not c.isspace() for c in source),selection=selection_binding(load_catalog(ROOT,BASIS),[INDEX]),requirements=[dict(requirement=r,judgment='preserved_under_stated_reading',reason=reason,definitions=defs) for r,reason,defs in rows],interpretation_limits=LIMITS,whole_paragraph_complete=False,verified_full_units=0,semantic_equivalence_automatically_proved=False,remaining_in_paragraph=['脚注u0279の内容の記述','段落全体の通読判断'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in paths})
