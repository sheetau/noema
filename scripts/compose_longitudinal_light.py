"""Bind the longitudinal light-ray substitutions to the same two-frame events."""
from copy import deepcopy
import json

from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from scripts.compose_moving_light_trip import ROOT, both
from scripts.compose_affine_time_form import CUT


def rational_definitions():
    return '''
d smx[light b speed b xprime b time b] c[w[u[k aa[v speed n p a b]]][w[k aa[v speed v light]][w[k aa[n p a b v time]][e[v xprime][k ad[k ab[v light k ac[v speed]] v time]]]]]].
d smy[light b scale b inverse b xprime b] b[k ad[k ad[v scale k ad[v light v light]] k ad[v inverse v xprime]]].
d smz[light b speed b scale b inverse b xprime b time b xi b] c[w[k sly[v light v speed v inverse]][w[k smx[v light v speed v xprime v time]][e[v xi][k ad[v light k slz[v light v speed v scale v inverse v xprime v time]]]]]].
'''


MEANINGS={
    'smx':'0≤v<Vと正の静止系時刻のもとで、光線の補助座標x′が(V-v)*tとなる有理数の条件。運動系の時刻τと分ける。',
    'smy':'同じ係数aとV²-v²の逆数によるa*V²*x′/(V²-v²)の有理数の式。',
    'smz':'同じ光線上のx′,t、係数a、逆数を使い、ξ=V*τのτへ先行する時間座標の式を代入した有理数の条件。',
}


