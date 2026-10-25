"""Connect the actual local curvature, sole normal action and both printed forms."""
from scripts.compose_traversed_potential import *
from scripts import compose_electron_deflection_response as response
from noema.grammar import number_word

PARENT=FULL;PARENT_BASIS=BASIS;PARENT_ANNOTATIONS=ANNOTATIONS
FULL='examples/v014/einstein-local-magnetic-radius.noema';CORE='examples/v014/local-magnetic-radius-core.noema'
BASIS='data/local-magnetic-radius-basis-v1.json';ANNOTATIONS='data/local-magnetic-radius-identifiers-v1.json'
SETTING=response.SHARED+[(n,t) for n,t in response.TRACE if n!='scene']+[('context','d')]+[(n,R) for n in ('longitudinal','magnetic','radius')]+[('radiusunit','a'),('radiusscale','b')]
CONTRIBUTION=[(n,'a') for n in ('record','matter','frame','event','forceunit')]+[('force',POINT),('context','d')]
NUMERIC=[(n,R) for n in ('light','speed','mass','charge','magnetic','ay','radius')]
PRIMITIVES={
 'eis4t':(CONTRIBUTION,'recordが、同じmatter・frame・eventで実際に作用する一つの機械的相互作用の寄与を、同じforceunitの三成分forceで記述するという物理的帰属。力は運動量変化への寄与又はそれを釣り合わせる機械的作用により同定する。相互作用の区別はその物理的作用源に基づき、都合のよい数値分割や、異なる作用源を相殺して零とした一記録への集約ではない。この関係の範囲は同じ出来事の全ての実際の寄与を含み、観測済みの記録一覧に限定しない。同じ作用の複数の記述は許す。磁気的分類、他の寄与の不存在・方向、合力、特定の運動方程式又は原文の曲率公式は含めない。'),
}
FIXED={n:s for n,s in energy.FIXED.items() if n in dict(response.SHARED)}|{'speed':'eisxt','chargescale':'eis4m','radiusunit':'ta','radiusscale':energy.FIXED['lengthscale']}
NEW_VALUES={}
for i,(n,t) in enumerate((x for x in SETTING if x[0] not in FIXED and x[0]!='context')):
    symbol='eis5'+number_word(i);FIXED[n]=symbol;NEW_VALUES[symbol]=(t,'第三項の同じ磁気偏向事例の'+n+'。同じ電子・K・単位を使うが、第二項の静電加速の全軌道とは別の局所事例である。役割はeso–esvで接続する。')
