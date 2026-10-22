"""Tie matched obstacles to departure, then compose an assessed gradual trend."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT,closure
from scripts.compose_qualitative_influence import both,MODEL,STATE
from scripts.compose_paired_influence import MATCH
from scripts.compose_present_epoch_assessment import FRAME,ARGS,HISTORY,BEFORE,PEOPLE
from scripts.compose_declining_hindrances import GRADUAL,CHECKED,interval,count
from scripts.compose_limits import call as k
from scripts.compose_situated_criticism import params,args

PARENTS=('data/qualified-pursuit-opening-basis-v1.json','data/royal-intervention-sentence-basis-v1.json','data/religious-collective-assessment-basis-v1.json')
LIBRARY='examples/v016/departure-hindrance-trend.noema';BASIS='data/departure-hindrance-trend-basis-v1.json'
TARGET='group a reference d frame a initial d'
TARGS='v group v reference v frame v initial'
PROFILE='obstacle a '+TARGET+' '+MODEL+' worlds h['+STATE+'] d matches '+MATCH
PARGS='v obstacle '+TARGS+' v variables v equations v factor v worlds v matches'
MAPS='variables h[a] j[a] equations h[a d] h[a '+STATE+'] c factors h[a] a worlds h[a d '+STATE+'] d matches h[a d '+STATE+' '+STATE+'] c frames h[d] a'
MAPARGS='v variables v equations v factors v worlds v matches v frames'
TEMPORAL='group a reference d candidate d start d end d obstacles j[a] scope h[a] c bound b '+MAPS
TMARGS='v group v reference v candidate v start v end v obstacles v scope v bound '+MAPARGS
SOURCE=FRAME+' topic a first d processes h[a a] a obstacles j[a] scope h[a] c bound b '+MAPS
SARGS=ARGS+' v topic v first v processes v obstacles v scope v bound '+MAPARGS
PRIMITIVES={
 'h26kg':('[a d d] c',['condition','reference','candidate'],
   '同じ固定基準で指定条件・制度・作用要因が候補状況に存在又は適用される。妨害するか否かとは独立の有無。介入の真偽はこの同じ要因の有無へ合わせ、別の条件や要因の効果を有無へ取り替えない。'),
}
MEANINGS={
 'r5t5':'同じ人が同じ候補履歴・固定された比較期間で、初期点以後の二点に生存し、その間の同じ過程beで自己に帰責される未成熟bpから自立的行使能力upへ離脱する。既に能力を持つ人数や宗教的な質付き能力r5tbの獲得へ置換しない。',
 'r5t6':'固定された非空・重複なしの完全な人間集団と、同じ候補の有効な履歴・初期点・未来がある。比較期間の初期点以後で各人が生存する全点のfo能力評価が整う。未知や評価不足を離脱なしへ補わない。',
 'r5t7':'固定集団の成員のうちr5t5の同じ離脱過程が比較期間にある人の割合。一人に複数過程があっても一人として数える。集団・履歴の妥当性はr5t6で確認する。',
 'r5ua':'同じ集団・基準・比較期間・初期点の二候補でr5t6が成立し、左のr5t7離脱割合が右以上である。後付けの人口や期間の選択で比較を逆転させない。',
 'r5ub':'同じモデルの要因有無の全介入解で、要因の真偽が同じ条件h26kgの有無と一致する。空解はこの対応だけでは拒否せず、r5ucの両側存在条件へ結ぶ。',
 'r5uc':'同じ条件の有無の対応r5ubと、同じ人々の離脱r5t6/r5uaについてr2wjの全解評価・対応完備性・比較整合性が成立する。比較組は同じ背景と選択枝に固定する。',
 'r5ud':'r5ucの有効な対応組の少なくとも一つで、条件ありの離脱割合が条件なしより低い。一般的啓蒙すなわち自己に帰責される未成熟からの離脱を妨げうる条件として扱う。現実の発生・全背景の悪化・観測頻度は追加しない。',
 'r5ue':'固定集団・基準と候補別・時点別のモデルを、同じ条件とその時点を初期点とするr5ucの評価へ渡す。比較期間の選択規則はframesに固定する。',
 'r5uf':'r5ueと同じモデル・集団・基準・比較期間規則でr5udの潜在的妨害を評価する。時点ごとに目標や人々を取り替えない。',
 'r5ug':'rl2の全候補・全区間評価の下、終点の妨害件数が始点より少なく、正の一段階上限を超える減少には中間の件数があり、全体にも両端と異なる中間値がある。途中の増加を許し、一挙の減少だけや終点増加を拒否する。',
 'r5uh':'同じ固定集団・基準・現実候補の履歴・前後点に、r5ueの評価とr5ufの同じ離脱への妨害を渡してr5ugの漸減を構成する。条件を数える粒度と候補範囲を期間中に替えない。',
 'r5ui':'同じ現在人口・話者・時代・終点にr5t3の自由な取り組みの新規開放とr5uhの離脱への障害漸減がともにある。取り組みの目標r5tbと障害の対象beを混同せず、同じ人口の進行へ連言する。',
 'r5uj':'r5uiの同じ現在と諸設定を閉じた進行内容にする。外側の評価点で現在を動かさず、第一文問答のr5tk/tnに渡せる形を作る。問答・徴候・著者帰属の全体はこの内容だけでは完了しない。',
}
LIMITS=[
 'u0014第三文のdahinは前文の宗教的な質付き能力、障害の対象はallgemeinen Aufklärung, oder des Ausganges aus ihrer selbst verschuldeten Unmündigkeitと区別する。後者の過程は第一段落で確認済みのbeへ接続する。全ての離脱をsicher und gutという修飾へ強化しない。',
 '一般的な離脱の進行を、固定集団で同じ比較期間に離脱過程がある人の割合として評価する明示的な有限モデルの読み。期間、集団、要因の粒度、全候補範囲、比較期間の選択規則は結果を見ず固定する。原文が数値尺度又は一定期間を指定したとはしない。',
 '条件の有無を変えた同じ背景・初期状況・非決定的選択枝を対応させ、その対応組で離脱割合が低下しうることを潜在的妨害と読む。生存条件、評価基準や別の要因を比較側ごとに都合よく交換しない。matchesは結果の高低から選ばない。モデルの現実への適合は入力の意味規約であり、この有限検査から証明しない。',
 '比較の履歴には初期点と未来を要し、生存中の全関連点の能力評価を求める。帰責・過程・条件対応の未知値も評価器が拒否する。既知の不成立、評価不足、未知を区別する。全員の同時離脱や能力の現在保有は要求しない。',
 'allmälig wenigerを、全区間の固定候補の妨害件数が途中の戻りを許しつつ複数段階で減るものとして読む。上限は局所的な減少だけを制限する。全区間非増加の旧rl4を改変せず別定義にする。二回以上の減少・件数という読みは明示したモデル化で、全ての日常的な漸減の必要条件とはしない。',
 '候補の全消滅、候補ごとの単調な除去、経過時間に対する速度を要求しない。有限履歴の点の間に現実の変動がなかったことを証明せず、強度や確率の漸減はこの件数モデルとは別である。',
 '開放と障害漸減を同じ現在人口の進行内容に連言する。場の比喩、oderによる説明的言い換えの提示、現在進行とdoch、明瞭な徴候、第一文の条件付き問答と帰属、第二文の甚だしい不足、最後のFriederichsと段落通読は未完。新たな本文主張・全単位判断・意味確認文字を追加しない。',
]
@lru_cache(None)
def parents():return tuple(load_catalog(ROOT,p) for p in PARENTS)

def definitions():
    hist='i[point d][k h7q[v frame v candidate v point]]';before='i[first d last d][k ic[v first v last v candidate]]'
    departure=both('k h7q[v frame v candidate v first]','k h7q[v frame v candidate v last]',
        'x[e[v initial][v first]][k ic[v initial v first v candidate]]','k ic[v first v last v candidate]',
        'k h256o[v person v candidate v first]','k h256o[v person v candidate v last]','k be[v person v process v first v last]')
    text='d r5t5[person a frame a initial d candidate d] c['+both('k aa[v person]','g process a[g first d[g last d['+departure+']]]')+'].\n'
    relevant=both('k h7q[v frame v candidate v point]','x[e[v initial][v point]][k ic[v initial v point v candidate]]','k h256o[v person v candidate v point]')
    checked='f person a[y[c['+PEOPLE+'][v person]][f point d[y['+relevant+'][t[k fo[v person]][v point]]]]]'
    text+='d r5t6['+TARGET+' candidate d] c['+both('k r5te[v group v reference '+PEOPLE+']','k rcm[k mp[v group] '+PEOPLE+']','k rqtb['+hist+' '+before+' v initial]',checked)+'].\n'
    text+='d r5t7['+TARGET+' candidate d] b[k pb[k mp[v group] i[person a][k r5t5[v person v frame v initial v candidate]]]].\n'
    text+='d r5ua['+TARGET+' left d right d] c['+both('k r5t6['+TARGS+' v left]','k r5t6['+TARGS+' v right]','u[k hc[k r5t7['+TARGS+' v left] k r5t7['+TARGS+' v right]]]')+'].\n'
    align='k r2vc[v variables v equations v factor i[state '+STATE+'][z[c[v state][v factor]][k h26kg[v obstacle v reference c[v worlds][v state]]]]]'
    text+='d r5ub['+PROFILE+'] c['+align+'].\n'
    valid='i[state '+STATE+'][k r5t6['+TARGS+' c[v worlds][v state]]]'
    order='i[left '+STATE+' right '+STATE+'][k r5ua['+TARGS+' c[v worlds][v left] c[v worlds][v right]]]'
    text+='d r5uc['+PROFILE+'] c['+both('k r5ub['+PARGS+']','k r2wj[v variables v equations v factor v matches '+valid+' '+order+']')+'].\n'
    text+='d r5ud['+PROFILE+'] c['+both('k r5uc['+PARGS+']','k r2wk[v variables v equations v factor v matches '+order+']')+'].\n'
    mapped='v obstacle v group v reference c[v frames][v point] v point c[v variables][v obstacle] c[v equations][v obstacle v point] c[v factors][v obstacle] i[state '+STATE+'][c[v worlds][v obstacle v point v state]] i[on '+STATE+' off '+STATE+'][c[v matches][v obstacle v point v on v off]]'
    for n,target in (('r5ue','r5uc'),('r5uf','r5ud')):
        text+='d '+n+'[group a reference d '+MAPS+'] h[a d] c[i[obstacle a point d][k '+target+'['+mapped+']]].\n'
    ordered=both(interval('first'),interval('last'),'c[v before][v first v last]')
    adjacent=both(interval('first'),interval('last'),'k rl5[v history v before v first v last]')
    large='k hc[k ha['+count('last')+' v bound] '+count('first')+']'
    intermediate='g middle d['+both(interval('middle'),'c[v before][v first v middle]','c[v before][v middle v last]',k('hc',count('middle'),count('first')),k('hc',count('last'),count('middle')))+']'
    limited='f first d[f last d[y['+adjacent+'][u['+large+']]]]'
    resolved='f first d[f last d[y['+both(ordered,large)+']['+intermediate+']]]'
    middle='g middle d['+both(interval('middle'),'c[v before][v start v middle]','c[v before][v middle v end]',k('hc',count('middle'),count('start')),k('hc',count('end'),count('middle')))+']'
    text+='d r5ug['+params(GRADUAL)+'] c['+both(k('rl2',*args(CHECKED)),'k hc[n p a b v bound]',k('hc',count('end'),count('start')),limited,resolved,middle)+'].\n'
    text+='d r5uh['+TEMPORAL+'] c[k r5ug['+HISTORY+' '+BEFORE+' v start v end v obstacles v scope k r5ue[v group v reference '+MAPARGS+'] k r5uf[v group v reference '+MAPARGS+'] v bound]].\n'
    text+='d r5ui['+SOURCE+'] c['+both('k r5t3['+ARGS+' v topic v first v processes]','k r5uh[v group v reference v candidate v first v point v obstacles v scope v bound '+MAPARGS+']')+'].\n'
    text+='d r5uj['+SOURCE+'] e[b outer[k r5ui['+SARGS+']]].\n'
    return text

def build():
    libs=parents();entries={};merged=[]
    for lib in libs:
        for d in lib.document['declarations']:
            n=d['name']
            if n in entries:assert d==entries[n]['declaration'] and lib.entries[n]['meaning_ja']==entries[n]['meaning_ja'],n
            else:merged.append(d);entries[n]=lib.entries[n]
    doc=deepcopy(libs[0].document);doc.update(declarations=merged,statements=[])
    roots=['be','fo','aa','h7q','ic','h256o','r5te','rcm','mp','pb','rqtb','r2vc','r2wj','r2wk','h246c','hc','ha','rl2','rly','rlz','rl5','h257z','r5t3']
    doc['declarations']=closure(doc,roots);imported={d['name']:entries[d['name']] for d in doc['declarations']}
    assert not(set(PRIMITIVES)|set(MEANINGS))&set(entries)
    doc=parse(format_graph(doc,'compact')+''.join('r '+n+v[0]+'.' for n,v in PRIMITIVES.items())+definitions());ds={d['name']:d for d in doc['declarations']}
    prims={n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=e['arguments'],meaning_ja=e['meaning_ja']) for n,e in imported.items() if e['kind']=='primitive'}
    prims.update({n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=v[1],meaning_ja=v[2]) for n,v in PRIMITIVES.items()})
    paths=set().union(*(set(lib.source_sha256) for lib in libs))
    basis=dict(status='departure_hindrance_and_nonmonotone_gradual_trend_dependency',document=LIBRARY,primitives=prims,
        definitions={n:e['meaning_ja'] for n,e in imported.items() if e['kind']=='definition'}|MEANINGS,
        imported_symbols={n:e['meaning_basis'] for n,e in imported.items()},import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)},limitations=LIMITS)
    return {LIBRARY:format_graph(doc,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n'}
