"""Collect four coordinates while preserving the changed coefficient meaning."""
from copy import deepcopy
import json

from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from scripts.compose_moving_light_trip import ROOT, both
from scripts.compose_affine_time_form import CUT, TAU, PHI


def rational_definitions():
    return '''
d sor[light b speed b component b beta b] c[w[k sla[v light v speed v component]][w[k aa[n p a b v beta]][e[k ad[v component v beta]][v light]]]].
d sos[oldscale b scale b beta b] c[w[k aa[n p a b v beta]][e[v scale][k ad[v oldscale v beta]]]].
d sot[light b speed b scale b beta b inverse b x b time b] b[k ad[k ad[v scale v beta] k ab[v time k ac[k ad[k ad[v speed v inverse] v x]]]]].
d sou[speed b scale b beta b x b time b] b[k ad[k ad[v scale v beta] k ab[v x k ac[k ad[v speed v time]]]]].
d sov[scale b coordinate b] b[k ad[v scale v coordinate]].
d spt[left h[a] c right h[a] c relation h[a a] c same h[a a] c] c[f first a[f second a[f other a[y[w[c[v left][v first]][w[c[v right][v second]][w[c[v right][v other]][w[c[v relation][v first v other]][c[v same][v second v other]]]]]][c[v relation][v first v second]]]]]].
'''


def calibration_definition():
    row=lambda args:'k sld[v cx v cy v cz v ct v offset '+' '.join(args)+']'
    z='n p a b';one='n p b b'
    args='light b speed b component b cx b cy b cz b ct b offset b longitudinal b transversey b transversez b'
    return 'd sow['+args+'] c['+both('k sla[v light v speed v component]',
        'e['+row((z,z,z,z))+']['+z+']','e['+row(('v speed',z,z,one))+']['+z+']',
        'e['+row(('v light',z,z,one))+'][v longitudinal]',
        'e['+row(('v speed','v component',z,one))+'][v transversey]',
        'e['+row(('v speed',z,'v component',one))+'][v transversez]')+'].\n'+'''
d sox[speed b longitudinal b transversey b transversez b longitudinalinverse b transverseinverse b x b y b z b time b] b[k ab[k ad[k ad[v longitudinal v longitudinalinverse] k ab[v x k ac[k ad[v speed v time]]]] k ab[k ad[k ad[v transversey v transverseinverse] v y] k ad[k ad[v transversez v transverseinverse] v z]]]].
'''


MEANINGS={
    'sor':'本文のβ=V/√(V²-v²)を正の横成分との積で結ぶ有理数の条件。βをv/Vとして使わない。',
    'sos':'新しい係数φの値が先行するaと正のβの積であるという再表示。aとφを同じ値に固定しない。',
    'sot':'φ*β*(t-v*x/V²)の有理数の式。inverseはV²の逆数を呼出側で与える。',
    'sou':'φ*β*(x-v*t)の有理数の式。',
    'sov':'横座標に共通するφとの積。',
    'spt':'同じ入力に対応する出力記録を、同じ座標値の別記録に替えても対応が成立するという追加条件。記録識別子に依存する対応を、値だけの方程式と同一視しない。',
    'sow':'空間座標の一行のアフィン式に、零点、運動原点の一単位後、三方向の光の一単位後の値を指定する十分条件。原文に全て明記された前提とはしない。',
    'sox':'sowの五つの値に合う空間座標の行。横成分とV-vの正の逆数を呼出側が結ぶ。',
}


