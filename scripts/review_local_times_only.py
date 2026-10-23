"""Collate the third local-time sentence and record its scoped reading."""
import json,re
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,selection_binding
from scripts.compose_local_times_only import ROOT,read,FULL,BASIS,INDEX,LIMITS

INVENTORY='artifacts/written-units-v1/einstein-1905.json'
DOC='docs/local-times-only-v1.md'
SOURCE='data/einstein-local-times-only-source-reading-v1.json'


def source_record():
    inv=json.loads(read(INVENTORY));u=inv['units'][12];s=u['text'][561:821]
    assert s.startswith('Es ist aber ohne weitere Festsetzung') and s.endswith('gemeinsame „Zeit“ definiert.')
    ids={f'M{i:04}':('A','ziq') if i%2 else ('B','zir') for i in range(9,15)}
    maths=[]
    for m in inv['math']:
        if m['id'] in ids:
            printed,ref=ids[m['id']];assert '<mi>'+printed+'</mi>' in m['mathml']
            maths.append(dict(id=m['id'],sha256=m['sha256'],printed=printed,referent=ref))
    assert len(maths)==6
    paths=[INVENTORY,'artifacts/einstein-synchrony-continuation-v1/page-894.jpg','artifacts/einstein-synchrony-continuation-v1/page-894.html','artifacts/einstein-synchrony-continuation-v1/retrieval.json','scripts/review_local_times_only.py']
    return dict(version='einstein-local-times-only-source-reading-v1',reviewer='assistant_visual_and_text_review',pages=['894'],images=[paths[1]],segments=[dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[561,821],text=s,nonblank_characters=sum(not c.isspace() for c in re.sub(r'\[M\d+\]','',s)),math=maths)],observations=['原刊894頁のEs ist aberからgemeinsame „Zeit“ definiert.までを第三文として確認した。ohne weitere Festsetzung、bisher nur、aber keineとセミコロンを保持する。','M0009–M0014は順にA・B・A・B・A・B。中間の二記号は引用されたA-Zeit・B-Zeitの場所指定、末尾の二記号は一つの共通時間の適用先である。','次のDie letztere Zeit kann nun definiert werdenからは追加の定義の導入となる。この文の未定義を後続の状態まで延長しない。'],semantic_completion=False,source_sha256={p:digest((ROOT/p).read_bytes()) for p in paths})


def build_reading():
    u=json.loads(read(INVENTORY))['units'][12]
    rows=[
        ('原文範囲と場所記号','181本文文字、六つのA/B、引用符、セミコロン、二つのaberを原刊894頁へ照合した。',['eisiz','ziq','zir']),
        ('同じ二地点の出来事の比較','局所規則・二時計・場所・系・単位・論述段階を同じ課題へ結び、出来事の型と所在地を確認する。',['eisis','eilt']),
        ('追加規定なしという限定','適用可能な手続きの全範囲、各手続きの全必要規定、非空の全必要条件を分ける。既定義の規定だけを使い全条件を満たす手続きの不存在を合成する。',['eisit','eisiu','eisgk','eisiv','eilu','eilv','eilw','eilx','eily']),
        ('局所A時間とB時間','前二文の同じ課題・観測者・時計・表示・地点によるeik4を局所時間規約へ結ぶ。物理的な全読取り済みへ変えない。',['eisiw','eisix','eisip','eilp','eilz']),
        ('これまでと二つだけ','著者のこの二地点の議論における第三文直前の段階へ定義済み範囲を固定する。両局所規約の定義と、全既定義規約がそのいずれかであることを要求する。',['eisiy','eisiq','eilq']),
        ('共通時間の未定義','同じ時間規約の共有された解釈・比較関係が両地点へ適用されるものを、当該段階の既定義範囲から否定する。将来の定義や共通時間一般の存在を否定しない。',['eisir','eilr','eils','eil2']),
        ('セミコロンの説明と二対比','局所時間だけと共通未定義を結び、その内容を比較不能の説明理由とする。前文の局所評価の可能性と今回の比較不能、および局所二時間と共通未定義の対比を保持する。',['eil3','eil4','eisdk','zbc','eil6']),
        ('呼称と著者の主張','A-Zeit・B-Zeitの指示を各地点・局所規約に結び、wirを同じ著者の定義行為の参照として保持する。主張メッセージ・帰属・前文からの順序を接続する。',['eisi2','eisi3','eisi4','eil5','eil6']),
    ]
    paths=[INVENTORY,DOC,SOURCE,'scripts/review_local_times_only.py']
    return dict(schema_version='noema-sentence-reading-1',status='sentence_content_and_presentation_checked_under_explicit_reading',reviewer='assistant_close_reading',document=FULL,meaning_basis=BASIS,unit=u['id'],range=[561,821],source=u['text'][561:821],source_text_sha256=u['text_sha256'],source_nonblank_characters=181,math=source_record()['segments'][0]['math'],selection=selection_binding(load_catalog(ROOT,BASIS),[INDEX]),requirements=[dict(requirement=r,judgment='preserved_under_stated_reading',reason=reason,definitions=defs) for r,reason,defs in rows],interpretation_limits=LIMITS,whole_paragraph_complete=False,verified_full_units=0,semantic_equivalence_automatically_proved=False,remaining_in_paragraph=['第四文以降の等片道時間・往復光・同期式と段落全体の判断'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in paths})
