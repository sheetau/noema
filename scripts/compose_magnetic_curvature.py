"""Define local spatial curvature and retain the printed magnetic orientation."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document,extract_basis
from noema.meaning_basis import audit_basis
from scripts.compose_convention_comparison import ROOT,CUT
from scripts.compose_origin_clock import definition,v
from scripts.compose_limits import call as k,app,both,op,ZERO
from scripts.compose_situated_criticism import params,args
from scripts.compose_material_acceleration import AT,PROFILES,ACCEL,coord,ROLES
from scripts.compose_field_equations import FIELD,REGION

PARENT='examples/v014/einstein-potential-speed.noema'
SOURCE='examples/v014/einstein-magnetic-curvature.noema'
LIBRARY='examples/v014/magnetic-curvature.noema'
CORE='examples/v014/magnetic-curvature-core.noema'
READING='data/magnetic-curvature-reading-v1.json'
GEOMETRY='vx vy vz ax ay az radius'
NUMERIC='light speed beta mass charge magnetic acceleration radius'
LOCAL=AT+[('radius',CUT)]
SETTING=LOCAL+[(n,CUT) for n in ('speed','magnetic')]+[('electricfield',FIELD),('magneticfield',FIELD),('region',REGION),('only','h[a a a '+FIELD+' d] c')]


def definitions():
    text=''
    for real,geometry,chain,formula,general in ((False,'sevb','seve','sevg','sevi'),(True,'sevc','sevf','sevh','sevj')):
        typ=CUT if real else 'b';zero=k('bb',ZERO) if real else ZERO
        fields=lambda names:[(n,typ) for n in names.split()]
        valid=lambda values:[k('ba',x) for x in values] if real else []
        mul=lambda a,b:k('shv' if real else 'ad',a,b)
        add=lambda a,b:k('bd' if real else 'ab',a,b)
        sub=lambda a,b:k('bf',a,b) if real else add(a,k('ac',b))
        lt=lambda a,b:k('bg' if real else 'aa',a,b)
        eq=lambda a,b:k('sca',a,b) if real else op('e',a,b)
        sq=lambda a:mul(a,a)
        dot=lambda a,b:add(add(mul(a[0],b[0]),mul(a[1],b[1])),mul(a[2],b[2]))
        velocity=list(map(v,('vx','vy','vz')));acceleration=list(map(v,('ax','ay','az')));R=v('radius')
        S=dot(velocity,velocity);A=dot(acceleration,acceleration);D=dot(velocity,acceleration)
        cross=sub(mul(S,A),sq(D))
        text+=definition(geometry,params(fields(GEOMETRY)),both(*valid(args(fields(GEOMETRY))),lt(zero,S),lt(zero,cross),lt(zero,R),
            eq(mul(sq(R),cross),mul(sq(S),S))))
        V,s,b,m,q,N,a,R=map(v,NUMERIC.split());law=k('setk' if real else 'setj',V,s,b,m,q,zero,N,a)
        text+=definition(chain,params(fields(NUMERIC)),both(*valid([R]),law,lt(zero,s),lt(zero,R),eq(mul(sub(zero,a),R),sq(s))))
        reduced='light speed beta mass charge magnetic radius'
        text+=definition(formula,params(fields(reduced)),both(*valid(args(fields(reduced))),k('srd' if real else 'sra',V,s,b),
            lt(zero,m),lt(zero,s),lt(zero,R),lt(zero,mul(q,N)),eq(mul(R,mul(q,N)),mul(mul(m,b),mul(V,s)))))
        text+=definition(general,params(fields(NUMERIC)),both(law,k(geometry,s,zero,zero,zero,a,zero,R)))
    time=coord(v('point'),'zc7');velocity=[app(v(n),time) for n,_ in PROFILES]
    text+=definition('sevd',params(LOCAL),both(k('sepp',*args(AT)),k('sevc',*velocity,*args(ACCEL),v('radius'))))
    zero=k('bb',ZERO);point=v('point');coordinates=[coord(point,axis) for axis in ROLES]
    field_at=lambda name,axis:app(app(v(name),k(axis)),*coordinates)
    conditions=[k('sevd',*args(LOCAL)),k('va',v('frame')),
        k('znn',v('frame'),v('electricfield'),v('magneticfield'),v('region'),v('context')),
        app(v('region'),*coordinates),app(v('only'),v('matter'),v('frame'),v('event'),v('magneticfield'),v('context')),
        k('sca',velocity[0],v('speed')),k('bg',zero,v('speed')),k('sca',velocity[1],zero),k('sca',velocity[2],zero),k('sca',v('az'),zero)]
    # Only the normal force is restricted. Tangential acceleration and Ex need
    # not vanish to calculate an instantaneous curvature radius.
    conditions += [k('ba',field_at('electricfield','yn'))]
    conditions += [k('sca',field_at('electricfield',axis),zero) for axis in ROLES[1:3]]
    conditions += [k('sca',field_at('magneticfield',axis),zero if i<2 else v('magnetic')) for i,axis in enumerate(ROLES[:3])]
    text+=definition('sevk',params(SETTING),both(*conditions))
    return text


MEANINGS={
    'sevb':'ユークリッド三空間の速度u、加速度aから、S=u・u、C=S(a・a)-(u・a)^2としてR^2*C=S^3を満たす正の曲率半径を定める有理数の関係。SとCを正とし、静止と曲率零を有限の半径へ押し込まない。',
    'sevc':'sevbの実切断版。接線方向の加速度も含め、法線方向だけから曲率を決める。',
    'sevd':'同じ物質点・基準系・出来事の座標履歴と一階・二階微分seppへ、三次元の局所曲率sevcを結ぶ。軌道全体が円であるとは述べない。',
    'seve':'非零の正の速度・半径について、磁場だけの横方向運動方程式と-a_y*R=v^2を保持する有理数の等号列。原文の負のy方向への向きを保つ。',
    'sevf':'seveの実切断版。qNが負で曲がる方向が反対なら、この原文の向きの式は成立しない。',
    'sevg':'正の質量・光速度・速度・半径と正規化beta、qN>0の下でR*q*N=mu*beta*V*vとなる有理数の式。非零分母と符号条件を保存したM0442の形。',
    'sevh':'sevgの実切断版。符号を捨てた半径の式へ原文を黙って置き換えない。',
    'sevi':'磁場だけの横方向方程式と、方向を問わない幾何学的半径を合わせる有理数の関係。逆向きに曲がる例を原文の方向条件から分ける。',
    'sevj':'seviの実切断版。電荷と磁場の積が負でも正の曲率半径を保持できる。',
    'sevk':'同じ履歴・系・時刻で速度をx方向、磁場をz方向に取り、横電場を零にして磁場だけが偏向の原因である設定を明示する。既存znnで場を割り当て、接線加速度と縦電場の存在は排除しない。',
    'sevl':'本文の同じ電子・系Kと新しい磁場の事例について、sevkの軌道・場・半径を結ぶ内容。前段の静電加速の軌道とは同一視しない。',
    'sevm':'本文の設定sevlに、原文M0441の向き付きの式sevfを結ぶ。',
    'sevn':'本文の設定sevlに、原文M0442の半径式sevhを結ぶ。',
    'sevo':'同じ設定、横方向の運動方程式、qN>0という座標の向きを保持した導出候補の前提。',
}
LIMITS=[
    'Rは正の幾何学的な半径である。原文の-a_y=v^2/Rは負のy側へ曲がる座標の選び方を含むと読む。反対向きの運動には一般定義sevi/sevjを使い、原文の符号を変更しない。',
    '局所曲率を座標時刻の一階・二階微分で構成する。全軌道が円であること、磁場が空間全域で一様であること、速度が時間的に一定であることは推定しない。',
    'onlyは同じ事例で磁場以外の偏向原因がないという明示的な物理的入力である。横電場が零であることだけからこの排他条件を補わない。縦方向の運動方程式はこの記述の対象外。',
    '三空間座標は同じ長さ尺度、時刻は同じ時間尺度、場・電荷・質量は原文の式と整合する単位を前提とする。測定・校正、電磁的な力の基礎説明と幾何学的な接触円による特徴づけは残る。',
    '解析的な多項式の微分モデルと有理数の一般命題を検査する。全実切断の微分法則と曲率公式の同値の機械的証明、原文全体の意味一致は未完。',
]


def build():
    old=parse((ROOT/PARENT).read_text(encoding='utf-8'));doc=deepcopy(old);doc['statements']=[]
    fixed={'matter':k('zramatter'),'frame':k('ra'),'context':v('context'),'speed':k('zb7'),'az':k('bb',ZERO)}
    values={'zro'+n:(sort,'u0271の磁場中の軌道の'+n+'への参照。') for n,sort in SETTING if n not in fixed}
    values.update({'zro'+n:('a','u0271からu0274の'+n+'への参照。') for n in ('chainnode','radiusnode','reasonnode','reformnode','scope')})
    values['zroonly']=(dict(SETTING)['only'],'同じ物質点・系・出来事・磁場・文脈で、この磁場以外の偏向原因がないという明示条件。')
    extra=definitions()+''.join('r '+n+'[] '+sort+'.' for n,(sort,_) in values.items())
    binding=k('sevk',*[fixed.get(n,k('zro'+n)) for n,_ in SETTING])
    content=lambda n:'t['+k(n)+']['+v('context')+']'
    numbers=[k('tc'),k('zb7'),k('soy',k('tc'),k('zb7')),k('zramu'),k('zrgcharge'),k('zromagnetic'),k('zroay'),k('zroradius')]
    formulas={'sevl':binding,'sevm':both(content('sevl'),k('sevf',*numbers)),
        'sevn':both(content('sevl'),k('sevh',*numbers[:6],numbers[7])),
        'sevo':both(content('sevl'),k('setk',*numbers[:5],k('bb',ZERO),*numbers[5:7]),k('bg',k('bb',ZERO),k('shv',numbers[4],numbers[5])))}
    for n,formula in formulas.items():extra+=definition(n,'','b context['+formula+']','e')
    doc=parse(format_graph(doc,'compact')+extra)
    statements=''.join('s[k uh[k zro'+node+'[] k rd[] r[k '+target+'[]] k zroscope[] k ri[]]].' for node,target in [('chainnode','sevm'),('radiusnode','sevn')])
    statements+=''.join('s[k zc[k zro'+node+'[] k rd[] r[k '+premise+'[]] r[k '+conclusion+'[]] k zroscope[] k ri[]]].' for node,premise,conclusion in [('reasonnode','sevo','sevm'),('reformnode','sevm','sevn')])
    doc['statements']=old['statements']+parse(format_graph(doc,'compact')+statements)['statements']
    basis=json.loads((ROOT/'data/einstein-potential-speed-basis-v1.json').read_text(encoding='utf-8'))
    basis.update(version='einstein-magnetic-curvature-basis-v1',document=SOURCE);basis['definitions'].update(MEANINGS);basis['unresolved']+=LIMITS
    lookup={d['name']:d for d in doc['declarations']}
    for n,(_,meaning) in values.items():
        d=lookup[n];basis['primitives'].append(dict(symbol=n,parameters=d['parameters'],result=d['result'],arguments=[],meaning_ja=meaning))
    audit_basis(doc,basis)
    files={SOURCE:format_graph(doc,'compact')+'\n','data/einstein-magnetic-curvature-basis-v1.json':basis}
    for path,roots,indices in ((LIBRARY,list(MEANINGS)[:10],[]),(CORE,['sevb','seve','sevg','sevi','sevj'],list(range(len(old['statements']),len(doc['statements']))))):
        selected=extract_document(doc,roots=roots,statement_indices=indices);stem=path.rsplit('/',1)[1][:-6]
        files[path]=format_graph(selected.document,'compact')+'\n'
        files['data/'+stem+'-basis-v1.json']=extract_basis(doc,basis,selected,version=stem+'-basis-v1',document_path=path)
    return {p:x if isinstance(x,str) else json.dumps(x,ensure_ascii=False,indent=2)+'\n' for p,x in files.items()}


def main():
    for p,body in build().items():
        path=ROOT/p
        if path.exists():assert path.read_text(encoding='utf-8')==body,p
        else:
            with path.open('x',encoding='utf-8',newline='\n') as f:f.write(body)
        print(p,len(body),flush=True)


if __name__=='__main__':main()
