"""Compose manifested dispositions, causal acquisition, paths and retention."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT,closure
from scripts.compose_qualitative_influence import both

PARENTS=('data/shared-liberty-policy-basis-v1.json','data/public-offers-sentence-basis-v1.json')
LIBRARY='examples/v016/social-attitude-paths.noema';BASIS='data/social-attitude-paths-basis-v1.json'
STATE='i c[h[a] e]'
MAPS=(('sender','a'),('recipient','a'),('activity','a'),('process','a'),('start','d'),('acted','d'),('end','d'))
MAP_FIELDS=' '.join(n+' h[a] '+t for n,t in MAPS)
MAP_ARGS=' '.join('v '+n for n,t in MAPS)
FRAME='state '+STATE+' history h[d] c before h[d d] c'
FARGS='v state v history v before'
STEP='actor a target a act a process a start d acted d end d '+FRAME
SARGS='v actor v target v act v process v start v acted v end '+FARGS
PATH='first a rest j[a] origin a target a '+FRAME+' '+MAP_FIELDS
PARGS='v first v rest v origin v target '+FARGS+' '+MAP_ARGS
REGIONS=('ruler','rulingoffice','community','government','foreignoffice','foreigncommunity')
REGION_FIELDS=' '.join(n+' a' for n in REGIONS)
REGION_ARGS=' '.join('v '+n for n in REGIONS)
PRIMITIVES={
 'h26ph':('[a a '+STATE+' d] c',['activity','person','state','result_point'],
   'この活動が同じ人について、段階2の記述で指定された状態を、この結果点で生じさせる。g3の結果生成を高い引用段階の同じ性質へ保つ。状態の共存・時間的先行・誰かが原因だと説明することとは分ける。活動の生起点、変化の前後、状態の真理、意図・唯一原因・機構の詳細は合成側又は別の記述で扱う。'),
 'h26pi':('[a a '+STATE+' d] c',['activity','actor','state','point'],
   'この活動の内容又は行い方が、この人の指定された状態・態度の表れとなっている。同じ活動を行い同じ状態を持つという偶然の共存、態度と無関係な行動、他人の態度の中立的な紹介とは分ける。言語での自己申告だけに限らず、実践・制度運営・非言語的な応対による表れも含む。活動生起・本人の当事者性・実際の状態は合成側で確認し、受け手の取得・同意・本人の伝達意図をこの関係だけから導かない。'),
}
MEANINGS={
 'r56o':'固定基準の閉じた呼称で、r56nの共通自由方針を支持する人物性質を段階2へ閉じる。支持の対象である方針記述と、支持という状態の記述を区別する。',
 'r56p':'同じ順序付き履歴の前後で、同じ人の記述された状態が不成立から成立へ変わり、同じ過程の変化対象となる。その過程を構成する同じ活動が区間内で生起し、同じ状態を後端で生じさせる。活動時点と取得完了点は分け、活動の前後を別履歴から取らない。',
 'r56q':'同じ人が同じ点で実際の活動の当事者となり、同じ記述された態度を持ち、その活動が当人のその態度の表れh26piとなる。状態だけ、活動だけ、活動と無関係な態度では満たさない。',
 'r56r':'異なる二人について、前の人の同じ態度の表れr56qとなる同じ活動が、後の人の同じ態度の取得r56pを生じさせる。発話・受領・理解という特定経路を必須にせず、内容と因果の同一性を保持した社会的取得の一段階である。',
 'r56s':'指定した一段階から取り出す当事者二人・活動・過程・三時点を、同じr56rへ渡す。段階識別子は内容の真偽ではなく、同じ経路の設定を束ねるための参照である。',
 'r56t':'最初の一段階と任意の有限な後続列を、同じ状態記述と履歴の社会的取得経路にする。各段階がr56sを満たし、直前の取得者が次の活動者となり、前の取得完了が次の表れ活動以前にある。始点と終点の本人を固定し、経路外の活動・別内容・時間逆転を混ぜない。',
 'r56u':'r56tの最後の同じ段階・過程・前後から、同じ最終本人と記述された状態が基準点まで続くことを既存rafで要求する。中継者全員の永久的な保持や、発信者の現在までの保持は要求しない。',
 'r56v':'固定基準の呼称を確認し、r56oの同じ共通自由方針への態度をr56uの経路全体と最終保持に接続する。元と先の政府・居場所はこの一般経路とは別に固定し、伝播から自由政策そのものの実現を導かない。',
 'r56w':'基準点の同じ君主・最高職・共同体の管轄下にいる元の人r54wと、異なる共同体の公的政府・役職の管轄下にいて元の最高職の管轄下にはいない到達者を結ぶ。国外を元の制度的統治圏の外と読む。外国側に君主制、自由政策、思想への賛同を要求しない。',
 'r56x':'r56wの同じ元の人・国外の人を、r56vの同じ自由への態度の経路の始点・終点へ接続する。地域の人の存在と無関係な別人への経路を寄せ集めず、同じ基準点で国外への到達と最終保持を調べる。',
 'r56y':'元の統治者・統治圏・人、外国の政府・統治圏、共通基準・履歴を固定し、指定された経路の証人からr56xを満たす国外の取得者が少なくとも一人いる。到達者ごとに最初の段階と後続列を渡し、集団全員への到達・人口割合・全ての可能経路の探索完了は主張しない。',
}
LIMITS=[
 'u0015第三文の広がりを、同じ自由方針への態度が社会的な影響を通じて別の人にも取得され、基準点まで保持される読みで構成する。全域への拡大の完了や全員の取得を要求せず、少なくとも一経路という読みの人口・地域への接続は後続で行う。',
 '発話の同一内容・受領・理解を必須にする旧hznz/hzocはそのまま適用しない。同じ態度の表れとなる活動からの結果生成を用い、観察・実践・制度上の応対なども排除しない。影響の実際の経路と心理機構は明示した基本関係の解釈入力であり、単なる同時生起や人数差から因果を認定しない。',
 'rqteと同じ状態記述による変化・結果生成を段階2の性質へ保ち、g3の段階0型へ落とさない。既存th/rafの履歴・順序・前後の真偽・持続を再利用する。活動は前後区間内にあり、取得完了より前でも同時でもよい。',
 '一段階は後の人が前端ではその態度を持たず後端で持つ取得である。既存の態度の強化だけは取得と数えず、以前の取得後に失われて再取得する可能性を生涯の初回という条件で排除しない。中継者は次の表れの時点で同じ態度を持つが、経路終了後まで保持し続ける必要はない。',
 '経路は実際に指定された任意長の有限列であり、固定長へ限定しない。時系列と因果は各段階の内容へ結び、同じ言葉だけ・別の態度への変化・引用された自由政策の実現とは区別する。経路や人・活動・過程の現実の完全な個体化を有限試験で証明するものではない。',
 'außerhalbは元の君主の制度的統治圏の外と読み、異なる共同体の政府の下に属する人への少なくとも一つの社会的取得経路を要求する。旅行時の物理座標や近代的国籍そのものとはしない。経路証人は実際の取得を示すもので、全潜在経路を列挙したものではなく、全世界への到達を加えない。',
 '先行する自由の例と同じ精神への照応、元と先の統治者・国の本文設定、外的障害・格闘の必要・政府の自己誤解、auch/selbstと全文帰属・通読は残る。本文114主張、既存17単位と二文763文字の意味判断を保持し、第三文の確認分量は増やさない。',
]

@lru_cache(None)
def parents():return tuple(load_catalog(ROOT,p) for p in PARENTS)
def app(n,*xs):return 'c[v '+n+']['+' '.join(xs)+']'
def at(n,step='v step'):return app(n,step)
def le(a,b):return 'x[e['+a+']['+b+']][c[v before]['+a+' '+b+']]'
def definitions():
    text='d r56o[reference i[d]] '+STATE+'[o a[r c[p r56n]][v reference]].\n'
    acquired='k th[v history v before v process v start v end p ag c[s[v state]][v target]]'
    text+='d r56p[target a act a process a start d acted d end d '+FRAME+'] c['+both(acquired,
        'k la[v target v process v start v end]','c[v history][v acted]',le('v start','v acted'),le('v acted','v end'),
        'k dg[v process v end]','k dg[v act v acted]','k h6a[v act v process v acted]',
        'k h26ph[v act v target v state v end]')+'].\n'
    text+='d r56q[actor a act a state '+STATE+' point d] c['+both('k aa[v actor]','k dg[v act v point]',
        'k df[v actor v act v point]','t[c[s[v state]][v actor]][v point]','k h26pi[v act v actor v state v point]')+'].\n'
    text+='d r56r['+STEP+'] c['+both('k aa[v target]','u[e[v actor][v target]]',
        'k r56q[v actor v act v state v acted]',
        'k r56p[v target v act v process v start v acted v end '+FARGS+']')+'].\n'
    text+='d r56s[step a '+FRAME+' '+MAP_FIELDS+'] c[k r56r['+' '.join(at(n) for n,t in MAPS)+' '+FARGS+']].\n'
    check=lambda step:'k r56s['+step+' '+FARGS+' '+MAP_ARGS+']'
    initial='i[last a]['+both('e[v last][v first]','e['+at('sender','v first')+'][v origin]',check('v first'))+']'
    link=both('c[v previous][v prior]','e['+at('recipient','v prior')+']['+at('sender')+']',le(at('end','v prior'),at('acted')))
    follow='i[previous h[a] c step a][i[last a]['+both('e[v last][v step]',check('v step'),'g prior a['+link+']')+']]'
    last='q[v rest][v first][i[prior a step a][v step]]'
    text+='d r56t['+PATH+'] c['+both('c[q[v rest]['+initial+']['+follow+']]['+last+']',
        'e['+at('recipient',last)+'][v target]')+'].\n'
    retain='k raf[v history v before v target s[v state] '+at('process',last)+' '+at('start',last)+' '+at('end',last)+' v anchor p ag p la]'
    text+='d r56u['+PATH+' anchor d] c['+both('k r56t['+PARGS+']',retain)+'].\n'
    fixed='first a rest j[a] origin a target a reference d history h[d] c before h[d d] c '+MAP_FIELDS+' anchor d'
    text+='d r56v['+fixed+'] c['+both('e[s[k h223h[v reference]]][v reference]',
        'k r56u[v first v rest v origin v target k r56o[k h223h[v reference]] v history v before '+MAP_ARGS+' v anchor]')+'].\n'
    text+='d r56w['+REGION_FIELDS+' origin a target a anchor d] c['+both(
        'k r54w[v ruler v rulingoffice v community v origin v anchor]',
        'u[e[v community][v foreigncommunity]]','k r5zj[v government v foreigncommunity v anchor]',
        'k h256p[v foreignoffice v government v anchor]','k aa[v target]',
        'k h26hi[v target v foreignoffice v foreigncommunity v anchor]',
        'u[k h26hi[v target v rulingoffice v community v anchor]]')+'].\n'
    fargs='v first v rest v origin v target v reference v history v before '+MAP_ARGS+' v anchor'
    text+='d r56x['+REGION_FIELDS+' '+fixed+'] c['+both('k r56w['+REGION_ARGS+' v origin v target v anchor]',
        'k r56v['+fargs+']')+'].\n'
    population=REGION_FIELDS+' origin a reference d firsts h[a] a tails h[a] j[a] history h[d] c before h[d d] c '+MAP_FIELDS+' anchor d'
    text+='d r56y['+population+'] c[g target a[k r56x['+REGION_ARGS+' c[v firsts][v target] c[v tails][v target] v origin v target v reference v history v before '+MAP_ARGS+' v anchor]]].\n'
    return text

def build():
    sources=parents();doc=deepcopy(sources[0].document);doc.update(declarations=[],statements=[]);imported={}
    for c,roots in zip(sources,(['r56n','h223h','aa'],['th','raf','ag','la','dg','df','h6a','r54w','r5zj','h256p','h26hi'])):
        for d in closure(c.document,roots):
            n=d['name'];e=c.entries[n]
            if n in imported:assert d==imported[n]['declaration'] and e['meaning_ja']==imported[n]['meaning_ja']
            else:doc['declarations'].append(d);imported[n]=e
    assert not (set(MEANINGS)|set(PRIMITIVES))&set().union(*(set(c.entries) for c in sources))
    doc=parse(format_graph(doc,'compact')+''.join('r '+n+r[0]+'.' for n,r in PRIMITIVES.items())+definitions());ds={d['name']:d for d in doc['declarations']}
    prims={n:dict(parameters=e['declaration']['parameters'],result=e['declaration']['result'],arguments=e['arguments'],meaning_ja=e['meaning_ja']) for n,e in imported.items() if e['kind']=='primitive'}
    prims.update({n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=r[1],meaning_ja=r[2]) for n,r in PRIMITIVES.items()})
    paths=set().union(*(set(c.source_sha256) for c in sources))
    basis=dict(status='same_disposition_causal_social_paths_and_retention_partial',document=LIBRARY,primitives=prims,
        definitions={n:e['meaning_ja'] for n,e in imported.items() if e['kind']=='definition'}|MEANINGS,
        imported_symbols={n:e['meaning_basis'] for n,e in imported.items()},import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)},limitations=LIMITS)
    return {LIBRARY:format_graph(doc,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n'}
