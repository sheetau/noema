"""Separate a bounded field approximation from its contextual sufficiency."""
from copy import deepcopy
import json

from noema.extraction import extract_document, extract_basis
from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from scripts.compose_origin_clock import ROOT, definition, v
from scripts.compose_limits import call as k, app, op, both, quant as q
from scripts.compose_field_equations import CUT, FIELD, REGION, POINT, ROLES
from scripts.compose_field_transform import rational_definitions as mixing_definitions
from scripts.compose_wave_readings import REP, parameters, invoke, ZERO, ONE
from scripts.compose_plane_waveforms import AMPLITUDES

PARENT='examples/v014/einstein-wave-readings.noema'
FIELDS=[(n,FIELD) for n in ('electric','magnetic','approximateelectric','approximatemagnetic')]
BOUNDS=[('electricbound',CUT),('magneticbound',CUT)]
APPROX=REP+BOUNDS
ADEQUATE='h[a a a '+CUT+' '+CUT+' d] c'
SUFFICIENT=APPROX+[('scope','a'),('time',CUT),('adequate',ADEQUATE)]


def rational_definitions():
    e,b=map(v,('error','bound'));z='n p a b'
    text=definition('seba','error b bound b',both(op('u',k('aa',b,z)),op('u',k('aa',e,k('ac',b))),op('u',k('aa',b,e))))
    text+=definition('sebb','beta b absolute b electricbound b magneticbound b',
        k('ad',v('beta'),k('ab',v('electricbound'),k('ad',v('absolute'),v('magneticbound')))),'b')
    text+=definition('sebc','ratio b absolute b',both(op('u',k('aa',v('absolute'),z)),
        op('e',k('ad',v('absolute'),v('absolute')),k('ad',v('ratio'),v('ratio')))))
    return text


RATIONAL_MEANINGS={
    'seba':'有理数の非負の上限で、符号付き誤差を両側から抑える。零の上限は誤差零を要求する。',
    'sebb':'β*(電気側上限＋速度比の絶対値*磁気側上限)という成分混合の誤差上限候補。引数の許容条件は別に要求する。',
    'sebc':'非負の値の二乗を速度比の二乗へ等置して、速度比の絶対値を指定する。',
}


def generic_composed():
    doc=parse('n:r aa[b b] c.r ab[b b] b.r ac[b] b.r ad[b b] b.'+mixing_definitions()+rational_definitions())
    labels={'aa':'有理数の厳密な小なり。','ab':'有理数の加算。','ac':'有理数の加法逆元。','ad':'有理数の乗算。'}
    basis={'version':'wave-approximation-basis-v1','document':'examples/v014/wave-approximation.noema',
        'primitives':[{'symbol':d['name'],'parameters':d['parameters'],'result':d['result'],
            'arguments':['value'] if d['name']=='ac' else ['left','right'],'meaning_ja':labels[d['name']]}
            for d in doc['declarations'] if d['kind']=='primitive'],
        'definitions':{**RATIONAL_MEANINGS,'s6b':'β*(own−ratio*cross)の成分混合。','s6c':'β*(own＋ratio*cross)の成分混合。'},
        'unresolved':['有理数の成分誤差の条件。近似が用途に十分かどうかや、全実数領域での場の条件とは区別する。']}
    audit_basis(doc,basis)
    return format_graph(doc,'compact')+'\n',basis


def definitions():
    text=rational_definitions()
    text+=definition('sear','value '+CUT+' approximation '+CUT+' bound '+CUT,both(
        k('ba',v('value')),k('ba',v('approximation')),k('svw',k('bf',v('value'),v('approximation')),v('bound'))))
    coords=[app(v('point'),k(role)) for role in ROLES]
    comparisons=[k('sear',app(app(v(actual),k(role)),*coords),app(app(v(approx),k(role)),*coords),v(bound))
        for actual,approx,bound in (('electric','approximateelectric','electricbound'),('magnetic','approximatemagnetic','magneticbound'))
        for role in ROLES[:3]]
    text+=definition('seas',parameters(FIELDS+BOUNDS+[('point',POINT)]),both(k('shn',k('shx'),v('point'),'p ba'),*comparisons))
    inside=both(k('shn',k('shx'),v('point'),'p ba'),app(v('region'),*coords))
    text+=definition('seat',parameters(FIELDS+BOUNDS+[('region',REGION)]),both(
        *(both(k('ba',v(n)),k('bc',ZERO,v(n))) for n,t in BOUNDS),
        q('g','point',POINT,inside),q('f','point',POINT,op('y',inside,invoke('seas',FIELDS+BOUNDS+[('point',POINT)])))))
    V,s=map(v,('light','speed'));ratio=k('shu',k('shv',s,k('sjd',V)))
    args=[('light',CUT),('speed',CUT),*BOUNDS]
    for name,own,other in (('seau','electricbound','magneticbound'),('seav','magneticbound','electricbound')):
        text+=definition(name,parameters(args),k('shv',k('soy',V,s),k('bd',v(own),k('shv',ratio,v(other)))),CUT)
    w,a,b,c=map(v,('rate','ax','ay','az'));amps=list(map(v,AMPLITUDES))
    E=k('sdx2',v('sine'),V,w,a,b,c,*amps[:3]);H=k('sdx2',v('sine'),V,w,a,b,c,*amps[3:])
    text+=definition('seaw',parameters(APPROX),both(k('va',v('frame')),k('cf',v('wave')),
        op('u',op('e',v('electrickind'),v('magnetickind'))),
        app(v('assigned'),*(v(n) for n in ('wave','frame','electric','magnetic','region','electrickind','magnetickind','context'))),
        k('znn',*(v(n) for n in ('frame','electric','magnetic','region','context'))),
        k('sd24',v('sine'),v('cosine'),V,ZERO,w,a,b,c,*amps),k('seaj',a,b,c,*amps),
        k('seat',v('electric'),v('magnetic'),E,H,v('electricbound'),v('magneticbound'),v('region'))))
    text+=definition('seax',parameters(SUFFICIENT),both(invoke('seaw',APPROX),k('ba',v('time')),
        app(v('region'),ZERO,ZERO,ZERO,v('time')),
        app(v('adequate'),v('wave'),v('frame'),v('scope'),v('electricbound'),v('magneticbound'),v('context'))))
    newfields=[k(name,V,s,v(E),v(H)) for E,H in (('electric','magnetic'),('approximateelectric','approximatemagnetic')) for name in ('s6k','s6l')]
    text+=definition('seaz',parameters(FIELDS+BOUNDS+[('region',REGION),('light',CUT),('speed',CUT)]),both(k('s45',V,s),
        op('y',invoke('seat',FIELDS+BOUNDS+[('region',REGION)]),
            k('seat',*newfields,invoke('seau',args),invoke('seav',args),k('s6m',V,s,v('region'))))))
    return text


