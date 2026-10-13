"""Compose geographically bound, otherwise matched clock-rate comparisons."""
from copy import deepcopy
import json
from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from scripts.compose_curved_clock import ROOT, CUT
from scripts.compose_origin_clock import definition
from scripts.compose_limits import call as k, op, both, quant as q

v=lambda name:'v '+name
PRIMITIVES=[
 ('zjg','a a d','c',['part','whole','setting'],'対象が全体の機械的な構成部分である。単なる同じ場所での共存ではない。'),
 ('zjh','a a a d','c',['oscillator','axis','spring','setting'],'慣性体が軸の周りに往復回転し、指定した弾性体が復元作用を与える機械的な振動系。質量・弾性・運動の基礎説明は残る。'),
 ('zji','a a d','c',['clock','oscillator','setting'],'時計がその振動系の反復を歩度の調整に用いる。近くに振動系があるだけでは成立しない。'),
 ('zjj','a a d','c',['condition','clock','setting'],'その時計が指定された比較条件に置かれている。条件の値を含む個体への関係。'),
 ('zjk','a a d','c',['condition','scope','setting'],'比較範囲でその他の条件として採用する条件。比較対象の運動と位置そのものはこの範囲の対象外。'),
 ('zjl','a d','c',['scope','setting'],'その他の条件の指定範囲が比較に必要な条件を尽くしている。空の選択や恣意的な省略を完全な条件一致とは扱わない。'),
 ('zjm','a a a d','c',['clock','place','body','setting'],'時計を指定物体上の場所に固定し、その場所と共に動く配置。'),
 ('zjn','a a a d','c',['body','axis','frame','setting'],'同じ物体が指定基準系で指定した中心回転軸の周りを一様に回転する設定。実際の地球への適用は解釈前提。'),
 ('zjo','a a a a d',CUT,['place','body','axis','lengthunit','setting'],'物体の中心を通り回転軸に垂直な面から、場所までの軸方向の符号付き座標。'),
 ('zjp','a a a a d',CUT,['place','body','axis','lengthunit','setting'],'場所から中心回転軸までの垂直距離。同じ長さ単位で測る非負の値。'),
 ('zjq','a a d','c',['place','body','setting'],'指定された場所が同じ物体の表面にある。'),
 ('zju','a a a a d',CUT,['clock','interval','frame','timeunit','setting'],'指定した共通の比較時間区間における時計の指示の進みを座標時間の進みで割った平均の進み率。同じ時間単位と基準系を使い、文字盤の原点を含まない。観測・校正からこの率を求める一般的説明は未完。'),
 ('zjv',CUT+' '+CUT+' a d','c',['difference','reference_rate','scope','setting'],'同じ単位の進み率の差が、この参照率と比較文脈で「非常に小さい」に当たるという程度基準。正の差であることは呼出し側で要求し、具体的な数値閾値は補わない。'),
 ('zjr','','a',[],'地球を指す固有の参照。綴りを地球の一般的な概念定義として扱わない。'),
 ('zjs','','a',[],'この設定の地球の中心回転軸を指す参照。'),
 ('zjt','','d',[],'地球上の二時計を比較する設定。'),
 ('zjw','','a',[],'この二時計のその他の条件と程度基準を指定する比較範囲。'),
 ('zjx','','a',[],'二時計の進み率に共通の比較時間区間。'),
 ('zjy','','a',[],'赤道の時計が極の時計より僅かに遅いと帰結する箇所。'),
]