def generic_composed():
    doc=parse((ROOT/'examples/v014/transverse-space.noema').read_text(encoding='utf-8')+rational_definitions()+calibration_definition())
    basis=deepcopy(json.loads((ROOT/'data/transverse-space-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='four-coordinates-basis-v1',document='examples/v014/four-coordinates.noema')
    basis['definitions'].update(MEANINGS)
    basis['unresolved']+=['光線から全座標への拡張には、共通のアフィン係数と運動原点の条件を追加して十分条件を明示する。実際の測定全域でそれらが成立することは別に必要。']
    audit_basis(doc,basis)
    return format_graph(doc,'compact')+'\n',basis


def source_composed():
    doc=parse((ROOT/'examples/v014/einstein-transverse-space.noema').read_text(encoding='utf-8'))
    statements,doc['statements']=doc['statements'],[]
    text=format_graph(doc,'compact')+rational_definitions()+calibration_definition()
    zero='k bb[n p a b]';one='k bb[n p b b]'
    text+='d soy[light '+CUT+' speed '+CUT+'] '+CUT+'[k sje[v light k sle[v light v speed]]].\n'
    ratio='k sje[v speed v light]'
    text+='d soz[light '+CUT+' speed '+CUT+'] '+CUT+'[k sjd[k sky[k bf['+one+' k shv['+ratio+' '+ratio+']]]]].\n'
    text+='d spa[light '+CUT+' speed '+CUT+' beta '+CUT+'] c['+both('k skz[v light v speed k sle[v light v speed]]',
        'k ba[v beta]','k bg['+zero+' v beta]','k sca[v beta k soy[v light v speed]]','k sca[v beta k soz[v light v speed]]')+'].\n'
    text+='d spb[light '+CUT+' coefficient '+PHI+'] '+PHI+'[i[speed '+CUT+'][k shv[c[v coefficient][v speed] k soy[v light v speed]]]].\n'
    text+='d spc[] '+PHI+'[k spb[k tc[] k zeq[]]].\n'
    text+='d spd[light '+CUT+' speed '+CUT+' scale '+CUT+' x '+CUT+' time '+CUT+'] '+CUT+'[k shv[k shv[v scale k soy[v light v speed]] k bf[v time k shv[k sje[v speed k shv[v light v light]] v x]]]].\n'
    text+='d spe[light '+CUT+' speed '+CUT+' scale '+CUT+' x '+CUT+' time '+CUT+'] '+CUT+'[k shv[k shv[v scale k soy[v light v speed]] k sin[v speed v x v time]]].\n'
    text+='d spf[scale '+CUT+' coordinate '+CUT+'] '+CUT+'[k shv[v scale v coordinate]].\n'
    V='k tc[]';v='k zb7[]';old='c[k zeq[]]['+v+']';new='c[k spc[]]['+v+']'
    coords={role:'k zc6[v first k '+role+'[]]' for role in ('yn','yo','yp','zc7')}
    x,y,z,t=[coords[role] for role in ('yn','yo','yp','zc7')];xp='k sin['+v+' '+x+' '+t+']'
    earlier=['k smh['+V+' '+v+' '+old+' '+xp+' '+t+']','k snb['+V+' '+v+' '+old+' '+xp+']',
        'k sob['+V+' '+v+' '+old+' '+y+']','k sob['+V+' '+v+' '+old+' '+z+']']
    normalized=['k spd['+V+' '+v+' '+new+' '+x+' '+t+']','k spe['+V+' '+v+' '+new+' '+x+' '+t+']',
        'k spf['+new+' '+y+']','k spf['+new+' '+z+']']
    for name,expressions in (('spg',normalized),('sph',earlier)):
        clauses=['k sha[v first p ba]','k sha[v second p ba]','k spa['+V+' '+v+' k soy['+V+' '+v+']]','k ba['+old+']','k ba['+new+']']
        for role,expression in zip(('zc7','yn','yo','yp'),expressions):clauses+=['k ba['+expression+']','k sca[k zc6[v second k '+role+'[]] '+expression+']']
        text+='d '+name+'[first a second a] c['+both(*clauses)+'].\n'
    text+='d spi[equations h[a a] c] c['+both('k sgw[p shf p shg p she p shh]',
        'f first a[f second a[y[w[k shf[v first]][k shg[v second]]][z[c[v equations][v first v second]][k she[v first v second]]]]]')+'].\n'
    text+='d spj[] e[b context[k spi[p sph]]].\n'
    text+='d spk[] e[b context[k spi[p spg]]].\n'
    # Explicit sufficient calibration premises, distinguished from source text.
    args='function '+TAU+' role a light '+CUT+' speed '+CUT+' scale '+CUT
    w='k sle[v light v speed]'
    probes=[(zero,zero,zero,zero),('v speed',zero,zero,one),('v light',zero,zero,one),('v speed',w,zero,one),('v speed',zero,w,one)]
    evaluated=['c[v function]['+' '.join(p)+']' for p in probes]
    roles=('yn','yo','yp')
    clauses=['x[e[v role][k yn[]]][x[e[v role][k yo[]]][e[v role][k yp[]]]]',
        *('u[e[k '+r+'[]][k '+s+'[]]]' for i,r in enumerate(roles) for s in roles[i+1:]),
        'k skz[v light v speed '+w+']','k ba[v scale]',*('k ba['+p+']' for p in evaluated),
        'k sca['+evaluated[0]+' '+zero+']','k sca['+evaluated[1]+' '+zero+']']
    for role,p,expected in zip(roles,evaluated[2:],('k snb[v light v speed v scale k sna[v light v speed]]','k shv[v scale v light]','k shv[v scale v light]')):
        clauses+=['y[e[v role][k '+role+'[]]][k sca['+p+' '+expected+']]',
            'y[u[e[v role][k '+role+'[]]]][k sca['+p+' '+zero+']]']
    text+='d spl['+args+'] c['+both(*clauses)+'].\n'
    coefficients=('cx','cy','cz','ct','offset')
    body=both('k smd[v function '+' '.join('v '+c for c in coefficients)+']','k spl[v function v role v light v speed v scale]')
    for name in reversed(coefficients):body='g '+name+' '+CUT+'['+body+']'
    text+='d spm['+args+'] c['+body+'].\n'
    expression='c[v function]['+' '.join(coords[r] for r in ('yn','yo','yp','zc7'))+']'
    text+='d spn[function '+TAU+' role a] c[f first a[f second a[y[k she[v first v second]]['+both('k ba['+expression+']','k sca['+expression+' k zc6[v second v role]]')+']]]].\n'
    text+='r zfh[a] '+TAU+'.r zfi[] a.r zfj[] a.r zfk[] a.r zfl[a a i[e] i[e] a d] c.\n'
    selected='x[e[v role][k yn[]]][x[e[v role][k yo[]]][e[v role][k yp[]]]]'
    text+='d spo[] e[b context['+both('t[k shi[]][v context]','k spt[p shf p shg p she p shh]',
        'k sio[k zd4[]]','k smj[k zd4[] k zeq[] '+V+' '+v+']',
        'f role a[y['+selected+']['+both('k spm[k zfh[v role] v role '+V+' '+v+' '+old+']','k spn[k zfh[v role] v role]')+']]')+']].\n'
    text+='d spq[] e[b context[k spa['+V+' '+v+' k soy['+V+' '+v+']]]].\n'
    text+='d spr[] e[b context[w[t[k spj[]][v context]][t[k spq[]][v context]]]].\n'
    doc=parse(text);doc['statements']=statements
    doc=parse(format_graph(doc,'compact')+'''
s[k zfl[k zfi[] k rd[] r[k spo[]] r[k spj[]] k rh[] k ri[]]].
s[k zd3[k zfj[] k rd[] r[k spr[]] r[k spj[]] r[k spk[]] k rh[] k ri[]]].
s[k uh[k zfk[] k rd[] r[k spq[]] k rh[] k ri[]]].
''')
    basis=deepcopy(json.loads((ROOT/'data/einstein-transverse-space-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='einstein-four-coordinates-basis-v1',document='examples/v014/einstein-four-coordinates.noema')
    basis['definitions'].update(MEANINGS|{
        'soy':'正の横成分から作る本文のβ=V/√(V²-v²)。',
        'soz':'本文の表示どおりのβ=1/√(1-(v/V)²)。定義域とsoyとの一致をspaで要求する。',
        'spa':'0≤v<Vのもとで正のβと二つの平方根表示を結ぶ。現代に使われるv/Vというβの慣習を代入しない。',
        'spb':'速度関数aを、同じ速度のβとの積φへ写す。aの未知性を特定値で埋めない。',
        'spc':'この四座標の式でのφ。先行するa=zeqとは別の関数で、φ(v)=a(v)*β(v)として接続する。',
        'spd':'新しいφによるτ=φβ(t-v*x/V²)の実切断の式。',
        'spe':'新しいφによるξ=φβ(x-v*t)の実切断の式。',
        'spf':'ηとζに共通するφと元の横座標との積。',
        'spg':'同じ二つの有効な座標記録について、同じV,v,φで四つの正規化後の式を全て要求する。原点定数は零の版である。',
        'sph':'同じ二記録に対する先行係数aの四式。x′を同じx-v*tで置き換える。',
        'spi':'指定範囲の座標対応が非空で関数的であり、全記録対で四式の成立と同じ出来事の対応が過不足なく一致する。',
        'spj':'全指定記録対で、先行係数aによる四座標の式が同じ出来事の対応を記述する内容。',
        'spk':'全指定記録対で、新しいφとβによる四座標の式が同じ出来事の対応を記述する内容。',
        'spl':'空間成分の候補関数について、零点、運動原点の一単位後、三軸の光の一単位後の五つの値を指定する追加の十分条件。単位は先行設定に固定する。',
        'spm':'同じ五つの値を持つ空間成分の候補が、一組の係数で全入力を表すアフィン関数であるという追加前提。',
        'spn':'同じ出来事に対応する二記録について、候補空間成分の値を運動系記録の指定成分へ結ぶ。',
        'spo':'先行するτの式、非空で関数的な座標対応、同じ値の出力記録への置換の許容、空間三成分のアフィン表示・五つの値・測定への接続を明示した拡張前提。',
        'spq':'本文のβの定義と、その正の横成分による同値表示という内容。',
        'spr':'係数の再表示とx′の置換を行うための、先行する四式とβの定義という前提内容。'})
    decls={d['name']:d for d in doc['declarations']}
    for name,args,meaning in (
        ('zfh',['coordinate_role'],'指定した空間成分の、静止系四座標を引数とする候補関数。実際の記録との一致はspnで要求する。'),
        ('zfi',[],'光線上の式を四座標の関係へまとめる際に補う、十分条件の解釈注記。'),
        ('zfj',[],'x′の値を戻し四座標の式をまとめる本文箇所。'),
        ('zfk',[],'本文のβの式を指定する箇所。'),
        ('zfl',['node','source_author','additional_premise','conclusion','scope','context'],'本文の推論を指定した追加前提による十分条件として明示化する部分解釈。著者が追加条件を全て述べたことも、その実世界での成立も含意しない。')):
        d=decls[name];basis['primitives'].append(dict(symbol=name,parameters=d['parameters'],result=d['result'],arguments=args,meaning_ja=meaning))
    basis['unresolved']+=generic_composed()[1]['unresolved'][-1:]+[
        'u0081〜u0084の部分記述。前のa=φ(v)という表記から、この四式のφへはφ=a*βという再表示が必要であり、同じ文字を同じ識別子にしない。',
        '空間成分のアフィン性と五つの値を、全座標への拡張の十分条件として補った。任意の光線の測定や原点の静止からこれらを一般的に導く証明は未完。',
        'spnだけでは方程式の解から記録の対応へ戻れないため、shiの存在性とsptの値による置換条件を拡張前提へ加えた。実際の記録範囲での成立や、同じ座標を持つ異なる出来事の同一視の妥当性は未確認。',
        '有理数のアフィン係数の一意性は検査するが、一般の実切断での体の法則と全空間の関数の一意性の機械的証明とは区別する。',
        'u0085の原点条件を外した加法定数と、その段階での未知性の記述、原刊照合、全文の意味一致は未完。']
    audit_basis(doc,basis)
    return format_graph(doc,'compact')+'\n',basis


def main():
    for compose,name in ((generic_composed,'four-coordinates'),(source_composed,'einstein-four-coordinates')):
        text,basis=compose()
        for filename,body in ((basis['document'],text),('data/'+name+'-basis-v1.json',json.dumps(basis,ensure_ascii=False,indent=2)+'\n')):
            path=ROOT/filename
            if path.exists():
                if path.read_text(encoding='utf-8')!=body:raise ValueError('Stored four coordinates differ: '+filename)
            else:
                with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(body)
    print('Four coordinate equations and the changed coefficient meaning composed')


if __name__=='__main__':main()
