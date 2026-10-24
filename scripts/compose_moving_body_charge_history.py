"""Describe whole-body charge histories without assuming fixed charge on every part."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_limits import ROOT,R,F,v,call as k,app,op,both,quant as q
from scripts.compose_material_relative_frame import define
from scripts.compose_material_body_motion import FIELDS as HISTORY,FAMILY
from scripts.compose_attached_material_charge import LABELS,PHYSICAL,args,coord
from scripts.compose_doppler_infinity import quantified
from scripts.compose_relativity_conjecture import content

def read(path):return (ROOT/path).read_text(encoding='utf-8')
PARENT='examples/v014/einstein-convective-relativity-claim.noema';PARENT_BASIS='data/convective-relativity-claim-basis-v1.json'
FULL='examples/v014/einstein-moving-body-charge-history.noema';CORE='examples/v014/moving-body-charge-history-core.noema'
BASIS='data/moving-body-charge-history-basis-v1.json';ANNOTATIONS='data/moving-body-charge-history-identifiers-v1.json'
MODEL=HISTORY+[('distribution','a'),('chargeunit','a'),('charge',F),('anchor','a')]
LOCAL=MODEL+[('event','a'),('time',R)]
CONSTANT=[('lower',R),('upper',R),('charge',F)]
SHARED=[('body','a'),('context','d'),('lengthunit','a'),('timeunit','a'),('distribution','a'),('chargeunit','a'),('members',LABELS),('anchor','a')]
SERIES=[('lower',R),('upper',R)]+[(n,FAMILY) for n in ('x','y','z')]+[('charge',F)]
SETTING=SHARED+SERIES+[('ownframe','a')]+[('own'+n,t) for n,t in SERIES]
PAIR=SETTING+[('event','a'),('time',R),('owntime',R)]
CASES=[(n,t) for n,t in SETTING if n!='context']
ZERO=k('bb','n p a b')
MEANINGS={
 'ek22':'指定した同じ物体・分布・系・出来事・座標時刻・単位・全成員について、charge(time)が有効な実数であり、全物質部分membersの電気量zorの保有量eisvyである。空間の固定箱、代表点一個の量、密度、速度又は別時刻の量ではない。',
 'ek23':'同じ物体の非空で完全な全物質点履歴eiad、座標系va、分布の全成員の一致、同じ成員anchorを保持する。全区間時刻にanchorの記録が存在し、その時刻の同じanchorの全記録でek22の全体電荷を要求する。存在する成功記録だけを選んで矛盾又は欠落を隠さず、内部の各部分の量が一定とは要求しない。',
 'ek24':'正長の実時間閉区間における有効な全量履歴について、任意の二時刻の値が実数として等しいという一定性。端点だけの一致、単位の時間変化、一方の時刻の存在だけでは代用しない。符号と零を許し、値そのものを他系と等置しない。',
 'ek25':'同じ区間内の少なくとも一時刻で有効な総電荷が非零であること。帯電物体の巨視的な正味電荷という採用読解の非零条件であり、正電荷だけ又は全物質点の非零へ狭めない。',
 'ek26':'ek23の同じ全物体電荷履歴を保ち、指定された同じ物質成員anchorが全区間でこの系の空間原点にある。物体とともに動く系を、その物体の追跡点へ原点を随伴させた座標系として読む。全物質点の静止・剛性・非回転・等速・慣性系を要求しない。',
 'ek27':'同じ物体の同じ追跡点anchorと同じ出来事を、Kと随伴系のそれぞれの区間・座標時刻・三座標・単位へsbで結ぶ。時刻値又は全体の同時切片を同じにせず、一般運動へ一つの定速Lorentz写像を適用しない。',
 'ek3a':'K側と随伴側の同じ追跡点の全対象記録について、同じ出来事を共有するek27の相手時刻が各々存在するという双方向の期間対応。成功した記録だけに対象を狭めず、片側に欠落した出来事も検出する。物体全体の二つの同時切片を同じ出来事集合にはしない。',
 'ek3b':'同じ物体・分布・全成員・追跡点と固定単位について、Kの全体電荷履歴ek23、随伴系のek26、両期間のek3a、Kに対する物体の運動eiag、随伴側の帯電ek25を結ぶ設定。任意性は全てのこの設定への量化で扱い、等速・剛体・一様密度・各部分の不変付着を条件へ足さない。',
 'ek3c':'同じ設定で、随伴系の全体電荷がその全区間で一定なら、Kの同じ全体電荷も対応する全区間で一定であるという条件文。二系の値の等値、前件が偽のときのKの一定、物体外の電荷不在は要求しない。',
 'ek3d':'同じ評価点の全20設定引数について、ek3bの同じ任意運動の帯電物体の設定ならek3cを要求する閉じた定理内容。原文からの容易な導出、重要さ、補足の役割、著者帰属は後続で接続し、この内容をまだ新しい本文主張にしない。',
}
LIMITS=[
 'u0238の定理内容に必要な依存群。新しい原始記号・本文主張・全単位の意味判断は追加しない。Es möge noch kurz bemerkt werden、developed equationsから容易に導けること、重要な定理、コロンとauchの提示、Kの引用符付き呼称、全文の通読判断が残る。',
 '物体は同じ固定された全物質点を追跡する持続的な物体として読む。eiadは正長区間の完全な実座標履歴と連続性を含むが、剛性・等速・一様密度・共通の静止慣性系を含めない。物質の生成消滅や開放系への構成員の出入りを無条件にこのモデルへ含めたとはしない。',
 '随伴系は物体に属する一つの同じ追跡点へ原点を付けた系という明示した読みを採る。加速や回転を許し、拡がりのある物体全体を一つの瞬間静止慣性系に入れない。物体内部の変形や運動は許す。原文がこの追跡点又は原点規約を別途印字したとはしない。',
 '比較期間は同じ追跡点の同じ出来事の全範囲を両方向で対応させる。各系の座標時刻の数値と各時刻の全体電荷を計る同時切片は別である。有限区間は同じ過程を比較する明示した読みで、世界全体の永遠の履歴や他の物体の期間まで要求しない。',
 '全体の保有量は既存eisvyの同じ物質部分の加法的な符号付き電気量として読む。全体membersだけを量の対象とし、全部分の不変付着ekx2/ekx3を流用しない。内部での正負電荷の交換・移動と全体の一定性を区別する。量の物理的帰属を任意の数値関数で代用しない。',
 '帯電は随伴する系での正味総電荷が少なくとも一時刻で非零という通常の巨視的な読み。負電荷を含み、内部の全点が非零とは要求しない。前件の一定性と合わせればその期間の非零が保たれるが、非零をKへ自動的に移す前提にはしない。',
 '両系での時間不変を条件として結ぶのであり、二系の数値総電荷の等値を定理内容へ追加しない。固定した共通の電荷単位を使うが、時間とともに尺度を変えて一定性を作ることは許さない。旧seni/senhの定速・一様密度による相殺だけで任意運動の結論を済ませない。',
 'この定理内容を記述することは、第九節の方程式からの一般的な物理的導出を証明することとは別である。局所電荷保存、内部部分の一定、特定の運動方程式を原文の条件へ補って推論を修理しない。',
 '全実時間・全座標族の量化を維持する。有限標本は結合・欠落・取り違え・定数条件の診断であり、連続体や原文同義性の自動証明ではない。',
]

def record(fields=MODEL,**replace):
    b={n:replace.get(n,v(n)) for n,t in fields};t=replace.get('time',v('time'));event=replace.get('event',v('event'))
    return k('sb',b['anchor'],event,b['frame'],b['context'],b['lengthunit'],b['timeunit'],t,*(app(app(b[a],b['anchor']),t) for a in ('x','y','z')))

def side(own=False,**extra):
    return {n:extra.get(n,k('ra') if n=='frame' and not own else v('ownframe') if n=='frame' else v('own'+n) if own and n in dict(SERIES) else v(n)) for n,t in MODEL}

def vals(fields,b):return [b.get(n,v(n)) for n,t in fields]

def definitions():
    t=v('time');event=v('event');value=app(v('charge'),t);inside=k('lg',v('lower'),v('upper'),t)
    text=define('ek22',LOCAL,both(inside,k('ba',value),k('eisvy',*args(PHYSICAL,kind=k('zor'),part=v('members'),quantityunit=v('chargeunit'),amount=value))))
    rec=record();membership=q('f','label','a',op('z',app(v('members'),v('label')),app(k('zqn'),v('label'),v('distribution'),v('context'))))
    each=q('f','time',R,op('y',inside,both(q('g','event','a',rec),q('f','event','a',op('y',rec,k('ek22',*args(LOCAL)))))))
    text+=define('ek23',MODEL,both(k('eiad',*args(HISTORY)),k('va',v('frame')),membership,app(v('members'),v('anchor')),each))
    first,last=v('first'),v('last');selected=both(k('lg',v('lower'),v('upper'),first),k('lg',v('lower'),v('upper'),last))
    constant=q('f','first',R,q('f','last',R,op('y',selected,k('sca',app(v('charge'),first),app(v('charge'),last)))))
    text+=define('ek24',CONSTANT,both(k('ba',v('lower')),k('ba',v('upper')),k('bg',v('lower'),v('upper')),q('f','time',R,op('y',inside,k('ba',value))),constant))
    text+=define('ek25',CONSTANT,q('g','time',R,both(inside,k('ba',value),op('u',k('sca',value,ZERO)))))
    origin=q('f','time',R,op('y',inside,both(*(both(k('ba',coord(a,v('anchor'),t)),k('sca',coord(a,v('anchor'),t),ZERO)) for a in ('x','y','z')))))
    text+=define('ek26',MODEL,both(k('ek23',*args(MODEL)),origin))
    old,new=side(),side(True);own=v('owntime')
    oldrec=record(**old);newrec=record(**new,time=own)
    oldselected=both(k('lg',v('lower'),v('upper'),t),oldrec);newselected=both(k('lg',v('ownlower'),v('ownupper'),own),newrec)
    text+=define('ek27',PAIR,both(oldselected,newselected))
    directions=[quantified('f',[('event','a'),(name,R)],op('y',selection,q('g',other,R,k('ek27',*args(PAIR))))) for name,other,selection in [('time','owntime',oldselected),('owntime','time',newselected)]]
    text+=define('ek3a',SETTING,both(*directions))
    text+=define('ek3b',SETTING,both(k('ek23',*vals(MODEL,old)),k('ek26',*vals(MODEL,new)),k('eiag',*vals(HISTORY,old)),k('ek25',*vals(CONSTANT,new)),k('ek3a',*args(SETTING))))
    text+=define('ek3c',SETTING,op('y',k('ek24',*vals(CONSTANT,new)),k('ek24',*vals(CONSTANT,old))))
    text+=content('ek3d',quantified('f',CASES,op('y',k('ek3b',*args(SETTING,context=v('point'))),k('ek3c',*args(SETTING,context=v('point'))))))
    return text

@lru_cache(None)
def build():
    old=parse(read(PARENT));assert len(old['statements'])==412
    assert not set(MEANINGS)&{d['name'] for d in old['declarations']}
    doc=deepcopy(old);doc['statements']=[];doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']
    added=doc['declarations'][len(old['declarations']):]
    basis=dict(status='whole_body_charge_histories_with_arbitrary_motion',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives={},definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=[]).document
    ann=json.loads(read('data/convective-relativity-claim-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode()))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
