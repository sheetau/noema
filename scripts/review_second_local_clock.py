"""Record the page-spanning B-clock sentence and its explicit interpretation."""
import json,re
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,selection_binding
from scripts.compose_second_local_clock import ROOT,read,FULL,BASIS,INDEX,LIMITS

INVENTORY='artifacts/written-units-v1/einstein-1905.json';DOC='docs/second-local-clock-v1.md'
SOURCE='data/einstein-second-local-clock-source-reading-v1.json'

def source_record():
    inv=json.loads(read(INVENTORY));u=inv['units'][12];s=u['text'][252:560]
    assert s.startswith('Befindet sich auch') and s.endswith('Beobachter möglich.')
    ids={'M0005':('B','zir'),'M0006':('A','ziq'),'M0007':('B','zir'),'M0008':('B','zir')}
    maths=[]
    for m in inv['math']:
        if m['id'] in ids:
            printed,ref=ids[m['id']];assert '<mi>'+printed+'</mi>' in m['mathml']
            maths.append(dict(id=m['id'],sha256=m['sha256'],printed=printed,referent=ref))
    assert len(maths)==4
    annotation=next(a for a in inv['annotations'] if a['id']=='A0005');assert annotation['kind']=='page' and annotation['source_id']=='894'
    paths=[INVENTORY,'artifacts/einstein-time-continuation-v1/page-893.jpg','artifacts/einstein-time-continuation-v1/page-893.html','artifacts/einstein-time-continuation-v1/retrieval.json','artifacts/einstein-synchrony-continuation-v1/page-894.jpg','artifacts/einstein-synchrony-continuation-v1/page-894.html','artifacts/einstein-synchrony-continuation-v1/retrieval.json','scripts/review_second_local_clock.py']
    return dict(version='einstein-second-local-clock-source-reading-v1',reviewer='assistant_visual_and_text_review',pages=['893','894'],images=[paths[1],paths[4]],segments=[dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[252,560],text=s,nonblank_characters=sum(not c.isspace() for c in re.sub(r'\[M\d+\]','',s)),math=maths)],page_boundary=dict(id='A0005',printed_page='894',before_math='M0007'),observations=['893頁末のBefindet sich auch im Punkte Bから、894頁冒頭のB durch einen in B befindlichen Beobachter möglich.までを第二文として照合した。Beschaffen-heitの行末分割を接続し、genau derselbenと二つのauch、wir wollen hinzufügenの挿入を確認した。','M0005・M0007・M0008はB、挿入中のM0006はAである。A0005は頁894の境界であり、別の主張・脚注や文末ではない。','二時計の構成の一致を付け加えることと、近傍の出来事を局所的に評価できることを分ける。後の共通時間と同期条件の文へ今回の範囲を広げない。'],semantic_completion=False,source_sha256={p:digest((ROOT/p).read_bytes()) for p in paths})

def build_reading():
    u=json.loads(read(INVENTORY))['units'][12];source=u['text'][252:560]
    rows=[
        ('固定原文と頁境界','234本文文字とB・A・B・Bを893–894頁へ照合し、頁境界を文の一部として誤読しない。',['eisio','ziq','zir']),
        ('A側を保つ追加設定','A側の同じ時計を比較元にし、別のB側時計がBにある条件を追加する。',['eile','eilf','eilj']),
        ('全く同じ構成','同じ完全な比較規約の全特徴で、非空の構成記述集合が両方向に一致することを要求する。近似や一つの共通属性へ弱めない。',['eisif','eisig','eisih','eilc','eild','eilg']),
        ('追加する意思と挿入','同じ構成条件をこの設定へ採用する行為を、付け加える意思の対象とし、挿入の提示も保持する。',['eilk','eill','eisii']),
        ('B側の局所評価','Bにいる観測者・同じ時計・表示・B近傍の対象を第一文と同じeik6へまとめて結ぶ。',['eili','eik6']),
        ('二つのauch','時計を追加することと、同様に局所評価が可能であることを別の二内容対で追加する。',['eisij','eilo']),
        ('条件と可能性','条件付きの局所可能性と著者の意思を保持し、遠隔同期・時計原点の一致・実行済みを補わない。',['eilj','eilm','eiln']),
        ('本文接続と限界','第一文からの順序と同じ著者への帰属を保持する。構成の物理的実証と後続の共通時間の記述は今回の完了扱いにしない。',['eilo']),
    ]
    paths=[INVENTORY,DOC,SOURCE,'scripts/review_second_local_clock.py']
    return dict(schema_version='noema-sentence-reading-1',status='sentence_content_and_presentation_checked_under_explicit_reading',reviewer='assistant_close_reading',document=FULL,meaning_basis=BASIS,unit=u['id'],range=[252,560],source=source,source_text_sha256=u['text_sha256'],source_nonblank_characters=234,math=source_record()['segments'][0]['math'],selection=selection_binding(load_catalog(ROOT,BASIS),[INDEX]),requirements=[dict(requirement=r,judgment='preserved_under_stated_reading',reason=reason,definitions=defs) for r,reason,defs in rows],interpretation_limits=LIMITS,whole_paragraph_complete=False,verified_full_units=0,semantic_equivalence_automatically_proved=False,remaining_in_paragraph=['第三文以降の共通時間・同期と段落全体の判断'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in paths})
