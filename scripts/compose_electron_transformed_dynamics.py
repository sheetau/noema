"""Connect the same two histories, equation (A), and the preceding law question."""
from scripts.compose_electron_comoving_equations_v2 import *
from scripts.compose_material_acceleration import AT

PARENT='examples/v014/einstein-electron-comoving-equations-v2.noema'
PARENT_BASIS='data/electron-comoving-equations-basis-v2.json'
FULL='examples/v014/einstein-electron-transformed-dynamics.noema'
CORE='examples/v014/electron-transformed-dynamics-core.noema'
BASIS='data/electron-transformed-dynamics-basis-v1.json'
ANNOTATIONS='data/electron-transformed-dynamics-identifiers-v1.json'
INDEX=421
REFERENCES={
 'eisyl':'u0250のMit Hilfeからerhaltenまで、直前の変換式を用いて同じkの運動三式をKへ移す導入箇所。',
 'eisym':'u0251のM0416にある運動三式(A)の表示箇所。',
 'eisyn':'同じ電子の初期運動について式(A)で与える法則個体への参照。内容はeld/eで全適用設定の全対応記述のviへ接続し、名前だけで法則を説明しない。',
 'eisyo':'u0251の三式全体を指す式ラベル(A)。質量又は加速度の値ではない。',
}
MEANINGS={
 'ek75':'同じ正のV=tcと瞬間速さeisxtに対する正のβで、新旧三加速度をa′x=β³ax,a′y=β²ay,a′z=β²azへ結ぶ。初期の旧速度(v,0,0)という適用条件はek63にあり、任意方向の速度へこの式を無条件適用しない。',
 'ek76':'PAIRの同じ電子・出来事・文脈・両履歴で、旧新の三速度関数と三加速度がそれぞれseppの実座標時刻微分である。新時刻へ旧時刻をそのまま流用せずnew_values()を共有する。',
 'ek77':'同じ物理設定・履歴・座標対応ek63と実二階微分ek76の下でek75を述べる条件付き加速度変換。結論を物理設定の前提に含めない。',
 'ela':'同じKの指定四点での実二場から、ax=εX/(μβ³), ay=ε(Y−vN/V)/(μβ), az=ε(Z+vM/V)/(μβ)という(A)の三行を構成する。正のμとV、0≤v<V、正のβ、各成分の有効性を要求する。',
 'elb':'同じKの数値三式elaと同じ旧速度関数の右側初期変化ek74を合わせる。elc又はek63と結ぶことで三加速度は実二階微分となり、有限時間の等加速解へ拡張しない。',
 'elc':'同じK・電子・指定出来事の代表設定ek6fに0≤v<Vの適用範囲を加える。運動三式、共動系の場の値又は法則への適合を前提にはしない。',
 'eld':'一つの固定したSETTINGの完全な運動記述が少なくとも一つあり、その全対応記述について同じlawへの適合viと同じ(A)の初期運動内容elbが同値である。都合のよい一記述だけを選ばず、適合を無条件の真にしない。',
 'ele':'同じlawと物理的contextを固定し、elcを満たすすべてのSETTINGへeldを要求する内容対応。法則の許容内容を全適用設定で(A)へ結び、法則の真理eisbiや各設定の実際の適合はこの対応からは認定しない。',
 'elf':'同じ固定設定について(A)の初期運動elbを保持し、同じlawが前の質問ek4xの候補条件ek4wを満たす。低速質量・電荷・時点・記述・系を答えの途中で選び直さない。',
 'elg':'同じ両系の設定ek63、先行kの初期三式ek7c、先行七変換式ek66を合わせる変換適用の前件。加速度の変換又は(A)を前件に追加しない。',
 'elh':'同じPAIRのelgから実二階微分の変換ek75とKの初期三式elbへ至る条件文。一般の連鎖律や原文同義性が有限検査で証明されたという主張ではない。',
 'eli':'先行の同じkの初期三式ek7mと七変換式ek7sを、同じ文脈の導出の前提として合わせる。上の運動式とこれらの変換式という二つの照応を混同しない。',
 'elj':'同じ非空の共動物理設定ek7lを保ち、その全設定で実加速度変換ek75とKの初期三式elbを得るという内容。二系の値を別の共同証人へ分離しない。',
 'elk':'同じ全共動設定に対するKの初期三式elbの閉じた内容。M0416の表示とラベル(A)はこの同じ内容を指す。',
 'ell':'一つの法則個体eisynの内容を全代表設定でeleへ固定し、同じ全共動設定でその法則が先の質問の候補elfであるとする内容。別設定ごとに違うlawを答えにしない。',
 'elm':'表示する(A)の内容elkと、前の運動法則の問いへの同じ内容を持つ候補ellを合わせる。実験による確認又は唯一の法則の発見を追加しない。',
 'eln':'著者が直前の七変換式と上のkの三式を用いてKの三式を得ると提示する。二つの照応、同じkからKへの向き、式表示と(A)の命名、先の法則探究との接続、本文順序を保つ。引用された物理内容の真理は実行しない。',
 'elo':'u0250–u0251の変換操作と得られた三式を伝える断定的メッセージ。',
 'elp':'同じ著者・論説へeloを帰属し、先行の七変換式に続ける主張421。',
}
LIMITS=[
 'u0250の一文とu0251の三行M0416を原刊918頁へ照合する。Mit Hilfeの手段、dieserの変換式照応、obigenのkの運動式照応、kからKへの向き、erhaltenの導出提示、三行の式と(A)のラベルを保持する。',
 '同じ電子eisxh・出来事eisxv・K=ra・k=eisxy・V=tc・瞬間速さeisxt・低速質量・電荷・全単位尺度を先行PAIRから共有する。旧Kの瞬間速度(v,0,0)での初期式であり、任意方向の速度や有限区間の解へ広げない。',
 'kでの実二階微分とKでの実二階微分をそれぞれseppへ結ぶ。座標変換による初期時刻変化率1/βを保ち、縦β³、横β²の係数を同じ加速度に適用する。物理設定ek63自体にはこの結論を追加しない。',
 '原刊u0246の小時間はtであるという訂正版の読解を継承する。Kの初期剰余o(Δt)、kのo(Δτ)と同じ出来事対応を保ち、座標時刻を固有時又は共通の変数へ置換しない。',
 '同じ実電磁二場は帰結の関数として最初から定義せず、同じ七式によって実新電場を旧二場の混合へ結ぶ。横方向の負号と正号、v/V、縦β³と横βを式(A)の右辺に保持する。',
 '法則の内容対応は同じlawへの全対応記述の適合viと具体的な(A)の初期条件の同値で構成する。旧GLOBAL型のeiswpをSETTINGへ流用しない。成立eisbi、法則の適用範囲、全記述への適合と前の質問ek4xの候補はek4wで別に要求する。問いの唯一解、全方向の式又は実験確認を補わない。',
 '著者が得たという提示はzc/uhと前文への照応で記述する。途中の加速度変換を意味接続として明示するが、原文に新しい表示式が印刷されているとはしない。七変換式を逆方向の座標対応にも用いてkの方程式をKの量で表す。',
 '検査は保持した有理関数軌道の解析的微分、非零の縦加速度、三軸と場の符号、全引数の接続、法則適合の全対応記述、引用の範囲を対照する。全実数・全関数域は有限列挙せず、未知入力は拒否する。物理法則の真理・連鎖律全域・原文同義性の自動証明とは区別する。',
 '後続の縦横の質量の問いと式の書換え、第十節見出しと残りの二作品全体は未完。旧421主張・規約・証拠を保持する。',
]

