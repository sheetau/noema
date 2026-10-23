"""Record the explicit reading of the moving-magnet explanation."""
import json
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,selection_binding
from scripts.compose_moving_magnet_case import ROOT,read,FULL,BASIS,INDEX

INVENTORY='artifacts/written-units-v1/einstein-1905.json';DOC='docs/moving-magnet-case-v1.md'
def build_reading():
    unit=next(u for u in json.loads(read(INVENTORY))['units'] if u['id']=='einstein-1905:u0003');source=unit['text'][550:770]
    assert source.startswith('Bewegt sich nämlich') and source.endswith('einen Strom erzeugt.')
    requirements=[
        ('固定原文','原刊891頁との照合記録を保ち、u0003[550,770)の一文を用いる。',['eisaq']),
        ('同じ磁石と導体の条件','前二文の同じ例と二物体を保ち、同じ評価系・区間で磁石運動、導体静止を要求する。',['eidm','eidu','eidv']),
        ('磁石周囲に生じる電場','同じ源の電気側場を周囲の空間範囲と生成に結ぶ。非零場の区間内証人を持ち、単なる数値場の指定や既存外場の共存で代用しない。',['eisal','eisam','eido','eids']),
        ('あるエネルギー値','同じ電気側場と領域の量を仕事・交換収支に接続した規約で帰属し、非負で有効な各時刻の値を要求する。時間一定性は加えない。',['eisan','eidp','eidq']),
        ('導体の部分がある場所','導体の全物質点の全区間の座標を同じ周囲領域へ結び、局所の場・担体への作用・断面輸送を共有する。',['eidn','eisao','eica']),
        ('その場が電流を生む','同じ場の電気的作用による全輸送応答への物理的帰属と、全履歴の妥当性・非零電流の証人を別に結ぶ。他原因の併存・零交差を排除しない。',['eisao','eidr','eids']),
        ('条件と量化','許容事例の運動静止条件から、同じ設定のエネルギーと電流の履歴および証人の存在を述べる。具体的数値や現実の実験実施を補わない。',['eidt','eidu']),
        ('通常の説明とnämlich','先行文の通常の理解による区別の具体化と読む。閉じた説明内容の見解帰属、主張の力、著者・文書への帰属と説明の談話関係を保つ。',['eidw','eidx','eidy','uf']),
    ]
    paths=[INVENTORY,DOC,'data/einstein-opening-source-reading-v1.json','data/einstein-opening-obligations-v1.json','data/observable-contrast-reading-v1.json','scripts/review_moving_magnet_case.py']
    return dict(schema_version='noema-sentence-reading-1',status='sentence_content_and_presentation_checked_under_explicit_reading',reviewer='assistant_close_reading',document=FULL,meaning_basis=BASIS,unit=unit['id'],range=[550,770],source=source,source_text_sha256=unit['text_sha256'],source_nonblank_characters=sum(not c.isspace() for c in source),selection=selection_binding(load_catalog(ROOT,BASIS),[INDEX]),requirements=[dict(requirement=r,judgment='preserved_under_stated_reading',reason=why,definitions=ds) for r,why,ds in requirements],interpretation_limits=['通常の理解による第一の場合の説明として読む','例のマクロな物体と準備、導体部分を含む磁石周囲の範囲','場の生成を初期の全空間の零場に限定しない','エネルギーは各時刻の値であって時間一定ではない','物理的生成の基礎帰属と局所作用型を保ち、強い全介入反転条件を加えない'],whole_paragraph_complete=False,verified_full_units=0,semantic_equivalence_automatically_proved=False,remaining_in_paragraph=['第一文の非対称性と認識上の留保','逆の場合の起電力・エネルギー・電流一致の一文','段落全体の通読判断'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in paths})
