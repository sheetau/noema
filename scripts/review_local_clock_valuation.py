"""Pin the first local-clock sentence and its printed occurrences of A."""
import json,re
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,selection_binding
from scripts.compose_local_clock_valuation import ROOT,read,FULL,BASIS,INDEX,LIMITS

INVENTORY='artifacts/written-units-v1/einstein-1905.json';DOC='docs/local-clock-valuation-v1.md'
SOURCE='data/einstein-local-clock-source-reading-v1.json'

def source_record():
    inv=json.loads(read(INVENTORY));u=inv['units'][12];s=u['text'][:251]
    assert s.startswith('Befindet sich im Punkte [M0002]') and s.endswith('Uhrzeigerstellungen.')
    maths=[dict(id=m['id'],sha256=m['sha256'],printed='A',referent='ziq') for m in inv['math'] if m['id'] in ('M0002','M0003','M0004')]
    assert len(maths)==3 and all(m['sha256']=='54d50fafeb332857187f47519e3fc74b679b89c2e3e779038dc2f566127bc4ff' for m in maths)
    paths=[INVENTORY,'artifacts/einstein-time-continuation-v1/page-893.jpg','artifacts/einstein-time-continuation-v1/page-893.html','artifacts/einstein-time-continuation-v1/retrieval.json','scripts/review_local_clock_valuation.py']
    return dict(version='einstein-local-clock-source-reading-v1',reviewer='assistant_visual_and_text_review',pages=['893'],images=[paths[1]],segments=[dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[0,251],text=s,nonblank_characters=sum(not c.isspace() for c in re.sub(r'\[M\d+\]','',s)),math=maths)],observations=['原刊893頁下部のBefindet sich im Punkte AからUhrzeigerstellungenまでの第一文を固定転記へ照合した。三つのAはいずれも同じ場所を指す。un-mittelbarenの行末分割を接続し、本文の条件・kann・durch Aufsuchenを保持する。','第一文の後で点Bの時計を導入し、第二文が894頁へ続く。今回の照合範囲に第二文や頁境界を含めない。','同頁の脚注は近接場所の局所同時性に対する理想化の留保を述べている。第一文のunmittelbare Umgebungはその読みと整合させる。'],semantic_completion=False,source_sha256={p:digest((ROOT/p).read_bytes()) for p in paths})

def build_reading():
    u=json.loads(read(INVENTORY))['units'][12];source=u['text'][:251]
    rows=[
        ('原文と記号','原刊893頁の第一文197本文文字と三つのAを固定し、M0002–M0004を同じziqへ結ぶ。',['ziq','eish2']),
        ('時計があるという条件','同じA側の時計が指定場所にあるという条件を、観測実行済みや無条件の時計存在へ替えない。',['eiky','eik7']),
        ('同じ場所の観測者','代表的な観測者と時計、指針、尺度を同じ場所へ結び、著者の私有時計・短針・原点に限定しない。',['eik2']),
        ('近傍の全範囲','同一場所と局所的な近接場所を含め、元の範囲の全対象を一つの成功候補で扱う。',['eisfp','eikz','eish7','eik5']),
        ('同時の表示を探す手段','対象の生起と同時の表示を探し当て、同じ時計と単位の有効な読みを対象に付与する。',['eisgm','eisgt','eish3','eish4','eik3']),
        ('候補と値の結合','同じ出来事・時計・状況に属する場所と表示の欄、値候補を結ぶ。既定値で未知を補わない。',['eish5','eish6','eik4']),
        ('可能性と全対象','同じ対象範囲・時計・場所を保つ操作の候補があり、全対象の対応がその候補で成立する。実行済みや全候補での保証にはしない。',['eisia','eik5','eik6','eik7']),
        ('前文への接続と帰属','既存の前方参照の始点eish2を用い、条件付き可能性の主張を同じ著者と論説へ帰属する。',['eila','eilb']),
    ]
    paths=[INVENTORY,DOC,SOURCE,'scripts/review_local_clock_valuation.py']
    return dict(schema_version='noema-sentence-reading-1',status='sentence_content_and_presentation_checked_under_explicit_reading',reviewer='assistant_close_reading',document=FULL,meaning_basis=BASIS,unit=u['id'],range=[0,251],source=source,source_text_sha256=u['text_sha256'],source_nonblank_characters=197,math=source_record()['segments'][0]['math'],selection=selection_binding(load_catalog(ROOT,BASIS),[INDEX]),requirements=[dict(requirement=r,judgment='preserved_under_stated_reading',reason=reason,definitions=defs) for r,reason,defs in rows],interpretation_limits=LIMITS,whole_paragraph_complete=False,verified_full_units=0,semantic_equivalence_automatically_proved=False,remaining_in_paragraph=['点Bの時計以降と段落全体の判断'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in paths})
