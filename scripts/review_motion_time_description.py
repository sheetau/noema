"""Record the two opening sentences without claiming the whole time paragraph."""
import json
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,selection_binding
from scripts.compose_motion_time_description import ROOT,read,FULL,BASIS,INDICES,LIMITS

INVENTORY='artifacts/written-units-v1/einstein-1905.json';DOC='docs/motion-time-description-v1.md'

def build_reading():
    unit=json.loads(read(INVENTORY))['units'][9];source=unit['text'][:337]
    assert source.startswith('Wollen wir') and source.endswith('verstanden wird.')
    rows=[
        ('固定原文','前二文の全範囲を原刊892頁へ照合し、数式・脚注の欠落がないことを確認した。後二文はこの判断に含めない。',['eiset','eiseu']),
        ('記述意図と方法','物質点の運動を記述しようとする条件から、三座標を時間関数として与える同じ著者の方法へ結ぶ。実際の意図の存在、点を動かす意思、既に実行した読者の行為へ替えない。',['eisen','eiil','eiim']),
        ('同じ点と三座標の時間依存','同じraの同じ物質点、長さ・時間単位、全対象期間、三関数の割当を保持し、有効な実時間入力に有効な実座標出力を要求する。定数・往復・非等速を除かない。',['eiii','eiij','eiik']),
        ('記述と物理的正しさ','全履歴対応seを同じ記述の正しさの基準として引用する。三関数の表示が存在するだけで提示行為を済ませず、基準の引用を物理的真理や実測へ昇格させない。',['se','eisem','eisep']),
        ('同種の数学的記述への参照','derartigeを前文と同じ数学的記述型へ結び、物理的意味や理解の成功した記述だけを選ばない。',['eiseo','eiip']),
        ('物理的意味と時間の理解','変数が物理的な対象・出来事・尺度を指す解釈と、その時間の指示・適用条件の明確な把握を分ける。予測が正しいことや他の人の理解を補わない。',['eiseq','eiser','eises']),
        ('先行する必要条件','同じ使用者・時間規約・記述に対する理解の到達が、現在より厳密に前であることをzm4で結ぶ。erst dann … wennを必要条件として保持し、逆向きの十分性や同時・後からの理解へ替えない。',['zm4','eiiq','eiir']),
        ('帰属と注意喚起','前二文を同じ著者・論説に主張として帰属し、前段落からの順序と第二文の注意すべき事項としての提示を保持する。読者の実際の注意や証明済みを要求しない。',['eiin','eiio','eiis','eiit','zei']),
        ('根拠と限界','全実数・全関数の量化を有限標本へ縮めず、局所本体・引数接続・先後関係・必要条件の方向を検査する。対照例の通過から同義性の自動証明を主張しない。',['eiij','eiil','eiip','eiiq','eiir']),
    ]
    paths=[INVENTORY,DOC,'data/einstein-motion-time-source-reading-v1.json','scripts/review_motion_time_description.py']
    return dict(schema_version='noema-sentence-reading-1',status='two_sentence_content_and_presentation_checked_under_explicit_reading',reviewer='assistant_close_reading',document=FULL,meaning_basis=BASIS,unit=unit['id'],range=[0,337],sentence_ranges=[[0,126],[127,337]],source=source,source_text_sha256=unit['text_sha256'],source_nonblank_characters=sum(not c.isspace() for c in source),selection=selection_binding(load_catalog(ROOT,BASIS),INDICES),requirements=[dict(requirement=r,judgment='preserved_under_stated_reading',reason=reason,definitions=defs) for r,reason,defs in rows],interpretation_limits=LIMITS,whole_paragraph_complete=False,verified_full_units=0,semantic_equivalence_automatically_proved=False,remaining_in_paragraph=['第三文の時間判断と同時的出来事','第四文の列車到着と時計の短針の引用例','原刊893頁の照合と段落全体の通読判断'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in paths})
