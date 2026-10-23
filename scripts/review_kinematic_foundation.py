"""Record the first kinematics-paragraph sentence under explicit scope readings."""
import json
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,selection_binding
from scripts.compose_kinematic_foundation import ROOT,read,FULL,BASIS,INDEX,LIMITS
INVENTORY='artifacts/written-units-v1/einstein-1905.json';DOC='docs/kinematic-foundation-v1.md'

def build_reading():
    unit=json.loads(read(INVENTORY))['units'][4];source=unit['text'][0:260]
    assert source.startswith('Die zu entwickelnde Theorie') and source.endswith('Prozessen betreffen.')
    rows=[
        ('固定原文','第三段落第一文を原刊892頁の照合記録と同じ全範囲に結ぶ。',['eisdl']),
        ('これから展開する理論','同じ論説の先行構成課題eigjの到達先を指す。既成の別理論や導出済みという事実へ替えない。',['eisdj','eig7','eigj']),
        ('剛体の運動学を基礎とする','全物質点対の剛性を持つ物体の位置・時刻・配置変化を扱う研究と、同じ理論がこれを量・適用条件の基礎に用いる関係を結ぶ。力の原因の理論や既成の時間規約の全採用にしない。',['eigy','eisdh','eisdi','eig6']),
        ('他のあらゆる電気力学との比較','現在の理論以外の全電気力学にも同じ基礎依存を課す。既知の例や動く物体だけの理論へ狭めない。',['eig4','eihb']),
        ('各理論の全主張','電気力学の文脈での各理論の全主張・論理的帰結に同じ指示規約を要求する。論理・数学を含む全学問という読みは採らず、その範囲を明示する。',['eiscr','eig5','eiha']),
        ('剛体と座標系の括弧説明','剛体を位置指定の物理的な基準物体として用いる役割へ結ぶ。抽象座標系そのものとの同一視や三非共線標識点の必要性は加えない。',['eisde','eigz']),
        ('時計と電磁過程','時間経過の指示と校正、同じ電荷・電磁作用による過程を分類する。遠隔同期、実測、光だけへの限定を追加しない。',['ca','eisdf','eig2','eisc3','eig3']),
        ('三者の間の関係を扱う','各主張の物理的な指示・量・適用条件が三種の対象を備える設定の関係によって解釈されると読む。各式の字面や三者の実在断言という読みに替えない。',['eisdg','eig5']),
        ('daの説明理由','全理論の主張の指示内容を理由として運動学への基礎依存を述べる。同じ判断点で両内容を成立させ、向きのある説明関係を別に保持する。',['eiha','eihb','eisdk','eihc']),
        ('一文全体の帰属と順序','比較と理由を含む全体を主張として同じ著者・論説へ帰属し、前段落の最終文からの本文順序を保持する。',['eihd','eihe']),
    ]
    paths=[INVENTORY,DOC,'data/einstein-kinematics-source-reading-v1.json','docs/rigid-body-kinematics-v1.md','reports/rigid-body-kinematics-v1.json','scripts/review_kinematic_foundation.py']
    return dict(schema_version='noema-sentence-reading-1',status='sentence_content_and_presentation_checked_under_explicit_reading',reviewer='assistant_close_reading',document=FULL,meaning_basis=BASIS,unit=unit['id'],range=[0,260],source=source,source_text_sha256=unit['text_sha256'],source_nonblank_characters=sum(not c.isspace() for c in source),selection=selection_binding(load_catalog(ROOT,BASIS),[INDEX]),requirements=[dict(requirement=r,judgment='preserved_under_stated_reading',reason=reason,definitions=defs) for r,reason,defs in rows],interpretation_limits=LIMITS,whole_paragraph_complete=False,verified_full_units=0,semantic_equivalence_automatically_proved=False,remaining_in_paragraph=['第二文の考慮不足と当時の困難','第三段落全体の通読判断'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in paths})
