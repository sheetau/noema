"""Connect the first-part summary to a collective electrodynamic application."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_parallel_group_claim import ROOT,read
from scripts.compose_material_relative_frame import define
from scripts.compose_relativity_conjecture import content
from scripts.compose_two_postulates import quote
from scripts.compose_limits import v,call as k,op,both,quant as q

PARENT='examples/v014/einstein-parallel-group-claim.noema'
PARENT_BASIS='data/parallel-group-claim-basis-v1.json'
FULL='examples/v014/einstein-kinematic-transition-claim.noema'
CORE='examples/v014/kinematic-transition-claim-core.noema'
BASIS='data/kinematic-transition-claim-basis-v1.json'
ANNOTATIONS='data/kinematic-transition-claim-identifiers-v1.json'
INDICES=(150,151)
MEANINGS={
 'ejrz':'指定体系が、物体の位置・時刻・配置の変化を力や原因の法則に先立って扱う運動学eihnの同じ研究対象を記述する。単なる分野名ではなくeiscmと既存の物体・運動の構成へ結ぶ。',
 'ejr2':'同じ命題項目の内容を閉じたdescriptionへeisoxで結び、その内容の論証を同じ著者が指定段階までに同じ範囲で提示した。内容の真理や論証の健全性を認定しない。',
 'ejr3':'基準段階における同じ命題項目の閉じた内容を、指定適用段階の同じ体系が指定範囲で前提として実際に用いる。内容の名前や真偽の一致、単なる言及で代用しない。',
 'ejr4':'命題項目の内容を表す閉じたNoema記述があり、その同じ記述についてejr2が成立する。未割当の旧zm6や有限の代表式の一覧に依存しない。',
 'ejr5':'命題項目の閉じた内容についてejr3が成立する。内容の参照段階referenceと応用を示す段階sceneを分離し、後の課題で別の命題へ交換しない。',
 'ejr6':'同じ著者・課題・段階に必要な命題が非空で、その全項目が指定体系に属し、その同じ内容の論証を指定範囲で提示済みである。必要な項目を検査済みのものだけに選び直さない。',
 'ejr7':'現在の同じ課題zm7に必要な命題を第一部znbで導出提示済みとするejr6。体系zncを運動学ejrzへ結び、現在の二原理eion/eiotを同じ第一部で前提として用いる。',
 'ejsa':'基準段階で同じ課題に必要な非空の全命題内容を、適用段階の一つの電気力学の記述体系が前提として用い、同じ著者がその構成例を示す。体系は複数の説明・導出を含められ、各命題に別々の例を要求しない。',
 'ejsb':'現在の基準riに必要な同じ命題群を用いる電気力学の体系の構成例を著者が示すという目標内容。応用体系自身をその前提使用の範囲とし、適用段階pointを現在の基準へ置き換えない。',
 'ejsc':'著者が第一部の範囲でejr7を総括する。導出済みという著者の内容と、処理系による論証の認定を分ける。',
 'ejsd':'著者が現在の段階から同じ課題zm7の目標ejsbへ取り組むという移行を提示する。目標の現在の達成や後続の実行完了を含意しない。',
 'ejse':'導出済みという総括ejscを述べるメッセージ。',
 'ejsf':'応用を示す課題への移行ejsdを述べるメッセージ。',
 'ejsg':'群の提示zluに続く総括zniを同じ著者・論説に帰属し、本文順序と箇所の区別を保持する。',
 'ejsh':'総括zniに続く移行znjを同じ著者・論説に帰属する。同じ文の前後半を順序づけ、別主体や別課題へ変更しない。',
}
LIMITS=[
 'u0150全文を原刊907頁に照合する。Wir/unsは同じ著者の論述上の声、nunはこの第一部末の現在段階riと読む。新たな共著者集団や時計による日時を補わない。',
 '必要は同じ著者が続く応用課題zm7のために必要とする命題の全範囲という読みを採る。znaの主体・課題・段階を固定し、非空性と全称を要求する。全人類に不可欠な知識、論理的必然性、運動学の全定理の有限一覧ではない。',
 '命題項目はeisoxで対象・量化・条件を保つ閉じたNoema内容へ結び、同じ内容のzfrを第一部znbで要求する。原文が有限一覧を与えないため、全閉記述への量化を用いる。入力の命題内容が不明な場合に任意の引用を割り当てて成功扱いにしない。',
 '二原理に対応する運動学は、同じ体系が現在の第一原理eionと第二原理eiotを前提として用いるという、導出の基礎を指す読みとする。体系全体と二原理の論理同値、二原理だけからの完全な公理化、全帰結の真理・無矛盾の証明は追加しない。',
 '運動学はeihn/eisdhと既存の物体・位置・時刻の記述へ、電気力学はeig4/eie5と電荷輸送eibf・電気作用eibs・磁気作用eicoへ結ぶ。分野名の綴りや説明のない分類だけでは済ませない。',
 'deren Anwendungは、同じ必要命題群を前提として用いる電気力学の記述・説明体系の構成例を示すという共同利用の読みを採る。体系は複数の導出・説明を含み得る。全結果を一つの式へ同時代入する条件や、各項目に独立した一例を要求する条件は加えない。',
 '応用はeiscmで分野と量の解釈を保つ体系へ結び、ztで同じ閉じた内容の前提使用、zngで同じ著者によるその構成例の提示を要求する。単なる引用・主題名・同じ真偽値だけでは成立しない。ここで体系を一つの構成例として扱い、適用範囲もその体系自身に固定する。',
 '目標の全項目と内容は現在riを基準とし、提示・前提使用・分野体系は目標の評価段階で要求する。課題開始はznhへ目標の引用を渡し、目標を実行しない。現在未達でもよく、既存の一例があることから課題開始を否定もしない。',
 '全閉記述を有限評価器で列挙せず、束縛の検査には有限の二記述を明示的に代入する。これは全命題の導出・応用の実証ではない。原文全体の意味判断は局所検査から分離する。u0151以降は残る。',
]


def definitions():
    text=define('ejrz',[('theory','a'),('reference','d')],q('g','inquiry','a',both(k('eiscm',v('theory'),v('inquiry'),v('reference')),k('eihn',v('inquiry'),v('reference')))))
    fs=[('item','a'),('description','i[e]'),('author','a'),('scope','a'),('reference','d')]
    text+=define('ejr2',fs,both(k('eisox',v('item'),v('description'),v('reference')),q('g','proof','a',k('zfr',v('proof'),v('author'),v('description'),v('reference'),v('scope')))))
    gs=[('item','a'),('description','i[e]'),('application','a'),('scope','a'),('reference','d'),('scene','d')]
    text+=define('ejr3',gs,both(k('eisox',v('item'),v('description'),v('reference')),k('zt',v('application'),v('description'),v('scope'),v('scene'))))
    for name,body,fields in (('ejr4','ejr2',fs),('ejr5','ejr3',gs)):
        text+=define(name,[(n,t) for n,t in fields if n!='description'],q('g','description','i[e]',k(body,*[v(n) for n,_ in fields])))
    needed=k('zna',v('author'),v('task'),v('item'),v('reference'))
    nonempty=q('g','item','a',needed)
    fields=[('author','a'),('task','a'),('theory','a'),('scope','a'),('reference','d')]
    each=both(k('eiscr',v('theory'),v('item'),v('reference')),k('ejr4',v('item'),v('author'),v('scope'),v('reference')))
    text+=define('ejr6',fields,both(nonempty,q('f','item','a',op('y',needed,each))))
    point=v('point');author=k('rd');scope=k('znb');theory=k('znc');task=k('zm7')
    text+=content('ejr7',both(k('ejr6',author,task,theory,scope,point),k('ejrz',theory,point),*(k('zt',theory,quote(p),scope,point) for p in ('eion','eiot'))))
    fields=[('author','a'),('task','a'),('application','a'),('scope','a'),('reference','d'),('scene','d')]
    each=k('ejr5',v('item'),v('application'),v('scope'),v('reference'),v('scene'))
    text+=define('ejsa',fields,both(nonempty,k('eig4',v('application'),v('scene')),q('f','item','a',op('y',needed,each)),k('zng',v('author'),v('application'),v('scene'))))
    text+=content('ejsb',q('g','application','a',k('ejsa',author,task,v('application'),v('application'),k('ri'),point)))
    text+=content('ejsc',k('uh',k('zni'),author,quote('ejr7'),scope,point))
    text+=content('ejsd',k('znh',k('znj'),author,task,quote('ejsb'),point,scope,point))
    for body,message,claim,node,previous in (('ejsc','ejse','ejsg','zni','zlu'),('ejsd','ejsf','ejsh','znj','zni')):
        text+='d '+message+'[] f[j s[k '+body+'[]]].\n'
        text+=define(claim,[],both(k('eir3',k(node),author,k('eirf'),quote(message),k('ri')),k('ue',k(previous),k(node),k('ri')),op('u',op('e',k(previous),k(node)))))
    return text


def build():
    old=parse(read(PARENT));assert len(old['statements'])==356
    doc=deepcopy(old);doc['statements']=[]
    assert not set(MEANINGS)&{d['name'] for d in old['declarations']}
    doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=deepcopy(old['statements'])
    for i,n in zip(INDICES,('ejsg','ejsh')):doc['statements'][i]=dict(kind='assert',body=dict(kind='call',symbol=n,arguments=[]))
    added=doc['declarations'][len(old['declarations']):]
    basis=dict(status='kinematic_summary_and_collective_electrodynamic_application',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives={},definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},replaced_partial_statements=list(INDICES),limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=list(INDICES)).document
    ann=json.loads(read('data/parallel-group-claim-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
