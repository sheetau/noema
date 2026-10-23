"""Record a close reading of the tentative time-definition proposal."""
import json
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,selection_binding
from scripts.compose_clock_definition_proposal import ROOT,read,FULL,BASIS,INDEX,LIMITS

INVENTORY='artifacts/written-units-v1/einstein-1905.json';DOC='docs/clock-definition-proposal-v1.md'

def build_reading():
    u=json.loads(read(INVENTORY))['units'][10];source=u['text'][:200]
    assert source.startswith('Es könnte scheinen,') and source.endswith('setze.')
    rows=[
        ('固定原文','原刊893頁に照合した第一文全172非空白文字を対象とし、第二文373文字を未完として分ける。',['eisgc']),
        ('自分の時計と短針','ichとmeinerを同じ著者の検討する声へ結び、その同じ時計の小さい針を時針として指定する。先行例の列車・7時・特定時計の同一性を補わない。',['eijh','eise6','eise7']),
        ('位置を時間に代える規則','時間の適用規約を定める同じ課題に、同じ時計・短針・系・尺度の指示と読みを規則として引用する。針という物体や語の綴りだけへの置換ではなく、値を示す位置を用いる定義案を保持する。',['eiji','eijj','eisdu','eisfw','eisfx']),
        ('全ての定義上の困難','同じ課題に属する困難を非空の全範囲として固定し、全てについて同じ案の採用により克服されることを要求する。成功した論点だけの抜粋や無関係の方法の成功にしない。',['eisfy','eisfz','eijk']),
        ('克服できる可能性','全困難を同じ一つの採用結果で克服できるという可能性を構成する。困難ごとに違う結果の成功や、現実での実施済み・全結果の成功保証へ替えない。',['eisf2','eijl','eijm']),
        ('思えるかもしれない','同じ内容について議論上可能な見方があり、その非空の見かけの候補全てで解決可能性が成立するという読みを採る。二種類の候補を分け、現実での全解決や著者の確信を断言しない。',['eisf3','eisf4','eijn','eijo']),
        ('帰属と順序','留保を含む同じ内容を主張の力で著者・論説へ帰属し、本文の直前の列車例からの順序を保持する。別単位の脚注を本文中の出来事順序に混ぜない。',['eijp','eijq','eir3','ue']),
        ('限界','短針の指示規則から日付・周期回数・遠隔同期・全出来事の時刻付与を導かない。有限対照例と全実数の評価拒否を区別し、次文の局所的十分性を先取りしない。',['eiji','eijj','eijo']),
    ]
    paths=[INVENTORY,DOC,'data/einstein-clock-definition-source-reading-v1.json','scripts/review_clock_definition_proposal.py']
    return dict(schema_version='noema-sentence-reading-1',status='sentence_content_and_presentation_checked_under_explicit_reading',reviewer='assistant_close_reading',document=FULL,meaning_basis=BASIS,unit=u['id'],range=[0,200],source=source,source_text_sha256=u['text_sha256'],source_nonblank_characters=sum(not c.isspace() for c in source),selection=selection_binding(load_catalog(ROOT,BASIS),[INDEX]),requirements=[dict(requirement=r,judgment='preserved_under_stated_reading',reason=reason,definitions=defs) for r,reason,defs in rows],interpretation_limits=LIMITS,whole_paragraph_complete=False,verified_full_units=0,semantic_equivalence_automatically_proved=False,remaining_in_paragraph=['第二文373文字の十分性・不十分性と二課題の同等性','段落全体の通読判断'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in paths})