REFERENCES={'eis4u':'u0271の第三項、曲率半径を計算する条件と第二(A)への参照。','eis4v':'u0272のM0441、負の横加速度・v²/R・磁場の式の表示。','eis4w':'u0273のoder、同じ条件の下での半径式への書換え。','eis4x':'u0274のM0442、Rについて解いた表示。','eis4y':'第三項で同じ局所曲率半径を呼ぶ記号R。','eis4z':'第三項で同じ磁場z成分を呼ぶ記号N。'}
MEANINGS={
 'esm':'同じ出来事・系・力単位の一つの実際の力の寄与があるなら、その記録が磁気的寄与であるか、三成分が有効でy,z成分が零である。後者は現在の速度x方向に対する接線方向の作用であり、大きさ零に限定しない。',
 'esn':'同じ磁気的寄与と電気的寄与を実際の寄与に含め、全ての作用源・力値にesmを要求する。磁気以外の偏向原因がないという排他条件を、横電場零又は他の力の総和零から推定しない。',
 'eso':'同じ電子・K・局所出来事・実三速度と二階微分・整合単位・低速質量・非零符号付き電荷・物理的二場を共有する。瞬間速度(v,0,0)、磁場(0,0,N)、電場(X,0,0)と二つの実力寄与、esnの唯一の偏向原因を結び、v>0とqN>0の印刷方向を採る。接線電場Xを零へ固定しない。',
 'esp':'esoと同じ実三速度・三加速度からsevcで正の局所曲率半径を作り、同じ座標長さ尺度の半径単位へ結ぶ。標準配置の瞬間の法平面をxy面に取りaz=0とする。接線加速度ax、全軌道の円・等速・一様場は要求しない。',
 'esq':'同じV,v,μ,q,N,ay,Rについて、既存sevfの適用範囲と印刷の−ay=v²/R=(q/μ)(v/V)N sqrt(1−(v/V)²)の両等号を保持する。',
 'esr':'同じ量とqN>0で、既存sevhと印刷のR=V²(μ/q)(v/V)/sqrt(1−(v/V)²)/Nを保持する。N又は電荷の絶対値へ替えない。',
 'ess':'同じ局所磁気偏向事例の実ayへ、Y=0とした第二(A)のsetkを適用する。これは場と軌道だけの定義とは別の力学的内容である。',
 'est':'同じ標準配置の物理的局所曲率espと第二(A)のessを合わせる導出・書換えの前提。',
 'esu':'同じ物理的局所曲率espにM0441の全等号列esqを接続する。',
 'esv':'同じ物理的局所曲率espにM0442の半径式esrを接続する。第二(A)の成立は式だけから逆推定しない。',
 'esw':'現在の第三項の同じ電子・磁気偏向事例のespという設定内容。','esx':'同じ第三項の事例に適用した第二(A)の内容。','esy':'同じ第三項の導出・同値書換えの前提est。','esz':'同じ第三項のM0441全等号列。','es2':'同じ第三項のM0442半径式。',
 'es3':'同じ導出前提esyの下で、M0441の内容eszとM0442の内容es2が同値であるという条件内容。前提なしの両式の同値や排他的選言ではない。',
 'es4':'同じ電子・局所事例の実曲率半径というRの量内容。候補値をespへ結び、答えとなる磁場公式を候補条件へ先取りしない。',
 'es5':'同じ電子の同じ局所事例での、物理的磁場z成分Nという量内容。力−qvN/Vとは区別し、同じ場・単位・点へ結ぶ。',
 'es6':'同じ物理的局所曲率半径の値を求める質問。現在の値又は磁場公式を既知の答えとして要求しない。',
 'es7':'u0271の第三項、条件付きの半径計算の取組、RとNの呼称、唯一の偏向原因という挿入、第二(A)からの導出と次表示への接続。',
 'eta':'u0271の唯一の偏向原因という同じ事例の挿入内容。','etb':'u0271全文のメッセージ。','etc':'u0271を同じ著者・論説へ帰属し、第二項の表示の後に置く。',
 'etd':'u0272のM0441全表示と著者主張。','ete':'u0272全文のメッセージ。','etf':'u0272を同じ著者・論説へ帰属し、第三項導入の後に置く。',
 'etg':'u0273のoderを、同じ前提の下でM0441からM0442への同値書換えとして提示する。','eth':'u0273の書換えメッセージ。','eti':'u0273を同じ著者・論説へ帰属し、M0441に続ける。',
 'etj':'u0274のM0442全表示と著者主張。','etk':'u0274全文のメッセージ。','etl':'u0274を同じ著者・論説へ帰属し、oderの後に置く。',
}
LIMITS=[
 '原刊921頁u0271–u0274。前項の静電加速とは別の局所磁気偏向事例で、同じ現在の電子・K・μ・q・Vと速度及び整合単位を使う。実軌道・出来事・実二場はこの事例に共有する。',
 '先行(A)の標準配置に沿い、瞬間速度を正x、磁場をz方向、瞬間の曲率の法平面をxy面に選ぶ。正の幾何学的Rと印刷の−ayを保つためqN>0の向きを採る。qとNがともに負でもよい。逆向きは既存の一般定義sevjで表せるが、原文を絶対値付きの公式へ訂正しない。',
 '唯一の偏向原因は、全ての実際の非磁気的作用源の寄与が接線方向だけにあることとする。二つの非磁気的な横力が相殺するだけの例は除く。電場の横成分零だけで排他条件を認定せず、非零の縦電場・接線加速度・接線方向の他の作用を許す。',
 'Rは校正された実座標時刻の一階・二階微分による局所曲率の逆数。局所の法平面という選び方を、全軌道が平面円であること、一様な磁場、全期間の等速又は等加速へ拡張しない。静止や曲率零に有限の正のRを割り当てない。',
 'M0441の負号と二つの等号、M0442のV²・μ/q・(v/V)/平方根・1/Nを保存する。oderは同じ第二(A)と方向・非零分母の下での同値書換え。半径式だけが合う反例から最初の加速度式まで成立したとしない。',
 'Wir berechnenは同じ著者の論述上の計算の取組。実測済み、計算機の証明完了、現代の電子の固定電荷や微視的機構は補わない。有限診断と全多項式係数の検査を、全実数の解析又は同義性の自動証明としない。旧437主張・意味・判断・証拠を保存する。',
]
def actual(fields,**replace):return [replace.get(n,v('point') if n=='context' else k(FIXED[n])) for n,t in fields]
def vectors():
    zero=k('bb',rat(0));qv=v('charge');s=v('speed');N=v('magnetic');V=v('light');vec=lambda x,y,z:k('ekbe',x,y,z)
    return vec(v('longitudinal'),zero,zero),vec(zero,zero,N),vec(s,zero,zero),vec(k('shv',qv,v('longitudinal')),zero,zero),vec(zero,k('bf',zero,k('shv',qv,k('shv',s,k('shv',N,k('sjd',V))))),zero)
