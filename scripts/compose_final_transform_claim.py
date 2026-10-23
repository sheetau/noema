"""Present phi=1 and the final current four-coordinate transformation."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_transverse_symmetry_claim import ROOT,read
from scripts.compose_coordinate_correspondence import SIDE,SYSTEM
from scripts.compose_material_relative_frame import define
from scripts.compose_two_postulates import quote
from scripts.compose_relativity_conjecture import content
from scripts.compose_limits import v,call as k,app,op,both

PARENT='examples/v014/einstein-transverse-symmetry-claim.noema';PARENT_BASIS='data/transverse-symmetry-claim-basis-v1.json'
FULL='examples/v014/einstein-final-transform-claim.noema';CORE='examples/v014/final-transform-claim-core.noema'
BASIS='data/final-transform-claim-basis-v1.json';ANNOTATIONS='data/final-transform-claim-identifiers-v1.json';INDICES=(323,324,325)
PRIMITIVES={'eisn4':([], '最終四座標変換の直後、u0107のwobeiからu0108のβの定義を補う発話位置。先行する同じβの導入位置zfkとは区別する。')}
MEANINGS={
 'ejea':'この関係ssk（同じφの正負値の一致）と先に得た関係sro（同じ二値の積1）を合わせた、原文が指す二関係の内容。正の枝をここへ追加しない。',
 'ejeb':'同じ正規化後の関数spcの対象速度zb7での有効な値が1である内容。原文通りφ(v)=1だけを表示し、別の関数や全速度の有限検証に替えない。',
 'ejec':'同じspcの対象速度での値が有効な正の実数であるという符号の内容。',
 'ejed':'二関係ejeaと正の枝ejecを合わせた十分条件。原文が明示した二関係だけの前提とは分ける。',
 'ejee':'直前の同じ棒の正の測定長とl/φの一致ejdlから正の枝ejecを採る解釈をzflで注記する。著者の発話メッセージの外側へ置く。',
 'ejef':'著者がこの関係と先の関係ejeaからφ(v)=1のejebが従わなければならないと述べる提示。処理系の含意証明を主張しない。',
 'ejeg':'係数1の最終四式をτ,ξ,η,ζの順序の有限列として構成する。各式は同じK/k二記録の左辺と右辺を返し、横二式は同じy,zそのもの。',
 'ejeh':'同じ正のβの定義を保ち、現在の全K/k記録対応に係数1の四式ssnが過不足なく一致し、同じ四式列ejegが現在の方程式課題eiy4を満たす内容。',
 'ejei':'既に得た現在のφ付き四式ei7c、今回のφ(v)=1であるejeb、同じβの定義spqを合わせる最終表示への書換え前提。',
 'ejej':'著者がφ=1を得たことにより、同じ既出の四式ei7cを同じ対象範囲の最終四式ejehへ書き換える提示。so daßとübergehen inを同じ前提・変換元・先に接続する。',
 'ejek':'直前の最終四式で用いたβを、同じV,vのspqで指定する著者の補足。wobeiの参照先は直前の四式で、別のβを導入しない。',
 'ejel':'φ(v)=1の必要性の推論ejefを述べるメッセージ。',
 'ejem':'u0105前半の推論を同じ著者・論説へ帰属し、直前の正負値の一致に続ける。正の枝の解釈ejeeは発話外へ併記する。',
 'ejen':'最終四式への書換えejejを述べるメッセージ。',
 'ejeo':'u0105後半からu0106の四式を同じ著者・論説へ帰属し、同じφ=1の推論に続ける。',
 'ejep':'最終四式のβの指定ejekを述べるメッセージ。',
 'ejeq':'u0107のwobeiとu0108のβ表示を同じ著者・論説へ帰属し、同じ最終四式に続ける。',
}
LIMITS=[
 'u0105–u0108を原刊902頁の段落末・四式・wobei・βまで照合する。dieserは直前のssk、vorhin gefundenen Relationは前のsroを指す。sein mußは既存zcの前提からの必要な帰結の提示として読む。',
 '正負の二値の一致と積1だけなら共通値−1も残る。原文が列挙する前提ejeaを改変せず、その推論を著者へ帰属する。直前の正の測定長と符号付き商l/φの一致ejdlが正の枝を選ぶ読みは、ejeeの解釈注記として発話の外に置く。',
 '正の枝を合わせたejedならφ(v)=1への十分条件となるが、有限有理例を実切断の一般定理・原論文の物理的導出・意味同値の自動証明にしない。原文の表示はφ(v)=1であり、φ(−v)=1の式を別に追加しない。',
 'φは先の四式と同じspcで、再正規化しない。既出の式ei7cと現在の全記録対応ei7lを再利用し、同じ対象出来事の全K/k四成分を扱う。全実数四組の測定記録の実在までは要求しない。同じ値の別記録は許す。',
 '最終四式はτ=β(t−vx/V²)、ξ=β(x−vt)、η=y、ζ=z。横二式にβを掛けず、時間式のV²やt/τの役割を変えない。四式列と双方向の全対応条件の両方を保持する。',
 'wobeiは同じ四式で使うβの指定。既存spqによる正の1/√(1−(v/V)²)と同値表示を用い、同じ光速Vと対象速度vを保つ。現行物理設定は0<v<Vで、負の根や別慣習のv/Vをβとしない。',
 '原刊902頁末はβ表示の後にコンマ、固定したMathMLは句点を持つ。この句読点差を記録し、β式の意味を変えない。続く§4の見出しと剛体・時計の考察はu0109以降へ残す。',
]
GROUPS=(('ejef','ejel','ejem','zho','zhn'),('ejej','ejen','ejeo','zhp','zho'),('ejek','ejep','ejeq','eisn4','zhp'))

def definitions():
    text='r eisn4[] a.\n';point=v('point');ev=lambda n:op('t',k(n),point)
    V=k('tc');speed=k('zb7');phi=app(k('spc'),speed);one=k('bb','n p b b');zero=k('bb','n p a b')
    text+=content('ejea',both(ev('ssk'),ev('sro')))
    text+=content('ejeb',both(k('ba',phi),k('sca',phi,one)))
    text+=content('ejec',both(k('ba',phi),k('bg',zero,phi)))
    text+=content('ejed',both(ev('ejea'),ev('ejec')))
    text+=define('ejee',[],k('zfl',k('zhq'),k('rd'),quote('ejdl'),quote('ejec'),k('eisms'),k('ri')))
    text+=content('ejef',k('zc',k('zho'),k('rd'),quote('ejea'),quote('ejeb'),k('eisms'),point))
    coord=lambda tup,role:k('zc6',tup,k(role))
    first=v('first');second=v('second');x,y,z,t=[coord(first,r) for r in ('yn','yo','yp','zc7')]
    rhs=(k('spd',V,speed,one,x,t),k('spe',V,speed,one,x,t),y,z);equations=[]
    for role,right in zip(('zc7','yn','yo','yp'),rhs):
        choice=op('x',both(v('left'),app(coord(second,role),v('number'))),both(op('u',v('left')),app(right,v('number'))))
        equations.append('i[first a second a left c][i[number b]['+choice+']]')
    text+=define('ejeg',[],'l['+SIDE+']['+' '.join(equations)+']',SYSTEM)
    text+=content('ejeh',both(ev('spq'),k('ei7l','p ssn'),k('eiy4',k('ejeg'))))
    text+=content('ejei',both(ev('ei7c'),ev('ejeb'),ev('spq')))
    text+=content('ejej',k('zd3',k('zhp'),k('rd'),quote('ejei'),quote('ei7c'),quote('ejeh'),k('eisms'),point))
    text+=content('ejek',k('uh',k('eisn4'),k('rd'),quote('spq'),k('eisms'),point))
    for value,message,claim,node,previous in GROUPS:
        text+='d '+message+'[] f[j s[k '+value+'[]]].\n'
        rows=[k('eir3',k(node),k('rd'),k('eirf'),quote(message),k('ri')),k('ue',k(previous),k(node),k('ri')),op('u',op('e',k(previous),k(node)))]
        if claim=='ejem':rows.insert(0,k('ejee'))
        text+=define(claim,[],both(*rows))
    return text

def build():
    old=parse(read(PARENT));assert len(old['statements'])==INDICES[0];doc=deepcopy(old);doc['statements']=[]
    assert not (set(MEANINGS)|set(PRIMITIVES))&{d['name'] for d in old['declarations']}
    doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']+[dict(kind='assert',body=dict(kind='call',symbol=g[2],arguments=[])) for g in GROUPS]
    added=doc['declarations'][len(old['declarations']):]
    primitives={d['name']:dict(parameters=d['parameters'],result=d['result'],arguments=[],meaning_ja=PRIMITIVES[d['name']][1]) for d in added if d['kind']=='primitive'}
    basis=dict(status='phi_one_and_final_current_transformation_presented',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives=primitives,definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=list(INDICES)).document
    ann=json.loads(read('data/transverse-symmetry-claim-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