MEANINGS={
    'sear':'有効な実数の値と近似値の差を、同じ非負の上限で両側から抑える。上限零では値の一致になる。',
    'seas':'同じ有効な四座標で、電気側と磁気側の三成分ずつを、それぞれ指定した上限で近似する。二つの量の種類の上限を混ぜない。',
    'seat':'非空の有効な四座標領域の全点でseasを要求する。二つの非負の上限は量化の外で固定し、点ごとに選び直さない。',
    'seau':'電気側の全成分に使える変換後の上限β*(εE＋|v/V|εH)。正のV、光速未満の速度、非負の上限は利用側で要求する。',
    'seav':'磁気側の全成分に使える変換後の上限β*(εH＋|v/V|εE)。相手側の誤差からの寄与を含む。',
    'seaw':'同じ波・基準系・文脈へ割り当てた二場を、指定した正弦・位相・横波振幅の二場でseatの範囲内に近似する。seanの完全一致とは区別し、近似から厳密な振幅記録を導かない。',
    'seax':'seawの近似領域が指定時刻の空間原点を含み、同じ波・基準系・用途・二つの上限・文脈についてadequate引数の十分性条件を満たす。上限が存在するだけでは十分と認定しない。',
    'seaz':'許容速度の下で、旧領域でseatを満たすなら、両組の場と領域を同じ逆座標変換で写したものがseau/seavの上限を満たすという条件文。定義自体を実数全域の証明とは扱わない。',
}


def source_composed():
    doc=parse((ROOT/PARENT).read_text(encoding='utf-8'))
    basis=deepcopy(json.loads((ROOT/'data/einstein-wave-readings-basis-v1.json').read_text(encoding='utf-8')))
    statements,doc['statements']=doc['statements'],[]
    doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=statements
    basis.update(version='einstein-wave-approximation-basis-v1',document='examples/v014/einstein-wave-approximation.noema')
    basis['definitions'].update(RATIONAL_MEANINGS);basis['definitions'].update(MEANINGS)
    basis['unresolved'] += [
        'u0179の原点を含む領域で十分な近似として波を表すという条件へ部分対応する。二場の成分ごとの一様な絶対誤差は今回の明示的な実現例であり、原文がこの尺度を一意に指定しているとはしない。',
        '用途と上限の十分性はadequate関係として明示する。数値上限を勝手に補わず、全域で有界という条件だけで用途に十分とはしない。遠方光源から誤差評価が導けることも未証明。',
        'seaxの空間原点の包含は明示した一時刻における条件である。原文の空間領域の全時間にわたる持続や開集合としての近傍、源との距離は別に記述する必要がある。',
        '厳密な測定記録seap/seaqは変更しない。seawを満たすことからそれらの厳密な振幅の一致は導かず、測定誤差と推定誤差の一般理論も未完。',
        '二系で同じ数値の誤差上限が通用するとは限らない。混合された二場の上限を変換するが、変換後にも同じ用途で十分であることは別条件である。',
        '有理数の成分誤差の証明と、実数切断の全域の場の条件を区別する。本文173主張を保持し、全文の意味一致は未完。',
    ]
    audit_basis(doc,basis)
    return format_graph(doc,'compact')+'\n',basis


def core_composed():
    text,basis=source_composed();doc=parse(text)
    selected=extract_document(doc,roots=['seax','seaz'],statement_indices=[])
    projected=extract_basis(doc,basis,selected,version='wave-approximation-core-basis-v1',document_path='examples/v014/wave-approximation-core.noema')
    return format_graph(selected.document,'compact')+'\n',projected


def main():
    for builder,stem in ((generic_composed,'wave-approximation'),(source_composed,'einstein-wave-approximation'),(core_composed,'wave-approximation-core')):
        text,basis=builder()
        for name,body in ((basis['document'],text),('data/'+stem+'-basis-v1.json',json.dumps(basis,ensure_ascii=False,indent=2)+'\n')):
            path=ROOT/name
            if path.exists():
                if path.read_text(encoding='utf-8')!=body:raise ValueError('Stored wave approximation differs: '+name)
            else:
                with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(body)
        print(stem,len(text),'characters')


if __name__=='__main__':main()
