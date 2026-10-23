"""Explicit reading of the final reception-alternative paragraph sentence."""
import json
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,selection_binding
from scripts.compose_practical_time_convention import ROOT,read,FULL,BASIS,INDEX,LIMITS

INVENTORY='artifacts/written-units-v1/einstein-1905.json';DOC='docs/practical-time-convention-v1.md'

def build_reading():
    u=json.loads(read(INVENTORY))['units'][11];source=u['text'][489:569]
    assert source=='Zu einer weit praktischeren Festsetzung gelangen wir durch folgende Betrachtung.'
    rows=[
        ('固定原文','原刊893頁へ照合した第三文の全71非空白文字を保持する。',['eishs']),
        ('規定の参照先','時間的評価の同じ課題について、後続の同期時計の時刻付与規則quと定義箇所rjへ新規定を結ぶ。',['eishq','eishx','eiku']),
        ('比較先と基準','前二文の同じ受信方式eisg7と比べ、複数地点の出来事を共通規約で扱う実用性を同じ基準へ固定する。',['eisht','eishu','eikt']),
        ('比較級と程度','両方式の程度を同じ尺度へ結び、厳密な優越と顕著な差をそれぞれ要求する。最適性や数値閾値へ替えない。',['eiks','eishv','eishw']),
        ('考察による到達','著者が同じ考察を通じて同じ規定へ至るという手段関係を保持する。単なる順序や仮の可能性にしない。',['eishy','eikv']),
        ('以下という指示','u0013の二地点の時計からu0018の時刻定義へ進む考察を固定し、導入文・始点・終点の文書順序を保持する。',['eishr','eish2','eishz','ue']),
        ('著者と発話の役割','wirを論述上の著者の声として、第三文の主張を同じ論説へ帰属する。前二文からの順序も保持する。',['eikw','eikx','eir3']),
        ('余分な完了の排除','規則の引用を全評価せず、後続の考察全体や物理的な同期の実証をこの一文で完成扱いしない。',['eiku','eikx']),
    ]
    paths=[INVENTORY,DOC,'data/einstein-reception-time-source-reading-v1.json','scripts/review_practical_time_convention.py']
    return dict(schema_version='noema-sentence-reading-1',status='sentence_content_and_presentation_checked_under_explicit_reading',reviewer='assistant_close_reading',document=FULL,meaning_basis=BASIS,unit=u['id'],range=[489,569],source=source,source_text_sha256=u['text_sha256'],source_nonblank_characters=71,selection=selection_binding(load_catalog(ROOT,BASIS),[INDEX]),requirements=[dict(requirement=r,judgment='preserved_under_stated_reading',reason=reason,definitions=defs) for r,reason,defs in rows],interpretation_limits=LIMITS,whole_paragraph_complete=False,verified_full_units=0,semantic_equivalence_automatically_proved=False,remaining_in_paragraph=['三文全体の通読判断'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in paths})
