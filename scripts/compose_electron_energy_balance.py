"""Connect work, initial kinetic energy and radiative loss without erasing assumptions."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document,extract_basis
from noema.meaning_basis import audit_basis
from scripts.compose_convention_comparison import ROOT,CUT
from scripts.compose_origin_clock import definition,v
from scripts.compose_limits import call as k,app,both,op,lam,ZERO
from scripts.compose_situated_criticism import params,args

PARENT='examples/v014/einstein-kinetic-energy-chain.noema'
SOURCE='examples/v014/einstein-electron-energy-balance.noema'
LIBRARY='examples/v014/electron-energy-balance.noema'
CORE='examples/v014/electron-energy-balance-core.noema'
READING='data/electron-energy-balance-reading-v1.json'
NAMES='withdrawn initial final radiated'
BASE=[(n,'a') for n in ('episode','particle','field','frame','start','end','unit')]+[('context','d')]
VALUES=[(n,CUT) for n in NAMES.split()]
RELATIONS=[('kinetic','h[a a a a '+CUT+' d] c'),
    ('withdrawal','h[a a a a a a a '+CUT+' d] c'),('radiation','h[a a a a a a '+CUT+' d] c'),
    ('closed','h[a a a a a a a d] c')]
ALL=BASE+VALUES+RELATIONS


def definitions():
    text=''
    for real,name in ((False,'serk'),(True,'serl')):
        typ=CUT if real else 'b';fields=[(n,typ) for n in NAMES.split()]
        withdrawn,initial,final,radiated=args(fields);zero=k('bb',ZERO) if real else ZERO
        add=lambda a,b:k('bd' if real else 'ab',a,b)
        sub=lambda a,b:k('bf',a,b) if real else k('ab',a,k('ac',b))
        lt=lambda a,b:k('bg' if real else 'aa',a,b)
        eq=lambda a,b:k('sca',a,b) if real else op('e',a,b)
        text+=definition(name,params(fields),both(*([k('ba',x) for x in args(fields)] if real else []),
            *[op('u',lt(x,zero)) for x in args(fields)],eq(withdrawn,add(sub(final,initial),radiated))))
    zero=k('bb',ZERO)
    text+=definition('serm',params(VALUES),both(k('serl',*args(VALUES)),k('sca',v('initial'),zero),k('sca',v('radiated'),zero)))
    text+=definition('sern',params(VALUES),both(*[k('ba',x) for x in args(VALUES)],k('sca',v('withdrawn'),v('final'))))
    lower,upper,charge,profile,work=map(v,('lower','upper','charge','profile','work'))
    integrand=lam('position',CUT,k('shv',charge,app(profile,v('position'))))
    workfields=[(n,CUT) for n in ('lower','upper','charge','work')]+[('profile','h['+CUT+'] '+CUT)]
    text+=definition('sero',params(workfields),both(*[k('ba',v(n)) for n in ('lower','upper','charge','work')],op('x',
        both(k('sca',lower,upper),k('sca',work,zero)),op('x',
            both(k('bg',lower,upper),k('sede',lower,upper,integrand,work)),
            both(k('bg',upper,lower),k('sede',upper,lower,integrand,k('bf',zero,work)))))))
    point,frame,start,end,unit,context=map(v,('particle','frame','start','end','unit','context'))
    text+=definition('serp',params(ALL),both(
        app(v('kinetic'),point,frame,start,unit,v('initial'),context),
        app(v('kinetic'),point,frame,end,unit,v('final'),context),
        app(v('withdrawal'),*args(BASE[:-1]),v('withdrawn'),context),
        app(v('radiation'),v('episode'),point,frame,start,end,unit,v('radiated'),context),
        app(v('closed'),*args(BASE))))
    return text


MEANINGS={
    'serk':'非負の取り出したエネルギー・初期と終状態の運動エネルギー・放射量について、withdrawn=final-initial+radiatedとする有理数の収支条件。物理法則からの導出はこの数式とは分ける。',
    'serl':'serkの実切断版。同じ単位規約での数値を使い、各量を同一の対象へ帰属させる条件はserpで別に保持する。',
    'serm':'収支serlに、初期運動エネルギー零と放射量零を合わせる。片方だけから取り出した量と最終運動エネルギーの一致を補わない。',
    'sern':'同じ四数値の有効性と、取り出した量が最終運動エネルギーに等しいこと。収支や無放射をこの等式だけから逆推定しない。',
    'sero':'位置の下端から上端までcharge*profile(position)を積分した符号付き仕事。正区間は既存sede、逆方向は符号反転、零区間は値零とする。電荷も場も正に固定しない。',
    'serp':'同じ交換過程・粒子・場・基準系・開始と終了・エネルギー単位・文脈に、二状態の運動エネルギー、場から取り出す量、放射量と他の移転がない設定を結ぶ。測定記録の存在を要求しない。',
    'serq':'本文の同じ過程と四値について、帰属serpと、初期零・無放射・収支sermを推論前提として記述する内容。ゆっくりした加速から無放射を導いたとはしない。',
    'serr':'serqと同じ対象・過程・四値を保持し、取り出した量と最終運動エネルギーWの等値を述べる結論内容。',
    'sert':'同じ場から同じ粒子への取り出した量を、原点から指定位置までのepsilon*Xの仕事積分に結ぶ部分内容。軸上の軌道・初速・静電場の基礎説明は残る。',
}
LIMITS=[
    '収支は明示した前提であり、場や粒子の物理法則から証明済みとはしない。closedはこの過程で他のエネルギー移転や内部エネルギー変化がない設定を指定する入力で、一般の荷電物体へ無条件に適用しない。',
    '初期運動エネルギー零は原文の初速零に対応させる前提として置く。原点・軸上の軌道・静電力・ゆっくりした加速から無放射への因果は今回定義していない。',
    '全てのエネルギー値は同じ正の単位尺度に従う。電荷・場・長さの単位は積の積分がそのエネルギー単位に整合する規約を前提とし、任意の単位の読みを直接積分する一般化ではない。',
    '仕事積分の上下端は対象経路の両端として与える。向きの反転を扱うが、曲がった経路の線積分や非静的な場の履歴はこの一次元の式に含めない。',
    'M0425の仕事積分とu0261の無放射・等値の部分への対応である。M0427の速度積分への変数変換、全実切断の積分法則、原文全体の意味一致は未完。',
]


def build():
    old=parse((ROOT/PARENT).read_text(encoding='utf-8'));doc=deepcopy(old);doc['statements']=[]
    values={
        'zrgepisode':('a','u0261の粒子が静電場からエネルギーを受け取る運動過程。'),
        'zrgfield':('a','同じ過程でエネルギーを取り出す静電場への参照。'),
        'zrgstart':('a','原点から初速零で出発するという設定の開始出来事。軌道による接続は未完。'),
        'zrgunit':('a','同じ過程の全エネルギー数値に共通する単位。'),
        'zrgwithdrawn':(CUT,'同じ場から取り出したエネルギーの候補値。'),
        'zrginitial':(CUT,'同じ粒子の開始時の運動エネルギー。推論前提で零を要求する。'),
        'zrgradiated':(CUT,'同じ粒子・過程の放射量。推論前提で零を要求する。'),
        'zrgposition':(CUT,'原点から軸上を移動した終点の位置。符号付きの座標値。'),
        'zrgcharge':(CUT,'この位置積分の間に固定した符号付き電荷epsilon。'),
        'zrgprofile':('h['+CUT+'] '+CUT,'同じ静電場の軸方向の値Xを位置に対応させる関数。'),
        'zrgworknode':('a','u0261の場から取り出したエネルギーの積分を提示する箇所。'),
        'zrgclaimnode':('a','u0261の取り出した量を運動エネルギーに等置する箇所。'),
        'zrgreasonnode':('a','同じ箇所で無放射等の前提から等置へ進む著者の推論。'),
        'zrgscope':('a','u0261の初期静止・一次元静電場・無放射という設定の議論。')}
    for name,sort in RELATIONS:values['zrg'+name]=(sort,{
        'kinetic':'同じ粒子・系・出来事・単位・値・文脈への運動エネルギーの帰属。',
        'withdrawal':'同じ過程・粒子・場・系・開始・終了・単位・値・文脈への、場から取り出したエネルギーの帰属。',
        'radiation':'同じ過程・粒子・系・開始・終了・単位・値・文脈への放射量の帰属。',
        'closed':'同じ過程・粒子・場・系・両端・単位・文脈で、記述した取り出し・運動エネルギー変化・放射以外の移転や内部変化がない設定。'}[name])
    text=definitions()+''.join('r '+n+'[] '+sort+'.' for n,(sort,_) in values.items())
    refs=[k('zrgepisode'),k('zramatter'),k('zrgfield'),k('ra'),k('zrgstart'),k('zraevent'),k('zrgunit')]
    numbers=[k('zrgwithdrawn'),k('zrginitial'),k('zrfenergy'),k('zrgradiated')]
    binding=k('serp',*refs,v('context'),*numbers,*[k('zrg'+n) for n,_ in RELATIONS])
    for name,target in (('serq','serm'),('serr','sern')):
        text+=definition(name,'','b context['+both(binding,k(target,*numbers))+']','e')
    work=k('sero',k('bb',ZERO),k('zrgposition'),k('zrgcharge'),numbers[0],k('zrgprofile'))
    text+=definition('sert','','b context['+both(app(k('zrgwithdrawal'),*refs,numbers[0],v('context')),work)+']','e')
    doc=parse(format_graph(doc,'compact')+text)
    new=parse(format_graph(doc,'compact')+
        's[k uh[k zrgworknode[] k rd[] r[k sert[]] k zrgscope[] k ri[]]].'+
        's[k uh[k zrgclaimnode[] k rd[] r[k serr[]] k zrgscope[] k ri[]]].'+
        's[k zc[k zrgreasonnode[] k rd[] r[k serq[]] r[k serr[]] k zrgscope[] k ri[]]].')['statements']
    doc['statements']=old['statements']+new
    basis=json.loads((ROOT/'data/einstein-kinetic-energy-chain-basis-v1.json').read_text(encoding='utf-8'))
    basis.update(version='einstein-electron-energy-balance-basis-v1',document=SOURCE)
    basis['definitions'].update(MEANINGS);basis['unresolved']+=LIMITS;lookup={d['name']:d for d in doc['declarations']}
    for name,(_,meaning) in values.items():
        d=lookup[name];basis['primitives'].append(dict(symbol=name,parameters=d['parameters'],result=d['result'],arguments=[],meaning_ja=meaning))
    audit_basis(doc,basis)
    files={SOURCE:format_graph(doc,'compact')+'\n','data/einstein-electron-energy-balance-basis-v1.json':basis}
    for path,roots,indices in ((LIBRARY,['serk','serl','serm','sern','sero','serp'],[]),(CORE,[],list(range(len(old['statements']),len(old['statements'])+3)))):
        selected=extract_document(doc,roots=roots,statement_indices=indices);stem=path.rsplit('/',1)[1][:-6]
        files[path]=format_graph(selected.document,'compact')+'\n'
        files['data/'+stem+'-basis-v1.json']=extract_basis(doc,basis,selected,version=stem+'-basis-v1',document_path=path)
    return {p:t if isinstance(t,str) else json.dumps(t,ensure_ascii=False,indent=2)+'\n' for p,t in files.items()}


def main():
    for name,body in build().items():
        path=ROOT/name
        if path.exists():assert path.read_text(encoding='utf-8')==body,name
        else:
            with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(body)
        print(name,len(body),flush=True)


if __name__=='__main__':main()
