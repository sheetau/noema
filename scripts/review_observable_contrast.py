"""Record the explicit reading of the observable/interpretation contrast sentence."""
import json
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,selection_binding
from scripts.compose_observable_contrast import ROOT,read,FULL,BASIS,INDEX

INVENTORY='artifacts/written-units-v1/einstein-1905.json'
DOC='docs/observable-contrast-v1.md'

def build_reading():
    unit=next(u for u in json.loads(read(INVENTORY))['units'] if u['id']=='einstein-1905:u0003');source=unit['text'][308:549]
    assert source.startswith('Das beobachtbare Phänomen') and source.endswith('streng voneinander zu trennen sind.')
    requirements=[
        ('固定原文','原刊891頁照合済みの固定u0003[308,549)を用い、版・文字範囲を保持する。',['eisaj']),
        ('この観測可能な現象','前文の同じ二対象と例を引き継ぎ、後続が比較する電流の大きさ・経過を中心とする読みを明示する。測定済みは要求しない。',['eida','eisae','eidg']),
        ('比較範囲','全ての妥当な候補に同じ材料・回路・尺度等の準備を保ち、一致する観測標本だけに縮めない。',['eisad','eida','eidc']),
        ('相対運動だけへの依存','相対履歴eia2が同じなら電流eibiが同じという条件を全候補へ課す。逆含意や常に非零の運動を要求せず、二つの入れ替え場合だけへ限定しない。',['eidb','eidc']),
        ('二場合の同一対象と運動役割','第一の磁石運動・導体静止、第二の磁石静止・導体運動を同じ二対象・各系・履歴へ結ぶ。相対運動一致はこの区別の前件にはしない。',['eide','eidf']),
        ('厳密に区別する制約','全許容説明で両場合の機構分類が存在し共通分類がないという説明規則を構成する。名前の不等値や観測値の違いで代用しない。',['eidd','eide']),
        ('通常の理解への帰属','論説記述時点での通常の見解へ閉じた制約内容を帰属し、著者の承認・客観的真理・現代の理解とは分ける。',['eisah','eisai','eidi']),
        ('währendと文の提示','観測現象の前半と見解帰属の後半を順序付きに対照し、同じ著者・文書・例・前文からの順序を保持する。',['eidj','eidk','eidl','zbc']),
    ]
    paths=[INVENTORY,DOC,'data/einstein-opening-source-reading-v1.json','data/einstein-opening-obligations-v1.json',
        'data/interaction-example-reading-v1.json','scripts/review_observable_contrast.py']
    return dict(schema_version='noema-sentence-reading-1',status='sentence_content_and_presentation_checked_under_explicit_reading',
        reviewer='assistant_close_reading',document=FULL,meaning_basis=BASIS,unit=unit['id'],range=[308,549],source=source,
        source_text_sha256=unit['text_sha256'],source_nonblank_characters=sum(not c.isspace() for c in source),selection=selection_binding(load_catalog(ROOT,BASIS),[INDEX]),
        requirements=[dict(requirement=r,judgment='preserved_under_stated_reading',reason=why,definitions=names) for r,why,names in requirements],
        interpretation_limits=['この例での電流の大きさ・経過を中心に観測現象を読む','同じ準備と既存のマクロな相対履歴の適用範囲','onlyは機能的依存であり逆含意や因果実験を加えない','厳密な区別は通常の理解で許容される説明に課す分類制約'],
        whole_paragraph_complete=False,verified_full_units=0,semantic_equivalence_automatically_proved=False,
        remaining_in_paragraph=['第一文の非対称性と現象には属さないように見えるという留保','後二文の電場・起電力・エネルギーの具体的な二説明','段落全体の通読判断'],
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in paths})
