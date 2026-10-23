"""Record the fourth sentence with its scoped negations and prospective result."""
import json
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,selection_binding
from scripts.compose_ether_dispensability import ROOT,read,FULL,BASIS,INDEX,LIMITS
INVENTORY='artifacts/written-units-v1/einstein-1905.json';DOC='docs/ether-dispensability-v1.md'

def build_reading():
    unit=json.loads(read(INVENTORY))['units'][3];source=unit['text'][1082:1425]
    assert source.startswith('Die Einführung eines „Lichtäthers“') and source.endswith('zugeordnet wird.')
    rows=[
        ('固定原文','第四文全体を固定転記と原刊892頁の照合記録へ結ぶ。',['eisdc']),
        ('光エーテルの導入','同じ光伝達媒体eisbyを指すと読み、理論の構成要素として導入することを語への言及や実在と分ける。',['eisby','eiscw']),
        ('不要性','同じ物理的対象・量・説明を保つ記述の仕方があり、そこでは光媒体を導入しないという内容。実在否定や説明範囲の削除へ替えない。',['eisc7','eigr']),
        ('将来明らかになるという予告','今後の論説展開で同じ不要性が明らかになると予告し、現在の導出・実証完了へ替えない。',['eisdb','eigs']),
        ('開発予定の見解','先行する同じ理論構成eigjをこの論説でこれから展開する見解へ結び、全条件で同じ見解を保つ。',['eiscv','eigt']),
        ('絶対静止空間と特殊な性質','空間自体の特権的な絶対静止と特殊な物理属性を結んだ導入を否定し、普通の幾何学的空間や相対静止は排除しない。',['eisbk','eiscx','eiscy','eigo']),
        ('真空空間と電磁過程','関係節を真空空間へ結ぶ読みを採用し、既存の電荷・電磁作用の語彙による過程が生じる空間の全点を扱う。',['eiscz','eisc2','eisc3','eign']),
        ('速度ベクトルの不付与','三実成分・基底・単位を持つ零を含む速度量を同じ空間点へ付与する組の不存在を表す。物体や光の速度・座標指定を否定しない。',['eisc4','eisc5','sch2','eigm','eisc6','eigp']),
        ('二否定による限定付き理由','weder/nochの両否定を保持し、その点・範囲を理由とする同じ不要性の予告へ結ぶ。無限定な一般化や同値条件にしない。',['eigq','eisda','eigs']),
        ('一文全体の帰属','一文の内容を主張として同じ著者・論説へ帰属し、第三文に続く別箇所の順序を保持する。',['eigt','eigu','eigv']),
    ]
    paths=[INVENTORY,DOC,'data/einstein-principles-source-reading-v1.json','docs/sufficient-postulates-v1.md','reports/sufficient-postulates-v1.json','scripts/review_ether_dispensability.py']
    return dict(schema_version='noema-sentence-reading-1',status='sentence_content_and_presentation_checked_under_explicit_reading',reviewer='assistant_close_reading',document=FULL,meaning_basis=BASIS,unit=unit['id'],range=[1082,1425],source=source,source_text_sha256=unit['text_sha256'],source_nonblank_characters=sum(not c.isspace() for c in source),selection=selection_binding(load_catalog(ROOT,BASIS),[INDEX]),requirements=[dict(requirement=r,judgment='preserved_under_stated_reading',reason=reason,definitions=defs) for r,reason,defs in rows],interpretation_limits=LIMITS,whole_paragraph_complete=False,verified_full_units=0,semantic_equivalence_automatically_proved=False,remaining_in_paragraph=['四文全体の通読判断'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in paths})
