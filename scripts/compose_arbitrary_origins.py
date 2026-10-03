"""Separate translated coordinates, possible trial choices and global scope."""
from copy import deepcopy
import json

from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from scripts.compose_moving_light_trip import ROOT, both
from scripts.compose_homogeneous_coordinates import CUT
from scripts.compose_comoving_labels import TAU

RATIONAL_TAU='h[b b b b] b'


def generic_definitions():
    return '''
d skh[function h[b b b b] b x b y b z b] h[b b b b] b[
 i[dx b dy b dz b time b][c[v function][k ab[v x v dx] k ab[v y v dy] k ab[v z v dz] v time]]].
d skj[point a actor a start d available h[a a d] c outcomes h[a a d d] c succeeds h[a a d] c] c[
 g trial a[w[c[v available][v actor v trial v start]][g alternative d[w[
 c[v outcomes][v actor v trial v start v alternative]
 ][c[v succeeds][v trial v point v alternative]]]]]].
'''


MEANINGS={
    'skh':'有理数の四引数関数について空間三引数の原点を指定量だけ移す。時刻の引数・関数の値は変更せず、尺度変更もしない。',
    'skj':'指定の主体・開始状況で選べる試行があり、その同じ試行の可能な結果の一つで、同じ地点について成功条件が成立する。実際の実行や全結果での保証は含意しない。',
}


