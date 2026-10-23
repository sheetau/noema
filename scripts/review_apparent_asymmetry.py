"""Record a reading of the general opening claim, not only its example."""
import json
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,selection_binding
from scripts.compose_apparent_asymmetry import ROOT,read,FULL,BASIS,INDEX
INVENTORY='artifacts/written-units-v1/einstein-1905.json';DOC='docs/apparent-asymmetry-v1.md'
def build_reading():
    unit=next(u for u in json.loads(read(INVENTORY))['units'] if u['id']=='einstein-1905:u0003');source=unit['text'][:209]
    assert source.startswith('Daß die Elektrodynamik Maxwells') and source.endswith('ist bekannt.')
    rows=[
      ('固定原文','原刊891頁との照合を保持したu0003[0,209)の冒頭文を用いる。',['eir7']),
      ('Maxwellの理論と通常の理解','歴史的な理論、その解釈、論説記述時点の通常性を区別して同じ対象へ結ぶ。',['eisax','eisay','eisah','eiey']),
      ('動く物体への適用','同じ対象・準備・尺度と運動の全履歴に従う一般比較への理論適用を述べ、後続の磁石・導体だけへ縮めない。',['eisaz','eiag','eiex']),
      ('説明上の非対称性','その適用が認める説明の全範囲で二事例の機構分類が非空で共通分類なしとなる区別を要求する。全適用への断定や実験二件を補わない。',['eidd','eiew','eiex']),
      ('同じ区別が現象には属さないように見える','同じ比較についての否定内容を非空の見かけの全候補で評価する。現実の不存在や未確認と同一視しない。',['eisa2','eisa3','eieu','eiev']),
      ('知られている','留保を含む同じ内容自体と、その周知性の提示を結ぶ。全人類の同意や現代の知識へ替えない。',['eiez','eie2']),
      ('挿入補足と主張','同じ通常理解の限定を挿入補足として保持し、著者・論説への主張の帰属と先行箇所eir7から例示への順序を保つ。',['eisa5','eie3','eie4']),
    ]
    paths=[INVENTORY,DOC,'data/einstein-opening-source-reading-v1.json','data/einstein-opening-obligations-v1.json','scripts/review_apparent_asymmetry.py']
    return dict(schema_version='noema-sentence-reading-1',status='sentence_content_and_presentation_checked_under_explicit_reading',reviewer='assistant_close_reading',document=FULL,meaning_basis=BASIS,unit=unit['id'],range=[0,209],source=source,source_text_sha256=unit['text_sha256'],source_nonblank_characters=sum(not c.isspace() for c in source),selection=selection_binding(load_catalog(ROOT,BASIS),[INDEX]),requirements=[dict(requirement=r,judgment='preserved_under_stated_reading',reason=reason,definitions=defs) for r,reason,defs in rows],interpretation_limits=['一般の理論適用での説明機構の区別として読む','非対称性は存在を述べ、全適用・実験件数を要求しない','非空の候補に基づく見かけを現実の真理と分ける','現在とは論説記述時点、周知性とはその論点の知識共同体での扱い'],whole_paragraph_complete=False,verified_full_units=0,semantic_equivalence_automatically_proved=False,remaining_in_paragraph=['五文全体の通読判断'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in paths})
