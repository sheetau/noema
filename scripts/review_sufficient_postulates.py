"""Record third-sentence sufficiency without claiming completed physical derivation."""
import json
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,selection_binding
from scripts.compose_sufficient_postulates import ROOT,read,FULL,BASIS,INDEX,LIMITS
INVENTORY='artifacts/written-units-v1/einstein-1905.json';DOC='docs/sufficient-postulates-v1.md'

def build_reading():
    unit=json.loads(read(INVENTORY))['units'][3];source=unit['text'][890:1081]
    assert source.startswith('Diese beiden Voraussetzungen genügen') and source.endswith('für ruhende Körper.')
    rows=[
        ('固定原文','同じ第二段落の第三文全体を固定原文と原刊892頁の照合記録へ結ぶ。',['eiscu']),
        ('同じ二前提','Diese beiden Voraussetzungenを前文で採用しようとした同じeifj/eifyへ結び、二内容をともに供給する。',['eifj','eify','eigh','eiscp','eiscq']),
        ('十分性と到達','同じ基礎と二前提によって同じ到達先へ至る許容方法の存在として読む。第三の独立物理前提、必要性・最小性、実行や実証の完了を補わない。',['eisco','eigi','eigj']),
        ('動く物体の電気力学','到達先の理論を、既存の電荷輸送・電気側と磁気側の作用・物体運動で記述する同じ主題へ結ぶ。',['eiscm','eige','eie5','eie6']),
        ('単純さ','同じ説明範囲を保持して少数の共通原理・概念・場合分けで扱うという文脈的評価を同じ到達先へ課す。数値閾値や特定の比較相手は補わない。',['eisct','eigi']),
        ('無矛盾','同じ到達先の全論理的帰結に、同じ意味・条件で否定し合う内容がないことを要求する。未調査を不存在としない。',['eiscr','eiscs','eigg']),
        ('静止物体のMaxwell理論を基礎とする','同じ構成方法の基礎をMaxwell理論の静止物体の場合へ結ぶ。巨視的な全物質点の系に対する静止として読み、静的電磁場だけ又は絶対静止へ替えない。',['eisax','eiah','eiscn','eigf']),
        ('全体の帰属と順序','全要件を同じ方法・基礎・到達先・判断点の存在量化で束ね、その十分性の主張を同じ著者と論説へ帰属し、第二文からの順序を保持する。',['eigi','eigj','eigk','eigl']),
    ]
    paths=[INVENTORY,DOC,'data/einstein-principles-source-reading-v1.json','docs/two-postulates-v1.md','reports/two-postulates-v1.json','scripts/review_sufficient_postulates.py']
    return dict(schema_version='noema-sentence-reading-1',status='sentence_content_and_presentation_checked_under_explicit_reading',reviewer='assistant_close_reading',document=FULL,meaning_basis=BASIS,unit=unit['id'],range=[890,1081],source=source,source_text_sha256=unit['text_sha256'],source_nonblank_characters=sum(not c.isspace() for c in source),selection=selection_binding(load_catalog(ROOT,BASIS),[INDEX]),requirements=[dict(requirement=r,judgment='preserved_under_stated_reading',reason=reason,definitions=defs) for r,reason,defs in rows],interpretation_limits=LIMITS,whole_paragraph_complete=False,verified_full_units=0,semantic_equivalence_automatically_proved=False,remaining_in_paragraph=['第四文の光エーテル不要','四文全体の通読判断'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in paths})
