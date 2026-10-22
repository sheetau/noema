"""Integrate Kant's ninth sentence, including restriction and figurative contempt."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT,closure
from scripts.compose_qualitative_influence import both
from scripts.compose_protected_remarks import bind

PARENT='examples/v016/kant-fixed-compact-sentence.noema'
PARENT_BASIS='data/fixed-compact-sentence-basis-v1.json'
DEPENDENCIES=('data/limited-personal-deferral-basis-v1.json','data/renunciation-rights-basis-v1.json')
FULL='examples/v016/kant-personal-renunciation-sentence.noema'
CORE='examples/v016/personal-renunciation-sentence-core.noema'
BASIS='data/personal-renunciation-sentence-basis-v1.json'
ANNOTATIONS='data/personal-renunciation-sentence-identifiers-v1.json'
FAMILY='i c[h[j[a] d] e]'
REF='k h26f2[]';CTX='k h255n[]';SOURCE='k h26ax[]';ROLE='k h26fz[]'
THREE_NAMES=('rights','actor','response')
FIVE_NAMES=(*THREE_NAMES,'earlier','posterity')
FOUR_NAMES=('actor','subject','response','period')
seq=lambda names:'l[a]['+' '.join('v '+n for n in names)+']'
THREE=seq(THREE_NAMES);FIVE=seq(FIVE_NAMES);FOUR=seq(FOUR_NAMES)
TWO='l[a][v actor v response]';POST='l[a][v actor v response v earlier v posterity]'
NODE_INFO={
 'h26gd':([2678,2985],'第九文全体。本人の一時延期の許容と、本人・後世についての放棄への権利評価。'),
 'h26ge':([2678,2815],'Ein Menschからaufschiebenまでの本人の限定された延期。'),
 'h26gf':([2816,2985],'aberから文末までの本人・後代の放棄への評価。'),
 'h26gg':([2694,2698],'zwarによる前半の限定付きの承認。'),
 'h26gh':([2717,2753],'und auch alsdann nur auf einige Zeitという、その場合にも必要な期間限定の取り立て。'),
 'h26gi':([2816,2820],'aberによる延期と放棄の対照。'),
 'h26gj':([2847,2871],'es sei für seine Personという本人についての場合。'),
 'h26gk':([2887,2911],'für die Nachkommenschaftという後代についての場合。'),
 'h26gl':([2872,2886],'mehr aber nochによる本人の場合から後代の場合への対照と増幅。'),
 'h26gm':([2913,2918],'heißtによる同じ放棄への評価的な性格づけ。'),
 'h26gn':([2968,2984],'mit Füßen tretenという同じ権利を足で踏みつける姿への見立て。'),
}
PRIMITIVES={
 'h26f6':('[a a d] c',['person','foot','reference'],'固定基準で、この部位は同じ人の身体の足に当たり、地面等に接して身体を支える末端部分である。他者の足・道具・比喩的な足場と区別する。行為の実行や足の損傷は別である。'),
 'h26f7':('[a a a d d] c',['activity','foot','object','reference','point'],'同じ行為・点で、指定した足の底面を同じ対象に上から押し当て、体重又は踏み込む力を加えるという身体動作の構成。足の所有者と行為主体は別に結ぶ。単なる近接・手で触れること・対象の破壊や規範的な軽視そのものと同一視しない。'),
 'h26ga':('[a a i d[e] '+FAMILY+' '+FAMILY+' '+FAMILY+' d d] c',['node','author','whole','scope','permission','qualification','reference','context'],'著者が同じ全体・箇所・対象範囲の下で、指定した許容を認める場合にも指定条件を必要な限定として取り立てる提示。同じ対象列・固定基準を三内容族へ渡す。限定条件から許容を逆に導かず、その場合にもという留保を保つ。引用内容の現実の真理は実行しない。'),
 'h26gb':('[a a i d[e] i d[e] i d[e] d] c',['node','author','whole','admitted','counterpart','context'],'著者が同じ全体の中で第一内容を認めつつ、後続の対照内容をなお保持するための譲歩的な承認として第一を提示する。第一の撤回や反語、両内容の論理的矛盾、読者の実際の期待や引用内容の実行は要求しない。'),
 'h26gc':('[a a i d[e] '+FAMILY+' '+FAMILY+' '+FAMILY+' d d] c',['node','author','whole','scope','conduct','appraisal','reference','context'],'著者が同じ全体・範囲の下で、同じ対象列・固定基準の行為を、指定された評価に当たるものとして性格づける提示。単なる共起や原因結果、語の綴りの同一性ではなく、その行為が何に当たるかという評価的な説明。逆向きの全同値や現実の行為実行を補わない。'),
}
PRIMITIVES.update({n:('[] a',[],'固定原文kant-1784:u0013['+str(span[0])+','+str(span[1])+')の'+meaning) for n,(span,meaning) in NODE_INFO.items()})
MEANINGS={
 'r5lp':'正確な権利・主体・応答・先行時代・後代集団の五対象列について、同じ権利r5ll、全後代と義務事項r5lc、同じ本人/後代の二つの全候補指定を共通に保つ比較範囲。実際の放棄や侵害評価を範囲の条件にしない。',
 'r5lq':'正確な権利・主体・応答の三対象列から、同じ本人の放棄へのr5lmの二評価を返す。固定基準は全文と同じh26f2。',
 'r5lr':'正確な五対象列から、同じ後代についての放棄へのr5lnの二評価を返す。',
 'r5ls':'正確な三対象列から、同じ主体が同じ応答行為を固定選択点で行い、自身の身体の足で同じ権利対象へ上から力を加えるという字義的な描写を返す。見立ての引用側にのみ置く。',
 'r5lt':'正確な三対象列から、同じ本人の同じ放棄r5liを同じ権利への不遜な軽視h26bvとして評価する内容。足の描写との対応対象にする。',
 'r5lu':'正確な五対象列から、同じ後代の放棄r5ljについて同じh26bvの評価を返す。',
 'r5lv':'正確な三対象列の同じ権利と本人の全義務事項・有効な履歴・固定選択点・全仮定候補を保つ、本人の場合の範囲。後代集団の存在を本人の場合の必要条件に追加しない。',
 'r5lw':'正確な五対象列について同じ権利、全後代と義務事項、後代についての同じ全仮定候補を保つ範囲。',
 'r5lx':'同じ五対象列の先頭三対象をr5lsへ射影する。後代の場合も、踏む主体は現在の選択主体、踏まれる対象は同じ権利であり、後代の人々を踏む描写に替えない。',
 'r5ly':'前半と同じ主体・対象本人・応答・期間の正確な四対象列から、本人自身・有界・再開方針r5k3という必要条件を返す。',
 'r5lz':'同じ四対象列から、同じ規範・立場の積極的で衝突のない許容r5k2を返す。',
 'r5l2':'同じ四対象列の全仮定枠r5kwで中断選択r5kzがなされる場合の範囲。許容や必要な限定を先に範囲条件へ追加しない。r5k7と同じ必要限定の提示に用いる。',
 'r5l3':'本人の限定された延期の一般的可能性と必要条件r5la、本人・後代の放棄と同じ権利への条件付き評価r5loを結ぶ第九文の中心内容。字義的な踏みつけや現実の放棄を連言しない。',
 'r5l4':'同じ人であるという共通観点を内容として返す。前半の本人の選択と後半の本人/後代に関する選択の対照に用いる。',
 'r5l5':'比較の五対象列の先頭三対象を本人の場合の評価r5lqへ射影する。後代の場合r5lrと同じ権利・主体・応答を共有する。',
 'r5l6':'本人の場合の三対象列から同じ主体・応答をr5lgへ射影する。評価の保護対象である権利は同じ列に保持する。',
 'r5l7':'後代の場合の五対象列から同じ主体・応答・先行時代・後代をr5lhへ射影する。',
 'r5ma':'第九文の全体・前半・後半を同じ著者と段落文脈へ帰属し、譲歩的承認、本人の場合にも残る必要限定、延期と放棄の対照、後代の場合の増幅、評価的性格づけ、両場合の同じ権利への踏みつけの見立てを結ぶ。引用内容を現実として実行しない。',
}
LIMITS=[
 'u0013第九文[2678,2985)の256非空白文字を対象とする。Ein Menschは一般の人として読む。kannは本人について一つ以上の許容される延期構成が可能という規範的な読みで、全ての有限期間への一括許可や現実の延期を加えない。',
 'für seine Personとauch alsdann nur auf einige Zeitは、本人自身の場合にも有界な期間と後に続ける方針を必要とする限定。一定の数値上限を補わない。知るべき事項と本人の営みはpersonal-enlightenment-choice、許容の全候補と必要条件はlimited-personal-deferralの明示読解を保持する。',
 'aufschiebenとVerzichtは、本人が同じ応答に採用する実践的方針を区別する。延期では期間内の不継続と後の再開、放棄では全未来の継続への拒否を保持し、単なる未達成・不能・忘却や実際の永久的不成功へ置換しない。auf sieは同じ啓蒙の営みを受ける。',
 'es sei für seine Person, mehr aber noch für die Nachkommenschaftは、本人についても後代についても同じ権利評価が当たり、後代の場合をさらに強く取り立てる読み。二場合を排他的にせず、後代を本人の血縁や直後の世代へ限定しない。程度差の数値や全員の個別被害は追加しない。',
 'heiligen Rechte der Menschheitはrenunciation-rightsの、通時的人類の啓蒙を追求する条件・機会への全関連請求と、その侵してはならない尊重を保持する。本人の都合による正当な権利消滅、神による授与、現代の全人権一覧を追加しない。',
 'heißtは放棄に同じ侵害と不遜な軽視の評価を与える性格づけであり、すべての侵害から放棄へ逆推論しない。mit Füßen tretenはその軽視を、同じ選択主体が自分の足で同じ権利対象を踏む姿に見立てる。描写の真理や権利の物理的実在、実際の破壊を中心命題へ加えない。',
 'zwarは前半を認める譲歩的な提示、aberは後半との対照と読む。前半の撤回や両内容の矛盾にはしない。mehr aber nochの対照・増幅は、同じ権利・主体・応答を共有する本人/後代の評価へ結ぶ。',
 '全語句との対応と通読は明示読解の下でのアシスタントの判断であり、有限検査からの自動同値証明、独立査読、唯一の歴史解釈ではない。第六段落の残部と二作品全体は未完である。',
]
NODES=('h26fi',*NODE_INFO)
@lru_cache(None)
def parent():return load_catalog(ROOT,PARENT_BASIS)
@lru_cache(None)
def dependencies():return tuple(load_catalog(ROOT,p) for p in DEPENDENCIES)

def definitions():
    refmatch='e[v reference]['+REF+']';rights='k r5ll[v rights]'
    selfcandidate='k h26f3[r[p r5lg] '+TWO+' v reference v candidate]'
    postcandidate='k h26f3[r[p r5lh] '+POST+' v reference v candidate]'
    postframe='k r5lc[v actor v response v earlier v posterity v reference v candidate]'
    anchor='k h26fw[v response v reference]'
    selfscope=both(refmatch,rights,'k aa[v actor]','k r5kn['+SOURCE+' v actor '+ROLE+' v reference]',
        'k ta[i[at d][k h257z[v reference v candidate v at]] i[first d last d][k ic[v first v last v candidate]]]',
        'k h257z[v reference v candidate '+anchor+']',selfcandidate)
    def emit(n,names,body):return 'd '+n+'[bindings j[a] reference d] e[b candidate['+bind(names,body)+']].\n'
    text=emit('r5lp',FIVE_NAMES,both(selfscope,postframe,postcandidate))
    text+=emit('r5lq',THREE_NAMES,both(refmatch,'k r5lm[v rights v actor v response v candidate]'))
    text+=emit('r5lr',FIVE_NAMES,both(refmatch,'k r5ln[v rights v actor v response v earlier v posterity v candidate]'))
    literal=both('t[k zzq[v actor v response]]['+anchor+']','g foot a['+both('k h26f6[v actor v foot v reference]',
        'k h26f7[v response v foot v rights v reference '+anchor+']')+']')
    text+=emit('r5ls',THREE_NAMES,literal)
    for n,names,target,bindings in (('r5lt',THREE_NAMES,'r5li',TWO),('r5lu',FIVE_NAMES,'r5lj',POST)):
        text+=emit(n,names,both(refmatch,'k h26bv['+SOURCE+' v rights v actor '+ROLE+' r[p '+target+'] '+bindings+' v reference v candidate]'))
    text+=emit('r5lv',THREE_NAMES,selfscope)
    text+=emit('r5lw',FIVE_NAMES,both(refmatch,rights,postframe,postcandidate))
    text+=emit('r5lx',FIVE_NAMES,'t[k r5ls['+THREE+' v reference]][v candidate]')
    args='v actor v subject v response v period v reference v candidate'
    for n,target in (('r5ly','r5k3'),('r5lz','r5k2')):text+=emit(n,FOUR_NAMES,'k '+target+'['+args+']')
    text+=emit('r5l2',FOUR_NAMES,both('k r5kw['+args+']','t[k r5kz['+FOUR+' v reference]][v candidate]'))
    text+='d r5l3[] e[b point['+both('t[k r5la[]][v point]','t[k r5lo[]][v point]')+']].\n'
    text+='d r5l4[person a] e[b point[k aa[v person]]].\n'
    text+=emit('r5l5',FIVE_NAMES,'t[k r5lq['+THREE+' v reference]][v candidate]')
    text+=emit('r5l6',THREE_NAMES,'t[k r5lg['+TWO+' v reference]][v candidate]')
    text+=emit('r5l7',FIVE_NAMES,'t[k r5lh['+POST+' v reference]][v candidate]')
    author='k wa[]';whole='r d[k r5l3[]]';q=lambda n:'r c[p '+n+']'
    clauses=['k h236i[k '+node+'[] '+author+' r d[k '+target+'[]] '+CTX+']' for node,target in (('h26gd','r5l3'),('h26ge','r5la'),('h26gf','r5lo'))]
    clauses+=['k h26gb[k h26gg[] '+author+' '+whole+' r d[k r5la[]] r d[k r5lo[]] '+CTX+']',
        'k h26ga[k h26gh[] '+author+' '+whole+' '+q('r5l2')+' '+q('r5lz')+' '+q('r5ly')+' '+REF+' '+CTX+']',
        'k h222q[k h26gi[] '+author+' k h26ge[] r b[k r5la[]] k h26gf[] r b[k r5lo[]] r[p r5l4] '+CTX+']']
    for relation in ('h26fe','h26fd'):
        clauses+=['k '+relation+'[k h26gl[] '+author+' '+whole+' '+q('r5lp')+' '+q('r5l5')+' '+q('r5lr')+' '+REF+' '+CTX+']']
    for scope,conduct,appraisal,described,depiction in (('r5lv','r5l6','r5lq','r5lt','r5ls'),('r5lw','r5l7','r5lr','r5lu','r5lx')):
        clauses+=['k h26gc[k h26gm[] '+author+' '+whole+' '+q(scope)+' '+q(conduct)+' '+q(appraisal)+' '+REF+' '+CTX+']',
            'k h26fc[k h26gn[] '+author+' '+whole+' '+q(scope)+' '+q(described)+' '+q(depiction)+' '+REF+' '+CTX+']']
    edges=(('h26fi','h26gd'),('h26gg','h26gh'),('h26ge','h26gf'),('h26gi','h26gj'),('h26gj','h26gl'),('h26gl','h26gk'),('h26gk','h26gm'),('h26gm','h26gn'))
    clauses+=['k ue[k '+a+'[] k '+b+'[] '+CTX+']' for a,b in edges]
    distinct=['u[e[k '+a+'[]][k '+b+'[]]]' for i,a in enumerate(NODES) for b in NODES[i+1:]]
    clauses += [both(*distinct[i:i+12]) for i in range(0,len(distinct),12)]
    text+='d r5ma[] c['+both(*clauses)+'].\n'
    return text

def build():
    old=parent();doc=deepcopy(old.document);statements,doc['statements']=doc['statements'],[];imported={}
    for lib in dependencies():
        for d in lib.document['declarations']:
            n=d['name'];previous=old.entries.get(n,imported.get(n))
            if previous:assert d==previous['declaration'] and lib.entries[n]['meaning_ja']==previous['meaning_ja'],n
            else:doc['declarations'].append(d);imported[n]=lib.entries[n]
    assert not (set(PRIMITIVES)|set(MEANINGS))&(set(old.entries)|set(imported))
    doc=parse(format_graph(doc,'compact')+''.join('r '+n+v[0]+'.' for n,v in PRIMITIVES.items())+definitions());added=doc['declarations'][len(old.document['declarations']):]
    new=dict(kind='assert',body=dict(kind='call',symbol='r5ma',arguments=[]));doc['statements']=statements+[new]
    core=deepcopy(doc);core.update(declarations=closure(doc,list(MEANINGS)),statements=[new]);ds={d['name']:d for d in added}
    prims={n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=e['arguments'],meaning_ja=e['meaning_ja']) for n,e in imported.items() if e['kind']=='primitive'}
    prims.update({n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=v[1],meaning_ja=v[2]) for n,v in PRIMITIVES.items()})
    paths=set().union(*(set(lib.source_sha256) for lib in dependencies()))
    basis=dict(status='personal_renunciation_sentence_under_explicit_reading',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,
        definitions={n:e['meaning_ja'] for n,e in imported.items() if e['kind']=='definition'}|MEANINGS,primitives=prims,
        new_signatures={d['name']:{k:d[k] for k in ('parameters','result')} for d in added},imported_symbols={n:e['meaning_basis'] for n,e in imported.items()},
        import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';annotations=json.loads((ROOT/'data/fixed-compact-sentence-identifiers-v1.json').read_text(encoding='utf-8'))
    annotations.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(annotations)}
