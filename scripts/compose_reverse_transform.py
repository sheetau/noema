"""Use signed velocities and one scale function across two transformations."""
from copy import deepcopy
import json

from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from scripts.compose_moving_light_trip import ROOT, both
from scripts.compose_affine_time_form import CUT, PHI


def definitions():
    return '''
d sra[light b speed b beta b] c[w[k aa[n p a b v light]][w[k aa[k ad[v speed v speed] k ad[v light v light]]][w[k aa[n p a b v beta]][e[k ad[k ad[v beta v beta] k ab[k ad[v light v light] k ac[k ad[v speed v speed]]]]][k ad[v light v light]]]]]].
d srb[light b speed b beta b scale b x b y b z b time b xx b yy b zz b tt b] c[w[k sra[v light v speed v beta]][w[e[v xx][k ad[k ad[v scale v beta] k ab[v x k ac[k ad[v speed v time]]]]]][w[e[v yy][k ad[v scale v y]]][w[e[v zz][k ad[v scale v z]]][e[k ad[k ad[v light v light] v tt]][k ad[k ad[v scale v beta] k ab[k ad[k ad[v light v light] v time] k ac[k ad[v speed v x]]]]]]]]]].
d src[light b speed b beta b plus b minus b x b y b z b time b xx b yy b zz b tt b xxx b yyy b zzz b ttt b] c[w[k srb[v light v speed v beta v plus v x v y v z v time v xx v yy v zz v tt]][k srb[v light k ac[v speed] v beta v minus v xx v yy v zz v tt v xxx v yyy v zzz v ttt]]].
'''


MEANINGS={
    'sra':'正負どちらの速度も許す有理数のβ条件。V>0、v²<V²、β>0、β²*(V²-v²)=V²を要求する。',
    'srb':'符号付き速度の四座標式。時刻式の正の分母V²を払い、係数φは独立した引数で与える。',
    'src':'速度vと−vで同じ四座標式を続けて適用する。二方向のφ値は独立とし、同じβの正の枝を使う。'}