def definitions():
    text=''.join('r '+n+'['+' '.join(t for _,t in fs)+'] c.\n' for n,(fs,_) in PRIMITIVES.items())+''.join('r '+n+'[] '+t+'.\n' for n,(t,_) in NEW_VALUES.items())+''.join('r '+n+'[] a.\n' for n in REFERENCES)
    zero=k('bb',rat(0));one=k('bb',rat(1));ctx=v('context');loc=v('location');V=v('light');s=v('speed');mass=v('mass');charge=v('charge');N=v('magnetic');radius=v('radius')
    E,B,velocity,EF,MF=vectors();vals={n:v(n) for n,t in SETTING}|dict(point=loc,carrier=v('matter'),electricconversion=one,magneticconversion=k('sjd',V))
    contribution=lambda record,force:k('eis4t',record,v('matter'),v('frame'),v('event'),v('forceunit'),force,ctx)
    force=v('force');record=v('record');components=[app(force,k(axis)) for axis in ROLES[:3]]
    nonnormal=both(*(k('ba',x) for x in components),*(k('sca',x,zero) for x in components[1:]))
    text+=define('esm',SETTING+[('record','a'),('force',POINT)],op('y',contribution(record,force),op('x',k('eirt',record,v('matter'),v('frame'),v('event'),ctx),nonnormal)))
    text+=define('esn',SETTING,both(contribution(v('electricrecord'),EF),contribution(v('magneticrecord'),MF),quantified('f',[('record','a'),('force',POINT)],k('esm',*args(SETTING),record,force))))
    physical=[k('ejsn',*[vals[n] for n,t in response.FIELDS]),k('ek3n',*[vals[n] for n,t in response.UNITS]),k('ek3o',*[vals[n] for n,t in response.MASS]),k('ek3u',*[vals[n] for n,t in response.CHARGE]),k('ek3q',*[vals[n] for n,t in response.KINEMATIC]),k('eisqd',v('matter'),v('frame'),v('event'),v('lengthunit'),v('timeunit'),loc,ctx)]
    physical += [k('s45',V,s),k('bg',zero,s),k('ba',N),k('ba',v('longitudinal')),k('bg',zero,k('shv',charge,N))]
    moment=coord(loc,ROLES[3]);physical += [k('sca',app(v(n),moment),value) for (n,t),value in zip(response.PROFILES,(s,zero,zero))]
    ea=vals|dict(forcerecord=v('electricrecord'),fieldunit=v('electricunit'),electric=E,force=EF,conversion=one)
    ma=vals|dict(forcerecord=v('magneticrecord'),magnetic=B,velocity=velocity,force=MF,conversion=k('sjd',V))
    physical += [k('eibs',*[ea[n] for n,t in response.ELECTRIC]),k('eico',*[ma[n] for n,t in response.MAGNETIC]),k('esn',*args(SETTING))]
    coords=[coord(loc,a) for a in ROLES]
    physical += [k('sca',app(app(v(field),k(axis)),*coords),value) for field,values in [('electricfield',(v('longitudinal'),zero,zero)),('magneticfield',(zero,zero,N))] for axis,value in zip(ROLES[:3],values)]
    text+=define('eso',SETTING,both(*physical))
    text+=define('esp',SETTING,both(k('eso',*args(SETTING)),k('sevc',*(app(v(n),moment) for n,t in response.PROFILES),*args(response.ACCEL),radius),k('sca',v('az'),zero),k('ejwb',v('radiusunit'),rat(1),rat(0),rat(0),v('radiusscale'),ctx),op('e',v('radiusscale'),v('lengthscale'))))
    ratio=k('shv',s,k('sjd',V));root=k('cj',k('bf',one,k('shv',ratio,ratio)));beta=k('soy',V,s)
    numeric=[V,s,beta,mass,charge,N,v('ay'),radius]
    first=k('bf',zero,v('ay'));middle=k('shv',k('shv',s,s),k('sjd',radius));last=k('shv',k('shv',charge,k('sjd',mass)),k('shv',ratio,k('shv',N,root)))
    text+=define('esq',NUMERIC,both(k('sevf',*numeric),k('sca',first,middle),k('sca',middle,last)))
    rhs=k('shv',k('shv',V,V),k('shv',k('shv',mass,k('sjd',charge)),k('shv',k('shv',ratio,k('sjd',root)),k('sjd',N))))
    text+=define('esr',NUMERIC,both(k('sevh',*numeric[:6],radius),k('sca',radius,rhs)))
    text+=define('ess',SETTING,k('setk',V,s,beta,mass,charge,zero,N,v('ay')))
    for name,part in [('est','ess'),('esu','esq'),('esv','esr')]:text+=define(name,SETTING,both(k('esp',*args(SETTING)),k(part,*args(SETTING if part=='ess' else NUMERIC))))
    ev=lambda n:op('t',k(n),v('point'))
    for name,target in [('esw','esp'),('esx','ess'),('esy','est'),('esz','esu'),('es2','esv')]:text+=content(name,k(target,*actual(SETTING)))
    text+=content('es3',op('y',ev('esy'),op('z',ev('esz'),ev('es2'))))
    for name,value,target in [('es4','radius','esp'),('es5','magnetic','eso')]:text+=define(name,[('matter','a'),('value',R),('context','d')],both(op('e',v('matter'),k('eisxh')),k(target,*actual(SETTING,**{value:v('value')},context=ctx))))
    text+=define('es6',[],'j v[i[value '+R+']['+k('es4',k('eisxh'),v('value'),k('ri'))+']]','g['+R+']')
    text+=content('eta',k('esn',*actual(SETTING)))
    p=v('point');who=k('rd');paper=k('eirf');section=k('eisxg');node=k('eis4u');display=k('eis4v');rewrite=k('eis4w');lastdisplay=k('eis4x')
    text+=content('es7',both(k('eislk',node,k('eis3w'),'n p d b',paper,p),k('eiszy',node,who,quote('es6'),section,p),k('eisnw',node,who,k('eis4y'),'r[p es4]',paper,p),k('eisnw',node,who,k('eis4z'),'r[p es5]',paper,p),k('ug',node,who,quote('esw'),section,p),k('eisa5',node,who,quote('esw'),quote('eta'),p),k('eis3v',quote('esx'),quote('elk'),rat(2),p),k('eiswm',node,who,k('eisym'),quote('elk'),paper,p),k('zc',node,who,quote('esy'),quote('esz'),section,p),k('uf',who,node,display,p)))
    text+=content('etd',both(k('eisox',display,quote('esz'),p),k('uh',display,who,quote('esz'),section,p)))
    text+=content('etg',both(k('zd3',rewrite,who,quote('esy'),quote('esz'),quote('es2'),section,p),k('uh',rewrite,who,quote('es3'),section,p),k('uf',who,rewrite,lastdisplay,p)))
    text+=content('etj',both(k('eisox',lastdisplay,quote('es2'),p),k('uh',lastdisplay,who,quote('es2'),section,p)))
    for body,msg,claim,n,previous in [('es7','etb','etc',node,k('eis4r')),('etd','ete','etf',display,node),('etg','eth','eti',rewrite,display),('etj','etk','etl',lastdisplay,rewrite)]:
        text+='d '+msg+'[] f[j s[k '+body+'[]]].\n';text+=define(claim,[],both(k('eir3',n,who,paper,quote(msg),k('ri')),k('ue',previous,n,k('ri'))))
    return text

@lru_cache(None)
def build():
    old=parse(read(PARENT));assert len(old['statements'])==437
    assert not(set(MEANINGS)|set(PRIMITIVES)|set(REFERENCES)|set(NEW_VALUES))&{d['name'] for d in old['declarations']}
    doc=deepcopy(old);doc['statements']=[];doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']+[dict(kind='assert',body=dict(kind='call',symbol=n,arguments=[])) for n in ('etc','etf','eti','etl')]
    added=doc['declarations'][len(old['declarations']):]
    prim={d['name']:dict(parameters=d['parameters'],result=d['result'],arguments=[n for n,t in PRIMITIVES[d['name']][0]] if d['name'] in PRIMITIVES else [],meaning_ja=PRIMITIVES[d['name']][1] if d['name'] in PRIMITIVES else NEW_VALUES[d['name']][1] if d['name'] in NEW_VALUES else REFERENCES[d['name']]) for d in added if d['kind']=='primitive'}
    basis=dict(status='sole_magnetic_deflection_and_local_radius_connected',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives=prim,definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=list(range(437,441))).document
    ann=json.loads(read(PARENT_ANNOTATIONS));ann.update(document=FULL,document_sha256=digest(body.encode()))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
