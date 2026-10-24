"""Make the speed parameter explicit and connect the named law's axial form."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.meaning_catalog import _references
from noema.semantic_reviews import digest
from scripts.compose_observed_doppler import ROOT,read,SETTING,VARIABLES
from scripts.compose_material_relative_frame import define,args
from scripts.compose_relativity_conjecture import content,evaluate
from scripts.compose_two_postulates import quote
from scripts.compose_limits import R,v,call as k,op,both,quant as q

PARENT='examples/v014/einstein-observed-doppler.noema';PARENT_BASIS='data/observed-doppler-basis-v1.json'
FULL='examples/v014/einstein-doppler-specialization.noema';CORE='examples/v014/doppler-specialization-core.noema'
BASIS='data/doppler-specialization-basis-v1.json';ANNOTATIONS='data/doppler-specialization-identifiers-v1.json';INDICES=[372,373]
LIFT=dict(zip(('eivv','eivw','eivy','eivz','ekb2','ekb3','ekci','ekck','ekcl','ekd6','ekd7','ekea'),('ekej','ekek','ekel','ekem','eken','ekeo','ekep','ekeq','eker','ekes','eket','ekeu')))
EXTENDED=[('speed',R)]+SETTING;QUANTIFIED=[('speed',R)]+VARIABLES
PRIMITIVES={
 'eissp':([('description','i[e]'),('scope','a'),('context','d')],'同じscopeの既出の記号・演算規約でdescriptionを読むとき、式の構成と量の依存が、入れ子の追跡や隠れた補助量の再構成を少なくして見渡せる形として評価される。式の提示形式に対する文脈上の明瞭さであり、内容の真理、導出の容易さ、全読者の実際の理解、計算時間、最短の文字列又は唯一の最簡形を含意しない。別の同値式へ評価を自動で移さず、同じ引用記述を評価対象に保持する。'),
 'eissq':([], 'u0190のドップラー原理としての同定・任意速度の範囲・φ=0の場合の見通しのよい形への提示を述べる箇所。'),
 'eissr':([], 'u0191=M0335のφ=0の場合の平方根比の式を表示する箇所。'),
 'eisss':([], 'u0190で先行の放射と受信の周期数の関係を指すDoppelersche Prinzipという呼称個体。原綴りを識別表記で保持し、その意味内容はeischで同じ一般速度の条件内容へ結ぶ。人名の綴りだけで周波数変化や原理の真理を定義しない。'),
}
MEANINGS={new:f'先行{old}の全対象・物理関係・単位・区間・近似条件を保ち、その依存経路に現れる固定速度zb7だけを追加の第一引数speedへ一貫して置き換えた定義。同じspeedを全ての呼出しへ渡し、速度に依存しない定義は共有する。旧定義・判断を変更せず、speed=zb7で先行本体へ戻る。' for old,new in LIFT.items()}
MEANINGS.update({
 'ekev':'Vとspeedが有効な実数でV>0かつ0<speed<Vである許容標準速度域。一次近似の小ささや選んだ標本値への制限を追加せず、光速以上や零速度の未定義な角へ広げない。',
 'ekew':'ν*sqrt((1−v/V)/(1+v/V))を構成する。差を分子、和を分母とする正の平方根であり、νを根号の外へ掛ける。利用域は呼出し側で指定する。',
 'ekex':'許容速度と正の周期数νについて、cosφ=1を指定した一般印刷形ekdrが同じekewと等しいことを述べる数値条件。φという実数角の零条件を余弦値だけで代替する本体ではなく、その角条件との接続はekeyに置く。',
 'ekey':'同じ60役割に一般化した物理的条件eketと許容速度ekevを保持し、同じ実数角angle=0を加えた特殊場合。cosφだけを独立に1へ替え、別の源・観測者を選ぶ条件にはしない。',
 'ekez':'同じ設定の受信周期数newfrequencyが、同じV・speed・放射frequencyによるekewの平方根比の形に等しい帰結。',
 'eke2':'固定K・V・第七節・評価状況以外の56役割を全称量化し、全許容速度と同じ物理条件eketの下で一般ドップラー形ekeuを述べる。速度を数式だけでなく系・観測者・座標・場へ一貫して渡す。',
 'eke3':'同じ56役割への全称条件で、φ=0を含むekeyの下に同じekezの簡明な形を述べる。条件と結論で周期数を選び直さない。',
 'eke4':'同じφ=0の条件ekeyの下で、同じ一般印刷形ekeuを述べる全称内容。eke3と適用域をそろえ、表示の書き換えを比較できるようにする。',
 'eke5':'先行表示eissnのekebを同じ設定の全速度の形eke2として明示し、この放射と受信の周期数の条件内容をeisssの原理名へ結ぶ。名称規約を物理法則の自動的な実証へ替えない。',
 'eke6':'同じφ=0の一般形eke4を平方根比のeke3として明示し、その同じ記述の見通しのよさeissp、コロンから同じ表示への説明ufと順序ueを保持する。',
 'eke7':'u0190の原理としての同定・任意速度の明示eke5と、φ=0での式の形と提示eke6を同じ点で連言する。',
 'ekfa':'u0190の二文全体eke7を述べるメッセージ。',
 'ekfb':'u0190の二文全体を同じ著者・論説へ帰属し、先行ドップラー表示の後に接続する。',
 'ekfc':'u0191の表示項目を、同じφ=0での条件付き内容eke3へ結ぶ。無条件の等式又は別の物理的仮説に替えない。',
 'ekfd':'u0191の表示対応ekfcを述べるメッセージ。',
 'ekfe':'u0191の表示を同じ著者・論説へ帰属し、u0190のコロンに続ける。',
})
LIMITS=[
 'u0190–u0191を原刊911–912頁の同じ式の同定・適用域・特殊形・表示として読む。Doppelersche Prinzipの印字は修正せず、呼称の内容を放射と受信の同じ周期数の法則へ結ぶ。人物の伝記や命名史は補わない。',
 'beliebige Geschwindigkeitenは、先行の標準配置の許容速度0<v<Vの全域と読む。小速度の一次近似へ縮めない。速度は追加の第一引数とし、物理的な系・計器・観測者の運動、座標と場の変換、位相率の全経路へ渡す。固定K/kの同じ状況に異なる速度の実在運動が同時に存在する主張ではなく、割当ごとの物理条件を前件にする。',
 'φ=0は実数角の零条件であり、先行の0からpiの角の規約からcosφ=1となる。原文にない横波の仮定、源の変更、測定実施を加えず、先行の近似と物理的位相の帰属を保持する。',
 'übersichtliche Formは同じ記号規約で量の依存が見渡しやすい式の形という著者の評価と読む。演算回数の最少性、全読者の心理、計算が容易という別の主張へ替えない。',
 '式はν′=ν*sqrt((1−v/V)/(1+v/V))。0<v<Vで1−v/Vと1+v/Vが正なので、一般形の正の平方根からこの形へ整理できる。負の平方根や根号内のν、分子分母の交換を許さない。',
 '全速度・全56役割の条件を有限列挙へ置き換えない。局所検査は数値対照、12定義の速度引数の一貫した伝達、元への特殊化、引用と提示の確認であり、物理法則の真理又は意味同義性の自動証明ではない。',
 'u0178及びu0192以降は未完。u0192の固定在庫と原刊の無限大の印字を、この式へ都合よく訂正した内容として先取りしない。',
]

def lifted(old):
    ds={d['name']:d for d in old['declarations']};rs=parse('n:\nr temp[] '+R+'.')['declarations'][0]['result'];parameter='speedparameter'
    def transform(node):
        if isinstance(node,list):return [transform(x) for x in node]
        if not isinstance(node,dict):return node
        if node.get('kind')=='call' and node['symbol']=='zb7':
            assert not node['arguments'];return dict(kind='variable',name=parameter)
        out={n:transform(x) for n,x in node.items()}
        if node.get('kind')=='call' and node['symbol'] in LIFT:
            out['symbol']=LIFT[node['symbol']];out['arguments']=[dict(kind='variable',name=parameter),*out['arguments']]
        return out
    result=[]
    for d in old['declarations']:
        if d['name'] not in LIFT:continue
        assert d['kind']=='definition' and all(p['name']!=parameter for p in d['parameters'])
        new=deepcopy(d);new['name']=LIFT[d['name']];new['parameters']=[dict(name=parameter,sort=rs),*new['parameters']];new['body']=transform(new['body']);result.append(new)
    assert len(result)==12
    assert all(not _references(d['body'])&({'zb7'}|set(LIFT)) for d in result)
    return result

def definitions():
    text=''.join('r '+n+'['+' '.join(t for _,t in fs)+'] '+('c' if fs else 'a')+'.\n' for n,(fs,_) in PRIMITIVES.items())
    zero=k('bb','n p a b');one=k('bb','n p b b');V=v('light');speed=v('speed');nu=v('frequency');ratio=k('shv',speed,k('sjd',V))
    text+=define('ekev',[('light',R),('speed',R)],both(k('ba',V),k('ba',speed),k('bg',zero,V),k('bg',zero,speed),k('bg',speed,V)))
    fields=[(n,R) for n in ('light','speed','frequency')]
    text+=define('ekew',fields,k('shv',nu,k('sky',k('shv',k('bf',one,ratio),k('sjd',k('bd',one,ratio))))),R)
    text+=define('ekex',fields,both(k('ekev',V,speed),k('ba',nu),k('bg',zero,nu),k('sca',k('ekdr',V,speed,nu,one),k('ekew',*args(fields)))))
    text+=define('ekey',EXTENDED,both(k('ekev',V,speed),k('eket',*args(EXTENDED)),k('sca',v('angle'),zero)))
    text+=define('ekez',EXTENDED,k('sca',v('newfrequency'),k('ekew',V,speed,nu)))
    fixed={'frame':k('ra'),'scope':k('eisrx'),'context':v('point'),'light':k('tc')};actual=[fixed.get(n,v(n)) for n,t in EXTENDED]
    for name,premise,conclusion in [('eke2',both(k('ekev',k('tc'),speed),k('eket',*actual)),k('ekeu',*actual)),('eke3',k('ekey',*actual),k('ekez',*actual)),('eke4',k('ekey',*actual),k('ekeu',*actual))]:
        body=op('y',premise,conclusion)
        for n,t in reversed(QUANTIFIED):body=q('f',n,t,body)
        text+=content(name,body)
    node=k('eissq');display=k('eissr');prior=k('eissn');author=k('rd');scope=k('eisrx');p=v('point')
    text+=content('eke5',both(k('eissb',node,prior,author,quote('ekeb'),quote('eke2'),scope,p),k('eisch',k('eisss'),quote('eke2'),scope,p)))
    text+=content('eke6',both(k('eissb',node,prior,author,quote('eke4'),quote('eke3'),scope,p),k('eissp',quote('eke3'),scope,p),k('uf',author,node,display,p),k('ue',node,display,p)))
    text+=content('eke7',both(evaluate('eke5'),evaluate('eke6')))
    text+=content('ekfc',k('eisox',display,quote('eke3'),p))
    for shown,msg,statement,item,previous in [('eke7','ekfa','ekfb','eissq','eissn'),('ekfc','ekfd','ekfe','eissr','eissq')]:
        text+='d '+msg+'[] f[j s[k '+shown+'[]]].\n'
        text+=define(statement,[],both(k('eir3',k(item),author,k('eirf'),quote(msg),k('ri')),k('ue',k(previous),k(item),k('ri')),op('u',op('e',k(previous),k(item)))))
    return text

def build():
    old=parse(read(PARENT));assert len(old['statements'])==372
    assert not(set(PRIMITIVES)|set(MEANINGS))&{d['name'] for d in old['declarations']}
    doc=deepcopy(old);doc['statements']=[];doc['declarations']+=lifted(old);doc=parse(format_graph(doc,'compact')+definitions())
    doc['statements']=old['statements']+[dict(kind='assert',body=dict(kind='call',symbol=n,arguments=[])) for n in ('ekfb','ekfe')]
    added=doc['declarations'][len(old['declarations']):]
    primitives={d['name']:dict(parameters=d['parameters'],result=d['result'],arguments=[n for n,t in PRIMITIVES[d['name']][0]],meaning_ja=PRIMITIVES[d['name']][1]) for d in added if d['kind']=='primitive'}
    basis=dict(status='all_admissible_speeds_named_doppler_law_and_zero_angle_form',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives=primitives,definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=INDICES).document
    ann=json.loads(read('data/observed-doppler-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    ann['entries'].append(dict(symbol='eisss',role='designation',forms=[dict(text='Doppelersche Prinzip',language='de',role='printed_identifying_form')]))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
