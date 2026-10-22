"""Give all fixed faculties room to reach their task range within one regime."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT,closure
from scripts.compose_qualitative_influence import both
from scripts.compose_civic_regime_barriers import STATE,CONTEXT,FIELDS,ARGS,FALSE

PARENT='data/civic-regime-barriers-basis-v1.json'
MAIN='data/whole-view-sentence-basis-v1.json'
LIBRARY='examples/v016/faculty-development-room.noema';BASIS='data/faculty-development-room-basis-v1.json'
SCOPE='community a order a person a faculty a reference d start d'
SCOPE_NAMES=('community','order','person','faculty','reference','start')
SCOPE_ARGS=' '.join('v '+n for n in SCOPE_NAMES)
PRIMITIVES={
 'h26zb':('[a a a d] c',['community','person','faculty','reference'],'同じ共同体の本人について対象とする精神的能力の全範囲。ここでは自分の悟性を用いた判断の働き・資源として個別化し、所有abと使用acを別に確認する。基準で固定し、現在の成功・許可の有無や後の発展結果に合わせて選別しない。'),
 'h26zc':('[a a a d] c',['person','faculty','task','reference'],'本人のこの能力が展開し得る関連判断課題の全範囲。能力の潜在的な働きと議論の文脈に相対的に基準で固定し、現在の達成可能性と区別する。結果から成功した課題だけを残さず、比較中に他の人・能力の課題へ取り替えない。'),
 'h26zd':('[a a d d d d] c',['community','order','reference','start','end','point'],'この開始点から候補終点へ発展する一つの履歴の全状況。開始点と終点を含む時間順序を合成側で検査し、中間の制度変更を隠すために状況を除外しない。代替的な結果の履歴を一つの直線上に置かず、開始と終点の組ごとに固定する。'),
 'h26ze':('[a a d d d d d] c',['community','order','reference','start','end','left','right'],'同じ候補発展履歴内でleftがrightに時間的に先行する関係。taで厳密な時間順序を検査する。高い側と低い側の制度の大小関係とは異なる。'),
 'h26zf':('[a a a a d a a d] c',['community','order','person','faculty','reference','actor','method','start'],'同じ共同体・法秩序・本人・能力・固定基準で、actorが開始点で利用できる発展方法。課題を遂行する方法と区別し、能力範囲を展開するための方法を指定する。外側の本人を固定してもコールバックのactorを無視しない。'),
 'h26zg':('[a a a a d a a d d] c',['community','order','person','faculty','reference','actor','method','start','outcome'],'同じ発展方法から生じ得る結果状況の全範囲。固定した能力の発展の候補であり、結果で制度・本人・課題範囲を替えない。成功した結果だけを可能性として選ばない。'),
 'h26zh':('[a a a a d a a d d] c',['community','order','person','faculty','reference','actor','method','start','outcome'],'同じ発展方法の可能な結果のうち、達成の評価に用いる範囲。空又は可能範囲外の結果は既存xdが拒否する。対象を成功結果だけへ事後選別せず、未評価を不能としない。'),
}
MEANINGS={
 'r6hy':'同じ本人・能力・課題・基準の判断目標。非空の全事項に、課題に属し理由に支えられ他人の指導を受けない本人の判断があり、その判断に使う本人所有の悟性資源をこの能力に一致させる。別能力の成功では代用しない。',
 'r6hz':'同じ人間の成員と指定能力・課題・非空の事項範囲を保持し、r6hyの目標に達する課題遂行方法がその状況であるというxd。現在実際に判断したこととは区別する。',
 'r6h2':'r6hzと同じ本人・能力・課題範囲と目標へのxfの評価。未評価の方法を、開始時の未展開又は達成不能へ読み替えない。',
 'r6h3':'本人の同じ能力を開始・終点で所有し、非空の固定課題範囲を両時点で評価でき、終点では全課題を達成できる。非空の厳密な時間履歴に両端を含み開始が先行する。全履歴で同じ法秩序を運用し、全関連市民的行為の許可集合を開始点と一致させる。個別能力ごとの厳密増加は要求しない。',
 'r6h4':'同じ共同体・法秩序・本人・能力・基準・開始点を固定し、候補結果状況でr6h3となる発展目標内容。別の制度への移行を成功へ混ぜない。',
 'r6h5':'本人が開始時に所有する指定能力の非空の課題範囲について、r6h4へ至るxdの発展方法がある。課題の実行方法と発展方法を分離する。現在既に展開したことや実際に方法を選ぶことは主張しない。',
 'r6h6':'非空の全人間成員がそれぞれ非空の能力範囲を持ち、その全能力にr6h5の展開又は維持の機会がある。全体には評価済みでまだ達成機会のない課題が少なくとも一つある。既に全課題を行使できる能力には維持を認め、各能力の厳密増大や全員共通の一つの方法を要求しない。',
 'r6h7':'同じ二制度の因果対応r6huを保持し、現在の低い側と、低い側を選ぶ介入の非空の全解でr6h6の余地がある。全て同じ低い側の法秩序・人・能力・課題範囲・基準を保つ。高い側にいかなる発展機会もないとは主張しない。',
 'r6ia':'同じ比較で制限対象となる全ての人・課題が、その人の指定能力の固定課題範囲のいずれかに含まれる。制限と展開の対象を無関係に置かず、前段r6hwが要求する非空の制限対象を落とさない。',
 'r6ib':'同じ観点・共同体・二法秩序・基準・比較起点で、r6hxの有利に見える内容と制限、r6h7の低い側での全能力への発展の余地、r6iaの対象接続を連言する。第三文の命題的な依存群であり、対照の提示・照応・全文帰属は別途統合する。',
}
LIMITS=[
 'u0017第三文後半verschaft hingegen diesem Raum, sich nach allem seinen Vermögen auszubreitenの依存群。Geist des Volksを同じ民衆の各人の自分の悟性による判断の働きへ分配し、Vermögenをその関連能力の全範囲と読む。語の唯一の歴史的意味や全精神機能の哲学的定義を主張しない。',
 'Raumは空間の広さではなく、同じ制度の下で能力の固定した潜在的課題範囲へ展開できる機会と読む。各能力の全課題を終点で行使できるという強い到達条件を明示する。量的強度・質・熟練の増加を別に数値化せず、実際の発展や実行を要求しない。',
 '既に行使できる能力には維持を認める。全体には評価済みで未達の課題が少なくとも一つあることを要求するが、全員・全能力がそれぞれ厳密に増加するという旧faculty-opportunitiesの条件を継承しない。人・能力ごとに別の方法と結果時点でよく、同時の共同計画の存在は主張しない。',
 '能力所有とその使用を判断目標で実評価する。同じ人・能力・事項・理由の関係を保ち、他能力・他人の判断で代用しない。課題遂行の方法と、課題を行使できる範囲を展開する方法を区別する。',
 '開始と終点で評価済みであり、終点の全課題の機会を要求する。途中に一時的に課題の機会が減らないことまでは要求しないが、全履歴で同じ法秩序の運用と同じ市民的許可集合を保ち、制度を変えた成功を排除する。履歴と順序の適合は全状況を提供する入力規約を含む。',
 '低い側の現在とその介入の非空の全解で余地があるという、明示した構造方程式モデル内の強い条件付きの制度的可能化である。高い側で全発展が不可能という比較は追加しない。前段の制限対象をこの能力・課題範囲へ接続するが、低い側で即座に全能力を行使できることは要求しない。',
 'doch/hingegenの対照提示、jener/diesemの照応、全文帰属と通読は未完。この依存群の検査から第三文の意味確認文字数を増やさない。',
]
@lru_cache(None)
def parent():return load_catalog(ROOT,PARENT)
@lru_cache(None)
def main_catalog():return load_catalog(ROOT,MAIN)

def definitions():
    goal=both('k h26yu[v person v task v judgment v reference v point]','k fb[v judgment v matter v point]',
      'k rcr[v person v judgment v point i[resource a owner a point d]['+both('e[v resource][v faculty]','k ab[v resource v owner v point]')+'] p ac p fa p fb p fc p fd p ad]')
    text='d r6hy[person a faculty a task a reference d] e[b point['+both('k aa[v person]',
      'g matter a[k h26yt[v task v matter v reference]]',
      'f matter a[y[k h26yt[v task v matter v reference]][g judgment a['+goal+']]]')+']].\n'
    scope=both('k r6hd[v person v community v reference]','k h26zb[v community v person v faculty v reference]',
      'k h26zc[v person v faculty v task v reference]','k h26ys[v community v person v task v reference]',
      'g matter a[k h26yt[v task v matter v reference]]')
    providers=' '.join(('i[actor a method a point d][k h26yv[v community v task v reference v actor v method v point]]',
      'i[actor a method a point d outcome d][k h26yw[v community v task v reference v actor v method v point v outcome]]',
      'i[actor a method a point d outcome d][k h26yx[v community v task v reference v actor v method v point v outcome]]'))
    for n,ability in (('r6hz','xd'),('r6h2','xf')):
        text+='d '+n+'[community a person a faculty a task a reference d point d] c['+both(scope,
          'k '+ability+'[v person k r6hy[v person v faculty v task v reference] v point '+providers+']')+'].\n'
    membership='k r6hd[v person v community v reference]';faculty='k h26zb[v community v person v faculty v reference]'
    tasks='k h26zc[v person v faculty v task v reference]';nonempty='g task a['+tasks+']'
    history='k h26zd[v community v order v reference v start v end v point]'
    before='k h26ze[v community v order v reference v start v end v left v right]'
    def assessment(n,point):return 'k '+n+'[v community v person v faculty v task v reference v '+point+']'
    def option(point):return 'k r6hf[v community v order v citizen v activity v reference v '+point+']'
    keep='f citizen a[f activity a[y[k r6he[v community v citizen v activity v reference]][e['+option('point')+']['+option('start')+']]]]'
    text+='d r6h3['+SCOPE+' end d] c['+both(membership,faculty,'k ab[v faculty v person v start]','k ab[v faculty v person v end]',nonempty,
      'f task a[y['+tasks+']['+both(assessment('r6h2','start'),assessment('r6h2','end'),assessment('r6hz','end'))+']]',
      'k ta[i[point d]['+history+'] i[left d right d]['+before+']]',
      'k h26zd[v community v order v reference v start v end v start]',
      'k h26zd[v community v order v reference v start v end v end]',
      'k h26ze[v community v order v reference v start v end v start v end]',
      'f point d[y['+history+']['+both('k r6fr[v community v order v reference v point]',keep)+']]')+'].\n'
    text+='d r6h4['+SCOPE+'] e[b end[k r6h3['+SCOPE_ARGS+' v end]]].\n'
    develop=' '.join('i[actor a method a point d'+(' outcome d' if n!='h26zf' else '')+'][k '+n+'[v community v order v person v faculty v reference v actor v method v point'+(' v outcome' if n!='h26zf' else '')+']]' for n in ('h26zf','h26zg','h26zh'))
    text+='d r6h5['+SCOPE+'] c['+both(membership,faculty,'k ab[v faculty v person v start]',nonempty,
      'k xd[v person k r6h4['+SCOPE_ARGS+'] v start '+develop+']')+'].\n'
    room=both('g faculty a['+faculty+']','f faculty a[y['+faculty+'][k r6h5['+SCOPE_ARGS+']]]')
    unfulfilled=both(membership,faculty,tasks,assessment('r6h2','start'),'u['+assessment('r6hz','start')+']')
    text+='d r6h6[community a order a reference d start d] c['+both('g person a['+membership+']',
      'f person a[y['+membership+']['+room+']]','g person a[g faculty a[g task a['+unfulfilled+']]]')+'].\n'
    variables='k h26y3['+ARGS+']';factor='k h26y5['+ARGS+']'
    equations='i[variable a state '+STATE+'][k h26y4['+ARGS+' v variable v state]]'
    text+='d r6h7['+FIELDS+'] c['+both('k r6hu['+ARGS+']',
      'k r6h6[v community v lowerorder v reference k h26yy[v community v reference v anchor]]',
      'k rw['+variables+' '+equations+' i[variable a][e[v variable]['+factor+']] i[variable a]['+FALSE+'] i[state '+STATE+'][k r6h6[v community v lowerorder v reference k h26y6['+ARGS+' v state]]]]')+'].\n'
    text+='d r6ia['+FIELDS+'] c[f person a[f task a[y[k h26za['+ARGS+' v person v task]][g faculty a['+both(faculty,tasks)+']]]]].\n'
    text+='d r6ib[observer a community a lowerorder a higherorder a reference d] e[b anchor['+both(
      't[k r6hx[v observer v community v lowerorder v higherorder v reference]][v anchor]',
      'k r6h7['+ARGS+']','k r6ia['+ARGS+']')+']].\n'
    return text

def build():
    p=parent();m=main_catalog();doc=deepcopy(p.document);doc['statements']=[];imported=dict(p.entries)
    for d in closure(m.document,('ta',)):
        n=d['name'];e=m.entries[n]
        if n in imported:assert d==imported[n]['declaration'] and e['meaning_ja']==imported[n]['meaning_ja'],n
        else:doc['declarations'].append(d);imported[n]=e
    assert not(set(PRIMITIVES)|set(MEANINGS))&set(imported)
    doc=parse(format_graph(doc,'compact')+''.join('r '+n+r[0]+'.' for n,r in PRIMITIVES.items())+definitions());by={d['name']:d for d in doc['declarations']}
    prims={n:dict(parameters=by[n]['parameters'],result=by[n]['result'],arguments=e['arguments'],meaning_ja=e['meaning_ja']) for n,e in imported.items() if e['kind']=='primitive'}
    prims.update({n:dict(parameters=by[n]['parameters'],result=by[n]['result'],arguments=r[1],meaning_ja=r[2]) for n,r in PRIMITIVES.items()})
    paths=set(p.source_sha256)|set(m.source_sha256)
    basis=dict(status='same_regime_all_faculties_development_room_partial',document=LIBRARY,primitives=prims,
      definitions={n:e['meaning_ja'] for n,e in imported.items() if e['kind']=='definition'}|MEANINGS,
      imported_symbols={n:e['meaning_basis'] for n,e in imported.items()},
      import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)},limitations=LIMITS)
    return {LIBRARY:format_graph(doc,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n'}
