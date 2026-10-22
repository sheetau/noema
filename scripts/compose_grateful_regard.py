"""Compose credited benefit, its valuation and a grounded appreciative attitude."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT,closure
from scripts.compose_qualitative_influence import both

PARENTS=('data/merit-praise-basis-v1.json','data/named-epoch-sentence-basis-v1.json')
LIBRARY='examples/v016/grateful-regard.noema';BASIS='data/grateful-regard-basis-v1.json'
GOAL='i[h[a] e]';ASPECT='i b[h[a] e]';CONTENT='i d[e]'
FIELDS='actor a activity a beneficiary a goal '+GOAL+' reference d candidate d point d'
ARGS='v actor v activity v beneficiary v goal v reference v candidate v point'
NAMES=('actor','activity','beneficiary','reference','candidate','point')
TAIL='activity a beneficiary a goal '+GOAL+' reference d candidate d point d'
TARGS='v activity v beneficiary v goal v reference v candidate v point'
PRIMITIVES={
 'h26nt':('[a a '+GOAL+' d] c',['holder','beneficiary','state','point'],
   '本人が、記述された状態にこの別の受益者があることを、その受益者にとって好ましいものとして積極的に受け入れる態度を保持する。idの自分の状態への受容を他者へ向ける関係であり、無反応、本人だけの利得、客観的な福利、状態の実在、その結果を作った人への好意とは分ける。睡眠など一時的に意識しないことだけで態度の消滅とはしない。'),
 'h26nu':('[a a '+ASPECT+' d] c',['holder','person','aspect','point'],
   '本人が、その記述の下で捉える相手に対し、肯定的に受け止め価値を認め、その点で相手を軽んじず敬意を保つ対人的な態度を保持する。単に相手について肯定命題を信じることや、自分の結果だけを喜ぶこととは別である。親密さ・愛着、常時の感情喚起、相手の全人格への賛同、実際の発話・返礼・服従を必要としない。記述の真理と、この態度を取る根拠は別に結ぶ。'),
 'h26nv':('[a a '+ASPECT+' '+CONTENT+' d] c',['holder','person','attitude_aspect','accepted_ground','point'],
   '本人が同じ相手を同じ記述の下で肯定的に受け止める態度を、この同じ受け入れた内容を根拠として保持している。認識と態度の単なる同時成立、別人への好意、無関係な好意の理由ではない。唯一の動機・心理的な十分原因、内容の真理、相手への客観的な義務・返礼の規範を追加しない。認識と態度そのものの成立は合成側で別に要求する。'),
}
MEANINGS={
 'r5yf':'同じ固定基準・候補履歴で、指定の人の同じ行為が先行点で生起し、その行為が同じ受益者の記述された状態を後続又は同時の結果点で生じさせ、状態が実際に成立する。両点は評価点以前であり、厳密な全順序の同じ履歴に属する。行為時と受益時の同時性、行為者の意図・唯一原因、現在も状態が続くことは要求しない。',
 'r5yg':'感謝する本人と受益者がともに人で、同一ならidによる自分の状態の好ましい受容、別人ならh26ntによるその人の状態の好ましい受容を持つ。受益者と認識主体を常に同一にせず、他者への恩恵を受け入れる場合を含める。',
 'r5yh':'r5yfの行為者・行為・受益者・状態記述・基準・候補履歴・評価点を固定した内容。外側の評価点を変えても、認められた出来事の評価時点を移さない。',
 'r5yi':'r5yhへ同じ閉じた個体名・状況名と状態記述そのものの引用を適用し、h26nfへ渡せる段階3の閉じた内容を構成する。構築時に過去の行為・結果・因果を実行しない。',
 'r5yj':'同じ行為・受益者・状態・基準・候補履歴・評価点で、r5yhを行為者別に返す性質。態度の向かう相手を、認められた恩恵の行為者として捉える。',
 'r5yk':'r5yjの同じ設定へ閉じた名前を渡す段階1の人物性質記述。状態内容の脱引用を含むため段階0には落とさず、相手への態度でこの記述の真理を要求しない。',
 'r5yl':'認める内容と相手の捉え方へ共用する三個体・三状況の呼称を元の値へ照合する。状態記述の引用はo rで同じ記述そのものから構成する。',
 'r5ym':'同じ全参照が整い、本人がh26nfによって同じ行為者の同じ恩恵内容を成り立つと認める。誤認を許し、実際の行為・受益・因果の真理をその判断から実行しない。',
 'r5yn':'同じ本人・相手・行為・受益者・状態・評価点について、結果への好ましい受容r5yg、相手の寄与を認めるr5ym、相手への肯定的態度h26nu、その認識を態度の根拠とするh26nvを結ぶ。結果だけの喜び、認識だけ、無関係な好意だけでは成立しない。',
 'r5yo':'同じ恩恵の行為・受益者・状態・固定基準と候補履歴を保持して、r5ynの態度を本人と相手の二引数の性質にする。発話や返礼をしなくても保持する態度として記述する。',
 'r5yp':'同じ話者・称揚行為・対象者・評価点で、r5yoの感謝の態度とr5x5の強い肯定的な評価表明を結ぶ。恩恵の行為と今の称揚行為は別引数であり、認識だけで発話済みにしない。態度と発話の同時成立で、態度が発話の唯一の心理原因だとはしない。',
}
LIMITS=[
 'u0015第一文のdankbarenを、恩恵を好ましく受け入れ、その寄与を相手に認め、その認識に基づいて相手を肯定的に受け止める持続的な態度として読む。一般的な経験的・倫理的な感謝の全理論や、返礼の義務そのものの定義にはしない。',
 '旧rooでは行為者による達成と本人自身の受容が中心だった。ここでは行為の生起点と結果点を分け、受益者と認識主体を分ける。過去の行為が後代の人の状態へ結果を生じさせる場合や、別の人への恩恵を好ましく受け入れる場合を許す。',
 '因果は既存g3の結果生成を使い、時間的な先行から生成を推論しない。直接・即時に限らない読みを採るが、中間経路の存在を入力なしで証明したり、全ての遠い出来事を原因に数えたりしない。具体的な解放の功績と後続者への効果は別途Noemaで閉じる。',
 '認める内容はh26nfの誤りうる判断として引用する。感謝の態度があっても実際の恩恵や相手の意図を導かず、相手の寄与と善意を区別する。恩恵自体が客観的に善であることと、本人が好ましく受け入れることも区別する。',
 'hzywの親しみを伴う愛着では、遠い時代の統治者への承認まで親密さを要求してしまう。ここでは肯定的な対人的態度を一般関係に分け、恩恵認識との根拠関係を別に結ぶ。常時の感情喚起、実際の称揚や返礼は態度の必要条件にしない。',
 '後年のAA VI 454–455の恩恵に対する相手への敬意、行為的な感謝と心情の区別、先祖への感謝を補助にする。1784年のこの形容詞に後年の義務論全体を追加しない。また同箇所の善意だけへの感謝まで、今回の実現した恩恵を認める構成の必要十分条件で説明したとはしない。',
 '相手を捉える記述は段階1、認める内容は既存h26nfに合わせ段階3とする。引用された行為・結果の内容を態度の判定時に実行せず、呼称の一致だけを実評価する。',
 'r5ypは感謝している話者による称揚を構成するが、功績の記述と恩恵の具体的な内容の対応は本文束縛で与える。現在と後代の全人物範囲、集団として感謝しているという分布の読み、時代順序、両範囲から値するという規範評価は次に統合する。',
 '最初の政府側の解放と良心事項の自由という功績、適合基準、固定設定・著者帰属・一文全体・後続は未完。本文112主張・登録簿v196・17単位判断と意味確認済み文字数を変えない。',
]

@lru_cache(None)
def parents():return tuple(load_catalog(ROOT,p) for p in PARENTS)

def name_args(names):
    return ' '.join('k '+('h223h' if n in ('reference','candidate','point') else 'h223g')+'[v '+n+']' for n in names)

def definitions():
    history='i[at d][k h257z[v reference v candidate v at]]';before='i[first d last d][k ic[v first v last v candidate]]'
    le=lambda a,b:'x[e[v '+a+'][v '+b+']][k ic[v '+a+' v '+b+' v candidate]]'
    episode=both('k h257z[v reference v candidate v first]','k h257z[v reference v candidate v last]',le('first','last'),le('last','point'),
        'k dg[v activity v first]','k df[v actor v activity v first]','k g3[v activity v beneficiary v goal v last]',
        't[c[s[v goal]][v beneficiary]][v last]')
    text='d r5yf['+FIELDS+'] c['+both('k aa[v actor]','k aa[v beneficiary]','k ta['+history+' '+before+']',
        'k h257z[v reference v candidate v point]','g first d[g last d['+episode+']]')+'].\n'
    same='e[v holder][v beneficiary]'
    text+='d r5yg[holder a beneficiary a goal '+GOAL+' point d] c['+both('k aa[v holder]','k aa[v beneficiary]',
        'x[w['+same+'][k id[v holder v goal v point]]][w[u['+same+']][k h26nt[v holder v beneficiary v goal v point]]]')+'].\n'
    text+='d r5yh['+FIELDS+'] e[b outer[k r5yf['+ARGS+']]].\n'
    named='actor i[a] activity i[a] beneficiary i[a] goal i['+GOAL+'] reference i[d] candidate i[d] point i[d]'
    text+='d r5yi['+named+'] '+CONTENT+'[o a[r d[p r5yh]][v actor v activity v beneficiary v goal v reference v candidate v point]].\n'
    text+='d r5yj['+TAIL+'] h[a] e[i[actor a][k r5yh['+ARGS+']]].\n'
    text+='d r5yk['+named.removeprefix('actor i[a] ')+'] '+ASPECT+'[o a[r b[p r5yj]][v activity v beneficiary v goal v reference v candidate v point]].\n'
    text+='d r5yl['+FIELDS+'] c['+both(*('e[s[k '+('h223h' if n in ('reference','candidate','point') else 'h223g')+'[v '+n+']]][v '+n+']' for n in NAMES))+'].\n'
    code='k r5yi['+name_args(NAMES[:3])+' o r[v goal] '+name_args(NAMES[3:])+']'
    aspect='k r5yk['+name_args(NAMES[1:3])+' o r[v goal] '+name_args(NAMES[3:])+']'
    text+='d r5ym[holder a '+FIELDS+'] c['+both('k r5yl['+ARGS+']','k h26nf[v holder '+code+' v point]')+'].\n'
    text+='d r5yn[holder a '+FIELDS+'] c['+both('k r5yg[v holder v beneficiary v goal v point]','k r5ym[v holder '+ARGS+']',
        'k h26nu[v holder v actor '+aspect+' v point]','k h26nv[v holder v actor '+aspect+' '+code+' v point]')+'].\n'
    settings=TAIL.removesuffix(' point d');sargs=TARGS.removesuffix(' v point')
    text+='d r5yo['+settings+'] h[a a] e[i[holder a actor a][b point[k r5yn[v holder v actor '+sargs+' v point]]]].\n'
    text+='d r5yp['+settings+' audience h[a] c ground '+GOAL+'] h[a a a] e[i[holder a response a actor a][b point['+both(
        't[c[k r5yo['+sargs+']][v holder v actor]][v point]',
        't[c[k r5x5[v audience v ground v reference]][v holder v response v actor]][v point]')+']]].\n'
    return text

def build():
    libs=parents();doc=deepcopy(libs[0].document);doc.update(declarations=[],statements=[]);imported={}
    for lib,roots in zip(libs,(['r5x5','h223g','h223h','h26nf'],['aa','ta','h257z','ic','dg','df','g3','id'])):
        for d in closure(lib.document,roots):
            n=d['name'];e=lib.entries[n]
            if n in imported:assert d==imported[n]['declaration'] and e['meaning_ja']==imported[n]['meaning_ja']
            else:doc['declarations'].append(d);imported[n]=e
    assert not(set(PRIMITIVES)|set(MEANINGS))&set().union(*(set(l.entries) for l in libs))
    doc=parse(format_graph(doc,'compact')+''.join('r '+n+r[0]+'.' for n,r in PRIMITIVES.items())+definitions());ds={d['name']:d for d in doc['declarations']}
    prims={n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=e['arguments'],meaning_ja=e['meaning_ja']) for n,e in imported.items() if e['kind']=='primitive'}
    prims.update({n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=r[1],meaning_ja=r[2]) for n,r in PRIMITIVES.items()})
    paths=set().union(*(set(l.source_sha256) for l in libs))
    basis=dict(status='credited_benefit_valuation_and_grounded_appreciative_attitude',document=LIBRARY,primitives=prims,
        definitions={n:e['meaning_ja'] for n,e in imported.items() if e['kind']=='definition'}|MEANINGS,
        imported_symbols={n:e['meaning_basis'] for n,e in imported.items()},import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)},limitations=LIMITS)
    return {LIBRARY:format_graph(doc,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n'}
