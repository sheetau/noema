"""Keep the actual claim fixed while comparing corresponding progress scenarios."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT,closure
from scripts.compose_qualitative_influence import both
from scripts.compose_situated_criticism import params,args

PARENTS=('data/departure-hindrance-trend-basis-v1.json','data/religious-collective-assessment-basis-v1.json','data/royal-intervention-sentence-basis-v1.json')
LIBRARY='examples/v016/progress-indications.noema';BASIS='data/progress-indications-basis-v1.json'
FIELDS=[('speaker','a'),('group','a'),('epoch','a'),('reference','d'),('topic','a'),
 ('candidates','h[d] d'),('points','h[d] d'),('firsts','h[d] d'),('processes','h[d a a] a'),
 ('obstacles','j[a]'),('scope','h[a] c'),('bound','b'),('variables','h[a] j[a]'),
 ('equations','h[a d] h[a h[a] c] c'),('factors','h[a] a'),('worlds','h[a d h[a] c] d'),
 ('matches','h[a d h[a] c h[a] c] c'),('frames','h[d] a')]
NAMES=[(n+'name','i['+t+']') for n,t in FIELDS]
NARGS=' '.join('v '+n for n,_ in NAMES)
FCODE='i c[h[d] e]';ACODE='i c[h[d] c]';TCODE='i d[e]'
SCORE=[('cases','j[d]'),('selected','h[d] c'),('weight','h[d] b'),('threshold','b'),
 ('classified','h[a d] c'),('contents','h[a] e'),('linked','h[a '+TCODE+' d] c'),('accessible','h[a a d] c')]
ITEM=[('family',FCODE),('actualname','i[d]'),('observer','a'),('context','d'),('item','a')]+SCORE
MULTIPLE=[(n,t) for n,t in ITEM if n!='item']
SOURCE=NAMES+[('actualname','i[d]')]+SCORE
PRIMITIVES={}
MEANINGS={
 'r5uk':'同じ人口・宗教主題・基準と比較規則を保ち、候補別の現在・開始点・過程で進行内容を評価できる条件を返す。各比較例の現在人口枠r5sc、全取り組み候補の両端評価、固定障害候補の全区間評価rl2、正の段階上限を確認する。評価不足を進行なしの例へ混ぜない。',
 'r5ul':'同じ設定から比較例別のr5uj進行内容を返す。比較例ごとに対応する候補履歴・現在・開始点・過程を使うが、人口・宗教主題・基準・候補範囲・モデルの選択規則を保つ。各例の内容自身はその例の現在を固定する。',
 'r5um':'閉じた引数記述からr5ulの同じ比較例別進行族を段階2の閉じたNoema記述として構成する。原語や不透明な文番号を内容の代用にしない。',
 'r5un':'r5umと同じ引数記述からr5ukの比較例別の評価条件を閉じた記述として構成する。比較の真偽を確認する前に同じ入力の有効性を調べる。',
 'r5uo':'指定した同じ進行族の実際の比較例を選び、その例の現在を固定した内容を返す。外側の評価点を替えて別の比較例へ移さない。',
 'r5up':'同じ進行族と実際の例の参照からr5uoの閉じた対象記述を構成する。徴候のdavonの指示対象はこの同じ記述で固定する。',
 'r5uq':'同じ進行族について、比較例ごとの閉じた内容をその例で評価する診断用の仮説内容。r5uoの実際の固定内容を全比較例に繰り返して真偽の両群を失う誤接続を避ける。',
 'r5ur':'同じ観察主体が現在利用でき、同じr5up対象へ結ばれ、実際の例で内容が成立する項目が、同じ全比較範囲でrmbの識別力基準を満たす。実際の例も比較範囲に含める。対象の現在の真理や主体の肯定判断は追加しない。',
 'r5us':'同じ設定で異なる二項目がそれぞれr5urを満たす。複数の徴候であり、独立性や情報量の加算を要求しない。',
 'r5ut':'同じr5ulの進行族に全比較例のr5uk評価を要求し、実際の例に対応する同じ話者・現在点でr5usの複数の徴候を構成する。人類全員が徴候を認識するとはしない。',
 'r5uu':'r5utの同じ実際の例・主体・現在・対象への徴候の存在を、外側の評価点に依存しない内容として閉じる。進行そのものの事実と、進行を示す徴候があることを別に保つ。',
 'r5uv':'同じ実際の例の話者・人口・時代・現在と宗教的事項について、r5tmの既に啓蒙された時代かという問いを返す。比較例ごとに実際の問いの時点を替えない。',
 'r5uw':'r5uvと同じ設定で、r5tnの未到達だが進行中という回答へ同じr5uo進行内容を渡す。徴候から進行の真理を導くのではなく、回答の主張内容として進行を明示する。',
}
LIMITS=[
 'u0014第三文davon haben wir doch deutliche Anzeigenの内容核と、第一文の問い・回答内容への同一設定の接続。deutlicheは、固定された比較モデルで対象が成り立つ例の方に十分偏って現れる、識別力を持つ徴候という読みを採る。原文が確率や数値係数を指定したとはしない。',
 'rmbの同じ全比較例・正の重み・真偽両側の正の量と1超の文脈係数を再利用する。実測頻度、事後確率、演繹的な保証、絶対的無謬性、独立な証拠の加算へ替えない。比較例・重み・係数・対応の規則は結果を見る前に固定する。',
 '比較例は同じ人口・主題・基準に関する代替的な状況の指標であり、現実の過去・未来の時刻列そのものではない。候補・現在・開始点・過程の対応を明示し、実際の現在を比較例の一つへ位置付ける。各例の両端・全候補の評価を確認し、評価不足を偽群へ数えない。',
 '実際の進行内容はr5uoで固定し、比較用にはr5uqで同じ族の各例を評価する。この二つを取り違えると固定内容に真偽の両群を作れなくなる。対象の引用、比較用の真偽、現にある徴候を区別する。',
 '徴候の内容はcontentsでNoemaの命題として明示し、linkedは同じ閉じた対象記述との証拠上の対応とする。accessibleは同じ観察主体の利用可能性であり、信念・因果・真理を含めない。分類は項目と仮説の全関連入力が既知であることを要求し、未知を偽で補わない。',
 'wirを著者を含む同じ話者側が利用できる徴候として読む。全人類の実際の認識、全読者の同意、特定の徴候一覧を原文へ補わない。二項目以上という複数性を採るが、相関した別項目の情報量を二倍としない。',
 '第一文は同じr5tm/tnへ具体的な進行内容を渡した段階。Wenn gefragt wird、denn/nun、Nein/aber wohl、著者帰属はまだ未統合。第三文の場の比喩、現在進行・doch・Allein、oderの説明的言い換えの提示も残る。これらを含む一文全体の判断は追加しない。',
]
@lru_cache(None)
def parents():return tuple(load_catalog(ROOT,p) for p in PARENTS)

def actual_fields(case='v case',named=False):
    val={n:('s[v '+n+'name]' if named else 'v '+n) for n,_ in FIELDS}
    return val|{n:'c['+val[f]+']['+case+']' for n,f in (('candidate','candidates'),('point','points'),('first','firsts'))}|{
        'process':'i[person a work a][c['+val['processes']+']['+case+' v person v work]]'}
def frame(v):return ' '.join(v[n] for n in ('speaker','group','epoch','reference','candidate','point'))
def progress(v):return frame(v)+' '+v['topic']+' '+v['first']+' '+v['process']+' '+' '.join(v[n] for n in ('obstacles','scope','bound','variables','equations','factors','worlds','matches','frames'))

def definitions():
    v=actual_fields();history='i[at d][k h257z[v reference '+v['candidate']+' v at]]';before='i[first d last d][k ic[v first v last '+v['candidate']+']]'
    relevant=both('k h246c[v group v person v reference]','k r5tp[v person v work v topic '+v['point']+']')
    checked='f person a[f work a[y['+relevant+']['+both('k r5tw[v person v work v topic '+v['point']+' '+v['first']+']','k r5tw[v person v work v topic '+v['point']+' '+v['point']+']')+']]]'
    model='k r5ue[v group v reference '+' '.join('v '+n for n in ('variables','equations','factors','worlds','matches','frames'))+']'
    valid=both('k r5sc['+frame(v)+']',checked,'k hc[n p a b v bound]','k rl2['+history+' '+before+' '+v['first']+' '+v['point']+' v obstacles v scope '+model+']')
    text='d r5uk['+params(FIELDS)+'] h[d] c[i[case d]['+valid+']].\n'
    text+='d r5ul['+params(FIELDS)+'] h[d] e[i[case d][k r5uj['+progress(v)+']]].\n'
    for n,target,sort in (('r5um','r5ul',FCODE),('r5un','r5uk',ACODE)):
        text+='d '+n+'['+params(NAMES)+'] '+sort+'[o a[r c[p '+target+']]['+NARGS+']].\n'
    text+='d r5uo[family '+FCODE+' actual d] e[c[s[v family]][v actual]].\n'
    text+='d r5up[family '+FCODE+' actualname i[d]] '+TCODE+'[o a[r d[p r5uo]][o r[v family] v actualname]].\n'
    text+='d r5uq[family '+FCODE+'] e[b case[t[c[s[v family]][v case]][v case]]].\n'
    signal='c[v contents][v item]';target='k r5up[v family v actualname]'
    diagnosis='k rmb['+signal+' k r5uq[v family] v cases v selected i[case d][c[v classified][v item v case]] v weight v threshold]'
    text+='d r5ur['+params(ITEM)+'] c['+both('c[v selected][s[v actualname]]','c[v accessible][v observer v item v context]',
        'c[v linked][v item '+target+' v context]','t['+signal+'][s[v actualname]]',diagnosis)+'].\n'
    one=lambda item:'k r5ur['+' '.join(('v '+item if n=='item' else 'v '+n) for n,_ in ITEM)+']'
    text+='d r5us['+params(MULTIPLE)+'] c[g first a[g second a['+both('u[e[v first][v second]]',one('first'),one('second'))+']]].\n'
    names='k r5um['+NARGS+']';validnames='k r5un['+NARGS+']';v=actual_fields('s[v actualname]',True)
    sourceargs=names+' v actualname '+v['speaker']+' '+v['point']+' '+' '.join('v '+n for n,_ in SCORE)
    checked='f case d[y[c[v selected][v case]][c[s['+validnames+']][v case]]]'
    text+='d r5ut['+params(SOURCE)+'] c['+both(checked,'k r5us['+sourceargs+']')+'].\n'
    text+='d r5uu['+params(SOURCE)+'] e[b outer[k r5ut['+' '.join('v '+n for n,_ in SOURCE)+']]].\n'
    dialogue=frame(v)+' '+v['topic']+' k h223h['+v['point']+']'
    text+='d r5uv['+params(NAMES)+' actualname i[d]] f[k r5tm['+dialogue+']].\n'
    text+='d r5uw['+params(NAMES)+' actualname i[d]] f[k r5tn['+dialogue+' k r5uo['+names+' s[v actualname]]]].\n'
    return text

def build():
    libs=parents();entries={};merged=[]
    for lib in libs:
        for d in lib.document['declarations']:
            n=d['name']
            if n in entries:assert d==entries[n]['declaration'] and lib.entries[n]['meaning_ja']==entries[n]['meaning_ja'],n
            else:merged.append(d);entries[n]=lib.entries[n]
    doc=deepcopy(libs[0].document);doc.update(declarations=merged,statements=[])
    doc['declarations']=closure(doc,['r5uj','r5sc','r5tp','r5tw','r5ue','rl2','h257z','ic','h246c','hc','rmb','r5tm','r5tn','h223h'])
    imported={d['name']:entries[d['name']] for d in doc['declarations']};assert not set(MEANINGS)&set(entries)
    doc=parse(format_graph(doc,'compact')+definitions());ds={d['name']:d for d in doc['declarations']}
    prims={n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=e['arguments'],meaning_ja=e['meaning_ja']) for n,e in imported.items() if e['kind']=='primitive'}
    paths=set().union(*(set(lib.source_sha256) for lib in libs))
    basis=dict(status='fixed_claim_and_corresponding_scenario_indications_dependency',document=LIBRARY,primitives=prims,
        definitions={n:e['meaning_ja'] for n,e in imported.items() if e['kind']=='definition'}|MEANINGS,
        imported_symbols={n:e['meaning_basis'] for n,e in imported.items()},import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)},limitations=LIMITS)
    return {LIBRARY:format_graph(doc,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n'}
