"""Open opportunities for self-directed pursuit of the same qualified ability."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT,closure
from scripts.compose_qualitative_influence import both,TRUE,FALSE
from scripts.compose_protected_remarks import bind
from scripts.compose_present_epoch_assessment import FRAME,ARGS,HISTORY,BEFORE,PEOPLE

PARENTS=('data/religious-collective-assessment-basis-v1.json','data/royal-intervention-sentence-basis-v1.json')
LIBRARY='examples/v016/qualified-pursuit-opening.noema';BASIS='data/qualified-pursuit-opening-basis-v1.json'
FAMILY='i b[h[j[a] d] e]'
FIELDS='person a work a topic a anchor d point d';PARGS='v person v work v topic v anchor v point'
ROLE='k h26ke[v person v anchor]'
BINDINGS='l[a][v person v work v topic '+ROLE+']'
TARGET='r b[p r5ts]'
OPEN='group a topic a reference d candidate d first d last d processes h[a a] a'
OARGS='v group v topic v reference v candidate v first v last v processes'
SOURCE=FRAME+' topic a first d processes h[a a] a'
SARGS=ARGS+' v topic v first v processes'
PRIMITIVES={
 'h26kd':('[a a d] c',['person','source','reference'],
   '同じ本人・固定基準で、その人の宗教的な自己形成の取り組みに適用される指図・禁止・義務を評価する全規範源の範囲。現に禁止した側や好ましい規範だけへ絞らず、関係する公的制度・共同の規則等を含める。具体的要求は同じ立場・内容・基準・評価点で別に確認する。規範源の存在、規範の正当性、積極的許可をこの範囲関係だけで導かない。'),
 'h26ke':('[a d] a',['person','reference'],
   '同じ本人・固定基準で、自分の宗教上の理解と判断のあり方を学習・探究・吟味により形成する側の立場。委託された職務で他者の指定を遂行する立場とは別に扱う。現に取り組んだこと、任意の全活動への自由、教義の真理、能力の達成をこの参照だけで要求しない。'),
 'h26kf':('[a a a d d] c',['person','work','topic','reference','point'],
   '同じ本人・候補の取り組み・主題・固定基準について、この点の機会を比較する入力が評価されている。適用する全規範源とその正負の要求、関係する権威的介入、方法の利用可能性と全結果の範囲が判断でき、未知や観測されない前状態を不存在で埋めていない。機会があること・許可の有無・目標能力の達成とは別で、前後の同じ項目で確認する。'),
}
MEANINGS={
 'r5to':'本人・宗教主題の正確な二対象列と固定基準について、h223hの閉じた基準参照の一致を確認し、同じ質付き宗教能力r5tbを目標内容にする。本文の能力評価と同じ事項・安定性・適切さを保持する。',
 'r5tp':'同じ人・宗教主題・固定基準の関連事項r5s6に、本人の同じ学習・探究・吟味の活動構成h26fxがある。成功・許可・実行・現に持つ意図は候補の条件にしない。',
 'r5tq':'r5tpの同じ取り組みが生起し本人が参加し、同じ活動で同じ本人・主題・基準のr5to能力を目指す。目標への志向h26hfは引用のまま保持し、能力の達成・実現可能性・原因としての成功を導かない。',
 'r5tr':'本人・取り組み・主題の正確な三対象列をr5tqの実行内容へ結ぶ。結果候補で実行を確認するときに使い、現在の実行と混同しない。',
 'r5ts':'本人・取り組み・主題・自己形成の立場の正確な四対象列について、同じh26keの立場とr5tqの実行内容を保持する。要求・介入の対象に同じ立場を明示する。',
 'r5tt':'同じ本人の固定された全規範源h26kdについて、同じ立場・取り組み内容r5ts・対象列・基準の実行要求と不実行要求がともにない。明示的な積極的許可を要求せず、他の立場の職務まで解除しない。',
 'r5tu':'同じ本人・立場・取り組み内容に、評価点で生起する活動による権威的・強制的な代行又は妨害h26hoがない。無関係な活動や単なる助言を介入へ替えない。',
 'r5tv':'同じr5tpの候補にr5ttの非強制・非禁止とr5tuの非介入があり、aeの方法利用とafの一つの同じ結果でr5tqの本人の取り組みが成立する。現在の実行、目標能力の獲得、全結果の成功は要求しない。',
 'r5tw':'r5tpの同じ候補にh26kfの機会評価が整う。評価済みと自由な機会の成立を区別し、評価不足を前の不自由へ補わない。',
 'r5tx':'宗教主題と元の固定基準を保ち、本人・取り組み別にr5tvの機会内容を返す。比較時点を動かしても目標能力・主題・規範の基準を替えない。',
 'r5ty':'同じ固定基準の集団が非空で全成員が人間である。現在人口との完全一致はr5t3で既存r5scへ結ぶ。',
 'r5tz':'同じ履歴の前後・固定集団・元の宗教的取り組み範囲についてrmtを適用し、全候補の両端評価と、各人に新しく成立した同じ機会と同じ変化過程ag/la/dgがある。本人ごとに異なる取り組みを許し、同時実行や能力獲得は要求しない。',
 'r5t2':'r5tzの前後・人口・主題・基準を閉じた内容に保持する。外側の評価点を原文の現在へ置換しない。',
 'r5t3':'同じ現在人口・話者・時代のr5scに、その現在点を終点としたr5tzの機会開放を結ぶ。未来の開放や別の集団の開放を現在の進行へ流用しない。',
 'r5t4':'r5t3の同じ現在点と設定を固定した内容。後続の障害漸減と連言するための開放側であり、これ一つを段落の全進行内容とはしない。',
}
LIMITS=[
 'u0014第三文sich dahin frei zu bearbeitenとFeld geöffnetを、同じ宗教的な質付き能力を目指す本人の学習・探究・吟味と、その機会の新規成立として読む。dahinは現在の成功又は別の無修飾能力に置き換えない。',
 'freiは、この取り組みについて適用される全規範源からの強制・禁止と、権威的な代行・妨害がないことと、実践上の実行機会を結ぶ明示的な読み。旧rlwの不実行にも積極的許可があるという強い条件は採らない。道徳的な正当性や全活動に無制限の自由があることを追加しない。',
 '同じ営みを方法として選べる活動構成と、その候補結果で本人が実行する活動という粒度で扱う。活動の生起・本人の参加・活動種類・目標志向は同じ証人へ結ぶ。目標能力そのものは実行条件にせず、試みが失敗しうることを保持する。',
 '目標は段階1の閉じたr5toと本人・主題の列、規範と介入の対象は同じr5tsと本人・取り組み・主題・立場の列である。別の目標や別の本人の同じ真偽の内容で代用しない。',
 'ihnenの人々に開かれる機会を、固定集団の各人に少なくとも一つ新しく成立する機会という読みで表す。全員が同じ方法を持つこと、同時に取り組めること、旧機会の全保持は要求しない。集団的な共通制度の機会をこれ以外に表せないとは主張しない。',
 '旧rmtの同じ前後点・機会・変化過程を再利用する。過去の機会が未評価であることを不在へ替えない。生起した変化過程と対象者を結び、特定の君主や行為者を受動文へ追加しない。全過程の原因や速度、未来の完了は主張しない。',
 '場という表現の比喩的提示、現在進行の提示、障害の漸減、自己責任の未成熟からの離脱との言い換え、徴候、第一文の条件付き問答と著者帰属は未完。開放側だけで第一文又は第三文の全意味判断を加算しない。',
]
@lru_cache(None)
def parents():return tuple(load_catalog(ROOT,p) for p in PARENTS)
def definitions():
    goal=both('e[s[k h223h[v reference]]][v reference]','t[c[k r5tb[v topic v reference k h223h[v reference]]][v person]][v point]')
    text='d r5to[bindings j[a] reference d] e[b point['+bind(('person','topic'),goal)+']].\n'
    candidate=both('k aa[v person]','g matter a['+both('k r5s6[v person v topic v matter v anchor]','k h26fx[v person v work v matter v anchor]')+']')
    text+='d r5tp[person a work a topic a anchor d] c['+candidate+'].\n'
    pursuit=both('k r5tp[v person v work v topic v anchor]','k dg[v work v point]','k df[v person v work v point]',
        'k h26hf[v person v work r b[p r5to] l[a][v person v topic] v anchor v point]')
    text+='d r5tq['+FIELDS+'] c['+pursuit+'].\n'
    execution='k r5tq[v person v work v topic v reference v point]'
    text+='d r5tr[bindings j[a] reference d] e[b point['+bind(('person','work','topic'),execution)+']].\n'
    text+='d r5ts[bindings j[a] reference d] e[b point['+bind(('person','work','topic','role'),both('e[v role][k h26ke[v person v reference]]',execution))+']].\n'
    norm=lambda sign:'k h237z[v source v person '+ROLE+' '+TARGET+' '+BINDINGS+' v anchor '+sign+' v point]'
    text+='d r5tt['+FIELDS+'] c[f source a[y[k h26kd[v person v source v anchor]]['+both('u['+norm(TRUE)+']','u['+norm(FALSE)+']')+']]].\n'
    intervention=both('k dg[v event v point]','k h26ho[v event v person '+TARGET+' '+BINDINGS+' v anchor v point]')
    text+='d r5tu['+FIELDS+'] c[u[g event a['+intervention+']]].\n'
    possible='g result d['+both('k af[v person v work v point v result]','k r5tq[v person v work v topic v anchor v result]')+']'
    text+='d r5tv['+FIELDS+'] c['+both('k r5tp[v person v work v topic v anchor]','k r5tt['+PARGS+']','k r5tu['+PARGS+']','k ae[v person v work v point]',possible)+'].\n'
    text+='d r5tw['+FIELDS+'] c['+both('k r5tp[v person v work v topic v anchor]','k h26kf['+PARGS+']')+'].\n'
    text+='d r5tx[topic a anchor d] h[a a] e[i[person a work a][b point[k r5tv['+PARGS+']]]].\n'
    member='k h246c[v group v person v reference]'
    text+='d r5ty[group a reference d] c['+both('g person a['+member+']','f person a[y['+member+'][k aa[v person]]]')+'].\n'
    scope='i[person a work a][k r5tp[v person v work v topic v last]]'
    assessed='i[person a work a point d][k r5tw[v person v work v topic v last v point]]'
    opening='k rmt['+HISTORY+' '+BEFORE+' v first v last '+PEOPLE+' '+scope+' '+assessed+' k r5tx[v topic v last] v processes p ag p la p dg]'
    text+='d r5tz['+OPEN+'] c['+both('k r5ty[v group v reference]',opening)+'].\n'
    text+='d r5t2['+OPEN+'] e[b outer[k r5tz['+OARGS+']]].\n'
    text+='d r5t3['+SOURCE+'] c['+both('k r5sc['+ARGS+']','k r5tz[v group v topic v reference v candidate v first v point v processes]')+'].\n'
    text+='d r5t4['+SOURCE+'] e[b outer[k r5t3['+SARGS+']]].\n'
    return text
def build():
    libs=parents();entries={};merged=[]
    for lib in libs:
        for d in lib.document['declarations']:
            n=d['name']
            if n in entries:assert d==entries[n]['declaration'] and lib.entries[n]['meaning_ja']==entries[n]['meaning_ja'],n
            else:merged.append(d);entries[n]=lib.entries[n]
    doc=deepcopy(libs[0].document);doc.update(declarations=merged,statements=[])
    doc['declarations']=closure(doc,['r5tb','r5s6','r5sc','rmt','h223h','h26fx','h26hf','h237z','h26ho','dg','df','ae','af','ag','la','rdr'])
    imported={d['name']:entries[d['name']] for d in doc['declarations']}
    assert not(set(PRIMITIVES)|set(MEANINGS))&set(entries)
    doc=parse(format_graph(doc,'compact')+''.join('r '+n+v[0]+'.' for n,v in PRIMITIVES.items())+definitions());ds={d['name']:d for d in doc['declarations']}
    prims={n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=e['arguments'],meaning_ja=e['meaning_ja']) for n,e in imported.items() if e['kind']=='primitive'}
    prims.update({n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=v[1],meaning_ja=v[2]) for n,v in PRIMITIVES.items()})
    paths=set().union(*(set(lib.source_sha256) for lib in libs))
    basis=dict(status='qualified_self_cultivation_and_new_free_opportunities_dependency',document=LIBRARY,primitives=prims,
        definitions={n:e['meaning_ja'] for n,e in imported.items() if e['kind']=='definition'}|MEANINGS,
        imported_symbols={n:e['meaning_basis'] for n,e in imported.items()},import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)},limitations=LIMITS)
    return {LIBRARY:format_graph(doc,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n'}
