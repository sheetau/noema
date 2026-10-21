"""Bind three kinds of cohort progress to each method's possible continuation."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT,closure
from scripts.compose_qualitative_influence import both

PARENTS=('data/covenant-nullity-basis-v1.json','data/cognitive-correction-basis-v1.json','data/cognitive-acquisition-basis-v1.json')
LIBRARY='examples/v016/cohort-progress-options.noema'
BASIS='data/cohort-progress-options-basis-v1.json'
PRIMITIVES={
 'h26ak':('[a a d d d d d] c',['group','method','scope','base','start','end','branch'],
    '同じ集団・方法・固定範囲・基準経過・起点から、この結果状況に至る可能な継続経過の全範囲に、この経過が属する。起点までの出来事・人々・認識の状態と、同じ時代区分・集団の同定を保つ。結果を日付の数字だけで表さず、その可能な状況として指定する。将来の出生や別の結果への分岐を許す。成功・不成功で継続を選別せず、方法又は結果が異なる継続を混ぜない。実際の選択・実現・合意の原因性は含意しない。'),
}
MEANINGS={
 'r5cq':'同じ候補・時点の対象集団に生存する人が少なくとも一人おり、その全員について固定範囲のr2qmの判断評価が有効である。集団外の生存者や未評価の人を流用せず、人口の消滅を進展なしへ読み替えない。',
 'r5cr':'同じ対象集団の有効な前後評価と順序の下で、その成員のr5abの新たな理由ある自己判断、又は後の成員が以前のどの生存成員にもなかった対象でr5aaを持つことがある。全生存人類のr5adをそのまま使わず、同じ集団へ限定する。',
 'r5cs':'同じ集団・固定範囲・真偽評価・候補・前後点について、認識の獲得r5co、誤りの訂正r5ci、理由ある自己判断の進展r5crの少なくとも一つがある。三つを同時達成するという連言へ置き換えない。',
 'r5ct':'同じ固定範囲と起点について、基準経過と継続経過の両方に起点があり、起点で生存する同じ集団の人々が個体ごとに一致する。将来を含む全成員の一致を要求せず、将来の出生を許す。起点までの履歴の保存全体はh26akの意味規約で保つ。',
 'r5cu':'同じ方法と結果の継続h26akが、厳密な全順序の履歴、起点より後の結果点、r5ctの同じ起点集団、前後のr5cqの非空で有効な評価を持つ。進展が起きることは要求しない。',
 'r5cv':'基準の起点にr5cqがあり、全利用可能方法の結果がrjaで非空である。各結果には継続があり、その全継続がr5cuを満たす。無効な継続だけを除外して空の成功範囲を作ることを許さない。方法がない場合の整合性は許す。',
 'r5cw':'r5cvを満たす同じ集団・方法・結果・継続について、どの利用可能方法のどの結果にもr5csの三種類のいずれの進展もない。別々の方法で各一種類を進める可能性や、成功を保証しない方法の成功結果も不能を反証する。',
}
LIMITS=[
 '啓蒙の進展は、前段と同じ、通常の場面で理由ある自己判断ができる対象の新たな獲得・広がりとして読む。既存r5aa/r5ab/r2qmを再利用し、対象を次の時代の同じ集団へ限定する。情報量だけや一回の正しい意見で代用しない。',
 '認識の獲得r5coと誤りの訂正r5ciの採用解釈・入力規約を保持する。進展は少なくとも一人の一部でよく、全知識の無損失や全員一致を加えない。三種類を同時に達成できないという弱い否定ではなく、いずれの成功可能性もないことを述べる。',
 '既存r5cj/r5cpは指定した一経過内の比較を目的にする。一般の方法選択では別の継続経過に成功結果があり得るため、今回のr5cwでは各結果とその全継続をh26akで結んで比較する。旧定義・旧証拠は変更せず、固定経過を全ての将来へ拡張したとは扱わない。',
 '方法と結果の関数は同じ集団・固定範囲・基準経過へ結び付けて渡す。個人の学習・検討と共同活動を含む全範囲とする。継続の選定を成功後に変えず、起点での生存集団の一致を検査する。過去の全事実の一致と現実の全候補の網羅は有限検査から証明しない。',
 '結果のない利用可能方法、継続のない結果、逆行・循環・別の起点集団・未評価・集団の消滅を不能性の証拠にしない。選択肢が本当にない場合は不能性と両立するが、未知の選択肢を空集合で代用しない。認識や理由の未知も偽へ補わない。',
 'ここでの不能性だけから、合意がその状態を生んだこと、実際に合意が形成されたこと、道徳的に許されないことを導かない。先行する合意の目的、後代を置く状態とmussの必然性、kann nichtの規範的否認、重要性・総括・共謀的提示・全文帰属を接続する作業が残る。全文の確認済み文字数を増やさない。',
]

@lru_cache(None)
def parents():return tuple(load_catalog(ROOT,p) for p in PARENTS)
def living(person,point,candidate='candidate'):
    return both('k aa[v '+person+']','k h246c[v group v '+person+' v '+candidate+']','k h256o[v '+person+' v '+candidate+' v '+point+']')
def timeline(candidate):return 'k ta[i[at d][k h257z[v scope v '+candidate+' v at]] i[before d after d][k ic[v before v after v '+candidate+']]]'
def definitions():
    text='d r5cq[group a scope d candidate d point d] c['+both('g person a['+living('person','point')+']',
        'f person a[y['+living('person','point')+'][k r2qm[v person v scope v point]]]')+'].\n'
    prior='g other a['+both(living('other','first'),'k h226u[v other v scope v topic]','k r5aa[v other v topic v scope v first]')+']'
    collective='g topic a['+both('k h226u[v person v scope v topic]','k r5aa[v person v topic v scope v last]','u['+prior+']')+']'
    individual=both(living('person','first'),'k r5ab[v person v scope v first v last]')
    gain='g person a['+both(living('person','last'),'x['+individual+']['+collective+']')+']'
    fields='group a scope d candidate d first d last d'
    text+='d r5cr['+fields+'] c['+both(timeline('candidate'),'k h257z[v scope v candidate v first]','k h257z[v scope v candidate v last]',
        'k ic[v first v last v candidate]','k r5cq[v group v scope v candidate v first]','k r5cq[v group v scope v candidate v last]',gain)+'].\n'
    fields='group a scope d assessment d candidate d first d last d';args='v group v scope v assessment v candidate v first v last'
    text+='d r5cs['+fields+'] c[x[k r5co['+args+']][x[k r5ci['+args+']][k r5cr[v group v scope v candidate v first v last]]]].\n'
    text+='d r5ct[group a scope d base d branch d start d] c['+both('k h257z[v scope v base v start]','k h257z[v scope v branch v start]',
        'f person a[z['+living('person','start','base')+']['+living('person','start','branch')+']]')+'].\n'
    fields='group a scope d base d start d method a end d branch d'
    branch='k h26ak[v group v method v scope v base v start v end v branch]'
    text+='d r5cu['+fields+'] c['+both(branch,timeline('branch'),'k h257z[v scope v branch v end]',
        'k ic[v start v end v branch]','k r5ct[v group v scope v base v branch v start]',
        'k r5cq[v group v scope v branch v start]','k r5cq[v group v scope v branch v end]')+'].\n'
    options='available h[a a d] c outcomes h[a a d d] c'
    available='c[v available][v group v method v start]';outcome='c[v outcomes][v group v method v start v end]'
    valid='k r5cu[v group v scope v base v start v method v end v branch]'
    covered=both('g branch d['+branch+']','f branch d[y['+branch+']['+valid+']]')
    complete='f method a[y['+available+'][f end d[y['+outcome+']['+covered+']]]]'
    text+='d r5cv[group a scope d base d start d '+options+'] c['+both(timeline('base'),'k h257z[v scope v base v start]',
        'k r5cq[v group v scope v base v start]','k rja[v group v start v available v outcomes]',complete)+'].\n'
    success='g method a[g end d[g branch d['+both(available,outcome,branch,'k r5cs[v group v scope v assessment v branch v start v end]')+']]]'
    text+='d r5cw[group a scope d assessment d base d start d '+options+'] c['+both('k r5cv[v group v scope v base v start v available v outcomes]','u['+success+']')+'].\n'
    return text

def build():
    sources=parents();doc=deepcopy(sources[0].document);doc.update(declarations=[],statements=[]);imported={}
    for source,roots in zip(sources,(['r5aa','r5ab','r2qm','h226u','aa','h256o','h246c','ic','ta','rja'],['r5ci','h257z'],['r5co'])):
        for d in closure(source.document,roots):
            n=d['name'];e=source.entries[n]
            if n in imported:assert d==imported[n]['declaration'] and e['meaning_ja']==imported[n]['meaning_ja'],n
            else:doc['declarations'].append(d);imported[n]=e
    assert not (set(PRIMITIVES)|set(MEANINGS))&set().union(*(set(s.entries) for s in sources))
    doc=parse(format_graph(doc,'compact')+''.join('r '+n+v[0]+'.' for n,v in PRIMITIVES.items())+definitions());ds={d['name']:d for d in doc['declarations']}
    prims={n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=e['arguments'],meaning_ja=e['meaning_ja']) for n,e in imported.items() if e['kind']=='primitive'}
    prims.update({n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=v[1],meaning_ja=v[2]) for n,v in PRIMITIVES.items()})
    paths=set().union(*(set(s.source_sha256) for s in sources))
    basis=dict(status='cohort_three_progress_kinds_and_method_specific_continuations',document=LIBRARY,primitives=prims,
        definitions={n:e['meaning_ja'] for n,e in imported.items() if e['kind']=='definition'}|MEANINGS,
        imported_symbols={n:e['meaning_basis'] for n,e in imported.items()},import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)},limitations=LIMITS)
    return {LIBRARY:format_graph(doc,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n'}
