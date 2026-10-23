"""Collate the hypothetical pulse and the displayed synchrony equation."""
import json,re
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,selection_binding
from scripts.compose_light_roundtrip_definition import ROOT,read,FULL,BASIS,INDEX,LIMITS

INVENTORY='artifacts/written-units-v1/einstein-1905.json';DOC='docs/light-roundtrip-definition-v1.md'
SOURCE='data/einstein-light-roundtrip-definition-source-reading-v1.json'


def source_record():
    inv=json.loads(read(INVENTORY));u,w=inv['units'][12:14];s=u['text'][1071:1347]
    assert s.startswith('Es gehe nämlich') and s.endswith('synchron, wenn') and w['text']=='[M0030]'
    refs={19:('A','ziq'),20:('t_A','eisjo'),21:('A','ziq'),22:('B','zir'),23:('B','zir'),24:('t_B','eisjp'),25:('B','zir'),26:('A','ziq'),27:('A','ziq'),28:('t′_A','eisjq'),29:('A','ziq'),30:('t_B − t_A = t′_A − t_B','eims')}
    maths=[]
    for m in inv['math']:
        i=int(m['id'][1:])
        if i in refs:
            printed,ref=refs[i];maths.append(dict(id=m['id'],sha256=m['sha256'],printed=printed,referent=ref,unit=w['id'] if i==30 else u['id']))
    assert len(maths)==12
    paths=[INVENTORY,'artifacts/einstein-synchrony-continuation-v1/page-894.jpg','artifacts/einstein-synchrony-continuation-v1/page-894.html','artifacts/einstein-synchrony-continuation-v1/retrieval.json','scripts/review_light_roundtrip_definition.py']
    segments=[dict(unit=z['id'],unit_sha256=z['text_sha256'],range=[a,b],text=z['text'][a:b],nonblank_characters=sum(not c.isspace() for c in re.sub(r'\[M\d+\]','',z['text'][a:b])),math=[m for m in maths if m['unit']==z['id']]) for z,a,b in ((u,1071,1347),(w,0,len(w['text'])))]
    return dict(version='einstein-light-roundtrip-definition-source-reading-v1',reviewer='assistant_visual_and_text_review',pages=['894'],images=[paths[1]],segments=segments,observations=['原刊894頁のEs gehe nämlichからzurück.までが第五文、Die beiden Uhren laufen definitionsgemäß synchron, wennに続く別行の式までが第六文である。原文の接続法・nämlich・definitionsgemäß・wennを保持する。','三読みはAの出発t_A、Bの反射t_B、Aの帰着t′_A。M0028のMathMLではプライムと添字の木が分かれているが、原刊では帰着のt′_Aを表す。別時計や別地点の記号ではない。','式M0030は左がt_B−t_A、右がt′_A−t_B。右辺の減数も同じt_Bであり、二つの差を比較する。末尾の句点を新たな命題とは数えない。'],semantic_completion=False,source_sha256={p:digest((ROOT/p).read_bytes()) for p in paths})


def build_reading():
    rows=[
        ('仮想設定の導入','接続法で述べた往復をugの引用対象とし、実際の発射済みや等時間式の成立としない。',['eiml','eimm','eimn']),
        ('同じ光の往復','同じ光のA→B、Bでの反射、B→Aを同じ三出来事と地点へ結ぶ。',['da','eimh','eisjk','eisjl','eisjm','eisjn']),
        ('三つの局所読取り','同じA/B時計・単位・系を用い、出発と帰着をA、反射をBへ結ぶ。記号とqc–qkの試行記録を同じ値へ固定する。',['eiml','eisjo','eisjp','eisjq']),
        ('二つの差の等値','M0030の二つの差を作り、その実数値を比較する。両辺のt_Bを同じ値へ結ぶ。',['eimi','eims']),
        ('同期の定義条件','具体的な条件式と全関連試行への適用を分け、同じ二時計の同期をその規約で定義する。非空・完全範囲を保ち、一回の偶然の一致に弱めない。',['qn','eimj','eimk','eisju','eimp']),
        ('前文の具体化と順序','nämlichを第四文の方法から具体的往復への説明へ結び、同じ局所時間の呼称、著者、論説、本文順序を保持する。',['eisjt','eisi4','eimo','eimr']),
    ]
    paths=[INVENTORY,DOC,SOURCE,'scripts/review_light_roundtrip_definition.py']
    return dict(schema_version='noema-connected-sentences-reading-1',status='sentence_content_and_presentation_checked_under_explicit_reading',reviewer='assistant_close_reading',document=FULL,meaning_basis=BASIS,segments=source_record()['segments'],source_nonblank_characters=162,selection=selection_binding(load_catalog(ROOT,BASIS),[INDEX,INDEX+1]),requirements=[dict(requirement=r,judgment='preserved_under_stated_reading',reason=reason,definitions=defs) for r,reason,defs in rows],interpretation_limits=LIMITS,whole_paragraph_complete=False,verified_full_units=0,semantic_equivalence_automatically_proved=False,remaining=['前四文を合わせたu0013・u0014全単位の通読判断'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in paths})
