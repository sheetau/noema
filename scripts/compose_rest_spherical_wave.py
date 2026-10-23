"""Connect a common-origin spherical wave to current measurements and its equation."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_light_proof_task import ROOT,read
from scripts.compose_material_relative_frame import define
from scripts.compose_two_postulates import quote
from scripts.compose_relativity_conjecture import content
from scripts.compose_limits import v,call as k,op,both,quant as q

PARENT='examples/v014/einstein-light-proof-task.noema';PARENT_BASIS='data/light-proof-task-basis-v1.json'
FULL='examples/v014/einstein-rest-spherical-wave.noema';CORE='examples/v014/rest-spherical-wave-core.noema'
BASIS='data/rest-spherical-wave-basis-v1.json';ANNOTATIONS='data/rest-spherical-wave-identifiers-v1.json';INDEX=305
MEANINGS={
 'ei73':'指定波の同じ構成光線が同じ放出出来事から対象出来事まで伝播する現在の一区間。ei44により系・設定・V・幾何学的光路長・両端の現在四座標と時計を結び、区間の放出参照whも始出来事に一致させる。',
 'ei74':'指定波・放出・到来出来事・系・設定について、ei73を満たす光線と測定区間が存在する。到来を数式だけや別の放出からの伝播で代用しない。',
 'ei75':'現在のeiyxが与える全対象出来事・全座標記録で、同じ波の到来ei74と正時刻の球面式sqlが過不足なく一致する。少なくとも一つの到来点を要求し、記録の別名を排除しない。',
 'ei76':'同じ放出出来事の現在の両座標が共通零原点ei46を満たし、構成光線が非空で、その全てが同じ放出からKで現在の伝播区間ei73を持つ。波の一部だけに共通放出を要求することはしない。',
 'ei77':'同じ波を共通零原点から放出するei76、現在のKの全光区間法則ei43、Kでの未来側球面波面ei75を一つの仮定内容へ結ぶ。',
 'ejaa':'同じ波が到来する任意の対象出来事とその現在のK座標記録について、x²+y²+z²=V²t²を述べる条件内容。一つの成功点への固定を避け、同じ記録の三位置と時刻を用いる。',
 'ejab':'共通零原点からのK球面波を仮定する著者提示と、その設定の下で任意の到来点が球面式を満たすという帰結を同じ第三節へ結ぶ。',
 'ejac':'球面波の仮定と到来点の式ejabを断定の伝達形式にする。仮定の実在や現実の放出行為をこの提示から導かない。',
 'ejad':'u0087–u0088の二文と球面式を同じ著者・論説へ帰属し、直前の証明課題と理由の箇所zfyからの順序を保つ。',
}
LIMITS=[
 'u0087の二文とu0088の式・句点を原刊901頁へ照合する。werde ... ausgesandtは仮定上の放出設定であり、実験を実施した報告や読者への命令にしない。',
 '放出時のt=τ=0と両系の共通空間原点を、同じ放出出来事と現在の二座標のei46へ結ぶ。両系の原点が全時刻で重なることや、全出来事でt=τになることは加えない。',
 '波は同じ放出に由来する構成光線の非空な全範囲として扱い、各光線の現在のK区間を同じ放出へ結ぶ。ei44は物理的な伝播・局所時計・幾何学的光路長と座標付与を保持し、単に球面式が真なら光が到来したとはしない。仮定上の測定規約であり、実験済みの記録だけに限定しない。',
 '球面波は全対象出来事の現在の座標範囲で、同じ波の到来が正時刻の球面式に過不足なく一致するという幾何学的波面の読みを採る。全範囲は成功標本だけに縮めず、未測定の全実数四組の現実的な実在や場の振幅・偏光・波長の指定は加えない。',
 '二乗式sqkと未来側の正時刻sqlを区別する。零時刻の放出点はei76で別に扱い、負時刻の二乗式の解を伝播後の波面へ含めない。Vは同じ正のtcであり、全K光区間にも現在のei43で同じ値を渡す。',
 'Ist (x,y,z) ... so ist alsoは、同じ波がいま到来する任意の点についての条件付き帰結と読む。全対象出来事と現在のK記録を量化し、その同じ記録の時刻と三位置を使う。到来後の任意の時刻や波の内部全体を到来波面に混ぜない。',
 'x²+y²+z²=V²t²の三平方・二加法・右辺の積と二平方を既存sqj/sqkで保持する。波の未来側の幾何学的読みを数式の文字そのものへ追加するのではなく、放出・到来・正時刻の内容と分ける。',
 '後続u0089以降の座標変換による計算、kでの球面波の結論、二原理の両立性の証明完了は先取りしない。φを1へ固定しない。有限対照例は全物理的モデルや意味同値の自動証明ではない。',
]

def definitions():
    w,e,a,f,c=map(v,('wave','emission','event','frame','context'));ray=v('ray');seg=v('segment')
    fields=[(n,'a') for n in ('wave','ray','emission','event','segment','frame')]+[('context','d')]
    text=define('ei73',fields,both(k('zft',w,ray,c),k('cf',ray),k('ei44',seg,ray,e,a,k('wq',seg),f,k('tc'),c),op('e',k('wh',seg),e)))
    text+=define('ei74',[(n,'a') for n in ('wave','emission','event','frame')]+[('context','d')],q('g','ray','a',q('g','segment','a',k('ei73',w,ray,e,a,seg,f,c))))
    rec=v('record');chart=both(k('zc4',a),k('eiyx',a,rec,f,c));arrival=k('ei74',w,e,a,f,c);future=k('sql',rec,k('tc'))
    text+=define('ei75',[(n,'a') for n in ('wave','emission','frame')]+[('context','d')],both(q('g','event','a',q('g','record','a',both(chart,arrival,future))),q('f','event','a',q('f','record','a',op('y',chart,op('z',arrival,future))))))
    member=k('zft',w,ray,c)
    every=q('f','ray','a',op('y',member,q('g','event','a',q('g','segment','a',k('ei73',w,ray,e,a,seg,k('ra'),c)))))
    text+=define('ei76',[('wave','a'),('emission','a'),('context','d')],both(k('ei46',e,k('zdz',e,k('ra'),c),k('zdz',e,k('zbm'),c),c),q('g','ray','a',member),every))
    wave=k('zfu');emission=k('zfv');ctx=k('zb6');rest=k('ra')
    text+=content('ei77',both(k('ei76',wave,emission,ctx),k('ei43',rest,k('tc'),ctx),k('ei75',wave,emission,rest,ctx)))
    selected=both(k('zc4',a),k('eiyx',a,rec,rest,ctx),k('ei74',wave,emission,a,rest,ctx))
    text+=content('ejaa',q('f','event','a',q('f','record','a',op('y',selected,k('sqk',rec,k('tc'))))))
    text+=content('ejab',both(k('ug',k('zgc'),k('rd'),quote('ei77'),k('eisms'),v('point')),k('zc',k('zgd'),k('rd'),quote('ei77'),quote('ejaa'),k('eisms'),v('point')),k('ue',k('zgc'),k('zgd'),v('point')),op('u',op('e',k('zgc'),k('zgd')))))
    text+='d ejac[] f[j s[k ejab[]]].\n'
    text+=define('ejad',[],both(k('eir3',k('zgc'),k('rd'),k('eirf'),quote('ejac'),k('ri')),k('ue',k('zfy'),k('zgc'),k('ri')),op('u',op('e',k('zfy'),k('zgc')))))
    return text

def build():
    old=parse(read(PARENT));assert len(old['statements'])==INDEX;doc=deepcopy(old);doc['statements']=[]
    assert not set(MEANINGS)&{d['name'] for d in old['declarations']}
    doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']+[dict(kind='assert',body=dict(kind='call',symbol='ejad',arguments=[]))]
    added=doc['declarations'][len(old['declarations']):]
    basis=dict(status='current_rest_spherical_wave_and_arrival_equation',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives={},definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=[INDEX]).document
    ann=json.loads(read('data/light-proof-task-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
