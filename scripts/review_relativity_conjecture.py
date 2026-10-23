"""Record a whole-sentence reading with a nonfactive conjecture target."""
import json
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,selection_binding
from scripts.compose_relativity_conjecture import ROOT,read,FULL,BASIS,INDEX,LIMITS
INVENTORY='artifacts/written-units-v1/einstein-1905.json';DOC='docs/relativity-conjecture-v1.md'

def build_reading():
    unit=json.loads(read(INVENTORY))['units'][3];source=unit['text'][:522]
    assert source.startswith('Beispiele ähnlicher Art') and source.endswith('bereits erwiesen ist.')
    rows=[
        ('固定原文','原刊891頁から続く段落の第一文全体を固定転記・照合記録と一致させる。',['eisb4']),
        ('類似例','複数の例全てを先行設定と同じ一般比較の論点へ結び、具体的な物体や実験実施を補わない。',['eifk','eifm','eisbs','eisbt']),
        ('地球と光媒体に対する運動','同じ地球と仮定する光媒体の静止系、全物質点・全区間の運動を検出目標の内容へ結ぶ。',['eisbx','eisby','eisbz','eiag','eifl']),
        ('試行と失敗','過去の該当する複数試行全てで同じ検出目標を共有し、成否の否定を目標自体の否定にしない。',['eisbu','eisbv','eisbw','eifn']),
        ('根拠から推測への導き','両根拠の成立、同じ内容を考える理由、推測という位置付けを保持し、決定的な証明や事実への昇格を追加しない。',['eifo','eisbq','eisbr','eifr']),
        ('推測の二内容','絶対静止への対応特性の力学・電気力学での不存在と、全力学適格系での共通電気力学・光学法則を同じ評価点へ結ぶ。',['eifb','eifc','eifd','eife','eiff','eifg','eifh','eifi','eifj']),
        ('一次の量と既証','同じ共通法則の量的内容を速度比の展開の一次までに制限し、その成立と既に確立していることの帰属を保持する。',['eisbn','eisbo','eisbp','eifp','eifq']),
        ('追加・対照・補足・主張','第一の否定を保持した範囲拡張、否定的特徴付けから積極的定式化、既証の限定への補足、同じ著者・論説・先行箇所への接続を保持する。',['eisb2','eisb3','eisa5','eifs','eift','eifu','eifv']),
    ]
    paths=[INVENTORY,DOC,'data/einstein-principles-source-reading-v1.json','docs/conjecture-laws-v1.md','reports/conjecture-laws-v1.json','scripts/review_relativity_conjecture.py']
    return dict(schema_version='noema-sentence-reading-1',status='sentence_content_and_presentation_checked_under_explicit_reading',reviewer='assistant_close_reading',document=FULL,meaning_basis=BASIS,unit=unit['id'],range=[0,522],source=source,source_text_sha256=unit['text_sha256'],source_nonblank_characters=sum(not c.isspace() for c in source),selection=selection_binding(load_catalog(ROOT,BASIS),[INDEX]),requirements=[dict(requirement=r,judgment='preserved_under_stated_reading',reason=reason,definitions=defs) for r,reason,defs in rows],interpretation_limits=LIMITS,whole_paragraph_complete=False,verified_full_units=0,semantic_equivalence_automatically_proved=False,remaining_in_paragraph=['第二文の推測の前提化・命名・見かけ上の不整合・光速度の仮定','第三文の二前提の十分性','第四文の光エーテル不要','四文全体の通読判断'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in paths})
