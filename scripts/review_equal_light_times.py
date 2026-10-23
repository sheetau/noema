"""Record the definitional equality of opposite light-travel times."""
import json,re
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,selection_binding
from scripts.compose_equal_light_times import ROOT,read,FULL,BASIS,INDEX,LIMITS

INVENTORY='artifacts/written-units-v1/einstein-1905.json';DOC='docs/equal-light-times-v1.md'
SOURCE='data/einstein-equal-light-times-source-reading-v1.json'


def source_record():
    inv=json.loads(read(INVENTORY));u=inv['units'][12];s=u['text'][822:1070]
    assert s.startswith('Die letztere Zeit kann nun definiert werden') and s.endswith('zu gelangen.')
    ids={'M0015':('A','ziq'),'M0016':('B','zir'),'M0017':('B','zir'),'M0018':('A','ziq')};maths=[]
    for m in inv['math']:
        if m['id'] in ids:
            printed,ref=ids[m['id']];assert '<mi>'+printed+'</mi>' in m['mathml']
            maths.append(dict(id=m['id'],sha256=m['sha256'],printed=printed,referent=ref))
    assert len(maths)==4
    paths=[INVENTORY,'artifacts/einstein-synchrony-continuation-v1/page-894.jpg','artifacts/einstein-synchrony-continuation-v1/page-894.html','artifacts/einstein-synchrony-continuation-v1/retrieval.json','scripts/review_equal_light_times.py']
    return dict(version='einstein-equal-light-times-source-reading-v1',reviewer='assistant_visual_and_text_review',pages=['894'],images=[paths[1]],segments=[dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[822,1070],text=s,nonblank_characters=sum(not c.isspace() for c in re.sub(r'\[M\d+\]','',s)),math=maths)],observations=['原刊894頁のDie letztere Zeit kannからnach A zu gelangen.までを第四文として照合した。nun、indem man、durch Definition、gleich istと両方の引用されたZeitを保持する。','方向はM0015=AからM0016=B、M0017=BからM0018=Aである。welche es brauchtのesは光を受け、Zeitという語の綴りや距離へ替えない。','続くEs gehe nämlichは具体的な光の出発・反射・帰着を導入する別文である。この第四文の定義上の等時間を実測済みの主張に変更しない。'],semantic_completion=False,source_sha256={p:digest((ROOT/p).read_bytes()) for p in paths})


def build_reading():
    u=json.loads(read(INVENTORY))['units'][12]
    rows=[
        ('固定原文と逆方向','181本文文字とA・B・B・Aを原刊894頁へ照合し、二方向を保持する。',['eisjh','ziq','zir']),
        ('光が進む所要時間','光・始終の出来事・二地点・系・単位を結び、候補の同じ規約による時刻割当ての差を所要時間とする。',['cf','cg','cb','eisi5','eil7']),
        ('両方向の等値','対応する二方向の候補記録を別に結び、双方の実数所要時間の数値的等値を要求する。違う時刻原点を許しても差は同じ値として比較する。',['eisi6','eisi7','eima','sca']),
        ('一般的な定義条件','対象となる全比較組に等片道時間を要求する規則とする。現実の発射済みや一つの光子の反射を余計な前提にしない。',['eisja','eimb']),
        ('定義で定める手段','同じ規約へ等時間の規則を引用して定義条件として採用し、それにより定義された規約が両地点に共通して適用されることを別に結ぶ。物理的な等時間の事実を採用関係から導かない。',['eisjb','eisiq','eilr','eimc']),
        ('定義可能性','同じ案・定義課題の可能な採用結果があり、その同じ結果で採用・定義・共通適用を満たす。実行済みやあらゆる結果での成功としない。',['eisf2','eimd','eime']),
        ('後者の時間と今','第三文で未定義とされた共通時間という種類に照応し、同じ局所A/B規則・時計・地点を保って、次の論述段階で定義を追加する。',['eisjc','eisjd','eisjg','eisji']),
        ('提示と限界','manを定義手続きの一般的提示と読み、著者の主張・本文順序を保持する。次文以降の往復光・同期式と段落判断は残す。',['eimf','eimg']),
    ]
    paths=[INVENTORY,DOC,SOURCE,'scripts/review_equal_light_times.py']
    return dict(schema_version='noema-sentence-reading-1',status='sentence_content_and_presentation_checked_under_explicit_reading',reviewer='assistant_close_reading',document=FULL,meaning_basis=BASIS,unit=u['id'],range=[822,1070],source=u['text'][822:1070],source_text_sha256=u['text_sha256'],source_nonblank_characters=181,math=source_record()['segments'][0]['math'],selection=selection_binding(load_catalog(ROOT,BASIS),[INDEX]),requirements=[dict(requirement=r,judgment='preserved_under_stated_reading',reason=reason,definitions=defs) for r,reason,defs in rows],interpretation_limits=LIMITS,whole_paragraph_complete=False,verified_full_units=0,semantic_equivalence_automatically_proved=False,remaining_in_paragraph=['第五文の具体的な往復光、第六文の同期式、段落全体の判断'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in paths})