def generic_composed():
    doc=parse((ROOT/'examples/v014/spherical-wave.noema').read_text(encoding='utf-8')+definitions())
    basis=deepcopy(json.loads((ROOT/'data/spherical-wave-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='reverse-transform-basis-v1',document='examples/v014/reverse-transform.noema')
    basis['definitions'].update(MEANINGS)
    basis['unresolved']+=['相反的な二係数の積が1という条件だけから、各係数が1であるとは結論しない。']
    audit_basis(doc,basis)
    return format_graph(doc,'compact')+'\n',basis


def source_composed():
    doc=parse((ROOT/'examples/v014/einstein-spherical-wave.noema').read_text(encoding='utf-8'))
    statements,doc['statements']=doc['statements'],[]
    text=format_graph(doc,'compact')+definitions();zero='k bb[n p a b]';one='k bb[n p b b]'
    neg=lambda value:'k bf['+zero+' '+value+']'
    mul=lambda x,y:'k shv['+x+' '+y+']'
    text+='d srd[light '+CUT+' speed '+CUT+' beta '+CUT+'] c['+both('k ba[v light]','k ba[v speed]','k ba[v beta]',
        'k bg['+zero+' v light]','k bg['+mul('v speed','v speed')+' '+mul('v light','v light')+']',
        'k bg['+zero+' v beta]','k sca[v beta k soy[v light v speed]]',
        'k sca['+mul(mul('v beta','v beta'),'k bf['+mul('v light','v light')+' '+mul('v speed','v speed')+']')+' '+mul('v light','v light')+']')+'].\n'
    args='first a second a light '+CUT+' speed '+CUT+' coefficient '+PHI
    scale='c[v coefficient][v speed]'
    x,y,z,t=['k zc6[v first k '+r+'[]]' for r in ('yn','yo','yp','zc7')]
    rhs=['k spe[v light v speed '+scale+' '+x+' '+t+']','k spf['+scale+' '+y+']','k spf['+scale+' '+z+']','k spd[v light v speed '+scale+' '+x+' '+t+']']
    clauses=['k sha[v first p ba]','k sha[v second p ba]','k srd[v light v speed k soy[v light v speed]]','k ba['+scale+']']
    for role,expr in zip(('yn','yo','yp','zc7'),rhs):clauses+=['k ba['+expr+']','k sca[k zc6[v second k '+role+'[]] '+expr+']']
    text+='d sre['+args+'] c['+both(*clauses)+'].\n'
    V='k tc[]';v='k zb7[]';phi='k spc[]';p='c['+phi+']['+v+']';m='c['+phi+']['+neg(v)+']'
    text+='d srf[first a middle a last a] c[w[k sre[v first v middle '+V+' '+v+' '+phi+']][k sre[v middle v last '+V+' '+neg(v)+' '+phi+']]].\n'
    clauses=['k sha[v first p ba]','k sha[v last p ba]','k ba[v scale]']
    for role in ('yn','yo','yp','zc7'):
        expr=mul('v scale','k zc6[v first k '+role+'[]]')
        clauses+=['k ba['+expr+']','k sca[k zc6[v last k '+role+'[]] '+expr+']']
    text+='d srg[first a last a scale '+CUT+'] c['+both(*clauses)+'].\n'
    text+='d srh[] '+CUT+'['+mul(p,m)+'].\n'
    text+='r zgi[] a.r zgj[a a a '+CUT+' a a d] c.r zgk[] a.r zgl[] d.\n'
    text+='r zgm[a a i['+PHI+'] d a d] c.r zgn[] a.r zgo[] a.r zgp[] a.r zgq[] a.r zgr[] a.r zgs[] a.r zgt[] a.\n'
    text+='d sri[event a first a middle a last a setting d] c['+both('k zc4[v event]',
        'u[e[k ra[]][k zbm[]]]','u[e[k ra[]][k zgi[]]]','u[e[k zbm[]][k zgi[]]]',
        'k shd[v event v first k ra[] v setting]','k shd[v event v middle k zbm[] v setting]','k shd[v event v last k zgi[] v setting]')+'].\n'
    third='k zdz[v event k zgi[] v setting]'
    text+='d srj[event a setting d] c['+both('k smk[v event v setting]',
        'k zbv[k zgi[] k zbn[k zgi[] v setting] v setting]','k cb[v event k zbn[k zgi[] v setting] k zgi[]]',
        'k shd[v event '+third+' k zgi[] v setting]',
        *('k sca[k zc6['+third+' k '+role+'[]] '+zero+']' for role in ('yn','yo','yp','zc7')))+'].\n'
    setting='k zb6[]'
    text+='d srk[] e[b context['+both('k srj[k zgk[] '+setting+']','k sfc[k zbm[] k zgi[] '+setting+']',
        'k zgj[k zgi[] k zbm[] k zbo[k zbm[] k yn[] '+setting+'] '+neg(v)+' k ta[] k rb[] '+setting+']')+']].\n'
    tri='k sri[v event v first v middle v last '+setting+']'
    existential='g first a[g middle a[g last a['+tri+']]]'
    exists_for_all='f event a[y[k zc4[v event]]['+existential+']]'
    def all_triples(body):return 'f event a[f first a[f middle a[f last a[y['+tri+']['+body+']]]]]'
    common=['g event a[k zc4[v event]]',exists_for_all]
    for name,body in (('srl','k srf[v first v middle v last]'),('srm','k srg[v first v last k srh[]]'),('srn','k shh[v first v last]')):
        text+='d '+name+'[] e[b context['+both(*common,all_triples(body))+']].\n'
    text+='d sro[] e[b context['+both('k ba['+p+']','k ba['+m+']','k sca[k srh[] '+one+']')+']].\n'
    # Preserve the earlier remaining-candidates definition, with a new discourse stage.
    pending=deepcopy(next(d for d in doc['declarations'] if d['name']=='sqd'));pending['name']='srp'
    def change_stage(node):
        if isinstance(node,dict):
            if node.get('symbol')=='zfm':node['symbol']='zgl'
            for value in node.values():change_stage(value)
        elif isinstance(node,list):
            for value in node:change_stage(value)
    change_stage(pending)
    newdoc=parse(text);newdoc['declarations'].append(pending);text=format_graph(newdoc,'compact')
    text+='d srq[] e[b context[w[t[k srk[]][v context]][t[k srl[]][v context]]]].\n'
    # At least one component; the all-zero origin cannot determine a scale.
    clauses=['u[k sca[k zc6[v first k '+role+'[]] '+zero+']]' for role in ('yn','yo','yp','zc7')]
    nonzero=clauses[-1]
    for clause in reversed(clauses[:-1]):nonzero='x['+clause+']['+nonzero+']'
    witness='g event a[g first a[g middle a[g last a[w['+tri+']['+nonzero+']]]]]'
    text+='d srr[] e[b context['+both('t[k srm[]][v context]','t[k srn[]][v context]',witness)+']].\n'
    text+='d srs[] e[b context[w[k x4[k zgi[] k ra[] '+setting+']][k x4[k ra[] k zgi[] '+setting+']]]].\n'
    doc=parse(text);doc['statements']=statements
    doc=parse(format_graph(doc,'compact')+'''
s[k uh[k zgt[] k rd[] r[k srp[]] k rh[] k ri[]]].
s[k zgm[k zgn[] k rd[] r[k spc[]] k zgl[] k rh[] k ri[]]].
s[k ug[k zgo[] k rd[] r[k srk[]] k rh[] k ri[]]].
s[k zc[k zgp[] k rd[] r[k srq[]] r[k srm[]] k rh[] k ri[]]].
s[k zc[k zgq[] k rd[] r[k srm[]] r[k srs[]] k rh[] k ri[]]].
s[w[k zc[k zgr[] k rd[] r[k srs[]] r[k srn[]] k rh[] k ri[]]][k zdg[k zgr[] k rd[] r[k srn[]] k rh[] k ri[]]]].
s[k zc[k zgs[] k rd[] r[k srr[]] r[k sro[]] k rh[] k ri[]]].
''')
    basis=deepcopy(json.loads((ROOT/'data/einstein-spherical-wave-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='einstein-reverse-transform-basis-v1',document='examples/v014/einstein-reverse-transform.noema')
    basis['definitions'].update(MEANINGS|{
        'srd':'実切断の符号付き速度で正のβを指定する。正速度に限定したspaを変更せず、負速度を受ける後続条件として追加する。',
        'sre':'指定した速度と同じ係数関数から四座標式を作る。負速度でも同じ関数を評価し、符号反転で同じφ値になることは仮定しない。',
        'srf':'同じ中間記録を挟み、vと−vで四式を二回適用する。両方とも正規化後の同じ関数spcを使う。',
        'srg':'二つの有効な四座標記録を、全成分に共通する倍率で結ぶ。元の空間成分に時刻項は混ぜない。',
        'srh':'同じ正規化後のφをvと−vで評価した積。両値の同一性は要求しない。',
        'sri':'異なる三基準系で、同じ一つの対象出来事が三つの記録を持つ。測定単位は先行するshdの規約を維持する。',
        'srj':'既出の両系の共通原点・零時刻に、第三系の原点と四座標零を結ぶ。第三系の時刻だけを省かない。',
        'srk':'第三系が運動系に対してその縦軸上を−vで平行並進し、三原点と三零時刻が一致する設定内容。',
        'srl':'対象出来事の範囲は非空で、全出来事に三系の記録が存在し、全対応三記録で二回の変換式が成立する。',
        'srm':'同じ全域と全三記録に対し、最後の記録が最初の記録のφ(v)φ(−v)倍になるという内容。',
        'srn':'同じ全域の三系の記録について最初と最後の四座標値が一致する。記録識別子の同一性は要求しない。',
        'sro':'φ(v)とφ(−v)は有効な値で、その積が1である。個々が1であるとはしない。',
        'srp':'係数を決める議論へ移ったu0092の段階でも、先行する正速度域で異なる候補関数が残る。負速度全域の候補集合を勝手に確定しない。',
        'srq':'第三系の設定と全三記録への二回適用を、共通倍率の結論の前提として合わせる。',
        'srr':'共通倍率と恒等性に、少なくとも一成分が非零の実測記録の存在を加えた積1への前提。零の原点だけから係数を決めない。',
        'srs':'第三系と初めの静止系が互いに静止しているという内容。単位・軸尺度・時計率の校正が一致することとは区別する。'})
    decls={d['name']:d for d in doc['declarations']}
    for name,args,meaning in (
        ('zgi',[],'再変換に導入する第三の座標系K′。初めのKと個体同一とはしない。'),
        ('zgj',['moving_frame','reference_frame','axis','signed_speed','length_unit','time_unit','setting'],'指定した参照系の軸上を運動系原点が符号付きの一定速度で進み、全系が同じ速度で平行並進する。単位を明示する測定関係であり、全軌道からの構成は未完。'),
        ('zgk',[],'三系の原点と時刻零を重ねる放出等に限定しない基準出来事。'),
        ('zgl',[],'未知係数を決定する議論へ移るu0092の段階。'),
        ('zgm',['node','author','function_description','stage','scope','context'],'著者が指定した関数の記述を対象として、その値を決定する意図を示す。決定済み・唯一解・計算手段を含意しない。'),
        ('zgn',[],'未知のφをこれから定める意図を示す箇所。'),
        ('zgo',[],'第三系の−vの並進と三原点・零時刻を設定する箇所。'),
        ('zgp',[],'変換を二回適用して共通倍率を得る箇所。'),
        ('zgq',[],'空間変換に時刻が現れないことから相対静止を述べる箇所。'),
        ('zgr',[],'相対静止から恒等変換であることを明らかとする箇所。'),
        ('zgs',[],'共通倍率と恒等性からφ(v)φ(−v)=1を得る箇所。'),
        ('zgt',[],'変換式にまだ未知の関数が残るとする箇所。')):
        d=decls[name];basis['primitives'].append(dict(symbol=name,parameters=d['parameters'],result=d['result'],arguments=args,meaning_ja=meaning))
    basis['unresolved']+=[
        'u0092〜u0096の部分記述。符号付きの三系の運動、全空間・全速度での測定、原刊照合と原文の意味一致は未完。',
        '相対静止と共通零点だけから、単位・軸尺度・時計率まで等しい恒等変換は導かない。u0095のその推論と明白さは著者への帰属とし、校正条件の論証は未完とする。',
        '積1には零でない記録が必要という十分前提をsrrで明示した。原文がその証人を逐語的に指定したことは主張しない。',
        '逆速度での関数値の有効性は二回適用の条件で要求する。先行する正速度域の未知性だけから負速度全域の値を補わない。',
        'φ(v)φ(−v)=1から各値1は従わない。横向きの棒と速度反転の対称性、符号の規約、全実切断の体の一般法則は後続の課題。']
    audit_basis(doc,basis)
    return format_graph(doc,'compact')+'\n',basis


def main():
    for compose,name in ((generic_composed,'reverse-transform'),(source_composed,'einstein-reverse-transform')):
        text,basis=compose()
        for filename,body in ((basis['document'],text),('data/'+name+'-basis-v1.json',json.dumps(basis,ensure_ascii=False,indent=2)+'\n')):
            path=ROOT/filename
            if path.exists():
                if path.read_text(encoding='utf-8')!=body:raise ValueError('Stored reverse transform differs: '+filename)
            else:
                with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(body)
    print('Signed reverse transform and reciprocal scale condition composed')


if __name__=='__main__':main()
