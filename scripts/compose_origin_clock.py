"""Bind an origin clock, alternative calibration cases and its rate question."""
from copy import deepcopy
import json

from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from scripts.compose_shape_contraction import ROOT, CUT
from scripts.compose_limits import call as k, op, both, quant as q

v=lambda n:'v '+n


def definition(name,params,body,result='c'):
    return 'd '+name+'['+params+'] '+result+'['+body+'].\n'


def rational_definitions():
    return '''
d suw[light b speed b beta b time b proper b] c[k srb[v light v speed v beta n p b b k ad[v speed v time] n p a b n p a b v time n p a b n p a b n p a b v proper]].
d sux[scale b offset b coordinate b reading b] c[w[k aa[n p a b v scale]][e[v reading][k ab[k ad[v scale v coordinate] v offset]]]].
'''


MEANINGS={
    'suw':'動く系の空間原点にある出来事の最終変換。観測系でx=v*t,y=z=0、動く系で空間三成分零という有理数条件。',
    'sux':'正の尺度と任意の原点を持つ時計の指示と座標時刻の校正。有理数の関係。'}


def generic_composed():
    doc=parse((ROOT/'examples/v014/shape-contraction.noema').read_text(encoding='utf-8')+rational_definitions())
    basis=deepcopy(json.loads((ROOT/'data/shape-contraction-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='origin-clock-basis-v1',document='examples/v014/origin-clock.noema')
    basis['definitions'].update(MEANINGS)
    basis['unresolved']+=['時計の指示の校正と座標変換は別の条件。共通の指示原点は差で消えるが、尺度の変更は進み率を変える。']
    audit_basis(doc,basis)
    return format_graph(doc,'compact')+'\n',basis


def source_composed():
    doc=parse((ROOT/'examples/v014/einstein-shape-contraction.noema').read_text(encoding='utf-8'))
    statements,doc['statements']=doc['statements'],[]
    text=format_graph(doc,'compact')+rational_definitions()
    z=k('bb','n p a b');one=k('bb','n p b b')
    V=k('tc');speed=k('zb7');frame=k('zbm');setting=v('setting');clock=v('clock')
    coord=lambda record,axis:k('zc6',record,k(axis))
    paired=lambda record,system:k('zdz',k('zad',record),k(system),setting)
    reading=lambda record:k('zag',record)
    instant=lambda record:coord(paired(record,'ra'),'zc7')
    selected=lambda record:k('zac',record,clock,setting)
    # Eligibility of an alternative setup is independent of actual placement.
    text+='r zid[a a d d] c.r zie[] a.r zif[] a.r zig[] a.r zih[a a i[g['+CUT+']] a d] c.r zii[] a.r zij[] a.\n'
    record=v('record');event=k('zad',record);place=k('zae',record);value=reading(record)
    text+=definition('suy','clock a frame a setting d',both(k('ca',clock),k('ci',k('rb')),k('x4',clock,v('frame'),setting),
        k('zai',clock,v('frame'),setting),q('g','record','a',selected(record)),q('f','record','a',op('y',selected(record),both(
            k('ba',value),k('zab',clock,event,place,v('frame'),setting),k('cb',event,place,v('frame')),
            k('ce',clock,event,v('frame'),k('rb'),value),q('g','coordinates','a',both(k('shd',event,v('coordinates'),v('frame'),setting),
                k('sha',v('coordinates'),'p ba'),k('sca',value,coord(v('coordinates'),'zc7')))))))))
    text+=definition('suz','clock a actual d',both(k('ca',clock),op('u',op('e',k('ra'),frame)),*(q('g','trial','d',both(
        k('zid',clock,k(system),v('actual'),v('trial')),k('suy',clock,k(system),v('trial')))) for system in ('ra','zbm'))))
    origin=k('zbn',frame,setting)
    text+=definition('sva','clock a event a observed a moving a setting d',both(k('ca',clock),k('ci',k('rb')),op('u',op('e',k('ra'),frame)),
        k('x4',clock,frame,setting),k('zbv',frame,origin,setting),k('cb',clock,origin,frame),
        k('zc4',v('event')),k('zab',clock,v('event'),origin,frame,setting),k('cb',v('event'),origin,frame),
        k('shd',v('event'),v('observed'),k('ra'),setting),k('shd',v('event'),v('moving'),frame,setting),
        k('sha',v('observed'),'p ba'),k('sha',v('moving'),'p ba'),
        *(k('sca',coord(v('moving'),axis),z) for axis in ('yn','yo','yp')),
        k('ce',clock,v('event'),frame,k('rb'),coord(v('moving'),'zc7'))))
    text+=definition('svb','clock a setting d',both(k('suy',clock,frame,setting),q('f','record','a',op('y',selected(record),both(
        k('sva',clock,event,paired(record,'ra'),paired(record,'zbm'),setting),k('sca',reading(record),coord(paired(record,'zbm'),'zc7')))))))
    first,last=v('first'),v('last')
    pair=both(selected(first),selected(last),k('bg',instant(first),instant(last)))
    rate=k('shv',v('rate'),k('bf',instant(last),instant(first)))
    # This question tests rate from readings, without inserting the expected answer.
    text+=definition('svc','clock a rate '+CUT+' setting d',both(k('sbg',v('rate')),k('svb',clock,setting),
        q('g','first','a',q('g','last','a',pair)),q('f','first','a',q('f','last','a',op('y',pair,k('sca',k('bf',reading(last),reading(first)),rate))))))
    text+=definition('svd','','j v[i[rate '+CUT+'][k svc[k zie[] v rate k zb6[]]]]','g['+CUT+']')
    text+=definition('sve','','b context['+both(k('suz',k('zie'),k('zb6')),k('svb',k('zie'),k('zb6')))+']','e')
    admissible=k('srd',V,speed,k('soy',V,speed))
    text+=definition('svf','observed a moving a',both(k('sha',v('observed'),'p ba'),k('sha',v('moving'),'p ba'),admissible,
        k('sca',coord(v('moving'),'zc7'),k('spd',V,speed,one,coord(v('observed'),'yn'),coord(v('observed'),'zc7')))))
    text+=definition('svg','observed a',both(k('sha',v('observed'),'p ba'),admissible,
        k('sca',coord(v('observed'),'yn'),k('shv',speed,coord(v('observed'),'zc7')))))
    def all_clock_records(body):
        return both(q('g','record','a',k('zac',record,k('zie'),k('zb6'))),q('f','record','a',op('y',k('zac',record,k('zie'),k('zb6')),body)))
    rest=k('zdz',event,k('ra'),k('zb6'));moving=k('zdz',event,frame,k('zb6'))
    text+=definition('svh','','b context['+all_clock_records(both(k('svf',rest,moving),k('svg',rest)))+']','e')
    text+=definition('svi','','b context['+both('t[k sve[]][v context]','t[k sso[]][v context]')+']','e')
    time=coord(v('observed'),'zc7');proper=coord(v('moving'),'zc7');factor=k('stw',V,speed)
    text+=definition('svj','observed a moving a',both(k('sha',v('observed'),'p ba'),k('sha',v('moving'),'p ba'),admissible,
        k('sca',proper,k('shv',factor,time)),k('sca',proper,k('bf',time,k('shv',k('bf',one,factor),time)))))
    text+=definition('svk','','b context['+all_clock_records(k('svj',rest,moving))+']','e')
    text+=definition('svl','','b context['+both('t[k sve[]][v context]','t[k svh[]][v context]')+']','e')
    text+=definition('svm','',factor,CUT)
    doc=parse(text);doc['statements']=statements
    doc=parse(format_graph(doc,'compact')+'''
s[k ug[k zif[] k rd[] r[k sve[]] k rh[] k ri[]]].
s[k zih[k zig[] k rd[] r[k svd[]] k rh[] k ri[]]].
s[k zc[k zii[] k rd[] r[k svi[]] r[k svh[]] k rh[] k ri[]]].
s[k zdg[k zii[] k rd[] r[k svh[]] k rh[] k ri[]]].
s[k zc[k zij[] k rd[] r[k svl[]] r[k svk[]] k rh[] k ri[]]].
''')
    basis=deepcopy(json.loads((ROOT/'data/einstein-shape-contraction-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='einstein-origin-clock-basis-v1',document='examples/v014/einstein-origin-clock.noema')
    basis['definitions'].update(MEANINGS|{
        'suy':'指定系で静止する同じ時計の非空かつ必要な全照合記録について、場所・出来事・単位・指示をその系の座標時刻と結ぶ。',
        'suz':'同じ時計に、Kで静止してtを表示する許容設定と、kで静止してτを表示する許容設定がある。二つの設定を現在の同時成立にしない。',
        'sva':'同じ時計と出来事が移動系の原点にあり、両系の記録が存在し、時計の指示が移動系の時刻に合い、移動系の空間三座標が零である。',
        'svb':'時計を移動系の原点に置き、必要な全照合記録でτを表示する現在の設定。候補座標記録を存在済みの測定へ結ぶ。',
        'svc':'観測系で時間の異なる少なくとも二つの記録があり、全ての時間順の組で指示差が候補進み率と観測時間差の積に等しい。答えへ平方根の式を先に代入しない。',
        'svd':'同じ時計を静止系から見た正の一定進み率を答えとする質問。答えの存在・一意性は先に主張しない。',
        'sve':'両系で時刻を表示できる時計を、今回移動系の原点に置いてτを表示させる設定内容。',
        'svf':'同じ出来事の二座標記録に対するτ=β*(t-v*x/V²)。空間原点の条件はこれだけでは含まない。',
        'svg':'観測系の同じ記録についてx=v*t。',
        'svh':'同じ時計の非空の全照合記録でsvfとsvgをともに要求する内容。',
        'svi':'時計の設定に、前段の最終四式の全記録対応を合わせた前提内容。',
        'svj':'同じ記録についてτ=f*t=t-(1-f)*tを結ぶ。符号付きの座標時刻の式であり、tを常に正の経過時間とはしない。',
        'svk':'同じ時計の全照合記録におけるsvjの内容。',
        'svl':'時計の設定と二つの方程式を合わせた導出の前提内容。',
        'svm':'進み率の候補√(1-(v/V)²)。質問の答えとして成立するにはsvcの測定と時間幅の条件が別途必要。'})
    decls={d['name']:d for d in doc['declarations']}
    for name,args,meaning in (
        ('zid',['clock','frame','actual','trial'],'同じ時計を指定系で静止させ時刻に合わせることのできる、実際の設定から許容される試行設定。能力の物理的な機構・実現可能性は外部規約として残る。'),
        ('zie',[],'§4で原点へ置く同じ時計。指示能力と実際の配置は定義で要求する。'),
        ('zif',[],'時計の能力と原点での配置・指示の設定を仮定する箇所。'),
        ('zig',[],'静止系から見た同じ時計の進み率を問う箇所。'),
        ('zih',['node','author','question','scope','context'],'著者が実数値を答えとする記述された質問を提示する。答えの発見済み・存在・一意性は含意しない。'),
        ('zii',[],'同じ時計の場所に関する二つの式を明らかとして提示する箇所。'),
        ('zij',[],'原点の軌道を代入してτとtの比例式・差の式を得る箇所。')):
        d=decls[name];basis['primitives'].append(dict(symbol=name,parameters=d['parameters'],result=d['result'],arguments=args,meaning_ja=meaning))
    basis['unresolved']+=[
        'u0118〜u0124の部分記述。時計の能力の許容設定と照合記録の完全性は外部規約として与え、有限記録から全時間の能力を証明しない。',
        '全記録の指示差による一定進み率は今回の等速・校正済み時計に適用する。瞬間的な変動率一般の定義や、加速中の時計の法則は含まない。',
        '同じ座標単位でτを指示する設定では尺度1・原点0を要求する。差の比だけなら共通の指示原点は消えるが、別々の原点変更や尺度変更を自動的に消さない。',
        '質問には観測系で異なる時刻の記録の存在が必要。方程式が一時刻で成立しただけでは進み率を特定しない。',
        '単位時間あたりの遅れと二次近似は後続で接続する。原刊照合と原文との意味一致、実切断全域の一般法則は未完。']
    audit_basis(doc,basis)
    return format_graph(doc,'compact')+'\n',basis


def main():
    for compose,name in ((generic_composed,'origin-clock'),(source_composed,'einstein-origin-clock')):
        text,basis=compose()
        for relative,body in ((basis['document'],text),('data/'+name+'-basis-v1.json',json.dumps(basis,ensure_ascii=False,indent=2)+'\n')):
            path=ROOT/relative
            if path.exists():
                if path.read_text(encoding='utf-8')!=body:raise ValueError('Stored origin clock differs: '+relative)
            else:
                with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(body)
    print('Origin clock placement, calibration alternatives and rate question composed')


if __name__=='__main__':main()
