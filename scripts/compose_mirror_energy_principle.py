"""Compose the four energy/work sentences and the pressure display without assuming conservation."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_limits import ROOT,R,v,call as k,op,both
from scripts.compose_material_relative_frame import define,args
from scripts.compose_relativity_conjecture import content,evaluate
from scripts.compose_two_postulates import quote
from scripts.compose_doppler_infinity import quantified
from scripts.compose_field_equations import REGION
from scripts.compose_mirror_energy_work import TOTAL,PRINTED,physical_rows
from scripts.compose_mirror_surface_pressure import BOUNDS
from scripts.compose_mirror_wave_quantities import FIXED

def read(path):return (ROOT/path).read_text(encoding='utf-8')
PARENT='examples/v014/einstein-mirror-energy-work.noema';PARENT_BASIS='data/mirror-energy-work-basis-v1.json'
FULL='examples/v014/einstein-mirror-energy-principle.noema';CORE='examples/v014/mirror-energy-principle-core.noema'
BASIS='data/mirror-energy-principle-basis-v1.json';ANNOTATIONS='data/mirror-energy-principle-identifiers-v1.json';INDICES=[402,403]
ENERGIES=[(n,R) for n in ('arriving','returning','transmitted','mechanical','other')]
BUDGET=[(n,'a') for n in ('interaction','body','patch','frame','lengthunit','timeunit','energyunit')]+[('region',REGION)]+[(n,R) for n in ('lower','upper','area')]+ENERGIES+[('scope','a'),('context','d')]
VARIABLES=[(n,t) for n,t in TOTAL if n not in FIXED]
PRINCIPLE_VARIABLES=[(n,t) for n,t in BUDGET if n!='context']
NAME_VARIABLES=[(n,t) for n,t in TOTAL if n not in {*FIXED,'patch','pressure'}]
CLAIMS={'ekub':'incoming','ekuc':'outgoing','ekud':'balance','ekue':'work','ekuf':'pressure'}
PRIMITIVES={
 'eisu2':(BUDGET,'同じinteractionによるbodyのpatchへのエネルギー移転について、指定frame・長さ時間・エネルギー単位とregion内の正長区間lower–upper・面積areaで、arrivingを入射側から到来する総エネルギー、returningを同じ側へ戻る総エネルギー、transmittedを反対側へ通過する総エネルギー、mechanicalをこの相互作用の力が物体の移動に行う符号付き機械的仕事、otherをそれ以外の正味の移転として採用する完全な有限区間の物理モデル対応。otherは内部蓄積・熱・その他の供給又は散逸を落とさず合わせた符号付き寄与で、非機械的移転の各経路の不存在までは含意しない。局所のeisudと同種のモデル採用を有限面部分・時間区間の総量で表し、そのretainedをmechanicalとotherに分けて扱う。数値的な保存式、経路の零、場からの積分、力からの仕事の計算はこの関係の意味に含めず別に構成する。面の静止、反射、光又は特定の原文の式も含意しない。'),
 'eisu3':([], 'u0222第一文の静止系で測った単位面積時間あたりの入射エネルギーとoffenbarの箇所。'),
 'eisu4':([], 'u0222第二文の同じ面から離れるエネルギーの箇所。'),
 'eisu5':([], 'u0222第三文の二表示の差とエネルギー原理による仕事への結合の箇所。'),
 'eisu6':([], 'u0222第四文のその仕事をP.vへ等置して光圧式を得る導入箇所。'),
 'eisu7':([], 'u0223=M0381の光圧の表示箇所。'),
 'eisva':([], '同じ論説のこの箇所のEnergieprinzipという呼称個体。内容は有限区間の完全収支に対する保存則ekuaへeischで結ぶ。'),
 'eisvb':([], '同じ鏡の物質的面部分のKにおける平均光圧Pの表記個体。物理的量はekuhで同じ力・時間・面積へ結び、閉じた光圧式を語義へ含めない。'),
}
MEANINGS={
 'ekt5':'一般の有限区間収支モデルeisu2に、有効な同じ区間と正面積、五つの有効な総エネルギーを結ぶ。入出・透過は非負、機械的仕事とその他の移転は符号付き。保存の等式は前提にしない。',
 'ekt6':'同じ102設定のektxへ、同じK・相互作用・物体・矩形・区間・単位・領域でのekt5を結ぶ。入出と仕事の同じ面積時間平均を面積*時間幅で総量へ変え、透過と非機械的な正味移転を零とした理想モデルを明示的に採用する。kでのretained=0からKでの仕事=0を推論せず、保存式も追加しない。',
 'ekt7':'五つの有効なエネルギーについてarriving=returning+transmitted+mechanical+otherという保存の等式。経路の帰属とは分けた数的な内容。',
 'ekua':'全ての同じ有限区間の完全収支設定でekt5ならekt7というエネルギー原理の内容。特定の光や零損失だけの法則へ縮めず、物理モデルの存在又は保存式の自動的証明は含めない。',
 'ekub':'同じ98の自由役割の全割当でekt6ならincomingがM0377のektvに等しいという第一文の内容。K・V・先行範囲・評価状況は固定する。',
 'ekuc':'同じ設定でoutgoingがM0378のektwに等しいという第二文の内容。三重プライムのK振幅と方向余弦を共有する。',
 'ekud':'同じ設定でektz、すなわちwork=incoming−outgoingという第三文の帰結内容。仕事は先行の同じ力の積分に結ばれ、差を仕事と命名するだけではない。',
 'ekue':'同じ設定でekt2、すなわち同じ機械的仕事の面積時間平均がP*vに等しいという第四文の等置内容。vによる除算を定義へ入れない。',
 'ekuf':'同じ設定で圧力がM0381のekt4に等しいという著者の表示内容。零速度の圧力の導出を仕事だけから保証しない。',
 'ekug':'同じ鏡・波・面部分・時間・単位・平均値を一つの98証人の存在割当で共有したekt6の設定内容。',
 'ekuh':'同じpatchとpressure及び評価状況へ、残る96証人によるekt6の構成を結ぶPの命名規則。量の対象を波単独や鏡全体へ取り違えない。',
 'ekui':'同じ設定ekug、二つのエネルギー表示ekub/ekuc及び一般のエネルギー原理ekuaを併せた第三文の導出根拠内容。帰結の収支式ekudを根拠へ先取りしない。',
 'ekuj':'同じ設定、入出表示、仕事の収支及びP*vへの等置を合わせた第四文の導出条件内容。得るべき閉じた光圧式ekufを条件に入れない。',
 'ekuk':'u0222第一文を著者が述べ、同じ内容を明らかと提示するoffenbarを保持する。',
 'ekul':'u0222第二文の離れるエネルギー表示を同じ著者へ帰属する。',
 'ekum':'u0222第三文でエネルギー原理を命名参照し、同じ二表示への照応とその根拠ekuiから仕事収支ekudを得るという著者の帰結提示を結ぶ。',
 'ekun':'u0222第四文のdie letztereを同じ第三文の仕事へ照応し、Pを同じ物質面部分の圧力として命名する。P*vへの等置の下で式を得るという条件付き帰結、コロン、後続表示の順序を保つ。',
 'ekuo':'u0222の四文を同じ評価状況で一続きに結び、四つの箇所の順序と区別を保持する。',
 'ekup':'u0223の圧力表示を同じekufへ結ぶ。',
 'ekuq':'u0222の四文全体ekuoを述べるメッセージ。',
 'ekur':'四文を同じ著者と論説へ帰属し、u0221からの順序を保持する。',
 'ekus':'u0223の表示ekupを述べるメッセージ。',
 'ekut':'光圧表示を同じ著者と論説へ帰属し、u0222の第四文からの順序を保持する。',
 'ekuu':'同じ102設定のincomingをM0377のektvへ等置する。一文の全量化と独立に数的な同一設定の結合を構成する。',
 'ekuv':'同じ102設定のoutgoingをM0378のektwへ等置する。戻した同じKの振幅と角を使う。',
}
LIMITS=[
 '原刊915頁u0222の四文全体359非空白本文文字、u0223及びM0377–M0381を対象とする。単位面積時間あたりのエネルギーは、先行と同じ物質的矩形の全面で一様な一周期平均と読む。第一文の静止系で測るという限定は両エネルギー・仕事・圧力の同じKを定める。',
 '入出平均と機械的仕事は前段のektxの物理場・動く境界Jx−v*u・全接線位置の積分平均・同じ力の仕事積分へ結ぶ。原刊のA‴全体を平方する。MathMLの空基底平方は別量の平方とせず、原刊の組版へ照合する。',
 'エネルギー原理は、完全な有限区間収支モデルの五経路の保存として明示する。一般関係eisu2は経路の物理的対応と完全性を担い、保存式・零損失・鏡・原文一文の内容は定義に隠さない。eisudの点ごとのモデルと、新しい有限面部分のモデルは同じ相互作用・物体・単位に結び付ける別の採用であり、観測又はモデル一致を自動推論しない。',
 '理想鏡のこの議論では、Kの同じ有限区間で透過と非機械的な正味移転が零で、正味移転は同じ光の力の機械的仕事になるという読みを明示的に採用する。kでの正味移転零だけからこのKの仮定を導いたとはしない。熱等の個別経路が全て不存在という、原文より強い条件は加えない。',
 'die Differenz dieser beiden Ausdrückeは第一・第二文の表示の差、die letztereは第三文の仕事への照応と読む。後者を出射エネルギーへ取り違えない。workは同じ面積時間あたりの平均であり、原文第三・第四文の面積単位の省略を同じ量への照応として補う。',
 'offenbarは著者による明白さの提示、nach dem Energieprinzipは同じ一般原理を根拠とする帰結提示、Setzt man ... so erhält manは仕事をP*vへ等置した下での条件付き導出提示とする。引用を実行して著者の全ての式の真理や正しい導出を認定しない。',
 'Pは同じK、物質的面部分、光の力、時間区間の平均法線圧力。符号付き仕事と接線力を許し、圧力を仕事/vで定義しない。零速度で仕事の等式だけからPを決定できない。表示右辺の零速度値は定義できるが、その値への極限又は別の力の議論をこの四文の証明済み内容へ補わない。',
 'kの角の先行結線読解、原刊M0376の周波数分母の不一致を保持する。ここではKの旧角と戻した角を用いる。先行の中間等式を修正したり、成立する数値だけへ設定を縮めたりしない。',
 '全実数・全関数の量化と全区間の積分を有限検査へ置換しない。検査は引数結合、数値反例、引用、照応・提示・保存の証拠であり、物理法則又は意味同義性の自動証明ではない。後続の近似と経験・他理論との一致、第八節見出し、二作品全体は未完。',
]

def budget_row():
    rows,force=physical_rows();row=rows[0]|dict(patch=v('patch'),lower=force['lower'],upper=force['upper'],area=k('ekqv',*args(BOUNDS)))
    scale=k('shv',row['area'],k('bf',row['upper'],row['lower']));zero=k('bb','n p a b')
    row.update({n:k('shv',v(mean),scale) for n,mean in [('arriving','incoming'),('returning','outgoing'),('mechanical','work')]})
    row.update(transmitted=zero,other=zero)
    return row

def conclusions():
    return {'ekub':k('ekuu',*args(TOTAL)),
            'ekuc':k('ekuv',*args(TOTAL)),
            'ekud':k('ektz',v('incoming'),v('outgoing'),v('work')),
            'ekue':k('ekt2',v('pressure'),v('speed'),v('work')),
            'ekuf':k('ekt4',*args(TOTAL))}

def definitions():
    text=''.join('r '+n+'['+' '.join(t for _,t in fs)+'] '+('c' if fs else 'a')+'.\n' for n,(fs,_) in PRIMITIVES.items())
    zero=k('bb','n p a b');row=budget_row()
    text+=define('ekt5',BUDGET,both(*(k('ba',v(n)) for n,t in BUDGET if t==R),k('bg',v('lower'),v('upper')),k('bg',zero,v('area')),*(k('bc',zero,v(n)) for n in ('arriving','returning','transmitted')),k('eisu2',*args(BUDGET))))
    text+=define('ekt6',TOTAL,both(k('ektx',*args(TOTAL)),k('ekt5',*[row[n] for n,t in BUDGET])))
    text+=define('ekt7',ENERGIES,both(*(k('ba',v(n)) for n,t in ENERGIES),k('sca',v('arriving'),k('bd',v('returning'),k('bd',v('transmitted'),k('bd',v('mechanical'),v('other')))))))
    text+=define('ekuu',TOTAL,k('sca',v('incoming'),k('ektv',*args(PRINTED))))
    text+=define('ekuv',TOTAL,k('sca',v('outgoing'),k('ektw',v('pi'),v('labamplitude'),v('light'),v('speed'),v('labanglecos'))))
    values=[v('point') if n=='context' else v(n) for n,t in BUDGET]
    text+=content('ekua',quantified('f',PRINCIPLE_VARIABLES,op('y',k('ekt5',*values),k('ekt7',*args(ENERGIES)))))
    actual=[FIXED.get(n,v(n)) for n,t in TOTAL]
    # Substitute the fixed slots in each conclusion through a typed helper call;
    # the arithmetic already has only light among those fixed slots.
    for root,body in conclusions().items():
        body=body.replace(v('light'),FIXED['light']).replace(v('frame'),FIXED['frame']).replace(v('scope'),FIXED['scope']).replace(v('context'),FIXED['context'])
        text+=content(root,quantified('f',VARIABLES,op('y',k('ekt6',*actual),body)))
    text+=content('ekug',quantified('g',VARIABLES,k('ekt6',*actual)))
    fixed=dict(FIXED,context=v('context'),patch=v('object'),pressure=v('value'))
    text+=define('ekuh',[('object','a'),('value',R),('context','d')],quantified('g',NAME_VARIABLES,k('ekt6',*[fixed.get(n,v(n)) for n,t in TOTAL])))
    text+=content('ekui',both(*(evaluate(n) for n in ('ekug','ekub','ekuc','ekua'))))
    text+=content('ekuj',both(*(evaluate(n) for n in ('ekug','ekub','ekuc','ekud','ekue'))))
    p=v('point');a=k('rd');paper=k('eirf');scope=k('eistk');nodes=[k(n) for n in ('eisu3','eisu4','eisu5','eisu6')];display=k('eisu7')
    text+=content('ekuk',both(k('uh',nodes[0],a,quote('ekub'),scope,p),k('zdg',nodes[0],a,quote('ekub'),scope,p)))
    text+=content('ekul',k('uh',nodes[1],a,quote('ekuc'),scope,p))
    text+=content('ekum',both(k('eisch',k('eisva'),quote('ekua'),scope,p),k('zc',nodes[2],a,quote('ekui'),quote('ekud'),scope,p),k('uh',nodes[2],a,quote('ekud'),scope,p),*(k('eisra',nodes[2],a,paper,node,quote(previous),quote('ekud'),scope,p) for node,previous in [(nodes[0],'ekub'),(nodes[1],'ekuc')])))
    text+=content('ekun',both(k('eislo',k('eisvb'),'r[p ekuh]',paper,p),k('eisra',nodes[3],a,paper,nodes[2],quote('ekud'),quote('ekue'),scope,p),k('zc',nodes[3],a,quote('ekuj'),quote('ekuf'),scope,p),k('uf',a,nodes[3],display,p),k('ue',nodes[3],display,p)))
    text+=content('ekuo',both(*(evaluate(n) for n in ('ekuk','ekul','ekum','ekun')),*(k('ue',x,y,p) for x,y in zip(nodes,nodes[1:])),*(op('u',op('e',x,y)) for i,x in enumerate(nodes) for y in nodes[i+1:])))
    text+=content('ekup',k('eisox',display,quote('ekuf'),p))
    for shown,msg,stmt,node,previous in [('ekuo','ekuq','ekur',nodes[0],k('eisuv')),('ekup','ekus','ekut',display,nodes[3])]:
        text+='d '+msg+'[] f[j s[k '+shown+'[]]].\n'
        text+=define(stmt,[],both(k('eir3',node,a,paper,quote(msg),k('ri')),k('ue',previous,node,k('ri')),op('u',op('e',previous,node))))
    return text

@lru_cache(None)
def build():
    old=parse(read(PARENT));assert len(old['statements'])==402
    assert not(set(MEANINGS)|set(PRIMITIVES))&{d['name'] for d in old['declarations']}
    doc=deepcopy(old);doc['statements']=[];doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']+[dict(kind='assert',body=dict(kind='call',symbol=n,arguments=[])) for n in ('ekur','ekut')]
    added=doc['declarations'][len(old['declarations']):]
    primitives={d['name']:dict(parameters=d['parameters'],result=d['result'],arguments=[n for n,t in PRIMITIVES[d['name']][0]],meaning_ja=PRIMITIVES[d['name']][1]) for d in added if d['kind']=='primitive'}
    basis=dict(status='same_mirror_energy_principle_and_pressure_derivation_presented',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives=primitives,definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=INDICES).document
    ann=json.loads(read('data/mirror-energy-work-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode()))
    ann['entries'] += [dict(symbol=symbol,role='designation',forms=[dict(text=label,language='de',role='printed_identifying_form')]) for symbol,label in [('eisva','Energieprinzip'),('eisvb','P')]]
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
