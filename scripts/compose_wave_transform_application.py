"""Apply coordinate and field transformations to the same local wave."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_wave_inquiry import ROOT,read,FAMILY,SETTING,query_args,QUESTION
from scripts.compose_wave_display import DISPLAY,PHASE,COORDS,representatives
from scripts.compose_distant_wave_source import WITNESSES,PROFILE,AMPLITUDES
from scripts.compose_field_equations import FIELD,REGION,POINT,TAU,ROLES
from scripts.compose_field_transformation_application import coordinates
from scripts.compose_wave_approximation import MEANINGS as ERROR_MEANINGS
from scripts.compose_material_relative_frame import define,args
from scripts.compose_relativity_conjecture import content
from scripts.compose_two_postulates import quote
from scripts.compose_electromotive_wording import bind
from scripts.compose_limits import R,v,call as k,app,op,both,quant as q

PARENT='examples/v014/einstein-wave-inquiry.noema';PARENT_BASIS='data/wave-inquiry-basis-v1.json'
FULL='examples/v014/einstein-wave-transform-application.noema';CORE='examples/v014/wave-transform-application-core.noema'
BASIS='data/wave-transform-application-basis-v1.json';ANNOTATIONS='data/wave-transform-application-identifiers-v1.json';INDICES=[367,368,369]
EVENTS=[('process','a'),('context','d')]
MAPPING=[('light',R),('speed',R),('oldpoint',POINT),('newpoint',POINT)]
EVENT_MAP=EVENTS+[('light',R),('speed',R)]
LOCAL=EVENT_MAP+[('region',REGION)]
WAVE=[('sine',PROFILE)]+[(n,R) for n in ('light','speed','rate','ax','ay','az',*AMPLITUDES)]
RESULT=[('electricrepresentative',FIELD),('magneticrepresentative',FIELD),('phase',TAU)]
CODE='i[h['+' '.join(t for n,t in FAMILY)+'] c]'
TRUE=op('e','n p a b','n p a b')
PRIMITIVES={
 'eissg':([('node','a'),('author','a'),('anchor','a'),('prior','i[e]'),('premise',CODE),('result',CODE),('immediate','c'),('scope','a'),('context','d')],'authorがscopeのanchorから引き継いだpriorの仮定について、同じ引数割当のpremiseからresultを得るとnodeで提示する。両規則は閉じた同じ型の引数列を取り、先行の対象と追加設定を答え候補又は変形の前後で選び直さない。immediateが真なら、採用する変換・規則の直接の代入と式の整理で得るものとして提示し、新たな物理的仮説・実験結果・別の中間的論証の導入をその場の導出手段としない。所要秒数・読者の容易さ・処理系の証明済みを意味しない。どの規則を適用するかはpremise/resultの本体と別の参照関係で指定する。導出の著者帰属であり、仮定の現実成立、引用の自動評価、物理法則又は計算の健全性の自動認定ではない。'),
 'eissh':([], 'u0182後半のDurch Anwendungからerhalten wir unmittelbar:までの、両変換の適用と結果導入の箇所。'),
 'eissi':([], 'u0183=M0325の六成分とu0184=M0326の位相を合わせた、同じ変換後の七表示式の箇所。'),
 'eissj':([], 'u0185のwobei、u0186=M0327の角周波数と三方向余弦の四式、u0187のgesetzt ist.を合わせた補足指定の箇所。'),
}
MEANINGS={
 'seau':ERROR_MEANINGS['seau'],
 'seav':ERROR_MEANINGS['seav'],
 'ekce':'有効な旧新の四座標と許容V/vについて、新点が係数1のs46(V,v,旧点)に、旧点がs46(V,−v,新点)に全四成分で一致する。時間と空間、正変換と逆変換を分ける。',
 'ekcf':'同じ過程の所属出来事が非空で、その全てがKとkの双方のeiyx座標記録を持つ。変換に成功した記録だけを所属範囲へ選ばず、別の出来事を両系へ一つずつ割り当てない。',
 'ekcg':'ekcfの同じ過程について、全ての同一出来事のK/k記録対ejtgがekceの四座標変換を満たす。任意の別過程の記録や、一つの成功対だけへ縮めない。',
 'ekch':'同じ過程に旧局所領域内の出来事が少なくとも一つあり、全ての同一出来事の記録対について旧領域所属と新逆像領域所属が一致する。過程全体や遠方の源を局所領域内に押し込めず、領域外の出来事も座標対応の範囲に保つ。',
 'ekci':'先行の同じ波を問う条件ekb3、同じ過程の物理的座標対応ekch、実際の二場をs6k/s6lで変換したものが同じ観測者の問いの物理的な候補ekccであることを合わせる。第六節の場変換則を現在の波に適用する条件であり、旧節の固定された別の場を流用しない。',
 'ekcj':'許容V/v・位相率・単位方向・六振幅の下で、指定した変換後の二表現場と位相が、同じ新四座標で七表示式を満たす点条件。四つの横成分の符号と交差相手、同じ変換後位相を保持する。',
 'ekck':'同じ適用条件ekciで、旧近似表現をs6k/s6lで変換した二場と、旧位相の逆座標による引戻しが、新領域の全点で七表示式を満たす。実際の変換場との近似もseatに保ち、二誤差をseau/seavの混合後上限へ結ぶ。',
 'ekcl':'同じekckの設定と表示について、ω′及びa′,b′,c′をsdq2の四式で明示し、六振幅も同じ成分混合sdz2へ結ぶ補足。別の波や別の位相の定数を導入しない。',
 'ekcm':'先行の31証人と追加観測者6役割を一つの割当として束縛した、両変換の適用条件ekciの内容。K、第七節、Vと評価状況を固定する。',
 'ekcn':'同じ37証人でekckの七表示式と近似を述べる結果内容。後の著者帰属で先行から同じ割当を引き継ぐ。',
 'ekco':'同じ37証人でekclの四つの変換パラメータまで明示する補足内容。',
 'ekcp':'著者が同じ波の仮定の下で両変換の適用により結果を直接得ると提示し、第六節の最終六場変換ejvmと第三節の最終座標時刻変換ejehをそれぞれ参照する。コロンを後続の表示への説明・順序関係へ結ぶ。',
 'ekcq':'両変換を適用して直ちに得るという提示ekcpを述べるメッセージ。',
 'ekcr':'u0182後半を同じ著者・論説へ帰属し、同じ波を問う第一文に続ける。',
 'ekcs':'六成分と位相の同じ七表示式の内容をekcnへ対応させる。各成分に別の設定を選ばない。',
 'ekct':'七表示式の提示ekcsを述べるメッセージ。',
 'ekcu':'u0183–u0184の七表示式を同じ著者・論説へ帰属し、直前の結果導入の後へ結ぶ。',
 'ekcv':'wobei ... gesetzt istを、直前の表示と同じ設定のパラメータを四式で指定する説明としてekcoへ結ぶ。先行結果ekcnを保持した明示と表示への内容対応を合わせる。',
 'ekcw':'四つの変換パラメータを指定する補足ekcvを述べるメッセージ。',
 'ekcx':'u0185–u0187の補足指定を同じ著者・論説へ帰属し、直前の七表示式に続ける。',
}
LIMITS=[
 'u0182後半とu0183–u0187を原刊911頁の一続きの導出・表示・補足として読む。固定在庫ではM0325は六成分、M0326は位相、M0327が角周波数と方向の四式である。前回の再開情報にあったM0326を方向変換とする案内は訂正し、原資料は変更しない。',
 '§6の参照は値1を採った最終六場変換ejvm、§3の参照は係数1の最終座標時刻変換ejehである。中間のφ/ψを再導入しない。先行の導出に関する反例と留保は保持し、参照と適用の著者帰属を新たな物理的証明へ格上げしない。',
 '同じ過程の全所属出来事へ両系の座標を要求し、同一出来事の全記録対へ変換を適用する。局所領域内の出来事の存在を別に要求するが、源も含めた全過程の全出来事が原点付近にあるとは要求しない。座標記録は先行の測定・時刻付与の規約を使う理想記述であり、実測済みのデータの報告ではない。',
 '表示のX′,Y′,Z′,L′,M′,N′は先行の近似表現を変換したものとして読む。実際の場の変換と同じ写像・混合を使い、誤差はβ(εE+|v/V|εH)とβ(εH+|v/V|εE)へ運ぶ。零誤差や実際の場が厳密な正弦波であることを補わない。元の用途上の十分性eisrwは同じ考察の設定に保持し、数値上限だけから周波数・方向の厳密同定や新しい精度保証を導かない。',
 'Φ′は旧Φを逆座標変換へ適用した同じ位相で、ω′(τ−(a′ξ+b′η+c′ζ)/V)に等しい。ω′は角周波数の位相率であり通常の周波数ν′と数値同一視しない。光源の方向、視線角、ドップラー原理と光行差の見出しへの接続は後続で必要である。',
 'wobei ... gesetzt istは同じ表示内の新しいパラメータを定める補足と読む。四式の分母1−av/Vとβ、三方向の各軸を保つ。βは正の枝、V>0、|v|<V、元の方向は単位長さであり、分母が零の範囲へ計算を広げない。',
 'unmittelbarは、ここで採用した両変換への代入と式の整理で直接結果を得るという著者の提示であり、反応時間や読者全員への容易さではない。Wirは論述主体である同じ著者の声と読む。引用した仮定と法則の現実成立を別に断言しない。',
 '同じ41引数の規則と37証人の内容を共有し、物理的な仮定・数式の表示・補足・著者帰属を分ける。有限算術例と有限の出来事モデルは束縛・符号・全範囲を診断するもので、全実数域・全関数域の列挙や正弦の全域の定理証明ではない。',
]

def transformed(speed=None):
    V=v('light');speed=speed or v('speed');old=representatives();beta=k('soy',V,speed);ratio=k('shv',speed,k('sjd',V))
    newamps=[v('ex'),k('s6d',beta,ratio,v('ey'),v('hz')),k('s6e',beta,ratio,v('ez'),v('hy')),v('hx'),k('s6e',beta,ratio,v('hy'),v('ez')),k('s6d',beta,ratio,v('hz'),v('ey'))]
    shifted=[k('sdn2',V,speed,v('rate'),v('ax')),k('sdo2',V,speed,v('ax')),k('sdp2',V,speed,v('ax'),v('ay')),k('sdp2',V,speed,v('ax'),v('az'))]
    fields=[k(n,V,speed,old['electricrepresentative'],old['magneticrepresentative']) for n in ('s6k','s6l')]
    inverse='i[point '+POINT+']['+k('s46',V,k('bf',k('bb','n p a b'),speed),v('point'))+']'
    phase=k('s6f',old['phase'],inverse)
    return newamps,shifted,fields,phase

def definitions():
    text=''.join('r '+n+'['+' '.join(t for _,t in fs)+'] '+('c' if fs else 'a')+'.\n' for n,(fs,_) in PRIMITIVES.items())
    V=v('light');speed=v('speed');ctx=v('context');process=v('process');old=v('oldpoint');new=v('newpoint');zero=k('bb','n p a b')
    error_args=[('light',R),('speed',R),('electricbound',R),('magneticbound',R)]
    ratio=k('shu',k('shv',speed,k('sjd',V)))
    for name,own,other in [('seau','electricbound','magneticbound'),('seav','magneticbound','electricbound')]:
        text+=define(name,error_args,k('shv',k('soy',V,speed),k('bd',v(own),k('shv',ratio,v(other)))),R)
    forward=k('s46',V,speed,old);inverse=k('s46',V,k('bf',zero,speed),new)
    text+=define('ekce',MAPPING,both(k('s45',V,speed),*(k('ba',app(p,k(role))) for p in (old,new) for role in ROLES),*(k('sca',app(new,k(role)),app(forward,k(role))) for role in ROLES),*(k('sca',app(old,k(role)),app(inverse,k(role))) for role in ROLES)))
    member=k('eispo',v('event'),process,ctx)
    records=both(*(q('g','record','a',k('ejtf',process,v('event'),v('record'),k(frame),ctx)) for frame in ('ra','zbm')))
    text+=define('ekcf',EVENTS,both(q('g','event','a',member),q('f','event','a',op('y',member,records))))
    lab=v('lab');own=v('own');selected=k('ejtg',process,lab,own,ctx);oldpoint=coordinates(lab);newpoint=coordinates(own)
    allpairs=lambda body:q('f','lab','a',q('f','own','a',op('y',selected,body)))
    text+=define('ekcg',EVENT_MAP,both(k('ekcf',*args(EVENTS)),allpairs(k('ekce',V,speed,oldpoint,newpoint))))
    oldinside=k('ejsj',oldpoint,v('region'));newinside=k('ejsj',newpoint,k('s6m',V,speed,v('region')))
    exists=q('g','lab','a',q('g','own','a',both(selected,oldinside)))
    text+=define('ekch',LOCAL,both(k('ekcg',*args(EVENT_MAP)),exists,allpairs(op('z',oldinside,newinside))))
    s=k('zb7');region=k('ekb2',v('space'),v('lower'),v('upper'),V);oldregion=k('ekau',v('space'),v('lower'),v('upper'))
    actual=[k(n,V,s,v('electricfield'),v('magneticfield')) for n in ('s6k','s6l')]
    text+=define('ekci',FAMILY,both(k('ekb3',*args(FAMILY)),k('ekch',process,ctx,V,s,oldregion),k('ekcc',*query_args(),*actual)))
    amps,shifted,fields,phase=transformed()
    display=[v('sine'),V,*shifted,*amps,*args(RESULT)]
    numeric=[V,speed,v('rate'),v('ax'),v('ay'),v('az'),*[v(n) for n in AMPLITUDES]]
    text+=define('ekcj',WAVE+RESULT+COORDS,both(k('sdy2',*numeric),k('ekbg',*display,*args(COORDS))))
    amps,shifted,fields,phase=transformed(s)
    display=[v('sine'),V,*shifted,*amps,*fields,phase]
    bounds=[k(n,V,s,v('electricbound'),v('magneticbound')) for n in ('seau','seav')]
    text+=define('ekck',FAMILY,both(k('ekci',*args(FAMILY)),k('ekbh',*display,region),k('seat',*actual,*fields,*bounds,region)))
    text+=define('ekcl',FAMILY,both(k('ekck',*args(FAMILY)),k('sdq2',V,s,v('rate'),v('ax'),v('ay'),v('az'),*shifted),k('sdz2',V,s,*[v(n) for n in AMPLITUDES],*amps)))
    witnesses=[(n,t) for n,t in FAMILY if n not in ('frame','scope','context','light')]
    override={'frame':k('ra'),'scope':k('eisrx'),'context':v('point'),'light':k('tc')}
    for root,rule in [('ekcm','ekci'),('ekcn','ekck'),('ekco','ekcl')]:text+=content(root,bind(witnesses,k(rule,*[override.get(n,v(n)) for n,t in FAMILY])))
    node=k('eissh');a=k('rd');scope=k('eisrx');p=v('point')
    refs=[k('eisov',node,a,k(section),quote(rule),k('eirf'),p) for section,rule in [('zno','ejvm'),('eisms','ejeh')]]
    text+=content('ekcp',both(k('eissg',node,a,k('eissf'),quote('ekbn'),'r[p ekci]','r[p ekcl]',TRUE,scope,p),*refs,k('uf',a,node,k('eissi'),p),k('ue',node,k('eissi'),p),op('u',op('e',node,k('eissi')))))
    text+=content('ekcs',k('eisox',k('eissi'),quote('ekcn'),p))
    text+=content('ekcv',both(k('eissb',k('eissj'),k('eissi'),a,quote('ekcn'),quote('ekco'),scope,p),k('eisox',k('eissj'),quote('ekco'),p),k('uf',a,k('eissi'),k('eissj'),p)))
    for shown,message,statement,node,prior in [('ekcp','ekcq','ekcr','eissh','eissf'),('ekcs','ekct','ekcu','eissi','eissh'),('ekcv','ekcw','ekcx','eissj','eissi')]:
        text+='d '+message+'[] f[j s[k '+shown+'[]]].\n'
        text+=define(statement,[],both(k('eir3',k(node),a,k('eirf'),quote(message),k('ri')),k('ue',k(prior),k(node),k('ri')),op('u',op('e',k(prior),k(node)))))
    return text

def build():
    old=parse(read(PARENT));assert len(old['statements'])==INDICES[0]
    assert not(set(PRIMITIVES)|set(MEANINGS))&{d['name'] for d in old['declarations']}
    doc=deepcopy(old);doc['statements']=[];doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']+[dict(kind='assert',body=dict(kind='call',symbol=n,arguments=[])) for n in ('ekcr','ekcu','ekcx')]
    added=doc['declarations'][len(old['declarations']):]
    primitives={d['name']:dict(parameters=d['parameters'],result=d['result'],arguments=[n for n,t in PRIMITIVES[d['name']][0]],meaning_ja=PRIMITIVES[d['name']][1]) for d in added if d['kind']=='primitive'}
    basis=dict(status='same_wave_coordinate_and_field_transformation_application',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives=primitives,definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=INDICES).document
    ann=json.loads(read('data/wave-inquiry-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
