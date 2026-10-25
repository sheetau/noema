"""Connect the three full properties to a scope-relative characterization of motion."""
from scripts.compose_experimental_list_opening import *

PARENT=FULL;PARENT_BASIS=BASIS;PARENT_ANNOTATIONS=ANNOTATIONS
FULL='examples/v014/einstein-complete-motion-expression.noema';CORE='examples/v014/complete-motion-expression-core.noema'
BASIS='data/complete-motion-expression-basis-v1.json';ANNOTATIONS='data/complete-motion-expression-identifiers-v1.json'
SCOPING=[('view','a'),('subject','a'),('frame','a'),('background','i[e]'),('base','d'),('candidate','d')]
SET_COMPARISON=[('scope','h[d] c'),('allowed','h[d] c'),('described','h[d] c')]
SCOPE_CALL=[(n,t) for n,t in SCOPING if n!='background']
P_FIXED={n:potential.FIXED[n] for n,t in response.SHARED if n!='speed'}
P_FIXED.update({n:potential.FIXED[n] for n in ('energyunit','energyscale','potentialunit','potentialscale','speedunit','speedscale','slowbound')})
R_FIXED={n:radius.FIXED[n] for n,t in response.SHARED if n!='speed'}|{n:radius.FIXED[n] for n in ('radiusunit','radiusscale')}
P_VARIABLE=[(n,t) for n,t in PBASE if n not in P_FIXED and n!='context']
R_VARIABLE=[(n,t) for n,t in radius.SETTING if n not in R_FIXED and n!='context']
PRIMITIVES={'eis6w':(SCOPING,'同じviewを記述するbaseで固定したbackgroundの対象・系・校正・理想化の下で、candidateが同じsubjectのframeに対する運動についての候補状況に属すること。背景を同じ内容として解釈し、対象の同一性、場・軌道・出来事・量の各帰属、基本的な運動学と物理量の定義を保持する。候補の範囲はその背景に適合する全ての運動記述であり、既に観測した例、都合のよい有限一覧、検査する運動法則又は比較する式の成否から選ばない。動力学法則に違反する候補も比較対象へ含める。viewにおいて物理的に許容されることは別のeisoeで問う。背景以外の理論の結論を先に要求せず、異なる対象・系・校正へ交換しない。')}
MEANINGS={
 'euu':'第二項の全パラメーターに対するer7の実電位・全場積分・仕事とesaの獲得速度式の合成。同じ引数を現在の第二項へ固定するとesdと同じ内容になる。',
 'euv':'第三項の同じ全物理設定について、esuの全加速度等号列、esvの半径表示、estの下での両表示の同値を合わせる。現在の第三項へ固定するとeuoと同じ内容になる。',
 'euw':'同じ電子・K・低速質量・符号付き電荷・V・単位校正と緩加速の基準を固定し、初期・終端・全軌道・場・電位区間・獲得速度・各エネルギーと記録の全ての組について、eudの適用条件ならeuuを要求する第二関係の法則図式。現在の一数値例だけへ縮めず、不適用の過程へ式を無条件に課さない。',
 'eux':'同じ電子・K・質量・電荷・V・単位の全局所事例について、espの実幾何学的半径と磁気だけによる偏向の適用条件ならeuvを要求する第三関係の法則図式。速度・軌道・加速度・場・記録・半径は全称化し、接線加速度を零又は全軌道を円へ固定しない。',
 'euy':'第一項eunの全偏向条件・比・任意許容速度の決定と、第二・第三項の全物理内容の適用図式euw/euxを合わせた三関係。第一項の理論内の可能試行という既存の読みを保つ。',
 'euz':'指定範囲で許される全候補が記述条件を満たす、という必要条件方向。',
 'eu2':'指定範囲で記述条件を満たす全候補が許される、という十分条件方向。',
 'eu3':'非空の指定範囲でeuzとeu2がともに成立する。記述の不足と過剰を区別した、状況上の双方向の一致。理論の現実的真理や実際に運動が生じたことを要求しない。',
 'eu4':'範囲内で記述が許すが理論が許さない反例。','eu5':'範囲内で理論が許すが記述が排除する反例。',
 'eu6':'現在の同じ電子・K・V・低速質量・非零符号付き電荷と校正単位の背景eq6。動力学の(A)や三関係の正しさは背景に入れない。',
 'eu7':'同じ背景eu6の全候補運動状況eis6wに、候補側でもその背景が保たれることを合わせた範囲。理論の許容eisoeから範囲を生成しない。',
 'eva':'同じ論説の理論規約eiscvについて、同じ電子・K・背景の全候補運動における許容eisoeと三関係euyとが双方向に一致する内容。mußを理論内の制約として読み、著者主張の物理的証明を行わない。',
 'evb':'直前の第一・第二・第三項の全内容eun/esd/euoを順序付きで引用した三関係の一覧。第二・第三の法則図式が現在の内容へ特殊化することは別の構造検査で確認する。',
 'evc':'u0275の同じ三項への後方参照、三つの異なる項目と全内容の対応、同じ論説の理論における完全表現の著者主張を接続する。',
 'evd':'u0275全文のメッセージ。','eve':'u0275を同じ著者・論説へ帰属し、第三項の最終表示の後へ置く。謝辞への既存接続も保持する。',
}
LIMITS=[
 '原刊921頁u0275を、第三項の半径式と謝辞の間の一文として確認した。Diese drei Beziehungenは既存の三項の全内容、vollständiger Ausdruckは同じ背景と適用条件での許容候補の双方向の一致として読む。原文の唯一の解釈とはせず、明示した解釈として保持する。',
 '同じ電子・K・低速質量・符号付き電荷・V・校正を共有する。第二項は初速零・静的軸上場・全電位区間・緩い加速・無放射・閉収支、第三項は同じ局所幾何・方向qN>0・唯一の偏向原因という適用条件を保持する。速度や軌道の成功例に限定しない。',
 '第二・第三の現在の事例を、全物理パラメーターを持つ法則図式の例として参照する。第一項の全速度にわたる条件・比・決定可能性も保存する。実験の実施や全物理理論の真理の証明を、この総括へ追加しない。',
 '比較範囲は背景が同じ全候補運動を含み、理論や式が正しいものだけを先に選ばない。個別の式が不適用の過程はその式では制約しない。全三式が同時に適用されること、各式の独立性、全場合でどれかの式が適用されることは完全一致とは別である。',
 'gemäß vorliegender Theorieとmußは、同じ論説の理論が許す運動への制約。規範的義務、因果的な強制、実測の一致、歴史的真理又はNoemaによる証明完了にしない。許容を三式から定義せず、独立した理論的入力eisoeとして比較する。',
 '状況の全称化と高階の物理パラメーターを有限標本で置き換えない。二値の束縛診断、境界の対照、原文への特殊化、旧物理検査の再利用を区別する。旧445主張と意味・証拠を保存し、u0239の見出しと最終完成監査を残す。',
]