def generic_composed():
    doc=parse((ROOT/'examples/v014/affine-time-form.noema').read_text(encoding='utf-8')+rational_definitions())
    basis=deepcopy(json.loads((ROOT/'data/affine-time-form-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='longitudinal-light-basis-v1',document='examples/v014/longitudinal-light.noema')
    basis['definitions'].update(MEANINGS)
    basis['unresolved']+=['光線上での代入による式と、光線外も含む一般座標変換を分ける。一直線上の一致だけから全入力での関数の一致を導かない。']
    audit_basis(doc,basis)
    return format_graph(doc,'compact')+'\n',basis


def frame_declarations(parent):
    """Parameterize the existing segment law; local times use the frame's clocks."""
    result=[]
    for old,new in (('sba','smu'),('sbb','smv')):
        d=deepcopy(next(d for d in parent['declarations'] if d['name']==old));d['name']=new
        d['parameters'].append({'name':'frame','sort':'individual'})
        def replace(node):
            if isinstance(node,list):return [replace(x) for x in node]
            if not isinstance(node,dict):return node
            if node.get('kind')=='call' and node.get('symbol')=='ra' and not node['arguments']:
                return {'kind':'variable','name':'frame'}
            output={k:replace(v) for k,v in node.items()}
            if node.get('kind')=='call' and node.get('symbol') in ('qt','sba'):
                output['symbol']={'qt':'smt','sba':'smu'}[node['symbol']]
                output['arguments'].append({'kind':'variable','name':'frame'})
            return output
        d['body']=replace(d['body']);result.append(d)
    return result


def source_composed():
    doc=parse((ROOT/'examples/v014/einstein-affine-time-form.noema').read_text(encoding='utf-8'))
    statements,doc['statements']=doc['statements'],[]
    zero='k bb[n p a b]'
    text=format_graph(doc,'compact')+rational_definitions()
    text+='d smt[event a clock a place a value '+CUT+' context d synchrony h[a a a a d] c frame a] c['+both(
        'k ba[v value]','k zbz[v frame v clock v context]','k zbz[v frame k zbh[v frame v context] v context]',
        'k saf[v event v clock v place k zbh[v frame v context] v frame k rb[] v value v context p ca p cb p cc p ci p ce v synchrony]',
        'k sgp[v event v place v frame k rb[] v context v synchrony p ba p sca]',
        'k sca[v value k zbe[v event v frame k rb[] v context]]')+'].\n'
    doc=parse(text);doc['declarations']+=frame_declarations(doc)
    text=format_graph(doc,'compact')+'''
d smw[frame a speed h[b] c context d] c[k smv[v speed v context p qo p sax v frame]].
r zey[] a.r zez[] a.r ze2[] a.r ze3[] a.r ze4[] a.r ze5[] a.r ze6[] a.r ze7[] a.
r zf2[a a i[e] j[a] a a d] c.
'''
    text+='d sna[light '+CUT+' speed '+CUT+'] '+CUT+'[k bf[v light v speed]].\n'
    delta='k bf[k shv[v light v light] k shv[v speed v speed]]'
    text+='d snb[light '+CUT+' speed '+CUT+' scale '+CUT+' xprime '+CUT+'] '+CUT+'[k shv[v scale k shv[k sje[k shv[v light v light] '+delta+'] v xprime]]].\n'
    text+='d snd[event a frame a role a context d] '+CUT+'[k zc6[k zdz[v event v frame v context] v role]].\n'
    text+='d sne[event a context d] '+CUT+'[k sin[k zb7[] k snd[v event k ra[] k yn[] v context] k snd[v event k ra[] k zc7[] v context]]].\n'
    f='c[k zd4[]][k sne[v event v context] k snd[v event k ra[] k yo[] v context] k snd[v event k ra[] k yp[] v context] k snd[v event k ra[] k zc7[] v context]]'
    text+='d snf[event a context d] c['+both('k ba['+f+']','k sca['+f+' k snd[v event k zbm[] k zc7[] v context]]')+'].\n'
    ctx='v context';depart='k wi[v moving]';end='k wj[v moving]';ray='k wf[v moving]'
    coord=lambda event,frame,role:'k snd['+event+' k '+frame+'[] k '+role+'[] '+ctx+']'
    clauses=['u[e[v rest][v moving]]','e[k wf[v rest]]['+ray+']','e[k wi[v rest]]['+depart+']','e[k wj[v rest]]['+end+']',
        'u[e['+depart+']['+end+']]','e[k wh[v moving]]['+depart+']','e[k wh[v rest]]['+depart+']',
        'k smk['+depart+' '+ctx+']','k sfm['+ctx+']',
        'k ba[k tc[]]','k ba[k zb7[]]','k bc['+zero+' k zb7[]]','k bg[k zb7[] k tc[]]']
    for segment,frame in (('rest','ra'),('moving','zbm')):
        clauses+=['k wa[v '+segment+' k '+frame+'[] k rb[] k ta[] '+ctx+']']
        for event,reader in ((depart,'wo'),(end,'wp')):
            clauses+=['k shd['+event+' k zdz['+event+' k '+frame+'[] '+ctx+'] k '+frame+'[] '+ctx+']',
                'k sca[k '+reader+'[v '+segment+'] '+coord(event,frame,'zc7')+']']
        clauses+=['k zbw[k '+frame+'[] k zbo[k '+frame+'[] k yn[] '+ctx+'] k yn[] '+ctx+']',
            'k zdw['+ray+' '+depart+' '+end+' k zbo[k '+frame+'[] k yn[] '+ctx+'] k '+frame+'[] '+ctx+']',
            'k bg['+zero+' '+coord(end,frame,'yn')+']',
            'k sca[k wq[v '+segment+'] k bf['+coord(end,frame,'yn')+' '+coord(depart,frame,'yn')+']]']
        for role in ('yo','yp'):clauses+=['k sca['+coord(end,frame,role)+' '+zero+']']
    clauses+=['k bg['+zero+' k sne['+end+' '+ctx+']]','k snf['+depart+' '+ctx+']','k snf['+end+' '+ctx+']']
    text+='d snc[rest a moving a context d] c['+both(*clauses)+'].\n'
    event='v event';V='k tc[]';v='k zb7[]';a='c[k zeq[]]['+v+']';x='k sne['+event+' '+ctx+']'
    t=coord(event,'ra','zc7');tau=coord(event,'zbm','zc7');xi=coord(event,'zbm','yn')
    for name,clauses in (
        ('sng',['k ba['+xi+']','k ba['+tau+']','k ba['+V+']','k sca['+xi+' k shv['+V+' '+tau+']]']),
        ('snh',[*('k ba['+value+']' for value in (xi,a,V,v,x,t)),'k bc['+zero+' '+v+']','k bg['+v+' '+V+']','k sca['+xi+' k shv['+V+' k smh['+V+' '+v+' '+a+' '+x+' '+t+']]]']),
        ('sni',[*('k ba['+value+']' for value in (x,t,V,v)),'k bg['+zero+' '+t+']','k bc['+zero+' '+v+']','k bg['+v+' '+V+']',
            'k sca['+x+' k shv[k sna['+V+' '+v+'] '+t+']]','k sca['+t+' k sje['+x+' k sna['+V+' '+v+']]]']),
        ('snj',[*('k ba['+value+']' for value in (xi,a,V,v,x)),'k bc['+zero+' '+v+']','k bg['+v+' '+V+']','k sca['+xi+' k snb['+V+' '+v+' '+a+' '+x+']]'])):
        text+='d '+name+'[event a context d] c['+both(*clauses)+'].\n'
    text+='d snk[rest a moving a context d] c['+both('k snc[v rest v moving v context]',
        'k sbc[k tc[] v context]','k smw[k zbm[] k tc[] v context]',
        'k smu[v rest k tc[] v context p qo p sax k ra[]]',
        'k smu[v moving k tc[] v context p qo p sax k zbm[]]',
        'k smj[k zd4[] k zeq[] k tc[] k zb7[]]')+'].\n'
    text+='''
d sno[] e[b context[w[k sat[k ra[] k zbm[] k zb6[]]][w[k sfm[k zb6[]]][w[t[k saw[]][k zb6[]]][k sbc[k tc[] k zb6[]]]]]]].
d snp[] e[b context[k smw[k zbm[] k tc[] k zb6[]]]].
d snq[] e[b context[k snk[k zez[] k zey[] k zb6[]]]].
d snr[] e[b context[k sng[k wj[k zey[]] k zb6[]]]].
d sns[] e[b context[k snh[k wj[k zey[]] k zb6[]]]].
d snt[] e[b context[k sni[k wj[k zey[]] k zb6[]]]].
d snu[] e[b context[k snj[k wj[k zey[]] k zb6[]]]].
d snv[] e[b context[w[k snk[k zez[] k zey[] k zb6[]]][k sni[k wj[k zey[]] k zb6[]]]]].
'''
    doc=parse(text);doc['statements']=statements
    doc=parse(format_graph(doc,'compact')+'''
s[k zf2[k ze7[] k rd[] r[k smn[]] l[a][k yn[] k yo[] k yp[]] k zdb[] k rh[] k ri[]]].
s[k zc[k ze2[] k rd[] r[k sno[]] r[k snp[]] k rh[] k ri[]]].
s[k zc[k ze3[] k rd[] r[k snq[]] r[k snr[]] k rh[] k ri[]]].
s[k zd3[k ze4[] k rd[] r[k snq[]] r[k snr[]] r[k sns[]] k rh[] k ri[]]].
s[k zc[k ze5[] k rd[] r[k snq[]] r[k snt[]] k rh[] k ri[]]].
s[k zd3[k ze6[] k rd[] r[k snv[]] r[k sns[]] r[k snu[]] k rh[] k ri[]]].
''')
    basis=deepcopy(json.loads((ROOT/'data/einstein-affine-time-form-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='einstein-longitudinal-light-basis-v1',document='examples/v014/einstein-longitudinal-light.noema')
    basis['definitions'].update(MEANINGS|{
        'smt':'指定系の局所時計と同系の参照時計を使う区間時刻。配置、同期、局所の読み、その系での一意な出来事時刻を結ぶ。',
        'smu':'既存sbaの光源、光線、区間、真空、単位、光路長の条件を指定系へ一般化し、局所時刻をsmtへ接続する。',
        'smv':'指定系の必要な全部分区間を尽くす非空の範囲に、同じ一つの光速を要求する。',
        'smw':'smvの時計の同期と速度条件を既存のqoとsaxへ接続する。',
        'sna':'同じ静止系の時刻と長さの単位による相対的な縦方向成分V-v。運動系で測る光速Vとは分ける。',
        'snb':'実切断によるa*V²*x′/(V²-v²)。分母の正性は光線の設定で要求する。',
        'snd':'同じ出来事・基準系・文脈の座標記録から、指定した成分を読む。記録の妥当性は呼出側で要求する。',
        'sne':'同じ出来事の静止系x,tと相対速度からx′=x-vtを読む。',
        'snf':'同じ出来事の四つの入力で先行するτを評価し、その出来事の運動系時刻に結ぶ。',
        'snc':'共通零点から正の縦方向へ進む同じ光線と二出来事を、両系の区間・時計・座標・正の光路長に接続する。',
        'sng':'指定した光線上の出来事についてξ=Vτである。光線外の全出来事には量化しない。',
        'snh':'同じξ=Vτのτへ、同じ速度と係数による先行する時間座標の式を代入した条件。',
        'sni':'同じ光線上でx′=(V-v)*tかつt=x′/(V-v)と要求する。tは静止系の時刻である。',
        'snj':'同じ光線上で時刻の値を代入して得るξ=a*V²*x′/(V²-v²)の条件。',
        'snk':'光線の設定、両系での同じVの伝播、同じτの式を結ぶ前提。',
        'sno':'先行する相対性原理と、静止系での同じ光速度の原理をこの運動設定へ適用する内容。',
        'snp':'運動系でも同じVを測るという全部分区間の法則の内容。',
        'snq':'選択した両系の光線区間についてのsnkの内容。',
        'snr':'選択した到達出来事でξ=Vτとなる内容。',
        'sns':'選択した到達出来事でτの式を代入した内容。',
        'snt':'選択した光線上の補助位置と静止系時刻の関係という内容。',
        'snu':'選択した光線上で得られる縦座標の式という内容。',
        'snv':'同じ光線の前提と静止系時刻の値をそろえた、代入の前提内容。'})
    decls={d['name']:d for d in doc['declarations']}
    for name,args,meaning in (
        ('zey',[],'τ=0に原点から正のξ方向へ出る光の、運動系での区間記録。'),
        ('zez',[],'同じ光と始終出来事の静止系での区間記録。時計・光路長の値は運動系記録と別に持つ。'),
        ('ze2',[],'二原理により運動系でも同じVを測ると述べる箇所。'),
        ('ze3',[],'正のξ方向への光にξ=Vτを与える箇所。'),
        ('ze4',[],'τの値を入れた式を同じ内容の別の形として提示する箇所。'),
        ('ze5',[],'静止系での原点との相対速度V-vから時刻を得る箇所。'),
        ('ze6',[],'そのtの値を代入して縦座標の式を得る箇所。'),
        ('ze7',[],'先行結果を使えば空間三座標が容易に得られると述べる箇所。'),
        ('zf2',['node','author','prior_result','coordinate_roles','task','scope','context'],'著者が指定先行結果を使い、指定課題の座標成分を容易に求められると提示する。実際の計算完了や負担の計測を主張しない。')):
        d=decls[name];basis['primitives'].append(dict(symbol=name,parameters=d['parameters'],result=d['result'],arguments=args,meaning_ja=meaning))
    basis['unresolved']+=generic_composed()[1]['unresolved'][-1:]+[
        'u0065〜u0072の部分記述。相対性原理の一般的記述から運動系の光速の測定法則を導く証明は未完であり、本文の推論の帰属として保存する。',
        'ξ=Vτには放出位置の原点規約が必要なため、直前の共通零点からの正方向の光線として接続する。原文の省略との意味上の過不足と原刊照合は未完。',
        '光源の独立性や光路長の測定は既存のsbaを一般化して保持した。指定系の参照時計と一意な出来事時刻への接続条件を追加した明示的モデルである。',
        '「容易」は著者による評価として保持し、成功する計算方法の負担からの構成説明は残る。',
        '異なる系の区間記録は同じ光と始終出来事を表すが、測定値は一致するとは限らない。V-vをτで測った光速に置き換えない。',
        'この光線上の代入だけでは全四座標での変換は決まらない。横方向の光線、光線外への拡張、全実切断の体の法則、全文の意味一致は未完。']
    audit_basis(doc,basis)
    return format_graph(doc,'compact')+'\n',basis


def main():
    for compose,name in ((generic_composed,'longitudinal-light'),(source_composed,'einstein-longitudinal-light')):
        text,basis=compose()
        for filename,body in ((basis['document'],text),('data/'+name+'-basis-v1.json',json.dumps(basis,ensure_ascii=False,indent=2)+'\n')):
            path=ROOT/filename
            if path.exists():
                if path.read_text(encoding='utf-8')!=body:raise ValueError('Stored longitudinal light differs: '+filename)
            else:
                with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(body)
    print('Longitudinal light coordinates and same-event substitutions composed')


if __name__=='__main__':main()
