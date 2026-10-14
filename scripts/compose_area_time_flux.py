"""Normalize energy and signed work over one positive area and time interval."""
from copy import deepcopy
from itertools import combinations
import json

from noema.extraction import extract_document,extract_basis
from noema.grammar import parse,format_graph
from noema.meaning_basis import audit_basis
from scripts.compose_origin_clock import ROOT,definition,v
from scripts.compose_limits import call as k,app,op,both
from scripts.compose_field_equations import CUT
from scripts.compose_wave_amplitudes import params
from scripts.compose_wave_readings import parameters,RECORDED
from scripts.compose_shared_light_law import READ
from scripts.compose_light_pressure import ALL,generic_composed as pressure_document

PARENT='examples/v014/einstein-light-pressure.noema'
EXTENT='area duration inenergy outenergy workenergy'
RATES='incoming outgoing work'
NORMAL=EXTENT+' '+RATES
TOTAL='inenergy outenergy workenergy'
COMBINED=ALL+' '+EXTENT
EXCHANGE='h[a a a a a a a d] c'
RECORDS=('area','duration','inenergy','outenergy','workenergy')
TARGETS=dict(area='patch',duration='interval',inenergy='incominglight',outenergy='outgoinglight',workenergy='mirror')
KINDS=dict(area='areakind',duration='timekind',inenergy='energykind',outenergy='energykind',workenergy='energykind')
INPUTS=[(n,'a') for n in ('episode','mirror','patch','interval','incominglight','outgoinglight','frame','observer',
    'areakind','timekind','energykind')]+[('context','d'),('recordedby',RECORDED),('exchange',EXCHANGE)]
INPUTS += [(n,CUT) for n in ALL.split()]
for name in RECORDS:
    INPUTS += [(name+field,sort) for field,sort in (('record','a'),('unit','a'),('scale','b'),('value',CUT))]


def definitions(real=False):
    norm,total,combined=('seld','sele','self') if real else ('sela','selb','selc')
    sort=CUT if real else 'b'
    zero=k('bb','n p a b') if real else 'n p a b'
    mul=lambda a,b:k('shv' if real else 'ad',a,b)
    sub=lambda a,b:k('bf',a,b) if real else k('ab',a,k('ac',b))
    eq=lambda a,b:k('sca',a,b) if real else op('e',a,b)
    lt=lambda a,b:k('bg' if real else 'aa',a,b)
    valid=lambda fields:[k('ba',v(n)) for n in fields.split()] if real else []
    span=mul(v('area'),v('duration'))
    conditions=valid(NORMAL)+[lt(zero,v('area')),lt(zero,v('duration'))]
    for amount,rate in zip(('inenergy','outenergy','workenergy'),RATES.split()):
        conditions.append(eq(v(amount),mul(span,v(rate))))
    for name in ('inenergy','outenergy','incoming','outgoing'):
        conditions.append(op('u',lt(v(name),zero)))
    text=definition(norm,params(NORMAL,sort),both(*conditions))
    text+=definition(total,params(TOTAL,sort),both(*valid(TOTAL),
        op('u',lt(v('inenergy'),zero)),op('u',lt(v('outenergy'),zero)),
        eq(v('workenergy'),sub(v('inenergy'),v('outenergy')))))
    text+=definition(combined,params(COMBINED,sort),both(
        k('sekm' if real else 'sekf',*map(v,ALL.split())),k(norm,*map(v,NORMAL.split()))))
    return text


RATIONAL_MEANINGS={
    'sela':'正の面積Sと時間Tについて、入射・出射エネルギーと仕事の量を、それぞれ同じS*Tと単位面積・単位時間あたりの値の積へ結ぶ。入出は非負だが仕事の量と率は符号付き。',
    'selb':'非負の入出エネルギーと符号付きの仕事について、仕事の量が入る量から出る量を引いた値である。面積と時間で正規化した率の式と区別する。',
    'selc':'反射・入出・圧力と仕事率の既存sekfにselaの同じ面積と時間による正規化を結ぶ。selbの総量収支は前提へ追加しない。',
}
MEANINGS={
    'seld':'selaの共通面積・時間による正規化を有効な実切断で記述する。面積と時間は厳密に正とする。',
    'sele':'selbのエネルギーと仕事の総量収支を有効な実切断で表す。',
    'self':'既存sekmの反射・入出・仕事率の条件をseldへ結び、同じ量の値を共有する。',
    'selg':'同じ交換設定・鏡・面部分・時間区間・入射光と出射光・系・観測者・文脈を五つの記録へ結ぶ。面積は面部分、時間は区間、入出エネルギーは各光、仕事は鏡に帰属し、三種類の量と各単位・尺度を保持する。',
    'selh':'selgの各値を正の尺度で基準単位へ換算し、同じ面積・時間・三つの総量をselfの反射と正規化へ結ぶ。別の面や時間の値を数値一致だけで転用しない。',
    'seli':'既存の積分によるpiの指定を要求し、C=8*piとしてselhの同じ記録と面積・時間へ接続する。',
}
LIMITS=[
    '面部分と時間区間にわたり入出と仕事の率が一定な設定を明示して使う。非一様・非定常な場の積分をS*T倍へ無条件に置き換えない。',
    'exchangeは同じ交換設定・鏡・面部分・時間区間・入出光・系への割当と一様・定常な比較設定を指定する関係引数。面積や時間の数値だけから所属・一様性・反射の物理的成立を導かない。',
    'recordedbyと既存の記録関係は仮定上の測定に使う。原文が五つの実測を報告したこと、誤差がないこと、装置と単位の実現を補わない。',
    '面積・時間・エネルギーの種類を区別する。仕事の総量はエネルギーと同じ種類を使い、単位と正の尺度は五記録ごとに異なってよい。無次元の数値の一致を量の同一性としない。',
    '圧力と速度の積は単位面積あたりの仕事率である。仕事の総量と同一視せず、同じ面積と時間を乗じる。負の速度と負の仕事を許し、零速度の圧力の未決定性を保持する。',
]


