"""Connect the numbered A/B symmetry and A/B/C fork conditions."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_consistent_synchrony import ROOT,read
from scripts.compose_material_relative_frame import define
from scripts.compose_two_postulates import quote
from scripts.compose_relativity_conjecture import content
from scripts.compose_limits import v,call as k,op,both

PARENT='examples/v014/einstein-consistent-synchrony.noema';PARENT_BASIS='data/consistent-synchrony-basis-v1.json'
FULL='examples/v014/einstein-synchrony-laws.noema';CORE='examples/v014/synchrony-laws-core.noema'
BASIS='data/synchrony-laws-basis-v1.json';ANNOTATIONS='data/synchrony-laws-identifiers-v1.json';INDEX=241
PAIR=[(n,'a') for n in ('first','firstplace','second','secondplace','frame','unit')]+[('context','d')]
PRIMITIVES={
 'eiskg':([], '第二の同期法則でCにあるとして考える時計の同じ指示対象。A時計eisib・B時計eisikと役割を区別し、Cの場所eiskhへ結ぶ。一般法則を述べる代表的な配置の参照であり、現実に新しい時計を設置したという主張ではない。'),
 'eiskh':([], '第二の同期法則でCと表記される同じ空間点。A/Bと同じ基準系の場所として時計eiskgへ結ぶ。記号の綴りだけから同期や時刻の同一性を導かない。'),
 'eiski':([('node','a'),('author','a'),('general','i[e]'),('form','i[e]'),('document','a'),('context','d')],'著者がnodeで一般関係generalを、同じ役割を維持したA/B又はA/B/Cの条件形formによって提示する。文字は対応する時計・場所を固定する代表名であり、一般性をその特定配置だけへ縮めない。引用した一般関係と条件形を同じ内容の具体的な提示として結び、その物理的真理を実行・証明しない。'),
 'eiskj':([('node','a'),('intro','a'),('ordinal','b'),('document','a'),('context','d')],'同じdocumentのintroのコロンから続く列挙でnodeがordinal番目の項目として提示される。本文の番号1・2と項目順を保つ。番号を物理量や時計の個数へ替えず、別の列挙へ混ぜない。'),
}
MEANINGS={
 'eim7':'同じ系で指定された各地点にある二時計について、同じ単位・文脈の既存qoの同期関係を述べる。同期の向きと場所対応を別に保持する。',
 'eina':'Bの時計がAの時計と同期するなら、Aの時計がBの時計と同期するという第一の条件形。同じ二時計と場所の役割を逆にする。',
 'einb':'同じA時計がB時計ともC時計とも同期するという両前件から、BとCが互いに同期するという第二の条件形。結論は両方向を明示する。既存qqは全三時計に量化するため、B/Cの代入順を交換した場合も含む。',
 'einc':'第一の条件形einaを主張するメッセージ。前件なしに全時計の同期を主張しない。',
 'eind':'第二の条件形einbを主張するメッセージ。二前件の片方だけを十分条件としない。',
 'eine':'第一法則の著者帰属、既存qpの一般性への接続、前単位の予告と同じ箇所・番号1・本文順序を保持する。',
 'einf':'第二法則の著者帰属、既存qqの一般性への接続、同じ箇所・番号2・前項からの順序を保持する。',
}
LIMITS=[
 'u0016の順序はBがAと同期するという前件からAがBと同期する結論へ向く。二つのB、二つのAをそれぞれ同じ地点・時計へ結ぶ。単に二時計の型番や一時点の読みが一致するという関係にはしない。',
 'u0017は同じA時計がBともCとも同期する二つの前件の連言を必要とする。BとCの相互同期という結論では両方向を明示する。一般の三時計条件qqは全三時計へ量化され、B/Cの代入順を交換して逆方向も得るため、この明示は一般法則を強めない。',
 'A/Bは前の同じ場所・時計、Cは同じ系で考える追加の場所・時計の代表参照とする。一般法則の範囲は前単位で仮定したqp/qqに保ち、この印字された配置だけに縮めない。条件形自体には原文にない個体不等式や実際の時計設置済みを足さない。',
 'qoは既存の有効な静止時計と、異なる二時計の完全な非空の全光往復試行による同期条件である。一回の偶然の等値や絶対的な時間の実在をこの関係へ替えない。',
 '番号1・2とコロンからの列挙、著者への帰属、一般関係の条件形での提示、二項目の順序を保持する。仮定の文脈での二法則を物理的な実証済みへ昇格させない。',
 '有限関係モデルと数値例は含意・連言・役割・既存同期条件への接続の検査であり、全物理的配置や意味同値の自動証明ではない。未知の関係・読取り・範囲は偽や零で埋めない。',
 'u0016の74本文文字と四つの場所記号、u0017の114本文文字と五つの場所記号を対象とする。後続u0018の思考上の物理的経験、同時性と時刻の定義へのまとめは未完。',
]


def definitions():
    text=''.join('r '+n+'['+' '.join(t for _,t in fs)+'] '+('a' if not fs else 'c')+'.\n' for n,(fs,_) in PRIMITIVES.items())
    text+=define('eim7',PAIR,both(k('cb',v('first'),v('firstplace'),v('frame')),k('cb',v('second'),v('secondplace'),v('frame')),k('qo',v('first'),v('second'),v('frame'),v('unit'),v('context'))))
    refs={'A':('eisib','ziq'),'B':('eisik','zir'),'C':('eiskg','eiskh')}
    relation=lambda a,b:k('eim7',*[k(n) for n in refs[a]+refs[b]+('ra','rb')],v('point'))
    text+=content('eina',op('y',relation('B','A'),relation('A','B')))
    text+=content('einb',op('y',both(relation('A','B'),relation('A','C')),both(relation('B','C'),relation('C','B'))))
    text+='d einc[] f[j s[k eina[]]].\nd eind[] f[j s[k einb[]]].\n'
    for root,node,prior,message,general,form,ordinal in (('eine','eiskd','eiskc','einc','qp','eina','b'),('einf','eiske','eiskd','eind','qq','einb','c')):
        text+=define(root,[],both(k('eir3',k(node),k('rd'),k('eirf'),quote(message),k('ri')),k('eiski',k(node),k('rd'),quote(general),quote(form),k('eirf'),k('ri')),k('eiskj',k(node),k('eiskc'),'n p '+ordinal+' b',k('eirf'),k('ri')),k('ue',k(prior),k(node),k('ri')),op('u',op('e',k(prior),k(node)))))
    return text


def build():
    old=parse(read(PARENT));assert len(old['statements'])==INDEX;doc=deepcopy(old);doc['statements']=[]
    assert not(set(MEANINGS)|set(PRIMITIVES))&{d['name'] for d in doc['declarations']}
    doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']+[dict(kind='assert',body=dict(kind='call',symbol=n,arguments=[])) for n in ('eine','einf')]
    added=doc['declarations'][len(old['declarations']):]
    primitives={d['name']:dict(parameters=d['parameters'],result=d['result'],arguments=[n for n,_ in PRIMITIVES[d['name']][0]],meaning_ja=PRIMITIVES[d['name']][1]) for d in added if d['kind']=='primitive'}
    basis=dict(status='numbered_symmetry_and_three_clock_synchrony_conditions',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives=primitives,definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=[],statement_indices=[INDEX,INDEX+1]).document
    ann=json.loads(read('data/consistent-synchrony-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