def generic_composed():
    doc=parse((ROOT/'examples/v014/tau-differential.noema').read_text(encoding='utf-8')+generic_definitions())
    basis=deepcopy(json.loads((ROOT/'data/tau-differential-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='arbitrary-origins-basis-v1',document='examples/v014/arbitrary-origins.noema')
    basis['definitions'].update(MEANINGS)
    basis['unresolved']+=['地点ごとに選べる試行が存在する条件と、単一の試行で全地点を扱う条件は異なる。可能な結果を現実の発生として評価しない。']
    audit_basis(doc,basis)
    return format_graph(doc,'compact')+'\n',basis


def source_composed():
    doc=parse((ROOT/'examples/v014/einstein-tau-differential.noema').read_text(encoding='utf-8'))
    statements,doc['statements']=doc['statements'],[]
    text=format_graph(doc,'compact')+generic_definitions()
    text+='d ski[function '+TAU+' x '+CUT+' y '+CUT+' z '+CUT+'] '+TAU+'[i[dx '+CUT+' dy '+CUT+' dz '+CUT+' time '+CUT+'][c[v function][k bd[v x v dx] k bd[v y v dy] k bd[v z v dz] v time]]].\n'
    pointargs='function '+TAU+' x '+CUT+' y '+CUT+' z '+CUT+' light '+CUT+' speed '+CUT+' time '+CUT
    shifted='k ski[v function v x v y v z]'
    text+='d skk['+pointargs+' radius '+CUT+'] c[k skc['+shifted+' v light v speed v time v radius]].\n'
    valid=[*('k ba[v '+n+']' for n in ('x','y','z','light','speed','time')),
        'k bc[k bb[n p a b] v speed]','k bg[v speed v light]']
    derivatives='v function v x v y v z v time v spacepartial v timepartial'
    text+='d skl['+pointargs+'] c['+both(*valid,'g radius '+CUT+'[g spacepartial '+CUT+'[g timepartial '+CUT+'['+both(
        'k skk[v function v x v y v z v light v speed v time v radius]',
        'k sjv['+derivatives+']','k sjw['+derivatives+']')+']]]')+'].\n'
    text+='d skm['+pointargs+'] c['+both(*valid,'g spacepartial '+CUT+'[g timepartial '+CUT+'['+both(
        'k sjw['+derivatives+']','k sjy[v light v speed v spacepartial v timepartial]')+']]')+'].\n'
    universal='f x '+CUT+'[f y '+CUT+'[f z '+CUT+'[y['+both('k ba[v x]','k ba[v y]','k ba[v z]')+'][k skm[v function v x v y v z v light v speed v time]]]]]'
    text+='d skn[function '+TAU+' light '+CUT+' speed '+CUT+' time '+CUT+'] c['+both(
        'k ba[v light]','k ba[v speed]','k ba[v time]','k bc[k bb[n p a b] v speed]','k bg[v speed v light]',universal)+'].\n'
    spatial='x '+CUT+' y '+CUT+' z '+CUT+' time '+CUT
    matched=both('k ys[v moment v context]','k zce[v point v moment k ra[] k ta[] v context]',
        'k zcf[v moment k ra[] k rb[] v context]','k sca[k yl[v moment k ra[] k rb[] v context] v time]',
        *('k sca[k sij[v point v moment k '+role+'[] v context p bf p shv] v '+value+']' for role,value in (('yn','x'),('yo','y'),('yp','z'))))
    text+='d sko[point a '+spatial+' context d] c['+both(*('k ba[v '+n+']' for n in ('x','y','z','time')),
        'k zdi[v point v context]','k zcu[v point k zbm[] v context]','k x4[v point k zbm[] v context]',
        'g moment a['+matched+']')+'].\n'
    text+='''
r zec[a a d] c.r zed[a a d d] c.r zee[] a.r zef[a a a a a d] c.
r zeg[] a.r zeh[] a.r zei[a a a d] c.
'''
    trial='v trial';frame='k zbm[]';ctx='v context';origin='k qc[v trial]';mirror='k qd[v trial]'
    clocks=['k te[v trial]','k tf[v trial]'];events=['k '+n+'[v trial]' for n in ('qe','qf','qg')]
    reads=['k '+n+'[v trial]' for n in ('qi','qj','qk')];ray='k qh[v trial]';axis='k zbo['+frame+' k yn[] '+ctx+']'
    clauses=['e['+origin+'][v point]','u[e['+origin+']['+mirror+']]','u[e['+clocks[0]+']['+clocks[1]+']]',
        'k qb['+' '.join(clocks)+' '+frame+' k rb[] '+ctx+' '+trial+']',
        'k da['+' '.join((*clocks,origin,mirror,*events,ray,frame,'k rb[]',*reads))+']',
        'k sde['+' '.join((ray,*events,frame,'p cf','p cg','p ch'))+']',
        'k qo['+' '.join(clocks)+' '+frame+' k rb[] '+ctx+']',
        'k zbw['+frame+' '+axis+' k yn[] '+ctx+']']
    for clock in clocks:clauses+=['k zbz['+frame+' '+clock+' '+ctx+']']
    for place in (origin,mirror):clauses+=['k zcu['+place+' '+frame+' '+ctx+']']
    for a,b in zip(events,events[1:]):clauses+=['k zef['+ray+' '+a+' '+b+' '+axis+' '+frame+' '+ctx+']']
    for event,place,value in zip(events,(origin,mirror,origin),reads):clauses+=['k ba['+value+']',
        'k sgp['+event+' '+place+' '+frame+' k rb[] '+ctx+' p qo p ba p sca]',
        'k sca['+value+' k zbe['+event+' '+frame+' k rb[] '+ctx+']]']
    for a,b in zip(reads,reads[1:]):clauses+=['k bg['+a+' '+b+']']
    text+='d skp[trial a point a context d] c['+both(*clauses)+'].\n'
    clauses=[]
    for event,reading in zip(events,reads):
        tup='k zdz['+event+' k ra[] '+ctx+']'
        args=['k sin[k zb7[] k zc6['+tup+' k yn[]] k zc6['+tup+' k zc7[]]]',
            'k zc6['+tup+' k yo[]]','k zc6['+tup+' k yp[]]','k zc6['+tup+' k zc7[]]']
        value='c[k zd4[]]['+' '.join(args)+']'
        clauses+=['k shd['+event+' '+tup+' k ra[] '+ctx+']','k ba['+value+']','k sca['+value+' '+reading+']']
    text+='d skq[trial a context d] c['+both(*clauses)+'].\n'
    text+='d skr[trial a point a '+spatial+' baseline d alternative d] c['+both(
        'k sfm[v alternative]','k sbc[k tc[] v alternative]',
        'k sko[v point v x v y v z v time v baseline]','k sko[v point v x v y v z v time v alternative]',
        'k skp[v trial v point v alternative]','k skq[v trial v alternative]',
        'k sca[k sjh[k qe[v trial] v alternative] v time]',
        'k skl[k zd4[] v x v y v z k tc[] k zb7[] v time]')+'].\n'
    text+='d sks['+spatial+' context d] c[g point a['+both('k sko[v point v x v y v z v time v context]',
        'k skj[v point k zee[] v context p zec p zed i[trial a point a alternative d][k skr[v trial v point v x v y v z v time v context v alternative]]]')+']].\n'
    allpoints='f x '+CUT+'[f y '+CUT+'[f z '+CUT+'[y['+both('k ba[v x]','k ba[v y]','k ba[v z]')+'][k sks[v x v y v z v time v context]]]]]'
    text+='d skt[time '+CUT+' context d] c['+both('k ba[v time]','k sio[k zd4[]]',allpoints)+'].\n'
    time='k sjh[k qe[k zdq[]] k zb6[]]'
    text+='d sku[] e[b context[k skt['+time+' k zb6[]]]].\n'
    text+='d skv[] e[b context[k skn[k zd4[] k tc[] k zb7[] '+time+']]].\n'
    doc=parse(text);doc['statements']=statements
    doc=parse(format_graph(doc,'compact')+'''
s[w[k uh[k zeg[] k rd[] r[k sku[]] k rh[] k ri[]]][k zei[k zeg[] k rd[] k rh[] k ri[]]]].
s[k zc[k zeh[] k rd[] r[k sku[]] r[k skv[]] k rh[] k ri[]]].
''')
    basis=deepcopy(json.loads((ROOT/'data/einstein-tau-differential-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='einstein-arbitrary-origins-basis-v1',document='examples/v014/einstein-arbitrary-origins.noema')
    basis['definitions'].update(MEANINGS|{
        'ski':'四引数の実切断関数について空間の原点を移す。f(x₀+dx,y₀+dy,z₀+dz,t)を返し、時刻や尺度を変更しない。',
        'skk':'移した原点を出発点とするτの中点式を、全ての十分小さい正の変位について要求する。',
        'skl':'指定した任意の位置と同じ時刻で、正の近傍半径と二偏微分値が存在し、移した中点式・元の関数の全微分可能性・各偏微分が成立する局所前提。',
        'skm':'指定した位置と時刻で、同じ関数の二偏微分値が存在し、整理後の微分形の式が成立する。原点の偏微分値を全位置へ定数として流用しない。',
        'skn':'同じ関数・速度・時刻について、全ての有効な実数のx′,y,zでskmを要求する。記録された有限の地点集合とは区別する。',
        'sko':'同じ設定の運動系で静止する地点について、指定時刻の静止系の履歴からx-vt・y・zを取得して指定値に照合する。運動系の測定座標ξと混同しない。',
        'skp':'指定地点から同じ地点へ戻る光往復。原点との一致は要求せず、X軸に平行な経路、同じ光・時計・三出来事・同期・局所時刻を保持する。',
        'skq':'その同じ試行の三出来事の静止系座標から補助座標と時刻を作り、共通のτ候補の値を運動系の時計の読みに照合する。',
        'skr':'候補となる別の設定で、同じ速度と光速度の条件、同じ地点の同じ補助座標と時刻、そこから出る試行と時計の読みに合う共通関数、および局所前提を要求する。',
        'sks':'指定座標を表す地点が元の設定にあり、議論を行う主体が選べる試行の可能な結果の一つで、その同じ地点についてskrが成立する。',
        'skt':'同じτ候補・時刻について、全ての空間座標を表す地点ごとにsksが成立する。地点ごとに異なる試行や別設定を選べる。',
        'sku':'出発点を任意の場所に選べるという、前段の局所条件を明示した内容。実際に全試行が行われたことは含意しない。',
        'skv':'その同じτ候補・時刻について、空間座標の全値で微分形の式が成立するという内容。'})
    declarations={d['name']:d for d in doc['declarations']}
    for name,args,meaning in (
        ('zec',['actor','trial','context'],'指定の議論の設定で主体が選べる候補試行。実行済みの試行の一覧とは区別する。'),
        ('zed',['actor','trial','context','alternative'],'その主体がその試行を選ぶ場合に考察する可能な結果設定。実際の履歴や全結果の保証ではない。'),
        ('zee',[],'本文で別の出発点を選べたと述べる、議論を行う側。著者の「われわれ」の指示対象として扱い、構成員は確定しない。'),
        ('zef',['ray','from_event','to_event','axis','frame','context'],'その系・設定で同じ光の二出来事間の経路全体が、指定軸に平行な一つの直線上にある。進行方向の正負は限定せず、支持線が軸と一致する場合も許す。伝播・反射・場所は別に検査する。'),
        ('zeg',[],'原点の代わりに任意の他の点を出発点として選べたと指摘する箇所。'),
        ('zeh',[],'この選択の自由から式が空間座標の全値に成り立つと述べる箇所。'),
        ('zei',['node','author','scope','context'],'著者がその箇所を注意すべき事項として提示する。明白さや証明済みを意味しない。')):
        d=declarations[name];basis['primitives'].append(dict(symbol=name,parameters=d['parameters'],result=d['result'],arguments=args,meaning_ja=meaning))
    basis['unresolved']+=[
        'u0058の部分記述。元の原点の場合と任意の他の点の場合を合わせ、全空間座標について記述する。今回は時刻を前段と同じパラメータに保つ。',
        '可能な選択には、前段で明示した正の変位全体の式と局所微分可能性を成功条件として含める。この十分条件の補足を、原文に明記された条件とは扱わない。',
        '平行移動した光路から近傍全体の中点式を得る物理的・幾何学的な一般定理と、局所条件から微分式への全実数上の導出は未証明。',
        '全ての座標に対応する地点と可能な試行の存在は、有限の例の検査では保証しない。実際の全地点・全履歴、原刊照合、全文の意味確認は未完。']
    audit_basis(doc,basis)
    return format_graph(doc,'compact')+'\n',basis


def main():
    for compose,filename in ((generic_composed,'data/arbitrary-origins-basis-v1.json'),(source_composed,'data/einstein-arbitrary-origins-basis-v1.json')):
        text,basis=compose()
        for name,body in ((basis['document'],text),(filename,json.dumps(basis,ensure_ascii=False,indent=2)+'\n')):
            path=ROOT/name
            if path.exists():
                if path.read_text(encoding='utf-8')!=body:raise ValueError('Stored arbitrary origins differ: '+name)
            else:
                with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(body)
    print('Translated origins, possible trial choices and all-space differential scope composed')


if __name__=='__main__':main()
