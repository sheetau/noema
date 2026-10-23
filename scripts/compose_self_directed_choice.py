"""Distinguish reason-directed acting/refraining and standing ability under liberty."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT,closure
from scripts.compose_qualitative_influence import both

PARENT='data/civic-spirit-sentence-basis-v1.json'
PROFILE_BASIS='data/civic-disposition-profile-basis-v1.json'
LIBRARY='examples/v016/self-directed-choice.noema';BASIS='data/self-directed-choice-basis-v1.json'
TRUE='e[n p a b][n p a b]';FALSE='u['+TRUE+']'
FIELDS='community a reference d person a activity a';ARGS='v community v reference v person v activity'
PRIMITIVES={
 'h27cr':('[a a a c d d] c',['person','activity','judgment','positive','reference','point'],'同じ本人の実践的判断が、同じ固定基準と状況で、指定行為を行う又は控えるという極性の結論を持つ。判断の対象への言及、本人の理解力・理由の使用と他人の指導の不在はrcrとfbで別に構成する。活動の名称だけから判断内容を補わない。'),
 'h27cs':('[a a a c d d] c',['person','judgment','activity','positive','reference','point'],'本人の指定判断が、同じ状況で、指定行為を行う又は控える本人自身の決定とその遂行を実際に導いている。理由を述べただけ、後からの口実、偶然の不実行、睡眠や不能による不実行、別人に身体を動かされただけの場合は含めない。実際の行為の成立又は不成立は別に照合する。'),
 'h27ct':('[a d a a d d] c',['community','reference','person','activity','anchor','candidate'],'基準点の本人について、同じ市民的行為を自分で行う又は控える能力を比較する全場面。自由な選択の外的条件を与えた場面として固定し、成功する場面だけを選ばない。基準点での現実の許可や実行とは分ける。'),
 'h27cu':('[a d a a d d] c',['community','reference','person','activity','anchor','candidate'],'この比較場面は基準点の本人の関連した理解・判断・身体的技能・習慣等の既有基盤を保つ。新たな訓練、別人の能力、強い補助を与えて能力の有無を作らない。成長を比較する二つの基準点の基盤まで同一とはしない。'),
 'h27cv':('[a d a a d d d] c',['community','reference','person','activity','anchor','preferred','other'],'同じ能力比較の外的な妨害や課題条件から、preferredをotherより通常とする厳密な優先関係。能力の成否から優先順位を定めない。rqt4で比較の整合性と極小候補の非空性を確認する。'),
 'h27cw':('[a d a a] a',['community','reference','person','activity'],'同じ本人・市民的行為について、自由な選択を認めた比較場面を構成する法秩序。結果又は評価点によって選び直さず、同じ共同体の秩序としてr6frで運用を確認する。実際の低い制度が既に拡大したという主張ではない。'),
 'h27cx':('[a d a a a d] c',['community','reference','activity','actor','method','point'],'固定した共同体・行為・基準の能力比較で、この本人がこの場面で利用できる方法。方法は本人による実行又は意図的な不実行を実現する手順であり、規範上許されることや現に採ったことだけと同一視しない。'),
 'h27cy':('[a d a a a d d] c',['community','reference','activity','actor','method','point','outcome'],'同じ本人・行為・方法・起点の下で、その方法を採る場合の全候補結果状況。実行側と控える側で同じ方法空間と評価条件を使い、結果に応じて別人・別行為・別基準へ交換しない。'),
 'h27cz':('[a d a a a d d] c',['community','reference','activity','actor','method','point','outcome'],'同じ方法と起点の候補のうち、明示した能力比較で評価する全結果状況。目的に合う結果だけを後から選ばず、xa/xe/xfで非空性と候補の整合を検査する。未知を成功又は不能へ補わない。'),
 'h27c2':('[a d a] j[a]',['community','reference','person'],'同じ民衆の本人について、h26yoで固定した関連する市民的行為の全有限列。成功・許可・途中の能力に応じて選び直さず、r6koで非空・重複なし・全範囲との一致を要求する。'),
 'h27c3':('[a d a a] b',['community','reference','person','activity'],'同じ人と行為の組に先に割り当てる正の有理重み。自分で行う・控える能力の広がりを比較する尺度であり、結果に応じた再重み付けや特定人の改善だけの選別をしない。心理的応答特徴の重みh27cgとは別。'),
 'h27c4':('[a d] b',['community','reference'],'同じ民衆と固定した能力尺度で一段階に許す変化量の正の上限。観測された飛躍に合わせて後から増やさない。心的応答傾向の上限h27cjと同一の数値とは限らない。'),
}
MEANINGS={
 'r6kg':'同じ本人が指定行為を実際に遂行する内容。行為の発生dgと同じ本人の能動的参加dfを連言する。単なる発生や別人の実行を本人の実行としない。',
 'r6kh':'同じ本人が、自分の理解力と支持理由による他人の指導を受けない実践的判断を持ち、その判断が同じ行為の指定極性を結論とし、その決定・遂行を実際に導く内容。正極性ならr6kg、負極性ならその否定を照合する。控える内容自体が積極的な判断と決定を含み、行う内容の単なる否定ではない。',
 'r6ki':'同じ共同体の本人・行為について、比較用に固定した法秩序が運用され、同じ規範的出所・市民の立場・実行記述に、正負双方の積極的許可と反対極性の要求の不在がある。能力評価の外的背景であり、現実の基準点の許可や能力そのものではない。',
 'r6kj':'r6kiの自由な選択の背景で、同じ本人・行為の自分の判断に従う実行と控えの二つの目標について、同じ方法空間のxf評価条件が成立する。評価の欠落を能力の欠如へ変換しない。',
 'r6kk':'r6kjと同じ条件で、自分の判断に従う実行と控えの各内容を満たすxdの方法がそれぞれある。異なる二方法でよく、一方法で矛盾する二結果を同時に達成させない。',
 'r6kl':'同じ本人・行為・基準点の全比較場面で本人の既有基盤が保持され、r6kjで評価でき、通常性の比較が整っている。基準点で能力が成立したという結論はまだ要求しない。',
 'r6km':'r6klのもとで、全ての極小通常場面にr6kkが成立する既有の実践的選択能力。例外的な場面での失敗を許し、現実に行為したことや現在の法的自由の増大は含意しない。',
 'r6kn':'同じ共同体・基準を保った本人と行為の二引数について、基準点ごとのr6kmを返す内容族。後続の民衆の能力増加と心的変化による媒介へ渡す入口。',
 'r6ko':'同じ民衆の全人間成員と各人の全市民的行為を非空・重複なしで列挙し、各組の固定重みを正とする。途中で構成員や行為を落として能力の増加を作らない。',
 'r6kp':'同じ全成員・全行為の組でr6kmの既有能力がある場合の固定重みの総和。現在の許可や行為の実績を数えず、同じ能力範囲の広がりを集団について比較する。',
 'r6kq':'同じ全区間の厳密な順序と両端を確認し、区間内の全人・全行為・全時点でr6klの能力評価が整うことを要求する。評価の欠落を不能や増加へ変えない。',
 'r6kr':'r6kqの同じ尺度で終点の能力得点が始点より高く、その間に厳密に中間の得点を持つ時点がある。固定上限より大きい上昇又は下降を持つ任意の二点の間にもその方向の中間得点を要求する。局所的な後退・停滞や個人間の増減を許し、全員の単調改善は要求しない。',
 'r6ks':'同じ民衆・基準・開始点を保って、終点ごとのr6krの漸次的な能力増加を返す内容。心的変化による原因又は媒介はまだ含まない。',
}
LIMITS=[
 'Freiheit zu handelnへの能力を、自由な選択が認められる比較条件で、自分の理由に基づく判断に従い行う又は控えられる既有の実践的能力として読む。単に動作できること、許可の件数の増加、現に行為したことと分ける。',
 '自分の判断の使用はrcrを再利用し、行為についての結論と決定を導く関係を別に結ぶ。絶対的に正しい判断、完全な道徳性、他者から何も学ばないこと、形而上学的な自由意志の証明は追加しない。',
 '控える側にも本人の判断と意図的な決定を要求する。旧rxcの目標とその単純否定を、そのまま自立的な実行と控えの二内容へ読み替えない。二内容は両方偽になり得るが、同じ状況で両方真にはならない。',
 '比較用の同じ法秩序・公的な規範的出所・市民の立場で、同じ閉じた実行内容への正負双方の許可を確認する。自由な比較場面を与えることと、実際の法秩序が既に自由を拡大したことは別である。',
 '全比較場面で本人の既有基盤を保ち、通常場面全体での能力を使う。未知入力を偽とせず、成功する場面や方法の結果だけを事後に選ばない。有限比較の範囲と通常性は公開する解釈条件。',
 '後年のAA VI 188注は、自由において自分の力を用いることと成熟の比較資料として保存した。1784年の文の唯一の語義に置き換えず、後年の政治的主張や道徳的な責任の全理論を今回の文へ追加しない。',
 'fähigerを同じ全成員・全関連行為についての正の重み付き能力範囲が広がることとする。個人全員の改善、共通の一つの実行計画、技能の強度や成功確率の全意味は追加しない。有限の行為範囲・重み・段階上限は公開する解釈入力であり、原文が数値を指定しているとはしない。',
 'nach und nachは正の終点増加と中間得点、固定上限を超す変化への中間値によって構成する。停滞や局所的後退を許す。wodurchの心的変化による媒介、Wenn/so全体、政府原則以降・全文帰属は後続で接続し、括弧文全体の意味確認文字数は増やさない。',
]
@lru_cache(None)
def parent():return load_catalog(ROOT,PARENT)
@lru_cache(None)
def profile_catalog():return load_catalog(ROOT,PROFILE_BASIS)

def definitions():
    text='d r6kg[person a activity a] e[b point['+both('k dg[v activity v point]','k df[v person v activity v point]')+']].\n'
    judged='k rcr[v person v judgment v point p ab p ac p fa p fb p fc p fd p ad]'
    execution='t[k r6kg[v person v activity]][v point]'
    text+='d r6kh[person a activity a reference d positive c] e[b point['+both('k aa[v person]',
      'g judgment a['+both(judged,'k fb[v judgment v activity v point]',
      'k h27cr[v person v activity v judgment v positive v reference v point]',
      'k h27cs[v person v judgment v activity v positive v reference v point]')+']','z['+execution+'][v positive]')+']].\n'
    source='k h26yp[k h27cw['+ARGS+'] v community v reference v point]';role='k h26yq[v community v person v reference]'
    allowed=lambda sign:'k rdm['+source+' v person '+role+' v activity r[p r6kg] '+sign+' v point p h7a p h7b]'
    selected='k r6he[v community v person v activity v reference]'
    text+='d r6ki['+FIELDS+' point d] c['+both(selected,'k r6fr[v community k h27cw['+ARGS+'] v reference v point]',allowed(TRUE),allowed(FALSE))+'].\n'
    providers=' '.join(('i[actor a method a at d][k h27cx[v community v reference v activity v actor v method v at]]',
      'i[actor a method a at d outcome d][k h27cy[v community v reference v activity v actor v method v at v outcome]]',
      'i[actor a method a at d outcome d][k h27cz[v community v reference v activity v actor v method v at v outcome]]'))
    ability=lambda base,sign:'k '+base+'[v person k r6kh[v person v activity v reference '+sign+'] v point '+providers+']'
    text+='d r6kj['+FIELDS+' point d] c['+both('k r6ki['+ARGS+' v point]',*[ability('xf',sign) for sign in (TRUE,FALSE)])+'].\n'
    text+='d r6kk['+FIELDS+' point d] c['+both('k r6kj['+ARGS+' v point]',*[ability('xd',sign) for sign in (TRUE,FALSE)])+'].\n'
    fixed=ARGS+' v anchor';cases='i[candidate d][k h27ct['+fixed+' v candidate]]'
    order='i[left d right d][k h27cv['+fixed+' v left v right]]'
    text+='d r6kl['+FIELDS+' anchor d] c['+both(selected,
      'f candidate d[y[k h27ct['+fixed+' v candidate]]['+both('k h27cu['+fixed+' v candidate]','k r6kj['+ARGS+' v candidate]')+']]',
      'k rqt4['+cases+' '+order+' i[candidate d]['+TRUE+']]')+'].\n'
    text+='d r6km['+FIELDS+' anchor d] c['+both('k r6kl['+fixed+']','k rqt4['+cases+' '+order+' i[candidate d][k r6kk['+ARGS+' v candidate]]]')+'].\n'
    text+='d r6kn[community a reference d] h[a a] e[i[person a activity a][b anchor[k r6km['+ARGS+' v anchor]]]].\n'
    c='v community v reference';pop='k h27b5['+c+']';acts='k h27c2['+c+' v person]';zero='n p a b'
    member='k r6hd[v person v community v reference]';act='k h26yo[v community v person v activity v reference]'
    each=lambda body:'f person a[y['+member+'][f activity a[y['+act+']['+body+']]]]'
    text+='d r6ko[community a reference d] c['+both('k rcm['+pop+' i[person a]['+member+']]',
      'f person a[y['+member+'][k rcm['+acts+' i[activity a]['+act+']]]]',each('k hc['+zero+' k h27c3['+ARGS+']]'))+'].\n'
    score='q['+acts+']['+zero+'][i[subtotal b activity a][k ha[v subtotal k hb[k h27c3['+ARGS+'] k hd[k r6km['+ARGS+' v point]]]]]]'
    text+='d r6kp[community a reference d point d] b[q['+pop+']['+zero+'][i[total b person a][k ha[v total '+score+']]]].\n'
    hist='i[point d][k h27ch['+c+' v start v end v point]]';order='i[left d right d][k h27ci['+c+' v start v end v left v right]]'
    inside=lambda p:'c[k rlz['+hist+' '+order+' v start v end]][v '+p+']'
    before=lambda a,b:'k h27ci['+c+' v start v end v '+a+' v '+b+']'
    text+='d r6kq[community a reference d start d end d] c['+both('k r6ko['+c+']','k ta['+hist+' '+order+']',
      'k h27ch['+c+' v start v end v start]','k h27ch['+c+' v start v end v end]',before('start','end'),
      'f point d[y['+inside('point')+']['+each('k r6kl['+ARGS+' v point]')+']]')+'].\n'
    score=lambda p:'k r6kp['+c+' v '+p+']'
    middle=lambda a,b,up:'g middle d['+both(inside('middle'),before(a,'middle'),before('middle',b),
      'k hc['+score(a if up else b)+' '+score('middle')+']','k hc['+score('middle')+' '+score(b if up else a)+']')+']'
    limits=[]
    for up in (True,False):
        low,high=('left','right') if up else('right','left')
        large=both(inside('left'),inside('right'),before('left','right'),'k hc[k ha['+score(low)+' k h27c4['+c+']] '+score(high)+']')
        limits.append('f left d[f right d[y['+large+']['+middle('left','right',up)+']]]')
    text+='d r6kr[community a reference d start d end d] c['+both('k r6kq['+c+' v start v end]','k hc['+zero+' k h27c4['+c+']]',
      'k hc['+score('start')+' '+score('end')+']',middle('start','end',True),*limits)+'].\n'
    text+='d r6ks[community a reference d start d] e[b end[k r6kr['+c+' v start v end]]].\n'
    return text

def build():
    p=parent();doc=deepcopy(p.document);doc.update(declarations=closure(p.document,('r6he','r6fr','rdm','rcr','xd','xf','rqt4','dg','df','h7a','h7b','h26yp','h26yq','ab','ac','fa','fb','fc','fd','ad','rcm','ta','rlz','hb')),statements=[])
    imports={d['name']:p.entries[d['name']] for d in doc['declarations']}
    for d in closure(profile_catalog().document,('h27b5','h27ch','h27ci')):
        n=d['name'];e=profile_catalog().entries[n]
        if n in imports:assert d==imports[n]['declaration'] and e['meaning_ja']==imports[n]['meaning_ja']
        else:doc['declarations'].append(d);imports[n]=e
    assert not(set(PRIMITIVES)|set(MEANINGS))&set(p.entries)
    doc=parse(format_graph(doc,'compact')+''.join('r '+n+r[0]+'.' for n,r in PRIMITIVES.items())+definitions());by={d['name']:d for d in doc['declarations']}
    prims={n:dict(parameters=by[n]['parameters'],result=by[n]['result'],arguments=e['arguments'],meaning_ja=e['meaning_ja']) for n,e in imports.items() if e['kind']=='primitive'}
    prims.update({n:dict(parameters=by[n]['parameters'],result=by[n]['result'],arguments=r[1],meaning_ja=r[2]) for n,r in PRIMITIVES.items()})
    basis=dict(status='reason_directed_standing_choice_capacity_partial',document=LIBRARY,primitives=prims,
      definitions={n:e['meaning_ja'] for n,e in imports.items() if e['kind']=='definition'}|MEANINGS,
      imported_symbols={n:e['meaning_basis'] for n,e in imports.items()},import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(set(parent().source_sha256)|set(profile_catalog().source_sha256))},limitations=LIMITS)
    return {LIBRARY:format_graph(doc,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n'}
