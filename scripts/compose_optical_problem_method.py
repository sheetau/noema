"""Present the universal optical-method claim without selecting only solvable cases."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_limits import ROOT,R,v,call as k,app,op,both,quant as q
from scripts.compose_material_relative_frame import define,args
from scripts.compose_body_rest_field_method import SETTING,FIELD,REGION,history
from scripts.compose_field_answer_records import CODEC,METHOD
from scripts.compose_relativity_conjecture import content,evaluate
from scripts.compose_two_postulates import quote

def read(path):return (ROOT/path).read_text(encoding='utf-8')
PARENT='examples/v014/einstein-field-answer-records.noema';PARENT_BASIS='data/field-answer-records-basis-v1.json'
FULL='examples/v014/einstein-optical-problem-method.noema';CORE='examples/v014/optical-problem-method-core.noema'
BASIS='data/optical-problem-method-basis-v1.json';ANNOTATIONS='data/optical-problem-method-identifiers-v1.json';INDEX=406
FAMILY='h[a] g[a]';SEQUENCE='j[a]';MAPPER='h[j[a]] a'
EXTRACTOR='h[j[a] '+FIELD+' '+FIELD+'] a'
LIGHT=[('lightsource','a'),('wave','a')]
CASE=[(n,t) for n,t in SETTING if n not in ('newframe','speed','newlower','newupper','newx','newy','newz')]+LIGHT
OPERATION=SETTING+LIGHT
typed=lambda fields,result='c':'i[h['+' '.join(t for n,t in fields)+'] '+result+']'
REBUILD=[('light',R),('speed',R),*CODEC[:2],('extractor',EXTRACTOR),('mapper',MAPPER),('slot','b')]
REBUILD_SCOPE=REBUILD+[('targets',SEQUENCE),('questions',FAMILY)]
PLAN=[('method','a'),('sourceproblem','a'),('targets',SEQUENCE),('mapper',MAPPER),('reference','d')]
WITNESSES=METHOD+LIGHT+[('fieldproblem','a'),('slot','b'),('extractor',EXTRACTOR)]
DETAIL=PLAN+WITNESSES
PRIMITIVES={
 'eisvk':([('problem','a'),('question','g[a]'),('topic',typed(CASE)),('scope','a'),('context','d')],'problemの問いが同じquestionという実際のNoema質問であり、scopeの下でtopicが明示する物理的な種類の設定・現象・作用についての量や性質を求める問題に属するという主題分類。topicは閉じた条件規則で、問題の与件又は検討する仮定の種類を記述する。分類だけでその仮定の現実成立・解答・解の存在・方法の適用成功を要求しない。対象範囲はその主題の全問題であり、鏡・平面波・成功済みの例だけを選ばない。問題ごとの追加条件・求める量・答えの型付き内容はquestionに保持し、題名や単なる話題の言及へ縮めない。'),
 'eisvl':([('problem','a'),('process','a'),('body','a'),('frame','a'),('physicalcontext','d'),('reference','d')],'同じproblemの問いと固定した与件において、process・body・frame・physicalcontextが対象となる過程・作用する物体・記述系・物理設定として対応する。referenceはこの問題を扱う論述文脈で、仮定上の物理設定と区別する。この対応だけで問いの正解や与件の現実成立を認定せず、問題の条件を結果に合わせて取り替えない。他の対象を含む問題も許すが、ここで共有する対象は同一に保つ。'),
 'eisvm':([('problem','a'),('context','d')],'同じproblemの全条件・求める対象・個体解答記録の判定条件を持つ、実際のNoema質問g[a]。記録の型付き内容への接続を含む質問値であり、問題名や自然言語文字列ではない。解答があること・既知性・同じ方法での計算可能性は含めない。原文が全問題へ量化するため、有限の成功問題一覧だけをこの対応の定義域としない。'),
 'eisvn':([('method','a'),('problem','a'),('targets',SEQUENCE),('slot','b'),('extractor',EXTRACTOR),('context','d')],'同じmethodとproblemの固定与件について、指定targetsの各答えとslotの場の下位問題から逆変換で戻した二場を入力とし、求める元の解答記録を組み立てるextractorが、認められた手続き案の後処理として使える。固定与件・還元先の解・指定操作による構成であり、元の正解を先に仮定して定数として格納する案や無関係な集合論的写像を手段としない。静止問題を実際に解く部分は各質問とその解存在へ別に結ぶ。案の採用・実行済み・正しさ・全ての還元先に解があることをこの関係だけに含めない。'),
 'eisvo':([('method','a'),('operation',typed(OPERATION)),('scope','a'),('context','d')],'scopeで特徴付ける同じmethodにおいて、閉じたoperation規則が、その方法を成立させる中心的で不可欠な操作内容を記述する。単に一度使える付随的操作・所要時間の最短化・計算の容易さの評価ではない。具体的な物理対象・両場・変換・静止の内容はoperationの本体に置く。どの問題にも適用できることや既に実行したことは別の主張である。'),
 'eisvp':([], 'u0226がここで用いた方法と指す、先行の光の二系比較・反射計算で用いた同じ変換による問題の扱い方への参照。光・両場・相対静止系・還元・解決可能性は後続の合成へ接続し、この名前だけで意味を代用しない。'),
 'eisvq':([('method','a'),('prior','a'),('content','i[e]'),('document','a'),('context','d')],'同じdocumentの先行箇所priorで提示したcontentにおいて用いた扱い方を、同じmethodとして再び参照する。先行の提示箇所と閉じた内容を保持し、新しい別の方法をここで用いたものへ取り替えない。先行計算の物理的真理、原式の健全性又は実験実施済みを認定する関係ではない。'),
 'eisvr':([('node','a'),('author','a'),('method','a'),('operation',typed(OPERATION)),('result','i[e]'),('scope','a'),('context','d')],'authorがnodeで、同じmethodのoperationを手段としてresultが得られると提示する。操作と帰結を別々の対象や方法へ分離せず、単なる時間的後続又は同時成立と区別する。実際の操作、対象範囲、帰結は引用された規則と内容で構成し、この提示関係だけで実行又は一般的な成功を証明しない。'),
 'eisvs':([], 'u0226第一文のNach der hier benutzten Methodeからgelöst werden.までの箇所。'),
 'eisvt':([], 'u0226第二文のDas Wesentliche istからtransformiert werden.までの箇所。'),
 'eisvu':([], 'u0226第三文のDadurchからzurückgeführt.までの箇所。'),
}
MEANINGS={
 'ekwl':'同じ源・波・電磁過程の放射帰属eisru、物理的な二場ejsn、同じ物体の作用eisvi、同じ正の光速度と正の旧履歴区間を合わせる光学的設定の共通部分。遠方源・正弦波・完全鏡を条件に加えない。',
 'ekwm':'ekwlの同じ物体・全物質点・旧系・文脈・ta/rb・区間のeiag運動を要求する、動く物体の光学の主題条件。静止系や問題の解の存在を分類の前提にしない。',
 'ekwn':'ekwlと同じ型の設定についてeiahの全物質点の静止を要求する、静止物体の光学の主題条件。動く物体の問題との区別を、名前だけや既に解けたことへ置き換えない。',
 'ekwo':'同じ解答列の指定recordから二readerで得た二場を、同じ光速・反対速度のs6k/s6lで旧系へ戻し、解答列全体と共にextractorへ渡した個体がmapper(answers)と一致する。電気側・磁気側・逆変換の符号・他の下位問題の答えを保持する。',
 'ekwp':'同じtargetsとquestionsに対する全ての完全な正解列及びそのslotの記録についてekwoを要求する。単一の都合のよい正解だけで再構成を済ませず、列外位置や別位置の記録を使わない。',
 'ekwq':'同じ光源・波・過程への放射帰属と、同じ物体の相対静止系への両場変換ekv6、正逆s46の全座標規約eisqtを結ぶ中心的操作の規則。元の二場・作用する物体・新系・同一出来事・単位を共有する。',
 'ekwr':'同じ方法・元問題・問題列・再構成写像の手続き案を、同じ物理設定と光の中心操作ekwq、忠実な場の解答記録化ekwi、質問族の同じ場の下位問題、同一対象の新系での全還元先問題、逆変換を含むekwp、後処理の適格性eisvnへ結ぶ。原文Reiheを少なくとも二項の順序付き有限列と読み、成否で範囲を縮めない。',
 'ekws':'同じmethod・sourceproblem・targets・mapper・論述文脈について、ekwrを満たす一組の物理設定・源・波・記録の読書き・場の下位問題・位置・後処理が存在する。全構成へ同じ存在証人を共有し、原問題の正解を先に仮定しない。',
 'ekwt':'同じ論述文脈で各問題へeisvmの実際のg[a]質問を対応させる族。二場以外の量・性質を問う問題を、場だけの問いへ置き換えない。',
 'ekwu':'同じ第八節の文脈で、ekwmの動く物体の光学を主題とする全問題の選択述語。eisvkには同じ問題の実際の質問と閉じた主題規則を渡し、解決又は静止系の存在を選択条件にしない。',
 'ekwv':'同じ文脈でekwnの静止物体の光学を主題とする全問題の選択述語。原問題と同じ物体・過程・新系への実際の対応は手続き案で別に要求する。',
 'ekww':'同じここで用いた方法の中心的操作がekwqであるという特徴付けの内容。任意の問題で操作が現実に実行されたという意味ではなく、次の全問題への主張とも分ける。',
 'ekwx':'同じ方法・実際の質問族・静止問題の種類・ekws手続き案について、非空の全動く物体の光学問題がekvtの解決可能性を満たすという内容。全ての還元先の完全解答列の存在を含み、実行済み又は解の一意性にはしない。',
 'ekwy':'同じ方法と全問題範囲について、各問題がekvrの正しい還元を持つという内容。各問題で異なる有限列を許すが、ekwsにより同じ対象と相対静止系、実際の操作と逆再構成を保持する。',
 'ekwz':'第一文の全問題の解決可能性ekwxを同じ著者へ帰属し、先行の反射後の二系比較で提示したektiを、同じ方法の使用として参照する。ここでという照応を保持し、先行原式の不一致を修正したことにしない。',
 'ekw2':'第二文の本質的な操作の特徴付けekwwを同じ著者へ帰属する。引用されたekwq内の、同じ光・影響する動体・両場・相対静止する系の関係を保持する。',
 'ekw3':'第三文の全問題の静止側問題列への還元ekwyを同じ著者へ帰属し、同じ方法の中心操作ekwqを手段とすることと、直前の特徴付けへのDadurchの参照を保持する。',
 'ekw4':'u0226の三文の提示を同じ方法・著者・論説・範囲へ接続し、第一文、中心操作の説明、手段による還元の順序と三箇所の相違を保持する。',
 'ekw5':'同じ三文の提示内容ekw4を述べるメッセージ。物理的な全問題の解決を評価器が証明したという主張へ変えない。',
 'ekw6':'u0226の全三文を同じ著者と論説へ帰属し、先行の光圧近似表示の後へ置く本文主張。',
}
LIMITS=[
 'u0226の三文全体を対象とする。原刊915頁の語句・順序・参照を固定し、Nach der hier benutzten Methode、können alle、Das Wesentliche、同じ光への関係節、elektrische und magnetische Kraft、relativ zu dem Körper ruhend、Dadurch、jedes、eine Reihe von Problemenを省かない。',
 '全問題の分類は、実際のNoema質問と閉じた光学的な主題条件への対応で行う。分類だけで仮定の現実成立・静止系・解又は手段の存在を要求しない。原文の主題は動く物体の作用を受ける光についての問題と読み、その量・性質を二場だけに限定しない。',
 'können gelöst werdenは、認められた同じ方法の案による正しい還元と、還元先の完全解答列が存在し、元の正解記録を構成できるという可能性として読む。現在の実行済み・著者の既知性・一意解・計算時間上限を追加しない。手続きの適格性eisvnを原始入力として明示し、任意の正解定数を持つ写像の存在だけで方法としない。',
 'Reiheは少なくとも二項の順序付き有限列と読む。全ての項が静止物体の光学の問題であり、同じ設定の対象・新系を共有する。項の反復は原文が排除しないため許す。一項だけで原文の複数を済ませず、無限列へ拡張しない。',
 '手続き案は同じ光の二場を静止系へ変換し、その場の下位問題を任意位置で扱い、全問題の答えと逆変換した二場から元の答えを構成する。候補の前後で対象・質問・物理設定・位置・reader・mapperを選び直さない。静止側の解法自体は原文が列挙しないため各質問と解存在及び案の適格性に保つ。',
 '変換は先行の一様なLorentz変換を用いる。任意の加速・回転・変形体に一つの静止慣性系が存在することや全問題が実際に解けることは証明しない。問題分類から困難な例を除かず、全問題への適用可能性は著者の主張として保持する。',
 '本質的という語は、同じ方法を特徴付ける中心的で不可欠な操作内容として読む。最短・最速の計算や形而上学的な本質論にはしない。eisvoはこの一般的な方法と操作の役割関係だけを扱い、操作の物理内容はekwqで合成する。',
 'ここで用いた方法は、先行の反射後の二系比較の導出提示ektiへ結ぶ。過去の角の読みや印刷された周波数式の不一致を消さず、先行内容の真理又は物理的健全性をこの照応から認定しない。',
 '記録の完全性・全実数全関数域・全問題の量化・仮説上の物理的帰属を保持する。有限対照、原刊照合、原文意味判断は別の証拠であり、テスト成功を全問題の物理的可解性の証明へ転用しない。既存406主張と旧判断を保存する。',
]

def quantify(kind,fields,body):
    for n,t in reversed(fields):body=q(kind,n,t,body)
    return body
def emission():return k('eisru',v('lightsource'),v('process'),v('wave'),v('oldframe'),k('ta'),k('rb'),v('electricunit'),v('magneticunit'),v('electricfield'),v('magneticfield'),v('region'),v('context'))
def questions(reference):return 'i[problem a]['+k('eisvm',v('problem'),reference)+']'
def positions(xs,slot,value):return 'a['+xs+']['+slot+']['+value+']'

def definitions():
    text=''
    for n,(fs,meaning) in PRIMITIVES.items():
        result='g[a]' if n=='eisvm' else 'c' if fs else 'a'
        text+='r '+n+'['+' '.join(t for _,t in fs)+'] '+result+'.\n'
    V=v('light');speed=v('speed');ctx=v('context');reg=v('region');one=k('bb','n p b b');zero=k('bb','n p a b')
    calibrated=k('ejsn',v('oldframe'),k('ta'),k('rb'),ctx,reg,*(v(n) for n in ('chargeunit','electricunit','magneticunit','forceunit')),one,k('sjd',V),v('electricfield'),v('magneticfield'))
    text+=define('ekwl',CASE,both(k('ba',V),k('bg',zero,V),k('ba',v('oldlower')),k('ba',v('oldupper')),k('bg',v('oldlower'),v('oldupper')),calibrated,emission(),k('eisvi',v('body'),v('process'),v('oldframe'),reg,ctx)))
    for root,motion in [('ekwm','eiag'),('ekwn','eiah')]:text+=define(root,CASE,both(k('ekwl',*args(CASE)),k(motion,*history('old'))))
    rec=v('record');answers=v('answers');new=[app(v(n),rec) for n in ('electricreader','magneticreader')]
    old=[k(n,V,k('be',speed),*new) for n in ('s6k','s6l')]
    text+=define('ekwo',REBUILD+[('answers',SEQUENCE),('record','a')],op('e',app(v('mapper'),answers),app(v('extractor'),answers,*old)))
    guarded=both(k('ekvi',v('targets'),answers,v('questions')),positions(answers,v('slot'),rec))
    text+=define('ekwp',REBUILD_SCOPE,quantify('f',[('answers',SEQUENCE),('record','a')],op('y',guarded,k('ekwo',*args(REBUILD),answers,rec))))
    from scripts.compose_field_equations import POINT
    maps=[('oldframe','newframe',speed),('newframe','oldframe',k('be',speed))]
    charts=[k('eisqt',v(a),v(b),k('ta'),k('rb'),'i[point '+POINT+']['+k('s46',V,s,v('point'))+']',ctx) for a,b,s in maps]
    text+=define('ekwq',OPERATION,both(emission(),k('ekv6',*args(SETTING)),*charts))
    reference=v('reference');qs=questions(reference);target=v('target')
    bound=lambda problem,frame:k('eisvl',problem,v('process'),v('body'),frame,ctx,reference)
    alltargets='q[v targets][e[n p a b][n p a b]][i[prior c target a]['+both(v('prior'),bound(target,v('newframe')))+']]'
    rebuild=[qs if n=='questions' else v(n) for n,t in REBUILD_SCOPE]
    rows=[k('sca',V,k('tc')),k('ekwq',*args(OPERATION)),k('ekwi',*args(METHOD)),k('ekwe',v('fieldproblem'),qs,k('ekwf',*args(METHOD))),positions(v('targets'),v('slot'),v('fieldproblem')),k('aa','n p b b','d[v targets]'),bound(v('sourceproblem'),v('oldframe')),alltargets,k('ekwp',*rebuild),k('eisvn',v('method'),v('sourceproblem'),v('targets'),v('slot'),v('extractor'),reference)]
    text+=define('ekwr',DETAIL,both(*rows))
    text+=define('ekws',PLAN,quantify('g',WITNESSES,k('ekwr',*args(DETAIL))))
    text+=define('ekwt',[('reference','d')],qs,FAMILY)
    for root,rule in [('ekwu','ekwm'),('ekwv','ekwn')]:text+=define(root,[('reference','d')],'i[problem a]['+k('eisvk',v('problem'),k('eisvm',v('problem'),reference),'r[p '+rule+']',k('eistk'),reference)+']','h[a] c')
    p=v('point');method=k('eisvp');scope=k('eistk');author=k('rd');paper=k('eirf');operation='r[p ekwq]'
    text+=content('ekww',k('eisvo',method,operation,scope,p))
    supplied=[method,k('ekwt',p),k('ekwv',p),'p ekws',p,k('ekwu',p)]
    text+=content('ekwx',k('ekvt',*supplied));text+=content('ekwy',k('ekvr',*supplied))
    text+=content('ekwz',both(k('uh',k('eisvs'),author,quote('ekwx'),scope,p),k('eisvq',method,k('eisuu'),quote('ekti'),paper,p)))
    text+=content('ekw2',k('uh',k('eisvt'),author,quote('ekww'),scope,p))
    text+=content('ekw3',both(k('uh',k('eisvu'),author,quote('ekwy'),scope,p),k('eisvr',k('eisvu'),author,method,operation,quote('ekwy'),scope,p),k('eisra',k('eisvu'),author,paper,k('eisvt'),quote('ekww'),quote('ekwy'),scope,p)))
    nodes=[k(n) for n in ('eisvs','eisvt','eisvu')]
    text+=content('ekw4',both(*(evaluate(n) for n in ('ekwz','ekw2','ekw3')),*(k('ue',a,b,p) for a,b in zip(nodes,nodes[1:])),*(op('u',op('e',a,b)) for i,a in enumerate(nodes) for b in nodes[i+1:])))
    text+='d ekw5[] f[j s[k ekw4[]]].\n'
    text+=define('ekw6',[],both(k('eir3',nodes[0],author,paper,quote('ekw5'),k('ri')),k('ue',k('eisvh'),nodes[0],k('ri')),op('u',op('e',k('eisvh'),nodes[0]))))
    return text

@lru_cache(None)
def build():
    old=parse(read(PARENT));assert len(old['statements'])==406
    assert not (set(MEANINGS)|set(PRIMITIVES))&{d['name'] for d in old['declarations']}
    doc=deepcopy(old);doc['statements']=[];doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']+[dict(kind='assert',body=dict(kind='call',symbol='ekw6',arguments=[]))]
    added=doc['declarations'][len(old['declarations']):]
    primitives={d['name']:dict(parameters=d['parameters'],result=d['result'],arguments=[n for n,t in PRIMITIVES[d['name']][0]],meaning_ja=PRIMITIVES[d['name']][1]) for d in added if d['kind']=='primitive'}
    basis=dict(status='all_optical_problems_reduction_solvability_and_essential_method',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives=primitives,definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=[INDEX]).document
    ann=json.loads(read('data/field-answer-records-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode()))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
