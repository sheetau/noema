"""Record the explicit first-sentence reading of the reception-time alternative."""
import json
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,selection_binding
from scripts.compose_reception_time_alternative import ROOT,read,FULL,BASIS,INDEX,LIMITS

INVENTORY='artifacts/written-units-v1/einstein-1905.json';DOC='docs/reception-time-alternative-v1.md'

def build_reading():
    u=json.loads(read(INVENTORY))['units'][11];source=u['text'][:309]
    assert source.startswith('Wir könnten uns allerdings') and source.endswith('zuordnet.')
    rows=[
        ('固定原文','原刊893頁と照合した第一文全269非空白文字を対象とする。後二文と全段落の判断は未完として分ける。',['eishg']),
        ('同じ原点の観測者と時計','時計とともに原点に位置する観測者を導入し、同じ系・原点割当・時計校正・指針表示・尺度を結ぶ。著者本人、法的所有、短針だけ、全体静止へ限定しない。',['eika','eisgr','eisgs','zbv','cb']),
        ('出来事を知らせる光','評価対象出来事に結び付いた同じ光信号と出発を固定し、真空を通って同じ観測者に到達する受信を結ぶ。無関係の信号や原出来事を受信そのものへ取り替えない。',['eisge','eisgu','eisgv','eisb5','eisca','eikb']),
        ('対応する針位置','受信に局所的に一致する同じ時計の表示・読みを、その信号と元の出来事への時間的評価として対応付ける。光伝播時間の補正や、元の出来事の時刻と受信の等値を要求しない。',['eisgt','eisgm','eisg2','ce','eikc']),
        ('各該当信号の全範囲','対応記録の五欄と候補値を同じ記録・時計・尺度へ結び、全該当到達に同じ規則を要求する。成功記録だけの抜粋、役割の交換、未知値の既定値補完を認めない。',['eisgw','eisgx','eisgy','eisgz','eikd','eike']),
        ('ひとまず済ませる可能性','同じ方式が成立する採用候補で、その方式だけで済ませる著者の態度を要求する。現実の実施済み、喜び、最善性、後の欠点の不存在へ替えない。',['eisg4','eisg5','eikf','eikg','eikh']),
        ('譲歩と帰属','先行する局所定義の限界を踏まえた代案としてallerdingsを保持し、可能性のまま同じ著者・論説へ帰属する。先行限界の撤回や内容の現実での実行にしない。',['eisg6','eiki','eikj','eir3','ue']),
        ('検査範囲','元の出来事が3、受信と表示が9の対照設定でも対応を許す。全実数の妥当性は有限標本へ替えず、物理的証拠・到達・採用候補の規約を明示した入力とする。',['eikb','eikc','eikh']),
    ]
    paths=[INVENTORY,DOC,'data/einstein-reception-time-source-reading-v1.json','scripts/review_reception_time_alternative.py']
    return dict(schema_version='noema-sentence-reading-1',status='sentence_content_and_presentation_checked_under_explicit_reading',reviewer='assistant_close_reading',document=FULL,meaning_basis=BASIS,unit=u['id'],range=[0,309],source=source,source_text_sha256=u['text_sha256'],source_nonblank_characters=sum(not c.isspace() for c in source),selection=selection_binding(load_catalog(ROOT,BASIS),[INDEX]),requirements=[dict(requirement=r,judgment='preserved_under_stated_reading',reason=reason,definitions=defs) for r,reason,defs in rows],interpretation_limits=LIMITS,whole_paragraph_complete=False,verified_full_units=0,semantic_equivalence_automatically_proved=False,remaining_in_paragraph=['第二文の観測者位置への依存と経験からの知識','第三文のより実用的な取り決めへの導入','三文全体の通読判断'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in paths})