def generic_composed():
    text,basis=pressure_document();basis=deepcopy(basis)
    doc=parse(text+definitions())
    basis.update(version='area-time-flux-basis-v1',document='examples/v014/area-time-flux.noema')
    basis['definitions'].update(RATIONAL_MEANINGS);basis['unresolved']+=LIMITS
    audit_basis(doc,basis)
    return format_graph(doc,'compact')+'\n',basis


def reading_definitions():
    conditions=[k('va',v('frame')),k('cf',v('incominglight')),k('cf',v('outgoinglight')),
        app(v('exchange'),*map(v,('episode','mirror','patch','interval','incominglight','outgoinglight','frame','context')))]
    for a,b in combinations(('areakind','timekind','energykind'),2):conditions.append(op('u',op('e',v(a),v(b))))
    for name in RECORDS:
        fields=dict(record=v(name+'record'),target=v(TARGETS[name]),kind=v(KINDS[name]),frame=v('frame'),
            event=v('episode'),unit=v(name+'unit'),observer=v('observer'),scale=v(name+'scale'),value=v(name+'value'),
            context=v('context'),recordedby=v('recordedby'))
        conditions.append(k('seia',*(fields[n] for n,_ in READ)))
    text=definition('selg',parameters(INPUTS),both(*conditions))
    converted={n:k('bj',v(n+'scale'),v(n+'value')) for n in RECORDS}
    text+=definition('selh',parameters(INPUTS),both(k('selg',*(v(n) for n,_ in INPUTS)),
        k('self',*(converted[n] if n in converted else v(n) for n in COMBINED.split()))))
    pi_inputs=[('pi',sort) if n=='conversion' else (n,sort) for n,sort in INPUTS]
    text+=definition('seli',parameters(pi_inputs),both(k('sedi',v('pi')),
        k('selh',*(k('shv',k('bb','n p i b'),v('pi')) if n=='conversion' else v(n) for n,_ in INPUTS))))
    return text


def source_composed():
    doc=parse((ROOT/PARENT).read_text(encoding='utf-8'))
    basis=deepcopy(json.loads((ROOT/'data/einstein-light-pressure-basis-v1.json').read_text(encoding='utf-8')))
    statements,doc['statements']=doc['statements'],[]
    doc=parse(format_graph(doc,'compact')+definitions()+definitions(True)+reading_definitions());doc['statements']=statements
    basis.update(version='einstein-area-time-flux-basis-v1',document='examples/v014/einstein-area-time-flux.noema')
    basis['definitions'].update(RATIONAL_MEANINGS|MEANINGS);basis['unresolved']+=LIMITS+[
        'u0222の同じ鏡面の単位面積・単位時間と静止系で測るエネルギーへ、明示した一様・定常な記録設定を部分接続する。新たな原始概念・局所参照・著者の主張は追加しない。',
        '面積測度と時間区間の端点・時計の構成、完全反射の境界条件、光の電磁場から各振幅と流れへの帰属、圧力の測定と力・変位による仕事の一般定義は未完。',
        '総量と正規化された率の代数的対応は、物理的エネルギー原理の証明や原文全文の意味一致ではない。零速度での圧力の物理的正当化と著者の導出の談話は残る。',
    ]
    audit_basis(doc,basis)
    return format_graph(doc,'compact')+'\n',basis


def core_composed():
    text,basis=source_composed();doc=parse(text)
    selected=extract_document(doc,roots=['sele','seli'],statement_indices=[])
    projected=extract_basis(doc,basis,selected,version='area-time-flux-core-basis-v1',document_path='examples/v014/area-time-flux-core.noema')
    return format_graph(selected.document,'compact')+'\n',projected


BUILDERS=((generic_composed,'area-time-flux'),(source_composed,'einstein-area-time-flux'),(core_composed,'area-time-flux-core'))


def main():
    for builder,stem in BUILDERS:
        text,basis=builder()
        for name,body in ((basis['document'],text),('data/'+stem+'-basis-v1.json',json.dumps(basis,ensure_ascii=False,indent=2)+'\n')):
            path=ROOT/name
            if path.exists():
                if path.read_text(encoding='utf-8')!=body:raise ValueError('Stored area/time flux differs: '+name)
            else:
                with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(body)
        print(stem,len(text),'characters')


if __name__=='__main__':main()
