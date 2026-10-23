"""Compose numbered part/section headings and their nonassertive topic roles."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_kinematic_difficulties import ROOT,read
from scripts.compose_material_relative_frame import define
from scripts.compose_limits import v,call as k,op,both

PARENT='examples/v014/einstein-kinematic-difficulties.noema';PARENT_BASIS='data/kinematic-difficulties-basis-v1.json'
FULL='examples/v014/einstein-kinematics-headings.noema';CORE='examples/v014/kinematics-headings-core.noema'
BASIS='data/kinematics-headings-basis-v1.json';ANNOTATIONS='data/kinematics-headings-identifiers-v1.json';INDICES=(219,220)
TOPIC='i[h[a d] c]';SIM='i[h[a a a a d] c]'
SAME=[('first','a'),('second','a'),('frame','a'),('unit','a'),('context','d')]
HEADING=[('node','a'),('division','a'),('parent','a'),('document','a'),('level','b'),('ordinal','b'),('topic',TOPIC),('context','d')]
PRIMITIVES={
 'eisdt':([('inquiry','a'),('simultaneous',SIM),('context','d')],'inquiryが、simultaneousの閉じた型で指定した、出来事に同じ基準系・時間尺度で付与した時刻の一致という関係を対象とする研究である。局所時計・共通参照・同期・付与値の有効性と一意性を型の意味規約から引き継ぐ。実際に同時な特定の出来事の存在や、異なる系に共通の絶対的同時性を主張する分類ではない。関係の意味と適用範囲への研究主題であり、原語の綴りへの言及だけとは区別する。'),
 'eisdu':([('inquiry','a'),('context','d')],'inquiryが、対象とする概念・関係の意味、何をもってその適用とするかの基準、その範囲と参照規約を明示する定義の仕事として位置付けられる。語源説明、真である具体例の列挙、対象名の言及だけとは異なる。定義を与えるという課題・論述の種類を指定し、見出しの時点で全定義・証明・実測が完了しているとは要求しない。'),
 'eisdv':([('node','a'),('division','a'),('parent','a'),('document','a'),('level','b'),('ordinal','b'),('context','d')],'nodeがdocumentのdivisionを開く番号付き見出しであり、divisionは同じ文書階層でparentに直接属する。levelは文書を深さ0として数えた正の整数の階層深さ、ordinalは紙面に表示された正の整数の部・節番号である。この論説では深さ1は部、深さ2は節を指す。ordinalを単に配列中の位置へ替えず、節番号が部をまたいで続くことも許す。divisionの支配範囲はこの見出しから次の同じ深さ又は上位の見出しの直前までで、下位の見出しとその本文も含む。見出しが指す区分と見出しの箇所を区別し、数字の書体・字形から物理量を作らない。'),
 'eisdw':([('node','a'),('division','a'),('topic',TOPIC),('context','d')],'nodeの見出しが、同じdivisionでこれから扱う論述の主題を、閉じたtopicの研究領域として読者に示す。区分全体の案内であり、各文がその主題名を繰り返すこと、全分野の網羅、本文の物理的主張の真理、定義や導出の完了は意味しない。topicの引用は主題を同定するために用い、具体的な物理的事例をその場で実行しない。'),
 'eisdx':([], 'この論説の第一部という文書区分。固定原文u0006の見出しから第二部u0151の直前までを含む。主題内容と番号・階層は別の関係で指定する。'),
 'eisdy':([], 'この論説の第一節という文書区分。固定原文u0007の見出しから第二節u0023の直前までを含み、第一部の直接の下位区分である。主題内容は別に指定する。'),
 'eisdz':([], '固定原文einstein-1905:u0006の部見出し全体の箇所。第一部の区分個体とは区別し、運動学という主題を個体名そのものへ隠さない。'),
 'eisd2':([], '固定原文einstein-1905:u0007の節見出し全体の箇所。第一節の区分個体とは区別し、同時性の定義という主題を個体名そのものへ隠さない。'),
}
MEANINGS={
 'eihm':'同じ系・時間単位・判断文脈の有効で一意に付与された二出来事の時刻が一致するという同時性の関係。両時刻の付与をseh、物理的時計の規約をeisb7、値の一致をscaへ接続する。未付与を非同時と認定せず、出来事又は場所が同一であることも要求しない。',
 'eihn':'eigyの剛体についての位置・時刻・配置とその変化を扱う、既存eisdhの運動学という研究主題。力の原因の理論や全物体の現実の運動命題とは区別する。',
 'eiho':'eihmの同じ系での物理的時刻の一致を対象とする研究主題。具体的な出来事が同時であるという主張ではない。',
 'eihp':'同じ研究がeihoの同時性を対象とし、その意味・適用基準を明示する定義の仕事であるという複合主題。',
 'eihq':'同じ見出し・区分・親区分・論説・階層深さ・表示番号と主題の案内を結ぶ。箇所と区分及び親子区分を同一視しない。',
 'eihr':'第一部の見出しを、論説に直接属する深さ1・表示番号1の区分と、運動学eihnの主題に結ぶ。導入第三段落の後の別箇所として順序を保持する。',
 'eihs':'第一節の見出しを、同じ第一部に属する深さ2・表示番号1の区分と、同時性の定義eihpの主題に結ぶ。第一部の見出しの後の別箇所として順序を保持する。',
}
LIMITS=[
 '見出しは後続区分の主題と構造の案内であり、物理的な命題を著者が断言したという発話へ変換しない。見出しを記述したことから本文の定義・導出の完成を認定しない。',
 '部番号Iと節番号1はともに整数1として保持し、元のローマ数字と§の表記は固定原文へ残す。部と節は階層深さと親区分を区別する。装飾書体や中央配置は意味条件に追加しない。',
 '運動学は先行段落の剛体の運動学と同じ物理的主題として読む。同時性は同じ基準系・校正尺度の時刻の一致とし、遠隔場所にも対応する同期・局所読みの規約を再利用する。全系での同時性の不変は補わない。',
 '主題として引用する関係を有限標本で実行せず、全実数の一意性や光同期の全範囲を有限例から証明しない。未付与の時刻の扱いと同時性の真偽を区別する。',
 '第一部と第一節の全範囲を案内する二見出しを記述する。後続u0008以降の本文とその全単位意味判断は別に進める。',
]

def definitions():
    text=''.join('r '+n+'['+' '.join(t for _,t in fs)+'] '+('a' if not fs else 'c')+'.\n' for n,(fs,_) in PRIMITIVES.items())
    stamp=lambda event:k('zbe',v(event),v('frame'),v('unit'),v('context'))
    assigned=lambda event:k('seh',v(event),v('frame'),v('unit'),v('context'),'p qo','p ba','p sca')
    text+=define('eihm',SAME,both(k('va',v('frame')),k('zbd',v('first')),k('zbd',v('second')),k('eisb7',v('frame'),k('zbh',v('frame'),v('context')),v('unit'),v('context')),assigned('first'),assigned('second'),k('sca',stamp('first'),stamp('second'))))
    fs=[('inquiry','a'),('context','d')]
    text+=define('eihn',fs,k('eisdh',v('inquiry'),'r[p eigy]',v('context')))
    text+=define('eiho',fs,k('eisdt',v('inquiry'),'r[p eihm]',v('context')))
    text+=define('eihp',fs,both(k('eiho',v('inquiry'),v('context')),k('eisdu',v('inquiry'),v('context'))))
    text+=define('eihq',HEADING,both(k('eisdv',*[v(n) for n,_ in HEADING if n!='topic']),k('eisdw',v('node'),v('division'),v('topic'),v('context')),op('u',op('e',v('node'),v('division'))),op('u',op('e',v('division'),v('parent')))))
    text+=define('eihr',[],both(k('eihq',k('eisdz'),k('eisdx'),k('eirf'),k('eirf'),'n p b b','n p b b','r[p eihn]',k('ri')),k('ue',k('eisds'),k('eisdz'),k('ri')),op('u',op('e',k('eisds'),k('eisdz')))))
    text+=define('eihs',[],both(k('eihq',k('eisd2'),k('eisdy'),k('eisdx'),k('eirf'),'n p c b','n p b b','r[p eihp]',k('ri')),k('ue',k('eisdz'),k('eisd2'),k('ri')),op('u',op('e',k('eisdz'),k('eisd2')))))
    return text

def build():
    old=parse(read(PARENT));assert len(old['statements'])==INDICES[0];doc=deepcopy(old);doc['statements']=[]
    assert not(set(MEANINGS)|set(PRIMITIVES))&{d['name'] for d in doc['declarations']}
    doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']+[dict(kind='assert',body=dict(kind='call',symbol=n,arguments=[])) for n in ('eihr','eihs')]
    added=doc['declarations'][len(old['declarations']):]
    primitives={d['name']:dict(parameters=d['parameters'],result=d['result'],arguments=[n for n,_ in PRIMITIVES[d['name']][0]],meaning_ja=PRIMITIVES[d['name']][1]) for d in added if d['kind']=='primitive'}
    basis=dict(status='numbered_kinematics_and_simultaneity_definition_headings',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives=primitives,definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=[],statement_indices=list(INDICES)).document
    ann=json.loads(read('data/kinematic-difficulties-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
