"""Record the general temporal-judgment sentence under an explicit aboutness reading."""
import json
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,selection_binding
from scripts.compose_temporal_judgments import ROOT,read,FULL,BASIS,INDEX,LIMITS

INVENTORY='artifacts/written-units-v1/einstein-1905.json';DOC='docs/temporal-judgments-v1.md'

def build_reading():
    unit=json.loads(read(INVENTORY))['units'][9];source=unit['text'][338:481]
    assert source.startswith('Wir haben zu berücksichtigen') and source.endswith('Ereignisse sind.')
    rows=[
        ('固定原文','原刊893頁上端に対応する第三文全123非空白文字を覆う。gleich-zeitigeの行末分割を転記のgleichzeitigeへ対応させる。',['eise3']),
        ('われわれの判断一般','著者がこの物理的時間の論点で指す人間の判断の全範囲を取り、著者の実際の発言だけや有限の測定成功例へ狭めない。',['eisev']),
        ('時間の関与','時刻付与・先後・持続などが内容上の役割を持つ判断を取る。Zeitという綴りの有無や判断の真偽によって選ばない。',['eisew']),
        ('全て・いつも','全範囲の中の時間に関わる全判断へ同じ説明条件を課す。説明できる例だけを後から選ばず、例外を認めない全称として保持する。',['eiix']),
        ('同時的出来事についての判断','同じ判断の時間的内容を、同時性の関係を適用する非空の全項目によって解釈する。元の対象・否定・量化・条件を保持し、実際の全出来事の同時性や一つの肯定文への置換を主張しない。',['eisex','eisey','eisez','eiiu','eiiv','eiiw']),
        ('同時性の意味','既存eihmの同じ系・単位・文脈の有効で一意な時刻付与と値の一致を再利用する。引用による関係の同定から具体的な時計同期・時刻付与を実行せず、未付与を非同時としない。',['eihm','eiiu']),
        ('考慮しなければならない','一般的な性質を内容として保持し、その同じ内容を議論に反映すべき方法上の要請を結ぶ。単なる意図、実際の考慮完了、読者の心理的注意や法的義務へ替えない。',['eise2','eiiy']),
        ('著者への帰属と順序','同じ著者・論説へ全内容を主張として帰属し、時間の意味の先行理解を説く前文からの本文順序を保持する。',['eiiz','eii2']),
        ('検査と限界','関係の引用、引数接続、説明の全項目、全判断の範囲、性質と要請の両条件を対照例で点検する。意味保持の入力を自動的な同義証明へ昇格させない。',['eiiu','eiiv','eiiw','eiix','eiiy']),
    ]
    paths=[INVENTORY,DOC,'data/einstein-time-continuation-source-reading-v1.json','scripts/review_temporal_judgments.py']
    return dict(schema_version='noema-sentence-reading-1',status='sentence_content_and_presentation_checked_under_explicit_reading',reviewer='assistant_close_reading',document=FULL,meaning_basis=BASIS,unit=unit['id'],range=[338,481],source=source,source_text_sha256=unit['text_sha256'],source_nonblank_characters=sum(not c.isspace() for c in source),selection=selection_binding(load_catalog(ROOT,BASIS),[INDEX]),requirements=[dict(requirement=r,judgment='preserved_under_stated_reading',reason=reason,definitions=defs) for r,reason,defs in rows],interpretation_limits=LIMITS,whole_paragraph_complete=False,verified_full_units=0,semantic_equivalence_automatically_proved=False,remaining_in_paragraph=['第四文の列車到着と時計の短針の引用例','脚注u0279の留保と本文からの参照','段落全体の通読判断'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in paths})