def definitions():
    text=''.join('r '+n+'[] a.\n' for n in REFERENCES)
    beta=k('soy',k('tc'),k('eisxt'));square=k('shv',beta,beta);cube=k('shv',square,beta)
    values=[v(n) for n,t in ACCEL]+[v('new'+n) for n,t in ACCEL]
    text+=define('ek75',PAIR,both(k('s45',k('tc'),k('eisxt')),*(k('ba',x) for x in values),*(k('sca',v('new'+n),k('shv',power,v(n))) for (n,t),power in zip(ACCEL,(cube,square,square)))))
    text+=define('ek76',PAIR,both(k('sepp',*args(AT)),k('sepp',*new_args(AT))))
    text+=define('ek77',PAIR,op('y',both(k('ek63',*args(PAIR)),k('ek76',*args(PAIR))),k('ek75',*args(PAIR))))
    point=v('point');coordinates=[coord(point,a) for a in ROLES]
    E=[app(app(v('electricfield'),k(a)),*coordinates) for a in ROLES[:3]]
    B=[app(app(v('magneticfield'),k(a)),*coordinates) for a in ROLES[:3]]
    ratio=k('shv',k('eisxt'),k('sjd',k('tc')))
    force=(E[0],k('bf',E[1],k('shv',ratio,B[2])),k('bd',E[2],k('shv',ratio,B[1])))
    right=[k('shv',k('shv',v('charge'),k('sjd',k('shv',v('mass'),power))),f) for power,f in zip((cube,beta,beta),force)]
    text+=define('ela',SETTING,both(k('s45',k('tc'),k('eisxt')),k('bc',ZERO,k('eisxt')),valid(point),*(k('ba',x) for x in [v('mass'),v('charge'),*E,*B,*args(ACCEL)]),k('bg',ZERO,v('mass')),*(k('sca',v(n),value) for (n,t),value in zip(ACCEL,right))))
    text+=define('elb',SETTING,both(k('ela',*args(SETTING)),k('ek74',*args(SETTING))))
    text+=define('elc',SETTING,both(k('ek6f',*args(SETTING)),k('s45',k('tc'),k('eisxt')),k('bc',ZERO,k('eisxt'))))
    represented=k('eisxo',v('representation'),*args(SETTING))
    text+=define('eld',SETTING+[('law','a')],both(q('g','representation','a',represented),q('f','representation','a',op('y',represented,op('z',k('vi',v('law'),v('representation'),v('context')),k('elb',*args(SETTING)))))))
    cases=[(n,t) for n,t in SETTING if n!='context']
    text+=define('ele',[('law','a'),('context','d')],quantified('f',cases,op('y',k('elc',*args(SETTING)),k('eld',*args(SETTING),v('law')))))
    text+=define('elf',SETTING+[('law','a')],both(k('elb',*args(SETTING)),k('ek4w',*args(SETTING),v('law'))))
    text+=define('elg',PAIR,both(k('ek63',*args(PAIR)),k('ek7c',*args(PAIR)),k('ek66',*args(PAIR))))
    text+=define('elh',PAIR,op('y',k('elg',*args(PAIR)),both(k('ek75',*args(PAIR)),k('elb',*shared_setting()))))
    text+=content('eli',both(op('t',k('ek7m'),v('point')),op('t',k('ek7s'),v('point'))))
    shared_old=shared()[:len(SETTING)]
    text+=content('elj',both(op('t',k('ek7l'),v('point')),quantified('f',BOUND,op('y',k('ek63',*shared()),both(k('ek75',*shared()),k('elb',*shared_old))))))
    text+=content('elk',quantified('f',BOUND,op('y',k('ek63',*shared()),k('elb',*shared_old))))
    text+=content('ell',both(k('ele',k('eisyn'),v('point')),quantified('f',BOUND,op('y',k('ek63',*shared()),k('elf',*shared_old,k('eisyn'))))))
    text+=content('elm',both(op('t',k('elk'),v('point')),op('t',k('ell'),v('point'))))
    p=v('point');who=k('rd');paper=k('eirf');scope=k('eisxg');intro=k('eisyl');display=k('eisym')
    text+=content('eln',both(k('zc',intro,who,quote('eli'),quote('elj'),scope,p),k('zc',intro,who,quote('elj'),quote('elm'),scope,p),k('uh',intro,who,quote('elm'),scope,p),k('eiswm',intro,who,k('eisyi'),quote('ek7s'),paper,p),k('eiswm',intro,who,k('eisye'),quote('ek7m'),paper,p),k('eisov',intro,who,k('eisyi'),quote('ek7s'),paper,p),k('eisd4',intro,who,k('eisx4'),k('eisxy'),paper,p),k('eisd4',intro,who,k('eisnb'),k('ra'),paper,p),k('eisra',intro,who,paper,k('eisxs'),quote('ek4y'),quote('elm'),scope,p),k('eisox',display,quote('elk'),p),k('eisch',k('eisyo'),quote('elk'),scope,p),k('uf',who,intro,display,p),k('ue',intro,display,p),op('u',op('e',intro,display))))
    text+='d elo[] f[j s[k eln[]]].\n'
    text+=define('elp',[],both(k('eir3',intro,who,paper,quote('elo'),k('ri')),k('ue',k('eisyi'),intro,k('ri')),op('u',op('e',k('eisyi'),intro))))
    return text

def shared_setting():return args(SETTING)

@lru_cache(None)
def build():
    old=parse(read(PARENT));assert len(old['statements'])==INDEX
    assert not(set(MEANINGS)|set(REFERENCES))&{d['name'] for d in old['declarations']}
    doc=deepcopy(old);doc['statements']=[];doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']+[dict(kind='assert',body=dict(kind='call',symbol='elp',arguments=[]))]
    added=doc['declarations'][len(old['declarations']):]
    prim={d['name']:dict(parameters=d['parameters'],result=d['result'],arguments=[],meaning_ja=REFERENCES[d['name']]) for d in added if d['kind']=='primitive'}
    basis=dict(status='same_histories_transformed_initial_equations_and_law_candidate',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives=prim,definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=[INDEX]).document
    ann=json.loads(read('data/electron-comoving-equations-identifiers-v2.json'));ann.update(document=FULL,document_sha256=digest(body.encode()))
    ann['entries'].append(dict(symbol='eisyo',role='designation',forms=[dict(text='(A)',language='de',role='printed_identifying_form')]))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
