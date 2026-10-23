"""Describe the same moving wave and the author's compatibility conclusion."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_spherical_equation_rewrite import ROOT,read
from scripts.compose_material_relative_frame import define
from scripts.compose_two_postulates import quote
from scripts.compose_relativity_conjecture import content
from scripts.compose_limits import v,call as k,op,both,quant as q

PARENT='examples/v014/einstein-spherical-equation-rewrite.noema';PARENT_BASIS='data/spherical-equation-rewrite-basis-v1.json'
FULL='examples/v014/einstein-wave-compatibility-conclusion.noema';CORE='examples/v014/wave-compatibility-conclusion-core.noema'
BASIS='data/wave-compatibility-conclusion-basis-v1.json';ANNOTATIONS='data/wave-compatibility-conclusion-identifiers-v1.json';INDEX=307
MEANINGS={
 'ejal':'指定波の構成光線は非空で、全構成光線が同じ放出から指定系で現在の伝播区間ei73を持つ。その波の全適用区間について、放出whは同じ放出であり、ei44による現在の同じ系の時計・始終座標・幾何学的光路長・速度Vを要求する。放出点から始まる区間だけでなく途中の区間も含み、別の波の全区間へは広げない。',
 'ejam':'同じ波・放出・系・設定について、全構成光線と全適用区間の現在V伝播ejalと、全対象出来事で到来が正時刻の球面式に過不足なく一致するei75を合わせる。式の数値だけや一つの成功光線で波の全体を代用しない。',
 'ejan':'検討中の同じ波zfuと放出zfvが同じ設定zb6でKの球面波面を持ち、kでも現在のV伝播を持つ球面波ejamであるという内容。auchの既出Kと追加kを保持し、全ての波・全ての光の普遍法則へ拡張しない。',
 'ejao':'現在の同じ球面波設定・K式・四式・記録範囲を含むejagと、得られたk二乗式ejafを合わせた、波の結論に先行する内容。これだけで未来側の全到来波面が論理的に従うとは認定しない。',
 'ejap':'同じ球面波の設定と変換結果ejao、および両系の同じ波の結論ejanを合わせ、Hiermitが指す球面波の議論の内容を特定する。単独の数値例や無関係な証明へ替えない。',
 'ejaq':'著者が先行設定とk式ejaoから、同じ波がkでも球面波であるejanを帰結として提示する。理由・結果・著者・第三節・箇所zgfを結ぶ。',
 'ejar':'同じ著者が球面波の議論ejapから、現行の二原理の両立性eif5を帰結として提示し、同じ箇所zggの内容を既に示されたものとして扱う。uiによる著者の証明済みという位置付けと、処理系の妥当性認定を分ける。',
 'ejas':'kでも同じVの球面波であるという帰結提示ejaqを断定の伝達形式にする。',
 'ejat':'波の結論を同じ著者・論説へ帰属し、前の球面方程式変換zgeからの順序を保持する。',
 'ejau':'二原理の両立性が示されたというejarを断定の伝達形式にする。',
 'ejav':'両立性の証明完了の提示を同じ著者・論説へ帰属し、同じ波の結論zgfからの順序を保持する。',
}
LIMITS=[
 'u0091の二文全体を原刊901頁へ照合する。Die betrachtete Welleは同じzfu、bewegten Systemは既出のk=zbm、Vは同じtc。auchは既出のK球面波にkでの球面性を加える関係として読む。',
 '球面波は前段と同じ幾何学的な到来波面の読みを採る。全対象出来事の現在記録で到来と正時刻の球面式が過不足なく一致し、波の全構成光線と全適用伝播区間が同じ放出・系・Vへ結ばれる。振幅・偏光・波長やMaxwell場全体の追加はしない。',
 '伝播速度の範囲は検討中の波に属する全適用区間であり、kの他の波や全光源の法則を第一文へ加えない。途中の区間も対象に含め、途中区間の始出来事を元の放出出来事に無理に等置しない。',
 '二乗式ejafは未来方向・全到来一致・全波の区間速度をそれだけでは保証しない。本文はそのような帰結を著者が述べたことをzcで記述する。原著者の物理的推論の妥当性を翻訳の完成条件とせず、欠けた前提を著者の発話へ追加して推論を修理しない。',
 '旧sqzは正のφ・記録存在・同じ到来の追跡を加える旧座標規約上の十分条件として保存するが、この本文の依存には用いない。現在の本文で一般物理的導出を証明するとも、φが正・非零・1だとここで決まるとも述べない。',
 'Hiermitは先行の同じ波の設定・座標変換・両系の波の結論を指す。unsere beiden Grundprinzipienは現在の相対性内容eifjと真空光速度内容eifyであり、同じ物理的意味の許容設定eiscjで共に成立し得るeif5を使う。別々の設定で一つずつ成り立つことへ弱めない。',
 'ist gezeigtは同じ著者が同じ箇所の内容を証明済みと位置付けるuiで表す。単なる期待・未証明課題や検査器による証明認定に替えない。u0086で以前の段階に証明が未提示だったことを取り消さず、論述の進行を保つ。',
 '語義・対象範囲・量化・参照・帰結と証明済みの提示を全て記述する。有限対照の成功から、一般実数域・連続空間・全物理的モデルや原文との意味同値を自動証明したとはしない。後続u0092の未知φを決める課題とu0093以降の第三系は残る。',
]
GROUPS=(('ejaq','ejas','ejat','zgf','zge'),('ejar','ejau','ejav','zgg','zgf'))


def definitions():
    w,e,f,c=map(v,('wave','emission','frame','context'));ray=v('ray');event=v('event');seg=v('segment')
    member=lambda r:k('zft',w,r,c)
    every_ray=q('f','ray','a',op('y',member(ray),q('g','event','a',q('g','segment','a',k('ei73',w,ray,e,event,seg,f,c)))))
    applicable=both(k('eiscd',seg,f,k('ta'),k('rb'),c),member(k('wf',seg)))
    measured=both(op('e',k('wh',seg),e),k('ei44',seg,k('wf',seg),k('wi',seg),k('wj',seg),k('wq',seg),f,k('tc'),c))
    fields=[('wave','a'),('emission','a'),('frame','a'),('context','d')]
    text=define('ejal',fields,both(q('g','ray','a',member(ray)),every_ray,q('f','segment','a',op('y',applicable,measured))))
    text+=define('ejam',fields,both(k('ejal',w,e,f,c),k('ei75',w,e,f,c)))
    wave=k('zfu');emission=k('zfv');ctx=k('zb6');point=v('point')
    text+=content('ejan',both(k('ei75',wave,emission,k('ra'),ctx),k('ejam',wave,emission,k('zbm'),ctx)))
    for name,parts in (('ejao',('ejag','ejaf')),('ejap',('ejao','ejan'))):
        text+=content(name,both(*(op('t',k(n),point) for n in parts)))
    text+=content('ejaq',k('zc',k('zgf'),k('rd'),quote('ejao'),quote('ejan'),k('eisms'),point))
    text+=content('ejar',both(k('zc',k('zgg'),k('rd'),quote('ejap'),quote('eif5'),k('eisms'),point),k('ui',k('rd'),k('zgg'),point)))
    for body,message,author,node,previous in GROUPS:
        text+='d '+message+'[] f[j s[k '+body+'[]]].\n'
        text+=define(author,[],both(k('eir3',k(node),k('rd'),k('eirf'),quote(message),k('ri')),k('ue',k(previous),k(node),k('ri')),op('u',op('e',k(previous),k(node)))))
    return text


def build():
    old=parse(read(PARENT));assert len(old['statements'])==INDEX;doc=deepcopy(old);doc['statements']=[]
    assert not set(MEANINGS)&{d['name'] for d in old['declarations']}
    doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']+[dict(kind='assert',body=dict(kind='call',symbol=g[2],arguments=[])) for g in GROUPS]
    added=doc['declarations'][len(old['declarations']):]
    basis=dict(status='same_moving_spherical_wave_and_attributed_compatibility_conclusion',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives={},definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=[INDEX,INDEX+1]).document
    ann=json.loads(read('data/spherical-equation-rewrite-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
