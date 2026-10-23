"""Present the current four-coordinate equations and coefficient reparameterization."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_spatial_affine_calibration import ROOT,read
from scripts.compose_coordinate_correspondence import SIDE,SYSTEM
from scripts.compose_material_relative_frame import define
from scripts.compose_two_postulates import quote
from scripts.compose_relativity_conjecture import content
from scripts.compose_limits import v,call as k,app,op,both,quant as q

PARENT='examples/v014/einstein-spatial-affine-calibration.noema';PARENT_BASIS='data/spatial-affine-calibration-basis-v1.json'
FULL='examples/v014/einstein-four-coordinate-claim.noema';CORE='examples/v014/four-coordinate-claim-core.noema'
BASIS='data/four-coordinate-claim-basis-v1.json';ANNOTATIONS='data/four-coordinate-claim-identifiers-v1.json';INDEX=300
MEANINGS={
 'ei67':'先行係数aによるτ,ξ,η,ζの四式を、左右が実数値を返す同じ非空有限列へ組む。x′は同じK四入力のx−v*tとして読み、同じa,V,vを全式に渡す。',
 'ei7a':'正規化後のφ=spcとβを使う本文の四式を、同じ順序・同じ二記録の左右実数値を返す列へ組む。φとaを同じ値へ固定せず、横二式へ余分なβを掛けない。',
 'ei7b':'先行係数aの四式sphが現在の全K/k座標対の同じ出来事対応に過不足なく一致し、同じ四式列ei67が前段の方程式課題eiy4を満たす内容。速度と係数の有効性も保持する。',
 'ei7c':'新しいφとβの四式spgが現在の全K/k座標対に過不足なく一致し、同じ四式列ei7aが方程式課題eiy4を満たす内容。単独の光線上の式に限定しない。',
 'ei7d':'光線から全座標への拡張を、現在の同じ行列・原点・三光線を結ぶ追加十分条件ei66から先行四式ei7bへ至る解釈注記zflとして明示する。著者の発話メッセージの外側に置く。',
 'ei7e':'同じ現在の先行四式ei7bと、同じV,vのβの定義spqを保持する書換え前提。未知係数の値を1へ固定しない。',
 'ei7f':'著者がx′の同じx−vtの値を戻し、同じaからφ=aβへ再表示した四式ei7cを得るというzd3の書換え提示。先行内容・前提・結果を同じ第三節へ結ぶ。',
 'ei7g':'四座標の書換えei7fを断定の伝達形式にする。追加較正の解釈注記をこの発話の中に混ぜない。',
 'ei7h':'追加解釈ei7dと、著者による四式の書換えの帰属を区別して併記する。後者は同じ論説へのeir3で帰属し、先のζの結果からの順序を保つ。',
 'ei7i':'直前の四式で使うβを、本文通り1/√(1−(v/V)²)で指定する著者の補足。既存spqは同じ正のV/√(V²−v²)表示との一致も保持する。',
 'ei7j':'βの指定ei7iを断定の伝達形式にする。',
 'ei7k':'βの指定を同じ著者・論説へ帰属し、直前の四座標式に続ける。',
 'ei7l':'指定した二記録の式条件と、現在の全eiyz/eiy2範囲の同じ出来事対応eiyyが双方向に一致する。非空で値として関数的な対応sgwを保ち、別記録の同値をshhで扱う。',
}
LIMITS=[
 'u0081–u0084を原刊900頁の四式とβまで照合する。Setzen wir ... einは同じx′=x−vtの代入を示す著者の計算提示であり、実際の計算履歴や読者の参加を追加しない。',
 '原刊では以前aをφ(v)と呼んだ後、四式で再びφ(v)と書く。同じ数値のままでは式が一致しないため、ここは既存spcによる新しいφ(v)=a(v)*β(v)への再表示として読む。同じ文字の参照先の変化を明示し、aやφを1に固定しない。',
 '四式は現在の同じ出来事のK/k四座標を全範囲で結ぶ。全実数四組が実際の測定記録として存在するという追加主張ではない。余分な解と対応の欠落を双方向の条件で拒否し、同じ値を持つ別記録を一つの識別子へ潰さない。',
 '三光線から一般式への拡張は、先行の同じアフィン係数と零原点を用いる。ei66で全入力の空間行、現在の全対応、実際の原点と三光線の独立な正時刻による五点条件を結ぶ。原文に逐語的にはない十分条件であるため、既存zflの解釈注記として著者発話の外に置く。',
 '先行四式のx′は同じKのx−vtを指し、新しい四式ではτ=φβ(t−vx/V²)、ξ=φβ(x−vt)、η=φy、ζ=φzと記述する。時間式と縦式だけにβがあり、y/zの結果やt/τの役割を交換しない。',
 'wobeiはこの四式で用いたβの記号規約を補うものとして読む。βは正の1/√(1−(v/V)²)であり、v/Vという別の慣習を使わない。定義域は0≤v<V、現在の物理設定では既出v>0を保つ。',
 '有理多項式による再表示・較正補題と有限切断・引用の対照検査を、一般実数体・物理的導出や意味同値の自動証明とはしない。未知性と初期位置の仮定を外した加法定数は次のu0085へ残す。',
]
GROUPS=(('ei7f','ei7g','ei7h','zfj','zff'),('ei7i','ei7j','ei7k','zfk','zfj'))

def definitions():
    first=v('first');second=v('second');V=k('tc');speed=k('zb7');old=app(k('zeq'),speed);new=app(k('spc'),speed)
    coord=lambda tup,role:k('zc6',tup,k(role))
    x,y,z,t=[coord(first,a) for a in ('yn','yo','yp','zc7')];xp=k('sin',speed,x,t)
    earlier=[k('smh',V,speed,old,xp,t),k('snb',V,speed,old,xp),k('sob',V,speed,old,y),k('sob',V,speed,old,z)]
    normalized=[k('spd',V,speed,new,x,t),k('spe',V,speed,new,x,t),k('spf',new,y),k('spf',new,z)]
    text=''
    for name,expressions in (('ei67',earlier),('ei7a',normalized)):
        equations=[]
        for role,rhs in zip(('zc7','yn','yo','yp'),expressions):
            choice=op('x',both(v('left'),app(coord(second,role),v('number'))),both(op('u',v('left')),app(rhs,v('number'))))
            equations.append('i[first a second a left c][i[number b]['+choice+']]')
        text+=define(name,[],'l['+SIDE+']['+' '.join(equations)+']',SYSTEM)
    body=q('f','first','a',q('f','second','a',op('y',both(k('eiyz',first),k('eiy2',second)),op('z',app(v('equations'),first,second),k('eiyy',first,second)))))
    text+=define('ei7l',[('equations','h[a a] c')],both(k('sgw','p eiyz','p eiy2','p eiyy','p shh'),body))
    for name,predicate,system in (('ei7b','sph','ei67'),('ei7c','spg','ei7a')):
        text+=content(name,both(k('spa',V,speed,k('soy',V,speed)),k('ba',old),k('ba',new),k('ei7l','p '+predicate),k('eiy4',k(system))))
    text+=define('ei7d',[],k('zfl',k('zfi'),k('rd'),quote('ei66'),quote('ei7b'),k('eisms'),k('ri')))
    text+=content('ei7e',both(op('t',k('ei7b'),v('point')),op('t',k('spq'),v('point'))))
    text+=content('ei7f',k('zd3',k('zfj'),k('rd'),quote('ei7e'),quote('ei7b'),quote('ei7c'),k('eisms'),v('point')))
    text+=content('ei7i',k('uh',k('zfk'),k('rd'),quote('spq'),k('eisms'),v('point')))
    for body,message,author,node,previous in GROUPS:
        text+='d '+message+'[] f[j s[k '+body+'[]]].\n'
        rows=[k('eir3',k(node),k('rd'),k('eirf'),quote(message),k('ri')),k('ue',k(previous),k(node),k('ri')),op('u',op('e',k(previous),k(node)))]
        if author=='ei7h':rows.insert(0,k('ei7d'))
        text+=define(author,[],both(*rows))
    return text

def build():
    old=parse(read(PARENT));assert len(old['statements'])==INDEX;doc=deepcopy(old);doc['statements']=[]
    assert not set(MEANINGS)&{d['name'] for d in old['declarations']}
    doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']+[dict(kind='assert',body=dict(kind='call',symbol=g[2],arguments=[])) for g in GROUPS]
    added=doc['declarations'][len(old['declarations']):]
    basis=dict(status='current_four_coordinate_equations_and_beta_presented',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives={},definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=list(range(INDEX,INDEX+len(GROUPS)))).document
    ann=json.loads(read('data/spatial-affine-calibration-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
