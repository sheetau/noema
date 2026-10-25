"""Connect the undertaking to enumerate the three experimentally accessible properties."""
from scripts.compose_experimental_relation_tests import *

PARENT=FULL;PARENT_BASIS=BASIS;PARENT_ANNOTATIONS=ANNOTATIONS
FULL='examples/v014/einstein-experimental-list-opening.noema';CORE='examples/v014/experimental-list-opening-core.noema'
BASIS='data/experimental-list-opening-basis-v1.json';ANNOTATIONS='data/experimental-list-opening-identifiers-v1.json'
ENUMERATION=[('node','a'),('author','a'),('items','j[a]'),('contents','j[i[e]]'),('scope','a'),('document','a'),('context','d')]
PRIMITIVES={'eis6v':(ENUMERATION,'authorがnodeという現在の論述段階で、同じdocument・scopeのitemsの各箇所に、対応するcontentsの内容を順に一項ずつ挙げて示す意向を表明する。二列の同じ位置を対応させ、これから列挙に移る取組として読む。項数・対象分野・個別内容は引数で指定し、既に列挙したこと、内容の真理・証明・実験の実施は含意しない。単に将来の話題に言及すること、量を求める質問、既述の二法則だけの予告とは区別する。')}
MEANINGS={
 'eum':'非空の項目列と同じ長さの内容列について、eis6vの現在の段階からの列挙の取組を述べる一般的な合成。固定の三項や特定の論文を原始関係に埋め込まない。',
 'eun':'第一項の同じ電気・磁気偏向の同じ強さの条件erb、比erc、任意の許容速度の決定eq7という運動の性質を合わせる。実験の方法は別のerwへ保持する。',
 'euo':'第三項の同じ局所事例の全加速度等号列esz、半径表示es2、同じ前提での同値書換えes3をまとめる。第二項の静電過程へ交換しない。',
 'eup':'第一項eun、第二項esd、第三項euoの全てを、既存の同じ電子・K・理論・単位と各適用条件へ結んだ三性質の内容。裸の数値関係だけで代用しない。',
 'euq':'同じ(A)のelkに、第一項の校正された同じ背景eq6、第二項の初速零・静電過程・緩い加速・無放射・閉収支epd、第三項の局所的設定eswを合わせる導出の前提。実験可能性や観測結果の一致を前提にしない。',
 'eur':'u0265の現在からの三項の列挙の取組、同じ(A)への照応、適用条件と(A)から三性質を得るという著者の理由、全三項への実験的アクセスの主張を合わせる。',
 'eus':'u0265全文のメッセージ。','eut':'u0265を同じ著者・論説へ帰属し、u0264の物質点への拡張の後、既存の第一項の前へ置く。',
}
LIMITS=[
 '原刊920頁u0265。Wirは同じ著者の論述上の一人称複数、wollenは列挙へ移る意向・取組、nunはこの論述段階からの移行として読む。共同著者、読者全員の実行、特定の時刻、既に列挙を完了したことは付加しない。',
 '後続の1・2・3を同じ電子の運動に関する三性質として参照する。第一項は偏向条件・比・速度決定、第二項は全電位差関係、第三項は局所曲率の二表示と条件付き書換えを含め、単なる名前や数値の一部に縮めない。',
 'aus dem Gleichungssystem (A) resultierendenは同じ(A)を根拠とする著者の帰結提示。後続各項の物理的適用条件を共有して読む。校正、無放射・閉収支や磁気だけによる偏向を(A)から自動導出せず、実験可能性も代数式だけからの定理にはしない。',
 '実験へのアクセスは第一項erwと第二・第三項euj/eukの全部。各項の同じ量・対象・単位、独立した校正と取得、同じ可能過程の記録共有・比較を保持する。実験での支持・既に実施済み・全装置の実現を補わない。',
 '原文がここで個別装置を指定したとは扱わない。後続の三項から参照内容を展開する読みであり、この一文に三式が印刷されているとはしない。特定の歴史的実験の成功や物理法則の真理は完成条件ではない。',
 '旧444主張・意味・証拠を保存し、u0265の判断を一件だけ追加する。u0239の見出しとu0275の完全表現という総括はまだ判断しない。',
]
def definitions():
    text=''.join('r '+n+'['+' '.join(t for _,t in fs)+'] c.\n' for n,(fs,_) in PRIMITIVES.items())
    text+=define('eum',ENUMERATION,both(k('aa',rat(0),'d[v items]'),op('e','d[v items]','d[v contents]'),k('eis6v',*args(ENUMERATION))))
    ev=lambda n:op('t',k(n),v('point'))
    for name,parts in [('eun',('erb','erc','eq7')),('euo',('esz','es2','es3')),('eup',('eun','esd','euo'))]:text+=content(name,both(*(ev(n) for n in parts)))
    text+=content('euq',both(ev('elk'),q('g','chargescale','b',k('eq6',v('chargescale'),v('point'))),ev('epd'),ev('esw')))
    p=v('point');node=k('eis3w');author=k('rd');paper=k('eirf');scope=k('eisxg')
    items=['eis3x','eis4q','eis4u'];targets=['eun','esd','euo']
    text+=content('eur',both(k('eum',node,author,'l[a]['+' '.join(k(n) for n in items)+']','l[i[e]]['+' '.join(quote(n) for n in targets)+']',scope,paper,p),*(k('eislk',k(n),node,num(i+1),paper,p) for i,n in enumerate(items)),k('eiswm',node,author,k('eisym'),quote('elk'),paper,p),k('eis3v',quote('elk'),quote('euq'),rat(1),p),k('zc',node,author,quote('euq'),quote('eup'),scope,p),k('uh',node,author,quote('eul'),scope,p)))
    text+='d eus[] f[j s[k eur[]]].\n'
    text+=define('eut',[],both(k('eir3',node,author,paper,quote('eus'),k('ri')),k('ue',k('eis3p'),node,k('ri')),k('ue',node,k('eis3x'),k('ri'))))
    return text
@lru_cache(None)
def build():
    old=parse(read(PARENT));assert len(old['statements'])==444
    assert not(set(MEANINGS)|set(PRIMITIVES))&{d['name'] for d in old['declarations']}
    doc=deepcopy(old);doc['statements']=[];doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']+[dict(kind='assert',body=dict(kind='call',symbol='eut',arguments=[]))]
    added=doc['declarations'][len(old['declarations']):]
    prim={d['name']:dict(parameters=d['parameters'],result=d['result'],arguments=[n for n,t in PRIMITIVES[d['name']][0]],meaning_ja=PRIMITIVES[d['name']][1]) for d in added if d['kind']=='primitive'}
    basis=dict(status='three_experimental_properties_list_opening_connected',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives=prim,definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=[444]).document
    ann=json.loads(read(PARENT_ANNOTATIONS));ann.update(document=FULL,document_sha256=digest(body.encode()))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
