"""Connect the seventh heading to physical settings and theoretical accounts."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_observed_intensity import ROOT,read
from scripts.compose_doppler_specialization import EXTENDED as DOPPLER,QUANTIFIED as DOPPLER_VARIABLES
from scripts.compose_aberration_presentation import SETTING as ABERRATION,VARIABLES as ABERRATION_VARIABLES
from scripts.compose_doppler_infinity import quantified
from scripts.compose_relativity_conjecture import content
from scripts.compose_two_postulates import quote
from scripts.compose_material_relative_frame import define
from scripts.compose_limits import v,call as k,op,both

PARENT='examples/v014/einstein-observed-intensity.noema';PARENT_BASIS='data/observed-intensity-basis-v1.json'
FULL='examples/v014/einstein-seventh-section-heading.noema';CORE='examples/v014/seventh-section-heading-core.noema'
BASIS='data/seventh-section-heading-basis-v1.json';ANNOTATIONS='data/seventh-section-heading-identifiers-v1.json';INDEX=384
PRIMITIVES={
 'eisth':([('inquiry','a'),('settings','i[e]'),('account','i[e]'),('context','d')],'同じinquiryが、settingsの閉じた記述で意味と役割を指定した対象・量・条件の関係について、accountの閉じた定式化を参照しながら、その規則性・成立条件・他の原理との関係・理論的説明及び導出を研究の主題とする。単なる名称の列挙、実例の収集、語源の説明だけとは区別する。settingsとaccountは同じ論点の対象と量を共有し、前者は扱う設定の種類、後者は検討する定式化を指定する。主題の案内であり、引用した設定の現実成立、定式化の真理・導出成功・実証済み、全研究の完了を要求しない。不整合を含む定式化も検討対象として参照できるが、無関係な記述を同じ対象の説明と認めない。'),
 'eisti':([], '固定原文einstein-1905:u0178の第七節見出しの箇所。既存の区分eisrx、前の第六節末尾eisrs、次の波の仮定eisryとは別である。'),
}
MEANINGS={
 'ekkp':'K・V・第七節と評価状況を固定し、同じ60役割の許容速度と物理的な放射源・波・観測者・二系・周期・周期数をeketへ一つの56証人として結ぶ設定記述。研究対象を示すために引用し、ドップラー等式を設定へ含めない。',
 'ekkq':'同じ65役割の源・波・観測者・二系・単位・角と新系の波面法線及び光線方向をekgyへ一つの61証人として結ぶ設定記述。結線との新角の字義的読解を保持し、印刷された光行差の等式を設定へ追加しない。',
 'ekkr':'同じDoppelersche Prinzipの呼称ekkvを既存eke2の放射/受信周期数の関係へ結び、同じ研究がekkpの物理設定とeke2の定式化を対象に規則性・条件・説明・導出を扱うというドップラー側の理論主題。',
 'ekks':'同じ研究がekkqの波の方向・角の物理設定と、既存ekhcの光行差の定式化を対象に理論的な説明を扱うという光行差側の主題。本文の法則名eiss3と同じ定式化への対応を保持し、方向変化を原語名だけへ縮めない。',
 'ekkt':'同じinquiryとcontextでekkrとekksの両方を扱う複合主題。Theorieが両項へ掛かる読みとundの並列を保持する。二つの別の研究や片方だけへ分けない。',
 'ekku':'同じ第二部の深さ2・表示番号7の既存第七節eisrxを、ekktの二主題へ結ぶ見出し。第六節末尾eisrsから見出しeisti、続く波の仮定eisryへの順序と箇所の区別を保持する。本文の物理的な結果を断言するメッセージではない。',
 'ekkv':'本文で既に命名した同じDoppelersche Prinzipの呼称eisssを返す別表記用の参照。見出しの属格Doppelerschen Prinzipsを別添えの識別表記に保持し、別の原理個体や意味へ変えない。',
}
LIMITS=[
 'u0178全文を原刊910頁に照合する。§7、Theorie、Doppelerschen Prinzips、und der Aberrationを保持し、Doppelerschenを現在一般的な綴りへ訂正しない。本文の既存呼称と同じ個体への別表記参照を作り、旧識別記録を変更しない。',
 'Theorieは二現象の規則性・成立条件・原理との関係・説明及び導出を扱う研究主題として読む。既に完成した真の理論の存在、見出しにおける物理法則の断言、実験実施、二分野全体の網羅を意味しない。',
 'ドップラー側は同じ源の放射周期数と、相対運動する同じ観測者の系での受信周期数の関係を対象とする。既存の周期と位相率の区別、同じ波・二系・単位・旧角・許容速度を保持し、音波や単なる文字列の名称を代わりにしない。',
 '光行差側は同じ波の変換後法線・光線方向と、源と観測者の結線に対する角という本文の規約を対象にする。設定ekgyと定式化ekhcを分離し、原刊の印刷式との不整合を主題の正しさのために消さない。特定の直角例や速度方向への暗黙の訂正へ縮めない。',
 '同じ一つの研究について両主題を連言する。各設定記述は引用内にあるため、見出しの成立時に二つの物理的実例が実在するとは要求しない。Theorieの射程を第一項だけへ限定しない。',
 '既存eisrxを第七節の区分として再利用する。第二部eispbに直接属する深さ2、紙面番号7、範囲u0178–u0201を保ち、次の同階層の見出しu0202で閉じる。箇所・区分・親を区別し、旧主張の配列を並べ替えず本文順序ueで接続する。',
 '新しい一般関係は設定記述と検討する定式化を分ける理論研究の主題関係だけである。物理量・波・周波数・方向・角・運動は既存の合成へ結び、原文一文を一原始語で代用しない。',
 '有限検査は各設定証人の結合、主題の同一研究への接続、引用と名前の対応、番号・階層・順序を検査する。全実数・全関数の設定を有限標本に置き換えず、引用した設定や法則を見出しから真と認定しない。',
]

def definitions():
    text=''.join('r '+n+'['+' '.join(t for _,t in fs)+'] '+('c' if fs else 'a')+'.\n' for n,(fs,_) in PRIMITIVES.items())
    fixed={'frame':k('ra'),'light':k('tc'),'scope':k('eisrx'),'context':v('point')}
    ds=[fixed.get(n,v(n)) for n,t in DOPPLER];ab=[fixed.get(n,v(n)) for n,t in ABERRATION]
    text+=content('ekkp',quantified('g',DOPPLER_VARIABLES,both(k('ekev',k('tc'),v('speed')),k('eket',*ds))))
    text+=content('ekkq',quantified('g',ABERRATION_VARIABLES,k('ekgy',*ab)))
    text+=define('ekkv',[],k('eisss'),'a')
    topic=[('inquiry','a'),('context','d')];inquiry=v('inquiry');ctx=v('context')
    for name,settings,account,designation in [('ekkr','ekkp','eke2','ekkv'),('ekks','ekkq','ekhc','eiss3')]:
        text+=define(name,topic,both(k('eisch',k(designation),quote(account),k('eisrx'),ctx),k('eisth',inquiry,quote(settings),quote(account),ctx)))
    text+=define('ekkt',topic,both(k('ekkr',inquiry,ctx),k('ekks',inquiry,ctx)))
    node=k('eisti');section=k('eisrx');previous=k('eisrs');following=k('eisry');point=k('ri')
    text+=define('ekku',[],both(k('eihq',node,section,k('eispb'),k('eirf'),'n p c b','n p h b','r[p ekkt]',point),k('ue',previous,node,point),k('ue',node,following,point),op('u',op('e',previous,node)),op('u',op('e',node,following))))
    return text

def build():
    old=parse(read(PARENT));assert len(old['statements'])==INDEX
    assert not(set(PRIMITIVES)|set(MEANINGS))&{d['name'] for d in old['declarations']}
    doc=deepcopy(old);doc['statements']=[];doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']+[dict(kind='assert',body=dict(kind='call',symbol='ekku',arguments=[]))]
    added=doc['declarations'][len(old['declarations']):]
    primitives={d['name']:dict(parameters=d['parameters'],result=d['result'],arguments=[n for n,t in PRIMITIVES[d['name']][0]],meaning_ja=PRIMITIVES[d['name']][1]) for d in added if d['kind']=='primitive'}
    basis=dict(status='seventh_section_doppler_and_aberration_theory_heading',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives=primitives,definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=[INDEX]).document
    ann=json.loads(read('data/observed-intensity-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    ann['entries'].append(dict(symbol='ekkv',role='designation',forms=[dict(text='Doppelerschen Prinzips',language='de',role='printed_identifying_form')]))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
