"""Connect the rod's initial measurement, imagined motion and two-method inquiry."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_rod_geometry import ROOT,read
from scripts.compose_material_body_motion import FAMILY
from scripts.compose_material_relative_frame import define
from scripts.compose_two_postulates import quote
from scripts.compose_relativity_conjecture import content
from scripts.compose_limits import R,v,call as k,op,both,quant as q

PARENT='examples/v014/einstein-rod-geometry.noema';PARENT_BASIS='data/rod-geometry-basis-v1.json'
FULL='examples/v014/einstein-rod-experiment.noema';CORE='examples/v014/rod-experiment-core.noema'
BASIS='data/rod-experiment-basis-v1.json';ANNOTATIONS='data/rod-experiment-identifiers-v1.json';INDICES=(252,253,254)
HISTORY=[('body','a'),('frame','a'),('lengthunit','a'),('timeunit','a'),('axis','a'),('context','d')]
PRIMITIVES={
 'eislr':([], 'd','長軸をX軸上へ置いた後、並進運動を与える前の棒の静止設定。初期測定yc及び運動後ydと区別する。'),
 'eisls':([('frame','a'),('timeunit','a'),('context','d')],R,'指定系・時間単位のcontextで全履歴を扱う区間の始時刻候補。同じ設定の棒と物差しへ共通に渡す。有限標本の最初の観測時刻ではなく、区間の妥当性と全域性は合成で要求する。'),
 'eislt':([('frame','a'),('timeunit','a'),('context','d')],R,'eislsと同じ指定による区間の終時刻候補。数値の有効性・順序・幅と全区間の物理的対応を別に要求する。'),
 'eislu':(HISTORY,FAMILY,'同じbodyの履歴について、指定frame・長さ単位・時間単位・空間軸役割・contextの各物質点又は幾何学的標識から、その点の実数時刻に対する座標候補関数を選ぶ。数値だけで物理的帰属を認定せず、全物質点にはeiad、軸標識にはseの全区間出来事対応を要求する。'),
 'eislv':([('body','a'),('frame','a'),('context','d')],'a','同じ物体・評価系・設定で長軸の一方の端面中心として指定する幾何学的標識の候補。eislqと全履歴への接続でその役割を確かめる。端面中心を必ず物質点とはしない。'),
 'eislw':([('body','a'),('frame','a'),('context','d')],'a','eislvと対になる、同じ物体の他方の長軸端面中心の候補。向きの正負や移動前後の数値長の一致はこの選択から要求しない。'),
 'eislx':([('body','a'),('before','d'),('placed','d')],'c','同じ物体をbeforeの設定から、その後のplacedの位置・向きへ置き直す思考上の操作。物体の構成と大きさを保った配置変更として扱い、その後の運動付与や現実の実行と分ける。置き直す位置・向きは到達設定の座標条件で別に指定し、加速中の軌跡や実現可能性は含意しない。'),
 'eisly':([], 'a','u0029の第二文、長軸をX軸上へ置き、その後に棒へ正のX方向等速並進を与えると考える箇所。'),
 'eislz':([('node','a'),('author','a'),('construction','i[e]'),('scope','a'),('context','d')],'c','authorがnodeでconstructionの閉じた内容の設定又は操作を、scopeの思考上の構成として想定する。著者の考察上の行為を記述し、その内容の物理的実在、実行、信念、実現可能性の証明を要求しない。'),
 'eisl2':([('node','a'),('author','a'),('body','a'),('frame','a'),('setting','d'),('condition','i[h[d] c]'),('question','i[g[a '+R+']]'),('methods','j[a]'),('scope','a'),('document','a'),('context','d')],'c','authorがnodeで、同じbodyをframeに対してsettingのconditionで扱う考察のquestionを、列methodsに指定した後続の操作によって解くものとして想定する。questionの方法付き値候補と列の方法の指示を対応させ、同じscope・documentを保つ。これは問いをどの操作で調べるかという想定であり、答えの存在・一意性、二操作の値の一致、現実の測定完了、conditionの現実での成立を断言しない。'),
}
MEANINGS={
 'eiph':'同じ指定物体の全物質点をeirhで選び、同じ静止系ra・単位ta/rb・設定の共通区間と各点の三座標をeiahへ渡す。区間に正の時間幅を要求し、瞬間に位置があるだけで静止としない。',
 'eipi':'初期設定でsbqの同じ棒xi・静止物差しxj・正の初期長yaの読みを保持し、棒の全履歴・剛性・軸長eipeと物差しの全区間静止eiphを結ぶ。同じ時刻規約の共通区間を使い、測定観測者は存在だけを要求する。',
 'eipj':'軸配置後の同じ棒についてeipeの静止・剛性・初期長yaと、eipdの長軸のX軸上配置を要求する。配置変更だけの段階であり、移動後の長さへyaを代入しない。',
 'eipk':'同じ棒xiの指定設定で、同じ静止系・単位・全物質点履歴・長軸をeipgへ渡し、既出のybを正のX方向一定速度とする。加速過程を等速区間へ混ぜない。',
 'eipl':'第一文で仮定する初期静止棒、同じく静止した物差しによる初期長の内容。指定設定ycへeipiを適用し、現実の実測を本文外で断言しない。',
 'eipm':'同じ棒の初期測定ycから軸配置eislr、その後の運動ydへの順を保ち、eipj/eipkと二方法ye/yfへの同じ運動の継承を結ぶ思考構成。配置の前後と移動後を混同しない。',
 'eipn':'同じ論説で棒xiと物差しxjを考察対象として導入し、第一文の初期内容eiplを範囲xyで仮定として採用する。物理的な対象の実在を要求しない。',
 'eipo':'初期の棒と測定長を設定として置くeipnの指示メッセージ。現実の実験を実行せよという命令ではない。',
 'eipp':'第一文の設定指示を著者と論説へ帰属し、第二原理の速度・時間説明からの順序を保持する。',
 'eipq':'著者が第二文でeipmの配置と運動を思考上に構成し、同じ考察範囲の仮定として採用するという内容。思考の構成と内容の真理を分ける。',
 'eipr':'第二文の想定を行う著者の記述eipqを述べるメッセージ。',
 'eips':'第二文を同じ著者・論説へ帰属し、初期の設定文の後へ置く。',
 'eipt':'著者が同じ範囲でsbvの二方法付き長さの問いを提示し、運動設定ydの同じ棒xiについて後続の二操作でその問いを調べると想定する。長さの主題、コロンに続く二項の順序を保持する。',
 'eipu':'問いの提示と二操作による決定の想定eiptを述べるメッセージ。実測値や二操作の値の一致を述べない。',
 'eipv':'第三文を同じ著者・論説へ帰属し、棒の運動を想定した第二文の後へ置く。',
}
LIMITS=[
 'u0029の496転記文字・395本文文字とM0043〜M0047を三文として扱う。第一文のEs seiは設定を置く指示、第二文のWir denken unsは思考上の操作、第三文のWir fragenは問いの提示と二操作による決定の想定と読む。Wirを著者の論述上の声とし、実験参加者の複数性を要求しない。',
 '初期測定yc、軸上へ置いた静止設定eislr、運動後yd、二測定ye/yfを区別する。配置は初期長と構成を保つ置き直し、加速は機構を指定しない思考上の運動付与とする。運動後に初期長yaを要求しない。',
 '同じ棒xi、同じ物差しxj、同じ静止系ra、長さ単位taと時間単位rbを保つ。lはya、vはyb、X/xは同じ系の第一空間成分ynを指す。ybは正の一定速度であり、光速度tcや任意の数値を補わない。',
 '直線状の長軸を持つ巨視的な棒を採用し、軸の端面中心は幾何学的標識でもよい。断面の厚みを零にせず、形状同定eislq・物差しの接触xd・読みxeは明示した物理的入力として用いる。幾何と全物質点の剛性・静止・並進は合成条件へ展開する。',
 '原文の初期長は同じ静止物差しを当てた直接の読みとして扱う。観測者の存在だけを置き、後続の観測者xkとの同一性や初期観測者の静止は追加しない。物差しの静止は同じ区間の全物質点履歴で要求する。',
 '二方法は既存のsbi/sbkを区別したsbvの前方参照。方法の内部の詳述はu0030/u0031で判断する。ここでは両方法を同じ運動する棒の長さの候補条件として参照し、値の存在・唯一性・一致や測定完了を要求しない。',
 '有限検査は履歴の引数、設定・測定・規則の同一性、問いの候補、引用と提示を区別する。全実数時刻と全物理状況の証明を行わず、既存の依存群の検査を保持する。',
]


def interval(context):return [k(n,k('ra'),k('rb'),context) for n in ('eisls','eislt')]
def history(body,context):
    return [body,k('ra'),context,k('ta'),k('rb'),*interval(context),'i[point a]['+k('eirh',body,v('point'),context)+']',*(k('eislu',body,k('ra'),k('ta'),k('rb'),k(role),context) for role in ('yn','yo','yp'))]
def axis(context):return history(k('xi'),context)+[k(n,k('xi'),k('ra'),context) for n in ('eislv','eislw')]
def positive_interval(context):return k('bg',*interval(context))


def definitions():
    text=''.join('r '+n+'['+' '.join(t for _,t in fs)+'] '+result+'.\n' for n,(fs,result,_) in PRIMITIVES.items())
    c=v('context')
    text+=define('eiph',[('body','a'),('context','d')],both(positive_interval(c),k('eiah',*history(v('body'),c))))
    text+=define('eipi',[('context','d')],both(k('sbq',c),positive_interval(c),k('eipe',*axis(c),k('ya')),k('eiph',k('xj'),c)))
    text+=define('eipj',[('context','d')],both(k('eipe',*axis(c),k('ya')),k('eipd',*axis(c))))
    text+=define('eipk',[('context','d')],k('eipg',*axis(c),k('yb')))
    text+=content('eipl',k('eipi',k('yc')))
    phases=[k(n) for n in ('yc','eislr','yd')]
    distinct=[op('u',op('e',phases[a],phases[b])) for a,b in ((0,1),(0,2),(1,2))]
    text+=content('eipm',both(*distinct,op('u',op('e',k('ye'),k('yf'))),k('eislx',k('xi'),k('yc'),k('eislr')),k('eipj',k('eislr')),k('yv',k('xi'),k('eislr'),k('yd')),k('eipk',k('yd')),k('yx',k('yd'),k('ye')),k('yx',k('yd'),k('yf'))))
    text+=content('eipn',both(*(k('eisd3',k('y2'),k(obj),k('eirf'),v('point')) for obj in ('xi','xj')),k('ug',k('y2'),k('rd'),quote('eipl'),k('xy'),v('point'))))
    text+='d eipo[] f[j m[k eipn[]]].\n'
    text+=define('eipp',[],both(k('eir3',k('y2'),k('rd'),k('eirf'),quote('eipo'),k('ri')),k('ue',k('eisll'),k('y2'),k('ri')),op('u',op('e',k('eisll'),k('y2')))))
    text+=content('eipq',both(k('eislz',k('eisly'),k('rd'),quote('eipm'),k('xy'),v('point')),k('ug',k('eisly'),k('rd'),quote('eipm'),k('xy'),v('point'))))
    text+='d eipr[] f[j s[k eipq[]]].\n'
    text+=define('eips',[],both(k('eir3',k('eisly'),k('rd'),k('eirf'),quote('eipr'),k('ri')),k('ue',k('y2'),k('eisly'),k('ri')),op('u',op('e',k('y2'),k('eisly')))))
    text+=content('eipt',both(k('yz',k('y3'),k('rd'),quote('sbv'),k('xy'),v('point')),k('eiskw',k('y3'),'r[p th]',v('point')),k('eisl2',k('y3'),k('rd'),k('xi'),k('ra'),k('yd'),'r[p eipk]',quote('sbv'),'l[a][k xw[] k xx[]]',k('xy'),k('eirf'),v('point')),k('eiskj',k('xw'),k('y3'),'n p b b',k('eirf'),v('point')),k('eiskj',k('xx'),k('y3'),'n p c b',k('eirf'),v('point')),k('ue',k('y3'),k('xw'),v('point')),k('ue',k('xw'),k('xx'),v('point')),op('u',op('e',k('xw'),k('xx')))))
    text+='d eipu[] f[j s[k eipt[]]].\n'
    text+=define('eipv',[],both(k('eir3',k('y3'),k('rd'),k('eirf'),quote('eipu'),k('ri')),k('ue',k('eisly'),k('y3'),k('ri')),op('u',op('e',k('eisly'),k('y3')))))
    return text


def build():
    old=parse(read(PARENT));assert len(old['statements'])==INDICES[0];doc=deepcopy(old);doc['statements']=[]
    assert not(set(MEANINGS)|set(PRIMITIVES))&{d['name'] for d in doc['declarations']}
    doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']+[dict(kind='assert',body=dict(kind='call',symbol=n,arguments=[])) for n in ('eipp','eips','eipv')]
    added=doc['declarations'][len(old['declarations']):]
    primitives={d['name']:dict(parameters=d['parameters'],result=d['result'],arguments=[n for n,_ in PRIMITIVES[d['name']][0]],meaning_ja=PRIMITIVES[d['name']][2]) for d in added if d['kind']=='primitive'}
    basis=dict(status='rod_initial_measurement_imagined_translation_and_two_method_question',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives=primitives,definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=[],statement_indices=list(INDICES)).document
    ann=json.loads(read('data/rod-geometry-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
