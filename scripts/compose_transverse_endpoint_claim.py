"""Connect the physical-meaning question, selected rod and both endpoint displays."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_transverse_segment import ROOT,read
from scripts.compose_material_relative_frame import define
from scripts.compose_two_postulates import quote
from scripts.compose_relativity_conjecture import content
from scripts.compose_rod_methods import interval
from scripts.compose_limits import R,v,call as k,app,op,both,quant as q

PARENT='examples/v014/einstein-transverse-segment.noema';PARENT_BASIS='data/transverse-segment-basis-v1.json'
FULL='examples/v014/einstein-transverse-endpoint-claim.noema';CORE='examples/v014/transverse-endpoint-claim-core.noema'
BASIS='data/transverse-endpoint-claim-basis-v1.json';ANNOTATIONS='data/transverse-endpoint-claim-identifiers-v1.json';INDICES=(315,316,317)
PRIMITIVES={
 'eisnx':([('node','a'),('author','a'),('object','a'),('characterization','i[e]'),('scope','a'),('reference','d')],'authorがnodeでobjectを、characterizationに記述された対象としてscopeの考察へ取り上げ、注意をその対象へ向ける論述行為。記述は同じ対象の特徴・設定を指定し、合成側がobjectとの同一参照を保つ。視覚的な目撃、材料の切断、実験の実行、記述内容の真理や考察目的の達成を含意しない。仮定の採用や結果の断言とは別の提示関係。'),
 'eisny':([], 'u0097のコロンに続く両端座標表示の第一項。η=l側の端1の三座標を提示する箇所の識別子。'),
 'eisnz':([], '同じ両端座標表示の第二項。undに続くη=0側の端2の三座標を提示する箇所の識別子。'),
}
MEANINGS={
 'ejcg':'同じ棒・端標識・出来事・文脈について、Kとkの現在記録をejceへ結ぶ。各系の時刻値・区間・履歴を保ち、同じ出来事の二記録であることを空間値の一致だけで代用しない。',
 'ejch':'指定したK時刻の同じ端について、ejcgの同じ出来事の二系記録が存在し、そのK記録の時刻値が指定値である。記録名の一意性は要求しない。',
 'ejci':'Kの正の時間幅を持つ対象区間の全実数時刻で、同じ端の現在二系記録ejchが存在する。一組だけの測定又は空集合上の全称で一般座標式を代用しない。k側の時刻をKの時刻へ等置しない。',
 'ejcj':'同じ端の全対象時刻に現在記録が存在するejciを保ち、全ての同じ出来事の二系記録ejcgへ、既存srwの現在四変換とkの(0,proper,0)、sryのKでのx=vt,y=proper/φ(v),z=0を適用する。同じ既出spcとzb7を用い、proper=0も扱う。',
 'ejck':'同じ横棒zguがkの(0,0,0)から(0,l,0)の全閉区間を占める現在設定ejcc。問いに続いて考察へ取り上げる対象の特徴を記述する。',
 'ejcl':'考察へ取り上げた同じ棒・両端・lに、Kでの全物質点の速度vの並進と自軸への直交を結ぶejcfの内容。',
 'ejcm':'同じ棒のη=l側zgwについて、全対象K時刻と同じ出来事の現在二系記録にejcjを課す第一表示の内容。第一端は高いη側であり、properは同じ正のl=zgz。',
 'ejcn':'同じ棒のη=0側zgvについて、同じ全範囲の現在二系記録にejcjを課す第二表示の内容。proper=0であり、第一表示の端や長さを混ぜない。',
 'ejco':'直前の相反積の後、同じ第三節で同じ正規化後φ=spcの物理的意味を今問いにするという著者の提示。関数値の計算問題や解答済みの主張にしない。nunはこの段階への談話上の移行として保つ。',
 'ejcp':'著者が同じ横棒zguをejckの軸区間として考察へ取り上げ、その同じ設定を議論に採用する。考察の対象と仮定内容を別の棒にしない。',
 'ejcq':'同じ著者がejclの横棒を述べ、その両端の現在座標ejcmとejcnを同じコロンに続く第一・第二の項として共に提示する。undを両項の連言と順序に保持し、後続の測定長や対称性の結論を加えない。',
 'ejcr':'同じφの意味への問いejcoを述べるメッセージ。',
 'ejcs':'u0097第一文の問いを同じ著者・論説へ帰属し、相反積の提示からの進行を保つ。',
 'ejct':'同じ軸区間を考察へ取り上げるejcpを述べるメッセージ。',
 'ejcu':'u0097第二文の対象の選定を同じ著者・論説へ帰属し、意味の問いに続ける。',
 'ejcv':'同じ棒の運動と二端の座標の列挙ejcqを述べるメッセージ。',
 'ejcw':'u0097第三文からu0100までを同じ著者・論説へ帰属し、指定区間の選定に続ける。',
}
LIMITS=[
 'u0097の三文とu0098/u0099/u0100の二端座標・undを一つの意味群として読む。原刊902頁の印字Hをkのη軸の役割とし、ξ=ζ=0、0≤η≤lの全閉区間を理想化した線状棒とする。材料の実際の切断を追加しない。',
 'nunは相反積を述べた後で同じφの物理的意味へ進む談話上の現在。wirは著者の論述上の声。ins Auge fassenは対象を考察へ取り上げる関係eisnxと読み、単なる仮定の採用ugや視覚的目撃だけに置き換えない。',
 'Dieses Stückとdessen Endenは直前に取り上げた同じzguと二端標識zgv/zgw。全物質点と全時刻の履歴・区間の占有・並進・自軸との直交をejcfへ保持する。厚い一般の棒を零厚みとする一般論ではない。',
 '表示はKの対象区間の任意時刻tについての両端の式と読む。各時刻に同じ端の同じ出来事の現在二系記録を要求し、全該当記録へ式を適用する。各系の時計・位置測定・履歴・時間区間はejceで結び、t=τは加えない。対象区間は既存eisls/eisltであり全宇宙の時間へ広げない。',
 'M0179の第一項はη=l側、M0180の第二項はη=0側。添字はこの端の番号であって時間番号ではない。両項は同じtの任意値について述べられ、各時刻の存在と全称により同じK時刻で両端を選べる。',
 'l/φ(v)は保存MathMLの分数。srxは正の分母φ²を用いる等価な除算であり、負のφを絶対値へ変えない。φは同じ正規化後spcで非零、速度は同じzb7。正値性、反転対称性、φ=1、棒の測定長の物理的解釈の結論はここで要求しない。',
 '表示を著者の主張として帰属し、検証器が現実の測定を行い又は全物理的導出を証明したとはしない。既存の物理履歴、現在の測定、純粋数式の意味規約を再利用する。全実数量化は有限標本へ縮めず、局所の例化検査と原刊通読の判断を区別する。',
]
GROUPS=(('ejco','ejcr','ejcs','zhh','zgs'),('ejcp','ejct','ejcu','zhi','zhh'),('ejcq','ejcv','ejcw','zhj','zhi'))

def definitions():
    text=''.join('r '+n+'['+' '.join(t for _,t in fs)+'] '+('a' if not fs else 'c')+'.\n' for n,(fs,_) in PRIMITIVES.items())
    body=v('body');end=v('endpoint');event=v('event');rest=v('rest');moving=v('moving');ctx=v('context');time=v('time');zero=k('bb','n p a b')
    pair=[('body','a'),('endpoint','a'),('event','a'),('rest','a'),('moving','a'),('context','d')]
    text+=define('ejcg',pair,both(k('ejce',body,end,event,rest,k('ra'),ctx),k('ejce',body,end,event,moving,k('zbm'),ctx)))
    hit=both(k('ejcg',*[v(n) for n,_ in pair]),k('sca',k('zc6',rest,k('zc7')),time))
    for n in reversed(('event','rest','moving')):hit=q('g',n,'a',hit)
    fields=[('body','a'),('endpoint','a'),('context','d')]
    text+=define('ejch',fields+[('time',R)],both(k('ba',time),hit))
    text+=define('ejci',fields,both(k('bg',*interval(k('ra'),ctx)),q('f','time',R,op('y',k('lg',*interval(k('ra'),ctx),time),k('ejch',body,end,ctx,time)))))
    condition=op('y',k('ejcg',*[v(n) for n,_ in pair]),both(k('srw',rest,moving,k('zb7'),v('proper')),k('sry',rest,k('zb7'),v('proper'),app(k('spc'),k('zb7')))))
    for n in reversed(('event','rest','moving')):condition=q('f',n,'a',condition)
    text+=define('ejcj',[('body','a'),('endpoint','a'),('proper',R),('context','d')],both(k('ejci',body,end,ctx),condition))
    setting=k('zb6');rod=k('zgu');low=k('zgv');high=k('zgw');extent=k('zgz')
    text+=content('ejck',k('ejcc',rod,low,high,setting,extent))
    text+=content('ejcl',k('ejcf',setting))
    text+=content('ejcm',k('ejcj',rod,high,extent,setting))
    text+=content('ejcn',k('ejcj',rod,low,zero,setting))
    author=k('rd');scope=k('eisms');paper=k('eirf');point=v('point')
    text+=content('ejco',both(k('zhg',k('zhh'),author,quote('spc'),scope,point),k('ue',k('zgs'),k('zhh'),point)))
    text+=content('ejcp',both(k('eisnx',k('zhi'),author,rod,quote('ejck'),scope,point),k('ug',k('zhi'),author,quote('ejck'),scope,point)))
    clauses=[k('uh',k('zhj'),author,quote('ejcl'),scope,point)]
    for node,value,ordinal in (('eisny','ejcm','b'),('eisnz','ejcn','c')):
        clauses += [k('uh',k(node),author,quote(value),scope,point),k('eiskj',k(node),k('zhj'),'n p '+ordinal+' b',paper,point)]
    clauses += [k('ue',k('zhj'),k('eisny'),point),k('ue',k('eisny'),k('eisnz'),point),op('u',op('e',k('eisny'),k('eisnz')))]
    text+=content('ejcq',both(*clauses))
    for value,message,claim,node,previous in GROUPS:
        text+='d '+message+'[] f[j s[k '+value+'[]]].\n'
        text+=define(claim,[],both(k('eir3',k(node),author,paper,quote(message),k('ri')),k('ue',k(previous),k(node),k('ri')),op('u',op('e',k(previous),k(node)))))
    return text

def build():
    old=parse(read(PARENT));assert len(old['statements'])==INDICES[0];doc=deepcopy(old);doc['statements']=[]
    assert not (set(MEANINGS)|set(PRIMITIVES))&{d['name'] for d in old['declarations']}
    doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']+[dict(kind='assert',body=dict(kind='call',symbol=g[2],arguments=[])) for g in GROUPS]
    added=doc['declarations'][len(old['declarations']):]
    primitives={d['name']:dict(parameters=d['parameters'],result=d['result'],arguments=[n for n,_ in PRIMITIVES[d['name']][0]],meaning_ja=PRIMITIVES[d['name']][1]) for d in added if d['kind']=='primitive'}
    basis=dict(status='transverse_rod_question_selection_and_endpoint_displays',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives=primitives,definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=list(INDICES)).document
    ann=json.loads(read('data/transverse-segment-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
