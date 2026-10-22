"""Bind active monarchical oversight to civil compatibility of implemented changes."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT,closure
from scripts.compose_qualitative_influence import both
from scripts.compose_protected_remarks import bind

PARENTS=('data/civic-compatibility-basis-v1.json','data/monarchical-sentence-basis-v1.json')
LIBRARY='examples/v016/civic-oversight.noema'
BASIS='data/civic-oversight-basis-v1.json'
FAMILY='i b[h[j[a] d] e]'
NAMES=('change','field','community','older','newer','standard')
FIELDS=' '.join(n+' a' for n in NAMES)
ARGS=' '.join('v '+n for n in NAMES)
TWO='l[a][v community v order]'
PRIMITIVES={
 'h26he':('[a a a d d] c',['activity','change','community','reference','point'],
   '同じ活動がこの点で、指定共同体の同じ変更内容を実践に導入する働きをする。変更の前後と領域は同じ固定基準のh26g6で指定し、単なる提案・予測・改善だという評価、別の変更の導入と区別する。活動生起と変更後の内容成立は別に構成する。制度改正だけに限定せず、個人の理解・判断・実践の変更も扱う。'),
 'h26hf':('[a a '+FAMILY+' j[a] d d] c',['person','activity','goal','bindings','reference','point'],
   '本人が同じ活動・点で、段階1の閉じた内容関数へ同じ対象列と固定基準を渡す内容を、その活動の目標として目指す。既存h26fvの目標関係を段階1へ広げる。引用内容の実行、実際の達成、単なる予測、別活動の目的、後付けの理由、活動の生起をこの関係だけでは補わない。'),
 'h26hg':('[a a '+FAMILY+' j[a] a d d] c',['person','activity','goal','bindings','aspect','reference','point'],
   '本人が同じ活動を進める中で、段階1の閉じた目標内容・同じ対象列・固定基準に関して、指定事項へ認知的な注意を向けている。既存hztjと同じ目標に即した注意を固定基準付きで扱う。単なる知覚、心配の感情、目的の採用、成功、他の活動への注意は別であり、目標を実行しない。'),
 'h26hh':('[a '+FAMILY+' j[a] d d] c',['activity','effect','bindings','reference','point'],
   '同じ活動の働きが、この点で、段階1の閉じた内容関数・同じ対象列・固定基準の結果を成立させ又は保つことに因果的に寄与する。新たな成立だけでなく、崩れないよう維持する寄与も含む。単なる共起、目的の保持、肩書、結果を観察しただけの場合と区別する。活動生起・実際の結果は合成側で別に要求し、唯一原因性・単独十分性・全未来の成功・脅威の実際の発生を加えない。'),
}
MEANINGS={
 'r5nc':'同じ宗教上の変更候補r5mwについて、生起する同じ活動がh26heでその変更を導入し、同じ変更後のh246e内容が同じ点で成立する。単なる改善判断や提案、別活動の生起と別内容の成立を実施へ替えない。',
 'r5nd':'同じ非空の市民的秩序の全変更候補で呼称妥当性を確認し、その点で真又は信じられた改善r5m4が実際に実施r5ncされるなら、同じ点で秩序の全条件r5m6を保つ。未実施の不適合案を実施可能にすることや、全案の実施を要求しない。',
 'r5ne':'正確な共同体・秩序の二対象列と固定基準をr5ndの実施適合内容へ渡す。目的、注意、因果的寄与、実際の結果で同じ内容族と引数を共有する。',
 'r5nf':'同じ点で同じ共同体の君主r2ujが、実際に生起する同じ活動へ参加し、r5neの同じ二対象・基準の内容を目指し、その同じ目標における同じ秩序へ注意を向けている。役職・生起・本人参加・目的・注意を別々に要求する。まだ成功や実効的寄与は要求しない。',
 'r5ng':'同じ君主・活動・共同体・秩序・基準・点のr5nfに、その同じ活動によるr5neへの因果的寄与h26hhと、同じr5ne内容の成立を結ぶ。願望・無視された注意・偶然の秩序成立だけでは満たさない。',
 'r5nh':'正確な君主・共同体・秩序の三対象列と固定基準について、同じ点でr5ngを満たす監督活動があるという内容。実効的な監督の条件であり、監督への規範的許可や義務、後半への条件命題、他の目的の全面排除は別に構成する。',
}
LIMITS=[
 '第十一文冒頭Wenn er nur darauf sieht, daß ... zusammen besteheの監督内容に向けた依存群。実施される真又は見かけの改善が同じ市民的秩序を保つよう、同じ君主が目的・注意を持ち実効的に寄与するという明示読解。条件文全体、nurの限定、後半、著者帰属は未接続で、意味確認文字数は増やさない。',
 '前回r5nbは全候補案それぞれの両立可能性を述べる比較用の構成であり、監督の必要条件には用いない。秩序に反する案を未実施にすることで秩序を保つ場合も認める必要がある。r5mw/m4/m5/m6を再利用し、実施された変更への全条件充足を新しい目標r5ndへ置く。前回の定義・証拠は変更しない。',
 '実施は同じ変更を導入する活動の生起と、同じ変更後の内容成立を結ぶ。まだ実施されていない案を自動的に排除せず、全候補を量化した上で実施の有無を条件内で判定する。改善評価の呼称不備を実施前件の偽へ隠さない。',
 'sieht daraufはここでは、実際の活動・本人参加・目的に即した注意と、同じ結果を成立又は維持させる実効的寄与を伴う監督として読む。単なる希望より強いが、君主だけが原因であること、本人がすべてを直接執行すること、全未来で一度も失敗しない保証は追加しない。',
 '評価は同じ点における監督と実施適合の構成であり、原文にない数値的な監督期間や全未来への保証を足さない。一般的・仮定的な事例範囲と後半への条件接続は全文側で固定する。',
 '目的・注意・因果は同じ段階1の閉じた内容族r5ne、共同体・秩序の二対象列、固定基準を保持する。内部で段階0のNoema内容を評価するため、段階0の目標関係h26fvやhztjへ無理に渡さない。',
 'この依存群は秩序以外への関与を許可する規範でも、宗教内容の真偽を君主が決める権能でもない。本人に委ねる範囲、職責、暴力的妨害の防止とnur/übrigens/wohl aberを接続する必要がある。',
]
@lru_cache(None)
def parents():return tuple(load_catalog(ROOT,p) for p in PARENTS)

def definitions():
    frame='k r5mw['+ARGS+' v reference]'
    actual='g activity a['+both('k dg[v activity v point]','k h26he[v activity v change v community v reference v point]',
        't[s[k h246e[v newer v reference]]][v point]')+']'
    text='d r5nc['+FIELDS+' reference d point d] c['+both(frame,actual)+'].\n'
    condition='y['+both('k r5m4['+ARGS+' v reference v point]','k r5nc['+ARGS+' v reference v point]')+'][k r5m6[v order v community v reference v point]]'
    valid='k r5m2[v older v newer v field v standard v reference]'
    universal='y['+frame+']['+both(valid,condition)+']'
    for n in reversed(NAMES):
        if n!='community':universal='f '+n+' a['+universal+']'
    text+='d r5nd[community a order a reference d] e[b point['+both('k r5m5[v order v community v reference]',universal)+']].\n'
    text+='d r5ne[bindings j[a] reference d] e[b point['+bind(('community','order'),'t[k r5nd[v community v order v reference]][v point]')+']].\n'
    goal='r b[p r5ne]';fields='actor a activity a community a order a reference d point d'
    args='v actor v activity v community v order v reference v point'
    purpose='k h26hf[v actor v activity '+goal+' '+TWO+' v reference v point]'
    attention='k h26hg[v actor v activity '+goal+' '+TWO+' v order v reference v point]'
    text+='d r5nf['+fields+'] c['+both('k r2uj[v actor v community v point]','k dg[v activity v point]',
        'k df[v actor v activity v point]',purpose,attention)+'].\n'
    text+='d r5ng['+fields+'] c['+both('k r5nf['+args+']','k h26hh[v activity '+goal+' '+TWO+' v reference v point]',
        't[k r5ne['+TWO+' v reference]][v point]')+'].\n'
    text+='d r5nh[bindings j[a] reference d] e[b point['+bind(('actor','community','order'),
        'g activity a[k r5ng[v actor v activity v community v order v reference v point]]')+']].\n'
    return text

def build():
    sources=parents();doc=deepcopy(sources[0].document);doc.update(declarations=[],statements=[]);imported={}
    for source,roots in zip(sources,(['r5mw','r5m2','r5m4','r5m5','r5m6'],['r2uj','dg','df'])):
        for d in closure(source.document,roots):
            n=d['name'];e=source.entries[n]
            if n in imported:assert d==imported[n]['declaration'] and e['meaning_ja']==imported[n]['meaning_ja'],n
            else:doc['declarations'].append(d);imported[n]=e
    assert not(set(PRIMITIVES)|set(MEANINGS))&set().union(*(set(s.entries) for s in sources))
    doc=parse(format_graph(doc,'compact')+''.join('r '+n+v[0]+'.' for n,v in PRIMITIVES.items())+definitions());ds={d['name']:d for d in doc['declarations']}
    prims={n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=e['arguments'],meaning_ja=e['meaning_ja']) for n,e in imported.items() if e['kind']=='primitive'}
    prims.update({n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=v[1],meaning_ja=v[2]) for n,v in PRIMITIVES.items()})
    paths=set().union(*(set(s.source_sha256) for s in sources))
    basis=dict(status='same_monarch_active_oversight_and_civil_order_of_implemented_improvements',document=LIBRARY,primitives=prims,
        definitions={n:e['meaning_ja'] for n,e in imported.items() if e['kind']=='definition'}|MEANINGS,
        imported_symbols={n:e['meaning_basis'] for n,e in imported.items()},import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)},limitations=LIMITS)
    return {LIBRARY:format_graph(doc,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n'}
