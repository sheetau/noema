"""Compose a large assessed shortfall in both current and attainable capacity."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT,closure
from scripts.compose_qualitative_influence import both
from scripts.compose_present_epoch_assessment import FRAME,ARGS,PEOPLE
from scripts.compose_topical_standing import ENABLING,EARGS
from scripts.compose_present_epoch_sentence import CURRENT,POINT,CTX,AUTHOR

PARENT='examples/v016/kant-present-epoch-sentence.noema';PARENT_BASIS='data/present-epoch-sentence-basis-v1.json'
FULL='examples/v016/kant-present-shortfall-sentence.noema';CORE='examples/v016/present-shortfall-sentence-core.noema'
BASIS='data/present-shortfall-sentence-basis-v1.json';ANNOTATIONS='data/present-shortfall-sentence-identifiers-v1.json'
ASSESS='group a reference d point d assessed h[a] e';AARGS='v group v reference v point v assessed'
GRADED=ASSESS+' capable h[a] e';GARGS=AARGS+' v capable'
SOURCE=FRAME+' topic a standardcontext i[d] '+ENABLING
SARGS=ARGS+' v topic v standardcontext '+EARGS
CURRENT_SUPPORT=CURRENT+' p h26lj p h26lk p h26ll'
CTYPE='i d[e]'
PRIMITIVES={
 'h26li':('[a d] b',['group','reference'],'同じ固定集団と解釈基準で、普及割合の到達基準h26kcからの不足が大きいとみなす最小の隔たり。結果を見る前に固定し、現在能力と能力状態へ置かれうる可能性の両分布に同じ尺度で適用する。正で到達基準以下という有効域はr5vaで確認する。原文に数値や一意の経験的閾値を補わない。'),
 'h26lj':('[a a d] c',['actor','person','reference'],'第七段落の同じ本人・元の現在基準で、本人を指定能力の状態へ置く実践上の手立ての実施者として検討する全範囲。個人・共同の実施者等を含め、成功する側や現に実施済みの側だけに絞らない。受動表現に特定の君主や必ず他人であるという条件を追加しない。範囲が既知の空であることと未知を区別する。'),
 'h26lk':('[a a a d] c',['actor','person','method','current'],'同じ現在の事情の下で、同じ実施者が本人に対して指定した手立てを実践上利用できる。学習・経験・機会や制度的な条件を整える等、能力状態へ置く方法の候補を扱う。現在の実施・成功・本人の既有能力は含めず、後の別の事情でのみ可能な方法を現在へ借りない。全ての結果はh26llで別に与える。'),
 'h26ll':('[a a a d d] c',['actor','person','method','current','result'],'同じ現在の事情から、指定実施者の同じ本人への同じ手立てを利用した場合に得られうる結果。成功する結果だけを選ばず、失敗も含む全結果を与える。各結果で元の主題・事項・質・参照を保った本人の能力を評価する。実施済み、全結果の成功、別人の獲得を含意しない。'),
 'h26lm':('[a a '+CTYPE+' '+CTYPE+' d d] c',['node','author','whole','evaluated','current','context'],'著者が同じ全体の対象評価を、指定した現在の事情に即して行うものとして提示する。利用可能な手立てと結果の範囲を同じ現在へ結び、あらゆる未来で不可能という無時制の一般化にしない。引用された評価の真理や現実の調査済みをこの提示だけで導かない。'),
 'h26ln':('[a a '+CTYPE+' '+CTYPE+' d d] c',['node','author','whole','attained','current','context'],'著者が同じ全体の内側で、指定の到達内容を現在の段階で既に実現しているという候補として取り上げる。外側の不足・否定の作用を保ち、実際の到達、現在より前の具体的時点の到達、通常より早いという数量的比較を補わない。'),
 'h26lo':('[a a '+CTYPE+' '+CTYPE+' '+CTYPE+' d] c',['node','author','whole','baseline','focus','context'],'著者が同じ全体の内側で、既に到達しているという基準側に対し、少なくともそこへ置かれうるという焦点側まで要求を下げて取り上げる。両側への外側の不足を保ち、焦点を実際の成功・唯一の条件・十分性としない。両命題間の全状況での論理的含意を取り立てだけから導かない。'),
 'h26lp':('[a a '+CTYPE+' '+CTYPE+' d d] c',['node','author','whole','target','current','context'],'著者が同じ目標に対する現在の不足を、解消を見込む評価の進行の中でなお残るものとして提示する。現状の不足の構成は全体内容に保持し、将来の必ずの解消、特定の以前の時点で同じ数値だけ不足していたという追加主張に替えない。'),
 'h26lq':('[a a '+CTYPE+' '+CTYPE+' '+CTYPE+' '+CTYPE+' d] c',['node','author','whole','first','second','alternatives','context'],'著者が同じ全体の不足の対象として、同じ二側を包含的な選択肢として提示する。alternativesは渡す二内容の選言であり、二側を満たす人々を先に合併して一つの分布へ替えない。排他性、どちらかの現実の成立、対象条件の真理を引用から導かない。'),
}
NODE_INFO={
 'h26lr':([148,412],'第二文全体の、既有能力とその状態へ置かれうることへの大きな不足。'),
 'h26ls':([166,193],'wie die Sachen jetzt stehenという現在の事情への限定。'),
 'h26lt':([215,220],'schonによる現在の段階での既到達という候補の取り立て。'),
 'h26lu':([238,280],'oder darin auch nur gesetzt werden könntenという可能性の側。'),
 'h26lv':([397,401],'nochによる不足がなお残るという提示。'),
 'h26lw':([385,412],'daran fehlt noch sehr viel.という前の二側への大きな不足。'),
 'h26lx':([249,257],'auch nurによる要求を下げた可能性の側への取り立て。'),
}
PRIMITIVES.update({n:('[] a',[],'固定原文kant-1784:u0014['+str(span[0])+','+str(span[1])+')の'+m) for n,(span,m) in NODE_INFO.items()})
MEANINGS={
 'r5va':'同じ人口・基準の到達閾値h26kcが有効で、不足の最小幅h26liが正かつその閾値以下である。大きな不足を任意の負数や到達不能な幅で判定しない。',
 'r5vb':'固定集団の非空・重複なしの完全列挙と全員の人間性、到達閾値の有効性、同じ点での全成員の評価を確認する。不足幅の基準はここには加えず、通常の到達も独立に評価できる。',
 'r5vc':'r5vbとr5vaが成立し、同じ全人口の能力割合に固定した大きな不足幅を足しても到達閾値を超えない。境界の幅も大きな不足へ含める明示的な最小幅の読み。単なる未到達・未知とは区別する。',
 'r5vd':'同じ現在人口・時代・宗教主題・質・元の現在基準で、現在能力r5tbと能力状態へ置かれうるr5tdの両分布がそれぞれ同じr5vcの大きな不足を持つ。r5taと全支援結果のr5tcを各側の評価に使う。個人別の選言を先に合併しない。',
 'r5ve':'r5vdの同じ現在と全設定を固定した第二文の不足内容。外側の評価点を現在と入れ替えず、将来にも決して可能にならないとは主張しない。',
 'r5vf':'同じ現在人口・時代・基準と宗教的な質付き能力について、全支援結果の評価が整い、能力状態へ置かれうる人の分布が同じ集団到達基準を満たす。人ごとに異なる実施者・方法・結果を許す普及の読みで、全員の同時達成を追加しない。',
 'r5vg':'第七段落第一文と同じ現在・人口・時代・主題・基準に全実施者範囲と現在の手立て・結果を供給したr5veの大きな不足内容。',
 'r5vh':'r5vgと同じ設定によるr5vfの、集団的に能力状態へ置かれうるという可能性の側。現在の能力の保有又は現実の支援成功とは区別する。',
 'r5vi':'同じ現在の既到達r5u2、又は同じ現在から能力状態へ置かれうるr5vhという二つの集団的内容の包含的選言。darin/daranが受ける対象をこの同じ能力状態と二側へ保つ。',
 'r5vj':'第二文全体と大きな不足の結びを同じ著者・第七段落の文脈へ帰属する。現在の事情、schonの既到達候補、oderの二側、auch nurの要求を下げた可能性、nochのなお残る不足、第一文からの順序を保持する。引用内容の真理を実行しない。',
}
LIMITS=[
 'u0014第二文[148,412)の223非空白文字を対象とする。第一文の同じ現在人口・時代・宗教領域・質付き能力と到達閾値を保持し、現在能力と能力状態へ置かれうる可能性を別々に評価する。',
 'im Ganzen genommenは既採用の有限人口の普及割合と固定した集団基準による。sehr vielの大きな不足は、その閾値からの隔たりが正の文脈的な最小幅以上という明示的な読み。数値、過半数、全員一致、唯一の歴史的尺度を原文へ補わない。',
 'daranの対象をA又はBという二つの集団的内容と読み、同じ幅で両方が大きく不足すると構成する。Aの人とBの人を混ぜた和集合の普及割合にはしない。この構成では未到達より強く、評価不足を不足へ変換しない。',
 'gesetzt werden könntenは、同じ現在の事情で実施者に利用可能な手立てと、その一つの同じ結果で本人の全関連事項の質付き能力が成立する可能性と読む。各人に異なる実施者・方法・結果を許し、全員を同時に到達させる一つの政策又は結果を必要条件にしない。',
 '全実施者・方法・結果の評価はr5tcで確認する。既知の空の実施者範囲は可能性なしだが未知ではない。実施者を特定の君主・他人に限定せず、実施済み・成功保証・現在の既有能力を支援可能性へ混ぜない。',
 'wie die Sachen jetzt stehenは現在の事情への限定。schonは現在に既に到達したという候補を不足の内側で取り上げる。auch nurは少なくとも能力状態へ置かれうる側へ要求を下げる提示であり、二側間の無条件な論理的含意を追加しない。',
 'nochは解消を見込む進行の中で不足がなお残るという提示と読む。特定の以前の時点の数値、未来の必ずの達成、永続的な不能を補わない。wären/könntenは不足の対象に置かれた未成立の到達と可能性を表し、実際の既達成や不可能な反事実という追加判断にはしない。',
 'sicher und gut、自分の理解力、他者の指導なし、宗教上の全関連事項はr5ta/tb/tc/tdの同じ実定義に保持する。受動のdarinと照応するdaranも同じ能力状態・二側へ結ぶ。原語の名前だけを能力内容にしない。',
 '有限の型・真偽・引数検査と原文の全語句照合・通読判断を区別する。第二文は明示した読みの下で確認するが、第三文の提示、最後の時代名、第七段落全体と二作品全体の完成は別に残る。',
]
@lru_cache(None)
def parent():return load_catalog(ROOT,PARENT_BASIS)
def definitions():
    theta='k h26kc[v group v reference]';margin='k h26li[v group v reference]'
    text='d r5va[group a reference d] c['+both('k r5tf[v group v reference]','k hc[n p a b '+margin+']','u[k hc['+theta+' '+margin+']]')+'].\n'
    checked='f person a[y[c['+PEOPLE+'][v person]][t[c[v assessed][v person]][v point]]]'
    text+='d r5vb['+ASSESS+'] c['+both('k r5te[v group v reference '+PEOPLE+']','k rcm[k mp[v group] '+PEOPLE+']','k r5tf[v group v reference]',checked)+'].\n'
    ratio='k pb[k mp[v group] i[person a][t[c[v capable][v person]][v point]]]'
    text+='d r5vc['+GRADED+'] c['+both('k r5vb['+AARGS+']','k r5va[v group v reference]','u[k hc['+theta+' k ha['+ratio+' '+margin+']]]')+'].\n'
    topic='v topic v point v standardcontext'
    current='k r5vc[v group v reference v point k r5ta['+topic+'] k r5tb['+topic+']]'
    support='k r5vc[v group v reference v point k r5tc['+topic+' '+EARGS+'] k r5td['+topic+' '+EARGS+']]'
    text+='d r5vd['+SOURCE+'] c['+both('k r5sc['+ARGS+']',current,support)+'].\n'
    text+='d r5ve['+SOURCE+'] e[b outer[k r5vd['+SARGS+']]].\n'
    mask='i[person a][t[c[k r5td['+topic+' '+EARGS+']][v person]][v point]]'
    text+='d r5vf['+SOURCE+'] c['+both('k r5sc['+ARGS+']','k r5vb[v group v reference v point k r5tc['+topic+' '+EARGS+']]','k r5tg[v group v reference '+PEOPLE+' '+mask+' v point]')+'].\n'
    text+='d r5vg[] e[k r5ve['+CURRENT_SUPPORT+']].\n'
    text+='d r5vh[] e[b outer[k r5vf['+CURRENT_SUPPORT+']]].\n'
    text+='d r5vi[] e[b outer[x[t[k r5u2[]][v outer]][t[k r5vh[]][v outer]]]].\n'
    whole='r d[k r5vg[]]';first='r d[k r5u2[]]';second='r d[k r5vh[]]';alternatives='r d[k r5vi[]]';head=AUTHOR+' '+whole+' '
    parts=['k h236i[k h26lr[] '+AUTHOR+' '+whole+' '+CTX+']','k h236i[k h26lw[] '+AUTHOR+' '+whole+' '+CTX+']',
      'k h26lm[k h26ls[] '+head+alternatives+' '+POINT+' '+CTX+']',
      'k h26ln[k h26lt[] '+head+first+' '+POINT+' '+CTX+']',
      'k h26lq[k h26lu[] '+head+first+' '+second+' '+alternatives+' '+CTX+']',
      'k h26lo[k h26lx[] '+head+first+' '+second+' '+CTX+']',
      'k h26lp[k h26lv[] '+head+alternatives+' '+POINT+' '+CTX+']']
    for a,b in (('h26la','h26lr'),('h26lt','h26lu'),('h26lu','h26lw')):parts.append('k ue[k '+a+'[] k '+b+'[] '+CTX+']')
    nodes=('h26la',*NODE_INFO)
    parts+=['u[e[k '+a+'[]][k '+b+'[]]]' for i,a in enumerate(nodes) for b in nodes[i+1:]]
    text+='d r5vj[] c['+both(*parts)+'].\n';return text
def build():
    old=parent();doc=deepcopy(old.document);statements,doc['statements']=doc['statements'],[]
    assert not(set(PRIMITIVES)|set(MEANINGS))&set(old.entries)
    doc=parse(format_graph(doc,'compact')+''.join('r '+n+row[0]+'.' for n,row in PRIMITIVES.items())+definitions());added=doc['declarations'][len(old.document['declarations']):]
    new=dict(kind='assert',body=dict(kind='call',symbol='r5vj',arguments=[]));doc['statements']=statements+[new]
    core=deepcopy(doc);core.update(declarations=closure(doc,list(MEANINGS)),statements=[new]);ds={d['name']:d for d in added}
    prims={n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=row[1],meaning_ja=row[2]) for n,row in PRIMITIVES.items()}
    basis=dict(status='present_shortfall_sentence_under_explicit_reading',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,
        definitions=MEANINGS,primitives=prims,new_signatures={d['name']:{k:d[k] for k in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';annotations=json.loads((ROOT/'data/present-epoch-sentence-identifiers-v1.json').read_text(encoding='utf-8'))
    annotations.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(annotations)}
