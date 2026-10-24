"""Compose a unipolar induction machine from operation, contacts and polarity."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_vacuum_field_domain import ROOT,read
from scripts.compose_material_relative_frame import define,args
from scripts.compose_field_equations import FIELD,REGION
from scripts.compose_moving_conductor_case import LAW
from scripts.compose_electromotive_wording import bind
from scripts.compose_limits import R,F,v,call as k,app,op,both,quant as q

PARENT='examples/v014/einstein-asymmetry-resolution.noema';PARENT_BASIS='data/asymmetry-resolution-basis-v1.json'
FULL='examples/v014/einstein-unipolar-machine.noema';CORE='examples/v014/unipolar-machine-core.noema'
BASIS='data/unipolar-machine-basis-v1.json';ANNOTATIONS='data/unipolar-machine-identifiers-v1.json';INDEX=361
POLARITY=[('lower',R),('upper',R),('output',F)]
MODE=[(n,'a') for n in ('device','rotor','returnpath','circuit','first','second','axis','frame','process','magneticunit','outputunit')]+[('lower',R),('upper',R),('turns',R),('electric',FIELD),('magnetic',FIELD),('region',REGION),('output',F),('operation','d')]
COUPLING=[(n,t) for n,t in MODE if n not in ('axis','turns')]+[('law',LAW)]
CIRCUIT=[(n,dict(MODE)[n]) for n in ('circuit','rotor','returnpath','first','second','lower','upper','operation')]
CONTACT=[(n,dict(MODE)[n]) for n in ('rotor','returnpath','lower','upper','operation')]
TURN=[(n,dict(MODE)[n]) for n in ('rotor','axis','frame','lower','upper','turns','operation')]
WITNESSES=[(n,t) for n,t in MODE if n!='device']
PRIMITIVES={
 'eisrc':([('device','a'),('context','d'),('operation','d')], '同じdeviceの設計・通常の接続・許容する駆動条件に従い、contextで考える利用可能な運転設定がoperationである。必要な外部の帰路・負荷・試験接続を許すが、装置を別機構へ作り替える改造や破壊、成功した出力だけを根拠とする選別は含めない。仮定上の運転を含み、現在実際に運転済みという主張とは区別する。運動・回路・出力は別に合成する。'),
 'eisrd':(COUPLING, '同じdeviceのoperationで、rotorの機械的運動が同じprocessの磁気側場との作用を通じて、指定circuitに誘導起電作用を与えるという物理的な変換への帰属。磁気的な局所駆動は、各導体部分の座標時刻速度と同じ位置の磁気成分・正の単位換算を、閉じたlawで指定する正の単位電荷の力/電荷の規則へ結ぶ。rotorとreturnpath、firstからsecondへの固定した向き、全経路・区間・基底を保つ。outputはその経路に沿う誘導作用の符号付き仕事/電荷をoutputunitで表す全時間履歴である。単位は同じ仕事と電荷の物理的基準に校正する。外部電池の起電力や端子名だけでこの帰属を代用しない。磁気場の単位magneticunitと同じ電磁過程への場帰属は別に照合する。これは回転由来の誘導作用と出力との物理的結合の規約であり、全回路の微視的導出、無負荷電位差との無条件同一視、出力の一定性・非零性・極性維持、磁石とrotorの別体性を含意しない。'),
 'eisre':(CIRCUIT, 'operationの同じ時間区間を通じて、rotor側とreturnpath側の導電経路がfirstとsecondの二接触で接続され、同じcircuitという閉じた電荷輸送の道を形成する。導電は通常の同じ条件で電荷が経路に沿って通過できる物理的接続であり、幾何学的な隣接や無関係な二電流の並置とは区別する。firstからsecondへの取り出し方向と経路の同一性を維持し、回転位相ごとの端子交換・経路切替による整流を含めない。輸送の実行、電流の非零性、外部帰路が装置内部の機械部品であることは要求しない。'),
 'eisrf':([('contact','a')]+CONTACT, 'operationの全指定区間で、contactがrotor側とreturnpath側の間の導電性の滑り接触として保たれる。接する物質部分が相対的に移りながら電荷の通過を可能にする接触であり、絶縁した近接、開路、位相ごとに別端子へ接続する整流切替とは区別する。接触手段を水銀、ブラシ、特定の材質又は寸法へ限定しない。'),
 'eisrg':(TURN, '同じoperation・frameでrotorがaxisの周りにlowerからupperまで回転した有向角変位を、完全な一回転を1とする巻き戻さない値turnsで表す物理的な角変位の帰属。同じ物体と固定軸の方位を連続に追跡し、始終で方位が同じだから零と扱わない。向きは軸の採用方向で定まる。一様回転、非零性、少なくとも一周したことは別に要求する。'),
 'eisrh':([], 'u0177第二文の括弧内Unipolarmaschinenという装置類を指す表現。対象の構成はekajへ接続し、原語の綴りだけで語義を代用しない。磁気単極子を指す語としては扱わない。'),
 'eisri':([], '固定原文einstein-1905:u0177第二文の括弧内で装置類を指定する箇所。第二文全体の主張内容や著者による問いへの評価を、この参照だけで表したとはしない。'),
 'eisrj':([('expression','a'),('rule','i[h[a d] c]'),('document','a'),('node','a'),('context','d')], '同じdocumentのnodeで使われるexpressionの対象への適用を、同じcontextと対象を引数にする閉じたruleにより解釈するという読解注記。対象の種類を構成する記述を保持し、別義への交換や綴りだけの代用を避ける。この注記は著者による装置の実在の主張・発明の帰属・問いへの回答ではなく、引用した規則を注記の評価時に実行しない。'),
}
MEANINGS={
 'ekag':'指定時刻が同じ正の区間内にあるとき、出力履歴のその値が有効な実数で、指定した一方の極性に従って非負又は非正であるという局所条件。値の大きさを一定にせず零を許す。',
 'ekah':'正の時間区間の全時刻で同じ出力の値が有効で、一方の極性を保ち、区間内の少なくとも一時刻で非零である。正又は負のどちらも許すが、途中で逆極性になる履歴と恒等的な零を除く。',
 'ekai':'一回転以上の非零な一様回転、装置に属するrotor、二つの異なる滑り接触による同じ閉回路、同じ過程と単位の磁場、機械的運動による誘導作用、整流切替なしの非反転な出力を一つの運転設定に結ぶ。',
 'ekaj':'deviceが、ekaiの構成を満たす利用可能な運転設定を持つ。これを単極誘導機の装置類の読みとする。現在の実行済みや全運転条件での成功を要求せず、外部回路を含む設定と機械本体を区別する。',
 'ekak':'u0177の括弧内の装置類の表現を、同じ論説・箇所でekajへ結ぶ読解注記。Sitzの問いとgegenstandslosの判断はこの注記に含まれない。',
}
LIMITS=[
 '単極誘導機を、磁場の下での機械的回転から、滑り接触と固定した回路方向を通じて、整流切替なしの一方向の誘導起電作用を取り出せる装置として読む。発電可能な運転設定を持つことを使い、現に運転済み、全時刻一定の値、全ての負荷条件での成功は加えない。',
 '磁場の源と回転する導体が必ず別の物体であるとは要求しない。磁石自体が導電性rotorである配置、外部の帰路を含む配置を許す。回転の基準は指定frameであり、磁石と導体の相対運動だけへ限定しない。',
 '円板・円筒という形、銅などの材質、水銀という接触、検流計、特定の磁石の作り方は一般概念の必須条件にしない。Faraday §§218–220,229–230はこの範囲を検討する一次資料であり、EinsteinのSitzの語義を確定する証拠とは別に扱う。',
 'outputの仕事/電荷は回路方向に沿う作用の量であり、u0174の局所的な三成分の電動力ejygをスカラーの端子量へ置換しない。局所的な磁気駆動には既存eidzを使い、回路出力への物理的な結合はeisrdの規約に明示する。',
 '今回は装置の意味を接続する読解注記を追加する。Sitzが問う所在の前提、その問いが対象を失うという第二文の内容、Auchの提示、u0177全体の意味判断は次に接続する。',
]

def definitions():
    text=''.join('r '+n+'['+' '.join(t for _,t in fs)+'] '+('c' if fs else 'a')+'.\n' for n,(fs,_) in PRIMITIVES.items())
    zero=k('bb','n p a b');one=k('bb','n p b b');minus=k('bb','n u b b');lo=v('lower');hi=v('upper');t=v('time');value=app(v('output'),t)
    inside=k('lg',lo,hi,t)
    sign=op('x',both(v('positive'),k('bc',zero,value)),both(op('u',v('positive')),k('bc',value,zero)))
    text+=define('ekag',POLARITY+[('positive','c'),('time',R)],op('y',inside,both(k('ba',value),sign)))
    allsign=lambda positive:q('f','time',R,k('ekag',lo,hi,v('output'),positive,t))
    # Truth literals are encoded as rational equality and its negation.
    yes=op('e','n p a b','n p a b');no=op('u',yes)
    nonzero=q('g','time',R,both(inside,k('ba',value),op('u',k('sca',zero,value))))
    text+=define('ekah',POLARITY,both(k('ba',lo),k('ba',hi),k('bg',lo,hi),op('x',allsign(yes),allsign(no)),nonzero))
    ctx=v('operation');fullturn=op('x',k('bc',one,v('turns')),k('bc',v('turns'),minus))
    physical=both(op('u',op('e',v('rotor'),v('returnpath'))),op('u',op('e',v('first'),v('second'))),k('zjg',v('rotor'),v('device'),ctx),k('va',v('frame')),k('zjn',v('rotor'),v('axis'),v('frame'),ctx),k('ba',v('turns')),fullturn,k('eisrg',*args(TURN)),k('eisre',*args(CIRCUIT)),*(k('eisrf',v(c),*args(CONTACT)) for c in ('first','second')),k('eispn',v('process'),v('frame'),v('electric'),v('magnetic'),v('region'),ctx),k('eirn',v('frame'),v('magnetic'),v('magneticunit'),ctx),k('eisrd',*[v(n) for n,_ in COUPLING if n!='law'],'r[p eidz]'),k('ekah',*args(POLARITY)))
    text+=define('ekai',MODE,physical)
    text+=define('ekaj',[('device','a'),('context','d')],bind(WITNESSES,both(k('eisrc',v('device'),v('context'),ctx),k('ekai',*args(MODE)))))
    text+=define('ekak',[],k('eisrj',k('eisrh'),'r[p ekaj]',k('eirf'),k('eisri'),k('ri')))
    return text

def build():
    old=parse(read(PARENT));assert len(old['statements'])==INDEX
    assert not(set(PRIMITIVES)|set(MEANINGS))&{d['name'] for d in old['declarations']}
    doc=deepcopy(old);doc['statements']=[];doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']+[dict(kind='assert',body=dict(kind='call',symbol='ekak',arguments=[]))]
    added=doc['declarations'][len(old['declarations']):]
    primitives={d['name']:dict(parameters=d['parameters'],result=d['result'],arguments=[n for n,_ in PRIMITIVES[d['name']][0]],meaning_ja=PRIMITIVES[d['name']][1]) for d in added if d['kind']=='primitive'}
    basis=dict(status='unipolar_induction_machine_operation_and_polarity_reading',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives=primitives,definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=[INDEX]).document
    ann=json.loads(read('data/asymmetry-resolution-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
