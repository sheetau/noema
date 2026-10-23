"""Record the second kinematics-paragraph sentence with its anaphora and cause."""
import json
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,selection_binding
from scripts.compose_kinematic_difficulties import ROOT,read,FULL,BASIS,INDEX,LIMITS
INVENTORY='artifacts/written-units-v1/einstein-1905.json';DOC='docs/kinematic-difficulties-v1.md'

def build_reading():
    unit=json.loads(read(INVENTORY))['units'][4];source=unit['text'][261:423]
    assert source.startswith('Die nicht genügende Berücksichtigung') and source.endswith('zu kämpfen hat.')
    rows=[
        ('固定原文','同じ第三段落第二文全体を固定原文と原刊892頁の照合記録へ結ぶ。',['eisds']),
        ('同じ事情','前文の理論の主張が剛体・時計・電磁過程の関係を扱う事情eihaへ照応する。別の前提や事情の偽を主張する文へ替えない。',['eiha','eihf','eihj']),
        ('十分ではない考慮','同じ事情の意味・数量・適用条件を理論の扱いに必要な範囲で反映しないという読み。見落としも部分的考慮も許し、無知・言及回数・未知入力へ替えない。',['eisdm','eisdn','eihf']),
        ('動く物体の電気力学','同じ研究分野を既存の電荷輸送・電気側と磁気側の作用及び物体運動の主題eie6へ結ぶ。電気力学一般や特定の人へ主語を交換しない。',['eie6','eihh']),
        ('当時の困難と取組','論説が指す複数の困難全体を、同じ研究分野が論説当時に直面し解消を課題とする支障として記述する。既に解決した問題、現在の読者の時点、文字通りの戦争にはしない。',['eisdo','eisdp','eisdr','eihg','eihh']),
        ('困難の根','同じ考慮不足の実践を、全対象困難の基礎的な原因へ結ぶ。単なる共存や軽微な寄与に弱めず、唯一原因・必要十分性・必ず解決する方法へ強めない。',['eisdq','eihi']),
        ('一文全体の接続','同じ事情・実践・分野・論説時点・困難群を存在量化と全称量化で保持し、全内容を同じ著者・論説の主張へ帰属する。第一文からの本文順序を保つ。',['eihj','eihk','eihl']),
    ]
    paths=[INVENTORY,DOC,'data/einstein-kinematics-source-reading-v1.json','data/kinematic-foundation-reading-v1.json','reports/kinematic-foundation-v1.json','scripts/review_kinematic_difficulties.py']
    return dict(schema_version='noema-sentence-reading-1',status='sentence_content_and_presentation_checked_under_explicit_reading',reviewer='assistant_close_reading',document=FULL,meaning_basis=BASIS,unit=unit['id'],range=[261,423],source=source,source_text_sha256=unit['text_sha256'],source_nonblank_characters=sum(not c.isspace() for c in source),selection=selection_binding(load_catalog(ROOT,BASIS),[INDEX]),requirements=[dict(requirement=r,judgment='preserved_under_stated_reading',reason=reason,definitions=defs) for r,reason,defs in rows],interpretation_limits=LIMITS,whole_paragraph_complete=False,verified_full_units=0,semantic_equivalence_automatically_proved=False,remaining_in_paragraph=['二文全体の通読判断'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in paths})