def schema_args(fields,fixed):return [v('point') if n=='context' else k(fixed[n]) if n in fixed else v(n) for n,t in fields]
def definitions():
    text=''.join('r '+n+'['+' '.join(t for _,t in fs)+'] c.\n' for n,(fs,_) in PRIMITIVES.items())
    text+=define('euu',PBASE,both(k('er7',*args(PBASE)),k('esa',*values(potential.NUMERIC,speed=v('finalspeed')))))
    a=args(radius.SETTING)
    text+=define('euv',radius.SETTING,both(k('esu',*a),k('esv',*a),op('y',k('est',*a),op('z',k('esu',*a),k('esv',*a)))))
    for name,fields,fixed,ws,pre,law in [('euw',PBASE,P_FIXED,P_VARIABLE,'eud','euu'),('eux',radius.SETTING,R_FIXED,R_VARIABLE,'esp','euv')]:
        vs=schema_args(fields,fixed);text+=content(name,quantified('f',ws,op('y',k(pre,*vs),k(law,*vs))))
    p=v('point');text+=content('euy',both(*(op('t',k(n),p) for n in ('eun','euw','eux'))))
    c=v('candidate');scope=app(v('scope'),c);allowed=app(v('allowed'),c);described=app(v('described'),c)
    text+=define('euz',SET_COMPARISON,q('f','candidate','d',op('y',both(scope,allowed),described)))
    text+=define('eu2',SET_COMPARISON,q('f','candidate','d',op('y',both(scope,described),allowed)))
    text+=define('eu3',SET_COMPARISON,both(q('g','candidate','d',scope),k('euz',*args(SET_COMPARISON)),k('eu2',*args(SET_COMPARISON))))
    text+=define('eu4',SET_COMPARISON,q('g','candidate','d',both(scope,described,op('u',allowed))))
    text+=define('eu5',SET_COMPARISON,q('g','candidate','d',both(scope,allowed,op('u',described))))
    text+=content('eu6',q('g','chargescale','b',k('eq6',v('chargescale'),p)))
    text+=define('eu7',SCOPE_CALL,both(k('eis6w',v('view'),v('subject'),v('frame'),quote('eu6'),v('base'),c),op('t',k('eu6'),c)))
    view=k('eis3k');subject=k('eisxh');frame=k('ra');paper=k('eirf');author=k('rd');node=k('eis6j');section=k('eisxg')
    s='i[candidate d]['+k('eu7',view,subject,frame,p,c)+']';a='i[candidate d]['+k('eisoe',view,p,c)+']';d='i[candidate d]['+op('t',k('euy'),c)+']'
    text+=content('eva',both(k('eiscv',view,paper,quote('eigj'),p),op('t',k('eu6'),p),k('eu3',s,a,d)))
    text+=define('evb',[],'l[i[e]]['+' '.join(quote(n) for n in ('eun','esd','euo'))+']','j[i[e]]')
    items=('eis3x','eis4q','eis4u');contents=('eun','esd','euo')
    clauses=[op('u',op('e',k(items[i]),k(items[j]))) for i,j in ((0,1),(0,2),(1,2))]
    clauses += [k('eiswm',node,author,k(item),quote(n),paper,p) for item,n in zip(items,contents)]
    clauses += [k('eis3v',quote(n),quote('eup'),num(i+1),p) for i,n in enumerate(contents)]
    clauses += [k('uh',node,author,quote('eva'),section,p)]
    text+=content('evc',both(*clauses));text+='d evd[] f[j s[k evc[]]].\n'
    text+=define('eve',[],both(k('eir3',node,author,paper,quote('evd'),k('ri')),k('ue',k('eis4x'),node,k('ri'))))
    return text
@lru_cache(None)
def build():
    old=parse(read(PARENT));assert len(old['statements'])==445
    assert not(set(MEANINGS)|set(PRIMITIVES))&{d['name'] for d in old['declarations']}
    doc=deepcopy(old);doc['statements']=[];doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']+[dict(kind='assert',body=dict(kind='call',symbol='eve',arguments=[]))]
    added=doc['declarations'][len(old['declarations']):]
    prim={d['name']:dict(parameters=d['parameters'],result=d['result'],arguments=[n for n,t in PRIMITIVES[d['name']][0]],meaning_ja=PRIMITIVES[d['name']][1]) for d in added if d['kind']=='primitive'}
    basis=dict(status='complete_expression_of_motion_laws_connected',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives=prim,definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=[445]).document
    ann=json.loads(read(PARENT_ANNOTATIONS));ann.update(document=FULL,document_sha256=digest(body.encode()))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
