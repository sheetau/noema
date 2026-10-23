"""Record the explicit reading of the second case and the scoped comparison."""
import json
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,selection_binding
from scripts.compose_moving_conductor_case import ROOT,read,FULL,BASIS,INDEX

INVENTORY='artifacts/written-units-v1/einstein-1905.json';DOC='docs/moving-conductor-case-v1.md'
def build_reading():
    units=json.loads(read(INVENTORY))['units'];unit=next(u for u in units if u['id']=='einstein-1905:u0003');source=unit['text'][771:1203]
    assert source.startswith('Ruht aber der Magnet') and source.endswith('die elektrischen Kräfte.')
    requirements=[
        ('固定原文','原刊891頁との照合記録を保ち、u0003[771,1203)の一文を用いる。',['eisav']),
        ('逆の運動役割','前文の同じ磁石・導体・例を保ち、同じ評価系で磁石静止・導体運動を条件とする。',['eiea','eied','eieh']),
        ('磁石周囲の電場の否定','同じ源に帰属する電気側場について、周囲領域・区間の全点で零を要求する。他の源の全場に拡張しない。',['eid4','eid5','eieq']),
        ('導体内に生じる起電力','単位電荷への局所的作用という本文の用法を参照し、導体の運動と源の磁場、校正した単位、同じ導体内の非零証人へ結ぶ。',['eidz','eid2','eid3','eisas','eier']),
        ('それ自体のエネルギーの否定','同じ駆動自体への独立の非零蓄積エネルギー帰属を排除し、零値と帰属なしを許す。仕事や他の物理系のエネルギーを否定しない。',['eisat','eid6','eid7','eies']),
        ('電流を生むこと','同じ局所駆動の物理的応答として全電流履歴を結び、非零電流の証人を持つ。単なる共存や強い全介入反転で代用しない。',['eisau','eiet','eieb']),
        ('相対運動一致の挿入留保','二場合の同じ相対履歴という条件は電流比較に置き、第二の場合の場・駆動・エネルギーの条件全体へ移動しない。',['eiec','eiee','eief','eieg']),
        ('同じ大きさと経過','第一の場合の電気的作用が生む電流と、第二の場合の駆動が生む電流を、同じ全断面と正方向・時間単位・定数時刻差で比較する。',['eiee','eibi','eiei']),
        ('提示と三つの対照','通常の理解による説明として主張の力と著者・論説への帰属を保ち、第一の場合とのaber、場の否定と駆動のdagegen、エネルギー否定と生成のaberを同じ束縛で示す。',['eiej','eiek','eiel','eiem','eisaw']),
    ]
    paths=[INVENTORY,DOC,'data/einstein-opening-source-reading-v1.json','data/einstein-opening-obligations-v1.json','data/moving-magnet-case-reading-v1.json','scripts/review_moving_conductor_case.py']
    context=[dict(unit=u['id'],source=u['text'],source_text_sha256=u['text_sha256'],role='lexical_context_not_new_completion') for u in units if u['id'] in ('einstein-1905:u0174','einstein-1905:u0176')]
    return dict(schema_version='noema-sentence-reading-1',status='sentence_content_and_presentation_checked_under_explicit_reading',reviewer='assistant_close_reading',document=FULL,meaning_basis=BASIS,unit=unit['id'],range=[771,1203],source=source,source_text_sha256=unit['text_sha256'],source_nonblank_characters=sum(not c.isspace() for c in source),selection=selection_binding(load_catalog(ROOT,BASIS),[INDEX]),requirements=[dict(requirement=r,judgment='preserved_under_stated_reading',reason=why,definitions=ds) for r,why,ds in requirements],interpretive_source_context=context,interpretation_limits=['同じ通常の理解による第二の場合の説明','起電力は本文の単位電荷用法に沿う局所的な力/電荷の係数','電場否定はこの例の磁石の源寄与と周囲の範囲','an sichは駆動自体の独立の蓄積エネルギーに限定','相対運動一致の留保は二場合の電流比較に適用'],whole_paragraph_complete=False,verified_full_units=0,semantic_equivalence_automatically_proved=False,remaining_in_paragraph=['第一文の非対称性と認識上の留保・周知性','段落全体の通読判断'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in paths})
