"""Close the same first public release inside both deserved grateful responses."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT,closure
from scripts.compose_qualitative_influence import both
from scripts.compose_qualified_prince_frame import FIELDS as PRINCE,ARGS as PARGS

PARENTS=('data/humanity-release-basis-v1.json','data/world-posterity-basis-v1.json','data/named-epoch-sentence-basis-v1.json')
LIBRARY='examples/v016/release-merit.noema';BASIS='data/release-merit-basis-v1.json'
BENEFIT='i[h[a] e]';GROUND='i b[h[a] e]';MESSAGE='i b[h[a] f]';RESPONSE='i b[h[a a a] e]'
STANDARD='h[a '+RESPONSE+' '+GROUND+'] e';ASSESSMENT='i[h[a d] c]'
NAMES=('activity','government','beforegroup','aftergroup','office','community','reference','candidate','first','acted','last','anchor')
DATES=set(NAMES[6:])
DETAILS=' '.join(n+(' d' if n in DATES else ' a') for n in NAMES)
DARGS=' '.join('v '+n for n in NAMES)
WORLD='currentgroup a postgroup a currentepoch a postepoch a hearers a beneficiary a firststandards j['+STANDARD+'] laststandards j['+STANDARD+']'
WARGS='v currentgroup v postgroup v currentepoch v postepoch v hearers v beneficiary v firststandards v laststandards'
CONCRETE=DETAILS+' assessment '+ASSESSMENT+' '+WORLD
CARGS=DARGS+' v assessment '+WARGS
RELEASE='v actor v activity v government v beforegroup v aftergroup v community v reference v candidate v first v acted v last v office v anchor'
PRIMITIVES={
 'h26n3':('[a a a '+GROUND+' d] c',['speaker','activity','subject','aspect','point'],
    'h26nrと同じ、話者が同じ伝達行為で対象者を指定性質の下で肯定的に評価する立場を自分の表明として示す関係を、段階1の閉じた人物性質へ保つ。報告・他人の評価の引用・反語の距離だけと区別し、内心の真摯さ、功績の真理、受け手の同意は要求しない。記述を実行しない。'),
 'h26n4':('[a a a '+GROUND+' d d] c',['speaker','activity','subject','aspect','reference','point'],
    'h26nsと同じ、表明された肯定的な評価が固定比較基準で通常の単なる肯定を越える高い程度にある関係を、段階1の閉じた人物性質へ保つ。音量、文字数、最大性、他の全対象への優越、数値尺度、内心の感情の強さとは同一視しない。記述を実行しない。'),
}
MEANINGS={
 'r52e':'同じ具体的な前後人口・公的活動・政府・共同体・役職・履歴・前後点・評価関係・基準現在を固定し、r52cの最初の解放を人物別に返す功績性質。外側の評価点が変わっても解放や比較の現在を移さない。',
 'r52f':'r52eの全設定へ閉じた名前と同じ比較評価関数の記述を構文適用する段階1の功績記述。実際の自由・結果生成の判定への依存を保持し、段階0へ落とさない。',
 'r52g':'r5x5と同じ非空の全聴衆への強い肯定的評価表明を、段階1の功績記述に接続する。既存h234gの段階1発話伝達を使い、同じ対象者への功績帰属を伝えるが真理を実行しない。',
 'r52h':'r5ypの同じ恩恵への感謝の態度と称揚を、段階1の功績を受けるr52gへ結ぶ。恩恵の状態記述は段階0のまま保持し、功績記述とは別の役割に置く。',
 'r52i':'r5ytの同じ全成員・生存・時代・現在以降の応答条件にr52hを結ぶ。集団・恩恵・受益者・功績・聴衆・本人を保つ。',
 'r52j':'r52iの全設定を閉じた段階1の応答記述。段階1の功績そのものを引用した値も段階1で保持し、恩恵の記述を上書きしない。',
 'r52k':'r5ywと同じ真の功績と非空の全適合基準を、段階1の功績・応答へ型を保って接続する。功績は実評価するが応答を実行せず、感謝や未来の発話を真にしない。',
 'r52l':'全設定の呼称を照合し、r52jの同じ集団・時代の応答にr52kの値する評価を適用する。真理値が同じ別の功績記述へ基準を移さない。',
 'r52m':'r5yyと同じ現在世界と全後代の範囲について、段階1の同じ功績へのr52lを双方に要求する。一方の基準だけで十分とせず、同じ基準現在で評価する。',
 'r52n':'r52dの同じ最初の解放で利益を受ける個人と、r5zpの同じ政府側の自由を選び、r52fの同じ具体的功績をr52mの両範囲から値する称揚へ渡す。全呼称と比較評価関数を保持し、任意の別の恩恵・功績を外から渡せない。',
 'r52o':'同じ人物・現在点についてr5xvの宗教的判断の到達状態とr52nの具体的功績への両範囲からの称揚適合を連言する。本人・政府・役職・共同体・評価点をずらさない。',
 'r52p':'r5xkの限定された同じ君主の一般条件へ、r52oの能力と具体的な最初の解放への称揚適合を結ぶ。前件と功績で役職・共同体・固定基準を共用し、内側の義務判断・自由政策の実現を前件へ加えない。',
}
LIMITS=[
 'als derjenige以下の功績をr52cの同じ最初の政府側の解放として閉じ、同じ活動と個人への自由の恩恵を、現在世界と後代双方から値する感謝を伴う称揚へ結ぶ。解放時の全人口と、応答する現在・後代の人口は別の時点・役割として保持する。',
 '感謝はその解放で実際に自由を得る一人の受益者への恩恵を認め受け入れる応答として具体化する。応答者が本人と別人でもよく、後代全員が自分自身の解放を直接経験したとは要求しない。この受益者は同じ解放の前後に生存し、前に不自由だった人に制限する。本文では同じ範囲内で選ぶ必要があり、任意の外部人物を足さない。',
 '具体的功績は段階0の自由内容を実評価するため、功績記述の最小段階は1である。既存の段階0功績の称揚・適合定義を変更せず、同じ関係を段階1へ保つ。発話伝達は既存h234gを再利用し、強い肯定的評価の表明についてのみh26nr/nsと同じ規約の段階1関係を追加する。',
 '恩恵の状態は同じr5zpの段階0記述、功績は同じr52fの段階1記述であり、型と内容を混ぜない。応答を閉じるときも同じ二記述を引用し、功績から実際の感謝・発言を導かない。',
 '比較評価はNoemaの閉じた二引数関数記述として渡し、功績の実評価と引用に同じ値を使う。具体的な供給元は本文で固定する。明示的な未評価を先行達成の不在にせず、検査用の常時真を本文の供給元にはしない。',
 '両範囲の全適合基準は非空列として同じ応答・功績・対象者へ適用する。原文に特定の倫理学説を追加せず、基準の内容・全範囲・採用根拠の本文設定はまだ必要である。基準充足の有限例を客観的に正しい功績評価の証明にはしない。',
 '前件と後件の同じ役職・共同体・固定基準を共有するが、規範出所の個人と政府組織は同一化しない。一般条件の全設定の量化と本文束縛、比較評価と基準の供給、wenigstens・sondern等の提示、名称評価の独立した著者帰属、一文全体と後続の判断は残る。本文112主張・v196・17単位判断を保持する。',
]

@lru_cache(None)
def parents():return tuple(load_catalog(ROOT,p) for p in PARENTS)
def sortof(s):return parse('p:r z['+s+'] c.')['declarations'][0]['parameters'][0]
def clone(old,new,parameters,renames):
    d=deepcopy(parents()[1].entries[old]['declaration']);d['name']=new
    for i,s in parameters.items():d['parameters'][i]['sort']=sortof(s)
    def walk(x):
        if old=='r5yw' and x==sortof(BENEFIT):return sortof(GROUND)
        if isinstance(x,list):return [walk(y) for y in x]
        if isinstance(x,dict):return {k:(renames.get(v,v) if k=='symbol' else walk(v)) for k,v in x.items()}
        return x
    d['body']=walk(d['body']);return d
def names():return ['k '+('h223h' if n in DATES else 'h223g')+'[v '+n+']' for n in NAMES]
def definitions():
    text='d r52e['+DETAILS+' assessed h[a d] c] h[a] e[i[actor a][b outer[k r52c['+RELEASE+' v assessed]]]].\n'
    named=' '.join(n+(' i[d]' if n in DATES else ' i[a]') for n in NAMES)
    text+='d r52f['+named+' assessed '+ASSESSMENT+'] '+GROUND+'[o a[r b[p r52e]]['+DARGS+' v assessed]].\n'
    speech='o a[r[p ro7]][v ground]'
    text+='d r52g[audience h[a] c ground '+GROUND+' reference d] h[a a a] e[i[speaker a activity a subject a][b point['+both(
        'k aa[v speaker]','k aa[v subject]','k dg[v activity v point]','k f3[v speaker v activity v point]',
        'g recipient a[c[v audience][v recipient]]','f recipient a[y[c[v audience][v recipient]][k h234g[v activity v recipient v subject '+speech+' v point]]]',
        'k h26n3[v speaker v activity v subject v ground v point]','k h26n4[v speaker v activity v subject v ground v reference v point]')+']]].\n'
    return text
def latter():
    from scripts.compose_world_posterity import NAMES as WN
    scope='group a epoch a hearers a benefaction a beneficiary a reference d candidate d anchor d benefit '+BENEFIT+' ground '+GROUND
    wn=['k '+('h223h' if n in ('reference','candidate','anchor') else 'h223g')+'[v '+n+']' for n in WN]
    valid=both(*('e[s['+c+']][v '+n+']' for n,c in zip(WN,wn)))
    code='k r52j['+' '.join(wn)+' o r[v benefit] o r[v ground]]'
    text='d r52l['+scope+' standards j['+STANDARD+']] h[a] e[i[actor a][b point['+both(valid,'t[k r52k[v actor '+code+' v ground v standards]][v point]')+']]].\n'
    return text
def bound():
    ns=names();ground='k r52f['+' '.join(ns)+' v assessment]'
    benefit='k r5zp['+' '.join('k '+('h223h' if n=='reference' else 'h223g')+'[v '+n+']' for n in ('government','community','reference'))+']'
    valid=both(*('e[s['+c+']][v '+n+']' for n,c in zip(NAMES,ns)))
    merit='t[c[k r52m[v reference v currentgroup v postgroup v currentepoch v postepoch v hearers v activity v beneficiary v candidate v anchor '+benefit+' '+ground+' v firststandards v laststandards]][v actor]][v point]'
    text='d r52n['+CONCRETE+'] h[a] e[i[actor a][b point['+both(valid,'k r52d['+RELEASE+' s[v assessment] v beneficiary]',merit)+']]].\n'
    text+='d r52o[topic a '+CONCRETE+'] h[a] e[i[actor a][b point['+both('t[c[k r5xv[v topic v reference]][v actor]][v point]',
        't[c[k r52n['+CARGS+']][v actor]][v point]')+']]].\n'
    tail=' '.join(n+(' d' if n in DATES else ' a') for n in NAMES if n not in ('office','community','reference'))
    text+='d r52p['+PRINCE+' '+tail+' assessment '+ASSESSMENT+' '+WORLD+'] e[k r5xk['+PARGS+' k r52o[v topic '+CARGS+']]].\n'
    return text
def build():
    libs=parents();doc=deepcopy(libs[0].document);doc.update(declarations=[],statements=[]);imported={}
    roots=(['r52c','r52d','r5zp'],['r5yp','r5yt','r5yu','r5yw','r5yy','r5xv','r5xk','h223g','h223h','ro7'],['h234g','dg','f3','aa'])
    for lib,selected in zip(libs,roots):
        for d in closure(lib.document,selected):
            n=d['name'];e=lib.entries[n]
            if n in imported:assert d==imported[n]['declaration'] and e['meaning_ja']==imported[n]['meaning_ja']
            else:doc['declarations'].append(d);imported[n]=e
    assert not(set(PRIMITIVES)|set(MEANINGS))&set().union(*(set(l.entries) for l in libs))
    doc=parse(format_graph(doc,'compact')+''.join('r '+n+v[0]+'.' for n,v in PRIMITIVES.items())+definitions())
    doc['declarations'] += [clone('r5yp','r52h',{6:GROUND},{'r5x5':'r52g'}),
        clone('r5yt','r52i',{9:GROUND},{'r5yp':'r52h'}),
        clone('r5yu','r52j',{9:'i b['+GROUND+']'},{'r5yt':'r52i'}),
        clone('r5yw','r52k',{2:GROUND,3:'j['+STANDARD+']'}, {})]
    doc=parse(format_graph(doc,'compact')+latter())
    doc['declarations'].append(clone('r5yy','r52m',{11:GROUND,12:'j['+STANDARD+']',13:'j['+STANDARD+']'},{'r5yx':'r52l'}))
    doc=parse(format_graph(doc,'compact')+bound());ds={d['name']:d for d in doc['declarations']}
    prims={n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=e['arguments'],meaning_ja=e['meaning_ja']) for n,e in imported.items() if e['kind']=='primitive'}
    prims.update({n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=r[1],meaning_ja=r[2]) for n,r in PRIMITIVES.items()})
    paths=set().union(*(set(l.source_sha256) for l in libs))
    basis=dict(status='same_first_release_merit_and_both_grateful_responses',document=LIBRARY,primitives=prims,
        definitions={n:e['meaning_ja'] for n,e in imported.items() if e['kind']=='definition'}|MEANINGS,
        imported_symbols={n:e['meaning_basis'] for n,e in imported.items()},import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)},limitations=LIMITS)
    return {LIBRARY:format_graph(doc,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n'}
