"""Bind generic human departure to noninterference in the same prospective course."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT,closure
from scripts.compose_qualitative_influence import both

PARENT='examples/v016/kant-manifest-example-sentence.noema'
PARENT_BASIS='data/manifest-example-sentence-basis-v1.json'
DEPENDENCIES=('data/noninterference-interval-basis-v1.json','data/gradual-self-departure-basis-v1.json')
FULL='examples/v016/kant-self-departure-sentence.noema';CORE='examples/v016/self-departure-sentence-core.noema'
BASIS='data/self-departure-sentence-basis-v1.json';ANNOTATIONS='data/self-departure-sentence-identifiers-v1.json'
REF='k h26pp[]';GROUP='k h26ru[]';CTX='k h26rz[]'
TIME='history h[d] c before h[d d] c first d'
FRAME='group a person a reference d '+TIME
ARGS='v group v person v reference v history v before v first'
SCOPED='group a person a candidate a reference d'
SARGS='v group v person v candidate v reference'
FUNCTION='h[a a d h[d] c h[d d] c d] c'
PROVIDERS={'history':('h26rw','i[h[d] c]'),'before':('h26rx','i[h[d d] c]'),'first':('h26ry','i[d]')}
PRIMITIVES={
 'h26ru':('[] a',[],
   '第五文のDie Menschenが一般的に扱う人々の範囲を表す集団。先行する特定の政府・聖職者・獲得者だけに限らず、文脈内の人々を含む。実際に離脱した者又は妨害されない者だけで事後選別しない。成員はh246cで固定基準に結び、非空性と人であることは合成側で要求する。'),
 'h26rv':('[a a a d] c',['group','person','candidate','reference'],
   '同じ対象範囲の本人と固定基準について、一般的な成長の条件文を評価する全関連の将来経過の一つである。本人ごとの開始点、そこからの経過全体と順序を指定し、現在の一つの実在経過へ限定しない。成功、妨害の不在、目的の採用、形成度の高さによって候補を選別せず、失敗や妨害を含む経過も残す。開始点は成功点から逆算せず、成長を考察する文脈により固定する。対象の全関連経過を含むことは明示した解釈入力で、全論理的可能世界や有限試験の列挙と同一視しない。'),
 'h26rz':('[] d',[],'固定原文kant-1784:u0015第五文の著者の論述文脈。内容の固定基準h26ppとは役割を分ける。'),
 'h26r2':('[a a i b[e] i b['+FUNCTION+'] i b['+FUNCTION+'] d] c',
   ['node','author','whole','condition','result','context'],
   '著者が同じ全体の条件文で、指定条件だけで指定結果への十分な条件になるという最小の要求として取り立てる。両関数記述は同じ集団・本人・固定基準・履歴・順序・開始点の束縛を共有する。nurを条件の限定とする談話関係で、条件の必要性、条件以外の全原因の不在、結果の無条件の成立を意味しない。条件から結果への含意そのものは全体内で別に構成し、帰属時に引用を実行しない。'),
 'h26r3':('[] a',[],'固定原文kant-1784:u0015[1210,1354)第五文全体の文章箇所。'),
 'h26r4':('[] a',[],'固定原文kant-1784:u0015の第五文内wenn man nur nichtから始まる条件節の文章箇所。'),
}
for role,(n,t) in PROVIDERS.items():
    PRIMITIVES[n]=('[a a a d] '+t,['group','person','candidate','reference'],
        '同じ集団・本人・候補経過・固定基準に属する'+role+'の閉じた記述。開始からの将来の経過全体を指定し、達成点や妨害点の前で都合よく切り詰めない。終点の締切は供給しない。各人・各候補は異なる履歴や開始点を持てる。候補選択の完全性とコードの妥当性は、条件の真偽・達成と別に扱う。')
MEANINGS={
 'r6ba':'開始点を最小点として含み、それより後の点が少なくとも一つある厳密な全順序履歴。未来の長さ、全員共通の締切、達成の既成事実は要求しない。',
 'r6bb':'同じ集団・基準・全将来履歴の全点、全成員、全行為者・活動にr6a6の完全で始点の一致する保持目的設定を要求する。欠落を妨害なしという条件の不成立へ変えて条件文を空虚に満たさないよう、本文ではこの妥当性を含意の外に置く。',
 'r6bc':'同じ集団・基準・全将来履歴のどの点にも、その成員を未陶冶に保持する意図的操作r6a5がない。本人・順序・開始点も共通引数として保持する。政府だけ、成功した操作だけ、都合のよい短期間だけに狭めない。',
 'r6bd':'同じ本人・基準・履歴・順序・開始点から、ある後の点と本人の過程が存在し、r6a4の自己からの漸進的離脱を満たす。到達点は後件の内側で存在量化し、全員の同時完了や事前の共通締切を補わない。',
 'r6be':'同じ六引数の履歴妥当性r6baと入力完全性r6bbを保ち、開始点で未陶冶である本人について、同じ全経過の非介入r6bcなら同じ本人の将来的離脱r6bdという一方向の含意を構成する。既にその状態を離れた人に逆戻りを要求しない。',
 'r6bf':'集団・本人・候補・基準を三つの記述供給へ共通に渡し、得た履歴・順序・開始点を一組としてr6beへ結ぶ。条件側と結果側で別の経過や別人の成功を借りない。',
 'r6bg':'非空の人間集団について各成員の候補経過が非空であり、全ての同じ候補でr6bfを要求する一般的条件内容。現に全員が離脱したことではなく、採用した将来的な読みでの全関連経過を扱う。',
 'r6bh':'第五文の集団と固定基準を閉じてr6bgへ渡す。外側の評価点を変えて参照基準や各人の開始点を変更しない。',
 'r6bi':'同じ第五文全文を著者に帰属し、nurによる非介入条件の最小要求としての限定と本文の先後、箇所の区別を結ぶ。引用された条件・結果の真理を著者帰属のために実行しない。',
}
LIMITS=[
 '固定原文u0015第五文[1210,1354)の121非空白文字を扱う。Die Menschenを文脈内の人々一般とし、特定の政府の成員や聖職者だけに限定しない。開始時に未陶冶である人の将来の成長についての一般的条件文として読む。既に離れた人を再び未陶冶に戻す主張にはしない。',
 'wennは、全関連の候補経過で非介入なら同じ本人の離脱過程があるという十分条件。必要条件・双条件・現在の全員の達成へ強めない。nurはこの条件だけを要求する提示であり、教育や助力、本人の努力など全ての他の原因を排除しない。',
 '全経過の持続的な非介入を前件とし、後件に到達点を存在量化する将来的な読み。任意の短い非介入期間内に必ず完了するとはしない。全員共通の開始・締切はない。妨害が後に始まる経過について、その以前の短期間だけで離脱を保証する主張にもならない。',
 '対象と候補の範囲、開始点と全将来の履歴は独立の解釈入力であり、成功や非介入の真偽で選別しない。十分な長さを成功で定義する補助条件も置かない。仮に短命等の失敗経過が関連範囲内に含まれれば、非介入でも離脱がなく、この著者内容は偽になり得る。その真理の実証を翻訳の完成条件にしない。',
 '保持操作は全行為者・全活動・全成員・経過の全点・全保持目的設定にわたる。manは特定の一人や政府に固定しない。absichtlichは選択・統御された関与、künstelnは状態を維持する条件への作為的操作、umは同じ対象の保持を目指す目的。失敗した操作も介入に数え、未来の保持成功は目的採用時に実行しない。',
 'sieは同じ人々、darinは同じ未陶冶の状態。Rohigkeitは思考・判断習慣の未陶冶として明示し、未成熟bfや民族的劣等、全人格の悪、恒久的本性に替えない。arbeiten sichは本人の精神的自己形成とその本人への結果生成、von selbstは本人からの働きかけ、nach und nachは質的な小段階を通る進行。途中の後退や停滞、教育・助言を排除しない。',
 '入力完全性と順序の妥当性は含意の外に置く。空の候補、欠けた目的設定、別の開始点、未知を条件の否定へ補って全文を成立させない。有限対照例は入力の現実の網羅性や原文との自動同義を証明しない。',
 '先行四文1033文字の判断と17全単位判断を保存する。第五文の全文判断は明示解釈に基づくアシスタントの通読判断であり、段落全体の判断・独立査読・二作品の完成ではない。原刊照合は訂正済みv2を用いる。',
]
@lru_cache(None)
def parent():return load_catalog(ROOT,PARENT_BASIS)
@lru_cache(None)
def dependencies():return tuple(load_catalog(ROOT,p) for p in DEPENDENCIES)
def definitions():
    text='d r6ba['+TIME+'] c['+both('k ta[v history v before]','c[v history][v first]',
        'g later d['+both('c[v history][v later]','c[v before][v first v later]')+']',
        'f point d[y[c[v history][v point]][x[e[v point][v first]][c[v before][v first v point]]]]')+'].\n'
    complete='f actor a[f activity a[f target a[f point d[y['+both('k h246c[v group v target v reference]','c[v history][v point]')+'][k r6a6[v actor v activity v target v reference v point]]]]]]'
    text+='d r6bb['+FRAME+'] c['+complete+'].\n'
    interference='i[actor a activity a target a][g point d['+both('c[v history][v point]','k r6a5[v actor v activity v target v reference v point]')+']]'
    text+='d r6bc['+FRAME+'] c[k r6av[v group v reference '+interference+']].\n'
    result='g process a[g last d['+both('c[v history][v last]','c[v before][v first v last]',
        'k r6a4[v person v process v reference v history v before v first v last]')+']]'
    text+='d r6bd['+FRAME+'] c['+result+'].\n'
    text+='d r6be['+FRAME+'] c['+both('k r6ba[v history v before v first]','k r6bb['+ARGS+']',
        'y[t[c[k r6ap[v reference]][v person]][v first]][y[k r6bc['+ARGS+']][k r6bd['+ARGS+']]]')+'].\n'
    delivered=' '.join('s[k '+n+'['+SARGS+']]' for n,t in PROVIDERS.values())
    text+='d r6bf['+SCOPED+'] c[k r6be[v group v person v reference '+delivered+']].\n'
    scope='k h26rv['+SARGS+']'
    cases=both('g candidate a['+scope+']','f candidate a[y['+scope+'][k r6bf['+SARGS+']]]')
    text+='d r6bg[group a reference d] e[b outer['+both('k r5ty[v group v reference]',
        'f person a[y[k h246c[v group v person v reference]]['+cases+']]')+']].\n'
    text+='d r6bh[] e[k r6bg['+GROUP+' '+REF+']].\n'
    parts=['k hzon[k h26r3[] k wa[] r b[k r6bh[]] '+CTX+']',
        'k h26r2[k h26r4[] k wa[] r b[k r6bh[]] r b[p r6bc] r b[p r6bd] '+CTX+']',
        'k ue[k h26ra[] k h26r3[] '+CTX+']','k ue[k h26r3[] k h26r4[] '+CTX+']']
    nodes=('h26ra','h26r3','h26r4')
    parts+=['u[e[k '+a+'[]][k '+b+'[]]]' for i,a in enumerate(nodes) for b in nodes[i+1:]]
    return text+'d r6bi[] c['+both(*parts)+'].\n'
def build():
    old=parent();doc=deepcopy(old.document);statements,doc['statements']=doc['statements'],[];imported={}
    for lib,roots in zip(dependencies(),(('r6a5','r6a6','r6av'),('r6a4','ta'))):
        for d in closure(lib.document,roots):
            n=d['name'];e=lib.entries[n]
            if n in old.entries:assert d==old.entries[n]['declaration'] and e['meaning_ja']==old.entries[n]['meaning_ja']
            elif n in imported:assert d==imported[n]['declaration'] and e['meaning_ja']==imported[n]['meaning_ja']
            else:doc['declarations'].append(d);imported[n]=e
    assert not(set(MEANINGS)|set(PRIMITIVES))&(set(old.entries)|set(imported))
    doc=parse(format_graph(doc,'compact')+''.join('r '+n+r[0]+'.' for n,r in PRIMITIVES.items())+definitions())
    added=doc['declarations'][len(old.document['declarations']):];ds={d['name']:d for d in added}
    new=dict(kind='assert',body=dict(kind='call',symbol='r6bi',arguments=[]));doc['statements']=statements+[new]
    core=deepcopy(doc);core.update(declarations=closure(doc,['r6bi']),statements=[new])
    prims={n:dict(parameters=e['declaration']['parameters'],result=e['declaration']['result'],arguments=e['arguments'],meaning_ja=e['meaning_ja']) for n,e in imported.items() if e['kind']=='primitive'}
    prims.update({n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=r[1],meaning_ja=r[2]) for n,r in PRIMITIVES.items()})
    paths=set().union(*(set(lib.source_sha256) for lib in dependencies()))
    basis=dict(status='self_departure_sentence_under_explicit_reading',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,
        definitions={n:e['meaning_ja'] for n,e in imported.items() if e['kind']=='definition'}|MEANINGS,primitives=prims,
        new_signatures={d['name']:{k:d[k] for k in ('parameters','result')} for d in added},imported_symbols={n:e['meaning_basis'] for n,e in imported.items()},
        import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';annotations=json.loads((ROOT/'data/manifest-example-sentence-identifiers-v1.json').read_text(encoding='utf-8'))
    annotations.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(annotations)}
