"""Record the second sentence's explicit local/remote reading."""
import json
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,selection_binding
from scripts.compose_clock_definition_scope import ROOT,read,FULL,BASIS,INDEX,LIMITS

INVENTORY='artifacts/written-units-v1/einstein-1905.json';DOC='docs/clock-definition-scope-v1.md'

def build_reading():
    u=json.loads(read(INVENTORY))['units'][10];source=u['text'][201:639]
    assert source.startswith('Eine solche Definition') and source.endswith('Orten stattfinden.')
    rows=[
        ('固定原文と照応','第二文全373非空白文字を扱い、Eine solche Definitionを前文の同じ定義案・時間課題・話者・時計・短針・系・尺度へ結ぶ。',['eij5','eijj']),
        ('局所規則','短針の指示と同じ場所の対象出来事の局所的一致を結び、両出来事の時計の読みを保つ。別周期の同じ表示や遠隔信号の受信へ取り替えない。',['eijr','eiji','eisgm','ce']),
        ('現在の場所だけ','時計が現在所在する場所を固定し、時間定義の対象出来事を非空の全範囲についてそこだけに限定する。過去の場所や成功例だけに替えない。',['eisgf','eijs','eijt']),
        ('異所の系列を結ぶ','異なる場所の少なくとも二つの出来事系列を保持し、各系列の全構成出来事をその場所へ結ぶ。目指すのは系列間の時間対応であり、各系列内の順や空間的連結だけに縮めない。',['eisgh','eisgi','eisgj','eiju','eijv']),
        ('遠隔出来事の時間的評価','同じ時計から局所的に離れた場所の全対象出来事に時刻を与える課題を保持し、同所・近接・空の対象を遠隔の課題に混ぜない。',['eisgg','eijw']),
        ('十分性と不十分性の条件','局所だけの課題なら同じ規則が全必要条件を満たし、異所の系列連結又は遠隔の時間的評価を課題とすると満たせない条件が残る。適用範囲による限界であり、単なる時間経過による故障ではない。',['eisgk','eisgl','eijx','eijy','eij2','eij3']),
        ('同じ課題への帰着','二つの遠隔課題が同じ対象と尺度について同じ解手続きを持つという両方向の一致を保持する。実装済み・手続きの存在・同義性の自動証明は補わない。',['eisgn','eijz','eij4']),
        ('提示と帰属','in der Tatの確認を局所の条件内容に限定し、aberの対比、oder以下の同等性の挿入、第一文からの順序を同じ著者・論説へ結ぶ。内容自体も主張に含め、挿入への言及だけで済ませない。',['eij5','eij6','eij7','eisgo','eisgp','zbc']),
    ]
    paths=[INVENTORY,DOC,'data/einstein-clock-definition-source-reading-v1.json','scripts/review_clock_definition_scope.py']
    return dict(schema_version='noema-sentence-reading-1',status='sentence_content_and_presentation_checked_under_explicit_reading',reviewer='assistant_close_reading',document=FULL,meaning_basis=BASIS,unit=u['id'],range=[201,639],source=source,source_text_sha256=u['text_sha256'],source_nonblank_characters=sum(not c.isspace() for c in source),selection=selection_binding(load_catalog(ROOT,BASIS),[INDEX]),requirements=[dict(requirement=r,judgment='preserved_under_stated_reading',reason=reason,definitions=defs) for r,reason,defs in rows],interpretation_limits=LIMITS,whole_paragraph_complete=False,verified_full_units=0,semantic_equivalence_automatically_proved=False,remaining_in_paragraph=['全二文545文字の通読判断'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in paths})