def composed():
    doc=parse((ROOT/'examples/v014/einstein-curved-clock.noema').read_text(encoding='utf-8'))
    statements,doc['statements']=doc['statements'],[];text=format_graph(doc,'compact')
    for name,parameters,result,_,_ in PRIMITIVES:text+='r '+name+'['+parameters+'] '+result+'.\n'
    zero=k('bb','n p a b');clock=v('clock');setting=v('setting')
    text+=definition('syi','clock a setting d',both(k('ca',clock),q('g','oscillator','a',q('g','axis','a',q('g','spring','a',both(
        op('u',op('e',v('oscillator'),v('spring'))),k('zjg',v('oscillator'),clock,setting),k('zjg',v('spring'),v('oscillator'),setting),
        k('zjh',v('oscillator'),v('axis'),v('spring'),setting),k('zji',clock,v('oscillator'),setting)))))))
    text+=definition('syj','first a second a scope a setting d',both(k('zjl',v('scope'),setting),
        q('g','condition','a',k('zjk',v('condition'),v('scope'),setting)),q('f','condition','a',op('y',k('zjk',v('condition'),v('scope'),setting),
            op('z',k('zjj',v('condition'),v('first'),setting),k('zjj',v('condition'),v('second'),setting))))))
    geo='place a body a axis a lengthunit a setting d'
    axial=k('zjo',*(v(n) for n in ('place','body','axis','lengthunit','setting')))
    radius=k('zjp',*(v(n) for n in ('place','body','axis','lengthunit','setting')))
    valid=both(k('zjq',v('place'),v('body'),setting),k('ba',axial),k('ba',radius),k('bc',zero,radius))
    text+=definition('syk',geo,both(valid,k('sca',axial,zero),k('bg',zero,radius)))
    text+=definition('syl',geo,both(valid,k('sca',radius,zero),op('u',k('sca',axial,zero))))
    pair='first a second a firstplace a secondplace a body a axis a frame a lengthunit a scope a setting d'
    text+=definition('sym',pair,both(op('u',op('e',v('first'),v('second'))),k('syi',v('first'),setting),k('syi',v('second'),setting),
        k('cd',v('first'),v('second')),k('syj',v('first'),v('second'),v('scope'),setting),
        k('zjn',v('body'),v('axis'),v('frame'),setting),
        k('zjm',v('first'),v('firstplace'),v('body'),setting),k('zjm',v('second'),v('secondplace'),v('body'),setting),
        k('syk',v('firstplace'),*(v(n) for n in ('body','axis','lengthunit','setting'))),
        k('syl',v('secondplace'),*(v(n) for n in ('body','axis','lengthunit','setting')))))
    first=k('zju',v('first'),v('interval'),v('frame'),v('timeunit'),setting)
    second=k('zju',v('second'),v('interval'),v('frame'),v('timeunit'),setting)
    text+=definition('syn','first a second a interval a frame a timeunit a scope a setting d',both(
        k('ci',v('timeunit')),k('sbg',first),k('sbg',second),k('bg',first,second),k('zjv',k('bf',second,first),second,v('scope'),setting)))
    setup=k('sym',v('first'),v('second'),v('firstplace'),v('secondplace'),k('zjr'),k('zjs'),k('ra'),k('ta'),k('zjw'),k('zjt'))
    result=k('syn',v('first'),v('second'),k('zjx'),k('ra'),k('rb'),k('zjw'),k('zjt'))
    body=op('y',setup,result)
    for name in reversed(('first','second','firstplace','secondplace')):body=q('f',name,'a',body)
    text+=definition('syo','','b context['+body+']','e')
    doc=parse(text);doc['statements']=statements
    doc=parse(format_graph(doc,'compact')+'s[k zc[k zjy[] k rd[] r[k syd[]] r[k syo[]] k zjd[] k ri[]]].\n')
    basis=deepcopy(json.loads((ROOT/'data/curved-clock-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='earth-clocks-basis-v1',document='examples/v014/einstein-earth-clocks.noema')
    decls={d['name']:d for d in doc['declarations']}
    for name,_,_,labels,meaning in PRIMITIVES:
        d=decls[name];basis['primitives'].append(dict(symbol=name,parameters=d['parameters'],result=d['result'],arguments=labels,meaning_ja=meaning))
    basis['definitions'].update({
        'syi':'時計の構成部分として復元作用を持つ回転振動系があり、それを歩度の調整に使う時計。Unruhuhrを振り子時計や単なる任意の時計と同一視しない構成的な草案。',
        'syj':'比較のその他の条件の範囲が完全・非空であり、全ての選択条件について両対象の成立・不成立が一致する。構造の一致とは別の条件。',
        'syk':'同じ物体の表面で、軸方向座標が零、回転軸からの距離が正である赤道上の場所。球半径や具体的緯度を語ごとに列挙しない。',
        'syl':'同じ物体の表面で、回転軸からの距離が零、軸方向座標が非零である極。軸の正負を固定せず両極を含める。',
        'sym':'同じ回転体の赤道と極に固定した異なる二時計が、同じ構造の回転振動系時計であり、その他の比較条件が一致するという設定。',
        'syn':'共通の時間区間・基準系・時間単位で第一時計の正の進み率が第二より小さく、その差が指定した程度基準を満たす。指示の絶対値や帰還時の同じ場所での比較は要求しない。',
        'syo':'同じ地球の赤道と一つの極にある、symで限定された任意の二時計について、第一が非常に僅かに遅く進むという条件付き内容。'})
    basis['unresolved'] += [
        'u0128末尾の部分記述。機構・条件の完全性・回転体の測定・平均進み率の物理的な実現は基礎関係として残る。地球という固有参照だけを意味の説明とは数えない。',
        'Unruhuhrは復元弾性を伴う回転振動系を歩度調整に使う時計と読む。機構の一般的な力学、脱進機の詳細と原刊照合は未完。',
        '赤道と極の時計は同じ場所へ帰還して対面比較する二時計ではない。曲線の帰還結果sydからの移行は著者の帰結として帰属し、実世界での十分な導出とは認定しない。',
        '非常に小さい差の数値は原文にないため固定しない。同構造から同じ進み率を推論せず、その他の条件の一致を別に保持する。',
        '地球の運動と環境の全体をこの比較から導いたとはしない。原文の全意味一致の確認は未完。']
    audit_basis(doc,basis)
    return format_graph(doc,'compact')+'\n',basis


def main():
    text,basis=composed()
    for relative,body in ((basis['document'],text),('data/earth-clocks-basis-v1.json',json.dumps(basis,ensure_ascii=False,indent=2)+'\n')):
        path=ROOT/relative
        if path.exists():
            if path.read_text(encoding='utf-8')!=body:raise ValueError('Stored earth clocks differ: '+relative)
        else:
            with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(body)
    print('Otherwise matched equatorial and polar clocks composed')


if __name__=='__main__':main()
