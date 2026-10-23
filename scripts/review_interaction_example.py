"""Record the explicit reading of the invitation sentence, not the whole paragraph."""
import json
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,selection_binding
from scripts.compose_interaction_example import ROOT,read,FULL,BASIS,INDEX

INVENTORY='artifacts/written-units-v1/einstein-1905.json'
DOC='docs/interaction-example-v1.md'

def build_reading():
    unit=next(u for u in json.loads(read(INVENTORY))['units'] if u['id']=='einstein-1905:u0003')
    source=unit['text'][210:307]
    assert source=='Man denke z. B. an die elektrodynamische Wechselwirkung zwischen einem Magneten und einem Leiter.'
    requirements=[
        ('固定範囲と版','原刊891頁を照合済みの固定原文u0003[210,307)を用いる。転記・原刊照合記録を保持する。',['eir6']),
        ('磁石と導体','eicr/eiciの基準付きの既存の読みを同じ左・右へ結ぶ。系・単位・源条件と基準は仮定内容内で量化する。',['eic2','eic3']),
        ('二物体の相互作用','同じ源の場を使う結合設定への基礎的な帰属eirzと、局所作用型eicwを明示する。一方向の一記録だけ、同時等大反対力、微視的機構の証明へ置き換えない。',['eic2','eirz','eicw']),
        ('同一対象','eisaa/eisab/eisacを例の談話対象とし、種類の説明を固定名へ置き換えない。後続もこの例を受ける。',['eic3','eic4']),
        ('考える呼びかけ','読者としての人が同じ閉じた内容を検討する内容に、directの発話の力を付ける。同意・実現・実験実施・実際の遵守を断言しない。',['eic5','eic6']),
        ('例示と先行論点','同じ例を先行[0,209)の論点の一例として取り上げ、本文順序を保持する。網羅・唯一・証明を補わない。',['eir5','eir7','eic7']),
        ('著者と文書への帰属','著者rd・論説eirf・提示riへ閉じたメッセージを帰属する。物理内容や読者の思考は帰属時に評価しない。',['eir3','eic7']),
    ]
    paths=[INVENTORY,DOC,'data/einstein-opening-source-reading-v1.json','data/einstein-opening-obligations-v1.json',
        'data/magnet-source-reading-v1.json','data/conductor-reading-decision-v1.json','scripts/review_interaction_example.py']
    return dict(schema_version='noema-sentence-reading-1',status='sentence_content_and_presentation_checked_under_explicit_reading',
        reviewer='assistant_close_reading',document=FULL,meaning_basis=BASIS,unit=unit['id'],range=[210,307],source=source,
        source_text_sha256=unit['text_sha256'],source_nonblank_characters=sum(not c.isspace() for c in source),
        selection=selection_binding(load_catalog(ROOT,BASIS),[INDEX]),
        requirements=[dict(requirement=r,judgment='preserved_under_stated_reading',reason=reason,definitions=names) for r,reason,names in requirements],
        interpretation_limits=['活動中の外部磁気源と通常の条件での基準付き導体能力という読み','電磁的結合は明示した物理モデルの基礎規約','原文の勧誘的な指示を一般の規範的義務や実行報告へ変えない'],
        whole_paragraph_complete=False,verified_full_units=0,semantic_equivalence_automatically_proved=False,
        remaining_in_paragraph=['先行第一文の非対称性と認識上の留保','同じ二対象を後続の二場合へ本文として引き継ぐこと','現象の相対運動への依存と通常の理解への対置','場・起電力・エネルギーと段落全体の通読判断'],
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in paths})
