"""Compose a disciplinary topic, its moving-body scope and a title framing."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_apparent_asymmetry import ROOT,read
from scripts.compose_material_body_motion import FIELDS as MOTION
from scripts.compose_electric_action import FIELDS as ELECTRIC
from scripts.compose_magnetic_action import FIELDS as MAGNETIC
from scripts.compose_current_distribution import HISTORY
from scripts.compose_material_relative_frame import define,args
from scripts.compose_limits import v,call as k,op,both

PARENT='examples/v014/einstein-apparent-asymmetry.noema';PARENT_BASIS='data/apparent-asymmetry-basis-v1.json'
FULL='examples/v014/einstein-electrodynamics-title.noema';CORE='examples/v014/electrodynamics-title-core.noema'
BASIS='data/electrodynamics-title-basis-v1.json';ANNOTATIONS='data/electrodynamics-title-identifiers-v1.json';INDEX=212
def code(fields):return 'i[h['+' '.join(t for _,t in fields)+'] c]'
TOPIC=[('inquiry','a'),('context','d')]
FIELD_TOPIC=[('inquiry','a'),('current',code(HISTORY)),('electric',code(ELECTRIC)),('magnetic',code(MAGNETIC)),('context','d')]
BODY_SCOPE=[('inquiry','a'),('motion',code(MOTION)),('context','d')]
HEADING=[('node','a'),('document','a'),('topic',code(TOPIC)),('context','d')]
PRIMITIVES={
 'eisa6':(FIELD_TOPIC,'指定inquiryが、currentで同定する電荷の輸送、electricとmagneticで区別する電気側・磁気側の場と物質への作用について、その時空間的な関係・生成・変化・作用を法則として記述し説明する研究主題に属する。三つの閉じた型の意味規約が電荷・電流・場・力の物理的同定を共有する。この主題分類は特定法則の正しさ、全法則の完成、実験の実施を認定しない。型内の個別の関係式をあらゆる理論への必要公理として課すのではなく、研究対象である物理量と作用の区別を指定する。単に数値関数を研究する主題や無説明の分野名とは区別する。'),
 'eisa7':(BODY_SCOPE,'指定inquiryの対象を、閉じたmotion型が記述する物体の基準系に対する運動を含む場合と、その運動が対象の記述にどう関係するかへ限定する主題関係。型の同じ物体・全物質点・系・尺度・区間履歴を用い、見かけの名札や中心一点の変位だけを運動としない。仮定上の運動の場合を扱うことを許し、現在ここに動く特定物体が存在すること、全ての物体が動くことを要求しない。比較や説明のための静止の場合を排除せず、対象を磁石と導体、等速並進、剛体だけへ限定しない。'),
 'eisba':([('node','a'),('document','a'),('context','d')],'nodeが同じdocumentの表題として提示され、その文書の主題を読者へ示して文書を識別する前付の箇所である。本文中の一命題、著者名の表示、他文献への言及とは区別する。特定の字形・書体や実際の印刷者を要求しない。'),
 'eisbb':(HEADING,'nodeで同じdocumentを、閉じたtopicが指定する研究主題についての考察・論説への寄与として位置付ける。topicのinquiryとcontextを保った主題を参照し、単にその分野名を引用するだけではない。この位置付けは論説の扱う内容の案内であり、その内容の真理、成功、新規性、分野全体の網羅、解答の完成や物理的事例の実在を保証しない。表題か本文かという提示箇所の役割は別関係で指定する。'),
 'eisbc':([], '固定原文einstein-1905:u0001の表題全体の箇所。主題内容をこの個体名そのものへ隠さず、eie5/eie6と表題の位置付けを別に合成する。'),
}
MEANINGS={
 'eie5':'同じinquiry・contextについて、電荷輸送eibf、電気的作用eibs、磁気的作用eicoの閉じた型をeisa6へ渡して電気力学という研究主題を指定する。Maxwellの特定の理論や当時の通常理解という個体へ主題を縮めない。',
 'eie6':'同じinquiry・contextで電気力学eie5と、全物質点・全区間による物体運動eiagへの対象限定eisa7を同時に要求する主題の型。単に運動学だけ又は静止の電気力学だけを主題にしない。現実に動く物体の存在命題を作らない。',
 'eie7':'同じ箇所が同じ文書の表題であり、同じ閉じたtopicへの考察・寄与としてその文書を位置付けるという合成。主題名だけや本文の主張だけを表題の役割としない。',
 'eifa':'この論説eirfの表題eisbcが、動く物体の電気力学eie6についての考察として同じ文書を提示することを記述する。前付文脈eirgを共有し、著者表示eireと導入冒頭eir7に先行する別の箇所として結ぶ。',
}
LIMITS=[
 'Zurを、この主題についての考察・論説への寄与として提示する前置と読む。完全体系、新規性、成功や後続本文の真理は補わない。',
 '電気力学は電荷・電流・電磁場と物質の作用の法則を扱う分野とし、型の既存規約で物理的対象を固定する。Maxwellの既存理論だけや通常理解だけへの限定ではない。',
 'bewegter Körperは物体運動を含む場合への研究主題の限定とする。運動の基準系・記述尺度と全履歴の規約を引き継ぎ、特定の現実の物体や系は選ばない。静止との比較を禁止する排他的な対象一覧ではない。',
 '引用した主題の提示を評価する際に運動や場の式を実行しない。本文の全物理主張の経験的証明と表題の記述を区別する。',
]

def definitions():
    text=''.join('r '+n+'['+' '.join(t for _,t in fs)+'] '+('a' if not fs else 'c')+'.\n' for n,(fs,_) in PRIMITIVES.items())
    text+=define('eie5',TOPIC,k('eisa6',v('inquiry'),'r[p eibf]','r[p eibs]','r[p eico]',v('context')))
    text+=define('eie6',TOPIC,both(k('eie5',*args(TOPIC)),k('eisa7',v('inquiry'),'r[p eiag]',v('context'))))
    text+=define('eie7',HEADING,both(k('eisba',v('node'),v('document'),v('context')),k('eisbb',*args(HEADING))))
    text+=define('eifa',[],both(k('eie7',k('eisbc'),k('eirf'),'r[p eie6]',k('eirg')),k('ue',k('eisbc'),k('eire'),k('eirg')),k('ue',k('eisbc'),k('eir7'),k('eirg')),op('u',op('e',k('eisbc'),k('eire'))),op('u',op('e',k('eisbc'),k('eir7')))))
    return text

def build():
    old=parse(read(PARENT));assert len(old['statements'])==INDEX;doc=deepcopy(old);doc['statements']=[]
    assert not(set(MEANINGS)|set(PRIMITIVES))&{d['name'] for d in doc['declarations']}
    doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']+[dict(kind='assert',body=dict(kind='call',symbol='eifa',arguments=[]))]
    added=doc['declarations'][len(old['declarations']):]
    primitives={d['name']:dict(parameters=d['parameters'],result=d['result'],arguments=[n for n,_ in PRIMITIVES[d['name']][0]],meaning_ja=PRIMITIVES[d['name']][1]) for d in added if d['kind']=='primitive'}
    basis=dict(status='electrodynamics_topic_motion_scope_and_title_framing',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives=primitives,definitions=MEANINGS,new_signatures={d['name']:{k:d[k] for k in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=[],statement_indices=[INDEX]).document
    ann=json.loads(read('data/apparent-asymmetry-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}

if __name__=='__main__':
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
