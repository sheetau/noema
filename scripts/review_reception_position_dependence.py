"""Record the explicit position-dependence and empirical-knowledge reading."""
import json
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,selection_binding
from scripts.compose_reception_position_dependence import ROOT,read,FULL,BASIS,INDEX,LIMITS

INVENTORY='artifacts/written-units-v1/einstein-1905.json';DOC='docs/reception-position-dependence-v1.md'

def build_reading():
    u=json.loads(read(INVENTORY))['units'][11];source=u['text'][310:488]
    assert source.startswith('Eine solche Zuordnung') and source.endswith('wissen.')
    rows=[
        ('固定原文','原刊893頁へ照合した第二文全151非空白文字を扱い、第三文と全段落の判断を未完として分ける。',['eishp']),
        ('同じ割当への照応','前文の同じ方式・課題を、同じ原出来事に適用する配置へ結ぶ。各配置が前文の真空伝播・受信・表示・対応規則eikdを満たすことを確認し、別方式の値へ交換しない。',['eishh','eishi','eishj','eikk','eikd']),
        ('観測者の位置','Standpunktを空間的位置として読み、時計を伴う観測者の原点の物理的な場所を比較する。同じ0の座標ラベルや心理的意見と取り違えない。',['eishk','eikl']),
        ('比較条件','元の出来事と準備、時計の校正・進み方・基準、時間尺度を保持した二配置を比較する。時計の初期ずれや別出来事による値の差を位置依存の根拠へ替えない。',['eishk','eikk','eikl']),
        ('独立でない','異なる場所で同じ出来事への割当値が実数値として異なる比較可能な二配置が存在する。全ての位置変更で差が出ることや、未測定・未知であることへ替えない。',['sca','eikl','eikm','eikn']),
        ('伴う不都合','同じ非独立性をその方式が伴い、時間的評価の課題にとって不都合であることを結ぶ。方式の全面否定・計器故障・単なる感情にしない。',['eishl','eishm','eikp']),
        ('経験から知る','同じ非独立性を著者が経験に基づいて知るという認識を保持し、内容自体も主張する。処理系による実験済み、特定の実験名、全人類の承認を追加しない。',['eishn','eiko','eikp']),
        ('対比と挿入と帰属','採用可能性とのaberの対比、wie以下の同じ主張に対する経験的知識の挿入、著者・論説への帰属、前文からの順序を保持する。',['eikq','eikr','zbc','eisho','ue']),
    ]
    paths=[INVENTORY,DOC,'data/einstein-reception-time-source-reading-v1.json','scripts/review_reception_position_dependence.py']
    return dict(schema_version='noema-sentence-reading-1',status='sentence_content_and_presentation_checked_under_explicit_reading',reviewer='assistant_close_reading',document=FULL,meaning_basis=BASIS,unit=u['id'],range=[310,488],source=source,source_text_sha256=u['text_sha256'],source_nonblank_characters=sum(not c.isspace() for c in source),selection=selection_binding(load_catalog(ROOT,BASIS),[INDEX]),requirements=[dict(requirement=r,judgment='preserved_under_stated_reading',reason=reason,definitions=defs) for r,reason,defs in rows],interpretation_limits=LIMITS,whole_paragraph_complete=False,verified_full_units=0,semantic_equivalence_automatically_proved=False,remaining_in_paragraph=['第三文71文字のより実用的な取り決めへの導入','三文全体の通読判断'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in paths})
